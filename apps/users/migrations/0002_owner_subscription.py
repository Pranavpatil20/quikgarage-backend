from datetime import timedelta

from django.db import migrations, models
from django.utils import timezone


def backfill_owner_trials(apps, schema_editor):
    User = apps.get_model('users', 'User')
    for user in User.objects.filter(role='owner', trial_ends_at__isnull=True):
        if user.created_at:
            user.trial_ends_at = user.created_at + timedelta(days=7)
        else:
            user.trial_ends_at = timezone.now() + timedelta(days=7)
        user.save(update_fields=['trial_ends_at'])


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='trial_ends_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='subscription_paid_until',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_owner_trials, migrations.RunPython.noop),
    ]
