#!/bin/bash
# =============================================================================
# RuoYi FastAPI 启动脚本
#   ./start-dev.sh            本地开发模式（本地前后端 + Docker MySQL/Redis）
#   ./start-dev.sh --docker   Docker 容器模式（全容器，模拟生产，按需 build）
#
# 改代码后的行为约定：
#   - 本地模式（默认）：前端 Vite HMR 热更新，后端 uvicorn --reload 自动重载
#     → 改前端代码保存即生效；改后端代码保存即生效
#   - Docker 模式（--docker）：脚本用 `docker compose up -d --build` 启动，
#     Docker 按构建上下文 hash 判断是否需要 rebuild；前端 nginx serve
#     构建产物不是热更新 → 必须重新跑 start-dev.sh --docker 触发 rebuild
#     → 改前端/后端代码后再次执行即可，无需手动 `build --no-cache`
# =============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/ruoyi-fastapi-backend"
FRONTEND_DIR="$PROJECT_ROOT/ruoyi-fastapi-frontend"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.my.yml"
ENV_FILE="$BACKEND_DIR/.env.dev"
ENV_LOCAL_FILE="$BACKEND_DIR/.env.local"

# ---- 颜色 ----
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC}  $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step()  { echo -e "${CYAN}[STEP]${NC}  $1"; }
log_mode()  { echo -e "${BOLD}${CYAN}$1${NC}"; }

check_cmd() {
  if ! command -v "$1" &> /dev/null; then
    log_error "命令 '$1' 未找到，请先安装。"
    exit 1
  fi
}

# ---- 检查工具 ----
check_docker() {
  if ! docker info &> /dev/null; then
    log_error "Docker 未运行，请先启动 Docker Desktop。"
    exit 1
  fi
}

# 镜像是否存在（任意 tag 都算存在）
image_exists() {
  local image="$1"
  docker image inspect "$image" &>/dev/null
}

# ---- Docker 容器管理 ----
# 全部 5 个容器（本地模式和 Docker 模式都会用到 MySQL/Redis）
ALL_CONTAINERS="ruoyi-mysql ruoyi-redis ruoyi-frontend ruoyi-backend-my ruoyi-pg"

is_container_running() {
  docker ps --filter "name=$1" --format '{{.Names}}' 2>/dev/null | grep -q "^${1}$"
}

stop_all_containers() {
  for name in $ALL_CONTAINERS; do
    if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q "^${name}$"; then
      if is_container_running "$name"; then
        log_warn "  停止容器: $name"
        docker rm -f "$name" > /dev/null 2>&1
      fi
    fi
  done
}

# 检查前端 dist 是否过期（源码比 dist 新 → 过期）
# 返回值：0 过期，1 不需要重建
frontend_dist_stale() {
  local dist="$FRONTEND_DIR/dist"
  [ ! -d "$dist" ] && return 0
  # 找 src 或 package.json 中比 dist 最新的 index.html 更新的文件
  local newer
  newer=$(find -L "$FRONTEND_DIR/src" "$FRONTEND_DIR/package.json" "$FRONTEND_DIR/index.html" "$FRONTEND_DIR/vite.config.*" \
    -type f -newer "$dist/index.html" 2>/dev/null | head -1)
  [ -n "$newer" ]
}

# Docker 模式：自动构建/提示前端 dist
ensure_frontend_dist() {
  if ! frontend_dist_stale; then
    log_info "  前端 dist: 最新，跳过构建 ✓"
    return 0
  fi

  if [ ! -d "$FRONTEND_DIR/dist" ]; then
    log_warn "  前端 dist 缺失"
  else
    log_warn "  前端源码比 dist 新，需要重新构建"
  fi

  local ans
  read -r -p "  是否现在自动构建前端 dist? [Y/n] " ans
  case "$ans" in
    [nN]|[nN][oO])
      log_warn "  跳过构建，Docker 镜像里将使用现有（可能过期）的 dist"
      return 0
      ;;
  esac

  log_info "  构建前端 dist..."
  cd "$FRONTEND_DIR"
  if [ ! -d "node_modules" ]; then
    log_info "  安装前端依赖..."
    npm install --no-audit --no-fund
  fi
  npm run build:docker
  cd "$PROJECT_ROOT"
  log_info "  前端 dist 构建完成 ✓"
}

