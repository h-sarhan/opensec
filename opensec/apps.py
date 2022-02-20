import asyncio

from django.apps import AppConfig


class OpensecConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "opensec"

    def ready(self):

        from .jobs import run_jobs_in_background, startup_job

        loop = asyncio.get_event_loop()
        asyncio.run_coroutine_threadsafe(startup_job(), loop)
        run_jobs_in_background()
