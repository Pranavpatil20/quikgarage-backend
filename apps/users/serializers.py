from rest_framework import serializers

from .models import User, UserRole


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'phone', 'name', 'role', 'firebase_uid',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'firebase_uid')


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('name', 'fcm_token')


class RoleSelectionSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=UserRole.choices)
