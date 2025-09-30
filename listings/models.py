from __future__ import annotations

import uuid
from typing import Any, Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Province(models.TextChoices):
    AB = "AB", "Alberta"
    BC = "BC", "British Columbia"
    MB = "MB", "Manitoba"
    NB = "NB", "New Brunswick"
    NL = "NL", "Newfoundland and Labrador"
    NS = "NS", "Nova Scotia"
    NT = "NT", "Northwest Territories"
    NU = "NU", "Nunavut"
    ON = "ON", "Ontario"
    PE = "PE", "Prince Edward Island"
    QC = "QC", "Quebec"
    SK = "SK", "Saskatchewan"
    YT = "YT", "Yukon"


class Drivetrain(models.TextChoices):
    FWD = "FWD", "Front-wheel drive"
    RWD = "RWD", "Rear-wheel drive"
    AWD = "AWD", "All-wheel drive"


class ChargePort(models.TextChoices):
    CCS = "CCS", "CCS"
    NACS = "NACS", "NACS"
    CHAdeMO = "CHAdeMO", "CHAdeMO"
    TESLA = "TESLA", "Tesla Proprietary"
    UNKNOWN = "UNKNOWN", "Unknown"


class ListingStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PENDING_REVIEW = "pending", "Pending moderation"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    ARCHIVED = "archived", "Archived"


class InquiryStatus(models.TextChoices):
    NEW = "new", "New"
    CONTACTED = "contacted", "Contacted"
    CLOSED = "closed", "Closed"


class InquiryDeliveryStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"


class ListingQuerySet(models.QuerySet):
    def published(self) -> "ListingQuerySet":
        return self.filter(status=ListingStatus.APPROVED)

    def active(self) -> "ListingQuerySet":
        now = timezone.now()
        return self.filter(
            status=ListingStatus.APPROVED,
        ).filter(models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now))

    def pending(self) -> "ListingQuerySet":
        return self.filter(status=ListingStatus.PENDING_REVIEW)


