"""
This module provides a high level API to the IP cameras that will be used with
OpenSec.

The CameraHub class has several methods that act as wrappers around lower-level
VidGear and OpenCV functions. These methods are responsible for streaming the
camera feeds to the front end and for object detection.
"""
import cv2 as cv
from vidgear.gears import CamGear
from vidgear.gears.asyncio import WebGear
from vidgear.gears.helper import reducer

DEBUG = False


class Camera:
    """
    doc
    """

    stream_options = {
        "frame_size_reduction": 50,
        "jpeg_compression_quality": 70,
        "jpeg_compression_fastdct": True,
        "jpeg_compression_fastupsample": True,
    }

    def __init__(self, name, source):
        self.name = name
        self.source = Camera.validate_source(source)
        self.camera = self.connect_to_cam()

    def connect_to_cam(self):
        """
        doc
        """

        try:
            camera = CamGear(source=self.source, logging=DEBUG).start()
        except RuntimeError as err:
            raise ValueError(
                "ERROR: Could not connect to camera using the provided source."
            ) from err
        return camera

    def read_frame(self, reduce_amount=None):
        """
        doc
        """
        frame = self.camera.read()
        if reduce_amount is None:
            return frame

        return reducer(frame, percentage=reduce_amount)

    def stop(self):
        """
        doc
        """
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

            frames = [cam.read_frame(reduce_amount=50) for cam in self.cameras]

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

    def __str__(self):
        pass


if __name__ == "__main__":

    cam_hub = CameraHub()
    cam_1 = Camera("webcam", 0)
    cam_2 = Camera("IP cam", "rtsp://admin:123456@192.168.1.226:554")
    cam_hub.add_camera(cam_1)
    cam_hub.add_camera(cam_2)
    cam_hub.display_cams()
