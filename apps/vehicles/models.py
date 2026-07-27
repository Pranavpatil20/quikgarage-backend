from django.conf import settings
from django.db import models


class VehicleType(models.TextChoices):
    CAR = 'car', 'Car'
    BIKE = 'bike', 'Bike'
    SUV = 'suv', 'SUV'
    TRUCK = 'truck', 'Truck'
    OTHER = 'other', 'Other'


class Vehicle(models.Model):
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vehicles',
    )
    vehicle_number = models.CharField(max_length=20, db_index=True)
    vehicle_type = models.CharField(max_length=20, choices=VehicleType.choices, default=VehicleType.CAR)
    make_model = models.CharField(max_length=120, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'vehicles'
        unique_together = ('customer', 'vehicle_number')
        ordering = ['-is_primary', '-created_at']

    def __str__(self):
        return f'{self.make_model or self.vehicle_type} - {self.vehicle_number}'

    def save(self, *args, **kwargs):
        if self.is_primary:
            Vehicle.objects.filter(customer=self.customer, is_primary=True).exclude(
                pk=self.pk,
            ).update(is_primary=False)
        super().save(*args, **kwargs)
