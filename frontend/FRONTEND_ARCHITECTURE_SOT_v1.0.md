# 前端渐进式目录重构计划 v1.2

> **文档状态**: SoT (Source of Truth)
> **创建日期**: 2025-12-08
> **更新日期**: 2025-12-08
> **目标**: 对齐 Kiranism/next-shadcn-dashboard-starter 架构
> **Phase 0**: ✅ 已完成 (2025-12-08)
> **Phase 1**: ✅ 已完成 (2025-12-08)
> **Phase 2**: ✅ 已完成 (2025-12-08)

---

## 1. 当前状态分析

### 1.1 现有目录结构问题

```
frontend/
├── app/                          # ❌ 旧入口 (混乱)
│   ├── (auth)/                   # 路由组已建
│   ├── (dashboard)/              # 路由组已建，但包含业务组件
│   │   └── projects/components/  # ❌ 反模式：组件与路由混放
│   ├── layout.tsx
│   └── globals.css
├── components/                   # ⚠️ 全局组件，但分类不清
│   ├── ui/                       # shadcn 组件
│   ├── layout/                   # 布局组件
│   ├── dashboard/                # Dashboard 专用组件
│   ├── projects/                 # ❌ 应迁移到 features/
│   ├── ad-accounts/              # ❌ 应迁移到 features/
│   └── ...
├── src/
│   ├── app/                      # ✅ 新入口 (需整合)
│   │   ├── projects/page.tsx     # ⚠️ 未放入路由组
│   │   └── ...
│   ├── features/                 # ✅ 业务模块 (需补全)
│   │   ├── projects/
│   │   ├── daily-reports/
│   │   └── ...
│   ├── lib/                      # ✅ 工具库
│   └── types/                    # ✅ 全局类型
└── tsconfig.json
```

### 1.2 关键问题清单

