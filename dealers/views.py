from __future__ import annotations

from typing import Any

from django.views.generic import DetailView, ListView

from listings.models import Listing

from .models import DealerProfile


class DealerListView(ListView):
    """Public directory of dealer profiles."""

    model = DealerProfile
    template_name = "dealers/list.html"
    context_object_name = "dealers"

    def get_queryset(self) -> Any:
        return DealerProfile.objects.order_by("name")


class DealerDetailView(DetailView):
    """Public profile page for a dealer including active inventory."""

    model = DealerProfile
    template_name = "dealers/detail.html"
    context_object_name = "dealer"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        dealer: DealerProfile = context["dealer"]
        listings = list(
            Listing.objects.active()
            .filter(dealer=dealer)
            .select_related("spec", "seller")
            .prefetch_related("photos")
            .order_by("-published_at", "-created_at")
        )
        context["listings"] = listings
        context["has_listings"] = bool(listings)
        return context
