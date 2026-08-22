from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='line_items',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Invoice lines: [{category,name,qty,rate,gst_percent,amount}]',
            ),
        ),
    ]
