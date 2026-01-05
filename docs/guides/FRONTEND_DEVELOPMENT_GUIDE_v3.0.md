# AI 广告代投系统 - 前端开发指南 v3.0

> **技术栈**: Next.js 16 + TanStack Query v5 + shadcn/ui + TypeScript
> **基准文档**: MASTER.md v4.9 + PRD v5.2 + STATE_MACHINE.md v2.9
> **后端状态**: ✅ 已完成 (57/57 任务)
> **文档版本**: v3.0 (AI 编程友好版 - 铁律前置 + Phase 边界明确)

---

## ⚠️ 第零章：开发铁律（生成任何代码前必读）

> **重要**: 本章内容为强制约束，违反将导致代码被拒绝

### 0.1 角色白名单（6 个，无 supervisor）

```typescript
// ✅ 合法角色 - 只能使用这 6 个
type Role = 'ceo' | 'project_owner' | 'finance' | 'pitcher' | 'account_manager' | 'admin';

// ❌ 已移除角色 - 禁止使用
// supervisor - 已合并到 project_owner
// data_operator - 从未存在
```

### 0.1.1 角色双层系统

> **来源**: STATE_MACHINE.md v2.9 §2.1

| 业务角色 (6个) | 技术层映射 | 说明 |
|---------------|-----------|------|
| ceo | admin | 系统最高权限 |
| project_owner | users.is_project_owner=true | 项目负责人 |
| finance | finance | 财务 |
| pitcher | media_buyer | 投手 |
| account_manager | account_manager | 户管 |
| admin | admin | 系统管理员 |

> **注意**: 技术层数据库 CHECK 约束使用 4 角色 (admin/finance/account_manager/media_buyer)
> 业务层通过 `is_project_owner` 属性扩展为 6 角色

### 0.2 日报状态（Phase 1 只用 3 个）

```typescript
// ✅ Phase 1 启用状态（当前使用）
type Phase1ReportStatus = 'raw_submitted' | 'trend_ok' | 'final_confirmed';

// Phase 1 状态流转：
// raw_submitted → trend_ok → final_confirmed

// ❌ Phase 2 状态（当前禁止使用）
// trend_pending, trend_flagged, trend_resolved, final_pending, final_locked

// 导出当前使用的类型
export type ReportStatus = Phase1ReportStatus;
```

### 0.3 充值状态（7 个）

```typescript
type TopupStatus =
  | 'draft'           // 草稿
  | 'pending_review'  // 待审核
  | 'finance_approve' // 财务已批准
  | 'paid'            // 已转账
  | 'completed'       // 已完成
  | 'rejected'        // 已拒绝
  | 'cancelled';      // 已取消
```

### 0.4 禁止事项清单

| 编号 | ❌ 禁止 | ✅ 正确做法 | 检测方法 |
|------|--------|-----------|----------|
| F-001 | 使用 supervisor 角色 | 使用 project_owner | `grep 'supervisor'` |
| F-002 | 使用 Phase 2 日报状态 | 只用 3 个 Phase 1 状态 | `grep 'trend_pending\|trend_flagged'` |
| F-003 | 手写 `<table>` 组件 | 使用 DataTable | `grep '<table'` |
| F-004 | 手写 fetch 请求 | 使用 apiGet/apiPost | `grep 'fetch('` |
| F-005 | 自定义状态值 | 只用白名单状态 | 对比白名单 |
| F-006 | 缺少 'use client' | 交互页面必须加 | 检查第一行 |

### 0.5 必须使用的组件

| 场景 | ✅ 必须用 | ❌ 禁止用 |
|------|----------|----------|
| 数据列表 | DataTable | 手写 table |
| 状态标签 | StatusBadge | 手写 span/badge |
| 页面标题 | PageHeader | 手写 h1 |
| 统计卡片 | MetricCard | 手写 card |
| 确认弹窗 | alert-dialog | 手写 modal |
| 加载状态 | LoadingState | 手写 skeleton |
| 空状态 | EmptyState | 手写 div |

---

## 一、决策树（快速定位任务）

### 1.1 我要开发什么类型的页面？

```
用户需求
    │
    ├─ 展示数据列表 ──────────→ 第七章 列表页面模板
    │   (日报列表、充值列表、项目列表)
    │
    ├─ 展示统计数据 ──────────→ 第六章 MetricCard 组件
    │   (驾驶舱、概览页)
    │
    ├─ 创建/编辑数据 ─────────→ 第八章 表单弹窗模板
    │   (新建项目、编辑用户)
    │
    ├─ 审批/状态操作 ─────────→ 第七章 操作按钮 + 状态流转
    │   (日报审核、充值审批)
    │
    └─ 筛选/搜索 ─────────────→ 第六章 DataTableToolbar
```

