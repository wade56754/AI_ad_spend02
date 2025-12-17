---
version: v2.1
status: candidate_freeze
layer: dev-guide
owner: wade
last_reviewed: 2025-12-03
baseline: MASTER.md v3.5, SoT Freeze v2.6, Dev-Guides Freeze vFinal
---

# FRONTEND_STYLE_GUIDE_v2.1

> **面向对象**: 前端工程师 + FE Agent（自动化代码生成工具）
>
> **核心原则**: 本文档中标记为「规则」的条目为强制约束，FE Agent 生成代码时必须遵循；标记为「示例」的条目仅供参考。

---

## 1. 总览与目标

### 1.1 文档定位

本文档是 AI Ad Spend 系统前端开发的 **唯一样式权威 (Single Source of Truth)**，覆盖：

- 技术栈与版本约定
- 应用布局与导航规范
- 组件分层与目录结构
- 设计系统（颜色、排版、间距）
- 状态与 SoT 对齐
- API 调用与数据流
- 权限与交互模式
- 禁止事项与自检清单

### 1.2 使用方式

| 使用者 | 使用方式 |
|--------|----------|
| 前端工程师 | 按规则编写代码，参考示例理解写法 |
| FE Agent | 将「规则」作为硬约束，生成符合规范的 TSX 代码 |
| Code Review | 以「规则」为依据判断代码是否合规 |

---

## 2. 技术栈与基础约定

### 2.1 核心技术栈

#### 规则

> **版本说明**：具体版本号以项目 `package.json` 和 `MASTER.md` 为准，本表仅列出技术选型约定。

| 技术 | 版本约定 | 用途 |
|------|----------|------|
| Next.js | App Router 模式 | 全栈框架，使用 `app/` 目录结构 |
| TypeScript | 严格模式 | 类型安全，`strict: true` 必须开启 |
| React | ^18.x | UI 库 |
| Tailwind CSS | ^3.x | 原子化样式 |
| shadcn/ui | latest | 基础组件库 |
| TanStack Query | ^5.x | 服务端状态管理 |
| Zustand | ^4.x | 客户端状态管理 |
| Zod | ^3.x | 运行时类型校验、表单验证 |
| lucide-react | latest | 图标库 |

#### 规则：TypeScript 配置

```json
// tsconfig.json 必须包含
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  }
}
```

### 2.2 Server/Client 组件边界

#### 规则

| 组件类型 | 使用场景 | 标记方式 |
|----------|----------|----------|
| Server Component | 数据获取、SEO 关键页面、无交互 UI | 默认（不需标记） |
| Client Component | useState/useEffect、事件处理、浏览器 API | 文件顶部 `'use client'` |

#### 规则：Client 边界最小化

- **必须**：`'use client'` 只在需要交互的最小组件范围使用
- **禁止**：在 `layout.tsx` 或 `page.tsx` 顶层添加 `'use client'`
- **推荐**：将交互逻辑封装到独立的 Client 组件，Page 保持 Server Component

#### 示例

```tsx
// ❌ 错误：整个页面标记为 Client
'use client'
export default function DashboardPage() { ... }

// ✅ 正确：仅交互部分为 Client
// app/(dashboard)/page.tsx (Server Component)
import { DashboardStats } from './components/DashboardStats'
import { InteractiveChart } from './components/InteractiveChart'

export default async function DashboardPage() {
  const data = await fetchDashboardData()
  return (
    <div>
      <DashboardStats data={data} />      {/* Server */}
      <InteractiveChart data={data} />    {/* Client */}
    </div>
  )
}

// components/InteractiveChart.tsx
'use client'
export function InteractiveChart({ data }) {
  const [filter, setFilter] = useState('week')
  // ... 交互逻辑
}
```

---

## 3. 应用布局与导航

### 3.1 App Shell 结构

#### 规则

系统采用标准 Dashboard App Shell 布局：

```
┌─────────────────────────────────────────────────────────┐
│ Header (h-16, fixed top)                                │
├────────────┬────────────────────────────────────────────┤
│            │                                            │
│  Sidebar   │  Main Content Area                         │
│  (w-64,    │  (flex-1, overflow-auto)                   │
│  fixed     │                                            │
│  left)     │  ┌────────────────────────────────────┐    │
│            │  │ Page Container (max-w-7xl mx-auto) │    │
│            │  └────────────────────────────────────┘    │
│            │                                            │
└────────────┴────────────────────────────────────────────┘
```

#### 规则：布局尺寸

| 元素 | 尺寸 | Tailwind 类 |
|------|------|-------------|
| Header 高度 | 64px | `h-16` |
| Sidebar 宽度 | 256px | `w-64` |
| Sidebar 折叠宽度 | 64px | `w-16` |
| 内容区最大宽度 | 1280px | `max-w-7xl` |
| 内容区内边距 | 24px | `p-6` |

#### 规则：响应式断点

| 断点 | 宽度 | 行为 |
|------|------|------|
| `sm` | 640px | 移动端基准 |
| `md` | 768px | Sidebar 可折叠 |
| `lg` | 1024px | Sidebar 默认展开 |
| `xl` | 1280px | 完整桌面布局 |
| `2xl` | 1400px | 大屏优化 |

