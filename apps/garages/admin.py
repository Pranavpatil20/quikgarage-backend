from django.contrib import admin

from .models import Garage


@admin.register(Garage)
class GarageAdmin(admin.ModelAdmin):
    list_display = ('garage_name', 'owner', 'opening_time', 'closing_time')
    search_fields = ('garage_name', 'owner__phone', 'owner__name')
