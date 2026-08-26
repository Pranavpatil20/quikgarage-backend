from datetime import time
from decimal import Decimal

from django.conf import settings
from django.db import models

WEEKDAY_KEYS = ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')


def _parse_time(value, fallback: time) -> time:
    if value is None or value == '':
        return fallback
    if isinstance(value, time):
        return value
    raw = str(value).strip()
    parts = raw.split(':')
    try:
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        second = int(parts[2]) if len(parts) > 2 else 0
        return time(hour, minute, second)
    except (TypeError, ValueError, IndexError):
        return fallback


class Garage(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='garages',
    )
    garage_name = models.CharField(max_length=200)
    address = models.TextField()
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    weekly_hours = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            'Per-weekday hours. Keys: mon..sun. '
            'Value: {"open": bool, "opening_time": "HH:MM:SS", "closing_time": "HH:MM:SS"}. '
            'Missing day = open with default opening/closing times.'
        ),
    )
    default_service_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('899.00'),
        help_text='Default General Service amount used when creating invoices.',
    )
    service_rates = models.JSONField(
        default=dict,
        blank=True,
        help_text='Default prices by service type key, e.g. {"oil_change": "499"}',
    )
    part_rates = models.JSONField(
        default=dict,
        blank=True,
        help_text='Default prices by part name, e.g. {"Engine Oil 10W30": "450"}',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'garages'
        ordering = ['garage_name']

    def __str__(self):
        return self.garage_name

    @staticmethod
    def weekday_key(booking_date) -> str:
        # Python: Monday=0 .. Sunday=6
        return WEEKDAY_KEYS[booking_date.weekday()]

    def hours_for_date(self, booking_date) -> tuple[bool, time, time]:
        """Return (is_open, opening, closing) for a calendar date."""
        key = self.weekday_key(booking_date)
        day = None
        if isinstance(self.weekly_hours, dict):
            day = self.weekly_hours.get(key)

        if not isinstance(day, dict):
            return True, self.opening_time, self.closing_time

        if day.get('open') is False:
            return False, self.opening_time, self.closing_time

        opening = _parse_time(day.get('opening_time'), self.opening_time)
        closing = _parse_time(day.get('closing_time'), self.closing_time)
        return True, opening, closing
