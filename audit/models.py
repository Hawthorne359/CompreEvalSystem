"""
审计与日志模型：OperationLog（统一操作日志）、AuditAttachment（佐证材料）、
LateSubmitRequest/LateSubmitChannel（补交申请与补交通道）。

设计原则
--------
* 一张主表 ``OperationLog`` 记录所有用户的所有操作，通过 ``level`` 和 ``is_audit_event``
  区分普通日志与正式审计事件，避免跨表 JOIN 带来的查询复杂度。
* ``AuditAttachment`` 存储需要上传佐证材料的操作附件（FK → OperationLog），
  与主表分离，保持主表字段干净。
* 补交业务统一由 ``LateSubmitRequest`` 与 ``LateSubmitChannel`` 承载，
  开启/关闭/推送动作由 ``OperationLog`` 留痕。
"""
from django.conf import settings
from django.db import models


class OperationLog(models.Model):
    """统一操作日志，覆盖系统中所有角色的所有操作，每次操作必写一条。"""

    # ------------------------------------------------------------------
    # 日志等级
    # ------------------------------------------------------------------
    LEVEL_INFO = 'INFO'
    LEVEL_NOTICE = 'NOTICE'
    LEVEL_WARNING = 'WARNING'
    LEVEL_CRITICAL = 'CRITICAL'
    LEVEL_CHOICES = [
        (LEVEL_INFO,     '一般'),    # 查看列表、登录等
        (LEVEL_NOTICE,   '关键'),    # 学生提交材料、查看报表等
        (LEVEL_WARNING,  '敏感'),    # 创建/修改用户、处理申诉等
        (LEVEL_CRITICAL, '高危'),    # 删除周期/项目、管理员改分等
    ]

    # ------------------------------------------------------------------
    # 业务模块
    # ------------------------------------------------------------------
    MODULE_AUTH = 'auth'
    MODULE_USERS = 'users'
    MODULE_ORG = 'org'
    MODULE_EVAL = 'eval'
    MODULE_SUBMISSION = 'submission'
    MODULE_SCORING = 'scoring'
    MODULE_APPEAL = 'appeal'
    MODULE_REPORT = 'report'
    MODULE_SYSTEM = 'system'
    MODULE_CHOICES = [
        (MODULE_AUTH,       '认证'),
        (MODULE_USERS,      '用户管理'),
        (MODULE_ORG,        '组织架构'),
        (MODULE_EVAL,       '测评管理'),
        (MODULE_SUBMISSION, '材料提交'),
        (MODULE_SCORING,    '评分'),
        (MODULE_APPEAL,     '申诉'),
        (MODULE_REPORT,     '报表'),
        (MODULE_SYSTEM,     '系统'),
    ]

    # ------------------------------------------------------------------
    # 操作者信息（快照防止删号后丢失信息）
    # ------------------------------------------------------------------
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operation_logs',
        verbose_name='操作者',
    )
    username_snapshot = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='用户名快照',
        help_text='操作时记录的用户名，防止账号删除后信息丢失',
    )
    role_snapshot = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='角色快照',
        help_text='操作时的角色名称，如"超级管理员"',
    )

    # ------------------------------------------------------------------
    # 网络元信息
    # ------------------------------------------------------------------
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='内网IP',
        help_text='局域网真实 IP（来自 X-Forwarded-For 或 REMOTE_ADDR）',
    )
    external_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='外网IP',
        help_text='客户端上报的公网 IP（仅供审查参考，不用于安全判断）',
    )
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='浏览器标识',
    )

    # ------------------------------------------------------------------
    # 操作分类
    # ------------------------------------------------------------------
    module = models.CharField(
        max_length=20,
        choices=MODULE_CHOICES,
        verbose_name='业务模块',
    )
    action = models.CharField(
        max_length=100,
        verbose_name='操作码',
        help_text='如 login / create_season / delete_project 等',
    )
    level = models.CharField(
        max_length=10,
        choices=LEVEL_CHOICES,
        default=LEVEL_INFO,
        verbose_name='日志等级',
    )

    # ------------------------------------------------------------------
    # 操作对象
    # ------------------------------------------------------------------
    target_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='目标类型',
        help_text='如 eval_season / eval_project / user',
    )
    target_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='目标ID',
    )
    target_repr = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='目标描述',
        help_text='人类可读的目标名称，如"2024-2025学年春季"',
    )

    # ------------------------------------------------------------------
    # 详情
    # ------------------------------------------------------------------
    extra = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='附加信息',
        help_text='旧值/新值/其他上下文，JSON 格式',
    )
    reason = models.TextField(
        blank=True,
        verbose_name='操作理由',
        help_text='WARNING/CRITICAL 级操作必填',
    )
    is_abnormal = models.BooleanField(
        default=False,
        verbose_name='异常标记',
    )
    is_audit_event = models.BooleanField(
        default=False,
        verbose_name='审计事件',
        help_text='True 时在"审计日志"视图中展示，通常对应需要正式存档的高危操作',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='操作时间',
    )

    class Meta:
        db_table = 'audit_operation_log'
        ordering = ['-created_at']
        verbose_name = '操作日志'
        verbose_name_plural = '操作日志'
        indexes = [
            models.Index(fields=['user', 'created_at'],        name='oplog_user_time_idx'),
            models.Index(fields=['module', 'action'],           name='oplog_module_action_idx'),
            models.Index(fields=['level', 'created_at'],        name='oplog_level_time_idx'),
            models.Index(fields=['is_audit_event', 'created_at'], name='oplog_audit_time_idx'),
            models.Index(fields=['is_abnormal', 'created_at'], name='oplog_abnormal_time_idx'),
            models.Index(fields=['created_at'],                 name='oplog_time_idx'),
        ]

    def __str__(self):
        return f"[{self.level}] {self.username_snapshot} · {self.action} @ {self.created_at:%Y-%m-%d %H:%M:%S}"


