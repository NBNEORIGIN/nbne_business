from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkingHours',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day_of_week', models.IntegerField(choices=[(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')], db_index=True)),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('break_minutes', models.PositiveIntegerField(default=0, help_text='Unpaid break in minutes')),
                ('is_active', models.BooleanField(default=True)),
                ('staff', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='working_hours', to='staff.staffprofile')),
            ],
            options={
                'db_table': 'staff_working_hours',
                'ordering': ['staff', 'day_of_week', 'start_time'],
                'indexes': [models.Index(fields=['staff', 'day_of_week'], name='staff_workin_staff_i_idx')],
            },
        ),
        migrations.CreateModel(
            name='TimesheetEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(db_index=True)),
                ('scheduled_start', models.TimeField(blank=True, null=True)),
                ('scheduled_end', models.TimeField(blank=True, null=True)),
                ('scheduled_break_minutes', models.PositiveIntegerField(default=0)),
                ('actual_start', models.TimeField(blank=True, null=True)),
                ('actual_end', models.TimeField(blank=True, null=True)),
                ('actual_break_minutes', models.PositiveIntegerField(default=0)),
                ('status', models.CharField(choices=[('SCHEDULED', 'Scheduled'), ('WORKED', 'Worked'), ('LATE', 'Late Arrival'), ('LEFT_EARLY', 'Left Early'), ('ABSENT', 'Absent'), ('SICK', 'Sick'), ('HOLIDAY', 'Holiday'), ('AMENDED', 'Amended')], db_index=True, default='SCHEDULED', max_length=20)),
                ('notes', models.TextField(blank=True, default='')),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('staff', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='timesheet_entries', to='staff.staffprofile')),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_timesheets', to='staff.staffprofile')),
            ],
            options={
                'db_table': 'staff_timesheet',
                'ordering': ['-date', 'staff__display_name'],
                'unique_together': {('staff', 'date')},
                'indexes': [models.Index(fields=['staff', 'date'], name='staff_timesh_staff_i_idx')],
            },
        ),
    ]
