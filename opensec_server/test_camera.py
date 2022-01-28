import unittest

from camera import Camera


class TestCamera(unittest.TestCase):
    def setUp(self):
        self.non_valid_sources = ["https://123.123.123:554/", "54", -23]
        self.valid_sources = [
            "rtsp://123.123.123:554",
            "rtsp://username:pass@123.123.123:554",
            23,
        ]

        # Camera 0 is usually going to be a laptop or usb webcam,
        # if you don't have one of those then most of these tests will fail
        self.working_camera = 0
        self.non_working_camera = "rtsp://123.123.123:554"

    def test_camera_non_valid_sources(self):
        for non_valid_source in self.non_valid_sources:
            with self.assertRaises(ValueError):
                Camera.validate_source(non_valid_source)

    def test_camera_valid_sources(self):
        for valid_source in self.valid_sources:
            self.assertIsNotNone(Camera.validate_source(valid_source))

    def test_create_camera(self):
        cam_1 = Camera("test_1", self.working_camera)
        self.assertIsNotNone(cam_1)
        cam_1.stop()

        with self.assertRaises(ValueError):
            cam_2 = Camera("test_2", self.non_working_camera)
            cam_2.stop()

    def test_reducer(self):
        cam = Camera("test_reducer", self.working_camera)

        w_1, h_1, _ = cam.read_frame().shape
        w_2, h_2, _ = cam.read_frame(50).shape

        self.assertLess(w_2, w_1)
        self.assertLess(h_2, h_1)

        cam.stop()

    def test_camera_equality(self):
        cam_1 = Camera("test", 0)
        cam_2 = Camera("test", 0)

        self.assertEqual(cam_1, cam_2)
        cam_1.stop()
        cam_2.stop()


if __name__ == "__main__":
    unittest.main()
