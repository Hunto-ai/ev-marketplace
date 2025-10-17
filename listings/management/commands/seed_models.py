from __future__ import annotations

from decimal import Decimal
from typing import Any, Tuple

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from dealers.models import DealerProfile
from listings.models import (
    ChargePort,
    Drivetrain,
    Inquiry,
    InquiryDeliveryStatus,
    InquiryEvent,
    InquiryStatus,
    Listing,
    ListingStatus,
    ModelSpec,
    Province,
)

# Baseline EV trims used for demo data, QA tooling, and local sandboxing.
MODEL_SPECS: list[dict[str, object]] = [
    {
        "make": "Tesla",
        "model": "Model 3",
        "trim": "RWD",
        "year": 2024,
        "battery_capacity_kwh": Decimal("57.5"),
        "usable_battery_capacity_kwh": Decimal("57.5"),
        "range_km": 438,
        "drivetrain": Drivetrain.RWD,
        "dc_fast_charge_type": ChargePort.NACS,
        "heat_pump_standard": True,
        "onboard_charger_kw": Decimal("11.5"),
        "seating_capacity": 5,
    },
    {
        "make": "Tesla",
        "model": "Model 3",
        "trim": "Long Range AWD",
        "year": 2024,
        "battery_capacity_kwh": Decimal("75"),
        "usable_battery_capacity_kwh": Decimal("75"),
        "range_km": 576,
        "drivetrain": Drivetrain.AWD,
        "dc_fast_charge_type": ChargePort.NACS,
        "heat_pump_standard": True,
        "onboard_charger_kw": Decimal("11.5"),
        "seating_capacity": 5,
    },
    {
        "make": "Tesla",
        "model": "Model Y",
        "trim": "Long Range AWD",
        "year": 2024,
        "battery_capacity_kwh": Decimal("75"),
        "usable_battery_capacity_kwh": Decimal("75"),
        "range_km": 497,
        "drivetrain": Drivetrain.AWD,
        "dc_fast_charge_type": ChargePort.NACS,
        "heat_pump_standard": True,
        "onboard_charger_kw": Decimal("11.5"),
        "seating_capacity": 5,
    },
    {
        "make": "Tesla",
        "model": "Model Y",
        "trim": "Performance",
        "year": 2024,
        "battery_capacity_kwh": Decimal("75"),
        "usable_battery_capacity_kwh": Decimal("75"),
        "range_km": 459,
        "drivetrain": Drivetrain.AWD,
        "dc_fast_charge_type": ChargePort.NACS,
        "heat_pump_standard": True,
        "onboard_charger_kw": Decimal("11.5"),
        "seating_capacity": 5,
    },
    {
        "make": "Hyundai",
        "model": "Kona Electric",
        "trim": "Preferred",
        "year": 2024,
        "battery_capacity_kwh": Decimal("64"),
        "usable_battery_capacity_kwh": Decimal("64"),
        "range_km": 420,
        "drivetrain": Drivetrain.FWD,
        "dc_fast_charge_type": ChargePort.CCS,
        "heat_pump_standard": True,
        "onboard_charger_kw": Decimal("10.8"),
        "seating_capacity": 5,
    },
    {
        "make": "Hyundai",
        "model": "Ioniq 5",
        "trim": "Preferred AWD Long Range",
        "year": 2024,
        "battery_capacity_kwh": Decimal("77.4"),
        "usable_battery_capacity_kwh": Decimal("74"),
        "range_km": 407,
        "drivetrain": Drivetrain.AWD,
        "dc_fast_charge_type": ChargePort.CCS,
        "heat_pump_standard": True,
        "onboard_charger_kw": Decimal("10.9"),
        "seating_capacity": 5,
    },
    {
        "make": "Hyundai",
        "model": "Ioniq 6",
        "trim": "Preferred AWD Long Range",
        "year": 2024,
        "battery_capacity_kwh": Decimal("77.4"),
        "usable_battery_capacity_kwh": Decimal("74.0"),
        "range_km": 499,
        "drivetrain": Drivetrain.AWD,
        "dc_fast_charge_type": ChargePort.CCS,
        "heat_pump_standard": True,
        "onboard_charger_kw": Decimal("10.9"),
        "seating_capacity": 5,
    },
    {
        "make": "Kia",
        "model": "EV6",
        "trim": "Wind AWD",
        "year": 2024,
        "battery_capacity_kwh": Decimal("77.4"),
        "usable_battery_capacity_kwh": Decimal("74"),
        "range_km": 406,
        "drivetrain": Drivetrain.AWD,
        "dc_fast_charge_type": ChargePort.CCS,
        "heat_pump_standard": True,
        "onboard_charger_kw": Decimal("10.9"),
        "seating_capacity": 5,
    },
    {
        "make": "Kia",
        "model": "EV9",
        "trim": "Land AWD",
        "year": 2024,
        "battery_capacity_kwh": Decimal("99.8"),
        "usable_battery_capacity_kwh": Decimal("95"),
        "range_km": 451,
        "drivetrain": Drivetrain.AWD,
        "dc_fast_charge_type": ChargePort.CCS,
        "heat_pump_standard": True,
        "onboard_charger_kw": Decimal("10.9"),
        "seating_capacity": 7,
    },
    {
        "make": "Nissan",
        "model": "Leaf",
        "trim": "SV Plus",
        "year": 2024,
        "battery_capacity_kwh": Decimal("62"),
        "usable_battery_capacity_kwh": Decimal("60"),
        "range_km": 363,
        "drivetrain": Drivetrain.FWD,
        "dc_fast_charge_type": ChargePort.CHAdeMO,
        "heat_pump_standard": True,
        "onboard_charger_kw": Decimal("6.6"),
        "seating_capacity": 5,
    },
    {
        "make": "Chevrolet",
        "model": "Bolt EUV",
        "trim": "Premier",
        "year": 2023,
        "battery_capacity_kwh": Decimal("65"),
        "usable_battery_capacity_kwh": Decimal("65"),
        "range_km": 397,
        "drivetrain": Drivetrain.FWD,
        "dc_fast_charge_type": ChargePort.CCS,
        "heat_pump_standard": False,
        "onboard_charger_kw": Decimal("11.5"),
        "seating_capacity": 5,
    },
    {
        "make": "Volkswagen",
        "model": "ID.4",
        "trim": "Pro AWD",
        "year": 2024,
        "battery_capacity_kwh": Decimal("82"),
        "usable_battery_capacity_kwh": Decimal("77"),
        "range_km": 410,
        "drivetrain": Drivetrain.AWD,
        "dc_fast_charge_type": ChargePort.CCS,
        "heat_pump_standard": True,
        "onboard_charger_kw": Decimal("11.0"),
        "seating_capacity": 5,
    },
    {
        "make": "Ford",
        "model": "Mustang Mach-E",
        "trim": "Premium AWD ER",
        "year": 2024,
        "battery_capacity_kwh": Decimal("98.7"),
        "usable_battery_capacity_kwh": Decimal("91"),
        "range_km": 435,
        "drivetrain": Drivetrain.AWD,
        "dc_fast_charge_type": ChargePort.CCS,
        "heat_pump_standard": True,
        "onboard_charger_kw": Decimal("10.5"),
        "seating_capacity": 5,
    },
    {
        "make": "Polestar",
        "model": "2",
        "trim": "Long Range AWD",
        "year": 2024,
        "battery_capacity_kwh": Decimal("82"),
        "usable_battery_capacity_kwh": Decimal("79"),
        "range_km": 470,
        "drivetrain": Drivetrain.AWD,
        "dc_fast_charge_type": ChargePort.CCS,
        "heat_pump_standard": True,
        "onboard_charger_kw": Decimal("11.0"),
        "seating_capacity": 5,
    },
    {
        "make": "BMW",
        "model": "i4",
        "trim": "eDrive40",
        "year": 2024,
        "battery_capacity_kwh": Decimal("83.9"),
        "usable_battery_capacity_kwh": Decimal("81"),
        "range_km": 484,
        "drivetrain": Drivetrain.RWD,
        "dc_fast_charge_type": ChargePort.CCS,
        "heat_pump_standard": True,
        "onboard_charger_kw": Decimal("11.0"),
        "seating_capacity": 5,
    },
    {
        "make": "Mercedes-Benz",
        "model": "EQB",
        "trim": "350 4MATIC",
        "year": 2024,
        "battery_capacity_kwh": Decimal("70.5"),
        "usable_battery_capacity_kwh": Decimal("66.5"),
        "range_km": 365,
        "drivetrain": Drivetrain.AWD,
        "dc_fast_charge_type": ChargePort.CCS,
        "heat_pump_standard": True,
        "onboard_charger_kw": Decimal("11.0"),
        "seating_capacity": 7,
    },
    {
        "make": "Volvo",
        "model": "XC40 Recharge",
        "trim": "Twin",
        "year": 2024,
        "battery_capacity_kwh": Decimal("82"),
        "usable_battery_capacity_kwh": Decimal("79"),
        "range_km": 471,
        "drivetrain": Drivetrain.AWD,
        "dc_fast_charge_type": ChargePort.CCS,
        "heat_pump_standard": True,
        "onboard_charger_kw": Decimal("11.0"),
        "seating_capacity": 5,
    },
    {
        "make": "Audi",
        "model": "Q4 e-tron",
        "trim": "50 quattro",
        "year": 2024,
        "battery_capacity_kwh": Decimal("82"),
        "usable_battery_capacity_kwh": Decimal("77"),
        "range_km": 400,
        "drivetrain": Drivetrain.AWD,
        "dc_fast_charge_type": ChargePort.CCS,
        "heat_pump_standard": True,
        "onboard_charger_kw": Decimal("11.0"),
        "seating_capacity": 5,
    },
    {
        "make": "Rivian",
        "model": "R1T",
        "trim": "Adventure",
        "year": 2024,
        "battery_capacity_kwh": Decimal("135"),
        "usable_battery_capacity_kwh": Decimal("135"),
        "range_km": 505,
        "drivetrain": Drivetrain.AWD,
        "dc_fast_charge_type": ChargePort.CCS,
        "heat_pump_standard": True,
        "onboard_charger_kw": Decimal("11.5"),
        "seating_capacity": 5,
    },
    {
        "make": "Lucid",
        "model": "Air",
        "trim": "Pure AWD",
        "year": 2024,
        "battery_capacity_kwh": Decimal("92"),
        "usable_battery_capacity_kwh": Decimal("88"),
        "range_km": 660,
        "drivetrain": Drivetrain.AWD,
        "dc_fast_charge_type": ChargePort.CCS,
        "heat_pump_standard": True,
        "onboard_charger_kw": Decimal("19.2"),
        "seating_capacity": 5,
    },
    {
        "make": "Subaru",
        "model": "Solterra",
        "trim": "Touring",
        "year": 2024,
        "battery_capacity_kwh": Decimal("72.8"),
        "usable_battery_capacity_kwh": Decimal("64"),
        "range_km": 360,
        "drivetrain": Drivetrain.AWD,
        "dc_fast_charge_type": ChargePort.CCS,
        "heat_pump_standard": True,
        "onboard_charger_kw": Decimal("6.6"),
        "seating_capacity": 5,
    },
    {
        "make": "Toyota",
        "model": "bZ4X",
        "trim": "XLE AWD",
        "year": 2024,
        "battery_capacity_kwh": Decimal("72.8"),
        "usable_battery_capacity_kwh": Decimal("64"),
        "range_km": 357,
        "drivetrain": Drivetrain.AWD,
        "dc_fast_charge_type": ChargePort.CCS,
        "heat_pump_standard": False,
        "onboard_charger_kw": Decimal("6.6"),
        "seating_capacity": 5,
    },
]


