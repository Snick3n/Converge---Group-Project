from django.contrib import admin
from .models import EventPlanner, Genre, Room, Event, RSVP

# Register your models here.
admin.site.register(EventPlanner)
admin.site.register(Genre)
admin.site.register(Room)
admin.site.register(Event)
admin.site.register(RSVP)