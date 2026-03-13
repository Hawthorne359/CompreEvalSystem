"""
为 EvalProject 增加 import_config JSONField，支持 Excel 导入列映射可配置化。
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eval', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='evalproject',
            name='import_config',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text=(
                    'Excel 批量导入列映射配置，留空使用系统默认（第0列学号，第1列指标名，第2列分数）。'
                    '示例：{"student_col": 0, "indicator_col": 1, "score_col": 2, '
                    '"student_field": "student_no", "round_type": 1, "comment": "批量导入"}'
                ),
            ),
        ),
    ]
