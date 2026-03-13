"""
⚠️  历史数据迁移工具 — 请勿定期执行，请勿在生产环境自动化调用！

用途：一次性补全「已拥有最高层级角色」的用户缺失的下级角色身份。
适用场景：系统首个超级管理员在数据库中直接创建（未走应用层保存流程），
         导致其 user_roles 未自动补全的情况。

⚠️  风险提示：若使用 --username 参数指定任意普通用户，
    该命令将把该用户提权至其当前最高角色以下的全部身份，请谨慎操作。

正常流程：新建/分配角色由 users/signals.py 信号自动处理，无需再运行本命令。
"""
from django.core.management.base import BaseCommand
from django.db.models import Max
from users.models import Role, User, UserRole


def ensure_user_has_roles_up_to_level(user, role):
    """使用户拥有该 role 及以下层级的全部身份。"""
    if not role or role.level is None:
        return
    for r in Role.objects.filter(level__lte=role.level).order_by('level'):
        UserRole.objects.get_or_create(
            user=user,
            role=r,
            scope_id=None,
            scope_type='',
            defaults={},
        )


class Command(BaseCommand):
    help = '为已拥有最高层级角色的用户补全全部下级身份（仅首次/历史数据用）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default=None,
            help='仅处理指定用户名的用户',
        )

    def handle(self, *args, **options):
        max_level = Role.objects.aggregate(m=Max('level'))['m']
        if max_level is None:
            self.stdout.write(self.style.WARNING('尚未创建任何角色，请先执行 init_roles'))
            return

        if options.get('username'):
            users = User.objects.filter(username=options['username'])
            if not users.exists():
                self.stdout.write(self.style.WARNING(f'未找到用户: {options["username"]}'))
                return
        else:
            # 拥有最高 level 角色的用户（current_role 或 user_roles）
            top_role = Role.objects.filter(level=max_level).first()
            if not top_role:
                self.stdout.write(self.style.WARNING('未找到最高层级角色'))
                return
            user_ids = set(
                UserRole.objects.filter(role=top_role).values_list('user_id', flat=True)
            )
            user_ids |= set(
                User.objects.filter(current_role=top_role).values_list('id', flat=True)
            )
            users = User.objects.filter(id__in=user_ids)

        for user in users:
            # 该用户当前最高 level（来自 current_role 或 user_roles）
            role_ids = set(UserRole.objects.filter(user=user).values_list('role_id', flat=True))
            if user.current_role_id:
                role_ids.add(user.current_role_id)
            if not role_ids:
                continue
            top = Role.objects.filter(id__in=role_ids).order_by('-level').first()
            if not top:
                continue
            ensure_user_has_roles_up_to_level(user, top)
            self.stdout.write(self.style.SUCCESS(f'已补全用户 {user.username} 的身份（level<={top.level}）'))

        self.stdout.write(self.style.SUCCESS('处理完成'))
