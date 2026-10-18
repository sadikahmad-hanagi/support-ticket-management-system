from django.urls import path
from . import views

urlpatterns = [
    path("", views.tickets, name="tickets"),
    path("create/", views.create, name="ticket_create"),
    path("<int:ticket_id>/", views.detail, name="ticket_detail"),
]
