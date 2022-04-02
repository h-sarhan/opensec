from __future__ import annotations

import os
import shutil
import subprocess

import config

from camera.camera import CameraSource
from camera.detection import DetectionSource


class LiveFeed:
    """
    Class used to manage the live feed of a camera source
    """

    def __init__(self, source: DetectionSource | CameraSource):
        self.source = source
        self.stream_directory = f"{config.STREAM_DIRECTORY}/{source.name}"
        self._stream_process: subprocess.Popen | None = None
        self._make_dir()

    def is_streaming(self) -> bool:
        if self._stream_process is None or self._stream_process.poll() is not None:
            return False
        return True

    def start_streaming(self) -> None:
        """
        Starts streaming the live feed of a camera source
        """
        rtsp_link = self.source.get_rtsp_link()
        stream_args = [
            shutil.which("ffmpeg"),
            "-i",
            rtsp_link,
            "-vcodec",
            "copy",
            "-an",
            "-sc_threshold",
            "0",
            "-f",
            "hls",
            "-hls_time",
            "10",
            "-hls_list_size",
            "10",
            "-hls_flags",
            "delete_segments",
            f"{self.stream_directory}/index.m3u8",
        ]

        self._stream_process = subprocess.Popen(
            stream_args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def start(self) -> str:
        """
        Starts the live feed
        """
        if self._stream_process is None:
            self.start_streaming()
        return f"/media/stream/{self.source.name}/index.m3u8"

    def stop(self) -> None:
        """
        Stops the live feed
        """
        if self._stream_process is not None:
            self._stream_process.kill()
        self._stream_process = None

    def _make_dir(self) -> None:
        """
        Creates a directory to store stream files if they don't exist
        If they do exist the function will delete the video files in each directory
        """
        if not os.path.exists(self.stream_directory):
            os.mkdir(self.stream_directory)
        else:
            for file in os.listdir(self.stream_directory):
                os.remove(f"{self.stream_directory}/{file}")
