"""
学生提交与佐证序列化器。
"""
import os
from rest_framework import serializers
from .models import StudentSubmission, Evidence, SubmissionAnswer
from .display_state import derive_submission_display_state


class EvidenceSerializer(serializers.ModelSerializer):
    """佐证材料。"""
    indicator_name = serializers.CharField(source='indicator.name', read_only=True, allow_null=True)
    file_ext = serializers.SerializerMethodField()

    class Meta:
        model = Evidence
        fields = ['id', 'file', 'file_ext', 'category', 'name', 'indicator', 'indicator_name', 'created_at']
        read_only_fields = ['created_at']

    def get_file_ext(self, obj):
        """返回附件扩展名（小写，不含点）。"""
        name = ''
        if obj.file:
            name = obj.file.name or ''
        _, ext = os.path.splitext(name)
        return ext.lower().lstrip('.')


class StudentSubmissionSerializer(serializers.ModelSerializer):
    """提交详情（含佐证）。"""
    evidences = serializers.SerializerMethodField()
    project_name = serializers.CharField(source='project.name', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_real_name = serializers.CharField(source='user.name', default='', read_only=True)
    user_student_no = serializers.CharField(source='user.student_no', default='', read_only=True)
    user_class_name = serializers.CharField(source='user.class_obj.name', default='', read_only=True)
    user_department_name = serializers.CharField(source='user.department.name', default='', read_only=True)
    answer_count = serializers.SerializerMethodField()
    is_arbitrated = serializers.SerializerMethodField()
    display_status = serializers.SerializerMethodField()
    display_tone = serializers.SerializerMethodField()

    class Meta:
        model = StudentSubmission
        fields = [
            'id', 'project', 'project_name', 'user', 'user_name',
            'user_real_name', 'user_student_no', 'user_class_name', 'user_department_name',
            'status', 'self_score', 'final_score', 'score_detail',
            'is_arbitrated',
            'display_status', 'display_tone',
            'submitted_at', 'remark', 'evidences',
            'answer_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['user', 'status', 'submitted_at', 'final_score', 'score_detail']

    def get_answer_count(self, obj):
        return obj.answers.count()

    def get_is_arbitrated(self, obj):
        """返回该提交是否存在仲裁记录。"""
        cache_value = getattr(obj, '_cached_is_arbitrated', None)
        if cache_value is not None:
            return bool(cache_value)
        from scoring.models import ArbitrationRecord
        result = ArbitrationRecord.objects.filter(submission=obj).exists()
        setattr(obj, '_cached_is_arbitrated', result)
        return result

    def get_display_status(self, obj):
        label, _ = derive_submission_display_state(
            obj.status,
            is_arbitrated=self.get_is_arbitrated(obj),
        )
        return label

    def get_display_tone(self, obj):
        _, tone = derive_submission_display_state(
            obj.status,
            is_arbitrated=self.get_is_arbitrated(obj),
        )
        return tone

    def get_evidences(self, obj):
        """只返回未删除的佐证材料。"""
        evidences = obj.evidences.filter(is_deleted=False).order_by('id')
        return EvidenceSerializer(evidences, many=True, context=self.context).data


class StudentSubmissionListSerializer(serializers.ModelSerializer):
    """提交列表（精简）。"""
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = StudentSubmission
        fields = ['id', 'project', 'project_name', 'status', 'submitted_at', 'final_score', 'created_at']


class StudentSubmissionCreateUpdateSerializer(serializers.ModelSerializer):
    """创建/更新提交（自评、佐证由单独接口或嵌套处理）。"""

    class Meta:
        model = StudentSubmission
        fields = ['id', 'project', 'self_score', 'remark']

    def update(self, instance, validated_data):
        validated_data.pop('project', None)  # 禁止更新 project
        return super().update(instance, validated_data)


class SubmissionTaskSerializer(serializers.Serializer):
    """学生任务中心列表项。"""
    project_id = serializers.IntegerField()
    project_name = serializers.CharField()
    season_id = serializers.IntegerField(allow_null=True)
    season_name = serializers.CharField(allow_blank=True)
    project_status = serializers.CharField()
    start_time = serializers.DateTimeField(allow_null=True)
    end_time = serializers.DateTimeField(allow_null=True)
    allow_late_submit = serializers.BooleanField()
    late_submit_deadline = serializers.DateTimeField(allow_null=True)
    submission_id = serializers.IntegerField(allow_null=True)
    submission_status = serializers.CharField(allow_null=True)
    final_score = serializers.FloatField(allow_null=True)
    is_arbitrated = serializers.BooleanField()
    submitted_at = serializers.DateTimeField(allow_null=True)
    can_submit = serializers.BooleanField()
    entry_state = serializers.CharField()
    entry_label = serializers.CharField()
    display_status = serializers.CharField()
    display_tone = serializers.CharField()
    recommended_action = serializers.CharField()
    action_label = serializers.CharField()


class SubmissionAnswerSerializer(serializers.ModelSerializer):
    """题目作答记录。"""

    class Meta:
        model = SubmissionAnswer
        fields = [
            'id', 'submission', 'indicator',
            'self_score', 'process_record', 'is_completed',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class SubmissionQuestionSerializer(serializers.Serializer):
    """题目化作答视图中的单题结构。"""
    indicator_id = serializers.IntegerField()
    indicator_name = serializers.CharField()
    score_source = serializers.CharField()
    section_name = serializers.CharField(allow_blank=True)
    subsection_name = serializers.CharField(allow_blank=True)
    max_score = serializers.DecimalField(max_digits=6, decimal_places=2, allow_null=True)
    order = serializers.IntegerField()
    self_score = serializers.DecimalField(max_digits=6, decimal_places=2, allow_null=True)
    process_record = serializers.CharField(allow_blank=True)
    is_completed = serializers.BooleanField()
    evidence_count = serializers.IntegerField()
    require_process_record = serializers.BooleanField()
    parent_indicator_id = serializers.IntegerField(allow_null=True)
    parent_agg_formula = serializers.CharField(allow_null=True, allow_blank=True)
    parent_max_score = serializers.CharField(allow_null=True, allow_blank=True)
    imported_score = serializers.CharField(allow_null=True, allow_blank=True)
    reviewer_score = serializers.CharField(allow_null=True, allow_blank=True)
