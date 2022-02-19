import os
import time
from threading import Thread

import config
import numpy as np
from vidgear.gears.asyncio import WebGear_RTC


class LiveFeedProducer:

    reduce_amount = 0.4

    def __init__(self, sources):
        self.sources = sources
        self.running = True
        self._live_feed_shape = (
            int(360 * (1 - self.reduce_amount)) * 2,
            int(640 * (1 - self.reduce_amount)) * 2,
            3,
        )
        self._single_frame_shape = (
            int(360 * (1 - self.reduce_amount)),
            int(640 * (1 - self.reduce_amount)),
            3,
        )
        self._live_feed_frame = np.zeros(self._live_feed_shape, np.uint8)
        # TODO: Draw text on blank frame
        self._blank_frame = np.zeros(self._single_frame_shape, np.uint8)
        self._frame_count = 0
        self._current_frame = None
        Thread(target=self._update_frame).start()

    def read(self):

        return self._current_frame

    def _update_frame(self):
        # TODO: Make this work with a variable number of sources

        while self.running:
            frames = []
            for source in self.sources:
                frame_height, frame_width = self._single_frame_shape[:2]
                frame = source.read(resize_frame=(frame_width, frame_height))
                if frame is None:
                    print("Frame is none")
                    frames.append(self._blank_frame)
                else:
                    frames.append(frame)

            frame_height, frame_width = self._single_frame_shape[:2]
            self._live_feed_frame[:frame_height, :frame_width] = frames[0]
            self._live_feed_frame[:frame_height, frame_width:] = frames[1]
            self._live_feed_frame[frame_height:, :frame_width] = frames[2]
            self._live_feed_frame[frame_height:, frame_width:] = frames[3]
            self._current_frame = self._live_feed_frame
            time.sleep(1 / config.FPS)

        self._current_frame = None

    def stop(self):
        """
        TODO
        """
        self.running = False


class LiveFeed:
    def __init__(self, sources, stream_directory="stream"):
        self.sources = sources
        self.stream_directory = stream_directory
        self.live_feed_options = {
            "custom_stream": LiveFeedProducer(self.sources),
            "custom_data_location": "./",
            "enable_live_broadcast": True,
            "frame_size_reduction": 0,
        }
        self.stream = WebGear_RTC(logging=True, **self.live_feed_options)

        self._streaming = False
        self._server = None

    @property
    def is_streaming(self):

        all_sources_inactive = all(not source.is_active for source in self.sources)
        if not self._streaming or all_sources_inactive:
            return False
        return True

    # @profile
    def start_streaming_live_feed(self):

        for source in self.sources:
            source.start()

        # Give the sources some time to read frames
        time.sleep(5)
        # uvicorn.run(self.stream(), host="0.0.0.0", port=8000)

    def start(self):

        self._streaming = True
        Thread(target=self.start_streaming_live_feed).start()

    def stop(self):

        print("Stopping streaming server")
        if self._streaming:
            self._streaming = False
            self.stream.shutdown()

    def _make_dirs(self):
        for source in self.sources:
            dir_name = f"stream/{source.name}"
            if not os.path.exists(dir_name):
                os.mkdir(dir_name)
