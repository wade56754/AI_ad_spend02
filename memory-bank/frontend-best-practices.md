# AI 广告代投管理系统 - 前端最佳实践

> **版本**: v1.0
> **更新日期**: 2026-01-05
> **核心原则**: SoT 驱动 + 防幻觉 + 小步验证 + 模式复用

---

## 1. 架构模式

### 1.1 Feature-First 模块化架构

```
frontend/src/
├── app/                    # Next.js App Router (薄壳层)
│   └── (dashboard)/        # 只做路由映射，不含业务逻辑
│
├── features/               # 核心：功能模块
│   ├── {module}/
│   │   ├── components/     # 业务组件
│   │   ├── hooks/          # React Query Hooks
│   │   ├── services/       # API 调用
│   │   ├── types/          # 类型定义
│   │   └── index.ts        # 模块导出
│   └── ...
│
├── components/
│   ├── ui/                 # shadcn/ui 组件 (54+)
│   ├── layout/             # 布局组件
│   └── shared/             # 共享业务组件
│
├── hooks/                  # 全局 Hooks
├── lib/                    # 工具库 (api.ts 核心)
└── types/                  # 全局类型
```

### 1.2 薄壳页面模式

```typescript
// app/(dashboard)/daily-reports/page.tsx
// 页面文件只做路由映射
import { DailyReportsPage } from '@/features/daily-reports';

export default function Page() {
  return <DailyReportsPage />;
}
```

---

## 2. 技术栈约束（不可变更）

| 层级 | 技术 | 备注 |
|------|------|------|
| 框架 | Next.js 16 (App Router) | strict mode |
| 服务端状态 | TanStack Query v5 | 替代 Redux |
| URL 状态 | nuqs / useSearchParams | 表格筛选 |
| UI 组件 | shadcn/ui + Tailwind | 禁止手写 |
| 表单 | react-hook-form + zod | 验证必须 |
| HTTP | `apiFetch` (@/lib/api.ts) | **禁止 fetch/axios** |
| 通知 | sonner (toast) | 统一反馈 |

---

## 3. 四层分离模式

### Layer 1: Types（类型定义）

```typescript
// features/{module}/types/{module}.types.ts

// SoT: STATE_MACHINE.md v2.8 §2
export type DailyReportStatus =
  | 'raw_submitted'   // Phase 1
  | 'trend_ok'        // Phase 1
  | 'final_confirmed'; // Phase 1

export interface DailyReport {
  id: string;
  report_date: string;
  status: DailyReportStatus;
  ad_spend: number;
  conversions: number;
}

export interface DailyReportListParams {
  page?: number;
  page_size?: number;
  status?: DailyReportStatus;
}
```

### Layer 2: Services（API 调用）

```typescript
// features/{module}/services/{module}Api.ts
import { apiGet, apiPost } from '@/lib/api';

const BASE_PATH = '/api/v1/daily-reports';

export async function getDailyReports(params: DailyReportListParams = {}) {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', String(params.page));
  if (params.status) searchParams.set('status', params.status);

  return apiGet<PaginatedResponse<DailyReport>>(`${BASE_PATH}?${searchParams}`);
}

export async function approveDailyReport(id: string): Promise<DailyReport> {
  return apiPost<DailyReport>(`${BASE_PATH}/${id}/approve`);
}
```

### Layer 3: Hooks（React Query）

```typescript
// features/{module}/hooks/useDailyReports.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Query Hook 标准模式
export function useDailyReports(params: DailyReportListParams = {}) {
  return useQuery({
    queryKey: ['daily-reports', params],
    queryFn: () => getDailyReports(params),
    staleTime: 2 * 60 * 1000,  // 2分钟新鲜期
  });
}

// Mutation Hook 标准模式
export function useApproveDailyReport() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: approveDailyReport,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['daily-reports'] });
      toast.success('审核通过');
    },
    onError: (error: ApiError) => {
      toast.error(error.message || '操作失败');
    },
  });
}
```

