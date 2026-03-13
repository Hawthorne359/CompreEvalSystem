from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scoring', '0003_reviewassignment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reviewassignment',
            name='role_type',
            field=models.CharField(
                choices=[
                    ('counselor', '评审老师（辅导员）'),
                    ('counselor_confirm', '辅导员最终确认'),
                    ('assistant', '学生助理')
                ],
                max_length=20
            ),
        ),
        migrations.AlterField(
            model_name='scorerecord',
            name='round_type',
            field=models.PositiveSmallIntegerField(
                choices=[(1, '初评'), (2, '二评'), (3, '仲裁'), (4, '辅导员确认')],
                default=1
            ),
        ),
    ]
