"""
TODO
"""

import cv2 as cv
from vidgear.gears.helper import reducer

NOISE_KERNEL = cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3))

# TODO: DOCUMENTATION
# TODO: WRITE TESTS
# TODO: INTEGRATE VIDEO RECORDING
# TODO: INTEGRATE OBJECT DETECTION QUEUE
# TODO: Implement detect in background method
class DetectionSource:
    """
    TODO
    """

    def __init__(self, name, source, recordings_path):
        self.name = name
        self.source = source
        self.recordings_path = recordings_path
        self.conseq_motion_frames = 0
        self.active = False

        self._bg_subtractor = cv.createBackgroundSubtractorKNN(detectShadows=False)
        self._cached_foreground_mask = None

    def start(self):
        """
        TODO
        """
        self.source.start()
        self.active = True

    def stop(self):
        """
        TODO
        """
        self.conseq_motion_frames = 0
        self.source.stop()
        self.active = False

    def read(self, reduce_amount=None):
        """
        TODO
        """
        frame = self.source.read()
        if frame is None:
            self.source.stop()
        elif reduce_amount:
            frame = reducer(
                frame,
                percentage=reduce_amount,
                interpolation=cv.INTER_NEAREST,
            )

        return frame

    def get_foreground_mask(self, frame, frame_count, fg_skip_frames):
        """
        TODO
        """
        if fg_skip_frames is None or frame_count % fg_skip_frames == 0:
            foreground_mask = self._bg_subtractor.apply(frame)

            denoised_foreground_mask = cv.morphologyEx(
                foreground_mask, cv.MORPH_OPEN, NOISE_KERNEL
            )
            dilated_foreground_mask = cv.dilate(
                denoised_foreground_mask, None, iterations=1
            )
            self._cached_foreground_mask = dilated_foreground_mask
            return dilated_foreground_mask

        return self._cached_foreground_mask

    def find_contours(self, foreground_mask, display_frame=None):
        """
        TODO
        """
        detection_mode = cv.RETR_EXTERNAL
        detection_method = cv.CHAIN_APPROX_SIMPLE

        contours, _ = cv.findContours(foreground_mask, detection_mode, detection_method)
        filtered_contours = self._filter_contours(contours, display_frame)
        return filtered_contours

    @staticmethod
    def _filter_contours(contours, display_frame):
        """
        TODO
        """
        filtered_contours = []
        # Loop through the contours if there are any
        for contour in contours:
            # Remove small instances of detected motion
            # this will mostly be lighting changes
            if cv.contourArea(contour) < 3000:
                continue

            filtered_contours.append(contour)

            # Performance optimization when there is no need to display a frame
            if display_frame is None:
                break

            DetectionSource._draw_bounding_boxes(display_frame, contour)
        return filtered_contours

    @staticmethod
    def _draw_bounding_boxes(display_frame, contour):
        # Get the bounding rectangle from the contour
        x_coord, y_coord, width, height = cv.boundingRect(contour)

        # Draw the bounding box
        cv.rectangle(
            display_frame,
            (x_coord, y_coord),
            (x_coord + width, y_coord + height),
            (0, 255, 0),
            1,
        )


class IntruderDetector:
    """
    TODO
    """

    def __init__(
        self,
        detection_sources,
        frame_reduction_amount=50,
        num_frames_to_record=300,
        display_frame=False,
    ):
        self.detection_sources = detection_sources
        self.reduce_amount = frame_reduction_amount

        self._display_frame = display_frame
        self._num_frames_to_record = num_frames_to_record

        self._detection_status = False

    def start_sources(self):
        """
        TODO
        """
        for source in self.detection_sources:
            source.start()

    def get_detection_status(self):
        """
        TODO
        """
        all_sources_inactive = all(
            not source.active for source in self.detection_sources
        )
        if not self._detection_status or all_sources_inactive:
            return False
        return True

    def read_frame(self, source):
        """
        TODO
        """
        frame = source.read(reduce_amount=self.reduce_amount)

        if frame is None and source.active:
            source.stop()
            if self._display_frame:
                cv.destroyWindow(f"({source.name}) Motion Detection")

        return frame

    def show_frame(self, frame, source):
        """
        TODO
        """
        if self._display_frame:
            # Show the resized frame with bounding boxes around intruders (if any)
            cv.imshow(f"({source.name}) Motion Detection", frame)

    @staticmethod
    def update_conseq_frames(source, contours):
        """
        TODO
        """
        if IntruderDetector.is_motion_frame(contours):
            source.conseq_motion_frames += 1
        else:
            source.conseq_motion_frames = 0

    def detect(
        self, fg_mask_skip_frames=4, source_skip_frames=False, min_conseq_frames=15
    ):
        """
        TODO
        """
        self._detection_status = True

        frame_count = 0
        self.start_sources()

        while self.get_detection_status():

            for source in self.detection_sources:
                if source_skip_frames and frame_count % 2 == 1:
                    break

                frame = self.read_frame(source)

                if frame is None:
                    continue

                self.detect_motion_in_frame(
                    frame, source, frame_count, fg_mask_skip_frames
                )

                self.check_for_intruders(source, min_conseq_frames)

            frame_count += 1

            if source_skip_frames and frame_count % 2 == 1:
                continue

            # Exit loop by pressing q
            if cv.waitKey(15) == ord("q"):
                break

        self.stop_detection()

        if self._display_frame:
            # Close all windows
            cv.destroyAllWindows()

    def detect_motion_in_frame(self, frame, source, frame_count, fg_mask_skip_frames):
        """
        TODO
        """
        foreground_mask = source.get_foreground_mask(
            frame, frame_count, fg_mask_skip_frames
        )

        contours = source.find_contours(foreground_mask, display_frame=frame)

        self.show_frame(frame, source)

        if frame_count % fg_mask_skip_frames == 0:
            self.update_conseq_frames(source, contours)

    @staticmethod
    def is_motion_frame(contours):
        """
        TODO
        """
        # If no contours have been found then this is not a motion frame
        return contours is not None and len(contours) != 0

    @staticmethod
    def check_for_intruders(source, min_conseq_frames):
        """
        TODO
        """
        if source.conseq_motion_frames >= min_conseq_frames:
            print(f"intruder detected at {source.name}")
            # source.start_recording()

    def record_intruder(self):
        """
        TODO
        """

    def stop_detection(self):
        """
        TODO
        """
        for source in self.detection_sources:
            source.stop()

        self._detection_status = False

    def detect_in_background(self):
        """
        TODO
        """


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
