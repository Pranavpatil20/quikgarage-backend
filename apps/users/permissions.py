from rest_framework import permissions

from .subscription import owner_has_active_subscription


class OwnerSubscriptionActive(permissions.BasePermission):
    """Customers always pass; owners must have active trial or paid subscription."""

    message = 'Subscription payment required.'
    code = 'subscription_required'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if not user.is_owner:
            return True
        return owner_has_active_subscription(user)
