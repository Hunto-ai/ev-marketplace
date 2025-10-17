from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardIndexView.as_view(), name="index"),
    path("notifications/", views.SellerNotificationsView.as_view(), name="notifications"),
    path("sell/", views.ListingCreateView.as_view(), name="create"),
    path("listings/create/", views.ListingCreateView.as_view(), name="create"),
    path("listings/<uuid:pk>/edit/", views.ListingUpdateView.as_view(), name="edit"),
    path("listings/<uuid:pk>/submit/", views.ListingSubmitView.as_view(), name="submit"),
    path("listings/<uuid:pk>/archive/", views.ListingArchiveView.as_view(), name="archive"),
    path("listings/<uuid:pk>/photos/upload-url/", views.PhotoUploadURLView.as_view(), name="photo-upload"),
    path("listings/photos/callback/", views.PhotoCallbackView.as_view(), name="photo-callback"),
]
