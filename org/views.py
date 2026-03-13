"""
组织架构 API：院系、专业、班级；辅导员负责班级下的学生（扩展用）。
"""
from django.db import transaction
from rest_framework import generics
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.models import OperationLog
from audit.services import log_action
from users.permissions import user_is_admin, IsAdminOrReadOnly

from users.role_resolver import ROLE_LEVEL_SUPERADMIN, get_role_display_name
from .models import Department, Major, Class
from .serializers import DepartmentSerializer, DepartmentTreeSerializer, MajorSerializer, ClassSerializer, ClassWithStudentsSerializer


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


# ---------------------------------------------------------------------------
# 辅导员/主任等「负责班级」下的学生列表
# ---------------------------------------------------------------------------
class ResponsibleClassStudentsAPIView(APIView):
    """GET /api/v1/responsible-class-students/?user_id=<id> 某用户负责的班级下的学生列表。"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.contrib.auth import get_user_model
        from users.models import UserRole
        from users.serializers import UserListSerializer

        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'detail': '请提供 user_id，例如 ?user_id=1'},
                status=400,
            )
        try:
            User = get_user_model()
            target_user = User.objects.get(pk=user_id)
        except (ValueError, User.DoesNotExist):
            return Response({'detail': '用户不存在'}, status=404)
        if not user_is_admin(request.user) and request.user.id != int(user_id):
            return Response({'detail': '无权限查看该用户负责的学生'}, status=403)

        class_ids = list(
            UserRole.objects.filter(
                user=target_user,
                scope_type='class',
                scope_id__isnull=False,
            ).values_list('scope_id', flat=True).distinct()
        )
        if not class_ids:
            return Response({
                'user_id': target_user.id,
                'responsible_class_ids': [],
                'students': [],
            })
        students = User.objects.filter(class_obj_id__in=class_ids).order_by('class_obj_id', 'student_no', 'username')
        return Response({
            'user_id': target_user.id,
            'responsible_class_ids': class_ids,
            'students': UserListSerializer(students, many=True).data,
        })


class DepartmentListAPIView(generics.ListCreateAPIView):
    """
    GET  /api/v1/departments/ 院系列表（树形可选 ?tree=1）；
    POST /api/v1/departments/ 新建院系（仅管理员）。
    """
    queryset = Department.objects.filter(parent__isnull=True).order_by('code')
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = DepartmentSerializer
    pagination_class = None

    def get_serializer_class(self):
        if self.request.method == 'GET' and self.request.query_params.get('tree'):
            return DepartmentTreeSerializer
        return DepartmentSerializer

    def get_queryset(self):
        if self.request.query_params.get('tree'):
            return Department.objects.filter(parent__isnull=True).order_by('code')
        return Department.objects.all().order_by('code')


    def perform_create(self, serializer):
        instance = serializer.save()
        log_action(
            user=self.request.user,
            action='dept_create',
            module=OperationLog.MODULE_ORG,
            level=OperationLog.LEVEL_WARNING,
            target_type='department',
            target_id=instance.id,
            target_repr=instance.name,
            request=self.request,
        )


class DepartmentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/departments/<id>/ 院系详情；
    PATCH  /api/v1/departments/<id>/ 更新；
    DELETE /api/v1/departments/<id>/ 删除（仅管理员）。
    """
    queryset = Department.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = DepartmentSerializer

    def perform_update(self, serializer):
        instance = serializer.save()
        log_action(
            user=self.request.user,
            action='dept_update',
            module=OperationLog.MODULE_ORG,
            level=OperationLog.LEVEL_WARNING,
            target_type='department',
            target_id=instance.id,
            target_repr=instance.name,
            request=self.request,
        )

    def perform_destroy(self, instance):
        target_repr = instance.name
        target_id = instance.id
        instance.delete()
        log_action(
            user=self.request.user,
            action='dept_delete',
            module=OperationLog.MODULE_ORG,
            level=OperationLog.LEVEL_CRITICAL,
            target_type='department',
            target_id=target_id,
            target_repr=target_repr,
            is_audit_event=True,
            request=self.request,
        )


