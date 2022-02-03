"""
Unit tests for the `camera.py` module.

These tests cover both the Camera and CameraHub classes. 
"""
import os
import time
import unittest

import numpy as np

from camera import STREAM_DIRECTORY, TEST_CAM, Camera, CameraHub

PORT = 8080


def clear_stream_directory(stream_directory=STREAM_DIRECTORY):
    """
    Helper function to clear the stream directory
    """
    if os.path.exists(stream_directory):
        for file in os.listdir(stream_directory):
            os.unlink(f"{stream_directory}/{file}")


class TestCamera(unittest.TestCase):
    def setUp(self):
        self.non_valid_sources = ["https://123.123.123:554/", "54", 23]
        self.valid_sources = [
            "rtsp://123.123.123:554",
            "rtsp://username:pass@123.123.123:554",
            "rtsp://username:pass@123.123.123:554/stream.amp",
        ]

        # Replace the TEST_CAM value with a working camera in your environment
        # if you want to pass the below tests
        self.working_camera = TEST_CAM

        self.non_working_camera = "rtsp://123.123.123:554"

    def test_camera_non_valid_sources(self):
        for non_valid_source in self.non_valid_sources:
            with self.assertRaises(ValueError):
                Camera.validate_source_url(non_valid_source)

    def test_camera_valid_sources(self):
        for valid_source in self.valid_sources:
            src = Camera.validate_source_url(valid_source)
            self.assertTrue(src == valid_source or src == f"{valid_source}/")

    def test_create_camera(self):
        cam_1 = Camera("test_working", self.working_camera)

        self.assertTrue(cam_1.connected)
        self.assertIsNotNone(cam_1)

        cam_1.stop()

        self.assertFalse(cam_1.connected)

        with self.assertRaises(RuntimeError):
            cam_2 = Camera("test_not_working", self.non_working_camera)
            cam_2.stop()

    def test_read(self):
        cam = Camera("test_read", self.working_camera)

        frame = cam.read()

        self.assertIsNotNone(frame)
        self.assertIsInstance(frame, np.ndarray)

        cam.stop()

    def test_reducer(self):
        cam = Camera("test_reducer", self.working_camera)

        w_1, h_1, _ = cam.read().shape
        w_2, h_2, _ = cam.read(reduce_amount=50).shape

        self.assertLess(w_2, w_1)
        self.assertLess(h_2, h_1)

        cam.stop()

    def test_camera_equality(self):
        cam_1 = Camera("test", self.working_camera)
        cam_2 = Camera("test", self.working_camera)

        self.assertEqual(cam_1, cam_2)
        cam_1.stop()
        cam_2.stop()

    def test_working_camera_stream(self):

        clear_stream_directory()
        cam = Camera("test", self.working_camera)

        cam.start_camera_stream(stream_name="test")

        # Give the stream some time to generate video segment files
        time.sleep(20)

        # Check that stream files have been generated
        self.assertTrue(os.path.exists(f"{STREAM_DIRECTORY}/test-stream.m3u8"))

        cam.stop()

    @unittest.skip("Not implemented")
    def test_non_working_camera_stream(self):
        # TODO: Implement
        pass

    @unittest.skip("Not implemented")
    def test_re_encoding_camera_stream(self):
        # TODO: Implement
        pass


class TestCameraHub(unittest.TestCase):
    def setUp(self):
        # Replace the TEST_CAM value with a working camera in your environment
        # if you want to pass the tests
        self.cams = [Camera(f"test_{idx+1}", TEST_CAM) for idx in range(4)]

    def test_add_camera(self):
        cam_hub = CameraHub()
        cam_hub.add_camera(self.cams[0])
        cam_hub.add_camera(self.cams[1])

        self.assertEqual(cam_hub.num_cameras, 2)

        with self.assertRaises(ValueError):
            cam_hub.add_camera(self.cams)

        with self.assertRaises(ValueError):
            cam_hub.add_camera("Not a Camera")

        with self.assertRaises(ValueError):
            cam_hub.add_camera(self.cams[1])

    def test_add_cameras(self):
        cam_hub = CameraHub()

        cam_hub.add_cameras(self.cams)

        self.assertEqual(cam_hub.num_cameras, len(self.cams))

        with self.assertRaises(ValueError):
            cam_hub.add_cameras("Not a Camera list")

        with self.assertRaises(ValueError):
            cam_hub.add_cameras([])

    def test_get_camera(self):

        cam_hub = CameraHub()
        cam_hub.add_camera(self.cams[0])
        cam_hub.add_camera(self.cams[1])

        cam_1_from_hub = cam_hub.get_camera("test_1")
        cam_2_from_hub = cam_hub.get_camera("test_2")

        self.assertIs(self.cams[0], cam_1_from_hub)
        self.assertIs(self.cams[1], cam_2_from_hub)

        with self.assertRaises(ValueError):
            cam_hub.get_camera(0)

        with self.assertRaises(ValueError):
            cam_hub.get_camera("test_3")

    def test_remove_camera(self):
        cam_hub = CameraHub()
        cam_hub.add_camera(self.cams[0])
        cam_hub.add_camera(self.cams[1])

        cam_hub.remove_camera(self.cams[0])
        self.assertEqual(cam_hub.num_cameras, 1)

        cam_hub.remove_camera("test_2")
        self.assertEqual(cam_hub.num_cameras, 0)

        with self.assertRaises(ValueError):
            cam_hub.remove_camera(self.cams[0])

        with self.assertRaises(ValueError):
            cam_hub.remove_camera("test_1")

        with self.assertRaises(ValueError):
            cam_hub.remove_camera(0)

    def test_camera_streams(self):

        clear_stream_directory()

        cam_hub = CameraHub()

        cam_hub.add_cameras(self.cams)

        cam_hub.start_camera_streams()

        # Give the streams some time to generate video segment files
        time.sleep(20)

        # Check that stream files have been generated
        for cam in self.cams:
            self.assertTrue(
                os.path.exists(f"{STREAM_DIRECTORY}/{cam.name}-stream.m3u8")
            )

        cam_hub.stop_camera_streams()

    def tearDown(self):
        for cam in self.cams:
            cam.stop()


if __name__ == "__main__":
    unittest.main()
