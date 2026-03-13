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
    attachments = AppealAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Appeal
        fields = [
            'id', 'submission', 'submission_detail',
            'indicator', 'indicator_name',
            'reason', 'status', 'original_submission_status',
            'handler', 'handler_name', 'handle_comment',
            'is_escalated', 'escalated_to', 'escalated_to_name', 'escalate_comment',
            'escalated_to_admin', 'escalated_to_admin_name', 'admin_comment',
            'attachments',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['submission', 'indicator', 'handler', 'status', 'handle_comment',
                            'original_submission_status',
                            'is_escalated', 'escalated_to', 'escalate_comment',
                            'escalated_to_admin', 'admin_comment']

    def get_submission_detail(self, obj):
        from submission.serializers import StudentSubmissionListSerializer
        return StudentSubmissionListSerializer(obj.submission).data

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


class AppealCreateUpdateSerializer(serializers.ModelSerializer):
    """创建/修改申诉理由（仅 pending 可改）。"""

    class Meta:
        model = Appeal
        fields = ['id', 'reason']
