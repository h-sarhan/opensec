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
    stream_link = models.CharField(
        "Link to camera stream", blank=True, null=True, max_length=500
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

    video = models.FilePathField(verbose_name="Video of intruder", blank=True)
    thumbnail = models.FilePathField(verbose_name="Intruder thumbnail", blank=True)

    camera = models.ForeignKey(
        Camera,
        verbose_name="Camera the intruder was detected with",
        on_delete=models.CASCADE,
    )

    def thumbnail_media_url(self):
        return f"/media/{self.thumbnail.split('media/')[-1]}"

    def video_media_url(self):
        return f"/media/{self.video.split('media/')[-1]}"

    def __str__(self):
        return f"{self.label} detected at {self.date_added}"
