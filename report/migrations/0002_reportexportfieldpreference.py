from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('eval', '0019_alter_evalindicator_id_alter_evalproject_id_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('report', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportExportFieldPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('common_field_keys', models.JSONField(blank=True, default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='report_export_field_preferences', to='eval.evalproject')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='report_export_field_preferences', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'report_export_field_preference',
                'ordering': ['-updated_at', '-id'],
                'unique_together': {('user', 'project')},
            },
        ),
    ]
