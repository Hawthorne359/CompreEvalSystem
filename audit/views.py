"""
审计与补交通道 API。
"""
import csv
from datetime import datetime, timedelta

from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.role_resolver import (
    ROLE_LEVEL_COUNSELOR,
    ROLE_LEVEL_DIRECTOR,
    ROLE_LEVEL_SUPERADMIN,
    get_role_display_name,
)

from users.permissions import user_is_admin, user_is_super_admin
from .models import (
    OperationLog,
    LateSubmitRequest,
    LateSubmitRequestAttachment,
    LateSubmitChannel,
    ImportPermissionRequest,
)
from .serializers import (
    OperationLogSerializer,
    OperationLogDetailSerializer,
    LateSubmitRequestSerializer,
    LateSubmitChannelSerializer,
    LatePendingSubmissionSerializer,
    ImportPermissionRequestSerializer,
)
from .services import log_action, log_action_with_attachment


def _apply_date_range(qs, params, dt_field='created_at'):
    """
    对 queryset 应用日期范围过滤。使用 __gte/__lt 代替 __date__gte/__date__lte，
    避免 MySQL CONVERT_TZ() 在时区表未填充时返回 NULL 的问题。
    """
    tz = timezone.get_current_timezone()
    date_from = params.get('date_from')
    if date_from:
        dt = datetime.strptime(date_from, '%Y-%m-%d')
        dt_aware = timezone.make_aware(dt, tz)
        qs = qs.filter(**{f'{dt_field}__gte': dt_aware})
    date_to = params.get('date_to')
    if date_to:
        dt = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
        dt_aware = timezone.make_aware(dt, tz)
        qs = qs.filter(**{f'{dt_field}__lt': dt_aware})
    return qs


def _build_keyword_q(keyword):
    """
    构建模糊搜索 Q 对象：同时搜索 action 英文代码、中文标签、
    module 英文/中文、target_repr、username_snapshot 等多个字段。
    中文关键词会反查 ACTION_LABELS / MODULE_LABELS 映射表，
    找到匹配的英文代码后一并加入 OR 查询。
    """
    from .serializers import ACTION_LABELS, MODULE_LABELS
    kw = keyword.strip()
    q = Q(action__icontains=kw) | Q(target_repr__icontains=kw) | Q(username_snapshot__icontains=kw)

    matched_actions = [code for code, label in ACTION_LABELS.items() if kw in label]
    if matched_actions:
        q |= Q(action__in=matched_actions)

    matched_modules = [code for code, label in MODULE_LABELS.items() if kw in label]
    if matched_modules:
        q |= Q(module__in=matched_modules)
    else:
        q |= Q(module__icontains=kw)

    return q


def _user_max_role_level(user):
    from django.db.models import Max
    max_level = user.user_roles.aggregate(max_level=Max('role__level')).get('max_level')
    return max_level if max_level is not None else -1


def _resolve_import_scope_snapshot(user, max_level):
    """记录申请时的权限范围快照，便于审计。"""
    scope = {'max_level': max_level}
    if max_level >= ROLE_LEVEL_DIRECTOR:
        scope['department_id'] = user.department_id
    if max_level >= ROLE_LEVEL_COUNSELOR:
        class_ids = list(
            user.user_roles.filter(scope_type='class', scope_id__isnull=False).values_list('scope_id', flat=True)
        )
        scope['class_ids'] = class_ids
    return scope


def _can_handle_import_request(handler, req):
    """仅直系上级可审批：评审->主任，主任->超管。"""
    current_level = handler.current_role.level if handler.current_role else -1
    if req.requester_level == ROLE_LEVEL_COUNSELOR:
        return (
            current_level == ROLE_LEVEL_DIRECTOR
            and handler.department_id
            and handler.department_id == req.requester.department_id
        )
    if req.requester_level == ROLE_LEVEL_DIRECTOR:
        return current_level >= ROLE_LEVEL_SUPERADMIN
    return False


