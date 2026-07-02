#!/bin/bash
# ============================================================
# Yao 后端一键部署脚本
# 适用环境：Rocky Linux 9.4 x86_64
# 功能：以容器形式部署 MariaDB + Python(FastAPI) + Nginx(HTTPS)
# 项目仓库：https://github.com/wuzuniao/yao.git
#
# 使用方式：
#   1. 将本脚本和证书文件 yao.wuzuniao.com_nginx.zip 上传到服务器
#   2. 以 root 执行：bash deploy.sh
#   3. 也可指定证书路径：CERT_ZIP_PATH=/path/to/yao.wuzuniao.com_nginx.zip bash deploy.sh
# ============================================================
set -e

# ============== 可配置参数（按需修改） ==============
PYTHON_VERSION="3.11"            # Python 容器版本
MARIADB_VERSION="10.11"          # MariaDB LTS 版本
NGINX_IMAGE="nginx:stable"       # Nginx 镜像

# Docker 镜像加速（Docker Hub 国内访问不稳定）
# 留空则自动配置 daemon.json 镜像加速器；填写则直接作为镜像前缀使用
# 例如：DOCKER_REGISTRY="docker.m.daocloud.io/library/"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-}"

INSTALL_DIR="/opt/yao"           # 项目克隆目录（会挂载到后端容器）
DEPLOY_DIR="${INSTALL_DIR}/deploy"  # 部署配置目录
REPO_URL="https://github.com/wuzuniao/yao.git"
BRANCH="master"

# GitHub 国内访问不稳定时使用的镜像源（按顺序尝试，留空则跳过）
# 也可通过环境变量 GITHUB_MIRROR 指定自定义镜像前缀
GITHUB_MIRRORS=(
  "https://gh-proxy.com"
  "https://ghproxy.net"
  "https://mirror.ghproxy.com"
)
# 若项目代码已手动上传到服务器，设置 LOCAL_PROJECT_DIR 指向其路径即可跳过克隆
# 例如：LOCAL_PROJECT_DIR=/tmp/yao bash deploy.sh
LOCAL_PROJECT_DIR="${LOCAL_PROJECT_DIR:-}"

DOMAIN="yao.wuzuniao.com"
CERT_ZIP_NAME="yao.wuzuniao.com_nginx.zip"

DB_NAME_MAIN="wuzuniao_yao"       # 业务数据库
DB_NAME_USER="wuzuniao_yonghu"    # 用户数据库
DB_USER="yao_backend"             # 后端数据库连接用户
DB_ROOT_PASSWORD="${DB_ROOT_PASSWORD:-}"  # 运行时自动生成
DB_PASSWORD="${DB_PASSWORD:-}"            # 运行时自动生成
# 若 MariaDB 数据目录存在旧数据导致 root 密码不匹配，设为 1 可清空数据目录重新初始化
# 警告：RESET_DB=1 会删除 /opt/yao/deploy/data/mariadb 下的全部数据！
RESET_DB="${RESET_DB:-0}"

