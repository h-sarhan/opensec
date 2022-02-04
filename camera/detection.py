"""
TODO
"""
import os
from enum import Enum
from threading import Thread

import config
import cv2 as cv
from vidgear.gears.helper import reducer

from .camera import Camera


class SourceType(Enum):
    """
    TODO
    """

    VIDEO_DIR = 1
    CAM_HUB = 2


class VideoBuffer:
    """
    TODO
    """

    def __init__(self, buffer_len):
        """
        TODO
        """
        pass

    def add_frame(self, frame):
        """
        TODO
        """
        pass

    def write_to_video(self):
        """
        TODO
        """
        pass

    def write_to_gif(self):
        """
        TODO
        """
        pass

    def write_thumbnail(self):
        """
        TODO
        """
        pass

    def _remove_frame(self):
        """
        TODO
        """
        pass


# TODO: CHANGE TO ACCEPT CAMERA HUB INSTEAD OF A SINGLE CAMERA
class IntruderDetector:
    """
    TODO
    """

    def __init__(self, source, video_buffer_len=1800):
        """
        TODO
        """
        self.source_type = None

        self._source = self._validate_source(source)
        self._detection_status = False
        self._bg_subtractor = cv.createBackgroundSubtractorKNN()
        # self.bg_subtractor = cv.createBackgroundSubtractorMOG2()
        self._noise_kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3))
        self._buffer = VideoBuffer(buffer_len=video_buffer_len)
        self._detection_thread = None

    def start_detection(self, display_cam=False):
        """
        TODO
        """
        self._detection_status = True
        self._detection_thread = Thread(
            target=self._detect_motion, kwargs={"display_cam": display_cam}
        )
        self._detection_thread.start()

    def stop_detection(self):
        """
        TODO
        """
        self._detection_status = False
        self._detection_thread.join()
        # cv.destroyAllWindows()

    def _get_detection_status(self):
        """
        TODO
        """
        return self._detection_status

    def _detect_motion(
        self,
        min_conseq_frames=10,
        max_motion_frames=120,
        frame_reduction_amount=50,
        display_cam=False,
    ):
        """
        TODO
        """

        # This keeps track of the number of consecutive motion frames
        conseq_motion_frames = 0

        # This stores the frames of motion to send to the object detector
        motion_frames = []

        while True:
            # This variable states whether the current frame is a motion frame or not
            is_motion_frame = False

            if self.source_type == SourceType.CAM_HUB:
                # Read a frame from the camera
                orig_frame = self._source.read(reduce_amount=frame_reduction_amount)
            else:
                # Read frame from video input if one is given
                ret, orig_frame = self._source.read()

                # This fixes a bug where OpenCV crashes when the video ends
                if not ret:
                    break

                # Resize the frame to improve performance
                orig_frame = reducer(orig_frame, percentage=frame_reduction_amount)

            self._buffer.add_frame(orig_frame)

            # Keep a copy of the original frame
            frame = orig_frame.copy()

            contours = self._find_contours(
                frame, self._bg_subtractor, self._noise_kernel
            )

            is_motion_frame = self._detect_motion_frame(contours, display_cam, frame)

            if display_cam:
                if self.source_type == SourceType.CAM_HUB:
                    # Display the camera name on the frame
                    cv.putText(
                        img=frame,
                        text=f"{self._source.name} (Motion Detection)",
                        org=(50, 50),
                        fontFace=cv.FONT_HERSHEY_DUPLEX,
                        fontScale=1,
                        color=(0, 0, 255),
                        thickness=1,
                    )

                # Show the resized frame with bounding boxes around intruders
                cv.imshow(f"{self._source} Motion Detection", frame)

            # Increment or reset conseq_motion_frames if the current frame is a motion frame or not
            if is_motion_frame:
                conseq_motion_frames += 1
            else:
                conseq_motion_frames = 0

            # Store the current frame if it is a motion frame
            # and if the number of consecutive motion frames is sufficient
            if (
                conseq_motion_frames >= min_conseq_frames
                and len(motion_frames) < max_motion_frames
            ):
                motion_frames.append(orig_frame)

            elif len(motion_frames) >= max_motion_frames:
                break
                # return motion_frames

            # if self.source_type == SourceType.VIDEO:
            # Exit loop when video is over or by pressing q
            if (
                cv.waitKey(1) == ord("q")
                or not self._source.isOpened()
                or not self._get_detection_status()
            ):
                break

        # return motion_frames

    def _find_contours(self, frame, bg_subtractor, noise_kernel):
        """
        TODO
        """
        # Update the background model with the current frame using our background subtractor
        fg_mask = bg_subtractor.apply(frame)

        # Apply some morphological transformations to remove noise from the foreground mask
        fg_mask = cv.morphologyEx(fg_mask, cv.MORPH_OPEN, noise_kernel)

        # The foreground mask includes shadow information that we are not interested in
        # The below line of code removes that information from the frame
        fg_mask = cv.threshold(fg_mask, 200, 255, cv.THRESH_BINARY)[1]

        # We can make the white lines thicker to make it easier to find contours in the frame
        fg_mask = cv.dilate(fg_mask, None, iterations=3)

        # This will find the contours in the foreground mask
        # The presence of contours tells us whether or not this frame is a motion frame
        contours = cv.findContours(fg_mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)[0]

        return contours

    def _detect_motion_frame(self, contours, display_cams=None, frame=None):
        """
        TODO
        """
        is_motion_frame = False

        # If no contours have been found then this is not a motion frame
        if not contours:
            return is_motion_frame

        # Loop through the contours if there are any
        for contour in contours:
            # Remove small instances of detected motion
            # This will mostly be lighting changes
            if cv.contourArea(contour) < 1500:
                continue

            is_motion_frame = True

            # Optionally display the bounding rectangles
            if display_cams:
                # Get the bounding rectangle from the contours
                x_coord, y_coord, width, height = cv.boundingRect(contour)

                # Draw the rectangle
                cv.rectangle(
                    img=frame,
                    pt1=(x_coord, y_coord),
                    pt2=(x_coord + width, y_coord + height),
                    color=(0, 255, 0),
                    thickness=1,
                )
            else:
                return is_motion_frame

        return is_motion_frame

    def _validate_source(self, source):
        """
        TODO
        """
        if isinstance(source, Camera):
            self.source_type = SourceType.CAM_HUB
            return source

        if isinstance(source, str) and os.path.exists(source):
            self.source_type = SourceType.VIDEO_DIR
            return cv.VideoCapture(source)

        raise ValueError("ERROR: `source` has to be a Camera Hub or a video directory")
