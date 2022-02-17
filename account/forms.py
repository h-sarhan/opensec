from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserChangeForm,
    UserCreationForm,
)

from .models import OpenSecUser


class OpenSecUserCreationForm(UserCreationForm):
    class Meta:
        model = OpenSecUser
        fields = (
            "username",
            "email",
        )


class OpenSecUserChangeForm(UserChangeForm):
    class Meta:
        model = OpenSecUser
        fields = (
            "username",
            "email",
        )


class OpenSecLoginForm(AuthenticationForm):
    class Meta:
        model = OpenSecUser
        fields = (
            "username",
            "password",
        )

    def __init__(self, *args, **kwargs):
        super(OpenSecLoginForm, self).__init__(*args, **kwargs)
        # for visible in self.visible_fields():
        #     visible.field.widget.attrs["class"] = "input"
        #     visible.field.widget.attrs["placeholder"] = "Username"
        self.fields["username"].widget.attrs["class"] = "input"
        self.fields["password"].widget.attrs["class"] = "input"

        self.fields["username"].widget.attrs["placeholder"] = "Username"
        self.fields["password"].widget.attrs["placeholder"] = "Password"
