from django.shortcuts import render, get_object_or_404, redirect
import calendar
from datetime import date, datetime
from django.urls import reverse
from django.utils import timezone
from .forms import EventBookingForm, EventPlannerForm
from django.views.generic.edit import UpdateView
from django.contrib.auth.models import Group, User
from django.http import HttpResponseBadRequest, HttpResponseForbidden, HttpResponseRedirect
from .models import Event, EventPlanner, Room, VALID_HOURS, RSVP
from django.views import View, generic
from django.db.models import Count
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


SLOTS_PER_DAY = 6

# Create your views here.

def _month_grid(year: int, month: int, capacity_aware: bool = True):

    cal = calendar.Calendar(firstweekday=6)
    weeks = cal.monthdatescalendar(year, month)

    month_start = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    month_end = date(year, month, last_day)

    visible_days_start = weeks[0][0]
    visible_days_end = weeks[-1][-1]

    counts_qs = (
        Event.objects
        .filter(
            approved=True,
            date__range=(visible_days_start, visible_days_end))
        .values('date')
        .annotate(count=Count('id'))
    )

    by_day = {row['date']: row['count'] for row in counts_qs}

    rooms_total = Room.objects.filter(status='a').count() or 1
    slots_total = rooms_total * 6

    def load_class(n: int) -> str:
        if not capacity_aware:
            if n == 0: return "load-0"
            if n <= 2: return "load-1"
            if n <= 4: return "load-2"
            return "load-3"
        ratio = n / slots_total
        if ratio == 0: return "load-0"
        if ratio <= 0.33: return "load-1"
        if ratio <= 0.66: return "load-2"
        return "load-3"

    grid = []
    for week in weeks:
        row = []
        for d in week:
            count = by_day.get(d, 0)
            row.append({
                "date": d,
                "in_month": (d.month == month),
                "count": count,
                "cls": load_class(count),
                "url": reverse("catalog:calendar-day", args=[d.year, d.month, d.day]),
            })
        grid.append(row)

    return {
        "year": year,
        "month": month,
        "name": calendar.month_name[month],
        "weeks": grid,
        "rooms_total": rooms_total,
        "slots_total": slots_total,
    }
def _cleanup_old_events():
    today = timezone.localtime().date()
    first_of_this_month = date(today.year, today.month, 1)
    Event.objects.filter(date__lt=first_of_this_month).delete()

def index(request):

    _cleanup_old_events()

    now = timezone.localtime()
    cy, cm = now.year, now.month
    ny, nm = (cy + 1, 1) if cm == 12 else (cy, cm + 1)

    current_month = _month_grid(cy, cm, capacity_aware=True)
    next_month    = _month_grid(ny, nm, capacity_aware=True)

    current_events = (
        Event.objects
        .filter(approved=True,
                date__range=(date(cy, cm, 1), date(cy, cm, calendar.monthrange(cy, cm)[1])))
        .order_by('date', 'time')[:4]
    )
    upcoming_events = (
        Event.objects
        .filter(approved=True,
            date__gt=date(cy, cm, calendar.monthrange(cy, cm)[1]))
        .order_by('date', 'time')[:4]
    )

    return render(request, "catalog/index.html", {
        "current_month": current_month,
        "next_month": next_month,
        "current_events": current_events,
        "upcoming_events": upcoming_events,
    })
class DayView(View):
    def get(self, request, year, month, day):
        d = date(int(year), int(month), int(day))
        rooms = list(Room.objects.order_by('name'))

        events = (
            Event.objects
            .filter(date=d)
            .select_related('room', 'planner')
        )
        by_key = {}
        for e in events:
            key = (e.room.id, e.time.hour)
            by_key.setdefault(key, []).append(e)

        rows = []
        for h in VALID_HOURS:
            cells = []
            for r in rooms:
                evs = by_key.get((r.id, h), [])

                book_url = (
                    f"{reverse('catalog:book')}"
                    f"?room={r.id}"
                    f"&date={d:%Y-%m-%d}"
                    f"&time={h:02d}:00"
                )
                has_approved = any(ev.approved for ev in evs)

                cells.append({
                    "room_name": r.name,
                    "room_id": str(r.id),
                    "events": evs,
                    "booked": bool(evs),
                    "has_approved": has_approved,
                    "book_url": book_url,
                })

            rows.append({
                "hour": h,
                "cells": cells,
            })

        can_book = (
            request.user.is_authenticated and (
                request.user.is_superuser
                or request.user.groups.filter(name="EventPlanner").exists()
            )
        )

        return render(
            request,
            "catalog/day.html",
            {
                "date": d,
                "rooms": rooms,
                "rows": rows,
                "can_book": can_book,
            }
        )

