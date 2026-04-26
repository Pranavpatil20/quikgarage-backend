from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    OWNER = "owner", "Owner"
    CUSTOMER = "customer", "Customer"


class User(AbstractUser):
    username = None
    phone_number = models.CharField(max_length=15, unique=True)
    role = models.CharField(max_length=20, choices=UserRole.choices)
    full_name = models.CharField(max_length=120)
    garage_name = models.CharField(max_length=120, blank=True)
    garage_timing = models.CharField(max_length=120, blank=True)
    default_general_service_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    app_language = models.CharField(max_length=20, default="English")

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    def __str__(self) -> str:
        return f"{self.full_name} ({self.phone_number})"


class OtpRequest(models.Model):
    phone_number = models.CharField(max_length=15, db_index=True)
    otp_code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self) -> str:
        return f"{self.phone_number} - {self.otp_code}"
