# 前后端打通完整方案

> **文档版本**: v1.0
> **最后更新**: 2025-12-10
> **文档类型**: 集成指南
> **适用范围**: 前后端开发人员

---

## 目录

1. [当前状态分析](#1-当前状态分析)
2. [CORS配置说明](#2-cors配置说明)
3. [认证流程说明](#3-认证流程说明)
4. [API调用示例](#4-api调用示例)
5. [环境变量配置](#5-环境变量配置)
6. [常见问题排查](#6-常见问题排查)

---

## 1. 当前状态分析

### 1.1 后端配置

**技术栈**:
- FastAPI 0.104+
- Python 3.11+
- PostgreSQL (Supabase)
- SQLAlchemy 2.0
- JWT (Supabase Auth)

**核心配置文件**:
- `backend/main.py` - FastAPI应用入口
- `backend/core/config.py` - 配置管理
- `backend/core/response.py` - 统一响应格式
- `backend/.env` - 环境变量配置

**已启用的API模块**:
```python
# backend/main.py
API_V1_PREFIX = "/api/v1"

# 已注册的路由器
- health           # /api/v1/health
- projects         # /api/v1/projects
- authentication   # /api/v1/auth
- ad_spend         # /api/v1/ad-spend
- ad_accounts      # /api/v1/ad-accounts
- channels         # /api/v1/channels
- topup            # /api/v1/topups
- daily_reports    # /api/v1/daily-reports
- suppliers        # /api/v1/suppliers
- settlements      # /api/v1/settlements
- transfers        # /api/v1/transfers
- ledger           # /api/v1/ledger
- finance_profit   # /api/v1/finance/profit
- import_jobs      # /api/v1/import-jobs
- reconciliation   # /api/v1/reconciliation
- reports          # /api/v1/reports
```

### 1.2 前端配置

**技术栈**:
- Next.js 15 (App Router)
- TypeScript
- Tailwind CSS
- React Query (TanStack Query)

**核心配置文件**:
- `frontend/src/lib/api.ts` - API客户端
- `frontend/.env.example` - 环境变量示例
- `frontend/src/app/providers.tsx` - 全局Provider

**已实现的页面**:
```
/login              # 登录页面
/                   # 仪表盘首页
/projects           # 项目管理
/daily-reports      # 日报管理
/topups             # 充值管理
/suppliers          # 供应商管理
/settlements        # 结算管理
/reconciliation     # 对账管理
/reports            # 报表中心
/ledger             # 财务总账
/finance/profit     # 财务利润
/ad-accounts        # 广告账户
/channels           # 渠道管理
/transfers          # 余额转移
/import-jobs        # 数据导入
```

### 1.3 集成状态评估

✅ **已完成**:
- 统一的API客户端封装 (`lib/api.ts`)
- 标准化响应格式 (Envelope模式)
- JWT认证机制
- Token自动管理 (localStorage)
- CORS跨域配置
- React Query查询键管理

⚠️ **待完善**:
- 前端页面的具体API调用实现
- 错误处理统一机制
- Token刷新逻辑
- 请求拦截器优化
- 响应拦截器优化

---

## 2. CORS配置说明

### 2.1 后端CORS配置

**配置位置**: `backend/main.py`

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,  # 从环境变量读取
    allow_credentials=True,                   # 允许携带凭证
    allow_methods=["*"],                      # 允许所有HTTP方法
    allow_headers=["*"],                      # 允许所有请求头
)
```

**环境变量配置**: `backend/.env`

```bash
# CORS 配置
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000
```

### 2.2 允许的请求头

后端默认允许所有请求头，前端需要设置的关键请求头：

```typescript
{
  'Content-Type': 'application/json',
  'Authorization': 'Bearer <token>',  // JWT令牌
  'Accept': 'application/json'
}
```

### 2.3 CORS预检请求

对于以下情况，浏览器会发送OPTIONS预检请求：
- 使用PUT、DELETE、PATCH等方法
- Content-Type为`application/json`
- 携带自定义请求头

**后端已自动处理预检请求**，无需额外配置。

---

## 3. 认证流程说明

### 3.1 认证架构

```
┌─────────────┐     JWT Token      ┌──────────────┐
│   Frontend  │ ◄─────────────────► │   Backend    │
│  (Next.js)  │                     │  (FastAPI)   │
└─────────────┘                     └──────────────┘
       │                                    │
       │                                    │
       ▼                                    ▼
┌─────────────┐                    ┌──────────────┐
│ localStorage│                    │  Supabase    │
│   (Token)   │                    │     Auth     │
└─────────────┘                    └──────────────┘
```

### 3.2 登录流程

#### 前端登录请求

**API端点**: `POST /api/v1/auth/login`

**请求示例**:
```typescript
import { apiPost } from '@/lib/api'

const login = async (identifier: string, password: string) => {
  const response = await apiPost('/api/v1/auth/login', {
    identifier,  // 用户名或邮箱
    password,
    remember_me: false
  })

  if (response.data) {
    // 保存token到localStorage
    const { access_token, refresh_token } = response.data.token
    localStorage.setItem('auth-token', access_token)
    localStorage.setItem('refresh-token', refresh_token)

    // 保存用户信息
    localStorage.setItem('user-info', JSON.stringify(response.data.user))

    return response.data
  }

  throw new Error(response.error?.message || '登录失败')
}
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid-string",
      "email": "user@example.com",
      "username": "username",
      "full_name": "Full Name",
      "role": "admin",
      "is_active": true
    },
    "token": {
      "access_token": "eyJhbGci...",
      "refresh_token": "eyJhbGci...",
      "token_type": "bearer",
      "expires_in": 1800
    }
  },
  "message": "登录成功",
  "code": null,
  "meta": null
}
```

**错误响应** (401):
```json
{
  "success": false,
  "data": null,
  "message": "用户名或密码错误",
  "code": "AUTH-001",
  "meta": null
}
```

### 3.3 Token管理

#### Token存储

前端在`lib/api.ts`中已实现自动Token管理：

```typescript
// 添加认证 token（如果存在）
if (typeof window !== 'undefined') {
  const token = localStorage.getItem('auth-token')
  if (token) {
    defaultHeaders['Authorization'] = `Bearer ${token}`
  }
}
```

#### Token刷新

**API端点**: `POST /api/v1/auth/refresh`

**请求示例**:
```typescript
const refreshToken = async () => {
  const refresh_token = localStorage.getItem('refresh-token')

  if (!refresh_token) {
    throw new Error('No refresh token available')
  }

  const response = await apiPost('/api/v1/auth/refresh', {
    refresh_token
  })

  if (response.data) {
    const { access_token, refresh_token: new_refresh_token } = response.data
    localStorage.setItem('auth-token', access_token)
    localStorage.setItem('refresh-token', new_refresh_token)
    return access_token
  }

  throw new Error('Token refresh failed')
}
```

### 3.4 获取当前用户

**API端点**: `GET /api/v1/auth/me`

**请求示例**:
```typescript
const getCurrentUser = async () => {
  const response = await apiGet('/api/v1/auth/me')
  return response.data
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid-string",
      "email": "user@example.com",
      "username": "username",
      "full_name": "Full Name",
      "role": "admin",
      "is_active": true
    },
    "profile": {
      // 用户配置信息
    }
  }
}
```

### 3.5 登出流程

**API端点**: `POST /api/v1/auth/logout`

**请求示例**:
```typescript
const logout = async () => {
  try {
    await apiPost('/api/v1/auth/logout')
  } finally {
    // 清除本地存储
    localStorage.removeItem('auth-token')
    localStorage.removeItem('refresh-token')
    localStorage.removeItem('user-info')

    // 重定向到登录页
    window.location.href = '/login'
  }
}
```

---

## 4. API调用示例

### 4.1 基础调用方式

前端已封装统一的API客户端 (`lib/api.ts`)，提供以下方法：

```typescript
// GET 请求
apiGet<T>(endpoint: string, params?: Record<string, any>): Promise<ApiResponse<T>>