DEALER_SEEDS: list[dict[str, Any]] = [
    {
        "user": {
            "email": "demo-dealer@evthing.test",
            "first_name": "Demo",
            "last_name": "Dealer",
            "role": "dealer",
            "phone_number": "+1-555-0101",
        },
        "profile": {
            "name": "Demo EV Hub",
            "summary": "Curated EV inventory for QA and demo flows.",
            "description": "Demo dealer seeded for UI smoke tests. Not a real storefront.",
            "phone_number": "+1-555-0101",
            "email": "demo-dealer@evthing.test",
            "website": "https://demo.evthing.test",
            "address_line1": "101 Demo Way",
            "city": "Vancouver",
            "province": Province.BC,
            "postal_code": "V6B 1A1",
            "inventory_notes": "Demo data only - remove before production launch.",
            "is_featured": True,
        },
        "listings": [
            {
                "slug": "demo-2024-tesla-model-3-rwd",
                "title": "[DEMO] 2024 Tesla Model 3 RWD",
                "year": 2024,
                "make": "Tesla",
                "model": "Model 3",
                "trim": "RWD",
                "price": Decimal("42990"),
                "mileage_km": 12800,
                "province": Province.BC,
                "city": "Vancouver",
                "description": "Demo listing for QA walkthroughs. Includes delivery metadata, moderation, and inquiry smoke coverage.",
            },
            {
                "slug": "demo-2024-hyundai-ioniq5-awd",
                "title": "[DEMO] 2024 Hyundai Ioniq 5 Preferred AWD",
                "year": 2024,
                "make": "Hyundai",
                "model": "Ioniq 5",
                "trim": "Preferred AWD Long Range",
                "price": Decimal("55990"),
                "mileage_km": 10450,
                "province": Province.BC,
                "city": "Vancouver",
                "description": "Seeded AWD Ioniq 5 for catalogue filter QA (AWD, heat pump, DC fast charge).",
            },
        ],
    },
    {
        "user": {
            "email": "demo-sunrise@evthing.test",
            "first_name": "Sunrise",
            "last_name": "Motors",
            "role": "dealer",
            "phone_number": "+1-555-0102",
        },
        "profile": {
            "name": "Sunrise EV Outlet (Demo)",
            "summary": "Western Canada EV specialists (demo data).",
            "description": "Demo listings representing a second dealer for catalogue/dealer detail smoke tests.",
            "phone_number": "+1-555-0102",
            "email": "demo-sunrise@evthing.test",
            "website": "https://sunrise-demo.evthing.test",
            "address_line1": "202 Demo Avenue",
            "city": "Calgary",
            "province": Province.AB,
            "postal_code": "T2P 2B7",
            "inventory_notes": "Demo data only - replace with production inventory feeds.",
            "is_featured": False,
        },
        "listings": [
            {
                "slug": "demo-2024-kia-ev9-land",
                "title": "[DEMO] 2024 Kia EV9 Land AWD",
                "year": 2024,
                "make": "Kia",
                "model": "EV9",
                "trim": "Land AWD",
                "price": Decimal("78990"),
                "mileage_km": 7600,
                "province": Province.AB,
                "city": "Calgary",
                "description": "Flagship three-row EV for dealer page smoke testing.",
            },
            {
                "slug": "demo-2024-vw-id4-pro-awd",
                "title": "[DEMO] 2024 Volkswagen ID.4 Pro AWD",
                "year": 2024,
                "make": "Volkswagen",
                "model": "ID.4",
                "trim": "Pro AWD",
                "price": Decimal("51990"),
                "mileage_km": 14600,
                "province": Province.AB,
                "city": "Calgary",
                "description": "Demo AWD crossover entry to exercise filter chips and dealer detail cards.",
            },
        ],
    },
]


