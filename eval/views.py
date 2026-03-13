"""
测评周期、项目、指标与规则 API。
"""
from django.core.cache import cache
from django.db import transaction
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from audit.models import OperationLog
from audit.services import log_action
from users.permissions import user_is_admin, user_level_at_least
from users.role_resolver import (
    ROLE_LEVEL_COUNSELOR, ROLE_LEVEL_DIRECTOR, ROLE_LEVEL_SUPERADMIN,
    get_role_display_name,
)

from .models import (
    EvalSeason,
    EvalProject,
    EvalIndicator,
    ScoreWeightRule,
    ReviewRule,
    EvalProjectConfigTemplate,
)
from .serializers import (
    EvalSeasonSerializer,
    EvalProjectListSerializer,
    EvalProjectSerializer,
    EvalIndicatorSerializer,
    EvalIndicatorTreeSerializer,
    ScoreWeightRuleSerializer,
    ReviewRuleSerializer,
    EvalProjectConfigTemplateSerializer,
)


def _require_superadmin(user):
    """是否为超级管理员（level >= 5）。"""
    return user_level_at_least(user, 5)


MAX_INDICATOR_DEPTH = 5


def _get_indicator_depth(indicator):
    """
    从该节点向上遍历，返回其所在深度（根节点=1）。
    用于深度校验，避免 N+1 — 深度最大 MAX_INDICATOR_DEPTH，查询次数有限。
    """
    depth, node = 1, indicator
    while node.parent_id is not None:
        depth += 1
        node = node.parent
    return depth


def _effective_max_score(child):
    """
    返回子项对父级聚合贡献的实际最大得分。

    若子项配置了 grade_rules，则对每条规则计算 min(raw_max × coeff, 规则行max_score)，
    取所有规则行中的最大值作为该子项的实际最大贡献。
    若无 grade_rules 或规则行为空，直接返回 child.max_score（Decimal）。

    此函数与 scoring/services.py 中 _apply_grade_rule 的打分逻辑保持语义一致，
    确保"配置时满分汇总"和"运行时实际得分上限"两套逻辑对齐。
    """
    from decimal import Decimal
    raw = Decimal(str(child.max_score))
    rules_config = child.grade_rules or {}
    rules = rules_config.get('rules') if isinstance(rules_config, dict) else None
    if not rules:
        return raw
    best = Decimal('0')
    for rule in rules:
        try:
            coeff = Decimal(str(rule.get('coefficient', 1) or 1))
            rule_max = rule.get('max_score')
            # 用规则行自身原始满分作为基准；若规则行未指定则退回 child.max_score
            rule_raw = Decimal(str(rule_max)) if rule_max is not None else raw
            effective = rule_raw * coeff
            if effective > best:
                best = effective
        except Exception:
            continue
    # 若所有规则行均异常导致 best 为 0，退回原始满分，避免汇总结果为 0
    return best if best > Decimal('0') else raw


def _child_effective_for_year(child, year_of_study):
    """
    @param {EvalIndicator} child - 子指标
    @param {int} year_of_study - 在读年级（1=大一,2=大二…）
    @returns {Decimal} 该子项在指定年级场景下对父级的实际最大贡献

    若子项无 grade_rules，直接返回 child.max_score。
    若有 grade_rules，找到匹配的规则行，返回 rule.max_score × coefficient。
    未匹配任何规则行时使用最后一条规则作为兜底（与打分逻辑一致）。
    """
    from decimal import Decimal
    raw = Decimal(str(child.max_score))
    rules_config = child.grade_rules or {}
    rules = rules_config.get('rules') if isinstance(rules_config, dict) else None
    if not rules:
        return raw
    matched = None
    fallback = None
    for rule in rules:
        try:
            min_y = int(rule.get('min_year', 0))
            max_y = int(rule.get('max_year', 99))
            if min_y <= year_of_study <= max_y:
                matched = rule
                break
            fallback = rule
        except (ValueError, TypeError):
            continue
    rule = matched or fallback
    if rule is None:
        return raw
    try:
        coeff = Decimal(str(rule.get('coefficient', 1) or 1))
        rule_max = rule.get('max_score')
        rule_raw = Decimal(str(rule_max)) if rule_max is not None else raw
        return rule_raw * coeff
    except Exception:
        return raw


def _collect_year_points(children):
    """
    @param {list[EvalIndicator]} children - 子指标列表
    @returns {list[int]|None} 所有子项 grade_rules 中出现的年级点集合（去重排序），
                              若无任何年级规则则返回 None

    用于枚举所有可能的年级场景，配合 _child_effective_for_year 做按场景汇总。
    """
    years = set()
    for child in children:
        rules_config = child.grade_rules or {}
        rules = rules_config.get('rules') if isinstance(rules_config, dict) else None
        if rules:
            for rule in rules:
                try:
                    min_y = int(rule.get('min_year', 0))
                    max_y = int(rule.get('max_year', 0))
                    for y in range(min_y, max_y + 1):
                        years.add(y)
                except (ValueError, TypeError):
                    continue
    return sorted(years) if years else None


def _sync_node_max_score(node):
    """
    @param {EvalIndicator} node - 待同步的父节点

    根据 node 的子项和 agg_formula 重算其 max_score，若无子项（叶节点）则跳过。
    支持 sum / weighted_sum / average / sum_capped 四种聚合方式。

    is_record_only=True 的子项不参与聚合计算，始终跳过。
    max_score=None 的子项（无上限记录性字段）也跳过聚合。
    sum_capped 模式下 max_score 由管理员手动配置（表示封顶值），不自动推算，直接 return。

    当子项含 grade_rules 时，采用「按年级场景汇总」算法：枚举所有可能的在读年级，
    为每个年级场景分别计算各子项的贡献之和，取各场景中的最大值作为父节点 max_score。
    这避免了"跨年级段取峰值再求和"导致的虚高（如用户案例中 120 vs 正确值 100）。
    """
    from decimal import Decimal
    children = [c for c in node.children.all() if not c.is_record_only and c.max_score is not None]
    if not children:
        return
    if node.agg_formula == 'sum_capped':
        return

    year_points = _collect_year_points(children)

    def _aggregate(contributions, formula):
        if formula == 'weighted_sum':
            return sum(
                contrib * Decimal(str(c.weight))
                for c, contrib in zip(children, contributions)
            )
        elif formula == 'average':
            return sum(contributions) / len(contributions)
        else:  # sum
            return sum(contributions)

    if year_points:
        best_total = Decimal('0')
        for year in year_points:
            contribs = [_child_effective_for_year(c, year) for c in children]
            total = _aggregate(contribs, node.agg_formula)
            if total > best_total:
                best_total = total
        total = best_total
    else:
        contribs = [Decimal(str(c.max_score)) for c in children]
        total = _aggregate(contribs, node.agg_formula)

    if node.max_score != total:
        node.max_score = total
        node.save(update_fields=['max_score'])