def find_best_room(date, time, expected_attendees):
    booked_room_ids = Event.objects.filter(
        date=date,
        time=time,
        approved=True,
    ).values_list('room_id', flat=True)

    available_rooms = Room.objects.filter(status='a').exclude(id__in=booked_room_ids)
    suitable_rooms = available_rooms.filter(capacity__gte=expected_attendees).order_by('capacity')
    return suitable_rooms.first()

def can_book_user(user):
    return (
        user.is_authenticated
        and (
        user.is_superuser or
        user.groups.filter(name="EventPlanner").exists()
        )
    )


@login_required
@user_passes_test(can_book_user)
def book_event(request):
    room_id = request.GET.get("room")
    date_str = request.GET.get("date")
    time_str = request.GET.get("time")

    if not room_id or not date_str or not time_str:
        return HttpResponseBadRequest("Missing room, date, or time.")

    room = get_object_or_404(Room, id=room_id)
    event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    start_time = datetime.strptime(time_str, "%H:%M").time()

    if request.method == "POST":
        form = EventBookingForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            detail = form.cleaned_data["detail"]
            expected_attendees = form.cleaned_data["expected_attendees"]
            selected_genres = form.cleaned_data.get("genre")

            if room.is_available(event_date, start_time) and room.capacity >= expected_attendees:
                chosen_room = room
            else:
                chosen_room = find_best_room(event_date, start_time, expected_attendees)
                if chosen_room:
                    messages.info(request, f"{room.name} was full — assigned {chosen_room.name} instead.")
                else:
                    messages.error(request, "No available rooms fit that group size at this time.")
                    return redirect(
                        "catalog:calendar-day",
                        year=event_date.year,
                        month=event_date.month,
                        day=event_date.day,
                    )

            event = Event(
                name=name,
                max_attendees=expected_attendees,
                date=event_date,
                time=start_time,
                detail=detail,
                room=chosen_room,
                approved=False,
            )

            try:
                event.planner = request.user.eventplanner
            except EventPlanner.DoesNotExist:
                pass

            event.save()
            if selected_genres:
                event.genre.set([selected_genres])

            messages.success(request, f"Event booked in {event.room.name}!")
            return redirect(
                "catalog:calendar-day",
                year=event_date.year,
                month=event_date.month,
                day=event_date.day,
            )
    else:
        form = EventBookingForm()

    return render(
        request,
        "catalog/book_event.html",
        {
            "form": form,
            "room": room,
            "date": event_date,
            "time": start_time,
        },
    )


class EventPlannerListView( generic.ListView):
    model = EventPlanner
class EventPlannerDetailView( generic.DetailView):
    model = EventPlanner

class EventPlannerUpdate(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = EventPlanner
    fields = ['name', 'detail', 'image']
    template_name = "catalog/eventplanner_form.html"

    def test_func(self):
        planner = self.get_object()
        user = self.request.user
        return user.is_superuser or planner.user == user

    def get_success_url(self):
        messages.success(self.request, "Event planner updated successfully.")
        return reverse('catalog:eventplanner_list')

def EventPlannerDelete(request, pk):
    eventplanner = get_object_or_404(EventPlanner, pk=pk)
    try:
        eventplanner.delete()
        messages.success(request, (eventplanner.name + " has been deleted."))
    except:
        messages.error(request, (eventplanner.name + " cannot be deleted. Events exist for this planner."))
    return redirect('catalog:eventplanner_list')
class EventListView( generic.ListView):
    model = Event
    template_name = "catalog/event_list.html"
    def get_queryset(self):
        qs = super().get_queryset().select_related("planner")
        user = self.request.user
        for e in qs:
            is_owner = bool(e.planner and getattr(e.planner, 'user', None) == user)
            can_manage= user.is_superuser or is_owner
            show_event = e.approved or can_manage
            e.is_owner = is_owner
            e.can_manage = can_manage
            e.show_event = show_event
        return qs
class EventDetailView( generic.DetailView):
    model = Event

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            context['user_rsvp'] = RSVP.objects.filter(event=self.object, user=user).first()
        else:
            context['user_rsvp'] = None
        return context
class EventUpdate(UpdateView):
    model = Event
    fields = [
        'name',
        'max_attendees',
        'planner',
        'genre',
        'detail',
        'approved',
    ]
    template_name = 'catalog/event_form.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if not self.request.user.is_superuser:
            form.fields.pop('approved',  None)
            form.fields.pop('planner', None)
        return form
    def form_valid(self, form):
        if not self.request.user.is_superuser:
            original = self.get_object()
            form.instance.approved = original.approved
            form.instance.planner = original.planner
        return super().form_valid(form)

    def get_success_url(self):
        next_url = self.request.GET.get("next")
        if next_url:
            return next_url
        event_date = self.object.date
        return reverse(
            "catalog:calendar-day",
            kwargs={
                "year": event_date.year,
                "month": event_date.month,
                "day": event_date.day,
            },
        )

def event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)

    event_date = event.date

    if not request.user.is_superuser:
        if not (event.planner and event.planner.user == request.user):
            messages.error(request, "You do not have permission to delete this event.")
            return redirect(
                'catalog:calendar-day',
                year=event_date.year,
                month=event_date.month,
                day=event_date.day,
            )

    try:
        event.delete()
        messages.success(request, f"{event.name} was deleted successfully.")
    except Exception:
        messages.error(request, f"{event.name} could not be deleted.")

    return redirect(
        'catalog:calendar-day',
        year=event_date.year,
        month=event_date.month,
        day=event_date.day,
    )
