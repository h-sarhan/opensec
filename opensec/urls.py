from django.urls import path

from .views import CameraManagerView

urlpatterns = [
    path("", CameraManagerView.as_view(), name="manage_cameras"),
]
