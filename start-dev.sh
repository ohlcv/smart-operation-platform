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

  # ---- 创建 Docker 网络（不存在则创建） ----
  if ! docker network ls --format '{{.Name}}' 2>/dev/null | grep -qx "ruoyi-network"; then
    log_info "  创建 ruoyi-network..."
    docker network create ruoyi-network > /dev/null 2>&1
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
          -v $PROJECT_ROOT/ruoyi-fastapi-backend/sql/ruoyi-fastapi.sql:/docker-entrypoint-initdb.d/01-ruoyi-fastapi.sql \
          -v $PROJECT_ROOT/ruoyi-fastapi-backend/sql/biz_init.sql:/docker-entrypoint-initdb.d/02-biz-init.sql \
          -v $PROJECT_ROOT/ruoyi-fastapi-backend/sql/biz_menus_roles_init.sql:/docker-entrypoint-initdb.d/03-biz-menus-roles.sql \
          -v $PROJECT_ROOT/ruoyi-fastapi-backend/sql/cockpit_v3_3_init.sql:/docker-entrypoint-initdb.d/04-cockpit-v3-3.sql \
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

  # ---- 增量 SQL：已建库时手动跑（initdb.d 只在首次启动生效） ----
  if is_container_running "ruoyi-mysql"; then
    # 探测 biz_channel.province 列是否存在，不存在就说明 v3.3 增量未跑
    has_province=$(LANG=C docker exec ruoyi-mysql mysql --default-character-set=utf8mb4 \
      -uroot -proot -N -B \
      -e "SHOW COLUMNS FROM biz_channel LIKE 'province'" 2>/dev/null | wc -l)
    if [ "${has_province:-0}" = "0" ]; then
      log_warn "  检测到 biz_channel.province 缺失，自动执行 v3.3 增量脚本..."
      LANG=C docker exec -i ruoyi-mysql mysql --default-character-set=utf8mb4 \
        -uroot -proot ruoyi-fastapi \
        < "$BACKEND_DIR/sql/cockpit_v3_3_init.sql" 2>&1 | tail -10 || \
        log_warn "  v3.3 增量脚本执行失败，请手动跑: docker exec -i ruoyi-mysql mysql -uroot -proot ruoyi-fastapi < $BACKEND_DIR/sql/cockpit_v3_3_init.sql"
    else
      log_info "  v3.3 增量已应用 ✓"
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

  # ---- 创建 Docker 网络（不存在则创建） ----
  if ! docker network ls --format '{{.Name}}' 2>/dev/null | grep -qx "ruoyi-network"; then
    log_info "  创建 ruoyi-network..."
    docker network create ruoyi-network > /dev/null 2>&1
  fi

  # ---- 清理并重建 ----
  log_step "重建 Docker 容器（删除旧容器 + 重新创建）..."
  stop_all_containers

  log_info "  拉取 / 构建镜像（首次较慢）..."
  cd "$PROJECT_ROOT"
  docker compose -f "$DOCKER_COMPOSE_FILE" up -d --build

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
  echo "  查看日志: docker compose -f $DOCKER_COMPOSE_FILE logs -f"
  echo "  停止服务: docker compose -f $DOCKER_COMPOSE_FILE down"
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
      --help|-h)   MODE="help" ;;
      *)           MODE="local" ;;
    esac
  done

  if [ "$MODE" = "help" ]; then
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  (默认)      本地开发模式：Docker MySQL/Redis + 本地前后端"
    echo "  --docker    Docker 容器模式：全容器，模拟生产环境"
    echo "  --help      显示帮助"
    exit 0
  fi

  if [ "$MODE" = "docker" ]; then
    run_docker_mode
  else
    run_local_mode
  fi
}

main "$@"
