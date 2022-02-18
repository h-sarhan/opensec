from django import forms

from .models import Camera


class EditCameraForm(forms.ModelForm):
    class Meta:
        model = Camera
        fields = ("name", "rtsp_url", "is_ptz")

    def __init__(self, *args, **kwargs):
        super(EditCameraForm, self).__init__(*args, **kwargs)

        rtsp_placeholder = "rtsp://username:password@123.123.123.123:554"

        self.fields["rtsp_url"].widget.attrs["class"] = "input"
        self.fields["name"].widget.attrs["class"] = "input"
        self.fields["name"].widget.attrs["placeholder"] = "Camera name"
        self.fields["rtsp_url"].widget.attrs["placeholder"] = rtsp_placeholder
