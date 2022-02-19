from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import OpenSecRegistrationForm, OpenSecUserChangeForm
from .models import OpenSecUser


class OpenSecUserAdmin(UserAdmin):
    add_form = OpenSecRegistrationForm
    form = OpenSecUserChangeForm
    model = OpenSecUser
    list_display = ("username", "email", "is_staff")
    list_filter = ("username", "email", "is_staff")
    fieldsets = ((None, {"fields": ("username", "email", "password")}),)
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2", "is_staff"),
            },
        ),
    )
    search_fields = (
        "username",
        "email",
    )
    ordering = ("username",)


admin.site.register(OpenSecUser, OpenSecUserAdmin)
