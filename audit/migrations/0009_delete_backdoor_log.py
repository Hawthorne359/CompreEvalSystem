"""
删除旧的全局补交通道表 BackdoorLog（audit_backdoor_log）。
新系统使用 LateSubmitRequest + LateSubmitChannel 精细化管理。
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0008_close_old_backdoor_logs'),
    ]

    operations = [
        migrations.DeleteModel(
            name='BackdoorLog',
        ),
    ]
