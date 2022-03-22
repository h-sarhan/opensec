from __future__ import annotations

from threading import Thread

import cv2 as cv

from .camera import CameraSource
from .detection import DetectionSource, IntruderDetector
from .live_feed import LiveFeed


class CameraManager:
    def __init__(self):
        self.detector: IntruderDetector | None = None
        self.cameras = {}
        self.camera_model = None
        self.intruder_model = None
        self.django_settings = None

    def setup_and_update_cameras(self):
        self.update_camera_list()

        self.connect_to_sources()
        self.update_snapshots()
        self.update_live_feeds()
        self.start_detection()

    def update_live_feeds(self):
        for camera_pk in self.cameras:
            camera, source, _ = self.cameras[camera_pk]
            if source is not None:
                feed = LiveFeed(source)
                stream_link = feed.start()
                self.cameras[camera_pk][2] = feed
                print(f"SETTING STREAM LINK TO {stream_link}")
                camera.stream_link = stream_link
                camera.save()

    def start_detection(self):
        if self.detector is not None:
            self.detector.stop_detection()
        self.detector = IntruderDetector(
            [camera[1] for camera in self.cameras.values() if camera[1] is not None],
            f"{self.django_settings.MEDIA_ROOT}/intruders",
            self.camera_model,
            self.intruder_model,
            num_frames_to_record=100,
            display_frame=False,
        )
        Thread(target=self.detector.detect, args=(30,)).start()

    def update_camera_list(self):
        new_camera_list = list(self.camera_model.objects.all())
        for camera in new_camera_list:
            if camera.pk not in self.cameras:
                self.cameras[camera.pk] = [camera, None, None]

                # Initially the cameras will be inactive
                camera.is_active = False
                camera.save()

        for _, (cam, source, feed) in self.cameras.items():
            if cam not in new_camera_list:
                source.stop()
                feed.stop()

    def connect_to_sources(self):
        for camera_pk in self.cameras:
            camera, old_source, _ = self.cameras[camera_pk]
            if not camera.is_active or old_source is None:
                try:
                    camera_source = CameraSource(
                        camera.name, camera.rtsp_url, max_reset_attempts=3
                    )
                    source = DetectionSource(camera.name, camera_source)
                    source.start()
                    self.cameras[camera_pk][1] = source
                    camera.is_active = True
                    camera.save()
                except RuntimeError:
                    print(f"Could not connect to camera {camera.name}")
                except ValueError:
                    print("Source must be a valid RTSP URL")

    def update_snapshots(self):
        for camera_pk in self.cameras:
            camera, source = self.cameras[camera_pk][:2]
            if source is None:
                continue
            frame = source.read()
            if frame is not None:
                snapshot_path = (
                    f"{self.django_settings.MEDIA_ROOT}/camera_snaps/{source.name}.jpg"
                )
                cv.imwrite(snapshot_path, frame)
                camera.snapshot = snapshot_path
                camera.save()

    def update_source(self, camera_instance):
        old_camera = self.cameras[camera_instance.pk]

        old_rtsp_link = old_camera[0].rtsp_url
        if old_rtsp_link != camera_instance.rtsp_url:
            print("SOURCE URL CHANGED")
            old_source, old_feed = old_camera[1:]

            if old_source is not None:
                old_source.stop()
                old_feed.stop()

            self.cameras.pop(old_camera[0].pk)
            self.cameras[camera_instance.pk] = [camera_instance, None, None]

            self.connect_to_sources()
            self.update_live_feeds()
            self.start_detection()

        old_source_name = old_camera[0].name
        if old_source_name != camera_instance.name:
            old_source = old_camera[0]
            if old_source is not None:
                old_source.name = camera_instance.name

    def remove_source(self, camera_instance):
        old_camera = self.cameras[camera_instance.pk]
        _, source, feed = old_camera

        if source is not None:
            source.stop()
            feed.stop()

        self.cameras.pop(camera_instance.pk)

        # self.connect_to_sources()
        # self.update_live_feeds()
        self.start_detection()
