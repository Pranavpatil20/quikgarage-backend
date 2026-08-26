from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('garages', '0004_garage_rates'),
    ]

    operations = [
        migrations.AddField(
            model_name='garage',
            name='weekly_hours',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text=(
                    'Per-weekday hours. Keys: mon..sun. '
                    'Value: {"open": bool, "opening_time": "HH:MM:SS", "closing_time": "HH:MM:SS"}. '
                    'Missing day = open with default opening/closing times.'
                ),
            ),
        ),
    ]