| 问题 | 严重程度 | 影响 |
|------|----------|------|
| 双入口 (app/ + src/app/) | 🔴 高 | 路由冲突、构建不稳定 |
| 业务组件散落在 components/ | 🟡 中 | 模块边界模糊 |
| 路由组未完整使用 | 🟡 中 | Layout 复用受限 |
| @/components/* 指向旧目录 | 🟡 中 | 迁移后 import 断裂 |

### 1.3 目标结构 (对齐 Kiranism 模板)

```
frontend/
├── src/
│   ├── app/                      # 仅路由壳
│   │   ├── (auth)/               # 认证路由组
│   │   │   ├── login/page.tsx
│   │   │   └── layout.tsx
│   │   ├── (dashboard)/          # 后台路由组
│   │   │   ├── projects/page.tsx
│   │   │   ├── daily-reports/page.tsx
│   │   │   └── layout.tsx
│   │   ├── layout.tsx            # 根布局
│   │   ├── globals.css
│   │   └── providers.tsx
│   │
│   ├── components/               # 全局共享组件
│   │   ├── ui/                   # shadcn 原子组件
│   │   ├── layout/               # Header, Sidebar, AppShell
│   │   └── shared/               # ErrorBoundary, DataState 等
│   │
│   ├── features/                 # 业务模块 ⭐
│   │   ├── projects/
│   │   │   ├── components/       # ProjectsPage, ProjectsTable
│   │   │   ├── hooks/            # useProjects
│   │   │   ├── services/         # projectsApi
│   │   │   ├── schemas/          # projectSchema (Zod)
│   │   │   ├── types/            # Project, ProjectFilter
│   │   │   └── index.ts          # 公开导出
│   │   └── ...
│   │
│   ├── hooks/                    # 全局 hooks
│   │   ├── use-table-params.ts   # nuqs 封装
│   │   └── use-media-query.ts
│   │
│   ├── lib/                      # 工具库
│   │   ├── api.ts                # API client
│   │   ├── utils.ts              # cn() 等
│   │   ├── constants.ts          # 常量
│   │   └── format.ts             # 格式化
│   │
│   ├── stores/                   # Zustand stores
│   │   └── auth-store.ts
│   │
│   └── types/                    # 全局类型
│       ├── common.ts
│       └── api.ts
│
├── public/
├── tsconfig.json
├── next.config.js
└── package.json
```

---

## 2. 重构阶段划分

### Phase 0: 入口整合与基础设施 (低风险)

**目标**: 统一入口为 `src/app/`，建立目录骨架

#### 步骤 0.1: 统一 app 入口

| 操作 | 旧路径 | 新路径 |
|------|--------|--------|
| 移动根布局 | `app/layout.tsx` | `src/app/layout.tsx` (已存在，合并) |
| 移动全局样式 | `app/globals.css` | `src/app/globals.css` (已存在) |
| 移动 providers | `app/providers.tsx` | `src/app/providers.tsx` (已存在) |
| 删除旧入口 | `app/layout.tsx` | 删除 |

**注意**: Next.js 14+ 默认查找 `app/` 目录，需要在 `next.config.js` 中配置:

```js
// next.config.js 需添加
experimental: {
  appDir: true,
},
// 或使用 src/ 结构时 Next.js 会自动检测 src/app/
```

#### 步骤 0.2: 建立路由组结构

```
src/app/
├── (auth)/
│   ├── layout.tsx         # 认证页面布局 (居中卡片)
│   ├── login/page.tsx
│   ├── sign-up/page.tsx
│   ├── forgot-password/page.tsx
│   └── update-password/page.tsx
├── (dashboard)/
│   ├── layout.tsx         # Dashboard 布局 (Sidebar + Header)
│   ├── page.tsx           # /dashboard 首页
│   ├── projects/page.tsx
│   ├── daily-reports/page.tsx
│   └── ...
├── layout.tsx             # 根布局
├── globals.css
└── providers.tsx
```

#### 步骤 0.3: 迁移全局组件到 src/components/

| 操作 | 旧路径 | 新路径 |
|------|--------|--------|
| ui 组件 | `components/ui/*` | `src/components/ui/*` |
| 布局组件 | `components/layout/*` | `src/components/layout/*` |
| 共享组件 | `components/shared/*` | `src/components/shared/*` |
| Dashboard 布局 | `components/dashboard/AppLayout.tsx` | `src/components/layout/AppLayout.tsx` |
| Dashboard 布局 | `components/dashboard/sidebar.tsx` | `src/components/layout/Sidebar.tsx` |
| Dashboard 布局 | `components/dashboard/header.tsx` | `src/components/layout/Header.tsx` |

#### 步骤 0.4: 更新 tsconfig.json paths

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@/components/*": ["./src/components/*"],
      "@/features/*": ["./src/features/*"],
      "@/lib/*": ["./src/lib/*"],
      "@/hooks/*": ["./src/hooks/*"],
      "@/stores/*": ["./src/stores/*"],
      "@/types/*": ["./src/types/*"]
    }
  }
}
```

**删除的别名**:
- ~~`@/modules/*`~~ → 统一使用 `@/features/*`

#### 步骤 0.5: 创建缺失的目录骨架

```bash
# 需要创建的空目录 (加 .gitkeep)
src/hooks/
src/stores/
```

#### Phase 0 验收标准

- [ ] `npm run dev` 正常启动
- [ ] 访问 `/login` 页面正常渲染
- [ ] 访问 `/projects` 页面正常渲染 (Dashboard 布局生效)
- [ ] `npm run build` 无 TypeScript 错误
- [ ] 旧 `app/` 目录已删除或标记废弃

---

### Phase 1: 业务模块迁移 (中风险)

**目标**: 将散落的业务组件整合到 `features/`

#### 模块清单与优先级

| 模块 | 当前状态 | 迁移优先级 | 依赖 |
|------|----------|------------|------|
| projects | 部分在 features/ | P0 | - |
| channels | 部分在 features/ | P0 | - |
| suppliers | 已在 features/ | ✅ 完成 | - |
| transfers | 已在 features/ | ✅ 完成 | - |
| settlements | 已在 features/ | ✅ 完成 | - |
| daily-reports | 部分在 features/ | P1 | - |
| reconciliation | 部分在 features/ | P1 | - |
| topups | 部分在 features/ | P1 | - |
| ledger | 部分在 features/ | P1 | - |
| ad-accounts | 在 components/ | P1 | - |
| finance-profit | 部分在 features/ | P2 | - |
| import-jobs | 部分在 features/ | P2 | - |
| reports | 部分在 features/ | P2 | - |

#### 步骤 1.1: 迁移 projects 模块 (示例)

**旧文件分布**:
```
components/projects/
├── project-form.tsx
├── project-kanban.tsx
└── modern-project-detail.tsx

app/(dashboard)/projects/
├── page.tsx
├── [id]/page.tsx
├── types.ts
└── components/
    ├── ProjectFilters.tsx
    ├── ProjectSummaryCards.tsx
    └── ProjectTable.tsx

src/features/projects/          # 已存在部分
├── components/
│   ├── ProjectsPage.tsx
│   ├── ProjectsTable.tsx
│   └── ProjectForm.tsx
├── hooks/useProjects.ts
├── services/projectsApi.ts
├── types/project.types.ts
└── index.ts
```

**迁移映射表**:

| 旧路径 | 新路径 | 操作 |
|--------|--------|------|
| `components/projects/project-form.tsx` | `src/features/projects/components/ProjectForm.tsx` | 合并或替换 |
| `components/projects/project-kanban.tsx` | `src/features/projects/components/ProjectKanban.tsx` | 移动 |
| `components/projects/modern-project-detail.tsx` | `src/features/projects/components/ProjectDetail.tsx` | 移动并重命名 |
| `app/(dashboard)/projects/types.ts` | `src/features/projects/types/project.types.ts` | 合并 |
| `app/(dashboard)/projects/components/*` | `src/features/projects/components/*` | 合并 |

**最终 projects 模块结构**:
```
src/features/projects/
├── components/
│   ├── ProjectsPage.tsx        # 列表页主组件
│   ├── ProjectsTable.tsx       # 表格组件
│   ├── ProjectForm.tsx         # 表单组件
│   ├── ProjectDetail.tsx       # 详情组件
│   ├── ProjectFilters.tsx      # 筛选器
│   ├── ProjectSummaryCards.tsx # 统计卡片
│   ├── ProjectKanban.tsx       # 看板视图
│   └── index.ts                # 导出
├── hooks/
│   ├── useProjects.ts          # 列表 hook
│   ├── useProject.ts           # 单条 hook
│   └── index.ts
├── services/
│   ├── projectsApi.ts          # API 调用
│   └── index.ts
├── schemas/
│   ├── project.schema.ts       # Zod schema
│   └── index.ts
├── types/
│   ├── project.types.ts        # TypeScript 类型
│   └── index.ts
└── index.ts                    # 公开导出
```

#### 步骤 1.2: 页面壳化

**app/page.tsx 应该只是一个薄壳**:

```tsx
// src/app/(dashboard)/projects/page.tsx
import { ProjectsPage } from '@/features/projects';

export default function Page() {
  return <ProjectsPage />;
}
```

```tsx
// src/app/(dashboard)/projects/[id]/page.tsx
import { ProjectDetail } from '@/features/projects';

export default function Page({ params }: { params: { id: string } }) {
  return <ProjectDetail id={params.id} />;
}
```

#### 步骤 1.3: 迁移 ad-accounts 模块

| 旧路径 | 新路径 |
|--------|--------|
| `components/ad-accounts/ad-account-form.tsx` | `src/features/ad-accounts/components/AdAccountForm.tsx` |
| `components/ad-accounts/batch-operations.tsx` | `src/features/ad-accounts/components/BatchOperations.tsx` |
| `app/(dashboard)/ad-accounts/components/*` | `src/features/ad-accounts/components/*` |
| `app/(dashboard)/ad-accounts/types.ts` | `src/features/ad-accounts/types/` |

#### 步骤 1.4: 迁移 daily-reports 模块

| 旧路径 | 新路径 |
|--------|--------|
| `components/daily-reports/*` | `src/features/daily-reports/components/*` |
| `app/(dashboard)/daily-reports/components/*` | `src/features/daily-reports/components/*` |
| `app/(dashboard)/daily-reports/types.ts` | `src/features/daily-reports/types/` |

#### 步骤 1.5: 迁移 reconciliation 模块

| 旧路径 | 新路径 |
|--------|--------|
| `components/reconciliation/*` | `src/features/reconciliation/components/*` |
| `app/(dashboard)/reconciliation/components/*` | `src/features/reconciliation/components/*` |

#### 步骤 1.6: 迁移 finance 模块

| 旧路径 | 新路径 |
|--------|--------|
| `components/finance/topup-request-form.tsx` | `src/features/topups/components/TopupRequestForm.tsx` |

#### Phase 1 验收标准

- [ ] `components/` 下不再有业务模块目录 (projects, ad-accounts, daily-reports, reconciliation, finance)
- [ ] `app/(dashboard)/*/components/` 目录已清空
- [ ] 所有业务模块都有完整的 features/xxx 结构
- [ ] 所有页面正常访问，功能不变
- [ ] TypeScript 编译无错误

---

### Phase 2: 增强能力引入 (低风险)

**目标**: 引入 nuqs、TanStack Table、ErrorBoundary 等

#### 步骤 2.1: 安装 nuqs 并创建 URL 状态管理 hook

```bash
npm install nuqs
```

创建 `src/hooks/use-table-params.ts`:
```tsx
// 封装分页、筛选、排序的 URL 状态管理
import { parseAsInteger, parseAsString, useQueryStates } from 'nuqs';

