from django import forms
from .models import Ticket
from django.contrib.auth import get_user_model

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'category', 'priority'] 

        def __init__(self, *args, **kwargs):
            super().__init__(self, *args, **kwargs)
            self.fields['priority'].initial = Ticket.Priority.MEDIUM


User = get_user_model()


class TicketAssignmentForm(forms.Form):
    assignee = forms.ModelChoiceField(
        queryset=User.objects.filter(role="AGENT"),
        required=False,
        empty_label="Unassigned",
        label="Assign to agent",
    )


class TicketStatusForm(forms.Form):
    status = forms.ChoiceField(
        choices=Ticket.Status.choices,
        label="Update status",
    )
