from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class UserModelTests(TestCase):
    def test_create_user_uses_email_as_username(self) -> None:
        user = User.objects.create_user(email="buyer@example.com", password="secret123")
        self.assertEqual(user.email, "buyer@example.com")
        self.assertTrue(user.check_password("secret123"))
        self.assertTrue(user.is_buyer)
        self.assertTrue(user.has_usable_password())

    def test_create_superuser_flags_set(self) -> None:
        admin = User.objects.create_superuser(email="admin@example.com", password="adminpass", role=User.Role.ADMIN)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertEqual(admin.role, User.Role.ADMIN)

    def test_role_helpers(self) -> None:
        seller = User.objects.create_user(email="seller@example.com", password="sellerpass", role=User.Role.SELLER)
        dealer = User.objects.create_user(email="dealer@example.com", password="dealerpass", role=User.Role.DEALER)
        admin = User.objects.create_user(email="mod@example.com", password="modpass", role=User.Role.ADMIN)

        self.assertTrue(seller.is_seller)
        self.assertTrue(dealer.is_dealer)
        self.assertTrue(admin.is_admin)
