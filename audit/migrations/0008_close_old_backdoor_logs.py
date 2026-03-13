"""
数据迁移：将旧全局 BackdoorLog 中仍处于"开启中"（close_at 为空）的记录标记为已关闭。
旧表 audit_backdoor_log 保留但不再用于权限判断，改由 LateSubmitChannel 控制。
"""
from django.db import migrations
from django.utils import timezone


def close_old_backdoor_logs(apps, schema_editor):
    """将所有 close_at 为空的旧 BackdoorLog 记录标记为当前时间关闭。"""
    BackdoorLog = apps.get_model('audit', 'BackdoorLog')
    now = timezone.now()
    BackdoorLog.objects.filter(close_at__isnull=True).update(close_at=now)


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0007_latesubmitrequest_latesubmitchannel'),
    ]

    operations = [
        migrations.RunPython(close_old_backdoor_logs, migrations.RunPython.noop),
    ]
