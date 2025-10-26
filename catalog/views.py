from django.shortcuts import render
import calendar
from datetime import date, datetime, timedelta
from django.urls import reverse
from django.utils import timezone
from .models import Event, Room, VALID_HOURS
from django.views import View
from django.db.models import Count
from django.contrib.auth.mixins import LoginRequiredMixin

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
        .filter(date__range=(visible_days_start, visible_days_end))
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

def index(request):
    now = timezone.localtime()
    cy, cm = now.year, now.month
    ny, nm = (cy + 1, 1) if cm == 12 else (cy, cm + 1)

    current_month = _month_grid(cy, cm, capacity_aware=True)
    next_month    = _month_grid(ny, nm, capacity_aware=True)

    current_events = (
        Event.objects
        .filter(date__range=(date(cy, cm, 1), date(cy, cm, calendar.monthrange(cy, cm)[1])))
        .order_by('date', 'time')[:4]
    )
    upcoming_events = (
        Event.objects
        .filter(date__gt=date(cy, cm, calendar.monthrange(cy, cm)[1]))
        .order_by('date', 'time')[:4]
    )

    return render(request, "index.html", {
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

        by_key = {(e.room.id, e.time.hour): e for e in events}

        rows = []
        for h in VALID_HOURS:
            cells = []
            for r in rooms:
                e = by_key.get((r.id, h))
                cells.append({
                    'room': r,
                    'event': e,
                    'booked': e is not None,
                    'book_url': f"{reverse('catalog:index')}?room={r.id}&date={d:%Y-%m-%d}&time={h:02d}:00",
                })

            rows.append({'hour': h, 'cells': cells})

        return render(
            request,
            'day.html',
            {'date': d, 'rooms': rooms, 'rows': rows}
        )
