from datetime import datetime, time, timedelta

from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.garages.models import Garage

from .models import Booking, BookingStatus


def generate_time_slots(garage: Garage, interval_minutes: int = 60) -> list[time]:
    slots = []
    current = datetime.combine(timezone.localdate(), garage.opening_time)
    end = datetime.combine(timezone.localdate(), garage.closing_time)
    delta = timedelta(minutes=interval_minutes)
    while current < end:
        slots.append(current.time())
        current += delta
    return slots


def get_booked_slots(garage_id: int, booking_date) -> set[time]:
    return set(
        Booking.objects.filter(
            garage_id=garage_id,
            booking_date=booking_date,
        ).exclude(status=BookingStatus.CANCELLED).values_list('time_slot', flat=True),
    )


def get_available_slots(garage: Garage, booking_date) -> list[dict]:
    all_slots = generate_time_slots(garage)
    booked = get_booked_slots(garage.id, booking_date)
    return [
        {
            'time': slot.strftime('%H:%M'),
            'available': slot not in booked,
        }
        for slot in all_slots
    ]


def validate_booking_slot(garage: Garage, booking_date, time_slot, exclude_booking_id=None):
    if time_slot < garage.opening_time or time_slot >= garage.closing_time:
        raise ValidationError({'time_slot': 'Selected time is outside garage operating hours.'})

    qs = Booking.objects.filter(
        garage=garage,
        booking_date=booking_date,
        time_slot=time_slot,
    ).exclude(status=BookingStatus.CANCELLED)

    if exclude_booking_id:
        qs = qs.exclude(pk=exclude_booking_id)

    if qs.exists():
        raise ValidationError({'time_slot': 'This time slot is already booked.'})


def validate_vehicle_ownership(customer, vehicle):
    if vehicle.customer_id != customer.id:
        raise ValidationError({'vehicle': 'Vehicle does not belong to this customer.'})
