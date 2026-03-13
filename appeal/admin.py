"""
申诉 Django Admin 配置。
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Appeal


@admin.register(Appeal)
class AppealAdmin(admin.ModelAdmin):
    """申诉管理。"""
    list_display = ['id', 'student_display', 'submission', 'status_badge', 'handler', 'created_at', 'updated_at']
    list_filter = ['status']
    search_fields = ['submission__user__username', 'handler__username', 'reason']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    STATUS_LABELS = {
        'pending': '待处理',
        'approved': '已通过',
        'rejected': '已驳回',
    }

    def student_display(self, obj):
        """显示申诉学生。"""
        user = obj.submission.user
        uname = user.name
        return f"{uname}（{user.username}）" if uname else user.username
    student_display.short_description = '申诉学生'

    def status_badge(self, obj):
        """状态彩色徽章。"""
        colors = {
            'pending': '#d97706',
            'approved': '#15803d',
            'rejected': '#b91c1c',
        }
        color = colors.get(obj.status, '#6b7280')
        label = self.STATUS_LABELS.get(obj.status, obj.status)
        return format_html('<span style="color:{};font-weight:500;">{}</span>', color, label)
    status_badge.short_description = '申诉状态'
