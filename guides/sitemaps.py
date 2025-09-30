from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .registry import Guide, get_guides


class GuidesSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return get_guides()

    def lastmod(self, obj: Guide):
        return obj.last_modified

    def location(self, obj: Guide) -> str:
        return reverse("guides:detail", args=[obj.slug])