class OperationLogPagination(PageNumberPagination):
    """操作日志分页器：支持通过 page_size 指定每页条数。"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class OperationLogListAPIView(generics.ListAPIView):
    """
    GET /api/v1/audit/logs/  超级管理员自己的操作日志列表（仅超级管理员可访问）。

    全量日志（含其他用户）请通过 Django admin 后台查看。

    支持的查询参数：
        - ``is_abnormal`` : 1 / 0
        - ``is_audit_event`` : 1 / 0
        - ``level``   : INFO / NOTICE / WARNING / CRITICAL
        - ``module``  : auth / users / org / eval / submission / scoring / appeal / report / system
        - ``action``  : 操作码（模糊匹配）
        - ``date_from``: YYYY-MM-DD
        - ``date_to``  : YYYY-MM-DD
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OperationLogSerializer
    pagination_class = OperationLogPagination
    queryset = OperationLog.objects.all().prefetch_related('attachments').order_by('-created_at')

    def get_queryset(self):
        if not user_is_super_admin(self.request.user):
            return OperationLog.objects.none()
        # 超管前端页面只返回该超管账号自己的操作记录
        qs = super().get_queryset().filter(user=self.request.user)
        p = self.request.query_params

        is_abnormal = p.get('is_abnormal')
        if is_abnormal == '1':
            qs = qs.filter(is_abnormal=True)
        elif is_abnormal == '0':
            qs = qs.filter(is_abnormal=False)

        is_audit = p.get('is_audit_event')
        if is_audit == '1':
            qs = qs.filter(is_audit_event=True)
        elif is_audit == '0':
            qs = qs.filter(is_audit_event=False)

        level = p.get('level')
        if level:
            qs = qs.filter(level=level)

        module = p.get('module')
        if module:
            qs = qs.filter(module=module)

        action = p.get('action')
        if action:
            qs = qs.filter(_build_keyword_q(action))

        qs = _apply_date_range(qs, p)

        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx


class OperationLogDetailAPIView(generics.RetrieveAPIView):
    """GET /api/v1/audit/logs/<pk>/ 超级管理员自己的操作日志详情。"""
    permission_classes = [IsAuthenticated]
    serializer_class = OperationLogDetailSerializer
    queryset = OperationLog.objects.all().prefetch_related('attachments')

    def get(self, request, *args, **kwargs):
        if not user_is_super_admin(request.user):
            return Response({'detail': '无权限查看操作日志'}, status=status.HTTP_403_FORBIDDEN)
        # 只允许查看自己的日志
        obj = self.get_object()
        if obj.user_id != request.user.pk:
            return Response({'detail': '无权限查看此日志'}, status=status.HTTP_403_FORBIDDEN)
        return super().get(request, *args, **kwargs)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx


class MyOperationLogListAPIView(generics.ListAPIView):
    """
    GET /api/v1/audit/my-logs/  当前登录用户自己的操作日志（所有角色均可访问）。

    每个用户只能看到自己账号的操作记录。
    若需查看其他用户的记录，请联系工程师通过 Django admin 后台查询。

    支持的查询参数：
        - ``level``    : INFO / NOTICE / WARNING / CRITICAL
        - ``module``   : auth / users / org / eval / submission / scoring / appeal / report / system
        - ``date_from``: YYYY-MM-DD
        - ``date_to``  : YYYY-MM-DD
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OperationLogSerializer
    pagination_class = OperationLogPagination

    def get_queryset(self):
        qs = OperationLog.objects.filter(
            user=self.request.user
        ).prefetch_related('attachments').order_by('-created_at')

        p = self.request.query_params

        level = p.get('level')
        if level:
            qs = qs.filter(level=level)

        module = p.get('module')
        if module:
            qs = qs.filter(module=module)

        qs = _apply_date_range(qs, p)

        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx


class MyOperationLogDetailAPIView(generics.RetrieveAPIView):
    """GET /api/v1/audit/my-logs/<pk>/ 当前用户自己的操作日志详情。"""
    permission_classes = [IsAuthenticated]
    serializer_class = OperationLogDetailSerializer

    def get_queryset(self):
        # 只能查看属于自己的日志
        return OperationLog.objects.filter(
            user=self.request.user
        ).prefetch_related('attachments')

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx


class OperationLogExportAPIView(APIView):
    """
    GET /api/v1/audit/logs/export/  导出操作日志为 CSV（仅管理员）。

    接受与列表接口相同的查询参数。最多导出最近 10000 条。
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not user_is_super_admin(request.user):
            return Response({'detail': '无权限导出日志'}, status=status.HTTP_403_FORBIDDEN)

        # 复用列表视图的过滤逻辑
        list_view = OperationLogListAPIView()
        list_view.request = request
        list_view.kwargs = {}
        list_view.format_kwarg = None
        qs = list_view.get_queryset()[:10000]

        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = (
            f'attachment; filename="operation_log_{timezone.now():%Y%m%d_%H%M%S}.csv"'
        )

        writer = csv.writer(response)
        writer.writerow([
            'ID', '时间', '等级', '模块', '操作码', '操作者', '角色',
            '内网IP', '外网IP', '目标类型', '目标ID', '目标描述', '理由', '异常', '审计事件',
        ])
        from .serializers import ACTION_LABELS, LEVEL_LABELS, MODULE_LABELS
        for log in qs:
            writer.writerow([
                log.id,
                log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                LEVEL_LABELS.get(log.level, log.level),
                MODULE_LABELS.get(log.module, log.module),
                ACTION_LABELS.get(log.action, log.action),
                log.username_snapshot,
                log.role_snapshot,
                log.ip_address or '',
                log.external_ip or '',
                log.target_type,
                log.target_id or '',
                log.target_repr,
                log.reason,
                '是' if log.is_abnormal else '否',
                '是' if log.is_audit_event else '否',
            ])

        # 记录导出操作本身
        log_action(
            user=request.user,
            action='audit_log_export',
            module=OperationLog.MODULE_SYSTEM,
            level=OperationLog.LEVEL_WARNING,
            target_type='operation_log',
            target_repr='日志导出',
            request=request,
        )
        return response