// POST 请求
apiPost<T>(endpoint: string, data?: any): Promise<ApiResponse<T>>

// PUT 请求
apiPut<T>(endpoint: string, data?: any): Promise<ApiResponse<T>>

// DELETE 请求
apiDelete<T>(endpoint: string): Promise<ApiResponse<T>>

// PATCH 请求
apiPatch<T>(endpoint: string, data?: any): Promise<ApiResponse<T>>
```

### 4.2 项目管理API示例

#### 获取项目列表

```typescript
import { apiGet } from '@/lib/api'

interface Project {
  id: number
  name: string
  status: string
  created_at: string
}

const fetchProjects = async (page = 1, pageSize = 20) => {
  const response = await apiGet<Project[]>('/api/v1/projects', {
    page,
    page_size: pageSize
  })

  return {
    projects: response.data,
    pagination: response.meta?.pagination
  }
}
```

#### 创建项目

```typescript
const createProject = async (data: {
  name: string
  description?: string
  client_name?: string
}) => {
  const response = await apiPost('/api/v1/projects', data)
  return response.data
}
```

#### 更新项目

```typescript
const updateProject = async (id: number, data: Partial<Project>) => {
  const response = await apiPut(`/api/v1/projects/${id}`, data)
  return response.data
}
```

#### 删除项目

```typescript
const deleteProject = async (id: number) => {
  const response = await apiDelete(`/api/v1/projects/${id}`)
  return response.data
}
```

### 4.3 日报管理API示例

#### 获取日报列表

```typescript
const fetchDailyReports = async (filters: {
  project_id?: number
  status?: string
  date_from?: string
  date_to?: string
  page?: number
  page_size?: number
}) => {
  const response = await apiGet('/api/v1/daily-reports', filters)
  return response
}
```

#### 创建日报

```typescript
const createDailyReport = async (data: {
  project_id: number
  report_date: string
  ad_account_id: number
  conversions_raw: number
  raw_spend: number
  // ... 其他字段
}) => {
  const response = await apiPost('/api/v1/daily-reports', data)
  return response.data
}
```

### 4.4 充值管理API示例

#### 获取充值申请列表

```typescript
const fetchTopups = async (filters: {
  status?: string
  project_id?: number
  page?: number
  page_size?: number
}) => {
  const response = await apiGet('/api/v1/topups', filters)
  return response
}
```

#### 创建充值申请

```typescript
const createTopup = async (data: {
  ad_account_id: number
  amount: number
  request_notes?: string
}) => {
  const response = await apiPost('/api/v1/topups', data)
  return response.data
}
```

### 4.5 使用React Query

推荐使用React Query进行数据管理：

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiGet, apiPost, queryKeys } from '@/lib/api'

// 查询项目列表
export function useProjects(params?: Record<string, unknown>) {
  return useQuery({
    queryKey: queryKeys.projects.list(params),
    queryFn: () => apiGet('/api/v1/projects', params),
  })
}

// 创建项目
export function useCreateProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: any) => apiPost('/api/v1/projects', data),
    onSuccess: () => {
      // 刷新项目列表
      queryClient.invalidateQueries({
        queryKey: queryKeys.projects.lists()
      })
    }
  })
}
```

