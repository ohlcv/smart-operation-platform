#!/bin/bash
# ============================================
# Traefik 部署脚本
# ============================================
# 使用方法:
#   chmod +x deploy-traefik.sh
#   ./deploy-traefik.sh
#
# 说明:
#   - 删除所有旧容器
#   - 重新创建全部容器
#   - 前端构建镜像,后端使用已有镜像
#
# 访问地址:
#   https://meowquant.site         (前端)
#   https://meowquant.site/docs    (API 文档)
#   https://traefik.meowquant.site (Traefik Dashboard)

set -e

echo "=========================================="
echo "  部署服务"
echo "  模式: 删除旧容器,重新创建全部"
echo "=========================================="

# 1. 创建必要目录
echo "[1/4] 创建配置目录..."
mkdir -p traefik/letsencrypt traefik/dynamic

# 2. 初始化 acme.json(存储 SSL 证书)
if [ ! -f traefik/letsencrypt/acme.json ]; then
    echo "[2/4] 初始化 SSL 证书存储..."
    cat > traefik/letsencrypt/acme.json << 'EOF'
{
  "letsencrypt": {
    "Account": {
      "Email": "your-email@meowquant.site",
      "Registration": {
        "Body": {
          "status": "valid"
        },
        "URI": "https://acme-v02.api.letsencrypt.org/acme/acct/placeholder"
      }
    },
    "Certificates": []
  }
}
EOF
    chmod 600 traefik/letsencrypt/acme.json
fi

# 3. 创建动态配置
if [ ! -f traefik/dynamic/traefik-dynamic.toml ]; then
    cat > traefik/dynamic/traefik-dynamic.toml << 'EOF'
# Traefik 动态配置 - API 路径路由
[http.routers]
  [http.routers.to-https]
    entryPoints = ["web"]
    rule = "Host(`meowquant.site`)"
    middlewares = ["redirect-to-https"]
    priority = 1

[http.middlewares]
  [http.middlewares.redirect-to-https]
    [http.middlewares.redirect-to-https.redirectScheme]
      scheme = "https"
      permanent = true

  [http.middlewares.backend-stripprefix]
    [http.middlewares.backend-stripprefix.stripPrefix]
      prefixes = ["/api"]

[http.services]
  [http.services.frontend-service]
    [[http.services.frontend-service.loadBalancer.servers]]
      url = "http://ruoyi-frontend:80"

  [http.services.backend-service]
    [[http.services.backend-service.loadBalancer.servers]]
      url = "http://ruoyi-backend-my:9099"
EOF
fi

# 4. 删除旧容器,重新创建全部
echo "[3/4] 删除所有旧容器..."
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true
echo "   删除完成"

echo "[4/4] 启动全部服务(前端构建,后端使用已有镜像)..."
docker compose -f docker-compose.traefik.yml -p smart-ops up -d --build

echo ""
echo "=========================================="
echo "  部署完成!"
echo "=========================================="
echo "  前端:    https://meowquant.site"
echo "  API:     https://meowquant.site/docs"
echo "  Traefik: https://traefik.meowquant.site"
echo "=========================================="
echo ""
echo "首次访问 HTTPS 会自动申请 Let's Encrypt 证书,"
echo "可能需要等待 30-60 秒。"
