from django.contrib.auth.forms import UserChangeForm, UserCreationForm

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
