"""
This module provides a high level API to the IP cameras that will be used with
OpenSec.

The CameraHub class has several methods that act as wrappers around lower-level
VidGear and OpenCV functions. These methods are responsible for streaming the
camera feeds to the front end and for object detection.
"""
import asyncio

# import os
import time

import cv2 as cv
import uvicorn
from starlette.responses import StreamingResponse
from starlette.routing import Route
from vidgear.gears import VideoGear
from vidgear.gears.asyncio import WebGear
from vidgear.gears.asyncio.helper import reducer as async_reducer
from vidgear.gears.helper import reducer

DEBUG = True


class Camera:
    """
    doc
    """

    def __init__(self, name, source, reset_attempts=50, reset_delay=5):
        self.name = name
        self.reset_attempts = reset_attempts
        self.reset_delay = reset_delay
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
        except RuntimeError:
            print("Attempting reconnection")
        return camera

    def read(self, reduce_amount=None):
        """
        doc
        """
        if self.reset_attempts > 0:
            frame = self.camera.read()
            if frame is None:
                self.stop()
                self.reset_attempts -= 1

                print(f"""Re-connection Attempt-{self.reset_attempts}""")

                time.sleep(self.reset_delay)
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

    @staticmethod
    def create_video_response(frame_producer):
        """
        Creates a video streaming http response to use with
        the uvicorn web server
        """

        async def video_response(scope):
            assert scope["type"] in ["http", "https"]
            await asyncio.sleep(0.00001)
            return StreamingResponse(
                frame_producer(),
                media_type="multipart/x-mixed-replace; boundary=frame",
            )

        return video_response

    def create_frame_producer(self):
        """
        Creates a frame producer (i.e. a generator) that will be used to make
        HTTP video streaming responses
        """

        async def frame_producer():

            while True:
                frame = self.read()

                if frame is None:
                    break

                frame = await async_reducer(frame, percentage=50)

                encode_param = [int(cv.IMWRITE_JPEG_QUALITY), 60]
                encoded_img = cv.imencode(".jpg", frame, encode_param)[1].tobytes()
                # yield frame in byte format
                yield (
                    b"--frame\r\nContent-Type:video/jpeg2000\r\n\r\n"
                    + encoded_img
                    + b"\r\n"
                )
                await asyncio.sleep(0.00001)
            # close stream
            self.stop()

        return frame_producer

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

    def start_web_server(self):
        """
        Starts a local web server to stream the cameras' live feed
        across the network
        """

        stream_options = {
            "custom_data_location": "./",
            "frame_size_reduction": 80,
            "jpeg_compression_quality": 40,
            "jpeg_compression_fastdct": True,
            "jpeg_compression_fastupsample": True,
        }

        # initialize WebGear app without any source
        web = WebGear(logging=True, **stream_options)

        frame_producers = [cam.create_frame_producer() for cam in self.cameras]

        web.config["generator"] = frame_producers[0]

        video_responses = [
            Camera.create_video_response(producer) for producer in frame_producers[1:]
        ]

        for index, video_response in enumerate(video_responses):
            web.routes.append(Route(f"/video{index+2}", endpoint=video_response))

        # run this app on Uvicorn server at address http://localhost:8000/
        uvicorn.run(web(), host="0.0.0.0", port=8000)

        # close app safely
        web.shutdown()

    def __str__(self):
        return f"CameraHub(num_cameras={self.num_cameras}, detection={self.detection})"


if __name__ == "__main__":

    cam_hub = CameraHub()
    cam_1 = Camera("webcam", 0)
    cam_2 = Camera("IP cam", "rtsp://admin:123456@192.168.1.226:554")
    cam_hub.add_camera(cam_1)
    cam_hub.add_camera(cam_2)
    # cam_hub.display_cams()
    cam_hub.start_web_server()
