#!/bin/bash
# ============================================
# 服务器部署脚本
# ============================================
# 上传打包文件到服务器并部署
#
# 使用方法:
#   chmod +x deploy-server.sh
#   ./deploy-server.sh
#
# 前提条件:
#   1. 先执行 ./build-local.sh 生成部署包
#   2. 确保本地和服务器 SSH 连接正常
#   3. 确保 /tmp/smart-ops.tar.gz 存在

set -e

# ====== 配置区域 ======
SERVER_USER="root"
SERVER_HOST="150.158.53.137"
SERVER_PATH="/home/project/smart-operation-platform"
# ======================

PACKAGE_FILE="/tmp/smart-ops.tar.gz"
PROJECT_NAME="smart-ops"

echo "==========================================="
echo "  服务器部署"
echo "==========================================="

# 1. 检查打包文件是否存在
echo "[1/5] 检查部署包..."
if [ ! -f "$PACKAGE_FILE" ]; then
    echo "   错误: $PACKAGE_FILE 不存在"
    echo "   请先执行: ./build-local.sh"
    exit 1
fi
echo "   部署包: $PACKAGE_FILE"
PACKAGE_SIZE=$(du -h "$PACKAGE_FILE" | cut -f1)
echo "   文件大小: ${PACKAGE_SIZE}"

# 2. 测试 SSH 连接
echo "[2/5] 测试 SSH 连接..."
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes ${SERVER_USER}@${SERVER_HOST} "echo 'SSH OK'" 2>/dev/null; then
    echo "   错误: 无法连接到服务器 ${SERVER_USER}@${SERVER_HOST}"
    echo "   请检查:"
    echo "   1. 服务器 IP 地址是否正确"
    echo "   2. SSH 密钥是否配置正确"
    echo "   3. 服务器是否开机"
    exit 1
fi
echo "   SSH 连接正常"

# 3. 清理服务器旧容器和镜像
echo "[3/5] 清理服务器旧容器..."
ssh ${SERVER_USER}@${SERVER_HOST} "cd ${SERVER_PATH} && \
    echo '   停止旧容器...' && \
    docker compose -f docker-compose.server.yml down --rmi local 2>/dev/null || true && \
    docker compose -f docker-compose.traefik.yml down --rmi local 2>/dev/null || true && \
    docker compose -f docker-compose.my.yml down --rmi local 2>/dev/null || true && \
    echo '   清理旧镜像...' && \
    docker image prune -f && \
    echo '   清理完成'"
echo "   清理完成"

# 4. 上传到服务器
echo "[4/5] 上传到服务器..."
scp -o ConnectTimeout=30 "$PACKAGE_FILE" ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/${PROJECT_NAME}.tar.gz
echo "   上传完成"

# 5. 服务器解压并部署
echo "[5/5] 服务器部署..."
echo ""
echo "==========================================="
echo "  服务器执行中..."
echo "==========================================="
ssh ${SERVER_USER}@${SERVER_HOST} "cd ${SERVER_PATH} && \
    echo '   解压文件...' && \
    tar -xzvf ${PROJECT_NAME}.tar.gz && \
    echo '   设置脚本权限...' && \
    chmod +x deploy-traefik.sh && \
    echo '   启动容器...' && \
    ./deploy-traefik.sh"

# 6. 显示结果
echo ""
echo "==========================================="
echo "  部署完成!"
echo "==========================================="
echo "  前端:    https://meowquant.site"
echo "  API:     https://meowquant.site/docs"
echo "  Traefik: https://traefik.meowquant.site"
echo ""
echo "  首次访问 HTTPS 会自动申请证书,"
echo "  可能需要等待 30-60 秒。"
echo "==========================================="
