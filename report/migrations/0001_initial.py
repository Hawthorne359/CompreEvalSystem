from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('eval', '0017_add_require_process_record'),
        ('org', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportExportTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('template_type', models.CharField(choices=[('word', 'Word 模板'), ('excel', 'Excel 模板')], max_length=20)),
                ('visibility', models.CharField(choices=[('private', '仅自己可见'), ('department', '院系可见'), ('global', '全局可见')], default='private', max_length=20)),
                ('file', models.FileField(upload_to='report/templates/%Y/%m/')),
                ('is_active', models.BooleanField(default=True)),
                ('version', models.PositiveIntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('department', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='report_export_templates', to='org.department')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='report_export_templates', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='report_export_templates', to='eval.evalproject')),
            ],
            options={
                'db_table': 'report_export_template',
                'ordering': ['-updated_at', '-id'],
            },
        ),
        migrations.CreateModel(
            name='ReportExportMapping',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('output_format', models.CharField(choices=[('word', 'Word'), ('pdf', 'PDF'), ('xlsx', 'Excel')], default='xlsx', max_length=20)),
                ('is_default', models.BooleanField(default=False)),
                ('config', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='report_export_mappings', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='report_export_mappings', to='eval.evalproject')),
                ('template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mappings', to='report.reportexporttemplate')),
            ],
            options={
                'db_table': 'report_export_mapping',
                'ordering': ['-updated_at', '-id'],
            },
        ),
    ]
