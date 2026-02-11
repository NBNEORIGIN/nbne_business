"""Add booking_date, booking_time fields and make time_slot nullable for staff-aware bookings."""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0003_disclaimer_models'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='time_slot',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='bookings',
                to='bookings.timeslot',
            ),
        ),
        migrations.AddField(
            model_name='booking',
            name='booking_date',
            field=models.DateField(
                blank=True,
                db_index=True,
                help_text='Direct date for staff-aware bookings',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='booking',
            name='booking_time',
            field=models.TimeField(
                blank=True,
                help_text='Direct start time for staff-aware bookings',
                null=True,
            ),
        ),
    ]
