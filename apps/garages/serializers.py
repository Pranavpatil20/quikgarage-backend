from rest_framework import serializers

from .models import Garage


class GarageSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.name', read_only=True)

    class Meta:
        model = Garage
        fields = (
            'id', 'owner', 'owner_name', 'garage_name', 'address',
            'opening_time', 'closing_time', 'default_service_cost',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'owner', 'created_at', 'updated_at')

    def validate(self, attrs):
        opening = attrs.get('opening_time') or getattr(self.instance, 'opening_time', None)
        closing = attrs.get('closing_time') or getattr(self.instance, 'closing_time', None)
        if opening and closing and opening >= closing:
            raise serializers.ValidationError(
                {'closing_time': 'Closing time must be after opening time.'},
            )
        return attrs

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)