# ---- 本地进程管理 ----
is_port_in_use() {
  if command -v lsof &> /dev/null; then
    lsof -i :"$1" > /dev/null 2>&1
  elif command -v ss &> /dev/null; then
    ss -tan "sport = :$1" 2>/dev/null | grep -q ESTABLISHED\|LISTEN
  else
    return 1
  fi
}

is_port_listening() {
  if command -v lsof &> /dev/null; then
    lsof -i :"$1" -sTCP:LISTEN > /dev/null 2>&1
  elif command -v ss &> /dev/null; then
    ss -tlnp "sport = :$1" 2>/dev/null | grep -q LISTEN
  else
    return 1
  fi
}

# 获取占用端口的所有 PID（不管状态）
get_port_pids() {
  if command -v lsof &> /dev/null; then
    lsof -ti :"$1" 2>/dev/null
  fi
}

_stop_by_port() {
  local port=$1
  local pids
  pids=$(get_port_pids "$port")
  if [ -n "$pids" ]; then
    echo "$pids" | tr ' ' '\n' | while read pid; do
      [ -n "$pid" ] && kill -9 "$pid" 2>/dev/null || true
    done
  fi
}

stop_local_by_port() {
  local port=$1
  local name=$2
  if is_port_in_use "$port"; then
    log_warn "  停止本地进程 (port=$port): $name"
    _stop_by_port "$port"
    sleep 1
  fi
}

stop_local_processes() {
  stop_local_by_port 9099  "后端 (uvicorn)"
  stop_local_by_port 8080    "前端 dev server (npm)"
  stop_local_by_port 12580 "前端 dev server (npm)"
  stop_local_by_port 13306 "MySQL (host port)"
  stop_local_by_port 16379 "Redis (host port)"
}

# ---- 清理残留 PID 文件 ----
clean_pid() {
  local pid_file="$BACKEND_DIR/.backend.pid"
  if [ -f "$pid_file" ]; then
    local pid=$(cat "$pid_file")
    if [ -n "$pid" ] && ! kill -0 "$pid" 2>/dev/null; then
      rm -f "$pid_file"
    fi
  fi
}

# ---- 清理被污染的 ruoyi-network ----
# 检测同名网络 ruoyi-network 是否存在：
#   - 不存在：直接返回
#   - 存在且是 compose 创建（带 com.docker.compose.network=ruoyi-network 标签）：保留
#   - 存在但是孤儿（无标签，可能是裸 docker network create 出来的）：删，让 compose 重建
#   - 存在但被容器占用：拒绝并提示，让用户手动处理
ensure_clean_ruoyi_network() {
  local net_name="ruoyi-network"

  # 网络不存在：什么都不做，让 compose 自己创建
  if ! docker network ls --format '{{.Name}}' 2>/dev/null | grep -qx "$net_name"; then
    return 0
  fi

  # 网络存在，检查是否有容器占用
  local using
  using=$(docker network inspect -f '{{range .Containers}}{{.Name}} {{end}}' "$net_name" 2>/dev/null | xargs)
  if [ -n "$using" ]; then
    log_warn "  $net_name 仍被容器占用: $using"
    log_warn "    请先停掉这些容器（生产容器不要用本脚本停），再重试"
    return 1
  fi

  # 网络存在，检查是否有 compose 标签
  local label
  label=$(docker network inspect -f '{{index .Labels "com.docker.compose.network"}}' "$net_name" 2>/dev/null || echo "")
  if [ -n "$label" ]; then
    # 是 compose 创建的（如本 compose 之前 down 残留），保留
    return 0
  fi

  # 孤儿网络（无标签），自动清理
  log_warn "  发现孤儿网络 $net_name（无 compose 标签，可能是裸 docker network create 创建）"
  log_info "  自动删除，让 docker compose 重新创建..."
  docker network rm "$net_name" > /dev/null 2>&1 || {
    log_error "  删除孤儿网络失败，请手动执行: docker network rm $net_name"
    return 1
  }
  log_info "  孤儿网络已清理 ✓"
  return 0
}

