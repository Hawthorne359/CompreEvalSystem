"""
成绩统计与报表 API：汇总、排名、导出、学生本人成绩。
"""
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Q
from django.conf import settings

from audit.models import OperationLog
from audit.services import log_action
from submission.models import StudentSubmission, Evidence
from eval.utils import raw_max_score as _raw_max_score
from submission.serializers import StudentSubmissionSerializer, StudentSubmissionListSerializer
from eval.models import EvalProject
from users.permissions import user_level_at_least
from scoring.models import ScoreRecord, ArbitrationRecord, ImportedScoreDetail
from scoring.services import get_indicator_final_score
from scoring.views import _attach_logical_round_fields
from .models import ReportExportTemplate, ReportExportMapping
from .serializers import ReportExportTemplateSerializer, ReportExportMappingSerializer
from .services import (
    build_download_response,
    build_export_payload,
    FIELD_VIEW_MODE_ADVANCED_ALL,
    FIELD_VIEW_MODE_TEMPLATE_COMMON,
    get_project_export_catalog,
    render_excel,
    render_pdf,
    render_pdf_zip,
    render_word,
    render_word_zip,
    resolve_report_queryset,
    validate_export_mapping_config,
)


def _resolve_default_mapping(user, project, output_format):
    """按项目+格式解析默认映射，优先项目级，再回退全局级。"""
    candidates = list(
        ReportExportMapping.objects.select_related('template').filter(
            output_format=output_format,
            is_default=True,
        ).filter(
            Q(project_id=project.id) | Q(project_id__isnull=True)
        )
    )
    if not candidates:
        return None
    # 同等条件下优先：
    # 1) 当前项目绑定映射 2) 当前用户创建 3) 最新记录
    candidates.sort(key=lambda obj: (
        0 if obj.project_id == project.id else 1,
        0 if obj.owner_id == user.id else 1,
        -obj.id,
    ))
    return candidates[0]


def _report_leaf_indicators(project):
    """返回项目下用于学生报表展示的叶子指标（self/import/reviewer）。"""
    indicators = list(
        project.indicators.select_related('parent__parent').order_by('order', 'id')
    )
    children_map = {}
    for ind in indicators:
        if ind.parent_id is not None:
            children_map.setdefault(ind.parent_id, []).append(ind.id)
    return [
        ind for ind in indicators
        if ind.score_source in ('self', 'import', 'reviewer') and ind.id not in children_map
    ]


def _display_user_name(user):
    """返回用于展示的用户姓名（优先 real_name）。"""
    if not user:
        return ''
    return getattr(user, 'real_name', '') or getattr(user, 'username', '') or ''


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _request_filters(request):
    return {
        'department_id': _to_int(request.query_params.get('department_id')),
        'major_id': _to_int(request.query_params.get('major_id')),
        'class_id': _to_int(request.query_params.get('class_id')),
        'search': request.query_params.get('search', '').strip(),
    }


def _can_access_template(user, template):
    if template.owner_id == user.id:
        return True
    if template.visibility == 'global' and user_level_at_least(user, 3):
        return True
    if template.visibility == 'department' and user.department_id and template.department_id == user.department_id:
        return True
    return False


