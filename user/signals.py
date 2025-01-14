# signals.py
from django.db.models.signals import post_save
from django.conf import settings
from django.dispatch import receiver
from .models import OtpToken
from django.core.mail import send_mail
from django.utils import timezone

def send_otp_email(user, otp_code):
    # Helper function to send OTP email.
    subject = "Anonymous Email Verification"
    message = f"""
    Hi {user.email}, welcome to Anonymous. 
    Your OTP is: {otp_code}
    It expires in exactly one hour.
    """
    sender = "muthondugithinji@gmail.com"
    receiver = [user.email]

    send_mail(subject, message, sender, receiver, fail_silently=False)


def create_token(user):
    # Generate and send OTP token for the user.
    otp_token = OtpToken.objects.create(user=user, otp_expires_at=timezone.now() + timezone.timedelta(hours=1))

    # Send OTP email
    send_otp_email(user, otp_token.otp_code)
    return otp_token


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def post_save_create_token(sender, instance, created, **kwargs):
    """
    Signal handler to generate OTP for newly created users.
    """
    if created and not instance.is_superuser and not instance.is_staff:
        create_token(instance)