### 1.2 我应该调用哪个 API？

```
业务模块
    │
    ├─ 认证相关 ──→ /api/v1/auth/*        (登录、获取用户)
    ├─ 用户相关 ──→ /api/v1/users/*       (用户 CRUD)
    ├─ 项目相关 ──→ /api/v1/projects/*    (项目 CRUD、盈亏)
    ├─ 账户相关 ──→ /api/v1/ad-accounts/* (账户 CRUD、分配)
    ├─ 日报相关 ──→ /api/v1/daily-reports/* (日报 CRUD、状态流转)
    ├─ 充值相关 ──→ /api/v1/topup-requests/* (充值 CRUD、审批)
    └─ 统计相关 ──→ /api/v1/stats/*       (驾驶舱、项目统计)
```

### 1.3 状态标签用什么 type？

```typescript
// 日报状态
<StatusBadge status="raw_submitted" type="report" />

// 充值状态
<StatusBadge status="pending_review" type="topup" />

// 项目状态
<StatusBadge status="active" type="project" />
```

---

## 二、项目初始化

### 2.1 依赖安装

```bash
npx create-next-app@14 frontend --typescript --tailwind --app
cd frontend

# 核心依赖
npm install @tanstack/react-query@5
npm install react-hook-form zod @hookform/resolvers
npm install date-fns lucide-react
npm install clsx tailwind-merge

# shadcn/ui
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card input table dialog form select toast skeleton badge alert-dialog
```

### 2.2 环境变量

```env
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=AI广告代投系统
```

---

## 三、核心基础设施代码

### 3.1 API 客户端 (src/lib/api.ts)

```typescript
// src/lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class ApiError extends Error {
  code: string;
  status: number;
  
  constructor(code: string, message: string, status: number = 400) {
    super(message);
    this.code = code;
    this.status = status;
    this.name = 'ApiError';
  }
}

export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = typeof window !== 'undefined' 
    ? localStorage.getItem('access_token') 
    : null;
  
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
  });

  const data = await response.json();
  
  // 401 未认证 - 跳转登录
  if (response.status === 401) {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    throw new ApiError('AUTH_401', '请重新登录', 401);
  }

  // 业务错误
  if (!response.ok || data.code !== 0) {
    throw new ApiError(
      data.error?.code || 'UNKNOWN',
      data.error?.message || data.message || '请求失败',
      response.status
    );
  }

  return data.data;
}

// 便捷方法
export const apiGet = <T>(url: string, params?: Record<string, any>) => {
  const searchParams = params ? '?' + new URLSearchParams(
    Object.entries(params).filter(([_, v]) => v !== undefined && v !== '')
  ).toString() : '';
  return apiFetch<T>(`${url}${searchParams}`);
};

export const apiPost = <T>(url: string, body?: any) =>
  apiFetch<T>(url, { method: 'POST', body: JSON.stringify(body) });

export const apiPut = <T>(url: string, body?: any) =>
  apiFetch<T>(url, { method: 'PUT', body: JSON.stringify(body) });

export const apiDelete = <T>(url: string) =>
  apiFetch<T>(url, { method: 'DELETE' });
```

### 3.2 工具函数 (src/lib/utils.ts)

