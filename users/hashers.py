"""
批量导入专用低迭代 PBKDF2 密码哈希器。

使用独立 algorithm 标识，确保 Django 登录时自动检测并升级为默认高迭代哈希。
"""
from django.contrib.auth.hashers import PBKDF2PasswordHasher


class LowIterPBKDF2PasswordHasher(PBKDF2PasswordHasher):
    """
    PBKDF2 低迭代变体，用于批量导入时加速初始密码哈希。

    algorithm 不同于默认 hasher，Django 登录验证后会自动用首选 hasher
    重新哈希并保存，保证长期安全性。
    """

    algorithm = 'pbkdf2_sha256_lowiter'
    iterations = 1000
