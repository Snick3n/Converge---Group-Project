from django.contrib import admin
from .models import EventPlanner, Genre, Room, Event, RSVP, BlockedDate

# Register your models here.
admin.site.register(EventPlanner)
admin.site.register(Genre)
admin.site.register(Room)
admin.site.register(Event)
admin.site.register(RSVP)
@admin.register(BlockedDate)
class BlockedDateAdmin(admin.ModelAdmin):
    list_display = ("date", "reason")
    search_fields = ("date", "reason")
    ordering = ("date",)