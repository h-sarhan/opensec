from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from .models import Camera


class ManageCamerasView(ListView):
    model = Camera
    template_name = "manage_cameras.html"
    context_object_name = "cameras"


class CameraView(DetailView):
    model = Camera
    template_name = "camera.html"
    context_object_name = "camera"


class EditCameraView(UpdateView):
    model = Camera
    fields = (
        "name",
        "rtsp_url",
    )
    template_name = "edit_camera.html"
    context_object_name = "camera"


class DeleteCameraView(DeleteView):
    model = Camera
    template_name = "delete_camera.html"
    success_url = reverse_lazy("manage_cameras")
    context_object_name = "camera"


class AddCameraView(CreateView):
    pass
