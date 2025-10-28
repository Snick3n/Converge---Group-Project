from django import forms
from .models import Event

class EventBookingForm(forms.ModelForm):
    expected_attendees = forms.IntegerField(min_value=1, max_value=100, required=True)

    class Meta:
        model = Event
        fields = ["name", "genre", "detail", "planner", "expected_attendees", "room"]

    def __init__(self, *args, **kwargs):
        available_rooms = kwargs.pop("available_rooms", None)
        super().__init__(*args, **kwargs)
        if available_rooms is not None:
            self.fields["room"].queryset = available_rooms
