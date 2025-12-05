---
version: v1.0
status: active
layer: dev-guide
owner: wade
last_reviewed: 2025-12-05
baseline: MASTER.md v3.5, FRONTEND_STYLE_GUIDE v2.3
---

# FRONTEND_MODULE_SHELL_PATTERN_v1.0

> **面向对象**: 前端工程师 + FE Agent
>
> **定位**: 定义前端模块的标准目录结构和 Shell 组件模式

---

## 1. 概述

### 1.1 设计目标

- **职责分离**: page.tsx 仅作入口，业务逻辑封装在模块层
- **可复用性**: Shell 组件可在不同上下文中复用
- **可测试性**: hooks 和组件独立，便于单元测试
- **一致性**: 所有模块遵循相同结构，降低认知成本

### 1.2 权威示例

本文档以 `Dashboard` 模块作为权威参考实现：

```
frontend/
├── app/dashboard/page.tsx              # 页面入口（编排层）
└── src/modules/dashboard/
    ├── index.ts                        # 模块导出
    ├── DashboardShell.tsx              # Shell 组件
    ├── components/                     # UI 组件
    ├── hooks/                          # 数据与状态 hooks
    ├── types/                          # TypeScript 类型
    └── data/                           # Mock 数据（可选）
```

---

## 2. 目录结构规范

### 2.1 标准模块结构

```
src/modules/{module-name}/
├── index.ts                     # 模块统一导出
├── {ModuleName}Shell.tsx        # Shell 组件（可选，复杂页面推荐）
├── components/
│   ├── index.ts                 # 组件导出
│   ├── {ModuleName}Header.tsx   # 页面头部
│   ├── {ModuleName}KpiRow.tsx   # KPI 指标区（如适用）
│   ├── {ModuleName}DataTable.tsx # 数据表格
│   └── ...                      # 其他业务组件
├── hooks/
│   ├── index.ts                 # hooks 导出
│   ├── use{ModuleName}Filters.ts # 筛选状态管理
│   └── use{ModuleName}Data.ts    # 数据获取
├── types/
│   └── index.ts                 # 类型定义
└── data/
    └── mock-data.ts             # Mock 数据（开发阶段）
```

### 2.2 页面入口结构

```
app/dashboard/{module-name}/
├── page.tsx                     # 页面入口
├── [id]/
│   └── page.tsx                 # 详情页入口
└── new/
    └── page.tsx                 # 新建页入口
```

---

## 3. 职责边界

### 3.1 各层职责定义

| 层级 | 文件 | 职责 | 禁止事项 |
|------|------|------|----------|
| **页面层** | `app/.../page.tsx` | 渲染 PageContainer + Shell | 业务逻辑、数据获取、事件处理 |
| **Shell 层** | `{ModuleName}Shell.tsx` | 组合 hooks 和组件、事件处理、状态编排 | 直接操作 DOM、定义类型 |
| **Hooks 层** | `use{ModuleName}*.ts` | 数据获取、状态管理、派生计算 | UI 渲染、路由操作 |
| **组件层** | `components/*.tsx` | 纯 UI 渲染、接收 props | 数据获取、全局状态访问 |
| **类型层** | `types/index.ts` | TypeScript 类型定义 | 业务逻辑、运行时代码 |

### 3.2 数据流向

```
┌─────────────────────────────────────────────────────────────┐
│  page.tsx                                                    │
│  └── PageContainer                                           │
│      └── {ModuleName}Shell                                   │
│          ├── use{ModuleName}Filters() ──┐                   │
│          │                               │ filters          │
│          ├── use{ModuleName}Data(filters) ◄─┘               │
│          │   └── { data, loading, error, refresh }          │
│          │                                                   │
│          └── 组件渲染 (props 传递)                           │
│              ├── Header(filters, onFilterChange)            │
│              ├── KpiRow(metrics)                            │
│              ├── DataTable(data, onRowClick)                │
│              └── ...                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. 代码模板

### 4.1 页面入口模板

```tsx
// app/dashboard/{module-name}/page.tsx

/**
 * {ModuleName} 页面
 *
 * 职责：页面级外壳 + 渲染 Shell
 */

'use client';

import PageContainer from '@/components/layout/page-container';
import { {ModuleName}Shell } from '@/modules/{module-name}';

export default function {ModuleName}Page() {
  return (
    <div className="min-h-screen bg-shell text-text-body antialiased">
      <PageContainer>
        <{ModuleName}Shell />
      </PageContainer>
    </div>
  );
}
```

### 4.2 Shell 组件模板

```tsx
// src/modules/{module-name}/{ModuleName}Shell.tsx

/**
 * {ModuleName}Shell - 模块级 Shell 组件
 *
 * 职责：整合 hooks 和组件、处理事件、状态编排
 */

'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  {ModuleName}Header,
  {ModuleName}KpiRow,
  {ModuleName}DataTable,
} from './components';
import { use{ModuleName}Filters, use{ModuleName}Data } from './hooks';