#### 示例：App Shell 实现

```tsx
// app/(dashboard)/layout.tsx
import { Sidebar } from '@/modules/shared/components/layout/Sidebar'
import { Header } from '@/modules/shared/components/layout/Header'

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      <Header className="fixed top-0 left-0 right-0 h-16 z-50" />
      <div className="flex pt-16">
        <Sidebar className="fixed left-0 w-64 h-[calc(100vh-4rem)] lg:block hidden" />
        <main className="flex-1 lg:ml-64 p-6">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
```

### 3.2 页面结构模式

#### 规则：标准页面结构

每个业务页面必须遵循以下结构：

```tsx
// 列表页模式
<PageContainer>
  <PageHeader title="日报列表" action={<CreateButton />} />
  <FilterBar filters={filters} />
  <DataTable data={data} />
  <Pagination meta={meta} />
</PageContainer>

// 详情页模式
<PageContainer>
  <PageHeader title="日报详情" backLink="/daily-reports" />
  <DetailCard data={data} />
  <ActionBar actions={allowedActions} />
</PageContainer>

// 表单页模式
<PageContainer>
  <PageHeader title="新建日报" backLink="/daily-reports" />
  <FormCard>
    <Form onSubmit={handleSubmit} />
  </FormCard>
</PageContainer>
```

#### 规则：基础组件物理位置

| 组件名 | 物理路径 | 职责 |
|--------|----------|------|
| `PageContainer` | `@/modules/shared/components/layout/PageContainer.tsx` | 页面内容区包装器 |
| `PageHeader` | `@/modules/shared/components/layout/PageHeader.tsx` | 页面标题栏（含返回、操作按钮） |
| `Header` | `@/modules/shared/components/layout/Header.tsx` | 应用顶部导航栏 |
| `Sidebar` | `@/modules/shared/components/layout/Sidebar.tsx` | 侧边菜单导航 |
| `DataTable` | `@/modules/shared/components/data-display/DataTable.tsx` | 通用数据表格 |
| `FilterBar` | `@/modules/shared/components/data-display/FilterBar.tsx` | 筛选条件栏 |
| `Pagination` | `@/modules/shared/components/data-display/Pagination.tsx` | 分页控件 |
| `LoadingSpinner` | `@/modules/shared/components/feedback/LoadingSpinner.tsx` | 加载指示器 |
| `ErrorDisplay` | `@/modules/shared/components/feedback/ErrorDisplay.tsx` | 错误展示 |
| `StatusBadge` | `@/modules/shared/components/ui/StatusBadge.tsx` | 状态标签 |
| `Button` | `@/modules/shared/components/ui/Button.tsx` | 按钮（shadcn 封装） |

> **FE Agent 注意**：生成页面时应优先导入上表中的组件，避免重复造轮子。

---

## 4. 目录结构与组件分层

### 4.1 目录结构

#### 规则

```
frontend/
├── app/                          # Next.js App Router
│   ├── (auth)/                   # 认证相关路由组
│   │   ├── login/page.tsx
│   │   └── layout.tsx
│   ├── (dashboard)/              # 主业务路由组
│   │   ├── daily-reports/
│   │   │   ├── page.tsx          # 列表页
│   │   │   ├── [id]/page.tsx     # 详情页
│   │   │   └── create/page.tsx   # 新建页
│   │   ├── topups/
│   │   ├── ledger/
│   │   ├── reconciliation/
│   │   └── layout.tsx            # Dashboard 布局
│   ├── layout.tsx                # 根布局
│   ├── providers.tsx             # 应用级 Provider（QueryClient 等）
│   └── globals.css
├── src/
│   ├── lib/                      # 核心工具库
│   │   ├── api/                  # API 客户端
│   │   │   ├── apiFetch.ts
│   │   │   ├── apiTypes.ts
│   │   │   ├── apiErrors.ts
│   │   │   ├── queryKeys.ts
│   │   │   └── index.ts          # API 客户端入口（re-export）
│   │   ├── auth/                 # 认证工具
│   │   ├── validation/           # Zod schemas
│   │   └── utils/                # 通用工具函数
│   ├── modules/                  # 业务模块（按领域划分）
│   │   ├── shared/               # 跨模块共享
│   │   │   ├── components/
│   │   │   │   ├── ui/           # 基础 UI（shadcn 封装）
│   │   │   │   ├── layout/       # 布局组件
│   │   │   │   └── feedback/     # 反馈组件
│   │   │   └── hooks/
│   │   ├── daily-reports/        # 日报模块
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── services/
│   │   │   ├── types/
│   │   │   ├── utils/
│   │   │   └── validation/       # Zod schemas
│   │   ├── topups/               # 充值模块
│   │   ├── ledger/               # 账本模块
│   │   └── reconciliation/       # 对账模块
│   ├── stores/                   # 全局 Zustand stores
│   └── types/                    # 全局类型定义
└── tests/
```

#### 规则：路径别名

| 别名 | 指向 | 用途 |
|------|------|------|
| `@/` | `src/` | 所有 src 目录下的导入必须使用此别名 |
| `@/lib` | `src/lib/` | 核心工具库 |
| `@/modules` | `src/modules/` | 业务模块 |
| `@/stores` | `src/stores/` | 全局状态 |
| `@/types` | `src/types/` | 全局类型 |

