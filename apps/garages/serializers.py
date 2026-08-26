from datetime import datetime, time

from rest_framework import serializers

from .models import WEEKDAY_KEYS, Garage


def _parse_hhmmss(value):
    if value is None or value == '':
        return None
    if isinstance(value, time):
        return value
    raw = str(value).strip()
    for fmt in ('%H:%M:%S', '%H:%M'):
        try:
            return datetime.strptime(raw, fmt).time()
        except ValueError:
            continue
    raise serializers.ValidationError(f'Invalid time "{value}". Use HH:MM or HH:MM:SS.')


class GarageSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.name', read_only=True)
    owner_phone = serializers.CharField(source='owner.phone', read_only=True)

    class Meta:
        model = Garage
        fields = (
            'id', 'owner', 'owner_name', 'owner_phone', 'garage_name', 'address',
            'opening_time', 'closing_time', 'weekly_hours', 'default_service_cost',
            'service_rates', 'part_rates',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'owner', 'created_at', 'updated_at')

    def validate_weekly_hours(self, value):
        if value in (None, ''):
            return {}
        if not isinstance(value, dict):
            raise serializers.ValidationError('weekly_hours must be an object.')

        cleaned = {}
        for key, day in value.items():
            key = str(key).lower().strip()
            if key not in WEEKDAY_KEYS:
                raise serializers.ValidationError(
                    f'Invalid weekday "{key}". Use mon, tue, wed, thu, fri, sat, sun.',
                )
            if not isinstance(day, dict):
                raise serializers.ValidationError(f'weekly_hours.{key} must be an object.')

            is_open = day.get('open', True)
            if isinstance(is_open, str):
                is_open = is_open.strip().lower() in ('1', 'true', 'yes', 'on')
            else:
                is_open = bool(is_open)

            entry = {'open': is_open}
            if is_open:
                opening = _parse_hhmmss(day.get('opening_time'))
                closing = _parse_hhmmss(day.get('closing_time'))
                if opening and closing and opening >= closing:
                    raise serializers.ValidationError(
                        {key: 'Closing time must be after opening time.'},
                    )
                if opening:
                    entry['opening_time'] = opening.strftime('%H:%M:%S')
                if closing:
                    entry['closing_time'] = closing.strftime('%H:%M:%S')
            cleaned[key] = entry
        return cleaned

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
