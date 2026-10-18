from django.shortcuts import render, redirect, get_object_or_404
from .forms import TicketForm
from django.contrib.auth.decorators import login_required
from .models import Ticket


# Create your views here.
@login_required
def create(request):
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
            return redirect('ticket_detail', ticket_id=obj.id)  # Redirect to the ticket list view after successful creation
    else:
        form = TicketForm()
    return render(request, 'tickets/create_ticket.html', {'form' : form})

@login_required
def tickets(request):
    tickets = Ticket.objects.filter(created_by=request.user)
    return render(request, 'tickets/ticket_list.html', {'tickets': tickets})

@login_required
def detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, id = ticket_id, created_by = request.user)
    return render(request, 'tickets/ticket_detail.html', {'ticket' : ticket})
