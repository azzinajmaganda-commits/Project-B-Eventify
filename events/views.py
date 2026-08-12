from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EventForm
from .models import Event


def organizer_required(request):
    return (
        request.user.is_authenticated
        and request.user.role == "organizer"
    )


def approved_admin_required(request):
    return (
        request.user.is_authenticated
        and request.user.role == "admin"
        and request.user.admin_access_status == "approved"
    )


def can_manage_event(request, event):
    """
    An event can be managed by:
    1. The organizer who created it.
    2. An approved administrator.
    """

    if not request.user.is_authenticated:
        return False

    if (
        request.user.role == "admin"
        and request.user.admin_access_status == "approved"
    ):
        return True

    if (
        request.user.role == "organizer"
        and event.created_by == request.user
    ):
        return True

    return False


@login_required
def event_list(request):
    """
    All logged-in users can see all events.
    """

    events = Event.objects.all().order_by("-created_at")

    return render(
        request,
        "events/event_list.html",
        {"events": events},
    )


@login_required
def event_create(request):
    """
    Only organizers can create events.
    """

    if not organizer_required(request):
        messages.error(
            request,
            "Only organizers can create events.",
        )
        return redirect("dashboard")

    if request.method == "POST":
        form = EventForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()

            messages.success(
                request,
                "Your event was created successfully.",
            )

            return redirect("event_list")

    else:
        form = EventForm()

    return render(
        request,
        "events/event_form.html",
        {
            "form": form,
            "page_title": "Create Event",
            "submit_label": "Create Event",
        },
    )


@login_required
def event_edit(request, pk):
    """
    Only the event owner or an approved admin
    can edit an event.
    """

    event = get_object_or_404(
        Event,
        pk=pk,
    )

    if not can_manage_event(request, event):
        messages.error(
            request,
            "You are not allowed to edit this event.",
        )
        return redirect("event_list")

    if request.method == "POST":
        form = EventForm(
            request.POST,
            request.FILES,
            instance=event,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "The event was updated successfully.",
            )

            return redirect("event_list")

    else:
        form = EventForm(instance=event)

    return render(
        request,
        "events/event_form.html",
        {
            "form": form,
            "event": event,
            "page_title": "Edit Event",
            "submit_label": "Save Changes",
        },
    )


@login_required
def event_delete(request, pk):
    """
    Only the event owner or an approved admin
    can delete an event.
    """

    event = get_object_or_404(
        Event,
        pk=pk,
    )

    if not can_manage_event(request, event):
        messages.error(
            request,
            "You are not allowed to delete this event.",
        )
        return redirect("event_list")

    if request.method == "POST":
        event.delete()

        messages.success(
            request,
            "The event was deleted successfully.",
        )

        return redirect("event_list")

    return render(
        request,
        "events/event_confirm_delete.html",
        {"event": event},
    )