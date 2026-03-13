"""
创建默认角色（含 level）。角色名可在后台修改，level 决定层级与自动补全范围。
"""
from django.core.management.base import BaseCommand
from users.models import Role


# (code, name, level)；仅首次创建时用 name/level，之后可在后台改
ROLES = [
    ('student', '学生', 0),
    ('counselor', '辅导员', 1),
    ('reviewer', '评审教师', 2),
    ('director', '院系主任', 3),
    ('admin', '管理员', 4),
    ('superadmin', '超级管理员', 5),
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
