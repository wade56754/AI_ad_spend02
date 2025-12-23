# 前端 AI 编程规范 v1.2

> **面向对象**: Claude Code / Cursor 等 AI 编程助手
> **核心原则**: 能抄不写，能复用不开发，最小代码量
> **SoT 对齐**: MASTER.md v4.4, PROJECT.md v1.3, AUTH_SPEC.md v2.0, STATE_MACHINE.md v2.6
> **文档状态**: 已审查校验，包含待实现功能标注 ⚠️

---

## 第一章 现有代码地图

### 1.1 目录结构（AI 必须先扫描）

```
frontend/src/
├── app/                      # 页面路由（App Router）
│   ├── (dashboard)/          # 需登录的页面（路由组）
│   │   ├── page.tsx          # 首页/驾驶舱
│   │   ├── daily-reports/    # 日报管理
│   │   ├── projects/         # 项目管理
│   │   ├── topups/           # 充值管理
│   │   └── ...
│   ├── login/                # 登录页
│   ├── register/             # 注册页
│   └── providers.tsx         # 全局 Provider
│
├── components/
│   ├── ui/                   # shadcn 基础组件（禁止修改）
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── data-table/       # 数据表格组件
│   │   ├── data-state/       # 加载/空/错误状态
│   │   ├── dialog.tsx
│   │   ├── form.tsx
│   │   └── ...
│   ├── dashboard/            # 驾驶舱专用组件
│   ├── layout/               # 布局组件
│   └── shared/               # 共享业务组件
│
├── features/                 # 功能模块（feature-based）
│   ├── auth/                 # 认证模块
│   │   ├── hooks/useAuth.ts  # 认证 hook
│   │   ├── services/         # API 调用
│   │   └── types/            # 类型定义
│   ├── daily-reports/        # 日报模块
│   ├── projects/             # 项目模块
│   ├── topups/               # 充值模块
│   └── ...
│
├── hooks/                    # 全局 hooks
│   ├── useAuth.ts            # → 重导出 features/auth/hooks
│   ├── use-table-params.ts   # 表格参数
│   └── use-theme.ts          # 主题切换
│
├── lib/
│   ├── api.ts                # API 调用封装（必须使用）
│   └── utils.ts              # 工具函数（cn 等）
│
├── config/                   # 配置常量 ⚠️ 待实现
│   ├── permissions.ts        # 权限矩阵（待实现）
│   ├── status/               # 状态常量（待实现）
│   └── phase.ts              # Phase 配置（待实现）
│
└── types/
    ├── common.ts             # 通用类型
    └── index.ts              # 类型导出
```

### 1.2 现有可复用资源清单

> **AI 开发新功能前必须检查此清单，找到可复用的代码**

#### 1.2.1 API 调用（lib/api.ts）

| 函数 | 用途 | 使用示例 |
|------|------|----------|
| `apiFetch<T>` | 通用请求 | `await apiFetch<User>('/api/v1/users/me')` |
| `apiFetchPaginated<T>` | 分页请求 | `await apiFetchPaginated<Project>('/api/v1/projects')` |
| `apiGet<T>` | GET 请求 | `await apiGet<User>('/api/v1/users/me')` |
| `apiPost<T>` | POST 请求 | `await apiPost<User>('/api/v1/users', data)` |
| `apiPatch<T>` | PATCH 请求 | `await apiPatch<User>('/api/v1/users/1', data)` |
| `apiDelete<T>` | DELETE 请求 | `await apiDelete('/api/v1/users/1')` |
| `apiUpload<T>` | 文件上传 | `await apiUpload<ImportJob>('/api/v1/import', file)` |
| `apiDownload` | 文件下载 | `await apiDownload('/api/v1/export', { saveAs: 'file.xlsx' })` |
| `queryKeys` | Query Key 工厂 | `queryKey: queryKeys.projects.list(params)` |

#### 1.2.2 认证相关（features/auth）

| 资源 | 位置 | 用途 |
|------|------|------|
| `useAuth` | `features/auth/hooks/useAuth.ts` | 获取用户/登录/登出 |
| `useRequireAuth` | 同上 | 页面级认证守卫 |
| `useRequireRole` | 同上 | 角色权限守卫 |
| `useProjectAccess` | `features/projects/hooks/useProjectAccess.ts` | 项目级权限检查 ⚠️ 待实现 |
| `UserRole` | `features/auth/types/auth.types.ts` | 角色枚举 |
| `User` | 同上 | 用户类型定义 |

#### 1.2.3 UI 组件（components/ui）

| 组件 | 位置 | 用途 |
|------|------|------|
| `Button` | `ui/button.tsx` | 按钮 |
| `Card` | `ui/card.tsx` | 卡片容器 |
| `DataTable` | `ui/data-table/` | 数据表格（含分页） |
| `Dialog` | `ui/dialog.tsx` | 弹窗对话框 |
| `Form` | `ui/form.tsx` | 表单（react-hook-form） |
| `Input` | `ui/input.tsx` | 输入框 |
| `Select` | `ui/select.tsx` | 下拉选择 |
| `Tabs` | `ui/tabs.tsx` | 标签页 |
| `StatusBadge` | `ui/StatusBadge.tsx` | 状态徽章 |
| `MetricCard` | `ui/MetricCard.tsx` | KPI 卡片 |
| `LoadingState` | `ui/data-state/LoadingState.tsx` | 加载状态 |
| `EmptyState` | `ui/data-state/EmptyState.tsx` | 空数据状态 |
| `ErrorState` | `ui/data-state/ErrorState.tsx` | 错误状态 |
| `Skeleton` | `ui/skeleton.tsx` | 骨架屏 |

#### 1.2.4 布局组件（components/layout）

| 组件 | 位置 | 用途 |
|------|------|------|
| `AppLayout` | `layout/AppLayout.tsx` | 应用整体布局 |
| `DashboardLayout` | `layout/DashboardLayout.tsx` | 驾驶舱布局 |
| `PageHeader` | `layout/page-header.tsx` | 页面标题栏 |
| `PageTemplate` | `layout/page-template.tsx` | 页面模板 |

#### 1.2.5 Feature 模块结构

每个 feature 模块遵循统一结构：