class ReportProjectSummaryAPIView(APIView):
    """GET /api/v1/report/project/<id>/summary/ 某项目成绩汇总。主任及以上(level>=3)看全部；评审老师(level>=2)看本班。"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        # 评审老师（辅导员）及以上（level>=2）才可访问
        if not user_level_at_least(request.user, 2):
            return Response({'detail': '无权限查看成绩汇总'}, status=status.HTTP_403_FORBIDDEN)
        try:
            project = EvalProject.objects.get(pk=pk)
        except EvalProject.DoesNotExist:
            return Response({'detail': '项目不存在'}, status=status.HTTP_404_NOT_FOUND)
        submissions = resolve_report_queryset(project, request.user, filters=_request_filters(request))
        by_class = {}
        for sub in submissions:
            c = sub.user.class_obj
            key = c.name if c else '未分班'
            if key not in by_class:
                by_class[key] = {'count': 0, 'total': 0, 'scores': []}
            by_class[key]['count'] += 1
            if sub.final_score is not None:
                by_class[key]['total'] += float(sub.final_score)
                by_class[key]['scores'].append(float(sub.final_score))
        for k, v in by_class.items():
            v['avg'] = v['total'] / len(v['scores']) if v['scores'] else 0
            del v['scores']
        return Response({'project_id': pk, 'project_name': project.name, 'by_class': by_class, 'total_count': submissions.count()})


class ReportProjectRankingAPIView(APIView):
    """GET /api/v1/report/project/<id>/ranking/ 排名（分页）。评审老师（辅导员）及以上可访问。"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        if not user_level_at_least(request.user, 2):
            return Response({'detail': '无权限查看排名'}, status=status.HTTP_403_FORBIDDEN)
        try:
            project = EvalProject.objects.get(pk=pk)
        except EvalProject.DoesNotExist:
            return Response({'detail': '项目不存在'}, status=status.HTTP_404_NOT_FOUND)
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        qs = resolve_report_queryset(project, request.user, filters=_request_filters(request))
        total = qs.count()
        start = (page - 1) * page_size
        items = qs[start:start + page_size]
        results = []
        for i, sub in enumerate(items, start=start + 1):
            results.append({
                'rank': i,
                'submission_id': sub.id,
                'user_id': sub.user_id,
                'student_no': getattr(sub.user, 'student_no', '') or sub.user.username,
                'username': sub.user.username,
                'real_name': sub.user.get_full_name() or sub.user.username,
                'final_score': float(sub.final_score) if sub.final_score is not None else None,
            })
        return Response({'total': total, 'page': page, 'page_size': page_size, 'results': results})


