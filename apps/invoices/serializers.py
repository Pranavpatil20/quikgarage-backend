from rest_framework import serializers

from apps.bookings.serializers import BookingSerializer

from .models import Invoice


class InvoiceSerializer(serializers.ModelSerializer):
    booking_detail = BookingSerializer(source='booking', read_only=True)

    class Meta:
        model = Invoice
        fields = (
            'id', 'booking', 'booking_detail', 'service_cost', 'parts_cost',
            'total_amount', 'line_items', 'payment_status', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'total_amount', 'created_at', 'updated_at')

    def validate_booking(self, booking):
        request = self.context['request']
        if booking.garage.owner_id != request.user.id:
            raise serializers.ValidationError('Booking does not belong to your garage.')
        if hasattr(booking, 'invoice') and (
            not self.instance or self.instance.booking_id != booking.id
        ):
            raise serializers.ValidationError('Invoice already exists for this booking.')
        return booking
