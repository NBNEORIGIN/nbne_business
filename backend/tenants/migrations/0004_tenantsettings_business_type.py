from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tenants", "0003_tenantsettings_booking_staff_label"),
    ]

    operations = [
        migrations.AddField(
            model_name="tenantsettings",
            name="business_type",
            field=models.CharField(
                choices=[
                    ("salon", "Salon / Beauty"),
                    ("restaurant", "Restaurant / Hospitality"),
                    ("gym", "Gym / Fitness"),
                    ("generic", "Generic / Other"),
                ],
                default="salon",
                help_text="Controls booking flow variant and admin sidebar",
                max_length=20,
            ),
        ),
    ]
