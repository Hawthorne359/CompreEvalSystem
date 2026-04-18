"""
申诉 API：提交、修改/撤回、列表、处理、上报、院系主任处理。
"""
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from audit.models import OperationLog
from audit.services import log_action
from .models import Appeal, AppealAttachment
from .serializers import AppealSerializer, AppealCreateUpdateSerializer, AppealAttachmentSerializer
from users.permissions import user_level_at_least, user_is_admin, get_user_level
from users.role_resolver import (
    ROLE_LEVEL_COUNSELOR, ROLE_LEVEL_DIRECTOR, ROLE_LEVEL_SUPERADMIN,
    get_role_display_name,
)


def _user_manages_submission_scope(user, submission):
    """
    判断用户是否在提交的院系/班级管辖范围内。
    """
    from users.models import UserRole
    class_id = getattr(submission.user, 'class_obj_id', None)
    dept_id = getattr(submission.user, 'department_id', None)
    if class_id and UserRole.objects.filter(
        user=user,
        scope_type='class',
        scope_id=class_id,
        role__level__gte=ROLE_LEVEL_COUNSELOR,
    ).exists():
        return True
    if dept_id and UserRole.objects.filter(
        user=user,
        scope_type='department',
        scope_id=dept_id,
        role__level__gte=ROLE_LEVEL_DIRECTOR,
    ).exists():
        return True
    return False


def _get_dept_head_for_submission(submission):
    """
    根据提交学生所在院系，查找对应院系主任用户。
    返回第一个匹配的院系主任，或 None。
    """
    from users.models import UserRole
    dept_id = submission.user.department_id
    if not dept_id:
        return None
    role_qs = UserRole.objects.filter(
        scope_type='department',
        scope_id=dept_id,
        role__level=3,
    ).select_related('user').first()
    if role_qs:
        return role_qs.user
    # 兜底：找有该院系管辖班级的 level=3 用户（院系主任通过班级 scope 关联时）
    from org.models import Class
    class_ids = list(Class.objects.filter(department_id=dept_id).values_list('id', flat=True))
    if class_ids:
        role_qs2 = UserRole.objects.filter(
            scope_type='class',
            scope_id__in=class_ids,
            role__level=3,
        ).select_related('user').first()
        if role_qs2:
            return role_qs2.user
    return None


class AppealListAPIView(generics.ListAPIView):
    """GET /api/v1/appeals/ 申诉列表。"""
    permission_classes = [IsAuthenticated]
    serializer_class = AppealSerializer

    def get_queryset(self):
        from django.db.models import Q
        user = self.request.user
        qs = (Appeal.objects.all()
              .select_related('submission', 'submission__project', 'handler',
                              'indicator', 'escalated_to', 'escalated_to_admin')
              .order_by('-created_at'))
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if user_is_admin(user):
            return qs
        level = get_user_level(user)
        if level >= 3:
            from users.models import UserRole
            from org.models import Class
            dept_ids = list(
                UserRole.objects.filter(user=user, scope_type='department')
                .values_list('scope_id', flat=True)
            )
            class_ids_from_dept = list(
                Class.objects.filter(department_id__in=dept_ids).values_list('id', flat=True)
            ) if dept_ids else []
            scope_class_ids = list(
                UserRole.objects.filter(user=user, scope_type='class')
                .values_list('scope_id', flat=True)
            )
            all_class_ids = list(set(class_ids_from_dept + scope_class_ids))
            if all_class_ids:
                return qs.filter(
                    Q(submission__user__class_obj_id__in=all_class_ids) | Q(escalated_to=user)
                )
            return qs.filter(escalated_to=user)
        if level >= 2:
            from users.models import UserRole
            scope_class_ids = list(
                UserRole.objects.filter(user=user, scope_type='class')
                .values_list('scope_id', flat=True)
            )
            if scope_class_ids:
                return qs.filter(
                    Q(submission__user__class_obj_id__in=scope_class_ids) | Q(submission__isnull=True, user__class_obj_id__in=scope_class_ids)
                )
            return qs.filter(Q(submission__user=user) | Q(user=user))
        return qs.filter(Q(submission__user=user) | Q(user=user))


