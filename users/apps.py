from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'users'

    def ready(self):
        import users.signals  # noqa: F401  注册 User/UserRole 保存时超级管理员自动补全身份
        from django.db.models.signals import post_migrate
        post_migrate.connect(_init_roles_after_migrate, sender=self)


def _init_roles_after_migrate(sender, **kwargs):
    """migrate 后自动初始化默认角色，确保角色表不为空。"""
    try:
        from users.models import Role
        from users.management.commands.init_roles import ROLES
        for code, name, level in ROLES:
            Role.objects.get_or_create(
                code=code,
                defaults={'name': name, 'level': level},
            )
    except Exception:
        pass  # 首次 migrate 时表可能还不存在，静默忽略
