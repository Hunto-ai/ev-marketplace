from django.urls import path

from . import views

app_name = "listings"

urlpatterns = [
    path("save-search/", views.SavedSearchCreateView.as_view(), name="save_search"),
    path("saved-search/<int:pk>/delete/", views.SavedSearchDeleteView.as_view(), name="delete_saved_search"),
    path("", views.ListingListView.as_view(), name="list"),
    path("<slug:slug>/inquire/", views.ListingInquiryView.as_view(), name="inquire"),
    path("<slug:slug>/", views.ListingDetailView.as_view(), name="detail"),
]