```typescript
// src/lib/utils.ts
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { format, parseISO } from 'date-fns';
import { zhCN } from 'date-fns/locale';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// 日期格式化
export function formatDate(date: string | Date, pattern = 'yyyy-MM-dd'): string {
  if (!date) return '-';
  const d = typeof date === 'string' ? parseISO(date) : date;
  return format(d, pattern, { locale: zhCN });
}

export function formatDateTime(date: string | Date): string {
  return formatDate(date, 'yyyy-MM-dd HH:mm');
}

// 金额格式化
export function formatCurrency(amount: number | string | null | undefined): string {
  if (amount === null || amount === undefined) return '¥0.00';
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  return `¥${num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

// 百分比格式化
export function formatPercent(value: number | null | undefined, decimals = 1): string {
  if (value === null || value === undefined) return '-';
  return `${value.toFixed(decimals)}%`;
}

// CPL 格式化
export function formatCPL(spend: number, leads: number): string {
  if (!leads || leads === 0) return '-';
  return formatCurrency(spend / leads);
}
```

### 3.3 认证工具 (src/lib/auth.ts)

```typescript
// src/lib/auth.ts
import { apiPost, apiGet } from './api';

// ⚠️ 角色白名单（6 个，无 supervisor）
export type Role = 'ceo' | 'project_owner' | 'finance' | 'pitcher' | 'account_manager' | 'admin';

export interface User {
  id: string;
  email: string;
  name: string;
  role: Role;
  is_active: boolean;
}

export interface LoginResponse {
  access_token: string;
  user: User;
}

// 登录
export async function login(email: string, password: string): Promise<LoginResponse> {
  const data = await apiPost<LoginResponse>('/api/v1/auth/login', { email, password });
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('user', JSON.stringify(data.user));
  return data;
}

// 登出
export function logout(): void {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
  window.location.href = '/login';
}

// 获取当前用户
export function getCurrentUser(): User | null {
  if (typeof window === 'undefined') return null;
  const userStr = localStorage.getItem('user');
  return userStr ? JSON.parse(userStr) : null;
}

// 检查角色权限
export function hasRole(allowedRoles: Role[]): boolean {
  const user = getCurrentUser();
  return user ? allowedRoles.includes(user.role) : false;
}

// 角色中文名
export const ROLE_LABELS: Record<Role, string> = {
  ceo: '老板',
  project_owner: '项目负责人',
  finance: '财务',
  pitcher: '投手',
  account_manager: '户管',
  admin: '管理员',
};
```

### 3.4 React Query 配置 (src/lib/query.ts)

```typescript
// src/lib/query.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,  // 5 分钟
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});
```

### 3.5 类型定义 (src/types/api.ts)

```typescript
// src/types/api.ts

// ============ 分页 ============
export interface PaginationParams {
  page?: number;
  page_size?: number;
}

export interface PaginatedData<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ============ 角色（6 个，无 supervisor）============
export type Role = 'ceo' | 'project_owner' | 'finance' | 'pitcher' | 'account_manager' | 'admin';

// ============ 日报状态（Phase 1 只用 3 个）============
// Phase 1 启用状态
export type Phase1ReportStatus = 'raw_submitted' | 'trend_ok' | 'final_confirmed';

// Phase 2 完整状态（当前禁用）
export type Phase2ReportStatus = 
  | 'raw_submitted' | 'trend_pending' | 'trend_ok' | 'trend_flagged'
  | 'trend_resolved' | 'final_pending' | 'final_confirmed' | 'final_locked';

// 当前使用 Phase 1
export type ReportStatus = Phase1ReportStatus;

// ============ 充值状态（7 个）============
export type TopupStatus =
  | 'draft'           // 草稿
  | 'pending_review'  // 待审核
  | 'finance_approve' // 财务已批准
  | 'paid'            // 已转账
  | 'completed'       // 已完成
  | 'rejected'        // 已拒绝
  | 'cancelled';      // 已取消

// ============ 项目状态 ============
export type ProjectStatus = 'draft' | 'active' | 'paused' | 'completed';

// ============ 账户状态 ============
export type AccountStatus = 'active' | 'disabled' | 'frozen';

// ============ 实体类型 ============
export interface User {
  id: string;
  email: string;
  name: string;
  role: Role;
  is_active: boolean;
  created_at: string;
}

export interface Project {
  id: string;
  name: string;
  client_name: string;
  status: ProjectStatus;
  owner_id: string;
  owner_name?: string;
  billing_type: 'per_lead' | 'fee_rate';
  unit_price?: number;
  fee_rate?: number;
  budget?: number;
  created_at: string;
}

export interface AdAccount {
  id: string;
  name: string;
  platform: string;
  account_id: string;
  status: AccountStatus;
  pitcher_id?: string;
  pitcher_name?: string;
  project_id?: string;
  balance: number;
  created_at: string;
}

export interface DailyReport {
  id: string;
  report_date: string;
  ad_account_id: string;
  ad_account_name?: string;
  pitcher_id: string;
  pitcher_name?: string;
  project_id: string;
  project_name?: string;
  spend: number;
  conversions: number;
  cpl?: number;
  status: ReportStatus;  // Phase 1: 只有 3 个状态
  remark?: string;
  created_at: string;
  updated_at: string;
}

export interface TopupRequest {
  id: string;
  ad_account_id: string;
  ad_account_name?: string;
  amount: number;
  reason?: string;
  status: TopupStatus;
  applicant_id: string;
  applicant_name?: string;
  reviewer_id?: string;
  reviewer_name?: string;
  review_comment?: string;
  created_at: string;
  updated_at: string;
}

// ============ 状态显示配置 ============
// Phase 1 日报状态（3 个）
export const REPORT_STATUS_LABELS: Record<Phase1ReportStatus, string> = {
  raw_submitted: '已提交',
  trend_ok: '已审核',
  final_confirmed: '已确认',
};