def _sync_ancestor_max_scores(indicator):
    """
    从 indicator 本身开始（若有子项则重算），然后逐级向上同步所有祖先节点。
    支持 sum / weighted_sum / average 三种聚合方式。

    起点包含 indicator 本身，是为了覆盖"节点自身的 agg_formula 被修改"的场景
    （如 A4 从 sum 改为 weighted_sum 时，A4 自己的 max_score 也需要重算）。
    """
    node = indicator
    while node is not None:
        _sync_node_max_score(node)
        node = node.parent



def _check_confirm_token(user, token):
    """校验密码确认 token（由 /auth/verify-password/ 签发，有效期 5 分钟）。"""
    if not token:
        return False
    cache_key = f'confirm_token:{user.id}:{token}'
    result = cache.get(cache_key)
    if result:
        # 一次性 token，使用后立即删除
        cache.delete(cache_key)
    return bool(result)


def _parse_batch_ids(raw_ids, field_name):
    """解析批量操作 ID 列表：去重、转 int、校验最少 2 条。"""
    if not isinstance(raw_ids, list):
        raise ValidationError({field_name: '请传入数组'})
    parsed = []
    for item in raw_ids:
        try:
            parsed.append(int(item))
        except (TypeError, ValueError):
            raise ValidationError({field_name: f'存在非法 ID：{item}'})
    unique_ids = list(dict.fromkeys(parsed))
    if len(unique_ids) < 2:
        raise ValidationError({field_name: '批量操作至少选择 2 条记录'})
    return unique_ids


def _can_manage_project_review_rule(user, project):
    """
    评审规则权限分级：
    - 超管（level>=5）：全局可改
    - 院系主任（level==3）：仅本院系范围内项目可改
    - 评审老师（level==2）：仅其负责班级范围内项目可改
    """
    from submission.models import StudentSubmission
    from users.models import UserRole

    level = user.current_role.level if user.current_role else -1
    if level >= 5:
        return True
    if level == 3:
        if not user.department_id:
            return False
        out_of_scope_exists = StudentSubmission.objects.filter(project=project).exclude(
            user__department_id=user.department_id
        ).exists()
        return not out_of_scope_exists
    if level == 2:
        scope_class_ids = list(
            UserRole.objects.filter(
                user=user, scope_type='class', scope_id__isnull=False
            ).values_list('scope_id', flat=True)
        )
        if not scope_class_ids:
            return False
        out_of_scope_exists = StudentSubmission.objects.filter(project=project).exclude(
            user__class_obj_id__in=scope_class_ids
        ).exists()
        return not out_of_scope_exists
    return False


class SeasonListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/v1/seasons/ 测评周期列表/创建（创建仅管理员）。"""
    queryset = EvalSeason.objects.all().order_by('-academic_year', '-semester')
    serializer_class = EvalSeasonSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        perms = [IsAuthenticated()]
        if self.request.method == 'POST':
            from users.permissions import user_is_admin
            if not user_is_admin(self.request.user):
                from rest_framework.permissions import BasePermission
                class AdminOnly(BasePermission):
                    def has_permission(self, request, view):
                        return user_is_admin(request.user)
                perms = [AdminOnly()]
        return perms

    def perform_create(self, serializer):
        if not user_is_admin(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(f'仅{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}可创建测评周期')
        instance = serializer.save()
        log_action(
            user=self.request.user,
            action='season_create',
            module=OperationLog.MODULE_EVAL,
            level=OperationLog.LEVEL_WARNING,
            target_type='eval_season',
            target_id=instance.id,
            target_repr=instance.name,
            request=self.request,
        )


class SeasonDetailView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/v1/seasons/<pk>/ 周期详情与更新。"""
    queryset = EvalSeason.objects.all()
    serializer_class = EvalSeasonSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        if not user_is_admin(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(f'仅{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}可修改测评周期')
        TRACKED = {
            'name': '名称', 'academic_year': '学年', 'semester': '学期',
            'status': '状态', 'start_time': '开始时间', 'end_time': '结束时间',
        }
        old_vals = {f: getattr(serializer.instance, f) for f in TRACKED}
        instance = serializer.save()
        changed = {}
        for field, label in TRACKED.items():
            old_v = old_vals[field]
            new_v = getattr(instance, field)
            if old_v != new_v:
                changed[label] = {
                    'old': str(old_v) if old_v is not None else '',
                    'new': str(new_v) if new_v is not None else '',
                }
        log_action(
            user=self.request.user,
            action='season_update',
            module=OperationLog.MODULE_EVAL,
            level=OperationLog.LEVEL_WARNING,
            target_type='eval_season',
            target_id=instance.id,
            target_repr=instance.name,
            extra={'changed': changed} if changed else {},
            request=self.request,
        )
        # 级联：若周期变为已结束，自动关闭其中仍为"进行中"的项目。
        # 硬关闭（status='closed'）：无条件关闭所有 ongoing 项目，迟交窗口不构成例外。
        # 软关闭（end_time 改为过去）：仅关闭没有有效迟交窗口的项目。
        from django.utils import timezone as tz
        now = tz.now()
        season_hard_closed = instance.status == 'closed'
        season_soft_closed = (
            not season_hard_closed
            and instance.end_time is not None
            and instance.end_time < now
        )
        if season_hard_closed or season_soft_closed:
            stale_projects = EvalProject.objects.filter(season=instance, status='ongoing')
            reason = '测评周期已被手动关闭' if season_hard_closed else '测评周期结束时间已过'
            for proj in stale_projects:
                # 周期一结束（无论硬关闭还是软关闭），项目无条件关闭
                proj.status = 'closed'
                proj.save(update_fields=['status'])
                log_action(
                    user=self.request.user,
                    action='project_update',
                    module=OperationLog.MODULE_EVAL,
                    level=OperationLog.LEVEL_WARNING,
                    target_type='eval_project',
                    target_id=proj.id,
                    target_repr=proj.name,
                    extra={
                        'changed': {'状态': {'old': 'ongoing', 'new': 'closed'}},
                        'auto_closed_reason': reason,
                    },
                    request=self.request,
                )


class SeasonDeleteView(APIView):
    """
    DELETE /api/v1/seasons/<pk>/
    删除测评周期。

    权限要求：超级管理员（level=5）+ 密码确认 token（由 /auth/verify-password/ 获取）。

    请求体（JSON 或 form-data）::

        {
            "confirm_token": "uuid-string",
            "reason": "删除原因（必填）"
        }
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        if not _require_superadmin(request.user):
            return Response({'detail': f'仅{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}可删除测评周期'}, status=status.HTTP_403_FORBIDDEN)

        confirm_token = request.data.get('confirm_token', '')
        reason = request.data.get('reason', '').strip()

        if not _check_confirm_token(request.user, confirm_token):
            return Response({'detail': '密码确认无效或已过期，请重新验证'}, status=status.HTTP_403_FORBIDDEN)
        if not reason:
            return Response({'detail': '删除理由不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            season = EvalSeason.objects.get(pk=pk)
        except EvalSeason.DoesNotExist:
            return Response({'detail': '测评周期不存在'}, status=status.HTTP_404_NOT_FOUND)

        season_name = season.name
        season_id = season.id
        season.delete()

        log_action(
            user=request.user,
            action='season_delete',
            module=OperationLog.MODULE_EVAL,
            level=OperationLog.LEVEL_CRITICAL,
            target_type='eval_season',
            target_id=season_id,
            target_repr=season_name,
            reason=reason,
            is_abnormal=False,
            is_audit_event=True,
            request=request,
        )
        return Response({'detail': f'已删除测评周期"{season_name}"'}, status=status.HTTP_200_OK)


class SeasonBatchStatusView(APIView):
    """POST /api/v1/seasons/batch-status/ 批量更新测评周期状态。"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not user_is_admin(request.user):
            raise PermissionDenied(f'仅{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}可批量修改测评周期状态')
        season_ids = _parse_batch_ids(request.data.get('season_ids', []), 'season_ids')
        new_status = request.data.get('status')
        if new_status not in {'draft', 'ongoing', 'closed'}:
            raise ValidationError({'status': '状态必须是 draft / ongoing / closed'})

        seasons = list(EvalSeason.objects.filter(id__in=season_ids).order_by('id'))
        if len(seasons) != len(season_ids):
            found = {s.id for s in seasons}
            missing = [sid for sid in season_ids if sid not in found]
            raise ValidationError({'season_ids': f'部分周期不存在：{missing}'})

        changed_items = []
        with transaction.atomic():
            for season in seasons:
                serializer = EvalSeasonSerializer(season, data={'status': new_status}, partial=True)
                serializer.is_valid(raise_exception=True)
                if season.status == new_status:
                    continue
                old_status = season.status
                serializer.save()
                changed_items.append({
                    'id': season.id,
                    'name': season.name,
                    'old_status': old_status,
                    'new_status': new_status,
                })

        log_action(
            user=request.user,
            action='season_batch_set_status',
            module=OperationLog.MODULE_EVAL,
            level=OperationLog.LEVEL_WARNING,
            target_type='eval_season',
            target_id=0,
            target_repr=f'批量修改周期状态 x{len(season_ids)}',
            extra={
                'season_ids': season_ids,
                'target_status': new_status,
                'changed_count': len(changed_items),
                'unchanged_count': len(season_ids) - len(changed_items),
                'changed_items': changed_items,
            },
            request=request,
        )
        return Response(
            {
                'detail': f'已处理 {len(season_ids)} 个周期，实际变更 {len(changed_items)} 个',
                'changed_count': len(changed_items),
            },
            status=status.HTTP_200_OK,
        )


class SeasonBatchDeleteView(APIView):
    """POST /api/v1/seasons/batch-delete/ 批量删除测评周期。"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not _require_superadmin(request.user):
            return Response({'detail': f'仅{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}可批量删除测评周期'}, status=status.HTTP_403_FORBIDDEN)

        season_ids = _parse_batch_ids(request.data.get('season_ids', []), 'season_ids')
        confirm_token = request.data.get('confirm_token', '')
        reason = (request.data.get('reason') or '').strip()
        if not _check_confirm_token(request.user, confirm_token):
            return Response({'detail': '密码确认无效或已过期，请重新验证'}, status=status.HTTP_403_FORBIDDEN)
        if not reason:
            return Response({'detail': '删除理由不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        seasons = list(EvalSeason.objects.filter(id__in=season_ids).order_by('id'))
        if len(seasons) != len(season_ids):
            found = {s.id for s in seasons}
            missing = [sid for sid in season_ids if sid not in found]
            return Response({'detail': f'部分周期不存在：{missing}'}, status=status.HTTP_400_BAD_REQUEST)

        deleted_items = [{'id': s.id, 'name': s.name} for s in seasons]
        with transaction.atomic():
            EvalSeason.objects.filter(id__in=season_ids).delete()

        log_action(
            user=request.user,
            action='season_batch_delete',
            module=OperationLog.MODULE_EVAL,
            level=OperationLog.LEVEL_CRITICAL,
            target_type='eval_season',
            target_id=0,
            target_repr=f'批量删除测评周期 x{len(season_ids)}',
            reason=reason,
            is_abnormal=False,
            is_audit_event=True,
            extra={'season_ids': season_ids, 'deleted_items': deleted_items},
            request=request,
        )
        return Response({'detail': f'已删除 {len(season_ids)} 个测评周期'}, status=status.HTTP_200_OK)


class SeasonProjectListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/v1/seasons/<id>/projects/ 某周期下项目列表/创建。"""
    serializer_class = EvalProjectListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return EvalProject.objects.filter(season_id=self.kwargs['season_id']).select_related('season').order_by('id')

    def get_permissions(self):
        perms = [IsAuthenticated()]
        if self.request.method == 'POST' and not user_is_admin(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(f'仅{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}可创建项目')
        return perms

    def perform_create(self, serializer):
        if not user_is_admin(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(f'仅{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}可创建项目')
        instance = serializer.save(season_id=self.kwargs['season_id'])
        log_action(
            user=self.request.user,
            action='project_create',
            module=OperationLog.MODULE_EVAL,
            level=OperationLog.LEVEL_WARNING,
            target_type='eval_project',
            target_id=instance.id,
            target_repr=instance.name,
            request=self.request,
        )


class ProjectDetailView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/v1/projects/<id>/ 项目详情/更新。"""
    queryset = EvalProject.objects.all().select_related('season')
    serializer_class = EvalProjectSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        if not user_is_admin(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(f'仅{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}可修改项目')
        TRACKED = {
            'name': '名称', 'description': '描述', 'status': '状态',
            'start_time': '开始时间', 'end_time': '结束时间', 'review_end_time': '评定截止',
            'allow_late_submit': '允许迟交', 'late_submit_deadline': '迟交截止',
        }
        old_vals = {f: getattr(serializer.instance, f) for f in TRACKED}
        instance = serializer.save()
        changed = {}
        for field, label in TRACKED.items():
            old_v = old_vals[field]
            new_v = getattr(instance, field)
            if old_v != new_v:
                changed[label] = {
                    'old': str(old_v) if old_v is not None else '',
                    'new': str(new_v) if new_v is not None else '',
                }
        log_action(
            user=self.request.user,
            action='project_update',
            module=OperationLog.MODULE_EVAL,
            level=OperationLog.LEVEL_WARNING,
            target_type='eval_project',
            target_id=instance.id,
            target_repr=instance.name,
            extra={'changed': changed} if changed else {},
            request=self.request,
        )
        # 级联：若项目结束时间被改为过去，自动关闭状态
        from django.utils import timezone as tz
        now = tz.now()
        if instance.end_time and instance.end_time < now and instance.status == 'ongoing':
            late_still_valid = (
                instance.allow_late_submit
                and instance.late_submit_deadline is not None
                and instance.late_submit_deadline > now
            )
            if not late_still_valid:
                instance.status = 'closed'
                instance.save(update_fields=['status'])
                log_action(
                    user=self.request.user,
                    action='project_update',
                    module=OperationLog.MODULE_EVAL,
                    level=OperationLog.LEVEL_WARNING,
                    target_type='eval_project',
                    target_id=instance.id,
                    target_repr=instance.name,
                    extra={
                        'changed': {'状态': {'old': 'ongoing', 'new': 'closed'}},
                        'auto_closed_reason': '项目结束时间已过',
                    },
                    request=self.request,
                )


class ProjectDeleteView(APIView):
    """
    DELETE /api/v1/projects/<pk>/
    删除测评项目。

    权限要求：超级管理员（level=5）+ 密码确认 token。

    请求体::

        {
            "confirm_token": "uuid-string",
            "reason": "删除原因（必填）"
        }
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        if not _require_superadmin(request.user):
            return Response({'detail': f'仅{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}可删除测评项目'}, status=status.HTTP_403_FORBIDDEN)

        confirm_token = request.data.get('confirm_token', '')
        reason = request.data.get('reason', '').strip()

        if not _check_confirm_token(request.user, confirm_token):
            return Response({'detail': '密码确认无效或已过期，请重新验证'}, status=status.HTTP_403_FORBIDDEN)
        if not reason:
            return Response({'detail': '删除理由不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            project = EvalProject.objects.select_related('season').get(pk=pk)
        except EvalProject.DoesNotExist:
            return Response({'detail': '测评项目不存在'}, status=status.HTTP_404_NOT_FOUND)

        project_name = project.name
        project_id = project.id
        project.delete()

        log_action(
            user=request.user,
            action='project_delete',
            module=OperationLog.MODULE_EVAL,
            level=OperationLog.LEVEL_CRITICAL,
            target_type='eval_project',
            target_id=project_id,
            target_repr=project_name,
            reason=reason,
            is_abnormal=False,
            is_audit_event=True,
            request=request,
        )
        return Response({'detail': f'已删除测评项目"{project_name}"'}, status=status.HTTP_200_OK)


class ProjectBatchStatusView(APIView):
    """POST /api/v1/projects/batch-status/ 批量更新测评项目状态。"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not user_is_admin(request.user):
            raise PermissionDenied(f'仅{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}可批量修改测评项目状态')
        project_ids = _parse_batch_ids(request.data.get('project_ids', []), 'project_ids')
        new_status = request.data.get('status')
        if new_status not in {'draft', 'ongoing', 'closed'}:
            raise ValidationError({'status': '状态必须是 draft / ongoing / closed'})

        projects = list(EvalProject.objects.select_related('season').filter(id__in=project_ids).order_by('id'))
        if len(projects) != len(project_ids):
            found = {p.id for p in projects}
            missing = [pid for pid in project_ids if pid not in found]
            raise ValidationError({'project_ids': f'部分项目不存在：{missing}'})

        changed_items = []
        with transaction.atomic():
            for project in projects:
                serializer = EvalProjectSerializer(project, data={'status': new_status}, partial=True)
                serializer.is_valid(raise_exception=True)
                if project.status == new_status:
                    continue
                old_status = project.status
                serializer.save()
                changed_items.append({
                    'id': project.id,
                    'name': project.name,
                    'old_status': old_status,
                    'new_status': new_status,
                })

        log_action(
            user=request.user,
            action='project_batch_set_status',
            module=OperationLog.MODULE_EVAL,
            level=OperationLog.LEVEL_WARNING,
            target_type='eval_project',
            target_id=0,
            target_repr=f'批量修改项目状态 x{len(project_ids)}',
            extra={
                'project_ids': project_ids,
                'target_status': new_status,
                'changed_count': len(changed_items),
                'unchanged_count': len(project_ids) - len(changed_items),
                'changed_items': changed_items,
            },
            request=request,
        )
        return Response(
            {
                'detail': f'已处理 {len(project_ids)} 个项目，实际变更 {len(changed_items)} 个',
                'changed_count': len(changed_items),
            },
            status=status.HTTP_200_OK,
        )


class ProjectBatchDeleteView(APIView):
    """POST /api/v1/projects/batch-delete/ 批量删除测评项目。"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not _require_superadmin(request.user):
            return Response({'detail': f'仅{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}可批量删除测评项目'}, status=status.HTTP_403_FORBIDDEN)

        project_ids = _parse_batch_ids(request.data.get('project_ids', []), 'project_ids')
        confirm_token = request.data.get('confirm_token', '')
        reason = (request.data.get('reason') or '').strip()
        if not _check_confirm_token(request.user, confirm_token):
            return Response({'detail': '密码确认无效或已过期，请重新验证'}, status=status.HTTP_403_FORBIDDEN)
        if not reason:
            return Response({'detail': '删除理由不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        projects = list(EvalProject.objects.filter(id__in=project_ids).order_by('id'))
        if len(projects) != len(project_ids):
            found = {p.id for p in projects}
            missing = [pid for pid in project_ids if pid not in found]
            return Response({'detail': f'部分项目不存在：{missing}'}, status=status.HTTP_400_BAD_REQUEST)

        deleted_items = [{'id': p.id, 'name': p.name} for p in projects]
        with transaction.atomic():
            EvalProject.objects.filter(id__in=project_ids).delete()

        log_action(
            user=request.user,
            action='project_batch_delete',
            module=OperationLog.MODULE_EVAL,
            level=OperationLog.LEVEL_CRITICAL,
            target_type='eval_project',
            target_id=0,
            target_repr=f'批量删除测评项目 x{len(project_ids)}',
            reason=reason,
            is_abnormal=False,
            is_audit_event=True,
            extra={'project_ids': project_ids, 'deleted_items': deleted_items},
            request=request,
        )
        return Response({'detail': f'已删除 {len(project_ids)} 个测评项目'}, status=status.HTTP_200_OK)


class ProjectIndicatorListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/v1/projects/<id>/indicators/ 指标扁平列表/创建。"""
    serializer_class = EvalIndicatorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return EvalIndicator.objects.filter(project_id=self.kwargs['project_id']).order_by('order', 'id')

    def perform_create(self, serializer):
        if not user_is_admin(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(f'仅{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}可创建指标')
        project_id = self.kwargs['project_id']
        parent = serializer.validated_data.get('parent')
        if parent is not None:
            # 校验 parent 属于同一项目
            if parent.project_id != project_id:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'parent': '父级指标必须属于同一测评项目'})
            # 深度校验：新子节点深度 = parent 深度 + 1，不得超过 MAX_INDICATOR_DEPTH
            if _get_indicator_depth(parent) >= MAX_INDICATOR_DEPTH:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'parent': f'指标嵌套不得超过 {MAX_INDICATOR_DEPTH} 级'})
        instance = serializer.save(project_id=project_id)
        _sync_ancestor_max_scores(instance)
        log_action(
            user=self.request.user,
            action='indicator_create',
            module=OperationLog.MODULE_EVAL,
            level=OperationLog.LEVEL_WARNING,
            target_type='eval_indicator',
            target_id=instance.id,
            target_repr=instance.name,
            request=self.request,
        )


def _build_indicator_tree(all_indicators):
    """
    将扁平的指标列表在内存中组装为嵌套树（任意深度），避免 N+1 查询。
    返回根节点列表（parent=None），每个节点含 _children 属性（已按 order/id 排序）。
    """
    by_parent = {}
    for ind in all_indicators:
        by_parent.setdefault(ind.parent_id, []).append(ind)

    def attach(node):
        node._children = sorted(by_parent.get(node.id, []), key=lambda c: (c.order, c.id))
        for child in node._children:
            attach(child)

    roots = sorted(by_parent.get(None, []), key=lambda c: (c.order, c.id))
    for root in roots:
        attach(root)
    return roots


class ProjectIndicatorTreeView(APIView):
    """GET /api/v1/projects/<project_id>/indicators/tree/ 返回嵌套树结构（任意深度）。"""
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        all_indicators = list(
            EvalIndicator.objects
            .filter(project_id=project_id)
            .order_by('order', 'id')
        )
        roots = _build_indicator_tree(all_indicators)
        # EvalIndicatorTreeSerializer is an alias for EvalIndicatorNodeSerializer (see serializers.py)
        serializer = EvalIndicatorTreeSerializer(roots, many=True)
        return Response(serializer.data)


class ProjectIndicatorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/v1/projects/<project_id>/indicators/<id>/。"""
    serializer_class = EvalIndicatorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return EvalIndicator.objects.filter(project_id=self.kwargs['project_id'])

    def perform_update(self, serializer):
        if not user_is_admin(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(f'仅{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}可修改指标')
        project_id = self.kwargs['project_id']
        parent = serializer.validated_data.get('parent', serializer.instance.parent)
        if parent is not None:
            if parent.project_id != project_id:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'parent': '父级指标必须属于同一测评项目'})
            # 深度校验
            if _get_indicator_depth(parent) >= MAX_INDICATOR_DEPTH:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'parent': f'指标嵌套不得超过 {MAX_INDICATOR_DEPTH} 级'})
            # 防止循环引用：指标不能将自身设为父级
            if parent.id == serializer.instance.id:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'parent': '指标不能将自身设为父级'})
        TRACKED = {
            'name': '名称', 'max_score': '满分', 'weight': '权重',
            'agg_formula': '聚合方式', 'score_source': '分数来源',
            'description': '描述', 'order': '排序',
        }
        old_vals = {f: getattr(serializer.instance, f) for f in TRACKED}
        instance = serializer.save()
        _sync_ancestor_max_scores(instance)
        changed = {}
        for field, label in TRACKED.items():
            old_v = old_vals[field]
            new_v = getattr(instance, field)
            if old_v != new_v:
                changed[label] = {
                    'old': str(old_v) if old_v is not None else '',
                    'new': str(new_v) if new_v is not None else '',
                }
        log_action(
            user=self.request.user,
            action='indicator_update',
            module=OperationLog.MODULE_EVAL,
            level=OperationLog.LEVEL_WARNING,
            target_type='eval_indicator',
            target_id=instance.id,
            target_repr=instance.name,
            extra={'changed': changed} if changed else {},
            request=self.request,
        )

    def perform_destroy(self, instance):
        if not user_is_admin(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(f'仅{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}可删除指标')
        target_repr = instance.name
        target_id = instance.id
        # 删除前将父节点引用保存到局部变量，delete() 后 instance.pk 变为 None，
        # 无法再通过 instance 查询 children，必须从 parent 开始向上同步。
        parent = instance.parent
        instance.delete()
        # 从父节点开始向上同步 max_score（跳过已删除的 instance）
        if parent is not None:
            _sync_ancestor_max_scores(parent)
        log_action(
            user=self.request.user,
            action='indicator_delete',
            module=OperationLog.MODULE_EVAL,
            level=OperationLog.LEVEL_WARNING,
            target_type='eval_indicator',
            target_id=target_id,
            target_repr=target_repr,
            request=self.request,
        )


class ProjectWeightRuleView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/v1/projects/<id>/weight-rule/ 总分权重规则。"""
    serializer_class = ScoreWeightRuleSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        project_id = self.kwargs['project_id']
        rule, _ = ScoreWeightRule.objects.get_or_create(project_id=project_id)
        return rule

    def perform_update(self, serializer):
        if not user_is_admin(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(f'仅{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}可修改权重规则')
        instance = serializer.save()
        log_action(
            user=self.request.user,
            action='weight_rule_update',
            module=OperationLog.MODULE_EVAL,
            level=OperationLog.LEVEL_WARNING,
            target_type='eval_project',
            target_id=instance.project_id,
            target_repr=f'项目#{instance.project_id}权重规则',
            request=self.request,
        )


class ProjectReviewRuleView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/v1/projects/<id>/review-rule/ 双评与仲裁规则。"""
    serializer_class = ReviewRuleSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        project_id = self.kwargs['project_id']
        rule, _ = ReviewRule.objects.get_or_create(project_id=project_id)
        return rule

    def perform_update(self, serializer):
        project = EvalProject.objects.get(pk=self.kwargs['project_id'])
        if not _can_manage_project_review_rule(self.request.user, project):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                f'您无权修改该项目的评审规则（{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}/'
                f'{get_role_display_name(ROLE_LEVEL_DIRECTOR)}/'
                f'{get_role_display_name(ROLE_LEVEL_COUNSELOR)}仅可在授权范围内修改）'
            )
        instance = serializer.save()
        log_action(
            user=self.request.user,
            action='review_rule_update',
            module=OperationLog.MODULE_EVAL,
            level=OperationLog.LEVEL_WARNING,
            target_type='eval_project',
            target_id=instance.project_id,
            target_repr=f'项目#{instance.project_id}评审规则',
            extra={
                'role_level': self.request.user.current_role.level if self.request.user.current_role else -1,
                'review_scope_mode': instance.review_scope_mode,
                'cross_class_shuffle_enabled': instance.cross_class_shuffle_enabled,
                'allowed_assistant_count_per_submission': instance.allowed_assistant_count_per_submission,
                'counselor_participation_mode': instance.counselor_participation_mode,
                'overall_score_diff_threshold': str(instance.overall_score_diff_threshold) if instance.overall_score_diff_threshold is not None else None,
                'module_diff_thresholds': instance.module_diff_thresholds or {},
            },
            is_audit_event=True,
            request=self.request,
        )


class ProjectImportConfigView(APIView):
    """
    GET/PATCH /api/v1/projects/<project_id>/import-config/
    项目统一导入配置。
    """
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _sanitize_import_config(raw_config):
        """
        规范化导入配置。
        新版导入为每生一行、列头动态识别，列号配置已废弃；
        仅保留 student_field（学号还是用户名匹配）和 comment（导入备注）两个有效字段。
        """
        config = raw_config or {}
        if not isinstance(config, dict):
            raise ValidationError({'import_config': 'import_config 必须为对象'})

        student_field = str(config.get('student_field', 'student_no')).strip()
        if student_field not in {'student_no', 'username'}:
            raise ValidationError({'student_field': '仅支持 student_no 或 username'})

        return {
            'student_field': student_field,
            'comment': str(config.get('comment', '批量导入')).strip() or '批量导入',
        }

    def get(self, request, project_id):
        try:
            project = EvalProject.objects.get(pk=project_id)
        except EvalProject.DoesNotExist:
            return Response({'detail': '项目不存在'}, status=status.HTTP_404_NOT_FOUND)
        if not _can_manage_project_review_rule(request.user, project):
            raise PermissionDenied('您无权查看该项目导入配置')
        current_cfg = self._sanitize_import_config(project.import_config or {})

        # 构建可统一导入的指标嵌套树：递归遍历任意深度，
        # 保留包含 score_source='import' 后代的完整分支路径。
        all_indicators = list(
            EvalIndicator.objects.filter(project=project).order_by('order', 'id')
        )
        children_map = {}
        roots = []
        for ind in all_indicators:
            if ind.parent_id is None:
                roots.append(ind)
            else:
                children_map.setdefault(ind.parent_id, []).append(ind)

        def _build_import_tree(node):
            """递归构建嵌套树，只保留自身或后代包含 import 的分支。"""
            child_nodes = []
            for child in children_map.get(node.id, []):
                sub = _build_import_tree(child)
                if sub is not None:
                    child_nodes.append(sub)
            is_import = node.score_source == 'import'
            if not is_import and not child_nodes:
                return None
            return {
                'id': node.id,
                'name': node.name,
                'max_score': str(node.max_score) if node.max_score is not None else None,
                'is_import': is_import,
                'children': child_nodes,
            }

        importable_indicators = []
        for root in roots:
            tree = _build_import_tree(root)
            if tree is not None:
                tree['category'] = root.category
                importable_indicators.append(tree)

        return Response({
            'project_id': project.id,
            'project_name': project.name,
            'import_config': current_cfg,
            'importable_indicators': importable_indicators,
        })

    def patch(self, request, project_id):
        try:
            project = EvalProject.objects.get(pk=project_id)
        except EvalProject.DoesNotExist:
            return Response({'detail': '项目不存在'}, status=status.HTTP_404_NOT_FOUND)
        if not _can_manage_project_review_rule(request.user, project):
            raise PermissionDenied('您无权修改该项目导入配置')

        payload = request.data.get('import_config', request.data)
        new_cfg = self._sanitize_import_config(payload)
        old_cfg = self._sanitize_import_config(project.import_config or {})
        project.import_config = new_cfg
        project.save(update_fields=['import_config', 'updated_at'])
        log_action(
            user=request.user,
            action='project_import_config_update',
            module=OperationLog.MODULE_EVAL,
            level=OperationLog.LEVEL_WARNING,
            target_type='eval_project',
            target_id=project.id,
            target_repr=project.name,
            extra={'old': old_cfg, 'new': new_cfg},
            is_audit_event=True,
            request=request,
        )
        return Response({'detail': '导入配置已更新', 'import_config': new_cfg}, status=status.HTTP_200_OK)


def _template_sections_from_request(data):
    sections = data.get('sections') or data.get('include_sections') or []
    if isinstance(sections, str):
        sections = [x.strip() for x in sections.split(',') if x.strip()]
    if not isinstance(sections, list):
        sections = []
    allowed = {'basic', 'indicator', 'weight', 'review'}
    normalized = []
    for s in sections:
        if s in allowed and s not in normalized:
            normalized.append(s)
    return normalized or ['basic', 'indicator', 'weight', 'review']


def _build_indicator_snapshot(project):
    indicators = list(
        EvalIndicator.objects.filter(project=project).order_by('order', 'id')
    )
    return [
        {
            'source_id': ind.id,
            'parent_source_id': ind.parent_id,
            'name': ind.name,
            'description': ind.description or '',
            'category': ind.category or '',
            'max_score': str(ind.max_score) if ind.max_score is not None else None,
            'weight': ind.weight,
            'agg_formula': ind.agg_formula,
            'score_source': ind.score_source,
            'grade_rules': ind.grade_rules or {},
            'is_record_only': ind.is_record_only,
            'require_process_record': ind.require_process_record,
            'record_only_requires_review': bool(getattr(ind, 'record_only_requires_review', False)),
            'order': ind.order,
        }
        for ind in indicators
    ]


def _build_template_payload(project, sections):
    payload = {}
    if 'basic' in sections:
        payload['basic'] = {
            'description': project.description,
            'status': project.status,
            'start_time': project.start_time.isoformat() if project.start_time else None,
            'end_time': project.end_time.isoformat() if project.end_time else None,
            'review_end_time': project.review_end_time.isoformat() if project.review_end_time else None,
            'allow_late_submit': bool(project.allow_late_submit),
            'late_submit_deadline': project.late_submit_deadline.isoformat() if project.late_submit_deadline else None,
            'import_config': project.import_config or {},
        }
    if 'indicator' in sections:
        payload['indicator'] = _build_indicator_snapshot(project)
    if 'weight' in sections:
        weight_rule, _ = ScoreWeightRule.objects.get_or_create(project=project)
        payload['weight'] = {
            'formula_type': weight_rule.formula_type,
            'formula_config': weight_rule.formula_config or {},
        }
    if 'review' in sections:
        review_rule, _ = ReviewRule.objects.get_or_create(project=project)
        payload['review'] = {
            'dual_review_enabled': review_rule.dual_review_enabled,
            'review_scope_mode': review_rule.review_scope_mode,
            'cross_class_shuffle_enabled': review_rule.cross_class_shuffle_enabled,
            'allowed_assistant_count_per_submission': review_rule.allowed_assistant_count_per_submission,
            'counselor_participation_mode': review_rule.counselor_participation_mode,
            'single_review_mode': review_rule.single_review_mode,
            'score_diff_threshold': str(review_rule.score_diff_threshold) if review_rule.score_diff_threshold is not None else None,
            'overall_score_diff_threshold': str(review_rule.overall_score_diff_threshold) if review_rule.overall_score_diff_threshold is not None else None,
            'module_diff_thresholds': review_rule.module_diff_thresholds or {},
            'final_score_rule': review_rule.final_score_rule,
            'allow_view_other_scores': review_rule.allow_view_other_scores,
            'require_arbitration_above_threshold': review_rule.require_arbitration_above_threshold,
        }
    return payload


def _parse_iso_dt(value):
    from django.utils.dateparse import parse_datetime
    if not value:
        return None
    dt = parse_datetime(value)
    return dt


def _project_has_submission_records(project):
    from submission.models import StudentSubmission
    return StudentSubmission.objects.filter(project=project).exists()


class ProjectConfigTemplateListAPIView(generics.ListAPIView):
    """GET /api/v1/project-config-templates/ 项目配置模板列表。"""
    serializer_class = EvalProjectConfigTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        from django.db.models import Q
        user = self.request.user
        return EvalProjectConfigTemplate.objects.filter(
            Q(created_by=user) | Q(visibility='global')
        ).select_related('created_by').order_by('-updated_at', '-id')


class ProjectConfigTemplateSaveAPIView(APIView):
    """POST /api/v1/projects/<project_id>/config-templates/save/ 保存项目配置模板。"""
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        if not user_is_admin(request.user):
            return Response({'detail': f'仅{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}可保存项目模板'}, status=status.HTTP_403_FORBIDDEN)
        try:
            project = EvalProject.objects.get(pk=project_id)
        except EvalProject.DoesNotExist:
            return Response({'detail': '项目不存在'}, status=status.HTTP_404_NOT_FOUND)
        name = (request.data.get('name') or '').strip()
        if not name:
            return Response({'detail': '模板名称不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        visibility = (request.data.get('visibility') or 'private').strip()
        if visibility not in {'private', 'global'}:
            return Response({'detail': 'visibility 仅支持 private/global'}, status=status.HTTP_400_BAD_REQUEST)
        sections = _template_sections_from_request(request.data)
        payload = _build_template_payload(project, sections)
        tpl = EvalProjectConfigTemplate.objects.create(
            name=name,
            visibility=visibility,
            created_by=request.user,
            include_sections=sections,
            payload=payload,
        )
        log_action(
            user=request.user,
            action='project_config_template_save',
            module=OperationLog.MODULE_EVAL,
            level=OperationLog.LEVEL_WARNING,
            target_type='eval_project_config_template',
            target_id=tpl.id,
            target_repr=tpl.name,
            extra={'project_id': project.id, 'sections': sections, 'visibility': visibility},
            is_audit_event=True,
            request=request,
        )
        return Response(EvalProjectConfigTemplateSerializer(tpl).data, status=status.HTTP_201_CREATED)


class ProjectConfigTemplateApplyAPIView(APIView):
    """POST /api/v1/projects/<project_id>/config-templates/<template_id>/apply/ 应用模板。"""
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id, template_id):
        if not user_is_admin(request.user):
            return Response({'detail': f'仅{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}可应用项目模板'}, status=status.HTTP_403_FORBIDDEN)
        try:
            project = EvalProject.objects.get(pk=project_id)
        except EvalProject.DoesNotExist:
            return Response({'detail': '项目不存在'}, status=status.HTTP_404_NOT_FOUND)
        try:
            tpl = EvalProjectConfigTemplate.objects.get(pk=template_id)
        except EvalProjectConfigTemplate.DoesNotExist:
            return Response({'detail': '模板不存在'}, status=status.HTTP_404_NOT_FOUND)
        if tpl.visibility == 'private' and tpl.created_by_id != request.user.id:
            return Response({'detail': '无权应用该私有模板'}, status=status.HTTP_403_FORBIDDEN)

        sections = _template_sections_from_request(request.data) if request.data else []
        if not sections:
            sections = list(tpl.include_sections or [])
        payload = tpl.payload or {}
        if _project_has_submission_records(project) and 'indicator' in sections:
            return Response({'detail': '项目已存在提交记录，禁止覆盖指标结构模板'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            if 'basic' in sections and isinstance(payload.get('basic'), dict):
                basic = payload.get('basic') or {}
                project.description = basic.get('description') or ''
                project.status = basic.get('status') or project.status
                project.start_time = _parse_iso_dt(basic.get('start_time'))
                project.end_time = _parse_iso_dt(basic.get('end_time'))
                project.review_end_time = _parse_iso_dt(basic.get('review_end_time'))
                project.allow_late_submit = bool(basic.get('allow_late_submit'))
                project.late_submit_deadline = _parse_iso_dt(basic.get('late_submit_deadline'))
                project.import_config = basic.get('import_config') or {}
                project.save()

            if 'indicator' in sections and isinstance(payload.get('indicator'), list):
                snapshots = payload.get('indicator') or []
                EvalIndicator.objects.filter(project=project).delete()
                id_map = {}
                for row in snapshots:
                    src_id = row.get('source_id')
                    is_record_only = bool(row.get('is_record_only', False))
                    require_process_record = bool(row.get('require_process_record', not is_record_only))
                    record_only_requires_review = bool(row.get('record_only_requires_review', False)) if is_record_only else False
                    ind = EvalIndicator.objects.create(
                        project=project,
                        parent=None,
                        name=row.get('name') or '未命名指标',
                        description=row.get('description') or '',
                        category=row.get('category') or '',
                        max_score=row.get('max_score'),
                        weight=row.get('weight') if row.get('weight') is not None else 1.0,
                        agg_formula=row.get('agg_formula') or 'sum',
                        score_source=row.get('score_source') or 'reviewer',
                        grade_rules=row.get('grade_rules') or {},
                        is_record_only=is_record_only,
                        require_process_record=require_process_record,
                        record_only_requires_review=record_only_requires_review,
                        order=row.get('order') if row.get('order') is not None else 0,
                    )
                    if src_id is not None:
                        id_map[src_id] = ind
                for row in snapshots:
                    src_id = row.get('source_id')
                    parent_src = row.get('parent_source_id')
                    if src_id is None or parent_src is None:
                        continue
                    cur = id_map.get(src_id)
                    parent = id_map.get(parent_src)
                    if cur and parent:
                        cur.parent = parent
                        cur.save(update_fields=['parent'])

            if 'weight' in sections and isinstance(payload.get('weight'), dict):
                weight_data = payload.get('weight') or {}
                wr, _ = ScoreWeightRule.objects.get_or_create(project=project)
                wr.formula_type = weight_data.get('formula_type') or 'weighted_sum'
                wr.formula_config = weight_data.get('formula_config') or {}
                wr.save()

            if 'review' in sections and isinstance(payload.get('review'), dict):
                review_data = payload.get('review') or {}
                rr, _ = ReviewRule.objects.get_or_create(project=project)
                rr.dual_review_enabled = bool(review_data.get('dual_review_enabled', rr.dual_review_enabled))
                rr.review_scope_mode = review_data.get('review_scope_mode') or rr.review_scope_mode
                rr.cross_class_shuffle_enabled = bool(review_data.get('cross_class_shuffle_enabled', rr.cross_class_shuffle_enabled))
                rr.allowed_assistant_count_per_submission = int(review_data.get('allowed_assistant_count_per_submission') or rr.allowed_assistant_count_per_submission or 2)
                rr.counselor_participation_mode = review_data.get('counselor_participation_mode') or rr.counselor_participation_mode
                rr.single_review_mode = review_data.get('single_review_mode') or rr.single_review_mode
                rr.score_diff_threshold = review_data.get('score_diff_threshold')
                rr.overall_score_diff_threshold = review_data.get('overall_score_diff_threshold')
                rr.module_diff_thresholds = review_data.get('module_diff_thresholds') or {}
                rr.final_score_rule = review_data.get('final_score_rule') or rr.final_score_rule
                rr.allow_view_other_scores = bool(review_data.get('allow_view_other_scores', rr.allow_view_other_scores))
                rr.require_arbitration_above_threshold = bool(review_data.get('require_arbitration_above_threshold', rr.require_arbitration_above_threshold))
                rr.save()

        log_action(
            user=request.user,
            action='project_config_template_apply',
            module=OperationLog.MODULE_EVAL,
            level=OperationLog.LEVEL_WARNING,
            target_type='eval_project',
            target_id=project.id,
            target_repr=project.name,
            extra={'template_id': tpl.id, 'sections': sections},
            is_audit_event=True,
            request=request,
        )
        return Response({'detail': '模板应用成功', 'project_id': project.id, 'template_id': tpl.id, 'sections': sections})
