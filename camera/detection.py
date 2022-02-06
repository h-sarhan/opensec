"""
TODO
"""
# import os

# import config
import os
from abc import abstractmethod

import cv2 as cv
from vidgear.gears import VideoGear

# from vidgear.gears import VideoGear
from vidgear.gears.helper import reducer

from .camera import Camera, VideoBuffer

# from enum import Enum
# from threading import Thread


class IntruderDetection:
    """
    TODO
    """

    def __init__(self, max_motion_frames=100, min_conseq_frames=15, fps=30):
        self.name = "base"
        self.buffer = VideoBuffer(fps=fps)
        self.motion_frames = []
        self.original_frame = None
        self.current_frame = None
        self.is_motion_frame = False

        self._fg_mask = None
        self._contours = []
        self._max_motion_frames = max_motion_frames
        self._min_conseq_frames = min_conseq_frames

        # self._bg_subtractor = cv.createBackgroundSubtractorMOG2(
        #     history=200, detectShadows=False
        # )
        self._bg_subtractor = cv.createBackgroundSubtractorKNN(
            history=200, detectShadows=False
        )
        self._noise_kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3))
        self._conseq_motion_frames = 0

        self._detection_status = False

    @abstractmethod
    def read(self, reduce_amount=55):
        """
        TODO
        """
        pass

    def get_detection_status(self):
        """
        TODO
        """
        return self._detection_status

    def update_fg_mask(self):
        """
        TODO
        """
        self._fg_mask = self._bg_subtractor.apply(self.current_frame)

        self._fg_mask = cv.morphologyEx(
            self._fg_mask, cv.MORPH_OPEN, self._noise_kernel
        )
        self._fg_mask = cv.dilate(self._fg_mask, None, iterations=3)

    def find_contours(self):
        """
        TODO
        """
        self._contours = cv.findContours(
            self._fg_mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE
        )[0]

    def filter_contours(self, draw_bounding_boxes=False):
        """
        TODO
        """
        filtered_contours = []
        # Loop through the contours if there are any
        for contour in self._contours:
            # Remove small instances of detected motion
            # This will mostly be lighting changes
            if cv.contourArea(contour) < 2000:
                continue

            filtered_contours.append(contour)

            # TODO: This could be a function e.g. self.draw_bounding_boxes()
            if draw_bounding_boxes:
                # Get the bounding rectangle from the contour
                x_coord, y_coord, width, height = cv.boundingRect(contour)

                # Draw the bounding box
                cv.rectangle(
                    self.current_frame,
                    (x_coord, y_coord),
                    (x_coord + width, y_coord + height),
                    (0, 255, 0),
                    1,
                )
        self._contours = filtered_contours

    def start_detection(
        self, reduce_amount=None, display_frame=False, bg_subtraction_skip_frames=4
    ):
        """
        TODO
        """
        self._detection_status = True
        frame_count = 0
        while self.get_detection_status():

            # This variable states whether the current frame is a motion frame or not
            self.is_motion_frame = False

            self.read(reduce_amount=reduce_amount)

            if self.current_frame is None:
                break

            if frame_count % bg_subtraction_skip_frames == 0:
                self.update_fg_mask()

            self.find_contours()
            self.filter_contours(draw_bounding_boxes=display_frame)

            # If no contours have been found then this is not a motion frame
            if not self._contours:
                self.is_motion_frame = False
            else:
                self.is_motion_frame = True

            if display_frame:
                # Show the resized frame with bounding boxes around intruders (if any)
                cv.imshow(f"({self.name}) Motion Detection", self.current_frame)

            # Increment or reset conseq_motion_frames if the current frame is a motion frame or not
            if self.is_motion_frame:
                self._conseq_motion_frames += 1
            else:
                self._conseq_motion_frames = 0

            # TODO: DO SOMETHING ELSE WITH THIS
            # Store the current frame if it is a motion frame
            # and if the number of consecutive motion frames is sufficient
            if (
                self._conseq_motion_frames >= self._min_conseq_frames
                and len(self.motion_frames) < self._max_motion_frames
            ):
                self.motion_frames.append(self.current_frame)
                print("INTRUDER DETECTED")

            frame_count += 1

            # Exit loop by pressing q
            if cv.waitKey(5) == ord("q"):
                break

        # Release the video object
        self.stop_detection()

        # Close all windows
        cv.destroyAllWindows()

    def record_intruder(self):
        """
        TODO
        """
        pass

    def stop_detection(self):
        """
        TODO
        """
        self._detection_status = False


class IntruderDetectionMultiCamera(IntruderDetection):
    pass


class IntruderDetectionVideoDirectory(IntruderDetection):
    pass


class IntruderDetectionCamera(IntruderDetection):
    """
    TODO
    """

    def __init__(
        self, name, source, max_motion_frames=100, min_conseq_frames=15, fps=30
    ):
        super().__init__(max_motion_frames, min_conseq_frames, fps)
        self.name = name
        self.source = source

    def read(self, reduce_amount=None):
        frame = self.source.read(reduce_amount)
        if frame is None:
            self.stop_detection()
            return

        self.original_frame = frame
        self.current_frame = self.original_frame.copy()
        self.buffer.add_frame(self.current_frame)


class IntruderDetectionVideoCapture(IntruderDetection):
    """
    TODO
    """

    def __init__(
        self, name, source, max_motion_frames=100, min_conseq_frames=15, fps=30
    ):
        super().__init__(max_motion_frames, min_conseq_frames, fps)
        self.name = name
        self.source = VideoGear(source=source).start()

    def read(self, reduce_amount=None):
        frame = self.source.read()
        if frame is None:
            self.stop_detection()
            return
        self.original_frame = frame
        if reduce_amount and self.original_frame is not None:
            self.original_frame = reducer(self.original_frame, percentage=reduce_amount)
        self.current_frame = self.original_frame.copy()
        self.buffer.add_frame(self.current_frame)

    def stop_detection(self):
        self._detection_status = False
        self.source.stop()


class Intruder:
    """
    TODO
    """

    def __init__(self, frames):
        """
        TODO
        """
        self.camera_name = None
        self.time_detected = None
        self.intruder_type = None

        self._frames = frames

    def analyze(self):
        """
        TODO
        """
