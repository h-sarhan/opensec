import os
from time import sleep
import unittest
from config import TEST_VID_DIRECTORY
from camera import VideoSource

import numpy as np


class TestCamera(unittest.TestCase):
    def test_video_source_is_active(self):
        for vid_name in os.listdir(TEST_VID_DIRECTORY):
            vid_path = f"{TEST_VID_DIRECTORY}/{vid_name}"
            vid_source = VideoSource(vid_path).start()
            self.assertIsNotNone(vid_source)
            self.assertTrue(vid_source.is_active)
            vid_source.stop()
            self.assertFalse(vid_source.is_active)

    def test_video_source_read_frame(self):
        for vid_name in os.listdir(TEST_VID_DIRECTORY):
            vid_path = f"{TEST_VID_DIRECTORY}/{vid_name}"
            vid_source = VideoSource(vid_path).start()
            frame_1 = vid_source.read()
            self.assertIsNotNone(frame_1)
            sleep(0.2)
            frame_2 = vid_source.read()
            self.assertFalse(np.array_equal(frame_1, frame_2))

            frame_3 = vid_source.read(resize_frame=(200, 150))
            shape_1, shape_2 = frame_2.shape, frame_3.shape
            self.assertFalse(np.array_equal(shape_1, shape_2))
            self.assertEqual(shape_2, (150, 200, 3))
            self.assertGreater(shape_1[0], shape_2[0])  # height
            self.assertGreater(shape_1[1], shape_2[1])  # width
            self.assertEqual(shape_1[2], shape_2[2])  # color channels
            vid_source.stop()


if __name__ == "__main__":
    unittest.main()
