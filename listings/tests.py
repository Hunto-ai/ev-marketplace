from decimal import Decimal
import json
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from dealers.models import DealerProfile
from guides.registry import get_guides

from listings.models import (
    Inquiry,
    InquiryDeliveryStatus,
    InquiryEvent,
    InquiryStatus,
    Listing,
    ListingStatus,
    ModelSpec,
    Photo,
    Province,
    ChargePort,
    Drivetrain,
    SavedSearch,
)
from listings.tasks import process_listing_photo
from listings.management.commands.seed_models import MODEL_SPECS


class SeedModelsCommandTests(TestCase):
    def test_seed_models_command_is_idempotent(self) -> None:
        call_command("seed_models", verbosity=0)
        initial_specs = ModelSpec.objects.count()
        initial_dealers = DealerProfile.objects.count()
        initial_listings = Listing.objects.count()
        initial_inquiries = Inquiry.objects.count()
        initial_events = InquiryEvent.objects.count()

        self.assertGreaterEqual(initial_specs, len(MODEL_SPECS))
        self.assertGreaterEqual(initial_dealers, 2)
        self.assertGreaterEqual(initial_listings, 4)
        self.assertGreaterEqual(initial_inquiries, 3)
        self.assertGreaterEqual(initial_events, 5)

        call_command("seed_models", verbosity=0)
        self.assertEqual(ModelSpec.objects.count(), initial_specs)
        self.assertEqual(DealerProfile.objects.count(), initial_dealers)
        self.assertEqual(Listing.objects.count(), initial_listings)
        self.assertEqual(Inquiry.objects.count(), initial_inquiries)
        self.assertEqual(InquiryEvent.objects.count(), initial_events)

        demo_listing = Listing.objects.get(slug="demo-2024-tesla-model-3-rwd")
        self.assertTrue(demo_listing.title.startswith("[DEMO]"))
        self.assertEqual(demo_listing.status, ListingStatus.APPROVED)
        self.assertIsNotNone(demo_listing.spec)
        self.assertEqual(demo_listing.dealer.name, "Demo EV Hub")
        self.assertEqual(demo_listing.inquiries.count(), 1)

        delivered = Inquiry.objects.get(email="delivered.buyer@example.com")
        self.assertEqual(delivered.delivery_status, InquiryDeliveryStatus.SENT)
        self.assertIsNotNone(delivered.delivered_at)
        self.assertIsNotNone(delivered.seller_notified_at)

        failed = Inquiry.objects.get(email="failed.delivery@example.com")
        self.assertEqual(failed.delivery_status, InquiryDeliveryStatus.FAILED)
        self.assertIn("sandbox", failed.delivery_error)


class ListingModelTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            email="seller@example.com",
            password="password123",
        )

    def test_listing_generates_slug_and_handles_status_transitions(self) -> None:
        listing = Listing.objects.create(
            seller=self.user,
            title="2022 Hyundai Kona Preferred",
            year=2022,
            make="Hyundai",
            model="Kona",
            trim="Preferred",
            price=42000,
            mileage_km=15000,
            province="BC",
            city="Vancouver",
            status=ListingStatus.PENDING_REVIEW,
        )

        self.assertTrue(listing.slug)
        self.assertIsNone(listing.approved_at)
        self.assertIsNone(listing.published_at)

        listing.transition(ListingStatus.APPROVED)
        listing.refresh_from_db()
        self.assertEqual(listing.status, ListingStatus.APPROVED)
        self.assertIsNotNone(listing.approved_at)
        self.assertIsNotNone(listing.published_at)

    def test_photo_primary_flags(self) -> None:
        listing = Listing.objects.create(
            seller=self.user,
            title="2021 Tesla Model 3 Long Range",
            year=2021,
            make="Tesla",
            model="Model 3",
            trim="Long Range",
            price=62000,
            mileage_km=8000,
            province="ON",
            city="Toronto",
        )

        photo1 = Photo.objects.create(listing=listing, image="photos/test1.jpg")
        photo2 = Photo.objects.create(listing=listing, image="photos/test2.jpg", is_primary=True)
        photo1.refresh_from_db()
        photo2.refresh_from_db()

        self.assertFalse(photo1.is_primary)
        self.assertTrue(photo2.is_primary)
        self.assertEqual(listing.photos.filter(is_primary=True).count(), 1)

    def test_inquiry_status_helpers(self) -> None:
        listing = Listing.objects.create(
            seller=self.user,
            title="2020 Nissan Leaf SV",
            year=2020,
            make="Nissan",
            model="Leaf",
            price=28000,
            mileage_km=30000,
            province="QC",
            city="Montreal",
        )

        inquiry = Inquiry.objects.create(
            listing=listing,
            name="Buyer",
            email="buyer@example.com",
            message="Is this still available?",
        )
        inquiry.mark_contacted()
        inquiry.refresh_from_db()
        self.assertEqual(inquiry.status, InquiryStatus.CONTACTED)
        self.assertIsNotNone(inquiry.responded_at)

        inquiry.mark_closed()
        inquiry.refresh_from_db()
        self.assertEqual(inquiry.status, InquiryStatus.CLOSED)

    def test_model_spec_slug_unique(self) -> None:
        spec = ModelSpec.objects.create(
            make="Ford",
            model="Mustang Mach-E",
            trim="Premium",
            year=2023,
        )
        self.assertTrue(spec.slug)

    def test_process_listing_photo_generates_derivatives(self) -> None:
        with TemporaryDirectory() as tmpdir, override_settings(MEDIA_ROOT=tmpdir):
            listing = Listing.objects.create(
                seller=self.user,
                title="2019 Chevrolet Bolt EV",
                year=2019,
                make="Chevrolet",
                model="Bolt EV",
                price=35000,
                province=Province.ON,
                city="Toronto",
            )

            image = Image.new("RGB", (1600, 900), color="blue")
            buffer = BytesIO()
            image.save(buffer, format="JPEG")
            buffer.seek(0)

            photo = Photo.objects.create(
                listing=listing,
                image=SimpleUploadedFile("test.jpg", buffer.getvalue(), content_type="image/jpeg"),
            )

            process_listing_photo(photo.pk)
            photo.refresh_from_db()

            self.assertIsNotNone(photo.processed_at)
            self.assertEqual(photo.original_width, 1600)
            self.assertEqual(photo.original_height, 900)
            self.assertTrue(photo.derivatives)
            self.assertTrue(photo.image_url.endswith('test.jpg'))
            thumbnail = photo.derivatives.get("thumbnail")
            display = photo.derivatives.get("display")
            self.assertIsNotNone(thumbnail)
            self.assertIsNotNone(display)
            self.assertLessEqual(thumbnail["width"], 320)
            self.assertLessEqual(display["width"], 1280)
            thumb_path = Path(tmpdir) / thumbnail["name"]
            display_path = Path(tmpdir) / display["name"]
            self.assertTrue(thumb_path.exists())
            self.assertTrue(display_path.exists())
            self.assertEqual(photo.thumbnail_url, thumbnail.get("url"))
            self.assertEqual(photo.display_url, display.get("url"))

            photo.derivatives = {}
            photo.save(update_fields=["derivatives"])
            photo.refresh_from_db()
            self.assertTrue(photo.thumbnail_url.endswith('test.jpg'))
            self.assertTrue(photo.display_url.endswith('test.jpg'))


class PublicListingViewsTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            email="seller@example.com",
            password="pass1234",
        )
        self.approved_listing = Listing.objects.create(
            seller=self.user,
            title="2024 Tesla Model 3 RWD",
            year=2024,
            make="Tesla",
            model="Model 3",
            price=Decimal("48990"),
            province=Province.BC,
            city="Vancouver",
            status=ListingStatus.APPROVED,
        )
        self.other_listing = Listing.objects.create(
            seller=self.user,
            title="2023 Hyundai Ioniq 5 AWD",
            year=2023,
            make="Hyundai",
            model="Ioniq 5",
            price=Decimal("55990"),
            province=Province.ON,
            city="Toronto",
            status=ListingStatus.APPROVED,
        )

    def test_public_list_view_returns_only_active_listings(self) -> None:
        response = self.client.get(reverse("listings:list"))
        self.assertEqual(response.status_code, 200)
        listings = response.context["listings"]
        self.assertIn(self.approved_listing, listings)
        self.assertIn(self.other_listing, listings)
        self.assertContains(response, "Tesla Model 3")

    def test_filtering_by_dealer_slug(self) -> None:
        user_model = get_user_model()
        dealer_user = user_model.objects.create_user(
            email="dealer@example.com",
            password="pass1234",
            role=user_model.Role.DEALER,
        )
        dealer = DealerProfile.objects.create(
            user=dealer_user,
            name="Dealer Hub",
            city="Toronto",
            province=Province.ON,
        )
        dealer_listing = Listing.objects.create(
            seller=dealer_user,
            dealer=dealer,
            title="2022 Nissan Leaf SV",
            year=2022,
            make="Nissan",
            model="Leaf",
            price=Decimal("32990"),
            province=Province.ON,
            city="Toronto",
            status=ListingStatus.APPROVED,
        )
        response = self.client.get(reverse("listings:list"), {"dealer": dealer.slug})
        listings = list(response.context["listings"])  # type: ignore[index]
        self.assertIn(dealer_listing, listings)
        self.assertNotIn(self.approved_listing, listings)

    def test_filtering_by_province(self) -> None:
        response = self.client.get(reverse("listings:list"), {"province": Province.BC})
        self.assertEqual(response.status_code, 200)
        listings = list(response.context["listings"])  # type: ignore[index]
        self.assertIn(self.approved_listing, listings)
        self.assertNotIn(self.other_listing, listings)

    def test_filtering_by_multiple_provinces(self) -> None:
        response = self.client.get(reverse("listings:list"), {"province": [Province.BC, Province.ON]})
        self.assertEqual(response.status_code, 200)
        listings = list(response.context["listings"])  # type: ignore[index]
        self.assertIn(self.approved_listing, listings)
        self.assertIn(self.other_listing, listings)

    def test_filtering_by_multiple_makes(self) -> None:
        response = self.client.get(reverse("listings:list"), {"make": ["Tesla", "Hyundai"]})
        self.assertEqual(response.status_code, 200)
        listings = list(response.context["listings"])  # type: ignore[index]
        self.assertIn(self.approved_listing, listings)
        self.assertIn(self.other_listing, listings)

    def test_filtering_by_multiple_drivetrains(self) -> None:
        self.approved_listing.drivetrain = Drivetrain.RWD
        self.approved_listing.save(update_fields=["drivetrain"])
        self.other_listing.drivetrain = Drivetrain.AWD
        self.other_listing.save(update_fields=["drivetrain"])
        response = self.client.get(reverse("listings:list"), {"drivetrain": [Drivetrain.AWD, Drivetrain.RWD]})
        self.assertEqual(response.status_code, 200)
        listings = list(response.context["listings"])  # type: ignore[index]
        self.assertIn(self.approved_listing, listings)
        self.assertIn(self.other_listing, listings)

    def test_filtering_by_multiple_charge_types(self) -> None:
        self.approved_listing.dc_fast_charge_type = ChargePort.CCS
        self.approved_listing.save(update_fields=["dc_fast_charge_type"])
        self.other_listing.dc_fast_charge_type = ChargePort.NACS
        self.other_listing.save(update_fields=["dc_fast_charge_type"])
        response = self.client.get(
            reverse("listings:list"),
            {"charge_type": [ChargePort.CCS, ChargePort.NACS]},
        )
        self.assertEqual(response.status_code, 200)
        listings = list(response.context["listings"])  # type: ignore[index]
        self.assertIn(self.approved_listing, listings)
        self.assertIn(self.other_listing, listings)

    def test_pagination_links_window(self) -> None:
        for idx in range(80):
            Listing.objects.create(
                seller=self.user,
                title=f"Extra Listing {idx}",
                year=2020,
                make="Brand",
                model=f"Model {idx}",
                price=Decimal("39990"),
                province=Province.BC if idx % 2 == 0 else Province.ON,
                city="Calgary",
                status=ListingStatus.APPROVED,
            )

        response = self.client.get(reverse("listings:list"), {"page": 2})
        self.assertEqual(response.status_code, 200)
        links = response.context["pagination_links"]
        numbers = [item["number"] for item in links if "number" in item]
        self.assertIn(1, numbers)
        self.assertIn(2, numbers)
        self.assertIn(response.context["page_obj"].paginator.num_pages, numbers)
        self.assertTrue(any(item.get("is_ellipsis") for item in links))

    @override_settings(FEATURE_SAVED_SEARCHES=True)
    def test_save_search_creation(self) -> None:
        self.client.login(email="seller@example.com", password="pass1234")
        response = self.client.post(
            reverse("listings:save_search"),
            {
                "name": "BC Deals",
                "querystring": "province=BC&make=Tesla",
                "next": reverse("listings:list"),
            },
        )
        self.assertRedirects(response, reverse("listings:list"), fetch_redirect_response=False)
        saved = SavedSearch.objects.get(user=self.user)
        self.assertEqual(saved.name, "BC Deals")
        self.assertEqual(saved.query_params["province"], "BC")

    @override_settings(FEATURE_SAVED_SEARCHES=True)
    def test_save_search_updates_existing(self) -> None:
        self.client.login(email="seller@example.com", password="pass1234")
        SavedSearch.objects.create(
            user=self.user,
            name="Old",
            querystring="province=BC",
            query_params={"province": "BC"},
        )
        response = self.client.post(
            reverse("listings:save_search"),
            {
                "name": "Updated",
                "querystring": "province=BC",
                "next": reverse("listings:list"),
            },
        )
        self.assertRedirects(response, reverse("listings:list"), fetch_redirect_response=False)
        saved = SavedSearch.objects.get(user=self.user)
        self.assertEqual(saved.name, "Updated")

    @override_settings(FEATURE_SAVED_SEARCHES=True)
    def test_delete_saved_search(self) -> None:
        self.client.login(email="seller@example.com", password="pass1234")
        saved = SavedSearch.objects.create(
            user=self.user,
            name="Commuters",
            querystring="province=ON",
            query_params={"province": "ON"},
        )
        response = self.client.post(
            reverse("listings:delete_saved_search", args=[saved.pk]),
            {"next": reverse("listings:list")},
        )
        self.assertRedirects(response, reverse("listings:list"), fetch_redirect_response=False)
        self.assertFalse(SavedSearch.objects.filter(pk=saved.pk).exists())

    def test_detail_view_renders(self) -> None:
        response = self.client.get(reverse("listings:detail", args=[self.approved_listing.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tesla Model 3")
        self.assertContains(response, "$48,990")

    def test_detail_view_includes_vehicle_schema(self) -> None:
        response = self.client.get(reverse("listings:detail", args=[self.approved_listing.slug]))
        schema_json = response.context["vehicle_schema_json"]
        data = json.loads(schema_json)
        self.assertEqual(data["@type"], "Vehicle")
        self.assertIn("offers", data)
        self.assertEqual(data["offers"]["price"], format(self.approved_listing.price, ".2f"))
        self.assertIn("address", data)
        self.assertEqual(data["address"]["addressRegion"], self.approved_listing.get_province_display())
        self.assertEqual(data.get("fuelType"), "Electric")

    def test_submit_inquiry_via_htmx(self) -> None:
        response = self.client.post(
            reverse("listings:inquire", args=[self.approved_listing.slug]),
            {
                "name": "Interested Buyer",
                "email": "buyer@example.com",
                "phone_number": "555-1234",
                "message": "I would like to schedule a test drive soon.",
            },
            HTTP_HX_REQUEST="true",
            REMOTE_ADDR="203.0.113.5",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Inquiry.objects.filter(listing=self.approved_listing).count(), 1)
        inquiry = Inquiry.objects.get(listing=self.approved_listing)
        event = inquiry.events.filter(event_type=InquiryEvent.EventType.CREATED).first()
        self.assertIsNotNone(event)
        if event:
            self.assertEqual(event.metadata.get("remote_addr"), "203.0.113.5")
        self.assertEqual(inquiry.delivery_status, InquiryDeliveryStatus.SENT)
        self.assertIsNotNone(inquiry.delivered_at)
        self.assertTrue(inquiry.events.filter(event_type=InquiryEvent.EventType.EMAIL_SENT).exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Tesla", mail.outbox[0].subject)

    def test_non_active_listings_hidden_publicly(self) -> None:
        pending = Listing.objects.create(
            seller=self.user,
            title="Awaiting approval",
            year=2022,
            make="Volkswagen",
            model="ID.4",
            price=Decimal("45990"),
            province=Province.AB,
            city="Calgary",
            status=ListingStatus.PENDING_REVIEW,
        )
        draft = Listing.objects.create(
            seller=self.user,
            title="Draft listing",
            year=2021,
            make="Chevrolet",
            model="Bolt",
            price=Decimal("32990"),
            province=Province.SK,
            city="Regina",
            status=ListingStatus.DRAFT,
        )
        response = self.client.get(reverse("listings:list"))
        listings = list(response.context["listings"])  # type: ignore[index]
        self.assertNotIn(pending, listings)
        self.assertNotIn(draft, listings)
        detail_response = self.client.get(reverse("listings:detail", args=[pending.slug]))
        self.assertEqual(detail_response.status_code, 404)

    @override_settings(INQUIRY_RATE_LIMIT_PER_MINUTE=1)
    def test_inquiry_rate_limit_per_listing_ip(self) -> None:
        payload = {
            "name": "Rate Limited Buyer",
            "email": "buyer@example.com",
            "phone_number": "555-9999",
            "message": "Checking availability.",
        }
        first = self.client.post(
            reverse("listings:inquire", args=[self.approved_listing.slug]),
            payload,
            HTTP_HX_REQUEST="true",
            REMOTE_ADDR="198.51.100.10",
        )
        self.assertEqual(first.status_code, 201)
        second = self.client.post(
            reverse("listings:inquire", args=[self.approved_listing.slug]),
            payload,
            HTTP_HX_REQUEST="true",
            REMOTE_ADDR="198.51.100.10",
        )
        self.assertEqual(second.status_code, 429)
        self.assertEqual(Inquiry.objects.filter(listing=self.approved_listing).count(), 1)
        inquiry = Inquiry.objects.get(listing=self.approved_listing)
        self.assertEqual(inquiry.delivery_status, InquiryDeliveryStatus.SENT)

    def test_inquiry_captcha_failure_blocks_submission(self) -> None:
        with mock.patch("listings.views.verify_captcha", return_value=(False, "Captcha failed", {})):
            response = self.client.post(
                reverse("listings:inquire", args=[self.approved_listing.slug]),
                {
                    "name": "Captcha Test",
                    "email": "buyer@example.com",
                    "phone_number": "555-0000",
                    "message": "Testing captcha.",
                },
                HTTP_HX_REQUEST="true",
                REMOTE_ADDR="198.51.100.20",
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(Inquiry.objects.filter(listing=self.approved_listing).count(), 0)
        self.assertEqual(InquiryEvent.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)
        self.assertIn("Captcha failed", response.content.decode())

    @mock.patch("listings.views.send_inquiry_notification", return_value=(False, {"error": "SES failure"}))
    def test_inquiry_email_failure_updates_status(self, mock_send) -> None:
        response = self.client.post(
            reverse("listings:inquire", args=[self.approved_listing.slug]),
            {
                "name": "Interested Buyer",
                "email": "buyer@example.com",
                "phone_number": "555-0000",
                "message": "Checking email delivery failure handling.",
            },
            HTTP_HX_REQUEST="true",
            REMOTE_ADDR="198.51.100.30",
        )
        self.assertEqual(response.status_code, 201)
        inquiry = Inquiry.objects.get(listing=self.approved_listing)
        self.assertEqual(inquiry.delivery_status, InquiryDeliveryStatus.FAILED)
        self.assertIn("SES failure", inquiry.delivery_error)
        self.assertTrue(inquiry.events.filter(event_type=InquiryEvent.EventType.EMAIL_FAILED).exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_sitemap_includes_active_listings_and_guides(self) -> None:
        response = self.client.get(reverse("sitemap"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn(self.approved_listing.slug, content)
        guide = get_guides()[0]
        self.assertIn(guide.slug, content)

    def test_robots_txt_reports_sitemap(self) -> None:
        response = self.client.get(reverse("robots"))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn("Sitemap:", body)
        self.assertIn("sitemap.xml", body)

    def test_search_query_filters_results(self) -> None:
        response = self.client.get(reverse("listings:list"), {"q": "toronto"})
        listings = list(response.context["listings"])  # type: ignore[index]
        self.assertIn(self.other_listing, listings)
        self.assertNotIn(self.approved_listing, listings)





