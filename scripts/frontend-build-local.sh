#!/bin/bash
# ============================================
# 本地构建打包脚本
# ============================================
# 在本地 Mac 执行,只做前端编译和打包
# 默认只打包前端,不包含后端代码
#
# 使用方法:
#   chmod +x build-local.sh
#   ./build-local.sh
#
# 执行后生成:
#   /tmp/smart-ops.tar.gz  (部署包,仅含前端)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_NAME="smart-ops"

echo "==========================================="
echo "  本地构建打包"
echo "  模式: 仅前端"
echo "==========================================="

cd "$SCRIPT_DIR"

# 1. 检查前端 dist 是否存在
echo "[1/4] 检查前端编译产物..."
if [ ! -d "ruoyi-fastapi-frontend/dist" ]; then
    echo "   dist/ 不存在,开始编译前端..."
else
    echo "   dist/ 已存在。如需重新编译,请先删除 dist/ 目录。"
    echo -n "   是否重新编译? (y/N): "
    read -r answer
    if [ "$answer" != "y" ] && [ "$answer" != "Y" ]; then
        echo "   跳过编译,使用现有 dist/ 目录。"
    else
        rm -rf ruoyi-fastapi-frontend/dist
    fi
fi

# 2. 编译前端
if [ ! -d "ruoyi-fastapi-frontend/dist" ]; then
    echo "[2/4] 安装依赖..."
    cd ruoyi-fastapi-frontend
    npm install
    cd ..

    echo "[3/4] 编译前端..."
    cd ruoyi-fastapi-frontend
    npm run build:docker
    cd ..
    echo "   编译完成!"
else
    echo "[2/4] 跳过编译(dist/ 已存在)"
    echo "[3/4] 跳过编译(dist/ 已存在)"
fi

# 3. 打包项目(不包含 backend)
echo "[4/4] 打包项目(仅前端)..."
tar --exclude=ruoyi-fastapi-frontend/node_modules \
    --exclude=ruoyi-fastapi-frontend/.git \
    --exclude=ruoyi-fastapi-backend \
    --exclude=ruoyi-fastapi-test \
    --exclude=.git \
    --exclude=*.log \
    --exclude=.DS_Store \
    --exclude=*.tar.gz \
    --exclude=scripts/__pycache__ \
    -czvf /tmp/${PROJECT_NAME}.tar.gz .

# 4. 显示结果
PACKAGE_SIZE=$(du -h /tmp/${PROJECT_NAME}.tar.gz | cut -f1)
echo ""
echo "==========================================="
echo "  构建完成!"
echo "==========================================="
echo "  打包文件: /tmp/${PROJECT_NAME}.tar.gz"
echo "  文件大小: ${PACKAGE_SIZE}"
echo "  包含: 仅前端"
echo ""
echo "  接下来执行部署脚本:"
echo "  ./deploy-server.sh"
echo "==========================================="
