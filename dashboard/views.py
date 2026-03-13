"""
工作台（Dashboard）API：按当前角色 level 返回差异化聚合数据。

角色等级对应：
  LV0=学生  LV1=学生助理  LV2=评审老师（辅导员）  LV3=院系主任  LV5=超级管理员
"""
from django.db.models import Count, Avg, Q, Subquery, OuterRef
from django.utils import timezone
from datetime import timedelta
from math import ceil
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import get_user_level
from users.role_resolver import (
    ROLE_LEVEL_ASSISTANT,
    ROLE_LEVEL_COUNSELOR,
    ROLE_LEVEL_DIRECTOR,
    ROLE_LEVEL_SUPERADMIN,
)
from submission.display_state import derive_submission_display_state


def _safe_int(value, default):
    try:
        return int(value)
    except Exception:
        return default


def _effective_metric_ids(sub_rows, arbitrated_ids):
    """
    统一工作台有效完成/有效成绩判定。
    - 有效完成：status=approved，或（已仲裁且 final_score 非空）
    - 有效成绩：status=approved 且 final_score 非空，或（已仲裁且 final_score 非空）
    @param sub_rows {list[dict]}
    @param arbitrated_ids {set[int]}
    @returns {tuple[set[int], set[int]]} (effective_completed_ids, effective_scored_ids)
    """
    completed_ids = set()
    scored_ids = set()
    for row in sub_rows:
        sid = row['id']
        status = row.get('status')
        final_score = row.get('final_score')
        if status == 'approved':
            completed_ids.add(sid)
            if final_score is not None:
                scored_ids.add(sid)
        if sid in arbitrated_ids and final_score is not None:
            completed_ids.add(sid)
            scored_ids.add(sid)
    return completed_ids, scored_ids


def _build_assignment_progress_maps(active_assignments):
    """
    生成评审任务完成判定与逻辑轮次映射。
    - 完成判定：同 submission+reviewer 存在 assignment 通道评分即视为已评分
    - 逻辑轮次：按 submission+reviewer 首次评分时间排序，映射 1评/2评...
    @param active_assignments {list}
    @returns {tuple[set, dict]}
    """
    if not active_assignments:
        return set(), {}

    from scoring.models import ScoreRecord

    submission_ids = {a.submission_id for a in active_assignments}
    scored_pairs = set(
        ScoreRecord.objects.filter(
            submission_id__in=submission_ids,
            score_channel='assignment',
        ).exclude(
            round_type=3,
        ).values_list('submission_id', 'reviewer_id').distinct()
    )

    first_rows = list(
        ScoreRecord.objects.filter(
            submission_id__in=submission_ids,
            score_channel='assignment',
        ).exclude(
            round_type=3,
        ).order_by('submission_id', 'created_at', 'id')
        .values_list('submission_id', 'reviewer_id')
    )
    logical_round_map = {}
    submission_order = {}
    for submission_id, reviewer_id in first_rows:
        key = (submission_id, reviewer_id)
        if key in logical_round_map:
            continue
        current_order = submission_order.get(submission_id, 0) + 1
        submission_order[submission_id] = current_order
        logical_round_map[key] = current_order
    return scored_pairs, logical_round_map


