from __future__ import annotations

from django import forms
from django.forms import inlineformset_factory

from .models import Inquiry, Listing, Photo, SavedSearch


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = [
            "title",
            "description",
            "year",
            "make",
            "model",
            "trim",
            "price",
            "mileage_km",
            "drivetrain",
            "dc_fast_charge_type",
            "range_km",
            "battery_capacity_kwh",
            "battery_warranty_years",
            "battery_warranty_km",
            "has_heat_pump",
            "province",
            "city",
            "spec",
            "tags",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "tags": forms.TextInput(attrs={"placeholder": "comma,separated,tags"}),
        }

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("spec"):
            # Suggest matching spec when possible, but optional for MVP.
            pass
        return cleaned



class InquiryForm(forms.ModelForm):
    class Meta:
        model = Inquiry
        fields = ["name", "email", "phone_number", "message"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 4, "placeholder": "Share details about your interest."}),
            "phone_number": forms.TextInput(attrs={"placeholder": "Optional"}),
        }

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) < 10:
            raise forms.ValidationError("Please provide a bit more detail in your message.")
        return message


PhotoFormSet = inlineformset_factory(
    Listing,
    Photo,
    fields=("image", "caption", "alt_text", "sort_order", "is_primary"),
    extra=3,
    can_delete=True,
    max_num=10,
)




class SavedSearchForm(forms.ModelForm):
    class Meta:
        model = SavedSearch
        fields = ["name", "querystring"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Optional label"}),
            "querystring": forms.HiddenInput(),
        }

    def clean_querystring(self) -> str:
        querystring = self.cleaned_data["querystring"].strip()
        if not querystring:
            raise forms.ValidationError("Nothing to save for this search.")
        return querystring



