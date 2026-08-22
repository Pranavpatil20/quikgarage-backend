from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('garages', '0003_garage_default_service_cost'),
    ]

    operations = [
        migrations.AddField(
            model_name='garage',
            name='service_rates',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Default prices by service type key, e.g. {"oil_change": "499"}',
            ),
        ),
        migrations.AddField(
            model_name='garage',
            name='part_rates',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Default prices by part name, e.g. {"Engine Oil 10W30": "450"}',
            ),
        ),
    ]
