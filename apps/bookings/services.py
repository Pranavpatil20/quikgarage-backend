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


def _aware_slot_datetime(booking_date, slot_time: time):
    slot_dt = datetime.combine(booking_date, slot_time)
    if timezone.is_naive(slot_dt):
        slot_dt = timezone.make_aware(slot_dt, timezone.get_current_timezone())
    return slot_dt


def get_available_slots(garage: Garage, booking_date) -> list[dict]:
    all_slots = generate_time_slots(garage)
    booked = get_booked_slots(garage.id, booking_date)
    now = timezone.localtime()
    result = []
    for slot in all_slots:
        available = slot not in booked
        # Past times for today are not bookable.
        if booking_date == now.date() and _aware_slot_datetime(booking_date, slot) <= now:
            available = False
        result.append({
            'time': slot.strftime('%H:%M'),
            'available': available,
        })
    return result


def validate_booking_slot(garage: Garage, booking_date, time_slot, exclude_booking_id=None):
    if time_slot < garage.opening_time or time_slot >= garage.closing_time:
        raise ValidationError({'time_slot': 'Selected time is outside garage operating hours.'})

    now = timezone.localtime()
    if _aware_slot_datetime(booking_date, time_slot) <= now:
        raise ValidationError({'time_slot': 'Cannot book a past date or time.'})

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
