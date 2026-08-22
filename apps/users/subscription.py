from datetime import timedelta

from django.db.models import Q
from django.utils import timezone


def owner_has_active_subscription(owner) -> bool:
    """Return True if owner is within trial or has paid through today."""
    if not owner.is_owner:
        return True
    now = timezone.now()
    if owner.trial_ends_at and now < owner.trial_ends_at:
        return True
    if owner.subscription_paid_until and now.date() <= owner.subscription_paid_until:
        return True
    return False


def active_owner_filter(prefix: str = '') -> Q:
    """Q filter for owners with active subscription (trial or paid)."""
    field = lambda name: f'{prefix}{name}' if prefix else name
    now = timezone.now()
    today = now.date()
    return Q(**{f'{field("trial_ends_at")}__gt': now}) | Q(
        **{f'{field("subscription_paid_until")}__gte': today},
    )


def filter_garages_for_customers(queryset):
    """Return only garages whose owner has an active subscription."""
    return queryset.filter(active_owner_filter(prefix='owner__'))


def trial_ends_at_for_new_owner():
    return timezone.now() + timedelta(days=7)
