#!/bin/bash
# ============================================================
# 脚本名称：build_h5.sh
# 功能：yao 项目 H5 前端增量构建与生效（不经完整 deploy.sh，快速更新前端）
#
# 与旧版流程的差异（架构升级后自动适配）：
#   - 部署目录已集中到 /opt/deploy（backend compose 在 /opt/deploy/yao）
#   - nginx 为多项目共享容器（同时承载 auth.wuzuniao.com），构建期间不停止，
#     dist 为目录级 bind mount，构建完成即时生效
#   - 仅停止 yao-backend 释放内存供构建使用，构建后自动拉起
#
# 使用方式：
#   bash /opt/yao/scripts/build_h5.sh                 # 标准增量构建
#   NPM_REGISTRY=https://registry.npmjs.org bash ...  # 自定义 npm 源
#   SKIP_BACKEND_STOP=1 bash ...                      # 不停后端（内存充裕时）
# ============================================================
set -euo pipefail

# ===== 可配置参数 =====
INSTALL_DIR="${INSTALL_DIR:-/opt/yao}"          # 项目源码目录（git 仓库）
DEPLOY_DIR="${DEPLOY_DIR:-/opt/deploy/yao}"     # 本项目部署目录（backend compose）
FRONTEND_DIR="$INSTALL_DIR/frontend"
NODE_IMAGE="${NODE_IMAGE:-node:20-slim}"
NPM_REGISTRY="${NPM_REGISTRY:-https://registry.npmmirror.com}"
# 构建容器资源上限（低内存服务器防 OOM；node 堆另限 768MB）
BUILD_MEMORY="${BUILD_MEMORY:-1g}"
BUILD_MEMORY_SWAP="${BUILD_MEMORY_SWAP:-2g}"
BUILD_CPUS="${BUILD_CPUS:-1.5}"
SKIP_BACKEND_STOP="${SKIP_BACKEND_STOP:-0}"

# ===== 颜色与日志 =====
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log_info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
log_ok()    { echo -e "${GREEN}[ OK ]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
log_step()  { echo -e "\n${BLUE}========== $* ==========${NC}"; }

# ===== 1. 前置检查 =====
check_prerequisites() {
    log_step "前置检查"

    if [[ $EUID -ne 0 ]]; then
        log_error "请以 root 用户运行此脚本"
        exit 1
    fi

    if ! command -v docker &>/dev/null; then
        log_error "未检测到 Docker"
        exit 1
    fi

    if [[ ! -f "$FRONTEND_DIR/package.json" ]]; then
        log_error "未找到 $FRONTEND_DIR/package.json"
        exit 1
    fi

    if ! docker ps --format '{{.Names}}' | grep -q "^nginx$"; then
        log_warn "共享 nginx 容器未运行，构建后站点不会自动生效"
    fi

    log_ok "检查通过：源码 $FRONTEND_DIR"
}

# ===== 2. 停止后端容器（释放内存供构建使用） =====
stop_backend() {
    if [[ "$SKIP_BACKEND_STOP" == "1" ]]; then
        log_warn "SKIP_BACKEND_STOP=1，跳过停止后端"
        return 0
    fi
    log_step "停止 yao-backend（释放内存，nginx 保持运行不影响线上）"
    if docker ps --format '{{.Names}}' | grep -q "^yao-backend$"; then
        (cd "$DEPLOY_DIR" && docker compose stop backend)
        log_ok "yao-backend 已停止"
    else
        log_warn "yao-backend 未在运行，跳过"
    fi
}

# ===== 3. 构建 H5 前端 =====
build_h5() {
    log_step "构建 H5 前端（npm install --legacy-peer-deps && npm run build:h5）"
    log_info "资源限制：memory=$BUILD_MEMORY swap=$BUILD_MEMORY_SWAP cpus=$BUILD_CPUS | npm 源：$NPM_REGISTRY"

    # NODE_OPTIONS 限制 node 堆，防止 vite/rollup 在低内存服务器触发 OOM
    docker run --rm \
        --memory="$BUILD_MEMORY" \
        --memory-swap="$BUILD_MEMORY_SWAP" \
        --cpus="$BUILD_CPUS" \
        -v "$FRONTEND_DIR:/app:z" \
        -e NODE_OPTIONS="--max-old-space-size=768" \
        -w /app \
        "$NODE_IMAGE" \
        sh -c "npm install --registry=$NPM_REGISTRY --legacy-peer-deps && npm run build:h5"

    if [[ ! -f "$FRONTEND_DIR/dist/build/h5/index.html" ]]; then
        log_error "构建失败：未找到 $FRONTEND_DIR/dist/build/h5/index.html"
        exit 1
    fi
    log_ok "H5 构建完成：$(stat -c '%y' "$FRONTEND_DIR/dist/build/h5/index.html" | cut -d. -f1)"
}

# ===== 4. 恢复后端容器 =====
start_backend() {
    if [[ "$SKIP_BACKEND_STOP" == "1" ]]; then
        return 0
    fi
    log_step "恢复 yao-backend"
    (cd "$DEPLOY_DIR" && docker compose up -d backend)
    log_ok "yao-backend 已启动"
}

# ===== 5. 验证服务 =====
verify_service() {
    log_step "验证服务"

    # 后端健康（等待就绪，最多 60 秒）
    local i=0
    while [[ $i -lt 30 ]]; do
        if docker exec yao-backend curl -sf http://localhost:8000/health &>/dev/null; then
            log_ok "yao-backend /health → 200"
            break
        fi
        i=$((i + 1))
        sleep 2
    done
    if [[ $i -ge 30 ]]; then
        log_warn "yao-backend 健康检查未通过，请查看：docker logs yao-backend"
    fi

    # H5 静态资源经共享 nginx 可访问（Host 指向 yao 站点）
    if curl -sk -o /dev/null -w '%{http_code}' --max-time 10 \
        -H "Host: yao.wuzuniao.com" https://localhost/ | grep -q 200; then
        log_ok "H5 首页（经共享 nginx）→ HTTPS 200，新产物已生效"
    else
        log_warn "H5 首页访问异常，请检查 nginx 与 dist 挂载"
    fi

    # 后端经容器网络可达
    if docker exec nginx curl -sf -o /dev/null -w '%{http_code}' \
        --max-time 10 http://yao-backend:8000/health | grep -q 200; then
        log_ok "Backend（nginx → yao-backend:8000/health）→ 200"
    else
        log_warn "后端经容器网络访问异常"
    fi

    echo ""
    log_info "容器运行状态："
    docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "NAMES|nginx|mariadb|backend"
}

# ===== 主流程 =====
main() {
    echo -e "${BLUE}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   yao H5 前端增量构建与生效 (build_h5.sh)   ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════╝${NC}"

    check_prerequisites
    stop_backend
    build_h5
    start_backend
    verify_service

    echo ""
    log_ok "H5 前端更新完成"
}

main "$@"
