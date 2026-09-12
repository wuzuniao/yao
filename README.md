# 无足鸟（药，yao）

> 制定通用打卡计划并按时提醒、记录的跨端APP。**免费 · 易用 · 安全 · 开源**。
>
> 隐私数据加密传输与存储，亦可自行部署。开源地址：<https://github.com/wuzuniao/yao>

[![License](https://img.shields.io/badge/license-GPLv3-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.14+-3776AB.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-009688.svg)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.x-4FC08D.svg)](https://cn.vuejs.org/)
[![MariaDB](https://img.shields.io/badge/MariaDB-10.11_(LTS)-003545.svg)](https://mariadb.org/)

---

## 功能特性

- **打卡计划**：创建计划（内容、持续周期、每日提醒时间、通知方式），到提醒时间自动发送通知。
- **多途径通知**：站内信、微信订阅消息、邮件（自配 SMTP）、App 推送（友盟+ U-Push）。
- **打卡记录**：按计划提醒时间点打卡，支持日历查看与按月统计。
- **账号体系**：微信一键登录、邮箱注册/登录；绑定邮箱并设置密码后可在无足鸟系列产品中多端通用。
- **新手引导**：未登录展示功能介绍，登录后提供分步引导，降低使用门槛。

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | uni-app（Vue 3） | 微信小程序 / H5 / App 跨端 |
| 前端 | Pinia / SCSS | 状态管理 / BEM 样式 |
| 后端 | FastAPI（异步） | RESTful API |
| 后端 | SQLAlchemy / Pydantic | ORM（asyncmy 驱动）/ 数据校验 |
| 后端 | PyJWT / cryptography | RS256 令牌本地验签（JWKS 公钥）/ AES-256-GCM 加密 |
| 认证服务 | auth（独立项目，auth.wuzuniao.com） | 用户账户体系：注册/登录/令牌签发（OIDC 标准），本服务持 JWKS 公钥本地验签 |
| 数据库 | MariaDB 10.11 (LTS) | 业务库 `wuzuniao_yao`（用户数据由 auth 认证服务持有） |
| 部署 | Docker + Docker Compose | 共享基础设施（MariaDB/Nginx 容器多项目复用）+ 项目专属 FastAPI 容器 |

---

## 项目结构

```
yao/
├── backend/                # 后端（FastAPI）
│   ├── app/
│   │   ├── api/v1/         # 路由（plans / checkins / notification_* / announcements）
│   │   ├── core/           # 配置 / 数据库 / 安全 / 依赖注入
│   │   ├── models/         # SQLAlchemy 数据模型
│   │   ├── schemas/        # Pydantic 请求/响应 Schema
│   │   ├── services/       # 业务逻辑（计划 / 打卡 / 通知 / 调度）
│   │   └── main.py         # 应用入口（含后台定时任务生命周期）
│   ├── sql/                # 数据库初始化 SQL
│   └── .env.template       # 环境变量模板
├── frontend/               # 前端（uni-app Vue 3，HBuilderX 标准布局，无 src 层）
│   ├── api/                # 请求封装（request + modules）
│   ├── components/         # 可复用组件
│   ├── composables/        # 组合式函数
│   ├── config/             # 全端环境配置（env.js 常量模块，取代 .env）
│   ├── pages/              # 主包（index / record / settings / notification / plan）+ 用户分包
│   ├── store/              # Pinia 状态管理
│   └── utils/              # 通用工具函数
├── scripts/                # 运维脚本（部署 / H5 增量构建 / 初始化 DB / 连接测试）
└── tests/                  # 测试套件（unit / integration / e2e）
```

---

## 配置

**后端**：复制 `backend/.env.template` 为 `backend/.env`，字段与 `app/core/config.py` 一一对应，涵盖数据库、微信小程序/订阅消息、友盟 U-Push 推送、加密密钥、auth 对接（`AUTH_*`）与 CORS。

**前端**：配置集中在 `frontend/config/env.js` 常量模块（HBuilderX 不加载 `.env`，以常量模块保证多端构建一致）：`API_BASE_URL`、`AUTH_BASE_URL`、`AUTH_CLIENT_ID`、`WX_SUBSCRIBE_TEMPLATE_ID`。该文件提交 Git，严禁写入密码/密钥。

**数据库**：本服务仅连接业务库 `wuzuniao_yao`（计划/打卡/通知/公告）；用户账户与认证数据由 auth 认证服务持有，本服务需要用户信息时经 auth 的 `/internal/*` 服务接口查询。初始化 SQL 位于 `backend/sql/create_yao_db.sql`。

---

## API

所有接口前缀 `/api/v1`，统一响应格式：

```json
{ "code": 0, "msg": "success", "data": { } }
```

主要模块：账号（`/account`，账号合并：bind-email 命中已有邮箱 need_merge 后迁移业务数据并上报 auth）、计划（`/plans`）、打卡（`/checkins`）、通知渠道（`/notification-channels`）、站内信（`/notification-logs`）、公告（`/announcements`）。本服务主动调用 auth 的 `/internal/*`（拉取待清理用户/上报删除完成/合并任务确认，X-Service-Token 认证）；auth 不回调本服务。用户认证接口（注册/登录/资料）由 auth 认证服务提供（`https://auth.wuzuniao.com`）。完整接口见 Swagger UI：`http://localhost:8000/docs`。

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

生产架构为「**共享基础设施 + 项目专属后端**」，部署配置集中在 `/opt/deploy`（git 仓库仅存源码）：

- **共享基础设施**（无项目前缀，多项目复用）：`mariadb` 与 `nginx` 容器（nginx 统一承载 yao 与 auth 站点）、`wuzuniao.com` 泛域名证书（acme.sh 自动续期，覆盖全部子域）、数据库数据与统一备份
- **本项目**（`/opt/deploy/yao`）：`yao-backend` 专属容器，经 `app-net` 网络访问共享服务

部署只需一条命令（脚本幂等：生成 Dockerfile/compose、写入 nginx 站点配置、初始化业务库与专用用户 `yao_backend`、构建 H5——产物已存在则跳过）：

```bash
git clone git@github.com:wuzuniao/yao.git && cd yao
bash scripts/deploy.sh
```

> **部署顺序**：先部署 auth 认证服务（独立项目，见其仓库 README），再部署本项目；本项目 `.env` 的 `AUTH_*` 三项须与 auth 侧配置一致。

> **📌 附注 —— 关于独立部署**：如无需独立认证服务、希望用户与业务合一（传统单体模式），建议使用 **V1.0.10 版本**——该版本用户业务合在一起，是**最后一个可独立部署的项目版本**；此后版本的用户模块由独立的 auth 认证服务承载，部署时需同时部署 auth。

常用运维：

```bash
cd /opt/deploy/yao && docker compose ps      # 本项目后端
cd /opt/deploy && docker compose ps          # 共享基础设施（mariadb / nginx）
```

---

## 增量更新（生产环境）

服务器内存仅 1.7GB，构建须限额（脚本已内置资源限制与内存防护）：

```bash
# H5 前端：停后端释放内存 → 限额构建 → 拉起后端 → 验证（共享 nginx 不停，dist 即时生效）
bash /opt/yao/scripts/build_h5.sh

# 后端：拉代码后重建（Dockerfile 未变时秒级完成）
cd /opt/yao && git pull && cd /opt/deploy/yao && docker compose up -d --build backend
```

---

## 常见问题（FAQ）

### 这是什么应用？
无足鸟按时吃药打卡是一款免费、开源的通用打卡计划与按时提醒工具。你可以为任何需要按时执行的事项（吃药、健身、学习、喝水等）创建计划，到点自动提醒，并记录打卡历史。

### 支持哪些平台？
微信小程序（主要）、H5 网页、Android/iOS App、鸿蒙（HarmonyOS）App（通过 HBuilderX 打包）。同一套 uni-app（Vue 3）代码跨端运行。

### 数据安全吗？
密码经 bcrypt 哈希，邮件客户端专用密码与微信 session_key 经 AES-256-GCM 加密存储，传输全程 HTTPS。支持自行部署，数据完全掌握在自己手中。

### 通知渠道有哪些？
站内信（默认，应用内查看）、微信订阅消息（一次性订阅，需用户授权）、邮件（用户自配 SMTP）、App 推送（友盟+ U-Push，仅 App 端）。同一计划可关联多个渠道，到点同时发送。

### 开源协议？
GNU GPLv3，开源地址 https://github.com/wuzuniao/yao 。

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
