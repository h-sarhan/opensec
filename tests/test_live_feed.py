import os
from time import sleep
import unittest

from config import TEST_CAMS
from camera import LiveFeed, CameraSource


class TestLiveFeed(unittest.TestCase):
    def test_live_feed(self):
        camera_source = CameraSource("test-cam", TEST_CAMS[0])
        feed = LiveFeed(camera_source)
        self.assertFalse(feed.is_streaming())

        feed.start()

        sleep(15)

        self.assertTrue(feed.is_streaming())
        self.assertTrue(os.path.exists(f"stream/{camera_source.name}"))
        self.assertTrue(os.path.exists(f"stream/{camera_source.name}/index.m3u8"))

        feed.stop()
        sleep(3)
        self.assertFalse(feed.is_streaming())


if __name__ == "__main__":
    unittest.main()
