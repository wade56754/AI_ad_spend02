# API设计规范 - 前后端协调开发指南

## 🎯 API设计原则

### 1. 统一响应格式
所有API返回必须遵循统一格式：

#### 成功响应
```typescript
{
  "success": true,
  "data": {
    // 实际数据
  },
  "message": "操作成功",
  "code": "SUCCESS",
  "request_id": "uuid-string",
  "timestamp": "2025-01-13T10:30:00Z"
}
```

#### 错误响应
```typescript
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": {}
  },
  "request_id": "uuid-string",
  "timestamp": "2025-01-13T10:30:00Z"
}
```

### 2. HTTP状态码规范
- `200 OK` - 成功获取数据
- `201 Created` - 成功创建资源
- `204 No Content` - 成功删除资源
- `400 Bad Request` - 请求参数错误
- `401 Unauthorized` - 未认证
- `403 Forbidden` - 权限不足
- `404 Not Found` - 资源不存在
- `500 Internal Server Error` - 服务器内部错误

### 3. 分页响应格式
```typescript
interface PaginatedResponse<T> {
  success: boolean;
  data: {
    items: T[];
    pagination: {
      current_page: number;
      page_size: number;
      total_items: number;
      total_pages: number;
      has_next: boolean;
      has_prev: boolean;
    };
  };
  message: string;
  code: string;
  request_id: string;
  timestamp: string;
}
```

## 📋 核心API接口设计

### 1. 项目管理API
```python
# 项目列表 (GET)
GET /api/v1/projects?page=1&page_size=20&status=active&priority=high&search=关键词

# 创建项目 (POST)
POST /api/v1/projects
{
  "name": "项目名称",
  "client_id": 1,
  "description": "项目描述",
  "budget": 50000,
  "start_date": "2025-01-01",
  "end_date": "2025-03-31",
  "priority": "high"
}

# 项目详情 (GET)
GET /api/v1/projects/{project_id}

# 更新项目 (PUT)
PUT /api/v1/projects/{project_id}
{
  "name": "更新的项目名称",
  "budget": 60000
}

# 删除项目 (DELETE)
DELETE /api/v1/projects/{project_id}
```

### 2. 广告账户API
```python
# 账户列表 (GET)
GET /api/v1/ad-accounts?page=1&page_size=20&platform=facebook&status=active

# 创建账户 (POST)
POST /api/v1/ad-accounts
{
  "account_name": "账户名称",
  "platform": "facebook",
  "account_id": "act_1234567890",
  "spending_limit": 10000,
  "assigned_user_id": 1
}

# 账户详情 (GET)
GET /api/v1/ad-accounts/{account_id}

# 批量操作 (POST)
POST /api/v1/ad-accounts/batch
{
  "account_ids": [1, 2, 3],
  "operation": "change_status",
  "status": "paused"
}
```

### 3. 日报管理API
```python
# 日报列表 (GET)
GET /api/v1/daily-reports?page=1&page_size=20&account_id=1&date_from=2025-01-01

# 提交日报 (POST)
POST /api/v1/daily-reports
{
  "account_id": 1,
  "report_date": "2025-01-13",
  "impressions": 10000,
  "clicks": 500,
  "spend": 250.50,
  "conversions": 25,
  "new_follows": 100
}

# 审核日报 (POST)
POST /api/v1/daily-reports/{report_id}/review
{
  "status": "approved",
  "comment": "审核通过"
}
```

### 4. 财务对账API
```python
# 对账批次列表 (GET)
GET /api/v1/reconciliation/batches?page=1&page_size=20

# 创建对账批次 (POST)
POST /api/v1/reconciliation/batches
{
  "batch_name": "2025年1月对账",
  "period_start": "2025-01-01",
  "period_end": "2025-01-31",
  "platform_spend_source": "api"
}

# 上传平台账单 (POST)
POST /api/v1/reconciliation/batches/{batch_id}/upload-bill
Content-Type: multipart/form-data
{
  "file": <binary_data>,
  "platform": "facebook"
}
```

### 5. 用户和权限API
```python
# 用户列表 (GET)
GET /api/v1/users?page=1&page_size=20&role=media_buyer

# 用户详情 (GET)
GET /api/v1/users/{user_id}

# 用户登录 (POST)
POST /api/v1/auth/login
{
  "username": "username",
  "password": "password"
}

# 获取用户信息 (GET)
GET /api/v1/auth/me
```

## 🔧 数据模型设计规范

### 1. 统一的命名规范
- 表名：使用复数形式 (`projects`, `users`, `accounts`)
- 字段名：使用下划线分隔 (`created_at`, `updated_at`)
- 时间字段：统一使用UTC时间
- ID字段：统一使用整数类型

