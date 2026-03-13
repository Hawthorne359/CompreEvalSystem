"""
双评任务分配服务。
"""
import random
from collections import defaultdict

from django.db import transaction

from submission.models import StudentSubmission
from users.models import UserRole, Role
from users.role_resolver import ROLE_LEVEL_ASSISTANT
from .models import ReviewAssignment


def _find_counselor_owner(class_id):
    """
    查找该班级的主负责辅导员（取最早绑定的一位，保证可复现）。
    """
    ur = (
        UserRole.objects.select_related('user', 'role')
        .filter(scope_type='class', scope_id=class_id, role__level__gte=2)
        .order_by('created_at', 'id')
        .first()
    )
    return ur.user if ur else None


def _counselor_scope_class_ids(counselor_user_id):
    return list(
        UserRole.objects.filter(
            user_id=counselor_user_id,
            scope_type='class',
            scope_id__isnull=False,
            role__level__gte=2,
        ).values_list('scope_id', flat=True).distinct()
    )


def _assistant_users_for_classes(class_ids):
    assistant_role = Role.objects.filter(level=ROLE_LEVEL_ASSISTANT).order_by('id').first()
    if not assistant_role or not class_ids:
        return []
    assistant_user_ids = list(
        UserRole.objects.filter(
            role=assistant_role,
            scope_type='class',
            scope_id__in=class_ids,
        ).values_list('user_id', flat=True).distinct()
    )
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return list(User.objects.filter(id__in=assistant_user_ids, is_active=True).order_by('id'))


def _assistant_users_for_major(major_id):
    """按专业查询可用助理池。"""
    assistant_role = Role.objects.filter(level=ROLE_LEVEL_ASSISTANT).order_by('id').first()
    if not assistant_role or not major_id:
        return []
    from org.models import Class
    class_ids = list(
        Class.objects.filter(major_id=major_id).values_list('id', flat=True)
    )
    if not class_ids:
        return []
    return _assistant_users_for_classes(class_ids)


def _pick_assistants_for_submission(submission, candidates, count, shuffle_enabled):
    """
    为单个提交挑选助理（避免本人、自班优先回避）。
    """
    if not candidates:
        return []
    pool = [u for u in candidates if u.id != submission.user_id]
    if not pool:
        return []
    # 优先跨班：先筛掉同班助理；若不足再回退全池
    cross_class = [u for u in pool if u.class_obj_id != submission.user.class_obj_id]
    picked_pool = cross_class if len(cross_class) >= count else pool
    if shuffle_enabled:
        random.shuffle(picked_pool)
    return picked_pool[:count]


def _resolve_candidates_for_submission(submission, rule, counselor):
    """
    根据策略模式解析当前提交的助理候选池。
    """
    mode = rule.review_scope_mode or 'same_class'
    if mode == 'same_class':
        if not submission.user.class_obj_id:
            return []
        return _assistant_users_for_classes([submission.user.class_obj_id])
    if mode == 'same_major':
        major_id = submission.user.class_obj.major_id if submission.user and submission.user.class_obj else None
        return _assistant_users_for_major(major_id)
    # same_counselor_classes（默认）
    if not counselor:
        return []
    class_ids = _counselor_scope_class_ids(counselor.id)
    return _assistant_users_for_classes(class_ids)


def _create_assignment_for_submission(sub, project, rule, counselor, operator_user=None):
    """
    为单条提交创建 ReviewAssignment（根据 ReviewRule 判断双评/单评模式）。
    @returns {bool} 是否成功创建
    """
    if counselor is None:
        return False

    dual_enabled = bool(rule.dual_review_enabled)
    if dual_enabled:
        ReviewAssignment.objects.create(
            submission=sub,
            project=project,
            reviewer=counselor,
            role_type='counselor_dispatch',
            round_type=0,
            strategy_mode=rule.review_scope_mode,
            assignment_version=1,
            assigned_by=operator_user,
            status='assigned',
        )
        return True

    single_mode = rule.single_review_mode or 'assistant_single'
    if single_mode == 'counselor_single':
        ReviewAssignment.objects.create(
            submission=sub,
            project=project,
            reviewer=counselor,
            role_type='counselor',
            round_type=1,
            strategy_mode='counselor_single',
            assignment_version=1,
            assigned_by=operator_user,
            status='assigned',
        )
        return True

    ReviewAssignment.objects.create(
        submission=sub,
        project=project,
        reviewer=counselor,
        role_type='counselor_dispatch',
        round_type=0,
        strategy_mode='assistant_single',
        assignment_version=1,
        assigned_by=operator_user,
        status='assigned',
    )
    return True


