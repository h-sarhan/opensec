import config
import cv2 as cv
import numpy as np
from vidgear.gears.asyncio import WebGear_RTC, webgear_rtc
from vidgear.gears.helper import reducer

# Lower the fps of the webRTC stream
webgear_rtc.VIDEO_PTIME = 1 / config.FPS


class LiveFeedFrameProducer:
    def __init__(self, frame_reduction_amount):
        self.frame_reduction_amount = frame_reduction_amount
        self._source = None
        self.running = True
        self._placeholder_frame = np.empty((720, 1280, 3), dtype=np.uint8)

        cv.putText(
            self._placeholder_frame,
            "no input",
            (200, 200),
            cv.FONT_HERSHEY_DUPLEX,
            3,
            (0, 255, 0),
        )

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, new_source):
        print(f"NEW SOURCE {new_source}")
        self._source = new_source

    def read(self):
        if self._source is None:
            return self._placeholder_frame

        frame = self._source.read()
        if frame is None:
            return self._placeholder_frame

        if self.frame_reduction_amount is not None:
            return reducer(
                frame,
                percentage=self.frame_reduction_amount,
                interpolation=cv.INTER_NEAREST,
            )

        return frame

    def stop(self):
        self.running = False
        if not self._source is None:
            print("LIVE FEED STOPPED")


class LiveFeed:
    def __init__(self, frame_reduction_amount=40):
        self._frame_producer = LiveFeedFrameProducer(frame_reduction_amount)
        self._live_feed_options = {
            "custom_stream": self._frame_producer,
            "custom_data_location": "./",
            "enable_live_broadcast": True,
            "frame_size_reduction": 40,
        }
        self._stream = WebGear_RTC(**self._live_feed_options)
        self._streaming = False

    @property
    def is_streaming(self):
        return self._streaming

    @property
    def source(self):
        return self._frame_producer.source

    @source.setter
    def source(self, new_source):
        self._frame_producer.source = new_source

    @property
    def stream_app(self):
        self._streaming = True
        return self._stream

    def stop(self):
        if self._streaming:
            print("Stopping streaming server")
            self._streaming = False
            self._stream.shutdown()
        else:
            print("Stream is already stopped")
