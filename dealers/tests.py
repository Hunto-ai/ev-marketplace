from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from listings.models import Listing, ListingStatus

from .models import DealerProfile

User = get_user_model()


class DealerPublicViewsTests(TestCase):
    def setUp(self) -> None:
        self.dealer_user = User.objects.create_user(
            email="dealer@example.com",
            password="password123",
            role=User.Role.DEALER,
        )
        self.dealer = DealerProfile.objects.create(
            user=self.dealer_user,
            name="EV World",
            city="Vancouver",
            province="BC",
            summary="Certified pre-owned EV specialist.",
            website="https://dealer.example.com",
        )
        self.listing = Listing.objects.create(
            seller=self.dealer_user,
            dealer=self.dealer,
            title="2023 Hyundai Ioniq 6 Preferred",
            year=2023,
            make="Hyundai",
            model="Ioniq 6",
            price=58990,
            mileage_km=4000,
            province="BC",
            city="Vancouver",
            status=ListingStatus.APPROVED,
        )

    def test_dealer_list_view(self) -> None:
        response = self.client.get(reverse("dealers:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.dealer.name)

    def test_dealer_detail_view_shows_inventory(self) -> None:
        response = self.client.get(reverse("dealers:detail", args=[self.dealer.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.dealer.name)
        self.assertContains(response, self.listing.title)
        self.assertContains(response, reverse("listings:detail", args=[self.listing.slug]))
