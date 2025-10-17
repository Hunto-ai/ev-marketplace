from django.urls import path

from . import views

app_name = "dealers"

urlpatterns = [
    path("", views.DealerListView.as_view(), name="list"),
    path("<slug:slug>/", views.DealerDetailView.as_view(), name="detail"),
]
