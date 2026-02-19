from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tenants", "0002_tenantsettings_enabled_modules_tenantsettings_slug"),
    ]

    operations = [
        migrations.AddField(
            model_name="tenantsettings",
            name="booking_staff_label",
            field=models.CharField(
                blank=True,
                default="Stylist",
                help_text="Label for staff picker in booking flow e.g. Stylist, Trainer, Host",
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name="tenantsettings",
            name="booking_staff_label_plural",
            field=models.CharField(
                blank=True,
                default="Stylists",
                help_text="Plural form e.g. Stylists, Trainers, Hosts",
                max_length=50,
            ),
        ),
    ]
