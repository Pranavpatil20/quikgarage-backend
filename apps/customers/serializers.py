from rest_framework import serializers

from apps.accounts.models import User, UserRole
from .models import CustomerProfile, Vehicle


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ["id", "vehicle_number", "brand", "model"]


class CustomerSerializer(serializers.ModelSerializer):
    vehicles = VehicleSerializer(many=True, required=False)
    phone_number = serializers.CharField(write_only=True)
    full_name = serializers.CharField(write_only=True)

    class Meta:
        model = CustomerProfile
        fields = ["id", "phone_number", "full_name", "whatsapp_opt_in", "vehicles"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["full_name"] = instance.user.full_name
        data["phone_number"] = instance.user.phone_number
        return data

    def create(self, validated_data):
        vehicles_data = validated_data.pop("vehicles", [])
        phone_number = validated_data.pop("phone_number")
        full_name = validated_data.pop("full_name")
        owner = self.context["request"].user

        user, _ = User.objects.get_or_create(
            phone_number=phone_number,
            defaults={"full_name": full_name, "role": UserRole.CUSTOMER},
        )
        customer = CustomerProfile.objects.create(user=user, owner=owner, **validated_data)
        for vehicle_data in vehicles_data:
            Vehicle.objects.create(customer=customer, **vehicle_data)
        return customer


class CustomerSelfProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name")
    phone_number = serializers.CharField(source="user.phone_number", read_only=True)

    class Meta:
        model = CustomerProfile
        fields = ["id", "full_name", "phone_number", "whatsapp_opt_in"]

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        if "full_name" in user_data:
            instance.user.full_name = user_data["full_name"]
            instance.user.save(update_fields=["full_name"])
        return super().update(instance, validated_data)
