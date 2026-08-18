from decimal import Decimal

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Booking, BookingStatus

# Fallback costs when garage has no default_service_cost set.
DEFAULT_SERVICE_COSTS = {
    'general_service': Decimal('899.00'),
    'oil_change': Decimal('799.00'),
    'ac_service': Decimal('1299.00'),
    'brake_service': Decimal('999.00'),
    'wash': Decimal('399.00'),
    'repair': Decimal('1999.00'),
    'inspection': Decimal('499.00'),
    'other': Decimal('999.00'),
}


def resolve_service_cost(booking) -> Decimal:
    """Prefer garage default General Service amount for invoice calculation."""
    garage = getattr(booking, 'garage', None)
    if garage is not None and getattr(garage, 'default_service_cost', None) is not None:
        return Decimal(garage.default_service_cost)
    return DEFAULT_SERVICE_COSTS.get(booking.service_type, Decimal('899.00'))


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

    if instance.status == BookingStatus.COMPLETED and not instance.completed_at:
        instance.completed_at = timezone.now()
    if instance.status != BookingStatus.COMPLETED:
        instance.completed_at = instance.completed_at  # keep historical if any


@receiver(post_save, sender=Booking)
def notify_booking_events(sender, instance, created, **kwargs):
    try:
        from apps.notifications.tasks import (
            _enqueue,
            notify_booking_created,
            send_booking_status_notification,
        )
        if created:
            _enqueue(notify_booking_created, instance.pk)
            return
        old_status = getattr(instance, '_old_status', None)
        if old_status == instance.status:
            return
        _enqueue(send_booking_status_notification, instance.pk, instance.status)
    except Exception:
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

    # Ensure garage is loaded for default cost.
    if instance.garage_id and not hasattr(instance, '_garage_prefetched'):
        try:
            instance.garage  # noqa: B018 — touch FK
        except Exception:
            pass

    service_cost = resolve_service_cost(instance)
    Invoice.objects.create(
        booking=instance,
        service_cost=service_cost,
        parts_cost=Decimal('0.00'),
        payment_status=PaymentStatus.PENDING,
    )
