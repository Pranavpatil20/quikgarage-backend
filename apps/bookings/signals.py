from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Booking


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
    from apps.notifications.tasks import send_booking_status_notification
    send_booking_status_notification.delay(instance.pk, instance.status)
