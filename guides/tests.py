from __future__ import annotations

from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape

from .registry import get_guides


class GuideViewTests(TestCase):
    def test_guides_list_renders(self) -> None:
        response = self.client.get(reverse("guides:list"))
        self.assertEqual(response.status_code, 200)
        for guide in get_guides():
            self.assertContains(response, escape(guide.title))
            self.assertContains(response, reverse("guides:detail", args=[guide.slug]))

    def test_guide_detail_renders_markdown(self) -> None:
        guide = get_guides()[0]
        response = self.client.get(reverse("guides:detail", args=[guide.slug]))
        self.assertEqual(response.status_code, 200)
        escaped_title = escape(guide.title)
        body = response.content.decode()
        self.assertIn(escaped_title, body)
        self.assertIn("<h1", body)

    def test_unknown_slug_returns_404(self) -> None:
        response = self.client.get(reverse("guides:detail", args=["does-not-exist"]))
        self.assertEqual(response.status_code, 404)
