from django import forms

from .models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "title",
            "description",
            "location",
            "event_date",
            "ticket_price",
            "max_tickets",
            "poster",
        ]

        widgets = {
            "event_date": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 6,
                }
            ),
        }

    def clean_ticket_price(self):
        price = self.cleaned_data["ticket_price"]

        if price < 0:
            raise forms.ValidationError(
                "Ticket price cannot be negative."
            )

        return price

    def clean_max_tickets(self):
        max_tickets = self.cleaned_data["max_tickets"]

        if max_tickets < 1:
            raise forms.ValidationError(
                "Maximum tickets must be at least 1."
            )

        return max_tickets

    def clean_poster(self):
        poster = self.cleaned_data.get("poster")

        if poster:
            max_size = 5 * 1024 * 1024

            if poster.size > max_size:
                raise forms.ValidationError(
                    "Poster image must be smaller than 5 MB."
                )

        return poster