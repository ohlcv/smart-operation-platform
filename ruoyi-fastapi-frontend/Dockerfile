# 构建阶段
FROM node:20-bookworm-slim AS builder
WORKDIR /app

# 设置npm镜像源
RUN npm config set registry https://registry.npmmirror.com

# 优先使用宿主机预先构建好的产物，避免在容器内进行网络依赖安装
# 本地构建方式：
#   cd ruoyi-fastapi-frontend
#   npm install
#   npm run build:docker
COPY dist ./dist

# 运行阶段
FROM nginx:latest
WORKDIR /usr/share/nginx/html

# 复制构建产物
COPY --from=builder /app/dist .

# 暴露端口
EXPOSE 80

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]