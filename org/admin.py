"""
组织架构 Django Admin 配置。
"""
from django.contrib import admin
from .models import Department, Major, Class


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """院系管理。"""
    list_display = ['name', 'code', 'parent']
    search_fields = ['name', 'code']
    list_filter = ['parent']


@admin.register(Major)
class MajorAdmin(admin.ModelAdmin):
    """专业管理。"""
    list_display = ['name', 'code', 'department']
    search_fields = ['name', 'code']
    list_filter = ['department']


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    """班级管理。"""
    list_display = ['name', 'department', 'major', 'grade', 'academic_year']
    search_fields = ['name']
    list_filter = ['department', 'major', 'grade', 'academic_year']
