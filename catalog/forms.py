from .models import Event, EventPlanner, Genre, BlockedDate, EventNotification, Room
from django import forms


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
class BlockedDateForm(forms.ModelForm):
    class Meta:
        model = BlockedDate
        fields = ['date', 'reason']
        widgets = {
            "date": forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            "reason": forms.TextInput(attrs={'class': 'form-control'}),
        }
class BulkBlockDatesForm(forms.Form):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    reason = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        if start and end and end < start:
            raise forms.ValidationError('End date cannot be before start date.')
        return cleaned_data

class EventNotificationForm(forms.ModelForm):
    class Meta:
        model = EventNotification
        fields = ['subject', 'body', 'scheduled_for']
        widgets = {
            'scheduled_for': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['scheduled_for'].input_formats = ['%Y-%m-%dT%H:%M']

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ["name", "capacity", "status"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "capacity": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 100}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }