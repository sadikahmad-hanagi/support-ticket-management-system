from django.shortcuts import render, redirect, get_object_or_404
from .forms import TicketForm, TicketAssignmentForm
from django.contrib.auth.decorators import login_required
from .models import Ticket
from .permissions import agent_required
from django.contrib import messages
from django.http import Http404

# Create your views here.
@login_required
def create(request):

    if request.user.role == "AGENT":
        return redirect("agent_queue")


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
    if request.user.role == "AGENT":
        return redirect("agent_queue")
    tickets = Ticket.objects.filter(created_by=request.user)
    return render(request, 'tickets/ticket_list.html', {'tickets': tickets})

@login_required
def detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, id = ticket_id)

    if request.user.role != "AGENT" and ticket.created_by != request.user:
        raise Http404
    
    return render(request, 'tickets/ticket_detail.html', {'ticket' : ticket})


@agent_required
def agent_queue(request):
    status = request.GET.get("status", "")

    valid_statuses = Ticket.Status.values

    tickets = Ticket.objects.select_related("created_by", "assigned_to")

    if status in valid_statuses:
        tickets = tickets.filter(status=status)
    elif status != "":
        status = ""

    return render(
        request,
        "tickets/agent_queue.html",
        {
            "tickets": tickets,
            "selected_status": status,
            "statuses": Ticket.Status.choices,
            "assignment_form": TicketAssignmentForm(),
        },
    )


@agent_required
def assign_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)

    if request.method == "POST":
        form = TicketAssignmentForm(request.POST)

        if form.is_valid():
            ticket.assigned_to = form.cleaned_data["assignee"]
            ticket.save(update_fields=["assigned_to", "updated_at"])

            messages.success(request, "Ticket assignment updated.")
        else:
            messages.error(request, "Invalid assignee. Please select an agent.")

    return redirect("agent_queue") 
