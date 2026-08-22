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
    """Sum garage service rates for selected types, else garage default / fallbacks."""
    garage = getattr(booking, 'garage', None)
    keys = [k.strip() for k in (booking.service_type or '').split(',') if k.strip()]
    if not keys:
        keys = ['general_service']

    rates = {}
    if garage is not None and isinstance(getattr(garage, 'service_rates', None), dict):
        rates = garage.service_rates

    total = Decimal('0.00')
    matched = False
    for key in keys:
        raw = rates.get(key)
        if raw is not None and str(raw).strip() != '':
            total += Decimal(str(raw))
            matched = True
        elif key in DEFAULT_SERVICE_COSTS:
            total += DEFAULT_SERVICE_COSTS[key]
            matched = True

    if matched and total > 0:
        return total

    if garage is not None and getattr(garage, 'default_service_cost', None) is not None:
        return Decimal(garage.default_service_cost)
    return DEFAULT_SERVICE_COSTS.get(keys[0], Decimal('899.00'))


def _line_amount(item: dict) -> Decimal:
    try:
        return Decimal(str(item.get('amount', 0)))
    except Exception:
        return Decimal('0.00')


def build_invoice_from_booking(booking) -> tuple[Decimal, Decimal, list]:
    """Return (service_cost, parts_cost, line_items) from booking.service_items or defaults."""
    items = list(booking.service_items or [])
    if items:
        service = Decimal('0.00')
        parts = Decimal('0.00')
        for item in items:
            amt = _line_amount(item)
            cat = (item.get('category') or 'parts').lower()
            if cat == 'labour':
                service += amt
            else:
                parts += amt
        return service, parts, items

    service = resolve_service_cost(booking)
    labour_line = {
        'category': 'labour',
        'name': booking.service_type or 'general_service',
        'qty': 1,
        'rate': float(service),
        'gst_percent': 0,
        'amount': float(service),
    }
    return service, Decimal('0.00'), [labour_line]


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

    service_cost, parts_cost, line_items = build_invoice_from_booking(instance)
    Invoice.objects.create(
        booking=instance,
        service_cost=service_cost,
        parts_cost=parts_cost,
        line_items=line_items,
        payment_status=PaymentStatus.PENDING,
    )
