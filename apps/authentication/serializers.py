from rest_framework import serializers

from apps.users.models import UserRole


def normalize_phone(phone: str) -> str:
    phone = (phone or '').strip().replace(' ', '')
    digits = ''.join(c for c in phone if c.isdigit())
    if phone.startswith('+') and len(digits) >= 10:
        return f'+{digits}'
    if len(digits) == 10:
        return f'+91{digits}'
    if digits.startswith('91') and len(digits) == 12:
        return f'+{digits}'
    if not phone.startswith('+') and digits:
        return f'+{digits}'
    return phone


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


class PasswordLoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=UserRole.choices, required=False)


class RegisterSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)
    name = serializers.CharField(max_length=120)
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=UserRole.choices)
    garage_name = serializers.CharField(max_length=200, required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        if attrs['role'] == UserRole.OWNER and not (attrs.get('garage_name') or '').strip():
            raise serializers.ValidationError({'garage_name': 'Garage name is required for owners.'})
        return attrs
