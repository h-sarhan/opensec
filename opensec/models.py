from django.db import models
from django.utils import timezone


class Camera(models.Model):
    name = models.CharField("Camera name", max_length=200, blank=False, null=False)
    rtsp_url = models.CharField(
        "RTSP URL",
        null=False,
        blank=False,
        max_length=200,
    )
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
    snapshot = models.ImageField(
        "Camera snapshot", upload_to="camera_snaps", blank=True
    )

    def __str__(self):
        return self.name


class Intruder(models.Model):

    date_added = models.DateTimeField("Intruder detection date", default=timezone.now)
    label = models.CharField("Auto-generated label", max_length=50, default="Unknown")

    video = models.FileField(
        "Video of intruder", upload_to="intuder_videos", blank=True
    )
    thumbnail = models.ImageField(
        "Intruder thumbnail", upload_to="intuder_thumbs", blank=True
    )

    camera = models.ForeignKey(
        Camera,
        verbose_name="Camera the intruder was detected with",
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f"{self.label} detected at {self.date_added}"
