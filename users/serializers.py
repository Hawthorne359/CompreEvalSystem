"""
用户与角色序列化器。
"""
from rest_framework import serializers
from .models import User, Role, UserRole, ImportedUserBatch
from org.models import Class as ClassModel
from .role_resolver import ROLE_LEVEL_STUDENT, ROLE_LEVEL_ASSISTANT, ROLE_LEVEL_DIRECTOR, ROLE_LEVEL_SUPERADMIN


class RoleSerializer(serializers.ModelSerializer):
    """角色简要信息（name/level 可在后台修改）。"""

    class Meta:
        model = Role
        fields = ['id', 'code', 'name', 'level', 'description']


class UserRoleSerializer(serializers.ModelSerializer):
    """用户-角色关联（含角色信息）。"""
    role = RoleSerializer(read_only=True)

    class Meta:
        model = UserRole
        fields = ['id', 'role', 'scope_id', 'scope_type', 'is_primary']


class UserSerializer(serializers.ModelSerializer):
    """用户详情（含角色列表与当前角色、负责班级；班级对应的专业/年级供编辑回填）。"""
    user_roles = UserRoleSerializer(many=True, read_only=True)
    current_role = RoleSerializer(read_only=True, allow_null=True)
    department_name = serializers.CharField(source='department.name', read_only=True, allow_null=True)
    class_name = serializers.CharField(source='class_obj.name', read_only=True, allow_null=True)
    class_grade = serializers.CharField(source='class_obj.grade', read_only=True, allow_null=True)
    gender_label = serializers.SerializerMethodField()
    class_major = serializers.PrimaryKeyRelatedField(
        source='class_obj.major', read_only=True, allow_null=True
    )
    responsible_class_ids = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'name',
            'phone', 'employee_no', 'student_no', 'gender', 'gender_label',
            'department', 'department_name', 'class_obj', 'class_name', 'class_grade', 'class_major',
            'current_role', 'is_active', 'must_change_password',
            'user_roles', 'responsible_class_ids',
            'date_joined', 'last_login',
        ]
        read_only_fields = ['username', 'date_joined', 'last_login']

    def get_gender_label(self, obj):
        """性别中文标签。"""
        return obj.get_gender_display() if obj.gender else '未知'

    def get_responsible_class_ids(self, obj):
        """非学生角色的「负责班级」：取最高级角色下 scope_type='class' 的 scope_id 列表。"""
        top_ur = (
            obj.user_roles.select_related('role')
            .order_by('-role__level')
            .first()
        )
        if not top_ur or not top_ur.role_id:
            return []
        return list(
            obj.user_roles.filter(role=top_ur.role, scope_type='class', scope_id__isnull=False)
            .values_list('scope_id', flat=True)
        )


class UserListSerializer(serializers.ModelSerializer):
    """用户列表（精简）。含 last_login、角色、班级对应专业/年级、非学生负责班级摘要。"""
    department_name = serializers.CharField(source='department.name', read_only=True, allow_null=True)
    class_name = serializers.CharField(source='class_obj.name', read_only=True, allow_null=True)
    class_grade = serializers.CharField(source='class_obj.grade', read_only=True, allow_null=True)
    class_major_name = serializers.CharField(source='class_obj.major.name', read_only=True, allow_null=True)
    gender_label = serializers.SerializerMethodField()
    role_names = serializers.SerializerMethodField()
    responsible_classes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'name',
            'phone', 'employee_no', 'student_no', 'gender', 'gender_label',
            'department', 'department_name', 'class_obj', 'class_name', 'class_grade', 'class_major_name',
            'is_active', 'last_login', 'role_names', 'responsible_classes',
        ]

    def get_gender_label(self, obj):
        """性别中文标签。"""
        return obj.get_gender_display() if obj.gender else '未知'

    def get_role_names(self, obj):
        """返回该用户最高级角色名称；利用预取缓存避免 N+1。"""
        all_urs = [ur for ur in obj.user_roles.all() if ur.role_id]
        if not all_urs:
            return []
        top_ur = max(all_urs, key=lambda ur: (ur.role.level if ur.role else 0))
        return [top_ur.role.name] if top_ur.role else []

    def get_responsible_classes(self, obj):
        """非学生用户的负责班级摘要列表；学生（有 class_obj）返回空。

        返回格式：[{id, name, grade, major_name}, ...]
        """
        # 学生用户不展示负责班级
        if obj.class_obj_id:
            return []
        all_urs = [ur for ur in obj.user_roles.all() if ur.role_id and ur.role]
        if not all_urs:
            return []
        top_role = max(all_urs, key=lambda ur: ur.role.level).role
        # 学生角色同样不展示
        if (top_role.level if top_role else -1) == ROLE_LEVEL_STUDENT:
            return []
        class_ids = [
            ur.scope_id
            for ur in obj.user_roles.all()
            if ur.role_id == top_role.id and ur.scope_type == 'class' and ur.scope_id
        ]
        if not class_ids:
            return []
        classes = ClassModel.objects.filter(id__in=class_ids).select_related('major')
        return [
            {
                'id': c.id,
                'name': c.name,
                'grade': c.grade or '',
                'major_name': c.major.name if c.major else '',
            }
            for c in classes
        ]