class ReportProjectExportAPIView(APIView):
    """GET /api/v1/report/project/<id>/export/?format=xlsx|pdf 导出。评审老师（辅导员）及以上可导出。"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        if not user_level_at_least(request.user, 2):
            return Response({'detail': '无权限导出报表'}, status=status.HTTP_403_FORBIDDEN)
        try:
            project = EvalProject.objects.get(pk=pk)
        except EvalProject.DoesNotExist:
            return Response({'detail': '项目不存在'}, status=status.HTTP_404_NOT_FOUND)
        fmt = request.query_params.get('output_format') or request.query_params.get('format', 'xlsx')
        fmt = str(fmt).lower()
        if fmt not in ('xlsx', 'pdf', 'word'):
            return Response({'detail': 'format 须为 xlsx / pdf / word'}, status=status.HTTP_400_BAD_REQUEST)
        multi_file = request.query_params.get('multi_file', 'false').lower() == 'true'
        group_by = request.query_params.get('group_by', '').strip().lower()  # '' or 'class'
        zip_filename_pattern = request.query_params.get('zip_filename_pattern', '').strip() or None
        mapping_id = _to_int(request.query_params.get('mapping_id'))
        template_id = _to_int(request.query_params.get('template_id'))
        mapping = None
        template = None
        if mapping_id:
            try:
                mapping = ReportExportMapping.objects.select_related('template').get(pk=mapping_id)
            except ReportExportMapping.DoesNotExist:
                return Response({'detail': '映射配置不存在'}, status=status.HTTP_404_NOT_FOUND)
            if mapping.owner_id != request.user.id and not user_level_at_least(request.user, 3):
                return Response({'detail': '无权限使用该映射'}, status=status.HTTP_403_FORBIDDEN)
            if mapping.template_id:
                try:
                    template = mapping.template
                except ReportExportTemplate.DoesNotExist:
                    return Response(
                        {'detail': '映射关联模板不存在，请重新选择模板并保存映射'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
        else:
            mapping = _resolve_default_mapping(request.user, project, fmt)
            if mapping and mapping.template_id:
                try:
                    template = mapping.template
                except ReportExportTemplate.DoesNotExist:
                    return Response(
                        {'detail': '默认映射关联模板不存在，请在导出模板配置中重新绑定模板'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
        if template_id:
            try:
                template = ReportExportTemplate.objects.get(pk=template_id, is_active=True)
            except ReportExportTemplate.DoesNotExist:
                return Response({'detail': '模板不存在'}, status=status.HTTP_404_NOT_FOUND)
        if template and not template.is_active:
            return Response(
                {'detail': '映射关联的模板已失效，请在导出模板配置中重新选择模板并保存映射'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if template and not _can_access_template(request.user, template):
            return Response({'detail': '无权限使用该模板'}, status=status.HTTP_403_FORBIDDEN)
        rows = build_export_payload(project, request.user, filters=_request_filters(request))
        cfg = (mapping.config if mapping else {}) or {}
        try:
            cfg = validate_export_mapping_config(cfg, output_format=fmt)
        except ValueError as exc:
            return Response({'detail': f'映射配置不合法：{str(exc)}'}, status=status.HTTP_400_BAD_REQUEST)
        template_path = template.file.path if (template and template.file) else None
        if fmt == 'xlsx' and template and template.template_type != 'excel':
            return Response({'detail': 'Excel 导出仅可使用 Excel 模板'}, status=status.HTTP_400_BAD_REQUEST)
        if fmt in ('word', 'pdf'):
            if template and template.template_type != 'word':
                return Response({'detail': 'Word/PDF 导出仅可使用 Word 模板'}, status=status.HTTP_400_BAD_REQUEST)
            if not template_path:
                return Response(
                    {'detail': '未找到可用 Word 模板：请在“导出模板配置”中保存并设为默认映射，或手动选择模板后再导出'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        try:
            if fmt == 'xlsx':
                payload = render_excel(rows, mapping_config=cfg, template_path=template_path)
                resp = build_download_response(
                    payload,
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    f'成绩报表_{project.name}.xlsx',
                )
            elif fmt == 'word' and multi_file:
                payload = render_word_zip(rows, mapping_config=cfg, template_path=template_path,
                                          group_by=group_by, zip_filename_pattern=zip_filename_pattern)
                suffix = '_按班级' if group_by == 'class' else '_逐人'
                resp = build_download_response(
                    payload,
                    'application/zip',
                    f'成绩报表_{project.name}{suffix}.zip',
                )
            elif fmt == 'word':
                payload = render_word(rows, mapping_config=cfg, template_path=template_path)
                resp = build_download_response(
                    payload,
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    f'成绩报表_{project.name}.docx',
                )
            elif fmt == 'pdf' and multi_file:
                payload = render_pdf_zip(rows, mapping_config=cfg, template_path=template_path,
                                         group_by=group_by, zip_filename_pattern=zip_filename_pattern)
                suffix = '_按班级' if group_by == 'class' else '_逐人'
                resp = build_download_response(
                    payload,
                    'application/zip',
                    f'成绩报表_{project.name}{suffix}.zip',
                )
            else:
                payload = render_pdf(rows, mapping_config=cfg, template_path=template_path)
                resp = build_download_response(payload, 'application/pdf', f'成绩报表_{project.name}.pdf')
        except RuntimeError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_501_NOT_IMPLEMENTED)
        except Exception as exc:
            return Response({'detail': f'导出失败：{str(exc)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        log_action(
            user=request.user,
            action='report_export',
            module=OperationLog.MODULE_REPORT,
            level=OperationLog.LEVEL_NOTICE,
            target_type='eval_project',
            target_id=project.id,
            target_repr=project.name,
            extra={
                'format': fmt,
                'mapping_id': mapping.id if mapping else None,
                'template_id': template.id if template else None,
                'rows': len(rows),
            },
            request=request,
        )
        return resp


class ReportStudentMeAPIView(APIView):
    """GET /api/v1/report/student/me/ 本人各项目得分与明细。"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        subs = StudentSubmission.objects.filter(user=request.user).exclude(status='draft').select_related('project').order_by('-submitted_at')
        data = []
        for sub in subs:
            data.append({
                'submission': StudentSubmissionListSerializer(sub).data,
                'final_score': float(sub.final_score) if sub.final_score is not None else None,
                'score_detail': sub.score_detail,
            })
        return Response(data)