### Layer 4: Components（UI 组件）

```typescript
// features/{module}/components/{Module}Page.tsx
'use client';  // 必须：交互页面第一行

import { useState } from 'react';
import { DataTable } from '@/components/ui/data-table';
import { Button } from '@/components/ui/button';
import { useTableParams } from '@/hooks';
import { useDailyReports } from '../hooks';
import { columns } from './columns';

export function DailyReportsPage() {
  // 1. URL 状态管理
  const { params, setParams } = useTableParams();

  // 2. 数据获取
  const { data, isLoading } = useDailyReports(params);

  // 3. 本地状态
  const [dialogOpen, setDialogOpen] = useState(false);

  // 4. 渲染
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">日报管理</h1>
        <Button onClick={() => setDialogOpen(true)}>新建</Button>
      </div>

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        loading={isLoading}
        pagination={{
          page: params.page ?? 1,
          pageSize: params.page_size ?? 20,
          total: data?.total ?? 0,
          onPageChange: (page) => setParams({ page }),
        }}
      />
    </div>
  );
}
```

---

## 4. 表单处理模式

```typescript
// react-hook-form + zod 验证
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

// 1. 定义 Schema
const schema = z.object({
  name: z.string().min(1, '名称不能为空').max(100),
  amount: z.number().min(0, '金额必须大于0'),
  status: z.enum(['draft', 'active']),
});

type FormValues = z.infer<typeof schema>;

// 2. 使用表单
const form = useForm<FormValues>({
  resolver: zodResolver(schema),
  defaultValues: { name: '', amount: 0, status: 'draft' },
});

// 3. 渲染表单
<Form {...form}>
  <form onSubmit={form.handleSubmit(onSubmit)}>
    <FormField
      control={form.control}
      name="name"
      render={({ field }) => (
        <FormItem>
          <FormLabel>名称</FormLabel>
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

---

## 5. 必须使用的组件

| 场景 | 必须用 | 禁止用 |
|------|--------|--------|
| 数据列表 | `DataTable` | 手写 `<table>` |
| 状态标签 | `StatusBadge` | 手写 span/badge |
| 表单 | `Form` + `FormField` | 原生 form |
| 弹窗 | `Dialog` / `AlertDialog` | 手写 modal |
| 按钮 | `Button` | 原生 button |
| 输入 | `Input` | 原生 input |
| 通知 | `toast` (sonner) | alert() |

---

## 6. SoT 驱动开发

### 6.1 代码来源标注

```typescript
// SoT: STATE_MACHINE.md v2.8 §2
type DailyReportStatus = 'raw_submitted' | 'trend_ok' | 'final_confirmed';

// SoT: MASTER.md v4.6 §INV-007 - 技术层角色 (4 个)
type TechRole = 'admin' | 'finance' | 'media_buyer' | 'account_manager';
```

### 6.2 开发前必查 SoT

| 开发场景 | 必查文档 |
|----------|---------|
| 显示状态标签 | STATE_MACHINE.md |
| 权限控制 | MASTER.md §INV-007 |
| API 调用 | API_SOT.md |
| 表单字段 | DATA_SCHEMA.md |
| 错误提示 | ERROR_CODES.md |

---

## 7. 禁止事项清单（铁律）

| 编号 | 禁止 | 正确做法 |
|------|------|----------|
| F-001 | `role === 'supervisor'` | `is_project_owner === true` |
| F-002 | Phase 2 日报状态 | 只用 3 个 Phase 1 状态 |
| F-003 | 手写 `<table>` | 使用 `DataTable` |
| F-004 | 直接 `fetch()` | 使用 `apiGet/apiPost` |
| F-005 | 手写 HTML 标签 | 使用 shadcn/ui |
| F-006 | 缺少 `'use client'` | 交互页面第一行加 |
| F-009 | 充值强制老板审批 | 日常充值不需要 |

### 5 秒扫描检查

```bash
# 必须无结果
grep -r "supervisor" frontend/src/
grep -r "data_operator" frontend/src/
grep -r "fetch\(" frontend/src/ | grep -v "lib/api"
```

---

## 8. Phase 1 原则

> **核心原则：只提示、不阻断**

```typescript
// 错误：自动阻断
if (overBudget) {
  toast.error('超预算，操作被拒绝');
  return;  // 阻断
}

