"""
学生提交 API：列表、创建、详情、更新、正式提交。
"""
from decimal import Decimal, InvalidOperation
import os

from django.conf import settings
from django.db.models import Prefetch, Sum
from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.models import OperationLog
from audit.services import log_action
from .models import StudentSubmission, Evidence, SubmissionAnswer
from .serializers import (
    StudentSubmissionSerializer,
    StudentSubmissionListSerializer,
    StudentSubmissionCreateUpdateSerializer,
    EvidenceSerializer,
    SubmissionTaskSerializer,
    SubmissionQuestionSerializer,
)
from .display_state import derive_submission_display_state
from .permissions import IsSubmissionOwnerOrReviewer
from eval.utils import raw_max_score as _raw_max_score


def _submission_attachment_rules():
    """
    读取附件相关规则（支持通过 settings 覆盖）。
    """
    max_size_mb = int(getattr(settings, 'SUBMISSION_MAX_EVIDENCE_SIZE_MB', 20))
    max_per_indicator = int(getattr(settings, 'SUBMISSION_MAX_EVIDENCE_PER_INDICATOR', 10))
    require_per_indicator = bool(getattr(settings, 'SUBMISSION_REQUIRE_EVIDENCE_PER_INDICATOR', False))
    allowed_exts = getattr(
        settings,
        'SUBMISSION_ALLOWED_EVIDENCE_EXTENSIONS',
        [
            '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.txt', '.zip', '.rar', '.7z',
        ],
    )
    normalized_exts = {str(ext).strip().lower() for ext in allowed_exts if str(ext).strip()}
    return {
        'max_size_bytes': max(1, max_size_mb) * 1024 * 1024,
        'max_size_mb': max(1, max_size_mb),
        'max_per_indicator': max(1, max_per_indicator),
        'require_per_indicator': require_per_indicator,
        'allowed_exts': normalized_exts,
    }


def _validate_evidence_file(file_obj):
    """
    校验附件扩展名与大小，返回错误信息（通过时返回 None）。
    """
    rules = _submission_attachment_rules()
    ext = os.path.splitext(file_obj.name or '')[1].lower()
    if rules['allowed_exts'] and ext not in rules['allowed_exts']:
        return '文件类型不支持，请上传图片、PDF、Office 或压缩包'
    if file_obj.size and file_obj.size > rules['max_size_bytes']:
        return f'文件大小不能超过 {rules["max_size_mb"]}MB'
    return None


def _submission_access_context(project, user):
    """
    计算提交可达性上下文，用于任务中心与提交流程统一判定。
    优先级：① 项目自有时间窗口（无则回退测评周期时间窗口）
            ② 项目级允许迟交截止（必须在测评周期时间内，由 validate 保证）
            ③ 个人/班级精细化补交通道（LateSubmitChannel）——唯一可在周期结束后提交的方式

    注意：若测评周期已结束（status='closed' 或 end_time 已过），
    跳过 ① 和 ② 的正常通道检查，直接进入补交通道检查。
    """
    from django.db.models import Q
    from django.utils import timezone
    now = timezone.now()

    season = getattr(project, 'season', None)
    season_closed = (
        season is not None and (
            season.status == 'closed' or
            (season.status == 'ongoing' and season.end_time is not None and now > season.end_time)
        )
    )

    if not season_closed:
        # ① 正常提交时间窗口（优先用项目自身时间，无则回退到所属周期时间）
        if project.start_time and project.end_time:
            if project.start_time <= now <= project.end_time:
                normal_window_open = True
            else:
                normal_window_open = False
        else:
            if season and season.start_time and season.end_time:
                if season.start_time <= now <= season.end_time:
                    normal_window_open = True
                else:
                    normal_window_open = False
            else:
                normal_window_open = False

        # ② 项目级允许迟交截止（validate 已保证 ≤ season.end_time）
        if project.allow_late_submit and project.late_submit_deadline and now <= project.late_submit_deadline:
            late_window_open = True
        else:
            late_window_open = False
    else:
        normal_window_open = False
        late_window_open = False

    # ③ 针对个人/班级的精细化补交通道（唯一可在周期结束后使用的通道）
    from audit.models import LateSubmitChannel
    class_obj = getattr(user, 'class_obj', None)
    class_filter = (
        Q(scope_type=LateSubmitChannel.SCOPE_CLASS, target_class=class_obj)
        if class_obj else Q(pk__in=[])
    )
    channel_exists = LateSubmitChannel.objects.filter(
        is_active=True,
        planned_close_at__gte=now,
        actual_close_at__isnull=True,
    ).filter(
        Q(project__isnull=True) | Q(project=project)
    ).filter(
        Q(scope_type=LateSubmitChannel.SCOPE_USER, target_user=user) | class_filter
    ).exists()
    can_submit = normal_window_open or late_window_open or channel_exists
    return {
        'can_submit': can_submit,
        'normal_window_open': normal_window_open,
        'late_window_open': late_window_open,
        'channel_open': channel_exists,
        'season_closed': season_closed,
    }


