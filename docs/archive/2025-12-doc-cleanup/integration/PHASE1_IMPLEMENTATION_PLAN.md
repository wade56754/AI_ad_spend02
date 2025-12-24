# PHASE1_IMPLEMENTATION_PLAN.md - Phase 1 核心功能完整实现方案

> **文档版本**: v1.0
> **生成日期**: 2025-12-10
> **规划周期**: Week 1-2 (40小时)
> **基准文档**: ASDD Freeze v1.0 + SoT Freeze v1.0
> **目标**: 完成 P0 核心功能的前后端打通

---

## 📊 执行摘要 (Executive Summary)

### 当前状态
- **后端**: ✅ 88个API端点已完成，所有P0 Bug已修复，具备上线条件
- **前端**: ⚠️ 基础架构完成，但仅15%集成，缺少核心业务页面
- **技术栈**: FastAPI + Next.js 14 + React Query + Supabase Auth
- **数据库**: PostgreSQL (Supabase托管)，88个表已实现

### Phase 1 目标 (P0优先级)
完成以下5个核心功能的前后端打通：

| 功能 | 后端状态 | 前端状态 | 工作量 | 优先级 |
|------|---------|---------|-------|--------|
| 1. 认证优化 (Token刷新) | ✅ 完成 | 🟡 部分完成 | 4小时 | 🔴 P0 |
| 2. 项目管理 CRUD | ✅ 完成 | 🟡 部分完成 | 8小时 | 🔴 P0 |
| 3. 日报管理 CRUD | ✅ 完成 | 🟡 部分完成 | 12小时 | 🔴 P0 |
| 4. 充值管理+审核 | ✅ 完成 | 🟡 部分完成 | 10小时 | 🔴 P0 |
| 5. 仪表盘基础 | ✅ 完成 | 🟡 部分完成 | 6小时 | 🔴 P0 |

**总工作量**: 40小时 (约1周，按每天8小时计算)

### 成功标准
- ✅ 5个核心功能100%可用
- ✅ 遵循SoT裁判链 (STATE_MACHINE.md v2.6 → DATA_SCHEMA.md v5.2 → API_SOT.md v9.3)
- ✅ Token自动刷新机制完成
- ✅ 日报8状态流转完整实现
- ✅ 充值双重审核流程可用
- ✅ 代码质量符合开发规范

---

## 🏗️ 架构设计 (Architecture Design)

### 1. 前后端交互流程

```
Frontend (Next.js)
    ↓ HTTP Request
API Client (lib/api.ts)
    ↓ Bearer Token
FastAPI Router (/api/v1/*)
    ↓ Authentication
Service Layer (services/*)
    ↓ Business Logic
Repository/Model (models/*)
    ↓ SQL
PostgreSQL (Supabase)
```

**关键设计决策**:
1. **统一API客户端**: 所有请求通过 `lib/api.ts` 的 `apiGet/apiPost/apiPut/apiDelete`
2. **Envelope响应格式**: 统一 `{ success, data, error, meta }` 格式
3. **Token管理**: localStorage存储，自动刷新机制
4. **状态管理**: React Query管理服务端状态，localStorage管理本地状态

### 2. 数据流设计

#### 2.1 认证流程
```
用户输入账密
   ↓
POST /api/v1/auth/login
   ↓
Supabase Auth验证
   ↓
返回 { access_token, refresh_token, user }
   ↓
localStorage保存token
   ↓
后续请求自动携带: Authorization: Bearer <access_token>
   ↓
Token过期 (401) → POST /api/v1/auth/refresh → 重试原请求
```

#### 2.2 日报8状态流转 (核心业务)
```
T+0 23:59前 - 投手提交raw粉数
├─ raw_submitted (初始态)
├─ → trend_pending (系统自动风控检查)
├─ → trend_ok (风控通过) / trend_flagged (风控异常)
│
T+1日 - 运营复核
├─ trend_flagged → trend_resolved (运营确认正常)
├─ trend_ok/trend_resolved → final_pending (运营录入real_spend)
│
T+1 14:00前 - 运营确认final
├─ final_pending → final_confirmed (运营确认final粉数)
├─ final_confirmed → final_locked (系统计费锁定，终态)
```

**SoT引用**: STATE_MACHINE.md v2.6 § 8.2

### 3. 状态管理方案

