"""
TODO
"""


import time

import cv2 as cv

from .camera import VideoRecorder

NOISE_KERNEL = cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3))

# TODO: INTEGRATE OBJECT DETECTION QUEUE
# TODO: Implement detect in background method
# TODO: DOCUMENTATION
# TODO: WRITE TESTS
class DetectionSource:
    """
    TODO
    """

    def __init__(self, name, source):
        self.name = name
        self.source = source
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
        if self.active:
            self.conseq_motion_frames = 0
            self.source.stop()
            self.active = False

    def read(self):
        """
        TODO
        """
        frame = self.source.read()
        if frame is None:
            self.stop()
        return frame

    def get_foreground_mask(self, frame):
        """
        TODO
        """
        foreground_mask = self._bg_subtractor.apply(frame)

        denoised_foreground_mask = cv.morphologyEx(
            foreground_mask, cv.MORPH_OPEN, NOISE_KERNEL
        )
        dilated_foreground_mask = cv.dilate(
            denoised_foreground_mask, None, iterations=1
        )
        self._cached_foreground_mask = dilated_foreground_mask
        return dilated_foreground_mask

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
        recording_directory,
        num_frames_to_record=300,
        display_frame=False,
    ):
        self.detection_sources = detection_sources

        self._display_frame = display_frame
        self._max_frames_to_record = num_frames_to_record

        self._detection_status = False
        self._recorder = VideoRecorder(
            self.detection_sources, recording_directory, num_frames_to_record
        )

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

    def read_frame(self, source: DetectionSource):
        """
        TODO
        """
        frame = source.read()

        if frame is None:
            source.stop()

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

    def detect(self, min_conseq_frames=15):
        """
        TODO
        """
        self._detection_status = True

        frame_count = 0
        self.start_sources()

        while self.get_detection_status():

            for source in self.detection_sources:
                if frame_count % 2 == 1:
                    time.sleep(0.02)
                    break

                frame = self.read_frame(source)

                if frame is None:
                    continue

                self.detect_motion_in_frame(frame, source)

                self.check_for_intruders(frame, source, min_conseq_frames)

            frame_count += 1

            # Exit loop by pressing q
            if cv.waitKey(20) == ord("q"):
                break

        self.stop_detection()

        if self._display_frame:
            # Close all windows
            cv.destroyAllWindows()

    def detect_motion_in_frame(self, frame, source):
        """
        TODO
        """
        foreground_mask = source.get_foreground_mask(frame)

        contours = source.find_contours(foreground_mask, display_frame=frame)

        self.show_frame(frame, source)

        self.update_conseq_frames(source, contours)

    @staticmethod
    def is_motion_frame(contours):
        """
        TODO
        """
        # If no contours have been found then this is not a motion frame
        return contours is not None and len(contours) != 0

    def check_for_intruders(self, frame, source, min_conseq_frames):
        """
        TODO
        """
        if source.conseq_motion_frames >= min_conseq_frames:
            print(f"intruder detected at {source.name}")
            self.record_frame(frame, source)

    def record_frame(self, frame, source):
        """
        TODO
        """
        num_frames_recorded = self._recorder.get_num_frames_recorded(source)
        if num_frames_recorded <= self._max_frames_to_record:
            self._recorder.add_frame(frame, source)
        else:
            self._save_recordings(source)

    def stop_detection(self):
        """
        TODO
        """
        for source in self.detection_sources:
            source.stop()

        self._detection_status = False

        for source in self.detection_sources:

            num_frames_recorded = self._recorder.get_num_frames_recorded(source)
            if num_frames_recorded >= 50:
                self._save_recordings(source)

    def _save_recordings(self, source):
        self._recorder.save(source)


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
