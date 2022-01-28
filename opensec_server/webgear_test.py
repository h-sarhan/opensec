"""
WebGear test server
"""
import uvicorn
from vidgear.gears.asyncio import WebGear

# various performance tweaks
options = {
    "frame_size_reduction": 50,
    "jpeg_compression_quality": 70,
    "jpeg_compression_fastdct": True,
    "jpeg_compression_fastupsample": True,
}

# initialize WebGear app
web = WebGear(source="rtsp://admin:123456@192.168.1.226:554", logging=True, **options)

# run this app on Uvicorn server at address http://localhost:8000/
uvicorn.run(web(), host="0.0.0.0", port=8000)

# close app safely
web.shutdown()
