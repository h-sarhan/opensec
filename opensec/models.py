from account.models import OpenSecUser
from django.db import models
from django.utils import timezone


class Camera(models.Model):
    name = models.CharField("Camera name", max_length=200, blank=False, null=False)
    rtsp_url = models.URLField("RTSP URL", null=False, blank=False, max_length=200)
    is_onvif = models.BooleanField("ONVIF compliant?", default=False)
    is_ptz = models.BooleanField("Has PTZ controls?", default=False)
    is_active = models.BooleanField("Is the camera currently active?", default=False)
    video_height = models.PositiveIntegerField(
        "Source video height", null=True, blank=True
    )
    video_width = models.PositiveIntegerField(
        "Source video width", null=True, blank=True
    )
    video_framerate = models.PositiveIntegerField(
        "Source video framerate", null=True, blank=True
    )
    date_added = models.DateTimeField("Camera addition date", default=timezone.now)

    user = models.ForeignKey(OpenSecUser, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Intruder(models.Model):

    date_added = models.DateTimeField("Intruder detection date", default=timezone.now)
    label = models.CharField("Auto-generated label", max_length=50, default="Unknown")

    # These will be file paths for now
    video_path = models.FilePathField("Video file path", null=True, blank=True)
    thumb_path = models.FilePathField("Thumbnail file path", null=True, blank=True)

    camera = models.ForeignKey(
        Camera,
        verbose_name="Camera the intruder was detected with",
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f"{self.label} detected at {self.date_added}"
