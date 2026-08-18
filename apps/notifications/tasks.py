import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)

STATUS_LABELS = {
    'pending': 'Pending',
    'confirmed': 'Confirmed',
    'in_progress': 'In Progress',
    'completed': 'Completed',
    'cancelled': 'Cancelled',
}


def _enqueue(task, *args, **kwargs):
    try:
        task.delay(*args, **kwargs)
    except Exception:
        task(*args, **kwargs)


@shared_task
def send_push_notification(user_id: int, title: str, message: str, data: dict | None = None):
    from apps.users.models import User
    from .models import Notification
    from .services import send_fcm_to_token

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.warning('User %s not found for notification', user_id)
        return

    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        data=data or {},
    )

    if user.fcm_token:
        sent = send_fcm_to_token(user.fcm_token, title, message, data or {})
        if sent:
            logger.info('FCM sent to user %s: %s', user_id, title)
    else:
        logger.info('No FCM token for user %s — in-app only: %s', user_id, title)


@shared_task
def notify_booking_created(booking_id: int):
    from apps.bookings.models import Booking

    try:
        booking = Booking.objects.select_related(
            'customer', 'garage', 'garage__owner', 'vehicle',
        ).get(pk=booking_id)
    except Booking.DoesNotExist:
        return

    vehicle = booking.vehicle.vehicle_number
    garage = booking.garage.garage_name
    slot = booking.time_slot.strftime('%I:%M %p').lstrip('0')
    date = booking.booking_date.strftime('%d %b %Y')
    payload = {
        'type': 'booking_created',
        'booking_id': str(booking_id),
        'status': booking.status,
    }

    _enqueue(
        send_push_notification,
        booking.customer_id,
        'Booking confirmed',
        f'Your booking for {vehicle} at {garage} is scheduled on {date} at {slot}.',
        payload,
    )
    owner_id = booking.garage.owner_id
    if owner_id and owner_id != booking.customer_id:
        customer_name = booking.customer.name or booking.customer.phone
        _enqueue(
            send_push_notification,
            owner_id,
            'New booking',
            f'{customer_name} booked {vehicle} on {date} at {slot}.',
            payload,
        )


@shared_task
def send_booking_status_notification(booking_id: int, new_status: str):
    from apps.bookings.models import Booking

    try:
        booking = Booking.objects.select_related(
            'customer', 'garage', 'garage__owner', 'vehicle',
        ).get(pk=booking_id)
    except Booking.DoesNotExist:
        return

    label = STATUS_LABELS.get(new_status, new_status)
    vehicle = booking.vehicle.vehicle_number
    garage = booking.garage.garage_name
    payload = {
        'type': 'booking_status',
        'booking_id': str(booking_id),
        'status': new_status,
    }

    customer_title = 'Service completed' if new_status == 'completed' else 'Booking update'
    customer_message = (
        f'Your {vehicle} service at {garage} is complete. Book again in 3 months to stay in shape.'
        if new_status == 'completed'
        else f'Your booking for {vehicle} at {garage} is now {label}.'
    )
    _enqueue(
        send_push_notification,
        booking.customer_id,
        customer_title,
        customer_message,
        payload,
    )

    owner_id = booking.garage.owner_id
    if owner_id and owner_id != booking.customer_id:
        customer_name = booking.customer.name or booking.customer.phone
        _enqueue(
            send_push_notification,
            owner_id,
            'Booking update',
            f'{customer_name} · {vehicle} is now {label}.',
            payload,
        )


@shared_task
def send_service_due_reminders():
    """Outside-app reminder: last completed service was about 3 months ago."""
    from apps.bookings.models import Booking, BookingStatus

    now = timezone.now()
    window_end = now - timedelta(days=90)
    window_start = now - timedelta(days=97)

    due = (
        Booking.objects.filter(
            status=BookingStatus.COMPLETED,
            completed_at__gte=window_start,
            completed_at__lte=window_end,
            service_reminder_sent_at__isnull=True,
            customer__role='customer',
        )
        .select_related('customer', 'garage', 'vehicle')
        .order_by('customer_id', '-completed_at')
    )

    reminded_customers = set()
    count = 0
    for booking in due:
        if booking.customer_id in reminded_customers:
            continue
        reminded_customers.add(booking.customer_id)
        vehicle = booking.vehicle.vehicle_number
        garage = booking.garage.garage_name
        send_push_notification(
            booking.customer_id,
            'Time for a service',
            f'It has been 3 months since {vehicle} was serviced at {garage}. Book your next visit with QuikGarage.',
            {
                'type': 'service_due',
                'booking_id': str(booking.id),
            },
        )
        Booking.objects.filter(pk=booking.pk).update(service_reminder_sent_at=now)
        count += 1

    logger.info('Service due reminders sent: %s', count)
    return count
