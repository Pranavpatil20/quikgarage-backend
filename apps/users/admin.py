from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'phone', 'name', 'role', 'subscription_active_display',
        'trial_ends_at', 'subscription_paid_until', 'is_active', 'created_at',
    )
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('phone', 'name', 'firebase_uid')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Profile', {'fields': ('name', 'role', 'firebase_uid', 'fcm_token')}),
        (
            'Subscription',
            {
                'fields': (
                    'trial_ends_at',
                    'subscription_paid_until',
                    'subscription_active_display',
                ),
            },
        ),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    readonly_fields = (
        'created_at', 'updated_at', 'last_login', 'trial_ends_at',
        'subscription_active_display',
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'name', 'role', 'password1', 'password2'),
        }),
    )

    @admin.display(boolean=True, description='Subscription active')
    def subscription_active_display(self, obj):
        return obj.subscription_active
