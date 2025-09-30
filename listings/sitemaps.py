from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Listing


class ListingSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Listing.objects.active()

    def lastmod(self, obj: Listing):
        return obj.updated_at or obj.published_at

    def location(self, obj: Listing) -> str:
        return reverse("listings:detail", args=[obj.slug])