```tsx
// ❌ 禁止：复杂相对路径
import { apiFetch } from '../../../lib/api/apiFetch'

// ✅ 正确：使用路径别名
import { apiFetch } from '@/lib/api/apiFetch'
import { useAuthStore } from '@/stores/authStore'
import { DailyReportCard } from '@/modules/daily-reports/components/DailyReportCard'
```

> **FE Agent 注意**：生成 import 语句时必须使用 `@/` 别名，禁止使用相对路径 `../`。

### 4.2 组件分层规则

#### 规则：五层组件体系

| 层级 | 目录 | 职责 | 可导入范围 |
|------|------|------|------------|
| Page | `app/**/page.tsx` | 路由入口，数据获取，布局组合 | 所有层 |
| Layout | `app/**/layout.tsx` | 路由组布局，共享 UI 框架 | shared, lib |
| Feature | `modules/{domain}/components/` | 业务组件，领域逻辑 | shared, lib, 同模块 |
| Shared | `modules/shared/components/` | 跨模块复用组件 | ui, lib |
| UI | `modules/shared/components/ui/` | 原子组件，无业务逻辑 | lib only |

#### 规则：组件职责边界

| 组件层 | 允许 | 禁止 |
|--------|------|------|
| UI (原子组件) | 接收 props 渲染、emit 事件 | 直接调用 API、包含业务逻辑 |
| Shared (共享组件) | 复用 UI 组件、简单状态 | 依赖特定业务模块 |
| Feature (业务组件) | 调用 hooks、处理业务逻辑 | 直接写 fetch、硬编码魔法字符串 |
| Page (页面) | 组合组件、SSR 数据获取 | 包含复杂业务逻辑 |

#### 示例：组件分层

```tsx
// ✅ UI 层：纯展示，无业务逻辑
// modules/shared/components/ui/Badge.tsx
export function Badge({ variant, children }: BadgeProps) {
  return <span className={variantStyles[variant]}>{children}</span>
}

// ✅ Shared 层：复用 UI，可含简单逻辑
// modules/shared/components/feedback/LoadingSpinner.tsx
export function LoadingSpinner({ size = 'md' }: LoadingSpinnerProps) {
  return <Spinner className={sizeStyles[size]} />
}

// ✅ Feature 层：业务组件，使用 hooks
// modules/daily-reports/components/DailyReportStatusBadge.tsx
import { Badge } from '@/modules/shared/components/ui/Badge'
import { REPORT_STATUS_CONFIG } from '../utils/statusConfig'

export function DailyReportStatusBadge({ status }: { status: DailyReportStatus }) {
  const config = REPORT_STATUS_CONFIG[status]
  return <Badge variant={config.variant}>{config.label}</Badge>
}
```

### 4.3 命名规范

#### 规则：文件命名

| 类型 | 命名规则 | 示例 |
|------|----------|------|
| 组件文件 | PascalCase | `DailyReportCard.tsx` |
| Hook 文件 | camelCase + use 前缀 | `useDailyReports.ts` |
| 服务文件 | camelCase + Api 后缀 | `dailyReportsApi.ts` |
| 类型文件 | camelCase + .types.ts | `dailyReport.types.ts` |
| 工具文件 | camelCase | `formatCurrency.ts` |
| Store 文件 | camelCase + Store 后缀 | `authStore.ts` |

#### 规则：导出规范

```tsx
// ✅ 组件使用命名导出
export function DailyReportCard() { ... }

// ✅ 类型使用命名导出
export interface DailyReport { ... }
export type DailyReportStatus = ...

// ✅ 模块入口使用 barrel export
// modules/daily-reports/index.ts
export * from './components'
export * from './hooks'
export * from './types'
```

---

## 5. 设计系统：颜色、排版、间距

### 5.1 颜色系统

#### 规则：使用 CSS 变量定义颜色

常规 UI 元素必须通过 Tailwind 配置中的 CSS 变量（设计 token）使用颜色，禁止硬编码十六进制值。

```tsx
// ❌ 禁止：硬编码十六进制颜色
<div className="bg-[#1a1a2e] text-[#eee]">

// ✅ 正确：使用设计 token
<div className="bg-background text-foreground">
```

#### 规则：语义化颜色 Token

| Token | 用途 | CSS 变量 |
|-------|------|----------|
| `background` | 页面/卡片背景 | `--background` |
| `foreground` | 主要文本 | `--foreground` |
| `primary` | 主要操作按钮 | `--primary` |
| `secondary` | 次要操作 | `--secondary` |
| `muted` | 禁用/辅助文本 | `--muted` |
| `accent` | 强调/高亮 | `--accent` |
| `destructive` | 删除/危险操作 | `--destructive` |

#### 规则：状态颜色集中管理

> **说明**：状态颜色是"禁止硬编码颜色"规则的**例外场景**。
> 状态颜色通过 `STATUS_VARIANT_MAP` 常量集中管理，在单一位置定义，全局复用。
> 这不算"硬编码"，因为颜色值只在常量文件中定义一次，组件通过 variant 引用。