```
features/{module}/
├── index.ts              # 模块导出
├── components/           # 模块组件
│   ├── {Module}Page.tsx  # 页面主组件
│   ├── {Module}Table.tsx # 表格组件
│   ├── {Module}Form.tsx  # 表单组件
│   └── index.ts
├── hooks/                # 模块 hooks
│   ├── use{Module}.ts    # 数据查询 hook
│   └── index.ts
├── services/             # API 调用
│   └── {module}Api.ts
└── types/                # 类型定义
    └── {module}.types.ts
```

---

## 第二章 AI 行为约束

### 2.1 禁止行为（NEVER）

```yaml
NEVER:
  # API 相关
  - 创建新的 API 调用方式（必须用 lib/api.ts）
  - 直接使用 fetch（必须用 apiFetch）
  - 使用 axios 或其他 HTTP 库
  - 使用 supabase-js 直连业务表（只用于 Auth）

  # 状态管理
  - 创建新的状态管理方案（必须用 TanStack Query）
  - 使用 Redux / Zustand / Jotai
  - 使用 React Context 管理服务端状态

  # UI 组件
  - 修改 components/ui/ 下的 shadcn 组件源码
  - 创建与 shadcn 功能重复的自定义组件
  - 引入新的 UI 库（Ant Design, Material UI 等）

  # 表单验证
  - 使用 yup 或其他验证库（必须用 Zod）
  - 手写表单验证逻辑

  # 代码规范
  - 使用 any 类型
  - 使用 @ts-ignore（可用 @ts-expect-error 并说明原因）
  - 引入新的 npm 依赖（除非明确要求）

  # 认证授权
  - 创建新的认证方式
  - 绕过 useAuth hook 直接读取 localStorage
  - 硬编码用户信息或 token
  - 新增角色（只能使用 7 个标准角色）
```

### 2.2 必须行为（ALWAYS）

```yaml
ALWAYS:
  # 开发前
  - 扫描现有代码，找可复用的组件/hooks/utils
  - 检查 features/ 下是否有相似模块可参考
  - 阅读相关的 SoT 文档（MASTER.md, STATE_MACHINE.md）

  # API 调用
  - 使用 lib/api.ts 的 apiFetch 系列函数
  - 使用 queryKeys 工厂生成 query key
  - 使用 TanStack Query 的 useQuery/useMutation

  # 组件开发
  - 使用 shadcn/ui 组件
  - 复用 components/ui/data-state/ 处理加载/空/错误状态
  - 复制最相似页面的代码结构
  - 遵循 feature 模块标准结构

  # 类型定义
  - 所有类型定义放在 types/ 或 features/*/types/
  - 复用 types/common.ts 的通用类型
  - 确保类型与后端 API 响应一致

  # 代码风格
  - 保持与现有代码一致的命名风格
  - 使用 cn() 合并 className
  - 使用 date-fns 处理日期
  - 使用 sonner 的 toast 显示提示

  # 权限检查
  - 页面级权限使用 useRequireRole
  - 项目级权限使用 useProjectAccess
  - 遵循 PAGE_ACCESS 权限矩阵
```

### 2.3 复用优先级

```
1. 完全相同 → 直接 import，不改一行
   例: import { useAuth } from '@/features/auth/hooks/useAuth'

2. 90% 相同 → 复制后改参数/配置
   例: 复制 DailyReportsPage，改 queryKey 和 columns

3. 70% 相同 → 复制后改逻辑
   例: 复制 useDailyReports hook，改 API 端点

4. 50% 相同 → 参考结构，重写内容
   例: 参考 daily-reports 模块结构，创建新模块

5. 完全不同 → 询问是否真的需要新建
   提示: "未找到可复用代码，是否确认需要新建？"
```

---

## 第三章 7 角色权限（硬编码）

> **SoT 来源**: MASTER.md v4.4 §2.4

### 3.1 角色常量（实际代码）

> **重要**: 实际代码使用技术角色名，与 MASTER.md v4.4 业务角色名存在映射关系

```typescript
// src/features/auth/types/auth.types.ts （实际代码）

/**
 * 用户角色枚举
 *
 * ⚠️ 实际代码使用技术名称，与 MASTER.md 业务角色有映射：
 *   - DATA_OPERATOR → supervisor（主管）
 *   - MEDIA_BUYER → pitcher（投手）
 *   - ceo 角色暂未实现，需扩展
 */
export enum UserRole {
  ADMIN = 'admin',                    // 管理员
  FINANCE = 'finance',                // 财务
  DATA_OPERATOR = 'data_operator',    // 主管（MASTER.md: supervisor）
  ACCOUNT_MANAGER = 'account_manager', // 户管
  MEDIA_BUYER = 'media_buyer',        // 投手（MASTER.md: pitcher）
  PROJECT_OWNER = 'project_owner',    // 项目负责人
  // ⚠️ CEO = 'ceo' 待实现
}
```

### 3.1.1 角色映射表

| MASTER.md 业务角色 | 实际代码技术角色 | 状态 |
|-------------------|-----------------|------|
| ceo（老板） | ❌ 待实现 | ⚠️ |
| project_owner | PROJECT_OWNER | ✅ |
| finance | FINANCE | ✅ |
| supervisor（主管） | DATA_OPERATOR | ✅ |
| pitcher（投手） | MEDIA_BUYER | ✅ |
| account_manager | ACCOUNT_MANAGER | ✅ |
| admin | ADMIN | ✅ |

### 3.1.2 角色标签（待实现）

```typescript
// ⚠️ 待实现：src/config/role-labels.ts

/**
 * 角色中文映射（用于显示）
 * 当前代码中未集中定义，需要创建
 */
export const ROLE_LABELS: Record<string, string> = {
  admin: '管理员',
  finance: '财务',
  data_operator: '主管',      // 显示为业务名
  account_manager: '户管',
  media_buyer: '投手',        // 显示为业务名
  project_owner: '项目负责人',
  // ceo: '老板',  // 待实现
};
```

### 3.2 角色映射（后端 ↔ 前端）⚠️ 待实现

