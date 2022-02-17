from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("account/", include("account.urls")),
    path("account/", include("django.contrib.auth.urls")),
    path(
        "",
        TemplateView.as_view(template_name="manage_cameras.html"),
        name="manage_cameras",
    ),
]