class LateRequestCreateView(APIView):
    """
    POST /api/v1/submissions/<submission_id>/late-request/
    学生为自己的某条提交发起补交申请。

    请求格式：multipart/form-data（支持同时上传佐证材料文件）
    必填字段：reason（申请理由）
    可选字段：files（可上传多个，如审批通过凭证截图、情况说明扫描件等）

    同一提交最多只能有一条 pending 申请。
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, submission_id):
        from submission.models import StudentSubmission
        try:
            submission = StudentSubmission.objects.select_related('project__season', 'user').get(pk=submission_id)
        except StudentSubmission.DoesNotExist:
            return Response({'detail': '提交不存在'}, status=status.HTTP_404_NOT_FOUND)
        if submission.user_id != request.user.id:
            return Response({'detail': '无权限操作此提交'}, status=status.HTTP_403_FORBIDDEN)

        reason = request.data.get('reason', '').strip()
        if not reason:
            return Response({'detail': '申请理由不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        # 已有 pending 申请则不允许重复提交
        if LateSubmitRequest.objects.filter(submission=submission, status=LateSubmitRequest.STATUS_PENDING).exists():
            return Response({'detail': f'已有待审核的补交申请，请等待{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}处理'}, status=status.HTTP_400_BAD_REQUEST)

        req = LateSubmitRequest.objects.create(submission=submission, reason=reason)

        # 保存佐证材料附件（支持多文件）
        files = request.FILES.getlist('files')
        for f in files:
            LateSubmitRequestAttachment.objects.create(request=req, file=f, name=f.name)

        log_action(
            user=request.user,
            action='late_request_file',
            module=OperationLog.MODULE_SUBMISSION,
            level=OperationLog.LEVEL_NOTICE,
            target_type='late_submit_request',
            target_id=req.id,
            target_repr=submission.project.name,
            extra={'attachment_count': len(files)},
            request=request,
        )
        return Response(
            LateSubmitRequestSerializer(req, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class LateStatusView(APIView):
    """
    GET /api/v1/submissions/<submission_id>/late-status/
    查询当前登录用户在该提交对应项目上的补交状态：
    是否有活跃通道、是否有 pending 申请、项目是否还在正常提交时间内。
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id):
        from submission.models import StudentSubmission
        try:
            submission = StudentSubmission.objects.select_related('project__season', 'user').get(pk=submission_id)
        except StudentSubmission.DoesNotExist:
            return Response({'detail': '提交不存在'}, status=status.HTTP_404_NOT_FOUND)
        if submission.user_id != request.user.id:
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)

        now = timezone.now()
        project = submission.project
        season = project.season

        # 判断项目是否仍在正常提交窗口内（优先用项目自身时间，无则回退到周期时间）
        project_open = True
        if project.start_time and project.end_time:
            project_open = project.start_time <= now <= project.end_time
        elif season and season.start_time and season.end_time:
            project_open = season.start_time <= now <= season.end_time

        # 查询活跃补交通道
        user = request.user
        class_obj = getattr(user, 'class_obj', None)
        channel_qs = LateSubmitChannel.objects.filter(
            is_active=True,
            planned_close_at__gte=now,
            actual_close_at__isnull=True,
        ).filter(
            Q(project__isnull=True) | Q(project=project)
        ).filter(
            Q(scope_type=LateSubmitChannel.SCOPE_USER, target_user=user) |
            (Q(scope_type=LateSubmitChannel.SCOPE_CLASS, target_class=class_obj) if class_obj else Q(pk__in=[]))
        )
        active_channel = channel_qs.order_by('planned_close_at').first()

        # 查询 pending 申请
        pending_req = LateSubmitRequest.objects.filter(
            submission=submission, status=LateSubmitRequest.STATUS_PENDING
        ).first()

        return Response({
            'project_open': project_open,
            'channel_active': active_channel is not None,
            'channel_expires_at': active_channel.planned_close_at if active_channel else None,
            'channel_id': active_channel.id if active_channel else None,
            'pending_request': pending_req is not None,
            'pending_request_id': pending_req.id if pending_req else None,
        })


