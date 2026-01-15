#!/bin/bash
# ============================================================
# AI 广告代投系统 - 宝塔面板自动化部署脚本
# 版本: v1.0
# 用途: 一键部署后端 + 前端到宝塔服务器
# ============================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量 (部署前请修改)
PROJECT_NAME="ai-ad-system"
PROJECT_DIR="/www/wwwroot/${PROJECT_NAME}"
DOMAIN="your-domain.com"  # 修改为你的域名
BACKEND_PORT=8000
FRONTEND_PORT=3000
PYTHON_VERSION="3.11"
NODE_VERSION="20"

# 打印带颜色的消息
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查是否为 root 用户
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "请使用 root 用户运行此脚本"
        exit 1
    fi
}

# 检查宝塔是否安装
check_bt() {
    if [ ! -f "/etc/init.d/bt" ]; then
        print_error "未检测到宝塔面板，请先安装宝塔"
        exit 1
    fi
    print_success "宝塔面板已安装"
}

# 安装系统依赖
install_system_deps() {
    print_info "安装系统依赖..."

    if command -v yum &> /dev/null; then
        yum install -y git curl wget gcc make
    elif command -v apt-get &> /dev/null; then
        apt-get update
        apt-get install -y git curl wget gcc make
    fi

    print_success "系统依赖安装完成"
}

# 创建项目目录
create_project_dir() {
    print_info "创建项目目录..."

    if [ -d "$PROJECT_DIR" ]; then
        print_warning "项目目录已存在: $PROJECT_DIR"
        read -p "是否删除并重新部署? (y/n): " confirm
        if [ "$confirm" = "y" ]; then
            rm -rf "$PROJECT_DIR"
        else
            print_info "保留现有目录，继续部署..."
        fi
    fi

    mkdir -p "$PROJECT_DIR"
    print_success "项目目录创建完成: $PROJECT_DIR"
}

