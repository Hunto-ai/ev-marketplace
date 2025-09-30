from django.urls import path

from . import views

app_name = "guides"

urlpatterns = [
    path("", views.GuideListView.as_view(), name="list"),
    path("<slug:slug>/", views.GuideDetailView.as_view(), name="detail"),
]
