from django.shortcuts import render, redirect, get_object_or_404
from .forms import TicketForm, TicketAssignmentForm, TicketStatusForm, TicketMessageForm
from django.contrib.auth.decorators import login_required
from .models import Ticket, TicketMessage
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


def get_authorized_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)

    if request.user.role != "AGENT" and ticket.created_by_id != request.user.id:
        raise Http404

    return ticket


@login_required
def detail(request, ticket_id):
    ticket = get_authorized_ticket(request, ticket_id)

    context = {
        "ticket": ticket,
        "ticket_messages": ticket.messages.select_related("author").all(),
        "message_form": TicketMessageForm(),
    }

    if request.user.role == "AGENT":
        context["status_form"] = TicketStatusForm(initial={"status": ticket.status})

    return render(request, 'tickets/ticket_detail.html', context)


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


@agent_required
def update_ticket_status(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk = ticket_id)

    if request.method != "POST":
        return redirect("ticket_detail", ticket_id=ticket.pk)

    form = TicketStatusForm(request.POST)
    if form.is_valid():
        ticket.status = form.cleaned_data["status"]
        ticket.save(update_fields=["status"])
        messages.success(request, "Ticket status updated successfully!")

    else:
        messages.error(request, "Invalid status. Please select a valid status")

    return redirect("ticket_detail", ticket_id = ticket.pk)


@login_required
def post_ticket_message(request, ticket_id):
    ticket = get_authorized_ticket(request, ticket_id)

    if request.method != "POST":
        return redirect("ticket_detail", ticket_id=ticket.pk)

    form = TicketMessageForm(request.POST)

    if form.is_valid():
        message = form.save(commit=False)
        message.ticket = ticket
        message.author = request.user
        message.save()

        messages.success(request, "Message sent successfully.")
    else:
        messages.error(
            request,
            "Please enter a valid message before submitting.",
        )

    return redirect("ticket_detail", ticket_id=ticket.pk)
