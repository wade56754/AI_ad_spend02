# Frontend CLAUDE.md - Next.js + TypeScript + shadcn/ui

> **专属范围**: `frontend/` 目录下的所有代码
> **技术栈**: Next.js 16 | TypeScript 5.6+ | shadcn/ui | TanStack Query v5

---

## 技术栈约束（不可变更）

```typescript
const STACK = {
  framework: "Next.js 16 (App Router)",
  language: "TypeScript (strict: true)",
  ui: "shadcn/ui + Tailwind CSS",
  state: "TanStack Query v5",
  form: "react-hook-form + zod",
  http: "apiFetch (lib/api.ts)",
  icons: "lucide-react",
  charts: "recharts",
  theme: "next-themes",
  toast: "sonner",
}
```

---

## 目录结构

```
frontend/src/
├── app/                      # Next.js App Router
│   ├── (dashboard)/          # 后台路由组
│   │   └── {page}/page.tsx   # 薄壳页面
│   ├── layout.tsx            # 根布局
│   └── providers.tsx         # 全局 Providers
│
├── features/                 # 功能模块 (核心)
│   └── {module}/
│       ├── components/       # 业务组件
│       │   ├── {Module}Page.tsx      # 主页面
│       │   ├── {Module}Table.tsx     # 数据表格
│       │   ├── {Module}Dialog.tsx    # 弹窗
│       │   └── index.ts              # 导出
│       ├── hooks/            # React Query hooks
│       │   ├── use{Module}.ts
│       │   └── index.ts
│       ├── services/         # API 调用
│       │   ├── {module}Api.ts
│       │   └── index.ts
│       ├── types/            # TypeScript 类型
│       │   ├── {module}.types.ts
│       │   └── index.ts
│       └── index.ts          # 模块导出
│
├── components/
│   ├── ui/                   # shadcn/ui (54+ 组件)
│   ├── layout/               # 布局组件
│   └── shared/               # 共享组件
│
├── hooks/                    # 全局 hooks
│   ├── use-table-params.ts   # 表格 URL 状态
│   └── index.ts
│
├── lib/                      # 工具库
│   ├── api.ts                # API 客户端 (关键)
│   └── utils.ts              # cn() 等工具
│
└── types/                    # 全局类型
    └── common.ts
```

---

## API 调用规范

### 禁止直接 fetch
```typescript
// ❌ 禁止
fetch('/api/...')
axios.get('/api/...')
supabase.from('...').select('*')

// ✅ 正确
import { apiGet, apiPost } from '@/lib/api'
const data = await apiGet<User>('/api/v1/users')
```

### Query Hook 模式
```typescript
// features/{module}/hooks/use{Module}.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { get{Module}s, create{Module} } from '../services/{module}Api'

export function use{Module}s(params: ListParams) {
  return useQuery({
    queryKey: ['{module}s', params],
    queryFn: () => get{Module}s(params),
    staleTime: 2 * 60 * 1000,  // 2 分钟
  })
}

export function useCreate{Module}() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: create{Module},
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['{module}s'] })
      toast.success('创建成功')
    },
    onError: (error: ApiError) => {
      toast.error(error.message || '操作失败')
    },
  })
}
```

### Service 层模式
```typescript
// features/{module}/services/{module}Api.ts
import { apiGet, apiPost, apiFetchPaginated } from '@/lib/api'
import type { {Module}, {Module}CreateInput, PaginatedResponse } from '../types'

const BASE_PATH = '/api/v1/{modules}'

export async function get{Module}s(
  params: ListParams = {}
): Promise<PaginatedResponse<{Module}>> {
  const searchParams = new URLSearchParams()
  if (params.page) searchParams.set('page', String(params.page))
  if (params.page_size) searchParams.set('page_size', String(params.page_size))
  // ... 更多参数

  const query = searchParams.toString()
  return apiFetchPaginated<{Module}>(`${BASE_PATH}?${query}`)
}

export async function create{Module}(
  input: {Module}CreateInput
): Promise<{Module}> {
  return apiPost<{Module}>(BASE_PATH, input)
}
```

---

## 组件规范

### 页面组件结构
```typescript
'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { DataTable } from '@/components/ui/data-table'
import { use{Module}s } from '../hooks'
import { columns } from './{Module}Columns'

export function {Module}Page() {
  // 1. URL 状态
  const { params, setParams } = useTableParams()

  // 2. 数据获取
  const { data, isLoading, error } = use{Module}s(params)

  // 3. 本地状态
  const [isDialogOpen, setIsDialogOpen] = useState(false)

  // 4. 渲染
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{Module} 管理</h1>
        <Button onClick={() => setIsDialogOpen(true)}>
          新建
        </Button>
      </div>

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        loading={isLoading}
        pagination={{
          page: params.page,
          pageSize: params.pageSize,
          total: data?.total ?? 0,
          onPageChange: (page) => setParams({ page }),
        }}
      />

      <{Module}Dialog
        open={isDialogOpen}
        onOpenChange={setIsDialogOpen}
      />
    </div>
  )
}
```

### 弹窗组件模式
```typescript
'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

const schema = z.object({
  name: z.string().min(1, '名称不能为空'),
  // ... 更多字段
})

type FormValues = z.infer<typeof schema>

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  data?: {Module}  // 编辑时传入
}

export function {Module}Dialog({ open, onOpenChange, data }: Props) {
  const isEdit = !!data

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: data?.name ?? '',
    },
  })

  const createMutation = useCreate{Module}()
  const updateMutation = useUpdate{Module}()

  const onSubmit = (values: FormValues) => {
    if (isEdit) {
      updateMutation.mutate({ id: data.id, ...values })
    } else {
      createMutation.mutate(values)
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEdit ? '编辑' : '新建'}</DialogTitle>
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
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                取消
              </Button>
              <Button type="submit" disabled={isPending}>
                {isPending ? '保存中...' : '保存'}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
```

