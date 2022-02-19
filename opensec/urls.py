from django.urls import path

from .views import (
    AddCameraView,
    AllCameraView,
    CameraView,
    DeleteCameraView,
    EditCameraView,
    ManageCamerasView,
)

urlpatterns = [
    path("", ManageCamerasView.as_view(), name="manage_cameras"),
    path("<int:pk>/edit/", EditCameraView.as_view(), name="edit_camera"),
    path("<int:pk>/view/", CameraView.as_view(), name="view_camera"),
    path("view-all-cams/", AllCameraView.as_view(), name="view_all_cameras"),
    path("<int:pk>/delete/", DeleteCameraView.as_view(), name="delete_camera"),
    path("add-cam/", AddCameraView.as_view(), name="add_camera"),
]