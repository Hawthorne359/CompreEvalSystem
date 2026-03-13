<div align="center">

# 综合素质测评系统

**陕西理工大学 · 学生综合素质测评管理平台**

![Django](https://img.shields.io/badge/Django-6.0-092E20?style=flat-square&logo=django&logoColor=white)
![Vue](https://img.shields.io/badge/Vue-3.4-4FC08D?style=flat-square&logo=vuedotjs&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=flat-square&logo=mysql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)

</div>

---

## 项目简介

本系统面向高校综合素质测评场景，覆盖从**学生材料提交 → 多级审核 → 双评网阅 → 仲裁申诉 → 成绩汇总导出**的完整业务闭环。

支持五类角色协同工作：学生、评审助理、辅导员、院系主任、系统超管，通过精细化权限控制实现各角色职责分离。

---

## 功能模块

| 模块 | 功能说明 |
|------|----------|
| 提交管理 | 学生在线填报综测材料，支持文件附件上传 |
| 评审网阅 | 双评制度，评审助理独立打分，差值超阈值触发辅导员介入 |
| 仲裁机制 | 评分差异自动上报，主任仲裁并锁定最终分 |
| 申诉流程 | 学生对评审结果提起申诉，多级流转审批 |
| 补交通道 | 辅导员/主任开启定向补交窗口，支持批量推送通知 |
| 成绩汇总 | 按指标树加权计算最终分，支持导出 Excel / Word 报告 |
| 用户管理 | Excel 批量导入学生/教师账号，角色灵活配置 |
| 操作审计 | 全链路操作日志记录，支持 IP / 时间追溯 |
| 实时推送 | 基于 SSE 的事件推送，评审状态变更即时通知 |
| 仪表盘 | 各角色专属数据看板，ECharts 可视化 |

---

## 技术栈

**后端**
- Python 3.12 · Django 6 · Django REST Framework
- JWT 认证（SimpleJWT）· SSE 实时推送（ASGI/Uvicorn）
- MySQL 8.0 · PyMySQL · python-dotenv

**前端**
- Vue 3 · Vue Router · Pinia
- Vite · Tailwind CSS · ECharts · GSAP

**部署**
- Docker · Docker Compose · Nginx
- AWS EC2 (Ubuntu 22.04)

---

## 快速开始（本地开发）

### 前置要求

- Python 3.12+
- Node.js 20+
- MySQL 8.0

### 后端启动

```bash
# 克隆项目
git clone https://github.com/zsh2646260452/CompreEvalSystem.git
cd CompreEvalSystem

# 创建虚拟环境并安装依赖
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

# 复制配置文件并填写数据库信息
cp .env.example .env
# 编辑 .env，填入 DB_PASSWORD 等本地配置

# 数据库迁移
python manage.py migrate

# 启动开发服务器
python manage.py runserver
# API 地址：http://127.0.0.1:8000/api/v1/
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
# 页面地址：http://localhost:5173
```

---

## 生产部署（Docker 一键启动）

服务器上只需安装 Docker，三条命令完成部署：

```bash
git clone https://github.com/zsh2646260452/CompreEvalSystem.git
cd CompreEvalSystem
cp .env.example .env   # 编辑 .env 填入生产配置
docker compose up -d --build
docker compose exec backend python manage.py migrate
```

详细部署步骤参见 [部署指南](docs/部署指南-AWS-Ubuntu.md)。

---

## 配置说明

项目所有环境相关配置通过根目录 `.env` 文件管理，参考 `.env.example` 模板：

```ini
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-domain.com
DB_NAME=campus_eval
DB_USER=root
DB_PASSWORD=your-password
DB_HOST=127.0.0.1
```

---

## 项目结构

```
CompreEvalSystem/
├── CompreEvalSystem/    # Django 项目配置
├── users/               # 用户与角色管理
├── org/                 # 院系班级组织管理
├── eval/                # 测评周期与指标配置
├── submission/          # 学生提交材料
├── scoring/             # 评分与仲裁
├── appeal/              # 申诉流程
├── audit/               # 操作审计与补交通道
├── report/              # 成绩汇总与报告导出
├── dashboard/           # 数据看板
├── realtime/            # SSE 实时事件推送
├── frontend/            # Vue 3 前端
├── nginx/               # Nginx 配置
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

<div align="center">
  <sub>陕西理工大学 · 计算机科学与工程学院 · 2026</sub>
</div>
