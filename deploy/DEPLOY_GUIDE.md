# AI 广告代投系统 - 宝塔部署指南

> 版本: v1.0
> 更新日期: 2025-12-11

---

## 一、部署前准备

### 1.1 服务器要求

| 项目 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 2核 | 4核 |
| 内存 | 4GB | 8GB |
| 硬盘 | 40GB SSD | 100GB SSD |
| 系统 | CentOS 7+ / Ubuntu 20.04+ | CentOS 8 / Ubuntu 22.04 |
| 带宽 | 3Mbps | 5Mbps+ |

### 1.2 宝塔面板安装

```bash
# CentOS
yum install -y wget && wget -O install.sh https://download.bt.cn/install/install_6.0.sh && sh install.sh ed8484bec

# Ubuntu
wget -O install.sh https://download.bt.cn/install/install-ubuntu_6.0.sh && sudo bash install.sh ed8484bec
```

### 1.3 宝塔软件安装

在宝塔软件商店安装：

- [x] Nginx 1.24+
- [x] Python 项目管理器 2.x
- [x] Node.js 版本管理器 (安装 Node 20.x)
- [x] PM2 管理器

---

## 二、快速部署 (自动脚本)

### 2.1 上传项目

将项目上传到服务器 `/www/wwwroot/ai-ad-system/`

### 2.2 修改配置

编辑部署脚本 `deploy/baota-deploy.sh`：

```bash
# 修改这些变量
DOMAIN="your-domain.com"  # 你的域名
```

### 2.3 执行部署

```bash
cd /www/wwwroot/ai-ad-system/deploy
chmod +x baota-deploy.sh
./baota-deploy.sh
```

---

## 三、手动部署步骤

### 3.1 后端部署

#### 创建 Python 虚拟环境

```bash
cd /www/wwwroot/ai-ad-system
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 配置环境变量

```bash
cp .env.example .env
nano .env
```

**必须修改的配置**：

```bash
# 生产模式
DEBUG=false
ENV_NAME=production

# 安全密钥 (生成命令)
# python -c "import secrets; print(secrets.token_urlsafe(64))"
JWT_SECRET=<生成的64位密钥>

# python -c "import secrets; print(secrets.token_urlsafe(32))"
ENCRYPTION_KEY=<生成的32位密钥>

# CORS (改为你的域名)
ALLOWED_ORIGINS=https://your-domain.com
FRONTEND_URL=https://your-domain.com
```

### 3.2 前端部署

```bash
cd /www/wwwroot/ai-ad-system/frontend

# 安装依赖
npm install

# 配置环境变量
cat > .env.production << 'EOF'
NEXT_PUBLIC_API_URL=https://your-domain.com/api
NEXT_PUBLIC_SUPABASE_URL=https://jzmcoivxhiyidizncyaq.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-anon-key>
EOF

# 构建
npm run build
```

### 3.3 PM2 配置

创建 `ecosystem.config.js`：

```javascript
module.exports = {
  apps: [
    {
      name: 'ai-ad-backend',
      cwd: '/www/wwwroot/ai-ad-system',
      script: 'venv/bin/uvicorn',
      args: 'backend.main:app --host 0.0.0.0 --port 8000 --workers 4',
      interpreter: 'none',
      env: {
        PYTHONPATH: '/www/wwwroot/ai-ad-system'
      }
    },
    {
      name: 'ai-ad-frontend',
      cwd: '/www/wwwroot/ai-ad-system/frontend',
      script: 'npm',
      args: 'start -- -p 3000',
      interpreter: 'none'
    }
  ]
}
```

启动服务：

```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### 3.4 Nginx 配置

在宝塔面板添加站点，然后修改 Nginx 配置：

```nginx
server {
    listen 80;
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL (宝塔申请后自动配置)
    ssl_certificate    /www/server/panel/vhost/cert/your-domain.com/fullchain.pem;
    ssl_certificate_key    /www/server/panel/vhost/cert/your-domain.com/privkey.pem;

    # 强制 HTTPS
    if ($server_port !~ 443){
        rewrite ^(/.*)$ https://$host$1 permanent;
    }

    # 前端
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        client_max_body_size 50m;
    }

    # 健康检查
    location /healthz {
        proxy_pass http://127.0.0.1:8000/healthz;
    }

    # 日志
    access_log /www/wwwlogs/your-domain.com.log;
    error_log /www/wwwlogs/your-domain.com.error.log;
}
```

