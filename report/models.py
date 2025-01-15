from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField

# Report model
class Report(models.Model):
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports")
    report_title = models.CharField(max_length=150)
    report_type = models.CharField(max_length=150)
    report_description = models.CharField(max_length=1000)
    report_status = models.BooleanField(default=False)
    image_data = CloudinaryField('image', blank=True, null=True)
    audio_data = CloudinaryField('audio', blank=True, null=True)
    video_data = CloudinaryField('video', blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.report_title}:{self.report_status}"