| 状态语义 | Variant Key | 对应的 Tailwind 类组合 |
|----------|-------------|------------------------|
| 成功/通过 | `success` | `bg-green-100 text-green-800 border-green-200` |
| 警告/待处理 | `warning` | `bg-yellow-100 text-yellow-800 border-yellow-200` |
| 错误/异常 | `error` | `bg-red-100 text-red-800 border-red-200` |
| 信息/草稿 | `info` | `bg-blue-100 text-blue-800 border-blue-200` |
| 标记/需关注 | `flagged` | `bg-orange-100 text-orange-800 border-orange-200` |
| 终态/锁定 | `locked` | `bg-gray-100 text-gray-800 border-gray-200` |

#### 规则：状态颜色常量位置

状态颜色必须定义在 `@/modules/shared/utils/statusColors.ts`，禁止在组件中散落定义。

```tsx
// @/modules/shared/utils/statusColors.ts（唯一定义位置）
export const STATUS_VARIANT_MAP = {
  success: 'bg-green-100 text-green-800 border-green-200',
  warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  error: 'bg-red-100 text-red-800 border-red-200',
  info: 'bg-blue-100 text-blue-800 border-blue-200',
  flagged: 'bg-orange-100 text-orange-800 border-orange-200',
  locked: 'bg-gray-100 text-gray-800 border-gray-200',
} as const

export type StatusVariant = keyof typeof STATUS_VARIANT_MAP

// 工具函数：根据 variant 获取样式类
export function getStatusClasses(variant: StatusVariant): string {
  return STATUS_VARIANT_MAP[variant]
}
```

```tsx
// ❌ 禁止：在组件中直接写颜色类
<span className="bg-green-100 text-green-800">成功</span>

// ✅ 正确：通过 variant 引用
import { getStatusClasses } from '@/modules/shared/utils/statusColors'
<span className={getStatusClasses('success')}>成功</span>

// ✅ 正确：通过 StatusBadge 组件
<StatusBadge variant="success">成功</StatusBadge>
```

### 5.2 排版系统

#### 规则：字体使用

| 用途 | 字体 | Tailwind 类 |
|------|------|-------------|
| 正文 | Inter | `font-sans` (默认) |
| 代码 | JetBrains Mono | `font-mono` |

#### 规则：字号层级

| 语义 | 大小 | Tailwind 类 | 用途 |
|------|------|-------------|------|
| h1 | 30px | `text-3xl font-bold` | 页面主标题 |
| h2 | 24px | `text-2xl font-semibold` | 区块标题 |
| h3 | 20px | `text-xl font-semibold` | 卡片标题 |
| h4 | 16px | `text-base font-medium` | 小标题 |
| body | 14px | `text-sm` | 正文内容 |
| caption | 12px | `text-xs` | 辅助说明 |

### 5.3 间距系统

#### 规则：间距比例

使用 4px 基准的间距系统：

| Token | 值 | Tailwind | 用途 |
|-------|-----|----------|------|
| 1 | 4px | `p-1` | 紧凑元素内边距 |
| 2 | 8px | `p-2` | 按钮内边距 |
| 3 | 12px | `p-3` | 小卡片内边距 |
| 4 | 16px | `p-4` | 标准内边距 |
| 6 | 24px | `p-6` | 大卡片/区块内边距 |
| 8 | 32px | `p-8` | 页面级间距 |

#### 规则：组件间距

| 场景 | 间距 | 示例 |
|------|------|------|
| 同组元素 | 8px | `gap-2` / `space-y-2` |
| 不同组元素 | 16px | `gap-4` / `space-y-4` |
| 区块分隔 | 24px | `gap-6` / `mb-6` |
| 页面区块 | 32px | `gap-8` / `py-8` |

---

## 6. 状态枚举与 SoT 对齐

### 6.1 状态类型定义

#### 规则：状态枚举引用 SoT

> **重要**：状态枚举的完整定义以 `STATE_MACHINE.md` 和 `DATA_SCHEMA.md` 为唯一 SoT。
> 前端类型文件 (`modules/{domain}/types/*.types.ts`) 必须与 SoT 保持同步。
> 本节仅展示**代码组织模式**，具体枚举值请查阅对应 SoT 文档。

#### 示例：状态类型定义模式

```tsx
// modules/daily-reports/types/dailyReport.types.ts

/**
 * 日报状态枚举
 *
 * ⚠️ 完整状态列表和流转规则请参阅：
 *    - STATE_MACHINE.md v2.6 第 8 章
 *    - DATA_SCHEMA.md v5.2 daily_reports.status 字段
 *
 * 此处仅为类型定义示例，实际枚举值以 SoT 文档为准。
 */
export type DailyReportStatus =
  | 'raw_submitted'
  | 'trend_pending'
  | 'trend_ok'
  | 'trend_flagged'
  | 'trend_resolved'
  | 'final_pending'
  | 'final_confirmed'
  | 'final_locked'
  // ... 完整列表请查阅 STATE_MACHINE.md
```

#### 规则：状态显示配置

每个状态类型必须有对应的显示配置，配置结构如下：

#### 示例：状态显示配置模式

