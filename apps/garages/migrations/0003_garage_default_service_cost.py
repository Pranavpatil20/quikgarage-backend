from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('garages', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='garage',
            name='default_service_cost',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('899.00'),
                help_text='Default General Service amount used when creating invoices.',
                max_digits=10,
            ),
        ),
    ]
