from datetime import timedelta

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0003_booking_completed_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='service_type',
            field=models.CharField(
                help_text='Comma-separated service type keys, e.g. oil_change,brake_service',
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name='booking',
            name='service_items',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Parts/labour used during service: [{category,name,qty,rate,gst_percent,amount}]',
            ),
        ),
    ]
