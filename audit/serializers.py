"""
审计与操作日志序列化器。
"""
import json
from rest_framework import serializers
from .models import (
    OperationLog,
    AuditAttachment,
    LateSubmitRequest,
    LateSubmitRequestAttachment,
    LateSubmitChannel,
    ImportPermissionRequest,
)
from submission.models import StudentSubmission

# 操作码 → 中文名称映射（按模块分组）
ACTION_LABELS = {
    # auth
    'login':                '登录',
    'logout':               '登出',
    'token_refresh':        '刷新Token',
    'switch_role':          '切换角色',
    'verify_password_fail': '密码验证失败',
    # users
    'user_create':     '创建用户',
    'user_update':     '修改用户',
    'user_delete':     '删除用户',
    'user_batch_set_active': '批量启用/禁用用户',
    'user_batch_reset_password': '批量重置密码',
    'user_batch_set_role': '批量调整角色',
    'user_batch_delete': '批量删除用户',
    'users_import':    '批量导入用户',
    'users_import_preview': '导入预检',
    'users_import_org_create': '导入时创建组织项',
    'users_import_commit': '导入正式提交',
    'assistant_assign': '指派学生助理',
    'assistant_revoke': '撤销学生助理',
    'role_assign':     '分配角色',
    # org
    'dept_create':   '新建院系',
    'dept_update':   '修改院系',
    'dept_delete':   '删除院系',
    'dept_batch_delete': '批量删除院系',
    'major_create':  '新建专业',
    'major_update':  '修改专业',
    'major_delete':  '删除专业',
    'class_create':  '新建班级',
    'class_update':  '修改班级',
    'class_delete':  '删除班级',
    'class_batch_delete': '批量删除班级',
    # eval
    'season_create':       '创建测评周期',
    'season_update':       '修改测评周期',
    'season_delete':       '删除测评周期',
    'season_batch_set_status': '批量修改测评周期状态',
    'season_batch_delete': '批量删除测评周期',
    'project_create':      '创建测评项目',
    'project_update':      '修改测评项目',
    'project_delete':      '删除测评项目',
    'project_batch_set_status': '批量修改测评项目状态',
    'project_batch_delete': '批量删除测评项目',
    'indicator_create':    '创建测评指标',
    'indicator_update':    '修改测评指标',
    'indicator_delete':    '删除测评指标',
    'weight_rule_update':  '修改权重规则',
    'review_rule_update':  '修改评审规则',
    'project_import_config_update': '修改统一导入配置',
    'project_config_template_save': '保存项目配置模板',
    'project_config_template_apply': '应用项目配置模板',
    # submission
    'submission_create':  '创建提交草稿',
    'submission_update':  '修改提交',
    'submission_submit':  '正式提交',
    'evidence_upload':    '上传佐证材料',
    'evidence_delete':    '删除佐证材料',
    # scoring
    'initial_review': '初审',
    'score_submit':   '提交评分',
    'score_update':   '修改评分',
    'arbitrate':      '仲裁打分',
    'assistant_score_submit': '助理提交评分',
    'review_assignment_generate': '生成评审任务',
    'review_assignment_release': '辅导员放行评审任务',
    'scores_import':  '批量导入成绩',
    'import_blocked_by_policy': '统一导入策略拦截',
    'score_override': '管理员改分',
    'import_policy_update': '修改导入策略',
    'import_permission_request_create': '发起导入权限申请',
    'import_permission_request_approve': '批准导入权限申请',
    'import_permission_request_reject': '拒绝导入权限申请',
    # appeal
    'appeal_file':   '发起申诉',
    'appeal_independent_create': '发起独立申诉',
    'appeal_withdraw': '撤回申诉',
    'appeal_handle': '处理申诉',
    'appeal_escalate': '上报申诉至院系主任',
    'appeal_escalate_admin': '上报申诉至超级管理员',
    'appeal_escalate_handle': '院系主任处理上报申诉',
    'appeal_admin_handle': '超级管理员终裁申诉',
    # report
    'report_export': '导出报表',
    'report_visibility_update': '修改学生报表可见策略',
    # system
    'backdoor_open':       '开启补交通道（旧版全局）',
    'backdoor_close':      '关闭补交通道（旧版全局）',
    'late_request_file':   '发起补交申请',
    'late_request_approve': '批准补交申请',
    'late_request_reject': '拒绝补交申请',
    'late_channel_open':   '开启补交通道',
    'late_channel_close':  '关闭补交通道',
    'late_batch_push':     '批量推送补交至评审',
}

LEVEL_LABELS = {
    OperationLog.LEVEL_INFO:     '一般',
    OperationLog.LEVEL_NOTICE:   '关键',
    OperationLog.LEVEL_WARNING:  '敏感',
    OperationLog.LEVEL_CRITICAL: '高危',
}

