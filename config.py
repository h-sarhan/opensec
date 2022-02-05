import os
import socket
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
HOST_NAME = socket.gethostname()
LOCAL_IP_ADDRESS = socket.gethostbyname(HOST_NAME)
STREAM_DIRECTORY = ROOT_DIR.joinpath("stream").as_posix()
CAM_DEBUG = True
PORT = 8080

load_dotenv()
TEST_CAM = os.getenv("TEST_CAM")
TEST_VID_DIRECTORY = ROOT_DIR.joinpath(os.getenv("TEST_VID_DIRECTORY")).as_posix()
TEST_VIDEO_OUTPUT_DIRECTORY = ROOT_DIR.joinpath(
    os.getenv("TEST_VIDEO_OUTPUT_DIRECTORY")
).as_posix()