INQUIRY_SEEDS: list[dict[str, Any]] = [
    {
        "listing_slug": "demo-2024-tesla-model-3-rwd",
        "name": "Ready Buyer",
        "email": "ready.buyer@example.com",
        "message": "Hi there! Can we schedule a virtual walk-through?",
        "status": InquiryStatus.NEW,
        "delivery_status": InquiryDeliveryStatus.PENDING,
        "metadata": {"source": "seed"},
        "events": [
            (InquiryEvent.EventType.CREATED, "Seeded inquiry (demo)", {"channel": "seed"}),
        ],
    },
    {
        "listing_slug": "demo-2024-hyundai-ioniq5-awd",
        "name": "Sent To Dealer",
        "email": "delivered.buyer@example.com",
        "message": "Loved the spec sheet - is pickup available this week?",
        "status": InquiryStatus.CONTACTED,
        "delivery_status": InquiryDeliveryStatus.SENT,
        "delivery_reference": "demo-message-id",
        "events": [
            (InquiryEvent.EventType.CREATED, "Seeded inquiry (demo)", {"channel": "seed"}),
            (InquiryEvent.EventType.EMAIL_SENT, "Delivered via demo SES", {"reference": "demo-message-id"}),
        ],
    },
    {
        "listing_slug": "demo-2024-kia-ev9-land",
        "name": "Delivery Failed",
        "email": "failed.delivery@example.com",
        "message": "Can you confirm third-row legroom?",
        "status": InquiryStatus.NEW,
        "delivery_status": InquiryDeliveryStatus.FAILED,
        "delivery_error": "SMTP sandbox rejection (demo)",
        "events": [
            (InquiryEvent.EventType.CREATED, "Seeded inquiry (demo)", {"channel": "seed"}),
            (InquiryEvent.EventType.EMAIL_FAILED, "Demo failure", {"reason": "sandbox"}),
        ],
    },
]





