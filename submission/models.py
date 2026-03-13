"""
学生提交与佐证材料模型。
"""
from django.conf import settings
from django.db import models


class StudentSubmission(models.Model):
    """学生某项目的提交（材料+自评）。"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('submitted', '已提交'),
        ('under_review', '审核中'),
        ('approved', '已通过'),
        ('rejected', '已驳回'),
        ('appealing', '申诉中'),
    ]
    project = models.ForeignKey(
        'eval.EvalProject',
        on_delete=models.CASCADE,
        related_name='submissions',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submissions',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    self_score = models.JSONField(default=dict, blank=True, help_text='自评分数明细')
    final_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='系统计算或管理员覆盖的最终总分',
    )
    score_detail = models.JSONField(default=dict, blank=True, help_text='各指标/模块得分明细')
    submitted_at = models.DateTimeField(null=True, blank=True)
    via_late_channel = models.BooleanField(
        default=False,
        verbose_name='通过补交通道提交',
        help_text='True 表示该提交是在正常提交窗口和迟交窗口均已关闭后，通过管理员开启的补交通道提交的',
    )
    remark = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'submission_student_submission'
        unique_together = [['project', 'user']]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.project.name}"


class Evidence(models.Model):
    """佐证材料（文件上传）。"""
    submission = models.ForeignKey(
        StudentSubmission,
        on_delete=models.CASCADE,
        related_name='evidences',
    )
    indicator = models.ForeignKey(
        'eval.EvalIndicator',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evidences',
        help_text='可选，绑定到具体模块/题目；为空表示提交级全局附件',
    )
    file = models.FileField(upload_to='evidence/%Y/%m/')
    category = models.CharField(max_length=50, blank=True)
    name = models.CharField(max_length=200, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'submission_evidence'
        ordering = ['submission', 'id']

    def __str__(self):
        return self.name or str(self.file)


class SubmissionAnswer(models.Model):
    """提交中的题目作答明细（模块级自评分 + 过程记录）。"""
    submission = models.ForeignKey(
        StudentSubmission,
        on_delete=models.CASCADE,
        related_name='answers',
    )
    indicator = models.ForeignKey(
        'eval.EvalIndicator',
        on_delete=models.CASCADE,
        related_name='submission_answers',
    )
    self_score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    process_record = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'submission_answer'
        ordering = ['submission', 'indicator_id']
        unique_together = [['submission', 'indicator']]

    def __str__(self):
        return f"submission#{self.submission_id}-indicator#{self.indicator_id}"
