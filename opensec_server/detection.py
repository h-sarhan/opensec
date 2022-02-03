import os
from enum import Enum

import cv2 as cv
from dotenv import load_dotenv

import camera

load_dotenv()

TEST_VID_DIRECTORY = os.getenv("TEST_VID_DIRECTORY")


class SourceType(Enum):
    VIDEO = 1
    CAM = 2


class VideoBuffer:
    def __init__(self, buffer_len):
        pass

    def add_frame(self, frame):
        pass

    def write_to_video(self):
        pass

    def write_to_gif(self):
        pass

    def write_thumbnail(self):
        pass

    def _remove_frame(self):
        pass


class IntruderDetector:
    def __init__(self, source, get_detection_status, video_buffer_len=1800):
        self.source_type = None

        self._source = self._validate_source(source)
        self._get_detection_status = get_detection_status
        self._bg_subtractor = cv.createBackgroundSubtractorKNN()
        # self.bg_subtractor = cv.createBackgroundSubtractorMOG2()
        self._noise_kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3))
        # This will be a queue
        self._buffer = VideoBuffer(buffer_len=video_buffer_len)

    def _detect_motion(
        self,
        min_conseq_frames=10,
        max_motion_frames=120,
        frame_reduction_amount=50,
        display_cams=False,
    ):

        # This keeps track of the number of consecutive motion frames
        conseq_motion_frames = 0

        # This stores the frames of motion to send to the object detector
        motion_frames = []

        while self._get_detection_status():
            # This variable states whether the current frame is a motion frame or not
            is_motion_frame = False

            if self.source_type == SourceType.CAM:
                # Read a frame from the camera
                orig_frame = self._source.read(reduce_amount=frame_reduction_amount)
            else:
                # Read frame from video input if one is given
                ret, orig_frame = self._source.read()

                # This fixes a bug where OpenCV crashes when the video ends
                if not ret:
                    break

                # Resize the frame to improve performance
                orig_frame = cv.resize(
                    orig_frame, (960, 540), interpolation=cv.INTER_AREA
                )

            self._buffer.add_frame(orig_frame)

            # Keep a copy of the original frame
            frame = orig_frame.copy()

            contours = self._find_contours(
                frame, self._bg_subtractor, self._noise_kernel
            )

            is_motion_frame = self._detect_motion_frame(contours, display_cams, frame)

            if display_cams:
                if self.source_type == SourceType.CAM:
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
                cv.imshow("Motion Detection", frame)

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
                return motion_frames

            if self.source_type == SourceType.VIDEO:
                # Exit loop when video is over or by pressing q
                if not self._source.isOpened() or cv.waitKey(1) == ord("q"):
                    break

        if self.source_type == SourceType.VIDEO:
            self._source.release()

        if display_cams:
            # Close all windows
            cv.destroyAllWindows()

        return motion_frames

    def _find_contours(self, frame, bg_subtractor, noise_kernel):
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
        if isinstance(source, camera.Camera):
            self.source_type = SourceType.CAM
            return source

        if isinstance(source, str) and os.path.exists(source):
            self.source_type = SourceType.VIDEO
            return cv.VideoCapture(source)

        raise ValueError(
            "ERROR: `source` has to be a Camera object or an existing video"
        )


if __name__ == "__main__":
    test_videos = os.listdir(TEST_VID_DIRECTORY)
    for video in test_videos:
        detector = IntruderDetector(
            source=f"{TEST_VID_DIRECTORY}/{video}", get_detection_status=lambda: True
        )
        detector._detect_motion(display_cams=True)
