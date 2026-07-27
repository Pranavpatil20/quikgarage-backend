from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'vehicle', 'garage', 'booking_date', 'time_slot', 'status', 'service_type',
    )
    list_filter = ('status', 'booking_date', 'garage')
    search_fields = ('vehicle__vehicle_number', 'customer__phone')