def _can_submit_or_edit(project, user):
    """是否在允许提交/编辑时间内。"""
    return _submission_access_context(project, user)['can_submit']


def _build_submission_task_item(project, submission, access_ctx, arbitrated_submission_ids=None):
    """
    构造学生任务中心列表项。
    """
    season = getattr(project, 'season', None)
    if submission is not None:
        arbitrated_submission_ids = arbitrated_submission_ids or set()
        submission_status = submission.status
        if submission_status == 'draft' and access_ctx['can_submit']:
            recommended_action = 'continue'
            action_label = '继续填写'
        else:
            recommended_action = 'view'
            action_label = '查看记录'
        entry_state = submission_status
        is_arbitrated = submission.id in arbitrated_submission_ids
        final_score = float(submission.final_score) if submission.final_score is not None else None
        entry_label_map = {
            'draft': '草稿（待提交）',
            'submitted': '已提交（待推送/待审核）',
            'under_review': '审核中',
            'approved': '已通过',
            'rejected': '已驳回',
            'appealing': '申诉中',
        }
        display_status, display_tone = derive_submission_display_state(
            submission_status,
            is_arbitrated=is_arbitrated,
        )
        # 草稿状态且当前可提交时，展示为"待提交"更具指导性
        if submission_status == 'draft' and access_ctx['can_submit']:
            display_status = '待提交'
            display_tone = 'warning'
        entry_label = display_status
    else:
        submission_status = None
        final_score = None
        is_arbitrated = False
        if access_ctx['channel_open'] and not access_ctx['normal_window_open']:
            entry_state = 'late_open'
            entry_label = '补交通道开放中'
            display_status = entry_label
            display_tone = 'warning'
        elif access_ctx['late_window_open'] and not access_ctx['normal_window_open']:
            entry_state = 'late_open'
            entry_label = '迟交窗口开放中'
            display_status = entry_label
            display_tone = 'warning'
        else:
            entry_state = 'pending'
            entry_label = '待提交'
            display_status = entry_label
            display_tone = 'warning'
        recommended_action = 'start'
        action_label = '开始填写'

    return {
        'project_id': project.id,
        'project_name': project.name,
        'season_id': season.id if season else None,
        'season_name': season.name if season else '',
        'project_status': project.status,
        'start_time': project.start_time,
        'end_time': project.end_time,
        'allow_late_submit': project.allow_late_submit,
        'late_submit_deadline': project.late_submit_deadline,
        'submission_id': submission.id if submission else None,
        'submission_status': submission_status,
        'final_score': final_score,
        'is_arbitrated': is_arbitrated,
        'submitted_at': submission.submitted_at if submission else None,
        'can_submit': access_ctx['can_submit'],
        'entry_state': entry_state,
        'entry_label': entry_label,
        'display_status': display_status,
        'display_tone': display_tone,
        'recommended_action': recommended_action,
        'action_label': action_label,
    }


def _self_leaf_indicators(project):
    """
    获取项目下需要学生作答的叶子指标（score_source='self'），预加载 parent 及 grandparent。
    """
    from eval.models import EvalIndicator

    indicators = list(
        EvalIndicator.objects.filter(project=project)
        .select_related('parent__parent')
        .order_by('order', 'id')
    )
    children_map = {}
    for ind in indicators:
        if ind.parent_id is not None:
            children_map.setdefault(ind.parent_id, []).append(ind.id)
    return [ind for ind in indicators if ind.score_source == 'self' and ind.id not in children_map]


