"""
This module provides a high level API to the IP cameras that will be used with
OpenSec.

The CameraHub class has several methods that act as wrappers around lower-level
VidGear and OpenCV functions. These methods are responsible for streaming the
camera feeds to the front end and for intruder detection.
"""
import json
import os
import random
import shutil
import subprocess
import time
from threading import Thread

import config
import cv2 as cv
import ffmpeg
import imageio
import numpy as np
from vidgear.gears import VideoGear, WriteGear
from vidgear.gears.helper import reducer

# TODO: Complete documentation
# TODO: Avoid type checking with isinstance


# TODO: Implement alternative camera stream implementation
# https://stackoverflow.com/questions/45906482/how-to-stream-opencv-frame-with-django-frame-in-realtime?answertab=active#tab-top


class VideoBuffer:
    """
    TODO
    """

    def __init__(self, output_path, video_dims, buffer_len=300, max_buffer_parts=5):
        """
        TODO
        """
        self.buffer_len = buffer_len
        self.output_path = output_path
        self._buffer = np.empty(
            shape=(self.buffer_len, *video_dims),
            dtype=np.uint8,
        )
        self._frame_idx = 0
        self._current_part = 0
        self._max_buffer_parts = max_buffer_parts

    def add_frame(self, frame):
        """
        TODO
        """
        if self._frame_idx < self.buffer_len:
            self._buffer[self._frame_idx] = frame
            self._frame_idx += 1
            print("add frame")
        elif (
            self._frame_idx == self.buffer_len
            and self._current_part < self._max_buffer_parts
        ):
            print("write buffer")
            self.write_buffer_to_video()
            self._frame_idx = 0
            self.clear()
            self._current_part += 1

        else:
            print("merge buffers")
            self.merge_parts()
            self._current_part = 0
            self._frame_idx = 0

    def write_buffer_to_video(self):
        """
        TODO
        """

        video_writer = WriteGear(
            f"{self.output_path}/recordings/parts/part-0{self._current_part}.mp4",
            compression_mode=False,
        )

        for idx, frame in enumerate(self._buffer):
            if idx >= self._frame_idx:
                break
            video_writer.write(frame)

        video_writer.close()

    def write_buffer_to_gif(self, num_frames=50, fps=10, skip_frames=4):
        """
        TODO
        """
        # We have to convert the openCV frames to rgb so they can
        # be accepted by the imageio library
        gif_frames = []
        end_idx = min(num_frames * skip_frames, self.buffer_len)
        for idx in range(0, end_idx, skip_frames):
            rgb_frame = cv.cvtColor(self._buffer[idx], cv.COLOR_BGR2RGB)
            reduced_frame = reducer(
                rgb_frame, percentage=70, interpolation=cv.INTER_NEAREST
            )
            gif_frames.append(reduced_frame)

        imageio.mimsave(
            f"{self.output_path}/gifs/intruder.gif",
            gif_frames,
            fps=fps,
            subrectangles=True,
            palettesize=128,
        )

    def write_thumbnail(self):
        """
        TODO
        """
        random_frame = self._buffer[random.randint(0, len(self._buffer) // 3)]
        cv.imwrite(f"{self.output_path}/thumbs/thumbnail.jpg", random_frame)

    def merge_parts(self, recording_name="recording"):
        """
        TODO
        """
        if self._frame_idx < self.buffer_len - 10:
            self.write_buffer_to_video()
        recording_path = f"{self.output_path}/recordings/{recording_name}.mp4"
        parts_path = f"{self.output_path}/recordings/parts"
        parts = [
            ffmpeg.input(f"{parts_path}/{part}") for part in os.listdir(parts_path)
        ]
        ffmpeg.concat(*parts).output(recording_path).run()

    def clear(self):
        """
        TODO
        """
        self._buffer = np.empty_like(self._buffer)

    def __len__(self):
        return self._frame_idx

    def __str__(self):
        return f"VideoBuffer(buffer_length={self._buffer.shape[0]})"


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