# =============================================================================
# 模式 A：本地开发模式
#   - Docker: MySQL + Redis
#   - 本地:  后端 (9099) + 前端 dev server (80)
# =============================================================================
run_local_mode() {
  log_mode ""
  log_mode "========================================"
  log_mode "  本地开发模式"
  log_mode "========================================"
  echo ""

  check_cmd docker
  check_cmd python3
  check_cmd npm
  check_docker

  # ---- 互斥：停止 Docker 前后端容器 ----
  log_step "互斥检查：停止 Docker 前后端容器..."
  for name in ruoyi-frontend ruoyi-backend-my; do
    if is_container_running "$name"; then
      log_warn "  停止冲突容器: $name"
      docker rm -f "$name" > /dev/null 2>&1
    fi
  done
  echo "  ✓ 无冲突"

# ---- 网络准备 ----
  # 关键设计：local 模式用裸 `docker run --network ruoyi-network` 启动 MySQL/Redis，
  # 所以网络必须在脚本里提前建好。但必须带 compose 标签，否则下次 docker mode 的
  # `docker compose up` 会拒绝（报 "incorrect label"）。
  ensure_clean_ruoyi_network
  if ! docker network ls --format '{{.Name}}' 2>/dev/null | grep -qx "ruoyi-network"; then
    log_info "  创建 ruoyi-network（带 compose 标签）..."
    docker network create \
      --label com.docker.compose.project=ruoyi \
      --label com.docker.compose.network=ruoyi-network \
      ruoyi-network > /dev/null 2>&1
  fi

  # ---- 启动 MySQL + Redis ----
  log_step "1/3 - 启动 MySQL + Redis..."
  for name in ruoyi-mysql ruoyi-redis; do
    if is_container_running "$name"; then
      log_info "  $name: 已在运行，跳过"
    else
      log_info "  启动 $name..."
      docker start "$name" 2>/dev/null || docker run -d \
        --name "$name" \
        --network ruoyi-network \
        --restart unless-stopped \
        $([ "$name" = "ruoyi-mysql" ] && echo "-e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=ruoyi-fastapi -p 13306:3306 \
          -v $PROJECT_ROOT/ruoyi-fastapi-backend/sql/00-bootstrap.sql:/docker-entrypoint-initdb.d/00-bootstrap.sql \
          -v $PROJECT_ROOT/mysql-conf/charset.cnf:/etc/mysql/conf.d/charset.cnf:ro" || echo "-p 16379:6379") \
        $([ "$name" = "ruoyi-mysql" ] && echo "mysql:8.0 --character-set-server=utf8mb4 --collation-server=utf8mb4_general_ci --skip-character-set-client-handshake=1" || echo "redis:latest")
    fi
  done

  # 等待端口就绪
  for name in ruoyi-mysql ruoyi-redis; do
    retries=30
    while [ $retries -gt 0 ]; do
      if is_container_running "$name"; then
        break
      fi
      retries=$((retries - 1)); sleep 2
    done
    if [ $retries -eq 0 ]; then
      log_error "$name 启动失败"
      exit 1
    fi
  done
  sleep 2
  log_info "  MySQL + Redis 就绪 ✓"

  # ---- schema/seed 迁移状态展示（v4.0 起由 Alembic 接管） ----
  # - 删卷重建时，MySQL 容器首次启动会跑 00-bootstrap.sql 自动 CREATE DATABASE
  # - backend 启动时 server.py 会自动执行 alembic upgrade head，应用所有未执行的迁移
  # - 这里打印当前数据库的 alembic 版本，便于排查「未应用」/「已 latest」
  if is_container_running "ruoyi-mysql"; then
    # 仅探测 ruoyi-fastapi 数据库是否存在（避免 .env 中无密码等连接问题导致整个启动卡住）
    if LANG=C docker exec ruoyi-mysql mysql --default-character-set=utf8mb4 \
        -uroot -proot -N -B \
        -e "SHOW DATABASES LIKE 'ruoyi-fastapi'" 2>/dev/null | grep -q '^ruoyi-fastapi$'; then
      log_info "  数据库 ruoyi-fastapi: 已建 ✓"
      log_info "  schema/seed 演进将由 backend 启动时 alembic upgrade head 自动应用 ✓"
      log_info "  （查看当前版本: cd ruoyi-fastapi-backend && alembic -c alembic.ini current）"
    else
      log_warn "  数据库 ruoyi-fastapi 不存在！可能原因："
      log_warn "    1) MySQL data 卷非首次启动（initdb.d 仅首次启动生效）→ 需 docker rm -f ruoyi-mysql + 删卷重建"
      log_warn "    2) 或者：手动 CREATE DATABASE ruoyi-fastapi（alembic 会自动建表）"
    fi
  fi

  # ---- MySQL 字符集自检（防双重 UTF-8 编码问题） ----
  if is_container_running "ruoyi-mysql"; then
    local charset_raw charset
    charset_raw=$(LANG=C docker exec ruoyi-mysql mysql --default-character-set=utf8mb4 \
      -uroot -proot -N -B \
      -e "SHOW VARIABLES WHERE Variable_name='character_set_client'" 2>&1)
    # SHOW VARIABLES 输出两列（name\tvalue），只取 value 列；避免 tr -d '[:space:]'
    # 把 name 和 value 拼到一起造成误判（如 "character_set_clientutf8mb4"）。
    charset=$(echo "$charset_raw" | tail -n 1 | awk -F'\t' '{print $2}')
    if [ "$charset" != "utf8mb4" ]; then
      log_error "MySQL character_set_client=[${charset}]（期望 utf8mb4）"
      log_error "完整返回值（用于诊断）："
      echo "$charset_raw" | sed 's/^/    /'
      log_error "可能原因：mysql-conf/charset.cnf 未挂载或被忽略"
      exit 1
    fi
    log_info "  MySQL 字符集自检: character_set_client=utf8mb4 ✓"
  fi

  # ---- 启动后端 ----
  log_step "2/3 - 启动后端..."
  clean_pid

  # 停止已有进程
  stop_local_by_port 9099 "后端"

  # 再次确保端口已释放（对付僵尸进程）
  if is_port_listening 9099; then
    log_warn "  端口仍被占用，强制释放..."
    _stop_by_port 9099
    sleep 2
  fi

  if [ ! -d "$BACKEND_DIR/venv" ]; then
    log_info "  创建 Python 虚拟环境..."
    python3 -m venv "$BACKEND_DIR/venv"
    source "$BACKEND_DIR/venv/bin/activate"
    cd "$BACKEND_DIR"
    pip install -q --upgrade pip
    pip install -q -e . 2>&1 | tail -3
    pip install -q -r "$BACKEND_DIR/requirements.txt" 2>&1 | tail -3
  fi

  mkdir -p "$BACKEND_DIR/logs"
  cd "$BACKEND_DIR"

  # 合并 env 文件：.env.local 覆盖 .env.dev
  cat "$ENV_FILE" "$ENV_LOCAL_FILE" > "$BACKEND_DIR/.env.merged"

  log_info "  后端启动前检查..."
  source "$BACKEND_DIR/venv/bin/activate"
  hash -r 2>/dev/null || true
  ruoyi app doctor --env=dev --use-merged || log_warn "  检查有警告，继续启动..."

  log_info "  启动后端 (uvicorn)..."
  nohup env PYTHONIOENCODING=utf-8 LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 \
    uvicorn app:app \
    --host 0.0.0.0 \
    --port 9099 \
    --reload \
    --env-file "$BACKEND_DIR/.env.merged" \
    > "$BACKEND_DIR/logs/backend.log" 2>&1 &

  BACKEND_PID=$!
  echo "$BACKEND_PID" > "$BACKEND_DIR/.backend.pid"
  log_info "  后端 PID=$BACKEND_PID"

  retries=30
  while [ $retries -gt 0 ]; do
    if is_port_listening 9099; then break; fi
    retries=$((retries - 1)); sleep 1
  done
  if [ $retries -eq 0 ]; then
    log_warn "  后端启动超时，最后尝试强制释放端口..."
    _stop_by_port 9099
    sleep 2
    log_info "  重试后端启动..."
    nohup env PYTHONIOENCODING=utf-8 LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 \
      uvicorn app:app \
      --host 0.0.0.0 \
      --port 9099 \
      --reload \
      --env-file "$BACKEND_DIR/.env.merged" \
      > "$BACKEND_DIR/logs/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo "$BACKEND_PID" > "$BACKEND_DIR/.backend.pid"
    sleep 5
    if is_port_listening 9099; then
      log_info "  后端就绪 (PID=$BACKEND_PID) ✓"
    else
      log_error "  后端启动失败，请查看日志: $BACKEND_DIR/logs/backend.log"
    fi
  else
    log_info "  后端就绪 (PID=$BACKEND_PID) ✓"
  fi

  # ---- 展示 alembic upgrade head 结果（从 backend.log 抓取） ----
  sleep 2
  if [ -f "$BACKEND_DIR/logs/backend.log" ]; then
    alembic_lines=$(grep -E "alembic upgrade head|Running upgrade|^✅.*alembic|^❌.*alembic" \
      "$BACKEND_DIR/logs/backend.log" | head -10)
    if [ -n "$alembic_lines" ]; then
      log_info "  ── Alembic 迁移结果 ──"
      echo "$alembic_lines" | sed 's/^/    /'
    fi
  fi

  # ---- 启动前端 ----
  log_step "3/3 - 启动前端..."
  stop_local_by_port 8080 "前端"

  cd "$FRONTEND_DIR"
  if [ ! -d "node_modules" ]; then
    log_info "  安装前端依赖..."
    npm install
  fi

  FRONTEND_PORT=8080
  nohup npm run dev -- --port "$FRONTEND_PORT" > "$FRONTEND_DIR/.vite.log" 2>&1 &
  FRONTEND_PID=$!
  log_info "  前端 PID=$FRONTEND_PID（如需停止：kill $FRONTEND_PID）"
  log_info "  前端地址: http://localhost:$FRONTEND_PORT"
  log_info "  前端本地开发就绪 ✓"

  echo ""
  echo "============================================"
  log_mode "  本地开发模式 - 启动完成"
  echo "============================================"
  echo "  前端:     http://localhost:$FRONTEND_PORT"
  echo "  后端:     http://127.0.0.1:9099/dev-api"
  echo "  API 文档: http://127.0.0.1:9099/dev-api/docs"
  echo "  后端日志: $BACKEND_DIR/logs/backend.log"
  echo "============================================"
}

