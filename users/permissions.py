"""
RBAC 权限：基于 role.level 数字等级判断，不硬绑定角色 code 名称。
等级约定（可在后台调整）：
  LV0=学生  LV1=学生助理  LV2=评审老师（辅导员）  LV3=院系主任  LV5=超级管理员
"""
from rest_framework.permissions import BasePermission

from .role_resolver import (
    ROLE_LEVEL_SUPERADMIN,
)

def get_user_level(user):
    """
    返回用户当前角色等级，未登录或无角色返回 -1。
    优先读 current_role.level，其次读 user_roles 中最高的 level。
    """
    if not user or not user.is_authenticated:
        return -1
    if user.current_role and user.current_role.level is not None:
        return user.current_role.level
    # 回退：取用户所有角色中最高级
    from django.db.models import Max
    max_level = user.user_roles.select_related('role').aggregate(max_level=Max('role__level'))['max_level']
    return max_level if max_level is not None else -1


def user_level_at_least(user, level):
    """
    判断用户当前角色等级是否 >= 指定 level。
    用于替代写死 code 字符串的权限判断，角色改名后依然生效。
    """
    return get_user_level(user) >= level


def user_is_admin(user):
    """
    是否为超级管理员（level >= 5）。
    原 LV4 管理员角色已移除，此函数保留名称以兼容现有调用点，实际等同于 user_is_super_admin。
    """
    return user_level_at_least(user, ROLE_LEVEL_SUPERADMIN)


def user_is_super_admin(user):
    """是否为超级管理员（level >= 5）。"""
    return user_level_at_least(user, ROLE_LEVEL_SUPERADMIN)


def user_has_role(user, role_code):
    """
    判断用户是否拥有某角色（通过 code 字符串）。
    保留此函数作向后兼容，新代码请优先使用 user_level_at_least。
    """
    if not user or not user.is_authenticated:
        return False
    if user.current_role and user.current_role.code == role_code:
        return True
    return user.user_roles.filter(role__code=role_code).exists()


class IsAdminOrReadOnly(BasePermission):
    """
    GET / HEAD / OPTIONS 所有认证用户均可访问；
    POST / PUT / PATCH / DELETE 仅超级管理员（level >= 5）。
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return user_is_admin(request.user)


class IsAdminOrReadSelf(BasePermission):
    """
    列表/创建/删除仅超级管理员（level >= 5）；本人可读自己的详情。
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if view.action in ('list', 'create', 'destroy'):
            return user_is_admin(request.user)
        return True

    def has_object_permission(self, request, view, obj):
        if user_is_admin(request.user):
            return True
        if view.action in ('retrieve', 'update', 'partial_update'):
            return obj == request.user
        return False
