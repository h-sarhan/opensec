from django.urls import path

from .views import OpenSecLoginView, OpenSecRegistrationView

urlpatterns = [
    path("register/", OpenSecRegistrationView.as_view(), name="register"),
    path("login/", OpenSecLoginView.as_view(), name="login"),
]
