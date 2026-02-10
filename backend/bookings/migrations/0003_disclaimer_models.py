from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0002_add_noshow_staff_deposit_pct'),
    ]

    operations = [
        migrations.CreateModel(
            name='DisclaimerTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(default='Terms & Conditions', max_length=255)),
                ('body', models.TextField(help_text='Full disclaimer text shown to the client')),
                ('is_active', models.BooleanField(default=True)),
                ('version', models.PositiveIntegerField(default=1, help_text='Increment to require re-signing')),
                ('validity_days', models.PositiveIntegerField(default=365, help_text='Days before signature expires (0=never)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'bookings_disclaimer_template',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ClientDisclaimer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_email', models.EmailField(db_index=True, max_length=254)),
                ('customer_name', models.CharField(max_length=255)),
                ('version_signed', models.PositiveIntegerField()),
                ('signed_at', models.DateTimeField(auto_now_add=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('is_void', models.BooleanField(default=False, help_text='Admin can void to force re-signing')),
                ('disclaimer', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='signatures',
                    to='bookings.disclaimertemplate',
                )),
            ],
            options={
                'db_table': 'bookings_client_disclaimer',
                'ordering': ['-signed_at'],
            },
        ),
        migrations.AddIndex(
            model_name='clientdisclaimer',
            index=models.Index(fields=['customer_email', 'disclaimer'], name='bookings_cl_custome_disc_idx'),
        ),
    ]
