from django.contrib.auth.forms import (
    AuthenticationForm,
    UserChangeForm,
    UserCreationForm,
)

from .models import OpenSecUser


class OpenSecRegistrationForm(UserCreationForm):
    class Meta:
        model = OpenSecUser
        fields = (
            "username",
            "email",
        )

    def __init__(self, *args, **kwargs):
        super(OpenSecRegistrationForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "input"

        self.fields["username"].widget.attrs["placeholder"] = "Username"
        self.fields["email"].widget.attrs["placeholder"] = "name@domain.com"
        self.fields["password1"].widget.attrs["placeholder"] = "Password"
        self.fields["password2"].widget.attrs["placeholder"] = "Confirm Password"


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
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "input"

        self.fields["username"].widget.attrs["placeholder"] = "Username"
        self.fields["password"].widget.attrs["placeholder"] = "Password"