export const TOPUP_STATUS_LABELS: Record<TopupStatus, string> = {
  draft: '草稿',
  pending_review: '待审核',
  finance_approve: '财务已批准',
  paid: '已转账',
  completed: '已完成',
  rejected: '已拒绝',
  cancelled: '已取消',
};

export const PROJECT_STATUS_LABELS: Record<ProjectStatus, string> = {
  draft: '草稿',
  active: '进行中',
  paused: '已暂停',
  completed: '已完成',
};
```

---

## 四、完整 API 端点映射

> **来源**: 后端 57 个 API 任务 + API_SOT.md

### 4.1 认证模块

| 功能 | 方法 | 端点 | 请求体 | 响应 |
|------|------|------|--------|------|
| 登录 | POST | `/api/v1/auth/login` | `{email, password}` | `{access_token, user}` |
| 获取当前用户 | GET | `/api/v1/auth/me` | - | `User` |

### 4.2 用户模块

| 功能 | 方法 | 端点 | 请求体/参数 | 响应 |
|------|------|------|------------|------|
| 用户列表 | GET | `/api/v1/users` | `?role=&project_id=` | `PaginatedData<User>` |
| 用户详情 | GET | `/api/v1/users/{id}` | - | `User` |
| 创建用户 | POST | `/api/v1/users` | `{email, name, role, ...}` | `User` |
| 更新用户 | PUT | `/api/v1/users/{id}` | `{name, role, ...}` | `User` |

### 4.3 项目模块

| 功能 | 方法 | 端点 | 请求体/参数 | 响应 |
|------|------|------|------------|------|
| 项目列表 | GET | `/api/v1/projects` | `?status=&owner_id=` | `PaginatedData<Project>` |
| 项目详情 | GET | `/api/v1/projects/{id}` | - | `Project` |
| 创建项目 | POST | `/api/v1/projects` | `{name, owner_id, ...}` | `Project` |
| 更新项目 | PUT | `/api/v1/projects/{id}` | `{name, status, ...}` | `Project` |
| 项目盈亏列表 | GET | `/api/v1/projects/profit-summary` | `?month=` | `ProjectProfit[]` |
| 项目成员列表 | GET | `/api/v1/projects/{id}/members` | - | `ProjectMember[]` |
| 添加项目成员 | POST | `/api/v1/projects/{id}/members` | `{user_id, role}` | `ProjectMember` |

### 4.4 广告账户模块

| 功能 | 方法 | 端点 | 请求体/参数 | 响应 |
|------|------|------|------------|------|
| 账户列表 | GET | `/api/v1/ad-accounts` | `?pitcher_id=&status=` | `PaginatedData<AdAccount>` |
| 账户详情 | GET | `/api/v1/ad-accounts/{id}` | - | `AdAccount` |
| 创建账户 | POST | `/api/v1/ad-accounts` | `{name, platform, ...}` | `AdAccount` |
| 更新账户 | PUT | `/api/v1/ad-accounts/{id}` | `{name, status, ...}` | `AdAccount` |
| 分配账户 | POST | `/api/v1/ad-accounts/{id}/assign` | `{pitcher_id}` | `AdAccount` |
| 取消分配 | POST | `/api/v1/ad-accounts/{id}/unassign` | - | `AdAccount` |

### 4.5 日报模块（核心）

| 功能 | 方法 | 端点 | 请求体/参数 | 响应 |
|------|------|------|------------|------|
| 日报列表 | GET | `/api/v1/daily-reports` | `?date=&project_id=&pitcher_id=&status=` | `PaginatedData<DailyReport>` |
| 日报详情 | GET | `/api/v1/daily-reports/{id}` | - | `DailyReport` |
| 提交日报 | POST | `/api/v1/daily-reports` | `{date, ad_account_id, spend, conversions}` | `DailyReport` |
| 更新日报 | PUT | `/api/v1/daily-reports/{id}` | `{spend, conversions, remark}` | `DailyReport` |
| **Phase 1 审核** | POST | `/api/v1/daily-reports/{id}/approve` | - | `DailyReport` |
| **Phase 1 确认** | POST | `/api/v1/daily-reports/{id}/confirm` | - | `DailyReport` |

> **Phase 1 状态流转**: `raw_submitted` → `trend_ok` → `final_confirmed`

### 4.6 充值模块

| 功能 | 方法 | 端点 | 请求体/参数 | 响应 |
|------|------|------|------------|------|
| 充值列表 | GET | `/api/v1/topup-requests` | `?status=&project_id=&applicant_id=` | `PaginatedData<TopupRequest>` |
| 充值详情 | GET | `/api/v1/topup-requests/{id}` | - | `TopupRequest` |
| 创建申请 | POST | `/api/v1/topup-requests` | `{ad_account_id, amount, reason}` | `TopupRequest` |
| 提交审核 | POST | `/api/v1/topup-requests/{id}/submit` | - | `TopupRequest` |
| 审批通过 | POST | `/api/v1/topup-requests/{id}/approve` | `{comment?}` | `TopupRequest` |
| 审批拒绝 | POST | `/api/v1/topup-requests/{id}/reject` | `{comment}` | `TopupRequest` |
| 确认转账 | POST | `/api/v1/topup-requests/{id}/pay` | - | `TopupRequest` |
| 确认到账 | POST | `/api/v1/topup-requests/{id}/complete` | - | `TopupRequest` |

### 4.7 统计模块

| 功能 | 方法 | 端点 | 参数 | 响应 |
|------|------|------|------|------|
| 驾驶舱统计 | GET | `/api/v1/stats/dashboard` | `?month=` | `DashboardStats` |
| 项目统计 | GET | `/api/v1/stats/project/{id}` | `?start_date=&end_date=` | `ProjectStats` |
| 投手统计 | GET | `/api/v1/stats/pitcher/{id}` | `?start_date=&end_date=` | `PitcherStats` |

---

## 五、导航菜单配置

### 5.1 菜单配置 (src/config/menu.ts)

```typescript
// src/config/menu.ts
import {
  LayoutDashboard, Wallet, TrendingUp, FileCheck, FileText,
  Calendar, FolderKanban, Users, BarChart3, Calculator,
  PlusCircle, CreditCard, Settings
} from 'lucide-react';
import type { Role } from '@/lib/auth';

