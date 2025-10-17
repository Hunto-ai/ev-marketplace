from __future__ import annotations

import os
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction
from listings.models import Listing, Photo
from django.core.files import File

class Command(BaseCommand):
    help = "Associate images with listings."

    def handle(self, *args: object, **options: object) -> None:
        verbosity = int(options.get("verbosity", 1))

        image_mapping = {
            "2023nissanleaf.jfif": {"make": "Nissan", "model": "Leaf", "year": 2023},
            "Hyundai-IONIQ_5-2024.jpg": {"make": "Hyundai", "model": "Ioniq 5", "year": 2024},
            "kiaev9.jpg": {"make": "Kia", "model": "EV9", "year": 2024},
            "tesla3model3.jpeg": {"make": "Tesla", "model": "Model 3", "year": 2024},
            "vwid4.jpeg": {"make": "Volkswagen", "model": "ID.4", "year": 2024},
        }

        images_dir = "images"
        created_count = 0
        skipped_count = 0

        with transaction.atomic():
            for image_name, listing_data in image_mapping.items():
                try:
                    listing = Listing.objects.get(
                        make=listing_data["make"],
                        model=listing_data["model"],
                        year=listing_data["year"],
                    )

                    image_path = os.path.join(images_dir, image_name)

                    # Mark the first photo as primary
                    is_primary = not listing.photos.exists()

                    with open(image_path, "rb") as f:
                        photo = Photo(listing=listing, is_primary=is_primary)
                        photo.image.save(image_name, File(f))
                        photo.save()
                        if verbosity > 0:
                            self.stdout.write(f"Image saved to: {photo.image.path}")
                        created_count += 1
                        if verbosity > 1:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"Associated {image_name} with listing {listing.id}"
                                )
                            )

                except Listing.DoesNotExist:
                    if verbosity > 1:
                        self.stdout.write(
                            self.style.WARNING(
                                f"No listing found for {image_name}, skipping."
                            )
                        )
                    skipped_count += 1
                    continue

        if verbosity:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully associated {created_count} images."
                )
            )
            if skipped_count:
                self.stdout.write(
                    self.style.WARNING(f"Skipped {skipped_count} images.")
                )
