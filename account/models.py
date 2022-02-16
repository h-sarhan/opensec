from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager


class OpenSecUser(AbstractBaseUser, PermissionsMixin):
    class Meta:
        verbose_name = "OpenSec User"
        verbose_name_plural = "OpenSec Users"

    username = models.CharField(verbose_name="Username", max_length=60, unique=True)
    email = models.EmailField(
        verbose_name="Email Address", name="email", unique=False, null=True, blank=True
    )
    is_staff = models.BooleanField(default=False)
    date_added = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    objects = UserManager()

    def __str__(self):
        return self.username