export interface {ModuleName}ShellProps {
  className?: string;
}

export function {ModuleName}Shell({ className }: {ModuleName}ShellProps) {
  const router = useRouter();

  // 筛选状态
  const {
    filters,
    setFilters,
    // ...其他筛选方法
  } = use{ModuleName}Filters();

  // 数据获取
  const {
    data,
    loading,
    error,
    refresh,
  } = use{ModuleName}Data(filters);

  // 事件处理
  const handleRowClick = (item: ItemType) => {
    router.push(`/dashboard/{module-name}/${item.id}`);
  };

  // 加载状态
  if (loading && !data.items.length) {
    return (
      <div className="flex items-center justify-center min-h-[400px] text-text-muted">
        <Loader2 className="w-8 h-8 animate-spin mr-2" />
        正在加载数据...
      </div>
    );
  }

  // 错误状态
  if (error && !data.items.length) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <p className="text-danger mb-4">{error.message}</p>
        <Button onClick={refresh}>重新加载</Button>
      </div>
    );
  }

  // 主渲染
  return (
    <div className={className}>
      <div className="flex flex-col gap-6 w-full py-6">
        <{ModuleName}Header
          filters={filters}
          onFilterChange={setFilters}
          onRefresh={refresh}
          loading={loading}
        />
        <{ModuleName}KpiRow metrics={data.metrics} />
        <{ModuleName}DataTable
          data={data.items}
          onRowClick={handleRowClick}
        />
      </div>
    </div>
  );
}

export default {ModuleName}Shell;
```

### 4.3 Hooks 模板

#### 筛选状态 Hook

```tsx
// src/modules/{module-name}/hooks/use{ModuleName}Filters.ts

'use client';

import { useState, useCallback, useMemo } from 'react';
import type { {ModuleName}FiltersState } from '../types';

const DEFAULT_FILTERS: {ModuleName}FiltersState = {
  dateRange: '7d',
  status: undefined,
  search: undefined,
};

export function use{ModuleName}Filters(initialFilters = {}) {
  const [filters, setFilters] = useState<{ModuleName}FiltersState>({
    ...DEFAULT_FILTERS,
    ...initialFilters,
  });

  const updateFilter = useCallback(<K extends keyof {ModuleName}FiltersState>(
    key: K,
    value: {ModuleName}FiltersState[K]
  ) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  }, []);

  const resetFilters = useCallback(() => {
    setFilters(DEFAULT_FILTERS);
  }, []);

  const hasActiveFilters = useMemo(() => {
    return Object.entries(filters).some(
      ([key, value]) => value !== DEFAULT_FILTERS[key as keyof typeof DEFAULT_FILTERS]
    );
  }, [filters]);

  return {
    filters,
    setFilters,
    updateFilter,
    resetFilters,
    hasActiveFilters,
  };
}
```

#### 数据获取 Hook

```tsx
// src/modules/{module-name}/hooks/use{ModuleName}Data.ts

'use client';

import { useState, useCallback, useEffect } from 'react';
import type { {ModuleName}FiltersState, {ModuleName}DataState } from '../types';

export type DataStatus = 'idle' | 'loading' | 'success' | 'error';

const DEFAULT_DATA: {ModuleName}DataState = {
  items: [],
  metrics: { /* ... */ },
};

export function use{ModuleName}Data(filters: {ModuleName}FiltersState) {
  const [data, setData] = useState<{ModuleName}DataState>(DEFAULT_DATA);
  const [status, setStatus] = useState<DataStatus>('idle');
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setStatus('loading');
    setError(null);

    try {
      // TODO: 替换为真实 API
      await new Promise(resolve => setTimeout(resolve, 500));
      setData({ /* mock or API data */ });
      setStatus('success');
    } catch (err) {
      setError(err instanceof Error ? err : new Error('加载失败'));
      setStatus('error');
    }
  }, [filters]);

  const refresh = useCallback(async () => {
    await fetchData();
  }, [fetchData]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    status,
    loading: status === 'loading',
    error,
    refresh,
  };
}
```

### 4.4 模块导出模板

```tsx
// src/modules/{module-name}/index.ts

/**
 * {ModuleName} 模块入口
 */

// Shell 组件
export { {ModuleName}Shell } from './{ModuleName}Shell';
export type { {ModuleName}ShellProps } from './{ModuleName}Shell';

// Components
export * from './components';

// Hooks
export * from './hooks';

// Types
export * from './types';
```

---

## 5. 新模块开发流程

以 `topup`（充值管理）模块为例：

### 步骤 1：创建目录结构

```bash
mkdir -p src/modules/topup/{components,hooks,types,data}
touch src/modules/topup/index.ts
touch src/modules/topup/TopupShell.tsx
touch src/modules/topup/components/index.ts
touch src/modules/topup/hooks/index.ts
touch src/modules/topup/types/index.ts
```

### 步骤 2：定义类型

```tsx
// src/modules/topup/types/index.ts

