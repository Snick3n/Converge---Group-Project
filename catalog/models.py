from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
import uuid #for unique room and event instances
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import time, timedelta
from django.db.models import Q
from django.contrib.auth.models import User


VALID_HOURS = (10, 12, 14, 16, 18, 20)
SLOT_DURATION = 2
LAST_END_HOUR = 22

class Genre(models.Model):
    name = models.CharField(max_length=100, help_text='Enter type of event (e.g. Speech, Birthday, Club Meeting)')
    def __str__(self):
        return self.name

class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    capacity = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    available_status = (('a', 'Available'), ('r', 'Reserved'), ('u', 'Unavailable'))
    status = models.CharField(max_length=1, choices=available_status, default='a', help_text='Room availability')
    class Meta:
        ordering = ['name', 'capacity', 'status']
    def is_available(self, date, time):
        return not Event.objects.filter(date=date, time=time, room=self, approved=True,).exists()
    def __str__(self):
        return self.name

class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    max_attendees = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    date = models.DateField()
    time = models.TimeField()
    planner = models.ForeignKey('EventPlanner', on_delete=models.CASCADE)
    genre = models.ManyToManyField('Genre', help_text='Select genres to add to this event')
    detail = models.TextField(max_length=1000)
    room = models.ForeignKey('Room', on_delete=models.RESTRICT)
    approved = models.BooleanField(default=False)
    rsvp_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['date', 'time']
        constraints = [
            models.UniqueConstraint(
                fields=['room', 'date', 'time'],
                condition=Q(approved=True),
                name='uniq_room_date_times'
                )
            ]
    def end_time(self) -> time:
        return (timezone.datetime.combine(self.date, self.time) + timedelta(hours=SLOT_DURATION)).time()
    def clean(self):
        if not self.time:
            return
        if self.time.minute != 0 or self.time.second != 0 or self.time.microsecond != 0:
            raise ValidationError('Events must start exactly on the hour.')
        if self.time.hour not in VALID_HOURS:
            raise ValidationError('Start time must be one of these: 10, 12, 14, 16, 18, or 20.')
        if self.time.hour + SLOT_DURATION > LAST_END_HOUR:
            raise ValidationError('Event would end after 10 PM.')

    def save(self, *args, **kwargs):
        approving_now = False
        is_creating = self._state.adding

        if not is_creating:
            previous = Event.objects.get(pk=self.pk)
            if not previous.approved and self.approved:
                approving_now = True
        else:
            if self.approved:
                approving_now = True

        super().save(*args, **kwargs)
        if approving_now:
            Event.objects.filter(
                room=self.room,
                date=self.date,
                time=self.time,
                approved=False,
            ).exclude(pk=self.pk).delete()

class EventPlanner(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    detail = models.TextField(max_length=1000)
    image = models.ImageField(upload_to='event-planner-images', null=True, blank=True)
    def get_absolute_url(self):
        return reverse('eventplanner_detail', args=[str(self.id)])
    def __str__(self):
        return self.name

class RSVP(models.Model):
    RSVP_STATUS = (('y', 'Attending'), ('n', 'Not attending'))

    id = models.AutoField(primary_key=True)  # ← let Django use an integer PK
    event = models.ForeignKey('Event', on_delete=models.CASCADE, related_name='rsvps')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, null=True, related_name='rsvps')
    status = models.CharField(max_length=1, choices=RSVP_STATUS, default='y')

    class Meta:
        ordering = ['event']
        unique_together = ('event', 'user')  # one RSVP per user per event

    def __str__(self):
        return f'{self.user} → {self.event} ({self.get_status_display()})'

class BlockedDate(models.Model):
    date = models.DateField(unique=True)
    reason = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ["date"]
        verbose_name = "Blocked Date"
        verbose_name_plural = "Blocked Dates"
    def __str__(self):
        return f"{self.date} ({self.reason}"  if self.reason else str(self.date)

class EventNotification(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='notifications')
    planner = models.ForeignKey('EventPlanner', on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    scheduled_for = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    sent = models.BooleanField(default=False)

    class Meta:
        ordering = ['scheduled_for']

    def __str__(self):
        return f"Notification for {self.event.name} at {self.scheduled_for}"