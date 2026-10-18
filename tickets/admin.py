from django.contrib import admin
from .models import Ticket, TicketMessage

# Register your models here.

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'title',
        'description',
        'category',
        'priority',
        'status',
        'created_by',
        'assigned_to',
        'created_at',
    ]

    list_filter = [
        'category',
        'priority',
        'status',
    ]

    search_fields = ('title', 'description',)


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'ticket',
        'author',
        'created_at',
    ]

    search_fields = ('body',)
