from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eval', '0008_reviewrule_allowed_assistant_count_per_submission_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reviewrule',
            name='allowed_assistant_count_per_submission',
            field=models.PositiveSmallIntegerField(default=2, help_text='每份提交分配的学生助理人数（至少2名）'),
        ),
        migrations.AddField(
            model_name='reviewrule',
            name='counselor_participation_mode',
            field=models.CharField(
                choices=[('arbitration_only', '仅超阈值仲裁介入'), ('always_confirm', '每份提交最终确认')],
                default='arbitration_only',
                help_text='辅导员介入模式：仅仲裁介入 / 每份最终确认',
                max_length=30,
            ),
        ),
    ]
