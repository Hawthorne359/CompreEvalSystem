"""
创建默认角色（含 level）。角色名可在后台修改，level 决定层级与自动补全范围。
"""
from django.core.management.base import BaseCommand
from users.models import Role


# (code, name, level)；仅首次创建时用 name/level，之后可在后台改
# 注意：admin/reviewer 已在 migration 0005_role_restructure 中合并删除，不在此列
ROLES = [
    ('student',           '学生',               0),
    ('student_assistant', '学生助理（评卷助理）', 1),
    ('counselor',         '评审老师（辅导员）',   2),
    ('director',          '院系主任',            3),
    ('superadmin',        '超级管理员',           5),
]


class Command(BaseCommand):
    help = '创建默认角色（含 level），已存在的角色不会覆盖 name/level'

    def handle(self, *args, **options):
        for code, name, level in ROLES:
            role, created = Role.objects.get_or_create(
                code=code,
                defaults={'name': name, 'level': level},
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'创建角色: {name} ({code}), level={level}'))
            else:
                self.stdout.write(f'角色已存在: {role.name} ({code})')