```typescript
// ⚠️ 待实现：src/config/role-mapping.ts

/**
 * 后端技术角色 → 前端业务角色 映射
 * SoT: MASTER.md v4.4 §9 INV-002
 * 
 * 后端使用技术名（data_operator, media_buyer）
 * 前端显示业务名（supervisor, pitcher）
 */
export const BACKEND_TO_FRONTEND_ROLE: Record<string, UserRole> = {
  data_operator: 'supervisor',
  media_buyer: 'pitcher',
  // 其他角色名称一致，无需映射
};

export const FRONTEND_TO_BACKEND_ROLE: Record<string, string> = {
  supervisor: 'data_operator',
  pitcher: 'media_buyer',
};

/**
 * 将后端返回的角色转换为前端角色
 * @param backendRole 后端返回的角色名
 * @returns 前端使用的角色名
 */
export function normalizeRole(backendRole: string): UserRole {
  return (BACKEND_TO_FRONTEND_ROLE[backendRole] || backendRole) as UserRole;
}

/**
 * 将前端角色转换为后端角色（用于 API 请求）
 * @param frontendRole 前端角色名
 * @returns 后端使用的角色名
 */
export function toBackendRole(frontendRole: UserRole): string {
  return FRONTEND_TO_BACKEND_ROLE[frontendRole] || frontendRole;
}

/**
 * 检查角色是否等价（考虑映射关系）
 * @param role1 角色1
 * @param role2 角色2
 * @returns 是否等价
 */
export function isRoleEquivalent(role1: string, role2: string): boolean {
  const normalized1 = normalizeRole(role1);
  const normalized2 = normalizeRole(role2);
  return normalized1 === normalized2;
}
```

### 3.3 页面权限矩阵（AI 必须遵守）⚠️ 待实现

```typescript
// ⚠️ 待实现：src/config/permissions.ts

import type { UserRole } from '@/features/auth/types';

/**
 * 页面访问权限矩阵
 * SoT: MASTER.md v4.4 §2.4 角色权限 + §6 核心页面
 * 
 * ⚠️ 修改此矩阵必须与 MASTER.md 保持一致
 */
export const PAGE_ACCESS: Record<string, UserRole[]> = {
  // === 老板视角模块 ===
  '/':                        ['ceo'],                                    // 老板驾驶舱（仅 CEO）
  '/dashboard/ceo':           ['ceo'],                                    // CEO Dashboard
  '/fund-overview':           ['ceo', 'finance'],                         // 资金总览
  '/project-pnl':             ['ceo', 'project_owner', 'finance'],        // 项目盈亏

  // === 流程管理模块 ===
  '/topups':                  ['ceo', 'project_owner', 'finance'],        // 充值列表
  '/topups/request':          ['project_owner'],                          // 申请充值
  '/topups/review':           ['finance'],                                // 财务审核
  '/topups/approve':          ['ceo'],                                    // CEO 批准
  '/daily-reports':           ['ceo', 'project_owner', 'supervisor', 'pitcher'], // 日报列表
  '/daily-reports/submit':    ['pitcher'],                                // 提交日报
  '/daily-reports/review':    ['supervisor'],                             // 审核日报
  '/weekly-brief':            ['ceo', 'project_owner'],                   // 周度简报

  // === 数据管理模块 ===
  '/projects':                ['ceo', 'project_owner', 'finance', 'admin'], // 项目管理
  '/projects/create':         ['admin'],                                  // 创建项目
  '/pitchers':                ['ceo', 'supervisor', 'admin'],             // 投手管理
  '/ad-spend':                ['ceo', 'project_owner', 'supervisor', 'pitcher'], // 消耗明细
  '/ad-accounts':             ['ceo', 'account_manager', 'admin'],        // 广告账户

  // === 结算模块 ===
  '/settlements':             ['ceo', 'finance'],                         // 月度结算
  '/settlements/lock':        ['ceo', 'finance'],                         // 锁定结算
  '/reconciliation':          ['ceo', 'finance'],                         // 对账

  // === 系统管理 ===
  '/settings':                ['admin'],                                  // 系统设置
  '/users':                   ['admin'],                                  // 用户管理
};

/**
 * 操作权限矩阵
 * SoT: MASTER.md v4.4 §2.4 角色权限矩阵
 */
export const ACTION_PERMISSIONS: Record<string, UserRole[]> = {
  // 充值相关
  'topup:request':            ['project_owner'],                          // 申请充值
  'topup:review':             ['finance'],                                // 财务审核
  'topup:approve':            ['ceo'],                                    // CEO 批准
  'topup:post':               ['finance'],                                // 打款确认

  // 日报相关
  'daily_report:submit':      ['pitcher'],                                // 提交日报
  'daily_report:review':      ['supervisor'],                             // 审核日报
  'daily_report:lock':        ['finance'],                                // 锁定日报

  // 项目相关
  'project:create':           ['admin'],                                  // 创建项目
  'project:edit':             ['project_owner', 'admin'],                 // 编辑项目
  'project:view_pnl':         ['ceo', 'project_owner', 'finance'],        // 查看盈亏

  // 结算相关
  'settlement:view':          ['ceo', 'finance'],                         // 查看结算
  'settlement:lock':          ['ceo', 'finance'],                         // 锁定结算
  'settlement:reversal':      ['finance'],                                // 红冲（需外部审批单号）
};

/**
 * 检查用户是否有页面访问权限
 */
export function hasPageAccess(path: string, role: UserRole): boolean {
  const allowedRoles = PAGE_ACCESS[path];
  if (!allowedRoles) return true; // 未定义的页面默认允许
  return allowedRoles.includes(role);
}

/**
 * 检查用户是否有操作权限
 */
export function hasActionPermission(action: string, role: UserRole): boolean {
  const allowedRoles = ACTION_PERMISSIONS[action];
  if (!allowedRoles) return false; // 未定义的操作默认禁止
  return allowedRoles.includes(role);
}
```

### 3.4 项目级权限（project_members）⚠️ 待实现

