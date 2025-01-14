from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.hashers import make_password, check_password
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.conf import settings
from django.utils.timezone import now
import hashlib
import secrets


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


# custom user model
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  
    anonymous_unique_id = models.CharField(max_length=256, editable=False)
    security_query_response = models.CharField(max_length=256)
    username = models.CharField(max_length=256 ,blank=True)
    department = models.CharField(max_length=256)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)
        if self.pk and User.objects.filter(email=self.email).exclude(pk=self.pk).exists():
            raise ValidationError({'email': 'This email address is already in use.'})

    def generate_anonymous_id(self):
        combined_string = f"{self.security_query_response}:{self.email}"
        anonymous_id = hashlib.sha256(combined_string.encode("utf-8")).hexdigest()
        return anonymous_id

    def has_changed(self, fields):
        if not self.pk:
            return True 
        old_instance = User.objects.filter(pk=self.pk).first()
        return any(getattr(self, field) != getattr(old_instance, field) for field in fields)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    def generate_username(self):
        user_email = self.email
        username = user_email.split('@')[0]
        return username


# 
@receiver(pre_save, sender=User)
def pre_save_user(sender, instance, **kwargs):
    if not instance.anonymous_unique_id or instance.has_changed(['email', 'security_query_response']):
        instance.anonymous_unique_id = instance.generate_anonymous_id()

    if not instance.password.startswith("pbkdf2_"):
        instance.password = make_password(instance.password)
    
    if not instance.username or instance.has_changed(['email']):
        instance.username = instance.generate_username()


# custom otp generator method
def generate_otp_code():
    return secrets.token_hex(3).upper()

# otp token model
class OtpToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="otps")
    otp_code = models.CharField(max_length=6, default=generate_otp_code().upper())
    otp_created_at = models.DateTimeField(auto_now_add=True)
    otp_expires_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.user.email

    def is_valid(self):
        """
        Check if the OTP is still valid based on the expiration time.
        """
        return self.otp_expires_at and self.otp_expires_at > now()
    