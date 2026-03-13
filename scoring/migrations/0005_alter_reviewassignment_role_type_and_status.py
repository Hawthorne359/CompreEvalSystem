from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scoring', '0004_alter_reviewassignment_role_type_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reviewassignment',
            name='role_type',
            field=models.CharField(
                choices=[
                    ('counselor', '评审老师（辅导员）'),
                    ('counselor_dispatch', '辅导员任务分发'),
                    ('counselor_confirm', '辅导员最终确认'),
                    ('assistant', '学生助理'),
                ],
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='reviewassignment',
            name='status',
            field=models.CharField(
                choices=[
                    ('assigned', '已分配'),
                    ('released', '已放行'),
                    ('completed', '已完成'),
                    ('cancelled', '已取消'),
                ],
                default='assigned',
                max_length=20,
            ),
        ),
    ]