class ReportExportFieldOptionsAPIView(APIView):
    """GET /api/v1/report/project/<id>/export/fields/ 导出可映射字段列表。"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        if not user_level_at_least(request.user, 2):
            return Response({'detail': '无权限查看导出字段'}, status=status.HTTP_403_FORBIDDEN)
        try:
            project = EvalProject.objects.get(pk=pk)
        except EvalProject.DoesNotExist:
            return Response({'detail': '项目不存在'}, status=status.HTTP_404_NOT_FOUND)
        view_mode = request.query_params.get('view_mode', FIELD_VIEW_MODE_TEMPLATE_COMMON)
        if view_mode not in (FIELD_VIEW_MODE_TEMPLATE_COMMON, FIELD_VIEW_MODE_ADVANCED_ALL):
            view_mode = FIELD_VIEW_MODE_TEMPLATE_COMMON
        catalog = get_project_export_catalog(project, view_mode=view_mode)
        return Response({
            'project_id': project.id,
            'project_name': project.name,
            'field_version': catalog.get('field_version', 1),
            'common_profile_version': catalog.get('common_profile_version', 1),
            'field_view_mode': catalog.get('field_view_mode', FIELD_VIEW_MODE_TEMPLATE_COMMON),
            'field_groups': catalog.get('field_groups', []),
            'fields': catalog.get('fields', []),
            'all_fields': catalog.get('all_fields', catalog.get('fields', [])),
            'field_tree': catalog.get('field_tree', []),
            'presets': catalog.get('presets', []),
        })


class ReportExportTemplateListCreateAPIView(APIView):
    """GET/POST 导出模板列表与创建。"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        if not user_level_at_least(request.user, 2):
            return Response({'detail': '无权限查看模板'}, status=status.HTTP_403_FORBIDDEN)
        qs = ReportExportTemplate.objects.filter(is_active=True)
        project_id = _to_int(request.query_params.get('project_id'))
        template_type = request.query_params.get('template_type')
        if project_id:
            qs = qs.filter(Q(project_id=project_id) | Q(project_id__isnull=True))
        if template_type:
            qs = qs.filter(template_type=template_type)
        if user_level_at_least(request.user, 5):
            pass
        elif user_level_at_least(request.user, 3):
            qs = qs.filter(
                Q(owner=request.user)
                | Q(visibility='global')
                | Q(visibility='department', department_id=request.user.department_id)
            )
        else:
            qs = qs.filter(owner=request.user)
        return Response(ReportExportTemplateSerializer(qs, many=True).data)

    def post(self, request):
        if not user_level_at_least(request.user, 2):
            return Response({'detail': '无权限上传模板'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ReportExportTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        visibility = serializer.validated_data.get('visibility', 'private')
        if visibility in ('department', 'global') and not user_level_at_least(request.user, 3):
            return Response({'detail': '仅主任及以上可创建院系/全局模板'}, status=status.HTTP_403_FORBIDDEN)
        # Multipart/FormData 场景下，布尔字段缺失可能被解析为 False，创建模板时强制激活。
        serializer.save(owner=request.user, department=request.user.department, is_active=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ReportExportTemplateDetailAPIView(APIView):
    """GET/PATCH/DELETE 单个导出模板。"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def _get_obj(self, pk):
        return ReportExportTemplate.objects.get(pk=pk, is_active=True)

    def get(self, request, pk):
        try:
            obj = self._get_obj(pk)
        except ReportExportTemplate.DoesNotExist:
            return Response({'detail': '模板不存在'}, status=status.HTTP_404_NOT_FOUND)
        if not _can_access_template(request.user, obj):
            return Response({'detail': '无权限查看模板'}, status=status.HTTP_403_FORBIDDEN)
        return Response(ReportExportTemplateSerializer(obj).data)

    def patch(self, request, pk):
        try:
            obj = self._get_obj(pk)
        except ReportExportTemplate.DoesNotExist:
            return Response({'detail': '模板不存在'}, status=status.HTTP_404_NOT_FOUND)
        if obj.owner_id != request.user.id and not user_level_at_least(request.user, 5):
            return Response({'detail': '无权限编辑模板'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ReportExportTemplateSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        try:
            obj = self._get_obj(pk)
        except ReportExportTemplate.DoesNotExist:
            return Response({'detail': '模板不存在'}, status=status.HTTP_404_NOT_FOUND)
        if obj.owner_id != request.user.id and not user_level_at_least(request.user, 5):
            return Response({'detail': '无权限删除模板'}, status=status.HTTP_403_FORBIDDEN)
        obj.is_active = False
        obj.save(update_fields=['is_active', 'updated_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReportExportMappingListCreateAPIView(APIView):
    """GET/POST 导出映射配置列表与创建。"""
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def get(self, request):
        if not user_level_at_least(request.user, 2):
            return Response({'detail': '无权限查看映射'}, status=status.HTTP_403_FORBIDDEN)
        project_id = _to_int(request.query_params.get('project_id'))
        qs = ReportExportMapping.objects.select_related('template').all()
        if project_id:
            qs = qs.filter(Q(project_id=project_id) | Q(project_id__isnull=True))
        if user_level_at_least(request.user, 3):
            qs = qs.filter(Q(owner=request.user) | Q(is_default=True))
        else:
            qs = qs.filter(owner=request.user)
        return Response(ReportExportMappingSerializer(qs, many=True).data)

    def post(self, request):
        if not user_level_at_least(request.user, 2):
            return Response({'detail': '无权限创建映射'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ReportExportMappingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(owner=request.user)
        if obj.is_default:
            ReportExportMapping.objects.filter(owner=request.user, output_format=obj.output_format).exclude(pk=obj.pk).update(is_default=False)
        return Response(ReportExportMappingSerializer(obj).data, status=status.HTTP_201_CREATED)


class ReportExportMappingDetailAPIView(APIView):
    """GET/PATCH/DELETE 单个导出映射配置。"""
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def _get_obj(self, pk):
        return ReportExportMapping.objects.select_related('template').get(pk=pk)

    def get(self, request, pk):
        try:
            obj = self._get_obj(pk)
        except ReportExportMapping.DoesNotExist:
            return Response({'detail': '映射不存在'}, status=status.HTTP_404_NOT_FOUND)
        if obj.owner_id != request.user.id and not user_level_at_least(request.user, 3):
            return Response({'detail': '无权限查看映射'}, status=status.HTTP_403_FORBIDDEN)
        return Response(ReportExportMappingSerializer(obj).data)

    def patch(self, request, pk):
        try:
            obj = self._get_obj(pk)
        except ReportExportMapping.DoesNotExist:
            return Response({'detail': '映射不存在'}, status=status.HTTP_404_NOT_FOUND)
        if obj.owner_id != request.user.id and not user_level_at_least(request.user, 5):
            return Response({'detail': '无权限编辑映射'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ReportExportMappingSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        if obj.is_default:
            ReportExportMapping.objects.filter(owner=obj.owner, output_format=obj.output_format).exclude(pk=obj.pk).update(is_default=False)
        return Response(ReportExportMappingSerializer(obj).data)

    def delete(self, request, pk):
        try:
            obj = self._get_obj(pk)
        except ReportExportMapping.DoesNotExist:
            return Response({'detail': '映射不存在'}, status=status.HTTP_404_NOT_FOUND)
        if obj.owner_id != request.user.id and not user_level_at_least(request.user, 5):
            return Response({'detail': '无权限删除映射'}, status=status.HTTP_403_FORBIDDEN)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReportStudentSubmissionDetailAPIView(APIView):
    """GET /api/v1/report/student/submissions/<id>/detail/ 学生端模块化成绩详情。"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            submission = StudentSubmission.objects.select_related('project', 'user').get(pk=pk)
        except StudentSubmission.DoesNotExist:
            return Response({'detail': '提交不存在'}, status=status.HTTP_404_NOT_FOUND)
        if submission.user_id != request.user.id:
            return Response({'detail': '无权限查看该成绩详情'}, status=status.HTTP_403_FORBIDDEN)

        indicators = _report_leaf_indicators(submission.project)
        indicator_ids = [ind.id for ind in indicators]

        answer_map = {
            ans.indicator_id: ans
            for ans in submission.answers.filter(indicator_id__in=indicator_ids)
        }
        arbitration_map = {
            row['indicator_id']: row['score']
            for row in ArbitrationRecord.objects.filter(
                submission=submission, indicator_id__in=indicator_ids
            ).values('indicator_id', 'score')
        }
        imported_score_map = {
            row['indicator_id']: row['score']
            for row in ImportedScoreDetail.objects.filter(
                submission=submission, indicator_id__in=indicator_ids
            ).values('indicator_id', 'score')
        }
        review_score_raw = {}
        for row in (
            ScoreRecord.objects.filter(submission=submission, indicator_id__in=indicator_ids)
            .exclude(round_type=3)
            .values('indicator_id', 'score', 'round_type')
            .order_by('indicator_id', '-round_type', '-id')
        ):
            iid = row['indicator_id']
            if iid not in review_score_raw:
                review_score_raw[iid] = row['score']

        score_records_raw = list(
            ScoreRecord.objects.filter(submission=submission, indicator_id__in=indicator_ids)
            .select_related('reviewer')
            .order_by('indicator_id', 'created_at', 'id')
        )
        score_record_rows = []
        for row in score_records_raw:
            score_record_rows.append({
                'id': row.id,
                'submission': row.submission_id,
                'indicator_id': row.indicator_id,
                'reviewer': row.reviewer_id,
                'reviewer_name': _display_user_name(row.reviewer),
                'score': str(row.score),
                'round_type': row.round_type,
                'score_channel': row.score_channel,
                'created_at': row.created_at,
            })
        _attach_logical_round_fields(score_record_rows)
        score_records_by_indicator = {}
        for row in score_record_rows:
            score_records_by_indicator.setdefault(row['indicator_id'], []).append({
                'logical_round_label': row.get('logical_round_label') or '',
                'score': row['score'],
                'reviewer_name': row.get('reviewer_name') or '',
                'score_channel': row.get('score_channel') or '',
                'created_at': row.get('created_at'),
            })

        imported_details = (
            ImportedScoreDetail.objects.filter(submission=submission, indicator_id__in=indicator_ids)
            .select_related('batch__uploaded_by')
            .order_by('indicator_id', 'created_at', 'id')
        )
        for detail in imported_details:
            uploader_name = _display_user_name(detail.batch.uploaded_by if detail.batch_id else None)
            score_records_by_indicator.setdefault(detail.indicator_id, []).append({
                'logical_round_label': '导入',
                'score': str(detail.score),
                'reviewer_name': uploader_name,
                'score_channel': 'import',
                'created_at': detail.created_at,
            })

        arbitration_details = (
            ArbitrationRecord.objects.filter(submission=submission, indicator_id__in=indicator_ids)
            .select_related('arbitrator')
            .order_by('indicator_id', 'created_at', 'id')
        )
        for record in arbitration_details:
            rows = score_records_by_indicator.setdefault(record.indicator_id, [])
            has_arbitration = any(item.get('logical_round_label') == '仲裁' for item in rows)
            if has_arbitration:
                continue
            rows.append({
                'logical_round_label': '仲裁',
                'score': str(record.score),
                'reviewer_name': _display_user_name(record.arbitrator),
                'score_channel': 'arbitration',
                'created_at': record.created_at,
            })

        evidences = Evidence.objects.filter(submission=submission, is_deleted=False).order_by('indicator_id', 'id')
        evidence_by_indicator = {}
        global_evidences = []
        for ev in evidences:
            ev_data = {
                'id': ev.id,
                'name': ev.name or '',
                'file': ev.file.url if ev.file else '',
                'category': ev.category or '',
                'indicator_id': ev.indicator_id,
            }
            if ev.indicator_id:
                evidence_by_indicator.setdefault(ev.indicator_id, []).append(ev_data)
            else:
                global_evidences.append(ev_data)

        items = []
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

            imported_score = None
            reviewer_score = None
            arbitration_score = arbitration_map.get(ind.id)
            if ind.score_source == 'import':
                raw = imported_score_map.get(ind.id)
                imported_score = str(raw) if raw is not None else None
            if ind.score_source == 'reviewer':
                raw = arbitration_score if arbitration_score is not None else review_score_raw.get(ind.id)
                reviewer_score = str(raw) if raw is not None else None

            final_leaf_score = get_indicator_final_score(submission, ind)
            items.append({
                'indicator_id': ind.id,
                'indicator_name': ind.name,
                'score_source': ind.score_source,
                'is_record_only': bool(ind.is_record_only),
                'section_name': section_name,
                'subsection_name': subsection_name,
                'max_score': str(_raw_max_score(ind)) if _raw_max_score(ind) is not None else None,
                'self_score': str(ans.self_score) if ans and ans.self_score is not None else None,
                'imported_score': imported_score,
                'reviewer_score': reviewer_score,
                'arbitration_score': str(arbitration_score) if arbitration_score is not None else None,
                'final_adopted_score': str(final_leaf_score) if final_leaf_score is not None else None,
                'is_arbitrated': arbitration_score is not None,
                'score_records': score_records_by_indicator.get(ind.id, []),
                'evidences': evidence_by_indicator.get(ind.id, []),
                'order': ind.order,
                # 仅用于稳定排序：按树节点 order + id，而非按名称字典序
                '_root_order': root.order if root else 0,
                '_root_id': root.id if root else 0,
                '_sub_order': parent.order if grandparent else 0,
                '_sub_id': parent.id if grandparent else 0,
            })

        items.sort(key=lambda q: (q['_root_order'], q['_root_id'], q['_sub_order'], q['_sub_id'], q['order'], q['indicator_id']))
        for item in items:
            item.pop('_root_order', None)
            item.pop('_root_id', None)
            item.pop('_sub_order', None)
            item.pop('_sub_id', None)
        return Response({
            'submission': StudentSubmissionSerializer(submission).data,
            'final_score': float(submission.final_score) if submission.final_score is not None else None,
            'global_evidences': global_evidences,
            'items': items,
        })
