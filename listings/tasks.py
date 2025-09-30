from __future__ import annotations

import logging
import os
from io import BytesIO
from typing import Any

from celery import shared_task
from django.apps import apps
from django.core.files.base import ContentFile
from django.utils import timezone
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

DERIVATIVE_SPECS = {
    "thumbnail": {"size": (320, 320), "quality": 75},
    "display": {"size": (1280, 1280), "quality": 85},
}


@shared_task(name="listings.process_listing_photo")
def process_listing_photo(photo_id: int) -> str:
    """Generate optimized derivatives and metadata for uploaded listing photos."""

    Photo = apps.get_model("listings", "Photo")
    photo = Photo.objects.filter(pk=photo_id).first()
    if not photo:
        logger.warning("Skipping photo processing; photo %s no longer exists.", photo_id)
        return "missing"
    if not photo.image:
        logger.warning("Skipping photo %s; no original image attached.", photo.pk)
        return "missing"

    storage = photo.image.storage
    image_name = photo.image.name
    try:
        with storage.open(image_name, "rb") as original_file:
            original_bytes = original_file.read()
    except FileNotFoundError:
        logger.warning("Original image for photo %s not found at %s.", photo.pk, image_name)
        return "missing"
    except Exception as exc:  # pragma: no cover - storage/credential issues vary per env
        logger.exception("Error opening photo %s: %s", photo.pk, exc)
        return "error"

    try:
        image = Image.open(BytesIO(original_bytes))
        image = ImageOps.exif_transpose(image)
        image.load()
    except Exception as exc:
        logger.exception("Unable to decode photo %s: %s", photo.pk, exc)
        return "error"

    derivatives: dict[str, Any] = {}
    new_file_names: set[str] = set()
    existing_names = {
        str(data.get("name"))
        for data in (photo.derivatives or {}).values()
        if isinstance(data, dict) and data.get("name")
    }

    for key, spec in DERIVATIVE_SPECS.items():
        derivative_image = image.copy()
        derivative_image.thumbnail(spec["size"], Image.Resampling.LANCZOS)
        if derivative_image.mode not in ("RGB", "L"):
            derivative_image = derivative_image.convert("RGB")

        width, height = derivative_image.width, derivative_image.height

        buffer = BytesIO()
        derivative_image.save(
            buffer,
            format="JPEG",
            quality=spec.get("quality", 85),
            optimize=True,
            progressive=True,
        )
        derivative_image.close()
        buffer.seek(0)

        base, _ = os.path.splitext(image_name)
        derivative_name = f"{base}_{key}.jpg"
        try:
            storage.delete(derivative_name)
        except Exception:  # pragma: no cover - deleting stale file best effort
            pass
        saved_name = storage.save(derivative_name, ContentFile(buffer.getvalue()))
        new_file_names.add(saved_name)

        derivative_info: dict[str, Any] = {
            "name": saved_name,
            "width": width,
            "height": height,
        }
        try:
            derivative_info["url"] = storage.url(saved_name)
        except Exception:  # pragma: no cover - storages may need configuration
            pass
        derivatives[key] = derivative_info

    image_width = getattr(image, "width", None)
    image_height = getattr(image, "height", None)
    image.close()

    photo.original_width = image_width
    photo.original_height = image_height
    photo.processed_at = timezone.now()
    photo.derivatives = derivatives
    photo.save(
        update_fields=[
            "original_width",
            "original_height",
            "processed_at",
            "derivatives",
            "updated_at",
        ]
    )

    stale_files = existing_names - new_file_names
    for name in stale_files:
        try:
            storage.delete(name)
        except Exception:  # pragma: no cover - storage implementations vary
            logger.debug("Could not delete stale derivative %s for photo %s", name, photo.pk)

    logger.info("Processed photo %s into %d derivatives.", photo.pk, len(derivatives))
    return str(photo.pk)
