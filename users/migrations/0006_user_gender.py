from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_role_restructure'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='gender',
            field=models.CharField(
                blank=True,
                choices=[('', '未知'), ('M', '男'), ('F', '女')],
                default='',
                max_length=1,
            ),
        ),
    ]

