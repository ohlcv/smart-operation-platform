#!/bin/bash
# =============================================================================
# RuoYi FastAPI 启动脚本
#   ./start-dev.sh            本地开发模式（本地前后端 + Docker MySQL/Redis）
#   ./start-dev.sh --docker   Docker 容器模式（全容器，模拟生产）
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
  log_step "清理旧容器并启动（不重建镜像）..."
  stop_all_containers

  cd "$PROJECT_ROOT"
  # 默认复用已有镜像：docker compose up -d 看到本地有 image tag 就直接起容器
  #   - 镜像存在 → 秒级起容器
  #   - 镜像缺失 → 报错提示
  # 改了代码想强制重建：手动 docker compose -f $DOCKER_COMPOSE_FILE build --no-cache
  log_info "  启动容器（复用本地镜像）..."
  if ! docker compose -f "$DOCKER_COMPOSE_FILE" up -d; then
    log_warn "  启动失败（很可能是镜像不存在），尝试自动构建一次..."
    docker compose -f "$DOCKER_COMPOSE_FILE" up -d --build
  fi

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

  echo ""
  echo "============================================"
  log_mode "  Docker 容器模式 - 启动完成"
  echo "============================================"
  echo "  前端:     http://localhost:12580"
  echo "  后端:     http://localhost:19099/dev-api"
  echo "  API 文档: http://localhost:19099/dev-api/docs"
  echo "  MySQL:    localhost:13306"
  echo "  Redis:    localhost:16379"
  echo ""
  echo "  查看日志:   docker compose -f $DOCKER_COMPOSE_FILE logs -f"
  echo "  停止服务:   docker compose -f $DOCKER_COMPOSE_FILE down"
  echo "  重建镜像:   docker compose -f $DOCKER_COMPOSE_FILE build --no-cache"
  echo "                （改代码/Dockerfile 后必须手动重建，脚本不会自动 build）"
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
  for arg in "$@"; do
    case $arg in
      --docker|-d) MODE="docker" ;;
      --stop|-s)   MODE="stop" ;;
      --help|-h)   MODE="help" ;;
      *)           MODE="local" ;;
    esac
  done

  if [ "$MODE" = "help" ]; then
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  (默认)        本地开发模式：Docker MySQL/Redis + 本地前后端"
    echo "  --docker      Docker 容器模式：全容器，模拟生产环境"
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
