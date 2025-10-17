from __future__ import annotations

import json
import logging
from pathlib import Path

from typing import Any

import boto3

from botocore.exceptions import BotoCoreError, NoCredentialsError

from django.conf import settings

from django.contrib import messages

from django.contrib.auth.mixins import LoginRequiredMixin

from django.http import HttpRequest, HttpResponse, HttpResponseForbidden, JsonResponse

from django.shortcuts import get_object_or_404, redirect, render

from django.urls import reverse, reverse_lazy

from django.utils import timezone

from django.utils.decorators import method_decorator

from django.views import View

from django.views.generic import TemplateView

from django.views.decorators.csrf import csrf_exempt

from accounts.models import User

from listings.forms import ListingForm, PhotoFormSet

from listings.models import Inquiry, Listing, ListingStatus

from listings.tasks import process_listing_photo

logger = logging.getLogger(__name__)

class SellerRequiredMixin(LoginRequiredMixin):

    """Ensure only seller/dealer/admin roles can access dashboard."""

    allowed_roles = {

        User.Role.SELLER,

        User.Role.DEALER,

        User.Role.ADMIN,

    }

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:

        if not request.user.is_authenticated:

            return self.handle_no_permission()

        if request.user.role not in self.allowed_roles:

            return HttpResponseForbidden("Seller access required")

        return super().dispatch(request, *args, **kwargs)


class SellerDashboardMixin(SellerRequiredMixin):
    def get_unread_inquiry_count(self) -> int:
        user = self.request.user
        if not user.is_authenticated:
            return 0
        return Inquiry.objects.filter(listing__seller=user, seller_notified_at__isnull=True).count()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.setdefault("inquiry_unread_count", self.get_unread_inquiry_count())
        return context


class DashboardIndexView(SellerDashboardMixin, TemplateView):

    template_name = "dashboard/listings/index.html"

    def get_queryset(self) -> Any:

        qs = Listing.objects.filter(seller=self.request.user).select_related("dealer")

        status = self.request.GET.get("status")

        if status:

            qs = qs.filter(status=status)

        return qs.order_by("-updated_at")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:

        ctx = super().get_context_data(**kwargs)

        ctx["listings"] = self.get_queryset()

        ctx["status_choices"] = ListingStatus.choices

        return ctx

    def render_to_response(self, context: dict[str, Any], **response_kwargs: Any) -> HttpResponse:

        if self.request.headers.get("HX-Request"):

            return render(self.request, "dashboard/listings/partials/list_table.html", context=context)

        return super().render_to_response(context, **response_kwargs)


class SellerNotificationsView(SellerDashboardMixin, TemplateView):
    template_name = "dashboard/notifications/index.html"
    page_size = 50

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self._unread_ids = list(
            Inquiry.objects.filter(listing__seller=request.user, seller_notified_at__isnull=True).values_list("id", flat=True)
        )
        response = super().get(request, *args, **kwargs)
        if self._unread_ids:
            now = timezone.now()
            Inquiry.objects.filter(pk__in=self._unread_ids).update(seller_notified_at=now, updated_at=now)
        return response

    def get_queryset(self) -> Any:
        return Inquiry.objects.filter(listing__seller=self.request.user).select_related("listing").order_by("-created_at")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        inquiries = list(self.get_queryset()[: self.page_size])
        context["inquiries"] = inquiries
        context["unread_ids"] = list(getattr(self, "_unread_ids", []))
        context["inquiry_unread_count"] = 0
        return context


