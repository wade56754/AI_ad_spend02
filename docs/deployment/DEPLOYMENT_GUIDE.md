# 部署指南

> **文档目的**: 为AI广告代投系统提供完整的部署配置和运维指南
> **目标读者**: DevOps工程师、系统管理员、开发团队
> **更新日期**: 2025-11-11
> **版本**: v1.0

---

## 📋 目录

1. [部署架构概览](#1-部署架构概览)
2. [环境配置](#2-环境配置)
3. [Docker容器化](#3-docker容器化)
4. [数据库部署](#4-数据库部署)
5. [CI/CD流程](#5-cicd流程)
6. [生产环境部署](#6-生产环境部署)
7. [监控和日志](#7-监控和日志)
8. [备份和恢复](#8-备份和恢复)
9. [安全配置](#9-安全配置)
10. [故障排查](#10-故障排查)

---

## 1. 部署架构概览

### 1.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        负载均衡层                            │
│                   Nginx Reverse Proxy                       │
│                   SSL Termination                           │
│                   Rate Limiting                             │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                       应用服务层                            │
│  ┌─────────────┐              ┌─────────────┐               │
│  │  Frontend   │              │   Backend    │               │
│  │ Next.js App │              │ FastAPI App  │               │
│  │  Port:3000  │              │  Port:8000   │               │
│  └─────────────┘              └─────────────┘               │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                       数据服务层                            │
│  ┌─────────────┐              ┌─────────────┐               │
│  │ PostgreSQL  │              │    Redis     │               │
│  │ Supabase    │              │    Cache     │               │
│  │  Port:5432  │              │  Port:6379   │               │
│  └─────────────┘              └─────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 部署环境

| 环境 | 用途 | 服务器配置 | 数据库规模 | 监控级别 |
|------|------|------------|------------|----------|
| **开发环境** | 日常开发和功能测试 | 2C4G | 小规模 | 基础监控 |
| **测试环境** | 集成测试和QA验证 | 4C8G | 中等规模 | 完整监控 |
| **预生产环境** | 生产前最终验证 | 8C16G | 接近生产 | 生产级监控 |
| **生产环境** | 正式业务运行 | 16C32G+ | 大规模 | 高级监控 |

### 1.3 技术栈

- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx
- **应用服务器**: Uvicorn (FastAPI)
- **数据库**: PostgreSQL (Supabase)
- **缓存**: Redis
- **CI/CD**: GitHub Actions
- **监控**: Prometheus + Grafana（现状：按需启用；完善度见“已实现 vs 规划”）
- **日志**: ELK Stack（规划能力；当前仅基础日志与告警）

---

## 2. 环境配置

### 2.1 服务器要求

#### 最低配置
- **CPU**: 4核心
- **内存**: 8GB RAM
- **存储**: 100GB SSD
- **网络**: 100Mbps带宽

#### 推荐配置
- **CPU**: 8核心
- **内存**: 16GB RAM
- **存储**: 200GB SSD
- **网络**: 1Gbps带宽

#### 生产配置
- **CPU**: 16核心+
- **内存**: 32GB+ RAM
- **存储**: 500GB+ SSD
- **网络**: 10Gbps带宽

### 2.2 操作系统准备

```bash
# Ubuntu 20.04+ 系统更新
sudo apt-get update && sudo apt-get upgrade -y

# 安装基础工具
sudo apt-get install -y curl wget git vim htop

# 配置时区
sudo timedatectl set-timezone Asia/Shanghai

# 配置主机名
sudo hostnamectl set-hostname ai-ad-spend-prod
```

### 2.3 Docker 安装

```bash
# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

### 2.4 防火墙配置

```bash
# 配置 UFW 防火墙
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 开放必要端口
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow from 127.0.0.1  # 本地访问

# 查看防火墙状态
sudo ufw status verbose
```

---

## 3. Docker容器化

### 3.1 项目结构

```
ai-ad-spend/
├── docker-compose.yml          # 生产环境配置
├── docker-compose.dev.yml      # 开发环境配置
├── docker-compose.prod.yml     # 生产环境覆盖配置
├── Dockerfile                  # 后端应用容器
├── Dockerfile.frontend         # 前端应用容器
├── nginx/
│   ├── nginx.conf              # Nginx 配置
│   ├── ssl/                    # SSL 证书目录
│   └── conf.d/
│       └── app.conf            # 应用配置
├── scripts/
│   ├── deploy.sh               # 部署脚本
│   ├── backup.sh               # 备份脚本
│   └── restore.sh              # 恢复脚本
└── monitoring/
    ├── prometheus.yml          # Prometheus 配置
    ├── grafana/
    │   └── dashboards/         # Grafana 仪表盘
    └── alertmanager.yml        # 告警配置
```

### 3.2 后端 Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
COPY requirements-prod.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非 root 用户
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3.3 前端 Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS builder

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 生产阶段
FROM nginx:alpine

# 复制构建结果
COPY --from=builder /app/.next /app/.next
COPY --from=builder /app/node_modules /app/node_modules
COPY --from=builder /app/package.json /app/
COPY --from=builder /app/public /app/public

# 复制 Next.js 配置
COPY --from=builder /app/next.config.js ./

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/nginx.conf

# 暴露端口
EXPOSE 3000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]
```

### 3.4 Docker Compose 配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  # 后端服务
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - JWT_SECRET=${JWT_SECRET}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY}
    env_file:
      - .env.prod
    depends_on:
      - postgres
      - redis
    networks:
      - app-network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.backend.rule=Host(`api.yourdomain.com`)"
      - "traefik.http.routers.backend.tls=true"

  # 前端服务
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      - NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com
      - NEXT_PUBLIC_SUPABASE_URL=${SUPABASE_URL}
      - NEXT_PUBLIC_SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
    networks:
      - app-network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.frontend.rule=Host(`yourdomain.com`)"
      - "traefik.http.routers.frontend.tls=true"

  # Nginx 反向代理
  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - ./nginx/conf.d:/etc/nginx/conf.d
    depends_on:
      - backend
      - frontend
    networks:
      - app-network

  # PostgreSQL 数据库
  postgres:
    image: postgres:15
    restart: unless-stopped
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    networks:
      - app-network

  # Redis 缓存
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - app-network

  # 监控服务
  prometheus:
    image: prom/prometheus:latest
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - app-network

  grafana:
    image: grafana/grafana:latest
    restart: unless-stopped
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
    networks:
      - app-network

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  app-network:
    driver: bridge
```

---

## 4. 数据库部署

### 4.1 PostgreSQL 配置

```yaml
# docker-compose.prod.yml (覆盖配置)
version: '3.8'

services:
  postgres:
    image: postgres:15
    restart: unless-stopped
    environment:
      - POSTGRES_DB=ai_ad_spend_prod
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
      - ./postgresql/postgresql.conf:/etc/postgresql/postgresql.conf
      - ./postgresql/pg_hba.conf:/etc/postgresql/pg_hba.conf
    command: postgres -c config_file=/etc/postgresql/postgresql.conf
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: '4'
    networks:
      - app-network
```

### 4.2 数据库初始化脚本

```sql
-- scripts/init-db.sql
-- 创建数据库和用户
CREATE DATABASE ai_ad_spend_prod;
CREATE USER app_user WITH ENCRYPTED PASSWORD '${DB_PASSWORD}';

-- 授权
GRANT ALL PRIVILEGES ON DATABASE ai_ad_spend_prod TO app_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO app_user;

-- 设置默认权限
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO app_user;

-- 连接到应用数据库
\c ai_ad_spend_prod;

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 退出
\c postgres;

-- 断开连接
\q
```

### 4.3 数据库迁移

```bash
#!/bin/bash
# scripts/migrate-db.sh

set -e

echo "开始数据库迁移..."

# 检查数据库连接
docker-compose exec postgres pg_isready -U postgres

# 运行 Alembic 迁移
docker-compose exec backend alembic upgrade head

# 验证迁移结果
docker-compose exec backend alembic current

echo "数据库迁移完成!"
```

---

## 5. CI/CD流程

### 5.1 GitHub Actions 工作流

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run tests
      run: |
        cd backend
        pytest --cov=app tests/
        coverage xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v4

    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: |
          ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
          ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}

    - name: Deploy to production
      uses: appleboy/ssh-action@v1.0.0
      with:
        host: ${{ secrets.PROD_HOST }}
        username: ${{ secrets.PROD_USER }}
        key: ${{ secrets.PROD_SSH_KEY }}
        script: |
          cd /opt/ai-ad-spend
          git pull origin main
          docker-compose pull
          docker-compose up -d
          docker system prune -f
```

### 5.2 部署脚本

```bash
#!/bin/bash
# scripts/deploy.sh

set -e

# 配置变量
DEPLOY_DIR="/opt/ai-ad-spend"
BACKUP_DIR="/opt/backups"
LOG_FILE="/var/log/deploy.log"

# 日志函数
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# 错误处理
error_exit() {
    log "ERROR: $1"
    exit 1
}

# 检查权限
check_permissions() {
    if [[ $EUID -ne 0 ]]; then
        error_exit "此脚本需要 root 权限运行"
    fi
}

# 备份数据库
backup_database() {
    log "开始备份数据库..."

    BACKUP_FILE="$BACKUP_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql"

    docker-compose exec postgres pg_dump -U postgres ai_ad_spend_prod > "$BACKUP_FILE"

    # 压缩备份文件
    gzip "$BACKUP_FILE"

    log "数据库备份完成: ${BACKUP_FILE}.gz"
}

# 更新代码
update_code() {
    log "更新应用代码..."

    cd "$DEPLOY_DIR"
    git fetch origin
    git reset --hard origin/main

    log "代码更新完成"
}

# 构建和部署
deploy_application() {
    log "开始部署应用..."

    cd "$DEPLOY_DIR"

    # 停止服务
    docker-compose down

    # 拉取最新镜像
    docker-compose pull

    # 启动服务
    docker-compose up -d

    # 等待服务启动
    sleep 30

    log "应用部署完成"
}

# 健康检查
health_check() {
    log "进行健康检查..."

    # 检查后端服务
    for i in {1..10}; do
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            log "后端服务健康检查通过"
            break
        fi

        if [[ $i -eq 10 ]]; then
            error_exit "后端服务健康检查失败"
        fi

        sleep 10
    done

    # 检查前端服务
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        log "前端服务健康检查通过"
    else
        error_exit "前端服务健康检查失败"
    fi

    log "健康检查完成"
}

# 清理旧镜像
cleanup() {
    log "清理旧镜像..."

    docker image prune -f

    # 保留最近5个版本的镜像
    docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}" | \
        grep ai-ad-spend | \
        tail -n +6 | \
        awk '{print $3}' | \
        xargs -r docker rmi -f

    log "清理完成"
}

# 主函数
main() {
    log "开始部署流程..."

    check_permissions
    backup_database
    update_code
    deploy_application
    health_check
    cleanup

    log "部署流程完成!"
}

# 执行主函数
main "$@"
```

---

## 6. 生产环境部署

### 6.1 服务器初始化

```bash
#!/bin/bash
# scripts/init-server.sh

set -e

# 更新系统
sudo apt-get update && sudo apt-get upgrade -y

# 安装基础软件
sudo apt-get install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 配置防火墙
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 创建应用目录
sudo mkdir -p /opt/ai-ad-spend
sudo mkdir -p /opt/backups
sudo mkdir -p /var/log/ai-ad-spend

# 设置权限
sudo chown -R $USER:$USER /opt/ai-ad-spend
sudo chown -R $USER:$USER /opt/backups
sudo chown -R $USER:$USER /var/log/ai-ad-spend

echo "服务器初始化完成!"
```

### 6.2 SSL 证书配置

```bash
#!/bin/bash
# scripts/setup-ssl.sh

DOMAIN="yourdomain.com"

# 安装 Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# 获取 SSL 证书
sudo certbot --nginx \
    --non-interactive \
    --agree-tos \
    --email admin@yourdomain.com \
    -d $DOMAIN \
    -d www.$DOMAIN

# 设置自动续期
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -

# 复制证书到应用目录
sudo mkdir -p /opt/ai-ad-spend/nginx/ssl
sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /opt/ai-ad-spend/nginx/ssl/
sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem /opt/ai-ad-spend/nginx/ssl/
sudo chown -R $USER:$USER /opt/ai-ad-spend/nginx/ssl

echo "SSL 证书配置完成!"
```

### 6.3 Nginx 配置

```nginx
# nginx/nginx.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # 日志格式
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    # 基本配置
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 50M;

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;

    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # 包含站点配置
    include /etc/nginx/conf.d/*.conf;
}
```

```nginx
# nginx/conf.d/app.conf
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:3000;
}

# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS 主站点
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL 配置
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # 前端应用
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API 请求
    location /api/ {
        proxy_pass http://backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 增加超时时间
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 健康检查
    location /health {
        proxy_pass http://backend/health;
        access_log off;
    }

    # 静态文件缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## 7. 监控和日志

### 7.1 Prometheus 配置

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:9113']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### 7.2 告警规则

```yaml
# monitoring/alert_rules.yml
groups:
  - name: application_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "高错误率告警"
          description: "错误率超过 10%"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "高响应时间告警"
          description: "95% 请求响应时间超过 1 秒"

      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "数据库服务宕机"
          description: "PostgreSQL 数据库无法访问"

      - alert: HighDatabaseConnections
        expr: pg_stat_activity_count > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "数据库连接数过高"
          description: "数据库活跃连接数超过 80"

      - alert: DiskSpaceUsage
        expr: (node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "磁盘空间使用率过高"
          description: "磁盘使用率超过 80%"
```

---

## 8. 备份和恢复

### 8.1 自动备份脚本

```bash
#!/bin/bash
# scripts/backup.sh

set -e

# 配置变量
BACKUP_DIR="/opt/backups"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p "$BACKUP_DIR"/{database,config,logs}

# 数据库备份
backup_database() {
    echo "开始数据库备份..."

    BACKUP_FILE="$BACKUP_DIR/database/db_backup_$DATE.sql"

    # 备份数据库
    docker-compose exec postgres pg_dump -U postgres ai_ad_spend_prod > "$BACKUP_FILE"

    # 压缩备份文件
    gzip "$BACKUP_FILE"

    echo "数据库备份完成: ${BACKUP_FILE}.gz"
}

# 配置文件备份
backup_config() {
    echo "开始配置文件备份..."

    CONFIG_BACKUP_DIR="$BACKUP_DIR/config/config_$DATE"
    mkdir -p "$CONFIG_BACKUP_DIR"

    # 复制配置文件
    cp -r /opt/ai-ad-spend/.env* "$CONFIG_BACKUP_DIR/"
    cp -r /opt/ai-ad-spend/nginx "$CONFIG_BACKUP_DIR/"
    cp -r /opt/ai-ad-spend/monitoring "$CONFIG_BACKUP_DIR/"

    # 创建压缩包
    tar -czf "$CONFIG_BACKUP_DIR.tar.gz" -C "$BACKUP_DIR/config" "config_$DATE"
    rm -rf "$CONFIG_BACKUP_DIR"

    echo "配置文件备份完成: ${CONFIG_BACKUP_DIR}.tar.gz"
}

# 日志备份
backup_logs() {
    echo "开始日志备份..."

    LOG_BACKUP_FILE="$BACKUP_DIR/logs/logs_$DATE.tar.gz"

    # 打包日志文件
    tar -czf "$LOG_BACKUP_FILE" -C /var/log ai-ad-spend

    echo "日志备份完成: $LOG_BACKUP_FILE"
}

# 清理旧备份
cleanup_old_backups() {
    echo "清理 $RETENTION_DAYS 天前的备份..."

    # 清理数据库备份
    find "$BACKUP_DIR/database" -name "*.gz" -mtime +$RETENTION_DAYS -delete

    # 清理配置备份
    find "$BACKUP_DIR/config" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete

    # 清理日志备份
    find "$BACKUP_DIR/logs" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete

    echo "旧备份清理完成"
}

# 主函数
main() {
    echo "开始备份流程..."

    backup_database
    backup_config
    backup_logs
    cleanup_old_backups

    echo "备份流程完成!"
}

# 执行主函数
main "$@"
```

### 8.2 恢复脚本

```bash
#!/bin/bash
# scripts/restore.sh

set -e

# 配置变量
BACKUP_DIR="/opt/backups"

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo "选项:"
    echo "  -d, --database FILE  恢复数据库"
    echo "  -c, --config FILE    恢复配置"
    echo "  -l, --logs FILE      恢复日志"
    echo "  -a, --all DATE       恢复所有备份 (格式: YYYYMMDD_HHMMSS)"
    echo "  -h, --help           显示帮助信息"
}

# 恢复数据库
restore_database() {
    local backup_file=$1

    echo "开始恢复数据库: $backup_file"

    # 停止应用服务
    docker-compose stop backend

    # 恢复数据库
    if [[ $backup_file == *.gz ]]; then
        gunzip -c "$backup_file" | docker-compose exec -T postgres psql -U postgres ai_ad_spend_prod
    else
        docker-compose exec -T postgres psql -U postgres ai_ad_spend_prod < "$backup_file"
    fi

    # 重启应用服务
    docker-compose start backend

    echo "数据库恢复完成"
}

# 恢复配置文件
restore_config() {
    local backup_file=$1

    echo "开始恢复配置: $backup_file"

    # 解压配置文件
    tar -xzf "$backup_file" -C /opt/ai-ad-spend/

    # 重启服务以应用新配置
    docker-compose restart nginx

    echo "配置文件恢复完成"
}

# 恢复所有备份
restore_all() {
    local date=$1

    echo "开始恢复所有备份: $date"

    # 查找备份文件
    DB_BACKUP=$(find "$BACKUP_DIR/database" -name "db_backup_$date.sql.gz" | head -n 1)
    CONFIG_BACKUP=$(find "$BACKUP_DIR/config" -name "config_$date.tar.gz" | head -n 1)
    LOGS_BACKUP=$(find "$BACKUP_DIR/logs" -name "logs_$date.tar.gz" | head -n 1)

    # 恢复各个组件
    if [[ -n "$DB_BACKUP" ]]; then
        restore_database "$DB_BACKUP"
    fi

    if [[ -n "$CONFIG_BACKUP" ]]; then
        restore_config "$CONFIG_BACKUP"
    fi

    if [[ -n "$LOGS_BACKUP" ]]; then
        tar -xzf "$LOGS_BACKUP" -C /var/log/
    fi

    echo "所有备份恢复完成"
}

# 参数解析
case "$1" in
    -d|--database)
        restore_database "$2"
        ;;
    -c|--config)
        restore_config "$2"
        ;;
    -l|--logs)
        tar -xzf "$2" -C /var/log/
        echo "日志恢复完成"
        ;;
    -a|--all)
        restore_all "$2"
        ;;
    -h|--help)
        show_help
        ;;
    *)
        show_help
        exit 1
        ;;
esac
```

---

## 9. 安全配置

### 9.1 安全加固

```bash
#!/bin/bash
# scripts/security-hardening.sh

# 禁用 root SSH 登录
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config

# 更改 SSH 端口
sudo sed -i 's/#Port 22/Port 2222/' /etc/ssh/sshd_config

# 重启 SSH 服务
sudo systemctl restart sshd

# 配置 fail2ban
sudo apt-get install -y fail2ban

# 创建 fail2ban 配置
sudo tee /etc/fail2ban/jail.local > /dev/null <<EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = 2222
logpath = /var/log/auth.log

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
EOF

# 启动 fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# 设置自动安全更新
sudo apt-get install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

echo "安全加固完成"
```

### 9.2 环境变量安全管理

```bash
#!/bin/bash
# scripts/setup-secrets.sh

# 创建 secrets 目录
mkdir -p /opt/ai-ad-spend/secrets
chmod 700 /opt/ai-ad-spend/secrets

# 生成随机密钥
generate_secret() {
    openssl rand -hex 32
}

# 生成环境变量文件
cat > /opt/ai-ad-spend/.env.prod <<EOF
# 应用配置
APP_NAME=AI广告代投系统
APP_VERSION=2.0.0
DEBUG=false
ENVIRONMENT=production

# 数据库配置
DATABASE_URL=postgresql://postgres:$(generate_secret)@postgres:5432/ai_ad_spend_prod
POSTGRES_PASSWORD=$(generate_secret)

# Supabase 配置
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Redis 配置
REDIS_URL=redis://:$(generate_secret)@redis:6379/0
REDIS_PASSWORD=$(generate_secret)

# JWT 配置
JWT_SECRET=$(generate_secret)
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS 配置
ALLOWED_ORIGINS=https://yourdomain.com

# 外部 API 配置
FACEBOOK_API_VERSION=v18.0
FACEBOOK_APP_ID=your-app-id
FACEBOOK_APP_SECRET=your-app-secret

# 监控配置
SENTRY_DSN=your-sentry-dsn
GRAFANA_PASSWORD=$(generate_secret)
EOF

# 设置文件权限
chmod 600 /opt/ai-ad-spend/.env.prod

echo "环境变量配置完成"
```

---

## 10. 故障排查

### 10.1 常见问题诊断

```bash
#!/bin/bash
# scripts/diagnose.sh

echo "=== AI广告代投系统诊断工具 ==="
echo ""

# 检查系统资源
echo "1. 系统资源检查:"
echo "CPU 使用率:"
top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}'

echo "内存使用率:"
free | grep Mem | awk '{printf("%.2f%%\n", $3/$2 * 100.0)}'

echo "磁盘使用率:"
df -h | grep -vE '^Filesystem|tmpfs|cdrom' | awk '{print $5 " " $1}'

# 检查 Docker 服务
echo ""
echo "2. Docker 服务检查:"
docker-compose ps

# 检查端口占用
echo ""
echo "3. 端口占用检查:"
for port in 80 443 8000 3000 5432 6379; do
    if netstat -tln | grep -q ":$port "; then
        echo "端口 $port: 已占用"
    else
        echo "端口 $port: 未占用"
    fi
done

# 检查日志错误
echo ""
echo "4. 应用日志错误检查:"
docker-compose logs --tail=50 backend | grep -i error || echo "无错误日志"

docker-compose logs --tail=50 frontend | grep -i error || echo "无错误日志"

# 检查数据库连接
echo ""
echo "5. 数据库连接检查:"
docker-compose exec postgres pg_isready -U postgres && echo "数据库连接正常" || echo "数据库连接异常"

# 检查 Redis 连接
echo ""
echo "6. Redis 连接检查:"
docker-compose exec redis redis-cli ping | grep -q PONG && echo "Redis 连接正常" || echo "Redis 连接异常"

echo ""
echo "=== 诊断完成 ==="
```

### 10.2 应急恢复流程

```bash
#!/bin/bash
# scripts/emergency-recovery.sh

echo "=== 应急恢复流程 ==="

# 停止所有服务
echo "1. 停止所有服务..."
docker-compose down

# 清理容器
echo "2. 清理容器..."
docker system prune -f

# 重新拉取镜像
echo "3. 重新拉取镜像..."
docker-compose pull

# 启动基础服务
echo "4. 启动基础服务..."
docker-compose up -d postgres redis

# 等待数据库启动
echo "5. 等待数据库启动..."
sleep 30

# 恢复数据库 (使用最新备份)
LATEST_BACKUP=$(ls -t /opt/backups/database/*.gz | head -n 1)
if [[ -n "$LATEST_BACKUP" ]]; then
    echo "6. 恢复数据库: $LATEST_BACKUP"
    gunzip -c "$LATEST_BACKUP" | docker-compose exec -T postgres psql -U postgres ai_ad_spend_prod
fi

# 启动应用服务
echo "7. 启动应用服务..."
docker-compose up -d

# 健康检查
echo "8. 进行健康检查..."
sleep 30

# 检查服务状态
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 后端服务正常"
else
    echo "❌ 后端服务异常"
fi

if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 前端服务正常"
else
    echo "❌ 前端服务异常"
fi

echo "=== 应急恢复完成 ==="
```

---

## 📞 技术支持

### 紧急联系方式
- **24/7 故障热线**: +86-xxx-xxxx-xxxx
- **技术负责人**: +86-xxx-xxxx-xxxx
- **DevOps 工程师**: devops@company.com

### 在线资源
- **监控面板**: https://monitor.yourdomain.com
- **日志系统**: https://logs.yourdomain.com
- **文档中心**: https://docs.company.com/ai-ad-spend

### 备份验证
- **每日备份**: 02:00 AM 自动执行
- **备份验证**: 每周日凌晨执行
- **异地备份**: 每月同步到云存储

---

**文档版本**: v1.0
**最后更新**: 2025-11-11
**下次审查**: 部署架构重大变更时
**维护责任人**: DevOps团队负责人