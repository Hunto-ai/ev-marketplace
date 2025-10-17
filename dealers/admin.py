from __future__ import annotations

from django.contrib import admin

from .models import DealerProfile


@admin.register(DealerProfile)
class DealerProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "province", "phone_number", "is_featured")
    list_editable = ("is_featured",)
    list_filter = ("province", "is_featured")
    search_fields = ("name", "user__email", "city", "province")
    readonly_fields = ("created_at", "updated_at")
    prepopulated_fields = {"slug": ("name",)}


__all__ = ["DealerProfileAdmin"]
