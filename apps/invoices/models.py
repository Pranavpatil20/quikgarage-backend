from decimal import Decimal

from django.db import models


class PaymentStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PAID = 'paid', 'Paid'
    PARTIAL = 'partial', 'Partial'
    REFUNDED = 'refunded', 'Refunded'


class Invoice(models.Model):
    booking = models.OneToOneField(
        'bookings.Booking',
        on_delete=models.CASCADE,
        related_name='invoice',
    )
    service_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    parts_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    line_items = models.JSONField(
        default=list,
        blank=True,
        help_text='Invoice lines: [{category,name,qty,rate,gst_percent,amount}]',
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'invoices'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.line_items:
            service = Decimal('0.00')
            parts = Decimal('0.00')
            for item in self.line_items:
                try:
                    amt = Decimal(str(item.get('amount', 0)))
                except Exception:
                    amt = Decimal('0.00')
                cat = (item.get('category') or 'parts').lower()
                if cat == 'labour':
                    service += amt
                else:
                    parts += amt
            self.service_cost = service
            self.parts_cost = parts
        self.total_amount = self.service_cost + self.parts_cost
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Invoice #{self.pk} - ₹{self.total_amount}'
