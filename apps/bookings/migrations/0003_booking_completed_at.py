from django.db import migrations, models
from django.db.models import F


def backfill_completed_at(apps, schema_editor):
    Booking = apps.get_model('bookings', 'Booking')
    Booking.objects.filter(status='completed', completed_at__isnull=True).update(
        completed_at=F('updated_at'),
    )


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='completed_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='service_reminder_sent_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_completed_at, migrations.RunPython.noop),
    ]
