"""
This module provides a high level API to the IP cameras that will be used with
OpenSec.

The CameraHub class has several methods that act as wrappers around lower-level
VidGear and OpenCV functions. These methods are responsible for streaming the
camera feeds to the front end and for intruder detection.
"""
import os
import shutil
import socket
import subprocess
import time
from threading import Thread

import cv2 as cv
from dotenv import load_dotenv
from vidgear.gears import VideoGear
from vidgear.gears.helper import reducer

# Loading environment variables
load_dotenv()

TEST_CAM = os.getenv("TEST_CAM")
STREAM_DIRECTORY = os.getenv("STREAM_DIRECTORY")
TEST_VID_DIRECTORY = os.getenv("TEST_VID_DIRECTORY")


CAM_DEBUG = True

HOST_NAME = socket.gethostname()
LOCAL_IP_ADDRESS = socket.gethostbyname(HOST_NAME)


# TODO: Add support for MJPEG streams
# TODO: Add error handling/reconnection to start_camera_stream


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

        self._camera = None
        self._stream_process = None
        self._reset_attempts = 0
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

    def read(self, reduce_amount=None):
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

        # Return the frame with an optional reduction in size
        if reduce_amount is None:
            return frame
        return reducer(frame, percentage=reduce_amount)

    def stop(self):
        """
        Stops the camera video capture object and stream.

        Sets the reset count to zero, sets the placeholder frame flag to True,
        and stops the camera stream and video capture object.
        """
        self.connected = False
        self._reset_attempts = 0

        self.stop_camera_stream()
        if self._camera:
            self._camera.stop()

        print(f"{self.name} stopped.")

    def start_camera_stream(
        self, stream_name=None, re_encode=False, scale=None, bitrate=None, logging=False
    ):
        """
        Starts streaming the camera feed to a server and saves the stream process.


        Parameters
        ----------
        stream_name : str, optional
            Give a name to the stream, if None the name of the
            camera will be used, by default None

        re_encode : bool, optional
            Choose whether or not to re-encode the camera stream, by default False

        scale : tuple, optional
            Choose to give a new scale to the video.
            If None, a frame with the same size as the source will be
            returned, by default None

            Warning: If `re_encode` is False then this setting will be ignored.

        bitrate : int, optional
            Choose a bitrate for the re-encoded video, by default 512

            Warning: If `re_encode` is False then this setting wil be ignored

        logging : bool, optional
            Choose to view Gstreamer logs, by default False

        Raises
        ------
        RuntimeError
            A RuntimeError is raised if Gstreamer is not installed.
        """

        if not os.path.exists(STREAM_DIRECTORY):
            os.mkdir(STREAM_DIRECTORY)

        if not stream_name:
            stream_name = self.name

        if not shutil.which("gst-launch-1.0"):
            raise RuntimeError("ERROR: Please install the latest version of GStreamer.")

        if not re_encode and (scale or bitrate):
            print("Warning: The stream is not being re-encoded so the ", end="")
            if scale:
                print("`scale` parameter will be ignored.")
            if bitrate:
                print("`bitrate` parameter will be ignored.")

        if re_encode:
            bitrate = 512

        # Path to the gstreamer executable
        gstreamer_arg = [shutil.which("gst-launch-1.0")]

        # These arguments define the video source
        video_source_args = [
            "-v",
            "rtspsrc",
            f'location="{self.source}"',
            "!",
            "rtph264depay",
        ]

        # These arguments define the re-encoding arguments
        re_encode_args = ["!", "avdec_h264", "!", "videoconvert", "!"]

        if scale:
            width, height = scale
            re_encode_args += [
                "videoscale",
                "!",
                f"video/x-raw,width={width} height={height}",
            ]

        re_encode_args += [
            "!",
            "x264enc",
            f"bitrate={bitrate}",
            "!",
            'video/x-h264,profile="high"',
        ]

        # These arguments define what container to use for the stream
        muxer_args = ["!", "mpegtsmux"]

        # These arguments define HLS stream arguments
        stream_args = [
            "!",
            "hlssink",
            f"playlist-root=http://{LOCAL_IP_ADDRESS}:8080/{''.join(STREAM_DIRECTORY.split('/')[1:])}",
            f"playlist-location={STREAM_DIRECTORY}/{stream_name}-stream.m3u8",
            f"location={STREAM_DIRECTORY}/{stream_name}-segment.%05d.ts",
            "target-duration=5",
            "max-files=5",
        ]

        # Assemble the arguments that will be used with GStreamer
        stream_process_args = gstreamer_arg + video_source_args

        if re_encode:
            stream_process_args += re_encode_args

        stream_process_args += muxer_args + stream_args

        if logging:
            console_output = None
        else:
            console_output = subprocess.DEVNULL

        # Create the Gstreamer process
        self._stream_process = subprocess.Popen(
            stream_process_args,
            stdout=console_output,
            stderr=console_output,
        )

    def stop_camera_stream(self):
        """
        Stops the camera stream process if it is running.
        """
        if self._stream_process:
            self._stream_process.kill()
        else:
            print("Camera stream is not running")

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

        If connection fails, a reconnection attempt will be made.

        Returns
        -------
        VideoGear object
            An object that can read frames from a remote camera

        """

        try:
            camera = VideoGear(source=self.source, logging=CAM_DEBUG).start()
            self.connected = True
            self._camera = camera
        except RuntimeError:
            self._reconnect()

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
        while self._reset_attempts < self._max_reconnect_attempts:
            print(f"{self.name} reconnection attempt #{self._reset_attempts+1}")

            self._reset_attempts += 1
            time.sleep(2)

            if self._camera:
                self._camera.stop()

            try:
                camera = VideoGear(source=self.source, logging=CAM_DEBUG).start()
                self.connected = True
                self._camera = camera
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


class CameraHub:
    """
    An API for the collection of cameras being used by OpenSec.
    With this API you can add/remove/retrieve individual cameras, start
    live streaming the cameras across the local network, and start
    detecting intruders.

    Public Attributes
    ----------
    num_cameras: int
        The number of cameras in the CameraHub object

    detection_status: bool
        Whether or not detection is turned on
    """

    def __init__(self):
        """
        Init CameraHub class
        """
        self.detection_status = False

        self._cameras = []
        self._camera_streams = []
        self._detection_threads = []

    @property
    def num_cameras(self):
        """
        Returns the number of cameras in the camera hub.
        """
        return len(self._cameras)

    def add_camera(self, camera):
        """
        Adds a camera to the camera hub.

        Parameters
        ----------
        camera: Camera object
            The camera to add to the camera hub

        Raises
        ----------
        ValueError:
            A ValueError is raised when `camera` is not a Camera
            object, and when `camera` is already in the camera hub
        """

        if isinstance(camera, list):
            raise ValueError("ERROR: Use `add_cameras` to add a list of cameras.")

        if not isinstance(camera, Camera):
            raise ValueError("ERROR: `camera` must be a Camera object.")

        if camera in self._cameras:
            raise ValueError("ERROR: This camera is already in the camera hub.")

        self._cameras.append(camera)

    def add_cameras(self, camera_list):
        """
        Similar to `add_camera` but accepts a list of Camera objects.

        Parameters
        ----------
        camera_list: list of Camera objects
            The list of cameras to add to the camera hub.

        Raises
        ----------
        ValueError
            A ValueError is raised if `camera_list` is not a list or
            if `camera_list` is an empty list.

        """
        if not isinstance(camera_list, list):
            raise ValueError("ERROR: `camera_list` must be a list of Camera objects.")

        if not camera_list:
            raise ValueError("ERROR: `camera_list` cannot be empty.")

        for camera in camera_list:
            self.add_camera(camera)

    def get_camera(self, name):
        """
        Returns the camera given its name.

        Parameters
        ----------
        name: str
            The name of the camera to retrieve.

        Returns
        ----------
        camera: Camera object
            If a camera with the given name is found then it will be returned

        Raise
        ----------
        ValueError
            A ValueError is raised if the camera can not be found.
        """

        if not isinstance(name, str):
            raise ValueError("ERROR: `name` must be a string.")

        for camera in self._cameras:
            if camera.name == name:
                return camera

        raise ValueError(f'ERROR: A camera with the name "{name}" could not be found.')

    def remove_camera(self, camera_to_remove):
        """
        Remove a camera using either the camera name or the camera
        object itself.

        Parameters
        ----------
        camera_to_remove: str, Camera object
            Specify which camera to remove by using either the name of the camera
            or the Camera object itself

        Raises
        ----------
        ValueError:
            A ValueError is raised if the `camera_to_remove` parameter is
            neither a Camera object or a string
        """

        if isinstance(camera_to_remove, Camera):
            try:
                self._cameras.remove(camera_to_remove)
                camera_to_remove.stop()
            except ValueError as err:
                raise ValueError(
                    f"ERROR: {camera_to_remove} not found in camera hub."
                ) from err

        elif isinstance(camera_to_remove, str):
            try:
                camera = self.get_camera(camera_to_remove)
                self._cameras.remove(camera)
                camera.stop()
            except ValueError as err:
                raise ValueError(
                    f"ERROR: {camera_to_remove} not found in camera hub."
                ) from err

        else:
            raise ValueError(
                "ERROR: `camera` parameter must be the name of the camera or the camera object."
            )

    def start_camera_streams(
        self,
        re_encode=False,
        scale=None,
        bitrate=None,
        logging=False,
    ):
        """
        Starts streaming each camera's live feed across the network.

        Parameters
        ----------
        re_encode : bool, optional
            Choose whether or not to re-encode the camera streams, by default False

        scale : tuple, optional
            Choose to give a new scale to the streams.
            If None, a frame with the same size as the source will be
            returned, by default None

            Warning: If `re_encode` is False then this setting will be ignored.

        bitrate : int, optional
            Choose a bitrate for the re-encoded streams, by default 512

            Warning: If `re_encode` is False then this setting wil be ignored

        logging : bool, optional
            Choose to view Gstreamer logs, by default False
        """

        self._camera_streams = [
            camera.start_camera_stream(
                stream_name=None,
                re_encode=re_encode,
                scale=scale,
                bitrate=bitrate,
                logging=logging,
            )
            for camera in self._cameras
        ]

    def stop_camera_streams(self):
        """
        Stops streaming the camera feed across the network and removes the
        video segment files from the stream directory.
        """
        if not self._camera_streams:
            print("Camera stream is not running")
            return

        for stream in self._camera_streams:
            if stream:
                stream.kill()

        self._camera_streams = None

    def display_cams(self):
        """
        Display the live feed of each camera in a separate window. This method
        is mainly used for testing purposes.

        Press q to stop displaying the cameras
        """
        while True:
            frames = [cam.read(reduce_amount=50) for cam in self._cameras]

            for cam, frame in zip(self._cameras, frames):
                cv.imshow(cam.name, frame)

            key = cv.waitKey(1) & 0xFF
            if key == ord("q"):
                break

        cv.destroyAllWindows()

    # def start_detection(self):
    #     self.detection_status = True
    #     for cam in self._cameras:
    #         detection_thread = Thread(
    #             target=cam.detect_intruders, args=(lambda: self.detection_status)
    #         )
    #         self._detection_threads.append(detection_thread)

    def __str__(self):
        """
        String representation of a camera hub
        """
        return f"CameraHub(num_cameras={self.num_cameras}, detection={self.detection_status})"


if __name__ == "__main__":
    pass
    # cam_hub = CameraHub()
    # cam_1 = Camera("IP cam 1", TEST_CAM)

    # cam_2 = Camera("IP cam 2", TEST_CAM)
    # cam_3 = Camera("IP cam 3", TEST_CAM)
    # cam_4 = Camera("IP cam 4", TEST_CAM)
    # cam_hub.add_camera(cam_1)
    # cam_hub.add_camera(cam_2)
    # cam_hub.add_camera(cam_3)
    # cam_hub.add_camera(cam_4)
    # cam_hub.start_camera_streams()
    # cam_1.start_camera_stream(stream_name="test")
    # input("Press enter to stop camera streaming")
    # cam_hub.stop_camera_streams()
    # cam_1.stop_camera_stream()
