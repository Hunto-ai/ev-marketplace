from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class DealerProfile(models.Model):
    """Additional profile data for dealer accounts."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dealer_profile",
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    summary = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    phone_number = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=128, blank=True)
    province = models.CharField(max_length=64, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    hero_image = models.ImageField(upload_to="dealers/hero/", blank=True)
    logo = models.ImageField(upload_to="dealers/logo/", blank=True)
    is_featured = models.BooleanField(default=False)
    inventory_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "Dealer profile"
        verbose_name_plural = "Dealer profiles"

    def __str__(self) -> str:  # pragma: no cover - admin readability
        return self.name

    def save(self, *args: object, **kwargs: object) -> None:
        if not self.slug:
            base_slug = slugify(self.name) or slugify(self.user.email)
            candidate = base_slug
            index = 1
            while DealerProfile.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
                index += 1
                candidate = f"{base_slug}-{index}"
            self.slug = candidate
        super().save(*args, **kwargs)
