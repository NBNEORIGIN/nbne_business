from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('compliance', '0001_initial'),
    ]

    operations = [
        # --- ComplianceCategory ---
        migrations.CreateModel(
            name='ComplianceCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, default='')),
                ('legal_requirement', models.BooleanField(default=False, help_text='Is this a legal requirement under UK law?')),
                ('order', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'compliance_category',
                'ordering': ['order', 'name'],
                'verbose_name': 'Compliance Category',
                'verbose_name_plural': 'Compliance Categories',
            },
        ),
        # --- ComplianceItem ---
        migrations.CreateModel(
            name='ComplianceItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, default='')),
                ('frequency_type', models.CharField(choices=[('weekly', 'Weekly'), ('monthly', 'Monthly'), ('annual', 'Annual'), ('3_year', 'Every 3 Years'), ('5_year', 'Every 5 Years'), ('custom_days', 'Custom (days)'), ('one_off', 'One-off')], default='annual', max_length=20)),
                ('frequency_days', models.IntegerField(blank=True, help_text='Custom frequency in days (only for custom_days)', null=True)),
                ('last_completed_date', models.DateField(blank=True, null=True)),
                ('next_due_date', models.DateField(blank=True, db_index=True, null=True)),
                ('status', models.CharField(choices=[('compliant', 'Compliant'), ('due_soon', 'Due Soon'), ('overdue', 'Overdue'), ('not_started', 'Not Started')], db_index=True, default='not_started', max_length=20)),
                ('is_baseline', models.BooleanField(default=False, help_text='Auto-created UK baseline item')),
                ('notes', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='compliance.compliancecategory')),
                ('responsible_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='compliance_responsibilities', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'compliance_item',
                'ordering': ['next_due_date', 'title'],
                'verbose_name': 'Compliance Item',
                'verbose_name_plural': 'Compliance Items',
            },
        ),
        # --- Add RIDDOR fields to IncidentReport ---
        migrations.AddField(
            model_name='incidentreport',
            name='injury_type',
            field=models.CharField(choices=[('none', 'No Injury'), ('minor', 'Minor Injury'), ('major', 'Major Injury'), ('fatality', 'Fatality'), ('disease', 'Occupational Disease'), ('dangerous_occurrence', 'Dangerous Occurrence')], default='none', max_length=30),
        ),
        migrations.AddField(
            model_name='incidentreport',
            name='riddor_reportable',
            field=models.BooleanField(default=False, help_text='Reportable under RIDDOR 2013?'),
        ),
        migrations.AddField(
            model_name='incidentreport',
            name='reviewed_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_incidents', to=settings.AUTH_USER_MODEL),
        ),
        # --- TrainingRecord ---
        migrations.CreateModel(
            name='TrainingRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('training_type', models.CharField(choices=[('first_aid', 'First Aid at Work'), ('fire_marshal', 'Fire Marshal'), ('manual_handling', 'Manual Handling'), ('coshh', 'COSHH'), ('food_hygiene', 'Food Hygiene'), ('safeguarding', 'Safeguarding'), ('dse', 'Display Screen Equipment'), ('working_at_height', 'Working at Height'), ('other', 'Other')], max_length=30)),
                ('title', models.CharField(blank=True, default='', help_text='Custom title if type is "other"', max_length=255)),
                ('provider', models.CharField(blank=True, default='', max_length=255)),
                ('certificate_file', models.FileField(blank=True, null=True, upload_to='compliance/training/%Y/%m/')),
                ('issue_date', models.DateField()),
                ('expiry_date', models.DateField(blank=True, db_index=True, null=True)),
                ('notes', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='training_records', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'compliance_training_record',
                'ordering': ['expiry_date', 'user'],
                'verbose_name': 'Training Record',
                'verbose_name_plural': 'Training Records',
            },
        ),
        # --- DocumentVault ---
        migrations.CreateModel(
            name='DocumentVault',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('file', models.FileField(upload_to='compliance/vault/%Y/%m/')),
                ('document_type', models.CharField(choices=[('policy', 'Policy'), ('certificate', 'Certificate'), ('risk_assessment', 'Risk Assessment'), ('insurance', 'Insurance'), ('license', 'License'), ('training_material', 'Training Material'), ('other', 'Other')], db_index=True, default='other', max_length=30)),
                ('description', models.TextField(blank=True, default='')),
                ('expiry_date', models.DateField(blank=True, db_index=True, null=True)),
                ('version', models.CharField(default='1.0', max_length=20)),
                ('is_current', models.BooleanField(db_index=True, default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('uploaded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='vault_uploads', to=settings.AUTH_USER_MODEL)),
                ('supersedes', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='superseded_by', to='compliance.documentvault')),
            ],
            options={
                'db_table': 'compliance_document_vault',
                'ordering': ['-created_at'],
                'verbose_name': 'Document',
                'verbose_name_plural': 'Document Vault',
            },
        ),
        # --- ComplianceActionLog ---
        migrations.CreateModel(
            name='ComplianceActionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('completed', 'Marked Completed'), ('created', 'Created'), ('updated', 'Updated'), ('status_change', 'Status Changed'), ('reminder_sent', 'Reminder Sent'), ('document_uploaded', 'Document Uploaded'), ('reviewed', 'Reviewed'), ('assigned', 'Assigned')], max_length=30)),
                ('notes', models.TextField(blank=True, default='')),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('compliance_item', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='action_logs', to='compliance.complianceitem')),
                ('incident', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='action_logs', to='compliance.incidentreport')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'compliance_action_log',
                'ordering': ['-timestamp'],
                'verbose_name': 'Action Log',
                'verbose_name_plural': 'Action Logs',
            },
        ),
    ]
