from django.contrib import admin

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "created_by",
        "event_date",
        "ticket_price",
        "max_tickets",
        "created_at",
    )

    list_filter = (
        "event_date",
        "created_at",
    )

    search_fields = (
        "title",
        "location",
        "created_by__email",
    )