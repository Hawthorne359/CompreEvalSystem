from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eval', '0011_evalprojectconfigtemplate'),
    ]

    operations = [
        migrations.AddField(
            model_name='reviewrule',
            name='module_diff_thresholds',
            field=models.JSONField(blank=True, default=dict, help_text='按模块配置分差阈值，如 {"A1": 5, "B1": 8}'),
        ),
        migrations.AddField(
            model_name='reviewrule',
            name='overall_score_diff_threshold',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='总分差超过此值触发仲裁（为空时回落到通用分差阈值）', max_digits=6, null=True),
        ),
    ]