class ModelSpec(models.Model):
    make = models.CharField(max_length=120)
    model = models.CharField(max_length=120)
    trim = models.CharField(max_length=120, blank=True)
    year = models.PositiveSmallIntegerField()
    battery_capacity_kwh = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    usable_battery_capacity_kwh = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    range_km = models.PositiveIntegerField(blank=True, null=True)
    drivetrain = models.CharField(max_length=10, choices=Drivetrain.choices, blank=True)
    dc_fast_charge_type = models.CharField(max_length=12, choices=ChargePort.choices, blank=True)
    heat_pump_standard = models.BooleanField(default=False)
    onboard_charger_kw = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    seating_capacity = models.PositiveSmallIntegerField(blank=True, null=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("make", "model", "trim", "year")
        unique_together = ("make", "model", "trim", "year")

    def __str__(self) -> str:  # pragma: no cover - admin readability
        return f"{self.year} {self.make} {self.model} {self.trim}".strip()

    def save(self, *args: object, **kwargs: object) -> None:
        if not self.slug:
            base_slug = slugify(f"{self.year}-{self.make}-{self.model}-{self.trim}")
            if not base_slug:
                base_slug = uuid.uuid4().hex[:12]
            candidate = base_slug
            index = 1
            while ModelSpec.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
                index += 1
                candidate = f"{base_slug}-{index}"
            self.slug = candidate
        super().save(*args, **kwargs)


class Listing(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="listings",
    )
    dealer = models.ForeignKey(
        "dealers.DealerProfile",
        on_delete=models.SET_NULL,
        related_name="listings",
        null=True,
        blank=True,
    )
    spec = models.ForeignKey(
        ModelSpec,
        on_delete=models.SET_NULL,
        related_name="listings",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True)
    year = models.PositiveSmallIntegerField()
    make = models.CharField(max_length=120)
    model = models.CharField(max_length=120)
    trim = models.CharField(max_length=120, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    mileage_km = models.PositiveIntegerField(default=0)
    exterior_color = models.CharField(max_length=120, blank=True)
    interior_color = models.CharField(max_length=120, blank=True)
    province = models.CharField(max_length=2, choices=Province.choices)
    city = models.CharField(max_length=120)
    drivetrain = models.CharField(max_length=10, choices=Drivetrain.choices, blank=True)
    dc_fast_charge_type = models.CharField(max_length=12, choices=ChargePort.choices, blank=True)
    range_km = models.PositiveIntegerField(blank=True, null=True)
    battery_capacity_kwh = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    battery_warranty_years = models.PositiveIntegerField(blank=True, null=True)
    battery_warranty_km = models.PositiveIntegerField(blank=True, null=True)
    has_heat_pump = models.BooleanField(default=False)
    vin = models.CharField(max_length=17, blank=True)
    status = models.CharField(max_length=20, choices=ListingStatus.choices, default=ListingStatus.DRAFT)
    approved_at = models.DateTimeField(blank=True, null=True)
    rejected_at = models.DateTimeField(blank=True, null=True)
    published_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    featured_until = models.DateTimeField(blank=True, null=True)
    is_promoted = models.BooleanField(default=False)
    tags = models.CharField(max_length=255, blank=True, help_text="Comma separated marketing tags")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ListingQuerySet.as_manager()

    class Meta:
        ordering = ("-published_at", "-created_at")
        indexes = [
            models.Index(fields=("status", "province", "city")),
            models.Index(fields=("make", "model", "year")),
            models.Index(fields=("-created_at",)),
        ]

    def __str__(self) -> str:  # pragma: no cover - admin readability
        return f"{self.year} {self.make} {self.model}"

    def clean(self) -> None:
        if self.status == ListingStatus.APPROVED and not self.published_at:
            self.published_at = timezone.now()
        if self.status != ListingStatus.APPROVED:
            self.is_promoted = False

    def save(self, *args: object, **kwargs: object) -> None:
        creating = self._state.adding
        if not self.dealer and hasattr(self.seller, "dealer_profile"):
            self.dealer = getattr(self.seller, "dealer_profile")
        if not self.slug:
            base_slug = slugify(self.title or f"{self.make}-{self.model}-{self.year}")
            if not base_slug:
                base_slug = uuid.uuid4().hex[:10]
            candidate = base_slug
            index = 1
            while Listing.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
                index += 1
                candidate = f"{base_slug}-{index}"
            self.slug = candidate
        if self.status == ListingStatus.APPROVED and not self.approved_at:
            self.approved_at = timezone.now()
        if self.status != ListingStatus.APPROVED:
            self.approved_at = None
        if self.status == ListingStatus.REJECTED and not self.rejected_at:
            self.rejected_at = timezone.now()
        if self.status != ListingStatus.REJECTED:
            self.rejected_at = None
        if self.status == ListingStatus.APPROVED and not self.published_at:
            self.published_at = timezone.now()
        if self.status != ListingStatus.APPROVED:
            self.published_at = None
        super().save(*args, **kwargs)
        if creating and self.photos.filter(is_primary=True).count() == 0:
            primary = self.photos.order_by("sort_order", "id").first()
            if primary:
                primary.is_primary = True
                primary.save(update_fields=["is_primary"])

    @property
    def is_published(self) -> bool:
        return self.status == ListingStatus.APPROVED

    @property
    def primary_photo(self) -> "Photo | None":
        photos = list(self.photos.all())
        for photo in photos:
            if photo.is_primary:
                return photo
        return photos[0] if photos else None

    def transition(self, new_status: str, *, moderator: settings.AUTH_USER_MODEL | None = None) -> None:
        if new_status not in ListingStatus.values:
            raise ValidationError("Invalid status transition")
        self.status = new_status
        if new_status == ListingStatus.APPROVED:
            self.approved_at = timezone.now()
            self.published_at = timezone.now()
            self.rejected_at = None
        elif new_status == ListingStatus.REJECTED:
            self.rejected_at = timezone.now()
            self.published_at = None
            self.approved_at = None
        elif new_status in {ListingStatus.DRAFT, ListingStatus.PENDING_REVIEW}:
            self.approved_at = None
            self.rejected_at = None
            self.published_at = None
        self.save()


class Photo(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="listings/photos/%Y/%m/")
    caption = models.CharField(max_length=255, blank=True)
    alt_text = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    original_width = models.PositiveIntegerField(blank=True, null=True)
    original_height = models.PositiveIntegerField(blank=True, null=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    derivatives = models.JSONField(blank=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "id")

    def __str__(self) -> str:  # pragma: no cover - admin readability
        return f"Photo for {self.listing} ({self.pk})"

    def _safe_storage_url(self, name: Optional[str]) -> Optional[str]:
        if not name:
            return None
        try:
            return self.image.storage.url(name)
        except Exception:  # pragma: no cover - storage backends may differ
            return None

    def _safe_image_url(self) -> Optional[str]:
        try:
            return self.image.url
        except Exception:  # pragma: no cover - storage configuration varies
            return None

    def get_derivative_info(self, key: str) -> Optional[dict[str, Any]]:
        data = self.derivatives or {}
        value = data.get(key)
        if not isinstance(value, dict):
            return None
        info: dict[str, Any] = dict(value)
        if not info.get("url"):
            storage_url = self._safe_storage_url(info.get("name"))
            if storage_url:
                info["url"] = storage_url
        return info if info else None

    def _derivative_url(self, key: str) -> Optional[str]:
        info = self.get_derivative_info(key)
        if info and info.get("url"):
            return str(info["url"])
        if info and info.get("name"):
            storage_url = self._safe_storage_url(info.get("name"))
            if storage_url:
                return storage_url
        return self._safe_image_url()

    @property
    def image_url(self) -> Optional[str]:
        return self._safe_image_url()

    @property
    def thumbnail_info(self) -> Optional[dict[str, Any]]:
        return self.get_derivative_info("thumbnail")

    @property
    def thumbnail_url(self) -> Optional[str]:
        return self._derivative_url("thumbnail")

    @property
    def display_info(self) -> Optional[dict[str, Any]]:
        return self.get_derivative_info("display")

    @property
    def display_url(self) -> Optional[str]:
        return self._derivative_url("display")

    def save(self, *args: object, **kwargs: object) -> None:
        super().save(*args, **kwargs)
        if self.is_primary:
            Photo.objects.filter(listing=self.listing).exclude(pk=self.pk).update(is_primary=False)
        elif not self.listing.photos.exclude(pk=self.pk).filter(is_primary=True).exists():
            # Ensure there is always a primary photo when photos exist.
            Photo.objects.filter(pk=self.pk).update(is_primary=True)


class Inquiry(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="inquiries")
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone_number = models.CharField(max_length=32, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=InquiryStatus.choices, default=InquiryStatus.NEW)
    delivery_status = models.CharField(
        max_length=20,
        choices=InquiryDeliveryStatus.choices,
        default=InquiryDeliveryStatus.PENDING,
    )
    delivery_reference = models.CharField(max_length=255, blank=True)
    delivery_error = models.TextField(blank=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    last_attempted_at = models.DateTimeField(blank=True, null=True)
    seller_notified_at = models.DateTimeField(blank=True, null=True)
    metadata = models.JSONField(blank=True, default=dict)
    internal_notes = models.TextField(blank=True)
    responded_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:  # pragma: no cover - admin readability
        return f"Inquiry for {self.listing} from {self.email}"

    def mark_contacted(self) -> None:
        self.status = InquiryStatus.CONTACTED
        self.responded_at = timezone.now()
        self.save(update_fields=["status", "responded_at"])

    def mark_closed(self) -> None:
        self.status = InquiryStatus.CLOSED
        self.save(update_fields=["status"])


    def mark_viewed(self) -> None:
        if not self.seller_notified_at:
            self.seller_notified_at = timezone.now()
            self.save(update_fields=["seller_notified_at", "updated_at"])



class InquiryEvent(models.Model):
    class EventType(models.TextChoices):
        CREATED = "created", "Created"
        RATE_LIMITED = "rate_limited", "Rate limited"
        EMAIL_SENT = "email_sent", "Email sent"
        EMAIL_FAILED = "email_failed", "Email failed"
        DASHBOARD_VIEWED = "dashboard_viewed", "Dashboard viewed"

    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=50, choices=EventType.choices)
    message = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(blank=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:  # pragma: no cover - admin readability
        return f"{self.get_event_type_display()} for {self.inquiry_id}"


class SavedSearch(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_searches",
    )
    name = models.CharField(max_length=255, blank=True)
    querystring = models.TextField()
    query_params = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        unique_together = ("user", "querystring")

    def __str__(self) -> str:  # pragma: no cover - admin readability
        return self.name or f"Search {self.pk}"

    def summary(self) -> str:
        params = self.query_params or {}
        pieces: list[str] = []
        for key, value in params.items():
            if value in (None, "", []):
                continue
            if isinstance(value, list):
                joined = ", ".join(str(item) for item in value)
            else:
                joined = str(value)
            pieces.append(f"{key}={joined}")
        return ", ".join(pieces) if pieces else "All listings"

