# CompreEvalSystem — Docker 部署指南（AWS EC2 Ubuntu）

> 适用环境：AWS EC2（Ubuntu 22.04 LTS）、本地 Windows + Xshell、项目托管于 GitHub  
> 本地电脑**无需安装 Docker**，只需正常 `git push` 代码，所有构建在服务器上完成。

## 部署流程总览

```
本地 Windows（你的电脑）
  └─ 写代码 → git push → GitHub
                              ↓ SSH 登录服务器后执行
EC2 Ubuntu Server
  └─ git pull
  └─ docker compose up --build   ← 服务器自己拉依赖、编译前端、构建镜像、启动容器

启动后运行的 3 个 Docker 容器：
  ├─ nginx    （端口 80 对外）反向代理 + 服务静态/媒体文件
  ├─ backend  （内部 8000）  Django + Uvicorn
  └─ mysql    （内部 3306）  MySQL 8.0 数据库
```

---

## 目录

1. [AWS 控制台配置](#1-aws-控制台配置)
2. [SSH 连接服务器](#2-ssh-连接服务器)
3. [服务器安装 Docker](#3-服务器安装-docker)
4. [将项目代码推送到 GitHub（本地电脑操作）](#4-将项目代码推送到-github)
5. [服务器拉取代码](#5-服务器拉取代码)
6. [.env 配置文件说明与创建](#6-env-配置文件说明与创建)
7. [首次启动](#7-首次启动)
8. [数据库初始化](#8-数据库初始化)
9. [验证部署结果](#9-验证部署结果)
10. [代码更新工作流](#10-代码更新工作流)
11. [常用运维命令速查](#11-常用运维命令速查)
12. [常见问题排查](#12-常见问题排查)

---

## 1. AWS 控制台配置

### 1.1 安全组入站规则

在 EC2 控制台 → 实例 → 安全组 → 编辑入站规则，添加以下规则：

| 类型 | 协议 | 端口 | 来源 | 说明 |
|------|------|------|------|------|
| SSH | TCP | 22 | 你的本地 IP（或 0.0.0.0/0 临时用） | SSH 连接 |
| HTTP | TCP | 80 | 0.0.0.0/0 | 用户访问 |
| HTTPS | TCP | 443 | 0.0.0.0/0 | 可选，配 SSL 后开启 |

> **注意：** MySQL 3306 端口**不要**对外开放，数据库只在容器内部访问。

### 1.2 记下服务器公网 IP

在 EC2 控制台找到实例的 **公有 IPv4 地址**，例如 `54.123.45.67`，后面会多次用到。

### 1.3 下载 .pem 密钥文件

创建实例时下载的 `.pem` 文件（如 `mykey.pem`），保存到本地固定位置，如：  
`C:\Users\你的用户名\.ssh\mykey.pem`

---

## 2. SSH 连接服务器

### 使用 Xshell

1. 打开 Xshell → 新建会话
2. 主机填 EC2 公网 IP，端口 22，协议 SSH
3. 用户身份验证 → 方法选 **Public Key**，用户名填 `ubuntu`
4. 浏览选择 `.pem` 文件 → 确定
5. 连接成功后看到：`ubuntu@ip-xxx-xxx-xxx-xxx:~$`

### 使用 PowerShell（Windows 10/11 内置）

```powershell
ssh -i "C:\Users\你的用户名\.ssh\mykey.pem" ubuntu@你的EC2公网IP
```

---

## 3. 服务器安装 Docker

以下命令全部在服务器终端（Xshell）中执行。

### 3.1 更新系统

```bash
sudo apt update && sudo apt upgrade -y
```

### 3.2 一键安装 Docker（官方脚本）

```bash
curl -fsSL https://get.docker.com | sudo sh
```

### 3.3 将当前用户加入 docker 组（免 sudo）

```bash
sudo usermod -aG docker ubuntu
```

> **重要：** 执行完这条命令后，**需要退出 SSH 重新登录**，权限才会生效。

```bash
exit
# 重新 SSH 连接后验证：
docker --version
docker compose version
```

看到版本号输出即安装成功，例如：
```
Docker version 27.x.x
Docker Compose version v2.x.x
```

---

## 4. 将项目代码推送到 GitHub

> 这一节在**本地 Windows 电脑**上操作，不是服务器。

### 4.1 在 GitHub 上创建仓库

1. 打开 [https://github.com](https://github.com)，登录账号
2. 点击右上角的 **"+"** 按钮 → 选择 **"New repository"**
3. 填写仓库信息：
   - **Repository name**：填 `CompreEvalSystem`（或你喜欢的名字）
   - **Description**：可选，填项目描述
   - **Public / Private**：
     - Public = 所有人可见（毕设展示推荐）
     - Private = 仅自己可见
   - **⚠️ 不要勾选** "Add a README file"、"Add .gitignore"、"Choose a license"（因为本地已有代码，勾选会冲突）
4. 点击绿色按钮 **"Create repository"**
5. 创建成功后，页面会显示仓库地址，复制 HTTPS 格式的地址，例如：  
   `https://github.com/你的用户名/CompreEvalSystem.git`

### 4.2 在本地初始化 Git 并推送代码

在本地项目目录打开 PowerShell 或 VSCode 终端（`Ctrl+`` `），执行以下命令：

```powershell
# 进入项目根目录
cd C:\Users\你的用户名\Desktop\biyesheji\CompreEvalSystem

# 初始化 Git 仓库（如果还没有）
git init

# 配置你的 Git 用户信息（只需执行一次）
git config --global user.name "你的名字"
git config --global user.email "你的GitHub邮箱"

# 将所有文件添加到暂存区
git add .

# 创建第一次提交
git commit -m "初始提交"

# 关联到刚才创建的 GitHub 仓库（替换为你的实际地址）
git remote add origin https://github.com/你的用户名/CompreEvalSystem.git

# 将代码推送到 GitHub
git push -u origin main
```

> **推送时需要 GitHub 登录验证：**  
> - 用户名：你的 GitHub 用户名  
> - 密码：**不是**登录密码，而是 **Personal Access Token（PAT）**
>
> **如何获取 PAT：**  
> 1. 登录 GitHub → 右上角头像 → **Settings**  
> 2. 左侧最底部 → **Developer settings**  
> 3. **Personal access tokens** → **Tokens (classic)** → **Generate new token (classic)**  
> 4. Note 填任意名字，Expiration 选 90 days 或 No expiration  
> 5. Scopes 勾选 **repo**（第一个大复选框）  
> 6. 点 **Generate token**，复制生成的 token（只显示一次！）  
> 7. 推送时"密码"处粘贴这个 token

### 4.3 验证推送成功

刷新 GitHub 仓库页面，能看到项目文件说明推送成功。

> **之后每次更新代码的本地操作：**
> ```powershell
> git add .
> git commit -m "描述本次改动"
> git push origin main
> ```

---

## 5. 服务器拉取代码

> 这一节在**服务器终端（Xshell）**中操作。

### 5.1 配置 Git

```bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"
```

### 5.2 克隆仓库

```bash
cd ~
git clone https://github.com/你的用户名/CompreEvalSystem.git
cd CompreEvalSystem
```

> **如果仓库是 Private 私有仓库**，克隆时需要身份验证，有两种方式：
>
> **方式一：使用 Personal Access Token（推荐，简单）**  
> 克隆时在地址里嵌入 token，无需交互输入：
> ```bash
> git clone https://你的用户名:你的PAT@github.com/你的用户名/CompreEvalSystem.git
> ```
>
> **方式二：配置服务器 SSH Key**
> ```bash
> # 在服务器上生成 SSH Key
> ssh-keygen -t ed25519 -C "你的邮箱"
> # 回车三次使用默认值
>
> # 查看公钥内容，全部复制
> cat ~/.ssh/id_ed25519.pub
>
> # 将复制的内容添加到 GitHub：
> # 登录 GitHub → Settings → SSH and GPG keys → New SSH key → 粘贴 → Add SSH key
> ```
> 然后使用 SSH 方式克隆：
> ```bash
> git clone git@github.com:你的用户名/CompreEvalSystem.git
> ```

---

## 6. .env 配置文件说明与创建

### 6.1 .env 文件是什么

`.env` 是项目的**统一配置文件**，存放所有"开发和生产环境不一样的配置"，包括：

- 数据库密码
- Django 密钥
- 允许访问的域名/IP
- 媒体文件存储路径
- 缓存后端等

**为什么不直接改代码？**

- 代码每次 `git pull` 都会被覆盖，但 `.env` 不会（它在 `.gitignore` 里，不提交到 Git）
- 密码不会意外泄露到 GitHub
- 所有配置集中在一个文件，部署/迁移时只需重新创建这一个文件

**项目根目录下的相关文件：**

```
CompreEvalSystem/
├── .env.example   ← 模板文件（已在 Git 里，展示所有可配置项）
├── .env           ← 实际配置文件（不在 Git 里，需要手动创建）
└── ...
```

### 6.2 在服务器上创建 .env

```bash
cd /home/ubuntu/CompreEvalSystem
nano .env
```

粘贴以下内容，**把所有 `替换为...` 的占位符换成实际值**：

```ini
# ── 核心安全 ─────────────────────────────────────────────────
# 生成强密钥（在服务器上执行此命令并把输出值填到下面）：
#   python3 -c "import secrets; print(secrets.token_urlsafe(50))"
DJANGO_SECRET_KEY=替换为上述命令生成的随机字符串

# 生产环境必须为 False
DJANGO_DEBUG=False

# 填入你的 EC2 公网 IP，多个值用英文逗号分隔（不要加空格）
DJANGO_ALLOWED_HOSTS=54.123.45.67,localhost

# ── 数据库 ──────────────────────────────────────────────────
# Docker 内部 MySQL 使用 root 用户
DB_NAME=campus_eval
DB_USER=root
DB_PASSWORD=替换为强密码（例如 MyStr0ng!Pass）
DB_HOST=mysql
DB_PORT=3306

# Docker MySQL 容器初始化用，与 DB_PASSWORD 填同一个密码
MYSQL_ROOT_PASSWORD=替换为强密码（与上面保持一致）
MYSQL_DATABASE=campus_eval

# ── 媒体文件路径 ─────────────────────────────────────────────
# 留空：用户上传的文件保存在项目目录下的 media/ 文件夹
# 也可填绝对路径，例如：MEDIA_ROOT=/data/uploads
MEDIA_ROOT=

# ── CORS 跨域 ────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS=False
# 填入你的前端访问地址（与 DJANGO_ALLOWED_HOSTS 一致）
CORS_ALLOWED_ORIGINS=http://54.123.45.67

# ── 缓存后端 ─────────────────────────────────────────────────
# file = 文件缓存（默认，无需额外服务）
# redis = Redis 缓存（需要额外安装 Redis，高并发时可考虑）
CACHE_BACKEND=file
CACHE_LOCATION=
CACHE_REDIS_URL=redis://127.0.0.1:6379/1

# ── 日志目录 ─────────────────────────────────────────────────
# 留空：日志保存在项目目录下的 logs/ 文件夹
LOG_DIR=
```

编辑完成后按 `Ctrl+X` → `Y` → `Enter` 保存退出。

### 6.3 验证 .env 文件内容

```bash
cat .env
```

确认没有多余的空格、引号等格式问题（`.env` 文件的值不需要加引号）。

---

## 7. 首次启动

### 7.1 确认 Docker 相关文件存在

```bash
ls Dockerfile docker-compose.yml nginx/nginx.conf
```

应该能看到这三个文件列出，如果缺少则说明代码有问题。

### 7.2 构建镜像并启动所有容器

```bash
cd /home/ubuntu/CompreEvalSystem
docker compose up -d --build
```

参数说明：
- `-d`：后台运行（detached），不占用终端
- `--build`：重新构建镜像

> 首次执行需要：下载 Python/Node/Nginx/MySQL 基础镜像 + 安装所有依赖 + 编译前端。  
> 预计耗时 **5~15 分钟**，取决于服务器网速，请耐心等待。

### 7.3 查看启动进度

```bash
# 查看所有容器状态
docker compose ps

# 实时查看后端日志（Ctrl+C 退出）
docker compose logs -f backend
```

等待所有容器状态变为 `running`：

```
NAME                  STATUS
compreevals-mysql-1   running (healthy)
compreevals-backend-1 running
compreevals-nginx-1   running
```

---

## 8. 数据库初始化

容器全部 `running` 后，执行数据库迁移：

```bash
# 执行 Django 数据库迁移（在 backend 容器内运行）
docker compose exec backend python manage.py migrate
```

创建后台超级管理员账号：

```bash
docker compose exec backend python manage.py createsuperuser
```

按提示输入用户名、邮箱（可留空）、密码。

> **提示：** 之后如果有新的数据库迁移（`git pull` 后有新的 migration 文件），重新执行 `docker compose exec backend python manage.py migrate` 即可，不会影响已有数据。

---

## 9. 验证部署结果

```bash
# 检查容器均在运行
docker compose ps

# 检查 80 端口正在监听
ss -tlnp | grep 80

# 本机测试 API
curl http://127.0.0.1/api/v1/users/auth/login/ -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}' | head -c 200
```

在浏览器中访问 `http://你的EC2公网IP`，应能看到前端登录页面。

访问 `http://你的EC2公网IP/admin/` 可以登录 Django 后台管理。

---

## 10. 代码更新工作流

### 本地电脑（你的 Windows）

正常写代码，然后推送到 GitHub：

```powershell
# 在 PowerShell 或 VSCode 终端里执行
git add .
git commit -m "描述本次改动"
git push origin main
```

### 服务器端（SSH 进入后执行）

```bash
cd /home/ubuntu/CompreEvalSystem

# 拉取最新代码
git pull origin main

# 重新构建并重启（后端代码有改动时必须 --build）
docker compose up -d --build

# 如果有新的数据库迁移
docker compose exec backend python manage.py migrate
```

> **提示：** 如果只改了前端或后端代码，`--build` 会重新构建镜像，大约需要 1~3 分钟。如果只修改了 `.env` 配置文件，不需要 `--build`，直接 `docker compose up -d` 重启即可。

### 创建一键更新脚本（可选）

只需创建一次，以后更新只需在服务器执行 `bash deploy.sh`：

```bash
cat > /home/ubuntu/CompreEvalSystem/deploy.sh << 'EOF'
#!/bin/bash
set -e
cd /home/ubuntu/CompreEvalSystem

echo "===== [1/3] 拉取最新代码 ====="
git pull origin main

echo "===== [2/3] 重新构建并重启容器 ====="
docker compose up -d --build

echo "===== [3/3] 执行数据库迁移 ====="
docker compose exec backend python manage.py migrate --noinput

echo "===== 部署完成 ====="
EOF

chmod +x /home/ubuntu/CompreEvalSystem/deploy.sh
```

之后每次更新只需：

```bash
cd /home/ubuntu/CompreEvalSystem && bash deploy.sh
```

---

## 11. 常用运维命令速查

```bash
# ── 容器管理 ─────────────────────────────────────────────────

# 查看所有容器状态
docker compose ps

# 启动所有容器（已有镜像，不重新构建）
docker compose up -d

# 停止所有容器（保留数据）
docker compose down

# 重启单个容器
docker compose restart backend
docker compose restart nginx
docker compose restart mysql

# ── 日志查看 ─────────────────────────────────────────────────

# 实时查看后端日志
docker compose logs -f backend

# 查看 Nginx 日志
docker compose logs -f nginx

# 查看 MySQL 日志
docker compose logs -f mysql

# ── Django 管理命令 ──────────────────────────────────────────

# 进入后端容器 shell
docker compose exec backend bash

# 执行 Django 命令（无需进入容器）
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py shell

# ── 数据库 ──────────────────────────────────────────────────

# 进入 MySQL 容器
docker compose exec mysql mysql -u root -p
# 输入 .env 中的 MYSQL_ROOT_PASSWORD

# ── 磁盘管理 ─────────────────────────────────────────────────

# 查看 Docker 磁盘占用
docker system df

# 清理未使用的镜像（释放磁盘空间）
docker image prune -f

# ── 数据目录（宿主机上的实际路径）──────────────────────────

# 用户上传文件
ls /home/ubuntu/CompreEvalSystem/media/

# 应用日志
ls /home/ubuntu/CompreEvalSystem/logs/

# 数据库数据（Docker volume，不是普通文件夹）
docker volume ls
```

---

## 12. 常见问题排查

### 问题：`docker compose up --build` 卡住或报错

```bash
# 查看详细构建日志（不加 -d，直接看输出）
docker compose up --build
```

常见原因：
- 网络问题导致下载镜像超时 → 等待重试，或考虑配置 Docker 镜像加速
- `npm install` 失败 → 检查 `frontend/package.json` 是否有误

### 问题：容器启动失败，状态为 `exited`

```bash
# 查看具体错误
docker compose logs backend
docker compose logs mysql
```

### 问题：浏览器访问页面空白或 502

```bash
# 检查容器是否都在运行
docker compose ps

# 查看后端错误日志
docker compose logs backend

# 检查 Nginx 是否连接到 backend
docker compose logs nginx
```

### 问题：API 返回 400 Bad Request / DisallowedHost

`.env` 中 `DJANGO_ALLOWED_HOSTS` 没有包含当前访问的 IP/域名。修改 `.env` 后执行：

```bash
docker compose up -d
```

### 问题：数据库连接失败（backend 日志报 `Can't connect to MySQL`）

MySQL 容器可能还没完成初始化（首次启动需要约 30~60 秒）。backend 容器配置了等待 MySQL 健康检查通过后才启动，但如果超时可以手动重启：

```bash
docker compose restart backend
```

### 问题：上传文件后无法访问（media 文件 404）

检查 `media/` 目录权限：

```bash
ls -la /home/ubuntu/CompreEvalSystem/media/
# 如果目录不存在，手动创建
mkdir -p /home/ubuntu/CompreEvalSystem/media
```

### 问题：前端页面刷新后 404

这是 Vue Router history 模式的正常需求，Nginx 配置已经包含 `try_files $uri $uri/ /index.html`。如果出现此问题，检查 nginx 容器是否在运行：

```bash
docker compose restart nginx
```

### 问题：.env 文件修改后不生效

修改 `.env` 后需要重启容器（不需要重新构建）：

```bash
docker compose up -d
```

---

> 文档版本：2026-03  
> 项目：CompreEvalSystem（陕西理工大学综合素质测评系统）
