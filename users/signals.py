"""
用户角色层级：分配某角色时，自动为该用户补全「该角色 level 及以下」的所有身份，
便于前端角色切换。不写死角色 code，角色名与层级均在后台可改。
"""
import logging

from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import User, Role, UserRole
from .role_resolver import clear_role_name_cache

logger = logging.getLogger(__name__)


def ensure_user_has_roles_up_to_level(user, role):
    """
    使用户拥有「该 role 及其以下层级」的全部身份（用于角色切换）。
    role 为 None 或 role.level 为 None 时不做处理。
    """
    if not role or role.level is None:
        return
    roles = Role.objects.filter(level__lte=role.level).order_by('level')
    for r in roles:
        UserRole.objects.get_or_create(
            user=user,
            role=r,
            scope_id=None,
            scope_type='',
            defaults={},
        )


@receiver(post_save, sender=User)
def ensure_roles_on_user_save(sender, instance, **kwargs):
    """
    用户保存后：若设置了 current_role，则为其补全该 level 及以下全部 UserRole。
    """
    if instance.current_role_id:
        ensure_user_has_roles_up_to_level(instance, instance.current_role)


@receiver(post_save, sender=UserRole)
def ensure_roles_on_user_role_save(sender, instance, **kwargs):
    """
    新增/保存 UserRole 后：为该用户补全该角色 level 及以下全部 UserRole。
    （例如在后台只加了一条「管理员」，会自动带上学生、辅导员等下级身份。）
    """
    if instance.role_id:
        ensure_user_has_roles_up_to_level(instance.user, instance.role)


@receiver(post_save, sender=UserRole)
def auto_assign_orphan_submissions(sender, instance, created, **kwargs):
    """
    新增「班级级别的评审角色 (level >= 2)」后，自动为该班级内
    尚未分配评审任务的孤立提交触发分配。
    解决先有学生提交、后导入评审老师/院系主任的场景。
    使用 on_commit 确保 UserRole 记录已持久化后再执行分配。
    """
    if not created:
        return
    if instance.scope_type != 'class' or not instance.scope_id:
        return
    role = instance.role
    if not role or role.level is None or role.level < 2:
        return

    class_id = instance.scope_id

    def _do_assign():
        from submission.models import StudentSubmission
        from scoring.assignment_services import auto_assign_submission

        orphan_subs = (
            StudentSubmission.objects
            .filter(
                user__class_obj_id=class_id,
                status__in=['submitted', 'under_review'],
            )
            .exclude(via_late_channel=True, status='submitted')
            .select_related('project', 'user', 'user__class_obj')
        )

        assigned_count = 0
        for sub in orphan_subs:
            try:
                result = auto_assign_submission(sub)
                if result.get('created'):
                    assigned_count += 1
            except Exception:
                logger.exception('Auto-assign failed for submission %s', sub.id)

        if assigned_count:
            logger.info(
                'Auto-assigned %d orphan submission(s) for class_id=%s',
                assigned_count, class_id,
            )
            try:
                from realtime.registry import broadcast
                broadcast({'type': 'data_changed', 'model': 'submission'})
            except Exception:
                pass

    transaction.on_commit(_do_assign)


@receiver(post_save, sender=Role)
def clear_role_cache_on_role_save(sender, instance, **kwargs):
    """角色新增/修改后，清理角色名称映射缓存。"""
    clear_role_name_cache()


@receiver(post_delete, sender=Role)
def clear_role_cache_on_role_delete(sender, instance, **kwargs):
    """角色删除后，清理角色名称映射缓存。"""
    clear_role_name_cache()