---

## 5. 环境变量配置

### 5.1 后端环境变量

**文件位置**: `backend/.env`

```bash
# 应用配置
APP_NAME=AI广告代投系统
DEBUG=true
ENV_NAME=development
LOG_LEVEL=DEBUG

# 数据库配置
DATABASE_URL=postgresql://user:password@host:port/database
POOL_SIZE=20
MAX_OVERFLOW=30
POOL_TIMEOUT=30

# JWT 和安全配置
JWT_SECRET=<your-64-character-secret>
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
ENCRYPTION_KEY=<your-32-character-key>

# Supabase 配置
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=<your-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>

# CORS 配置
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# API 配置
RATE_LIMIT=100
RATE_WINDOW=60
MAX_FILE_SIZE=10485760
```

### 5.2 前端环境变量

**文件位置**: `frontend/.env.local`

```bash
# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Feature Flags
NEXT_PUBLIC_ENABLE_DEVTOOLS=true
```

**说明**:
- `NEXT_PUBLIC_` 前缀的变量会暴露给浏览器
- API Base URL默认为 `http://localhost:8000`
- 生产环境需要修改为实际的后端地址

---

## 6. 常见问题排查

### 6.1 CORS跨域问题

**问题**: 浏览器报错 `Access to fetch at 'http://localhost:8000/api/v1/...' from origin 'http://localhost:3000' has been blocked by CORS policy`

