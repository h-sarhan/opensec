import json
import shutil
import subprocess
import time
from threading import Thread

import config
import cv2 as cv
from vidgear.gears import VideoGear

# TODO: Add logging and error handling
# TODO: Create BaseSource or Source class
# TODO: Avoid type checking with isinstance
# TODO: DOCUMENTATION
# TODO: WRITE TESTS


class CameraSource:
    def __init__(self, name, source, max_reset_attempts=5):
        """
        Inits Camera objects.
        """
        self.name = name
        self.source = CameraSource.validate_source_url(source)

        self._current_frame = None
        self._connected = False
        self._camera_open = False
        self._camera = None
        self._camera_thread = None
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = max_reset_attempts

        self._connect_to_cam()

    # @property
    # def fps(self):
    #     return self._camera.framerate

    @property
    def is_active(self):
        """
        TODO
        """
        return self._camera_open and self._connected

    def start(self):
        """
        TODO
        """
        if self._camera_open:
            print(f"Camera {self.name} is already on")
        else:
            self._camera_open = True
            self._camera_thread = Thread(target=self._update_frame)
            self._camera_thread.start()

    def read(self, resize_frame=None):
        """
        TODO
        """
        if resize_frame and self._current_frame is not None:
            return cv.resize(
                self._current_frame,
                resize_frame,
                cv.INTER_NEAREST,
            )
        return self._current_frame

    def _update_frame(self):

        while self.is_active:
            # Read a frame from the camera
            frame = self._camera.read()
            if frame is None and self.is_active:
                self._connected = False
                # Attempt a reconnection if the frame cannot be read
                try:
                    self._reconnect()
                except RuntimeError:
                    # Stop the camera if the reconnection attempt failed
                    print(f"ERROR: Could not connect to {self.name}.")
                    print("Stopping camera.")
                    self.stop()

            # Update frame
            self._current_frame = frame
            time.sleep(1 / config.FPS)

    def stop(self):
        print(f"Stopping camera source {self.name}.")
        self._connected = False
        self._camera_open = False
        self._reconnect_attempts = 0

        if self._camera and self._camera_open:
            self._camera.stop()

    @staticmethod
    def check_source_alive(source, timeout=5):
        if not shutil.which("ffprobe"):
            raise RuntimeError("ERROR: Please install ffmpeg/ffprobe.")

        result = None
        try:
            result = subprocess.run(
                [
                    shutil.which("ffprobe"),
                    "-v",
                    "quiet",
                    "-print_format",
                    "json",
                    "-show_streams",
                    source,
                ],
                timeout=timeout,
                check=False,
                capture_output=True,
            )
        except subprocess.TimeoutExpired:
            return False

        try:
            json.loads(result.stdout)
        except json.JSONDecodeError:
            return False

        return True

    @staticmethod
    def validate_source_url(source):

        err_message = "ERROR: Source must be an RTSP URL"
        if not isinstance(source, str):
            raise ValueError(err_message)

        if not source.startswith("rtsp://"):
            raise ValueError(err_message)

        if not source.endswith("/"):
            return source + "/"

        return source

    def _connect_to_cam(self):
        if not CameraSource.check_source_alive(self.source):
            raise RuntimeError(f"ERROR: Could not connect to camera {self.name}.")
        try:
            print(f"{self.name} alive attempting connection")
            options = {"THREADED_QUEUE_MODE": False}
            camera = VideoGear(
                source=self.source, logging=True, time_delay=2, **options
            ).start()
            self._connected = True
            self._camera = camera
            print(f"Connected to camera {self.name}")
        except RuntimeError as err:
            raise RuntimeError(
                f"ERROR: Could not connect to camera {self.name}."
            ) from err

    def _reconnect(self):
        while self._reconnect_attempts < self._max_reconnect_attempts:
            print(f"{self.name} reconnection attempt #{self._reconnect_attempts+1}")

            self._reconnect_attempts += 1
            time.sleep(2)

            if self._camera:
                self._camera.stop()

            if CameraSource.check_source_alive(self.source):
                print("Source alive. Attempting reconnection")
                try:
                    options = {"THREADED_QUEUE_MODE": False}
                    camera = VideoGear(
                        source=self.source, logging=True, time_delay=2, **options
                    ).start()
                    self._connected = True
                    self._camera = camera
                    self._reconnect_attempts = 0
                    return
                except RuntimeError:
                    pass

        raise RuntimeError("ERROR: Could not reconnect to camera")

    def __str__(self):
        return f"Camera({self.name}, {self.source})"

    def __eq__(self, other):
        return self.name == other.name


class VideoSource:
    def __init__(self, video_path):
        self.name = video_path.split("/")[-1]
        self._vid_cap = VideoGear(source=video_path)
        self._vid_cap_thread = None
        self._vid_cap_open = False
        self._current_frame = None

    @property
    def is_active(self):

        return self._vid_cap_open

    def start(self):

        if self._vid_cap_open:
            print(f"Video source {self.name} is already on")
        else:
            self._vid_cap.start()
            self._vid_cap_open = True
            self._vid_cap_thread = Thread(target=self._update_frame)
            self._vid_cap_thread.start()
        return self

    def read(self, resize_frame=None):

        if resize_frame and self._current_frame is not None:
            return cv.resize(
                self._current_frame,
                resize_frame,
                cv.INTER_NEAREST,
            )
        return self._current_frame

    def _update_frame(self):

        while self.is_active:
            # Read a frame from the camera
            frame = self._vid_cap.read()

            if frame is None:
                self._current_frame = None
                break

            # Update frame
            self._current_frame = frame
            time.sleep(1 / config.FPS)

    def stop(self):

        print(f"Stoping video source {self.name}")
        if self._vid_cap and self._vid_cap_open:
            self._vid_cap.stop()

        self._vid_cap_open = False