# =============================================================================
# 模式 B：Docker 容器模式（模拟生产环境）
#   - 停止所有本地进程
#   - docker compose up -d 全部 5 个容器
# =============================================================================
run_docker_mode() {
  log_mode ""
  log_mode "========================================"
  log_mode "  Docker 容器模式"
  log_mode "========================================"
  echo ""

  check_cmd docker
  check_docker

  # ---- 互斥：停止所有本地进程 ----
  log_step "互斥检查：停止所有本地进程..."
  stop_local_processes
  echo "  ✓ 无冲突"

# ---- 网络准备 ----
  # 关键设计：docker 模式让 docker compose 自己创建/管理网络（带 compose 标签）。
  # 脚本只负责清理"无标签孤儿网络"（老版本脚本裸 docker network create 留下的），
  # 真正的网络创建交给 `docker compose up`。
  ensure_clean_ruoyi_network

  # ---- 清理并启动 ----
  # 智能构建策略：
  #   1. ruoyi-frontend / ruoyi-backend-my 任一镜像不存在 → 必须 build
  #   2. 镜像都存在 → 默认复用现有镜像（秒级 up -d），不传 --build
  #   3. 用户显式传 --rebuild → 强制全部重建
  log_step "检查镜像并启动..."
  local need_build_flag=""
  local build_args=()
  if [ "${REBUILD:-0}" = "1" ]; then
    log_info "  用户指定 --rebuild，强制重建镜像"
    need_build_flag="--build --force-recreate --remove-orphans"
  else
    for img in ruoyi-frontend:latest ruoyi-backend-my:latest; do
      if ! image_exists "$img"; then
        log_info "  镜像 $img 缺失，需要构建"
        need_build_flag="--build"
        break
      fi
    done
    if [ -z "$need_build_flag" ]; then
      log_info "  镜像均存在，复用现有镜像（秒级启动）"
    fi
  fi

  # 透传镜像源配置到后端构建（默认阿里云）
  # 用户可通过环境变量自定义：PIP_INDEX_URL=https://mirrors.huaweicloud.com/repository/pypi/simple ./start-dev.sh --docker --rebuild
  if [ -n "${PIP_INDEX_URL:-}" ]; then
    log_info "  自定义 PIP 镜像源: $PIP_INDEX_URL"
    build_args+=("--build-arg" "PIP_INDEX_URL=$PIP_INDEX_URL")
  fi

  # 前端 dist 过期检查（如需构建则由 compose 在容器内 npm install；此处只判断 dist 是否存在）
  ensure_frontend_dist

  cd "$PROJECT_ROOT"
  log_info "  启动容器..."
  # 实时输出 compose 进度到终端（tee），同时保留日志文件用于事后回看。
  # 这样 rebuild 时用户能看到 pip 在下载哪一步；没 rebuild 时也能看到
  # Pulling/Extracting/Starting 的实时状态，不会误以为"卡住"。
  local up_log="/tmp/start-dev-up-$$.log"
  if ! docker compose -f "$DOCKER_COMPOSE_FILE" up -d $need_build_flag "${build_args[@]}" 2>&1 | tee "$up_log"; then
    log_error "  启动失败（原始日志见末尾）："
    sed 's/^/    /' "$up_log"
    log_error "  常见原因：网络 ruoyi-network 状态异常 / 端口冲突 / 配置错误 / 容器内应用崩"
    log_error "  排查建议："
    log_error "    1) docker network ls | grep ruoyi-network（确认网络存在）"
    log_error "    2) bash scripts/cleanup-orphan-network.sh（清理孤儿网络）"
    log_error "    3) docker compose -f $DOCKER_COMPOSE_FILE logs --tail=50 ruoyi-backend-my"
    rm -f "$up_log"
    exit 1
  fi
  rm -f "$up_log"

  # 等待容器就绪
  log_info "等待服务启动..."
  for name in ruoyi-mysql ruoyi-redis; do
    retries=60
    while [ $retries -gt 0 ]; do
      if is_container_running "$name"; then
        break
      fi
      retries=$((retries - 1)); sleep 2
    done
    if [ $retries -eq 0 ]; then
      log_error "$name 启动失败"
      exit 1
    fi
    log_info "  $name: running ✓"
  done

  # 后端和前端不依赖健康检查，但 compose 会等 depends_on
  sleep 3

  log_info "检查容器状态..."
  for name in ruoyi-frontend ruoyi-backend-my; do
    if is_container_running "$name"; then
      log_info "  $name: running ✓"
    else
      log_error "  $name: 未运行，请检查 docker compose logs"
    fi
  done

  # APP_ROOT_PATH 决定后端路由前缀：本地模式 = /dev-api，Docker 模式 = /docker-api
  # 从后端 .env.dockermy 读取，确保提示地址与实际路由前缀一致
  local app_root_path
  app_root_path=$(grep -E '^APP_ROOT_PATH[[:space:]]*=' "$BACKEND_DIR/.env.dockermy" 2>/dev/null \
    | tail -1 | sed -E "s/.*APP_ROOT_PATH[[:space:]]*=[[:space:]]*['\"]?([^'\"]+)['\"].*/\1/")
  app_root_path="${app_root_path:-/docker-api}"

  echo ""
  echo "============================================"
  log_mode "  Docker 容器模式 - 启动完成"
  echo "============================================"
  echo "  前端:     http://localhost:12580"
  echo "  后端:     http://localhost:19099${app_root_path}"
  echo "  API 文档: http://localhost:19099${app_root_path}/proxy-docs"
  echo "  MySQL:    localhost:13306"
  echo "  Redis:    localhost:16379"
  echo ""
  echo "  查看日志:   docker compose -f $DOCKER_COMPOSE_FILE logs -f"
  echo "  停止服务:   docker compose -f $DOCKER_COMPOSE_FILE down"
  echo "  强制重建:   docker compose -f $DOCKER_COMPOSE_FILE build --no-cache"
  echo "                （默认情况：改代码/Dockerfile 后下次启动会自动 rebuild，无需手动）"
  echo "============================================"
}

