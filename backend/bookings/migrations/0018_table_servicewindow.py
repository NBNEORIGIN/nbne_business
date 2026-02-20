from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("tenants", "0004_tenantsettings_business_type"),
        ("bookings", "0017_staff_break_times"),
    ]

    operations = [
        # Restaurant models first (Table must exist before Booking FK)
        migrations.CreateModel(
            name="Table",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(help_text="e.g. Table 1, Window Booth, Terrace 3", max_length=100)),
                ("min_seats", models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)])),
                ("max_seats", models.IntegerField(default=4, validators=[django.core.validators.MinValueValidator(1)])),
                ("combinable", models.BooleanField(default=False, help_text="Can be combined with adjacent table")),
                ("zone", models.CharField(blank=True, default="", help_text="e.g. Main, Terrace, Private", max_length=100)),
                ("active", models.BooleanField(default=True)),
                ("sort_order", models.IntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "combine_with",
                    models.ForeignKey(
                        blank=True,
                        help_text="Adjacent table for combining",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="bookings.table",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tables",
                        to="tenants.tenantsettings",
                    ),
                ),
            ],
            options={
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.CreateModel(
            name="ServiceWindow",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(help_text="e.g. Lunch, Dinner, Brunch", max_length=100)),
                (
                    "day_of_week",
                    models.IntegerField(
                        choices=[
                            (0, "Monday"), (1, "Tuesday"), (2, "Wednesday"),
                            (3, "Thursday"), (4, "Friday"), (5, "Saturday"), (6, "Sunday"),
                        ]
                    ),
                ),
                ("open_time", models.TimeField()),
                ("close_time", models.TimeField()),
                ("last_booking_time", models.TimeField(help_text="Latest time a booking can start")),
                (
                    "turn_time_minutes",
                    models.IntegerField(
                        default=90,
                        help_text="Default dining duration in minutes",
                        validators=[django.core.validators.MinValueValidator(15)],
                    ),
                ),
                (
                    "max_covers",
                    models.IntegerField(
                        default=50,
                        help_text="Max total covers in this window",
                        validators=[django.core.validators.MinValueValidator(1)],
                    ),
                ),
                ("active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="service_windows",
                        to="tenants.tenantsettings",
                    ),
                ),
            ],
            options={
                "ordering": ["day_of_week", "open_time"],
            },
        ),
        # Add restaurant fields to Booking model
        migrations.AddField(
            model_name="booking",
            name="party_size",
            field=models.IntegerField(blank=True, null=True, help_text="Number of guests (restaurant bookings)"),
        ),
        migrations.AddField(
            model_name="booking",
            name="table",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="bookings",
                to="bookings.table",
                help_text="Assigned table (restaurant bookings)",
            ),
        ),
    ]
