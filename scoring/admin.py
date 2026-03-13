"""
评分记录 Django Admin 配置。
"""
from django.contrib import admin
from .models import ScoreRecord, ArbitrationRecord, ImportedScoreBatch, ImportedScoreDetail


@admin.register(ScoreRecord)
class ScoreRecordAdmin(admin.ModelAdmin):
    """评分记录管理。"""
    list_display = ['id', 'submission', 'indicator', 'reviewer', 'score', 'round_label', 'created_at']
    list_filter = ['round_type']
    search_fields = ['submission__user__username', 'reviewer__username', 'indicator__name']
    ordering = ['-created_at']

    ROUND_LABELS = {1: '初评', 2: '二评', 3: '仲裁', 4: '辅导员确认'}

    def round_label(self, obj):
        """评分轮次中文。"""
        return self.ROUND_LABELS.get(obj.round_type, f'第{obj.round_type}轮')
    round_label.short_description = '评分轮次'


@admin.register(ArbitrationRecord)
class ArbitrationRecordAdmin(admin.ModelAdmin):
    """仲裁记录管理。"""
    list_display = ['id', 'submission', 'indicator', 'arbitrator', 'score', 'created_at']
    search_fields = ['submission__user__username', 'arbitrator__username']
    ordering = ['-created_at']


@admin.register(ImportedScoreBatch)
class ImportedScoreBatchAdmin(admin.ModelAdmin):
    """Excel 批量导入批次管理。"""
    list_display = ['id', 'project', 'file_name', 'status', 'row_count', 'created_at']
    list_filter = ['status', 'project']
    search_fields = ['file_name', 'project__name']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(ImportedScoreDetail)
class ImportedScoreDetailAdmin(admin.ModelAdmin):
    """批量导入明细管理。"""
    list_display = ['id', 'batch', 'submission', 'indicator', 'score', 'source']
    search_fields = ['submission__user__username', 'indicator__name']