export interface MenuItem {
  label: string;
  path: string;
  icon: any;
  roles: Role[];  // 6 角色，无 supervisor
}

export interface MenuGroup {
  title: string;
  items: MenuItem[];
}

// 管理端菜单
export const adminMenuGroups: MenuGroup[] = [
  {
    title: '数据概览',
    items: [
      { label: '驾驶舱', path: '/dashboard', icon: LayoutDashboard, roles: ['ceo', 'project_owner'] },
      { label: '资金总览', path: '/finance/overview', icon: Wallet, roles: ['ceo', 'finance', 'account_manager'] },
      { label: '项目盈亏', path: '/projects/profit', icon: TrendingUp, roles: ['ceo', 'project_owner', 'finance'] },
    ],
  },
  {
    title: '日常审批',
    items: [
      { label: '充值审批', path: '/topup/approval', icon: FileCheck, roles: ['ceo', 'finance', 'account_manager'] },
      { label: '日报审核', path: '/reports/daily', icon: FileText, roles: ['ceo', 'project_owner'] },
      { label: '周度简报', path: '/reports/weekly', icon: Calendar, roles: ['ceo', 'project_owner'] },
    ],
  },
  {
    title: '基础管理',
    items: [
      { label: '项目管理', path: '/projects', icon: FolderKanban, roles: ['ceo', 'project_owner', 'admin'] },
      { label: '投手管理', path: '/pitchers', icon: Users, roles: ['ceo', 'project_owner', 'account_manager'] },
      { label: '消耗明细', path: '/reports/spend', icon: BarChart3, roles: ['ceo', 'project_owner', 'finance', 'pitcher'] },
    ],
  },
  {
    title: '财务结算',
    items: [
      { label: '月度结算', path: '/settlement', icon: Calculator, roles: ['ceo', 'finance'] },
    ],
  },
];

// 投手端菜单
export const pitcherMenuItems: MenuItem[] = [
  { label: '填写日报', path: '/pitcher/daily-report', icon: FileText, roles: ['pitcher'] },
  { label: '申请充值', path: '/pitcher/topup-request', icon: PlusCircle, roles: ['pitcher'] },
  { label: '我的账户', path: '/pitcher/accounts', icon: CreditCard, roles: ['pitcher'] },
  { label: '消耗明细', path: '/reports/spend', icon: BarChart3, roles: ['pitcher'] },
];