# =============================================================================
# 模式 C：停止所有服务
# =============================================================================
stop_all_mode() {
  log_mode ""
  log_mode "========================================"
  log_mode "  停止所有服务"
  log_mode "========================================"
  echo ""

  check_cmd docker

  log_step "1/2 - 停止 Docker 容器..."
  cd "$PROJECT_ROOT"
  if docker compose -f "$DOCKER_COMPOSE_FILE" ps 2>/dev/null | grep -q ruoyi; then
    docker compose -f "$DOCKER_COMPOSE_FILE" down
  fi
  stop_all_containers
  echo "  ✓ 容器清理完毕"

  log_step "2/2 - 停止本地进程..."
  stop_local_processes
  echo "  ✓ 本地进程清理完毕"

  echo ""
  echo "============================================"
  log_mode "  全部停止完成"
  echo "============================================"
  echo "  数据卷保留（不会丢数据）。如需彻底清理："
  echo "    docker volume rm \$(docker volume ls -q | grep ruoyi)"
  echo "============================================"
}


# =============================================================================
# 入口
# =============================================================================
main() {
  MODE=""
  REBUILD=0
  for arg in "$@"; do
    case $arg in
      --docker|-d) MODE="docker" ;;
      --stop|-s)   MODE="stop" ;;
      --rebuild)   REBUILD=1 ;;
      --help|-h)   MODE="help" ;;
      *)           MODE="local" ;;
    esac
  done
  export REBUILD

  if [ "$MODE" = "help" ]; then
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  (默认)        本地开发模式：Docker MySQL/Redis + 本地前后端"
    echo "  --docker      Docker 容器模式：全容器，模拟生产环境"
    echo "  --rebuild     Docker 模式：强制重建镜像（搭配 --docker 使用）"
    echo "  --stop        停止所有服务（容器 + 本地进程）"
    echo "  --help        显示帮助"
    exit 0
  fi

  case "$MODE" in
    docker) run_docker_mode ;;
    stop)   stop_all_mode ;;
    *)      run_local_mode ;;
  esac
}

main "$@"
