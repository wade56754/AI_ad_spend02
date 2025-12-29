# AI 广告代投系统 - 前端 AI 编程最佳实践

> **版本**: v1.1
> **更新日期**: 2025-12-29
> **变更记录**: 修复角色定义与 auth.types.ts 对齐，统一术语
> **适用范围**: `frontend/` 目录下所有代码的 AI 辅助开发
> **核心原则**: SoT 驱动 + 防幻觉 + 小步验证 + 模式复用

---

## 目录

1. [工作流总览](#第一章工作流总览)
2. [技术栈约束](#第二章技术栈约束)
3. [目录结构规范](#第三章目录结构规范)
4. [SoT 驱动开发](#第四章sot-驱动开发)
5. [防幻觉规则](#第五章防幻觉规则)
6. [代码模式库](#第六章代码模式库)
7. [RBAC 权限系统](#第七章rbac-权限系统)
8. [组件开发规范](#第八章组件开发规范)
9. [质量门禁](#第九章质量门禁)
10. [提示词模板](#第十章提示词模板)

---

## 第一章：工作流总览

### 1.1 AI 编程标准循环

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        前端 AI 编程标准循环 (35-75 分钟)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Step 1          Step 2          Step 3          Step 4          Step 5   │
│   ─────────       ─────────       ─────────       ─────────       ─────────│
│   读取上下文       确认任务        AI 生成         验证测试        提交代码  │
│      │               │               │               │               │     │
│      ▼               ▼               ▼               ▼               ▼     │
│   ┌─────┐        ┌─────┐        ┌─────┐        ┌─────┐        ┌─────┐     │
│   │memory│  ──►  │任务卡│  ──►  │代码  │  ──►  │tsc   │  ──►  │git  │     │
│   │-bank │        │+SoT │        │生成  │        │+lint│        │commit│   │
│   └─────┘        └─────┘        └─────┘        └─────┘        └─────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 每次对话必做

| 步骤 | 动作 | 验证方式 |
|------|------|---------|
| 1 | 读取 `memory-bank/progress.md` | 知道当前进度 |
| 2 | 读取 `memory-bank/architecture.md` | 知道文件位置 |
| 3 | 确认 SoT 版本对齐 | 查阅 `quick-reference.md` |
| 4 | 查阅相关 SoT 文档 | 找到约束规则 |
| 5 | 生成代码并标注来源 | `// SoT: DOC#SECTION` |
| 6 | 运行 TypeScript 检查 | `npx tsc --noEmit` |
| 7 | 更新 progress.md | 记录完成状态 |

### 1.3 标准提示词模板

```markdown
阅读 /memory-bank 所有文档，
阅读 progress.md 了解之前进度，
然后继续实施计划第 N 步
```

---

## 第二章：技术栈约束

### 2.1 技术栈白名单（不可变更）

```typescript
const TECH_STACK = {
  // 框架层
  framework: "Next.js 16 (App Router)",
  language: "TypeScript 5.6+ (strict: true)",

  // UI 层
  ui: "shadcn/ui + Tailwind CSS",
  icons: "lucide-react",
  charts: "recharts",
  theme: "next-themes",
  toast: "sonner",

  // 状态管理层
  serverState: "TanStack Query v5",
  urlState: "nuqs (推荐) / useSearchParams",
  localState: "useState / useReducer",

  // 表单层
  form: "react-hook-form",
  validation: "zod",

  // HTTP 层
  http: "apiFetch (@/lib/api.ts)",

  // 认证层
  auth: "Supabase Auth",
} as const;
```

### 2.2 禁止使用的技术

| 禁止项 | 原因 | 替代方案 |
|--------|------|---------|
| `fetch()` 直接调用 | 无统一错误处理 | `apiGet/apiPost` |
| `axios` | 非标准依赖 | `apiFetch` |
| `supabase.from()` | 绕过 API 层 | 后端 API |
| `Redux` | 过度复杂 | TanStack Query |
| `styled-components` | 与 Tailwind 冲突 | Tailwind CSS |
| 手写 HTML 标签 | 无设计一致性 | shadcn/ui |

---

## 第三章：目录结构规范

### 3.1 完整目录结构

```
frontend/src/
├── app/                          # Next.js App Router (薄壳层)
│   ├── (auth)/                   # 认证路由组
│   │   ├── login/page.tsx
│   │   └── layout.tsx
│   ├── (dashboard)/              # 仪表盘路由组
│   │   ├── page.tsx              # 首页 → 驾驶舱
│   │   ├── projects/page.tsx
│   │   ├── daily-reports/page.tsx
│   │   ├── finance/page.tsx
│   │   └── layout.tsx
│   ├── layout.tsx                # 根布局
│   ├── providers.tsx             # 全局 Providers
│   └── globals.css
│
├── features/                     # 功能模块 (核心)
│   ├── auth/
│   │   ├── components/
│   │   │   ├── LoginForm.tsx
│   │   │   └── index.ts
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   └── index.ts
│   │   ├── services/
│   │   │   └── authApi.ts
│   │   ├── types/
│   │   │   └── auth.types.ts
│   │   └── index.ts
│   │
│   ├── dashboard/
│   │   ├── components/
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── StatCard.tsx
│   │   │   ├── TopLists.tsx
│   │   │   └── index.ts
│   │   ├── context/
│   │   │   └── FilterContext.tsx
│   │   ├── utils/
│   │   │   └── formatters.ts
│   │   └── index.ts
│   │
│   ├── daily-reports/
│   │   ├── components/
│   │   │   ├── DailyReportsPage.tsx
│   │   │   ├── DailyReportsTable.tsx
│   │   │   ├── DailyReportDialog.tsx
│   │   │   ├── columns.tsx
│   │   │   └── index.ts
│   │   ├── hooks/
│   │   │   ├── useDailyReports.ts
│   │   │   └── index.ts
│   │   ├── services/
│   │   │   └── dailyReportsApi.ts
│   │   ├── types/
│   │   │   └── dailyReport.types.ts
│   │   └── index.ts
│   │
│   └── [其他功能模块...]
│
├── components/
│   ├── ui/                       # shadcn/ui 组件 (54+)
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── dialog.tsx
│   │   ├── data-table/
│   │   │   ├── data-table.tsx
│   │   │   ├── data-table-pagination.tsx
│   │   │   ├── data-table-toolbar.tsx
│   │   │   └── index.ts
│   │   └── ...
│   │
│   ├── layout/                   # 布局组件
│   │   ├── Sidebar.tsx
│   │   ├── Header.tsx
│   │   ├── PageContainer.tsx
│   │   └── index.ts
│   │
│   └── shared/                   # 共享业务组件
│       ├── StatusBadge.tsx
│       ├── DateRangePicker.tsx
│       └── index.ts
│
├── config/                       # 配置文件
│   └── nav-config.ts             # 导航 + RBAC 配置
│
├── hooks/                        # 全局 Hooks
│   ├── use-filtered-nav.ts       # RBAC 导航过滤
│   ├── use-table-params.ts       # 表格 URL 状态
│   ├── use-theme.ts
│   └── index.ts
│
├── lib/                          # 工具库
│   ├── api.ts                    # API 客户端 (核心)
│   ├── utils.ts                  # cn() 等工具
│   └── format.ts                 # 格式化工具
│
└── types/                        # 全局类型
    ├── common.ts
    ├── navigation.ts
    └── index.ts
```

### 3.2 Feature 模块结构模式

```
features/{module}/
├── components/           # 业务组件
│   ├── {Module}Page.tsx         # 主页面组件
│   ├── {Module}Table.tsx        # 数据表格
│   ├── {Module}Dialog.tsx       # 新建/编辑弹窗
│   ├── {Module}Detail.tsx       # 详情页
│   ├── columns.tsx              # 表格列定义
│   └── index.ts                 # 统一导出
│
├── hooks/                # React Query Hooks
│   ├── use{Module}s.ts          # 列表查询
│   ├── use{Module}.ts           # 单条查询
│   ├── useCreate{Module}.ts     # 创建
│   ├── useUpdate{Module}.ts     # 更新
│   └── index.ts
│
├── services/             # API 调用
│   ├── {module}Api.ts
│   └── index.ts
│
├── types/                # 类型定义
│   ├── {module}.types.ts
│   └── index.ts
│
├── utils/                # 工具函数 (可选)
│   └── index.ts
│
├── constants/            # 常量 (可选)
│   └── index.ts
│
└── index.ts              # 模块导出
```

### 3.3 薄壳页面模式

```typescript
// app/(dashboard)/daily-reports/page.tsx
// 页面文件只做路由映射，实际组件在 features 中

import { DailyReportsPage } from '@/features/daily-reports';

export default function Page() {
  return <DailyReportsPage />;
}

// 元数据
export const metadata = {
  title: '日报管理',
};
```

---

## 第四章：SoT 驱动开发

### 4.1 SoT 裁判链

```
优先级顺序 (高 → 低):

MASTER.md v4.6           ← 架构宪法、角色定义
    ↓
DATA_SCHEMA.md v5.6      ← 数据模型、字段类型
    ↓
STATE_MACHINE.md v2.7    ← 状态机定义、状态流转
    ↓
BUSINESS_RULES.md v4.7   ← 业务规则
    ↓
API_SOT.md v9.4          ← API 规范
    ↓
ERROR_CODES_SOT.md v2.3  ← 错误码定义
```

### 4.2 开发前必查 SoT

| 开发场景 | 必查文档 | 查询内容 |
|----------|---------|---------|
| 显示状态标签 | STATE_MACHINE.md | 状态枚举值、颜色定义 |
| 权限控制 | AUTH_SPEC.md + auth.types.ts | 6 角色白名单 |
| API 调用 | API_SOT.md | 端点路径、请求/响应格式 |
| 表单字段 | DATA_SCHEMA.md | 字段类型、必填项 |
| 错误提示 | ERROR_CODES_SOT.md | 错误码、提示文案 |
| 金额显示 | BUSINESS_RULES.md | 金额格式化规则 |

> ⚠️ 前端角色定义以 `auth.types.ts` 为准，与 AUTH_SPEC.md v2.0 对齐

### 4.3 代码来源标注规范

```typescript
// ========== 类型定义 ==========

// SoT: STATE_MACHINE.md v2.7 §2
type DailyReportStatus =
  | 'raw_submitted'
  | 'trend_pending'
  | 'trend_ok'
  | 'trend_flagged'
  | 'trend_resolved'
  | 'final_pending'
  | 'final_confirmed'
  | 'final_locked';

// SoT: AUTH_SPEC.md v2.0 + auth.types.ts
enum UserRole {
  ADMIN = 'admin',
  FINANCE = 'finance',
  PROJECT_OWNER = 'project_owner',
  DATA_OPERATOR = 'data_operator',
  ACCOUNT_MANAGER = 'account_manager',
  MEDIA_BUYER = 'media_buyer',
}

// ========== 业务逻辑 ==========

// SoT: BUSINESS_RULES.md#BR-RPT-001
function validateReportDate(date: Date): boolean {
  // 日报日期不能是未来
  return date <= new Date();
}

// SoT: BUSINESS_RULES.md#BR-FIN-003
function formatMoney(amount: number): string {
  // 金额格式化：保留 2 位小数，千分位分隔
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
  }).format(amount);
}
```

---

## 第五章：防幻觉规则

### 5.1 五大防幻觉原则

| 原则 | 标题 | 规则 | 级别 |
|------|------|------|------|
| **AH-01** | 禁止假设数据一致 | 遇到缺失标记"待确认"，不自动填充 | BLOCKING |
| **AH-02** | 禁止自动做管理裁决 | 不生成自动拒绝/暂停/冻结代码 | BLOCKING |
| **AH-03** | 禁止引入 SoT 未定义概念 | 发现缺失 → 停止 → 询问 | BLOCKING |
| **AH-04** | 必须遵循 Phase 1 原则 | 仅提示+高亮+记录，不阻断 | WARNING |
| **AH-05** | 遇到歧义必须停止并询问 | 列出歧义点 → 询问用户 | BLOCKING |

### 5.2 前端禁止行为清单

```typescript
// ❌ F-001: 自创状态值
type Status = 'pending' | 'draft';  // 不在 STATE_MACHINE.md 中

// ✅ 正确: 使用 SoT 定义的状态
// SoT: STATE_MACHINE.md v2.7 §2
type Status = 'raw_submitted' | 'trend_ok' | 'final_confirmed';


// ❌ F-002: 使用废弃角色
if (user.role === 'supervisor') { ... }  // 已废弃
if (user.role === 'pitcher') { ... }     // 业务术语，应用 media_buyer

// ✅ 正确: 使用 6 角色白名单
// SoT: AUTH_SPEC.md v2.0 + auth.types.ts
if (user.role === 'media_buyer') { ... }  // 投手
if (user.role === 'data_operator') { ... } // 数据运营


// ❌ F-003: 自动阻断
if (overBudget) {
  toast.error('超预算，操作被拒绝');
  return;
}

// ✅ 正确: Phase 1 只提示不阻断
if (overBudget) {
  toast.warning('提示：已超预算 30%');
  // 继续执行，不阻断
}


// ❌ F-004: 硬编码错误消息
toast.error('操作失败，请重试');

// ✅ 正确: 使用 SoT 错误码
// SoT: ERROR_CODES_SOT.md v2.3
toast.error(getErrorMessage(error.code));
```

### 5.3 5 秒扫描检查（拿到代码后立即执行）

```bash
# 1. 废弃角色检查 (必须无结果)
grep -r "supervisor" frontend/src/
grep -r "pitcher" frontend/src/  # 应使用 media_buyer

# 2. 直接 fetch 检查 (必须无结果，排除 lib/api.ts)
grep -r "fetch\(" frontend/src/ --include="*.ts" --include="*.tsx" | grep -v "lib/api"

# 3. 手写 HTML 检查
grep -rE "<button|<input|<select|<table" frontend/src/ --include="*.tsx"

# ⚠️ 以下角色是合法的，不要标记为违规:
# ✅ admin, finance, project_owner, data_operator, account_manager, media_buyer
```

---

## 第六章：代码模式库

### 6.1 Query Hook 模式

```typescript
// features/{module}/hooks/use{Module}s.ts
import { useQuery } from '@tanstack/react-query';
import { get{Module}s } from '../services/{module}Api';
import type { {Module}ListParams } from '../types';

export function use{Module}s(params: {Module}ListParams = {}) {
  return useQuery({
    queryKey: ['{module}s', params],
    queryFn: () => get{Module}s(params),
    staleTime: 2 * 60 * 1000,  // 2 分钟新鲜期
  });
}

// 单条查询
export function use{Module}(id: number | undefined) {
  return useQuery({
    queryKey: ['{module}', id],
    queryFn: () => get{Module}(id!),
    enabled: !!id,  // 有 ID 才查询
  });
}
```

### 6.2 Mutation Hook 模式

```typescript
// features/{module}/hooks/useCreate{Module}.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { create{Module} } from '../services/{module}Api';
import type { {Module}CreateInput, ApiError } from '../types';

export function useCreate{Module}() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: {Module}CreateInput) => create{Module}(input),
    onSuccess: () => {
      // 刷新列表缓存
      queryClient.invalidateQueries({ queryKey: ['{module}s'] });
      toast.success('创建成功');
    },
    onError: (error: ApiError) => {
      // SoT: ERROR_CODES_SOT.md
      toast.error(error.message || '创建失败');
    },
  });
}
```

### 6.3 Service 层模式

```typescript
// features/{module}/services/{module}Api.ts
import { apiGet, apiPost, apiPatch, apiDelete } from '@/lib/api';
import type {
  {Module},
  {Module}CreateInput,
  {Module}UpdateInput,
  {Module}ListParams,
  PaginatedResponse,
} from '../types';

const BASE_PATH = '/api/v1/{modules}';

// 列表查询
export async function get{Module}s(
  params: {Module}ListParams = {}
): Promise<PaginatedResponse<{Module}>> {
  const searchParams = new URLSearchParams();

  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));
  if (params.status) searchParams.set('status', params.status);
  if (params.search) searchParams.set('search', params.search);

  const query = searchParams.toString();
  return apiGet<PaginatedResponse<{Module}>>(`${BASE_PATH}?${query}`);
}

// 单条查询
export async function get{Module}(id: number): Promise<{Module}> {
  return apiGet<{Module}>(`${BASE_PATH}/${id}`);
}

// 创建
export async function create{Module}(
  input: {Module}CreateInput
): Promise<{Module}> {
  return apiPost<{Module}>(BASE_PATH, input);
}

// 更新
export async function update{Module}(
  id: number,
  input: {Module}UpdateInput
): Promise<{Module}> {
  return apiPatch<{Module}>(`${BASE_PATH}/${id}`, input);
}

// 删除
export async function delete{Module}(id: number): Promise<void> {
  return apiDelete(`${BASE_PATH}/${id}`);
}
```

### 6.4 页面组件模式

```typescript
// features/{module}/components/{Module}Page.tsx
'use client';

import { useState } from 'react';
import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { DataTable } from '@/components/ui/data-table';
import { useTableParams } from '@/hooks';
import { use{Module}s } from '../hooks';
import { columns } from './columns';
import { {Module}Dialog } from './{Module}Dialog';

export function {Module}Page() {
  // 1. URL 状态管理
  const { params, setParams } = useTableParams();

  // 2. 数据获取
  const { data, isLoading, error } = use{Module}s(params);

  // 3. 本地状态
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selected, setSelected] = useState<{Module} | null>(null);

  // 4. 事件处理
  const handleCreate = () => {
    setSelected(null);
    setDialogOpen(true);
  };

  const handleEdit = (item: {Module}) => {
    setSelected(item);
    setDialogOpen(true);
  };

  // 5. 渲染
  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{Module}管理</h1>
          <p className="text-muted-foreground">
            管理系统中的{module}数据
          </p>
        </div>
        <Button onClick={handleCreate}>
          <Plus className="mr-2 h-4 w-4" />
          新建
        </Button>
      </div>

      {/* 数据表格 */}
      <DataTable
        columns={columns}
        data={data?.items ?? []}
        loading={isLoading}
        pagination={{
          page: params.page ?? 1,
          pageSize: params.page_size ?? 20,
          total: data?.total ?? 0,
          onPageChange: (page) => setParams({ page }),
          onPageSizeChange: (size) => setParams({ page_size: size }),
        }}
        onRowClick={handleEdit}
      />

      {/* 新建/编辑弹窗 */}
      <{Module}Dialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        data={selected}
      />
    </div>
  );
}
```

### 6.5 表单弹窗模式

```typescript
// features/{module}/components/{Module}Dialog.tsx
'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
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
import { useCreate{Module}, useUpdate{Module} } from '../hooks';
import type { {Module} } from '../types';

// Zod Schema
const formSchema = z.object({
  name: z.string().min(1, '名称不能为空').max(100, '名称最多100字'),
  // ... 更多字段
});

type FormValues = z.infer<typeof formSchema>;

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  data?: {Module} | null;
}

export function {Module}Dialog({ open, onOpenChange, data }: Props) {
  const isEdit = !!data;

  // 表单
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: '',
    },
  });

  // 编辑时填充数据
  useEffect(() => {
    if (data) {
      form.reset({
        name: data.name,
      });
    } else {
      form.reset({ name: '' });
    }
  }, [data, form]);

  // Mutations
  const createMutation = useCreate{Module}();
  const updateMutation = useUpdate{Module}();

  const isPending = createMutation.isPending || updateMutation.isPending;

  // 提交处理
  const onSubmit = async (values: FormValues) => {
    try {
      if (isEdit && data) {
        await updateMutation.mutateAsync({ id: data.id, ...values });
      } else {
        await createMutation.mutateAsync(values);
      }
      onOpenChange(false);
    } catch {
      // 错误已在 mutation 中处理
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>{isEdit ? '编辑' : '新建'}{Module}</DialogTitle>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
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

            {/* 更多字段... */}

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                取消
              </Button>
              <Button type="submit" disabled={isPending}>
                {isPending ? '保存中...' : '保存'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
```

### 6.6 表格列定义模式

```typescript
// features/{module}/components/columns.tsx
'use client';

import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Pencil, Trash } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { StatusBadge } from '@/components/shared';
import { formatDate, formatMoney } from '@/lib/format';
import type { {Module} } from '../types';

export const columns: ColumnDef<{Module}>[] = [
  {
    accessorKey: 'id',
    header: 'ID',
    size: 80,
  },
  {
    accessorKey: 'name',
    header: '名称',
  },
  {
    accessorKey: 'status',
    header: '状态',
    cell: ({ row }) => (
      // SoT: STATE_MACHINE.md v2.7
      <StatusBadge status={row.original.status} />
    ),
  },
  {
    accessorKey: 'amount',
    header: '金额',
    cell: ({ row }) => (
      // SoT: BUSINESS_RULES.md#BR-FIN-003
      <span className="font-mono">{formatMoney(row.original.amount)}</span>
    ),
  },
  {
    accessorKey: 'created_at',
    header: '创建时间',
    cell: ({ row }) => formatDate(row.original.created_at),
  },
  {
    id: 'actions',
    header: '操作',
    size: 80,
    cell: ({ row }) => (
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon">
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem>
            <Pencil className="mr-2 h-4 w-4" />
            编辑
          </DropdownMenuItem>
          <DropdownMenuItem className="text-destructive">
            <Trash className="mr-2 h-4 w-4" />
            删除
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];
```

### 6.7 完整示例：日报模块

> 以下是一个完整的功能模块实现，可直接参考

```typescript
// ========== features/daily-reports/types/dailyReport.types.ts ==========
// SoT: STATE_MACHINE.md v2.7 §2
export type DailyReportStatus =
  | 'raw_submitted'
  | 'trend_pending'
  | 'trend_ok'
  | 'trend_flagged'
  | 'trend_resolved'
  | 'final_pending'
  | 'final_confirmed'
  | 'final_locked';

export interface DailyReport {
  id: number;
  report_date: string;          // YYYY-MM-DD
  ad_account_id: number;
  ad_spend: number;             // 消耗金额 (分)
  conversions: number;          // 原始转化数
  conversions_final: number;    // 最终有效粉数
  status: DailyReportStatus;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface DailyReportListParams {
  page?: number;
  page_size?: number;
  status?: DailyReportStatus;
  date_from?: string;
  date_to?: string;
}

// ========== features/daily-reports/services/dailyReportsApi.ts ==========
import { apiGet, apiPost, apiPatch } from '@/lib/api';
import type { DailyReport, DailyReportListParams, PaginatedResponse } from '../types';

const BASE_PATH = '/api/v1/daily-reports';

export async function getDailyReports(
  params: DailyReportListParams = {}
): Promise<PaginatedResponse<DailyReport>> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));
  if (params.status) searchParams.set('status', params.status);
  if (params.date_from) searchParams.set('date_from', params.date_from);
  if (params.date_to) searchParams.set('date_to', params.date_to);

  return apiGet<PaginatedResponse<DailyReport>>(`${BASE_PATH}?${searchParams}`);
}

export async function getDailyReport(id: number): Promise<DailyReport> {
  return apiGet<DailyReport>(`${BASE_PATH}/${id}`);
}

// ========== features/daily-reports/hooks/useDailyReports.ts ==========
import { useQuery } from '@tanstack/react-query';
import { getDailyReports, getDailyReport } from '../services/dailyReportsApi';
import type { DailyReportListParams } from '../types';

export function useDailyReports(params: DailyReportListParams = {}) {
  return useQuery({
    queryKey: ['daily-reports', params],
    queryFn: () => getDailyReports(params),
    staleTime: 2 * 60 * 1000,
  });
}

export function useDailyReport(id: number | undefined) {
  return useQuery({
    queryKey: ['daily-report', id],
    queryFn: () => getDailyReport(id!),
    enabled: !!id,
  });
}
```

---

## 第七章：RBAC 权限系统

### 7.1 角色白名单（6 角色）

```typescript
// SoT: AUTH_SPEC.md v2.0 + auth.types.ts
// 与实际代码 frontend/src/features/auth/types/auth.types.ts 完全一致
export enum UserRole {
  ADMIN = 'admin',              // 管理员 - 系统配置
  FINANCE = 'finance',          // 财务 - 对账、资金
  PROJECT_OWNER = 'project_owner', // 项目负责人 - 项目盈亏
  DATA_OPERATOR = 'data_operator', // 数据运营 - 日报、数据导入
  ACCOUNT_MANAGER = 'account_manager', // 客户经理 - 账户分配
  MEDIA_BUYER = 'media_buyer',  // 投手 - 执行投放
}

// 禁止使用的角色
// ❌ supervisor (已废弃，合并到 project_owner)
// ❌ pitcher (业务层术语，代码层用 media_buyer)
// ❌ ceo (业务层术语，不在技术角色枚举中)

// ⚠️ 术语对照表 (业务层 vs 技术层)
// | 业务层 | 技术层 |
// |--------|--------|
// | 投手   | media_buyer |
// | 老板   | 无对应角色 (通过 admin 代理) |
```

### 7.2 导航权限配置

```typescript
// config/nav-config.ts
import type { NavGroup, NavItem } from '@/types/navigation';
import { UserRole } from '@/features/auth/types';

export const mainNavGroups: NavGroup[] = [
  {
    title: '业务管理',
    items: [
      {
        id: 'dashboard',
        title: '运营驾驶舱',
        url: '/',
        icon: LayoutDashboard,
        // 无 access = 所有角色可见
      },
      {
        id: 'projects',
        title: '项目管理',
        url: '/projects',
        icon: FolderKanban,
        access: {
          roles: [
            UserRole.ADMIN,
            UserRole.PROJECT_OWNER,
            UserRole.ACCOUNT_MANAGER,
            UserRole.FINANCE,
          ],
        },
      },
      {
        id: 'daily-reports',
        title: '日报管理',
        url: '/daily-reports',
        icon: FileText,
        access: {
          roles: [
            UserRole.ADMIN,
            UserRole.PROJECT_OWNER,
            UserRole.DATA_OPERATOR,
            UserRole.MEDIA_BUYER,
          ],
        },
      },
    ],
  },
  {
    title: '财务管理',
    access: {
      roles: [UserRole.ADMIN, UserRole.FINANCE, UserRole.PROJECT_OWNER],
    },
    items: [
      // 财务相关菜单...
    ],
  },
  {
    title: '系统管理',
    access: {
      roles: [UserRole.ADMIN],
    },
    items: [
      // 系统管理菜单...
    ],
  },
];
```

### 7.3 权限过滤 Hook

```typescript
// hooks/use-filtered-nav.ts
import { useMemo } from 'react';
import { useAuth } from '@/features/auth/hooks/useAuth';
import type { NavItem, NavGroup, PermissionCheck } from '@/types/navigation';

function checkAccess(
  access: PermissionCheck | undefined,
  userRole: UserRole | undefined
): boolean {
  if (!access) return true;
  if (!userRole) return false;
  if (access.roles && !access.roles.includes(userRole)) return false;
  return true;
}

export function useFilteredNavGroups(groups: NavGroup[]) {
  const { user } = useAuth();

  return useMemo(() => {
    return groups
      .filter((group) => checkAccess(group.access, user?.role))
      .map((group) => ({
        ...group,
        items: group.items.filter((item) =>
          checkAccess(item.access, user?.role)
        ),
      }))
      .filter((group) => group.items.length > 0);
  }, [groups, user?.role]);
}
```

### 7.4 权限矩阵

> 来源: nav-config.ts + AUTH_SPEC.md v2.0

| 菜单 | admin | finance | project_owner | data_operator | account_manager | media_buyer |
|------|:-----:|:-------:|:-------------:|:-------------:|:---------------:|:-----------:|
| 运营驾驶舱 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 项目管理 | ✓ | ✓ | ✓ | - | ✓ | - |
| 广告账户 | ✓ | - | ✓ | - | ✓ | ✓(只读) |
| 日报管理 | ✓ | - | ✓ | ✓ | - | ✓ |
| 周度简报 | ✓ | ✓ | ✓ | - | - | - |
| 财务管理 | ✓ | ✓ | ✓ | - | - | - |
| 充值管理 | ✓ | ✓ | ✓ | - | - | - |
| 对账管理 | ✓ | ✓ | - | - | - | - |
| 系统管理 | ✓ | - | - | - | - | - |

> ⚠️ 注意: 业务文档中的 `pitcher` 对应技术层的 `media_buyer`

---

## 第八章：组件开发规范

### 8.1 必须使用的组件

| 场景 | 组件 | 来源 |
|------|------|------|
| 按钮 | `Button` | `@/components/ui/button` |
| 输入框 | `Input` | `@/components/ui/input` |
| 选择器 | `Select` | `@/components/ui/select` |
| 复选框 | `Checkbox` | `@/components/ui/checkbox` |
| 表格 | `DataTable` | `@/components/ui/data-table` |
| 弹窗 | `Dialog` | `@/components/ui/dialog` |
| 确认框 | `AlertDialog` | `@/components/ui/alert-dialog` |
| 表单 | `Form` + `FormField` | `@/components/ui/form` |
| 卡片 | `Card` | `@/components/ui/card` |
| 骨架屏 | `Skeleton` | `@/components/ui/skeleton` |
| 下拉菜单 | `DropdownMenu` | `@/components/ui/dropdown-menu` |
| 工具提示 | `Tooltip` | `@/components/ui/tooltip` |
| 通知 | `toast` | `sonner` |

### 8.2 导入顺序规范

```typescript
// 1. React/Next.js 核心
import { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';

// 2. 第三方库
import { useQuery, useMutation } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

// 3. Icons
import { Plus, Pencil, Trash, MoreHorizontal } from 'lucide-react';

// 4. UI 组件
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog } from '@/components/ui/dialog';

// 5. 布局/共享组件
import { PageContainer } from '@/components/layout';
import { StatusBadge } from '@/components/shared';

// 6. Feature 内部导入
import { use{Module}s, useCreate{Module} } from '../hooks';
import { columns } from './columns';

// 7. 类型
import type { {Module}, {Module}CreateInput } from '../types';

// 8. 常量/工具
import { STATUS_CONFIG } from '../constants';
import { formatMoney } from '@/lib/format';
```

### 8.3 命名规范

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

## 第九章：质量门禁

### 9.1 开发阶段门禁

| 门禁 | 命令 | 通过标准 |
|------|------|---------|
| TypeScript | `npx tsc --noEmit` | 0 errors |
| ESLint | `npm run lint` | 0 errors |
| 构建 | `npm run build` | 成功 |

### 9.2 任务完成检查清单

```markdown
## 代码质量
- [ ] TypeScript 编译通过
- [ ] ESLint 无错误
- [ ] 无 `any` 类型

## SoT 合规
- [ ] 状态值在 STATE_MACHINE.md 中
- [ ] 角色值在 6 角色白名单中
- [ ] 错误码在 ERROR_CODES_SOT.md 中
- [ ] 代码有 SoT 来源标注

## 组件规范
- [ ] 使用 shadcn/ui 组件
- [ ] 无手写 HTML 标签
- [ ] 使用 apiFetch 调用 API

## 权限检查
- [ ] 无 supervisor 角色 (已废弃)
- [ ] 无 pitcher 角色 (应用 media_buyer)
- [ ] 角色值在 6 角色白名单中: admin, finance, project_owner, data_operator, account_manager, media_buyer
```

### 9.3 每日检查清单

```markdown
## 开始前 (5 分钟)
□ 读取 memory-bank/progress.md
□ 确认今天的任务
□ 打开相关 SoT 文档

## 生成代码后 (1 分钟)
□ 5 秒扫描: 搜索 supervisor
□ 5 秒扫描: 状态值在枚举内
□ 5 秒扫描: 代码有 SoT 标注

## 提交前 (3 分钟)
□ TypeScript 编译通过
□ ESLint 检查通过
□ progress.md 已更新
```

---

## 第十章：提示词模板

### 10.1 新建功能模块

```markdown
## 背景
项目：AI 广告代投系统
技术栈：Next.js 16 + TypeScript + shadcn/ui + TanStack Query v5

## 任务
为 [模块名] 创建完整的功能模块

## 目录结构
请在 features/[module]/ 下创建：
- components/{Module}Page.tsx
- components/{Module}Dialog.tsx
- components/columns.tsx
- hooks/use{Module}s.ts
- hooks/useCreate{Module}.ts
- services/{module}Api.ts
- types/{module}.types.ts

## SoT 约束
- 状态值：参考 STATE_MACHINE.md
- 角色：6 角色白名单 (admin, finance, project_owner, data_operator, account_manager, media_buyer)
- 禁止角色：supervisor (已废弃)、pitcher (业务术语，用 media_buyer)
- 错误码：参考 ERROR_CODES_SOT.md
- API 路径：参考 API_SOT.md

## 验收标准
- [ ] TypeScript 编译通过
- [ ] 使用 shadcn/ui 组件
- [ ] 使用 apiFetch
- [ ] 有 SoT 来源标注
```

### 10.2 添加表格列

```markdown
## 任务
为 [模块] 表格添加 [字段] 列

## 约束
- 字段类型：参考 DATA_SCHEMA.md
- 格式化：
  - 金额使用 formatMoney()
  - 日期使用 formatDate()
  - 状态使用 StatusBadge

## 参考
现有列定义在 features/[module]/components/columns.tsx
```

### 10.3 添加表单字段

```markdown
## 任务
在 [模块]Dialog 中添加 [字段] 输入

## 约束
- 字段验证：使用 zod schema
- 必填项：参考 DATA_SCHEMA.md
- 组件：使用 FormField + 对应 UI 组件

## 示例
```tsx
<FormField
  control={form.control}
  name="fieldName"
  render={({ field }) => (
    <FormItem>
      <FormLabel>字段名称</FormLabel>
      <FormControl>
        <Input {...field} />
      </FormControl>
      <FormMessage />
    </FormItem>
  )}
/>
```
```

### 10.4 修复 Bug

```markdown
## 问题描述
[描述问题现象]

## 复现步骤
1. [步骤1]
2. [步骤2]

## 期望行为
[应该发生什么]

## 实际行为
[实际发生什么]

## 要求
1. 分析根本原因
2. 修复问题
3. 不要破坏现有功能
4. 遵循项目代码规范
```

---

## 附录

### A. 快速命令

```bash
# 开发
npm run dev           # 启动开发服务器

# 检查
npx tsc --noEmit      # TypeScript 检查
npm run lint          # ESLint 检查
npm run build         # 构建检查

# 搜索违规
grep -r "supervisor" frontend/src/
grep -r "fetch\(" frontend/src/ | grep -v "lib/api"
```

### B. 相关文档

| 文档 | 路径 | 用途 |
|------|------|------|
| 前端 CLAUDE.md | frontend/CLAUDE.md | 技术栈约束 |
| AI 编程 SOP | docs/guides/AI_PROGRAMMING_SOP.md | 完整 SOP |
| 开发工作流 | memory-bank/dev-workflow.md | 工作流程 |
| 速查表 | memory-bank/quick-reference.md | 速查 |
| 任务卡 | docs/guides/TASK_CARDS_v2.md | 任务定义 |

### C. 参考项目

| 项目 | GitHub | 借鉴点 |
|------|--------|--------|
| next-shadcn-dashboard-starter | [链接](https://github.com/Kiranism/next-shadcn-dashboard-starter) | RBAC、目录结构、DataTable |
| SaaS-Boilerplate | [链接](https://github.com/ixartz/SaaS-Boilerplate) | 多租户、权限 |
| nextjs-fastapi-template | [链接](https://github.com/vintasoftware/nextjs-fastapi-template) | 前后端集成 |

---

**文档版本**: v1.1
**最后更新**: 2025-12-29
**维护者**: AI 代码工厂
**变更记录**:
- v1.1: 修复角色定义与 auth.types.ts 对齐，添加术语对照表，扩展权限矩阵，添加完整示例
