from __future__ import annotations

import http
import os
import shutil
import socketserver
import subprocess
from threading import Thread

import config

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
        self.stream_directory = f"{config.STREAM_DIRECTORY}/{source.name}"
        self._stream_process: subprocess.Popen | None = None
        self._make_dir()

    def is_streaming(self) -> bool:
        if self._stream_process is None or self._stream_process.poll() is not None:
            return False
        return True

    def start_streaming(self) -> None:
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

    def start(self) -> str:
        if self._stream_process is None:
            self.start_streaming()

        return f"{self.stream_directory}/index.m3u8"

    def stop(self) -> None:
        if self._stream_process is not None:
            self._stream_process.kill()
        self._stream_process = None

    def _make_dir(self) -> None:
        if not os.path.exists(self.stream_directory):
            os.mkdir(self.stream_directory)


class LiveFeedServer:
    def __init__(self):
        self._server = None

    def start_server(self):
        Thread(target=self._start_server).start()

    def _start_server(self) -> None:
        self._server = socketserver.TCPServer(("0.0.0.0", 8080), SuppressedHTTPHandler)
        print("Streaming server started at port", 8080)
        self._server.serve_forever()

    def stop_server(self):
        self._server.shutdown()
        self._server.server_close()