class AppealCreateAPIView(APIView):
    """POST /api/v1/submissions/<id>/appeal/ 提交申诉（支持 indicator_id）。"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk):
        from submission.models import StudentSubmission
        try:
            sub = StudentSubmission.objects.get(pk=pk)
        except StudentSubmission.DoesNotExist:
            return Response({'detail': '提交不存在'}, status=status.HTTP_404_NOT_FOUND)
        if sub.user_id != request.user.id:
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        reason = request.data.get('reason', '')
        if not reason:
            return Response({'detail': '请填写申诉理由'}, status=status.HTTP_400_BAD_REQUEST)

        indicator = None
        indicator_id = request.data.get('indicator_id')
        if indicator_id:
            from eval.models import EvalIndicator
            try:
                indicator = EvalIndicator.objects.get(pk=indicator_id, project=sub.project)
            except EvalIndicator.DoesNotExist:
                return Response({'detail': '指标不存在或不属于该项目'}, status=status.HTTP_400_BAD_REQUEST)
            if indicator.score_source not in ('import', 'reviewer'):
                return Response({'detail': '仅统一导入或评审打分类型的指标可以申诉'}, status=status.HTTP_400_BAD_REQUEST)

        appeal = Appeal.objects.create(
            user=request.user,
            submission=sub,
            indicator=indicator,
            reason=reason,
            original_submission_status=sub.status,
            status='pending',
        )
        sub.status = 'appealing'
        sub.save(update_fields=['status'])
        files = request.FILES.getlist('files')
        for file_obj in files:
            AppealAttachment.objects.create(
                appeal=appeal,
                file=file_obj,
                name=getattr(file_obj, 'name', '') or '',
                uploaded_by=request.user,
            )
        log_action(
            user=request.user,
            action='appeal_file',
            module=OperationLog.MODULE_APPEAL,
            level=OperationLog.LEVEL_NOTICE,
            target_type='appeal',
            target_id=appeal.id,
            target_repr=f'提交#{sub.id}' + (f' 指标#{indicator.id}' if indicator else ''),
            request=request,
        )
        return Response(AppealSerializer(appeal).data, status=status.HTTP_201_CREATED)


class AppealIndependentCreateAPIView(APIView):
    """POST /api/v1/appeals/independent/ 创建独立申诉（主题+内容+附件，不关联具体提交/指标）。"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        title = (request.data.get('title') or '').strip()
        reason = (request.data.get('reason') or '').strip()
        if not title:
            return Response({'detail': '请填写申诉主题'}, status=status.HTTP_400_BAD_REQUEST)
        if not reason:
            return Response({'detail': '请填写申诉内容'}, status=status.HTTP_400_BAD_REQUEST)

        submission_id = request.data.get('submission_id')
        submission = None
        if submission_id:
            from submission.models import StudentSubmission
            try:
                submission = StudentSubmission.objects.get(pk=submission_id, user=request.user)
            except StudentSubmission.DoesNotExist:
                return Response({'detail': '关联提交不存在或无权限'}, status=status.HTTP_400_BAD_REQUEST)

        appeal = Appeal.objects.create(
            title=title,
            user=request.user,
            submission=submission,
            indicator=None,
            reason=reason,
            original_submission_status=submission.status if submission else '',
            status='pending',
        )
        if submission:
            submission.status = 'appealing'
            submission.save(update_fields=['status'])

        files = request.FILES.getlist('files')
        for file_obj in files:
            AppealAttachment.objects.create(
                appeal=appeal,
                file=file_obj,
                name=getattr(file_obj, 'name', '') or '',
                uploaded_by=request.user,
            )
        log_action(
            user=request.user,
            action='appeal_independent_create',
            module=OperationLog.MODULE_APPEAL,
            level=OperationLog.LEVEL_NOTICE,
            target_type='appeal',
            target_id=appeal.id,
            target_repr=title,
            extra={'submission_id': submission.id if submission else None},
            request=request,
        )
        return Response(AppealSerializer(appeal).data, status=status.HTTP_201_CREATED)


