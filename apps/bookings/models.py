from django.conf import settings
from django.db import models
from django.db.models import Q


class BookingStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    CONFIRMED = 'confirmed', 'Confirmed'
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'


class ServiceType(models.TextChoices):
    GENERAL_SERVICE = 'general_service', 'General Service'
    OIL_CHANGE = 'oil_change', 'Oil Change'
    AC_SERVICE = 'ac_service', 'AC Service'
    BRAKE_SERVICE = 'brake_service', 'Brake Service'
    WASH = 'wash', 'Car Wash'
    REPAIR = 'repair', 'Repair'
    INSPECTION = 'inspection', 'Inspection'
    OTHER = 'other', 'Other'


class Booking(models.Model):
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings',
    )
    garage = models.ForeignKey(
        'garages.Garage',
        on_delete=models.CASCADE,
        related_name='bookings',
    )
    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.CASCADE,
        related_name='bookings',
    )
    service_type = models.CharField(max_length=40, choices=ServiceType.choices)
    booking_date = models.DateField(db_index=True)
    time_slot = models.TimeField(db_index=True)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bookings'
        ordering = ['booking_date', 'time_slot']
        constraints = [
            models.UniqueConstraint(
                fields=['garage', 'booking_date', 'time_slot'],
                condition=~Q(status=BookingStatus.CANCELLED),
                name='unique_active_slot_per_garage',
            ),
        ]

    def __str__(self):
        return f'{self.vehicle.vehicle_number} @ {self.booking_date} {self.time_slot}'

    @property
    def can_customer_cancel(self):
        return self.status in (
            BookingStatus.PENDING,
            BookingStatus.CONFIRMED,
        )
