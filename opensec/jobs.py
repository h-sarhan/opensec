import threading
import time

from django.db.models.signals import post_save
from django.dispatch import receiver
from schedule import Scheduler

import opensec.models
from .apps import camera_manager


def startup_job():
    print("UPDATING CAMERAS")
    print("CONNECTING TO SOURCES")
    camera_manager.setup_and_update_cameras()


def update_snapshots_job():
    print("Snapshot updated")
    camera_manager.update_snapshots()


# This allows the schedule module to run jobs in the background
# From: https://schedule.readthedocs.io/en/stable/background-execution.html
def run_continuously(self, interval=1):
    """
    Continuously run, while executing pending jobs at each elapsed
    time interval.
    """
    cease_continuous_run = threading.Event()

    class ScheduleThread(threading.Thread):
        @classmethod
        def run(cls):
            while not cease_continuous_run.is_set():
                self.run_pending()
                time.sleep(interval)

    continuous_thread = ScheduleThread()
    continuous_thread.setDaemon(True)
    continuous_thread.start()
    return cease_continuous_run


Scheduler.run_continuously = run_continuously


def run_jobs_in_background():
    scheduler = Scheduler()
    scheduler.every(10).seconds.do(update_snapshots_job)
    scheduler.run_continuously()


@receiver(post_save, sender=opensec.models.Camera)
def update_cameras(sender, instance, created, **kwargs):
    if camera_manager is not None:
        if created:
            print("ADDING NEW CAMERA")
            camera_manager.setup_and_update_cameras()
        else:
            camera_manager.update_source(instance)