```typescript
// ⚠️ 待实现：src/features/projects/hooks/useProjectAccess.ts

import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { apiFetch, queryKeys } from '@/lib/api';

/**
 * 项目成员角色
 * SoT: MASTER.md v4.4 - project_owner 必须用 project_members.project_role = 'owner' 表达
 */
export type ProjectRole = 'owner' | 'member' | 'viewer';

interface ProjectMembership {
  project_id: string;
  user_id: string;
  project_role: ProjectRole;
  permissions?: Record<string, boolean>;
}

interface UseProjectAccessProps {
  projectId: string;
  requiredRole?: ProjectRole;
}

interface UseProjectAccessResult {
  hasAccess: boolean;
  projectRole: ProjectRole | null;
  isLoading: boolean;
  isProjectOwner: boolean;
}

/**
 * 项目级权限检查 Hook
 * 
 * 使用场景：
 * - 检查用户是否为某项目的 owner
 * - 控制项目级别的操作权限
 * 
 * @example
 * const { hasAccess, isProjectOwner } = useProjectAccess({ 
 *   projectId: '123', 
 *   requiredRole: 'owner' 
 * });
 * 
 * if (!hasAccess) return <Unauthorized />;
 */
export function useProjectAccess({ 
  projectId, 
  requiredRole = 'member' 
}: UseProjectAccessProps): UseProjectAccessResult {
  const { user } = useAuth();

  const { data: membership, isLoading } = useQuery({
    queryKey: queryKeys.projectMembers.detail(projectId, user?.id || ''),
    queryFn: () => apiFetch<ProjectMembership>(
      `/api/v1/projects/${projectId}/members/${user?.id}`
    ),
    enabled: !!projectId && !!user?.id,
  });

  // CEO 和 Admin 默认有所有项目的最高权限
  if (user?.role === 'ceo' || user?.role === 'admin') {
    return {
      hasAccess: true,
      projectRole: 'owner',
      isLoading: false,
      isProjectOwner: true,
    };
  }

  // 检查 project_members.project_role
  const projectRole = membership?.project_role || null;
  const roleHierarchy: Record<ProjectRole, number> = {
    owner: 3,
    member: 2,
    viewer: 1,
  };

  const hasAccess = projectRole 
    ? roleHierarchy[projectRole] >= roleHierarchy[requiredRole]
    : false;

  return {
    hasAccess,
    projectRole,
    isLoading,
    isProjectOwner: projectRole === 'owner',
  };
}

/**
 * 获取用户负责的所有项目（project_role = 'owner'）
 */
export function useOwnedProjects() {
  const { user } = useAuth();

  return useQuery({
    queryKey: queryKeys.projects.owned(user?.id || ''),
    queryFn: () => apiFetch<{ id: string; name: string }[]>(
      `/api/v1/users/${user?.id}/owned-projects`
    ),
    enabled: !!user?.id,
  });
}
```

### 3.5 权限守卫组件 ⚠️ 待实现

```typescript
// ⚠️ 待实现：src/features/auth/components/RequireRole.tsx

'use client';

import { useAuth } from '../hooks/useAuth';
import type { UserRole } from '../types';
import { hasPageAccess } from '@/config/permissions';
import { usePathname, redirect } from 'next/navigation';

interface RequireRoleProps {
  roles: UserRole[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

/**
 * 角色权限守卫组件
 * 
 * @example
 * <RequireRole roles={['ceo', 'finance']}>
 *   <ApproveButton />
 * </RequireRole>
 */
export function RequireRole({ roles, children, fallback = null }: RequireRoleProps) {
  const { user, isLoading } = useAuth();

  if (isLoading) return null;
  if (!user || !roles.includes(user.role)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}

/**
 * 页面级权限守卫（用于 layout 或 page）
 * 
 * @example
 * export default function SettlementsPage() {
 *   return (
 *     <PageGuard>
 *       <SettlementsContent />
 *     </PageGuard>
 *   );
 * }
 */
export function PageGuard({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const pathname = usePathname();

  if (isLoading) {
    return <div>Loading...</div>; // 或使用 Skeleton
  }

  if (!user) {
    redirect('/login');
  }

  if (!hasPageAccess(pathname, user.role)) {
    redirect('/unauthorized');
  }

  return <>{children}</>;
}
```

---

## 第四章 状态常量 ⚠️ 待实现

> **SoT 来源**: STATE_MACHINE.md v2.6
>
> **注意**: 以下配置文件尚未创建，需要按此规范实现

### 4.1 日报状态（8 状态机）⚠️ 待实现

```typescript
// ⚠️ 待实现：src/config/status/daily-report-status.ts

/**
 * 日报状态枚举
 * SoT: STATE_MACHINE.md v2.6 §8
 */
export const DAILY_REPORT_STATUS = {
  RAW_SUBMITTED: 'raw_submitted',
  TREND_PENDING: 'trend_pending',
  TREND_OK: 'trend_ok',
  TREND_FLAGGED: 'trend_flagged',
  TREND_RESOLVED: 'trend_resolved',
  FINAL_PENDING: 'final_pending',
  FINAL_CONFIRMED: 'final_confirmed',
  FINAL_LOCKED: 'final_locked',
} as const;

export type DailyReportStatus = typeof DAILY_REPORT_STATUS[keyof typeof DAILY_REPORT_STATUS];

/**
 * 日报状态显示配置
 */
export const DAILY_REPORT_STATUS_CONFIG: Record<DailyReportStatus, {
  label: string;
  variant: 'default' | 'secondary' | 'success' | 'warning' | 'destructive';
  description: string;
}> = {
  raw_submitted: {
    label: '已提交',
    variant: 'default',
    description: '投手已提交 raw 数据',
  },
  trend_pending: {
    label: '趋势审核中',
    variant: 'secondary',
    description: '等待系统趋势风控检查',
  },
  trend_ok: {
    label: '趋势正常',
    variant: 'success',
    description: '趋势风控通过',
  },
  trend_flagged: {
    label: '异常标记',
    variant: 'warning',
    description: '趋势分析发现异常，需人工确认',
  },
  trend_resolved: {
    label: '异常已处理',
    variant: 'secondary',
    description: '异常已由主管确认处理',
  },
  final_pending: {
    label: '待确认',
    variant: 'secondary',
    description: '等待运营确认最终数据',
  },
  final_confirmed: {
    label: '已确认',
    variant: 'success',
    description: '最终数据已确认，可用于计费',
  },
  final_locked: {
    label: '已锁定',
    variant: 'default',
    description: '数据已锁定，不可修改',
  },
};

/**
 * 状态流转规则（Phase 1 简化版）
 * SoT: MASTER.md v4.4 §9 INV-003
 */
export const STATUS_TRANSITIONS: Record<DailyReportStatus, DailyReportStatus[]> = {
  raw_submitted: ['trend_pending'],
  trend_pending: ['trend_ok', 'trend_flagged'],
  trend_ok: ['final_pending'],
  trend_flagged: ['trend_resolved'],
  trend_resolved: ['final_pending'],
  final_pending: ['final_confirmed'],
  final_confirmed: ['final_locked'],
  final_locked: [], // 终态，不可流转
};
```

### 4.2 充值状态 ⚠️ 待实现

