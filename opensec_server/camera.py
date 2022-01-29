"""
This module provides a high level API to the IP cameras that will be used with
OpenSec.

The CameraHub class has several methods that act as wrappers around lower-level
VidGear and OpenCV functions. These methods are responsible for streaming the
camera feeds to the front end and for object detection.
"""
import shutil
import socket
import subprocess
import time

import cv2 as cv
from vidgear.gears import VideoGear
from vidgear.gears.helper import reducer

DEBUG = True

hostname = socket.gethostname()
LOCAL_IP_ADDRESS = socket.gethostbyname(hostname)


class Camera:
    """
    doc
    """

    def __init__(self, name, source, max_reset_attempts=20):
        self.name = name
        self.reset_attempts = 0
        self.max_reset_attempts = max_reset_attempts
        self.source = Camera.validate_source(source)
        self.camera = self.connect_to_cam()

        # Stores the last frame in case of a reconnection
        self.last_frame = None

    def connect_to_cam(self):
        """
        doc
        """

        try:
            camera = VideoGear(source=self.source, logging=DEBUG).start()
            return camera
        except RuntimeError as err:
            print(f"""Re-connection Attempt-{self.reset_attempts}""")
            time.sleep(0.5)
            self.reset_attempts += 1
            if self.reset_attempts >= self.max_reset_attempts:
                raise RuntimeError("ERROR: Could not reconnect to camera") from err
            self.connect_to_cam()

    def read(self, reduce_amount=None):
        """
        doc
        """

        if self.reset_attempts < self.max_reset_attempts:
            frame = self.camera.read()
            if frame is None:
                self.camera.stop()
                self.reset_attempts += 1

                print(f"""Re-connection Attempt-{self.reset_attempts}""")

                time.sleep(0.5)
                self.camera = self.connect_to_cam()

                # return previous frame
                if reduce_amount is None:
                    return self.last_frame
                return reducer(self.last_frame, percentage=reduce_amount)
            else:
                self.last_frame = frame
                if reduce_amount is None:
                    return frame
                return reducer(frame, percentage=reduce_amount)
        else:
            return None

    def stop(self):
        """
        doc
        """
        print("STOPPED")
        self.reset_attempts = 0
        self.last_frame = None
        self.camera.stop()

    @staticmethod
    def validate_source(source):
        """
        doc
        """
        err_message = "ERROR: Source must be an non-negative integer or RTSP URL"
        if not isinstance(source, (int, str)):
            raise ValueError(err_message)

        if isinstance(source, int):
            if source < 0:
                raise ValueError(err_message)

            return source

        if not source.startswith("rtsp://"):
            raise ValueError(err_message)

        if not source.endswith("/"):
            return source + "/"

        return source

    def start_camera_stream(self):
        """
        doc
        """

        stream_process = subprocess.Popen(
            [
                shutil.which("gst-launch-1.0"),
                "-v",
                "rtspsrc",
                f'location="{self.source}"',
                "!",
                "rtph264depay",
                "!",
                "avdec_h264",
                "!",
                "clockoverlay",
                "!",
                "videoconvert",
                "!",
                "videoscale",
                "!",
                "video/x-raw,width=640, height=360",
                "!",
                "x264enc",
                "bitrate=512",
                "!",
                'video/x-h264,profile="high"',
                "!",
                "mpegtsmux",
                "!",
                "hlssink",
                f"playlist-root=http://{LOCAL_IP_ADDRESS}:8080/stream",
                f"playlist-location=./stream/{self.name}-stream.m3u8",
                f"location=./stream/{self.name}-segment.%05d.ts",
                "target-duration=5",
                "max-files=5",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        return stream_process

    def __str__(self):
        return f"Camera({self.name}, {self.source})"

    def __eq__(self, other):
        return self.name == other.name and self.source == other.source


class CameraHub:
    """
    doc
    """

    def __init__(self):
        self.cameras = []
        self.detection = False
        self.camera_streams = []

    @property
    def num_cameras(self):
        """
        Return number of cameras
        """
        return len(self.cameras)

    def add_camera(self, camera):
        """
        doc
        """

        if not isinstance(camera, Camera):
            raise ValueError("ERROR: `camera` must be a Camera object.")

        if camera in self.cameras:
            raise ValueError("ERROR: This camera is already in the camera hub")

        self.cameras.append(camera)

    def get_camera(self, index):
        """
        doc
        """
        if index > self.num_cameras or index < 0:
            raise ValueError("ERROR: Invalid index.")

        return self.cameras[index]

    def remove_camera(self, camera):
        """
        Remove a camera using either the camera index or the camera
        object itself
        """

        if isinstance(camera, Camera):
            self.cameras.remove(camera)
            camera.stop()

        elif isinstance(camera, int):
            if camera > self.num_cameras or camera < 0:
                raise ValueError("ERROR: Invalid index.")

            try:
                camera = self.cameras.pop(camera)
            except IndexError as err:
                raise ValueError("ERROR:Invalid index") from err

            camera.stop()
        else:
            raise ValueError(
                "ERROR: `camera` parameter must be an integer or camera object"
            )

    def display_cams(self):
        """
        doc
        """
        while True:

            frames = [cam.read(reduce_amount=50) for cam in self.cameras]

            for frame in frames:
                if frame is None:
                    break

            for cam, frame in zip(self.cameras, frames):
                cv.imshow(cam.name, frame)

            key = cv.waitKey(1) & 0xFF
            if key == ord("q"):
                break

        cv.destroyAllWindows()
        for cam in self.cameras:
            cam.stop()

    def start_camera_streams(self):
        """
        Starts streaming each camera's live feed across the network
        """

        self.camera_streams = [camera.start_camera_stream() for camera in self.cameras]

    def stop_camera_streams(self):
        """
        doc
        """
        if not self.camera_streams:
            print("Camera stream is not running")
            return

        for stream in self.camera_streams:
            stream.kill()

        self.camera_streams = []

    def __str__(self):
        return f"CameraHub(num_cameras={self.num_cameras}, detection={self.detection})"


if __name__ == "__main__":

    cam_hub = CameraHub()
    # cam_1 = Camera("webcam", 0)
    cam_2 = Camera("IP cam", "rtsp://admin:123456@192.168.1.226:554")
    cam_3 = Camera("IP cam 2", "rtsp://admin:123456@192.168.1.226:554")
    cam_4 = Camera("IP cam 3", "rtsp://admin:123456@192.168.1.226:554")
    # cam_hub.add_camera(cam_1)
    cam_hub.add_camera(cam_2)
    cam_hub.add_camera(cam_3)
    cam_hub.add_camera(cam_4)
    cam_hub.start_camera_streams()
    # time.sleep(20)
    # cam_hub.stop_camera_streams()
    input("Press enter to stop camera streaming")
    cam_hub.stop_camera_streams()
