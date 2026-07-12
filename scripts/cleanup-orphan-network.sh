#!/bin/bash
# =============================================================================
# 一键清理被污染的 ruoyi-network（旧本地 compose 创建、没有 compose 标签）
# 前提：所有 ruoyi-* 容器已停止
# 用法：在服务器上 root 用户跑一次
# =============================================================================
set -e

NET_NAME="ruoyi-network"

echo "========================================"
echo "  检查 $NET_NAME"
echo "========================================"

if ! docker network ls --format '{{.Name}}' | grep -qx "$NET_NAME"; then
  echo "[OK] $NET_NAME 不存在，无需清理"
  exit 0
fi

# 检查是否有容器还在用
USING=$(docker network inspect -f '{{range .Containers}}{{.Name}} {{end}}' "$NET_NAME" 2>/dev/null | xargs)
if [ -n "$USING" ]; then
  echo "[ERROR] $NET_NAME 仍被容器占用: $USING"
  echo "        请先停掉这些容器再重试"
  exit 1
fi

# 检查是否是 compose 创建的（带标签 = 生产）
LABEL=$(docker network inspect -f '{{index .Labels "com.docker.compose.network"}}' "$NET_NAME" 2>/dev/null || echo "")
if [ -n "$LABEL" ]; then
  echo "[WARN] $NET_NAME 是 compose 创建的（label=$LABEL），可能是生产网络"
  echo "       请确认生产不在用后再删："
  echo "         docker network rm $NET_NAME"
  exit 2
fi

echo "[INFO] $NET_NAME 是孤儿网络（无 compose 标签、无容器使用），可安全删除"
docker network rm "$NET_NAME"
echo "[DONE]"