```typescript
// ⚠️ 待实现：src/config/status/topup-status.ts

/**
 * 充值请求状态
 * SoT: STATE_MACHINE.md
 */
export const TOPUP_STATUS = {
  DRAFT: 'draft',
  PENDING_FINANCE: 'pending_finance',
  PENDING_CEO: 'pending_ceo',
  APPROVED: 'approved',
  REJECTED: 'rejected',
  POSTED: 'posted',
} as const;

export type TopupStatus = typeof TOPUP_STATUS[keyof typeof TOPUP_STATUS];

export const TOPUP_STATUS_CONFIG: Record<TopupStatus, {
  label: string;
  variant: 'default' | 'secondary' | 'success' | 'warning' | 'destructive';
  nextAction?: string;
}> = {
  draft: {
    label: '草稿',
    variant: 'secondary',
    nextAction: '提交申请',
  },
  pending_finance: {
    label: '待财务审核',
    variant: 'warning',
    nextAction: '财务审核',
  },
  pending_ceo: {
    label: '待老板批准',
    variant: 'warning',
    nextAction: 'CEO 批准',
  },
  approved: {
    label: '已批准',
    variant: 'success',
    nextAction: '确认打款',
  },
  rejected: {
    label: '已拒绝',
    variant: 'destructive',
  },
  posted: {
    label: '已打款',
    variant: 'default',
  },
};
```

### 4.3 项目状态 ⚠️ 待实现

```typescript
// ⚠️ 待实现：src/config/status/project-status.ts

export const PROJECT_STATUS = {
  ACTIVE: 'active',
  PAUSED: 'paused',
  COMPLETED: 'completed',
  TERMINATED: 'terminated',
} as const;

export type ProjectStatus = typeof PROJECT_STATUS[keyof typeof PROJECT_STATUS];

export const PROJECT_STATUS_CONFIG: Record<ProjectStatus, {
  label: string;
  variant: 'default' | 'secondary' | 'success' | 'warning' | 'destructive';
}> = {
  active: { label: '进行中', variant: 'success' },
  paused: { label: '已暂停', variant: 'warning' },
  completed: { label: '已完成', variant: 'default' },
  terminated: { label: '已终止', variant: 'destructive' },
};
```

### 4.4 广告账户状态 ⚠️ 待实现

```typescript
// ⚠️ 待实现：src/config/status/ad-account-status.ts

/**
 * 广告账户状态
 * SoT: STATE_MACHINE.md §7.1 - 账户生命周期不可回溯
 */
export const AD_ACCOUNT_STATUS = {
  ACTIVE: 'active',
  RESTRICTED: 'restricted',
  DEAD: 'dead',
} as const;

export type AdAccountStatus = typeof AD_ACCOUNT_STATUS[keyof typeof AD_ACCOUNT_STATUS];

export const AD_ACCOUNT_STATUS_CONFIG: Record<AdAccountStatus, {
  label: string;
  variant: 'default' | 'secondary' | 'success' | 'warning' | 'destructive';
  description: string;
}> = {
  active: {
    label: '正常',
    variant: 'success',
    description: '账户正常运行中',
  },
  restricted: {
    label: '受限',
    variant: 'warning',
    description: '账户功能受限，可能需要申诉',
  },
  dead: {
    label: '死号',
    variant: 'destructive',
    description: '账户永久失效，不可恢复',
  },
};
```

---

## 第五章 Phase 配置 ⚠️ 待实现

> **SoT 来源**: MASTER.md v4.4 §3 - Phase 1 / Phase 2 执行边界
>
> **注意**: 以下配置文件尚未创建，需要按此规范实现

### 5.1 Phase 配置常量 ⚠️ 待实现

```typescript
// ⚠️ 待实现：src/config/phase.ts

/**
 * Phase 配置
 * SoT: MASTER.md v4.4 §3.4
 * 
 * Phase 1: 照亮阶段 - 记录事实、展示状态、提示异常，不强制阻断
 * Phase 2: 问责阶段 - 引入约束、强制审批、考核关联
 */
export const PHASE_CONFIG = {
  // 当前 Phase（从环境变量读取）
  CURRENT_PHASE: 1,

  // Phase 2 功能开关（默认全部关闭）
  PHASE2_FEATURES: {
    TOPUP_ENFORCEMENT: false,      // 充值强制审批（无批准不打款）
    DAILY_REPORT_REQUIRED: false,  // 日报必须审核
    WEEKLY_BRIEF_REQUIRED: false,  // 周报必须提交
    SETTLEMENT_LOCK: false,        // 结算锁定
    BUDGET_BLOCKING: false,        // 超预算阻断
  },
} as const;

/**
 * 检查 Phase 2 功能是否启用
 */
export function isPhase2Enabled(feature?: keyof typeof PHASE_CONFIG.PHASE2_FEATURES): boolean {
  if (PHASE_CONFIG.CURRENT_PHASE < 2) return false;
  if (!feature) return true;
  return PHASE_CONFIG.PHASE2_FEATURES[feature];
}
```

### 5.2 Phase 感知 Hook ⚠️ 待实现

```typescript
// ⚠️ 待实现：src/hooks/usePhaseConfig.ts

import { PHASE_CONFIG, isPhase2Enabled } from '@/config/phase';

/**
 * Phase 配置 Hook
 * 
 * @example
 * const { currentPhase, isPhase2, canBlock } = usePhaseConfig();
 * 
 * // Phase 1: 只提示，不阻断
 * if (hasWarning && !canBlock) {
 *   toast.warning('存在风险，建议关注');
 * }
 * 
 * // Phase 2: 可以阻断
 * if (hasWarning && canBlock) {
 *   return <BlockedMessage />;
 * }
 */
export function usePhaseConfig() {
  return {
    currentPhase: PHASE_CONFIG.CURRENT_PHASE,
    isPhase2: PHASE_CONFIG.CURRENT_PHASE >= 2,
    
    // Phase 2 功能检查
    canBlockTopup: isPhase2Enabled('TOPUP_ENFORCEMENT'),
    canRequireDailyReport: isPhase2Enabled('DAILY_REPORT_REQUIRED'),
    canRequireWeeklyBrief: isPhase2Enabled('WEEKLY_BRIEF_REQUIRED'),
    canLockSettlement: isPhase2Enabled('SETTLEMENT_LOCK'),
    canBlockBudget: isPhase2Enabled('BUDGET_BLOCKING'),
    
    // 通用检查
    isPhase2Enabled,
  };
}
```

