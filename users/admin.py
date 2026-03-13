"""
用户与角色 Django Admin 配置。
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, UserRole, ImportedUserBatch


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """用户管理。"""
    list_display = ['username', 'full_name_display', 'email', 'student_no', 'employee_no', 'department', 'class_obj', 'current_role', 'is_active']
    list_filter = ['is_active', 'current_role', 'department']
    search_fields = ['username', 'name', 'email', 'student_no', 'employee_no']
    ordering = ['username']

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('name', 'email')}),
        ('扩展信息', {
            'fields': ('phone', 'employee_no', 'student_no', 'gender', 'department', 'class_obj', 'current_role'),
        }),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('重要日期', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('username', 'password1', 'password2', 'name')}),
        ('扩展信息', {
            'fields': ('phone', 'employee_no', 'student_no', 'department', 'class_obj', 'current_role'),
        }),
    )

    def full_name_display(self, obj):
        """显示姓名。"""
        return obj.name or '—'
    full_name_display.short_description = '姓名'


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """角色管理。"""
    list_display = ['code', 'name', 'level', 'description', 'is_active_display']
    list_editable = ['name', 'level']
    search_fields = ['code', 'name']
    ordering = ['level', 'id']

    def is_active_display(self, obj):
        """是否启用。"""
        status = getattr(obj, 'is_active', True)
        return '启用' if status else '禁用'
    is_active_display.short_description = '状态'


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """用户角色关联管理。"""
    list_display = ['user', 'role', 'scope_type', 'scope_id', 'is_primary']
    list_filter = ['role', 'scope_type', 'is_primary']
    search_fields = ['user__username', 'role__name']
    raw_id_fields = ['user',]


@admin.register(ImportedUserBatch)
class ImportedUserBatchAdmin(admin.ModelAdmin):
    """批量导入用户批次管理。"""
    list_display = ['id', 'file_name', 'status', 'row_count', 'success_count', 'created_at']
    list_filter = ['status']
    search_fields = ['file_name']
    readonly_fields = ['file_name', 'row_count', 'success_count', 'error_log', 'created_at']
