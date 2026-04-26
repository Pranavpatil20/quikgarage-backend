from django.conf import settings
from django.db import models


class CustomerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer_profile")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="garage_customers"
    )
    whatsapp_opt_in = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.user.full_name


class Vehicle(models.Model):
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name="vehicles")
    vehicle_number = models.CharField(max_length=30, db_index=True)
    brand = models.CharField(max_length=80, blank=True)
    model = models.CharField(max_length=80, blank=True)

    class Meta:
        unique_together = ("customer", "vehicle_number")

    def __str__(self) -> str:
        return self.vehicle_number