MODULE_LABELS = dict(OperationLog.MODULE_CHOICES)


class AuditAttachmentSerializer(serializers.ModelSerializer):
    """审计佐证材料序列化器。"""
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = AuditAttachment
        fields = ['id', 'file_name', 'file_size', 'content_type', 'file_url', 'created_at']

    def get_file_url(self, obj):
        """返回附件文件的完整访问 URL。"""
        if not obj.file:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url


class OperationLogSerializer(serializers.ModelSerializer):
    """操作日志列表序列化器。"""
    action_label = serializers.SerializerMethodField()
    level_label = serializers.SerializerMethodField()
    module_label = serializers.SerializerMethodField()
    attachments = AuditAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = OperationLog
        fields = [
            'id',
            'username_snapshot', 'role_snapshot',
            'ip_address', 'external_ip', 'user_agent',
            'module', 'module_label',
            'action', 'action_label',
            'level', 'level_label',
            'target_type', 'target_id', 'target_repr',
            'extra', 'reason',
            'is_abnormal', 'is_audit_event',
            'attachments',
            'created_at',
        ]

    def get_action_label(self, obj):
        """返回操作码的中文名称。"""
        return ACTION_LABELS.get(obj.action, obj.action)

    def get_level_label(self, obj):
        """返回等级的中文名称。"""
        return LEVEL_LABELS.get(obj.level, obj.level)

    def get_module_label(self, obj):
        """返回模块的中文名称。"""
        return MODULE_LABELS.get(obj.module, obj.module)


class OperationLogDetailSerializer(OperationLogSerializer):
    """操作日志详情（额外展开 extra 的格式化 JSON）。"""
    extra_pretty = serializers.SerializerMethodField()

    class Meta(OperationLogSerializer.Meta):
        fields = OperationLogSerializer.Meta.fields + ['extra_pretty']

    def get_extra_pretty(self, obj):
        """返回 extra 字段的缩进格式化 JSON 字符串，便于前端展示。"""
        if obj.extra:
            try:
                return json.dumps(obj.extra, ensure_ascii=False, indent=2)
            except (TypeError, ValueError):
                pass
        return ''



class LateSubmitRequestAttachmentSerializer(serializers.ModelSerializer):
    """补交申请佐证附件序列化器。"""
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = LateSubmitRequestAttachment
        fields = ['id', 'name', 'file_url', 'uploaded_at']

    def get_file_url(self, obj):
        if not obj.file:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url


