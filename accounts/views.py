from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import RegistrationForm
from .models import AdminAccessRequest, User


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()

            # Admin accounts require approval from the existing administrator.
            if user.role == User.Role.ADMIN:
                AdminAccessRequest.objects.get_or_create(
                    user=user,
                    defaults={
                        "status": AdminAccessRequest.Status.PENDING,
                    },
                )

                messages.warning(
                    request,
                    "Your admin access request has been submitted. "
                    "Please wait for approval from the existing administrator.",
                )

                return redirect("admin_access_pending")

            # Organizer and Attendee accounts can log in immediately.
            login(request, user)

            messages.success(
                request,
                "Your account was created successfully.",
            )

            return redirect("dashboard")

    else:
        form = RegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form},
    )


@login_required
def dashboard_view(request):

    # ---------------------------------------------------------
    # ADMIN ACCESS CHECK
    # ---------------------------------------------------------

    if request.user.role == User.Role.ADMIN:

        # Admin request is still waiting for approval.
        if request.user.admin_access_status == "pending":
            return render(
                request,
                "accounts/admin_access_pending.html",
            )

        # Admin access was explicitly denied.
        if request.user.admin_access_status == "denied":
            return render(
                request,
                "accounts/admin_access_denied.html",
            )

        # Only an approved admin can continue.
        if request.user.admin_access_status != "approved":
            return render(
                request,
                "accounts/admin_access_denied.html",
            )

    return render(
        request,
        "accounts/dashboard.html",
    )


def admin_access_pending_view(request):
    return render(
        request,
        "accounts/admin_access_pending.html",
    )

    