class DepartmentBatchDeleteAPIView(APIView):
    """POST /api/v1/departments/batch-delete/ 批量删除院系。"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not user_is_admin(request.user):
            raise PermissionDenied(f'仅{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}可批量删除院系')
        department_ids = _parse_batch_ids(request.data.get('department_ids', []), 'department_ids')
        departments = list(Department.objects.filter(id__in=department_ids))
        if len(departments) != len(department_ids):
            found = {d.id for d in departments}
            missing = [did for did in department_ids if did not in found]
            raise ValidationError({'department_ids': f'部分院系不存在：{missing}'})

        deleted_items = [{'id': d.id, 'name': d.name} for d in departments]
        with transaction.atomic():
            Department.objects.filter(id__in=department_ids).delete()
        log_action(
            user=request.user,
            action='dept_batch_delete',
            module=OperationLog.MODULE_ORG,
            level=OperationLog.LEVEL_CRITICAL,
            target_type='department',
            target_id=0,
            target_repr=f'批量删除院系 x{len(department_ids)}',
            is_audit_event=True,
            extra={'department_ids': department_ids, 'deleted_items': deleted_items},
            request=request,
        )
        return Response({'detail': f'已删除 {len(department_ids)} 个院系'}, status=status.HTTP_200_OK)


class MajorListAPIView(generics.ListCreateAPIView):
    """
    GET  /api/v1/majors/ 专业列表，支持 ?department= 按院系筛选；
    POST /api/v1/majors/ 新建专业（仅管理员）。
    """
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = MajorSerializer
    pagination_class = None

    def get_queryset(self):
        qs = Major.objects.all().select_related('department').order_by('department', 'name')
        dept = self.request.query_params.get('department')
        if dept:
            qs = qs.filter(department_id=dept)
        return qs


    def perform_create(self, serializer):
        instance = serializer.save()
        log_action(
            user=self.request.user,
            action='major_create',
            module=OperationLog.MODULE_ORG,
            level=OperationLog.LEVEL_WARNING,
            target_type='major',
            target_id=instance.id,
            target_repr=instance.name,
            request=self.request,
        )


class MajorDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/majors/<id>/ 专业详情；
    PATCH  /api/v1/majors/<id>/ 更新；
    DELETE /api/v1/majors/<id>/ 删除。
    """
    queryset = Major.objects.all().select_related('department')
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = MajorSerializer

    def perform_update(self, serializer):
        instance = serializer.save()
        log_action(
            user=self.request.user,
            action='major_update',
            module=OperationLog.MODULE_ORG,
            level=OperationLog.LEVEL_WARNING,
            target_type='major',
            target_id=instance.id,
            target_repr=instance.name,
            request=self.request,
        )

    def perform_destroy(self, instance):
        target_repr = instance.name
        target_id = instance.id
        instance.delete()
        log_action(
            user=self.request.user,
            action='major_delete',
            module=OperationLog.MODULE_ORG,
            level=OperationLog.LEVEL_CRITICAL,
            target_type='major',
            target_id=target_id,
            target_repr=target_repr,
            is_audit_event=True,
            request=self.request,
        )


class ClassListAPIView(generics.ListCreateAPIView):
    """
    GET  /api/v1/classes/ 班级列表；
    POST /api/v1/classes/ 新建班级（仅管理员）。
    """
    queryset = Class.objects.all().select_related('department', 'major').order_by('department', 'grade', 'name')
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = ClassSerializer
    pagination_class = None

    def get_queryset(self):
        qs = super().get_queryset()
        dept = self.request.query_params.get('department')
        major = self.request.query_params.get('major')
        grade = self.request.query_params.get('grade')
        if dept:
            qs = qs.filter(department_id=dept)
        if major:
            qs = qs.filter(major_id=major)
        if grade:
            qs = qs.filter(grade=grade)
        return qs


    def perform_create(self, serializer):
        instance = serializer.save()
        log_action(
            user=self.request.user,
            action='class_create',
            module=OperationLog.MODULE_ORG,
            level=OperationLog.LEVEL_WARNING,
            target_type='class',
            target_id=instance.id,
            target_repr=instance.name,
            request=self.request,
        )


class ClassDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/classes/<id>/ 班级详情；
    PATCH  /api/v1/classes/<id>/ 更新；
    DELETE /api/v1/classes/<id>/ 删除。
    """
    queryset = Class.objects.all().select_related('department', 'major')
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = ClassSerializer

    def perform_update(self, serializer):
        instance = serializer.save()
        log_action(
            user=self.request.user,
            action='class_update',
            module=OperationLog.MODULE_ORG,
            level=OperationLog.LEVEL_WARNING,
            target_type='class',
            target_id=instance.id,
            target_repr=instance.name,
            request=self.request,
        )

    def perform_destroy(self, instance):
        target_repr = instance.name
        target_id = instance.id
        instance.delete()
        log_action(
            user=self.request.user,
            action='class_delete',
            module=OperationLog.MODULE_ORG,
            level=OperationLog.LEVEL_CRITICAL,
            target_type='class',
            target_id=target_id,
            target_repr=target_repr,
            is_audit_event=True,
            request=self.request,
        )


class ClassBatchDeleteAPIView(APIView):
    """POST /api/v1/classes/batch-delete/ 批量删除班级。"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not user_is_admin(request.user):
            raise PermissionDenied(f'仅{get_role_display_name(ROLE_LEVEL_SUPERADMIN)}可批量删除班级')
        class_ids = _parse_batch_ids(request.data.get('class_ids', []), 'class_ids')
        classes = list(Class.objects.filter(id__in=class_ids))
        if len(classes) != len(class_ids):
            found = {c.id for c in classes}
            missing = [cid for cid in class_ids if cid not in found]
            raise ValidationError({'class_ids': f'部分班级不存在：{missing}'})

        deleted_items = [{'id': c.id, 'name': c.name} for c in classes]
        with transaction.atomic():
            Class.objects.filter(id__in=class_ids).delete()
        log_action(
            user=request.user,
            action='class_batch_delete',
            module=OperationLog.MODULE_ORG,
            level=OperationLog.LEVEL_CRITICAL,
            target_type='class',
            target_id=0,
            target_repr=f'批量删除班级 x{len(class_ids)}',
            is_audit_event=True,
            extra={'class_ids': class_ids, 'deleted_items': deleted_items},
            request=request,
        )
        return Response({'detail': f'已删除 {len(class_ids)} 个班级'}, status=status.HTTP_200_OK)


