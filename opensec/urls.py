from django.urls import path

from .views import CameraView, DeleteCameraView, EditCameraView, ManageCamerasView

urlpatterns = [
    path("", ManageCamerasView.as_view(), name="manage_cameras"),
    path("<int:pk>/edit/", EditCameraView.as_view(), name="edit_cam"),
    path("<int:pk>/view/", CameraView.as_view(), name="view_cam"),
    path("<int:pk>/delete/", DeleteCameraView.as_view(), name="delete_cam"),
]