class DashboardAPIView(APIView):
    """
    GET /api/v1/dashboard/
    根据当前角色等级返回工作台所需数据，单接口多态，避免前端多次请求。
    超管/院系主任支持 query params 下钻：
      ?department_id=X          → 返回该院系下各专业统计
      ?department_id=X&major_id=Y → 返回该专业下各班级统计
      ?major_id=Y               → 院系主任下钻到班级
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        level = get_user_level(request.user)
        if level == 0:
            return Response(self._student_data(request.user))
        if level == 1:
            return Response(self._assistant_data(request.user))
        if level == 2:
            return Response(self._counselor_data(request.user, request))
        if level == 3:
            return Response(self._director_data(request.user, request))
        if level >= 5:
            return Response(self._superadmin_data(request))
        return Response({'role_level': level, 'message': '暂无工作台数据'})

    # ------------------------------------------------------------------
    # LV0 学生
    # ------------------------------------------------------------------
    def _student_data(self, user):
        from submission.models import StudentSubmission
        from eval.models import EvalProject
        from scoring.models import ArbitrationRecord

        ongoing_projects = EvalProject.objects.filter(status='ongoing')
        submitted_ids = set(
            StudentSubmission.objects.filter(user=user)
            .exclude(status='draft')
            .values_list('project_id', flat=True)
        )
        total_task_count = ongoing_projects.count()
        submitted_count = len(submitted_ids)
        pending_count = ongoing_projects.exclude(id__in=submitted_ids).count()

        subs = StudentSubmission.objects.filter(user=user).exclude(status='draft')
        status_counts = {s: 0 for s in ('submitted', 'under_review', 'approved', 'rejected', 'appealing')}
        for sub in subs.values('status').annotate(n=Count('id')):
            status_counts[sub['status']] = sub['n']

        recent_submissions = list(
            subs.select_related('project').order_by('-updated_at')[:5].values(
                'id', 'project__name', 'status', 'final_score', 'submitted_at', 'updated_at'
            )
        )
        recent_submission_ids = [item['id'] for item in recent_submissions]
        arbitrated_submission_ids = set(
            ArbitrationRecord.objects.filter(
                submission_id__in=recent_submission_ids
            ).values_list('submission_id', flat=True).distinct()
        ) if recent_submission_ids else set()

        for s in recent_submissions:
            s['project_name'] = s.pop('project__name')
            s['final_score'] = float(s['final_score']) if s['final_score'] is not None else None
            s['is_arbitrated'] = s['id'] in arbitrated_submission_ids
            display_status, display_tone = derive_submission_display_state(
                s.get('status'),
                is_arbitrated=s['is_arbitrated'],
            )
            s['display_status'] = display_status
            s['display_tone'] = display_tone

        now = timezone.now()
        upcoming_deadlines = []
        for p in ongoing_projects.filter(end_time__isnull=False, end_time__gte=now).order_by('end_time')[:3]:
            days_left = (p.end_time - now).days
            upcoming_deadlines.append({
                'project_name': p.name,
                'end_time': p.end_time,
                'days_left': days_left,
            })

        return {
            'role_level': 0,
            'pending_submission_count': pending_count,
            'total_task_count': total_task_count,
            'submitted_count': submitted_count,
            'status_counts': status_counts,
            'recent_submissions': recent_submissions,
            'upcoming_deadlines': upcoming_deadlines,
        }

    # ------------------------------------------------------------------
    # LV1 学生助理
    # ------------------------------------------------------------------
    def _assistant_data(self, user):
        from users.models import UserRole
        from scoring.models import ReviewAssignment

        scope_class_ids = list(
            UserRole.objects.filter(
                user=user,
                role__level=ROLE_LEVEL_ASSISTANT,
                scope_type='class',
            ).values_list('scope_id', flat=True)
        )

        assignments = list(
            ReviewAssignment.objects.filter(
                reviewer=user,
                status='assigned',
            ).select_related('submission', 'submission__project', 'submission__user')
            .order_by('-created_at')
        )
        active_assignments = assignments

        assigned_submission_ids = {a.submission_id for a in active_assignments}
        total_tasks = len(assigned_submission_ids)

        completed_pairs, _ = _build_assignment_progress_maps(active_assignments)
        completed_tasks = len({
            a.submission_id for a in active_assignments
            if (a.submission_id, a.reviewer_id) in completed_pairs
        })

        completion_rate = round(completed_tasks / total_tasks * 100, 1) if total_tasks else 0.0

        recent_tasks = []
        for a in active_assignments[:5]:
            student = a.submission.user
            recent_tasks.append({
                'id': a.submission_id,
                'project_name': a.project.name,
                'student_name': student.name or student.username,
                'status': a.submission.status,
                'updated_at': a.submission.updated_at,
                'already_scored': (a.submission_id, a.reviewer_id) in completed_pairs,
            })

        return {
            'role_level': 1,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': total_tasks - completed_tasks,
            'completion_rate': completion_rate,
            'responsible_class_count': len(scope_class_ids),
            'recent_tasks': recent_tasks,
        }

    # ------------------------------------------------------------------
    # LV2 评审老师（辅导员）
    # ------------------------------------------------------------------
    def _counselor_data(self, user, request):
        from submission.models import StudentSubmission
        from appeal.models import Appeal
        from users.models import UserRole
        from scoring.models import ReviewAssignment, ArbitrationRecord
        from org.models import Class as OrgClass

        scope_class_ids = list(
            UserRole.objects.filter(user=user, scope_type='class')
            .values_list('scope_id', flat=True)
        )

        pending_review = 0
        pending_appeal = 0
        completion_rate = 0.0
        avg_score = None
        review_rate = 0.0
        recent_submissions = []
        recent_appeals = []
        class_completion_stats = []
        avg_score_by_class = []
        grading_progress = {
            'total_assignments': 0,
            'completed': 0,
            'pending': 0,
            'valid_final_scores': 0,
            'arbitration_needed': 0,
        }
        round_stats = {'round_1_completed': 0, 'round_2_completed': 0}
        assignment_summary = {
            'total_assigned': 0,
            'assistant_assigned': 0,
            'counselor_assigned': 0,
            'strategy_modes': [],
        }

        if scope_class_ids:
            class_subs = StudentSubmission.objects.filter(
                user__class_obj_id__in=scope_class_ids
            )
            class_sub_rows = list(
                class_subs.values(
                    'id',
                    'status',
                    'final_score',
                    'user__class_obj_id',
                    'user__class_obj__name',
                )
            )
            class_sub_ids = [row['id'] for row in class_sub_rows]
            arbitrated_ids = set(
                ArbitrationRecord.objects.filter(submission_id__in=class_sub_ids)
                .values_list('submission_id', flat=True)
                .distinct()
            ) if class_sub_ids else set()
            effective_completed_ids, effective_scored_ids = _effective_metric_ids(class_sub_rows, arbitrated_ids)
            total = class_subs.count()
            approved = len(effective_completed_ids)
            pending_review = class_subs.filter(
                status__in=['submitted', 'under_review']
            ).exclude(via_late_channel=True, status='submitted').count()
            completion_rate = round(approved / total * 100, 1) if total else 0.0
            scored_values = [
                float(row['final_score']) for row in class_sub_rows
                if row['id'] in effective_scored_ids and row.get('final_score') is not None
            ]
            avg_score = round(sum(scored_values) / len(scored_values), 2) if scored_values else None

            pending_appeal = Appeal.objects.filter(
                status='pending',
                submission__user__class_obj_id__in=scope_class_ids,
            ).count()

            recent_submissions = list(
                class_subs.filter(
                    status__in=['submitted', 'under_review']
                ).select_related('project', 'user').order_by('-updated_at')[:5].values(
                    'id', 'project_id', 'project__name', 'user__name', 'user__username',
                    'user__student_no', 'status', 'submitted_at'
                )
            )
            for s in recent_submissions:
                s['project_name'] = s.pop('project__name')
                s['student_name'] = s.pop('user__name') or s.pop('user__username')
                if 'user__username' in s:
                    del s['user__username']
                s['student_no'] = s.pop('user__student_no', '')

            recent_appeals = list(
                Appeal.objects.filter(
                    status='pending',
                    submission__user__class_obj_id__in=scope_class_ids,
                ).select_related('submission__user', 'submission__project')
                .order_by('-created_at')[:5].values(
                    'id', 'submission__id', 'submission__project__name',
                    'submission__user__name', 'submission__user__username',
                    'reason', 'created_at'
                )
            )
            for a in recent_appeals:
                a['submission_id'] = a.pop('submission__id')
                a['project_name'] = a.pop('submission__project__name')
                a['student_name'] = (
                    a.pop('submission__user__name')
                    or a.pop('submission__user__username')
                )
                if 'submission__user__username' in a:
                    del a['submission__user__username']

            class_metrics = {}
            for row in class_sub_rows:
                cid = row['user__class_obj_id']
                c_name = row['user__class_obj__name'] or f'班级#{cid}'
                if cid not in class_metrics:
                    class_metrics[cid] = {
                        'class_name': c_name,
                        'total': 0,
                        'submitted': 0,
                        'approved': 0,
                        'scores': [],
                    }
                item = class_metrics[cid]
                item['total'] += 1
                if row.get('status') != 'draft':
                    item['submitted'] += 1
                if row['id'] in effective_completed_ids:
                    item['approved'] += 1
                if row['id'] in effective_scored_ids and row.get('final_score') is not None:
                    item['scores'].append(float(row['final_score']))
            for cid, row in class_metrics.items():
                c_name = row['class_name']
                c_total = row['total']
                c_approved = row['approved']
                c_rate = round(c_approved / c_total * 100, 1) if c_total else 0.0
                c_avg = round(sum(row['scores']) / len(row['scores']), 2) if row['scores'] else None
                class_completion_stats.append({
                    'class_id': cid,
                    'class_name': c_name,
                    'total': c_total,
                    'submitted': row['submitted'],
                    'approved': c_approved,
                    'completion_rate': c_rate,
                })
                avg_score_by_class.append({
                    'class_name': c_name,
                    'avg_score': c_avg,
                    'count': c_approved,
                })

            assign_qs = list(ReviewAssignment.objects.filter(
                submission__user__class_obj_id__in=scope_class_ids,
                status='assigned',
            ).select_related('project'))
            active_assignments = assign_qs
            assignment_summary = {
                'total_assigned': len(active_assignments),
                'assistant_assigned': sum(1 for a in active_assignments if a.role_type == 'assistant'),
                'counselor_assigned': sum(1 for a in active_assignments if a.role_type == 'counselor'),
                'strategy_modes': sorted(list({a.strategy_mode for a in active_assignments if a.strategy_mode})),
            }

            active_sub_ids = {a.submission_id for a in active_assignments}
            scored_pairs, logical_round_map = _build_assignment_progress_maps(active_assignments)
            arb_completed_sub_ids = set(
                ArbitrationRecord.objects.filter(
                    submission_id__in=active_sub_ids
                ).values_list('submission_id', flat=True).distinct()
            )
            completed_count = 0
            r1_done = 0
            r2_done = 0
            for a in active_assignments:
                if (a.submission_id, a.reviewer_id) in scored_pairs or a.submission_id in arb_completed_sub_ids:
                    completed_count += 1
                    logical_round = logical_round_map.get((a.submission_id, a.reviewer_id))
                    if logical_round == 1:
                        r1_done += 1
                    elif logical_round == 2:
                        r2_done += 1

            valid_final = len(effective_scored_ids)

            review_rate = round(completed_count / len(active_assignments) * 100, 1) if active_assignments else 0.0
            arb_needed = class_subs.filter(
                status='under_review'
            ).exclude(
                id__in=ArbitrationRecord.objects.values_list('submission_id', flat=True)
            ).count()
            arb_needed = min(arb_needed, pending_review)

            grading_progress = {
                'total_assignments': len(active_assignments),
                'completed': completed_count,
                'pending': len(active_assignments) - completed_count,
                'valid_final_scores': valid_final,
                'arbitration_needed': arb_needed,
            }
            round_stats = {
                'round_1_completed': r1_done,
                'round_2_completed': r2_done,
            }

        pending_dispatch_count = 0
        if scope_class_ids:
            pending_dispatch_count = ReviewAssignment.objects.filter(
                reviewer=user,
                role_type='counselor_dispatch',
                status='assigned',
            ).exclude(
                submission__status='approved',
            ).exclude(
                submission_id__in=ArbitrationRecord.objects.values_list('submission_id', flat=True),
            ).count()

        from django.db.models import Exists, OuterRef
        from users.models import UserRole as _DashUR
        from users.role_resolver import ROLE_LEVEL_ASSISTANT as _LV1
        assistant_submissions_pending = 0
        if scope_class_ids:
            assistant_submissions_pending = StudentSubmission.objects.filter(
                user__class_obj_id__in=scope_class_ids,
                status__in=['submitted', 'under_review'],
            ).exclude(
                id__in=ArbitrationRecord.objects.values_list('submission_id', flat=True),
            ).annotate(
                _is_asst=Exists(
                    _DashUR.objects.filter(
                        user_id=OuterRef('user_id'),
                        role__level=_LV1,
                    )
                )
            ).filter(_is_asst=True).count()

        return {
            'role_level': 2,
            'responsible_class_count': len(scope_class_ids),
            'pending_review_count': pending_review,
            'pending_dispatch_count': pending_dispatch_count,
            'pending_appeal_count': pending_appeal,
            'assistant_submissions_pending': assistant_submissions_pending,
            'completion_rate': completion_rate,
            'avg_score': avg_score,
            'review_rate': review_rate,
            'class_completion_stats': class_completion_stats,
            'avg_score_by_class': avg_score_by_class,
            'grading_progress': grading_progress,
            'round_stats': round_stats,
            'recent_submissions': recent_submissions,
            'recent_appeals': recent_appeals,
            'assignment_summary': assignment_summary,
        }

    # ------------------------------------------------------------------
    # LV3 院系主任
    # ------------------------------------------------------------------
    def _director_data(self, user, request):
        from submission.models import StudentSubmission
        from appeal.models import Appeal
        from scoring.models import ReviewAssignment, ArbitrationRecord
        dept = user.department
        major_id = request.query_params.get('major_id')

        subs_qs = StudentSubmission.objects.all()
        if dept:
            subs_qs = subs_qs.filter(user__department=dept)
        sub_rows = list(
            subs_qs.values(
                'id',
                'status',
                'final_score',
                'user__class_obj__major__id',
                'user__class_obj__major__name',
                'user__class_obj__id',
                'user__class_obj__name',
            )
        )
        sub_ids = [row['id'] for row in sub_rows]
        arbitrated_ids = set(
            ArbitrationRecord.objects.filter(submission_id__in=sub_ids)
            .values_list('submission_id', flat=True)
            .distinct()
        ) if sub_ids else set()
        effective_completed_ids, effective_scored_ids = _effective_metric_ids(sub_rows, arbitrated_ids)

        total = subs_qs.count()
        approved = len(effective_completed_ids)
        completion_rate = round(approved / total * 100, 1) if total else 0.0

        pending_review_count = subs_qs.filter(
            status__in=['submitted', 'under_review']
        ).exclude(via_late_channel=True, status='submitted').count()

        scored_values = [
            float(row['final_score']) for row in sub_rows
            if row['id'] in effective_scored_ids and row.get('final_score') is not None
        ]
        avg_score = round(sum(scored_values) / len(scored_values), 2) if scored_values else None
        valid_final_scores = len(effective_scored_ids)

        major_metrics = {}
        for row in sub_rows:
            mid = row['user__class_obj__major__id']
            major_name = row['user__class_obj__major__name'] or '未分专业'
            if mid not in major_metrics:
                major_metrics[mid] = {
                    'major_name': major_name,
                    'total': 0,
                    'approved': 0,
                    'scores': [],
                }
            item = major_metrics[mid]
            item['total'] += 1
            if row['id'] in effective_completed_ids:
                item['approved'] += 1
            if row['id'] in effective_scored_ids and row.get('final_score') is not None:
                item['scores'].append(float(row['final_score']))

        major_stats = []
        for mid, m in major_metrics.items():
            m_name = m['major_name']
            m_total = m['total']
            m_approved = m['approved']
            m_rate = round(m_approved / m_total * 100, 1) if m_total else 0.0
            m_avg = round(sum(m['scores']) / len(m['scores']), 2) if m['scores'] else None
            major_stats.append({
                'major_id': mid,
                'major_name': m_name,
                'avg_score': m_avg,
                'count': len(m['scores']),
                'total': m_total,
                'approved': m_approved,
                'completion_rate': m_rate,
            })
        major_stats.sort(key=lambda x: (x['avg_score'] is None, -(x['avg_score'] or 0)))
        major_stats = major_stats[:10]

        appeal_filter = Q(status='pending')
        if dept:
            appeal_filter &= Q(submission__user__department=dept)
        pending_appeal_count = Appeal.objects.filter(appeal_filter).count()

        total_with_appeal = (
            Appeal.objects.filter(submission__user__department=dept).count()
            if dept else Appeal.objects.count()
        )
        appeal_rate = round(total_with_appeal / total * 100, 2) if total else 0.0

        recent_appeals_qs = Appeal.objects.filter(status='pending')
        if dept:
            recent_appeals_qs = recent_appeals_qs.filter(submission__user__department=dept)
        recent_appeals = list(
            recent_appeals_qs.select_related('submission__user', 'submission__project')
            .order_by('-created_at')[:5].values(
                'id', 'submission__id', 'submission__project__name',
                'submission__user__name', 'submission__user__username',
                'reason', 'created_at'
            )
        )
        for a in recent_appeals:
            a['submission_id'] = a.pop('submission__id')
            a['project_name'] = a.pop('submission__project__name')
            a['student_name'] = (
                a.pop('submission__user__name')
                or a.pop('submission__user__username')
            )
            if 'submission__user__username' in a:
                del a['submission__user__username']

        class_completion_stats = []
        class_metrics = {}
        for row in sub_rows:
            cid = row['user__class_obj__id']
            c_name = row['user__class_obj__name'] or '未分班'
            if cid not in class_metrics:
                class_metrics[cid] = {'class_name': c_name, 'total': 0, 'approved': 0}
            item = class_metrics[cid]
            item['total'] += 1
            if row['id'] in effective_completed_ids:
                item['approved'] += 1
        for cid, c in class_metrics.items():
            c_name = c['class_name']
            c_total = c['total']
            c_approved = c['approved']
            c_rate = round(c_approved / c_total * 100, 1) if c_total else 0.0
            class_completion_stats.append({
                'class_name': c_name,
                'total': c_total,
                'approved': c_approved,
                'completion_rate': c_rate,
            })

        # --- 评阅进度统计 ---
        assign_filter = Q()
        if dept:
            assign_filter = Q(submission__user__department=dept)
        active_assignments = list(
            ReviewAssignment.objects.filter(assign_filter, status='assigned').select_related('project')
        )

        active_sub_ids = {a.submission_id for a in active_assignments}
        scored_pairs, logical_round_map = _build_assignment_progress_maps(active_assignments)
        arb_completed_sub_ids = set(
            ArbitrationRecord.objects.filter(
                submission_id__in=active_sub_ids
            ).values_list('submission_id', flat=True).distinct()
        ) if active_sub_ids else set()

        completed_count = 0
        r1_done = 0
        r2_done = 0
        for a in active_assignments:
            if (a.submission_id, a.reviewer_id) in scored_pairs or a.submission_id in arb_completed_sub_ids:
                completed_count += 1
                logical_round = logical_round_map.get((a.submission_id, a.reviewer_id))
                if logical_round == 1:
                    r1_done += 1
                elif logical_round == 2:
                    r2_done += 1

        review_rate = round(completed_count / len(active_assignments) * 100, 1) if active_assignments else 0.0

        arb_needed = subs_qs.filter(status='under_review').exclude(
            id__in=ArbitrationRecord.objects.values_list('submission_id', flat=True)
        ).count()
        arb_needed = min(arb_needed, pending_review_count)

        grading_progress = {
            'total_assignments': len(active_assignments),
            'completed': completed_count,
            'pending': len(active_assignments) - completed_count,
            'valid_final_scores': valid_final_scores,
            'arbitration_needed': arb_needed,
        }
        round_stats = {
            'round_1_completed': r1_done,
            'round_2_completed': r2_done,
        }

        # --- 下钻：某专业的各班级详情 ---
        drill_data = None
        if major_id:
            drill_subs = subs_qs.filter(user__class_obj__major_id=major_id)
            drill_rows = list(drill_subs.values('id', 'status', 'final_score', 'user__class_obj__id', 'user__class_obj__name'))
            drill_ids = [row['id'] for row in drill_rows]
            drill_arb_ids = set(
                ArbitrationRecord.objects.filter(submission_id__in=drill_ids).values_list('submission_id', flat=True).distinct()
            ) if drill_ids else set()
            drill_completed_ids, drill_scored_ids = _effective_metric_ids(drill_rows, drill_arb_ids)
            drill_map = {}
            for row in drill_rows:
                cid = row['user__class_obj__id']
                c_name = row['user__class_obj__name'] or '未分班'
                if cid not in drill_map:
                    drill_map[cid] = {'class_id': cid, 'class_name': c_name, 'total': 0, 'approved': 0, 'scores': []}
                item = drill_map[cid]
                item['total'] += 1
                if row['id'] in drill_completed_ids:
                    item['approved'] += 1
                if row['id'] in drill_scored_ids and row.get('final_score') is not None:
                    item['scores'].append(float(row['final_score']))
            drill_data = []
            for _, item in drill_map.items():
                item['completion_rate'] = round(item['approved'] / item['total'] * 100, 1) if item['total'] else 0.0
                item['avg_score'] = round(sum(item['scores']) / len(item['scores']), 2) if item['scores'] else None
                del item['scores']
                drill_data.append(item)
            drill_data.sort(key=lambda x: (x['class_name'] or ''))

        return {
            'role_level': 3,
            'department_name': dept.name if dept else '全校',
            'total_submissions': total,
            'total_approved': approved,
            'completion_rate': completion_rate,
            'pending_review_count': pending_review_count,
            'pending_appeal_count': pending_appeal_count,
            'appeal_rate': appeal_rate,
            'avg_score': avg_score,
            'valid_final_scores': valid_final_scores,
            'review_rate': review_rate,
            'major_stats': major_stats,
            'class_completion_stats': class_completion_stats,
            'grading_progress': grading_progress,
            'round_stats': round_stats,
            'recent_appeals': recent_appeals,
            'drill_data': drill_data,
        }

    # ------------------------------------------------------------------
    # LV5 超级管理员
    # ------------------------------------------------------------------
    def _superadmin_data(self, request):
        from django.contrib.auth import get_user_model
        from eval.models import EvalProject, EvalSeason
        from audit.models import OperationLog
        from submission.models import StudentSubmission
        from appeal.models import Appeal
        from scoring.models import ReviewAssignment, ArbitrationRecord
        from org.models import Department

        User = get_user_model()

        department_id = request.query_params.get('department_id')
        major_id = request.query_params.get('major_id')

        # --- 用户统计（保留） ---
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()

        cutoff = timezone.now() - timedelta(days=30)
        recent_login_users = (
            OperationLog.objects.filter(
                action='login', created_at__gte=cutoff
            ).values('user_id').distinct().count()
        )

        total_projects = EvalProject.objects.count()
        ongoing_seasons = EvalSeason.objects.filter(status='ongoing').count()

        season_status_counts = {}
        for row in EvalSeason.objects.values('status').annotate(n=Count('id')):
            season_status_counts[row['status']] = row['n']

        project_status_counts = {}
        for row in EvalProject.objects.values('status').annotate(n=Count('id')):
            project_status_counts[row['status']] = row['n']

        recent_logs = list(
            OperationLog.objects.filter(
                level__in=['WARNING', 'CRITICAL']
            ).order_by('-created_at')[:8].values(
                'id', 'username_snapshot', 'action', 'module', 'level',
                'target_repr', 'created_at', 'is_abnormal'
            )
        )

        # --- 全校测评业务数据 ---
        all_subs = StudentSubmission.objects.all()
        all_sub_rows = list(all_subs.values('id', 'status', 'final_score', 'user__department_id', 'user__department__name', 'user__class_obj__major__id', 'user__class_obj__major__name', 'user__class_obj__id', 'user__class_obj__name'))
        all_sub_ids = [row['id'] for row in all_sub_rows]
        all_arb_ids = set(
            ArbitrationRecord.objects.filter(submission_id__in=all_sub_ids)
            .values_list('submission_id', flat=True)
            .distinct()
        ) if all_sub_ids else set()
        effective_completed_ids, effective_scored_ids = _effective_metric_ids(all_sub_rows, all_arb_ids)

        total_submissions = all_subs.count()
        total_approved = len(effective_completed_ids)
        completion_rate = round(total_approved / total_submissions * 100, 1) if total_submissions else 0.0

        pending_review_count = all_subs.filter(
            status__in=['submitted', 'under_review']
        ).exclude(via_late_channel=True, status='submitted').count()

        pending_appeal_count = Appeal.objects.filter(status='pending').count()

        valid_final_scores = len(effective_scored_ids)
        scored_values = [
            float(row['final_score']) for row in all_sub_rows
            if row['id'] in effective_scored_ids and row.get('final_score') is not None
        ]
        avg_score = round(sum(scored_values) / len(scored_values), 2) if scored_values else None

        active_assignments = list(
            ReviewAssignment.objects.filter(status='assigned').select_related('project')
        )

        active_sub_ids = {a.submission_id for a in active_assignments}
        scored_pairs, _ = _build_assignment_progress_maps(active_assignments)
        arb_completed_sub_ids = set(
            ArbitrationRecord.objects.filter(
                submission_id__in=active_sub_ids
            ).values_list('submission_id', flat=True).distinct()
        ) if active_sub_ids else set()

        review_completed = sum(
            1 for a in active_assignments
            if (a.submission_id, a.reviewer_id) in scored_pairs or a.submission_id in arb_completed_sub_ids
        )
        review_rate = round(review_completed / len(active_assignments) * 100, 1) if active_assignments else 0.0

        # --- 各院系统计（单查询聚合替代循环 count，消除 N+1） ---
        dept_sub_agg = (
            all_subs.filter(user__department__isnull=False)
            .values('user__department_id', 'user__department__name')
            .annotate(
                total=Count('id'),
                pending_review=Count('id', filter=Q(status__in=['submitted', 'under_review']) & ~Q(via_late_channel=True, status='submitted')),
            )
        )
        dept_appeal_agg = dict(
            Appeal.objects.filter(status='pending', submission__user__department__isnull=False)
            .values_list('submission__user__department_id')
            .annotate(n=Count('id'))
            .values_list('submission__user__department_id', 'n')
        )
        dept_student_agg = dict(
            User.objects.filter(is_active=True, department__isnull=False)
            .values('department_id')
            .annotate(n=Count('id'))
            .values_list('department_id', 'n')
        )

        department_stats = []
        dept_scores_map = {}
        dept_completed_map = {}
        for row in all_sub_rows:
            did = row['user__department_id']
            if did is None:
                continue
            dept_completed_map.setdefault(did, 0)
            dept_scores_map.setdefault(did, [])
            if row['id'] in effective_completed_ids:
                dept_completed_map[did] += 1
            if row['id'] in effective_scored_ids and row.get('final_score') is not None:
                dept_scores_map[did].append(float(row['final_score']))
        for row in dept_sub_agg:
            d_total = row['total']
            if d_total == 0:
                continue
            did = row['user__department_id']
            d_approved = dept_completed_map.get(did, 0)
            d_rate = round(d_approved / d_total * 100, 1) if d_total else 0.0
            d_scores = dept_scores_map.get(did, [])
            d_avg = round(sum(d_scores) / len(d_scores), 2) if d_scores else None
            department_stats.append({
                'department_id': did,
                'department_name': row['user__department__name'],
                'total_students': dept_student_agg.get(did, 0),
                'total_submissions': d_total,
                'approved': d_approved,
                'completion_rate': d_rate,
                'avg_score': d_avg,
                'pending_review': row['pending_review'],
                'pending_appeal': dept_appeal_agg.get(did, 0),
            })

        # --- 各院系评审进度 ---
        sub_to_dept = dict(
            all_subs.filter(user__department__isnull=False)
            .values_list('id', 'user__department_id')
        )
        dept_review_stats = []
        for ds in department_stats:
            did = ds['department_id']
            dept_assigns = [
                a for a in active_assignments
                if sub_to_dept.get(a.submission_id) == did
            ]
            d_total_assigns = len(dept_assigns)
            d_completed = sum(
                1 for a in dept_assigns
                if (a.submission_id, a.reviewer_id) in scored_pairs or a.submission_id in arb_completed_sub_ids
            )
            d_review_rate = round(d_completed / d_total_assigns * 100, 1) if d_total_assigns else 0.0
            dept_review_stats.append({
                'department_id': did,
                'department_name': ds['department_name'],
                'total_assignments': d_total_assigns,
                'completed': d_completed,
                'review_rate': d_review_rate,
            })

        # --- 下钻逻辑 ---
        drill_type = None
        drill_data = None

        if department_id and major_id:
            drill_type = 'major'
            drill_subs = all_subs.filter(user__class_obj__major_id=major_id)
            drill_rows = list(drill_subs.values('id', 'status', 'final_score', 'user__class_obj__id', 'user__class_obj__name'))
            drill_ids = [row['id'] for row in drill_rows]
            drill_arb_ids = set(
                ArbitrationRecord.objects.filter(submission_id__in=drill_ids).values_list('submission_id', flat=True).distinct()
            ) if drill_ids else set()
            drill_completed_ids, drill_scored_ids = _effective_metric_ids(drill_rows, drill_arb_ids)
            drill_map = {}
            for row in drill_rows:
                cid = row['user__class_obj__id']
                cname = row['user__class_obj__name'] or '未分班'
                if cid not in drill_map:
                    drill_map[cid] = {'class_id': cid, 'class_name': cname, 'total': 0, 'approved': 0, 'scores': []}
                item = drill_map[cid]
                item['total'] += 1
                if row['id'] in drill_completed_ids:
                    item['approved'] += 1
                if row['id'] in drill_scored_ids and row.get('final_score') is not None:
                    item['scores'].append(float(row['final_score']))
            drill_data = []
            for _, item in drill_map.items():
                item['completion_rate'] = round(item['approved'] / item['total'] * 100, 1) if item['total'] else 0.0
                item['avg_score'] = round(sum(item['scores']) / len(item['scores']), 2) if item['scores'] else None
                del item['scores']
                drill_data.append(item)
            drill_data.sort(key=lambda x: (x['class_name'] or ''))

        elif department_id:
            drill_type = 'department'
            drill_subs = all_subs.filter(user__department_id=department_id)
            drill_rows = list(drill_subs.values('id', 'status', 'final_score', 'user__class_obj__major__id', 'user__class_obj__major__name'))
            drill_ids = [row['id'] for row in drill_rows]
            drill_arb_ids = set(
                ArbitrationRecord.objects.filter(submission_id__in=drill_ids).values_list('submission_id', flat=True).distinct()
            ) if drill_ids else set()
            drill_completed_ids, drill_scored_ids = _effective_metric_ids(drill_rows, drill_arb_ids)
            drill_map = {}
            for row in drill_rows:
                mid = row['user__class_obj__major__id']
                mname = row['user__class_obj__major__name'] or '未分专业'
                if mid not in drill_map:
                    drill_map[mid] = {'major_id': mid, 'major_name': mname, 'total': 0, 'approved': 0, 'scores': []}
                item = drill_map[mid]
                item['total'] += 1
                if row['id'] in drill_completed_ids:
                    item['approved'] += 1
                if row['id'] in drill_scored_ids and row.get('final_score') is not None:
                    item['scores'].append(float(row['final_score']))
            drill_data = []
            for _, item in drill_map.items():
                item['completion_rate'] = round(item['approved'] / item['total'] * 100, 1) if item['total'] else 0.0
                item['avg_score'] = round(sum(item['scores']) / len(item['scores']), 2) if item['scores'] else None
                del item['scores']
                drill_data.append(item)
            drill_data.sort(key=lambda x: (x['major_name'] or ''))

        return {
            'role_level': 5,
            # 用户统计
            'total_users': total_users,
            'active_users': active_users,
            'recent_login_users_30d': recent_login_users,
            # 项目周期
            'total_projects': total_projects,
            'ongoing_seasons': ongoing_seasons,
            'season_status_counts': season_status_counts,
            'project_status_counts': project_status_counts,
            # 全校测评数据
            'total_submissions': total_submissions,
            'total_approved': total_approved,
            'completion_rate': completion_rate,
            'pending_review_count': pending_review_count,
            'pending_appeal_count': pending_appeal_count,
            'valid_final_scores': valid_final_scores,
            'avg_score': avg_score,
            'review_rate': review_rate,
            # 院系统计
            'department_stats': department_stats,
            'dept_review_stats': dept_review_stats,
            # 下钻
            'drill_type': drill_type,
            'drill_data': drill_data,
            # 操作日志
            'recent_logs': recent_logs,
        }


class MissingSubmissionListAPIView(APIView):
    """
    GET /api/v1/dashboard/missing-list/
    独立的缺交名单接口，支持按角色权限筛选、分页、模糊搜索。

    @queryParam type       {string}  必填：unfilled（未填写，无记录）| unsubmitted（未提交，有草稿）
    @queryParam project_id {int}     可选：项目ID，默认取所有进行中项目
    @queryParam department {int}     可选：院系ID（仅超管可用）
    @queryParam major      {int}     可选：专业ID
    @queryParam class_obj  {int}     可选：班级ID
    @queryParam search     {string}  可选：模糊搜索（匹配姓名/学号）
    @queryParam page       {int}     页码，默认1
    @queryParam page_size  {int}     每页条数，默认20，最大100
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.contrib.auth import get_user_model
        from eval.models import EvalProject
        from submission.models import StudentSubmission
        from users.models import UserRole

        User = get_user_model()
        level = get_user_level(request.user)
        if level < ROLE_LEVEL_COUNSELOR:
            return Response({'detail': '权限不足'}, status=403)

        list_type = request.query_params.get('type', 'unfilled')
        if list_type not in ('unfilled', 'unsubmitted'):
            return Response({'detail': 'type 参数必须为 unfilled 或 unsubmitted'}, status=400)

        page = max(_safe_int(request.query_params.get('page'), 1), 1)
        page_size = min(max(_safe_int(request.query_params.get('page_size'), 20), 1), 100)

        project_id = request.query_params.get('project_id')
        if project_id:
            projects = list(
                EvalProject.objects.filter(id=project_id).values('id', 'name', 'end_time')
            )
        else:
            projects = list(
                EvalProject.objects.filter(status='ongoing').values('id', 'name', 'end_time')
            )
        project_ids = [p['id'] for p in projects]

        scope_qs = User.objects.filter(
            is_active=True,
            student_no__isnull=False,
        ).exclude(student_no='')

        if level >= ROLE_LEVEL_SUPERADMIN:
            dept_filter = request.query_params.get('department')
            if dept_filter:
                scope_qs = scope_qs.filter(department_id=dept_filter)
        elif level >= ROLE_LEVEL_DIRECTOR:
            dept = request.user.department
            if dept:
                scope_qs = scope_qs.filter(department=dept)
            else:
                scope_qs = scope_qs.none()
        elif level >= ROLE_LEVEL_COUNSELOR:
            scope_class_ids = list(
                UserRole.objects.filter(user=request.user, scope_type='class')
                .values_list('scope_id', flat=True)
            )
            if scope_class_ids:
                scope_qs = scope_qs.filter(class_obj_id__in=scope_class_ids)
            else:
                scope_qs = scope_qs.none()

        major_filter = request.query_params.get('major')
        if major_filter:
            scope_qs = scope_qs.filter(class_obj__major_id=major_filter)

        class_filter = request.query_params.get('class_obj')
        if class_filter:
            scope_qs = scope_qs.filter(class_obj_id=class_filter)

        search_kw = (request.query_params.get('search') or '').strip()
        if search_kw:
            scope_qs = scope_qs.filter(
                Q(name__icontains=search_kw) | Q(student_no__icontains=search_kw)
            )

        if not project_ids:
            return Response({
                'summary': {
                    'total_scope_students': scope_qs.count(),
                    'ongoing_project_count': 0,
                    'unfilled_count': 0,
                    'unsubmitted_count': 0,
                },
                'items': [],
                'page': 1,
                'page_size': page_size,
                'total': 0,
                'total_pages': 1,
            })

        has_submission_user_ids = (
            StudentSubmission.objects
            .filter(project_id__in=project_ids)
            .values_list('user_id', flat=True)
            .distinct()
        )
        draft_user_ids = (
            StudentSubmission.objects
            .filter(project_id__in=project_ids, status='draft')
            .values_list('user_id', flat=True)
            .distinct()
        )

        total_scope = scope_qs.count()
        unfilled_qs = scope_qs.exclude(id__in=Subquery(has_submission_user_ids.values('user_id')))
        unsubmitted_qs = scope_qs.filter(id__in=Subquery(draft_user_ids.values('user_id')))
        unfilled_count = unfilled_qs.count()
        unsubmitted_count = unsubmitted_qs.count()

        if list_type == 'unfilled':
            target_qs = unfilled_qs
        else:
            target_qs = unsubmitted_qs

        target_qs = target_qs.order_by('student_no', 'id')
        total = unfilled_count if list_type == 'unfilled' else unsubmitted_count
        total_pages = max(1, ceil(total / page_size))
        if page > total_pages:
            page = total_pages
        offset = (page - 1) * page_size

        rows = list(
            target_qs[offset:offset + page_size].values(
                'id', 'student_no', 'name', 'username',
                'class_obj__name', 'class_obj__major__name',
                'department__name',
            )
        )

        project_map = {p['id']: p for p in projects}

        if list_type == 'unsubmitted':
            user_ids_in_page = [r['id'] for r in rows]
            draft_subs = list(
                StudentSubmission.objects.filter(
                    user_id__in=user_ids_in_page,
                    project_id__in=project_ids,
                    status='draft',
                ).values('id', 'user_id', 'project_id', 'updated_at')
            )
            draft_map = {}
            for d in draft_subs:
                draft_map.setdefault(d['user_id'], []).append(d)
        else:
            draft_map = {}

        items = []
        for r in rows:
            uid = r['id']
            base = {
                'student_name': r.get('name') or r.get('username') or '—',
                'student_no': r.get('student_no') or '',
                'class_name': r.get('class_obj__name') or '—',
                'major_name': r.get('class_obj__major__name') or '—',
                'department_name': r.get('department__name') or '—',
            }
            if list_type == 'unfilled':
                for p in projects:
                    items.append({
                        **base,
                        'project_name': p.get('name') or '—',
                        'end_time': p.get('end_time'),
                        'submission_id': None,
                        'updated_at': None,
                    })
            else:
                user_drafts = draft_map.get(uid, [])
                for d in user_drafts:
                    pinfo = project_map.get(d['project_id']) or {}
                    items.append({
                        **base,
                        'project_name': pinfo.get('name') or '—',
                        'end_time': pinfo.get('end_time'),
                        'submission_id': d['id'],
                        'updated_at': d['updated_at'],
                    })

        return Response({
            'summary': {
                'total_scope_students': total_scope,
                'ongoing_project_count': len(projects),
                'unfilled_count': unfilled_count,
                'unsubmitted_count': unsubmitted_count,
            },
            'items': items,
            'page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': total_pages,
        })
