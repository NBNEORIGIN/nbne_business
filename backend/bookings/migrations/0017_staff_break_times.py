from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0016_backfill_tenant_nonnull'),
    ]

    operations = [
        migrations.AddField(
            model_name='staff',
            name='break_start',
            field=models.TimeField(blank=True, help_text='Daily break start (e.g. lunch)', null=True),
        ),
        migrations.AddField(
            model_name='staff',
            name='break_end',
            field=models.TimeField(blank=True, help_text='Daily break end', null=True),
        ),
    ]