class ListingFormMixin(SellerDashboardMixin):

    form_class = ListingForm

    template_name = "dashboard/listings/form.html"

    success_message = "Listing saved"

    def get_object(self) -> Listing | None:

        return None

    def get_form_kwargs(self) -> dict[str, Any]:

        kwargs = super().get_form_kwargs()

        instance = self.get_object()

        if instance is not None:

            kwargs["instance"] = instance

        return kwargs

    def get_photo_formset(self) -> PhotoFormSet:

        instance = self.get_object()

        if self.request.method in {"POST", "PUT"}:

            return PhotoFormSet(self.request.POST, self.request.FILES, instance=instance)

        return PhotoFormSet(instance=instance)

    def form_invalid(self, form: ListingForm, photos: PhotoFormSet) -> HttpResponse:

        return render(

            self.request,

            self.template_name,

            {

                "form": form,

                "photos": photos,

                "view": self,

            },

            status=400,

        )

    def form_valid(self, form: ListingForm, photos: PhotoFormSet) -> HttpResponse:

        listing = form.save(commit=False)

        listing.seller = self.request.user

        listing.save()

        photos.instance = listing

        photos.save()

        messages.success(self.request, self.success_message)

        return redirect(self.get_success_url(listing))

    def get_success_url(self, listing: Listing) -> str:

        return reverse("dashboard:edit", kwargs={"pk": listing.pk})

class ListingCreateView(ListingFormMixin, View):

    title = "Create listing"

    def get_object(self) -> Listing | None:  # type: ignore[override]

        return None

    def get(self, request: HttpRequest) -> HttpResponse:

        form = self.form_class()

        photos = self.get_photo_formset()

        return render(request, self.template_name, {"form": form, "photos": photos, "view": self})

    def post(self, request: HttpRequest) -> HttpResponse:

        form = self.form_class(request.POST)

        photos = self.get_photo_formset()

        if form.is_valid() and photos.is_valid():

            return self.form_valid(form, photos)

        return self.form_invalid(form, photos)

class ListingUpdateView(ListingFormMixin, View):

    title = "Edit listing"

    def get_object(self) -> Listing | None:  # type: ignore[override]

        return get_object_or_404(Listing, pk=self.kwargs["pk"], seller=self.request.user)

    def get(self, request: HttpRequest, pk: str) -> HttpResponse:

        listing = self.get_object()

        form = self.form_class(instance=listing)

        photos = self.get_photo_formset()

        return render(request, self.template_name, {"form": form, "photos": photos, "view": self})

    def post(self, request: HttpRequest, pk: str) -> HttpResponse:

        listing = self.get_object()

        form = self.form_class(request.POST, instance=listing)

        photos = PhotoFormSet(request.POST, request.FILES, instance=listing)

        if form.is_valid() and photos.is_valid():

            return self.form_valid(form, photos)

        return self.form_invalid(form, photos)

class ListingRowMixin(SellerRequiredMixin):

    template_name = "dashboard/listings/partials/listing_row.html"

    def get_listing(self) -> Listing:

        return get_object_or_404(Listing, pk=self.kwargs["pk"], seller=self.request.user)

    def render_partial(self, listing: Listing) -> HttpResponse:

        context = {"listing": listing}

        return render(self.request, self.template_name, context)

class ListingSubmitView(ListingRowMixin, View):

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:

        listing = self.get_listing()

        if listing.status not in {ListingStatus.DRAFT, ListingStatus.REJECTED}:

            return self.render_partial(listing)

        listing.status = ListingStatus.PENDING_REVIEW

        listing.published_at = None

        listing.approved_at = None

        listing.rejected_at = None

        listing.save(update_fields=["status", "published_at", "approved_at", "rejected_at", "updated_at"])

        messages.success(request, "Listing submitted for moderation")

        return self.render_partial(listing)

class ListingArchiveView(ListingRowMixin, View):

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:

        listing = self.get_listing()

        listing.status = ListingStatus.ARCHIVED

        listing.expires_at = timezone.now()

        listing.save(update_fields=["status", "expires_at", "updated_at"])

        messages.info(request, "Listing archived")

        return self.render_partial(listing)

