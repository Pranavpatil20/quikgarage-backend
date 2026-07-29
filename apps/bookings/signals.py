from decimal import Decimal

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Booking, BookingStatus

DEFAULT_SERVICE_COSTS = {
    'general_service': Decimal('1499.00'),
    'oil_change': Decimal('799.00'),
    'ac_service': Decimal('1299.00'),
    'brake_service': Decimal('999.00'),
    'wash': Decimal('399.00'),
    'repair': Decimal('1999.00'),
    'inspection': Decimal('499.00'),
    'other': Decimal('999.00'),
}


@receiver(pre_save, sender=Booking)
def cache_old_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Booking.objects.get(pk=instance.pk)
            instance._old_status = old.status
        except Booking.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Booking)
def notify_status_change(sender, instance, created, **kwargs):
    old_status = getattr(instance, '_old_status', None)
    if created or old_status == instance.status:
        return
    try:
        from apps.notifications.tasks import send_booking_status_notification
        send_booking_status_notification.delay(instance.pk, instance.status)
    except Exception:
        # Celery/broker may be unavailable in free deployments.
        pass


@receiver(post_save, sender=Booking)
def create_invoice_on_completed(sender, instance, created, **kwargs):
    """Auto-create a pending invoice when a booking is marked completed."""
    if created:
        return
    old_status = getattr(instance, '_old_status', None)
    if instance.status != BookingStatus.COMPLETED:
        return
    if old_status == BookingStatus.COMPLETED:
        return

    from apps.invoices.models import Invoice, PaymentStatus

    if Invoice.objects.filter(booking=instance).exists():
        return

    service_cost = DEFAULT_SERVICE_COSTS.get(
        instance.service_type,
        Decimal('999.00'),
    )
    Invoice.objects.create(
        booking=instance,
        service_cost=service_cost,
        parts_cost=Decimal('0.00'),
        payment_status=PaymentStatus.PENDING,
    )
