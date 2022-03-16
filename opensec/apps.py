import os

from django.apps import AppConfig


class OpensecConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "opensec"

    def ready(self):

        if os.environ.get("RUN_MAIN"):
            from opensec.models import Camera

            from .jobs import run_jobs_in_background, startup_job

            startup_job(Camera)
            run_jobs_in_background()
