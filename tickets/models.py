from django.db import models
from django.conf import settings


# Create your models here.
class Ticket(models.Model):
    class Category(models.TextChoices):
        BUG = "BUG", "Bug"
        BILLING = "BILLING", "Billing"
        ACCOUNT = "ACCOUNT", "Account"
        GENERAL = "GENERAL", "General"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        RESOLVED = "RESOLVED", "Resolved"
        CLOSED = "CLOSED", "Closed"

    title = models.CharField(max_length=200)
    description = models.TextField

    category = models.CharField(max_length=20, choices=Category.choices)
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPEN
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_tickets",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='assigned_tickets'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Ticket #{self.pk} - {self.title}"


class TicketMessage(models.Model):
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name="messages"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="authored_ticket_messages",
    )

    body = models.TextField
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message on Ticket {self.ticket_id} by {self.author}"
