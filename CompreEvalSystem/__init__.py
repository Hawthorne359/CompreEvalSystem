# 使用 PyMySQL 作为 MySQL 驱动（Django 默认认 mysqlclient）
import pymysql
pymysql.install_as_MySQLdb()
# Django 6 要求 mysqlclient >= 2.2.1，用 PyMySQL 时需满足版本检查
pymysql.version_info = (2, 2, 1, "final", 0)