@login_required
def become_event_planner(request):
    user = request.user

    if hasattr(user, "eventplanner"):
        messages.info(request, "You already have an event planner profile.")
        return redirect("catalog:index")

    if request.method == "POST":
        form = EventPlannerForm(request.POST, request.FILES)
        if form.is_valid():
            planner = form.save(commit=False)
            planner.user = user
            planner.save()

            planner_group, _ = Group.objects.get_or_create(name="EventPlanner")
            user.groups.add(planner_group)
            user.save()

            messages.success(request, "You're now an event planner!")
            return redirect("catalog:index")
    else:
        form = EventPlannerForm()

    return render(request, "catalog/become_event_planner.html", {"form": form})


@login_required
def rsvp_event(request, event_id, status):
    event = get_object_or_404(Event, id=event_id)

    valid_statuses = dict(RSVP.RSVP_STATUS).keys()  # ['y', 'n']
    if status not in valid_statuses:
        status = 'n'
        messages.error(request, "Invalid RSVP status; defaulted to 'Not attending'.")

    # Find any existing RSVP for this user+event
    existing = RSVP.objects.filter(event=event, user=request.user).first()
    previous_status = existing.status if existing else None

    # Figure out where to go back to
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or reverse('catalog:event_list')

    # If user is trying to change to 'Attending' and the event is full (and they weren't already attending)
    if previous_status != 'y' and status == 'y' and event.rsvp_count >= event.max_attendees:
        messages.error(request, "This event is full. You cannot RSVP as attending.")
        return redirect(next_url)

    # Create or update the RSVP
    if existing:
        rsvp = existing
        rsvp.status = status
        rsvp.save()
        created = False
    else:
        rsvp = RSVP.objects.create(
            event=event,
            user=request.user,
            status=status,
        )
        created = True

    # 🔢 Update event.rsvp_count based on status change
    if previous_status != 'y' and status == 'y':
        event.rsvp_count += 1
    elif previous_status == 'y' and status != 'y' and event.rsvp_count > 0:
        event.rsvp_count -= 1

    event.save()

    # Messages
    if created and status == 'y':
        messages.success(request, "You have signed up for this event.")
    elif status == 'y':
        messages.success(request, "Your RSVP has been updated to 'Attending'.")
    else:
        messages.success(request, "Your RSVP has been updated.")

    return redirect(next_url)

class UserRSVPListView(LoginRequiredMixin, generic.ListView):
    model = RSVP
    template_name = 'catalog/my_rsvps.html'
    context_object_name = 'rsvps'

    def get_queryset(self):
        return (
            RSVP.objects
            .filter(user=self.request.user, status='y')
            .select_related('event')
            .order_by('event__date', 'event__time')
        )

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

class UserListView(LoginRequiredMixin, AdminRequiredMixin, generic.TemplateView):
    template_name = "catalog/user_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admins = User.objects.filter(is_superuser=True).order_by("username")
        planners = (
            EventPlanner.objects
            .select_related("user")
            .order_by("user__username")
        )
        goers = (
            User.objects
            .filter(is_superuser=False)
            .exclude(eventplanner__isnull=False)
            .order_by("username")
        )
        context["admins"] = admins
        context["planners"] = planners
        context["goers"] = goers
        return context

class UserUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = User
    template_name = "catalog/user_form.html"
    fields = ["first_name", "last_name", "email"]

    def get_success_url(self):
        messages.success(self.request, "User updated successfully.")
        return reverse("catalog:user_list")

def user_delete(request, pk):
    user_obj = get_object_or_404(User, pk=pk)

    if user_obj == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('catalog:user_list')

    name = user_obj.get_full_name() or user_obj.username

    try:
        user_obj.delete()
        messages.success(request, f"{name} has been deleted.")
    except Exception:
        messages.error(request, f"{name} could not be deleted.")

    return redirect('catalog:user_list')