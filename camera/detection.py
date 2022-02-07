"""
TODO
"""


from collections import deque

import cv2 as cv
from vidgear.gears.helper import reducer

from .camera import VideoBuffer


class IntruderDetector:
    """
    TODO
    """

    def __init__(self, name, source, max_motion_frames=100, min_conseq_frames=15):
        self.name = name
        self.source = source
        self.buffer = VideoBuffer(buffer_len=300)
        self.motion_frames = deque(maxlen=max_motion_frames)
        self.current_frame = None
        self.is_motion_frame = False

        self._fg_mask = None
        self._contours = []
        self._max_motion_frames = max_motion_frames
        self._min_conseq_frames = min_conseq_frames

        self._bg_subtractor = cv.createBackgroundSubtractorKNN(detectShadows=False)
        self._noise_kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3))
        self._conseq_motion_frames = 0

        self._detection_status = False

    def read(self, reduce_amount=None):
        """
        TODO
        """
        frame = self.source.read()
        if frame is None:
            self.stop_detection()
            return
        if reduce_amount and frame is not None:
            frame = reducer(
                frame,
                percentage=reduce_amount,
                interpolation=cv.INTER_NEAREST,
            )
        self.current_frame = frame
        # self.buffer.add_frame(self.current_frame)

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
        self._fg_mask = cv.dilate(self._fg_mask, None, iterations=2)

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
        self.source.start()
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

            # TODO: DO SOMETHING ELSE WITH HERE
            if self._conseq_motion_frames >= self._min_conseq_frames:
                self.motion_frames.append(self.current_frame)

            frame_count += 1

            # Exit loop by pressing q
            if cv.waitKey(5) == ord("q"):
                break

        # Release the video object
        self.stop_detection()

        # Close all windows
        cv.destroyAllWindows()

    def log_intruder(self):
        """
        TODO
        """

    def record_intruder(self):
        """
        TODO
        """

    def stop_detection(self):
        """
        TODO
        """
        self.source.stop()
        self._detection_status = False


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
