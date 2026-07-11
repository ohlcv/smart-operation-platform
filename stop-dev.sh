#!/bin/bash
# =============================================================================
# RuoYi FastAPI 停止脚本
#   - 删除所有容器（MySQL/Redis/前端/后端）
#   - 停止所有本地进程
# =============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/ruoyi-fastapi-backend"

# ---- 颜色 ----
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC}  $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_step()  { echo -e "${CYAN}[STEP]${NC}  $1"; }

# ---- 容器列表 ----
DEV_CONTAINERS="ruoyi-mysql ruoyi-redis ruoyi-frontend ruoyi-backend-my ruoyi-pg"

# =============================================================================
# Docker 容器停止
# =============================================================================
stop_containers() {
  log_step "删除 Docker 容器..."
  if ! command -v docker &> /dev/null; then
    log_warn "  Docker 未安装，跳过"
    return
  fi
  if ! docker info > /dev/null 2>&1; then
    log_warn "  Docker 守护进程未运行，跳过容器停止"
    return
  fi
  local stopped=0
  for name in $DEV_CONTAINERS; do
    if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q "^${name}$"; then
      log_info "  删除容器: $name"
      docker rm -f "$name" > /dev/null 2>&1
      stopped=1
    fi
  done
  [ $stopped -eq 0 ] && log_info "  无需删除的容器"
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
  stop_by_port 9099    "后端 (uvicorn)"
  stop_by_port 8080    "前端 dev server"
  stop_by_port 12580 "前端 dev server"
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
  echo ""
  echo "========================================"
  echo -e "${BOLD}${RED}  停止开发环境${NC}"
  echo "========================================"
  echo ""

  stop_local_processes
  clean_pid
  stop_containers

  echo ""
  echo "========================================"
  log_info "  停止完成"
  echo "========================================"
}

main "$@"
