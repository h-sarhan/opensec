from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import OpenSecLoginForm, OpenSecRegistrationForm


class OpenSecRegistrationView(CreateView):
    form_class = OpenSecRegistrationForm
    success_url = reverse_lazy("login")
    template_name = "registration/register.html"


class OpenSecLoginView(LoginView):
    form_class = OpenSecLoginForm
    success_url = reverse_lazy("manage_cameras")
    template_name = "registration/login.html"
