from django.db import models
from datetime import timedelta
from django.utils.timezone import now

def default_expiry():
    return now() + timedelta(days=30)

class Guest(models.Model):
    guest_id = models.CharField(max_length=32, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expiry_at = models.DateTimeField(default=default_expiry)

    def is_expired(self):
        return now() > self.expiry_at
