# 无足鸟·按时打卡

> 微信小程序 — 帮助用户按时服药/打卡的提醒工具，支持邮件通知、站内信、自定义计划与打卡记录管理。

[![License](https://img.shields.io/badge/license-GPLv3-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.14+-3776AB.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-009688.svg)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.x-4FC08D.svg)](https://cn.vuejs.org/)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](tests/)

---

## 目录

- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [环境配置](#环境配置)
- [API 文档](#api-文档)
- [测试](#测试)
- [部署](#部署)
- [项目文档](#项目文档)
- [许可证](#许可证)

---

## 功能特性

### 用户系统
- 邮箱注册与登录（验证码邮件验证）
- 微信小程序一键登录
- JWT Token 认证（7 天有效期）
- 用户资料管理（昵称、签名、头像、邮箱绑定）
- 账号注销（24 小时冷静期，可撤销）

### 打卡计划
- 创建/编辑/删除打卡计划（起止日期、多个通知时间点）
- 计划状态管理（进行中、暂停、已结束）
- 优先级设置（0-7，数字越小优先级越高）
- 计划过期自动关闭

### 打卡记录
- 按计划通知时间点打卡
- 打卡记录查询（按月统计、最近记录）
- 打卡后自动标记相关站内信为已读

### 通知系统
- **站内信**：注册时自动创建，计划到期/打卡提醒自动生成站内信
- **邮件通知**：用户自配 SMTP（腾讯企业邮、QQ 邮箱、Gmail 等），支持 SSL/STARTTLS
- **通知渠道管理**：邮件渠道增删改，客户端专用密码 AES-256-GCM 加密存储
- **定时调度**：后台定时任务自动派发通知、清理过期账号、关闭过期计划

---

## 技术栈

| 层级 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 前端 | uni-app (Vue 3) | 最新 | 微信小程序 + H5 跨端 |
| 前端 | Pinia | ^2.3 | 状态管理 |
| 前端 | SCSS | ^1.101 | 样式预处理（BEM 命名） |
| 后端 | FastAPI | >=0.100 | 异步 Web 框架 |
| 后端 | SQLAlchemy | >=2.0 | 异步 ORM（asyncmy 驱动） |
| 后端 | Pydantic Settings | >=2.0 | 配置管理与数据校验 |
| 后端 | PyJWT | >=2.8 | JWT 认证 |
| 后端 | bcrypt | >=4.0 | 密码哈希 |
| 后端 | cryptography | >=42.0 | AES-256-GCM 加密 |
| 数据库 | MariaDB | 12.3 (LTS) | 主数据库（业务库 + 用户库分离） |
| 测试 | pytest + pytest-asyncio | >=8.0 | 异步测试框架 |
| 测试 | pytest-cov | >=5.0 | 覆盖率统计（100%） |
| 部署 | Docker + Docker Compose | — | 容器化部署（MariaDB + FastAPI + Nginx） |

---

## 项目结构

```
yao/
├── backend/                    # 后端（FastAPI）
│   ├── app/
│   │   ├── api/v1/             # API 路由（users / plans / checkins / notification_*）
│   │   ├── core/               # 核心模块（config / database / security / deps）
│   │   ├── models/             # SQLAlchemy 数据模型
│   │   ├── schemas/            # Pydantic 请求/响应 Schema
│   │   ├── services/           # 业务逻辑服务层
│   │   ├── utils/              # 工具（crypto / logger / timezone）
│   │   └── main.py             # FastAPI 应用入口
│   ├── sql/                    # 数据库初始化 SQL
│   ├── .env.template           # 环境变量模板
│   ├── requirements.txt        # 生产依赖
│   └── requirements-test.txt   # 测试依赖
├── frontend/                   # 前端（uni-app Vue 3）
│   ├── src/
│   │   ├── api/modules/        # API 请求封装（按业务模块）
│   │   ├── assets/             # 静态资源（图片 / 全局样式）
│   │   ├── components/         # 可复用组件（BottomNav / NoticeButton 等）
│   │   ├── composables/        # 组合式函数（usePlaceholder / useShare 等）
│   │   ├── pages/              # 页面（index / user）
│   │   ├── store/              # Pinia 状态管理
│   │   ├── App.vue             # 根组件
│   │   ├── main.js             # 入口文件
│   │   ├── pages.json          # 路由配置
│   │   └── uni.scss            # 全局样式变量
│   ├── .env.template           # 前端环境变量模板
│   └── package.json            # 依赖与脚本
├── scripts/                    # 运维脚本
│   ├── deploy.sh               # 一键部署脚本（Rocky Linux + Docker）
│   ├── init_db.py              # 数据库初始化脚本
│   └── test_db_connection.py   # 数据库连接测试
├── tests/                      # 测试套件
│   ├── unit/backend/           # 单元测试（124 个）
│   ├── integration/backend/    # 集成测试（184 个）
│   ├── e2e/                    # 端到端测试（8 个）
│   ├── conftest.py             # 全局 pytest 配置
│   ├── create_test_db.py       # 测试数据库创建脚本
│   └── .coveragerc             # 覆盖率配置
├── .gitignore
├── AGENTS.md                   # AI 编程指南
├── design_wise.md              # 设计语言规范
├── pytest.ini                  # pytest 配置
├── 目录结构.json               # 完整目录树（机器可读）
├── 更新记录.md                 # 变更日志
├── LICENSE                     # GPLv3
└── README.md
```

---

## 快速开始

### 环境准备

| 软件 | 版本要求 | 说明 |
|------|----------|------|
| Python | 3.14+ | 后端运行环境 |
| Node.js | 18+ | 前端构建 |
| MariaDB | 12.3+ (LTS) | 数据库（开发环境可直装） |
| 微信开发者工具 | 最新 | 小程序调试 |

### 1. 克隆项目

```bash
git clone https://github.com/wuzuniao/yao.git
cd yao
```

### 2. 后端安装与启动

```bash
# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS

# 安装依赖
pip install -r backend/requirements.txt
pip install -r backend/requirements-test.txt   # 测试依赖（可选）

# 配置环境变量
copy backend\.env.template backend\.env         # Windows
# cp backend/.env.template backend/.env          # Linux/macOS
# 编辑 backend/.env 填入实际的数据库密码、SMTP、微信小程序等配置

# 初始化数据库（需先启动 MariaDB 并创建数据库）
python scripts/init_db.py

# 启动后端
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端启动后访问：
- API 根路径：http://localhost:8000
- 健康检查：http://localhost:8000/health
- Swagger 文档：http://localhost:8000/docs
- ReDoc 文档：http://localhost:8000/redoc

### 3. 前端安装与启动

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
copy .env.template .env         # Windows
# cp .env.template .env          # Linux/macOS
# 编辑 .env 设置 VITE_API_BASE_URL=http://localhost:8000

# 开发模式（微信小程序）
npm run dev:mp-weixin
# 使用微信开发者工具打开 frontend/dist/dev/mp-weixin 目录进行调试

# 构建
npm run build:mp-weixin
```

---

## 环境配置

### 后端 (`backend/.env`)

从 `backend/.env.template` 复制并填写以下配置：

| 变量 | 说明 | 示例 |
|------|------|------|
| `DATABASE_URL` | MariaDB 连接字符串 | `mysql+asyncmy://root:root@127.0.0.1:3306/wuzuniao_yao?charset=utf8mb4` |
| `SMTP_HOST` | 发件 SMTP 主机 | `smtp.exmail.qq.com` |
| `SMTP_PORT` | SMTP 端口 | `465`（SSL） |
| `SMTP_USER` | 发件邮箱账号 | `noreply@your_domain.com` |
| `SMTP_PASSWORD` | SMTP 客户端专用密码 | — |
| `SMTP_SENDER_NAME` | 发件人显示名称 | `无足鸟` |
| `WX_APPID` | 微信小程序 AppID | — |
| `WX_APP_SECRET` | 微信小程序 AppSecret | — |
| `ENCRYPTION_SECRET_KEY` | AES-256-GCM 加密密钥（base64 编码 32 字节） | 生成方式见模板注释 |
| `JWT_SECRET_KEY` | JWT 签名密钥 | 生成方式见模板注释 |
| `JWT_EXPIRE_DAYS` | JWT 过期天数 | `7` |

### 前端 (`frontend/.env`)

| 变量 | 说明 | 示例 |
|------|------|------|
| `VITE_API_BASE_URL` | 后端 API 基础地址 | `http://localhost:8000`（开发）/ `https://your-domain.com`（生产） |

### 数据库

项目使用两个独立数据库：

| 数据库 | 用途 | 说明 |
|--------|------|------|
| `wuzuniao_yao` | 业务库 | 计划、打卡记录、通知渠道、通知日志 |
| `wuzuniao_yonghu` | 用户库 | 用户账号、小程序绑定记录 |

初始化 SQL 位于 `backend/sql/`：
- `create_yao_db.sql` — 业务库表结构
- `create_user_db.sql` — 用户库表结构

---

## API 文档

所有 API 统一前缀 `/api/v1`，响应格式：

```json
{
  "code": 0,
  "msg": "success",
  "data": { ... }
}
```

### 主要接口

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 用户 | POST | `/api/v1/users/register` | 邮箱注册 |
| 用户 | POST | `/api/v1/users/login` | 邮箱登录 |
| 用户 | POST | `/api/v1/users/wechat-login` | 微信登录 |
| 用户 | GET | `/api/v1/users/info` | 获取当前用户信息 |
| 用户 | PUT | `/api/v1/users/signature` | 更新个性签名 |
| 用户 | PUT | `/api/v1/users/avatar` | 更新头像 |
| 用户 | POST | `/api/v1/users/schedule-deletion` | 申请注销账号 |
| 用户 | POST | `/api/v1/users/cancel-deletion` | 撤销注销 |
| 计划 | POST | `/api/v1/plans/` | 创建计划 |
| 计划 | GET | `/api/v1/plans/list` | 查询计划列表 |
| 计划 | PUT | `/api/v1/plans/{plan_id}` | 更新计划 |
| 计划 | DELETE | `/api/v1/plans/{plan_id}` | 删除计划 |
| 打卡 | POST | `/api/v1/checkins/` | 打卡 |
| 打卡 | GET | `/api/v1/checkins/latest` | 最近打卡记录 |
| 打卡 | GET | `/api/v1/checkins/month` | 按月查询打卡记录 |
| 通知渠道 | GET | `/api/v1/notification-channels/list` | 查询通知渠道 |
| 通知渠道 | POST | `/api/v1/notification-channels/email` | 创建邮件渠道 |
| 通知渠道 | PUT | `/api/v1/notification-channels/{channel_id}` | 更新邮件渠道 |
| 通知渠道 | DELETE | `/api/v1/notification-channels/{channel_id}` | 删除通知渠道 |
| 站内信 | GET | `/api/v1/notification-logs/list` | 站内信列表 |
| 站内信 | PUT | `/api/v1/notification-logs/read` | 标记已读 |
| 站内信 | PUT | `/api/v1/notification-logs/read-all` | 全部标记已读 |
| 站内信 | GET | `/api/v1/notification-logs/unread-count` | 未读数量 |

完整接口文档请访问 Swagger UI：`http://localhost:8000/docs`

---

## 测试

### 测试架构

| 层级 | 目录 | 数量 | 说明 |
|------|------|------|------|
| 单元测试 | `tests/unit/backend/` | 124 | 独立函数/Schema/工具类测试，不依赖外部资源 |
| 集成测试 | `tests/integration/backend/` | 184 | API 接口、服务层、数据库交互测试 |
| E2E 测试 | `tests/e2e/` | 8 | 完整用户流程测试 |
| **合计** | — | **316** | **覆盖率 100%** |

### 测试数据库隔离

测试使用独立的测试数据库，与开发环境完全隔离：

| 测试库 | 对应开发库 | 说明 |
|--------|------------|------|
| `wuzuniao_yao_test` | `wuzuniao_yao` | 业务测试库 |
| `wuzuniao_yonghu_test` | `wuzuniao_yonghu` | 用户测试库 |

每个测试结束后自动 TRUNCATE 清理数据，不影响开发环境。

### 运行测试

```bash
# 运行全部测试（在项目根目录执行）
pytest

# 按标记运行
pytest -m unit          # 仅单元测试
pytest -m integration   # 仅集成测试
pytest -m e2e           # 仅端到端测试

# 查看覆盖率详情
pytest --cov=app --cov-report=term-missing

# 查看 HTML 覆盖率报告
# 运行后打开 htmlcov/index.html
pytest --cov=app --cov-report=html
```

---

## 部署

### 生产环境（Docker 容器化）

适用于 Rocky Linux 9.4 x86_64，一键部署脚本会自动完成：

1. 安装 Docker 与基础工具
2. 配置 Docker 镜像加速
3. 获取项目代码
4. 配置 HTTPS 证书
5. 生成 Dockerfile、Nginx 配置、docker-compose.yml
6. 启动 MariaDB + FastAPI + Nginx 三容器架构

```bash
# 上传部署脚本和证书到服务器
scp scripts/deploy.sh root@SERVER:/opt/
scp yao.wuzuniao.com_nginx.zip root@SERVER:/opt/

# 执行部署
ssh root@SERVER
cd /opt
bash deploy.sh

# 或指定证书路径
CERT_ZIP_PATH=/path/to/cert.zip bash deploy.sh
```

### 容器架构

| 容器 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| yao-mariadb | mariadb:10.11 | 127.0.0.1:3306 | 数据库（仅本机可访问） |
| yao-backend | python:3.11-slim | 8000（内部） | FastAPI 后端 |
| yao-nginx | nginx:stable | 80/443 | HTTPS 反向代理 |

### 常用运维命令

```bash
# 在部署目录下执行
cd /opt/yao/deploy

docker compose ps              # 查看容器状态
docker compose logs -f backend # 查看后端日志
docker compose restart backend # 重启后端
docker compose down            # 停止全部服务
docker compose up -d           # 启动全部服务

# 更新代码后重启
cd /opt/yao && git pull
docker compose -f deploy/docker-compose.yml restart backend
```

---

## 项目文档

| 文档 | 说明 |
|------|------|
| [AGENTS.md](AGENTS.md) | AI 编程指南 — 项目约束、编码规范、技术栈版本 |
| [design_wise.md](design_wise.md) | 设计语言规范 — 色彩、排版、组件风格 |
| [目录结构.json](目录结构.json) | 完整目录树（机器可读，含每个文件说明） |
| [更新记录.md](更新记录.md) | 变更日志（按时间倒序） |

---

## 许可证

本项目基于 [GNU General Public License v3](LICENSE) 开源。
