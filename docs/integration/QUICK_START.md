# 快速启动指南

> **文档版本**: v1.0
> **最后更新**: 2025-12-10
> **文档类型**: 快速启动
> **预计时间**: 15-20分钟

---

## 目录

1. [环境准备](#1-环境准备)
2. [后端启动](#2-后端启动)
3. [前端启动](#3-前端启动)
4. [数据库初始化](#4-数据库初始化)
5. [首次登录](#5-首次登录)
6. [验证集成](#6-验证集成)
7. [常见问题](#7-常见问题)

---

## 1. 环境准备

### 1.1 系统要求

- **操作系统**: Windows 10+, macOS 10.15+, Linux
- **Node.js**: 18.0+ (推荐 18.17+)
- **Python**: 3.11+ (推荐 3.11.5+)
- **包管理器**: npm 9+ 或 yarn 1.22+
- **数据库**: PostgreSQL 15+ (Supabase)
- **内存**: 最低 4GB (推荐 8GB+)

### 1.2 检查环境

```bash
# 检查 Node.js 版本
node --version
# 应该输出: v18.x.x 或更高

# 检查 Python 版本
python --version
# 应该输出: Python 3.11.x 或更高

# 检查 npm 版本
npm --version
# 应该输出: 9.x.x 或更高
```

### 1.3 克隆项目

```bash
# 克隆仓库
git clone https://github.com/wade56754/AI_ad_spend02.git

# 进入项目目录
cd AI_ad_spend02

# 查看项目结构
ls -la
# 应该看到: backend/, frontend/, docs/, ...
```

---

## 2. 后端启动

### 2.1 进入后端目录

```bash
cd backend
```

### 2.2 创建Python虚拟环境

**Windows**:
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate
```

**macOS/Linux**:
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate
```

**验证虚拟环境激活**:
```bash
# 命令提示符应该显示 (venv) 前缀
(venv) $ which python  # macOS/Linux
(venv) $ where python  # Windows
```

### 2.3 安装依赖

```bash
# 升级 pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt

# 验证安装
pip list | grep fastapi
# 应该看到: fastapi==0.104.x 或更高
```

### 2.4 配置环境变量

```bash
# 复制环境变量示例文件（如果没有.env文件）
# 注意：本项目已经有 .env 文件，可以直接使用

# 查看现有配置
cat .env
```

**重要配置项**:
```bash
# 数据库配置
DATABASE_URL=postgresql://postgres:55evtV3CDnh0YtnR@db.jzmcoivxhiyidizncyaq.supabase.co:5432/postgres

# Supabase配置
SUPABASE_URL=https://jzmcoivxhiyidizncyaq.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...

# CORS配置
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 2.5 运行数据库迁移

```bash
# 检查当前迁移状态
alembic current

# 运行所有迁移（升级到最新版本）
alembic upgrade head

# 验证迁移
alembic history
```

### 2.6 启动后端服务

```bash
# 开发模式启动（带自动重载）
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 或使用简化命令（如果配置了）
python -m backend.main
```

**启动成功标志**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
SUCCESS: 配置加载成功 - 环境: development
   - 数据库: postgresql://...
   - 允许源: ['http://localhost:3000', 'http://127.0.0.1:3000']
INFO:     Application startup complete.
```

### 2.7 验证后端服务

**打开新终端窗口**，测试API:

```bash
# 健康检查
curl http://localhost:8000/healthz

# 应该返回:
# {"status":"ok","timestamp":"2025-12-10T..."}

# API文档
# 浏览器访问: http://localhost:8000/docs
```

---

## 3. 前端启动

### 3.1 进入前端目录

**打开新终端窗口**（保持后端运行）:

```bash
# 从项目根目录
cd frontend
```

### 3.2 安装依赖

```bash
# 使用 npm
npm install

# 或使用 yarn
yarn install

# 验证安装
npm list react
# 应该看到: react@18.x.x 或更高
```

### 3.3 配置环境变量

```bash
# 创建本地环境变量文件
cp .env.example .env.local

# 编辑 .env.local
# Windows: notepad .env.local
# macOS/Linux: nano .env.local
```

**配置内容**:
```bash
# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Feature Flags
NEXT_PUBLIC_ENABLE_DEVTOOLS=true
```

### 3.4 启动前端服务

```bash
# 开发模式启动
npm run dev

# 或使用 yarn
yarn dev
```

**启动成功标志**:
```
   ▲ Next.js 15.0.x
   - Local:        http://localhost:3000
   - Network:      http://192.168.1.x:3000

 ✓ Ready in 2.3s
```

### 3.5 验证前端服务

**浏览器访问**: http://localhost:3000

应该看到登录页面。

---

## 4. 数据库初始化

### 4.1 连接到Supabase

项目已经配置好Supabase连接，无需额外设置。

### 4.2 检查表结构

```bash
# 在后端目录，激活虚拟环境后
python -c "from backend.core.db import get_engine; from sqlalchemy import inspect; engine = get_engine(); inspector = inspect(engine); print('Tables:', inspector.get_table_names())"
```

**应该看到以下表**:
- users
- projects
- ad_accounts
- daily_reports
- topup_requests
- suppliers
- settlements
- reconciliations
- ledger_entries
- ...

### 4.3 创建初始数据（可选）

如果需要测试数据，可以运行seed脚本：

```bash
# 运行数据填充脚本
python scripts/seed_data.py

# 或手动创建测试数据
```

---

## 5. 首次登录

### 5.1 注册测试账号

**方式1: 通过前端注册**

1. 浏览器访问: http://localhost:3000/register（如果有注册页面）
2. 填写注册信息:
   - 邮箱: test@example.com
   - 用户名: testuser
   - 密码: Test@123456
   - 全名: Test User

**方式2: 通过API注册**

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "Test@123456",
    "full_name": "Test User"
  }'
```

**方式3: 直接在Supabase创建用户**

1. 访问: https://supabase.com/dashboard
2. 登录到项目
3. 在 Authentication > Users 中创建用户

### 5.2 登录系统

1. 访问登录页面: http://localhost:3000/login

2. 输入凭证:
   - **用户名/邮箱**: test@example.com
   - **密码**: Test@123456

3. 点击"登录"

4. 登录成功后，应该跳转到仪表盘首页

### 5.3 验证登录状态

**浏览器开发工具检查**:

1. 按 F12 打开开发工具
2. 切换到 Application/Storage 标签
3. 查看 Local Storage
4. 应该看到以下键值:
   - `auth-token`: JWT access token
   - `refresh-token`: JWT refresh token
   - `user-info`: 用户信息 JSON

---

## 6. 验证集成

### 6.1 测试API调用

在浏览器控制台 (F12 > Console) 执行:

```javascript
// 测试获取当前用户信息
fetch('http://localhost:8000/api/v1/auth/me', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('auth-token')}`,
    'Content-Type': 'application/json'
  }
})
  .then(res => res.json())
  .then(data => console.log('User Info:', data))
  .catch(err => console.error('Error:', err))
```

**预期结果**:
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid-string",
      "email": "test@example.com",
      "username": "testuser",
      "full_name": "Test User",
      "role": "admin",
      "is_active": true
    }
  }
}
```

### 6.2 测试页面功能

访问各个页面，确保正常显示：

1. **仪表盘首页**: http://localhost:3000/
2. **项目管理**: http://localhost:3000/projects
3. **日报管理**: http://localhost:3000/daily-reports
4. **充值管理**: http://localhost:3000/topups
5. **供应商管理**: http://localhost:3000/suppliers
6. **结算管理**: http://localhost:3000/settlements

### 6.3 测试CRUD操作

**创建项目示例**:

1. 访问项目管理页面
2. 点击"新建项目"按钮
3. 填写项目信息:
   - 项目名称: 测试项目
   - 客户名称: 测试客户
   - 描述: 这是一个测试项目
4. 点击"提交"
5. 应该看到新项目出现在列表中

---

## 7. 常见问题

### 7.1 后端启动失败

**问题**: `ModuleNotFoundError: No module named 'backend'`

**解决方案**:
```bash
# 确保在backend目录
cd backend

# 确保虚拟环境已激活
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# 重新安装依赖
pip install -r requirements.txt
```

---

**问题**: `Database connection failed`

**解决方案**:
```bash
# 检查数据库配置
cat .env | grep DATABASE_URL

# 测试数据库连接
python -c "from backend.core.db import get_engine; engine = get_engine(); print('Connection OK' if engine else 'Connection Failed')"

# 如果连接失败，检查:
# 1. DATABASE_URL 是否正确
# 2. 网络是否正常
# 3. Supabase服务是否可用
```

### 7.2 前端启动失败

**问题**: `Error: Cannot find module 'next'`

**解决方案**:
```bash
# 删除 node_modules 和 package-lock.json
rm -rf node_modules package-lock.json

# 重新安装
npm install
```

---

**问题**: `Module not found: Can't resolve '@/lib/api'`

**解决方案**:
```bash
# 检查 tsconfig.json 的路径配置
cat tsconfig.json | grep "@"

# 应该看到:
# "paths": {
#   "@/*": ["./src/*"]
# }

# 重启开发服务器
npm run dev
```

### 7.3 CORS错误

**问题**: 浏览器控制台显示 `CORS policy` 错误

**解决方案**:

1. 检查后端CORS配置:
```bash
# backend/.env
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

2. 重启后端服务:
```bash
# 按 Ctrl+C 停止服务
# 重新启动
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

3. 清除浏览器缓存并刷新页面

### 7.4 登录失败

**问题**: 登录时提示 `Invalid credentials`

**解决方案**:

1. 确认用户已创建:
```bash
# 通过API检查用户
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <token>"
```

2. 重置密码（如果忘记）:
```bash
# 在Supabase Dashboard中重置
# 或使用忘记密码功能
```

3. 检查Supabase配置:
```bash
# backend/.env
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
```

### 7.5 API调用失败

**问题**: API返回 `401 Unauthorized`

**解决方案**:

1. 检查Token是否存在:
```javascript
console.log('Token:', localStorage.getItem('auth-token'))
```

2. 检查Token是否有效:
```bash
curl http://localhost:8000/api/v1/auth/verify-token \
  -H "Authorization: Bearer <token>"
```

3. 重新登录获取新Token

---

**问题**: API返回 `404 Not Found`

**解决方案**:

1. 检查API端点是否正确:
```javascript
// 正确: /api/v1/projects
// 错误: /projects
```

2. 检查后端服务是否启动:
```bash
curl http://localhost:8000/healthz
```

3. 查看后端日志:
```bash
# 后端终端应该显示请求日志
# 如果没有，说明请求未到达后端
```

### 7.6 获取帮助

如果问题仍未解决：

1. **查看完整文档**: [docs/integration/FRONTEND_BACKEND_INTEGRATION.md](./FRONTEND_BACKEND_INTEGRATION.md)
2. **检查日志**:
   - 后端日志: 终端输出
   - 前端日志: 浏览器控制台
   - 数据库日志: Supabase Dashboard
3. **查看API文档**: http://localhost:8000/docs
4. **联系开发团队**: 提供错误日志和复现步骤

---

## 附录: 快速命令参考

### 后端命令

```bash
# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# 启动开发服务器
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 运行迁移
alembic upgrade head

# 创建新迁移
alembic revision --autogenerate -m "description"

# 查看迁移历史
alembic history

# 运行测试
pytest

# 代码格式化
black .

# 代码检查
flake8
```

### 前端命令

```bash
# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 启动生产服务器
npm start

# 运行测试
npm test

# 代码检查
npm run lint

# 类型检查
npm run type-check
```

### 完整启动流程

**终端1 - 后端**:
```bash
cd backend
source venv/bin/activate  # 或 venv\Scripts\activate
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**终端2 - 前端**:
```bash
cd frontend
npm run dev
```

**浏览器**:
```
http://localhost:3000
```

---

**下一步**:
- 阅读 [API集成清单](./API_INTEGRATION_CHECKLIST.md) 了解需要实现的功能
- 阅读 [前后端集成指南](./FRONTEND_BACKEND_INTEGRATION.md) 了解详细的集成方案
- 查看 [API规范文档](../2.sot/API_SOT.md) 了解完整的API定义

**文档维护者**: AI Development Team
**最后更新**: 2025-12-10
