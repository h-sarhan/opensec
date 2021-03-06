from django.urls import path

from .views import (
    AddCameraView,
    CameraView,
    DeleteCameraView,
    EditCameraView,
    ManageCamerasView,
    IntruderListView,
    DeleteIntruderView,
    IntruderView,
)

urlpatterns = [
    path("", ManageCamerasView.as_view(), name="manage_cameras"),
    path("<int:pk>/edit/", EditCameraView.as_view(), name="edit_camera"),
    path("<int:pk>/view/", CameraView.as_view(), name="view_camera"),
    path("<int:pk>/delete/", DeleteCameraView.as_view(), name="delete_camera"),
    path("add-cam/", AddCameraView.as_view(), name="add_camera"),
    path("intruders/", IntruderListView.as_view(), name="intruder_list"),
    path(
        "intruders/<int:pk>/delete",
        DeleteIntruderView.as_view(),
        name="delete_intruder",
    ),
    path(
        "intruders/<int:pk>/view",
        IntruderView.as_view(),
        name="view_intruder",
    ),
]
