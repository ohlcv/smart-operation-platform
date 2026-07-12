#!/bin/bash
# =============================================================================
# RuoYi FastAPI 停止脚本
#   - 默认：删容器 + 删 volume（不删 image，不删 network）
#   - --keep-data：删容器，保留 volume（不删 image，不删 network）
#   - 不删 network：compose 中标了 external: true，可能由生产 compose 或运维创建
# =============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/ruoyi-fastapi-backend"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.my.yml"

# ---- 颜色 ----
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC}  $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_step()  { echo -e "${CYAN}[STEP]${NC}  $1"; }

# =============================================================================
# Docker 停止（用 docker compose down，删容器 + 可选 volume）
#   --keep-data：保留 volume，MySQL/Redis 数据不丢
#   默认（不带 --keep-data）：删 volume，数据重置
#   都不删 image（用户在 start-dev.sh --docker 里要求：复用 image 不重 build）
#   都不删 ruoyi-network（它在 compose 中标了 external: true，
#   可能由生产 compose (docker-compose.server.yml) 或运维创建，盲删会破坏生产）
# =============================================================================
stop_containers() {
  local keep_data=$1
  log_step "停止并删除 Docker 容器（不删 image、不删 network）..."

  if ! command -v docker &> /dev/null; then
    log_warn "  Docker 未安装，跳过"
    return
  fi
  if ! docker info > /dev/null 2>&1; then
    log_warn "  Docker 守护进程未运行，跳过容器停止"
    return
  fi

  # docker compose 优先（一次性清容器+network，对 orphan service 也清）
  if [ -f "$DOCKER_COMPOSE_FILE" ]; then
    cd "$PROJECT_ROOT"
    if [ "$keep_data" = "1" ]; then
      log_info "  [保留数据] docker compose down --remove-orphans"
      docker compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans 2>&1 | sed 's/^/    /' || true
    else
      log_info "  [默认删数据] docker compose down -v --remove-orphans"
      docker compose -f "$DOCKER_COMPOSE_FILE" down -v --remove-orphans 2>&1 | sed 's/^/    /' || true
    fi
  else
    log_warn "  找不到 $DOCKER_COMPOSE_FILE，回退手写循环..."
    for name in ruoyi-mysql ruoyi-redis ruoyi-frontend ruoyi-backend-my; do
      if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q "^${name}$"; then
        log_info "  删除容器: $name"
        docker rm -f "$name" > /dev/null 2>&1
      fi
    done
    # 网络 ruoyi-network 不再在此处删除（external: true，可能生产在用）
  fi

  log_info "  完成（image / network 已保留，下次 start-dev.sh --docker 将复用）"
}

# =============================================================================
# 本地进程停止
# =============================================================================
is_port_listening() {
  if command -v lsof &> /dev/null; then
    lsof -i :"$1" -sTCP:LISTEN > /dev/null 2>&1
  elif command -v ss &> /dev/null; then
    ss -tlnp "sport = :$1" 2>/dev/null | grep -q LISTEN
  else
    return 1
  fi
}

stop_by_port() {
  local port=$1
  local name=$2
  if is_port_listening "$port"; then
    log_warn "  停止本地进程 (port=$port): $name"
    if command -v lsof &> /dev/null; then
      lsof -ti :"$port" | xargs kill -9 2>/dev/null || true
    fi
  fi
}

stop_local_processes() {
  log_step "停止本地进程..."
  stop_by_port 9099   "后端 (uvicorn)"
  stop_by_port 8080   "前端 dev server (本地模式)"
  stop_by_port 12580  "前端 dev server (容器模式端口)"
  # Docker 宿主端口（容器停止后一般自动释放，但防僵尸进程漏配）
  stop_by_port 13306  "MySQL host port"
  stop_by_port 16379  "Redis host port"
  log_info "  完成"
}

# =============================================================================
# 清理残留
# =============================================================================
clean_pid() {
  log_step "清理残留文件..."
  if [ -f "$BACKEND_DIR/.backend.pid" ]; then
    local pid=$(cat "$BACKEND_DIR/.backend.pid")
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      kill -9 "$pid" 2>/dev/null || true
    fi
    rm -f "$BACKEND_DIR/.backend.pid"
  fi
  rm -f "$BACKEND_DIR/.env.merged"
  log_info "  清理完成"
}

# =============================================================================
# 入口
# =============================================================================
main() {
  KEEP_DATA=0
  for arg in "$@"; do
    case $arg in
      --keep-data|-k) KEEP_DATA=1 ;;
      --help|-h)
        echo "用法: $0 [选项]"
        echo ""
        echo "  (默认)         删容器 + 删 volume + 留 image + 留 network"
        echo "                 MySQL 数据会被清空，下次启动走 initdb.d 重灌"
        echo "  --keep-data    删容器 + 留 volume + 留 image + 留 network"
        echo "                 MySQL 数据不丢，下次启动 docker compose up -d 直接复用"
        echo "  --help         显示帮助"
        exit 0
        ;;
    esac
  done

  echo ""
  echo "========================================"
  echo -e "${BOLD}${RED}  停止开发环境${NC}"
  if [ $KEEP_DATA -eq 1 ]; then
    echo -e "  ${CYAN}模式: 保留数据 (volume)${NC}"
  else
    echo -e "  ${CYAN}模式: 清空数据 (volume)${NC}"
  fi
  echo "========================================"
  echo ""

  stop_local_processes
  clean_pid
  stop_containers $KEEP_DATA

  echo ""
  echo "========================================"
  log_info "  停止完成"
  echo "========================================"
}

main "$@"