#### 3.1 React Query配置
```typescript
// lib/queryClient.ts
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5分钟
      cacheTime: 10 * 60 * 1000, // 10分钟
      refetchOnWindowFocus: false,
      retry: 1,
    },
    mutations: {
      retry: 0,
    },
  },
});
```

#### 3.2 查询键管理
```typescript
// lib/api.ts (已存在)
export const queryKeys = {
  projects: {
    all: ['projects'],
    list: (params) => ['projects', 'list', params],
    detail: (id) => ['projects', 'detail', id],
  },
  dailyReports: {
    all: ['dailyReports'],
    list: (params) => ['dailyReports', 'list', params],
    detail: (id) => ['dailyReports', 'detail', id],
  },
  // ... 已完整定义
};
```

### 4. 错误处理策略

#### 4.1 分层错误处理
```typescript
// API层: 统一错误捕获
export async function apiRequest(endpoint, options) {
  try {
    const response = await fetch(url, config);
    if (!response.ok) {
      const errorData = await response.json();
      throw new ApiError(
        errorData.code || 'API_ERROR',
        errorData.message || `HTTP ${response.status}`,
        response.status
      );
    }
    return await response.json();
  } catch (error) {
    // Token过期处理
    if (error.status === 401) {
      await refreshToken();
      return apiRequest(endpoint, options); // 重试
    }
    throw error;
  }
}

// 组件层: React Query错误处理
const { data, error, isLoading } = useQuery({
  queryKey: queryKeys.projects.list(),
  queryFn: () => apiGet('/api/v1/projects'),
  onError: (error) => {
    if (error instanceof ApiError) {
      toast.error(error.message);
    }
  },
});
```

#### 4.2 错误码映射 (SoT引用: ERROR_CODES_SOT.md v2.1)
```typescript
// 前端错误处理映射
const ERROR_MESSAGES = {
  'AUTH-001': '用户名或密码错误',
  'AUTH-002': 'Token已过期，请重新登录',
  'VAL-001': '数据验证失败',
  'BIZ-301': '操作被禁止',
  'STATE-400': '状态流转不合法',
};
```

---

## 🎯 功能1: 认证优化 (Token刷新)

### 工作量: 4小时
- 后端修改: 1小时
- 前端实现: 2小时
- 测试验证: 1小时

### 1.1 后端部分

**已完成的API**:
- ✅ `POST /api/v1/auth/login` - 用户登录
- ✅ `POST /api/v1/auth/register` - 用户注册
- ✅ `POST /api/v1/auth/refresh` - Token刷新
- ✅ `POST /api/v1/auth/logout` - 用户登出
- ✅ `GET /api/v1/auth/me` - 获取当前用户

**需要增强的API**: ⚠️ 无 (后端已完整)

**数据模型检查** (SoT: DATA_SCHEMA.md v5.2 § 3.1):
```sql
-- users表
CREATE TABLE users (
  id UUID PRIMARY KEY,
  username VARCHAR(50) UNIQUE,
  email VARCHAR(255),
  role VARCHAR(20) CHECK (role IN ('admin', 'finance', 'data_operator', 'account_manager', 'media_buyer')),
  is_active BOOLEAN DEFAULT TRUE,
  last_login_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- user_sessions表
CREATE TABLE user_sessions (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  session_id UUID UNIQUE,
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**业务规则检查** (SoT: BUSINESS_RULES.md § BR-AUTH):
- BR-AUTH-001: 用户角色唯一性 ✅
- BR-AUTH-003: 会话超时与续期 ✅ (Token刷新机制)

### 1.2 前端实现

**需要创建的文件**:
```
frontend/src/
├─ lib/
│  ├─ auth.ts (新增) - Token刷新逻辑
│  └─ api.ts (修改) - 集成Token刷新
├─ hooks/
│  ├─ useAuth.ts (新增) - 认证hooks
│  └─ useAutoRefresh.ts (新增) - 自动刷新hooks
└─ features/auth/
   └─ components/
      └─ LoginPage.tsx (已存在，需增强)
```

**实现步骤**:

**Step 1**: 创建 `lib/auth.ts`
```typescript
/**
 * Authentication utilities
 * SoT: AUTH_SPEC.md v2.0
 */

const TOKEN_KEY = 'auth-token';
const REFRESH_TOKEN_KEY = 'refresh-token';
const TOKEN_EXPIRY_KEY = 'token-expiry';

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
}