class AuditAttachment(models.Model):
    """审计佐证材料，关联到具体的操作日志条目。"""

    operation_log = models.ForeignKey(
        OperationLog,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='关联日志',
    )
    file = models.FileField(
        upload_to='audit_attachments/%Y/%m/',
        verbose_name='附件文件',
    )
    file_name = models.CharField(
        max_length=255,
        verbose_name='原始文件名',
    )
    file_size = models.PositiveIntegerField(
        default=0,
        verbose_name='文件大小（字节）',
    )
    content_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='MIME类型',
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_attachments',
        verbose_name='上传者',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='上传时间',
    )

    class Meta:
        db_table = 'audit_attachment'
        ordering = ['-created_at']
        verbose_name = '审计附件'
        verbose_name_plural = '审计附件'

    def __str__(self):
        return f"{self.file_name} → Log#{self.operation_log_id}"



class LateSubmitRequest(models.Model):
    """学生补交申请：项目截止后学生可提交申请，由管理员审批并开启补交通道。"""

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING,  '待审核'),
        (STATUS_APPROVED, '已批准'),
        (STATUS_REJECTED, '已拒绝'),
    ]

    submission = models.ForeignKey(
        'submission.StudentSubmission',
        on_delete=models.CASCADE,
        related_name='late_requests',
        verbose_name='关联提交',
    )
    reason = models.TextField(verbose_name='申请理由')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='审批状态',
    )
    handler = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='handled_late_requests',
        verbose_name='处理人',
    )
    handle_comment = models.TextField(blank=True, verbose_name='处理意见')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='申请时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'audit_late_submit_request'
        ordering = ['-created_at']
        verbose_name = '补交申请'
        verbose_name_plural = '补交申请'

    def __str__(self):
        return f"补交申请#{self.id} [{self.get_status_display()}] 提交#{self.submission_id}"


class LateSubmitRequestAttachment(models.Model):
    """学生随补交申请上传的佐证材料（审批通过凭证、情况说明等）。"""
    request = models.ForeignKey(
        LateSubmitRequest,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='关联补交申请',
    )
    file = models.FileField(
        upload_to='late_request_attachments/%Y/%m/',
        verbose_name='附件文件',
    )
    name = models.CharField(max_length=255, blank=True, verbose_name='原始文件名')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')

    class Meta:
        db_table = 'audit_late_submit_request_attachment'
        ordering = ['request', 'uploaded_at']
        verbose_name = '补交申请附件'
        verbose_name_plural = '补交申请附件'

    def __str__(self):
        return f"{self.name or self.file.name} → 申请#{self.request_id}"


class LateSubmitChannel(models.Model):
    """管理员针对个人或班级开启的补交通道，支持自动到期和手动关闭。"""

    SCOPE_USER = 'user'
    SCOPE_CLASS = 'class'
    SCOPE_CHOICES = [
        (SCOPE_USER,  '指定用户'),
        (SCOPE_CLASS, '指定班级'),
    ]

    CLOSE_AUTO_EXPIRE = 'auto_expire'
    CLOSE_SUBMITTED   = 'submitted'
    CLOSE_MANUAL      = 'manual'
    CLOSE_REASON_CHOICES = [
        (CLOSE_AUTO_EXPIRE, '自动到期'),
        (CLOSE_SUBMITTED,   '学生已提交'),
        (CLOSE_MANUAL,      '管理员手动关闭'),
    ]

    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='opened_late_channels',
        verbose_name='开启者',
    )
    scope_type = models.CharField(
        max_length=10,
        choices=SCOPE_CHOICES,
        default=SCOPE_USER,
        verbose_name='范围类型',
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='late_channels',
        verbose_name='目标用户',
        help_text='scope_type=user 时必填',
    )
    target_class = models.ForeignKey(
        'org.Class',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='late_channels',
        verbose_name='目标班级',
        help_text='scope_type=class 时必填',
    )
    project = models.ForeignKey(
        'eval.EvalProject',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='late_channels',
        verbose_name='限定项目',
        help_text='为空表示对该用户/班级的所有项目均开放',
    )
    reason = models.TextField(verbose_name='开启理由')
    duration_hours = models.PositiveIntegerField(
        default=24,
        verbose_name='有效时长（小时）',
        help_text='最少 1 小时',
    )
    open_at = models.DateTimeField(auto_now_add=True, verbose_name='开启时间')
    planned_close_at = models.DateTimeField(verbose_name='计划关闭时间')
    actual_close_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='实际关闭时间',
    )
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='closed_late_channels',
        verbose_name='关闭者',
    )
    close_reason = models.CharField(
        max_length=20,
        choices=CLOSE_REASON_CHOICES,
        blank=True,
        verbose_name='关闭原因',
    )
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    from_request = models.OneToOneField(
        LateSubmitRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='channel',
        verbose_name='来源申请',
        help_text='由审批申请自动开启时关联，手动开启时为空',
    )

    class Meta:
        db_table = 'audit_late_submit_channel'
        ordering = ['-open_at']
        verbose_name = '补交通道'
        verbose_name_plural = '补交通道'

    def __str__(self):
        target = self.target_user or self.target_class or '—'
        return f"补交通道#{self.id} → {target} ({'激活' if self.is_active else '已关闭'})"
