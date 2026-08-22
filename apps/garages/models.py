from decimal import Decimal

from django.conf import settings
from django.db import models


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
