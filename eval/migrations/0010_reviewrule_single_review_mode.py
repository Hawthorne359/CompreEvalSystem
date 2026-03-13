from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eval', '0009_reviewrule_counselor_participation_mode_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='reviewrule',
            name='single_review_mode',
            field=models.CharField(
                choices=[('assistant_single', '学生助理单评'), ('counselor_single', '辅导员单评')],
                default='assistant_single',
                help_text='单评执行人模式：学生助理单评 / 辅导员单评',
                max_length=30,
            ),
        ),
    ]