def _all_leaf_indicators(project):
    """
    获取项目下所有需要学生展示的叶子指标（含 self/import/reviewer，排除 children 汇总节点），
    预加载 parent 及 grandparent，用于题目化作答全量展示。
    """
    from eval.models import EvalIndicator

    indicators = list(
        EvalIndicator.objects.filter(project=project)
        .select_related('parent__parent')
        .order_by('order', 'id')
    )
    children_map = {}
    for ind in indicators:
        if ind.parent_id is not None:
            children_map.setdefault(ind.parent_id, []).append(ind.id)
    return [
        ind for ind in indicators
        if ind.score_source in ('self', 'import', 'reviewer') and ind.id not in children_map
    ]


def _sync_submission_self_score(submission):
    """
    将题目化作答回写到 submission.self_score，保持旧字段兼容。
    """
    answer_qs = SubmissionAnswer.objects.filter(submission=submission, self_score__isnull=False)
    score_map = {str(ans.indicator_id): float(ans.self_score) for ans in answer_qs}
    submission.self_score = score_map
    submission.save(update_fields=['self_score', 'updated_at'])


class SubmissionTaskListAPIView(APIView):
    """GET /api/v1/submission-tasks/ 学生进行中的测评任务列表。"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from eval.models import EvalProject
        from eval.serializers import _compute_effective_project_status
        from scoring.models import ArbitrationRecord

        user = request.user
        if not user.is_authenticated:
            return Response([], status=status.HTTP_200_OK)

        projects = list(
            EvalProject.objects.select_related('season').order_by('-season_id', 'id')
        )
        submissions = list(
            StudentSubmission.objects.filter(user=user).select_related('project')
        )
        submission_map = {s.project_id: s for s in submissions}
        submission_ids = [s.id for s in submissions]
        arbitrated_submission_ids = set(
            ArbitrationRecord.objects.filter(
                submission_id__in=submission_ids
            ).values_list('submission_id', flat=True).distinct()
        ) if submission_ids else set()

        items = []
        for project in projects:
            # 使用统一规则计算项目有效状态，保证与项目管理口径一致。
            project.status = _compute_effective_project_status(project)
            submission = submission_map.get(project.id)
            access_ctx = _submission_access_context(project, user)
            if submission is None and not access_ctx['can_submit']:
                continue
            items.append(_build_submission_task_item(project, submission, access_ctx, arbitrated_submission_ids))

        serializer = SubmissionTaskSerializer(items, many=True)
        return Response(serializer.data)


class SubmissionListCreateView(generics.ListCreateAPIView):
    """GET /api/v1/submissions/ 我的提交列表；POST 创建草稿。"""
    permission_classes = [IsAuthenticated]
    serializer_class = StudentSubmissionListSerializer

    def get_queryset(self):
        qs = StudentSubmission.objects.filter(user=self.request.user).select_related('project').order_by('-created_at')
        project = self.request.query_params.get('project')
        status_filter = self.request.query_params.get('status')
        if project:
            qs = qs.filter(project_id=project)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StudentSubmissionCreateUpdateSerializer
        return StudentSubmissionListSerializer

    def perform_create(self, serializer):
        from eval.models import EvalProject
        raw_project = serializer.validated_data.get('project')
        project = EvalProject.objects.select_related('season').get(pk=raw_project.pk)
        if StudentSubmission.objects.filter(project=project, user=self.request.user).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'detail': '该项目已有提交记录'})
        if not _can_submit_or_edit(project, self.request.user):
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'detail': '当前不在提交时间内'})
        instance = serializer.save(user=self.request.user, status='draft', project=project)
        log_action(
            user=self.request.user,
            action='submission_create',
            module=OperationLog.MODULE_SUBMISSION,
            level=OperationLog.LEVEL_NOTICE,
            target_type='submission',
            target_id=instance.id,
            target_repr=project.name,
            request=self.request,
        )


class SubmissionDetailView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/v1/submissions/<id>/ 详情与更新（自评、佐证）。"""
    permission_classes = [IsAuthenticated]
    serializer_class = StudentSubmissionSerializer

    def get_queryset(self):
        return StudentSubmission.objects.all().select_related('project', 'project__season', 'user').prefetch_related(
            Prefetch('evidences', queryset=Evidence.objects.filter(is_deleted=False).order_by('id')),
            'answers',
        )

    def get_serializer_class(self):
        if self.request.method in ('PATCH', 'PUT'):
            return StudentSubmissionCreateUpdateSerializer
        return StudentSubmissionSerializer

    def get_permissions(self):
        return [IsSubmissionOwnerOrReviewer()]

    def perform_update(self, serializer):
        obj = self.get_object()
        if obj.status != 'draft':
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'detail': '仅草稿可修改'})
        from eval.models import EvalProject
        project = EvalProject.objects.select_related('season').get(pk=obj.project_id)
        if not _can_submit_or_edit(project, self.request.user):
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'detail': '当前不在提交时间内'})
        instance = serializer.save()
        log_action(
            user=self.request.user,
            action='submission_update',
            module=OperationLog.MODULE_SUBMISSION,
            level=OperationLog.LEVEL_NOTICE,
            target_type='submission',
            target_id=instance.id,
            target_repr=project.name,
            request=self.request,
        )