class UserCreateUpdateSerializer(serializers.ModelSerializer):
    """创建/更新用户；支持 role_ids、responsible_class_ids（非学生角色负责的多个班级）。"""
    password = serializers.CharField(write_only=True, required=False)
    role_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        write_only=True,
        help_text='角色 id 列表（单选时为单元素）；不含 superadmin。',
    )
    responsible_class_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        write_only=True,
        help_text='非学生角色时生效：负责的班级 id 列表，可多选。',
    )

    class Meta:
        model = User
        fields = [
            'username', 'password', 'email', 'name',
            'phone', 'employee_no', 'student_no', 'gender',
            'department', 'class_obj', 'is_active', 'role_ids', 'responsible_class_ids',
        ]

    def _allowed_role_ids(self, role_ids):
        """过滤掉 superadmin，仅允许分配其下角色。"""
        if not role_ids:
            return []
        allowed = set(
            Role.objects.filter(level__lt=ROLE_LEVEL_SUPERADMIN, id__in=role_ids).values_list('id', flat=True)
        )
        return [i for i in role_ids if i in allowed]

    def _sync_user_roles(self, user, role_ids, responsible_class_ids=None):
        """同步 UserRole：角色身份 + 非学生时同步「负责班级」scope。"""
        role_ids = self._allowed_role_ids(role_ids)
        user.user_roles.exclude(role_id__in=role_ids).delete()
        for rid in role_ids:
            UserRole.objects.get_or_create(
                user=user, role_id=rid, scope_id=None, scope_type='', defaults={}
            )
        top = Role.objects.filter(id__in=role_ids).order_by('-level').first() if role_ids else None
        if top:
            user.current_role = top
            user.save(update_fields=['current_role'])
        # 非学生角色：同步「负责班级」UserRole(scope_type='class', scope_id=class_id)
        if top and top.level != ROLE_LEVEL_STUDENT and responsible_class_ids is not None:
            if top.level == ROLE_LEVEL_ASSISTANT:
                responsible_class_ids = [user.class_obj_id] if user.class_obj_id else []
            user.user_roles.filter(role=top, scope_type='class').delete()
            for cid in responsible_class_ids:
                if cid:
                    UserRole.objects.get_or_create(
                        user=user, role=top, scope_id=cid, scope_type='class', defaults={}
                    )
            if top.level >= ROLE_LEVEL_DIRECTOR and user.department_id:
                user.user_roles.filter(role=top, scope_type='department').delete()
                UserRole.objects.get_or_create(
                    user=user, role=top,
                    scope_id=user.department_id, scope_type='department',
                )

    def create(self, validated_data):
        role_ids = validated_data.pop('role_ids', None)
        responsible_class_ids = validated_data.pop('responsible_class_ids', None)
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        if role_ids is not None:
            self._sync_user_roles(user, role_ids, responsible_class_ids)
        return user

    def update(self, instance, validated_data):
        role_ids = validated_data.pop('role_ids', None)
        responsible_class_ids = validated_data.pop('responsible_class_ids', None)
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        if role_ids is not None:
            self._sync_user_roles(instance, role_ids, responsible_class_ids)
        return instance


class ImportedUserBatchSerializer(serializers.ModelSerializer):
    """批量导入用户批次序列化器。"""

    class Meta:
        model = ImportedUserBatch
        fields = [
            'id', 'file_name', 'status', 'row_count', 'current_count',
            'success_count', 'error_log', 'warning_log',
            'hash_iterations', 'created_at',
        ]