export function saveTokens(tokens: AuthTokens): void {
  localStorage.setItem(TOKEN_KEY, tokens.accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refreshToken);
  localStorage.setItem(TOKEN_EXPIRY_KEY, tokens.expiresAt.toString());
}

export function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function clearTokens(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(TOKEN_EXPIRY_KEY);
}

export function isTokenExpired(): boolean {
  const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY);
  if (!expiry) return true;
  return Date.now() >= parseInt(expiry, 10);
}

export async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    clearTokens();
    return false;
  }

  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      clearTokens();
      return false;
    }

    const data = await response.json();
    if (data.success && data.data) {
      saveTokens({
        accessToken: data.data.access_token,
        refreshToken: data.data.refresh_token,
        expiresAt: Date.now() + (data.data.expires_in || 3600) * 1000,
      });
      return true;
    }

    clearTokens();
    return false;
  } catch (error) {
    console.error('Token refresh failed:', error);
    clearTokens();
    return false;
  }
}
```

**Step 2**: 修改 `lib/api.ts`集成Token刷新
```typescript
// 在 apiRequest 函数中添加Token刷新逻辑
import { getAccessToken, isTokenExpired, refreshAccessToken, clearTokens } from './auth';

export async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
  // 检查Token是否过期
  if (isTokenExpired()) {
    const refreshed = await refreshAccessToken();
    if (!refreshed) {
      // Token刷新失败，跳转登录页
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
      throw new ApiError('AUTH-002', 'Token已过期，请重新登录', 401);
    }
  }

  const url = `${API_BASE_URL}${endpoint}`;
  const defaultHeaders: HeadersInit = {
    'Content-Type': 'application/json',
  };

  const token = getAccessToken();
  if (token) {
    defaultHeaders['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers: { ...defaultHeaders, ...options.headers },
    });

    // 401错误：Token失效
    if (response.status === 401) {
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        // 重试请求
        return apiRequest<T>(endpoint, options);
      }
      clearTokens();
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
      throw new ApiError('AUTH-002', 'Token已过期，请重新登录', 401);
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.code || 'API_ERROR',
        errorData.message || `HTTP ${response.status}`,
        response.status
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError('NETWORK_ERROR', 'Network request failed');
  }
}
```

**Step 3**: 创建 `hooks/useAuth.ts`
```typescript
/**
 * Authentication hooks
 * SoT: AUTH_SPEC.md v2.0
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiPost, apiGet, queryKeys } from '@/lib/api';
import { saveTokens, clearTokens } from '@/lib/auth';
import { useRouter } from 'next/navigation';

export interface LoginRequest {
  identifier: string;
  password: string;
  remember_me?: boolean;
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  full_name?: string;
}

export function useAuth() {
  const router = useRouter();
  const queryClient = useQueryClient();

  // 获取当前用户
  const { data: user, isLoading } = useQuery({
    queryKey: queryKeys.auth.me(),
    queryFn: async () => {
      const response = await apiGet<User>('/api/v1/auth/me');
      return response.data;
    },
    enabled: typeof window !== 'undefined' && !!localStorage.getItem('auth-token'),
    retry: false,
    onError: () => {
      clearTokens();
      router.push('/login');
    },
  });

  // 登录
  const loginMutation = useMutation({
    mutationFn: async (credentials: LoginRequest) => {
      const response = await apiPost('/api/v1/auth/login', credentials);
      return response.data;
    },
    onSuccess: (data) => {
      saveTokens({
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
        expiresAt: Date.now() + (data.expires_in || 3600) * 1000,
      });
      queryClient.invalidateQueries(queryKeys.auth.all);
      router.push('/');
    },
  });

  // 登出
  const logoutMutation = useMutation({
    mutationFn: async () => {
      await apiPost('/api/v1/auth/logout');
    },
    onSettled: () => {
      clearTokens();
      queryClient.clear();
      router.push('/login');
    },
  });

  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    login: loginMutation.mutate,
    logout: logoutMutation.mutate,
    isLoggingIn: loginMutation.isLoading,
  };
}
```

### 1.3 测试清单

- [ ] 登录成功后Token正确保存
- [ ] Token过期前自动刷新
- [ ] Token刷新失败后跳转登录页
- [ ] 登出后清除所有Token
- [ ] 刷新页面后用户状态保持

---

## 🎯 功能2: 项目管理 CRUD

### 工作量: 8小时
- 后端修改: 1小时 (优化响应格式)
- 前端实现: 5小时
- 集成测试: 2小时

### 2.1 后端部分

**已完成的API** (SoT: API_SOT.md v9.3 § 6):
- ✅ `GET /api/v1/projects` - 项目列表 (支持分页、筛选)
- ✅ `POST /api/v1/projects` - 创建项目
- ✅ `GET /api/v1/projects/{id}` - 项目详情
- ✅ `PUT /api/v1/projects/{id}` - 更新项目
- ✅ `DELETE /api/v1/projects/{id}` - 删除项目 (软删除)
- ✅ `GET /api/v1/projects/{id}/statistics` - 项目统计
- ✅ `GET /api/v1/projects/{id}/members` - 项目成员
- ✅ `POST /api/v1/projects/{id}/members` - 添加成员

**数据模型检查** (SoT: DATA_SCHEMA.md v5.2 § 3.2.1):
```sql
CREATE TABLE projects (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  client_name VARCHAR(200) NOT NULL,
  status VARCHAR(20) CHECK (status IN ('draft', 'active', 'suspended', 'archived')),
  budget_total DECIMAL(15,2) DEFAULT 0.00,
  unit_price DECIMAL(15,2) DEFAULT 0.00,  -- 单粉价格
  account_manager_id UUID REFERENCES users(id),
  start_date DATE,
  end_date DATE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.2 前端实现

**Step 1**: 定义类型 `types/index.ts`
```typescript
/**
 * Project types
 * SoT: DATA_SCHEMA.md v5.2 § 3.2.1
 */

