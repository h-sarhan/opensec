from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import OpenSecUserCreationForm


class RegistrationView(CreateView):
    form_class = OpenSecUserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/register.html"
