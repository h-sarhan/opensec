"""
This module provides a high level API to the IP cameras that will be used with
OpenSec.

The CameraHub class has several methods that act as wrappers around lower-level
VidGear and OpenCV functions. These methods are responsible for streaming the
camera feeds to the front end and for intruder detection.
"""
import json
import os
import shutil
import subprocess
import time
from threading import Thread

import config
import cv2 as cv
import numpy as np
import uvicorn
from vidgear.gears import VideoGear
from vidgear.gears.asyncio import WebGear_RTC

# TODO: Add logging and error handling
# TODO: Create BaseSource or Source class
# TODO: Avoid type checking with isinstance
# TODO: DOCUMENTATION
# TODO: WRITE TESTS


class CameraSource:
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

    def read(self, resize=False):
        """
        TODO
        """
        if resize and self._current_frame is not None:
            return cv.resize(
                self._current_frame,
                (config.RESIZED_FRAME_WIDTH, config.RESIZED_FRAME_HEIGHT),
                cv.INTER_NEAREST,
            )
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
        """
        Stops the camera video capture object and stream.

        Sets the reset count to zero, sets the placeholder frame flag to True,
        and stops the camera stream and video capture object.
        """
        print(f"Stopping camera source {self.name}.")
        self._connected = False
        self._camera_open = False
        self._reconnect_attempts = 0

        if self._camera and self._camera_open:
            self._camera.stop()

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
        """
        TODO
        """
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
        """
        String representation of a Camera object.
        """
        return f"Camera({self.name}, {self.source})"

    def __eq__(self, other):
        """
        Define the equals operator for Camera objects.
        """
        return self.name == other.name


class VideoSource:
    """
    TODO
    """

    def __init__(self, video_path):
        self.name = video_path.split("/")[-1]
        self._vid_cap = VideoGear(source=video_path)
        self._vid_cap_thread = None
        self._vid_cap_open = False
        self._current_frame = None

    @property
    def is_active(self):
        """
        TODO
        """
        return self._vid_cap_open

    def start(self):
        """
        TODO
        """
        if self._vid_cap_open:
            print(f"Video source {self.name} is already on")
        else:
            self._vid_cap.start()
            self._vid_cap_open = True
            self._vid_cap_thread = Thread(target=self._update_frame)
            self._vid_cap_thread.start()

    def read(self, resize=False):
        """
        TODO
        """
        if resize and self._current_frame is not None:
            return cv.resize(
                self._current_frame,
                (config.RESIZED_FRAME_WIDTH, config.RESIZED_FRAME_HEIGHT),
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
        """
        TODO
        """
        print(f"Stoping video source {self.name}")
        if self._vid_cap and self._vid_cap_open:
            self._vid_cap.stop()

        self._vid_cap_open = False


class LiveFeedProducer:
    """
    TODO
    """

    def __init__(self, sources):
        self.sources = sources
        self.running = True
        self._live_feed_shape = (
            config.RESIZED_FRAME_HEIGHT * 2,
            config.RESIZED_FRAME_WIDTH * 2,
            3,
        )
        self._single_frame_shape = (
            config.RESIZED_FRAME_HEIGHT,
            config.RESIZED_FRAME_WIDTH,
            3,
        )
        self._live_feed_frame = np.zeros(self._live_feed_shape, np.uint8)
        # TODO: Draw text on blank frame
        self._blank_frame = np.zeros(self._single_frame_shape, np.uint8)
        self._frame_count = 0
        self._current_frame = None
        Thread(target=self._update_frame).start()

    def read(self):
        """
        TODO
        """
        return self._current_frame

    def _update_frame(self):
        # TODO: Make this work with a variable number of sources

        while self.running:
            frames = []
            for source in self.sources:
                frame = source.read(resize=True)
                if frame is None:
                    print("Frame is none")
                    frames.append(self._blank_frame)
                else:
                    frames.append(frame)

            frame_height, frame_width, _ = self._single_frame_shape
            self._live_feed_frame[:frame_height, :frame_width] = frames[0]
            self._live_feed_frame[:frame_height, frame_width:] = frames[1]
            self._live_feed_frame[frame_height:, :frame_width] = frames[2]
            self._live_feed_frame[frame_height:, frame_width:] = frames[3]
            self._current_frame = self._live_feed_frame
            time.sleep(1 / config.FPS)

        self._current_frame = None

    def stop(self):
        """
        TODO
        """
        self.running = False


class LiveFeed:
    """
    TODO
    """

    def __init__(self, sources, stream_directory="stream"):
        self.sources = sources
        self.stream_directory = stream_directory
        self.live_feed_options = {
            "custom_stream": LiveFeedProducer(self.sources),
            "custom_data_location": "./",
            "enable_live_broadcast": True,
            "frame_size_reduction": 0,
        }
        self.stream = WebGear_RTC(logging=True, **self.live_feed_options)

        self._streaming = False
        self._server = None

    @property
    def is_streaming(self):
        """
        TODO
        """
        all_sources_inactive = all(not source.is_active for source in self.sources)
        if not self._streaming or all_sources_inactive:
            return False
        return True

    # @profile
    def start_streaming_live_feed(self):
        """
        TODO
        """
        for source in self.sources:
            source.start()

        # Give the sources some time to read frames
        time.sleep(10)
        uvicorn.run(self.stream(), host="0.0.0.0", port=8000)

    def start(self):
        """
        TODO
        """
        self._streaming = True
        Thread(target=self.start_streaming_live_feed).start()

    def stop(self):
        """
        TODO
        """
        print("Stopping streaming server")
        if self._streaming:
            self._streaming = False
            self.stream.shutdown()

    def _make_dirs(self):
        for source in self.sources:
            dir_name = f"stream/{source.name}"
            if not os.path.exists(dir_name):
                os.mkdir(dir_name)
