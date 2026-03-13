"""
用户、角色与权限模型（RBAC+）。
"""
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    自定义用户：支持学号/工号、院系、班级等。
    """
    GENDER_UNKNOWN = ''
    GENDER_MALE = 'M'
    GENDER_FEMALE = 'F'
    GENDER_CHOICES = [
        (GENDER_UNKNOWN, '未知'),
        (GENDER_MALE, '男'),
        (GENDER_FEMALE, '女'),
    ]

    name = models.CharField(max_length=150, blank=True, default='', help_text='完整姓名（中文场景不拆分姓/名）')
    phone = models.CharField(max_length=20, blank=True)
    employee_no = models.CharField(max_length=50, blank=True, null=True, unique=True)
    student_no = models.CharField(max_length=50, blank=True, null=True, unique=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, default=GENDER_UNKNOWN)
    department = models.ForeignKey(
        'org.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
    )
    class_obj = models.ForeignKey(
        'org.Class',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        db_column='class_id',
    )
    current_role = models.ForeignKey(
        'Role',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users_current',
    )
    must_change_password = models.BooleanField(
        default=False,
        help_text='首次登录强制修改密码（批量导入用户自动置 True）',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users_user'

    def __str__(self):
        return self.name or self.username

    def get_full_name(self):
        return self.name or self.username

    def get_short_name(self):
        return self.name or self.username


class Role(models.Model):
    """
    角色：name/code 可在后台修改（仅超级管理员 code 固定为 superadmin）。
    level 表示层级，数字越大权限越高；高等级用户自动拥有所有 level 不高于自己的身份，便于前端切换。
    """
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=50, unique=True)
    level = models.PositiveSmallIntegerField(
        default=0,
        help_text='层级，0 最低，数字越大权限越高；分配某角色时自动拥有该 level 及以下所有角色',
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_role'
        ordering = ['level', 'id']

    def __str__(self):
        return self.name


class UserRole(models.Model):
    """用户-角色关联，支持多角色与 scope（如辅导员负责的班级）。"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_roles',
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='user_roles',
    )
    scope_id = models.PositiveIntegerField(null=True, blank=True, help_text='如 class_id 表示辅导员负责的班级')
    scope_type = models.CharField(max_length=50, blank=True, help_text='如 class')
    is_primary = models.BooleanField(default=False, help_text='当前主身份')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_user_role'
        unique_together = [['user', 'role', 'scope_id', 'scope_type']]
        ordering = ['user', 'role']

    def __str__(self):
        return f"{self.user.username} - {self.role.code}"


class ImportedUserBatch(models.Model):
    """批量导入用户批次。"""
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='imported_user_batches',
    )
    file_name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '待处理'),
            ('processing', '处理中'),
            ('completed', '完成'),
            ('failed', '失败'),
        ],
        default='pending',
    )
    row_count = models.PositiveIntegerField(default=0)
    current_count = models.PositiveIntegerField(default=0, help_text='已处理行数（含失败）')
    success_count = models.PositiveIntegerField(default=0)
    error_log = models.JSONField(default=list, blank=True)
    warning_log = models.JSONField(default=list, blank=True)
    hash_iterations = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='本批次使用的密码哈希迭代次数，NULL 表示默认',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_imported_user_batch'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.file_name} - {self.status}"
