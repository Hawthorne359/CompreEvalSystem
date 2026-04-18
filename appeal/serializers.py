"""
申诉序列化器。
"""
from rest_framework import serializers
import os
from .models import Appeal, AppealAttachment


class AppealAttachmentSerializer(serializers.ModelSerializer):
    """申诉附件。"""
    file_ext = serializers.SerializerMethodField()
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True, allow_null=True)

    class Meta:
        model = AppealAttachment
        fields = ['id', 'file', 'file_ext', 'name', 'uploaded_by', 'uploaded_by_name', 'created_at']
        read_only_fields = ['uploaded_by', 'created_at']

    def get_file_ext(self, obj):
        """返回附件扩展名。"""
        name = obj.file.name if obj.file else ''
        _, ext = os.path.splitext(name)
        return ext.lower().lstrip('.')


class AppealSerializer(serializers.ModelSerializer):
    """申诉详情。"""
    submission_detail = serializers.SerializerMethodField()
    handler_name = serializers.CharField(source='handler.username', read_only=True, allow_null=True)
    indicator_name = serializers.SerializerMethodField()
    escalated_to_name = serializers.SerializerMethodField()
    escalated_to_admin_name = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    current_handler_level = serializers.SerializerMethodField()
    current_handler_level_name = serializers.SerializerMethodField()
    progress_steps = serializers.SerializerMethodField()
    attachments = AppealAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Appeal
        fields = [
            'id', 'title', 'user', 'user_name',
            'submission', 'submission_detail',
            'indicator', 'indicator_name',
            'reason', 'status', 'original_submission_status',
            'handler', 'handler_name', 'handle_comment',
            'is_escalated', 'escalated_to', 'escalated_to_name', 'escalate_comment',
            'escalated_to_admin', 'escalated_to_admin_name', 'admin_comment',
            'current_handler_level', 'current_handler_level_name', 'progress_steps',
            'attachments',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['submission', 'indicator', 'handler', 'status', 'handle_comment',
                            'original_submission_status',
                            'is_escalated', 'escalated_to', 'escalate_comment',
                            'escalated_to_admin', 'admin_comment']

    def get_submission_detail(self, obj):
        if obj.submission_id is None:
            return None
        from submission.serializers import StudentSubmissionListSerializer
        return StudentSubmissionListSerializer(obj.submission).data

    def get_user_name(self, obj):
        if obj.user_id:
            u = obj.user
            return u.get_full_name() or u.username if u else None
        if obj.submission_id and obj.submission:
            u = obj.submission.user
            return u.get_full_name() or u.username if u else None
        return None

    def get_indicator_name(self, obj):
        if obj.indicator_id:
            return obj.indicator.name if obj.indicator else None
        return None

    def get_escalated_to_name(self, obj):
        if obj.escalated_to_id:
            u = obj.escalated_to
            return u.get_full_name() or u.username if u else None
        return None

    def get_escalated_to_admin_name(self, obj):
        if obj.escalated_to_admin_id:
            u = obj.escalated_to_admin
            return u.get_full_name() or u.username if u else None
        return None

    HANDLER_LEVEL_MAP = {
        'pending': (2, '评审老师'),
        'escalated': (3, '院系主任'),
        'escalated_to_admin': (5, '超级管理员'),
    }

    def get_current_handler_level(self, obj):
        entry = self.HANDLER_LEVEL_MAP.get(obj.status)
        return entry[0] if entry else None

    def get_current_handler_level_name(self, obj):
        entry = self.HANDLER_LEVEL_MAP.get(obj.status)
        return entry[1] if entry else None

    def get_progress_steps(self, obj):
        steps = [{'key': 'filed', 'label': '已发起', 'done': True, 'time': obj.created_at}]
        if obj.handler_id or obj.status not in ('pending',):
            steps.append({
                'key': 'counselor',
                'label': '评审老师处理',
                'done': obj.handler_id is not None,
                'handler': obj.handler.get_full_name() if obj.handler_id and obj.handler else None,
                'comment': obj.handle_comment or None,
                'active': obj.status == 'pending',
            })
        if obj.is_escalated or obj.status in ('escalated', 'escalated_to_admin', 'approved', 'rejected'):
            if obj.escalated_to_id or obj.status in ('escalated',):
                steps.append({
                    'key': 'director',
                    'label': '院系主任处理',
                    'done': obj.status not in ('escalated',),
                    'handler': obj.escalated_to.get_full_name() if obj.escalated_to_id and obj.escalated_to else None,
                    'comment': obj.escalate_comment or None,
                    'active': obj.status == 'escalated',
                })
        if obj.escalated_to_admin_id or obj.status == 'escalated_to_admin':
            steps.append({
                'key': 'admin',
                'label': '超级管理员处理',
                'done': obj.status not in ('escalated_to_admin',),
                'handler': obj.escalated_to_admin.get_full_name() if obj.escalated_to_admin_id and obj.escalated_to_admin else None,
                'comment': obj.admin_comment or None,
                'active': obj.status == 'escalated_to_admin',
            })
        if obj.status in ('approved', 'rejected'):
            steps.append({
                'key': 'result',
                'label': '已通过' if obj.status == 'approved' else '已驳回',
                'done': True,
            })
        return steps


class AppealCreateUpdateSerializer(serializers.ModelSerializer):
    """创建/修改申诉理由（仅 pending 可改）。"""

    class Meta:
        model = Appeal
        fields = ['id', 'reason']
