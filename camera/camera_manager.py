import cv2 as cv
from asgiref.sync import sync_to_async
from django.conf import settings

from .camera import CameraSource
from .live_feed import LiveFeed


class CameraManager:
    def __init__(self):
        self.cameras = []
        self.sources = []
        self.feed = LiveFeed()

    @sync_to_async
    def update_camera_list(self, camera_model):
        self.cameras = list(camera_model.objects.all())

    def connect_to_sources(self):
        for camera in self.cameras:
            try:
                source = CameraSource(camera.name, camera.rtsp_url).start()
                self.sources.append(source)
            except RuntimeError:
                print(f"Could not connect to camera {camera.name}")
                self.sources.append(None)
                continue

    def update_snapshots(self):
        for camera, source in zip(self.cameras, self.sources):
            if source is None:
                continue
            frame = source.read()
            snapshot_path = f"{settings.MEDIA_ROOT}/camera_snaps/{source.name}.jpg"
            cv.imwrite(snapshot_path, frame)
            camera.snapshot = snapshot_path
            camera.save()

    def get_stream_app(self):
        return self.feed.stream_app

    def swap_feed_source(self, new_source):
        self.feed.source = new_source


camera_manager = CameraManager()