// 根据角色获取菜单
export function getMenuForRole(role: Role): MenuGroup[] {
  if (role === 'pitcher') {
    return [{ title: '投手工作台', items: pitcherMenuItems }];
  }
  
  return adminMenuGroups.map(group => ({
    ...group,
    items: group.items.filter(item => item.roles.includes(role)),
  })).filter(group => group.items.length > 0);
}
```

---

## 六、组件库一览（60+ 组件）

> **说明**: 基于 shadcn/ui + 自定义业务组件

### 6.1 shadcn/ui 基础组件

| 分类 | 组件 |
|------|------|
| **按钮/输入** | button, input, textarea, checkbox, radio-group, switch, slider, select |
| **表单** | form, label, calendar |
| **数据展示** | table, card, badge, avatar, progress, skeleton |
| **反馈** | alert, alert-dialog, dialog, sheet, sonner (toast) |
| **导航** | tabs, breadcrumb, dropdown-menu, context-menu |
| **布局** | separator, scroll-area, collapsible, accordion |
| **覆盖层** | popover, tooltip, hover-card, command |

### 6.2 业务组件

| 组件 | 路径 | 用途 |
|------|------|------|
| MetricCard | `components/ui/MetricCard.tsx` | KPI 指标卡片 |
| StatusBadge | `components/ui/StatusBadge.tsx` | 状态标签 |
| SSRSafeWrapper | `components/ui/SSRSafeWrapper.tsx` | SSR 安全包装器 |
| user-profile-dropdown | `components/ui/user-profile-dropdown.tsx` | 用户头像下拉 |

### 6.3 数据表格组件

| 组件 | 路径 | 用途 |
|------|------|------|
| DataTable | `components/ui/data-table/DataTable.tsx` | 通用数据表格 |
| DataTablePagination | `components/ui/data-table/DataTablePagination.tsx` | 表格分页 |
| DataTableToolbar | `components/ui/data-table/DataTableToolbar.tsx` | 表格工具栏 |

### 6.4 布局组件

| 组件 | 路径 | 用途 |
|------|------|------|
| AppShell | `components/layout/AppShell.tsx` | 应用外壳 |
| Header | `components/layout/Header.tsx` | 顶部导航栏 |
| Sidebar | `components/layout/Sidebar.tsx` | 侧边栏导航 |
| PageHeader | `components/layout/page-header.tsx` | 页面标题区域 |

### 6.5 数据状态组件

| 组件 | 用途 |
|------|------|
| LoadingState | 加载中状态 |
| EmptyState | 空数据状态 |
| ErrorState | 错误状态 |

### 6.6 组件使用示例

```typescript
// DataTable 使用
import { DataTable } from '@/components/ui/data-table/DataTable';
<DataTable columns={columns} data={data} />

// MetricCard 使用
import { MetricCard } from '@/components/ui/MetricCard';
<MetricCard title="本月消耗" value={formatCurrency(spend)} icon={DollarSign} />

// StatusBadge 使用 - 注意 Phase 1 日报只有 3 个状态
import { StatusBadge } from '@/components/ui/StatusBadge';
<StatusBadge status="raw_submitted" type="report" />  // Phase 1 ✅
<StatusBadge status="trend_ok" type="report" />       // Phase 1 ✅
<StatusBadge status="final_confirmed" type="report" /> // Phase 1 ✅
// ❌ 禁止使用: trend_pending, trend_flagged, trend_resolved, final_pending, final_locked

// 布局组件使用
import { AppShell } from '@/components/layout/AppShell';
import { PageHeader } from '@/components/layout/page-header';

export default function DailyReportsPage() {
  return (
    <>
      <PageHeader title="日报审核" description="审核投手每日填报的数据" />
      {/* 页面内容 */}
    </>
  );
}
```

### 6.7 组件选择指南

| 场景 | 推荐组件 |
|------|----------|
| 列表页面 | DataTable + DataTablePagination + DataTableToolbar |
| 统计卡片 | MetricCard |
| 状态展示 | StatusBadge |
| 数据加载 | LoadingState / EmptyState / ErrorState |
| 页面布局 | AppShell + Sidebar + Header |
| 页面标题 | PageHeader |
| 弹窗确认 | alert-dialog |
| 表单弹窗 | dialog + form |
| 通知提示 | sonner (toast) |

---

## 七、列表页面完整示例

### 7.1 日报审核页面（Phase 1 版本）

```typescript
// src/app/(dashboard)/reports/daily/page.tsx
'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/page-header';
import { DataTable } from '@/components/ui/data-table/DataTable';
import { DataTablePagination } from '@/components/ui/data-table/DataTablePagination';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Button } from '@/components/ui/button';
import { LoadingState } from '@/components/shared/LoadingState';
import { EmptyState } from '@/components/shared/EmptyState';
import { apiGet, apiPost } from '@/lib/api';
import { formatDate, formatCurrency, formatCPL } from '@/lib/utils';
import { toast } from 'sonner';
import type { DailyReport, PaginatedData, Phase1ReportStatus } from '@/types/api';

// Phase 1 日报状态（只有 3 个）
const PHASE1_STATUS_OPTIONS = [
  { value: 'raw_submitted', label: '已提交' },
  { value: 'trend_ok', label: '已审核' },
  { value: 'final_confirmed', label: '已确认' },
];

