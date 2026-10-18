from django import forms
from .models import Ticket

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'category', 'priority'] 

        def __init__(self, *args, **kwargs):
            super().__init__(self, *args, **kwargs)
            self.fields['priority'].initial = Ticket.Priority.MEDIUM

    
        