class ClassStudentListAPIView(generics.GenericAPIView):
    """GET /api/v1/classes/<id>/students/ 某班学生列表。"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        from django.contrib.auth import get_user_model
        from users.serializers import UserListSerializer

        try:
            cls = Class.objects.get(pk=pk)
        except Class.DoesNotExist:
            return Response({'detail': '班级不存在'}, status=status.HTTP_404_NOT_FOUND)
        if not user_is_admin(request.user) and not self._user_can_access_class(request.user, pk):
            return Response({'detail': '无权限查看该班级'}, status=status.HTTP_403_FORBIDDEN)
        User = get_user_model()
        users = User.objects.filter(class_obj_id=pk).order_by('student_no', 'username')
        return Response({
            'class': ClassSerializer(cls).data,
            'students': UserListSerializer(users, many=True).data,
        })

    def _user_can_access_class(self, user, class_id):
        """评审老师（辅导员）及以上（level>=2）可看自己管辖的班级。"""
        from users.models import UserRole
        from users.permissions import user_level_at_least
        if user.class_obj_id == int(class_id):
            return True
        if user_level_at_least(user, 2):
            return UserRole.objects.filter(
                user=user, role__level__gte=2,
                scope_type='class', scope_id=int(class_id),
            ).exists()
        return False


class DepartmentPersonnelTreeAPIView(APIView):
    """
    GET /api/v1/departments/personnel-tree/
    统一架构树：组织结构（院系→专业→班级）+ 人员信息（系主任、辅导员、学生助理）。
    角色名称从数据库 Role.name 动态获取，不硬编码。
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from users.models import UserRole

        departments = list(Department.objects.order_by('code', 'id'))
        dept_ids = [d.id for d in departments]

        majors = list(Major.objects.filter(department_id__in=dept_ids).order_by('department', 'name'))
        majors_by_dept = {}
        major_ids = []
        for m in majors:
            majors_by_dept.setdefault(m.department_id, []).append(m)
            major_ids.append(m.id)

        classes = list(Class.objects.filter(department_id__in=dept_ids).order_by('grade', 'name'))
        classes_by_major = {}
        class_ids = []
        for c in classes:
            key = c.major_id or f'dept-{c.department_id}'
            classes_by_major.setdefault(key, []).append(c)
            class_ids.append(c.id)

        director_urs_dept = list(UserRole.objects.filter(
            role__level=3, scope_type='department', scope_id__in=dept_ids,
        ).select_related('user', 'role'))

        director_urs_class = list(UserRole.objects.filter(
            role__level=3, scope_type='class', scope_id__in=class_ids,
        ).select_related('user', 'role'))

        director_urs = director_urs_dept

        counselor_urs = list(UserRole.objects.filter(
            role__level=2, scope_type='class', scope_id__in=class_ids,
        ).select_related('user', 'role'))

        assistant_urs = list(UserRole.objects.filter(
            role__level=1, scope_type='class', scope_id__in=class_ids,
        ).select_related('user', 'role'))

        def _person(ur):
            """从 UserRole 构建人员节点，含动态 role_name。"""
            u = ur.user
            name = u.name or u.username
            return {
                'id': u.id,
                'username': u.username,
                'name': name,
                'role_name': ur.role.name if ur.role else '',
            }

        class_to_dept = {c.id: c.department_id for c in classes}

        directors_by_dept = {}
        seen_director_keys = set()
        for ur in director_urs:
            key = (ur.user_id, ur.scope_id)
            if key not in seen_director_keys:
                seen_director_keys.add(key)
                directors_by_dept.setdefault(ur.scope_id, []).append(_person(ur))
        for ur in director_urs_class:
            dept_id = class_to_dept.get(ur.scope_id)
            if dept_id:
                key = (ur.user_id, dept_id)
                if key not in seen_director_keys:
                    seen_director_keys.add(key)
                    directors_by_dept.setdefault(dept_id, []).append(_person(ur))
                    UserRole.objects.get_or_create(
                        user=ur.user, role=ur.role,
                        scope_id=dept_id, scope_type='department',
                    )

        counselors_by_class = {}
        counselor_ur_by_class = {}
        for ur in counselor_urs:
            counselors_by_class.setdefault(ur.scope_id, []).append(_person(ur))
            counselor_ur_by_class.setdefault(ur.scope_id, []).append(ur)

        assistants_by_class = {}
        for ur in assistant_urs:
            assistants_by_class.setdefault(ur.scope_id, []).append(_person(ur))

        def _build_class_node(cls_obj):
            """构建班级节点，含辅导员及其下属助理。"""
            cid = cls_obj.id
            coun_list = counselors_by_class.get(cid, [])
            asst_list = assistants_by_class.get(cid, [])

            counselor_nodes = []
            for coun in coun_list:
                counselor_nodes.append({
                    **coun,
                    'assistants': [
                        {**a, 'class_id': cid, 'class_name': cls_obj.name}
                        for a in asst_list
                    ],
                })
            if not coun_list and asst_list:
                counselor_nodes.append({
                    'id': 0, 'username': '', 'name': '（未指定辅导员）', 'role_name': '',
                    'assistants': [
                        {**a, 'class_id': cid, 'class_name': cls_obj.name}
                        for a in asst_list
                    ],
                })

            return {
                'id': cls_obj.id,
                'name': cls_obj.name,
                'grade': cls_obj.grade,
                'department': cls_obj.department_id,
                'major': cls_obj.major_id,
                'counselors': counselor_nodes,
            }

        result = []
        for dept in departments:
            dept_majors = majors_by_dept.get(dept.id, [])
            major_nodes = []
            for m in dept_majors:
                cls_list = classes_by_major.get(m.id, [])
                major_nodes.append({
                    'id': m.id,
                    'name': m.name,
                    'grades': m.grades or [],
                    'classes': [_build_class_node(c) for c in cls_list],
                })

            result.append({
                'id': dept.id,
                'name': dept.name,
                'code': dept.code,
                'directors': directors_by_dept.get(dept.id, []),
                'majors': major_nodes,
            })

        return Response(result)
