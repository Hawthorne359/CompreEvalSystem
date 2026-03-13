"""
评分记录、双评、仲裁与批量导入模型。
"""
from django.conf import settings
from django.db import models


class ScoreRecord(models.Model):
    """单条评分记录（初评/二评/仲裁）。"""
    ROUND_CHOICES = [
        (1, '初评'),
        (2, '二评'),
        (3, '仲裁'),
        (4, '辅导员确认'),
    ]
    SCORE_CHANNEL_CHOICES = [
        ('assignment', '按分配任务评分'),
        ('arbitration', '仲裁'),
        ('import', '批量导入'),
    ]
    submission = models.ForeignKey(
        'submission.StudentSubmission',
        on_delete=models.CASCADE,
        related_name='score_records',
    )
    indicator = models.ForeignKey(
        'eval.EvalIndicator',
        on_delete=models.CASCADE,
        related_name='score_records',
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='score_records_given',
    )
    score = models.DecimalField(max_digits=6, decimal_places=2)
    comment = models.TextField(blank=True)
    round_type = models.PositiveSmallIntegerField(choices=ROUND_CHOICES, default=1)
    score_channel = models.CharField(
        max_length=30,
        choices=SCORE_CHANNEL_CHOICES,
        default='assignment',
        help_text='评分通道：assignment=按分配任务 | arbitration=仲裁 | import=批量导入',
    )
    scorer_role_level = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text='评分时评分者的 current_role.level',
    )
    scorer_max_role_level = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text='评分者所有角色中的最高 level',
    )
    is_delegated = models.BooleanField(
        default=False,
        help_text='是否为降权代劳（评分者最高角色 level 高于当前角色 level）',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'scoring_score_record'
        ordering = ['submission', 'indicator', 'round_type']
        unique_together = [['submission', 'indicator', 'reviewer', 'round_type']]

    def __str__(self):
        return f"{self.submission_id} #{self.indicator_id} R{self.round_type}={self.score}"


class ArbitrationRecord(models.Model):
    """仲裁记录。"""
    submission = models.ForeignKey(
        'submission.StudentSubmission',
        on_delete=models.CASCADE,
        related_name='arbitration_records',
    )
    indicator = models.ForeignKey(
        'eval.EvalIndicator',
        on_delete=models.CASCADE,
        related_name='arbitration_records',
    )
    arbitrator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='arbitration_records',
    )
    score = models.DecimalField(max_digits=6, decimal_places=2)
    comment = models.TextField(blank=True)
    triggered_reason = models.CharField(max_length=100, blank=True)
    arbitrator_level = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text='仲裁者的最高角色等级，用于层级保护（高权限仲裁不可被低权限覆盖）',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'scoring_arbitration_record'
        ordering = ['submission', 'indicator']

    def __str__(self):
        return f"Arbitration {self.submission_id} #{self.indicator_id}"


class ImportedScoreBatch(models.Model):
    """批量导入成绩批次。"""
    project = models.ForeignKey(
        'eval.EvalProject',
        on_delete=models.CASCADE,
        related_name='imported_batches',
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='imported_batches',
    )
    file_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, default='pending')
    row_count = models.PositiveIntegerField(default=0)
    error_log = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'scoring_imported_score_batch'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.file_name} ({self.created_at})"


class ImportedScoreDetail(models.Model):
    """批量导入的单条成绩。"""
    batch = models.ForeignKey(
        ImportedScoreBatch,
        on_delete=models.CASCADE,
        related_name='details',
    )
    submission = models.ForeignKey(
        'submission.StudentSubmission',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='imported_score_details',
    )
    indicator = models.ForeignKey(
        'eval.EvalIndicator',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='imported_score_details',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='imported_score_details',
    )
    score = models.DecimalField(max_digits=6, decimal_places=2)
    source = models.CharField(max_length=50, blank=True, help_text='如 physical_education')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'scoring_imported_score_detail'
        ordering = ['batch', 'id']


class ReviewAssignment(models.Model):
    """评审任务分配（用于双评任务归属与越权校验）。"""
    ROLE_TYPE_CHOICES = [
        ('counselor', '评审老师（辅导员）'),
        ('counselor_dispatch', '辅导员任务分发'),
        ('counselor_confirm', '辅导员最终确认'),
        ('assistant', '学生助理'),
    ]
    STATUS_CHOICES = [
        ('assigned', '已分配'),
        ('released', '已放行'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    submission = models.ForeignKey(
        'submission.StudentSubmission',
        on_delete=models.CASCADE,
        related_name='review_assignments',
    )
    project = models.ForeignKey(
        'eval.EvalProject',
        on_delete=models.CASCADE,
        related_name='review_assignments',
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='review_assignments',
    )
    role_type = models.CharField(max_length=20, choices=ROLE_TYPE_CHOICES)
    round_type = models.PositiveSmallIntegerField(default=1)
    strategy_mode = models.CharField(max_length=50, default='same_class')
    assignment_version = models.PositiveIntegerField(default=1)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='review_assignments_created',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'scoring_review_assignment'
        ordering = ['-created_at', 'id']
        unique_together = [['submission', 'reviewer', 'round_type', 'assignment_version']]

    def __str__(self):
        return f"Assign#{self.id} sub={self.submission_id} reviewer={self.reviewer_id} round={self.round_type}"


class ReviewObjection(models.Model):
    """审核模块异议工单。"""
    STATUS_CHOICES = [
        ('pending_counselor', '待辅导员处理'),
        ('resolved_by_counselor', '辅导员已处理'),
        ('escalated_to_director', '已上报院系主任'),
        ('resolved_by_director', '院系主任已处理'),
        ('escalated_to_admin', '已上报超管'),
        ('resolved_by_admin', '超管已处理'),
        ('rejected', '已驳回'),
    ]
    SOURCE_ROLE_CHOICES = [
        ('assistant', '学生助理'),
        ('counselor', '评审老师'),
    ]
    submission = models.ForeignKey(
        'submission.StudentSubmission',
        on_delete=models.CASCADE,
        related_name='review_objections',
    )
    indicator = models.ForeignKey(
        'eval.EvalIndicator',
        on_delete=models.CASCADE,
        related_name='review_objections',
    )
    raised_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='review_objections_raised',
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='review_objections_assigned',
    )
    source_role = models.CharField(max_length=20, choices=SOURCE_ROLE_CHOICES, default='assistant')
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default='pending_counselor')
    current_handler_level = models.PositiveSmallIntegerField(default=2)
    reason = models.TextField()
    resolution_comment = models.TextField(blank=True)
    resolved_score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'scoring_review_objection'
        ordering = ['-created_at']

    def __str__(self):
        return f'Objection#{self.id} sub={self.submission_id} ind={self.indicator_id}'


class ReviewObjectionAttachment(models.Model):
    """审核异议附件。"""
    objection = models.ForeignKey(
        ReviewObjection,
        on_delete=models.CASCADE,
        related_name='attachments',
    )
    file = models.FileField(upload_to='review_objection/%Y/%m/')
    name = models.CharField(max_length=200, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='review_objection_attachments',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'scoring_review_objection_attachment'
        ordering = ['id']

    def __str__(self):
        return self.name or str(self.file)
