from datetime import timedelta
import random

from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import OtpRequest, User, UserRole


class SendOtpSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)

    def create(self, validated_data):
        otp = f"{random.randint(100000, 999999)}"
        OtpRequest.objects.create(
            phone_number=validated_data["phone_number"],
            otp_code=otp,
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        return {"phone_number": validated_data["phone_number"], "otp": otp}


class VerifyOtpSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    otp_code = serializers.CharField(max_length=6)
    role = serializers.ChoiceField(choices=UserRole.choices)
    full_name = serializers.CharField(max_length=120, required=False, allow_blank=True)

    def validate(self, attrs):
        otp_request = (
            OtpRequest.objects.filter(
                phone_number=attrs["phone_number"], otp_code=attrs["otp_code"], is_verified=False
            )
            .order_by("-created_at")
            .first()
        )
        if not otp_request or otp_request.expires_at < timezone.now():
            raise serializers.ValidationError("Invalid or expired OTP.")
        attrs["otp_request"] = otp_request
        return attrs

    def create(self, validated_data):
        otp_request = validated_data["otp_request"]
        otp_request.is_verified = True
        otp_request.save(update_fields=["is_verified"])

        user, created = User.objects.get_or_create(
            phone_number=validated_data["phone_number"],
            defaults={
                "full_name": validated_data.get("full_name", "").strip() or "User",
                "role": validated_data["role"],
            },
        )
        if not created and validated_data.get("full_name"):
            user.full_name = validated_data["full_name"]
            user.save(update_fields=["full_name"])

        refresh = RefreshToken.for_user(user)
        return {
            "user_id": user.id,
            "full_name": user.full_name,
            "phone_number": user.phone_number,
            "role": user.role,
            "garage_name": user.garage_name,
            "garage_timing": user.garage_timing,
            "default_general_service_amount": str(user.default_general_service_amount),
            "app_language": user.app_language,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "phone_number",
            "role",
            "garage_name",
            "garage_timing",
            "default_general_service_amount",
            "app_language",
        ]
        read_only_fields = ["id", "phone_number", "role"]
