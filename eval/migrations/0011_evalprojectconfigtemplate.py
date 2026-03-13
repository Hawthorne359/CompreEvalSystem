from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eval', '0010_reviewrule_single_review_mode'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EvalProjectConfigTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('visibility', models.CharField(choices=[('private', '仅自己可见'), ('global', '全局可见')], default='private', max_length=20)),
                ('include_sections', models.JSONField(blank=True, default=list, help_text='保存片段：basic/indicator/weight/review')),
                ('payload', models.JSONField(blank=True, default=dict, help_text='模板快照内容')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='eval_project_config_templates', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'eval_project_config_template',
                'ordering': ['-updated_at', '-id'],
            },
        ),
    ]