```tsx
// modules/daily-reports/utils/statusConfig.ts
import type { DailyReportStatus } from '../types'
import type { StatusVariant } from '@/modules/shared/utils/statusColors'

/**
 * 状态配置接口
 */
interface StatusConfig {
  label: string           // 显示文本
  variant: StatusVariant  // 颜色变体（引用 STATUS_VARIANT_MAP）
  icon: string            // lucide-react 图标名
  allowEdit: boolean      // 是否允许编辑
}

/**
 * 日报状态显示配置
 *
 * ⚠️ 状态流转规则（allowTransitions）不在此定义。
 *    流转白名单以 STATE_MACHINE.md v2.6 第 8.2 节为准。
 *    前端只负责 UI 展示，状态变更由后端 API 校验。
 */
export const REPORT_STATUS_CONFIG: Record<DailyReportStatus, StatusConfig> = {
  raw_submitted: { label: '已提交', variant: 'info', icon: 'FileCheck', allowEdit: true },
  trend_pending: { label: '趋势检查中', variant: 'warning', icon: 'Clock', allowEdit: false },
  trend_ok: { label: '趋势正常', variant: 'success', icon: 'CheckCircle', allowEdit: true },
  trend_flagged: { label: '趋势异常', variant: 'flagged', icon: 'AlertTriangle', allowEdit: true },
  trend_resolved: { label: '异常已解决', variant: 'success', icon: 'CheckCircle2', allowEdit: true },
  final_pending: { label: '待确认', variant: 'warning', icon: 'FileQuestion', allowEdit: false },
  final_confirmed: { label: '已确认', variant: 'success', icon: 'FileCheck2', allowEdit: false },
  final_locked: { label: '已锁定', variant: 'locked', icon: 'Lock', allowEdit: false }, // INV-002
  // ... 完整配置请参照实际 types 文件
}
```

> **FE Agent 注意**：生成状态相关代码时，必须从 `modules/{domain}/types` 导入类型定义，从 `modules/{domain}/utils/statusConfig` 导入显示配置。不要在组件中硬编码状态字符串。

### 6.2 终态不可变规则

#### 规则：INV-002 终态不可修改

根据 `MASTER.md` v3.5 INV-002，终态记录不可修改，前端必须：

1. **禁用编辑按钮**：当 `status === 'final_locked'` 时
2. **隐藏删除操作**：终态记录不可删除
3. **显示锁定提示**：告知用户记录已锁定

```tsx
// ✅ 正确：根据状态禁用编辑
function ReportActions({ report }: { report: DailyReport }) {
  const config = REPORT_STATUS_CONFIG[report.status]

  return (
    <div className="flex gap-2">
      {config.allowEdit ? (
        <Button onClick={handleEdit}>编辑</Button>
      ) : (
        <Button disabled title="此状态下不可编辑">
          编辑
        </Button>
      )}

      {report.status === 'final_locked' && (
        <div className="text-sm text-muted-foreground flex items-center gap-1">
          <Lock className="w-4 h-4" />
          <span>记录已锁定 (INV-002)</span>
        </div>
      )}
    </div>
  )
}
```

---

## 7. API 调用与数据流

### 7.1 apiFetch 规则

#### 规则：统一使用 apiFetch

所有 API 调用必须通过 `lib/api/apiFetch.ts`，禁止直接使用 fetch 或 axios。

#### 规则：API 客户端导入路径

- **统一入口**：所有 API 客户端方法从 `@/lib/api` 导入
- **index.ts 约定**：`src/lib/api/index.ts` 负责 re-export `apiFetch`、`queryKeys` 等

```tsx
// src/lib/api/index.ts（入口文件）
export { apiFetch } from './apiFetch'
export { queryKeys } from './queryKeys'
export { ApiError, getErrorMessage } from './apiErrors'
export type { ApiResponse, PaginatedResponse } from './apiTypes'
```

```tsx
// ❌ 禁止：直接使用 fetch
const res = await fetch('/api/v1/daily-reports')

// ❌ 禁止：直接使用 axios
const res = await axios.get('/api/v1/daily-reports')

// ❌ 禁止：直接导入内部文件
import { apiFetch } from '@/lib/api/apiFetch'

// ✅ 正确：从统一入口导入
import { apiFetch } from '@/lib/api'
const data = await apiFetch<DailyReport[]>('/api/v1/daily-reports')
```

#### 规则：apiFetch 响应格式

响应格式对齐 `API_SOT.md` v9.0 Section 4：

```tsx
// lib/api/apiTypes.ts
interface ApiResponse<T> {
  success: boolean
  data: T | null
  message: string
  code: string
  request_id: string
  timestamp: string
}

interface ApiError {
  success: false
  error: {
    code: string      // ERROR_CODES_SOT.md v2.1
    message: string
    details?: Record<string, unknown>
  }
  request_id: string
  timestamp: string
}
```

### 7.2 TanStack Query 规范

#### 规则：Query Key 工厂模式

```tsx
// lib/api/queryKeys.ts
export const queryKeys = {
  dailyReports: {
    all: ['daily-reports'] as const,
    lists: () => [...queryKeys.dailyReports.all, 'list'] as const,
    list: (filters: DailyReportFilters) =>
      [...queryKeys.dailyReports.lists(), filters] as const,
    detail: (id: number) =>
      [...queryKeys.dailyReports.all, 'detail', id] as const,
  },
  topups: {
    all: ['topups'] as const,
    list: (filters: TopupFilters) =>
      [...queryKeys.topups.all, 'list', filters] as const,
    detail: (id: number) =>
      [...queryKeys.topups.all, 'detail', id] as const,
  },
} as const
```

