from rest_framework import serializers

from .models import Vehicle


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = (
            'id', 'customer', 'vehicle_number', 'vehicle_type',
            'make_model', 'is_primary', 'created_at',
        )
        read_only_fields = ('id', 'customer', 'created_at')

    def create(self, validated_data):
        validated_data['customer'] = self.context['request'].user
        return super().create(validated_data)
