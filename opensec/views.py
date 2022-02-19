from django.conf import settings
from django.urls import reverse
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from .forms import AddCameraForm, EditCameraForm
from .models import Camera


class ManageCamerasView(ListView):
    model = Camera
    template_name = "manage_cameras.html"
    context_object_name = "cameras"


class CameraView(DetailView):
    model = Camera
    template_name = "view_camera.html"
    context_object_name = "camera"


class EditCameraView(UpdateView):
    model = Camera
    form_class = EditCameraForm
    template_name = "edit_camera.html"
    context_object_name = "camera"

    def get_success_url(self):
        return reverse("manage_cameras")


class DeleteCameraView(DeleteView):
    model = Camera
    template_name = "delete_camera.html"
    context_object_name = "camera"

    def get_success_url(self):
        return reverse("manage_cameras")


class AddCameraView(CreateView):
    model = Camera
    form_class = AddCameraForm
    template_name = "add_camera.html"
    context_object_name = "camera"

    def get_success_url(self):
        return reverse("manage_cameras")


class AllCameraView(TemplateView):
    template_name = "view_all_cameras.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["live_feed"] = f"{settings.MEDIA_URL}stream/playlist.m3u8"
        return context