#### 规则：Query Hook 模式

```tsx
// modules/daily-reports/hooks/useDailyReports.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { dailyReportsApi } from '../services/dailyReportsApi'
import { queryKeys } from '@/lib/api/queryKeys'

// ✅ 列表查询
export function useDailyReportsList(filters: DailyReportFilters) {
  return useQuery({
    queryKey: queryKeys.dailyReports.list(filters),
    queryFn: () => dailyReportsApi.list(filters),
    staleTime: 5 * 60 * 1000, // 5 分钟
  })
}

// ✅ 详情查询
export function useDailyReportDetail(id: number) {
  return useQuery({
    queryKey: queryKeys.dailyReports.detail(id),
    queryFn: () => dailyReportsApi.getById(id),
    enabled: !!id,
  })
}

// ✅ 变更操作
export function useDailyReportSubmit() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => dailyReportsApi.submit(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.dailyReports.all })
    },
  })
}
```

#### 规则：QueryClientProvider 放置位置

QueryClient 必须在应用根部创建一次，通过 Provider 传递给整个组件树。

```tsx
// ✅ 正确：在 app/providers.tsx 中创建并提供
// app/providers.tsx
'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'

export function Providers({ children }: { children: React.ReactNode }) {
  // 使用 useState 确保每个请求创建独立的 QueryClient（SSR 安全）
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000,
        refetchOnWindowFocus: false,
      },
    },
  }))

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

// app/layout.tsx
import { Providers } from './providers'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
```

```tsx
// ❌ 禁止：在页面或组件中重复创建 QueryClient
function SomePage() {
  const queryClient = new QueryClient() // 错误！
  return <QueryClientProvider client={queryClient}>...</QueryClientProvider>
}
```

> **FE Agent 注意**：生成组件时直接使用 `useQuery` / `useMutation`，不需要创建 QueryClient。

### 7.3 Zod 表单验证

#### 规则：表单必须使用 Zod 校验

所有表单提交前必须使用 Zod schema 进行客户端验证。

#### 规则：Schema 存放位置

| Schema 类型 | 存放位置 | 说明 |
|-------------|----------|------|
| 通用 Schema | `@/lib/validation/common.ts` | 如日期、货币、UUID 等通用格式 |
| 领域 Schema | `@/modules/{domain}/validation/{entity}.schema.ts` | 如日报表单、充值表单 |

#### 规则：Schema 与 SoT 对齐

Zod schema 的字段定义必须与 `DATA_SCHEMA.md` v5.2 保持一致。

#### 示例：表单验证模式

```tsx
// @/modules/topups/validation/topupRequest.schema.ts
import { z } from 'zod'

/**
 * 充值请求表单 Schema
 * @sot DATA_SCHEMA.md v5.2 topup_requests 表
 */
export const topupRequestSchema = z.object({
  ad_account_id: z.string().uuid('请选择广告账户'),
  amount_requested: z.number()
    .positive('金额必须大于 0')
    .max(1000000, '单笔最大 100 万'),
  currency_code: z.enum(['CNY', 'USD'], { message: '请选择币种' }),
  urgency_level: z.enum(['normal', 'urgent']).default('normal'),
  notes: z.string().max(500).optional(),
})

export type TopupRequestFormData = z.infer<typeof topupRequestSchema>
```

```tsx
// 组件中使用
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { topupRequestSchema, type TopupRequestFormData } from '../validation/topupRequest.schema'

function TopupForm() {
  const form = useForm<TopupRequestFormData>({
    resolver: zodResolver(topupRequestSchema),
    defaultValues: { urgency_level: 'normal' },
  })

  // ...
}
```

### 7.4 错误处理

#### 规则：错误码映射

错误码必须与 `ERROR_CODES_SOT.md` v2.1 对齐：

```tsx
// lib/api/apiErrors.ts
export const ERROR_MESSAGES: Record<string, string> = {
  // 认证错误
  AUTH_001: '用户名或密码错误',
  AUTH_400: '未提供认证令牌',
  AUTH_401: '无效的认证令牌',
  AUTH_402: '认证令牌已过期',
  AUTH_500: '权限不足',

  // 业务错误
  BIZ_001: '资源不存在',
  BIZ_002: '记录未找到',
  BIZ_301: '状态转换非法',

  // 状态机错误
  STATE_001: '非法状态转换',
  STATE_002: '终态不可修改',
  STATE_409: '并发冲突，请刷新重试',

  // 验证错误
  VALIDATION_001: '必填字段缺失',
  VALIDATION_010: '数据格式错误',
}

export function getErrorMessage(code: string): string {
  return ERROR_MESSAGES[code] || '操作失败，请重试'
}
```

---

## 8. 权限与交互模式

### 8.1 权限控制策略

#### 规则：两种权限场景

