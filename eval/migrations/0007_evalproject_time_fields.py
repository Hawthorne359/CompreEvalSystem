"""
Migration: Add start_time, end_time, review_end_time to EvalProject.

start_time       — student submission window opens
end_time         — student submission window closes
review_end_time  — teacher scoring deadline (may exceed end_time, must not exceed season.end_time)

All fields are nullable so existing rows remain valid without defaults.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eval', '0006_alter_evalindicator_id_alter_evalproject_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='evalproject',
            name='start_time',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='项目开始时间（学生提交开放）',
            ),
        ),
        migrations.AddField(
            model_name='evalproject',
            name='end_time',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='项目结束时间（学生提交截止）',
            ),
        ),
        migrations.AddField(
            model_name='evalproject',
            name='review_end_time',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='成绩评定截止时间',
                help_text='教师评分截止时间，可晚于项目结束时间，但不得晚于测评周期结束时间',
            ),
        ),
    ]
