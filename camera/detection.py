"""
TODO
"""

from __future__ import annotations

import os
import random
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import config
import cv2 as cv
import numpy as np
import opensec.models
from vidgear.gears import WriteGear

from . import CameraSource, VideoSource

NOISE_KERNEL = cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3))

# TODO: Add object detection
# TODO: Clean dependencies
# TODO: DOCUMENTATION


class IntruderRecorder:
    num_frames_to_analyze = 10

    def __init__(
        self,
        detection_sources: List[DetectionSource],
        recording_directory: str,
        max_stored_frames: int = 80,
    ):
        self.sources = detection_sources
        self.recordings_directory = recording_directory
        self.max_stored_frames = max_stored_frames

        self._video_writers: Dict[str, WriteGear] = {}
        self._start_times: Dict[str, str] = {}
        self._stored_frames: Dict[str, List[np.ndarray]] = {}
        self._intruder_labels: Dict[str, List[str]] = {}
        self._analyzer = IntruderAnalyzer()
        self._is_analyzing = False
        self._setup()

    def get_labels(self) -> Dict[str, List[str]] | None:
        if self._is_analyzing:
            return None
        return self._intruder_labels

    def get_num_frames_recorded(self, source: DetectionSource) -> int:

        return len(self._stored_frames[source.name])

    def add_frame(self, frame: np.ndarray | None, source: DetectionSource) -> None:

        if self._start_times[source.name] is None:
            current_date_time = datetime.now().strftime("%Y_%m_%d %Hh %Mm %Ss")
            self._start_times[source.name] = current_date_time

        if frame is not None:
            stored_frames = self._stored_frames[source.name]
            if len(stored_frames) < self.max_stored_frames:
                stored_frames.append(frame)

            writer = self._video_writers[source.name]
            writer.write(frame)

    def save(self, source: DetectionSource, thumb: bool = True) -> List[str]:

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

        frames_to_analyze = [
            random.choice(self._stored_frames[source.name])
            for _ in range(self.num_frames_to_analyze)
        ]
        self._analyze_intruders(source, frames_to_analyze)
        self._start_times[source.name] = None
        self._stored_frames[source.name] = []
        return paths

    def _rename_video(self, source: DetectionSource) -> str:

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

    def _save_thumb(self, source: DetectionSource) -> str | None:

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

    def _setup(self) -> None:

        self._make_paths()
        self._make_video_writers()
        for source in self.sources:
            self._start_times[source.name] = None
            self._stored_frames[source.name] = []

    def _make_video_writers(self) -> None:
        for source in self.sources:
            output_params = {"-fourcc": "mp4v", "-fps": config.FPS // 2}
            self._video_writers[source.name] = WriteGear(
                f"{self.recordings_directory}/videos/{source.name}/intruder.mp4",
                compression_mode=False,
                logging=False,
                **output_params,
            )

    def _make_paths(self) -> None:
        if not os.path.exists(self.recordings_directory):
            os.mkdir(self.recordings_directory)

        directories = [
            f"{self.recordings_directory}/videos",
            f"{self.recordings_directory}/thumbnails",
        ]
        for directory in directories:
            if not os.path.exists(directory):
                os.mkdir(directory)

            for source in self.sources:
                if source is not None and not os.path.exists(
                    f"{directory}/{source.name}"
                ):
                    os.mkdir(f"{directory}/{source.name}")

    def _analyze_intruders(self, source: DetectionSource, frames: List[np.ndarray]):
        self._is_analyzing = True
        predictions: List[str] = []
        for random_frame in frames:
            frame_labels = self._analyzer.analyze_frame(random_frame)
            if frame_labels is not None:
                predictions.extend(frame_labels)

        self._intruder_labels[source.name] = predictions
        self._is_analyzing = False


class DetectionSource:
    def __init__(self, name: str, source: CameraSource | VideoSource):
        self.name = name
        self.source = source
        self.conseq_motion_frames = 0

        self._bg_subtractor = cv.bgsegm.createBackgroundSubtractorCNT(
            minPixelStability=config.FPS // 2,
            maxPixelStability=(config.FPS // 2) * 4,
            isParallel=False,
        )

    def get_rtsp_link(self):
        return self.source.source

    @property
    def is_active(self) -> bool:

        return self.source.is_active

    def start(self) -> None:

        self.source.start()

    def stop(self) -> None:

        if self.is_active:
            self.conseq_motion_frames = 0
            self.source.stop()

    def read(self, resize_frame: Optional[Tuple[int, int]] = None) -> np.ndarray | None:

        frame = self.source.read(resize_frame)
        # read_attempts = 0
        # while frame is None and read_attempts < 3:
        #     time.sleep(0.5)
        #     frame = self.source.read()
        #     read_attempts += 1

        if frame is None:
            self.stop()

        return frame

    def get_foreground_mask(self, frame: np.ndarray) -> np.ndarray:

        foreground_mask = self._bg_subtractor.apply(frame)

        denoised_foreground_mask = cv.morphologyEx(
            foreground_mask, cv.MORPH_OPEN, NOISE_KERNEL
        )
        return cv.dilate(denoised_foreground_mask, None, iterations=3)

    def find_contours(
        self, foreground_mask: np.ndarray, display_frame: Optional[np.ndarray] = None
    ) -> List[np.ndarray]:

        detection_mode = cv.RETR_EXTERNAL
        detection_method = cv.CHAIN_APPROX_SIMPLE

        contours = cv.findContours(foreground_mask, detection_mode, detection_method)[0]

        return self.filter_contours(contours, display_frame)

    def filter_contours(
        self, contours: List[np.ndarray], display_frame: Optional[np.ndarray] = None
    ) -> List[np.ndarray]:

        filtered_contours: List[np.ndarray] = []

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
    def _draw_bounding_boxes(display_frame: np.ndarray, contour: np.ndarray) -> None:

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
    def __init__(
        self,
        detection_sources: List[DetectionSource],
        recording_directory: str,
        num_frames_to_record: int = 30,
        display_frame: bool = False,
    ):
        self.detection_sources = detection_sources

        self._display_frame = display_frame
        self._max_frames_to_record = num_frames_to_record

        self._detection_status = False
        self._recorder = IntruderRecorder(
            self.detection_sources, recording_directory, num_frames_to_record
        )

    def start_sources(self) -> None:

        for source in self.detection_sources:
            source.start()

    def get_intruder_labels(self) -> Dict[str, str] | None:
        labels = self._recorder.get_labels()
        if labels is None:
            return labels
        intruders: Dict[str, str] = {}
        for source, intruder_labels in labels.items():
            if "cat" in intruder_labels or "dog" in intruder_labels:
                intruders[source] = "animal"
            if "person" in intruder_labels:
                intruders[source] = "person"

        return intruders

    def get_detection_status(self) -> bool:

        all_sources_inactive = all(
            not source.is_active for source in self.detection_sources
        )
        if not self._detection_status or all_sources_inactive:
            return False
        return True

    def read_frame(
        self, source: DetectionSource, resize_frame: Tuple[int, int] = None
    ) -> np.ndarray | None:

        frame = source.read(resize_frame)

        if frame is None:
            source.stop()

        return frame

    def update_conseq_frames(
        self, source: DetectionSource, contours: List[np.ndarray]
    ) -> None:

        if IntruderDetector.is_motion_frame(contours):
            source.conseq_motion_frames += 1
        else:
            if source.conseq_motion_frames > 0:
                self._save_recordings(source)
            source.conseq_motion_frames = 0

    def detect(self, min_conseq_frames: int = 15) -> None:

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

    def detect_motion_in_frame(
        self, frame: np.ndarray, source: DetectionSource
    ) -> None:

        foreground_mask = source.get_foreground_mask(frame)

        contours = source.find_contours(foreground_mask, display_frame=frame)

        self.update_conseq_frames(source, contours)

    @staticmethod
    def is_motion_frame(contours: List[np.ndarray]) -> bool:

        # If no contours have been found then this is not a motion frame
        return contours is not None and len(contours) != 0

    def check_for_intruders(
        self, frame: np.ndarray, source: DetectionSource, min_conseq_frames: int
    ) -> None:

        if source.conseq_motion_frames >= min_conseq_frames:
            print(f"intruder detected at {source.name}")
            self.record_frame(frame, source)

    def record_frame(self, frame: np.ndarray, source: DetectionSource) -> None:

        num_frames_recorded = self._recorder.get_num_frames_recorded(source)
        if num_frames_recorded <= self._max_frames_to_record:
            self._recorder.add_frame(frame, source)
        else:
            self._save_recordings(source)

    def stop_detection(self) -> None:

        self._detection_status = False

        for source in self.detection_sources:

            num_frames_recorded = self._recorder.get_num_frames_recorded(source)
            if num_frames_recorded >= self._max_frames_to_record // 4:
                print(f"Saving recordings for source {source.name}")
                self._save_recordings(source)

    def add_intruder(
        self, source: DetectionSource, video_path: str, thumb_path: Optional[str] = None
    ):
        intruder_labels = self.get_intruder_labels()
        label = intruder_labels.get(source.name, None)

        # If no label is produced then don't add intruder to database
        if label is not None:
            camera = opensec.models.Camera.objects.get(name=source.name)
            if thumb_path is not None:
                opensec.models.Intruder.objects.create(
                    label=label,
                    video=video_path,
                    thumbnail=thumb_path,
                    camera=camera,
                )
            else:
                opensec.models.Intruder.objects.create(
                    label=label,
                    video=video_path,
                    camera=camera,
                )

    def _save_recordings(self, source: DetectionSource) -> None:
        num_frames_recorded = self._recorder.get_num_frames_recorded(source)
        if num_frames_recorded > self._max_frames_to_record // 2:
            print("Saving recording and adding intruder to database")
            paths = self._recorder.save(source, thumb=True)
            if len(paths) == 2:
                self.add_intruder(source, video_path=paths[0], thumb_path=paths[1])
            else:
                self.add_intruder(source, video_path=paths[0])


class IntruderAnalyzer:

    ssd_classes = [
        "background",
        "aeroplane",
        "bicycle",
        "bird",
        "boat",
        "bottle",
        "bus",
        "car",
        "cat",
        "chair",
        "cow",
        "diningtable",
        "dog",
        "horse",
        "motorbike",
        "person",
        "pottedplant",
        "sheep",
        "sofa",
        "train",
        "tvmonitor",
    ]

    def __init__(self):
        # Path to Yolo weights and configuration files
        ssd_weights = "./ssd/MobileNetSSD_deploy.caffemodel"
        ssd_config = "./ssd/MobileNetSSD_deploy.prototxt"

        self.net = cv.dnn.readNetFromCaffe(ssd_config, ssd_weights)

    def analyze_frame(self, frame: np.ndarray) -> List[str] | None:
        # Convert the frame into an appropriate format for SSD
        if frame is None:
            print("frame passed to analyze_frame is None")
            return None
        blob = cv.dnn.blobFromImage(frame, 0.007843, (300, 300), 127.5)
        self.net.setInput(blob)
        # Perform inference on the frame
        detections = self.net.forward()

        predicted_labels = []
        for i in np.arange(0, detections.shape[2]):
            # Get confidence score
            confidence = detections[0, 0, i, 2]
            if confidence > 0.5:
                class_id = int(detections[0, 0, i, 1])
                predicted_labels.append((self.ssd_classes[class_id], confidence))

        if not predicted_labels:
            return None
        # Get labels only
        return [label for label, _ in predicted_labels]
