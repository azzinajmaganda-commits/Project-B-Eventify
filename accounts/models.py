from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import CustomUserManager


class User(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        ORGANIZER = "organizer", "Organizer"
        ATTENDEE = "attendee", "Attendee"

    # Remove Django's original username field.
    username = None

    email = models.EmailField(
        unique=True,
        help_text="The email address used to log in.",
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ATTENDEE,
    )

    # Admin access status
    admin_access_status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("denied", "Denied"),
        ],
        default="approved",
    )

    # The original / real administrator of the system.
    # This account can never be removed or demoted by
    # another administrator.
    is_primary_admin = models.BooleanField(
        default=False,
        help_text="Protect this account as the primary system administrator.",
    )

    # Django will authenticate users with email.
    USERNAME_FIELD = "email"

    # These fields are requested by createsuperuser.
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        name = self.get_full_name().strip()
        return name or self.email


class AdminAccessRequest(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        DENIED = "denied", "Denied"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="admin_access_request",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    requested_at = models.DateTimeField(
        auto_now_add=True,
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_admin_requests",
    )

    def __str__(self):
        return f"{self.user.email} - {self.status}"