import os
import unittest

import cv2 as cv
import numpy as np
from camera import Camera, CameraHub, IntruderDetector, VideoBuffer
from config import TEST_CAM, TEST_VID_DIRECTORY, TEST_VIDEO_OUTPUT_DIRECTORY


# TODO: Refactor VideoBuffer tests and comment if necessary
class TestBuffer(unittest.TestCase):
    def setUp(self):
        self.test_vid_dir = TEST_VID_DIRECTORY
        self.test_video_output_dir = TEST_VIDEO_OUTPUT_DIRECTORY
        self.test_vids = [
            os.path.join(self.test_vid_dir, vid)
            for vid in os.listdir(self.test_vid_dir)
        ]
        self.test_frames = [TestBuffer.read_frames(video) for video in self.test_vids]

    @staticmethod
    def read_frames(video):
        print(video)
        frames = []
        video_cap = cv.VideoCapture(video)
        while video_cap.isOpened():
            ret, frame = video_cap.read()
            if not ret:
                break
            frames.append(frame)
        return frames

    def clear_video_output_directory(self):
        if os.path.exists(self.test_video_output_dir):
            for file in os.listdir(self.test_video_output_dir):
                os.unlink(f"{self.test_video_output_dir}/{file}")

    def test_buffer_len(self):
        # Create video buffers with a length of 5 seconds @ 30fps
        buffer_len = 5
        fps = 30

        for frames in self.test_frames:
            vid_buffer = VideoBuffer(buffer_len=buffer_len, fps=fps)

            # Add frames to video buffer and check length
            for frame_idx, frame in enumerate(frames):
                vid_buffer.add_frame(frame)
                if frame_idx < buffer_len * fps:
                    self.assertEqual(len(vid_buffer), frame_idx + 1)
                elif frame_idx >= buffer_len * fps:
                    self.assertEqual(len(vid_buffer), buffer_len * fps)

    def test_write_to_video(self):
        self.clear_video_output_directory()

        buffer_len = 5
        fps = 30

        buffers = []
        for frames in self.test_frames:
            vid_buffer = VideoBuffer(buffer_len=buffer_len, fps=fps)

            # Add frames to video buffer
            for frame in frames:
                vid_buffer.add_frame(frame)
            buffers.append(vid_buffer)

        for idx, buffer in enumerate(buffers):
            path = f"{self.test_video_output_dir}/test_video_out_{idx+1}.mp4"
            buffer.write_to_video(path)
            video_capture = cv.VideoCapture(path)
            self.assertEqual(
                video_capture.get(cv.CAP_PROP_FRAME_COUNT), buffer_len * fps
            )
            video_capture.release()

    def test_write_to_gif(self):
        self.clear_video_output_directory()

        buffer_len = 5
        fps = 30

        buffers = []
        for frames in self.test_frames:
            vid_buffer = VideoBuffer(buffer_len=buffer_len, fps=fps)

            # Add frames to video buffer
            for frame in frames:
                vid_buffer.add_frame(frame)
            buffers.append(vid_buffer)

        for idx, buffer in enumerate(buffers):
            path = f"{self.test_video_output_dir}/test_gif_out_{idx+1}.gif"
            buffer.write_to_gif(path)

            self.assertTrue(os.path.exists(path))

    def test_write_thumbnail(self):
        self.clear_video_output_directory()

        buffer_len = 5
        fps = 30

        buffers = []
        for frames in self.test_frames:
            vid_buffer = VideoBuffer(buffer_len=buffer_len, fps=fps)

            # Add frames to video buffer
            for frame in frames:
                vid_buffer.add_frame(frame)
            buffers.append(vid_buffer)

        for idx, buffer in enumerate(buffers):
            path_a = f"{self.test_video_output_dir}/test_thumb_out_{idx+1}_a.jpg"
            path_b = f"{self.test_video_output_dir}/test_thumb_out_{idx+1}_b.jpg"
            buffer.write_thumbnail(path_a)
            buffer.write_thumbnail(path_b)

            img_a = cv.imread(path_a)
            img_b = cv.imread(path_b)

            self.assertIsNotNone(img_a)
            self.assertIsNotNone(img_b)

            # Use a numpy method to see if the two images are equal
            self.assertFalse(np.array_equal(img_a, img_b))


class TestIntruderDetector(unittest.TestCase):
    def test_read_frames_from_cam_hub(self):
        cam_hub = CameraHub()
        cam_hub.add_cameras([Camera(f"test-{idx+1}", TEST_CAM) for idx in range(4)])
        detector = IntruderDetector(source=cam_hub)
        frames = detector._read_frames()
        frames_reduced = detector._read_frames(reduce_amount=50)

        self.assertEqual(len(frames), 4)

        for frame, frame_reduced in zip(frames, frames_reduced):
            self.assertIsNotNone(frame)
            self.assertIsInstance(frame, np.ndarray)
            self.assertTrue(frame.ndim, 3)

            self.assertIsNotNone(frame_reduced)
            self.assertIsInstance(frame_reduced, np.ndarray)
            self.assertTrue(frame_reduced.ndim, 3)

            width_1, height_1, color_channels_1 = frame.shape
            width_2, height_2, color_channels_2 = frame_reduced.shape

            self.assertLess(width_2, width_1)
            self.assertLess(height_2, height_1)
            self.assertEqual(color_channels_1, color_channels_2)

    def test_read_frames_from_video_directory(self):
        detector = IntruderDetector(source=TEST_VID_DIRECTORY)
        frames = detector._read_frames()
        frames_reduced = detector._read_frames(reduce_amount=50)

        self.assertEqual(len(frames), len(os.listdir(TEST_VID_DIRECTORY)))

        for frame, frame_reduced in zip(frames, frames_reduced):
            self.assertIsNotNone(frame)
            self.assertIsInstance(frame, np.ndarray)
            self.assertTrue(frame.ndim, 3)

            self.assertIsNotNone(frame_reduced)
            self.assertIsInstance(frame_reduced, np.ndarray)
            self.assertTrue(frame_reduced.ndim, 3)

            width_1, height_1, color_channels_1 = frame.shape
            width_2, height_2, color_channels_2 = frame_reduced.shape

            self.assertLess(width_2, width_1)
            self.assertLess(height_2, height_1)
            self.assertEqual(color_channels_1, color_channels_2)

    @unittest.skip("Not implemented")
    def test_something(self):
        pass


if __name__ == "__main__":
    unittest.main()
