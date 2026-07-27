from django.contrib import admin

from .models import Invoice


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('booking', 'total_amount', 'payment_status', 'created_at')
    list_filter = ('payment_status',)
