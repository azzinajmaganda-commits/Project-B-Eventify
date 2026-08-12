from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label="First name",
    )

    last_name = forms.CharField(
        max_length=150,
        required=True,
        label="Last name",
    )

    email = forms.EmailField(
        required=True,
        label="Email address",
    )

    role = forms.ChoiceField(
        choices=[
            (User.Role.ADMIN, "Admin"),
            (User.Role.ORGANIZER, "Organizer"),
            (User.Role.ATTENDEE, "Attendee"),
        ],
        label="Account role",
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "role",
            "password1",
            "password2",
        ]

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email address already exists."
            )

        return email

    def save(self, commit=True):
        user = super().save(commit=False)

        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        user.role = self.cleaned_data["role"]

        # Only users requesting the Admin role need approval.
        if user.role == User.Role.ADMIN:
            user.admin_access_status = "pending"
        else:
            user.admin_access_status = "approved"

        # Never give Django admin permissions during public registration.
        user.is_staff = False
        user.is_superuser = False

        if commit:
            user.save()

        return user


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(
            attrs={
                "autofocus": True,
                "autocomplete": "email",
            }
        ),
    )
