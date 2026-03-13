"""
测评周期、项目、指标与规则序列化器。
"""
from django.utils import timezone
from rest_framework import serializers
from .models import (
    EvalSeason,
    EvalProject,
    EvalIndicator,
    ScoreWeightRule,
    ReviewRule,
    EvalProjectConfigTemplate,
)


class EvalSeasonSerializer(serializers.ModelSerializer):
    """测评周期。"""

    class Meta:
        model = EvalSeason
        fields = [
            'id', 'name', 'academic_year', 'semester', 'status',
            'start_time', 'end_time', 'created_at', 'updated_at',
        ]

    def to_representation(self, instance):
        """若存储状态为"进行中"但已超过结束时间，读时自动返回"已结束"（不写库）。"""
        data = super().to_representation(instance)
        if (
            instance.status == 'ongoing'
            and instance.end_time is not None
            and timezone.now() > instance.end_time
        ):
            data['status'] = 'closed'
        return data

    def validate(self, attrs):
        instance = self.instance
        start_time = attrs.get('start_time', instance.start_time if instance else None)
        end_time = attrs.get('end_time', instance.end_time if instance else None)

        # 时间顺序检查
        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError({'end_time': '结束时间必须晚于开始时间'})

        # 若要设置为"进行中"，当前时间不得超过结束时间
        new_status = attrs.get('status', instance.status if instance else 'draft')
        if new_status == 'ongoing' and end_time and timezone.now() > end_time:
            raise serializers.ValidationError({
                'status': '测评周期结束时间已过，无法设为"进行中"。请先将结束时间调整到未来。'
            })
        return attrs


class EvalProjectListSerializer(serializers.ModelSerializer):
    """项目列表（含 season 名和项目时间字段）。"""
    season_name = serializers.CharField(source='season.name', read_only=True)

    class Meta:
        model = EvalProject
        fields = [
            'id', 'season', 'season_name', 'name', 'description', 'status',
            'start_time', 'end_time', 'review_end_time',
            'allow_late_submit', 'late_submit_deadline', 'created_at', 'updated_at',
        ]

    def to_representation(self, instance):
        """若存储状态为"进行中"但已超过结束时间且无有效迟交窗口，读时自动返回"已结束"（不写库）。"""
        data = super().to_representation(instance)
        data['status'] = _compute_effective_project_status(instance)
        return data


def _season_effectively_closed(season, now):
    """
    判断周期是否实际已结束：
    - DB status='closed'（管理员手动硬关闭），或
    - DB status='ongoing' 且 end_time 已过（时间到期软关闭）
    """
    if season is None:
        return False
    if season.status == 'closed':
        return True
    if season.status == 'ongoing' and season.end_time is not None and now > season.end_time:
        return True
    return False


def _compute_effective_project_status(instance):
    """
    计算项目的有效状态（不修改数据库）。
    规则（优先级由高到低）：

    1. 测评周期已结束（status='closed' 或 end_time 已过）→ 项目无条件"已结束"。
       测评周期是最外层硬边界，周期一结束，周期内所有项目立即停止，
       迟交窗口不构成任何例外。如需在周期结束后补交，须由管理员开启补交通道。

    2. 项目自有结束时间已过（或回退到周期结束时间已过）→ 若项目级迟交窗口仍开放
       则保持进行中（迟交窗口是项目截止后、周期内的宽限期），否则"已结束"。

    3. 其他情况 → 保持原存储状态。
    """
    if instance.status != 'ongoing':
        return instance.status
    now = timezone.now()

    # 规则 1：周期已结束（硬关闭或时间到期）→ 项目无条件结束，无任何例外
    if _season_effectively_closed(instance.season, now):
        return 'closed'

    # 规则 2：检查项目自有结束时间；未设置则回退到周期结束时间
    effective_end_time = instance.end_time
    if effective_end_time is None:
        effective_end_time = instance.season.end_time if instance.season else None
    if effective_end_time is None:
        return instance.status  # 项目和周期均无结束时间，保持原状
    if now <= effective_end_time:
        return instance.status  # 仍在时间窗口内
    # 项目截止后：迟交窗口有效则继续（迟交窗口由 validate 保证 ≤ season.end_time）
    late_still_valid = (
        instance.allow_late_submit
        and instance.late_submit_deadline is not None
        and instance.late_submit_deadline > now
    )
    return instance.status if late_still_valid else 'closed'


