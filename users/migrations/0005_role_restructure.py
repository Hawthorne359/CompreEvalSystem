"""
角色体系重构数据迁移（Phase 1）。

操作顺序（先加后删，保证安全）：
1. 创建 student_assistant 角色（LV1，新增）
2. 将 counselor（旧 LV1）升级到 LV2 并重命名为「评审老师（辅导员）」
3. 将所有持有 reviewer（旧 LV2）的 UserRole 改为持有 counselor（新 LV2）
4. 将 current_role 是 reviewer 的用户改为 counselor
5. 删除 reviewer 角色
6. 将所有持有 admin（LV4）的 UserRole 改为持有 superadmin（LV5）
7. 将 current_role 是 admin 的用户改为 superadmin
8. 删除 admin 角色
"""
from django.db import migrations


def restructure_roles(apps, schema_editor):
    Role = apps.get_model('users', 'Role')
    UserRole = apps.get_model('users', 'UserRole')
    User = apps.get_model('users', 'User')

    # ------------------------------------------------------------------ #
    # Step 1: 创建 student_assistant 角色（LV1）                          #
    # ------------------------------------------------------------------ #
    Role.objects.get_or_create(
        code='student_assistant',
        defaults={
            'name': '学生助理（评卷助理）',
            'level': 1,
            'description': '由辅导员从本班学生中指派，协助参与评卷工作',
        },
    )

    # ------------------------------------------------------------------ #
    # Step 2: 将 counselor（旧 LV1）升级到 LV2，重命名                   #
    # ------------------------------------------------------------------ #
    counselor = Role.objects.filter(code='counselor').first()
    if counselor:
        counselor.level = 2
        counselor.name = '评审老师（辅导员）'
        counselor.description = '负责本班/本年级测评审核、申诉处理及双评确认；可指派学生担任助理'
        counselor.save()

    # ------------------------------------------------------------------ #
    # Step 3: 将 reviewer（旧 LV2）UserRole 迁移到 counselor（新 LV2）   #
    # ------------------------------------------------------------------ #
    reviewer = Role.objects.filter(code='reviewer').first()
    if reviewer and counselor:
        for ur in UserRole.objects.filter(role=reviewer):
            # 若该用户已有 counselor 角色记录，直接删除旧 reviewer 记录
            exists = UserRole.objects.filter(
                user_id=ur.user_id,
                role=counselor,
                scope_id=ur.scope_id,
                scope_type=ur.scope_type,
            ).exists()
            if exists:
                ur.delete()
            else:
                ur.role = counselor
                ur.save(update_fields=['role'])

    # ------------------------------------------------------------------ #
    # Step 4: 将 current_role 是 reviewer 的用户改为 counselor            #
    # ------------------------------------------------------------------ #
    if reviewer and counselor:
        User.objects.filter(current_role=reviewer).update(current_role=counselor)

    # ------------------------------------------------------------------ #
    # Step 5: 删除 reviewer 角色                                          #
    # ------------------------------------------------------------------ #
    if reviewer:
        reviewer.delete()

    # ------------------------------------------------------------------ #
    # Step 6: 将 admin（LV4）UserRole 迁移到 superadmin（LV5）           #
    # ------------------------------------------------------------------ #
    admin_role = Role.objects.filter(code='admin').first()
    superadmin = Role.objects.filter(code='superadmin').first()
    if admin_role and superadmin:
        for ur in UserRole.objects.filter(role=admin_role):
            exists = UserRole.objects.filter(
                user_id=ur.user_id,
                role=superadmin,
                scope_id=ur.scope_id,
                scope_type=ur.scope_type,
            ).exists()
            if exists:
                ur.delete()
            else:
                ur.role = superadmin
                ur.save(update_fields=['role'])

    # ------------------------------------------------------------------ #
    # Step 7: 将 current_role 是 admin 的用户改为 superadmin              #
    # ------------------------------------------------------------------ #
    if admin_role and superadmin:
        User.objects.filter(current_role=admin_role).update(current_role=superadmin)

    # ------------------------------------------------------------------ #
    # Step 8: 删除 admin 角色                                             #
    # ------------------------------------------------------------------ #
    if admin_role:
        admin_role.delete()


def reverse_restructure(apps, schema_editor):
    """回滚：仅作提示，实际回滚需手动处理数据。"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_importeduserbatch'),
    ]

    operations = [
        migrations.RunPython(restructure_roles, reverse_code=reverse_restructure),
    ]
