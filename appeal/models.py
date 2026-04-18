"""
申诉模型。
"""
from django.conf import settings
from django.db import models


class Appeal(models.Model):
    """学生申诉。"""
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('approved', '已通过'),
        ('rejected', '已驳回'),
        ('escalated', '已上报院系主任'),
        ('escalated_to_admin', '已上报超级管理员'),
    ]
    title = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text='独立申诉主题；指标级/整份提交申诉可留空',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='filed_appeals',
        help_text='申诉发起人；独立申诉必填，旧申诉通过 submission.user 推断',
    )
    submission = models.ForeignKey(
        'submission.StudentSubmission',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='appeals',
        help_text='关联提交；独立申诉可为空',
    )
    indicator = models.ForeignKey(
        'eval.EvalIndicator',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appeals',
        help_text='针对具体指标的申诉；为空表示整份提交申诉',
    )
    reason = models.TextField()
    original_submission_status = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text='发起申诉前的提交状态，用于撤回时恢复',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    handler = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='handled_appeals',
    )
    handle_comment = models.TextField(blank=True)
    is_escalated = models.BooleanField(default=False, help_text='是否已上报院系主任')
    escalated_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='escalated_appeals',
        help_text='上报对象（院系主任）',
    )
    escalate_comment = models.TextField(blank=True, help_text='院系主任处理意见')
    escalated_to_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='admin_escalated_appeals',
        help_text='二级上报对象（超级管理员）',
    )
    admin_comment = models.TextField(blank=True, help_text='超级管理员处理意见')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'appeal_appeal'
        ordering = ['-created_at']

    def __str__(self):
        return f"Appeal #{self.id} ({self.submission_id})"


class AppealAttachment(models.Model):
    """申诉附件。"""
    appeal = models.ForeignKey(
        Appeal,
        on_delete=models.CASCADE,
        related_name='attachments',
    )
    file = models.FileField(upload_to='appeal/%Y/%m/')
    name = models.CharField(max_length=200, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appeal_attachments',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'appeal_attachment'
        ordering = ['id']

    def __str__(self):
        return self.name or str(self.file)