---

## 第六章 Phase 1 规则

> **SoT 来源**: MASTER.md v4.4 §3 - Phase 1 照亮阶段

### 6.1 核心约束

```yaml
Phase1_原则:
  允许:
    - 记录事实
    - 展示状态
    - 提示异常（高亮警告）
    - 数据统计
    - 趋势分析

  禁止:
    - 自动阻断/拒绝/暂停/冻结
    - 自动惩罚（扣分、禁用账户）
    - 强制审批流程（可绕行）
    - 禁用按钮（仅因数据异常）
    - 必填强制（可为空）
```

### 6.2 异常展示（只高亮，不阻断）

```typescript
// ✅ Phase 1 正确做法：高亮 + 提示
import { cn } from '@/lib/utils';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { AlertTriangle } from 'lucide-react';

interface ValueDisplayProps {
  value: number;
  isAbnormal?: boolean;
  abnormalReason?: string;
}

function ValueDisplay({ value, isAbnormal, abnormalReason }: ValueDisplayProps) {
  return (
    <span className={cn(
      'tabular-nums',
      isAbnormal && 'text-red-600 bg-red-50 px-2 py-0.5 rounded'
    )}>
      {value.toLocaleString()}
      {isAbnormal && (
        <Tooltip>
          <TooltipTrigger asChild>
            <AlertTriangle className="inline h-4 w-4 ml-1 text-red-500" />
          </TooltipTrigger>
          <TooltipContent>
            <p>{abnormalReason || '数据异常，建议关注'}</p>
          </TooltipContent>
        </Tooltip>
      )}
    </span>
  );
}

// ❌ Phase 1 禁止：阻断操作
function BadExample({ isAbnormal }: { isAbnormal: boolean }) {
  if (isAbnormal) {
    return <Alert variant="destructive">无法提交，请先修正异常</Alert>;
  }
  // 这种写法阻断了用户操作，违反 Phase 1 原则
}
```

### 6.3 按钮状态（可点击，提交后提示警告）

```typescript
// ✅ Phase 1 正确做法：按钮可点击，提交后显示警告
import { toast } from 'sonner';
import { useMutation } from '@tanstack/react-query';

function SubmitButton({ data }: { data: FormData }) {
  const mutation = useMutation({
    mutationFn: submitData,
    onSuccess: (result) => {
      toast.success('提交成功');

      // 如果有警告，显示警告信息（但已成功提交）
      if (result.warnings?.length) {
        toast.warning('注意', {
          description: result.warnings.join('\n'),
          duration: 5000,
        });
      }
    },
  });

  return (
    <Button
      onClick={() => mutation.mutate(data)}
      disabled={mutation.isPending}  // ✅ 只在请求中禁用
    >
      提交
    </Button>
  );
}

// ❌ Phase 1 禁止：因数据异常禁用按钮
function BadButton({ hasWarnings }: { hasWarnings: boolean }) {
  return (
    <Button disabled={hasWarnings}>  {/* ❌ 禁止！不能因警告禁用 */}
      提交
    </Button>
  );
}
```

### 6.4 Phase 2 预留点

```typescript
// Phase 2 功能预留示例
import { usePhaseConfig } from '@/hooks/usePhaseConfig';

function ApprovalButton({ canApprove, hasWarnings }: Props) {
  const { canBlockTopup } = usePhaseConfig();

  // Phase 2: 强制审批，有警告时禁用
  if (canBlockTopup && hasWarnings) {
    return (
      <Button disabled>
        无法批准（存在未解决的警告）
      </Button>
    );
  }

  // Phase 1: 可点击，只提示
  return (
    <Button onClick={handleApprove}>
      批准
      {hasWarnings && (
        <Badge variant="warning" className="ml-2">有警告</Badge>
      )}
    </Button>
  );
}
```

### 6.5 表单验证（必填 vs 建议填）

```typescript
// ✅ Phase 1：关键字段必填，其他字段可选
const dailyReportSchema = z.object({
  // 必填字段（业务事实）
  project_id: z.string().min(1, '请选择项目'),
  date: z.string().min(1, '请选择日期'),
  conversions: z.number().min(0, '进粉数不能为负'),
  
  // 可选字段（Phase 1 不强制）
  spend: z.number().optional(),
  notes: z.string().optional(),
});

// ❌ Phase 1 禁止：所有字段都必填
const badSchema = z.object({
  project_id: z.string().min(1),
  date: z.string().min(1),
  conversions: z.number(),
  spend: z.number(),  // ❌ Phase 1 不应强制
  notes: z.string().min(1),  // ❌ Phase 1 不应强制
});
```

---

## 第七章 代码模板

> **AI 开发新功能时，复制以下模板**

### 7.1 列表页模板

```typescript
// src/app/(dashboard)/{resource}/page.tsx
'use client';

import { useQuery } from '@tanstack/react-query';
import { apiFetchPaginated, queryKeys } from '@/lib/api';
import { DataTable } from '@/components/ui/data-table';
import { PageTemplate } from '@/components/layout/page-template';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/data-state';
import { columns } from './columns';
import type { Resource } from '@/features/{resource}/types';

export default function ResourceListPage() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: queryKeys.resources.list(),
    queryFn: () => apiFetchPaginated<Resource>('/api/v1/resources'),
  });

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState error={error} onRetry={refetch} />;
  if (!data?.items.length) return <EmptyState message="暂无数据" />;

  return (
    <PageTemplate
      title="资源列表"
      subtitle="管理所有资源"  // ✅ 注意：使用 subtitle 而非 description
      actions={<CreateButton />}
    >
      <DataTable columns={columns} data={data.items} />
    </PageTemplate>
  );
}
```

### 7.2 详情页模板