def auto_assign_submission(submission):
    """
    学生提交后自动创建评审分配（幂等：已有分配则跳过）。
    已有分配时也会修正残留的 submitted 状态。
    @returns {dict} {'created': bool, 'reason': str}
    """
    if ReviewAssignment.objects.filter(submission=submission).exists():
        if submission.status == 'submitted':
            submission.status = 'under_review'
            submission.save(update_fields=['status'])
        return {'created': False, 'reason': 'already_assigned'}

    project = submission.project
    rule = getattr(project, 'review_rule', None)
    if rule is None:
        return {'created': False, 'reason': 'no_review_rule'}

    class_id = getattr(submission.user, 'class_obj_id', None)
    if not class_id:
        return {'created': False, 'reason': 'no_class'}

    counselor = _find_counselor_owner(class_id)
    if counselor is None:
        return {'created': False, 'reason': 'no_counselor'}

    ok = _create_assignment_for_submission(sub=submission, project=project,
                                           rule=rule, counselor=counselor)
    if ok and submission.status == 'submitted':
        submission.status = 'under_review'
        submission.save(update_fields=['status'])
    return {'created': ok, 'reason': 'ok' if ok else 'create_failed'}


@transaction.atomic
def generate_review_assignments_for_project(project, operator_user):
    """
    为项目补充生成评审任务（增量模式：跳过已有分配的提交）。
    返回统计信息。
    """
    rule = getattr(project, 'review_rule', None)
    if rule is None:
        return {'created': 0, 'skipped': 0, 'detail': '项目未配置评审规则'}

    submissions = list(
        StudentSubmission.objects.select_related('user', 'user__class_obj')
        .filter(project=project, status__in=['submitted', 'under_review'])
        .order_by('id')
    )
    if not submissions:
        return {'created': 0, 'skipped': 0, 'detail': '无待分配提交'}

    already_assigned_ids = set(
        ReviewAssignment.objects.filter(
            project=project,
            submission_id__in=[s.id for s in submissions],
        ).values_list('submission_id', flat=True).distinct()
    )

    created_count = 0
    skipped_count = 0

    for sub in submissions:
        if sub.id in already_assigned_ids:
            if sub.status == 'submitted':
                sub.status = 'under_review'
                sub.save(update_fields=['status'])
            continue

        counselor = _find_counselor_owner(sub.user.class_obj_id) if sub.user.class_obj_id else None
        ok = _create_assignment_for_submission(
            sub=sub, project=project, rule=rule,
            counselor=counselor, operator_user=operator_user,
        )
        if ok:
            created_count += 1
            if sub.status == 'submitted':
                sub.status = 'under_review'
                sub.save(update_fields=['status'])
        else:
            skipped_count += 1

    return {
        'created': created_count,
        'skipped': skipped_count,
        'already_assigned': len(already_assigned_ids),
        'detail': 'ok',
        'dual_review_enabled': bool(rule.dual_review_enabled),
        'review_scope_mode': rule.review_scope_mode,
        'cross_class_shuffle_enabled': bool(rule.cross_class_shuffle_enabled),
        'allowed_assistant_count_per_submission': int(rule.allowed_assistant_count_per_submission or 2),
        'counselor_participation_mode': rule.counselor_participation_mode,
        'single_review_mode': rule.single_review_mode or 'assistant_single',
    }