**解决方案**:

1. 检查后端CORS配置:
```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

2. 检查环境变量:
```bash
# backend/.env
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

3. 确保前端API Base URL正确:
```typescript
// frontend/src/lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
```

### 6.2 401 Unauthorized 错误

**问题**: API返回401状态码

**可能原因**:
1. Token未传递或格式错误
2. Token已过期
3. Token无效

**解决方案**:

1. 检查Token是否正确保存:
```typescript
const token = localStorage.getItem('auth-token')
console.log('Current token:', token)
```

2. 检查请求头:
```typescript
// 应该包含
Authorization: Bearer eyJhbGci...
```

3. 实现Token刷新机制:
```typescript
// 在API客户端中添加拦截器
if (response.status === 401) {
  // 尝试刷新Token
  const newToken = await refreshToken()
  // 重试原请求
  return apiRequest(endpoint, { ...options, token: newToken })
}
```

### 6.3 422 Validation Error

**问题**: API返回422状态码，表示请求参数验证失败

**解决方案**:

1. 检查API文档中的参数要求
2. 确保必填字段都已提供
3. 验证字段类型和格式

**示例错误响应**:
```json
{
  "success": false,
  "code": "VALIDATION_001",
  "message": "必填字段缺失: project_id",
  "data": null
}
```

### 6.4 Network Error

**问题**: 请求失败，提示网络错误

**可能原因**:
1. 后端服务未启动
2. API地址配置错误
3. 网络连接问题

**解决方案**:

1. 检查后端服务状态:
```bash
# 访问健康检查端点
curl http://localhost:8000/healthz
```

2. 检查前端API配置:
```typescript
// frontend/src/lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
console.log('API Base URL:', API_BASE_URL)
```

3. 检查浏览器控制台的网络请求

### 6.5 Response格式不符合预期

**问题**: 后端返回的数据格式与前端预期不一致

**解决方案**:

确保后端使用标准Envelope格式：

```python
# 成功响应
from backend.core.response import success_response

return success_response(
    data=result,
    message="操作成功"
)

# 错误响应
from backend.core.response import error_response

return error_response(
    code="ERR-001",
    message="操作失败",
    status_code=400
)
```

前端统一处理响应：

```typescript
const response = await apiGet('/api/v1/projects')

if (response.data) {
  // 处理成功响应
  console.log(response.data)
} else if (response.error) {
  // 处理错误响应
  console.error(response.error.code, response.error.message)
}
```

### 6.6 调试技巧

#### 后端调试

1. 启用调试模式:
```bash
# backend/.env
DEBUG=true
LOG_LEVEL=DEBUG
```

2. 查看日志:
```bash
# 查看FastAPI日志
tail -f logs/app.log
```

3. 使用FastAPI自动文档:
```
http://localhost:8000/docs
```

#### 前端调试

1. 使用浏览器开发工具
   - Network标签: 查看请求/响应
   - Console标签: 查看错误日志
   - Application标签: 查看localStorage

2. 添加日志:
```typescript
console.log('API Request:', endpoint, options)
console.log('API Response:', response)
```

3. 使用React DevTools查看组件状态

---

## 附录: 标准响应格式

### 成功响应

```typescript
{
  success: true,
  data: T,              // 实际数据
  message: string,      // 成功消息
  code: null,           // 成功时为null
  meta?: {              // 可选元数据
    pagination?: {
      page: number,
      page_size: number,
      total: number,
      total_pages: number
    }
  }
}
```

### 错误响应

```typescript
{
  success: false,
  data: null,
  message: string,      // 错误消息
  code: string,         // 错误码 (如 "AUTH-001")
  meta: null
}
```

---

**文档维护者**: AI Development Team
**相关文档**:
- [API_SOT.md](../2.sot/API_SOT.md) - API规范
- [QUICK_START.md](./QUICK_START.md) - 快速启动指南
- [API_INTEGRATION_CHECKLIST.md](./API_INTEGRATION_CHECKLIST.md) - API对接清单
