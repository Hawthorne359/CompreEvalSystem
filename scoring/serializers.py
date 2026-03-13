"""
评分、仲裁、导入序列化器。
"""
from rest_framework import serializers
from .models import (
    ScoreRecord,
    ArbitrationRecord,
    ImportedScoreBatch,
    ImportedScoreDetail,
    ReviewAssignment,
    ReviewObjection,
    ReviewObjectionAttachment,
)
from submission.display_state import derive_submission_display_state


class ScoreRecordSerializer(serializers.ModelSerializer):
    """评分记录。"""
    reviewer_name = serializers.CharField(source='reviewer.username', read_only=True, allow_null=True)
    indicator_name = serializers.CharField(source='indicator.name', read_only=True)

    class Meta:
        model = ScoreRecord
        fields = [
            'id', 'submission', 'indicator', 'indicator_name',
            'reviewer', 'reviewer_name', 'score', 'comment', 'round_type',
            'score_channel', 'scorer_role_level', 'scorer_max_role_level', 'is_delegated',
            'created_at',
        ]
        read_only_fields = ['created_at']


class ArbitrationRecordSerializer(serializers.ModelSerializer):
    """仲裁记录。"""
    arbitrator_name = serializers.CharField(source='arbitrator.username', read_only=True, allow_null=True)

    class Meta:
        model = ArbitrationRecord
        fields = ['id', 'submission', 'indicator', 'arbitrator', 'arbitrator_name', 'arbitrator_level', 'score', 'comment', 'triggered_reason', 'created_at']


class ImportedScoreBatchSerializer(serializers.ModelSerializer):
    """导入批次。"""

    class Meta:
        model = ImportedScoreBatch
        fields = ['id', 'project', 'file_name', 'status', 'row_count', 'error_log', 'created_at']


class ReviewQuestionEvidenceSerializer(serializers.Serializer):
    """审核题目中的佐证材料。"""
    id = serializers.IntegerField()
    name = serializers.CharField(allow_blank=True)
    file = serializers.CharField(allow_blank=True)
    file_ext = serializers.CharField(allow_blank=True)
    created_at = serializers.DateTimeField(allow_null=True)


class ReviewQuestionSerializer(serializers.Serializer):
    """审核题目结构（与学生题目化作答保持一致）。"""
    indicator_id = serializers.IntegerField()
    indicator_name = serializers.CharField()
    section_name = serializers.CharField(allow_blank=True)
    max_score = serializers.DecimalField(max_digits=6, decimal_places=2)
    order = serializers.IntegerField()
    self_score = serializers.DecimalField(max_digits=6, decimal_places=2, allow_null=True)
    process_record = serializers.CharField(allow_blank=True)
    is_completed = serializers.BooleanField()
    evidence_count = serializers.IntegerField()
    require_process_record = serializers.BooleanField()
    is_record_only = serializers.BooleanField(required=False, default=False)
    evidences = ReviewQuestionEvidenceSerializer(many=True)
    latest_score = serializers.DecimalField(max_digits=6, decimal_places=2, allow_null=True)
    latest_comment = serializers.CharField(allow_blank=True)
    parent_indicator_id = serializers.IntegerField(allow_null=True)
    parent_agg_formula = serializers.CharField(allow_null=True, allow_blank=True)
    parent_max_score = serializers.CharField(allow_null=True, allow_blank=True)


class ReviewTaskSubmissionSerializer(serializers.Serializer):
    """审核任务列表序列化器，在 StudentSubmission 基础上增加 has_score_dispute 标记。"""
    id = serializers.IntegerField()
    project = serializers.IntegerField(source='project_id')
    project_name = serializers.CharField(source='project.name')
    user = serializers.IntegerField(source='user_id')
    user_name = serializers.CharField(source='user.username')
    user_real_name = serializers.CharField(source='user.name', default='')
    user_student_no = serializers.CharField(source='user.student_no', default='')
    user_class_name = serializers.CharField(source='user.class_obj.name', default='')
    user_department_name = serializers.CharField(source='user.department.name', default='')
    status = serializers.CharField()
    self_score = serializers.JSONField(default=dict)
    final_score = serializers.DecimalField(max_digits=8, decimal_places=2, allow_null=True)
    submitted_at = serializers.DateTimeField(allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    has_score_dispute = serializers.SerializerMethodField()
    is_assistant_submission = serializers.SerializerMethodField()
    is_arbitrated = serializers.SerializerMethodField()
    display_status = serializers.SerializerMethodField()
    display_tone = serializers.SerializerMethodField()

    def get_has_score_dispute(self, obj):
        """存在双评分歧（2 个及以上评审员评分）。"""
        rc = getattr(obj, '_reviewer_count', 0) or 0
        return rc >= 2

    def get_is_assistant_submission(self, obj):
        """通过 queryset 注解判断提交人是否为学生助理。"""
        return bool(getattr(obj, '_is_assistant_sub', False))

    def get_is_arbitrated(self, obj):
        """通过 queryset 注解判断是否存在仲裁记录。"""
        return bool((getattr(obj, '_arb_count', 0) or 0) > 0)

    def get_display_status(self, obj):
        label, _ = derive_submission_display_state(
            getattr(obj, 'status', None),
            is_arbitrated=self.get_is_arbitrated(obj),
        )
        return label

    def get_display_tone(self, obj):
        _, tone = derive_submission_display_state(
            getattr(obj, 'status', None),
            is_arbitrated=self.get_is_arbitrated(obj),
        )
        return tone


class ReviewAssignmentSerializer(serializers.ModelSerializer):
    """评审任务分配记录。"""
    reviewer_name = serializers.CharField(source='reviewer.username', read_only=True)
    submission_user_name = serializers.CharField(source='submission.user.username', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = ReviewAssignment
        fields = [
            'id', 'project', 'project_name', 'submission', 'submission_user_name',
            'reviewer', 'reviewer_name', 'role_type', 'round_type',
            'strategy_mode', 'assignment_version', 'status',
            'created_at', 'updated_at',
        ]


class ReviewObjectionAttachmentSerializer(serializers.ModelSerializer):
    """审核异议附件。"""
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True, allow_null=True)

    class Meta:
        model = ReviewObjectionAttachment
        fields = ['id', 'file', 'name', 'uploaded_by', 'uploaded_by_name', 'created_at']
        read_only_fields = ['uploaded_by', 'created_at']


class ReviewObjectionSerializer(serializers.ModelSerializer):
    """审核异议工单。"""
    submission_id = serializers.IntegerField(source='submission.id', read_only=True)
    submission_user_name = serializers.CharField(source='submission.user.username', read_only=True)
    indicator_name = serializers.CharField(source='indicator.name', read_only=True)
    raised_by_name = serializers.CharField(source='raised_by.username', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True, allow_null=True)
    attachments = ReviewObjectionAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = ReviewObjection
        fields = [
            'id',
            'submission',
            'submission_id',
            'submission_user_name',
            'indicator',
            'indicator_name',
            'raised_by',
            'raised_by_name',
            'assigned_to',
            'assigned_to_name',
            'source_role',
            'status',
            'current_handler_level',
            'reason',
            'resolution_comment',
            'resolved_score',
            'attachments',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'raised_by',
            'assigned_to',
            'source_role',
            'status',
            'current_handler_level',
            'resolution_comment',
            'resolved_score',
            'created_at',
            'updated_at',
        ]