```typescript
// src/app/(dashboard)/{resource}/[id]/page.tsx
'use client';

import { useQuery } from '@tanstack/react-query';
import { apiFetch, queryKeys } from '@/lib/api';
import { useParams } from 'next/navigation';
import { PageTemplate } from '@/components/layout/page-template';
import { LoadingState, ErrorState } from '@/components/ui/data-state';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import type { Resource } from '@/features/{resource}/types';

export default function ResourceDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: queryKeys.resources.detail(id),
    queryFn: () => apiFetch<Resource>(`/api/v1/resources/${id}`),
    enabled: !!id,
  });

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState error={error} onRetry={refetch} />;
  if (!data) return <ErrorState error="资源不存在" />;

  return (
    <PageTemplate
      title={data.name}
      backLink="/resources"
      actions={<EditButton id={id} />}
    >
      <Card>
        <CardHeader>
          <CardTitle>基本信息</CardTitle>
        </CardHeader>
        <CardContent>
          {/* 详情内容 */}
        </CardContent>
      </Card>
    </PageTemplate>
  );
}
```

### 7.3 表单页模板

```typescript
// src/app/(dashboard)/{resource}/create/page.tsx
'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { apiPost, queryKeys } from '@/lib/api';
import { PageTemplate } from '@/components/layout/page-template';
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { resourceSchema, type ResourceForm } from './schema';

export default function CreateResourcePage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const form = useForm<ResourceForm>({
    resolver: zodResolver(resourceSchema),
    defaultValues: {
      name: '',
    },
  });

  const mutation = useMutation({
    mutationFn: (data: ResourceForm) =>
      apiPost('/api/v1/resources', data),
    onSuccess: () => {
      toast.success('创建成功');
      queryClient.invalidateQueries({ queryKey: queryKeys.resources.list() });
      router.push('/resources');
    },
    onError: (error) => {
      toast.error('创建失败', { description: error.message });
    },
  });

  return (
    <PageTemplate title="创建资源" backLink="/resources">
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit((data) => mutation.mutate(data))}
          className="space-y-6 max-w-2xl"
        >
          <FormField
            control={form.control}
            name="name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>名称</FormLabel>
                <FormControl>
                  <Input placeholder="请输入名称" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <div className="flex gap-4">
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? '提交中...' : '创建'}
            </Button>
            <Button type="button" variant="outline" onClick={() => router.back()}>
              取消
            </Button>
          </div>
        </form>
      </Form>
    </PageTemplate>
  );
}
```

### 7.4 Feature 模块模板

```typescript
// src/features/{module}/types/{module}.types.ts
export interface Resource {
  id: string;
  name: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ResourceListParams {
  page?: number;
  page_size?: number;
  search?: string;
  status?: string;
}

// src/features/{module}/services/{module}Api.ts
import { apiFetch, apiFetchPaginated, apiPost, apiPatch, apiDelete } from '@/lib/api';
import type { Resource, ResourceListParams } from '../types';

export async function getResources(params: ResourceListParams = {}) {
  return apiFetchPaginated<Resource>('/api/v1/resources', { params });
}

export async function getResource(id: string) {
  return apiFetch<Resource>(`/api/v1/resources/${id}`);
}

export async function createResource(data: Partial<Resource>) {
  return apiPost<Resource>('/api/v1/resources', data);
}

export async function updateResource(id: string, data: Partial<Resource>) {
  return apiPatch<Resource>(`/api/v1/resources/${id}`, data);
}

export async function deleteResource(id: string) {
  return apiDelete(`/api/v1/resources/${id}`);
}

// src/features/{module}/hooks/use{Module}.ts
import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '@/lib/api';
import { getResources, getResource } from '../services';
import type { ResourceListParams } from '../types';

export function useResources(params: ResourceListParams = {}) {
  return useQuery({
    queryKey: queryKeys.resources.list(params),
    queryFn: () => getResources(params),
  });
}

export function useResource(id: string) {
  return useQuery({
    queryKey: queryKeys.resources.detail(id),
    queryFn: () => getResource(id),
    enabled: !!id,
  });
}
```

---

## 第八章 AI 开发检查清单

> **AI 在开发任何新功能前，必须执行以下检查**

```markdown
## 开发前检查

□ 1. 扫描现有代码，是否有可复用的？
     命令: 搜索 features/ 和 components/ 目录
     目标: 找到相似的组件、hooks、服务

□ 2. 是否有相似页面可以复制？
     命令: 查看 app/(dashboard)/ 下的页面
     目标: 找到结构相似的页面作为模板

□ 3. 是否需要新建组件？
     判断: 90% 情况不需要，用 shadcn 组合即可
     如需新建: 放在 features/{module}/components/

□ 4. 是否需要新建 hook？
     命令: 检查 features/*/hooks/ 是否已有
     目标: 复用现有 hook 或参考结构新建

□ 5. API 调用是否使用 lib/api.ts？
     检查: 必须使用 apiFetch / queryKeys
     禁止: 直接使用 fetch / axios

□ 6. 权限是否符合 PAGE_ACCESS 定义？
     对照: 第三章权限矩阵
     使用: useRequireRole hook

□ 7. 项目级权限是否使用 useProjectAccess？
     场景: 检查 project_members.project_role
     使用: useProjectAccess({ projectId, requiredRole: 'owner' })

□ 8. 是否遵守 Phase 1 规则？
     原则: 只高亮不阻断，只提示不禁用
     检查: 没有 disabled={hasWarnings} 这类代码

□ 9. 状态常量是否使用 config/status/？
     检查: 日报/充值/项目状态使用统一常量
     禁止: 硬编码状态字符串

□ 10. 类型定义是否完整？
      位置: features/{module}/types/
      检查: 无 any 类型，与后端响应一致

□ 11. 角色映射是否正确？
      检查: 后端 data_operator → 前端 supervisor
      使用: normalizeRole() 函数
```

---

## 附录 A：快速复制代码库

### A.1 API 调用

```typescript
import { apiFetch, apiFetchPaginated, apiPost, queryKeys } from '@/lib/api';

// GET 单个
const user = await apiFetch<User>('/api/v1/users/me');

// GET 列表（分页）
const { items, total } = await apiFetchPaginated<Project>('/api/v1/projects');

// POST
const result = await apiPost<Project>('/api/v1/projects', { name: 'New' });

// Query Key
const queryKey = queryKeys.projects.list({ page: 1 });
```

### A.2 权限检查

```typescript
import { useAuth, useRequireRole } from '@/features/auth/hooks/useAuth';
import { useProjectAccess } from '@/features/projects/hooks/useProjectAccess';

// 获取当前用户
const { user, isAuthenticated, isLoading } = useAuth();

// 角色守卫
const { hasAccess } = useRequireRole(['ceo', 'finance']);
if (!hasAccess) return <Unauthorized />;

// 项目级权限
const { isProjectOwner } = useProjectAccess({ projectId: '123' });

// 条件渲染
{user?.role === 'ceo' && <AdminPanel />}
```

