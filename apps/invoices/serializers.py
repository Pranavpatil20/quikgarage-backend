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

    def validate_line_items(self, items):
        if items is None:
            return []
        if not isinstance(items, list):
            raise serializers.ValidationError('line_items must be a list.')
        cleaned = []
        for raw in items:
            if not isinstance(raw, dict):
                continue
            name = str(raw.get('name') or '').strip()
            if not name:
                raise serializers.ValidationError('Each line item needs a name.')
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
