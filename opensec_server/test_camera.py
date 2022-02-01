"""
Unit tests for the `camera.py` module.

These tests cover both the Camera and CameraHub classes. 
"""
import os
import time
import unittest

from camera import LOCAL_IP_ADDRESS, TEST_CAM, Camera, CameraHub

PORT = 8080


class TestCamera(unittest.TestCase):
    def setUp(self):
        self.non_valid_sources = ["https://123.123.123:554/", "54", 23]
        self.valid_sources = [
            "rtsp://123.123.123:554",
            "rtsp://username:pass@123.123.123:554",
            "rtsp://username:pass@123.123.123:554/stream.amp",
        ]

        # Replace this value with a working camera in your environment
        # if you want to pass the below tests
        self.working_camera = TEST_CAM
        self.non_working_camera = "rtsp://123.123.123:554"

    def test_camera_non_valid_sources(self):
        for non_valid_source in self.non_valid_sources:
            with self.assertRaises(ValueError):
                Camera.validate_source(non_valid_source)

    def test_camera_valid_sources(self):
        for valid_source in self.valid_sources:
            src = Camera.validate_source(valid_source)
            self.assertTrue(src == valid_source or src == f"{valid_source}/")

    def test_create_camera(self):
        cam_1 = Camera("test_1", self.working_camera)
        self.assertIsNotNone(cam_1)
        cam_1.stop()

        with self.assertRaises(RuntimeError):
            cam_2 = Camera("test_2", self.non_working_camera)
            cam_2.stop()

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

    def test_camera_stream(self):
        # Clear stream folder
        if os.path.exists("./stream"):
            for file in os.listdir("./stream"):
                os.unlink(f"./stream/{file}")

        cam = Camera("test", self.working_camera)

        cam.start_camera_stream(stream_name="test")

        # Give the stream some time to generate video segment files
        time.sleep(20)

        cam.stop()

        # Check that stream files have been generated
        self.assertTrue(os.path.exists("./stream/test-stream.m3u8"))


class TestCameraHub(unittest.TestCase):
    def setUp(self):
        # Replace this value with a working camera in your environment
        self.working_camera = [TEST_CAM] * 4

    def test_add_cameras(self):
        cam_1 = Camera("test", self.working_cameras[0])
        cam_2 = Camera("test", self.working_cameras[1])

        cam_hub = CameraHub()
        cam_hub.add_camera(cam_1)
        cam_hub.add_camera(cam_2)

        self.assertEqual(cam_hub.num_cameras, 2)
        cam_1.stop()
        cam_2.stop()

    def test_get_camera(self):
        cam_1 = Camera("test", self.working_cameras[0])
        cam_2 = Camera("test", self.working_cameras[1])

        cam_hub = CameraHub()
        cam_hub.add_camera(cam_1)
        cam_hub.add_camera(cam_2)

        cam_1_from_hub = cam_hub.get_camera(0)
        cam_2_from_hub = cam_hub.get_camera(1)

        self.assertEqual(cam_1, cam_1_from_hub)
        self.assertEqual(cam_2, cam_2_from_hub)
        cam_1.stop()
        cam_2.stop()

        with self.assertRaises(ValueError):
            cam_hub.get_camera(5)

    def test_remove_camera(self):
        cam_1 = Camera("test", self.working_cameras[0])
        cam_2 = Camera("test", self.working_cameras[1])

        cam_hub = CameraHub()
        cam_hub.add_camera(cam_1)
        cam_hub.add_camera(cam_2)

        cam_hub.remove_camera(cam_1)
        self.assertEqual(cam_hub.num_cameras, 1)

        cam_hub.remove_camera(0)
        self.assertEqual(cam_hub.num_cameras, 0)

        with self.assertRaises(ValueError):
            cam_hub.remove_camera(cam_1)

        with self.assertRaises(ValueError):
            cam_hub.remove_camera(0)


if __name__ == "__main__":
    unittest.main()
