from __future__ import annotations

import logging
from decimal import Decimal
from http import HTTPStatus
from functools import cached_property
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.mail import send_mail
from django.db.models import Max, Min, Q
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from urllib.parse import parse_qs
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, ListView

from dealers.models import DealerProfile

from .captcha import get_field_name as get_captcha_field_name, get_provider as get_captcha_provider, get_site_key as get_captcha_site_key, verify_captcha
from .emails import send_inquiry_notification
from .forms import InquiryForm, SavedSearchForm
from .models import ChargePort, Drivetrain, InquiryDeliveryStatus, InquiryEvent, Listing, Province, SavedSearch
from .schema import dumps_vehicle_schema


logger = logging.getLogger(__name__)

def build_canonical_url(request: HttpRequest, path: str) -> str:
    base = getattr(settings, "SITE_BASE_URL", "").rstrip("/")
    if base:
        return f"{base}{path}"
    return request.build_absolute_uri(path)


class ListingListView(ListView):
    """Public catalogue of approved listings with lightweight filtering."""

    model = Listing
    template_name = "listings/list.html"
    context_object_name = "listings"
    paginate_by = 12

    def get_queryset(self) -> Any:
        qs = (
            Listing.objects.active()
            .select_related("dealer", "spec", "seller")
            .prefetch_related("photos")
        )

        filters = self.filters

        if filters["dealer"]:
            qs = qs.filter(dealer__slug=filters["dealer"])
        if filters["makes"]:
            qs = qs.filter(make__in=filters["makes"])
        if filters["provinces"]:
            qs = qs.filter(province__in=filters["provinces"])
        if filters["drivetrains"]:
            qs = qs.filter(drivetrain__in=filters["drivetrains"])
        if filters["charge_types"]:
            qs = qs.filter(dc_fast_charge_type__in=filters["charge_types"])
        if filters["year_min"]:
            qs = qs.filter(year__gte=filters["year_min"])
        if filters["year_max"]:
            qs = qs.filter(year__lte=filters["year_max"])
        if filters["price_min"]:
            qs = qs.filter(price__gte=filters["price_min"])
        if filters["price_max"]:
            qs = qs.filter(price__lte=filters["price_max"])

        search_query = filters["query"]
        if search_query:
            qs = qs.filter(
                Q(title__icontains=search_query)
                | Q(make__icontains=search_query)
                | Q(model__icontains=search_query)
                | Q(trim__icontains=search_query)
                | Q(city__icontains=search_query)
                | Q(province__icontains=search_query)
                | Q(tags__icontains=search_query)
            )

        return qs.order_by("-published_at", "-created_at")

    @cached_property
    def filters(self) -> dict[str, Any]:
        """Return normalized filter values from the query string."""

        request = self.request

        def as_int(value: str | None) -> int | None:
            if not value:
                return None
            try:
                return int(value)
            except (TypeError, ValueError):
                return None

        def as_decimal(value: str | None) -> Decimal | None:
            if not value:
                return None
            try:
                return Decimal(value)
            except (TypeError, ValueError):
                return None

        def as_list(name: str) -> list[str]:
            values = [value.strip() for value in request.GET.getlist(name) if value]
            if values:
                return values
            single = request.GET.get(name, "").strip()
            return [single] if single else []

        return {
            "query": request.GET.get("q", "").strip(),
            "dealer": request.GET.get("dealer", "").strip(),
            "makes": as_list("make"),
            "provinces": as_list("province"),
            "drivetrains": as_list("drivetrain"),
            "charge_types": as_list("charge_type"),
            "year_min": as_int(request.GET.get("year_min")),
            "year_max": as_int(request.GET.get("year_max")),
            "price_min": as_decimal(request.GET.get("price_min")),
            "price_max": as_decimal(request.GET.get("price_max")),
        }


    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        querystring = self.request.GET.urlencode()
        context.update(
            {
                "filters": self.filters,
                "filter_options": self.get_filter_options(),
                "querystring_without_page": self.get_querystring(exclude=("page",)),
                "querystring_without_dealer": self.get_querystring(exclude=("page", "dealer")),
                "current_querystring": querystring,
            }
        )
        dealer_slug = self.filters.get("dealer")
        if dealer_slug:
            context["selected_dealer"] = DealerProfile.objects.filter(slug=dealer_slug).first()
        if context.get("is_paginated"):
            context["pagination_links"] = self.build_pagination_links(context["page_obj"])
        context["canonical_url"] = build_canonical_url(self.request, reverse("listings:list"))
        feature_saved_searches = getattr(settings, "FEATURE_SAVED_SEARCHES", False)
        context["feature_saved_searches"] = feature_saved_searches
        if feature_saved_searches and self.request.user.is_authenticated:
            if querystring:
                context["save_search_form"] = SavedSearchForm(initial={"querystring": querystring})
            else:
                context["save_search_form"] = None
            context["saved_searches"] = list(
                SavedSearch.objects.filter(user=self.request.user).order_by("-created_at")[:5]
            )
        else:
            context["save_search_form"] = None
            context["saved_searches"] = []
        return context

    def get_querystring(self, *, exclude: tuple[str, ...] = ()) -> str:
        params = self.request.GET.copy()
        for key in exclude:
            params.pop(key, None)
        return params.urlencode()

    def build_pagination_links(self, page_obj) -> list[dict[str, Any]]:
        """Return a compact list of pages with ellipses for display controls."""

        total = page_obj.paginator.num_pages
        current = page_obj.number
        window = 2
        pages = {1, total, current}
        for offset in range(1, window + 1):
            pages.add(current - offset)
            pages.add(current + offset)

        ordered_pages = [number for number in sorted(pages) if 1 <= number <= total]
        links: list[dict[str, Any]] = []
        previous_number: int | None = None
        for number in ordered_pages:
            if previous_number is not None and number - previous_number > 1:
                links.append({"is_ellipsis": True})
            links.append({"number": number, "is_current": number == current})
            previous_number = number
        return links

    def get_filter_options(self) -> dict[str, list[tuple[str, str]] | list[str]]:
        """Collect options for select inputs."""

        qs = Listing.objects.active()
        makes = (
            qs.exclude(make="")
            .values_list("make", flat=True)
            .order_by("make")
            .distinct()
        )
        years = (
            qs.exclude(year__isnull=True)
            .values_list("year", flat=True)
            .order_by("-year")
            .distinct()
        )
        prices = qs.aggregate(min=Min("price"), max=Max("price"))
        return {
            "makes": list(makes),
            "provinces": Province.choices,
            "drivetrains": Drivetrain.choices,
            "charge_types": ChargePort.choices,
            "years": list(years),
            "prices": prices,
        }



