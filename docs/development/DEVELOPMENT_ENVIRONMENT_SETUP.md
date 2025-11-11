# 开发环境配置指南

> **文档目的**: 为AI广告代投系统提供统一的开发环境配置标准
> **目标读者**: 开发团队成员、DevOps工程师
> **更新日期**: 2025-11-11
> **版本**: v1.0

---

## 📋 目录

1. [系统要求](#1-系统要求)
2. [开发工具安装](#2-开发工具安装)
3. [环境配置](#3-环境配置)
4. [项目搭建](#4-项目搭建)
5. [数据库配置](#5-数据库配置)
6. [开发服务启动](#6-开发服务启动)
7. [代码规范配置](#7-代码规范配置)
8. [常见问题排查](#8-常见问题排查)

---

## 1. 系统要求

### 1.1 操作系统支持
- **推荐**: Windows 10/11, macOS 10.15+, Ubuntu 20.04+
- **最低**: Windows 8.1, macOS 10.14, Ubuntu 18.04

### 1.2 硬件要求
- **CPU**: 4核心以上
- **内存**: 16GB以上 (推荐32GB)
- **存储**: 50GB可用空间
- **网络**: 稳定的互联网连接

### 1.3 软件版本要求

| 组件 | 最低版本 | 推荐版本 | 用途 |
|------|----------|----------|------|
| Docker Desktop | 4.0 | 4.20+ | 容器化开发环境 |
| Node.js | 18.0 | 20.10+ | 前端开发运行时 |
| npm | 8.0 | 10.0+ | 前端包管理器 |
| Python | 3.11 | 3.11.7+ | 后端开发语言 |
| Git | 2.30 | 2.40+ | 版本控制 |

---

## 2. 开发工具安装

### 2.1 Docker Desktop 安装

#### Windows
```bash
# 下载并安装 Docker Desktop
# https://www.docker.com/products/docker-desktop/

# 安装完成后验证
docker --version
docker-compose --version
```

#### macOS
```bash
# 使用 Homebrew 安装
brew install --cask docker

# 验证安装
docker --version
docker-compose --version
```

#### Ubuntu
```bash
# 安装 Docker
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 将用户添加到 docker 组
sudo usermod -aG docker $USER
```

### 2.2 Node.js 安装

#### 使用 nvm (推荐)
```bash
# 安装 nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc

# 安装并使用 Node.js 20
nvm install 20
nvm use 20

# 验证安装
node --version
npm --version
```

#### 直接安装
```bash
# Windows: 从官网下载安装包
# https://nodejs.org/

# macOS (使用 Homebrew)
brew install node@20

# Ubuntu
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 2.3 Python 安装

#### Windows
```bash
# 从官网下载 Python 3.11.7
# https://www.python.org/downloads/release/python-3117/
# 安装时勾选 "Add Python to PATH"

# 验证安装
python --version
pip --version
```

#### macOS
```bash
# 使用 Homebrew
brew install python@3.11

# 验证安装
python3 --version
pip3 --version
```

#### Ubuntu
```bash
# 更新包列表
sudo apt-get update

# 安装 Python 3.11
sudo apt-get install -y python3.11 python3.11-pip python3.11-venv

# 验证安装
python3.11 --version
pip3 --version
```

### 2.4 Git 安装

#### Windows
```bash
# 下载并安装 Git for Windows
# https://git-scm.com/download/win

# 验证安装
git --version
```

#### macOS
```bash
# 使用 Homebrew
brew install git

# 或者从官网下载
# https://git-scm.com/download/mac

# 验证安装
git --version
```

#### Ubuntu
```bash
sudo apt-get install git

# 验证安装
git --version
```

---

## 3. 环境配置

### 3.1 Git 配置

```bash
# 设置用户信息
git config --global user.name "Your Name"
git config --global user.email "your.email@company.com"

# 设置默认分支名
git config --global init.defaultBranch main

# 设置行结束符 (Windows)
git config --global core.autocrlf true

# 设置行结束符 (macOS/Linux)
git config --global core.autocrlf input

# 设置编辑器
git config --global core.editor "code --wait"

# 设置推送策略
git config --global push.default simple
```

### 3.2 SSH 密钥配置

```bash
# 生成 SSH 密钥
ssh-keygen -t ed25519 -C "your.email@company.com"

# 启动 ssh-agent
eval "$(ssh-agent -s)"

# 添加私钥到 ssh-agent
ssh-add ~/.ssh/id_ed25519

# 复制公钥到剪贴板
# macOS
pbcopy < ~/.ssh/id_ed25519.pub
# Linux
cat ~/.ssh/id_ed25519.pub | xclip -selection clipboard
# Windows
cat ~/.ssh/id_ed25519.pub | clip

# 将公钥添加到 GitHub/GitLab 等平台
```

### 3.3 镜像源配置

#### npm 镜像源
```bash
# 设置淘宝镜像
npm config set registry https://registry.npmmirror.com

# 验证镜像源
npm config get registry
```

#### pip 镜像源
```bash
# 创建 pip 配置目录
mkdir -p ~/.pip

# 创建配置文件
cat > ~/.pip/pip.conf << EOF
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
EOF
```

---

## 4. 项目搭建

### 4.1 克隆项目代码

```bash
# 克隆项目仓库
git clone git@github.com:your-org/ai-ad-spend.git
cd ai-ad-spend

# 查看项目结构
tree -L 2
```

### 4.2 后端环境搭建

```bash
# 进入后端目录
cd backend

# 创建 Python 虚拟环境
python3.11 -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 安装 pre-commit 钩子
pre-commit install
```

### 4.3 前端环境搭建

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 或使用 yarn
yarn install
```

### 4.4 环境变量配置

#### 后端环境变量 (.env)
```bash
# 在 backend 目录创建 .env 文件
cat > .env << EOF
# 应用配置
APP_NAME=AI广告代投系统
APP_VERSION=2.0.0
DEBUG=true
ENVIRONMENT=development

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/ai_ad_spend
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# JWT 配置
JWT_SECRET=your-jwt-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS 配置
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# 外部 API 配置
FACEBOOK_API_VERSION=v18.0
FACEBOOK_APP_ID=your-app-id
FACEBOOK_APP_SECRET=your-app-secret

# 日志配置
LOG_LEVEL=DEBUG
LOG_FORMAT=json

# 监控配置
SENTRY_DSN=your-sentry-dsn
PROMETHEUS_ENABLED=true
EOF
```

#### 前端环境变量 (.env.local)
```bash
# 在 frontend 目录创建 .env.local 文件
cat > .env.local << EOF
# API 配置
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# Supabase 配置
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# 应用配置
NEXT_PUBLIC_APP_NAME=AI广告代投系统
NEXT_PUBLIC_APP_VERSION=2.0.0
NEXT_PUBLIC_ENVIRONMENT=development

# 功能开关
NEXT_PUBLIC_ENABLE_ANALYTICS=false
NEXT_PUBLIC_ENABLE_ERROR_REPORTING=false
NEXT_PUBLIC_ENABLE_PERFORMANCE_MONITORING=false
EOF
```

---

## 5. 数据库配置

### 5.1 Docker 启动数据库

```bash
# 在项目根目录启动开发数据库
docker-compose -f docker-compose.dev.yml up -d postgres redis

# 等待服务启动
sleep 10

# 查看服务状态
docker-compose -f docker-compose.dev.yml ps
```

### 5.2 数据库迁移

```bash
# 进入后端目录
cd backend

# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 安装 Alembic
pip install alembic

# 初始化 Alembic
alembic init alembic

# 创建数据库表
alembic upgrade head

# 或者直接使用脚本创建
python scripts/create_database.py
```

### 5.3 种子数据

```bash
# 运行种子数据脚本
python scripts/seed_data.py

# 检查种子数据
python scripts/check_seed_data.py
```

---

## 6. 开发服务启动

### 6.1 启动后端服务

```bash
# 进入后端目录
cd backend

# 激活虚拟环境
source venv/bin/activate

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用启动脚本
./scripts/dev_start.sh
```

### 6.2 启动前端服务

```bash
# 新开终端，进入前端目录
cd frontend

# 启动开发服务器
npm run dev

# 或使用 yarn
yarn dev
```

### 6.3 验证服务启动

```bash
# 检查后端健康状态
curl http://localhost:8000/health

# 检查前端页面
curl http://localhost:3000

# 检查 API 文档
curl http://localhost:8000/docs
```

---

## 7. 代码规范配置

### 7.1 VS Code 配置

#### 安装扩展
```json
{
  "recommendations": [
    "ms-python.python",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "ms-python.black-formatter",
    "charliermarsh.ruff",
    "dbaeumer.vscode-eslint",
    "ms-vscode.vscode-typescript-next",
    "ms-vscode-remote.remote-containers"
  ]
}
```

#### 工作区配置 (.vscode/settings.json)
```json
{
  "python.defaultInterpreterPath": "./backend/venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/node_modules": true,
    "**/dist": true,
    "**/.next": true
  }
}
```

### 7.2 Python 代码规范

#### Black 配置 (pyproject.toml)
```toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  migrations
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["app"]

[tool.ruff]
line-length = 88
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501",  # line too long, handled by black
    "B008",  # do not perform function calls in argument defaults
]
```

### 7.3 TypeScript 代码规范

#### ESLint 配置 (.eslintrc.js)
```javascript
module.exports = {
  extends: [
    'next/core-web-vitals',
    '@typescript-eslint/recommended',
    'prettier',
  ],
  parser: '@typescript-eslint/parser',
  plugins: ['@typescript-eslint'],
  rules: {
    '@typescript-eslint/no-unused-vars': 'error',
    '@typescript-eslint/no-explicit-any': 'warn',
    'prefer-const': 'error',
    'no-var': 'error',
  },
};
```

#### Prettier 配置 (.prettierrc)
```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2,
  "useTabs": false
}
```

### 7.4 Pre-commit 钩子

#### 配置文件 (.pre-commit-config.yaml)
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-merge-conflict

  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.280
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.0.0
    hooks:
      - id: prettier
        types_or: [javascript, jsx, ts, tsx, json, css, scss, md]
```

---

## 8. 常见问题排查

### 8.1 Docker 相关问题

#### 问题: Docker Desktop 启动失败
```bash
# 检查 Docker 状态
docker version
docker info

# 重启 Docker Desktop
# Windows/macOS: 重启 Docker Desktop 应用
# Linux: sudo systemctl restart docker
```

#### 问题: 端口被占用
```bash
# 查看端口占用
# Windows
netstat -ano | findstr :8000
# macOS/Linux
lsof -i :8000

# 杀死占用进程
# Windows
taskkill /PID <PID> /F
# macOS/Linux
kill -9 <PID>
```

### 8.2 Python 环境问题

#### 问题: 虚拟环境激活失败
```bash
# 重新创建虚拟环境
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 重新安装依赖
pip install -r requirements.txt
```

#### 问题: 依赖安装失败
```bash
# 清理 pip 缓存
pip cache purge

# 升级 pip
pip install --upgrade pip

# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 8.3 Node.js 环境问题

#### 问题: npm 安装依赖失败
```bash
# 清理 npm 缓存
npm cache clean --force

# 删除 node_modules 重新安装
rm -rf node_modules package-lock.json
npm install

# 使用 yarn 替代
yarn install
```

#### 问题: EACCES 权限错误
```bash
# 修复 npm 权限
npm config set prefix ~/.npm-global
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

### 8.4 数据库连接问题

#### 问题: PostgreSQL 连接失败
```bash
# 检查数据库容器状态
docker ps | grep postgres

# 查看数据库日志
docker logs <postgres-container-name>

# 重启数据库容器
docker-compose restart postgres
```

#### 问题: 迁移失败
```bash
# 检查迁移状态
alembic current

# 回滚迁移
alembic downgrade -1

# 重新生成迁移
alembic revision --autogenerate -m "fix migration"
alembic upgrade head
```

### 8.5 性能优化

#### 问题: 启动速度慢
```bash
# 增加内存限制
docker-compose -f docker-compose.dev.yml up -d --scale postgres=1

# 优化 Docker 配置
# 在 Docker Desktop 中分配更多资源
```

#### 问题: 前端构建慢
```bash
# 增加 Node.js 内存限制
export NODE_OPTIONS="--max-old-space-size=8192"

# 使用 SWC 编译器
npm run build -- --swc
```

---

## 📞 技术支持

### 开发团队支持
- **后端技术支持**: backend-team@company.com
- **前端技术支持**: frontend-team@company.com
- **DevOps 支持**: devops-team@company.com
- **技术架构师**: architect@company.com

### 在线资源
- **项目文档**: https://docs.company.com/ai-ad-spend
- **API 文档**: http://localhost:8000/docs
- **GitHub 仓库**: https://github.com/your-org/ai-ad-spend
- **问题反馈**: https://github.com/your-org/ai-ad-spend/issues

### 应急联系
- **紧急故障**: +86-xxx-xxxx-xxxx
- **技术负责人**: +86-xxx-xxxx-xxxx

---

**文档版本**: v1.0
**最后更新**: 2025-11-11
**下次审查**: 环境工具重大更新时
**维护责任人**: 开发团队负责人