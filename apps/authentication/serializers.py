from rest_framework import serializers

from apps.users.models import UserRole


class FirebaseAuthSerializer(serializers.Serializer):
    firebase_uid = serializers.CharField(max_length=128)
    phone = serializers.CharField(max_length=20)
    id_token = serializers.CharField(required=False, allow_blank=True)
    name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=UserRole.choices, required=False)
    fcm_token = serializers.CharField(required=False, allow_blank=True)


class PhoneAuthSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)
    name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=UserRole.choices, required=False)
