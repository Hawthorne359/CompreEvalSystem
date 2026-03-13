"""
组织架构模型：院系、专业、班级。
"""
from datetime import date

from django.db import models


class Department(models.Model):
    """院系，支持 parent 层级。"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True, blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'org_department'
        ordering = ['code']

    def __str__(self):
        return self.name


class Major(models.Model):
    """专业，归属院系；用于班级、用户管理按专业筛选。"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, blank=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='majors',
    )
    grades = models.JSONField(
        default=list,
        blank=True,
        help_text='该专业已有的年级列表，如 ["2021", "2022", "2023"]',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'org_major'
        ordering = ['department', 'name']
        unique_together = [('name', 'department')]

    def __str__(self):
        return self.name


class Class(models.Model):
    """班级；归属院系，可选归属专业，含年级（如 2022 级）。"""
    name = models.CharField(max_length=100)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='classes',
    )
    major = models.ForeignKey(
        Major,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='classes',
    )
    grade = models.CharField(max_length=20, blank=True, help_text='年级，如 2022、2023')
    academic_year = models.CharField(max_length=20, blank=True, help_text='历史字段，已改为自动计算')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def current_academic_year(self):
        """基于当前日期自动推算学年：9 月起为新学年。"""
        today = date.today()
        if today.month >= 9:
            return f'{today.year}-{today.year + 1}'
        return f'{today.year - 1}-{today.year}'

    class Meta:
        db_table = 'org_class'
        ordering = ['department', 'grade', 'name']
        verbose_name_plural = 'Classes'
        unique_together = [('name', 'department', 'grade')]

    def __str__(self):
        return self.name
