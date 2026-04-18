from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('eval', '0020_import_config_policy_defaults'),
        ('audit', '0010_add_late_submit_request_attachment'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ImportPermissionRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('requester_level', models.PositiveSmallIntegerField(default=2, verbose_name='申请时角色等级')),
                ('target_scope', models.JSONField(blank=True, default=dict, verbose_name='申请范围快照')),
                ('reason', models.TextField(verbose_name='申请理由')),
                ('status', models.CharField(choices=[('pending', '待审核'), ('approved', '已批准'), ('rejected', '已拒绝')], default='pending', max_length=20, verbose_name='审批状态')),
                ('handle_comment', models.TextField(blank=True, verbose_name='处理意见')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='申请时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('handler', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='handled_import_permission_requests', to=settings.AUTH_USER_MODEL, verbose_name='处理人')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='import_permission_requests', to='eval.evalproject', verbose_name='关联项目')),
                ('requester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='import_permission_requests', to=settings.AUTH_USER_MODEL, verbose_name='申请人')),
            ],
            options={
                'verbose_name': '导入权限申请',
                'verbose_name_plural': '导入权限申请',
                'db_table': 'audit_import_permission_request',
                'ordering': ['-created_at'],
            },
        ),
    ]
