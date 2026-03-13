"""
报表导出模板与映射配置模型。
"""
from django.conf import settings
from django.db import models


class ReportExportTemplate(models.Model):
    """导出模板（Word/Excel）。"""

    TEMPLATE_TYPE_CHOICES = [
        ('word', 'Word 模板'),
        ('excel', 'Excel 模板'),
    ]
    VISIBILITY_CHOICES = [
        ('private', '仅自己可见'),
        ('department', '院系可见'),
        ('global', '全局可见'),
    ]

    name = models.CharField(max_length=120)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES)
    project = models.ForeignKey(
        'eval.EvalProject',
        on_delete=models.CASCADE,
        related_name='report_export_templates',
        null=True,
        blank=True,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='report_export_templates',
    )
    department = models.ForeignKey(
        'org.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='report_export_templates',
    )
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='private')
    file = models.FileField(upload_to='report/templates/%Y/%m/')
    is_active = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'report_export_template'
        ordering = ['-updated_at', '-id']

    def __str__(self):
        return f'{self.name}({self.template_type})'


class ReportExportMapping(models.Model):
    """导出映射配置。"""

    OUTPUT_FORMAT_CHOICES = [
        ('word', 'Word'),
        ('pdf', 'PDF'),
        ('xlsx', 'Excel'),
    ]

    name = models.CharField(max_length=120)
    project = models.ForeignKey(
        'eval.EvalProject',
        on_delete=models.CASCADE,
        related_name='report_export_mappings',
        null=True,
        blank=True,
    )
    template = models.ForeignKey(
        ReportExportTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mappings',
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='report_export_mappings',
    )
    output_format = models.CharField(max_length=20, choices=OUTPUT_FORMAT_CHOICES, default='xlsx')
    is_default = models.BooleanField(default=False)
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'report_export_mapping'
        ordering = ['-updated_at', '-id']

    def __str__(self):
        return f'{self.name}({self.output_format})'
