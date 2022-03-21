from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from .forms import AddCameraForm, EditCameraForm
from .models import Camera, Intruder


class ManageCamerasView(LoginRequiredMixin, ListView):
    model = Camera
    template_name = "manage_cameras.html"
    context_object_name = "cameras"
    login_url = "account/login"


class IntruderListView(LoginRequiredMixin, ListView):
    model = Intruder
    template_name = "intruder_list.html"
    context_object_name = "intruders"
    login_url = "account/login"


class CameraView(LoginRequiredMixin, DetailView):
    model = Camera
    template_name = "view_camera.html"
    context_object_name = "camera"
    login_url = "account/login"


class EditCameraView(LoginRequiredMixin, UpdateView):
    model = Camera
    form_class = EditCameraForm
    template_name = "edit_camera.html"
    context_object_name = "camera"
    login_url = "account/login"

    def get_success_url(self):
        return reverse("manage_cameras")


class DeleteCameraView(LoginRequiredMixin, DeleteView):
    model = Camera
    template_name = "delete_camera.html"
    context_object_name = "camera"
    login_url = "account/login"

    def get_success_url(self):
        return reverse("manage_cameras")


class AddCameraView(LoginRequiredMixin, CreateView):
    model = Camera
    form_class = AddCameraForm
    template_name = "add_camera.html"
    context_object_name = "camera"
    login_url = "account/login"

    def get_success_url(self):
        return reverse("manage_cameras")