export interface TopupFiltersState {
  dateRange: '7d' | '30d' | '90d' | 'custom';
  status?: 'pending' | 'approved' | 'rejected';
  search?: string;
}

export interface TopupRequest {
  id: string;
  amount: number;
  status: string;
  // ...
}

export interface TopupDataState {
  items: TopupRequest[];
  summary: TopupSummary;
}
```

### 步骤 3：实现 Hooks

```tsx
// src/modules/topup/hooks/useTopupFilters.ts
// src/modules/topup/hooks/useTopupData.ts
// src/modules/topup/hooks/index.ts
```

### 步骤 4：实现组件

```tsx
// src/modules/topup/components/TopupHeader.tsx
// src/modules/topup/components/TopupKpiRow.tsx
// src/modules/topup/components/TopupDataTable.tsx
// src/modules/topup/components/index.ts
```

### 步骤 5：实现 Shell

```tsx
// src/modules/topup/TopupShell.tsx
```

### 步骤 6：配置模块导出

```tsx
// src/modules/topup/index.ts
export { TopupShell } from './TopupShell';
export * from './components';
export * from './hooks';
export * from './types';
```

### 步骤 7：创建页面入口

```tsx
// app/dashboard/topup/page.tsx
'use client';

import PageContainer from '@/components/layout/page-container';
import { TopupShell } from '@/modules/topup';

export default function TopupPage() {
  return (
    <div className="min-h-screen bg-shell text-text-body antialiased">
      <PageContainer>
        <TopupShell />
      </PageContainer>
    </div>
  );
}
```

### 步骤 8：验证

```bash
cd frontend
pnpm lint
pnpm type-check
pnpm dev  # 访问 /dashboard/topup 验证
```

---

## 6. 命名规范

### 6.1 文件命名

| 类型 | 命名格式 | 示例 |
|------|----------|------|
| Shell 组件 | `{ModuleName}Shell.tsx` | `DashboardShell.tsx` |
| Header 组件 | `{ModuleName}Header.tsx` | `DashboardHeader.tsx` |
| KPI 组件 | `{ModuleName}KpiRow.tsx` | `DashboardKpiRow.tsx` |
| 表格组件 | `{ModuleName}DataTable.tsx` | `TopupDataTable.tsx` |
| 筛选 Hook | `use{ModuleName}Filters.ts` | `useDashboardFilters.ts` |
| 数据 Hook | `use{ModuleName}Data.ts` | `useDashboardData.ts` |

### 6.2 导出命名

| 类型 | 命名格式 | 示例 |
|------|----------|------|
| Shell 组件 | `{ModuleName}Shell` | `DashboardShell` |
| Props 类型 | `{ModuleName}ShellProps` | `DashboardShellProps` |
| 筛选状态类型 | `{ModuleName}FiltersState` | `DashboardFiltersState` |
| 数据状态类型 | `{ModuleName}DataState` | `DashboardDataState` |

---

## 7. 检查清单

### 7.1 新模块自检

- [ ] 目录结构符合 2.1 节规范
- [ ] page.tsx 仅包含 PageContainer + Shell
- [ ] Shell 组件不直接操作 DOM
- [ ] Hooks 不包含 UI 渲染逻辑
- [ ] 组件通过 props 接收数据
- [ ] 类型定义完整，无 `any`
- [ ] 导出文件配置正确
- [ ] 通过 `pnpm lint` 和 `pnpm type-check`

### 7.2 Code Review 检查点

- [ ] 职责边界是否清晰
- [ ] 数据流是否单向
- [ ] 事件处理是否在 Shell 层
- [ ] 组件是否可独立测试
- [ ] 命名是否符合规范

---

## 附录 A：Dashboard 模块完整结构

```
src/modules/dashboard/
├── index.ts                           # 模块导出
├── DashboardShell.tsx                 # Shell 组件 (~190 行)
├── components/
│   ├── index.ts
│   ├── DashboardHeader.tsx            # 头部 + 筛选器
│   ├── DashboardKpiRow.tsx            # KPI 指标行
│   ├── DashboardTrendSection.tsx      # 趋势图表
│   ├── DashboardRiskPanel.tsx         # 风险预警
│   ├── DashboardTodayTasks.tsx        # 今日待办
│   └── DashboardFundsOverview.tsx     # 资金概览
├── hooks/
│   ├── index.ts
│   ├── useDashboardFilters.ts         # 筛选状态
│   └── useDashboardData.ts            # 数据获取
├── types/
│   └── index.ts                       # 类型定义
└── data/
    └── mock-data.ts                   # Mock 数据

app/dashboard/
└── page.tsx                           # 页面入口 (~24 行)
```

---

## 变更记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0 | 2025-12-05 | 初版发布，基于 Dashboard 模块实现 |
