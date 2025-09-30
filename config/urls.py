"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
"""
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from dashboard.views import ListingCreateView
from guides.sitemaps import GuidesSitemap
from listings.sitemaps import ListingSitemap
from listings.views import ListingListView
from .views import robots_txt

sitemaps = {
    "listings": ListingSitemap,
    "guides": GuidesSitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("dealers/", include("dealers.urls")),
    path("guides/", include("guides.urls")),
    path("listings/", include("listings.urls")),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("robots.txt", robots_txt, name="robots"),
    path("sell/", ListingCreateView.as_view(), name="sell"),
    path("", ListingListView.as_view(), name="home"),
]
