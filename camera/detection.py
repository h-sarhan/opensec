"""
TODO
"""

import cv2 as cv
from vidgear.gears.helper import reducer

noise_kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3))

# TODO: Refactor DetectionSource functions return variables rather than store state
class DetectionSource:
    """
    TODO
    """

    def __init__(self, name, source, recordings_path):
        self.name = name
        self.source = source
        self.recordings_path = recordings_path
        self.current_frame = None
        self.conseq_motion_frames = 0
        self.active = False

        self._fg_mask = None
        self._contours = []
        self._bg_subtractor = cv.createBackgroundSubtractorKNN(detectShadows=False)

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
        self.current_frame = None
        self.conseq_motion_frames = 0
        self.source.stop()
        self.active = False

    def is_motion_frame(self):
        """
        TODO
        """
        # If no contours have been found then this is not a motion frame
        return self._contours is not None or len(self._contours) == 0

    def update_frame(self, reduce_amount=None):
        """
        TODO
        """
        frame = self.source.read()
        if frame is None:
            self.source.stop()
            self.current_frame = None
        elif reduce_amount:
            frame = reducer(
                frame,
                percentage=reduce_amount,
                interpolation=cv.INTER_NEAREST,
            )

        self.current_frame = frame

    def update_fg_mask(self):
        """
        TODO
        """
        self._fg_mask = self._bg_subtractor.apply(self.current_frame)

        self._fg_mask = cv.morphologyEx(self._fg_mask, cv.MORPH_OPEN, noise_kernel)
        self._fg_mask = cv.dilate(self._fg_mask, None, iterations=3)

    def find_contours(self, draw_bounding_boxes=False):
        """
        TODO
        """
        contours = cv.findContours(
            self._fg_mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE
        )[0]
        self._contours = self._filter_contours(contours, draw_bounding_boxes)

    def _filter_contours(self, contours, draw_bounding_boxes):
        """
        TODO
        """
        filtered_contours = []
        # Loop through the contours if there are any
        for contour in contours:
            # Remove small instances of detected motion
            # This will mostly be lighting changes
            if cv.contourArea(contour) < 2500:
                continue

            filtered_contours.append(contour)

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
        return filtered_contours


class IntruderDetector:
    """
    TODO
    """

    def __init__(
        self,
        detection_sources,
        min_conseq_frames=30,
        frame_reduction_amount=50,
        num_frames_to_record=300,
    ):
        self.detection_sources = detection_sources
        self.num_sources = len(self.detection_sources)
        self.reduce_amount = frame_reduction_amount
        # self.current_frames = [None for _ in range(self.num_sources)]
        # self.buffer = VideoBuffer(self.recordings_output_path)

        self._min_conseq_frames = min_conseq_frames
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

    def start_detection(
        self, display_frame=False, bg_subtraction_skip_frames=4, skip_frames=False
    ):
        """
        TODO
        """
        self._detection_status = True

        frame_count = 0
        self.start_sources()

        while self.get_detection_status():

            for source in self.detection_sources:
                if skip_frames and frame_count % 2 != 0:
                    break

                source.update_frame(reduce_amount=self.reduce_amount)

                if source.current_frame is None:
                    if source.active:
                        source.stop()
                        if display_frame:
                            cv.destroyWindow(f"({source.name}) Motion Detection")
                    continue

                if frame_count % bg_subtraction_skip_frames == 0:
                    source.update_fg_mask()

                source.find_contours(draw_bounding_boxes=display_frame)

                if display_frame:
                    # Show the resized frame with bounding boxes around intruders (if any)
                    cv.imshow(f"({source.name}) Motion Detection", source.current_frame)

                # Increment or reset conseq_motion_frames if the current frame is a motion frame or not
                if source.is_motion_frame():
                    source.conseq_motion_frames += 1
                else:
                    source.conseq_motion_frames = 0

                if source.conseq_motion_frames >= self._min_conseq_frames:
                    print(f"intruder detected at {source.name}")
                    # TODO START RECORDING VIDEO
                    # source.start_recording()

            # Exit loop by pressing q
            if cv.waitKey(10) == ord("q"):
                break

            frame_count += 1
        # Release the video object
        self.stop_detection()

        if display_frame:
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
        # self.buffer.merge_parts(f"{self.name}-recording")
        # self.buffer.stop()
        for source in self.detection_sources:
            source.stop()

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