class AppealAttachmentUploadAPIView(APIView):
    """POST /api/v1/appeals/<id>/attachments/ 上传申诉附件（仅申诉人、pending）。"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk):
        try:
            appeal = Appeal.objects.select_related('submission').get(pk=pk)
        except Appeal.DoesNotExist:
            return Response({'detail': '申诉不存在'}, status=status.HTTP_404_NOT_FOUND)
        appeal_user_id = appeal.user_id or (appeal.submission.user_id if appeal.submission_id else None)
        if appeal_user_id != request.user.id:
            return Response({'detail': '仅申诉人可上传附件'}, status=status.HTTP_403_FORBIDDEN)
        if appeal.status != 'pending':
            return Response({'detail': '仅待处理申诉可上传附件'}, status=status.HTTP_400_BAD_REQUEST)

        files = request.FILES.getlist('files')
        if not files:
            return Response({'detail': '请至少上传一个附件'}, status=status.HTTP_400_BAD_REQUEST)
        created = []
        for file_obj in files:
            att = AppealAttachment.objects.create(
                appeal=appeal,
                file=file_obj,
                name=getattr(file_obj, 'name', '') or '',
                uploaded_by=request.user,
            )
            created.append(att)
        return Response(AppealAttachmentSerializer(created, many=True).data, status=status.HTTP_201_CREATED)


class AppealAttachmentDeleteAPIView(APIView):
    """DELETE /api/v1/appeals/<id>/attachments/<attachment_id>/ 删除申诉附件。"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk, attachment_id):
        try:
            appeal = Appeal.objects.select_related('submission').get(pk=pk)
        except Appeal.DoesNotExist:
            return Response({'detail': '申诉不存在'}, status=status.HTTP_404_NOT_FOUND)
        if appeal.submission.user_id != request.user.id and not user_is_admin(request.user):
            return Response({'detail': '无权限删除附件'}, status=status.HTTP_403_FORBIDDEN)
        if appeal.status != 'pending' and not user_is_admin(request.user):
            return Response({'detail': '仅待处理申诉可删除附件'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            attachment = AppealAttachment.objects.get(pk=attachment_id, appeal=appeal)
        except AppealAttachment.DoesNotExist:
            return Response({'detail': '附件不存在'}, status=status.HTTP_404_NOT_FOUND)
        attachment.delete()
        return Response({'detail': '删除成功'})


class AppealDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/v1/appeals/<id>/ 详情、修改理由与撤回（仅 pending）。"""
    permission_classes = [IsAuthenticated]
    serializer_class = AppealSerializer

    def get_serializer_class(self):
        if self.request.method in ('PATCH', 'PUT'):
            return AppealCreateUpdateSerializer
        return AppealSerializer

    def get_queryset(self):
        from django.db.models import Q
        user = self.request.user
        qs = Appeal.objects.all().select_related(
            'submission', 'handler', 'indicator', 'escalated_to', 'user'
        )
        if user_is_admin(user):
            return qs
        level = get_user_level(user)
        if level >= ROLE_LEVEL_DIRECTOR:
            from users.models import UserRole
            from org.models import Class
            dept_ids = list(
                UserRole.objects.filter(user=user, scope_type='department')
                .values_list('scope_id', flat=True)
            )
            class_ids_from_dept = list(
                Class.objects.filter(department_id__in=dept_ids).values_list('id', flat=True)
            ) if dept_ids else []
            scope_class_ids = list(
                UserRole.objects.filter(user=user, scope_type='class')
                .values_list('scope_id', flat=True)
            )
            all_class_ids = list(set(class_ids_from_dept + scope_class_ids))
            if all_class_ids:
                return qs.filter(
                    Q(submission__user__class_obj_id__in=all_class_ids) | Q(escalated_to=user) | Q(user__class_obj_id__in=all_class_ids)
                )
            return qs.filter(escalated_to=user)
        if level >= ROLE_LEVEL_COUNSELOR:
            from users.models import UserRole
            scope_class_ids = list(
                UserRole.objects.filter(user=user, scope_type='class')
                .values_list('scope_id', flat=True)
            )
            if scope_class_ids:
                return qs.filter(
                    Q(submission__user__class_obj_id__in=scope_class_ids) | Q(escalated_to=user) | Q(user__class_obj_id__in=scope_class_ids)
                )
            return qs.filter(Q(submission__user=user) | Q(user=user))
        return qs.filter(Q(submission__user=user) | Q(user=user))

    def perform_update(self, serializer):
        if serializer.instance.status != 'pending':
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'detail': '仅待处理状态可修改或撤回'})
        appeal_user_id = serializer.instance.user_id or (serializer.instance.submission.user_id if serializer.instance.submission_id else None)
        if appeal_user_id != self.request.user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('仅本人可修改')
        serializer.save()

    def perform_destroy(self, instance):
        """仅允许申诉发起人撤回待处理申诉，并恢复提交状态。"""
        if instance.status != 'pending':
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'detail': '仅待处理状态可撤回'})
        appeal_user_id = instance.user_id or (instance.submission.user_id if instance.submission_id else None)
        if appeal_user_id != self.request.user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('仅本人可撤回')
        submission = instance.submission
        instance_id = instance.id
        restore_status = instance.original_submission_status or ''
        instance.delete()
        if submission:
            if restore_status not in {'draft', 'submitted', 'under_review', 'approved', 'rejected', 'appealing'}:
                restore_status = 'approved' if submission.final_score is not None else 'under_review'
            submission.status = restore_status
            submission.save(update_fields=['status'])
            if restore_status == 'submitted':
                from scoring.assignment_services import auto_assign_submission
                auto_assign_submission(submission)
        log_action(
            user=self.request.user,
            action='appeal_withdraw',
            module=OperationLog.MODULE_APPEAL,
            level=OperationLog.LEVEL_NOTICE,
            target_type='appeal',
            target_id=instance_id,
            target_repr=f'提交#{submission.id}',
            request=self.request,
        )


class AppealHandleAPIView(APIView):
    """POST /api/v1/appeals/<id>/handle/ 评审老师处理申诉（通过/驳回/上报院系主任）。"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            appeal = Appeal.objects.select_related('submission', 'submission__user').get(pk=pk)
        except Appeal.DoesNotExist:
            return Response({'detail': '申诉不存在'}, status=status.HTTP_404_NOT_FOUND)
        if not user_level_at_least(request.user, 2):
            return Response({'detail': f'{get_role_display_name(ROLE_LEVEL_COUNSELOR)}及以上角色方可处理申诉'}, status=status.HTTP_403_FORBIDDEN)
        is_admin_user = user_is_admin(request.user)
        if is_admin_user:
            if appeal.status not in ('pending', 'escalated'):
                return Response({'detail': '该申诉当前状态不可直接处理'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            if appeal.status != 'pending':
                return Response({'detail': '该申诉已处理'}, status=status.HTTP_400_BAD_REQUEST)
            if not _user_manages_submission_scope(request.user, appeal.submission):
                return Response({'detail': '您不在该申诉的管辖范围内'}, status=status.HTTP_403_FORBIDDEN)

        action_type = request.data.get('action')  # approved | rejected | escalate
        handle_comment = request.data.get('handle_comment', '')

        if action_type == 'escalate':
            if is_admin_user:
                return Response({'detail': '超级管理员无需上报，请直接终裁'}, status=status.HTTP_400_BAD_REQUEST)
            # 上报院系主任
            dept_head = _get_dept_head_for_submission(appeal.submission)
            appeal.status = 'escalated'
            appeal.is_escalated = True
            appeal.escalated_to = dept_head
            appeal.handler = request.user
            appeal.handle_comment = handle_comment
            appeal.save(update_fields=['status', 'is_escalated', 'escalated_to_id', 'handler_id', 'handle_comment'])
            log_action(
                user=request.user,
                action='appeal_escalate',
                module=OperationLog.MODULE_APPEAL,
                level=OperationLog.LEVEL_WARNING,
                target_type='appeal',
                target_id=appeal.id,
                target_repr=f'提交#{appeal.submission_id}',
                extra={'escalated_to': dept_head.id if dept_head else None},
                request=request,
            )
            return Response(AppealSerializer(appeal).data)

        if action_type not in ('approved', 'rejected'):
            return Response({'detail': 'action 须为 approved、rejected 或 escalate'}, status=status.HTTP_400_BAD_REQUEST)

        appeal.status = action_type
        appeal.handler = request.user
        appeal.handle_comment = handle_comment
        appeal.save(update_fields=['status', 'handler_id', 'handle_comment'])
        sub = appeal.submission
        sub.status = 'under_review' if action_type == 'approved' else 'rejected'
        sub.save(update_fields=['status'])
        log_action(
            user=request.user,
            action='appeal_handle',
            module=OperationLog.MODULE_APPEAL,
            level=OperationLog.LEVEL_WARNING,
            target_type='appeal',
            target_id=appeal.id,
            target_repr=f'提交#{sub.id}',
            extra={'result': action_type, 'comment': handle_comment},
            request=request,
        )
        return Response(AppealSerializer(appeal).data)


def _get_super_admin():
    """查找一个最高管理角色用户，用于上报目标。"""
    from users.models import UserRole
    role_qs = UserRole.objects.filter(role__level=ROLE_LEVEL_SUPERADMIN).select_related('user').first()
    return role_qs.user if role_qs else None


def _apply_score_overrides(appeal, score_overrides, user):
    """
    在申诉通过时写入评分裁定覆盖。
    score_overrides: [{ indicator_id, score, comment? }]
    """
    if not score_overrides:
        return
    from scoring.models import ArbitrationRecord
    from scoring.services import recompute_submission_final_score
    sub = appeal.submission
    for item in score_overrides:
        ind_id = item.get('indicator_id')
        score_val = item.get('score')
        comment = item.get('comment', '')
        if ind_id is None or score_val is None:
            continue
        ArbitrationRecord.objects.update_or_create(
            submission=sub, indicator_id=ind_id,
            defaults={
                'arbitrator': user,
                'score': score_val,
                'comment': comment,
                'triggered_reason': 'appeal_override',
            },
        )
    recompute_submission_final_score(sub)


class AppealEscalateHandleAPIView(APIView):
    """POST /api/v1/appeals/<id>/escalate-handle/ 院系主任处理上报申诉（通过/驳回/上报超管）。"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            appeal = Appeal.objects.select_related('submission').get(pk=pk)
        except Appeal.DoesNotExist:
            return Response({'detail': '申诉不存在'}, status=status.HTTP_404_NOT_FOUND)
        if appeal.status != 'escalated':
            return Response({'detail': '该申诉未处于已上报状态'}, status=status.HTTP_400_BAD_REQUEST)
        if not user_level_at_least(request.user, 3):
            return Response({'detail': f'{get_role_display_name(ROLE_LEVEL_DIRECTOR)}及以上角色方可处理上报申诉'}, status=status.HTTP_403_FORBIDDEN)
        if not user_is_admin(request.user) and appeal.escalated_to_id != request.user.id:
            return Response({'detail': '此申诉未上报给您'}, status=status.HTTP_403_FORBIDDEN)

        action_type = request.data.get('action')  # approved | rejected | escalate_admin
        escalate_comment = request.data.get('escalate_comment', '')

        if action_type == 'escalate_admin':
            admin_user = _get_super_admin()
            appeal.status = 'escalated_to_admin'
            appeal.escalated_to_admin = admin_user
            appeal.escalate_comment = escalate_comment
            appeal.save(update_fields=['status', 'escalated_to_admin_id', 'escalate_comment'])
            log_action(
                user=request.user,
                action='appeal_escalate_admin',
                module=OperationLog.MODULE_APPEAL,
                level=OperationLog.LEVEL_WARNING,
                target_type='appeal',
                target_id=appeal.id,
                target_repr=f'提交#{appeal.submission_id}',
                extra={'escalated_to_admin': admin_user.id if admin_user else None},
                request=request,
            )
            return Response(AppealSerializer(appeal).data)

        if action_type not in ('approved', 'rejected'):
            return Response({'detail': 'action 须为 approved、rejected 或 escalate_admin'}, status=status.HTTP_400_BAD_REQUEST)

        appeal.status = action_type
        appeal.escalate_comment = escalate_comment
        appeal.save(update_fields=['status', 'escalate_comment'])

        score_overrides = request.data.get('score_overrides')
        if action_type == 'approved' and score_overrides:
            _apply_score_overrides(appeal, score_overrides, request.user)

        sub = appeal.submission
        sub.status = 'under_review' if action_type == 'approved' else 'rejected'
        sub.save(update_fields=['status'])
        log_action(
            user=request.user,
            action='appeal_escalate_handle',
            module=OperationLog.MODULE_APPEAL,
            level=OperationLog.LEVEL_WARNING,
            target_type='appeal',
            target_id=appeal.id,
            target_repr=f'提交#{sub.id}',
            extra={'result': action_type, 'comment': escalate_comment},
            request=request,
        )
        return Response(AppealSerializer(appeal).data)


class AppealAdminHandleAPIView(APIView):
    """POST /api/v1/appeals/<id>/admin-handle/ 最高管理角色处理上报申诉（终裁，可含评分覆盖）。"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not user_is_admin(request.user):
            return Response(
                {'detail': f'仅{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}可处理此申诉'},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            appeal = Appeal.objects.select_related('submission').get(pk=pk)
        except Appeal.DoesNotExist:
            return Response({'detail': '申诉不存在'}, status=status.HTTP_404_NOT_FOUND)
        if appeal.status != 'escalated_to_admin':
            return Response(
                {'detail': f'该申诉未处于已上报{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}状态'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        action_type = request.data.get('action')  # approved | rejected
        admin_comment = request.data.get('admin_comment', '')
        if action_type not in ('approved', 'rejected'):
            return Response({'detail': 'action 须为 approved 或 rejected'}, status=status.HTTP_400_BAD_REQUEST)

        appeal.status = action_type
        appeal.admin_comment = admin_comment
        appeal.save(update_fields=['status', 'admin_comment'])

        score_overrides = request.data.get('score_overrides')
        if action_type == 'approved' and score_overrides:
            _apply_score_overrides(appeal, score_overrides, request.user)

        sub = appeal.submission
        sub.status = 'under_review' if action_type == 'approved' else 'rejected'
        sub.save(update_fields=['status'])
        log_action(
            user=request.user,
            action='appeal_admin_handle',
            module=OperationLog.MODULE_APPEAL,
            level=OperationLog.LEVEL_WARNING,
            target_type='appeal',
            target_id=appeal.id,
            target_repr=f'提交#{sub.id}',
            extra={'result': action_type, 'comment': admin_comment},
            request=request,
        )
        return Response(AppealSerializer(appeal).data)