| 场景 | 处理方式 | 示例 |
|------|----------|------|
| 模块/菜单入口无权限 | **隐藏** | 无 `topups:read` 权限时隐藏「充值」菜单 |
| 按钮/操作无权限 | **禁用 + 提示** | 无 `topups:approve` 权限时禁用「批准」按钮并显示 tooltip |

#### 规则：权限 Hook

```tsx
// modules/shared/hooks/usePermission.ts
import { useAuthStore } from '@/stores/authStore'

export function usePermission() {
  const user = useAuthStore((s) => s.user)

  const hasPermission = (permission: string): boolean => {
    return user?.permissions?.includes(permission) ?? false
  }

  const hasAnyPermission = (permissions: string[]): boolean => {
    return permissions.some(hasPermission)
  }

  const hasAllPermissions = (permissions: string[]): boolean => {
    return permissions.every(hasPermission)
  }

  return { hasPermission, hasAnyPermission, hasAllPermissions }
}
```

### 8.2 权限组件模式

#### 规则：PermissionGate 组件

```tsx
// modules/shared/components/auth/PermissionGate.tsx
interface PermissionGateProps {
  permission: string | string[]
  mode?: 'hide' | 'disable'
  fallback?: React.ReactNode
  disabledMessage?: string
  children: React.ReactNode
}

export function PermissionGate({
  permission,
  mode = 'hide',
  fallback = null,
  disabledMessage = '您没有此操作的权限',
  children,
}: PermissionGateProps) {
  const { hasPermission, hasAnyPermission } = usePermission()

  const hasAccess = Array.isArray(permission)
    ? hasAnyPermission(permission)
    : hasPermission(permission)

  if (!hasAccess) {
    if (mode === 'hide') {
      return <>{fallback}</>
    }
    // mode === 'disable'
    return (
      <Tooltip content={disabledMessage}>
        <div className="opacity-50 cursor-not-allowed">
          {children}
        </div>
      </Tooltip>
    )
  }

  return <>{children}</>
}
```

#### 示例：权限使用

```tsx
import Link from 'next/link'

// 隐藏无权限菜单（使用 Next.js Link）
<PermissionGate permission="admin:read" mode="hide">
  <Link href="/admin">管理后台</Link>
</PermissionGate>

// 禁用无权限按钮
<PermissionGate permission="topups:approve" mode="disable">
  <Button onClick={handleApprove}>批准</Button>
</PermissionGate>

// 带 fallback 的只读视图
<PermissionGate
  permission="reports:edit"
  mode="hide"
  fallback={<ReadOnlyReportView data={data} />}
>
  <EditableReportForm data={data} />
</PermissionGate>
```

---

## 9. Anti-Pattern（禁止事项）

### 规则：必须避免的 12 个常见错误

| # | Anti-Pattern | 正确做法 |
|---|--------------|----------|
| 1 | 在 `page.tsx` 或 `layout.tsx` 顶层写 `'use client'` | 将交互逻辑拆分到独立的 Client 组件 |
| 2 | 在组件内直接写 `fetch()` 或 `axios` | 使用 `apiFetch` + TanStack Query hooks |
| 3 | 硬编码状态字符串 `status === 'pending'` | 使用 `types/` 中的类型和 `utils/statusConfig` 中的配置 |
| 4 | 硬编码十六进制颜色 `bg-[#ff0000]` | 使用设计 token 或 `STATUS_VARIANT_MAP` |
| 5 | 在 UI 组件中调用 API | UI 组件只接收 props 和 emit 事件，API 调用在 hooks 中 |
| 6 | 使用 `any` 类型 | 定义明确的 TypeScript 类型 |
| 7 | 在组件中定义魔法数字 | 使用常量文件统一管理 |
| 8 | 忽略加载/错误状态 | 必须处理 `isLoading`、`isError` 和 `error` |
| 9 | 不处理终态（如 `final_locked`） | 根据 INV-002 禁用编辑操作 |
| 10 | 在 Server Component 中使用 useState/useEffect | 仅在 Client Component 中使用 React hooks |
| 11 | 在 `app/(dashboard)/` 下创建 `components/` 目录 | 所有可复用组件必须放在 `src/modules/` 分层中 |
| 12 | 在页面/组件内创建 QueryClient | QueryClient 只在 `app/providers.tsx` 中创建一次 |

### 示例：Anti-Pattern 对照

```tsx
// ❌ Anti-Pattern #1：整个页面 Client
'use client'
export default function ReportsPage() { ... }

// ✅ 正确：Page 保持 Server，交互拆分
// app/(dashboard)/reports/page.tsx
import { ReportFilters } from './components/ReportFilters'
export default async function ReportsPage() {
  const data = await fetchInitialData()
  return <ReportFilters initialData={data} />
}

// ❌ Anti-Pattern #2：直接 fetch
function ReportList() {
  useEffect(() => {
    fetch('/api/v1/reports').then(...)
  }, [])
}

// ✅ 正确：使用 Query Hook
function ReportList() {
  const { data, isLoading, error } = useReportsList()
  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorDisplay error={error} />
  return <DataTable data={data} />
}

// ❌ Anti-Pattern #3：硬编码状态
{report.status === 'final_locked' && <Badge>已锁定</Badge>}

// ✅ 正确：使用配置常量
const config = REPORT_STATUS_CONFIG[report.status]
<Badge variant={config.variant}>{config.label}</Badge>
```

