import logging

from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


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
        send_fcm_to_token(user.fcm_token, title, message, data or {})


@shared_task
def send_booking_status_notification(booking_id: int, new_status: str):
    from apps.bookings.models import Booking

    try:
        booking = Booking.objects.select_related('customer', 'garage').get(pk=booking_id)
    except Booking.DoesNotExist:
        return

    status_labels = {
        'pending': 'Pending',
        'confirmed': 'Confirmed',
        'in_progress': 'In Progress',
        'completed': 'Completed',
        'cancelled': 'Cancelled',
    }
    label = status_labels.get(new_status, new_status)
    title = 'Booking Update'
    message = (
        f'Your booking for {booking.vehicle.vehicle_number} '
        f'at {booking.garage.garage_name} is now {label}.'
    )
    send_push_notification.delay(
        booking.customer_id, title, message,
        {'booking_id': booking_id, 'status': new_status},
    )
