"""
realtime 应用配置。
"""
from django.apps import AppConfig


class RealtimeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'realtime'
    verbose_name = '实时推送'

    def ready(self):
        import realtime.signals  # noqa: F401
