from django.urls import path
from . import views

urlpatterns = [
    path("", views.tickets, name="tickets"),
    path("create/", views.create, name="ticket_create"),
    path("agent/queue/", views.agent_queue, name="agent_queue"),
    path("<int:ticket_id>/", views.detail, name="ticket_detail"),
    path(
        "<int:ticket_id>/assign/",
        views.assign_ticket,
        name="ticket_assign",
    ),
    path(
        "<int:ticket_id>/status/",
        views.update_ticket_status,
        name="ticket_status_update",
    ),
]
