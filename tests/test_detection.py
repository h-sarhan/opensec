import os
from time import sleep
import unittest

import numpy as np
from camera import VideoSource, DetectionSource, IntruderDetector, IntruderRecorder
from config import TEST_VID_DIRECTORY, TEST_VIDEO_OUTPUT_DIRECTORY


class TestDetection(unittest.TestCase):
    def test_detection_source(self):
        vid_name = os.listdir(TEST_VID_DIRECTORY)[0]
        vid_path = f"{TEST_VID_DIRECTORY}/{vid_name}"
        vid_source = VideoSource(vid_path).start()
        detection_source = DetectionSource("Test detection", vid_source)
        detection_source.start()

        self.assertTrue(detection_source.is_active)
        for _ in range(10):
            frame = detection_source.read((640, 360))
            self.assertIsInstance(frame, np.ndarray)

            fg_mask = detection_source.get_foreground_mask(frame)
            self.assertIsInstance(fg_mask, np.ndarray)

            contours = detection_source.find_contours(fg_mask)
            self.assertIsInstance(contours, list)

        detection_source.stop()

    def test_intruder_detector(self):
        vid_names = os.listdir(TEST_VID_DIRECTORY)[:3]
        vid_paths = [f"{TEST_VID_DIRECTORY}/{vid_name}" for vid_name in vid_names]
        vid_sources = [VideoSource(vid_path).start() for vid_path in vid_paths]
        detection_sources = [
            DetectionSource(vid_source.name, vid_source) for vid_source in vid_sources
        ]

        detector = IntruderDetector(
            detection_sources,
            f"{TEST_VIDEO_OUTPUT_DIRECTORY}/detection_intruder_test",
            num_frames_to_record=30,
        )
        detector.start_sources()
        self.assertFalse(detector.get_detection_status())
        for source in detection_sources:
            for _ in range(50):
                frame = detector.read_frame(source, (640, 360))
                self.assertIsInstance(frame, np.ndarray)
                detector.detect_motion_in_frame(frame, source)
                detector.check_for_intruders(frame, source, 5)
                sleep(1 / 15)

        detector.stop_detection()

        for source in detection_sources:
            source.stop()

        self.assertTrue(
            os.path.exists(f"{TEST_VIDEO_OUTPUT_DIRECTORY}/detection_intruder_test")
        )


if __name__ == "__main__":
    unittest.main()