export function useTableParams() {
  return useQueryStates({
    page: parseAsInteger.withDefault(1),
    pageSize: parseAsInteger.withDefault(20),
    search: parseAsString.withDefault(''),
    sortBy: parseAsString,
    sortOrder: parseAsString,
  });
}
```

#### 步骤 2.2: 配置全局 ErrorBoundary

创建 `src/components/shared/GlobalErrorBoundary.tsx`

在 `src/app/layout.tsx` 中包裹:
```tsx
<GlobalErrorBoundary>
  <Providers>{children}</Providers>
</GlobalErrorBoundary>
```

#### 步骤 2.3: 配置 React Query 全局错误处理

在 `src/app/providers.tsx` 中:
```tsx
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 5 * 60 * 1000,
    },
    mutations: {
      onError: (error) => {
        toast.error(error.message);
      },
    },
  },
});
```

#### 步骤 2.4: 创建通用 DataTable 组件

位置: `src/components/ui/data-table/`
```
src/components/ui/data-table/
├── DataTable.tsx           # 主组件
├── DataTablePagination.tsx # 分页
├── DataTableToolbar.tsx    # 工具栏
├── DataTableFilters.tsx    # 筛选器
└── index.ts
```

#### Phase 2 验收标准

- [ ] nuqs 安装并在至少一个列表页使用 URL 状态
- [ ] 全局 ErrorBoundary 生效，错误页面正常显示
- [ ] API 错误自动 toast 提示
- [ ] DataTable 组件可复用

---

## 3. FE Agent 生成规范

### 3.1 文件生成位置规则

| 类型 | 路径前缀 | 示例 |
|------|----------|------|
| 新页面路由 | `src/app/(dashboard)/` | `src/app/(dashboard)/invoices/page.tsx` |
| 认证页面 | `src/app/(auth)/` | `src/app/(auth)/reset-password/page.tsx` |
| 业务组件 | `src/features/{module}/components/` | `src/features/invoices/components/InvoiceForm.tsx` |
| 业务 Hook | `src/features/{module}/hooks/` | `src/features/invoices/hooks/useInvoice.ts` |
| 业务 API | `src/features/{module}/services/` | `src/features/invoices/services/invoicesApi.ts` |
| 业务类型 | `src/features/{module}/types/` | `src/features/invoices/types/invoice.types.ts` |
| Zod Schema | `src/features/{module}/schemas/` | `src/features/invoices/schemas/invoice.schema.ts` |
| 全局 UI 组件 | `src/components/ui/` | `src/components/ui/date-range-picker.tsx` |
| 全局 Hook | `src/hooks/` | `src/hooks/use-debounce.ts` |
| 工具函数 | `src/lib/` | `src/lib/currency.ts` |
| 全局类型 | `src/types/` | `src/types/pagination.ts` |
| Zustand Store | `src/stores/` | `src/stores/filter-store.ts` |

### 3.2 禁止写入的位置

| 禁止路径 | 原因 |
|----------|------|
| ~~`app/`~~ (根目录下) | 已废弃，统一用 src/app/ |
| ~~`src/app/**/components/`~~ | 页面目录不放组件 |
| ~~`components/`~~ (根目录下) | 已废弃，统一用 src/components/ |
| ~~`src/modules/`~~ | 已废弃，统一用 src/features/ |

### 3.3 新模块脚手架模板

当 FE Agent 创建新业务模块时，应生成以下结构:

```
src/features/{module-name}/
├── components/
│   ├── {ModuleName}Page.tsx      # 列表页主组件
│   ├── {ModuleName}Table.tsx     # 表格
│   ├── {ModuleName}Form.tsx      # 表单 (可选)
│   ├── {ModuleName}Detail.tsx    # 详情 (可选)
│   └── index.ts
├── hooks/
│   ├── use{ModuleName}s.ts       # 列表 hook
│   ├── use{ModuleName}.ts        # 单条 hook (可选)
│   └── index.ts
├── services/
│   ├── {moduleName}Api.ts        # API 调用
│   └── index.ts
├── schemas/
│   ├── {moduleName}.schema.ts    # Zod 校验
│   └── index.ts
├── types/
│   ├── {moduleName}.types.ts     # 类型定义
│   └── index.ts
└── index.ts                      # 公开导出
```

### 3.4 Import 规范

```tsx
// ✅ 正确
import { ProjectsPage } from '@/features/projects';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useTableParams } from '@/hooks/use-table-params';
import type { Project } from '@/features/projects/types';

