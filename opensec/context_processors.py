from .models import Camera


def camera_list_processor(request):
    """
    This context processor makes a list of cameras
    available to every template
    """
    cameras = Camera.objects.all()
    return {"cameras": cameras}
