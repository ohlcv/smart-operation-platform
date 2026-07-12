#!/bin/bash
# ============================================
# 服务器部署脚本
# ============================================
# 上传打包文件到服务器并部署
#
# 使用方法:
#   chmod +x deploy-server.sh
#   ./deploy-server.sh              # 默认: 跳过上传,重新部署全部容器
#   ./deploy-server.sh --upload      # 上传本地文件 + 重新部署
#
# 说明:
#   - 前端: 重新构建镜像
#   - 后端: 使用已有镜像(不重新构建)
#
# 前提条件:
#   1. SSH 免密码登录已配置
#   2. 服务器已有 smart-ops.tar.gz(默认模式)

set -e

# ====== 配置区域 ======
SERVER_USER="root"
SERVER_HOST="150.158.53.137"
SERVER_PATH="/home/project/smart-operation-platform"
# ======================

PACKAGE_FILE="/tmp/smart-ops.tar.gz"
PROJECT_NAME="smart-ops"

# ====== 解析参数 ======
UPLOAD_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --upload|-u)
            UPLOAD_MODE=true
            shift
            ;;
        --help|-h)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --upload, -u  上传本地部署包到服务器"
            echo "  --help, -h    显示此帮助信息"
            echo ""
            echo "默认行为: 跳过上传,重新部署全部容器"
            echo ""
            echo "示例:"
            echo "  $0                    # 跳过上传,重新部署"
            echo "  $0 --upload           # 上传本地文件并部署"
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
done

echo "==========================================="
echo "  服务器部署"
echo "  模式: 删除旧容器,重新创建全部"
if [ "$UPLOAD_MODE" = true ]; then
    echo "  上传: 是"
else
    echo "  上传: 跳过"
fi
echo "==========================================="

# 1. 检查打包文件是否存在(仅上传模式需要)
echo "[1/5] 检查部署包..."
if [ "$UPLOAD_MODE" = true ]; then
    if [ ! -f "$PACKAGE_FILE" ]; then
        echo "   错误: $PACKAGE_FILE 不存在"
        echo "   请先执行: ./build-local.sh"
        exit 1
    fi
    echo "   部署包: $PACKAGE_FILE"
    PACKAGE_SIZE=$(du -h "$PACKAGE_FILE" | cut -f1)
    echo "   文件大小: ${PACKAGE_SIZE}"
else
    echo "   跳过(使用服务器已有文件)"
fi

# 2. 测试 SSH 连接
echo "[2/5] 测试 SSH 连接..."
if ssh -o ConnectTimeout=10 -o BatchMode=yes ${SERVER_USER}@${SERVER_HOST} "echo 'SSH OK'" 2>/dev/null; then
    echo "   SSH 密钥连接成功"
elif ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_HOST} "echo 'SSH OK'" 2>/dev/null; then
    echo "   SSH 连接成功(已接受主机密钥)"
else
    echo "   错误: 无法连接到服务器 ${SERVER_USER}@${SERVER_HOST}"
    echo "   请手动执行一次: ssh ${SERVER_USER}@${SERVER_HOST}"
    echo "   输入密码确认后,再重新执行本脚本"
    exit 1
fi

# 3. 清理所有旧容器
echo "[3/5] 清理所有旧容器..."
ssh ${SERVER_USER}@${SERVER_HOST} "cd ${SERVER_PATH} && \
    echo '   删除所有容器...' && \
    docker stop \$(docker ps -aq) 2>/dev/null || true && \
    docker rm \$(docker ps -aq) 2>/dev/null || true && \
    echo '   清理完成'"
echo "   清理完成"

# 4. 上传到服务器(可选)
if [ "$UPLOAD_MODE" = true ]; then
    echo "[4/5] 上传文件..."
    echo "   删除服务器旧包..."
    ssh ${SERVER_USER}@${SERVER_HOST} "rm -f ${SERVER_PATH}/${PROJECT_NAME}.tar.gz"
    echo "   上传新包..."
    scp -o ConnectTimeout=30 "$PACKAGE_FILE" ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/${PROJECT_NAME}.tar.gz
    echo "   上传完成"
else
    echo "[4/5] 上传文件... 跳过(使用服务器已有文件)"
fi

# 5. 服务器部署(只构建前端,后端用已有镜像)
echo "[5/5] 服务器部署..."
echo ""
echo "==========================================="
echo "  服务器执行中..."
echo "==========================================="
ssh ${SERVER_USER}@${SERVER_HOST} "cd ${SERVER_PATH} && \
    if [ -f ${PROJECT_NAME}.tar.gz ]; then
        echo '   解压文件...' && \
        tar -xzvf ${PROJECT_NAME}.tar.gz
    fi && \
    echo '   启动全部服务(前端构建,后端使用已有镜像)...' && \
    docker compose -f docker-compose.traefik.yml -p smart-ops up -d --build"

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
