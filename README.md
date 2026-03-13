# 校园综合测评管理系统 (CampusEvalSystem)

Django + Vue.js 实现的综测提交、多级审核、双评网阅、仲裁与审计系统。

## 技术栈

- 后端：Django 6、Django REST Framework、JWT (SimpleJWT)、MySQL/SQLite
- 前端：Vue 3、Vue Router、Pinia、Axios、Tailwind CSS、Vite

## 本地运行

### 后端

```bash
# 虚拟环境（已有 .venv 可略过）
python -m venv .venv
.venv\Scripts\activate   # Windows

# 依赖
pip install -r requirements.txt

# 初始化角色
python manage.py init_roles

# 创建超级用户（首次）
python manage.py createsuperuser

# 开发服务器
python manage.py runserver
```

API 根路径：`http://127.0.0.1:8000/api/v1/`

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问：`http://localhost:5173`，登录后使用。开发时 Vite 会代理 `/api`、`/media` 到后端。

## 生产部署要点

- 将 `settings.py` 中 `DEBUG=False`，`ALLOWED_HOSTS` 设为实际域名，`CORS_ALLOWED_ORIGINS` 设为前端域名。
- 数据库：可切换为 MySQL，在 `DATABASES` 中配置。
- 后端：使用 Gunicorn + Nginx；收集静态文件：`python manage.py collectstatic`。
- 前端：`npm run build`，将 `frontend/dist` 由 Nginx 提供或挂到 Django 静态目录。

## 项目结构

- `CompreEvalSystem/`：Django 项目配置
- `users`：用户、角色、JWT、角色切换、批量导入
- `org`：院系、班级
- `eval`：测评周期、项目、指标、权重与评审规则
- `submission`：学生提交、佐证
- `scoring`：评分、双评、仲裁、批量导入成绩
- `appeal`：申诉
- `audit`：审计日志、补交通道
- `report`：汇总、排名、导出
- `frontend/`：Vue 3 SPA

## 首次使用

1. 执行 `python manage.py createsuperuser` 创建管理员。
2. 执行 `python manage.py init_roles` 初始化角色。
3. 在 Django Admin 或接口中创建院系、班级、测评周期与项目，并为用户分配角色。

## 批量导入用户

管理员可通过「用户管理」或「系统管理」页面进入批量导入功能：

1. 点击「批量导入」按钮进入导入页面
2. 下载 Excel 导入模板（含表头说明与角色代码）
3. 按模板填写用户信息（用户名、角色代码为必填；学号/工号唯一；院系/班级名称需与系统一致）
4. 上传填写好的 Excel 文件，系统将显示导入结果与错误详情

**注意事项**：
- 用户名和角色代码为必填项
- 学号/工号必须唯一，不能与已有用户重复
- 院系/班级名称需与系统中现有名称完全一致
- 初始密码留空则默认为 123456
- 不允许通过导入创建超级管理员角色
