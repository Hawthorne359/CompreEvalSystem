"""
学生提交与佐证材料 Django Admin 配置。
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import StudentSubmission, Evidence


@admin.register(StudentSubmission)
class StudentSubmissionAdmin(admin.ModelAdmin):
    """学生提交管理。"""
    list_display = ['id', 'project', 'student_display', 'status_badge', 'final_score', 'submitted_at', 'created_at']
    list_filter = ['status', 'project']
    search_fields = ['user__username', 'user__name', 'project__name']
    readonly_fields = ['created_at', 'submitted_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    STATUS_LABELS = {
        'draft': '草稿',
        'submitted': '已提交',
        'under_review': '评审中',
        'approved': '已通过',
        'rejected': '已驳回',
        'appealing': '申诉中',
    }

    def student_display(self, obj):
        """显示学生姓名+用户名。"""
        uname = obj.user.name
        return f"{uname}（{obj.user.username}）" if uname else obj.user.username
    student_display.short_description = '学生'

    def status_badge(self, obj):
        """状态彩色徽章。"""
        colors = {
            'draft': '#6b7280',
            'submitted': '#2563eb',
            'under_review': '#d97706',
            'approved': '#15803d',
            'rejected': '#b91c1c',
            'appealing': '#7c3aed',
        }
        color = colors.get(obj.status, '#6b7280')
        label = self.STATUS_LABELS.get(obj.status, obj.status)
        return format_html('<span style="color:{};font-weight:500;">{}</span>', color, label)
    status_badge.short_description = '状态'


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    """佐证材料管理。"""
    list_display = ['id', 'submission', 'name', 'category', 'file_link']
    list_filter = ['category']
    search_fields = ['name', 'submission__user__username']

    def file_link(self, obj):
        """文件下载链接。"""
        if obj.file:
            return format_html('<a href="{}" target="_blank">查看文件</a>', obj.file.url)
        return '—'
    file_link.short_description = '文件'