class EvalProjectSerializer(serializers.ModelSerializer):
    """项目详情（含所属周期时间，供前端状态校验和时间约束验证用）。"""
    season_start_time = serializers.DateTimeField(source='season.start_time', read_only=True)
    season_end_time = serializers.DateTimeField(source='season.end_time', read_only=True)

    class Meta:
        model = EvalProject
        fields = [
            'id', 'season', 'name', 'description', 'status',
            'start_time', 'end_time', 'review_end_time',
            'allow_late_submit', 'late_submit_deadline',
            'import_config',
            'season_start_time', 'season_end_time',
            'created_at', 'updated_at',
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['status'] = _compute_effective_project_status(instance)
        return data

    def validate(self, attrs):
        instance = self.instance
        now = timezone.now()

        # 取各时间字段（支持 PATCH partial update）
        # 创建时 season 来自 attrs；更新时来自已有实例
        season = attrs.get('season', getattr(instance, 'season', None) if instance else None)
        p_start = attrs.get('start_time', instance.start_time if instance else None)
        p_end = attrs.get('end_time', instance.end_time if instance else None)
        r_end = attrs.get('review_end_time', instance.review_end_time if instance else None)
        allow_late = attrs.get('allow_late_submit', instance.allow_late_submit if instance else False)
        late_deadline = attrs.get('late_submit_deadline', instance.late_submit_deadline if instance else None)
        new_status = attrs.get('status', instance.status if instance else 'draft')

        # ── 项目时间顺序 ──────────────────────────────────────────
        if p_start and p_end and p_end <= p_start:
            raise serializers.ValidationError({'end_time': '项目结束时间必须晚于开始时间'})

        if p_end and r_end and r_end < p_end:
            raise serializers.ValidationError(
                {'review_end_time': '成绩评定截止时间不得早于项目结束时间'}
            )

        # ── 项目时间必须在测评周期范围内 ──────────────────────────
        if season:
            if season.start_time and p_start and p_start < season.start_time:
                raise serializers.ValidationError(
                    {'start_time': '项目开始时间不得早于所属测评周期的开始时间'}
                )
            if season.end_time and p_end and p_end > season.end_time:
                raise serializers.ValidationError(
                    {'end_time': '项目结束时间不得晚于所属测评周期的结束时间'}
                )
            if season.end_time and r_end and r_end > season.end_time:
                raise serializers.ValidationError(
                    {'review_end_time': '成绩评定截止时间不得晚于所属测评周期的结束时间'}
                )

        # ── 迟交截止时间约束 ──────────────────────────────────────
        if allow_late and late_deadline:
            if p_end and late_deadline <= p_end:
                raise serializers.ValidationError(
                    {'late_submit_deadline': '迟交截止时间必须晚于项目结束时间'}
                )
            if r_end and late_deadline > r_end:
                raise serializers.ValidationError(
                    {'late_submit_deadline': '迟交截止时间不得晚于成绩评定截止时间（教师需有时间批改补交材料）'}
                )
            # 迟交截止时间不得晚于测评周期结束时间（周期是最外层硬边界）
            if season and season.end_time and late_deadline > season.end_time:
                raise serializers.ValidationError(
                    {'late_submit_deadline': '迟交截止时间不得晚于所属测评周期的结束时间'}
                )

        # ── 状态校验 ──────────────────────────────────────────────
        if new_status == 'ongoing':
            # 前置检查 A：周期被手动关闭（硬关闭）→ 无条件拒绝，迟交窗口不构成例外
            if season and season.status == 'closed':
                raise serializers.ValidationError({
                    'status': (
                        '所属测评周期已被关闭，无法将项目设置为"进行中"。'
                        '请先重新开放所属测评周期后再试。'
                    )
                })
            # 条件 A：当前时间在项目自有时间窗口内
            project_window_valid = p_start and p_end and p_start <= now <= p_end
            # 条件 A 回退：项目无自有时间则检查测评周期时间
            if not project_window_valid and (not p_start or not p_end):
                season_valid = (
                    season is not None
                    and season.start_time is not None
                    and season.end_time is not None
                    and season.start_time <= now <= season.end_time
                )
            else:
                season_valid = False
            # 条件 B：迟交窗口仍开放
            late_valid = bool(allow_late and late_deadline and late_deadline > now)

            if not project_window_valid and not season_valid and not late_valid:
                raise serializers.ValidationError({
                    'status': (
                        '当前时间已超出项目开放范围且迟交截止时间已过（或未开放），'
                        '无法将项目设置为"进行中"。'
                        '请修改项目时间或设置有效的迟交截止时间后再试。'
                    )
                })
        return attrs


class EvalIndicatorSerializer(serializers.ModelSerializer):
    """指标（扁平结构）：用于列表查询与创建/更新操作。"""

    class Meta:
        model = EvalIndicator
        fields = [
            'id', 'project', 'parent',
            'name', 'description', 'category',
            'max_score', 'weight', 'agg_formula', 'score_source',
            'is_record_only', 'require_process_record', 'record_only_requires_review',
            'grade_rules',
            'order', 'created_at', 'updated_at',
        ]
        read_only_fields = ['project']

    def validate(self, attrs):
        """仅记录模块字段兜底：默认不强制过程记录，且非仅记录时不进入推评审。"""
        is_record_only = attrs.get('is_record_only')
        if is_record_only is None and self.instance is not None:
            is_record_only = self.instance.is_record_only
        if is_record_only and 'require_process_record' not in attrs:
            attrs['require_process_record'] = False
        score_source = attrs.get('score_source')
        if score_source is None and self.instance is not None:
            score_source = self.instance.score_source
        if (not is_record_only) or score_source != 'self':
            attrs['record_only_requires_review'] = False
        return attrs


class EvalIndicatorNodeSerializer(serializers.ModelSerializer):
    """
    指标节点（递归嵌套），用于 /indicators/tree/ 接口（只读，任意深度）。
    子节点列表从调用方预先挂载的 _children 属性读取，避免 N+1 查询。
    """
    children = serializers.SerializerMethodField()

    class Meta:
        model = EvalIndicator
        fields = [
            'id', 'project', 'parent',
            'name', 'description', 'category',
            'max_score', 'weight', 'agg_formula', 'score_source',
            'is_record_only', 'require_process_record', 'record_only_requires_review',
            'grade_rules',
            'order', 'children', 'created_at', 'updated_at',
        ]

    def get_children(self, obj):
        # _children 由 _build_indicator_tree 在内存中预组装好，无额外 DB 查询
        children = getattr(obj, '_children', [])
        return EvalIndicatorNodeSerializer(children, many=True).data


# 保持旧名称别名，兼容 views.py 中尚未更新的引用
EvalIndicatorTreeSerializer = EvalIndicatorNodeSerializer


class ScoreWeightRuleSerializer(serializers.ModelSerializer):
    """总分权重规则。"""

    class Meta:
        model = ScoreWeightRule
        fields = ['id', 'project', 'formula_type', 'formula_config', 'created_at', 'updated_at']


class ReviewRuleSerializer(serializers.ModelSerializer):
    """双评与仲裁规则。"""

    def validate_allowed_assistant_count_per_submission(self, value):
        """双评人数下限校验。"""
        if value is None:
            return 2
        if int(value) < 2:
            raise serializers.ValidationError('每份提交分配助理人数至少为 2')
        return int(value)

    def validate_single_review_mode(self, value):
        """单评执行人校验。"""
        if not value:
            return 'assistant_single'
        allowed = {choice[0] for choice in ReviewRule.SINGLE_REVIEW_MODE_CHOICES}
        if value not in allowed:
            raise serializers.ValidationError('单评执行人模式不合法')
        return value

    def validate_module_diff_thresholds(self, value):
        """模块阈值校验。"""
        if value in (None, ''):
            return {}
        if not isinstance(value, dict):
            raise serializers.ValidationError('模块阈值必须为对象')
        normalized = {}
        for raw_key, raw_val in value.items():
            key = str(raw_key).strip()
            if not key:
                continue
            try:
                num = float(raw_val)
            except (TypeError, ValueError):
                raise serializers.ValidationError(f'模块[{key}]阈值不是合法数字')
            if num < 0:
                raise serializers.ValidationError(f'模块[{key}]阈值不能小于0')
            normalized[key] = num
        return normalized

    class Meta:
        model = ReviewRule
        fields = [
            'id', 'project', 'dual_review_enabled',
            'review_scope_mode', 'cross_class_shuffle_enabled', 'allowed_assistant_count_per_submission',
            'counselor_participation_mode',
            'single_review_mode',
            'score_diff_threshold',
            'overall_score_diff_threshold',
            'module_diff_thresholds',
            'final_score_rule', 'allow_view_other_scores', 'require_arbitration_above_threshold',
            'created_at', 'updated_at',
        ]


class EvalProjectConfigTemplateSerializer(serializers.ModelSerializer):
    """测评项目配置模板。"""
    created_by_name = serializers.SerializerMethodField()

    def get_created_by_name(self, obj):
        if not obj.created_by:
            return ''
        return obj.created_by.name or obj.created_by.username

    class Meta:
        model = EvalProjectConfigTemplate
        fields = [
            'id', 'name', 'visibility', 'created_by', 'created_by_name',
            'include_sections', 'payload', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
