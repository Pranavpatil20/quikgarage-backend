from rest_framework import serializers

from .models import User, UserRole


class UserSerializer(serializers.ModelSerializer):
    subscription_active = serializers.SerializerMethodField()
    is_payment_locked = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'phone', 'name', 'role', 'firebase_uid',
            'trial_ends_at', 'subscription_paid_until',
            'subscription_active', 'is_payment_locked',
            'created_at', 'updated_at',
        )
        read_only_fields = (
            'id', 'created_at', 'updated_at', 'firebase_uid',
            'trial_ends_at', 'subscription_paid_until',
            'subscription_active', 'is_payment_locked',
        )

    def get_subscription_active(self, obj):
        return obj.subscription_active

    def get_is_payment_locked(self, obj):
        return obj.is_payment_locked


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('name', 'fcm_token')


class RoleSelectionSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=UserRole.choices)
