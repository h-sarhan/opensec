import os
import socket
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
HOST_NAME = socket.gethostname()
LOCAL_IP_ADDRESS = socket.gethostbyname(HOST_NAME)
STREAM_DIRECTORY = "media/stream"
CAM_DEBUG = True
PORT = 8080
FPS = 15

load_dotenv()
TEST_CAMS = [
    os.getenv("TEST_CAM_1"),
    os.getenv("TEST_CAM_2"),
    os.getenv("TEST_CAM_3"),
    os.getenv("TEST_CAM_4"),
]
TEST_VID_DIRECTORY = ROOT_DIR.joinpath(os.getenv("TEST_VID_DIRECTORY")).as_posix()
TEST_VIDEO_OUTPUT_DIRECTORY = ROOT_DIR.joinpath(
    os.getenv("TEST_VIDEO_OUTPUT_DIRECTORY")
).as_posix()
