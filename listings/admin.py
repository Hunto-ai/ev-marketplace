from __future__ import annotations

from django.contrib import admin

from .models import Inquiry, InquiryEvent, Listing, ModelSpec, Photo


class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 1
    fields = ("image", "caption", "alt_text", "sort_order", "is_primary")
    ordering = ("sort_order",)


@admin.register(ModelSpec)
class ModelSpecAdmin(admin.ModelAdmin):
    list_display = ("make", "model", "trim", "year", "range_km", "heat_pump_standard")
    list_filter = ("make", "year", "heat_pump_standard")
    search_fields = ("make", "model", "trim")
    prepopulated_fields = {"slug": ("make", "model", "trim", "year")}


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "seller",
        "status",
        "province",
        "price",
        "published_at",
    )
    list_filter = ("status", "province", "is_promoted", "has_heat_pump", "drivetrain")
    search_fields = ("title", "slug", "seller__email", "make", "model", "vin")
    readonly_fields = (
        "created_at",
        "updated_at",
        "approved_at",
        "rejected_at",
        "published_at",
    )
    inlines = (PhotoInline,)
    autocomplete_fields = ("seller", "dealer", "spec")
    list_editable = ("status",)
    fieldsets = (
        (None, {"fields": ("seller", "dealer", "spec", "title", "slug", "description")}),
        ("Vehicle", {
            "fields": (
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
                "vin",
                "tags",
            )
        }),
        ("Location", {"fields": ("province", "city")}),
        ("Status", {"fields": ("status", "is_promoted", "featured_until", "expires_at", "approved_at", "rejected_at", "published_at")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ("listing", "sort_order", "is_primary")
    list_editable = ("sort_order", "is_primary")
    search_fields = ("listing__title", "listing__seller__email")


class InquiryEventInline(admin.TabularInline):
    model = InquiryEvent
    extra = 0
    readonly_fields = ("event_type", "message", "metadata", "created_at")
    can_delete = False
    ordering = ("-created_at",)



@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ("listing", "email", "status", "delivery_status", "created_at", "responded_at")
    list_filter = ("status", "delivery_status", "created_at")
    search_fields = ("email", "name", "listing__title")
    readonly_fields = ("created_at", "updated_at", "responded_at", "delivery_status", "delivery_reference", "delivery_error", "delivered_at", "last_attempted_at", "seller_notified_at")
    inlines = (InquiryEventInline,)
    fieldsets = (
        (None, {"fields": ("listing", "name", "email", "phone_number", "message")}),
        ("Status", {"fields": ("status", "delivery_status", "delivery_reference", "delivery_error", "delivered_at", "last_attempted_at", "seller_notified_at", "responded_at")}),
        ("Metadata", {"fields": ("metadata", "internal_notes")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

__all__ = [
    "ModelSpecAdmin",
    "ListingAdmin",
    "PhotoAdmin",
    "InquiryAdmin",
]
