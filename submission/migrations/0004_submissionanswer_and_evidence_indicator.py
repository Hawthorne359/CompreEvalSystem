from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('eval', '0007_evalproject_time_fields'),
        ('submission', '0003_add_via_late_channel_to_submission'),
    ]

    operations = [
        migrations.AddField(
            model_name='evidence',
            name='indicator',
            field=models.ForeignKey(
                blank=True,
                help_text='可选，绑定到具体模块/题目；为空表示提交级全局附件',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='evidences',
                to='eval.evalindicator',
            ),
        ),
        migrations.CreateModel(
            name='SubmissionAnswer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('self_score', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('process_record', models.TextField(blank=True)),
                ('is_completed', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('indicator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submission_answers', to='eval.evalindicator')),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='submission.studentsubmission')),
            ],
            options={
                'db_table': 'submission_answer',
                'ordering': ['submission', 'indicator_id'],
                'unique_together': {('submission', 'indicator')},
            },
        ),
    ]
