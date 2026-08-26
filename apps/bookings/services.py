from datetime import datetime, time, timedelta

from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.garages.models import Garage

from .models import Booking, BookingStatus


def generate_time_slots(
    garage: Garage,
    booking_date=None,
    interval_minutes: int = 60,
) -> list[time]:
    if booking_date is None:
        booking_date = timezone.localdate()
        is_open, opening, closing = True, garage.opening_time, garage.closing_time
    else:
        is_open, opening, closing = garage.hours_for_date(booking_date)

    if not is_open:
        return []

    slots = []
    current = datetime.combine(booking_date, opening)
    end = datetime.combine(booking_date, closing)
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


def get_available_slots(garage: Garage, booking_date) -> dict:
    is_open, opening, closing = garage.hours_for_date(booking_date)
    if not is_open:
        return {
            'closed': True,
            'slots': [],
            'opening_time': None,
            'closing_time': None,
        }

    all_slots = generate_time_slots(garage, booking_date)
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
    return {
        'closed': False,
        'slots': result,
        'opening_time': opening.strftime('%H:%M'),
        'closing_time': closing.strftime('%H:%M'),
    }


def validate_booking_slot(garage: Garage, booking_date, time_slot, exclude_booking_id=None):
    is_open, opening, closing = garage.hours_for_date(booking_date)
    if not is_open:
        raise ValidationError({
            'booking_date': 'Garage is closed on this day. Please choose another date.',
        })

    if time_slot < opening or time_slot >= closing:
        open_label = opening.strftime('%I:%M %p').lstrip('0')
        close_label = closing.strftime('%I:%M %p').lstrip('0')
        raise ValidationError({
            'time_slot': f'Booking time must be between {open_label} and {close_label}.',
        })

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