### A.3 角色映射

```typescript
import { normalizeRole, toBackendRole, ROLE_LABELS } from '@/config/role-mapping';

// 后端角色 → 前端角色
const frontendRole = normalizeRole('data_operator'); // 'supervisor'

// 前端角色 → 后端角色
const backendRole = toBackendRole('pitcher'); // 'media_buyer'

// 显示中文
const label = ROLE_LABELS[user.role]; // '主管'
```

### A.4 状态显示

```typescript
import { StatusBadge } from '@/components/ui/StatusBadge';
import { DAILY_REPORT_STATUS_CONFIG } from '@/config/status/daily-report-status';

function ReportStatusBadge({ status }: { status: string }) {
  const config = DAILY_REPORT_STATUS_CONFIG[status];
  return (
    <StatusBadge variant={config.variant}>
      {config.label}
    </StatusBadge>
  );
}
```

### A.5 Phase 感知

```typescript
import { usePhaseConfig } from '@/hooks/usePhaseConfig';

const { isPhase2, canBlockTopup } = usePhaseConfig();

// Phase 1: 提示
if (!isPhase2 && hasWarning) {
  toast.warning('存在风险，建议关注');
}

// Phase 2: 阻断
if (canBlockTopup && hasWarning) {
  return <BlockedMessage />;
}
```

### A.6 表格

```typescript
import { DataTable } from '@/components/ui/data-table';
import type { ColumnDef } from '@tanstack/react-table';

const columns: ColumnDef<Item>[] = [
  { accessorKey: 'name', header: '名称' },
  { accessorKey: 'status', header: '状态' },
];

<DataTable columns={columns} data={items} />
```

### A.7 表单

```typescript
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from '@/components/ui/form';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

const form = useForm({ resolver: zodResolver(schema) });

<Form {...form}>
  <form onSubmit={form.handleSubmit(onSubmit)}>
    <FormField
      control={form.control}
      name="field"
      render={({ field }) => (
        <FormItem>
          <FormLabel>标签</FormLabel>
          <FormControl>
            <Input {...field} />
          </FormControl>
          <FormMessage />
        </FormItem>
      )}
    />
  </form>
</Form>
```

### A.8 弹窗

```typescript
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';

<Dialog>
  <DialogTrigger asChild>
    <Button>打开</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>标题</DialogTitle>
    </DialogHeader>
    {/* 内容 */}
  </DialogContent>
</Dialog>
```

### A.9 状态展示

```typescript
import { LoadingState, EmptyState, ErrorState } from '@/components/ui/data-state';

if (isLoading) return <LoadingState />;
if (error) return <ErrorState error={error} onRetry={refetch} />;
if (!data?.length) return <EmptyState message="暂无数据" />;
```

### A.10 提示消息

```typescript
import { toast } from 'sonner';

toast.success('操作成功');
toast.error('操作失败', { description: error.message });
toast.warning('注意', { description: '存在异常数据' });
```

---

## 附录 B：API 端点清单

> **与后端 API 对应的端点常量**

```typescript
// src/config/api-endpoints.ts

export const API_ENDPOINTS = {
  // 认证
  AUTH: {
    ME: '/api/v1/users/me',
    LOGIN: '/api/v1/auth/login',
    LOGOUT: '/api/v1/auth/logout',
  },

  // 日报
  DAILY_REPORTS: {
    LIST: '/api/v1/daily-reports',
    DETAIL: (id: string) => `/api/v1/daily-reports/${id}`,
    SUBMIT: '/api/v1/daily-reports',
    REVIEW: (id: string) => `/api/v1/daily-reports/${id}/review`,
  },

  // 项目
  PROJECTS: {
    LIST: '/api/v1/projects',
    DETAIL: (id: string) => `/api/v1/projects/${id}`,
    PNL: (id: string) => `/api/v1/projects/${id}/pnl`,
    MEMBERS: (id: string) => `/api/v1/projects/${id}/members`,
  },

  // 充值
  TOPUPS: {
    LIST: '/api/v1/topups',
    DETAIL: (id: string) => `/api/v1/topups/${id}`,
    REQUEST: '/api/v1/topups/request',
    APPROVE: (id: string) => `/api/v1/topups/${id}/approve`,
  },

  // Dashboard
  DASHBOARD: {
    CEO_SUMMARY: '/api/v1/dashboards/ceo/summary',
    FUND_OVERVIEW: '/api/v1/dashboards/fund-overview',
  },
} as const;
```

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-23 | 初始版本，对齐 MASTER.md v4.4 |
| v1.1 | 2025-12-23 | P0 修复：权限矩阵对齐、角色映射、project_members、状态常量、Phase 预留 |
| v1.2 | 2025-12-23 | AI 代码工厂审查修复：对齐实际代码库，标注待实现功能 |

---

**v1.2 变更摘要**（AI 代码工厂审查修复）：
- §1.1 标注 `config/` 目录为「待实现」
- §1.2.2 标注 `useProjectAccess` 为「待实现」
- §3.1 对齐实际代码 UserRole 枚举（DATA_OPERATOR, MEDIA_BUYER），添加角色映射表
- §3.2-3.5 标注 role-mapping.ts, permissions.ts, useProjectAccess.ts, RequireRole.tsx 为「待实现」
- §4 标注所有 status 配置文件为「待实现」
- §5 标注 phase.ts, usePhaseConfig.ts 为「待实现」
- §7.1 修复 PageTemplate props（description → subtitle）
- 添加文档状态说明

**v1.1 变更摘要**：
- §3.2 新增角色映射（data_operator ↔ supervisor, media_buyer ↔ pitcher）
- §3.3 修正页面权限矩阵（驾驶舱仅 CEO、结算仅 CEO+财务）
- §3.4 新增项目级权限 useProjectAccess（基于 project_members.project_role）
- §4 新增状态常量（日报 8 状态、充值状态、项目状态、账户状态）
- §5 新增 Phase 配置（usePhaseConfig hook、Phase 2 功能预留）
- §6.4 新增 Phase 2 预留点示例
- 附录 B 新增 API 端点清单

---

**文档维护者**: AI 编程助手
**生效范围**: 所有前端开发任务
**SoT 对齐**: MASTER.md v4.4, PROJECT.md v1.3
