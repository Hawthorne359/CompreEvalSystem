"""
删除 BackdoorLog.created_at 重复字段（与 open_at 语义相同，均为 auto_now_add）。
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0002_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='backdoorlog',
            name='created_at',
        ),
    ]