// ❌ 错误
import { ProjectsPage } from '@/modules/projects';  // 旧别名
import { Button } from '../../../components/ui/button';  // 相对路径
import { cn } from '../../lib/utils';  // 相对路径
```

---

## 4. 迁移执行清单

### Phase 0 Checklist

- [ ] 0.1 合并 app/layout.tsx 到 src/app/layout.tsx
- [ ] 0.2 删除旧 app/ 目录 (保留 app/(auth) 和 app/(dashboard) 布局临时)
- [ ] 0.3 创建 src/app/(auth)/ 路由组
- [ ] 0.4 创建 src/app/(dashboard)/ 路由组
- [ ] 0.5 迁移 components/ui/* → src/components/ui/*
- [ ] 0.6 迁移 components/layout/* → src/components/layout/*
- [ ] 0.7 迁移 components/shared/* → src/components/shared/*
- [ ] 0.8 更新 tsconfig.json paths
- [ ] 0.9 验证 npm run dev 正常
- [ ] 0.10 验证 npm run build 通过

### Phase 1 Checklist

- [ ] 1.1 迁移 projects 模块
- [ ] 1.2 迁移 ad-accounts 模块
- [ ] 1.3 迁移 daily-reports 模块
- [ ] 1.4 迁移 reconciliation 模块
- [ ] 1.5 迁移 topups 模块
- [ ] 1.6 壳化所有页面 (page.tsx 只 import feature 组件)
- [ ] 1.7 删除 components/ 下的业务模块目录
- [ ] 1.8 删除 app/(dashboard)/*/components/ 目录
- [ ] 1.9 验证所有页面功能正常

### Phase 2 Checklist

- [ ] 2.1 安装 nuqs
- [ ] 2.2 创建 use-table-params hook
- [ ] 2.3 配置 GlobalErrorBoundary
- [ ] 2.4 配置 React Query 全局错误处理
- [ ] 2.5 创建通用 DataTable 组件
- [ ] 2.6 在 projects 列表页应用 nuqs

---

## 5. 风险与回滚

### 风险点

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| Import 路径断裂 | 高 | 中 | 分批迁移，每步验证 |
| 路由冲突 | 中 | 高 | 先删旧再建新 |
| 样式丢失 | 低 | 中 | globals.css 统一管理 |

### 回滚策略

每个 Phase 完成后创建 Git tag:
```bash
git tag -a frontend-phase0-done -m "Phase 0 完成"
git tag -a frontend-phase1-done -m "Phase 1 完成"
git tag -a frontend-phase2-done -m "Phase 2 完成"
```

---

## 附录 A: 完整模块清单

| 模块名 | 路由 | features/ 路径 | 状态 |
|--------|------|----------------|------|
| projects | /projects | src/features/projects | 待完善 |
| channels | /channels | src/features/channels | 待迁移 |
| suppliers | /suppliers | src/features/suppliers | ✅ |
| transfers | /transfers | src/features/transfers | ✅ |
| settlements | /settlements | src/features/settlements | ✅ |
| daily-reports | /daily-reports | src/features/daily-reports | 待完善 |
| reconciliation | /reconciliation | src/features/reconciliation | 待完善 |
| topups | /topups | src/features/topups | 待完善 |
| ledger | /ledger | src/features/ledger | 待完善 |
| ad-accounts | /ad-accounts | src/features/ad-accounts | 待迁移 |
| finance-profit | /finance/profit | src/features/finance-profit | 待完善 |
| import-jobs | /import-jobs | src/features/import-jobs | 待完善 |
| reports | /reports | src/features/reports | 待完善 |

---

**文档维护者**: FE Agent / Claude Code
**最后更新**: 2025-12-08
