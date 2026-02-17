from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0006_training_course_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='staffprofile',
            name='pay_type',
            field=models.CharField(
                choices=[('salaried', 'Salaried'), ('hourly', 'Hourly')],
                default='hourly',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='staffprofile',
            name='overtime_eligible',
            field=models.BooleanField(
                default=False,
                help_text='If salaried, can they claim overtime?',
            ),
        ),
        migrations.AddField(
            model_name='staffprofile',
            name='contracted_hours_per_week',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Contracted weekly hours (e.g. 37.5)',
                max_digits=5,
            ),
        ),
        migrations.AddField(
            model_name='staffprofile',
            name='hourly_rate',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='£/hour for hourly staff or overtime rate',
                max_digits=8,
            ),
        ),
        migrations.AddField(
            model_name='staffprofile',
            name='annual_leave_days',
            field=models.DecimalField(
                decimal_places=1,
                default=28,
                help_text='Annual leave allowance in days (UK default 28 inc bank hols)',
                max_digits=5,
            ),
        ),
    ]