class PhotoUploadURLView(SellerRequiredMixin, View):
    max_photos = 10
    max_upload_bytes = 10 * 1024 * 1024
    presign_expires_seconds = 300

    def post(self, request: HttpRequest, pk: str, *args: Any, **kwargs: Any) -> HttpResponse:
        listing = get_object_or_404(Listing, pk=pk, seller=request.user)
        current_photos = listing.photos.count()
        if current_photos >= self.max_photos:
            return JsonResponse({"error": "You already have the maximum number of photos."}, status=400)

        raw_filename = request.POST.get("filename")
        content_type = request.POST.get("content_type")
        if not raw_filename or not content_type:
            return JsonResponse({"error": "filename and content_type required"}, status=400)
        if not content_type.startswith("image/"):
            return JsonResponse({"error": "Only image uploads are allowed."}, status=400)

        filename = Path(raw_filename).name
        if not filename:
            return JsonResponse({"error": "Invalid filename provided."}, status=400)

        bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", "")
        if not bucket:
            return JsonResponse({"error": "Storage bucket not configured."}, status=503)

        photo_model = listing.photos.model
        photo_instance = photo_model(listing=listing)
        storage_key = photo_instance.image.field.generate_filename(photo_instance, filename)

        session_kwargs: dict[str, str] = {}
        access_key = getattr(settings, "AWS_ACCESS_KEY_ID", None)
        secret_key = getattr(settings, "AWS_SECRET_ACCESS_KEY", None)
        session_token = getattr(settings, "AWS_SESSION_TOKEN", None)
        region_name = getattr(settings, "AWS_DEFAULT_REGION", None)
        if access_key and secret_key:
            session_kwargs["aws_access_key_id"] = access_key
            session_kwargs["aws_secret_access_key"] = secret_key
        if session_token:
            session_kwargs["aws_session_token"] = session_token

        try:
            session = boto3.session.Session(**session_kwargs) if session_kwargs else boto3.session.Session()
            client = session.client("s3", region_name=region_name)
            presigned = client.generate_presigned_post(
                Bucket=bucket,
                Key=storage_key,
                Fields={"Content-Type": content_type},
                Conditions=[["content-length-range", 0, self.max_upload_bytes], {"Content-Type": content_type}],
                ExpiresIn=self.presign_expires_seconds,
            )
        except (NoCredentialsError, BotoCoreError, AttributeError, ValueError) as exc:
            return JsonResponse({"error": f"Unable to generate upload URL: {exc}"}, status=503)

        return JsonResponse({
            "upload": {
                "url": presigned["url"],
                "fields": presigned["fields"],
                "expires_in": self.presign_expires_seconds,
                "max_file_size": self.max_upload_bytes,
            },
            "photo": {
                "storage_key": storage_key,
                "bucket": bucket,
                "content_type": content_type,
                "remaining_slots": self.max_photos - current_photos,
            },
        })

@method_decorator(csrf_exempt, name="dispatch")

class PhotoCallbackView(SellerRequiredMixin, View):
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        listing = get_object_or_404(Listing, pk=payload.get("listing_id"), seller=request.user)
        image_key = payload.get("storage_key")
        if not image_key:
            return JsonResponse({"error": "storage_key missing"}, status=400)

        current_count = listing.photos.count()
        if current_count >= PhotoUploadURLView.max_photos:
            return JsonResponse({"error": "Photo limit reached for this listing."}, status=400)

        Photo = listing.photos.model  # type: ignore[attr-defined]
        photo, created = Photo.objects.get_or_create(
            listing=listing,
            image=image_key,
            defaults={"sort_order": current_count},
        )
        remaining_slots = max(PhotoUploadURLView.max_photos - (current_count + (1 if created else 0)), 0)

        try:
            image_url = photo.image.url
        except Exception:
            image_url = None

        try:
            process_listing_photo.delay(photo.pk)
        except Exception as exc:  # pragma: no cover - broker availability differs per env
            logger.warning("Unable to enqueue photo processing task", exc_info=exc)

        return JsonResponse({
            "photo_id": photo.pk,
            "image_url": image_url,
            "remaining_slots": remaining_slots,
            "created": created,
        })

