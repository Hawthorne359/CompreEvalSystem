"""
EvalIndicator 层级结构升级：添加 parent（自引用外键）、agg_formula、score_source、description 字段，
并将 category 改为允许空值，以支持两级父子指标结构。
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eval', '0002_evalproject_import_config'),
    ]

    operations = [
        # 新增 parent 自引用外键（null=True 向下兼容现有扁平指标）
        migrations.AddField(
            model_name='evalindicator',
            name='parent',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='children',
                to='eval.evalindicator',
                help_text='父级指标；为空表示一级维度',
            ),
        ),
        # 新增 description 字段
        migrations.AddField(
            model_name='evalindicator',
            name='description',
            field=models.TextField(blank=True, default='', help_text='评分细则说明（可选）'),
            preserve_default=False,
        ),
        # 新增 agg_formula 字段
        migrations.AddField(
            model_name='evalindicator',
            name='agg_formula',
            field=models.CharField(
                choices=[('sum', '求和'), ('weighted_sum', '加权求和')],
                default='sum',
                max_length=20,
                help_text='仅一级指标有意义：子项聚合方式（求和 / 加权求和）',
            ),
        ),
        # 新增 score_source 字段
        migrations.AddField(
            model_name='evalindicator',
            name='score_source',
            field=models.CharField(
                choices=[('reviewer', '评审打分'), ('import', '统一导入'), ('self', '学生自评')],
                default='reviewer',
                max_length=20,
                help_text='仅叶子（二级）指标有意义：评分来源',
            ),
        ),
        # 将 category 改为允许空值（二级子项不需要 category）
        migrations.AlterField(
            model_name='evalindicator',
            name='category',
            field=models.CharField(
                blank=True,
                max_length=50,
                help_text='仅一级指标使用，用于映射总分权重规则（如 F1/F2/德育/智育）',
            ),
        ),
        # 更新 weight 字段的 help_text
        migrations.AlterField(
            model_name='evalindicator',
            name='weight',
            field=models.FloatField(
                default=1.0,
                help_text='二级子项：在父级加权求和中的权重；一级指标：占总分比例（在权重规则中配置）',
            ),
        ),
    ]
