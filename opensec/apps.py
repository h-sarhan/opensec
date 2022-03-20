import os

from django.apps import AppConfig
import camera

camera_manager = camera.CameraManager()


class OpensecConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "opensec"

    def ready(self):

        if os.environ.get("RUN_MAIN"):
            from opensec.models import Camera, Intruder
            from .jobs import run_jobs_in_background, startup_job
            from django.conf import settings

            camera_manager.camera_model = Camera
            camera_manager.intruder_model = Intruder
            camera_manager.django_settings = settings

            startup_job()
            run_jobs_in_background()
