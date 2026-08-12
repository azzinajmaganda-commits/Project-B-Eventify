from django.conf import settings
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from decimal import Decimal


class Event(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="events",
    )

    title = models.CharField(
        max_length=200,
    )

    description = models.TextField()

    location = models.CharField(
        max_length=255,
    )

    event_date = models.DateTimeField()

    ticket_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
    )

    max_tickets = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
        ],
    )

    poster = models.ImageField(
        upload_to="event_posters/",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["jpg", "jpeg", "png", "webp"]
            )
        ],
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.title