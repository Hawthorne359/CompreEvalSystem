"""
测评周期与项目 Django Admin 配置。
"""
from django.contrib import admin
from .models import (
    EvalSeason,
    EvalProject,
    EvalIndicator,
    ScoreWeightRule,
    ReviewRule,
    EvalProjectConfigTemplate,
)


@admin.register(EvalSeason)
class EvalSeasonAdmin(admin.ModelAdmin):
    """测评周期管理。"""
    list_display = ['name', 'academic_year', 'semester', 'status', 'start_time', 'end_time']
    list_filter = ['status', 'semester', 'academic_year']
    search_fields = ['name']
    ordering = ['-academic_year', '-semester']


@admin.register(EvalProject)
class EvalProjectAdmin(admin.ModelAdmin):
    """测评项目管理。"""
    list_display = ['name', 'season', 'status', 'allow_late_submit', 'late_submit_deadline']
    list_filter = ['status', 'season', 'allow_late_submit']
    search_fields = ['name']
    raw_id_fields = ['season']


@admin.register(EvalIndicator)
class EvalIndicatorAdmin(admin.ModelAdmin):
    """测评指标管理。"""
    list_display = ['name', 'project', 'category', 'score_source', 'max_score', 'weight', 'require_process_record', 'order']
    list_editable = ['require_process_record', 'order']
    list_filter = ['category', 'project', 'score_source', 'require_process_record']
    search_fields = ['name', 'project__name']
    ordering = ['project', 'order']


@admin.register(ScoreWeightRule)
class ScoreWeightRuleAdmin(admin.ModelAdmin):
    """总分权重规则管理。"""
    list_display = ['project', 'formula_type']
    search_fields = ['project__name']


@admin.register(ReviewRule)
class ReviewRuleAdmin(admin.ModelAdmin):
    """评审规则管理。"""
    list_display = ['project', 'dual_review_enabled', 'score_diff_threshold', 'final_score_rule']
    list_filter = ['dual_review_enabled', 'final_score_rule']


@admin.register(EvalProjectConfigTemplate)
class EvalProjectConfigTemplateAdmin(admin.ModelAdmin):
    """项目配置模板管理。"""
    list_display = ['name', 'visibility', 'created_by', 'updated_at']
    list_filter = ['visibility']
    search_fields = ['name', 'created_by__username']
