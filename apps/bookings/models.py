from django.conf import settings
from django.db import models

from apps.customers.models import CustomerProfile, Vehicle


class ServiceType(models.TextChoices):
    ENGINE_ISSUE = "engine_issue", "Engine Issue"
    BRAKE_PROBLEM = "brake_problem", "Brake Problem"
    OIL_CHANGE = "oil_change", "Oil Change"
    BATTERY_ISSUE = "battery_issue", "Battery Issue"
    GENERAL_SERVICE = "general_service", "General Service"
    OTHERS = "others", "Others"


class BookingStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    CONFIRMED = "confirmed", "Confirmed"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class Booking(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owner_bookings")
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name="bookings")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="bookings")
    service_type = models.CharField(max_length=30, choices=ServiceType.choices)
    custom_service_type = models.CharField(max_length=120, blank=True)
    booking_date = models.DateField()
    time_slot = models.TimeField()
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=BookingStatus.choices, default=BookingStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("owner", "booking_date", "time_slot")
        ordering = ["booking_date", "time_slot"]

    def __str__(self) -> str:
        return f"{self.vehicle.vehicle_number} @ {self.booking_date} {self.time_slot}"


class Invoice(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="invoice")
    service_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    parts_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.total_amount = (self.service_cost or 0) + (self.parts_cost or 0)
        super().save(*args, **kwargs)