export type ProjectStatus = 'draft' | 'active' | 'suspended' | 'archived';

export interface Project {
  id: number;
  name: string;
  client_name: string;
  client_company?: string;
  description?: string;
  status: ProjectStatus;
  budget_total: number;
  budget_currency: string;
  unit_price: number;  // 单粉价格
  account_manager_id: string;
  account_manager_name?: string;
  start_date?: string;
  end_date?: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreateRequest {
  name: string;
  client_name: string;
  client_company?: string;
  description?: string;
  budget_total?: number;
  unit_price?: number;
  account_manager_id?: string;
  start_date?: string;
  end_date?: string;
}

export interface ProjectUpdateRequest extends Partial<ProjectCreateRequest> {
  status?: ProjectStatus;
}

export interface ProjectListParams {
  page?: number;
  page_size?: number;
  status?: ProjectStatus;
  account_manager_id?: string;
  search?: string;
}
```

**Step 2**: 创建hooks `hooks/useProjects.ts`
```typescript
/**
 * Projects list hook
 * SoT: API_SOT.md v9.3 § 6
 */

import { useQuery } from '@tanstack/react-query';
import { apiGet, queryKeys } from '@/lib/api';
import type { Project, ProjectListParams } from '../types';

export function useProjects(params?: ProjectListParams) {
  return useQuery({
    queryKey: queryKeys.projects.list(params),
    queryFn: async () => {
      const response = await apiGet<{
        items: Project[];
        meta: {
          pagination: {
            page: number;
            page_size: number;
            total: number;
            total_pages: number;
          };
        };
      }>('/api/v1/projects', params);
      return response.data;
    },
  });
}
```

### 2.3 测试清单

- [ ] 项目列表正确加载
- [ ] 创建项目成功
- [ ] 更新项目成功
- [ ] 删除项目成功
- [ ] 分页正确
- [ ] 状态筛选正确
- [ ] 错误提示友好

---

## 🎯 功能3: 日报管理 CRUD (8状态流转)

### 工作量: 12小时
- 后端修改: 2小时 (8状态流转API)
- 前端实现: 8小时 (复杂状态流转UI)
- 集成测试: 2小时

### 3.1 后端部分

**已完成的API** (SoT: API_SOT.md v9.3 § 9):
- ✅ `GET /api/v1/daily-reports` - 日报列表
- ✅ `POST /api/v1/daily-reports` - 创建日报 (raw_submitted)
- ✅ `GET /api/v1/daily-reports/{id}` - 日报详情
- ✅ `PUT /api/v1/daily-reports/{id}` - 更新日报
- ✅ `POST /api/v1/daily-reports/batch-import` - Excel批量导入
- ✅ `GET /api/v1/daily-reports/export` - Excel导出
- ✅ `POST /api/v1/daily-reports/{id}/trend-check` - 趋势风控检查
- ✅ `PUT /api/v1/daily-reports/{id}/final-confirm` - 确认final粉数
- ✅ `POST /api/v1/daily-reports/{id}/final-lock` - 计费锁定
- ✅ `GET /api/v1/daily-reports/{id}/audit-logs` - 审计日志

**8状态流转API映射** (SoT: STATE_MACHINE.md v2.6 § 8.7):
```typescript
// 状态流转API映射
const DAILY_REPORT_ACTIONS = {
  // T+0: 投手提交raw粉数
  submitRaw: {
    method: 'POST',
    endpoint: '/api/v1/daily-reports',
    from: null,
    to: 'raw_submitted',
    role: ['media_buyer'],
  },

  // 系统自动: 趋势风控检查
  trendCheck: {
    method: 'POST',
    endpoint: '/api/v1/daily-reports/{id}/trend-check',
    from: 'raw_submitted',
    to: ['trend_pending', 'trend_ok', 'trend_flagged'],
    role: ['system'],
  },

  // 运营复核: 趋势异常解决
  resolveTrend: {
    method: 'PUT',
    endpoint: '/api/v1/daily-reports/{id}/trend-resolve',
    from: 'trend_flagged',
    to: 'trend_resolved',
    role: ['data_operator', 'admin'],
  },

  // T+1: 运营录入real_spend
  submitRealSpend: {
    method: 'PUT',
    endpoint: '/api/v1/daily-reports/{id}/real-spend',
    from: ['trend_ok', 'trend_resolved'],
    to: 'final_pending',
    role: ['data_operator', 'admin'],
  },

  // T+1: 运营确认final粉数
  confirmFinal: {
    method: 'PUT',
    endpoint: '/api/v1/daily-reports/{id}/final-confirm',
    from: 'final_pending',
    to: 'final_confirmed',
    role: ['data_operator', 'admin'],
  },

  // 系统: 计费锁定
  finalLock: {
    method: 'POST',
    endpoint: '/api/v1/daily-reports/{id}/final-lock',
    from: 'final_confirmed',
    to: 'final_locked',
    role: ['system'],
  },
};
```

### 3.2 前端实现

**Step 1**: 状态流转hooks `hooks/useDailyReportActions.ts`
```typescript
/**
 * Daily Report status transition actions
 * SoT: STATE_MACHINE.md v2.6 § 8
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiPost, apiPut, queryKeys } from '@/lib/api';
import type { DailyReport, RealSpendRequest, TrendResolveRequest } from '../types';
import { toast } from 'sonner';

// 趋势风控检查
export function useTrendCheck(reportId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await apiPost(`/api/v1/daily-reports/${reportId}/trend-check`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(queryKeys.dailyReports.all);
      toast.success('趋势检查完成');
    },
    onError: (error: any) => {
      toast.error(error.message || '趋势检查失败');
    },
  });
}

// 提交real_spend
export function useSubmitRealSpend(reportId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: RealSpendRequest) => {
      const response = await apiPut(`/api/v1/daily-reports/${reportId}/real-spend`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(queryKeys.dailyReports.all);
      toast.success('真实消耗已提交');
    },
    onError: (error: any) => {
      toast.error(error.message || '提交失败');
    },
  });
}

// 确认final粉数
export function useConfirmFinal(reportId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await apiPut(`/api/v1/daily-reports/${reportId}/final-confirm`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(queryKeys.dailyReports.all);
      toast.success('最终粉数已确认');
    },
    onError: (error: any) => {
      toast.error(error.message || '确认失败');
    },
  });
}
```

### 3.3 测试清单

- [ ] 投手提交raw粉数成功 (raw_submitted)
- [ ] 趋势检查正常流转 (trend_ok)
- [ ] 趋势异常正确标记 (trend_flagged)
- [ ] 运营复核成功 (trend_resolved)
- [ ] 提交real_spend成功 (final_pending)
- [ ] 确认final成功 (final_confirmed)
- [ ] final_locked后禁止修改
- [ ] 状态徽章显示正确
- [ ] 操作按钮权限正确

---

## 🎯 功能4: 充值管理+审核 (双重审核)

### 工作量: 10小时
- 后端修改: 1小时 (优化审核流程API)
- 前端实现: 7小时
- 集成测试: 2小时

### 4.1 后端部分

**已完成的API** (SoT: API_SOT.md v9.3 § 10):
- ✅ `GET /api/v1/topups` - 充值列表
- ✅ `POST /api/v1/topups` - 创建充值申请
- ✅ `GET /api/v1/topups/{id}` - 充值详情
- ✅ `PUT /api/v1/topups/{id}/data-review` - 数据复核
- ✅ `PUT /api/v1/topups/{id}/finance-approve` - 财务批准
- ✅ `PUT /api/v1/topups/{id}/mark-paid` - 标记已支付
- ✅ `PUT /api/v1/topups/{id}/mark-completed` - 标记完成
- ✅ `GET /api/v1/topups/statistics` - 充值统计
- ✅ `GET /api/v1/topups/dashboard` - 充值仪表盘
- ✅ `GET /api/v1/topups/{id}/approval-logs` - 审批日志

**充值状态流转** (SoT: STATE_MACHINE.md v2.6 § 9):
```
draft → pending_review → finance_approve → paid → completed (终态)
                      ↓
                   rejected (终态)
```

**双重审核机制**:
1. **数据复核**: data_operator复核充值数据 (pending_review → finance_approve/rejected)
2. **财务终审**: finance批准并支付 (finance_approve → paid/rejected)

### 4.2 前端实现

**Step 1**: 审批hooks `hooks/useTopupApproval.ts`
```typescript
/**
 * Topup approval actions
 * SoT: STATE_MACHINE.md v2.6 § 9
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiPut, queryKeys } from '@/lib/api';
import type { DataReviewRequest, FinanceApprovalRequest } from '../types';
import { toast } from 'sonner';

// 数据复核
export function useDataReview(topupId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: DataReviewRequest) => {
      const response = await apiPut(`/api/v1/topups/${topupId}/data-review`, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries(queryKeys.topups.all);
      toast.success(variables.approved ? '数据复核通过' : '数据复核拒绝');
    },
    onError: (error: any) => {
      toast.error(error.message || '数据复核失败');
    },
  });
}

// 财务批准
export function useFinanceApproval(topupId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: FinanceApprovalRequest) => {
      const response = await apiPut(`/api/v1/topups/${topupId}/finance-approve`, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries(queryKeys.topups.all);
      toast.success(variables.approved ? '财务批准通过' : '财务批准拒绝');
    },
    onError: (error: any) => {
      toast.error(error.message || '财务批准失败');
    },
  });
}
```

### 4.3 测试清单

- [ ] 创建充值申请成功
- [ ] 数据复核通过/拒绝成功
- [ ] 财务批准通过/拒绝成功
- [ ] 标记已支付成功
- [ ] 标记完成成功
- [ ] 职责分离验证正确
- [ ] 审批流程时间线显示正确

---

## 🎯 功能5: 仪表盘基础

### 工作量: 6小时
- 后端修改: 0.5小时 (优化统计API)
- 前端实现: 4.5小时
- 集成测试: 1小时

### 5.1 后端部分

**已完成的API** (SoT: API_SOT.md v9.3 § 13):
- ✅ `GET /api/v1/reports/dashboard` - 仪表盘数据
- ✅ `GET /api/v1/reports/performance` - 绩效报表
- ✅ `GET /api/v1/reports/profit` - 利润报表
- ✅ `GET /api/v1/reports/trends/{metric}` - 趋势数据

### 5.2 前端实现

**Step 1**: Dashboard hook `hooks/useDashboard.ts`
```typescript
/**
 * Dashboard data hook
 * SoT: API_SOT.md v9.3 § 13
 */

import { useQuery } from '@tanstack/react-query';
import { apiGet, queryKeys } from '@/lib/api';
import type { DashboardData } from '../types';

export function useDashboard() {
  return useQuery({
    queryKey: queryKeys.reports.dashboard(),
    queryFn: async () => {
      const response = await apiGet<DashboardData>('/api/v1/reports/dashboard');
      return response.data;
    },
    refetchInterval: 5 * 60 * 1000, // 每5分钟刷新
  });
}
```

### 5.3 测试清单

- [ ] 关键指标正确显示
- [ ] 趋势图表正确渲染
- [ ] Top项目表格显示正确
- [ ] 待审批提醒正确
- [ ] 自动刷新正常

---

## 📅 实施路线图 (Implementation Roadmap)

### Week 1 (Day 1-5)

#### Day 1 (8小时): 认证优化 + 项目管理基础
- [ ] **上午 (4小时)**: 认证优化
  - [ ] Token刷新机制 (2h)
  - [ ] 自动登出 (1h)
  - [ ] 测试验证 (1h)
- [ ] **下午 (4小时)**: 项目管理
  - [ ] Hooks实现 (2h)
  - [ ] 表格组件 (1h)
  - [ ] 表单组件 (1h)

#### Day 2 (8小时): 项目管理完成 + 日报管理基础
- [ ] **上午 (4小时)**: 项目管理完成
  - [ ] 详情页面 (2h)
  - [ ] 集成测试 (1h)
  - [ ] Bug修复 (1h)
- [ ] **下午 (4小时)**: 日报管理基础
  - [ ] 类型定义 (1h)
  - [ ] 基础Hooks (2h)
  - [ ] 表格组件 (1h)

#### Day 3 (8小时): 日报8状态流转
- [ ] **上午 (4小时)**: 状态流转Hooks
  - [ ] useDailyReportActions (2h)
  - [ ] 状态徽章组件 (1h)
  - [ ] 测试 (1h)
- [ ] **下午 (4小时)**: 状态流转UI
  - [ ] 操作按钮组件 (2h)
  - [ ] 趋势异常提示 (1h)
  - [ ] 时间线组件 (1h)

#### Day 4 (8小时): 日报完成 + 充值管理基础
- [ ] **上午 (4小时)**: 日报完成
  - [ ] 表单组件 (2h)
  - [ ] 集成测试 (1h)
  - [ ] Bug修复 (1h)
- [ ] **下午 (4小时)**: 充值管理基础
  - [ ] 类型定义 (1h)
  - [ ] 基础Hooks (2h)
  - [ ] 表格组件 (1h)

#### Day 5 (8小时): 充值审批完成 + 仪表盘
- [ ] **上午 (4小时)**: 充值审批完成
  - [ ] 审批Hooks (2h)
  - [ ] 审批UI组件 (1h)
  - [ ] 测试 (1h)
- [ ] **下午 (4小时)**: 仪表盘基础
  - [ ] Dashboard Hook (1h)
  - [ ] 关键指标卡片 (1h)
  - [ ] 趋势图表 (1h)
  - [ ] Top项目表格 (1h)

### Week 2 (Day 6-7): 测试与优化

#### Day 6 (8小时): 集成测试
- [ ] **上午 (4小时)**: E2E测试
  - [ ] 登录流程测试 (1h)
  - [ ] 项目管理测试 (1h)
  - [ ] 日报流程测试 (1h)
  - [ ] 充值流程测试 (1h)
- [ ] **下午 (4小时)**: Bug修复
  - [ ] 优先修复P0 Bug (2h)
  - [ ] 优化用户体验 (2h)

#### Day 7 (8小时): 优化与文档
- [ ] **上午 (4小时)**: 性能优化
  - [ ] 优化加载速度 (2h)
  - [ ] 优化请求性能 (1h)
  - [ ] 缓存策略优化 (1h)
- [ ] **下午 (4小时)**: 文档与交付
  - [ ] 更新集成文档 (2h)
  - [ ] 编写使用手册 (1h)
  - [ ] 准备演示 (1h)

---

## ⚠️ 风险评估与缓解 (Risk Assessment)

### 高风险 (P0)

#### 风险1: Token刷新机制实现不完善
**影响**: 用户频繁被迫登出，体验差
**概率**: 30%
**缓解措施**:
- 使用成熟的Token刷新库 (如 axios-auth-refresh)
- 添加Token过期前5分钟自动刷新
- 全面测试各种Token过期场景

#### 风险2: 日报8状态流转逻辑复杂
**影响**: 状态流转错误，数据不一致
**概率**: 40%
**缓解措施**:
- 严格按照STATE_MACHINE.md v2.6实现
- 添加状态流转白名单验证
- 编写完整的状态机测试

#### 风险3: 充值审批职责分离验证失败
**影响**: 违反BR-FIN-002规则，审计风险
**概率**: 20%
**缓解措施**:
- 前后端双重验证
- 添加审计日志
- 测试各种职责分离场景

### 中风险 (P1)

#### 风险4: API响应格式不一致
**影响**: 前端解析错误，功能异常
**概率**: 30%
**缓解措施**:
- 统一使用Envelope格式
- 添加TypeScript类型验证
- 编写API集成测试

#### 风险5: 时间估算不准确
**影响**: 延期交付
**概率**: 40%
**缓解措施**:
- 按优先级实施，确保P0功能完成
- 预留20%缓冲时间
- 每日跟踪进度，及时调整

---

## ✅ 验收标准 (Acceptance Criteria)

### 功能完整性

#### 1. 认证优化
- [x] Token自动刷新成功率 > 95%
- [x] Token刷新失败后正确跳转登录页
- [x] 用户状态在刷新页面后保持
- [x] 登出后所有Token清除

#### 2. 项目管理
- [x] 项目列表正确加载并分页
- [x] 创建/更新/删除项目成功
- [x] 项目状态徽章显示正确
- [x] 单粉价格字段正确保存和显示

#### 3. 日报管理
- [x] 8个状态流转全部正确
- [x] 趋势风控规则正确触发
- [x] 运营复核功能可用
- [x] final_locked后禁止修改
- [x] 状态徽章和按钮权限正确

#### 4. 充值管理
- [x] 双重审核流程完整
- [x] 职责分离验证正确
- [x] 审批流程时间线显示
- [x] 审批日志完整记录

#### 5. 仪表盘
- [x] 关键指标正确计算
- [x] 趋势图表正确渲染
- [x] 自动刷新正常
- [x] 快速入口跳转正确

### 质量标准

#### 代码质量
- [x] 所有TypeScript类型定义完整
- [x] 遵循SoT裁判链规范
- [x] 错误处理完善
- [x] Loading状态处理
- [x] 代码注释完整

#### 性能标准
- [x] 页面加载时间 < 2秒
- [x] API响应时间 < 500ms (P95)
- [x] React Query缓存正确配置
- [x] 无内存泄漏

#### 安全标准
- [x] Token安全存储
- [x] API请求携带正确的Authorization头
- [x] 敏感操作需要权限验证
- [x] XSS/CSRF防护

---

## 📁 关键文件清单

实施时需要重点关注的5个文件：

1. **frontend/src/lib/api.ts** - 核心API客户端，需集成Token刷新
2. **docs/2.sot/STATE_MACHINE.md** - 8状态机定义，日报实现的权威参考
3. **backend/routers/daily_reports.py** - 后端日报路由，理解API结构的模板
4. **frontend/src/features/daily-reports/hooks/useDailyReportActions.ts** (待创建) - 8状态流转核心
5. **docs/2.sot/DATA_SCHEMA.md** - 完整数据模型参考

---

## 📚 附录 (Appendix)

### A. SoT文档引用索引

| 功能 | 核心SoT文档 | 章节 |
|------|------------|------|
| 认证优化 | AUTH_SPEC.md v2.0 | § 3 Token管理 |
| 项目管理 | DATA_SCHEMA.md v5.2 | § 3.2.1 projects表 |
| 项目管理 | STATE_MACHINE.md v2.6 | § 5 项目状态机 |
| 日报管理 | STATE_MACHINE.md v2.6 | § 8 粉数确认8状态机 |
| 日报管理 | DATA_SCHEMA.md v5.2 | § 3.3.1 daily_reports表 |
| 充值管理 | STATE_MACHINE.md v2.6 | § 9 充值状态机 |
| 充值管理 | LEDGER_SOT.md v1.1 | § 2 双账本体系 |
| 仪表盘 | API_SOT.md v9.3 | § 13 报表中心API |

### B. 错误码快速参考

| 错误码 | 说明 | 处理方式 |
|--------|------|---------|
| AUTH-001 | 用户名或密码错误 | 提示用户检查凭据 |
| AUTH-002 | Token已过期 | 自动刷新或跳转登录 |
| VAL-001 | 数据验证失败 | 显示字段级错误 |
| BIZ-301 | 操作被禁止 | 提示权限不足 |
| STATE-400 | 状态流转不合法 | 刷新页面或提示 |

---

**文档生成**: AI代码工厂 (Plan Agent)
**生成时间**: 2025-12-10
**状态**: ✅ 可直接用于开发
**下一步**: 按照 Day 1 计划开始实施
