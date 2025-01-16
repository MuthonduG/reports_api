from celery import shared_task
from .models import Guest
from django.utils.timezone import now

@shared_task
def delete_expired_guests():
    expired_guests = Guest.objects.filter(expiry_at__lt=now())
    count = expired_guests.count()
    expired_guests.delete()
    return f"{count} expired guest(s) deleted."