---

## 10. 前端开发自检清单

### 10.1 开发前检查

- [ ] 确认需求对应的 SoT 文档版本（STATE_MACHINE、DATA_SCHEMA、API_SOT）
- [ ] 确认涉及的状态枚举已在 `types/` 中定义
- [ ] 确认 API 端点已在 `services/` 中封装

### 10.2 组件开发检查

- [ ] 组件放置在正确的目录层级（ui/shared/features）
- [ ] 使用正确的命名规范（PascalCase/camelCase）
- [ ] 定义了 Props 接口并使用类型标注
- [ ] 处理了 loading、error、empty 状态
- [ ] Client 组件边界最小化

### 10.3 样式检查

- [ ] 使用 Tailwind 类而非内联样式
- [ ] 颜色使用设计 token 而非硬编码值
- [ ] 间距遵循 4px 基准系统
- [ ] 状态颜色通过 `STATUS_VARIANT_MAP` 统一管理

### 10.4 数据流检查

- [ ] API 调用通过 `apiFetch` 封装
- [ ] 使用 TanStack Query 管理服务端状态
- [ ] Query Key 遵循工厂模式
- [ ] Mutation 后正确 invalidate 相关 queries
- [ ] 未在组件内创建 QueryClient（使用全局 Providers）
- [ ] 表单使用 Zod schema 进行验证
- [ ] 导入路径使用 `@/` 别名

### 10.5 权限检查

- [ ] 模块入口使用 `PermissionGate` 隐藏无权限菜单
- [ ] 操作按钮使用 `PermissionGate` 禁用并提示
- [ ] 终态（如 `final_locked`）禁用编辑操作

### 10.6 SoT 对齐检查

- [ ] 状态枚举与 STATE_MACHINE.md v2.6 一致
- [ ] 字段定义与 DATA_SCHEMA.md v5.2 一致
- [ ] API 路径与 API_SOT.md v9.0 一致
- [ ] 错误码与 ERROR_CODES_SOT.md v2.1 一致
- [ ] 权限字符串与 AUTH_SPEC.md v2.0 一致

---

## 11. SoT 关系索引

| SoT 文档 | 版本 | 前端应用 |
|----------|------|----------|
| `STATE_MACHINE.md` | v2.6 | 状态枚举、流转白名单、UI 状态映射 |
| `DATA_SCHEMA.md` | v5.2 | 实体类型定义、字段校验规则 |
| `API_SOT.md` | v9.0 | API 端点、请求/响应格式、分页参数 |
| `ERROR_CODES_SOT.md` | v2.1 | 错误码映射、用户提示消息 |
| `AUTH_SPEC.md` | v2.0 | 权限字符串、角色定义 |
| `BUSINESS_RULES.md` | v3.1 | 表单校验规则、业务约束 |
| `MASTER.md` | v3.5 | 全局不变量（INV-002 终态不可变） |

---

## 附录 A：快速参考卡片

### A.1 组件层级速查

```
Page → Layout → Feature → Shared → UI
  ↓       ↓        ↓         ↓      ↓
路由    布局    业务组件   复用组件  原子组件
```

### A.2 状态颜色速查

> **注意**：本表仅为视觉速查参考。实际生效的颜色配置以 `STATUS_VARIANT_MAP` 为唯一 SoT（定义在 `@/modules/shared/utils/statusColors.ts`）。当本表与代码不一致时，以代码为准。

| 语义 | Variant Key | Tailwind 类 | 用于 |
|------|-------------|-------------|------|
| 成功 | `success` | `bg-green-100 text-green-800` | ok, confirmed, completed |
| 警告 | `warning` | `bg-yellow-100 text-yellow-800` | pending |
| 错误 | `error` | `bg-red-100 text-red-800` | rejected, failed |
| 信息 | `info` | `bg-blue-100 text-blue-800` | submitted, draft |
| 标记 | `flagged` | `bg-orange-100 text-orange-800` | flagged |
| 锁定 | `locked` | `bg-gray-100 text-gray-800` | locked |

### A.3 命名速查

| 类型 | 规则 | 示例 |
|------|------|------|
| 组件 | PascalCase | `DailyReportCard.tsx` |
| Hook | use + camelCase | `useDailyReports.ts` |
| 服务 | camelCase + Api | `dailyReportsApi.ts` |
| 类型 | camelCase + .types | `dailyReport.types.ts` |

---

**文档版本**: v2.1
**状态**: candidate_freeze（待验证）
**最后更新**: 2025-12-03
**维护者**: wade
**基准**: MASTER.md v3.5, SoT Freeze v2.6, Dev-Guides Freeze vFinal

> **变更说明 (v2.0 → v2.1)**:
> - 技术栈版本改为"以 package.json 为准"
> - 修复 NavLink → Next.js Link
> - 状态枚举降级为示例模式，SoT 指向 STATE_MACHINE.md
> - 增加路径别名、QueryClientProvider、Zod 验证规范
> - 增加基础组件物理位置表
> - 澄清状态颜色集中管理机制
> - Anti-Pattern 从 10 条扩展到 12 条
