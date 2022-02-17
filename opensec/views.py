from django.views.generic import ListView

from .models import Camera


class CameraManagerView(ListView):
    model = Camera
    template_name = "manage_cameras.html"
    context_object_name = "cameras"
