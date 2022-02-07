"""
This module provides a high level API to the IP cameras that will be used with
OpenSec.

The CameraHub class has several methods that act as wrappers around lower-level
VidGear and OpenCV functions. These methods are responsible for streaming the
camera feeds to the front end and for intruder detection.
"""
import json
import random
import shutil
import subprocess
import time
from collections import deque
from threading import Thread

import config
import cv2 as cv
import imageio
from vidgear.gears import VideoGear
from vidgear.gears.helper import reducer

# TODO: Complete documentation
# TODO: Avoid type checking with isinstance


# TODO: Implement alternative camera stream implementation
# https://stackoverflow.com/questions/45906482/how-to-stream-opencv-frame-with-django-frame-in-realtime?answertab=active#tab-top


class VideoBuffer:
    """
    TODO
    """

    def __init__(self, buffer_len=3600):
        """
        TODO
        """
        self._buffer = deque(maxlen=buffer_len)

    def add_frame(self, frame):
        """
        TODO
        """
        self._buffer.append(frame)

    def write_to_video(self, video_path, fps=30):
        """
        TODO
        """
        video_dims = self._get_input_dimensions()
        codec = cv.VideoWriter_fourcc(*list("mp4v"))
        video_writer = cv.VideoWriter(video_path, codec, fps, video_dims)

        for frame in self._buffer:
            video_writer.write(frame)
        video_writer.release()

    def write_to_gif(self, gif_path, num_frames=100, fps=30):
        """
        TODO: Lower GIF size/improve performance
        """
        # We have to convert the openCV frames to rgb so they can
        # be accepted by the imageio library
        gif_frames = []
        for idx in range(num_frames):
            rgb_frame = cv.cvtColor(self._buffer[idx], cv.COLOR_BGR2RGB)
            gif_frames.append(rgb_frame)

        imageio.mimsave(gif_path, gif_frames, fps=fps)

    def write_thumbnail(self, img_path):
        """
        TODO
        """
        random_frame = self._buffer[random.randint(0, len(self._buffer) // 3)]
        cv.imwrite(img_path, random_frame)

    def clear(self):
        """
        TODO
        """
        self._buffer.clear()

    def _get_input_dimensions(self):
        height, width, _ = self._buffer[0].shape
        return width, height

    def __len__(self):
        return len(self._buffer)

    def __str__(self):
        return f"VideoBuffer(buffer_length={self._buffer.maxlen})"


class Camera:
    """
    This class provides a high-level API to a wireless IP camera located
    on the local network.
    With this API you can read frames from the camera and stream the camera
    feed across the local network.

    Public Attributes
    ----------
    name: str
        The name to give the camera

    source: str
        The RTSP URL that is used to access the camera feed

    connected: boolean
        A boolean flag to show whether or not the camera is connected

    fps: int
        The frame rate of the camera
    """

    def __init__(self, name, source, max_reset_attempts=5):
        """
        Inits Camera objects.
        """
        self.name = name
        self.source = Camera.validate_source_url(source)
        self.connected = False
        self.camera_open = False

        self._current_frame = None
        self._camera = None
        self._camera_thread = None
        self._stream_process = None
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = max_reset_attempts

        self._connect_to_cam()

    @property
    def fps(self):
        """
        Returns the camera's frame rate

        Returns
        -------
        fps: int
            The frame rate of the connected camera
        """
        return self._camera.framerate

    def start(self):
        """
        TODO
        """
        self.camera_open = True
        self._camera_thread = Thread(target=self._update_frame, daemon=True)
        self._camera_thread.start()

    def read(self):
        """
        TODO
        """
        return self._current_frame

    def _update_frame(self):
        """
        Reads a frame from the camera.

        Returns a frame from the remote camera with an option
        to reduce its size.

        Parameters
        ----------
        reduce_amount : int, optional
            Percentage amount to reduce the frame size by.
            If `reduce_amount` is None the original frame will be
            returned, by default None

        Returns
        -------
        numpy array
            Returns an n-dimensional matrix representing a single frame
            from the remote camera. Typically this matrix will have a shape of
            (width, height, number_of_channels).
        """
        while self.camera_open:
            # Read a frame from the camera
            frame = self._camera.read()
            if frame is None:
                self.connected = False
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
            time.sleep(0.01)

    def stop(self):
        """
        Stops the camera video capture object and stream.

        Sets the reset count to zero, sets the placeholder frame flag to True,
        and stops the camera stream and video capture object.
        """
        self.connected = False
        self._reconnect_attempts = 0
        self.camera_open = False

        if self._camera:
            self._camera.stop()

        print(f"{self.name} stopped.")

    @staticmethod
    def check_source_alive(source, timeout=5):
        """
        TODO
        """
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
        """
        Helper function to check that the source is a valid RTSP URL

        Parameters
        ----------
        source : Any
            Source object that is being validated.

        Returns
        -------
        source: str
            Will return the source if it is valid.

        Raises
        ------
        ValueError
            Will raise a ValueError if the source is not valid.
        """

        err_message = "ERROR: Source must be an RTSP URL"
        if not isinstance(source, str):
            raise ValueError(err_message)

        if not source.startswith("rtsp://"):
            raise ValueError(err_message)

        if not source.endswith("/"):
            return source + "/"

        return source

    def _connect_to_cam(self):
        """
        Attempts connection to remote camera.

        Returns
        -------
        VideoGear object
            An object that can read frames from a remote camera

        """

        if not Camera.check_source_alive(self.source):
            raise RuntimeError("ERROR: Could not connect to camera.")
        try:
            camera = VideoGear(source=self.source, logging=config.CAM_DEBUG).start()
            self.connected = True
            self._camera = camera
        except RuntimeError as err:
            raise RuntimeError("ERROR: Could not connect to camera.") from err

    def _reconnect(self):
        """
        Attempts a reconnection to the camera

        A maximum of `self._max_reconnect_attempts` will be made before raising
        an exception.

        Returns
        -------
        camera: VideoGear object
            A VideoGear video capture object will be returned after a
            successful connection.

        Raises
        ------
        RuntimeError
            A RuntimeError is raised when `self._reset_attempts`
            reaches the maximum value
        """
        while self._reconnect_attempts < self._max_reconnect_attempts:
            print(f"{self.name} reconnection attempt #{self._reconnect_attempts+1}")

            self._reconnect_attempts += 1
            time.sleep(2)

            if self._camera:
                self._camera.stop()

            if Camera.check_source_alive(self.source):
                print("Source alive. Attempting reconnection")
                try:
                    camera = VideoGear(
                        source=self.source, logging=config.CAM_DEBUG
                    ).start()
                    self.connected = True
                    self._camera = camera
                    self._reconnect_attempts = 0
                except RuntimeError:
                    pass

        raise RuntimeError("ERROR: Could not reconnect to camera")

    def __str__(self):
        """
        String representation of a Camera object.
        """
        return f"Camera({self.name}, {self.source})"

    def __eq__(self, other):
        """
        Define the equals operator for Camera objects.
        """
        return self.name == other.name
