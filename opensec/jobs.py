import threading
import time

from camera import CameraManager
from schedule import Scheduler

cam_manager = CameraManager()


async def startup_job():
    await cam_manager.get_cameras()
    cam_manager.connect_to_sources()
    cam_manager.update_snapshots()


def update_snapshots_job():
    cam_manager.update_snapshots()


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


def reconnect_cameras():
    pass
