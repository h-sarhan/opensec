from __future__ import annotations
from threading import Thread

from typing import List

import cv2 as cv
from django.conf import settings
from opensec.models import Camera

from .camera import CameraSource
from .detection import DetectionSource, IntruderDetector
from .live_feed import LiveFeed, LiveFeedServer


class CameraManager:
    def __init__(self):
        self.cameras: List[Camera] = []
        self.sources: List[DetectionSource] = []
        self.live_feeds: List[LiveFeed] = []
        self.detector: IntruderDetector | None = None
        self.live_feed_server: LiveFeedServer = LiveFeedServer()

    def setup(self, camera_model: Camera):
        self.update_camera_list(camera_model)

        # Initially the cameras will be inactive
        for camera in self.cameras:
            camera.is_active = False
            camera.save()

        self.connect_to_sources()
        self.update_snapshots()
        self.setup_live_feeds()
        self.start_detection()

    def setup_live_feeds(self):
        for source, camera in zip(self.sources, self.cameras):
            if source is not None:
                feed = LiveFeed(source)
                stream_link = feed.start()
                self.live_feeds.append(feed)
                camera.stream_link = stream_link
                camera.save()
            else:
                self.live_feeds.append(None)
        self.live_feed_server.start_server()

    def start_detection(self):
        self.detector = IntruderDetector(
            self.sources,
            f"{settings.MEDIA_ROOT}/intruders",
            num_frames_to_record=100,
            display_frame=False,
        )
        Thread(target=self.detector.detect).start()

    def update_camera_list(self, camera_model: Camera):
        self.cameras = list(camera_model.objects.all())

    def connect_to_sources(self):
        for camera in self.cameras:
            if not camera.is_active:
                try:
                    camera_source = CameraSource(
                        camera.name, camera.rtsp_url, max_reset_attempts=3
                    )
                    source = DetectionSource(camera.name, camera_source)
                    source.start()
                    self.sources.append(source)
                    camera.is_active = True
                    camera.save()
                except RuntimeError:
                    print(f"Could not connect to camera {camera.name}")
                    self.sources.append(None)
                    continue

    def update_snapshots(self):
        for camera, source in zip(self.cameras, self.sources):
            if source is None:
                continue
            frame = source.read()
            if frame is not None:
                snapshot_path = f"{settings.MEDIA_ROOT}/camera_snaps/{source.name}.jpg"
                cv.imwrite(snapshot_path, frame)
                camera.snapshot = snapshot_path
                camera.save()


camera_manager = CameraManager()