class LateSubmitRequestSerializer(serializers.ModelSerializer):
    """补交申请序列化器（管理员与学生均使用）。"""
    handler_name = serializers.CharField(source='handler.username', read_only=True, allow_null=True)
    student_name = serializers.CharField(source='submission.user.username', read_only=True)
    student_no = serializers.CharField(source='submission.user.student_no', read_only=True)
    project_name = serializers.CharField(source='submission.project.name', read_only=True)
    submission_status = serializers.CharField(source='submission.status', read_only=True)
    status_label = serializers.SerializerMethodField()
    has_channel = serializers.SerializerMethodField()
    attachments = LateSubmitRequestAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = LateSubmitRequest
        fields = [
            'id',
            'submission', 'submission_status',
            'student_name', 'student_no', 'project_name',
            'reason', 'status', 'status_label',
            'handler', 'handler_name', 'handle_comment',
            'has_channel',
            'attachments',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['status', 'handler', 'handle_comment', 'created_at', 'updated_at']

    def get_status_label(self, obj):
        """返回审批状态中文名称。"""
        return obj.get_status_display()

    def get_has_channel(self, obj):
        """是否已存在关联的补交通道。"""
        return hasattr(obj, 'channel') and obj.channel is not None


class LateSubmitChannelSerializer(serializers.ModelSerializer):
    """补交通道序列化器。"""
    opened_by_name = serializers.CharField(source='opened_by.username', read_only=True, allow_null=True)
    closed_by_name = serializers.CharField(source='closed_by.username', read_only=True, allow_null=True)
    target_user_name = serializers.CharField(source='target_user.username', read_only=True, allow_null=True)
    target_user_student_no = serializers.CharField(source='target_user.student_no', read_only=True, allow_null=True)
    target_class_name = serializers.CharField(source='target_class.name', read_only=True, allow_null=True)
    project_name = serializers.CharField(source='project.name', read_only=True, allow_null=True)
    scope_label = serializers.SerializerMethodField()
    close_reason_label = serializers.SerializerMethodField()
    pending_submissions_count = serializers.SerializerMethodField()
    pending_submissions = serializers.SerializerMethodField()

    class Meta:
        model = LateSubmitChannel
        fields = [
            'id',
            'opened_by', 'opened_by_name',
            'scope_type', 'scope_label',
            'target_user', 'target_user_name', 'target_user_student_no',
            'target_class', 'target_class_name',
            'project', 'project_name',
            'reason', 'duration_hours',
            'open_at', 'planned_close_at',
            'actual_close_at', 'closed_by', 'closed_by_name',
            'close_reason', 'close_reason_label',
            'is_active',
            'from_request',
            'pending_submissions_count',
            'pending_submissions',
        ]

    def get_scope_label(self, obj):
        """返回范围类型中文名称。"""
        return obj.get_scope_type_display()

    def get_close_reason_label(self, obj):
        """返回关闭原因中文名称。"""
        return obj.get_close_reason_display() if obj.close_reason else ''

    def _channel_submission_queryset(self, obj):
        """
        构造“属于该通道”的待推送提交查询：
        1) 范围匹配（用户/班级）
        2) 项目匹配（限定项目或不限）
        3) 补交通道提交 + 已提交状态
        4) 提交时间落在通道开启-关闭窗口内，避免历史通道误吸收新提交
        """
        from django.db.models import Q
        from submission.models import StudentSubmission

        if obj.scope_type == LateSubmitChannel.SCOPE_USER and obj.target_user:
            user_q = Q(user=obj.target_user)
        elif obj.scope_type == LateSubmitChannel.SCOPE_CLASS and obj.target_class:
            user_q = Q(user__class_obj=obj.target_class)
        else:
            return StudentSubmission.objects.none()

        base_q = Q(via_late_channel=True, status='submitted', submitted_at__isnull=False)
        if obj.project:
            base_q &= Q(project=obj.project)
        if obj.open_at:
            base_q &= Q(submitted_at__gte=obj.open_at)
        close_boundary = obj.actual_close_at or obj.planned_close_at
        if close_boundary:
            base_q &= Q(submitted_at__lte=close_boundary)

        return StudentSubmission.objects.filter(base_q).filter(user_q)

    def get_pending_submissions_count(self, obj):
        """返回该通道下待推送的补交记录数量。"""
        ctx = self.context or {}
        precomputed = (ctx.get('channel_pending_count_map') or {}).get(obj.id)
        if precomputed is not None:
            return precomputed
        return self._channel_submission_queryset(obj).count()

    def get_pending_submissions(self, obj):
        """返回该通道下待推送的补交记录列表（仅在请求详情时返回）。"""
        # 只有在请求参数中明确要求时才返回详细列表，避免列表接口性能问题
        request = self.context.get('request')
        if not request or request.query_params.get('include_submissions') != '1':
            return None

        submissions = self._channel_submission_queryset(obj).select_related(
            'user', 'project'
        ).order_by('-submitted_at')

        # 返回简化的数据结构
        return [
            {
                'id': sub.id,
                'student_name': sub.user.username if sub.user else '—',
                'student_no': sub.user.student_no if sub.user else '—',
                'project_name': sub.project.name if sub.project else '—',
                'submitted_at': sub.submitted_at,
                'status': sub.status,
            }
            for sub in submissions
        ]


class LatePendingSubmissionSerializer(serializers.ModelSerializer):
    """待推送中心扁平记录序列化器（按补交提交记录维度）。"""
    student_name = serializers.CharField(source='user.username', read_only=True)
    student_no = serializers.CharField(source='user.student_no', read_only=True, allow_null=True)
    department_name = serializers.CharField(source='user.department.name', read_only=True, allow_null=True)
    major_name = serializers.CharField(source='user.class_obj.major.name', read_only=True, allow_null=True)
    class_name = serializers.CharField(source='user.class_obj.name', read_only=True, allow_null=True)
    class_grade = serializers.CharField(source='user.class_obj.grade', read_only=True, allow_null=True)
    season_name = serializers.CharField(source='project.season.name', read_only=True, allow_null=True)
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = StudentSubmission
        fields = [
            'id',
            'student_name', 'student_no',
            'department_name', 'major_name', 'class_name', 'class_grade',
            'season_name', 'project_name',
            'submitted_at', 'status',
        ]


class ImportPermissionRequestSerializer(serializers.ModelSerializer):
    """导入权限申请序列化器。"""
    requester_name = serializers.CharField(source='requester.username', read_only=True)
    requester_role = serializers.CharField(source='requester.current_role.name', read_only=True, allow_null=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    handler_name = serializers.CharField(source='handler.username', read_only=True, allow_null=True)
    status_label = serializers.SerializerMethodField()

    class Meta:
        model = ImportPermissionRequest
        fields = [
            'id',
            'project',
            'project_name',
            'requester',
            'requester_name',
            'requester_role',
            'requester_level',
            'target_scope',
            'reason',
            'status',
            'status_label',
            'handler',
            'handler_name',
            'handle_comment',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['status', 'handler', 'handle_comment', 'created_at', 'updated_at']

    def get_status_label(self, obj):
        return obj.get_status_display()