class SavedSearchDeleteView(LoginRequiredMixin, View):
    """Delete a saved search owned by the authenticated user."""

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not getattr(settings, "FEATURE_SAVED_SEARCHES", False):
            raise Http404()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request: HttpRequest, pk: int, *args: Any, **kwargs: Any) -> HttpResponse:
        redirect_to = request.POST.get("next") or request.META.get("HTTP_REFERER") or reverse("listings:list")
        saved = get_object_or_404(SavedSearch, pk=pk, user=request.user)
        saved.delete()
        messages.success(request, "Removed the saved search.")
        return redirect(redirect_to)



class SavedSearchCreateView(LoginRequiredMixin, View):
    """Persist the current filter set for the authenticated user."""

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not getattr(settings, "FEATURE_SAVED_SEARCHES", False):
            raise Http404()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        form = SavedSearchForm(request.POST)
        redirect_to = request.POST.get("next") or request.META.get("HTTP_REFERER") or reverse("listings:list")
        if not form.is_valid():
            messages.error(request, "Unable to save search. Please provide a name or adjust your filters.")
            return redirect(redirect_to)

        querystring = form.cleaned_data["querystring"]
        params = parse_qs(querystring, keep_blank_values=False)
        normalized: dict[str, Any] = {}
        for key, values in params.items():
            cleaned = [value for value in values if value]
            if not cleaned:
                continue
            normalized[key] = cleaned if len(cleaned) > 1 else cleaned[0]

        name = form.cleaned_data["name"].strip()
        if not name:
            name = self._build_default_name(normalized)

        saved, created = SavedSearch.objects.get_or_create(
            user=request.user,
            querystring=querystring,
            defaults={"name": name, "query_params": normalized},
        )
        if not created:
            saved.name = name or saved.name
            saved.query_params = normalized
            saved.save(update_fields=["name", "query_params", "updated_at"])
            messages.info(request, "Updated your saved search.")
        else:
            messages.success(request, "Saved this search to your account.")

        return redirect(redirect_to)

    def _build_default_name(self, params: dict[str, Any]) -> str:
        if not params:
            return "All listings"
        key_labels = {
            "make": "Make",
            "province": "Province",
            "drivetrain": "Drivetrain",
            "charge_type": "Charge",
            "q": "Keyword",
        }
        pieces: list[str] = []
        for key, label in key_labels.items():
            value = params.get(key)
            if not value:
                continue
            if isinstance(value, list):
                joined = ", ".join(str(item) for item in value)
            else:
                joined = str(value)
            pieces.append(f"{label}: {joined}")
        return " | ".join(pieces) if pieces else "Custom search"



