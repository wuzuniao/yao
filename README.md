# 无足鸟（药，yao）

> 制定通用打卡计划并按时提醒、记录的跨端小程序。**免费 · 易用 · 安全 · 开源**。
>
> 隐私数据加密传输与存储，亦可自行部署。开源地址：<https://github.com/wuzuniao/yao>

[![License](https://img.shields.io/badge/license-GPLv3-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.14+-3776AB.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-009688.svg)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.x-4FC08D.svg)](https://cn.vuejs.org/)
[![MariaDB](https://img.shields.io/badge/MariaDB-12.3-003545.svg)](https://mariadb.org/)

---

## 功能特性

- **打卡计划**：创建计划（内容、持续周期、每日提醒时间、通知方式），到提醒时间自动发送通知。
- **多途径通知**：支持站内信、微信订阅消息、邮件等多种渠道，可自配 SMTP。
- **打卡记录**：按计划提醒时间点打卡，支持日历查看与按月统计。
- **账号体系**：微信一键登录、邮箱注册/登录；绑定邮箱并设置密码后可在无足鸟系列产品中多端通用。
- **新手引导**：未登录展示功能介绍，登录后提供分步引导，降低使用门槛。

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | uni-app（Vue 3） | 微信小程序跨端 |
| 前端 | Pinia / SCSS | 状态管理 / BEM 样式 |
| 后端 | FastAPI（异步） | RESTful API |
| 后端 | SQLAlchemy / Pydantic | ORM（asyncmy 驱动）/ 数据校验 |
| 后端 | PyJWT / bcrypt / cryptography | 认证 / 密码哈希 / AES-256-GCM 加密 |
| 数据库 | MariaDB 12.3 (LTS) | 业务库与用户库分离 |
| 部署 | Docker + Docker Compose | MariaDB + FastAPI + Nginx |

---

## 项目结构

```
yao/
├── backend/                # 后端（FastAPI）
│   ├── app/
│   │   ├── api/v1/         # 路由（users / plans / checkins / notification_* / announcements）
│   │   ├── core/           # 配置 / 数据库 / 安全 / 依赖注入
│   │   ├── models/         # SQLAlchemy 数据模型
│   │   ├── schemas/        # Pydantic 请求/响应 Schema
│   │   ├── services/       # 业务逻辑（用户 / 计划 / 打卡 / 通知 / 调度）
│   │   └── main.py         # 应用入口（含后台定时任务生命周期）
│   ├── sql/                # 数据库初始化 SQL
│   └── .env.template       # 环境变量模板
├── frontend/               # 前端（uni-app Vue 3）
│   └── src/
│       ├── api/            # 请求封装（request + modules）
│       ├── components/     # 可复用组件
│       ├── composables/    # 组合式函数
│       ├── pages/          # 主包（index / record / settings）+ 用户分包
│       ├── store/          # Pinia 状态管理
│       └── .env.template   # 前端环境变量模板
├── scripts/                # 运维脚本（部署 / 初始化 DB / 连接测试）
├── tests/                  # 测试套件（unit / integration / e2e）
├── AGENTS.md               # AI 编程指南
├── design_wise.md          # 设计语言规范
├── 目录结构.json            # 完整目录树（机器可读）
└── 更新记录.md             # 变更日志
```

---

## 快速开始

### 环境准备

| 软件 | 版本要求 | 说明 |
|------|----------|------|
| Python | 3.14+ | 后端运行环境 |
| Node.js | 18+ | 前端构建 |
| MariaDB | 12.3+ (LTS) | 开发环境可直装 |
| 微信开发者工具 | 最新 | 小程序调试 |

### 1. 克隆项目

```bash
git clone https://github.com/wuzuniao/yao.git
cd yao
```

### 2. 启动后端

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS

pip install -r backend/requirements.txt
pip install -r backend/requirements-test.txt   # 测试依赖（可选）

cp backend/.env.template backend/.env    # Linux/macOS；Windows 用 copy
python scripts/init_db.py                 # 初始化数据库（需先启动 MariaDB）

cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

启动后访问：API 根路径 `http://localhost:8000`、健康检查 `/health`、Swagger 文档 `/docs`、ReDoc `/redoc`。

### 3. 启动前端

```bash
cd frontend
npm install

cp .env.template .env    # Windows 用 copy；设置 VITE_API_BASE_URL=http://localhost:8000

npm run dev:mp-weixin    # 开发模式（微信小程序）
# 用微信开发者工具打开 frontend/dist/dev/mp-weixin 调试
npm run build:mp-weixin  # 生产构建
```

---

## 配置

### 后端（`backend/.env`）

从 `.env.template` 复制，关键配置：

| 变量 | 说明 |
|------|------|
| `DATABASE_URL` | MariaDB 连接串，如 `mysql+asyncmy://root:root@127.0.0.1:3306/wuzuniao_yao?charset=utf8mb4` |
| `SMTP_*` | 发件 SMTP 主机/端口/账号/密码/发件名 |
| `WX_APPID` / `WX_APP_SECRET` | 微信小程序凭证 |
| `ENCRYPTION_SECRET_KEY` | AES-256-GCM 加密密钥（base64 编码 32 字节） |
| `JWT_SECRET_KEY` / `JWT_EXPIRE_DAYS` | JWT 签名密钥 / 过期天数（默认 7） |

### 前端（`frontend/.env`）

| 变量 | 说明 |
|------|------|
| `VITE_API_BASE_URL` | 后端地址，开发 `http://localhost:8000`、生产填域名 |

### 数据库

使用两个独立数据库：`wuzuniao_yao`（业务库：计划/打卡/通知/公告）与 `wuzuniao_yonghu`（用户库：账号/小程序绑定）。初始化 SQL 位于 `backend/sql/`（`create_yao_db.sql`、`create_user_db.sql`）。

---

## API

所有接口前缀 `/api/v1`，统一响应格式：

```json
{ "code": 0, "msg": "success", "data": { } }
```

主要模块：用户（`/users`）、计划（`/plans`）、打卡（`/checkins`）、通知渠道（`/notification-channels`）、站内信（`/notification-logs`）、公告（`/announcements`）。完整接口与请求/响应示例见 Swagger UI：`http://localhost:8000/docs`。

---

## 测试

测试套件基于 `pytest + pytest-asyncio + pytest-cov`，使用独立测试库（与开发库隔离，每例结束自动清理）：

```bash
pytest                 # 运行全部
pytest -m unit         # 仅单元测试
pytest -m integration  # 仅集成测试
pytest -m e2e          # 仅端到端测试
pytest --cov=app --cov-report=term-missing   # 覆盖率
```

---

## 部署

生产环境为 Rocky Linux + Docker 容器化，由 `scripts/deploy.sh` 一键完成（具体镜像版本由该脚本控制）：

- `yao-mariadb`：数据库（仅本机可访问）
- `yao-backend`：FastAPI 后端
- `yao-nginx`：HTTPS 反向代理

```bash
# 上传脚本与证书到服务器后执行
bash deploy.sh
# 或指定证书路径： CERT_ZIP_PATH=/path/to/cert.zip bash deploy.sh
```

常用运维（在部署目录下）：

```bash
docker compose ps                   # 查看容器状态
docker compose logs -f backend      # 后端日志
docker compose restart backend      # 重启后端
```

---

## 项目文档

| 文档 | 说明 |
|------|------|
| [AGENTS.md](AGENTS.md) | AI 编程指南（约束与编码规范） |
| [design_wise.md](design_wise.md) | 设计语言规范（色彩 / 排版 / 组件） |
| [目录结构.json](目录结构.json) | 完整目录树（含每个文件说明） |
| [更新记录.md](更新记录.md) | 变更日志 |

---

## 许可证

本项目基于 [GNU General Public License v3](LICENSE) 开源。
