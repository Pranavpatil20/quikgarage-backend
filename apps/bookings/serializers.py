from rest_framework import serializers

from apps.garages.models import Garage
from apps.garages.serializers import GarageSerializer
from apps.users.serializers import UserSerializer
from apps.vehicles.models import Vehicle
from apps.vehicles.serializers import VehicleSerializer

from apps.users.subscription import owner_has_active_subscription

from .models import Booking, BookingStatus
from .services import validate_booking_slot, validate_vehicle_ownership


class BookingSerializer(serializers.ModelSerializer):
    customer_detail = UserSerializer(source='customer', read_only=True)
    garage_detail = GarageSerializer(source='garage', read_only=True)
    vehicle_detail = VehicleSerializer(source='vehicle', read_only=True)
    can_cancel = serializers.BooleanField(source='can_customer_cancel', read_only=True)

    class Meta:
        model = Booking
        fields = (
            'id', 'customer', 'customer_detail', 'garage', 'garage_detail',
            'vehicle', 'vehicle_detail', 'service_type', 'booking_date',
            'time_slot', 'notes', 'status', 'can_cancel', 'service_items',
            'created_at', 'updated_at', 'completed_at',
        )
        read_only_fields = (
            'id', 'customer', 'status', 'created_at', 'updated_at', 'completed_at',
        )

    def validate(self, attrs):
        request = self.context['request']
        garage = attrs.get('garage') or getattr(self.instance, 'garage', None)
        vehicle = attrs.get('vehicle') or getattr(self.instance, 'vehicle', None)
        booking_date = attrs.get('booking_date') or getattr(self.instance, 'booking_date', None)
        time_slot = attrs.get('time_slot') or getattr(self.instance, 'time_slot', None)

        if vehicle:
            validate_vehicle_ownership(request.user, vehicle)

        if garage:
            owner = getattr(garage, 'owner', None)
            if owner is None:
                owner = garage.owner
            if not owner_has_active_subscription(owner):
                raise serializers.ValidationError(
                    {'garage': 'This garage is not available for booking.'},
                )

        if garage and booking_date and time_slot:
            validate_booking_slot(
                garage, booking_date, time_slot,
                exclude_booking_id=getattr(self.instance, 'pk', None),
            )

        return attrs

    def create(self, validated_data):
        validated_data['customer'] = self.context['request'].user
        return super().create(validated_data)


class OwnerBookingCreateSerializer(serializers.ModelSerializer):
    customer_phone = serializers.CharField(write_only=True)
    vehicle_number = serializers.CharField(write_only=True)
    make_model = serializers.CharField(required=False, allow_blank=True)
    vehicle_type = serializers.CharField(required=False, allow_blank=True, default='bike')

    class Meta:
        model = Booking
        fields = (
            'customer_phone', 'vehicle_number', 'make_model', 'vehicle_type',
            'garage', 'service_type', 'booking_date', 'time_slot', 'notes',
        )

    def validate_customer_phone(self, value):
        from apps.authentication.serializers import validate_indian_phone
        return validate_indian_phone(value)

    def validate(self, attrs):
        from apps.users.models import User, UserRole

        request = self.context['request']
        garage = attrs.get('garage')
        if garage.owner_id != request.user.id:
            raise serializers.ValidationError({'garage': 'Not your garage.'})

        phone = attrs.pop('customer_phone')
        vehicle_number = attrs.pop('vehicle_number')
        make_model = attrs.pop('make_model', '')
        vehicle_type = (attrs.pop('vehicle_type', None) or 'bike').lower()
        if vehicle_type not in ('bike', 'car'):
            vehicle_type = 'bike'

        customer, _ = User.objects.get_or_create(
            phone=phone,
            defaults={'name': phone, 'role': UserRole.CUSTOMER},
        )
        vehicle, created = Vehicle.objects.get_or_create(
            customer=customer,
            vehicle_number=vehicle_number.upper(),
            defaults={'make_model': make_model, 'vehicle_type': vehicle_type},
        )
        if not created and vehicle_type:
            vehicle.vehicle_type = vehicle_type
            if make_model:
                vehicle.make_model = make_model
            vehicle.save(update_fields=['vehicle_type', 'make_model'])

        attrs['customer'] = customer
        attrs['vehicle'] = vehicle
        validate_booking_slot(garage, attrs['booking_date'], attrs['time_slot'])
        return attrs

    def create(self, validated_data):
        return Booking.objects.create(**validated_data)

    def to_representation(self, instance):
        return BookingSerializer(instance, context=self.context).data


class BookingStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ('status',)

    def validate_status(self, value):
        instance = self.instance
        # Owners can move forward through the flow without dead-ends.
        # Confirmed → Completed is allowed so "Mark Completed" works without
        # requiring an In Progress step first.
        allowed = {
            BookingStatus.PENDING: {
                BookingStatus.CONFIRMED,
                BookingStatus.IN_PROGRESS,
                BookingStatus.COMPLETED,
                BookingStatus.CANCELLED,
            },
            BookingStatus.CONFIRMED: {
                BookingStatus.IN_PROGRESS,
                BookingStatus.COMPLETED,
                BookingStatus.CANCELLED,
            },
            BookingStatus.IN_PROGRESS: {
                BookingStatus.COMPLETED,
                BookingStatus.CANCELLED,
            },
            BookingStatus.COMPLETED: set(),
            BookingStatus.CANCELLED: set(),
        }
        if value not in allowed.get(instance.status, set()):
            raise serializers.ValidationError(
                f'Cannot transition from {instance.status} to {value}.',
            )
        return value

    def to_representation(self, instance):
        return BookingSerializer(instance, context=self.context).data


class OwnerBookingServiceItemsSerializer(serializers.ModelSerializer):
    """Owner updates parts/labour used while service is in progress."""

    class Meta:
        model = Booking
        fields = ('service_items', 'service_type', 'notes')

    def validate_service_items(self, value):
        if value is None:
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError('service_items must be a list.')
        cleaned = []
        for raw in value:
            if not isinstance(raw, dict):
                raise serializers.ValidationError('Each service item must be an object.')
            name = str(raw.get('name') or '').strip()
            if not name:
                raise serializers.ValidationError('Each item needs a name.')
            try:
                qty = float(raw.get('qty', 1) or 1)
                rate = float(raw.get('rate', 0) or 0)
            except (TypeError, ValueError) as exc:
                raise serializers.ValidationError('Invalid qty/rate.') from exc
            amount = qty * rate
            if raw.get('amount') is not None:
                try:
                    amount = float(raw.get('amount'))
                except (TypeError, ValueError):
                    pass
            cleaned.append({
                'category': str(raw.get('category') or 'parts').lower(),
                'name': name,
                'qty': qty,
                'rate': rate,
                'gst_percent': 0,
                'amount': round(amount, 2),
            })
        return cleaned

    def to_representation(self, instance):
        return BookingSerializer(instance, context=self.context).data
