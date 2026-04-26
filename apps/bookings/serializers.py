from datetime import datetime, timedelta
from django.db.models import Sum
from rest_framework import serializers

from apps.accounts.models import User, UserRole
from apps.customers.models import CustomerProfile, Vehicle
from .models import Booking, BookingStatus, Invoice


class BookingSerializer(serializers.ModelSerializer):
    owner_id = serializers.IntegerField(write_only=True, required=False)
    customer = serializers.PrimaryKeyRelatedField(
        queryset=CustomerProfile.objects.all(),
        required=False,
    )
    vehicle = serializers.PrimaryKeyRelatedField(
        queryset=Vehicle.objects.all(),
        required=False,
    )
    customer_phone_input = serializers.CharField(write_only=True, required=False)
    vehicle_number_input = serializers.CharField(write_only=True, required=False)
    customer_name = serializers.CharField(source="customer.user.full_name", read_only=True)
    customer_phone = serializers.CharField(source="customer.user.phone_number", read_only=True)
    vehicle_number = serializers.CharField(source="vehicle.vehicle_number", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "owner",
            "owner_id",
            "customer",
            "vehicle",
            "customer_phone_input",
            "vehicle_number_input",
            "service_type",
            "custom_service_type",
            "booking_date",
            "time_slot",
            "notes",
            "status",
            "created_at",
            "customer_name",
            "customer_phone",
            "vehicle_number",
        ]
        read_only_fields = ["owner", "status", "created_at"]

    def validate(self, attrs):
        request = self.context["request"]
        booking_date = attrs["booking_date"]
        time_slot = attrs["time_slot"]
        target_owner = request.user
        if request.user.role == "customer":
            owner_id = attrs.get("owner_id")
            if not owner_id:
                raise serializers.ValidationError("owner_id is required for customer booking.")
            from apps.accounts.models import User

            target_owner = User.objects.filter(id=owner_id, role="owner").first()
            if not target_owner:
                raise serializers.ValidationError("Invalid owner_id.")

        exists = Booking.objects.filter(
            owner=target_owner, booking_date=booking_date, time_slot=time_slot
        ).exists()
        if exists:
            raise serializers.ValidationError("Selected slot is already booked.")
        return attrs

    def create(self, validated_data):
        request_user = self.context["request"].user
        owner_id = validated_data.pop("owner_id", None)
        customer_phone_input = validated_data.pop("customer_phone_input", None)
        vehicle_number_input = validated_data.pop("vehicle_number_input", None)
        customer_input = validated_data.pop("customer", None)
        vehicle_input = validated_data.pop("vehicle", None)

        if request_user.role == "owner":
            owner = request_user
        else:
            if owner_id is None:
                raise serializers.ValidationError("owner_id is required for customer booking.")
            owner = User.objects.filter(id=owner_id, role="owner").first()
            if not owner:
                raise serializers.ValidationError("Valid owner_id is required.")

        customer = None
        if customer_input:
            customer = customer_input if customer_input.owner_id == owner.id else None
        elif customer_phone_input:
            customer = CustomerProfile.objects.filter(user__phone_number=customer_phone_input, owner=owner).first()
            if not customer and request_user.role == "owner":
                customer_user, _ = User.objects.get_or_create(
                    phone_number=customer_phone_input,
                    defaults={
                        "full_name": f"Customer {customer_phone_input}",
                        "role": UserRole.CUSTOMER,
                    },
                )
                customer, _ = CustomerProfile.objects.get_or_create(user=customer_user, owner=owner)
        if not customer:
            raise serializers.ValidationError("Valid customer or customer_phone is required.")
        if request_user.role == "customer" and customer.user_id != request_user.id:
            raise serializers.ValidationError("Customers can only book for their own profile.")

        vehicle = None
        if vehicle_input:
            vehicle = vehicle_input if vehicle_input.customer_id == customer.id else None
        elif vehicle_number_input:
            vehicle = Vehicle.objects.filter(
                vehicle_number__iexact=vehicle_number_input, customer=customer
            ).first()
            if not vehicle and request_user.role == "owner":
                vehicle = Vehicle.objects.create(
                    customer=customer,
                    vehicle_number=vehicle_number_input,
                )
        if not vehicle:
            raise serializers.ValidationError("Valid vehicle or vehicle_number_input is required.")

        return Booking.objects.create(owner=owner, customer=customer, vehicle=vehicle, **validated_data)


class BookingStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["status"]


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ["id", "booking", "service_cost", "parts_cost", "total_amount", "is_paid"]
        read_only_fields = ["total_amount"]


class DashboardSerializer(serializers.Serializer):
    today_bookings = serializers.IntegerField()
    pending_bookings = serializers.IntegerField()
    upcoming_bookings = serializers.IntegerField()
    total_customers = serializers.IntegerField()
    today_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    week_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    completed_bookings = serializers.IntegerField()
    cancelled_bookings = serializers.IntegerField()

    @staticmethod
    def build(owner, today, week_start):
        booking_qs = Booking.objects.filter(owner=owner)
        revenue = Invoice.objects.filter(booking__owner=owner)
        return {
            "today_bookings": booking_qs.filter(booking_date=today).count(),
            "pending_bookings": booking_qs.filter(status=BookingStatus.PENDING).count(),
            "upcoming_bookings": booking_qs.filter(booking_date__gt=today).count(),
            "total_customers": booking_qs.values("customer").distinct().count(),
            "today_revenue": revenue.filter(booking__booking_date=today).aggregate(v=Sum("total_amount"))["v"] or 0,
            "week_revenue": revenue.filter(booking__booking_date__gte=week_start).aggregate(v=Sum("total_amount"))["v"] or 0,
            "completed_bookings": booking_qs.filter(status=BookingStatus.COMPLETED).count(),
            "cancelled_bookings": booking_qs.filter(status=BookingStatus.CANCELLED).count(),
        }


class SlotAvailabilitySerializer(serializers.Serializer):
    date = serializers.DateField()
    slots = serializers.ListField(child=serializers.DictField())

    @staticmethod
    def build(owner, booking_date):
        start = datetime.strptime("09:00", "%H:%M")
        end = datetime.strptime("20:00", "%H:%M")
        all_slots = []
        cursor = start
        while cursor <= end:
            all_slots.append(cursor.strftime("%H:%M:%S"))
            cursor += timedelta(minutes=30)

        booked = set(
            Booking.objects.filter(owner=owner, booking_date=booking_date).values_list("time_slot", flat=True)
        )
        booked_str = {slot.strftime("%H:%M:%S") for slot in booked}

        return {
            "date": booking_date,
            "slots": [{"time": slot, "available": slot not in booked_str} for slot in all_slots],
        }
