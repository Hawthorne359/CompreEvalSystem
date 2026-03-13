"""
初始化默认超级管理员账号（幂等，可重复执行）。

用途：容器首次启动时由 entrypoint 自动调用，确保系统开箱即用。
      若 superadmin 用户已存在，则跳过创建，仅补全缺失的 UserRole。

账号信息：
  username : superadmin
  password : 123456
  name     : 超级管理员
"""
from django.core.management.base import BaseCommand
from django.db import transaction

SUPERADMIN_USERNAME = 'superadmin'
SUPERADMIN_PASSWORD = '123456'
SUPERADMIN_NAME = '超级管理员'


class Command(BaseCommand):
    help = '初始化默认超级管理员账号（幂等）'

    @transaction.atomic
    def handle(self, *args, **options):
        from users.models import Role, User, UserRole

        # 确保角色表已就绪
        superadmin_role = Role.objects.filter(code='superadmin').first()
        if not superadmin_role:
            self.stdout.write(self.style.WARNING(
                '未找到 superadmin 角色，请先执行 init_roles 或等待 post_migrate 信号完成'
            ))
            return

        # 创建用户（幂等）
        user, created = User.objects.get_or_create(
            username=SUPERADMIN_USERNAME,
            defaults={
                'name': SUPERADMIN_NAME,
                'is_superuser': True,
                'is_staff': True,
                'is_active': True,
            },
        )

        if created:
            user.set_password(SUPERADMIN_PASSWORD)
            user.save(update_fields=['password'])
            self.stdout.write(self.style.SUCCESS(
                f'已创建超级管理员账号: {SUPERADMIN_USERNAME} / {SUPERADMIN_PASSWORD}'
            ))
        else:
            self.stdout.write(f'超级管理员账号已存在: {SUPERADMIN_USERNAME}，跳过创建')

        # 补全全部层级的 UserRole（幂等）
        for role in Role.objects.filter(level__lte=superadmin_role.level).order_by('level'):
            _, role_created = UserRole.objects.get_or_create(
                user=user,
                role=role,
                scope_id=None,
                scope_type='',
                defaults={},
            )
            if role_created:
                self.stdout.write(self.style.SUCCESS(
                    f'  已补全角色身份: {role.name} ({role.code})'
                ))

        # 设置 current_role（若未设置或指向了错误角色）
        if user.current_role_id != superadmin_role.pk:
            user.current_role = superadmin_role
            user.save(update_fields=['current_role'])
            self.stdout.write(self.style.SUCCESS(
                f'  已设置 current_role -> {superadmin_role.name}'
            ))

        self.stdout.write(self.style.SUCCESS('超级管理员初始化完成'))
