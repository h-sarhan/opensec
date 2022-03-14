from __future__ import annotations
import os
import subprocess
import shutil
import http
import socketserver
from threading import Thread

from camera.camera import CameraSource, VideoSource
from camera.detection import DetectionSource

# Removes console output from base Http handler
# https://stackoverflow.com/questions/56227896/how-do-i-avoid-the-console-logging-of-http-server
class SuppressedHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


class LiveFeed:
    def __init__(self, source: VideoSource | DetectionSource | CameraSource):
        self.source = source
        self.stream_directory = f"stream/{source.name}"
        self._stream_process: subprocess.Popen | None = None
        self._server: socketserver.TCPServer | None = None
        self._make_dir()

    def is_streaming(self) -> bool:
        if self._stream_process is None or self._stream_process.poll() is not None:
            return False
        return True

    def start_streaming(self) -> None:

        stream_args = [
            shutil.which("ffmpeg"),
            "-i",
            self.source.source,
            "-vcodec",
            "copy",
            "-an",
            "-sc_threshold",
            "0",
            "-f",
            "hls",
            "-hls_time",
            "5",
            "-hls_list_size",
            "5",
            "-hls_flags",
            "delete_segments",
            f"{self.stream_directory}/index.m3u8",
        ]

        self._stream_process = subprocess.Popen(
            stream_args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def start_server(self) -> None:
        """
        TODO
        """
        self._server = socketserver.TCPServer(("0.0.0.0", 8000), SuppressedHTTPHandler)
        print("Streaming server started at port", 8000)
        self._server.serve_forever()

    def start(self) -> None:
        if self._stream_process is None:
            self.start_streaming()
        if self._server is None:
            Thread(target=self.start_server).start()

    def stop(self) -> None:
        if self._stream_process is not None:
            self._stream_process.kill()
        self._server.shutdown()
        self._server.server_close()
        self._server = None
        self._stream_process = None

    def _make_dir(self) -> None:
        dir_name = f"stream/{self.source.name}"
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)
