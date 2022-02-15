"""
TODO
"""


import os
import random
import time
from datetime import datetime
from threading import Thread

import config
import cv2 as cv
import imageio
from vidgear.gears import WriteGear
from vidgear.gears.helper import reducer

NOISE_KERNEL = cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3))

# TODO: Add object detection
# TODO: Clean dependencies
# TODO: DOCUMENTATION
# TODO: WRITE TESTS


class IntuderRecorder:
    """
    TODO
    """

    def __init__(self, detection_sources, recording_directory, max_stored_frames=80):
        self.sources = detection_sources
        self.recordings_directory = recording_directory
        self.max_stored_frames = max_stored_frames

        self._video_writers = {}
        self._start_times = {}
        self._stored_frames = {}
        self._setup()

    def get_num_frames_recorded(self, source):
        """
        TODO
        """
        return len(self._stored_frames[source.name])

    def add_frame(self, frame, source):
        """
        TODO
        """
        if self._start_times[source.name] is None:
            current_date_time = datetime.now().strftime("%Y_%m_%d %Hh %Mm %Ss")
            self._start_times[source.name] = current_date_time

        if frame is not None:
            stored_frames = self._stored_frames[source.name]
            if len(stored_frames) < self.max_stored_frames:
                stored_frames.append(frame)

            writer = self._video_writers[source.name]
            writer.write(frame)

    def save(self, source, gif=True, thumb=True):
        """
        TODO
        """
        writer = self._video_writers[source.name]
        writer.close()
        video_path = self._rename_video(source)
        if source.is_active:
            print("Creating video writer")
            output_params = {"-fourcc": "mp4v", "-fps": config.FPS // 2}
            self._video_writers[source.name] = WriteGear(
                f"{self.recordings_directory}/videos/{source.name}/intruder.mp4",
                compression_mode=False,
                logging=False,
                **output_params,
            )

        paths = [video_path]
        if thumb:
            print("Creating thumbnail")
            thumb_path = self._save_thumb(source)
            paths.append(thumb_path)
        if gif:
            print("Creating GIF")
            gif_path = self._save_gif(source)
            paths.append(gif_path)

        self._start_times[source.name] = None
        self._stored_frames[source.name] = []
        return paths

    def _rename_video(self, source):
        """
        TODO
        """
        videos_directory = f"{self.recordings_directory}/videos"
        base_name = f"{videos_directory}/{source.name}"
        old_file_path = f"{base_name}/intruder.mp4"
        new_file_path = f"{base_name}/{self._start_times[source.name]}.mp4"

        rename_tries = 0
        while not os.path.exists(old_file_path):
            if rename_tries == 3:
                return None
            time.sleep(2)
            rename_tries += 1
        os.rename(old_file_path, new_file_path)
        return new_file_path

    def _save_thumb(self, source):
        """
        TODO
        """
        thumbnails_directory = f"{self.recordings_directory}/thumbnails"
        base_dir = f"{thumbnails_directory}/{source.name}"
        thumb_name = self._start_times[source.name]
        thumb_path = f"{base_dir}/{thumb_name}.jpg"
        stored_frames = self._stored_frames[source.name]
        if stored_frames is not None and len(stored_frames) != 0:
            thumb_frame = random.choice(stored_frames)
            if thumb_frame is not None:
                cv.imwrite(thumb_path, thumb_frame)
                return thumb_path
        return None

    def _save_gif(self, source):
        """
        TODO
        """
        gif_frames = []
        stored_frames = self._stored_frames[source.name]
        for frame_idx, frame in enumerate(stored_frames):
            if frame_idx % 4 != 0:
                continue
            rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            reduced_frame = reducer(
                rgb_frame, percentage=40, interpolation=cv.INTER_NEAREST
            )
            gif_frames.append(reduced_frame)

        gifs_directory = f"{self.recordings_directory}/gifs"
        base_dir = f"{gifs_directory}/{source.name}"
        gif_name = self._start_times[source.name]
        gif_path = f"{base_dir}/{gif_name}.gif"
        if gif_frames:
            imageio.mimsave(
                gif_path, gif_frames, fps=5, subrectangles=True, palettesize=64
            )

            return gif_path

        return None

    def _setup(self):
        """
        TODO
        """
        self._make_paths()
        self._make_video_writers()
        for source in self.sources:
            self._start_times[source.name] = None
            self._stored_frames[source.name] = []

    def _make_video_writers(self):
        for source in self.sources:
            output_params = {"-fourcc": "mp4v", "-fps": config.FPS // 2}
            self._video_writers[source.name] = WriteGear(
                f"{self.recordings_directory}/videos/{source.name}/intruder.mp4",
                compression_mode=False,
                logging=False,
                **output_params,
            )

    def _make_paths(self):
        if not os.path.exists(self.recordings_directory):
            os.mkdir(self.recordings_directory)

        directories = [
            f"{self.recordings_directory}/videos",
            f"{self.recordings_directory}/thumbnails",
            f"{self.recordings_directory}/gifs",
        ]
        for directory in directories:
            if not os.path.exists(directory):
                os.mkdir(directory)

            for source in self.sources:
                if not os.path.exists(f"{directory}/{source.name}"):
                    os.mkdir(f"{directory}/{source.name}")


class DetectionSource:
    """
    TODO
    """

    def __init__(self, name, source):
        self.name = name
        self.source = source
        self.conseq_motion_frames = 0

        self._bg_subtractor = cv.bgsegm.createBackgroundSubtractorCNT(
            minPixelStability=config.FPS // 2,
            maxPixelStability=(config.FPS // 2) * 4,
            isParallel=False,
        )

    @property
    def is_active(self):
        """
        TODO
        """
        return self.source.is_active

    def start(self):
        """
        TODO
        """
        self.source.start()

    def stop(self):
        """
        TODO
        """
        if self.is_active:
            self.conseq_motion_frames = 0
            self.source.stop()

    def read(self, resize_frame=None):
        """
        TODO
        """
        frame = self.source.read(resize_frame)
        # read_attempts = 0
        # while frame is None and read_attempts < 3:
        #     time.sleep(0.5)
        #     frame = self.source.read()
        #     read_attempts += 1

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
        return cv.dilate(denoised_foreground_mask, None, iterations=3)

    def find_contours(self, foreground_mask, display_frame=None):
        """
        TODO
        """
        detection_mode = cv.RETR_EXTERNAL
        detection_method = cv.CHAIN_APPROX_SIMPLE

        contours = cv.findContours(foreground_mask, detection_mode, detection_method)[0]

        return self.filter_contours(contours, display_frame)

    def filter_contours(self, contours, display_frame=None):
        """
        TODO
        """
        filtered_contours = []

        # Maybe vectorize this
        # Loop through the contours if there are any
        for contour in contours:
            # Remove small instances of detected motion
            # this will mostly be lighting changes
            if cv.contourArea(contour) < 3000:
                continue

            filtered_contours.append(contour)

            # # Performance optimization when there is no need to display a frame
            if display_frame is None:
                break

            DetectionSource._draw_bounding_boxes(display_frame, contour)
        return filtered_contours

    @staticmethod
    def _draw_bounding_boxes(display_frame, contour):
        """
        TODO
        """
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
        num_frames_to_record=100,
        display_frame=False,
    ):
        self.detection_sources = detection_sources

        self._display_frame = display_frame
        self._max_frames_to_record = num_frames_to_record

        self._detection_status = False
        self._recorder = IntuderRecorder(
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
            not source.is_active for source in self.detection_sources
        )
        if not self._detection_status or all_sources_inactive:
            return False
        return True

    def read_frame(self, source: DetectionSource, resize_frame=None):
        """
        TODO
        """
        frame = source.read(resize_frame)

        if frame is None:
            source.stop()

        return frame

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
        time.sleep(1)
        while self.get_detection_status():

            if frame_count % 2 == 1:
                time.sleep(1 / config.FPS)
                frame_count += 1
                continue

            for source in self.detection_sources:

                frame = self.read_frame(source, resize_frame=(640, 360))

                if frame is None:
                    continue

                self.detect_motion_in_frame(frame, source)

                if self._display_frame:
                    # Show the resized frame with bounding boxes around intruders (if any)
                    cv.imshow(f"({source.name}) Motion Detection", frame)

                self.check_for_intruders(frame, source, min_conseq_frames)
            frame_count += 1
            if cv.waitKey(1000 // config.FPS) == ord("q"):
                break

        if self._display_frame:
            # Close all windows
            cv.destroyAllWindows()

        self.stop_detection()

    def detect_motion_in_frame(self, frame, source):
        """
        TODO
        """
        foreground_mask = source.get_foreground_mask(frame)

        contours = source.find_contours(foreground_mask, display_frame=frame)

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
        self._detection_status = False

        for source in self.detection_sources:

            num_frames_recorded = self._recorder.get_num_frames_recorded(source)
            if num_frames_recorded >= 50:
                print(f"Saving recordings for source {source.name}")
                self._save_recordings(source)

    def _save_recordings(self, source):
        Thread(target=self._recorder.save, args=(source, False), daemon=True).start()


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
        # self.analyze_in_background()

    def _read_frames(self):
        pass

    def _analyze(self):
        """
        TODO
        """
