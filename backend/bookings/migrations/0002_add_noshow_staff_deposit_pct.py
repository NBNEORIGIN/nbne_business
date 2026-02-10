from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bookings', '0001_initial'),
    ]

    operations = [
        # Add deposit_percentage to Service
        migrations.AddField(
            model_name='service',
            name='deposit_percentage',
            field=models.PositiveIntegerField(
                default=0,
                help_text='Default deposit as % of price (0=use deposit_pence instead)',
            ),
        ),
        # Add assigned_staff FK to Booking
        migrations.AddField(
            model_name='booking',
            name='assigned_staff',
            field=models.ForeignKey(
                blank=True,
                help_text='Staff member assigned to this booking',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='assigned_bookings',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        # Update status choices to include NO_SHOW
        migrations.AlterField(
            model_name='booking',
            name='status',
            field=models.CharField(
                choices=[
                    ('PENDING', 'Pending'),
                    ('PENDING_PAYMENT', 'Pending Payment'),
                    ('CONFIRMED', 'Confirmed'),
                    ('COMPLETED', 'Completed'),
                    ('NO_SHOW', 'No Show'),
                    ('CANCELLED', 'Cancelled'),
                ],
                db_index=True,
                default='PENDING',
                max_length=20,
            ),
        ),
    ]