class LateRequestListView(generics.ListAPIView):
    """
    GET /api/v1/admin/late-requests/
    管理员查看所有补交申请（支持 status 过滤）。
    返回结果含学生上传的佐证材料附件列表。
    """
    permission_classes = [IsAuthenticated]
    serializer_class = LateSubmitRequestSerializer

    def get_queryset(self):
        if not user_is_admin(self.request.user):
            return LateSubmitRequest.objects.none()
        qs = LateSubmitRequest.objects.select_related(
            'submission__user', 'submission__project', 'handler'
        ).prefetch_related('attachments').order_by('-created_at')
        req_status = self.request.query_params.get('status')
        if req_status:
            qs = qs.filter(status=req_status)
        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx


class LateRequestHandleView(APIView):
    """
    POST /api/v1/admin/late-requests/<pk>/handle/
    管理员审批补交申请。
    action=approve 时同步创建补交通道；action=reject 时仅更新状态。
    必填：action (approve/reject)、reason（开启理由或拒绝说明）；
    approve 时额外必填：hours（≥1）。
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not user_is_admin(request.user):
            return Response({'detail': f'仅{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}可审批补交申请'}, status=status.HTTP_403_FORBIDDEN)
        try:
            req = LateSubmitRequest.objects.select_related('submission__user', 'submission__project').get(pk=pk)
        except LateSubmitRequest.DoesNotExist:
            return Response({'detail': '申请不存在'}, status=status.HTTP_404_NOT_FOUND)
        if req.status != LateSubmitRequest.STATUS_PENDING:
            return Response({'detail': '该申请已处理'}, status=status.HTTP_400_BAD_REQUEST)

        action = request.data.get('action', '')
        comment = request.data.get('comment', '').strip()

        if action == 'reject':
            req.status = LateSubmitRequest.STATUS_REJECTED
            req.handler = request.user
            req.handle_comment = comment
            req.save(update_fields=['status', 'handler', 'handle_comment', 'updated_at'])
            log_action(
                user=request.user,
                action='late_request_reject',
                module=OperationLog.MODULE_SYSTEM,
                level=OperationLog.LEVEL_WARNING,
                target_type='late_submit_request',
                target_id=req.id,
                target_repr=f'补交申请#{req.id}',
                request=request,
            )
            return Response(LateSubmitRequestSerializer(req).data)

        if action == 'approve':
            hours = request.data.get('hours', 24)
            try:
                hours = max(1, int(hours))
            except (TypeError, ValueError):
                hours = 24
            if not comment:
                return Response({'detail': '请填写开启理由'}, status=status.HTTP_400_BAD_REQUEST)
            now = timezone.now()
            channel = LateSubmitChannel.objects.create(
                opened_by=request.user,
                scope_type=LateSubmitChannel.SCOPE_USER,
                target_user=req.submission.user,
                project=req.submission.project,
                reason=comment,
                duration_hours=hours,
                planned_close_at=now + timedelta(hours=hours),
                from_request=req,
            )
            req.status = LateSubmitRequest.STATUS_APPROVED
            req.handler = request.user
            req.handle_comment = comment
            req.save(update_fields=['status', 'handler', 'handle_comment', 'updated_at'])
            approve_extra = {'hours': hours, 'from_request': req.id}
            proj = req.submission.project
            if proj is not None:
                season = getattr(proj, 'season', None)
                if season and season.end_time and season.end_time < now:
                    approve_extra['season_ended'] = True
                    approve_extra['season_end_time'] = str(season.end_time)
            log_action(
                user=request.user,
                action='late_channel_open',
                module=OperationLog.MODULE_SYSTEM,
                level=OperationLog.LEVEL_CRITICAL,
                target_type='late_submit_channel',
                target_id=channel.id,
                target_repr=f'补交通道#{channel.id} → {req.submission.user.username}',
                reason=comment,
                extra=approve_extra,
                is_abnormal=True,
                is_audit_event=True,
                request=request,
            )
            return Response(LateSubmitChannelSerializer(channel).data, status=status.HTTP_201_CREATED)

        return Response({'detail': 'action 参数错误，应为 approve 或 reject'}, status=status.HTTP_400_BAD_REQUEST)


class ImportPermissionRequestCreateView(APIView):
    """
    POST /api/v1/projects/<project_id>/import-requests/
    下级发起导入权限申请（直系上级审批）。
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        from eval.models import EvalProject

        try:
            project = EvalProject.objects.get(pk=project_id)
        except EvalProject.DoesNotExist:
            return Response({'detail': '项目不存在'}, status=status.HTTP_404_NOT_FOUND)

        max_level = _user_max_role_level(request.user)
        if max_level < ROLE_LEVEL_COUNSELOR:
            return Response({'detail': '当前身份不可发起导入权限申请'}, status=status.HTTP_403_FORBIDDEN)
        if max_level >= ROLE_LEVEL_SUPERADMIN:
            return Response({'detail': f'{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}无需发起导入申请'}, status=status.HTTP_400_BAD_REQUEST)

        if ImportPermissionRequest.objects.filter(
            project=project,
            requester=request.user,
            status=ImportPermissionRequest.STATUS_PENDING,
        ).exists():
            return Response({'detail': '已存在待审批申请，请勿重复提交'}, status=status.HTTP_400_BAD_REQUEST)

        reason = str(request.data.get('reason', '')).strip()
        if not reason:
            return Response({'detail': '申请理由不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        req = ImportPermissionRequest.objects.create(
            project=project,
            requester=request.user,
            requester_level=ROLE_LEVEL_DIRECTOR if max_level >= ROLE_LEVEL_DIRECTOR else ROLE_LEVEL_COUNSELOR,
            target_scope=_resolve_import_scope_snapshot(request.user, max_level),
            reason=reason,
        )
        log_action(
            user=request.user,
            action='import_permission_request_create',
            module=OperationLog.MODULE_SCORING,
            level=OperationLog.LEVEL_WARNING,
            target_type='import_permission_request',
            target_id=req.id,
            target_repr=f'{project.name} 导入权限申请',
            reason=reason,
            is_audit_event=True,
            request=request,
        )
        return Response(
            ImportPermissionRequestSerializer(req, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class ImportPermissionRequestListView(generics.ListAPIView):
    """
    GET /api/v1/admin/import-requests/
    审批人查看导入权限申请（直系上级待办）。
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ImportPermissionRequestSerializer

    def get_queryset(self):
        current_level = self.request.user.current_role.level if self.request.user.current_role else -1
        qs = ImportPermissionRequest.objects.select_related(
            'project', 'requester', 'requester__current_role', 'handler'
        ).order_by('-created_at')
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
        if current_level >= ROLE_LEVEL_SUPERADMIN:
            return qs.filter(requester_level=ROLE_LEVEL_DIRECTOR)
        if current_level == ROLE_LEVEL_DIRECTOR and self.request.user.department_id:
            return qs.filter(
                requester_level=ROLE_LEVEL_COUNSELOR,
                requester__department_id=self.request.user.department_id,
            )
        return ImportPermissionRequest.objects.none()


class ImportPermissionRequestHandleView(APIView):
    """
    POST /api/v1/admin/import-requests/<pk>/handle/
    直系上级审批导入权限申请。
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            req = ImportPermissionRequest.objects.select_related('project', 'requester').get(pk=pk)
        except ImportPermissionRequest.DoesNotExist:
            return Response({'detail': '申请不存在'}, status=status.HTTP_404_NOT_FOUND)
        if req.status != ImportPermissionRequest.STATUS_PENDING:
            return Response({'detail': '该申请已处理'}, status=status.HTTP_400_BAD_REQUEST)
        if not _can_handle_import_request(request.user, req):
            return Response({'detail': '仅直系上级可审批该申请'}, status=status.HTTP_403_FORBIDDEN)

        action = request.data.get('action', '')
        comment = str(request.data.get('comment', '')).strip()
        if action not in {'approve', 'reject'}:
            return Response({'detail': 'action 参数错误，应为 approve 或 reject'}, status=status.HTTP_400_BAD_REQUEST)
        if action == 'reject' and not comment:
            return Response({'detail': '请填写拒绝说明'}, status=status.HTTP_400_BAD_REQUEST)

        req.handler = request.user
        req.handle_comment = comment
        if action == 'approve':
            req.status = ImportPermissionRequest.STATUS_APPROVED
            action_code = 'import_permission_request_approve'
        else:
            req.status = ImportPermissionRequest.STATUS_REJECTED
            action_code = 'import_permission_request_reject'
        req.save(update_fields=['status', 'handler', 'handle_comment', 'updated_at'])

        log_action(
            user=request.user,
            action=action_code,
            module=OperationLog.MODULE_SCORING,
            level=OperationLog.LEVEL_WARNING,
            target_type='import_permission_request',
            target_id=req.id,
            target_repr=f'{req.project.name} 导入权限申请',
            reason=comment,
            is_audit_event=True,
            request=request,
        )
        return Response(ImportPermissionRequestSerializer(req, context={'request': request}).data)


class LateChannelListCreateView(APIView):
    """
    GET  /api/v1/admin/late-channels/   管理员查看补交通道列表（active_only=1 过滤仅激活）。
    POST /api/v1/admin/late-channels/   管理员手动开启补交通道（针对个人或班级）。
    """
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _build_pending_count_context(channels):
        """
        预计算每个通道的待推送计数（按通道时间窗口过滤），
        避免“已关闭历史通道吸收新提交”。
        """
        from django.db.models import Q
        from submission.models import StudentSubmission

        pending_count_map = {}
        for ch in channels:
            if ch.scope_type == LateSubmitChannel.SCOPE_USER and ch.target_user_id:
                user_q = Q(user_id=ch.target_user_id)
            elif ch.scope_type == LateSubmitChannel.SCOPE_CLASS and ch.target_class_id:
                user_q = Q(user__class_obj_id=ch.target_class_id)
            else:
                pending_count_map[ch.id] = 0
                continue

            base_q = Q(via_late_channel=True, status='submitted', submitted_at__isnull=False)
            if ch.project_id:
                base_q &= Q(project_id=ch.project_id)
            if ch.open_at:
                base_q &= Q(submitted_at__gte=ch.open_at)
            close_boundary = ch.actual_close_at or ch.planned_close_at
            if close_boundary:
                base_q &= Q(submitted_at__lte=close_boundary)
            pending_count_map[ch.id] = StudentSubmission.objects.filter(base_q).filter(user_q).count()

        return {'channel_pending_count_map': pending_count_map}

    def get(self, request):
        if not user_is_admin(request.user):
            return Response({'detail': f'仅{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}可查看补交通道'}, status=status.HTTP_403_FORBIDDEN)
        qs = LateSubmitChannel.objects.select_related(
            'opened_by', 'closed_by', 'target_user', 'target_class', 'project'
        ).order_by('-open_at')
        if request.query_params.get('active_only') == '1':
            now = timezone.now()
            qs = qs.filter(is_active=True, planned_close_at__gte=now, actual_close_at__isnull=True)
        channels = list(qs)
        pending_count_ctx = self._build_pending_count_context(channels)
        return Response(
            LateSubmitChannelSerializer(
                channels,
                many=True,
                context={'request': request, **pending_count_ctx},
            ).data
        )

    def post(self, request):
        if not user_is_admin(request.user):
            return Response({'detail': f'仅{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}可开启补交通道'}, status=status.HTTP_403_FORBIDDEN)

        scope_type = request.data.get('scope_type', LateSubmitChannel.SCOPE_USER)
        reason = request.data.get('reason', '').strip()
        if not reason:
            return Response({'detail': '开启理由不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        hours = request.data.get('hours', 24)
        try:
            hours = max(1, int(hours))
        except (TypeError, ValueError):
            hours = 24

        target_user = None
        target_class = None

        if scope_type == LateSubmitChannel.SCOPE_USER:
            # 支持按学号或用户名搜索目标学生
            student_no = request.data.get('student_no', '').strip()
            username = request.data.get('username', '').strip()
            user_id = request.data.get('user_id')
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                if user_id:
                    target_user = User.objects.get(pk=user_id)
                elif student_no:
                    target_user = User.objects.get(student_no=student_no)
                elif username:
                    target_user = User.objects.get(username=username)
                else:
                    return Response({'detail': '请提供 student_no、username 或 user_id'}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({'detail': '目标用户不存在'}, status=status.HTTP_404_NOT_FOUND)
        elif scope_type == LateSubmitChannel.SCOPE_CLASS:
            class_id = request.data.get('class_id')
            if not class_id:
                return Response({'detail': '请提供 class_id'}, status=status.HTTP_400_BAD_REQUEST)
            from org.models import Class
            try:
                target_class = Class.objects.get(pk=class_id)
            except Class.DoesNotExist:
                return Response({'detail': '班级不存在'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'detail': 'scope_type 应为 user 或 class'}, status=status.HTTP_400_BAD_REQUEST)

        # 可选：限定到某个测评项目
        project = None
        project_id = request.data.get('project_id')
        if project_id:
            from eval.models import EvalProject
            try:
                project = EvalProject.objects.get(pk=project_id)
            except EvalProject.DoesNotExist:
                return Response({'detail': '测评项目不存在'}, status=status.HTTP_404_NOT_FOUND)

        now = timezone.now()
        channel = LateSubmitChannel.objects.create(
            opened_by=request.user,
            scope_type=scope_type,
            target_user=target_user,
            target_class=target_class,
            project=project,
            reason=reason,
            duration_hours=hours,
            planned_close_at=now + timedelta(hours=hours),
        )
        target_repr = (target_user.username if target_user else target_class.name) if (target_user or target_class) else '—'

        # 检查关联项目的测评周期是否已结束，用于审计标记
        extra_data = {'scope_type': scope_type, 'hours': hours}
        if project is not None:
            season = getattr(project, 'season', None)
            if season and season.end_time and season.end_time < now:
                extra_data['season_ended'] = True
                extra_data['season_end_time'] = str(season.end_time)

        log_action(
            user=request.user,
            action='late_channel_open',
            module=OperationLog.MODULE_SYSTEM,
            level=OperationLog.LEVEL_CRITICAL,
            target_type='late_submit_channel',
            target_id=channel.id,
            target_repr=f'补交通道#{channel.id} → {target_repr}',
            reason=reason,
            extra=extra_data,
            is_abnormal=True,
            is_audit_event=True,
            request=request,
        )
        return Response(LateSubmitChannelSerializer(channel).data, status=status.HTTP_201_CREATED)


class LateChannelCloseView(APIView):
    """
    POST /api/v1/admin/late-channels/<pk>/close/
    管理员手动关闭指定补交通道（comment 可选）。
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not user_is_admin(request.user):
            return Response({'detail': f'仅{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}可关闭补交通道'}, status=status.HTTP_403_FORBIDDEN)
        try:
            channel = LateSubmitChannel.objects.get(pk=pk)
        except LateSubmitChannel.DoesNotExist:
            return Response({'detail': '补交通道不存在'}, status=status.HTTP_404_NOT_FOUND)
        if not channel.is_active:
            return Response({'detail': '该通道已关闭'}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        channel.is_active = False
        channel.actual_close_at = now
        channel.closed_by = request.user
        channel.close_reason = LateSubmitChannel.CLOSE_MANUAL
        channel.save(update_fields=['is_active', 'actual_close_at', 'closed_by', 'close_reason'])

        log_action(
            user=request.user,
            action='late_channel_close',
            module=OperationLog.MODULE_SYSTEM,
            level=OperationLog.LEVEL_WARNING,
            target_type='late_submit_channel',
            target_id=channel.id,
            target_repr=f'补交通道#{channel.id}',
            reason=request.data.get('comment', '管理员手动关闭'),
            request=request,
        )
        return Response(LateSubmitChannelSerializer(channel).data)


class LatePendingSubmissionListView(APIView):
    """
    GET /api/v1/admin/late-submissions/pending/
    待推送中心扁平列表：按“补交提交记录”展示，不按通道分组。
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not user_is_admin(request.user):
            return Response({'detail': f'仅{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}可查看待推送中心'}, status=status.HTTP_403_FORBIDDEN)

        from submission.models import StudentSubmission

        qs = StudentSubmission.objects.filter(
            via_late_channel=True,
            status='submitted',
            submitted_at__isnull=False,
        ).select_related(
            'user__department',
            'user__class_obj__major',
            'project__season',
        ).order_by('-submitted_at', '-id')

        p = request.query_params
        keyword = (p.get('keyword') or '').strip()
        if keyword:
            qs = qs.filter(Q(user__username__icontains=keyword) | Q(user__student_no__icontains=keyword))

        season_id = p.get('season_id')
        if season_id:
            qs = qs.filter(project__season_id=season_id)

        project_id = p.get('project_id')
        if project_id:
            qs = qs.filter(project_id=project_id)

        department_id = p.get('department_id')
        if department_id:
            qs = qs.filter(user__department_id=department_id)

        major_id = p.get('major_id')
        if major_id:
            qs = qs.filter(user__class_obj__major_id=major_id)

        class_id = p.get('class_id')
        if class_id:
            qs = qs.filter(user__class_obj_id=class_id)

        qs = _apply_date_range(qs, p, dt_field='submitted_at')

        return Response(LatePendingSubmissionSerializer(qs, many=True).data)


class LatePendingSubmissionBatchPushView(APIView):
    """
    POST /api/v1/admin/late-submissions/batch-push/
    按提交记录批量推送：将 selected submission 由 submitted 更新为 under_review。
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not user_is_admin(request.user):
            return Response({'detail': f'仅{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}可批量推送补交提交'}, status=status.HTTP_403_FORBIDDEN)

        raw_ids = request.data.get('submission_ids', [])
        if not isinstance(raw_ids, list):
            return Response({'detail': 'submission_ids 必须为数组'}, status=status.HTTP_400_BAD_REQUEST)
        selected_ids = []
        seen = set()
        for sid in raw_ids:
            try:
                sid_int = int(sid)
            except (TypeError, ValueError):
                continue
            if sid_int <= 0 or sid_int in seen:
                continue
            seen.add(sid_int)
            selected_ids.append(sid_int)
        if not selected_ids:
            return Response({'detail': '请至少选择一条待推送记录'}, status=status.HTTP_400_BAD_REQUEST)

        from submission.models import StudentSubmission
        valid_qs = StudentSubmission.objects.filter(
            id__in=selected_ids,
            via_late_channel=True,
            status='submitted',
            submitted_at__isnull=False,
        )
        pushed_submissions = list(valid_qs.select_related('project', 'user'))
        pushed_count = len(pushed_submissions)
        if pushed_count == 0:
            return Response({'detail': '所选记录均不可推送（可能已推送或状态变更）', 'pushed_count': 0, 'invalid_count': len(selected_ids)})

        valid_qs.update(status='under_review')
        from scoring.assignment_services import auto_assign_submission
        for sub in pushed_submissions:
            sub.status = 'under_review'
            auto_assign_submission(sub)
        from realtime.registry import broadcast
        broadcast({'type': 'data_changed', 'model': 'submission'})
        invalid_count = len(selected_ids) - pushed_count

        log_action(
            user=request.user,
            action='late_batch_push',
            module=OperationLog.MODULE_SCORING,
            level=OperationLog.LEVEL_WARNING,
            target_type='late_submission_pool',
            target_repr='待推送中心批量推送',
            extra={'pushed_count': pushed_count, 'selected_count': len(selected_ids), 'invalid_count': invalid_count},
            request=request,
        )
        return Response({
            'detail': f'已推送 {pushed_count} 条补交记录至评审流程',
            'pushed_count': pushed_count,
            'invalid_count': invalid_count,
        })


class ScoreOverrideAPIView(APIView):
    """POST /api/v1/admin/score-override/ 管理员修改最终分（必填 reason，可上传凭证，写 CRITICAL 审计日志）。"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        if not user_is_admin(request.user):
            return Response({'detail': f'仅{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}可修改最终分'}, status=status.HTTP_403_FORBIDDEN)
        submission_id = request.data.get('submission_id')
        final_score = request.data.get('final_score')
        reason = request.data.get('reason', '')
        if not reason:
            return Response({'detail': '必须填写修改理由'}, status=status.HTTP_400_BAD_REQUEST)
        if submission_id is None or final_score is None:
            return Response({'detail': '请提供 submission_id 和 final_score'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            final_score = float(final_score)
        except (TypeError, ValueError):
            return Response({'detail': 'final_score 必须为有效数字'}, status=status.HTTP_400_BAD_REQUEST)
        from submission.models import StudentSubmission
        try:
            sub = StudentSubmission.objects.get(pk=submission_id)
        except StudentSubmission.DoesNotExist:
            return Response({'detail': '提交不存在'}, status=status.HTTP_404_NOT_FOUND)
        old_score = sub.final_score
        sub.final_score = final_score
        sub.save(update_fields=['final_score'])
        evidence_file = request.FILES.get('evidence_file')
        log_action_with_attachment(
            user=request.user,
            action='score_override',
            module=OperationLog.MODULE_SCORING,
            level=OperationLog.LEVEL_CRITICAL,
            target_type='submission',
            target_id=sub.id,
            target_repr=f'提交#{sub.id}',
            reason=reason,
            extra={
                'old_score': str(old_score) if old_score is not None else None,
                'new_score': str(final_score),
            },
            is_abnormal=True,
            is_audit_event=True,
            file_obj=evidence_file,
            request=request,
        )
        from submission.serializers import StudentSubmissionSerializer
        return Response(StudentSubmissionSerializer(sub).data)