---

## 必须使用的组件

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
| 状态标签 | `StatusBadge` | `@/components/ui/status-badge` |
| 通知 | `toast` | `sonner` |

---

## 禁止事项

```typescript
// ❌ 手写 HTML 标签
<button>Click</button>
<input type="text" />
<table><tr><td>...</td></tr></table>
<select><option>...</option></select>

// ✅ 使用 shadcn/ui
<Button>Click</Button>
<Input type="text" />
<DataTable columns={cols} data={data} />
<Select>...</Select>
```

```typescript
// ❌ 使用 any
const data: any = response
function handler(e: any) {}

// ✅ 定义具体类型
const data: UserResponse = response
function handler(e: React.MouseEvent<HTMLButtonElement>) {}
```

```typescript
// ❌ 直接 fetch
const res = await fetch('/api/users')

// ✅ 使用 apiFetch
const data = await apiGet<User[]>('/api/v1/users')
```

```typescript
// ❌ 缺少 'use client'
export default function Page() {
  const [state, setState] = useState()  // 错误！
}

// ✅ 添加 'use client'
'use client'

export default function Page() {
  const [state, setState] = useState()
}
```

---

## 状态约束

### 日报状态 (8 状态机)
> 来源: STATE_MACHINE.md v2.6 §8

```typescript
type DailyReportStatus =
  | 'raw_submitted'    // 投手提交原始数据
  | 'trend_pending'    // 趋势风控检测中
  | 'trend_ok'         // 趋势正常
  | 'trend_flagged'    // 趋势异常待审核
  | 'trend_resolved'   // 趋势异常已解决
  | 'final_pending'    // 等待最终确认
  | 'final_confirmed'  // 运营确认最终粉数
  | 'final_locked'     // 计费锁定 (终态)
```

### 角色白名单 (5 个技术层角色)
> 来源: PROJECT_RULES.md v3.5 §四

```typescript
type Role = 'admin' | 'finance' | 'data_operator' | 'account_manager' | 'media_buyer'

// ❌ 禁止使用废弃角色
// 'data_clerk' | 'manager' | 'trader'
// ❌ 禁止使用业务层概念作为角色
// 'ceo' | 'project_owner' | 'pitcher'
```

---

## 类型定义规范

### 全局类型
```typescript
// types/common.ts
export type UUID = string
export type ISODateString = string
export type DateString = string  // YYYY-MM-DD

export interface Money {
  amount: number      // 分为单位
  currency: 'CNY' | 'USD'
}

export interface PaginationParams {
  page?: number
  page_size?: number
}

export interface SortParams {
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export type ListParams = PaginationParams & SortParams & {
  search?: string
}
```

### 模块类型
```typescript
// features/{module}/types/{module}.types.ts
export interface {Module} {
  id: number
  name: string
  status: {Module}Status
  created_at: ISODateString
  updated_at: ISODateString
}

export interface {Module}CreateInput {
  name: string
}

export interface {Module}UpdateInput extends Partial<{Module}CreateInput> {}

export interface {Module}ListParams extends ListParams {
  status?: {Module}Status
}
```

---

## 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 组件文件 | PascalCase | `DailyReportTable.tsx` |
| Hook 文件 | camelCase + use | `useDailyReports.ts` |
| 服务文件 | camelCase + Api | `dailyReportsApi.ts` |
| 类型文件 | camelCase + .types | `dailyReport.types.ts` |
| 页面组件 | PascalCase + Page | `DailyReportsPage.tsx` |
| 弹窗组件 | PascalCase + Dialog | `CreateReportDialog.tsx` |

---

## 导入顺序

```typescript
// 1. React/Next.js
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

// 2. 第三方库
import { useQuery, useMutation } from '@tanstack/react-query'
import { z } from 'zod'

// 3. UI 组件
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

// 4. 本地 hooks/services
import { useDailyReports } from '../hooks'
import { getDailyReports } from '../services'

// 5. 类型
import type { DailyReport } from '../types'

// 6. 样式/常量
import { STATUS_CONFIG } from '../constants'
```

---

## TanStack Query 配置

```typescript
// providers.tsx
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 2 * 60 * 1000,     // 2 分钟新鲜
      gcTime: 10 * 60 * 1000,       // 10 分钟缓存
      refetchOnWindowFocus: false,  // 窗口聚焦不刷新
      retry: 3,                      // 重试 3 次
      retryDelay: (i) => Math.min(1000 * 2 ** i, 30000),
    },
    mutations: {
      retry: 1,
    },
  },
})
```

---

## 错误处理

```typescript
// API 错误
interface ApiError {
  code: string       // 来自 ERROR_CODES_SOT.md
  message: string
  status: number
}

// Mutation 错误处理
const mutation = useMutation({
  mutationFn: createItem,
  onSuccess: () => {
    toast.success('创建成功')
    onOpenChange(false)
  },
  onError: (error: ApiError) => {
    toast.error(error.message || '操作失败')
  },
})
```

---

## 性能优化

```typescript
// 1. 使用 React.memo
export const ExpensiveList = React.memo(({ items }) => {
  return items.map(item => <Item key={item.id} {...item} />)
})

// 2. 使用 useMemo
const sortedData = useMemo(() =>
  data.sort((a, b) => a.date - b.date),
  [data]
)

// 3. 使用 useCallback
const handleClick = useCallback(() => {
  setOpen(true)
}, [])

// 4. 图片懒加载
import Image from 'next/image'
<Image src={url} loading="lazy" alt="" />
```

---

**文档版本**: v1.0
**最后更新**: 2025-12-28
