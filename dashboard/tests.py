from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from listings.models import Inquiry, InquiryDeliveryStatus, Listing, ListingStatus

User = get_user_model()


class DashboardAccessTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.seller = User.objects.create_user(
            email="seller@example.com",
            password="password123",
            role=User.Role.SELLER,
        )
        self.login_url = reverse("account_login")

    def test_requires_authentication(self) -> None:
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.login_url, response.url)

    def test_requires_seller_role(self) -> None:
        buyer = User.objects.create_user(email="buyer@example.com", password="pass")
        self.client.login(email="buyer@example.com", password="pass")
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 403)

    def test_seller_can_access(self) -> None:
        self.client.login(email="seller@example.com", password="password123")
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 200)


class ListingCrudTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.seller = User.objects.create_user(
            email="seller@example.com",
            password="password123",
            role=User.Role.SELLER,
        )
        self.client.login(email="seller@example.com", password="password123")

    def _listing_form_payload(self, overrides: dict[str, str] | None = None) -> dict[str, str]:
        payload = {
            "title": "2022 Hyundai Kona Preferred",
            "description": "Well maintained EV.",
            "year": "2022",
            "make": "Hyundai",
            "model": "Kona",
            "trim": "Preferred",
            "price": "42000",
            "mileage_km": "15000",
            "drivetrain": "FWD",
            "dc_fast_charge_type": "CCS",
            "range_km": "420",
            "battery_capacity_kwh": "64",
            "battery_warranty_years": "8",
            "battery_warranty_km": "160000",
            "has_heat_pump": "on",
            "province": "BC",
            "city": "Vancouver",
            "tags": "kona,ev",
            "spec": "",
            # formset management
            "photos-TOTAL_FORMS": "0",
            "photos-INITIAL_FORMS": "0",
            "photos-MIN_NUM_FORMS": "0",
            "photos-MAX_NUM_FORMS": "10",
        }
        if overrides:
            payload.update(overrides)
        return payload

    def test_create_listing(self) -> None:
        response = self.client.post(reverse("dashboard:create"), data=self._listing_form_payload())
        self.assertEqual(response.status_code, 302)
        listing = Listing.objects.get()
        self.assertEqual(listing.seller, self.seller)
        self.assertEqual(listing.status, ListingStatus.DRAFT)

    def test_update_listing(self) -> None:
        listing = Listing.objects.create(
            seller=self.seller,
            title="Initial",
            year=2020,
            make="Nissan",
            model="Leaf",
            price=25000,
            mileage_km=30000,
            province="BC",
            city="Vancouver",
        )
        url = reverse("dashboard:edit", kwargs={"pk": listing.pk})
        payload = self._listing_form_payload({"title": "Updated title"})
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 302)
        listing.refresh_from_db()
        self.assertEqual(listing.title, "Updated title")

    def test_submit_listing_via_htmx(self) -> None:
        listing = Listing.objects.create(
            seller=self.seller,
            title="Draft listing",
            year=2021,
            make="Tesla",
            model="Model 3",
            price=50000,
            mileage_km=10000,
            province="BC",
            city="Vancouver",
        )
        url = reverse("dashboard:submit", kwargs={"pk": listing.pk})
        response = self.client.post(url, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        listing.refresh_from_db()
        self.assertEqual(listing.status, ListingStatus.PENDING_REVIEW)

    def test_archive_listing(self) -> None:
        listing = Listing.objects.create(
            seller=self.seller,
            title="Live listing",
            year=2021,
            make="Ford",
            model="Mustang Mach-E",
            price=60000,
            mileage_km=5000,
            province="BC",
            city="Vancouver",
            status=ListingStatus.APPROVED,
        )
        url = reverse("dashboard:archive", kwargs={"pk": listing.pk})
        response = self.client.post(url, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        listing.refresh_from_db()
        self.assertEqual(listing.status, ListingStatus.ARCHIVED)


class NotificationsViewTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.seller = User.objects.create_user(
            email="seller@example.com",
            password="password123",
            role=User.Role.SELLER,
        )
        self.client.login(email="seller@example.com", password="password123")
        self.listing = Listing.objects.create(
            seller=self.seller,
            title="Demo Listing",
            year=2023,
            make="Tesla",
            model="Model Y",
            price=60000,
            mileage_km=5000,
            province="BC",
            city="Vancouver",
            status=ListingStatus.APPROVED,
        )
        self.inquiry = Inquiry.objects.create(
            listing=self.listing,
            name="Buyer One",
            email="buyer@example.com",
            message="Is this still available?",
            delivery_status=InquiryDeliveryStatus.SENT,
            delivery_reference="msg-123",
        )

    def test_notifications_list_and_mark_read(self) -> None:
        self.assertIsNone(self.inquiry.seller_notified_at)
        response = self.client.get(reverse("dashboard:notifications"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Buyer One")
        self.assertIn(self.inquiry, list(response.context["inquiries"]))
        self.assertIn(self.inquiry.id, response.context["unread_ids"])
        self.assertEqual(response.context["inquiry_unread_count"], 0)
        self.inquiry.refresh_from_db()
        self.assertIsNotNone(self.inquiry.seller_notified_at)

    def test_notifications_subsequent_visit_retains_state(self) -> None:
        self.client.get(reverse("dashboard:notifications"))
        self.client.get(reverse("dashboard:notifications"))
        self.inquiry.refresh_from_db()
        self.assertIsNotNone(self.inquiry.seller_notified_at)