---

## 四、SSL 证书

### 4.1 宝塔申请 Let's Encrypt

```
网站 → 设置 → SSL → Let's Encrypt → 申请
```

### 4.2 手动申请 (可选)

```bash
# 安装 certbot
yum install -y certbot

# 申请证书
certbot certonly --webroot -w /www/wwwroot/ai-ad-system -d your-domain.com

# 自动续期
crontab -e
0 0 1 * * certbot renew --quiet && nginx -s reload
```

---

## 五、运维命令

### 5.1 服务管理

```bash
# 查看状态
pm2 status

# 查看日志
pm2 logs
pm2 logs ai-ad-backend
pm2 logs ai-ad-frontend

# 重启服务
pm2 restart ai-ad-backend
pm2 restart ai-ad-frontend
pm2 restart all

# 停止服务
pm2 stop all

# 删除服务
pm2 delete all
```

### 5.2 Nginx 管理

```bash
# 测试配置
nginx -t

# 重载配置
nginx -s reload

# 查看日志
tail -f /www/wwwlogs/your-domain.com.log
tail -f /www/wwwlogs/your-domain.com.error.log
```

### 5.3 更新部署

```bash
cd /www/wwwroot/ai-ad-system

# 拉取最新代码
git pull

# 更新后端依赖
source venv/bin/activate
pip install -r requirements.txt

# 更新前端
cd frontend
npm install
npm run build

# 重启服务
pm2 restart all
```

---

## 六、监控与告警

### 6.1 宝塔监控

```
宝塔面板 → 监控 → 开启系统监控
```

### 6.2 健康检查

```bash
# 手动检查
curl https://your-domain.com/healthz

# 定时检查 (crontab)
*/5 * * * * curl -sf https://your-domain.com/healthz || echo "服务异常" | mail -s "告警" admin@example.com
```

### 6.3 日志监控

```bash
# 监控错误日志
tail -f /www/wwwlogs/your-domain.com.error.log | grep -i error
```

---

## 七、常见问题

### Q1: 502 Bad Gateway

**原因**: 后端服务未启动或端口错误

**解决**:
```bash
pm2 status
pm2 restart ai-ad-backend
pm2 logs ai-ad-backend
```

### Q2: 前端白屏

**原因**: 前端构建失败或环境变量错误

**解决**:
```bash
cd /www/wwwroot/ai-ad-system/frontend
npm run build
pm2 logs ai-ad-frontend
```

### Q3: 数据库连接失败

**原因**: Supabase 配置错误或 IP 未加白名单

**解决**:
1. 检查 `.env` 中的 DATABASE_URL
2. 在 Supabase 后台添加服务器 IP 到白名单

### Q4: CORS 错误

**原因**: ALLOWED_ORIGINS 配置错误

**解决**:
```bash
# 编辑 .env
ALLOWED_ORIGINS=https://your-domain.com

# 重启后端
pm2 restart ai-ad-backend
```

### Q5: 上传文件失败

**原因**: Nginx client_max_body_size 限制

**解决**:
在 Nginx 配置中添加：
```nginx
client_max_body_size 50m;
```

---

## 八、部署检查清单

| 项目 | 检查内容 | 状态 |
|------|---------|------|
| **服务器** | 宝塔面板已安装 | ☐ |
| | Nginx 已安装 | ☐ |
| | Python 3.11 已安装 | ☐ |
| | Node.js 20 已安装 | ☐ |
| | PM2 已安装 | ☐ |
| **配置** | .env 已配置 | ☐ |
| | JWT_SECRET 已更换 | ☐ |
| | ENCRYPTION_KEY 已更换 | ☐ |
| | DEBUG=false | ☐ |
| | CORS 配置正确 | ☐ |
| **前端** | .env.production 已配置 | ☐ |
| | npm run build 成功 | ☐ |
| **服务** | 后端已启动 (端口 8000) | ☐ |
| | 前端已启动 (端口 3000) | ☐ |
| | /healthz 返回正常 | ☐ |
| **安全** | SSL 证书已申请 | ☐ |
| | HTTPS 强制跳转 | ☐ |
| | 防火墙规则配置 | ☐ |

---

## 九、联系支持

如遇问题，请提供以下信息：

1. 服务器系统版本
2. 宝塔面板版本
3. 错误日志 (`pm2 logs`)
4. Nginx 错误日志

---

**文档版本**: v1.0
**最后更新**: 2025-12-11