### 2. 核心数据结构
```typescript
// 项目数据结构
interface Project {
  id: number;
  name: string;
  client_id: number;
  client_name?: string;
  description: string;
  currency: string;
  budget: number;
  current_spend: number;
  status: 'planning' | 'active' | 'paused' | 'completed' | 'archived';
  priority: 'low' | 'medium' | 'high';
  start_date: string; // ISO格式
  end_date: string;   // ISO格式
  progress: number;    // 0-100
  team_lead_id?: number;
  created_at: string;
  updated_at: string;
}

// 广告账户数据结构
interface AdAccount {
  id: number;
  account_name: string;
  platform: 'facebook' | 'tiktok' | 'google' | 'twitter';
  account_id: string;
  status: 'active' | 'paused' | 'banned' | 'pending';
  account_type: 'personal' | 'business';
  currency: string;
  timezone: string;
  spending_limit: number;
  current_spend: number;
  balance: number;
  assigned_user_id?: number;
  created_at: string;
  updated_at: string;
}
```

### 3. 关联关系设计
```python
# 项目与广告账户的关联
class ProjectAccount(BaseModel):
    project_id = ForeignKey('projects.id')
    ad_account_id = ForeignKey('ad_accounts.id')
    is_active = True
    assigned_at = datetime.utcnow()
    assigned_by = ForeignKey('users.id')

# 项目团队成员
class ProjectMember(Base):
    project_id = ForeignKey('projects.id')
    user_id = ForeignKey('users.id')
    role = 'lead' | 'member' | 'analyst' | 'designer'
    joined_at = datetime.utcnow()
    left_at = None
```

## 🚀 接口实现优先级

### Phase 1: 核心API (优先级：P0)
1. 用户认证 (`/api/v1/auth/*`)
2. 用户管理 (`/api/v1/users/*`)
3. 项目管理 (`/api/v1/projects/*`)
4. 广告账户 (`/api/v1/ad-accounts/*`)

### Phase 2: 业务API (优先级：P0)
1. 日报管理 (`/api/v1/daily-reports/*`)
2. 财务对账 (`/api/v1/reconciliation/*`)
3. 充值管理 (`/api/v1/topup/*`)

### Phase 3: 增强API (优先级：P1)
1. 统计报表 (`/api/v1/reports/*`)
2. 系统配置 (`/api/v1/settings/*`)
3. 审计日志 (`/api/v1/audit-logs/*`)

## 📝 API文档生成

### 1. 自动生成OpenAPI规范
```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI()

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    return get_openapi(
        title="AI广告代投系统 API",
        version="1.0.0",
        description="智能广告投放管理系统的RESTful API接口",
        routes=app.routes,
    )

app.openapi_schema = custom_openapi()
```

### 2. Swagger UI集成
```python
from fastapi import FastAPI

app = FastAPI()

# 自动生成API文档
# 访问 http://localhost:8000/docs 查看
```

## 🔄 实时数据同步

### 1. WebSocket实时推送
```python
from fastapi import WebSocket, WebSocketDisconnect
import json

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            # 接收前端消息
            data = await websocket.receive_text()
            message = json.loads(data)

            # 处理实时数据更新
            if message['type'] == 'subscribe_project':
                # 订阅项目更新
                await handle_project_subscription(websocket, message['project_id'])

            elif message['type'] == 'subscribe_metrics':
                # 订阅实时指标
                await handle_metrics_subscription(websocket)

    except WebSocketDisconnect:
        pass
```

### 2. Server-Sent Events (SSE)
```python
from fastapi import Response
from fastapi.responses import StreamingResponse

@app.get("/api/v1/events/metrics")
async def metrics_events():
    async def event_generator():
        while True:
            # 获取最新指标数据
            metrics = await get_latest_metrics()

            yield f"data: {json.dumps(metrics)}\n\n"
            await asyncio.sleep(5)  # 每5秒推送一次

    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        },
    )
```

## 🧪 前端API调用最佳实践

### 1. 统一的API客户端
```typescript
// lib/api-client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    if (error.response?.status === 401) {
      // 处理认证失败
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### 2. React Query集成
```typescript
// lib/api-hooks.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './api-client';

// 自定义hook模板
export function createApiHook<T = any>(endpoint: string) {
  return useQuery<T>({
    queryKey: [endpoint],
    queryFn: async () => {
      const response = await apiClient.get(endpoint);
      return response.data;
    },
  });
}

// 创建CRUD hook
export function createApiMutation<T = any>(endpoint: string) {
  return useMutation<T, Error>({
    mutationFn: async (data: T) => {
      const response = await apiClient.post(endpoint, data);
      return response.data;
    },
  });
}

// 使用示例
export const useProjects = () => createApiHook<Project[]>('/api/v1/projects');
export const useCreateProject = () => createApiMutation<Project>('/api/v1/projects');
```

### 3. 类型安全
```typescript
// types/api.ts
export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message: string;
  code: string;
  request_id: string;
  timestamp: string;
}

export interface PaginatedApiResponse<T> extends ApiResponse<T[]> {
  data: {
    items: T[];
    pagination: {
      current_page: number;
      page_size: number;
      total_items: number;
      total_pages: number;
      has_next: boolean;
      has_prev: boolean;
    };
  };
}

// 使用示例
interface Project {
  id: number;
  name: string;
  client_id: number;
}

const response: ApiResponse<Project[]> = await apiClient.get('/api/v1/projects');
```

这个设计规范确保了前后端开发的协调性和一致性，为并行开发提供了坚实的基础。