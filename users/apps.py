from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'users'

    def ready(self):
        import users.signals  # noqa: F401  注册 User/UserRole 保存时超级管理员自动补全身份
