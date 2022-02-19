import os
import unittest

import config
from camera import LiveFeed, VideoSource
from starlette.testclient import TestClient

vids = [
    f"{config.TEST_VID_DIRECTORY}/{video}"
    for video in os.listdir(config.TEST_VID_DIRECTORY)
]


class TestLiveFeed(unittest.TestCase):
    def test_live_feed(self):
        source = VideoSource(vids[0])
        source.start()

        feed = LiveFeed()
        feed.source = source

        stream = feed.stream_app
        client = TestClient(stream())
        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("video", response.text)
        source.stop()
        feed.stop()


if __name__ == "__main__":
    unittest.main()