class SubmissionSubmitView(APIView):
    """POST /api/v1/submissions/<id>/submit/ 正式提交。"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            submission = StudentSubmission.objects.get(pk=pk)
        except StudentSubmission.DoesNotExist:
            return Response({'detail': '提交不存在'}, status=status.HTTP_404_NOT_FOUND)
        if submission.user_id != request.user.id:
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        if submission.status != 'draft':
            return Response({'detail': '仅草稿可提交'}, status=status.HTTP_400_BAD_REQUEST)
        from eval.models import EvalProject
        project = EvalProject.objects.select_related('season').get(pk=submission.project_id)
        if not _can_submit_or_edit(project, request.user):
            return Response({'detail': '当前不在提交时间内'}, status=status.HTTP_400_BAD_REQUEST)

        # 提交前校验：所有自评叶子题至少完成“分数 + 过程记录”。
        required_indicators = _self_leaf_indicators(project)
        if required_indicators:
            answer_map = {
                ans.indicator_id: ans
                for ans in SubmissionAnswer.objects.filter(submission=submission, indicator_id__in=[i.id for i in required_indicators])
            }
            missing_names = []
            for ind in required_indicators:
                ans = answer_map.get(ind.id)
                if not ans or ans.self_score is None:
                    missing_names.append(ind.name)
                elif ind.require_process_record and not (ans.process_record or '').strip():
                    missing_names.append(ind.name)
            if missing_names:
                return Response(
                    {
                        'detail': '存在未完成模块，请补充分数与过程记录后再提交',
                        'missing_count': len(missing_names),
                        'missing_indicators': missing_names[:20],
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            rules = _submission_attachment_rules()
            if rules['require_per_indicator']:
                required_ids = [i.id for i in required_indicators]
                evidence_indicator_ids = set(
                    Evidence.objects.filter(
                        submission=submission,
                        is_deleted=False,
                        indicator_id__in=required_ids,
                    ).values_list('indicator_id', flat=True)
                )
                missing_evidence = [ind.name for ind in required_indicators if ind.id not in evidence_indicator_ids]
                if missing_evidence:
                    return Response(
                        {
                            'detail': '存在未上传佐证材料的模块，请补充后再提交',
                            'missing_evidence_count': len(missing_evidence),
                            'missing_evidence_indicators': missing_evidence[:20],
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        from django.db.models import Q
        from django.utils import timezone
        now = timezone.now()
        # 判断是否通过补交通道提交（正常提交窗口和迟交窗口均已关闭）
        season = project.season
        season_closed = (
            season is not None and (
                season.status == 'closed' or
                (season.status == 'ongoing' and season.end_time is not None and now > season.end_time)
            )
        )
        if season_closed:
            via_channel = True
        else:
            normal_window_open = False
            if project.start_time and project.end_time:
                normal_window_open = project.start_time <= now <= project.end_time
            elif season and season.start_time and season.end_time:
                normal_window_open = season.start_time <= now <= season.end_time
            late_window_open = (
                project.allow_late_submit
                and project.late_submit_deadline is not None
                and now <= project.late_submit_deadline
            )
            via_channel = not normal_window_open and not late_window_open
        submission.status = 'submitted'
        submission.submitted_at = now
        submission.via_late_channel = via_channel
        submission.save(update_fields=['status', 'submitted_at', 'via_late_channel'])
        if not via_channel:
            from scoring.assignment_services import auto_assign_submission
            auto_assign_submission(submission)
        log_action(
            user=request.user,
            action='submission_submit',
            module=OperationLog.MODULE_SUBMISSION,
            level=OperationLog.LEVEL_NOTICE,
            target_type='submission',
            target_id=submission.id,
            target_repr=project.name,
            request=request,
        )
        # 提交成功后自动关闭该用户名下针对本项目的活跃补交通道
        from audit.models import LateSubmitChannel
        LateSubmitChannel.objects.filter(
            is_active=True,
            actual_close_at__isnull=True,
            scope_type=LateSubmitChannel.SCOPE_USER,
            target_user=request.user,
        ).filter(
            Q(project__isnull=True) | Q(project=project)
        ).update(
            is_active=False,
            actual_close_at=now,
            close_reason=LateSubmitChannel.CLOSE_SUBMITTED,
        )
        from realtime.registry import broadcast
        broadcast({'type': 'data_changed', 'model': 'late_channel'})
        return Response(StudentSubmissionSerializer(submission).data)


class EvidenceUploadView(APIView):
    """POST /api/v1/submissions/<id>/evidences/ 上传佐证。"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk):
        try:
            submission = StudentSubmission.objects.get(pk=pk)
        except StudentSubmission.DoesNotExist:
            return Response({'detail': '提交不存在'}, status=status.HTTP_404_NOT_FOUND)
        if submission.user_id != request.user.id:
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        if submission.status != 'draft':
            return Response({'detail': '仅草稿可上传佐证'}, status=status.HTTP_400_BAD_REQUEST)
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'detail': '请选择文件'}, status=status.HTTP_400_BAD_REQUEST)
        file_error = _validate_evidence_file(file_obj)
        if file_error:
            return Response({'detail': file_error}, status=status.HTTP_400_BAD_REQUEST)
        indicator = None
        indicator_id = request.data.get('indicator_id')
        if indicator_id not in (None, ''):
            from eval.models import EvalIndicator
            try:
                indicator = EvalIndicator.objects.get(pk=int(indicator_id), project=submission.project, score_source='self')
            except (ValueError, EvalIndicator.DoesNotExist):
                return Response({'detail': '模块不存在或不属于当前项目'}, status=status.HTTP_400_BAD_REQUEST)
        rules = _submission_attachment_rules()
        exist_count = Evidence.objects.filter(
            submission=submission,
            indicator=indicator,
            is_deleted=False,
        ).count()
        if exist_count >= rules['max_per_indicator']:
            return Response(
                {'detail': f'单个模块最多上传 {rules["max_per_indicator"]} 份附件'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        evidence = Evidence.objects.create(
            submission=submission,
            indicator=indicator,
            file=file_obj,
            category=request.data.get('category', ''),
            name=request.data.get('name', file_obj.name),
        )
        log_action(
            user=request.user,
            action='evidence_upload',
            module=OperationLog.MODULE_SUBMISSION,
            level=OperationLog.LEVEL_NOTICE,
            target_type='evidence',
            target_id=evidence.id,
            target_repr=evidence.name,
            extra={'submission_id': submission.id, 'indicator_id': indicator.id if indicator else None},
            request=request,
        )
        return Response(EvidenceSerializer(evidence).data, status=status.HTTP_201_CREATED)


class EvidenceDeleteView(APIView):
    """DELETE /api/v1/submissions/<id>/evidences/<evidence_id>/ 软删除佐证。"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk, evidence_id):
        try:
            submission = StudentSubmission.objects.get(pk=pk)
        except StudentSubmission.DoesNotExist:
            return Response({'detail': '提交不存在'}, status=status.HTTP_404_NOT_FOUND)
        if submission.user_id != request.user.id:
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        if submission.status != 'draft':
            return Response({'detail': '仅草稿可删除佐证'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            evidence = Evidence.objects.get(pk=evidence_id, submission=submission, is_deleted=False)
        except Evidence.DoesNotExist:
            return Response({'detail': '附件不存在或已删除'}, status=status.HTTP_404_NOT_FOUND)
        evidence.is_deleted = True
        evidence.save(update_fields=['is_deleted'])
        log_action(
            user=request.user,
            action='evidence_delete',
            module=OperationLog.MODULE_SUBMISSION,
            level=OperationLog.LEVEL_NOTICE,
            target_type='evidence',
            target_id=evidence.id,
            target_repr=evidence.name or f'evidence#{evidence.id}',
            extra={'submission_id': submission.id, 'indicator_id': evidence.indicator_id},
            request=request,
        )
        return Response({'detail': '删除成功'})


class SubmissionQuestionListView(APIView):
    """GET /api/v1/submissions/<pk>/questions/ 获取题目化作答视图（含全类型指标）。"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            submission = StudentSubmission.objects.select_related('project', 'user').get(pk=pk)
        except StudentSubmission.DoesNotExist:
            return Response({'detail': '提交不存在'}, status=status.HTTP_404_NOT_FOUND)
        if submission.user_id != request.user.id:
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)

        indicators = _all_leaf_indicators(submission.project)
        indicator_ids = [i.id for i in indicators]

        # 自评作答
        answer_map = {
            ans.indicator_id: ans
            for ans in SubmissionAnswer.objects.filter(submission=submission, indicator_id__in=indicator_ids)
        }

        # 佐证材料计数
        from django.db.models import Count
        evidence_counts = {
            row['indicator_id']: row['count']
            for row in (
                Evidence.objects.filter(submission=submission, indicator_id__in=indicator_ids, is_deleted=False)
                .values('indicator_id')
                .annotate(count=Count('id'))
            )
        }

        # 统一导入成绩（import 类型）
        from scoring.models import ImportedScoreDetail
        imported_score_map = {
            row['indicator_id']: row['score']
            for row in ImportedScoreDetail.objects.filter(
                submission=submission, indicator_id__in=indicator_ids
            ).values('indicator_id', 'score')
        }

        # 评审打分成绩（reviewer 类型）：取最终仲裁分或最高轮次评分
        from scoring.models import ScoreRecord, ArbitrationRecord
        arbitration_map = {
            row['indicator_id']: row['score']
            for row in ArbitrationRecord.objects.filter(
                submission=submission, indicator_id__in=indicator_ids
            ).values('indicator_id', 'score')
        }
        review_score_raw = {}
        for row in (ScoreRecord.objects.filter(submission=submission, indicator_id__in=indicator_ids)
                    .values('indicator_id', 'score', 'round_type')
                    .order_by('indicator_id', '-round_type')):
            iid = row['indicator_id']
            if iid not in review_score_raw:
                review_score_raw[iid] = row['score']

        questions = []
        for ind in indicators:
            ans = answer_map.get(ind.id)
            parent = ind.parent if ind.parent_id else None
            grandparent = parent.parent if (parent and parent.parent_id) else None
            if grandparent:
                root = grandparent
                section_name = grandparent.name
                subsection_name = parent.name
            elif parent:
                root = parent
                section_name = parent.name
                subsection_name = ''
            else:
                root = None
                section_name = ''
                subsection_name = ''

            # 已导入/已评分成绩
            imported_score = None
            reviewer_score = None
            if ind.score_source == 'import':
                raw = imported_score_map.get(ind.id)
                imported_score = str(raw) if raw is not None else None
            elif ind.score_source == 'reviewer':
                arb_raw = arbitration_map.get(ind.id)
                raw = arb_raw if arb_raw is not None else review_score_raw.get(ind.id)
                reviewer_score = str(raw) if raw is not None else None

            questions.append({
                'indicator_id': ind.id,
                'indicator_name': ind.name,
                'score_source': ind.score_source,
                'section_name': section_name,
                'subsection_name': subsection_name,
                'max_score': _raw_max_score(ind),
                'order': ind.order,
                'self_score': ans.self_score if ans else None,
                'process_record': ans.process_record if ans else '',
                'is_completed': (ans.is_completed if ans else False) if ind.score_source == 'self' else (imported_score is not None or reviewer_score is not None),
                'evidence_count': evidence_counts.get(ind.id, 0),
                'require_process_record': ind.require_process_record,
                'parent_indicator_id': ind.parent_id,
                'parent_agg_formula': parent.agg_formula if parent else None,
                'parent_max_score': str(parent.max_score) if parent else None,
                'imported_score': imported_score,
                'reviewer_score': reviewer_score,
                '_root_order': root.order if root else 0,
                '_root_id': root.id if root else 0,
                '_sub_order': parent.order if grandparent else 0,
                '_sub_id': parent.id if grandparent else 0,
            })
        questions.sort(key=lambda q: (q['_root_order'], q['_root_id'], q['_sub_order'], q['_sub_id'], q['order'], q['indicator_id']))
        serializer = SubmissionQuestionSerializer(questions, many=True)
        return Response(serializer.data)


class SubmissionQuestionSaveView(APIView):
    """PATCH /api/v1/submissions/<pk>/questions/<indicator_id>/ 保存单题作答。"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk, indicator_id):
        try:
            submission = StudentSubmission.objects.select_related('project').get(pk=pk)
        except StudentSubmission.DoesNotExist:
            return Response({'detail': '提交不存在'}, status=status.HTTP_404_NOT_FOUND)
        if submission.user_id != request.user.id:
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        if submission.status != 'draft':
            return Response({'detail': '仅草稿可保存作答'}, status=status.HTTP_400_BAD_REQUEST)

        from eval.models import EvalIndicator
        try:
            indicator = EvalIndicator.objects.get(pk=indicator_id, project=submission.project, score_source='self')
        except EvalIndicator.DoesNotExist:
            return Response({'detail': '题目不存在或不可自评'}, status=status.HTTP_404_NOT_FOUND)

        raw_score = request.data.get('self_score')
        process_record = (request.data.get('process_record') or '').strip()
        score_val = None
        if raw_score not in (None, ''):
            try:
                score_val = Decimal(str(raw_score))
            except (InvalidOperation, ValueError):
                return Response({'detail': 'self_score 必须为合法数字'}, status=status.HTTP_400_BAD_REQUEST)
            if score_val < Decimal('0'):
                return Response({'detail': 'self_score 不能为负数'}, status=status.HTTP_400_BAD_REQUEST)
            raw_limit = _raw_max_score(indicator)
            if raw_limit is not None and score_val > raw_limit:
                return Response({'detail': f'self_score 不能超过该模块满分 {raw_limit}'}, status=status.HTTP_400_BAD_REQUEST)
            if indicator.parent_id:
                parent = indicator.parent
                if parent and parent.agg_formula == 'sum_capped' and parent.max_score is not None:
                    sibling_sum = SubmissionAnswer.objects.filter(
                        submission=submission,
                        indicator__parent=parent,
                        self_score__isnull=False,
                    ).exclude(indicator=indicator).aggregate(
                        total=Sum('self_score')
                    )['total'] or Decimal('0')
                    cap = Decimal(str(parent.max_score))
                    remaining = cap - sibling_sum
                    if score_val > remaining:
                        return Response(
                            {'detail': f'封顶求和限制：父项满分 {cap}，其他子项已用 {sibling_sum}，剩余可用 {remaining}'},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

        if indicator.require_process_record:
            completed = bool(score_val is not None and process_record)
        else:
            completed = score_val is not None
        answer, _ = SubmissionAnswer.objects.update_or_create(
            submission=submission,
            indicator=indicator,
            defaults={
                'self_score': score_val,
                'process_record': process_record,
                'is_completed': completed,
            },
        )
        _sync_submission_self_score(submission)
        return Response({
            'indicator_id': indicator.id,
            'self_score': answer.self_score,
            'process_record': answer.process_record,
            'is_completed': answer.is_completed,
        })