// 正确：Phase 1 只提示
if (overBudget) {
  toast.warning('提示：已超预算 30%');
  // 继续执行，不阻断
}
```

---

## 9. 质量门禁

### 每次提交前

```bash
# 1. TypeScript 检查
npx tsc --noEmit          # 必须 0 errors

# 2. ESLint 检查
npm run lint              # 必须 0 errors

# 3. 构建检查
npm run build             # 必须成功
```

### 代码审查清单

- [ ] 第一行是否为 'use client' (交互页面)
- [ ] 无 supervisor/data_operator 角色
- [ ] 无 Phase 2 日报状态
- [ ] 无手写 table/fetch
- [ ] 使用 shadcn/ui 组件
- [ ] 有 SoT 来源标注
- [ ] toast 通知完整 (成功/失败)

---

## 10. 快速参考

### 角色白名单

```typescript
// 技术层角色 (4 个) - 数据库 CHECK 约束
type TechRole = 'admin' | 'finance' | 'media_buyer' | 'account_manager';

// 业务属性判断
if (user.is_project_owner === true) { ... }

// 禁止: supervisor, data_operator, pitcher(作为role), project_owner(作为role)
```

### Phase 1 日报状态

```typescript
// 只有 3 个状态
type Phase1ReportStatus = 'raw_submitted' | 'trend_ok' | 'final_confirmed';

// 流转：raw_submitted → trend_ok → final_confirmed
```

### 关键文件

| 用途 | 文件路径 |
|------|---------|
| API 客户端 | `lib/api.ts` |
| 表格 URL 状态 | `hooks/use-table-params.ts` |
| 状态标签 | `components/ui/StatusBadge.tsx` |
| 数据表格 | `components/ui/data-table/` |

---

## 11. 导入顺序规范

```typescript
// 1. React/Next.js 核心
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

// 2. 第三方库
import { useQuery, useMutation } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

// 3. Icons
import { Plus, Pencil, Trash } from 'lucide-react';

// 4. UI 组件
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

// 5. 布局/共享组件
import { PageContainer } from '@/components/layout';
import { StatusBadge } from '@/components/shared';

// 6. Feature 内部导入
import { use{Module}s } from '../hooks';
import { columns } from './columns';

// 7. 类型
import type { {Module} } from '../types';

// 8. 常量/工具
import { formatMoney } from '@/lib/format';
```

---

## 12. 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 页面组件 | PascalCase + Page | `DailyReportsPage.tsx` |
| 表格组件 | PascalCase + Table | `DailyReportsTable.tsx` |
| 弹窗组件 | PascalCase + Dialog | `CreateReportDialog.tsx` |
| 列定义 | columns | `columns.tsx` |
| Query Hook | use + 复数 | `useDailyReports.ts` |
| Mutation Hook | use + 动词 + 名词 | `useCreateReport.ts` |
| Service 文件 | camelCase + Api | `dailyReportsApi.ts` |
| 类型文件 | camelCase + .types | `dailyReport.types.ts` |

---

## 相关文档

- [技术栈](./tech-stack.md)
- [架构说明](./architecture.md)
- [前端开发指南](../docs/guides/FRONTEND_DEVELOPMENT_GUIDE_v3.0.md)
- [AI 编程最佳实践](../docs/guides/FRONTEND_AI_PROGRAMMING_BEST_PRACTICES_v1.2.md)
