from typing import List
import cv2 as cv
from django.conf import settings

from .camera import CameraSource
from .detection import DetectionSource
from .live_feed import LiveFeed
from opensec.models import Camera


class CameraManager:
    def __init__(self):
        self.cameras: List[Camera] = []
        self.sources: List[CameraSource] = []
        self.live_feeds: List[LiveFeed] = []

    def update_camera_list(self, camera_model: Camera):
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


camera_manager = CameraManager()