class ListingDetailView(DetailView):
    """Public listing detail page."""

    model = Listing
    template_name = "listings/detail.html"
    context_object_name = "listing"

    def get_queryset(self) -> Any:
        return Listing.objects.active().select_related("dealer", "spec", "seller").prefetch_related("photos")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        listing = context["listing"]
        context["breadcrumbs"] = [
            (reverse("listings:list"), "Listings"),
            (None, listing.title or str(listing)),
        ]
        initial: dict[str, str] = {}
        user = self.request.user
        if user.is_authenticated:
            full_name = user.get_full_name().strip() if hasattr(user, "get_full_name") else ""
            if full_name:
                initial["name"] = full_name
            if getattr(user, "email", None):
                initial.setdefault("name", user.email)
                initial["email"] = user.email
        context["inquiry_form"] = InquiryForm(initial=initial)
        context["vehicle_schema_json"] = dumps_vehicle_schema(listing, self.request)
        context["canonical_url"] = build_canonical_url(self.request, reverse("listings:detail", args=[listing.slug]))
        context["captcha_provider"] = get_captcha_provider()
        context["captcha_site_key"] = get_captcha_site_key()
        context["captcha_field_name"] = get_captcha_field_name()
        return context

class ListingInquiryView(View):
    """Handle public inquiries for a listing with HTMX support."""

    template_form = "listings/partials/inquiry_form.html"
    template_success = "listings/partials/inquiry_success.html"

    def post(self, request: HttpRequest, slug: str, *args: Any, **kwargs: Any) -> HttpResponse:
        listing = get_object_or_404(
            Listing.objects.active().select_related("seller", "dealer"),
            slug=slug,
        )
        form = InquiryForm(request.POST)
        remote_ip = self._get_client_ip(request)
        if self._is_rate_limited(listing, remote_ip):
            error_message = "Too many inquiries from your network. Please wait a minute and try again."
            form.add_error(None, error_message)
            if not request.headers.get("HX-Request"):
                messages.error(request, error_message)
            return self._render_form(request, listing, form, status=HTTPStatus.TOO_MANY_REQUESTS)

        if form.is_valid():
            captcha_token = self._extract_captcha_token(request)
            captcha_ok, captcha_error, captcha_payload = verify_captcha(captcha_token, remote_ip)
            if not captcha_ok:
                message_text = captcha_error or "Captcha verification failed. Please try again."
                form.add_error(None, message_text)
                if not request.headers.get("HX-Request"):
                    messages.error(request, message_text)
                return self._render_form(request, listing, form, status=HTTPStatus.UNPROCESSABLE_ENTITY)

            inquiry = form.save(commit=False)
            inquiry.listing = listing
            metadata = inquiry.metadata or {}
            captcha_metadata: dict[str, Any] = {"provider": get_captcha_provider(), "verified": captcha_ok}
            if captcha_payload:
                allowed_keys = {"action", "score", "hostname", "challenge_ts"}
                details = {key: captcha_payload.get(key) for key in allowed_keys if key in captcha_payload}
                if details:
                    captcha_metadata["details"] = details
            metadata.update(
                {
                    "source": "public_detail",
                    "remote_addr": remote_ip,
                    "user_agent": request.META.get("HTTP_USER_AGENT"),
                    "referer": request.META.get("HTTP_REFERER"),
                    "captcha": captcha_metadata,
                }
            )
            inquiry.metadata = metadata
            inquiry.save()
            self._increment_rate_limit(listing, remote_ip)

            InquiryEvent.objects.create(
                inquiry=inquiry,
                event_type=InquiryEvent.EventType.CREATED,
                message="Inquiry submitted from public listing detail page.",
                metadata={
                    "source": "public_detail",
                    "remote_addr": remote_ip,
                    "user_agent": request.META.get("HTTP_USER_AGENT"),
                    "captcha": captcha_metadata,
                },
            )

            send_success, delivery_data = send_inquiry_notification(inquiry)
            now_ts = timezone.now()
            inquiry.last_attempted_at = now_ts
            inquiry.delivery_reference = str(delivery_data.get("message_id") or delivery_data.get("backend") or "")
            update_fields = ["delivery_status", "delivery_reference", "delivery_error", "last_attempted_at", "updated_at"]
            if send_success:
                inquiry.delivery_status = InquiryDeliveryStatus.SENT
                inquiry.delivery_error = ""
                inquiry.delivered_at = now_ts
                update_fields.append("delivered_at")
                InquiryEvent.objects.create(
                    inquiry=inquiry,
                    event_type=InquiryEvent.EventType.EMAIL_SENT,
                    message="Inquiry email delivered to seller.",
                    metadata=delivery_data,
                )
            else:
                inquiry.delivery_status = InquiryDeliveryStatus.FAILED
                inquiry.delivery_error = str(delivery_data.get("error") or "Unable to deliver inquiry email.")
                InquiryEvent.objects.create(
                    inquiry=inquiry,
                    event_type=InquiryEvent.EventType.EMAIL_FAILED,
                    message="Inquiry email delivery failed.",
                    metadata=delivery_data,
                )
            inquiry.save(update_fields=update_fields)


            if request.headers.get("HX-Request"):
                return render(
                    request,
                    self.template_success,
                    {"listing": listing, "inquiry": inquiry},
                    status=HTTPStatus.CREATED,
                )

            messages.success(
                request,
                "Thanks! We'll pass your inquiry to the seller and they will reach out shortly.",
            )
            return redirect("listings:detail", slug=listing.slug)

        if not request.headers.get("HX-Request"):
            messages.error(request, "Please correct the errors below and try again.")
        status_code = HTTPStatus.UNPROCESSABLE_ENTITY if request.headers.get("HX-Request") else HTTPStatus.BAD_REQUEST
        return self._render_form(request, listing, form, status=status_code)

    def _render_form(self, request: HttpRequest, listing: Listing, form: InquiryForm, *, status: HTTPStatus) -> HttpResponse:
        context = {"listing": listing, "form": form}
        if request.headers.get("HX-Request"):
            return render(request, self.template_form, context, status=status)
        return render(request, "listings/detail.html", context, status=status)

    def _get_client_ip(self, request: HttpRequest) -> str | None:
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded_for:
            for part in forwarded_for.split(","):
                candidate = part.strip()
                if candidate:
                    return candidate
        return request.META.get("REMOTE_ADDR")

    def _rate_limit_key(self, listing: Listing, remote_ip: str | None) -> str | None:
        if not remote_ip:
            return None
        return f"inquiry-rate:{listing.pk}:{remote_ip}"

    def _is_rate_limited(self, listing: Listing, remote_ip: str | None) -> bool:
        limit = getattr(settings, "INQUIRY_RATE_LIMIT_PER_MINUTE", 0)
        try:
            limit_value = int(limit)
        except (TypeError, ValueError):
            limit_value = 0
        if limit_value <= 0:
            return False
        cache_key = self._rate_limit_key(listing, remote_ip)
        if not cache_key:
            return False
        attempts = cache.get(cache_key, 0) or 0
        try:
            attempts_int = int(attempts)
        except (TypeError, ValueError):
            attempts_int = 0
        return attempts_int >= limit_value

    def _increment_rate_limit(self, listing: Listing, remote_ip: str | None) -> None:
        cache_key = self._rate_limit_key(listing, remote_ip)
        if not cache_key:
            return
        try:
            current = int(cache.get(cache_key, 0) or 0)
        except (TypeError, ValueError):
            current = 0
        cache.set(cache_key, current + 1, timeout=60)

    def _extract_captcha_token(self, request: HttpRequest) -> str | None:
        field_name = get_captcha_field_name()
        tokens: list[str] = []
        if field_name:
            token = request.POST.get(field_name)
            if token:
                tokens.append(token)
        fallback = request.POST.get("captcha_token")
        if fallback:
            tokens.append(fallback)
        return tokens[0] if tokens else None




