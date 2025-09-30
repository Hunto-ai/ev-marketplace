from __future__ import annotations

import json
from typing import Any

from django.http import HttpRequest
from django.urls import reverse

from .models import Drivetrain, Listing

DRIVETRAIN_SCHEMA = {
    Drivetrain.FWD: "https://schema.org/FrontWheelDriveConfiguration",
    Drivetrain.RWD: "https://schema.org/RearWheelDriveConfiguration",
    Drivetrain.AWD: "https://schema.org/AllWheelDriveConfiguration",
}


def _collect_image_urls(listing: Listing, request: HttpRequest) -> list[str]:
    urls: list[str] = []
    for photo in listing.photos.all():
        try:
            url = request.build_absolute_uri(photo.image.url)
        except Exception:  # pragma: no cover - storage edge cases
            continue
        if url and url not in urls:
            urls.append(url)
    return urls


def _drive_configuration(drivetrain: str | None) -> str | None:
    if not drivetrain:
        return None
    return DRIVETRAIN_SCHEMA.get(drivetrain)


def build_vehicle_schema(listing: Listing, request: HttpRequest) -> dict[str, Any]:
    """Return schema.org metadata for a listing detail page."""

    detail_url = request.build_absolute_uri(
        reverse("listings:detail", args=[listing.slug])
    )
    schema: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "Vehicle",
        "name": (listing.title or f"{listing.year} {listing.make} {listing.model}").strip(),
        "url": detail_url,
        "fuelType": "Electric",
        "sku": str(listing.pk),
    }

    if listing.description:
        schema["description"] = listing.description

    images = _collect_image_urls(listing, request)
    if images:
        schema["image"] = images

    if listing.make:
        schema["brand"] = {"@type": "Brand", "name": listing.make}
    if listing.model:
        schema["model"] = listing.model
    if listing.trim:
        schema["vehicleConfiguration"] = listing.trim
    if listing.year:
        schema["vehicleModelDate"] = listing.year
    if listing.exterior_color:
        schema["color"] = listing.exterior_color
    if listing.vin:
        schema["vehicleIdentificationNumber"] = listing.vin

    drive_config = _drive_configuration(listing.drivetrain)
    if drive_config:
        schema["driveWheelConfiguration"] = drive_config

    if listing.mileage_km:
        schema["mileageFromOdometer"] = {
            "@type": "QuantitativeValue",
            "value": listing.mileage_km,
            "unitCode": "KMT",
        }
    if listing.range_km:
        schema["vehicleRange"] = {
            "@type": "QuantitativeValue",
            "value": listing.range_km,
            "unitCode": "KMT",
        }
    if listing.battery_capacity_kwh:
        schema["batteryCapacity"] = str(listing.battery_capacity_kwh)

    address: dict[str, Any] = {"@type": "PostalAddress", "addressCountry": "CA"}
    if listing.city:
        address["addressLocality"] = listing.city
    if listing.province:
        address["addressRegion"] = listing.get_province_display()
    if len(address) > 2:
        schema["address"] = address

    if listing.price:
        offer: dict[str, Any] = {
            "@type": "Offer",
            "price": str(listing.price),
            "priceCurrency": "CAD",
            "url": detail_url,
            "availability": "https://schema.org/InStock"
            if listing.is_published
            else "https://schema.org/PreOrder",
            "itemCondition": "https://schema.org/UsedCondition",
        }
        if listing.expires_at:
            offer["priceValidUntil"] = listing.expires_at.date().isoformat()
        schema["offers"] = offer

    seller_data: dict[str, Any] | None = None
    dealer = listing.dealer
    if dealer and dealer.name:
        seller_data = {"@type": "AutoDealer", "name": dealer.name}
        if dealer.website:
            seller_data["url"] = dealer.website
        seller_address: dict[str, Any] = {"@type": "PostalAddress"}
        if dealer.address_line1:
            street = dealer.address_line1
            if dealer.address_line2:
                street = f"{street}, {dealer.address_line2}"
            seller_address["streetAddress"] = street
        if dealer.city:
            seller_address["addressLocality"] = dealer.city
        if dealer.province:
            seller_address["addressRegion"] = dealer.province
        if dealer.postal_code:
            seller_address["postalCode"] = dealer.postal_code
        if seller_address:
            seller_address["addressCountry"] = "CA"
            seller_data["address"] = seller_address
    elif listing.city or listing.province:
        seller_data = {"@type": "Person", "name": "Private Seller"}
        location: dict[str, Any] = {"@type": "PostalAddress", "addressCountry": "CA"}
        if listing.city:
            location["addressLocality"] = listing.city
        if listing.province:
            location["addressRegion"] = listing.get_province_display()
        seller_data["address"] = location

    if seller_data:
        schema["seller"] = seller_data

    return schema


def dumps_vehicle_schema(listing: Listing, request: HttpRequest) -> str:
    """JSON encode the schema with Decimal-safe defaults."""

    schema = build_vehicle_schema(listing, request)
    return json.dumps(schema, separators=(",", ":"), default=str)
