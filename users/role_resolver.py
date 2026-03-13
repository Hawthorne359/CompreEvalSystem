"""
角色解析工具：统一管理 level 常量、角色查询与动态名称映射。
"""
from django.core.cache import cache

from .models import Role

ROLE_LEVEL_STUDENT = 0
ROLE_LEVEL_ASSISTANT = 1
ROLE_LEVEL_COUNSELOR = 2
ROLE_LEVEL_DIRECTOR = 3
ROLE_LEVEL_SUPERADMIN = 5

ROLE_NAME_CACHE_KEY = 'users:role_name_map_by_level'
ROLE_NAME_CACHE_TTL = 60


def get_role_name_map_by_level():
    """
    获取 level->角色名称映射（短缓存）。
    同一 level 若存在多条角色，取 id 最小的一条作为展示名。
    """
    cached = cache.get(ROLE_NAME_CACHE_KEY)
    if cached:
        return cached
    result = {}
    for role in Role.objects.all().order_by('level', 'id'):
        result.setdefault(role.level, role.name)
    cache.set(ROLE_NAME_CACHE_KEY, result, ROLE_NAME_CACHE_TTL)
    return result


def get_role_display_name(level, default=''):
    """
    按 level 获取当前角色名称（动态来自角色表）。
    """
    name = get_role_name_map_by_level().get(level)
    if name:
        return name
    if default:
        return default
    return f'等级{level}角色'


def get_role_by_level(level):
    """
    获取某 level 的角色对象（优先 id 最小项）。
    """
    return Role.objects.filter(level=level).order_by('id').first()


def clear_role_name_cache():
    """
    清理角色名称缓存。
    """
    cache.delete(ROLE_NAME_CACHE_KEY)