export default function DailyReportsPage() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<Phase1ReportStatus | ''>('');
  const queryClient = useQueryClient();

  // 获取日报列表
  const { data, isLoading } = useQuery({
    queryKey: ['daily-reports', page, status],
    queryFn: () => apiGet<PaginatedData<DailyReport>>('/api/v1/daily-reports', {
      page,
      page_size: 20,
      status: status || undefined,
    }),
  });

  // Phase 1 审核操作（raw_submitted → trend_ok）
  const approveMutation = useMutation({
    mutationFn: (id: string) => apiPost(`/api/v1/daily-reports/${id}/approve`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['daily-reports'] });
      toast.success('审核通过');
    },
    onError: (error: any) => {
      toast.error(error.message || '操作失败');
    },
  });

  // Phase 1 确认操作（trend_ok → final_confirmed）
  const confirmMutation = useMutation({
    mutationFn: (id: string) => apiPost(`/api/v1/daily-reports/${id}/confirm`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['daily-reports'] });
      toast.success('确认成功');
    },
    onError: (error: any) => {
      toast.error(error.message || '操作失败');
    },
  });

  // 表格列定义
  const columns = [
    { accessorKey: 'report_date', header: '日期', cell: ({ row }) => formatDate(row.original.report_date) },
    { accessorKey: 'pitcher_name', header: '投手' },
    { accessorKey: 'project_name', header: '项目' },
    { accessorKey: 'ad_account_name', header: '账户' },
    { accessorKey: 'spend', header: '消耗', cell: ({ row }) => formatCurrency(row.original.spend) },
    { accessorKey: 'conversions', header: '进粉' },
    { accessorKey: 'cpl', header: 'CPL', cell: ({ row }) => formatCPL(row.original.spend, row.original.conversions) },
    { 
      accessorKey: 'status', 
      header: '状态', 
      cell: ({ row }) => <StatusBadge status={row.original.status} type="report" />
    },
    {
      id: 'actions',
      header: '操作',
      cell: ({ row }) => {
        const report = row.original;
        
        // Phase 1 状态流转: raw_submitted → trend_ok → final_confirmed
        if (report.status === 'raw_submitted') {
          return (
            <Button size="sm" onClick={() => approveMutation.mutate(report.id)}>
              审核通过
            </Button>
          );
        }
        
        if (report.status === 'trend_ok') {
          return (
            <Button size="sm" onClick={() => confirmMutation.mutate(report.id)}>
              确认数据
            </Button>
          );
        }
        
        // final_confirmed 是终态
        return <span className="text-muted-foreground">已完成</span>;
      },
    },
  ];

  if (isLoading) return <LoadingState />;

  return (
    <>
      <PageHeader 
        title="日报审核" 
        description="审核投手每日填报的消耗和进粉数据（Phase 1: 3 状态）"
      />
      
      {/* 筛选器 - 只显示 Phase 1 的 3 个状态 */}
      <div className="flex gap-4 mb-4">
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value as Phase1ReportStatus | '')}
          className="border rounded px-3 py-2"
        >
          <option value="">全部状态</option>
          {PHASE1_STATUS_OPTIONS.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>

      {/* 数据表格 */}
      {!data?.items.length ? (
        <EmptyState title="暂无日报" description="当前没有需要审核的日报" />
      ) : (
        <>
          <DataTable columns={columns} data={data.items} />
          <DataTablePagination
            page={page}
            pageSize={20}
            total={data.total}
            onChange={setPage}
          />
        </>
      )}
    </>
  );
}
```

---

## 八、AI 编码提示词模板

### 模板 1: 列表页面

```markdown
## 任务
创建 {{页面名称}} 列表页面。

## 技术栈
- Next.js 14 App Router + TypeScript
- TanStack Query v5
- shadcn/ui + Tailwind CSS

## 铁律检查
- [ ] 角色使用 6 角色白名单（无 supervisor）
- [ ] 日报状态使用 Phase 1 的 3 个状态
- [ ] 使用 DataTable 组件（禁止手写 table）
- [ ] 使用 StatusBadge 组件
- [ ] 使用 apiGet/apiPost（禁止直接 fetch）

## 页面信息
- 文件路径: src/app/(dashboard)/{{path}}/page.tsx
- API 端点: GET /api/v1/{{endpoint}}
- 允许角色: {{roles}}

## 输出
完整的 page.tsx 文件，包含 'use client' 指令

