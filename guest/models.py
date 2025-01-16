from django.db import models
from datetime import timedelta
from django.utils.timezone import now

class Guest(models.Model):
    guest_id = models.CharField(max_length=32, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expiry_at = models.DateTimeField(default=lambda: now() + timedelta(days=30))

    def is_expired(self):
        return now() > self.expiry_at