# ============== 颜色与日志 ==============
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log_info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
log_ok()    { echo -e "${GREEN}[ OK ]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
log_step()  { echo -e "\n${BLUE}========== $* ==========${NC}"; }

# docker compose 辅助函数（在 DEPLOY_DIR 下执行，确保读取 .env）
dc() {
  (cd "$DEPLOY_DIR" && docker compose "$@")
}

# ============== 1. 前置检查 ==============
check_prerequisites() {
  log_step "前置检查"

  if [[ $EUID -ne 0 ]]; then
    log_error "请以 root 用户运行此脚本"
    exit 1
  fi
  log_ok "当前为 root 用户"

  local arch
  arch=$(uname -m)
  if [[ "$arch" != "x86_64" ]]; then
    log_warn "当前架构为 $arch，本脚本面向 x86_64 环境"
  else
    log_ok "系统架构：x86_64"
  fi

  if [[ -f /etc/rocky-release ]]; then
    log_ok "操作系统：$(cat /etc/rocky-release)"
  else
    log_warn "未检测到 Rocky Linux，脚本基于 Rocky Linux 9.4 编写，可能不完全兼容"
  fi
}

# ============== 2. 安装 Docker 及基础工具 ==============
install_docker() {
  log_step "检查并安装 Docker 与基础工具"

  # 基础工具
  for pkg in git openssl unzip curl; do
    if ! command -v "$pkg" &>/dev/null; then
      log_info "安装 $pkg ..."
      dnf install -y "$pkg"
    fi
  done
  log_ok "基础工具已就绪"

  # Docker
  if command -v docker &>/dev/null; then
    log_ok "Docker 已安装：$(docker --version)"
  else
    log_info "安装 Docker CE ..."
    dnf install -y dnf-plugins-core
    dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    systemctl enable --now docker
    log_ok "Docker 安装完成"
  fi

  systemctl is-active --quiet docker || systemctl start docker

  if docker compose version &>/dev/null; then
    log_ok "Docker Compose 可用：$(docker compose version)"
  else
    log_error "Docker Compose 插件不可用，请检查 docker-compose-plugin 安装"
    exit 1
  fi
}

# ============== 2.1 配置 Docker 镜像加速 ==============
setup_docker_mirror() {
  log_step "配置 Docker 镜像加速"

  # 如果用户指定了 DOCKER_REGISTRY，则直接使用该前缀，跳过 daemon.json 配置
  if [[ -n "$DOCKER_REGISTRY" ]]; then
    # 规范化：确保以 / 结尾
    [[ "$DOCKER_REGISTRY" != */ ]] && DOCKER_REGISTRY="${DOCKER_REGISTRY}/"
    log_ok "使用指定镜像前缀：$DOCKER_REGISTRY"
    return 0
  fi

  local daemon_json="/etc/docker/daemon.json"

  # 国内 Docker Hub 镜像加速器（按优先级排列）
  local mirrors
  if [[ -n "${DOCKER_MIRRORS:-}" ]]; then
    # 用户自定义镜像加速器（逗号分隔）
    IFS=',' read -ra mirrors <<< "$DOCKER_MIRRORS"
  else
    mirrors=(
      "https://docker.m.daocloud.io"
      "https://docker.1panel.live"
      "https://docker.unsee.tech"
      "https://docker.nju.edu.cn"
    )
  fi

  # 若已配置 registry-mirrors 则跳过
  if [[ -f "$daemon_json" ]] && grep -q "registry-mirrors" "$daemon_json" 2>/dev/null; then
    log_ok "daemon.json 已配置镜像加速器，跳过"
    return 0
  fi

  # 构建 JSON 镜像数组
  local mirror_json="["
  local first=true
  for m in "${mirrors[@]}"; do
    [[ "$first" == true ]] && first=false || mirror_json+=","
    mirror_json+="\"$m\""
  done
  mirror_json+="]"

  # 备份已有 daemon.json
  if [[ -f "$daemon_json" ]]; then
    cp "$daemon_json" "${daemon_json}.bak.$(date +%s)"
    log_info "已备份原 daemon.json"
  fi

  # 合并或创建 daemon.json
  if [[ -f "$daemon_json" ]] && command -v jq &>/dev/null; then
    jq --argjson m "$mirror_json" '. + {"registry-mirrors": $m}' "$daemon_json" > "${daemon_json}.tmp"
    mv "${daemon_json}.tmp" "$daemon_json"
  else
    cat > "$daemon_json" <<EOF
{
  "registry-mirrors": $mirror_json
}
EOF
  fi

  # 重启 Docker 生效
  systemctl restart docker
  sleep 3
  log_ok "Docker 镜像加速已配置并重启 Docker"
  log_info "加速器：${mirrors[*]}"
}

# ============== 2.2 预拉取容器镜像（带重试） ==============
pull_images() {
  log_step "预拉取容器镜像"

  local images=(
    "${DOCKER_REGISTRY}mariadb:${MARIADB_VERSION}"
    "${DOCKER_REGISTRY}python:${PYTHON_VERSION}-slim"
    "${DOCKER_REGISTRY}nginx:stable"
  )

  for img in "${images[@]}"; do
    log_info "拉取 $img ..."
    local ok=false
    for i in 1 2 3; do
      if docker pull "$img" 2>&1; then
        log_ok "$img 拉取成功"
        ok=true
        break
      fi
      [[ $i -lt 3 ]] && log_warn "第 $i 次拉取失败，5 秒后重试 ..." && sleep 5
    done
    if [[ "$ok" != true ]]; then
      log_error "镜像 $img 拉取失败（已重试 3 次）"
      log_warn "请手动配置可用镜像源后重试："
      echo "  方式一：设置镜像前缀  DOCKER_REGISTRY=docker.m.daocloud.io/library/ bash /opt/deploy.sh"
      echo "  方式二：自定义加速器  DOCKER_MIRRORS=https://your-mirror.com bash /opt/deploy.sh"
      echo "  方式三：使用代理      export https_proxy=http://127.0.0.1:7890 && bash /opt/deploy.sh"
      exit 1
    fi
  done
}

# ============== 3. 配置防火墙 ==============
setup_firewall() {
  log_step "配置防火墙"

  if systemctl is-active --quiet firewalld; then
    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-service=https
    firewall-cmd --reload
    log_ok "已开放 80/443 端口"
  else
    log_warn "firewalld 未运行，跳过防火墙配置（请确保 80/443 端口可访问）"
  fi
}

# ============== 4. 获取项目代码 ==============
clone_repo() {
  log_step "获取项目代码"

  # 优化 git 网络配置（缓解 SSL unexpected eof 问题）
  git config --global http.postBuffer 524288000  || true
  git config --global http.version HTTP/1.1      || true
  git config --global https.version HTTP/1.1     || true
  git config --global http.lowSpeedLimit 0       || true
  git config --global http.lowSpeedTime 999999   || true

  # --- 情况 A：项目目录已存在（.git 存在） ---
  if [[ -d "$INSTALL_DIR/.git" ]]; then
    log_info "项目目录已存在，执行 git pull ..."
    git -C "$INSTALL_DIR" pull origin "$BRANCH" || log_warn "git pull 失败，使用现有代码继续"
    return 0
  fi

  # --- 情况 B：项目目录已有代码但无 .git（手动上传的代码） ---
  if [[ -n "$LOCAL_PROJECT_DIR" && -d "$LOCAL_PROJECT_DIR" ]]; then
    log_info "使用本地项目目录：$LOCAL_PROJECT_DIR"
    mkdir -p "$(dirname "$INSTALL_DIR")"
    cp -a "$LOCAL_PROJECT_DIR" "$INSTALL_DIR"
    log_ok "项目代码已复制到 $INSTALL_DIR"
    return 0
  fi
  if [[ -d "$INSTALL_DIR" && -f "$INSTALL_DIR/backend/run.py" ]]; then
    log_ok "检测到 $INSTALL_DIR 已有项目代码（无 .git），直接使用"
    return 0
  fi

  # --- 情况 C：从远程克隆 ---
  mkdir -p "$(dirname "$INSTALL_DIR")"

  # 构建克隆源列表：原始 URL + 镜像加速
  local clone_urls=("$REPO_URL")
  local mirror
  for mirror in "${GITHUB_MIRRORS[@]}"; do
    clone_urls+=("${mirror}/${REPO_URL}")
  done
  # 支持用户通过环境变量 GITHUB_MIRROR 指定自定义镜像
  if [[ -n "${GITHUB_MIRROR:-}" ]]; then
    clone_urls=("${GITHUB_MIRROR}/${REPO_URL}" "${clone_urls[@]}")
  fi

  local url idx=1 total=${#clone_urls[@]}
  for url in "${clone_urls[@]}"; do
    log_info "[$idx/$total] 尝试克隆：$url"
    if git clone -b "$BRANCH" --depth 1 "$url" "$INSTALL_DIR" 2>&1; then
      log_ok "项目克隆成功（来源：$url）"
      # 补全完整历史（可选，浅克隆已足够部署）
      git -C "$INSTALL_DIR" fetch --unshallow 2>/dev/null || true
      return 0
    fi
    log_warn "[$idx/$total] 克隆失败，尝试下一个源 ..."
    rm -rf "$INSTALL_DIR"
    idx=$((idx + 1))
    sleep 2
  done

  # --- 所有远程克隆均失败 ---
  log_error "所有克隆源均失败，网络无法访问 GitHub"
  echo ""
  log_warn "请选择以下任一方式手动上传项目代码后重新运行脚本："
  echo ""
  echo "  方式一：在可访问 GitHub 的机器上下载 zip，上传到服务器后解压"
  echo "    # 本地机器下载："
  echo "    wget https://github.com/wuzuniao/yao/archive/refs/heads/master.zip -O yao.zip"
  echo "    # 上传并解压到服务器："
  echo "    unzip yao.zip -d /opt/"
  echo "    mv /opt/yao-master /opt/yao"
  echo "    # 然后重新运行：bash /opt/deploy.sh"
  echo ""
  echo "  方式二：通过 scp/rsync 直接上传项目目录"
  echo "    scp -r yao/ root@SERVER:/opt/yao"
  echo "    # 然后重新运行：bash /opt/deploy.sh"
  echo ""
  echo "  方式三：指定自定义镜像或代理"
  echo "    GITHUB_MIRROR=https://your-mirror.com bash /opt/deploy.sh"
  echo "    # 或设置 http 代理："
  echo "    export https_proxy=http://127.0.0.1:7890"
  echo "    bash /opt/deploy.sh"
  echo ""
  exit 1
}

# ============== 5. 密码管理（支持重复执行） ==============
load_or_generate_passwords() {
  log_step "准备数据库密码"

  local compose_env="$DEPLOY_DIR/.env"
  local backend_env="$INSTALL_DIR/backend/.env"

  # root 密码：优先从 compose .env 读取
  if [[ -z "$DB_ROOT_PASSWORD" && -f "$compose_env" ]]; then
    DB_ROOT_PASSWORD=$(grep -E "^DB_ROOT_PASSWORD=" "$compose_env" 2>/dev/null | cut -d= -f2- || true)
  fi
  if [[ -z "$DB_ROOT_PASSWORD" ]]; then
    DB_ROOT_PASSWORD=$(openssl rand -hex 16)
    log_info "已生成新的 MariaDB root 密码"
  else
    log_info "复用已有的 MariaDB root 密码"
  fi

  # 后端用户密码：优先从 backend/.env 的 DATABASE_URL 中提取
  if [[ -z "$DB_PASSWORD" && -f "$backend_env" ]]; then
    DB_PASSWORD=$(grep -E "^DATABASE_URL=" "$backend_env" 2>/dev/null \
      | sed -n 's|.*://[^:]*:\([^@]*\)@.*|\1|p' || true)
  fi
  if [[ -z "$DB_PASSWORD" ]]; then
    DB_PASSWORD=$(openssl rand -hex 16)
    log_info "已生成新的后端数据库用户密码"
  else
    log_info "复用已有的后端数据库用户密码"
  fi
}

# ============== 6. 配置 HTTPS 证书 ==============
setup_certs() {
  log_step "配置 HTTPS 证书"

  local cert_dir="$DEPLOY_DIR/certs"
  mkdir -p "$cert_dir"

  # 查找证书 zip
  local zip_path="${CERT_ZIP_PATH:-}"
  if [[ -z "$zip_path" ]]; then
    for dir in "$(pwd)" "$DEPLOY_DIR" "$INSTALL_DIR" /root /tmp /opt; do
      if [[ -f "$dir/$CERT_ZIP_NAME" ]]; then
        zip_path="$dir/$CERT_ZIP_NAME"
        break
      fi
    done
  fi

  if [[ -z "$zip_path" || ! -f "$zip_path" ]]; then
    log_warn "未找到证书文件 $CERT_ZIP_NAME"
    log_warn "请将该文件放到以下任一位置后重新运行：$DEPLOY_DIR / /root / /tmp / /opt"
    log_warn "或通过环境变量指定：CERT_ZIP_PATH=/path/to/$CERT_ZIP_NAME bash deploy.sh"
    log_warn "本次部署将生成临时自签名证书以供测试使用"

    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
      -keyout "$cert_dir/$DOMAIN.key" \
      -out "$cert_dir/$DOMAIN.pem" \
      -subj "/CN=$DOMAIN" 2>/dev/null
    chmod 600 "$cert_dir/$DOMAIN.key"
    chmod 644 "$cert_dir/$DOMAIN.pem"
    log_ok "已生成临时自签名证书"
    return
  fi

  log_info "找到证书文件：$zip_path"

  local tmp_dir
  tmp_dir=$(mktemp -d)
  unzip -o "$zip_path" -d "$tmp_dir" >/dev/null

  # 查找私钥（.key）
  local key_file
  key_file=$(find "$tmp_dir" -type f -name "*.key" | head -1)
  if [[ -z "$key_file" ]]; then
    log_error "证书包中未找到 .key 私钥文件"
    rm -rf "$tmp_dir"
    exit 1
  fi

  # 查找证书（.pem 或 .crt，排除 .key）
  local cert_file
  cert_file=$(find "$tmp_dir" -type f \( -name "*.pem" -o -name "*.crt" \) ! -name "*.key" | head -1)
  if [[ -z "$cert_file" ]]; then
    log_error "证书包中未找到 .pem/.crt 证书文件"
    rm -rf "$tmp_dir"
    exit 1
  fi

  cp "$key_file" "$cert_dir/$DOMAIN.key"
  cp "$cert_file" "$cert_dir/$DOMAIN.pem"
  chmod 600 "$cert_dir/$DOMAIN.key"
  chmod 644 "$cert_dir/$DOMAIN.pem"
  rm -rf "$tmp_dir"
  log_ok "证书配置完成：$cert_dir/$DOMAIN.{pem,key}"
}

# ============== 7. 生成后端 Dockerfile ==============
generate_dockerfile() {
  log_step "生成后端 Dockerfile"

  cat > "$DEPLOY_DIR/Dockerfile.backend" <<'EOF'
FROM __REGISTRY__python:__PY_VER__-slim

ENV TZ=Asia/Shanghai
ENV PYTHONUNBUFFERED=1

# asyncmy 编译需要 gcc 与 MySQL 客户端开发库；curl 用于健康检查
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend

# 构建时安装 Python 依赖（运行时代码通过卷挂载提供）
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

  sed -i \
    -e "s|__REGISTRY__|$DOCKER_REGISTRY|g" \
    -e "s|__PY_VER__|$PYTHON_VERSION|g" \
    "$DEPLOY_DIR/Dockerfile.backend"
  log_ok "Dockerfile 已生成：$DEPLOY_DIR/Dockerfile.backend"
}

# ============== 8. 生成 Nginx 配置（HTTPS 反向代理） ==============
generate_nginx_conf() {
  log_step "生成 Nginx 配置"

  mkdir -p "$DEPLOY_DIR/nginx"
  cat > "$DEPLOY_DIR/nginx/default.conf" <<'EOF'
# HTTP -> HTTPS 重定向
server {
    listen 80;
    server_name __DOMAIN__;
    return 301 https://$host$request_uri;
}

# HTTPS 反向代理到后端 FastAPI
server {
    listen 443 ssl;
    http2 on;
    server_name __DOMAIN__;

    ssl_certificate     /etc/nginx/certs/__DOMAIN__.pem;
    ssl_certificate_key /etc/nginx/certs/__DOMAIN__.key;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache   shared:SSL:10m;
    ssl_session_timeout 10m;

    client_max_body_size 20m;

    location / {
        proxy_pass http://backend:8000;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
EOF

  sed -i "s/__DOMAIN__/$DOMAIN/g" "$DEPLOY_DIR/nginx/default.conf"
  log_ok "Nginx 配置已生成：$DEPLOY_DIR/nginx/default.conf"
}

# ============== 9. 生成 docker-compose.yml ==============
generate_compose_file() {
  log_step "生成 docker-compose.yml"

  cat > "$DEPLOY_DIR/docker-compose.yml" <<'EOF'
services:
  mariadb:
    image: __REGISTRY__mariadb:__MARIADB_VER__
    container_name: yao-mariadb
    restart: unless-stopped
    environment:
      MARIADB_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
      TZ: Asia/Shanghai
    volumes:
      - __DEPLOY_DIR__/data/mariadb:/var/lib/mysql:z
    ports:
      - "127.0.0.1:3306:3306"
    networks:
      - yao-net
    healthcheck:
      test: ["CMD", "healthcheck.sh", "--connect", "--innodb_initialized"]
      interval: 10s
      timeout: 5s
      retries: 12
      start_period: 20s

  backend:
    build:
      context: __INSTALL_DIR__
      dockerfile: deploy/Dockerfile.backend
    container_name: yao-backend
    restart: unless-stopped
    volumes:
      # 以挂载本地目录方式将项目挂载到容器中运行
      - __INSTALL_DIR__:/app:z
    working_dir: /app/backend
    command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
    depends_on:
      mariadb:
        condition: service_healthy
    networks:
      - yao-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 40s

  nginx:
    image: __REGISTRY____NGINX_IMAGE__
    container_name: yao-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - __DEPLOY_DIR__/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro,z
      - __DEPLOY_DIR__/certs:/etc/nginx/certs:ro,z
    depends_on:
      - backend
    networks:
      - yao-net

networks:
  yao-net:
    driver: bridge
EOF

  sed -i \
    -e "s|__REGISTRY__|$DOCKER_REGISTRY|g" \
    -e "s|__MARIADB_VER__|$MARIADB_VERSION|g" \
    -e "s|__NGINX_IMAGE__|$NGINX_IMAGE|g" \
    -e "s|__INSTALL_DIR__|$INSTALL_DIR|g" \
    -e "s|__DEPLOY_DIR__|$DEPLOY_DIR|g" \
    "$DEPLOY_DIR/docker-compose.yml"
  log_ok "docker-compose.yml 已生成：$DEPLOY_DIR/docker-compose.yml"
}

# ============== 10. 生成 compose 环境变量文件 ==============
generate_compose_env() {
  cat > "$DEPLOY_DIR/.env" <<EOF
# Docker Compose 环境变量（由部署脚本自动生成，请勿提交 Git）
DB_ROOT_PASSWORD=$DB_ROOT_PASSWORD
EOF
  chmod 600 "$DEPLOY_DIR/.env"
  log_ok "Compose .env 已生成"
}

# ============== 11. 启动 MariaDB ==============
start_mariadb() {
  log_step "启动 MariaDB 容器"
  dc up -d mariadb
  log_ok "MariaDB 容器已启动"
}

# ============== 12. 等待 MariaDB 就绪 ==============
# 注意：MariaDB 容器自带的 healthcheck.sh --connect 与 mysqladmin ping 都只检测
# 服务是否存活，不校验密码。当数据目录已有旧数据时，MARIADB_ROOT_PASSWORD 会被
# 忽略，容器仍显示 healthy，但用新密码连接会报 Access denied。
# 因此这里分两阶段：先等容器健康，再用 mysql -uroot -e "SELECT 1" 校验凭据。
wait_for_mariadb() {
  log_info "等待 MariaDB 容器变为 healthy ..."

  local max=60 i=0 health=""
  while [[ $i -lt $max ]]; do
    health=$(docker inspect --format='{{.State.Health.Status}}' yao-mariadb 2>/dev/null || echo "")
    [[ "$health" == "healthy" ]] && break
    i=$((i + 1))
    sleep 2
  done

  if [[ "$health" != "healthy" ]]; then
    log_error "MariaDB 容器启动超时（120 秒未变为 healthy）"
    log_warn "请查看容器日志：docker logs yao-mariadb"
    exit 1
  fi
  log_ok "MariaDB 容器已健康"

  verify_mariadb_credentials
}

# 校验 root 凭据；失败时根据 RESET_DB 决定重置数据目录还是退出
verify_mariadb_credentials() {
  log_info "校验 MariaDB root 凭据 ..."
  if docker exec -e MYSQL_PWD="$DB_ROOT_PASSWORD" yao-mariadb \
      mysql -uroot -e "SELECT 1" &>/dev/null; then
    log_ok "MariaDB root 凭据校验通过"
    return 0
  fi

  log_warn "root 凭据校验失败（密码与现有数据目录不匹配）"

  local data_dir="$DEPLOY_DIR/data/mariadb"
  local has_stale_data=false
  if [[ -d "$data_dir" ]] && [[ -n "$(ls -A "$data_dir" 2>/dev/null)" ]]; then
    has_stale_data=true
  fi

  if [[ "$RESET_DB" == "1" ]]; then
    if [[ "$has_stale_data" == true ]]; then
      log_warn "RESET_DB=1：正在清空 MariaDB 数据目录并重新初始化 ..."
      log_warn "  清空目录：$data_dir （其中数据将丢失）"
      docker rm -f yao-mariadb &>/dev/null || true
      rm -rf "${data_dir:?}/"* 2>/dev/null || true
      rm -rf "${data_dir:?}/".[!.]* 2>/dev/null || true
      dc up -d mariadb
      # 等待重新初始化完成
      local j=0 h=""
      while [[ $j -lt 60 ]]; do
        h=$(docker inspect --format='{{.State.Health.Status}}' yao-mariadb 2>/dev/null || echo "")
        [[ "$h" == "healthy" ]] && break
        j=$((j + 1))
        sleep 2
      done
      if [[ "$h" != "healthy" ]]; then
        log_error "重新初始化后 MariaDB 仍未就绪，请查看 docker logs yao-mariadb"
        exit 1
      fi
      if docker exec -e MYSQL_PWD="$DB_ROOT_PASSWORD" yao-mariadb \
          mysql -uroot -e "SELECT 1" &>/dev/null; then
        log_ok "重新初始化后 root 凭据校验通过"
        return 0
      fi
      log_error "重新初始化后凭据仍失败，请检查 docker logs yao-mariadb"
      exit 1
    else
      # 数据目录为空但凭据失败：可能是初始化未完成，再多等一会
      log_warn "RESET_DB=1 但数据目录为空，继续等待初始化完成 ..."
      local k=0
      while [[ $k -lt 15 ]]; do
        sleep 2
        if docker exec -e MYSQL_PWD="$DB_ROOT_PASSWORD" yao-mariadb \
            mysql -uroot -e "SELECT 1" &>/dev/null; then
          log_ok "MariaDB root 凭据校验通过"
          return 0
        fi
        k=$((k + 1))
      done
      log_error "MariaDB root 凭据持续校验失败，请查看 docker logs yao-mariadb"
      exit 1
    fi
  fi

  # 未启用 RESET_DB：给出明确的重置指引
  log_error "MariaDB root 凭据校验失败，无法继续初始化数据库"
  echo ""
  log_warn "原因：MariaDB 数据目录已有旧数据，忽略了 MARIADB_ROOT_PASSWORD 环境变量"
  log_warn "      （mysqladmin ping / healthcheck.sh --connect 只检测服务存活，不校验密码）"
  echo ""
  log_warn "解决方案（任选其一）："
  echo "  方式一（推荐，清空旧数据库重新初始化）："
  echo "    RESET_DB=1 bash /opt/deploy.sh"
  echo ""
  echo "  方式二（手动清理后重跑）："
  echo "    docker compose -f $DEPLOY_DIR/docker-compose.yml down"
  echo "    rm -rf $data_dir/*"
  echo "    bash /opt/deploy.sh"
  echo ""
  echo "  方式三（若记得旧 root 密码，复用旧密码继续）："
  echo "    DB_ROOT_PASSWORD='旧密码' bash /opt/deploy.sh"
  echo ""
  exit 1
}

# ============== 13. 初始化数据库（建库 + 建表） ==============
init_databases() {
  log_step "初始化数据库"

  local sql_dir="$INSTALL_DIR/backend/sql"

  # 幂等检查：若业务库已有表则跳过
  local table_count
  table_count=$(docker exec -e MYSQL_PWD="$DB_ROOT_PASSWORD" yao-mariadb \
    mysql -uroot -N -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$DB_NAME_MAIN'" 2>/dev/null || echo 0)

  if [[ "$table_count" -gt 0 ]]; then
    log_info "数据库 $DB_NAME_MAIN 已有表结构，跳过 SQL 导入"
    return 0
  fi

  # 导入业务库
  if [[ -f "$sql_dir/create_yao_db.sql" ]]; then
    log_info "导入 $DB_NAME_MAIN 数据库结构与表 ..."
    docker exec -i -e MYSQL_PWD="$DB_ROOT_PASSWORD" yao-mariadb \
      mysql -uroot < "$sql_dir/create_yao_db.sql"
    log_ok "$DB_NAME_MAIN 导入完成"
  else
    log_warn "未找到 $sql_dir/create_yao_db.sql，跳过"
  fi

  # 导入用户库
  if [[ -f "$sql_dir/create_user_db.sql" ]]; then
    log_info "导入 $DB_NAME_USER 数据库结构与表 ..."
    docker exec -i -e MYSQL_PWD="$DB_ROOT_PASSWORD" yao-mariadb \
      mysql -uroot < "$sql_dir/create_user_db.sql"
    log_ok "$DB_NAME_USER 导入完成"
  else
    log_warn "未找到 $sql_dir/create_user_db.sql，跳过"
  fi
}

# ============== 14. 创建后端专用数据库用户 ==============
create_db_user() {
  log_step "创建后端数据库连接用户"

  docker exec -i -e MYSQL_PWD="$DB_ROOT_PASSWORD" yao-mariadb mysql -uroot <<EOF
CREATE USER IF NOT EXISTS '$DB_USER'@'%' IDENTIFIED BY '$DB_PASSWORD';
ALTER USER '$DB_USER'@'%' IDENTIFIED BY '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON $DB_NAME_MAIN.*  TO '$DB_USER'@'%';
GRANT ALL PRIVILEGES ON $DB_NAME_USER.* TO '$DB_USER'@'%';
FLUSH PRIVILEGES;
EOF

  log_ok "后端用户 '$DB_USER' 已创建并授予 $DB_NAME_MAIN / $DB_NAME_USER 全部权限"
}

# ============== 15. 生成后端 .env（更新数据库连接到环境变量） ==============
generate_backend_env() {
  log_step "生成后端环境变量配置"

  local env_file="$INSTALL_DIR/backend/.env"

  # 保留已有的 SMTP / 微信配置（若 .env 已存在）
  local smtp_user="" smtp_pass="" wx_appid="" wx_secret=""
  if [[ -f "$env_file" ]]; then
    smtp_user=$(grep -E "^SMTP_USER="     "$env_file" 2>/dev/null | cut -d= -f2- || true)
    smtp_pass=$(grep -E "^SMTP_PASSWORD=" "$env_file" 2>/dev/null | cut -d= -f2- || true)
    wx_appid=$(grep -E "^WX_APPID="       "$env_file" 2>/dev/null | cut -d= -f2- || true)
    wx_secret=$(grep -E "^WX_APP_SECRET=" "$env_file" 2>/dev/null | cut -d= -f2- || true)
    cp "$env_file" "${env_file}.bak.$(date +%s)"
    log_info "已备份原 .env，并保留 SMTP / 微信配置"
  fi

  # 生成 AES-256-GCM 加密密钥
  local enc_key
  enc_key=$(openssl rand -base64 32)

  # DATABASE_URL 使用后端专用用户连接 mariadb 容器（服务名 mariadb）
  local db_url="mysql+asyncmy://${DB_USER}:${DB_PASSWORD}@mariadb:3306/${DB_NAME_MAIN}?charset=utf8mb4"

  cat > "$env_file" <<EOF
# ============================================================
# 后端环境变量（由部署脚本自动生成）
# 生成时间：$(date '+%Y-%m-%d %H:%M:%S')
# ============================================================
# 数据库连接（使用后端专用用户，连接 mariadb 容器服务名）
DATABASE_URL=${db_url}

# 腾讯企业邮 SMTP 配置（发送注册验证码邮件，请按需填写）
SMTP_HOST=smtp.exmail.qq.com
SMTP_PORT=465
SMTP_USER=${smtp_user}
SMTP_PASSWORD=${smtp_pass}
SMTP_SENDER_NAME=无足鸟

# 微信小程序配置（微信一键登录，请按需填写）
WX_APPID=${wx_appid}
WX_APP_SECRET=${wx_secret}

# 数据加密密钥（AES-256-GCM，base64 编码 32 字节，请妥善保管）
ENCRYPTION_SECRET_KEY=${enc_key}
EOF

  chmod 600 "$env_file"
  log_ok "后端 .env 已生成：$env_file"
  log_info "DATABASE_URL 用户：$DB_USER  →  连接 mariadb:3306/$DB_NAME_MAIN"
}

# ============== 16. 构建并启动后端与 Nginx ==============
start_backend_nginx() {
  log_step "构建并启动后端与 Nginx 容器"
  dc up -d --build backend nginx
  log_ok "后端与 Nginx 容器已启动"
}

# ============== 17. 验证部署 ==============
verify_deployment() {
  log_step "验证部署"

  # 等待后端健康
  log_info "等待后端服务就绪 ..."
  local max=30 i=0
  while [[ $i -lt $max ]]; do
    if docker exec yao-backend curl -sf http://localhost:8000/health &>/dev/null; then
      log_ok "后端健康检查通过 /health → {\"status\":\"ok\"}"
      break
    fi
    i=$((i + 1))
    sleep 2
  done
  if [[ $i -ge $max ]]; then
    log_warn "后端健康检查未通过，请查看日志：docker logs yao-backend"
  fi

  # Nginx 配置检查
  if docker exec yao-nginx nginx -t &>/dev/null; then
    log_ok "Nginx 配置语法正确"
  else
    log_warn "Nginx 配置检查失败，请查看日志：docker logs yao-nginx"
  fi

  echo ""
  log_info "容器运行状态："
  docker ps --filter "name=yao-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

# ============== 18. 输出部署摘要 ==============
print_summary() {
  echo ""
  echo -e "${GREEN}================================================${NC}"
  echo -e "${GREEN}  Yao 后端部署完成${NC}"
  echo -e "${GREEN}================================================${NC}"
  cat <<EOF

  项目目录：       $INSTALL_DIR
  部署配置目录：   $DEPLOY_DIR

  数据库信息：
    MariaDB 版本：    $MARIADB_VERSION
    业务数据库：      $DB_NAME_MAIN
    用户数据库：      $DB_NAME_USER
    后端连接用户：    $DB_USER
    后端用户密码：    $DB_PASSWORD
    root 密码：       $DB_ROOT_PASSWORD

  容器服务：
    MariaDB  →  yao-mariadb  (内部 3306，仅本机可访问)
    Backend  →  yao-backend  (内部 8000)
    Nginx    →  yao-nginx    (对外 80/443)

  访问地址：
    HTTPS：          https://$DOMAIN
    健康检查：        https://$DOMAIN/health
    API 入口：        https://$DOMAIN/api/v1

  常用命令（在 $DEPLOY_DIR 下执行）：
    查看全部日志：    docker compose logs -f
    查看后端日志：    docker logs -f yao-backend
    重启全部服务：    docker compose restart
    停止全部服务：    docker compose down
    查看运行状态：    docker compose ps

  注意事项：
    1. 请在 $INSTALL_DIR/backend/.env 中填写 SMTP 和微信小程序配置
    2. root 密码保存在 $DEPLOY_DIR/.env，后端用户密码保存在 $INSTALL_DIR/backend/.env
    3. 更新代码：cd $INSTALL_DIR && git pull，然后 docker compose -f $DEPLOY_DIR/docker-compose.yml restart backend
    4. 如遇 SELinux 导致的挂载问题，可执行 setenforce 0 临时关闭后重试

EOF
}

# ============== 主流程 ==============
main() {
  echo -e "${BLUE}╔══════════════════════════════════════════════╗${NC}"
  echo -e "${BLUE}║   Yao 后端一键部署脚本  (Rocky Linux 9.4)   ║${NC}"
  echo -e "${BLUE}╚══════════════════════════════════════════════╝${NC}"

  check_prerequisites
  install_docker
  setup_docker_mirror
  setup_firewall
  clone_repo

  # 创建部署目录结构
  mkdir -p "$DEPLOY_DIR"/{nginx,certs,data/mariadb}

  load_or_generate_passwords
  setup_certs
  generate_dockerfile
  generate_nginx_conf
  generate_compose_file
  generate_compose_env

  # 预拉取镜像（在启动容器前确保镜像可用）
  pull_images

  start_mariadb
  wait_for_mariadb
  init_databases
  create_db_user
  generate_backend_env

  start_backend_nginx
  verify_deployment
  print_summary
}

main "$@"