class Command(BaseCommand):
    help = "Seed ModelSpec data used across the marketplace (idempotent)."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing ModelSpec rows before seeding.",
        )

    def handle(self, *args: object, **options: object) -> None:
        verbosity = int(options.get("verbosity", 1))
        flush_existing = bool(options.get("flush"))

        with transaction.atomic():
            spec_created, spec_updated = self._seed_model_specs(flush_existing, verbosity)
            dealer_created, dealer_updated, listing_created, listing_updated, listing_lookup = self._seed_demo_inventory()
            inquiry_created, inquiry_updated = self._seed_demo_inquiries(listing_lookup)

        if verbosity:
            self.stdout.write(
                self.style.SUCCESS(
                    "Seeded ModelSpec data (%s created, %s updated)." % (spec_created, spec_updated)
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    "Seeded demo DealerProfile data (%s created, %s updated)." % (dealer_created, dealer_updated)
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    "Seeded demo Listings (%s created, %s updated)." % (listing_created, listing_updated)
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    "Seeded demo Inquiries (%s created, %s updated)." % (inquiry_created, inquiry_updated)
                )
            )

    def _seed_model_specs(self, flush_existing: bool, verbosity: int) -> Tuple[int, int]:
        if flush_existing:
            count, _ = ModelSpec.objects.all().delete()
            if verbosity:
                self.stdout.write(self.style.WARNING(f"Deleted {count} ModelSpec rows."))

        created = 0
        updated = 0
        for spec in MODEL_SPECS:
            lookup = {
                "make": spec["make"],
                "model": spec["model"],
                "trim": spec.get("trim", ""),
                "year": spec["year"],
            }
            defaults = {key: value for key, value in spec.items() if key not in lookup}
            _, was_created = ModelSpec.objects.update_or_create(defaults=defaults, **lookup)
            if was_created:
                created += 1
            else:
                updated += 1
        return created, updated

    def _seed_demo_inventory(self) -> Tuple[int, int, int, int, dict[str, Listing]]:
        user_model = get_user_model()
        role_enum = getattr(user_model, "Role", None)

        dealer_created = 0
        dealer_updated = 0
        listing_created = 0
        listing_updated = 0
        listing_lookup: dict[str, Listing] = {}

        for dealer_seed in DEALER_SEEDS:
            user_data = dealer_seed["user"].copy()
            role_value = user_data.pop("role", None)
            if role_enum and role_value:
                enum_value = getattr(role_enum, role_value.upper(), role_value)
                user_data["role"] = enum_value
            elif role_value:
                user_data["role"] = role_value

            email = user_data["email"]
            user_defaults = {key: value for key, value in user_data.items() if key != "email"}
            user, user_created = user_model.objects.update_or_create(email=email, defaults=user_defaults)
            if user_created:
                user.set_unusable_password()
                user.save(update_fields=["password"])

            profile_defaults = dealer_seed["profile"]
            dealer_profile, profile_created = DealerProfile.objects.update_or_create(
                user=user,
                defaults=profile_defaults,
            )
            if profile_created:
                dealer_created += 1
            else:
                dealer_updated += 1

            for listing_seed in dealer_seed["listings"]:
                spec = ModelSpec.objects.filter(
                    make=listing_seed["make"],
                    model=listing_seed["model"],
                    trim=listing_seed.get("trim", ""),
                    year=listing_seed["year"],
                ).first()

                defaults = {
                    "seller": user,
                    "dealer": dealer_profile,
                    "spec": spec,
                    "title": listing_seed["title"],
                    "description": listing_seed.get(
                        "description",
                        "Demo listing generated by seed_models for QA checkpoints.",
                    ),
                    "year": listing_seed["year"],
                    "make": listing_seed["make"],
                    "model": listing_seed["model"],
                    "trim": listing_seed.get("trim", ""),
                    "price": listing_seed["price"],
                    "mileage_km": listing_seed.get("mileage_km", 0),
                    "province": listing_seed["province"],
                    "city": listing_seed["city"],
                    "tags": listing_seed.get("tags", "demo,seed"),
                    "status": ListingStatus.APPROVED,
                    "has_heat_pump": bool(spec.heat_pump_standard) if spec else False,
                    "drivetrain": spec.drivetrain if spec and spec.drivetrain else listing_seed.get("drivetrain", ""),
                    "dc_fast_charge_type": spec.dc_fast_charge_type
                    if spec and spec.dc_fast_charge_type
                    else listing_seed.get("dc_fast_charge_type", ""),
                    "range_km": spec.range_km if spec and spec.range_km else listing_seed.get("range_km"),
                    "battery_capacity_kwh": spec.battery_capacity_kwh
                    if spec and spec.battery_capacity_kwh
                    else listing_seed.get("battery_capacity_kwh"),
                }

                listing_obj, created_listing = Listing.objects.update_or_create(
                    slug=listing_seed["slug"],
                    defaults=defaults,
                )
                listing_lookup[listing_obj.slug] = listing_obj
                if created_listing:
                    listing_created += 1
                else:
                    listing_updated += 1

        return dealer_created, dealer_updated, listing_created, listing_updated, listing_lookup

    def _seed_demo_inquiries(self, listing_lookup: dict[str, Listing]) -> Tuple[int, int]:
        created = 0
        updated = 0
        for seed in INQUIRY_SEEDS:
            listing = listing_lookup.get(seed["listing_slug"])
            if not listing:
                continue

            defaults = {
                "name": seed["name"],
                "message": seed["message"],
                "status": seed.get("status", InquiryStatus.NEW),
                "delivery_status": seed.get("delivery_status", InquiryDeliveryStatus.PENDING),
                "metadata": seed.get("metadata", {"source": "seed"}),
                "delivery_reference": seed.get("delivery_reference", ""),
                "delivery_error": seed.get("delivery_error", ""),
            }

            delivery_status = defaults["delivery_status"]
            now = timezone.now()
            if delivery_status == InquiryDeliveryStatus.SENT:
                defaults.update({
                    "delivered_at": seed.get("delivered_at", now),
                    "seller_notified_at": seed.get("seller_notified_at", now),
                    "last_attempted_at": seed.get("last_attempted_at", now),
                })
            elif delivery_status == InquiryDeliveryStatus.FAILED:
                defaults.update({
                    "delivered_at": None,
                    "seller_notified_at": None,
                    "last_attempted_at": seed.get("last_attempted_at", now),
                })
            else:
                defaults.update({
                    "delivered_at": None,
                    "seller_notified_at": None,
                    "last_attempted_at": None,
                })

            inquiry, was_created = Inquiry.objects.update_or_create(
                listing=listing,
                email=seed["email"],
                defaults=defaults,
            )
            if was_created:
                created += 1
            else:
                updated += 1

            for event_type, message, metadata in seed.get("events", []):
                InquiryEvent.objects.update_or_create(
                    inquiry=inquiry,
                    event_type=event_type,
                    defaults={"message": message, "metadata": metadata},
                )

        return created, updated
