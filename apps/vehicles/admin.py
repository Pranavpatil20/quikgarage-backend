from django.contrib import admin

from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('vehicle_number', 'make_model', 'vehicle_type', 'customer', 'is_primary')
    search_fields = ('vehicle_number', 'make_model', 'customer__phone')