## 验证清单
- [ ] 第一行是 'use client'
- [ ] 使用了 PageHeader 组件
- [ ] 使用了 DataTable 组件
- [ ] 使用了 StatusBadge 组件
- [ ] 无 TypeScript 错误
```

### 模板 2: 表单弹窗

```markdown
## 任务
创建 {{实体名称}} 的创建/编辑表单弹窗。

## 技术栈
- react-hook-form + zod 验证
- shadcn/ui Dialog + Form

## 表单字段
{{字段列表}}

## 铁律检查
- [ ] 角色字段使用 6 角色白名单
- [ ] 状态字段使用对应白名单
- [ ] 使用 apiPost/apiPut 提交

## 输出
1. Zod schema 定义
2. 表单组件代码

## 验证清单
- [ ] 所有必填字段有 required 验证
- [ ] 使用 toast 显示操作结果
- [ ] 提交成功后刷新列表
```

### 模板 3: API 服务 + Hook

```markdown
## 任务
为 {{模块名称}} 创建 API 服务和 TanStack Query Hook。

## API 端点
- 列表: GET /api/v1/{{endpoint}}
- 详情: GET /api/v1/{{endpoint}}/{id}
- 创建: POST /api/v1/{{endpoint}}
- 更新: PUT /api/v1/{{endpoint}}/{id}

## 铁律检查
- [ ] 使用 apiGet/apiPost/apiPut 函数
- [ ] 状态值来自白名单
- [ ] 正确使用 queryKey 和 invalidateQueries

## 输出
1. src/modules/{{module}}/services/{{name}}.ts
2. src/modules/{{module}}/hooks/use{{Name}}.ts
```

---

## 九、开发检查清单

### 9.1 代码生成前检查

```
□ 确认当前是 Phase 1（日报只用 3 状态）
□ 确认角色在 6 角色白名单内（无 supervisor）
□ 确认状态值来源（日报 3 状态 / 充值 6 状态）
□ 确认 API 端点存在
□ 确认使用必须组件（DataTable, StatusBadge, PageHeader）
```

### 9.2 代码生成后检查

```
□ 第一行是否为 'use client'（交互页面）
□ 是否使用了禁止的角色（supervisor）
□ 是否使用了 Phase 2 日报状态
□ 是否手写了 table/fetch
□ 是否有 TypeScript 错误
□ 页面是否能正常渲染
```

---

## 十、快速参考

### 6 个角色（无 supervisor）

```typescript
type Role = 'ceo' | 'project_owner' | 'finance' | 'pitcher' | 'account_manager' | 'admin';
```

### Phase 1 日报状态（3 个）

```typescript
type Phase1ReportStatus = 'raw_submitted' | 'trend_ok' | 'final_confirmed';
// 流转: raw_submitted → trend_ok → final_confirmed
```

### 充值状态（6 个）

```typescript
type TopupStatus = 'draft' | 'pending_review' | 'approved' | 'rejected' | 'paid' | 'completed';
```

### 关键文件路径

```
src/
├── app/(dashboard)/
│   ├── dashboard/page.tsx          # 驾驶舱
│   ├── reports/daily/page.tsx      # 日报审核
│   ├── topup/approval/page.tsx     # 充值审批
│   ├── projects/page.tsx           # 项目管理
│   └── pitcher/
│       ├── daily-report/page.tsx   # 投手填日报
│       └── topup-request/page.tsx  # 投手申请充值
├── components/
│   ├── ui/                         # shadcn/ui + 业务组件
│   ├── layout/                     # 布局组件
│   └── shared/                     # 共享组件
├── lib/
│   ├── api.ts                      # API 客户端
│   ├── auth.ts                     # 认证工具
│   ├── utils.ts                    # 工具函数
│   └── query.ts                    # React Query 配置
└── types/
    └── api.ts                      # 类型定义
```

---

## 十一、版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v3.1 | 2026-01-05 | 对齐 SoT: 充值状态 7 个、版本更新、角色双层系统 |
| v3.0 | 2025-12-28 | AI 编程友好版：铁律前置 + Phase 边界明确 + 决策树 |
| v2.2 | 2025-12-28 | 整合实际代码库组件 60+ |
| v2.1 | 2025-12-28 | 修复 API 对齐 + 恢复提示词模板 |

---

**文档版本**: v3.1
**创建日期**: 2025-12-28
**最后更新**: 2026-01-05
**核心改进**: 
- ✅ 铁律前置（第零章）
- ✅ Phase 1 日报状态明确为 3 个
- ✅ 决策树帮助快速定位
- ✅ 禁止事项清单
- ✅ 组件强制使用规则
- ✅ 完整页面示例（Phase 1 版本）

**基准文档**: MASTER.md v4.9 + PRD v5.2 + STATE_MACHINE.md v2.9
