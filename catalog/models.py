from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
import uuid #for unique room and event instances

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
    def __str__(self):
        return self.name

class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    max_attendees = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    date = models.DateField()
    time = models.TimeField()
    planner = models.ForeignKey('EventPlanner', on_delete=models.RESTRICT)
    genre = models.ManyToManyField('Genre', help_text='Select genres to add to this event')
    detail = models.TextField(max_length=1000)
    room = models.ForeignKey('Room', on_delete=models.RESTRICT)
    class Meta:
        ordering = ['date', 'time']
    def get_absolute_url(self):
        return reverse('event detail', args=[str(self.id,)])
    def __str__(self):
        return self.name

class EventPlanner(models.Model):
    name = models.CharField(max_length=255)
    detail = models.TextField(max_length=1000)
    image = models.ImageField(upload_to='event-planner-images', null=True, blank=True)
    def get_absolute_url(self):
        return reverse('event planner detail', args=[str(self.id,)])
    def __str__(self):
        return self.name

class RSVP(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey('Event', on_delete=models.CASCADE)
    planner = models.ForeignKey('EventPlanner', on_delete=models.CASCADE)
    message = models.TextField(max_length=500)
    send_date = models.DateField()
    rsvp_count = models.IntegerField(default=0)
    class Meta:
        ordering = ['event']
    def increase_rsvp(self):
        self.rsvp_count += 1
        return self.rsvp_count
    def __str__(self):
        return f'{self.id} ({self.event})'