# 克隆或复制项目
setup_project() {
    print_info "设置项目文件..."

    # 如果脚本在项目目录中运行，复制文件
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PARENT_DIR="$(dirname "$SCRIPT_DIR")"

    if [ -f "$PARENT_DIR/requirements.txt" ]; then
        print_info "从本地复制项目文件..."
        cp -r "$PARENT_DIR"/* "$PROJECT_DIR/"
    else
        print_warning "请手动将项目文件上传到 $PROJECT_DIR"
        print_warning "或修改脚本使用 git clone"
        exit 1
    fi

    print_success "项目文件设置完成"
}

# 配置 Python 环境
setup_python() {
    print_info "配置 Python 环境..."

    cd "$PROJECT_DIR"

    # 创建虚拟环境
    python${PYTHON_VERSION} -m venv venv
    source venv/bin/activate

    # 升级 pip
    pip install --upgrade pip

    # 安装依赖
    pip install -r requirements.txt

    print_success "Python 环境配置完成"
}

# 配置环境变量
setup_env() {
    print_info "配置环境变量..."

    cd "$PROJECT_DIR"

    if [ ! -f ".env" ]; then
        cp .env.example .env

        # 生成安全密钥
        JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(64))")
        ENCRYPTION_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

        # 替换密钥
        sed -i "s/CHANGE_THIS_IN_PRODUCTION_USE_GENERATED_64_CHAR_SECRET/$JWT_SECRET/" .env
        sed -i "s/CHANGE_THIS_IN_PRODUCTION_USE_GENERATED_32_CHAR_SECRET/$ENCRYPTION_KEY/" .env

        # 设置生产模式
        sed -i "s/DEBUG=true/DEBUG=false/" .env
        sed -i "s/ENV_NAME=development/ENV_NAME=production/" .env

        # 设置 CORS
        sed -i "s|FRONTEND_URL=http://localhost:3000|FRONTEND_URL=https://${DOMAIN}|" .env
        sed -i "s|ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000|ALLOWED_ORIGINS=https://${DOMAIN}|" .env

        print_warning "请编辑 .env 文件，确认 Supabase 配置正确"
        print_warning "配置文件路径: $PROJECT_DIR/.env"
    else
        print_info ".env 文件已存在，跳过创建"
    fi

    print_success "环境变量配置完成"
}

# 配置前端
setup_frontend() {
    print_info "配置前端环境..."

    cd "$PROJECT_DIR/frontend"

    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js 未安装，请在宝塔面板安装 Node.js 版本管理器"
        exit 1
    fi

    # 安装依赖
    pnpm install

    # 创建生产环境配置
    cat > .env.production << EOF
NEXT_PUBLIC_API_URL=https://${DOMAIN}/api
NEXT_PUBLIC_SUPABASE_URL=https://jzmcoivxhiyidizncyaq.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
EOF

    print_warning "请编辑前端环境配置: $PROJECT_DIR/frontend/.env.production"

    # 构建
    pnpm run build

    print_success "前端配置完成"
}

# 安装 PM2
setup_pm2() {
    print_info "配置 PM2..."

    if ! command -v pm2 &> /dev/null; then
        pnpm add -g pm2
    fi

    # 创建 PM2 配置
    cat > "$PROJECT_DIR/ecosystem.config.js" << EOF
module.exports = {
  apps: [
    {
      name: 'ai-ad-backend',
      cwd: '${PROJECT_DIR}',
      script: 'venv/bin/uvicorn',
      args: 'backend.main:app --host 0.0.0.0 --port ${BACKEND_PORT} --workers 4',
      interpreter: 'none',
      env: {
        PYTHONPATH: '${PROJECT_DIR}'
      }
    },
    {
      name: 'ai-ad-frontend',
      cwd: '${PROJECT_DIR}/frontend',
      script: 'pnpm',
      args: 'start -- -p ${FRONTEND_PORT}',
      interpreter: 'none'
    }
  ]
}
EOF

    print_success "PM2 配置完成"
}

# 创建 Nginx 配置
create_nginx_config() {
    print_info "创建 Nginx 配置..."

    NGINX_CONF="/www/server/panel/vhost/nginx/${DOMAIN}.conf"

    cat > "$NGINX_CONF" << EOF
server {
    listen 80;
    listen 443 ssl http2;
    server_name ${DOMAIN};
    index index.html;
    root ${PROJECT_DIR}/frontend;

    # SSL 配置 (宝塔申请证书后自动填充)
    #ssl_certificate    /www/server/panel/vhost/cert/${DOMAIN}/fullchain.pem;
    #ssl_certificate_key    /www/server/panel/vhost/cert/${DOMAIN}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_timeout 10m;
    ssl_session_cache builtin:1000 shared:SSL:10m;

    # 强制 HTTPS
    if (\$server_port !~ 443){
        rewrite ^(/.*)$ https://\$host\$1 permanent;
    }

    # 前端代理
    location / {
        proxy_pass http://127.0.0.1:${FRONTEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 60s;
    }

    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:${BACKEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        client_max_body_size 50m;
    }

    # 健康检查
    location /healthz {
        proxy_pass http://127.0.0.1:${BACKEND_PORT}/healthz;
    }

    # 静态资源
    location /_next/static {
        proxy_pass http://127.0.0.1:${FRONTEND_PORT};
        proxy_cache_valid 200 60m;
        add_header Cache-Control "public, immutable, max-age=31536000";
    }

    # 日志
    access_log /www/wwwlogs/${DOMAIN}.log;
    error_log /www/wwwlogs/${DOMAIN}.error.log;
}
EOF

    print_success "Nginx 配置创建完成: $NGINX_CONF"
    print_warning "请在宝塔面板申请 SSL 证书后，取消 ssl_certificate 行的注释"
}

# 启动服务
start_services() {
    print_info "启动服务..."

    cd "$PROJECT_DIR"

    # 使用 PM2 启动
    pm2 start ecosystem.config.js
    pm2 save
    pm2 startup

    # 重载 Nginx
    nginx -t && nginx -s reload

    print_success "服务启动完成"
}

# 验证部署
verify_deployment() {
    print_info "验证部署..."

    sleep 3

    # 检查后端
    if curl -s "http://127.0.0.1:${BACKEND_PORT}/healthz" | grep -q "ok\|healthy"; then
        print_success "后端服务正常 (端口 ${BACKEND_PORT})"
    else
        print_error "后端服务异常，请检查日志"
    fi

    # 检查前端
    if curl -s "http://127.0.0.1:${FRONTEND_PORT}" | grep -q "html"; then
        print_success "前端服务正常 (端口 ${FRONTEND_PORT})"
    else
        print_error "前端服务异常，请检查日志"
    fi

    # 显示状态
    pm2 list
}

# 显示部署信息
show_info() {
    echo ""
    echo "============================================================"
    echo -e "${GREEN}部署完成!${NC}"
    echo "============================================================"
    echo ""
    echo "项目目录: $PROJECT_DIR"
    echo "后端端口: $BACKEND_PORT"
    echo "前端端口: $FRONTEND_PORT"
    echo ""
    echo "访问地址: https://${DOMAIN}"
    echo "API 地址: https://${DOMAIN}/api/"
    echo "健康检查: https://${DOMAIN}/healthz"
    echo ""
    echo "============================================================"
    echo "常用命令:"
    echo "============================================================"
    echo "查看日志:     pm2 logs"
    echo "重启后端:     pm2 restart ai-ad-backend"
    echo "重启前端:     pm2 restart ai-ad-frontend"
    echo "重启全部:     pm2 restart all"
    echo "查看状态:     pm2 status"
    echo "============================================================"
    echo ""
    echo -e "${YELLOW}注意事项:${NC}"
    echo "1. 请在宝塔面板申请 SSL 证书"
    echo "2. 编辑 .env 确认数据库配置"
    echo "3. 编辑 frontend/.env.production 确认前端配置"
    echo ""
}

# 主函数
main() {
    echo ""
    echo "============================================================"
    echo "AI 广告代投系统 - 宝塔自动化部署"
    echo "============================================================"
    echo ""

    check_root
    check_bt
    install_system_deps
    create_project_dir
    setup_project
    setup_python
    setup_env
    setup_frontend
    setup_pm2
    create_nginx_config
    start_services
    verify_deployment
    show_info
}

# 运行
main "$@"
