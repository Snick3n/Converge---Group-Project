from .models import Event,EventPlanner, Genre
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class EventBookingForm(forms.Form):
    name = forms.CharField(label="Event name", max_length=255)
    detail = forms.CharField(
        label="Details",
        widget=forms.Textarea,
        required=False
    )
    expected_attendees = forms.IntegerField(label="Expected attendees", min_value=1)

    genre = forms.ModelChoiceField(
        label="Select genres to add to this event",
        queryset=Genre.objects.all(),
        required=False,
    )

class EventPlannerForm(forms.ModelForm):
    class Meta:
        model = EventPlanner
        fields = ['name', 'detail', 'image']