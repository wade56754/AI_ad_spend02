---
version: v1.3
status: ready_for_implementation
layer: architecture
owner: wade
last_reviewed: 2025-12-04
baseline:
  - FRONTEND_STRUCTURE_SPEC.md v1.0
  - MASTER.md v3.5
  - API_SOT_v9.0 (路由与权限部分)
template_source: Kiranism/next-shadcn-dashboard-starter
---

# 前端结构迁移计划 v1.3

## 1. 文档说明

### 1.1 目的

本文档定义如何在**不动后端、不动业务逻辑**的前提下，将 AI_ad_spend02 现有前端结构迁移到统一的 Dashboard 布局 + Sidebar + 通用 UI 模式。

**本轮核心目标**（Phase 1）：

1. **统一布局**：一套 `(dashboard)` 路由组布局 + 新版可折叠 Sidebar
2. **补齐 UI 基础设施**：scroll-area / sheet / tooltip / collapsible 等通用组件
3. **建立导航 SoT**：`nav-items.ts` 作为导航唯一数据来源

**Phase 2（后续）**：业务模块迁移到 `modules/*` 结构，不在本轮范围。

### 1.2 范围边界

| 范围     | 包含                                                         | 不包含                                              |
|----------|--------------------------------------------------------------|-----------------------------------------------------|
| 布局     | Dashboard 布局、Sidebar、Header、PageContainer               | 业务页面内容本身                                    |
| 组件     | sidebar.tsx、scroll-area、sheet、tooltip、collapsible        | 业务组件（Product、Kanban 等模板示例）              |
| 模式     | 导航配置、折叠逻辑、响应式处理                               | Clerk/Sentry/kbar 等第三方 SaaS                     |
| Hooks    | use-mobile、use-sidebar                                       | 业务强绑定 Hooks                                    |
| SoT 对齐 | 路由结构 ↔ nav-items.ts 同步规则                              | 后端 API_SOT / SoT 文档修改                         |

**硬约束**：所有改动只发生在 `frontend/` 目录下，禁止修改 `backend/`。

### 1.3 术语约定

| 术语 | 定义 |
|------|------|
| 模板项目 | `D:\git\playground\front-templates`（Kiranism/next-shadcn-dashboard-starter） |
| 目标项目 | `D:\git\1108\AI_ad_spend02\frontend` |
| Phase 1 | 基础设施迁移（布局壳子可用、Sidebar 折叠可用） |
| Phase 2 | 业务模块重构（迁移到 `modules/*`） |
| 导航 SoT | `constants/nav-items.ts`，Dashboard 导航的唯一数据来源 |

---

## 2. 前端现状与目标结构

### 2.1 当前状态（实际快照 2025-12-04）

**技术栈**：

| 依赖          | 版本     | 备注                    |
|---------------|----------|-------------------------|
| Next.js       | 16.0.2   | App Router              |
| React         | 18.3.1   |                         |
| TanStack Query| 5.59.x   |                         |
| Tailwind CSS  | 3.4.x    | 模板使用 v4，本项目暂不升级 |
| shadcn/ui     | 已安装   | `components/ui/` 约 25+ 组件 |
| Zustand       | 4.5.x    |                         |

**当前目录结构（已完成部分 Phase 1 迁移）**：

```text
frontend/
├── app/
│   ├── layout.tsx              # 根布局（已集成 ErrorBoundary + Providers）
│   ├── page.tsx                # 首页（旧布局）
│   ├── (dashboard)/            # ⭐ 新路由组（已创建）
│   │   ├── layout.tsx          # SidebarProvider + Header（已完成）
│   │   └── page.tsx            # Dashboard 首页占位
│   ├── daily-reports/          # 业务页面（待迁入 dashboard）
│   ├── topup/                  # 业务页面（待迁入 dashboard）
│   └── ...
├── components/
│   ├── ui/
│   │   ├── sidebar.tsx         # ⭐ 新 Sidebar（已从模板迁移）
│   │   ├── scroll-area.tsx     # ⭐ 已添加
│   │   ├── sheet.tsx           # ⭐ 已添加
│   │   ├── tooltip.tsx         # ⭐ 已添加
│   │   ├── collapsible.tsx     # ⭐ 已添加
│   │   └── ...（约 25 个组件）
│   ├── layout/
│   │   ├── app-sidebar.tsx     # ⭐ 新版（使用 nav-items.ts）
│   │   ├── header.tsx          # ⭐ 新版 Header
│   │   ├── page-container.tsx  # ⭐ 新增
│   │   ├── providers.tsx       # ⭐ 整合 Providers
│   │   ├── Sidebar.legacy.tsx  # 旧版（已重命名）
│   │   ├── AppShell.tsx        # ⚠️ deprecated，待删除
│   │   ├── DashboardLayout.tsx # ⚠️ 旧布局，待清理
│   │   └── AppLayout.tsx       # 保留（独立场景）
│   ├── common/
│   │   └── ErrorBoundary.tsx   # ⭐ 新增
│   └── dashboard/
├── constants/
│   └── nav-items.ts            # ⭐ 导航 SoT（已创建）
├── hooks/
│   ├── use-mobile.ts           # ⭐ 已添加
│   ├── use-sidebar.ts          # ⭐ 已添加
│   ├── use-theme.ts            # 保留
│   └── use-auth.ts
├── lib/
│   ├── api/
│   │   └── client.ts           # API 客户端（已优化）
│   └── utils.ts
├── stores/
│   └── authStore.ts
└── types/
    └── nav.types.ts            # ⭐ 已创建
```

### 2.2 问题诊断（按优先级）

| # | 问题 | 影响 | 优先级 | 当前状态 |
|---|------|------|--------|----------|
| 1 | 布局组件存在多套（AppShell/DashboardLayout/AppLayout） | 新人不知该用哪套 | P0 | 部分解决（新 dashboard 布局已建立） |
| 2 | 旧布局文件未清理 | 代码冗余，易混淆 | P1 | 待处理 |
| 3 | 业务页面未迁入 (dashboard) 路由组 | 不能统一使用新布局 | P1 | 待处理 |
| 4 | app/page.tsx 使用旧布局模式 | 首页与 Dashboard 风格不一致 | P2 | 可接受 |

### 2.3 目标目录结构（Phase 1 + Phase 2 完成后）

```text
frontend/
├── app/
│   ├── layout.tsx               # 根布局（Providers + ErrorBoundary）
│   ├── globals.css
│   ├── (dashboard)/             # Dashboard 路由组
│   │   ├── layout.tsx           # SidebarProvider + Header + PageContainer
│   │   ├── page.tsx             # Dashboard 首页
│   │   ├── projects/
│   │   ├── ad-accounts/
│   │   ├── daily-reports/       # 从 app/daily-reports 迁入
│   │   ├── topup/               # 从 app/topup 迁入
│   │   ├── reconciliation/
│   │   ├── ledger/
│   │   └── settings/
│   └── auth/                    # 鉴权 UI
│
├── components/
│   ├── ui/                      # shadcn + 通用 UI
│   ├── layout/                  # 布局组件（只保留活跃组件）
│   │   ├── app-sidebar.tsx
│   │   ├── header.tsx
│   │   ├── page-container.tsx
│   │   └── providers.tsx
│   ├── common/                  # 通用业务无关组件
│   │   └── ErrorBoundary.tsx
│   └── forms/                   # 表单组件（Phase 2）
│
├── constants/
│   └── nav-items.ts             # 导航 SoT
│
├── hooks/
│   ├── use-mobile.ts
│   ├── use-sidebar.ts
│   ├── use-theme.ts
│   └── use-auth.ts
│
├── lib/
│   ├── api/
│   │   └── client.ts
│   ├── utils/
│   │   └── index.ts             # cn() 等工具
│   └── validation/              # Zod schemas（Phase 2）
│
├── modules/                     # 业务模块（Phase 2）
│   ├── shared/
│   ├── daily-reports/
│   ├── topups/
│   ├── ledger/
│   └── reconciliation/
│
├── stores/
├── types/
│   └── nav.types.ts
└── styles/
```

---

## 3. 迁移计划 v1.3（Phase 1 收尾 + Phase 2 规划）

### 3.1 Phase 1 剩余工作（布局收尾）

Phase 1 大部分工作已完成，以下是剩余任务：

#### 3.1.1 旧布局组件退场策略

| 组件 | 当前状态 | Phase 1 处理 | Phase 2 处理 |
|------|----------|--------------|--------------|
| `AppShell.tsx` | 存在，未使用 | 添加 `// @deprecated` 注释 | 删除 |
| `DashboardLayout.tsx` | 存在，部分页面使用 | 保留，服务存量页面 | 迁移完成后删除 |
| `AppLayout.tsx` | 存在，独立场景使用 | 保留不动 | 视情况保留/合并 |
| `Sidebar.legacy.tsx` | 已重命名 | 保留作为备份 | 删除 |
| `modern-navigation.tsx` | 存在 | 评估是否需要 | 删除或合并 |
| `optimized-navigation.tsx` | 存在 | 评估是否需要 | 删除或合并 |

**退场原则**：
1. 新页面/新模块 → 一律使用 `(dashboard)/layout.tsx`
2. 老页面 → 逐步迁入 `(dashboard)` 路由组后切换到新布局
3. 所有标记 `@deprecated` 的组件在 Phase 2 结束后统一清理

#### 3.1.2 Header 组件优化

当前 `header.tsx` 路径为 `components/layout/header.tsx`（小写），需确认：
- 是否已移除 UserNav/ThemeSelector/CtaGithub 等模板依赖
- 是否已接入 SidebarTrigger + Breadcrumb

### 3.2 Sidebar 迁移安全规则（已执行，供审计参考）

从模板复制 `sidebar.tsx` 时已遵循的规则：

**强制删除/替换**：
- ❌ `@clerk/*` 相关导入与调用（useUser、UserButton 等）
- ❌ `@sentry/*` 导入
- ❌ `kbar` 相关导入与组件
- ❌ demo 数据（tenants、company 等硬编码）
- ⚠️ Tabler Icons → 改用 `lucide-react`

**必须保留**：
- ✅ SidebarProvider / useSidebar 及其 Context
- ✅ 折叠模式实现（`collapsible="icon"` 等）
- ✅ 移动端 Sheet 抽屉（配合 `sheet.tsx`）
- ✅ 键盘快捷键 Cmd+B 切换折叠

**禁止新增**：
- ❌ 任何新的第三方 SaaS 依赖

### 3.3 工具函数与 Hooks 规范

#### 3.3.1 Hook 命名规则

| 功能 | 文件名 | 函数名 | 状态 |
|------|--------|--------|------|
| 移动端检测 | `use-mobile.ts` | `useMobile()` | ✅ 已有 |
| Sidebar 状态 | `use-sidebar.ts` | `useSidebar()` | ✅ 已有 |
| 主题切换 | `use-theme.ts` | `useTheme()` | ✅ 已有 |
| 认证状态 | `use-auth.ts` | `useAuth()` | ✅ 已有 |

**规则**：
- 文件名：kebab-case（`use-xxx.ts`）
- 函数名：camelCase（`useXxx`）
- 每个功能只保留一个官方 Hook，禁止平行版本

#### 3.3.2 utils 统一规范

`cn()` 函数已在 `src/lib/utils/index.ts` 统一实现：

```typescript
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

**检查点**：
- 所有组件的 `cn` 必须从 `@/lib/utils` 导入
- 禁止在其他文件重复定义 `cn`

### 3.4 导航配置与路由 SoT

#### 3.4.1 导航 SoT 文件

**位置**：`frontend/constants/nav-items.ts`

**职责**：
- Dashboard 导航的**唯一数据来源**
- 所有 Sidebar / 顶部导航组件只从这里取数据
- 禁止在组件中硬编码导航 URL

#### 3.4.2 导航 ↔ 路由 同步规则

**强制约束**：`navItems[].url` 必须与 `app/(dashboard)/` 下的实际路由目录一一对应。

**变更流程**：

| 操作 | 步骤 |
|------|------|
| 新增路由 | 1. 在 `app/(dashboard)/xxx` 建立页面 → 2. 在 `nav-items.ts` 增加对应项 |
| 删除路由 | 1. 从 `nav-items.ts` 删除导航项 → 2. 删除路由目录 |
| 重命名路由 | 同时修改目录名和 `nav-items.ts` 的 URL |

**当前导航项（nav-items.ts）**：

| 标题 | URL | 路由目录状态 |
|------|-----|--------------|
| 概览 | `/dashboard` | ✅ 存在 |
| 项目管理 | `/dashboard/projects` | ⚠️ 待创建 |
| 渠道账户 | `/dashboard/ad-accounts` | ⚠️ 待创建 |
| 日报管理 | `/dashboard/daily-reports` | ⚠️ 待迁入 |
| 充值管理 | `/dashboard/topup` | ⚠️ 待迁入 |
| 对账管理 | `/dashboard/reconciliation` | ⚠️ 待创建 |
| 账本查询 | `/dashboard/ledger` | ⚠️ 待创建 |
| 系统设置 | `/dashboard/settings` | ⚠️ 待创建 |

#### 3.4.3 类型定义

**位置**：`frontend/types/nav.types.ts`

```typescript
import type { LucideIcon } from 'lucide-react';

export interface NavItem {
  title: string;
  url: string;
  icon: LucideIcon;
  isActive?: boolean;
  shortcut?: string[];
  items?: NavItem[];  // 子菜单
  badge?: number;     // 角标数字
}

export interface NavGroup {
  label: string;
  items: NavItem[];
}
```

### 3.5 不迁移清单

以下内容**一律不迁入** AI_ad_spend02：

**第三方依赖**：
- `@clerk/*`（鉴权）
- `@sentry/*`（APM）
- `kbar/*`（命令面板）
- Stripe 等计费相关代码

**模板业务模块**：
- `features/products/*`
- `features/kanban/*`
- 任何示例业务数据

**其他 UI 组件**：
- `org-switcher.tsx`（依赖 Clerk）
- `user-avatar-profile.tsx`（依赖 Clerk）
- `theme-selector.tsx`（可选后续集成）
- `cta-github.tsx`

**使用方式**：这些模块只当"模式参考"学习交互设计，不复制代码/字段/业务命名。

---

## 4. 代码改动摘要

### 4.1 Phase 1 文件清单（当前状态）

| # | 文件路径 | 操作 | 状态 |
|---|----------|------|------|
| 1 | `components/ui/sidebar.tsx` | 新建 | ✅ 完成 |
| 2 | `components/ui/scroll-area.tsx` | 新建 | ✅ 完成 |
| 3 | `components/ui/sheet.tsx` | 新建 | ✅ 完成 |
| 4 | `components/ui/tooltip.tsx` | 新建 | ✅ 完成 |
| 5 | `components/ui/collapsible.tsx` | 新建 | ✅ 完成 |
| 6 | `hooks/use-mobile.ts` | 新建 | ✅ 完成 |
| 7 | `hooks/use-sidebar.ts` | 新建 | ✅ 完成 |
| 8 | `constants/nav-items.ts` | 新建 | ✅ 完成 |
| 9 | `types/nav.types.ts` | 新建 | ✅ 完成 |
| 10 | `components/layout/page-container.tsx` | 新建 | ✅ 完成 |
| 11 | `components/layout/app-sidebar.tsx` | 新建 | ✅ 完成 |
| 12 | `components/layout/header.tsx` | 改写 | ✅ 完成 |
| 13 | `components/layout/providers.tsx` | 整合 | ✅ 完成 |
| 14 | `app/(dashboard)/layout.tsx` | 新建 | ✅ 完成 |
| 15 | `app/(dashboard)/page.tsx` | 新建 | ✅ 完成 |
| 16 | `app/layout.tsx` | 改写 | ✅ 完成（集成 ErrorBoundary） |
| 17 | `components/layout/Sidebar.tsx` → `Sidebar.legacy.tsx` | 重命名 | ✅ 完成 |
| 18 | `components/common/ErrorBoundary.tsx` | 新建 | ✅ 完成 |
| 19 | `lib/api/client.ts` | 优化 | ✅ 完成（API URL + 超时 + 认证检查） |
| 20 | `src/lib/utils/index.ts` | 修复 | ✅ 完成（导出 cn） |

### 4.2 Phase 1 完成判定标准（DoD）

满足以下**全部条件**，Phase 1 才视为完成：

| # | 验收项 | 验证方法 | 状态 |
|---|--------|----------|------|
| 1 | Dashboard 正常渲染 | 访问 `/dashboard`，出现 Sidebar + Header + 主内容区，无红色错误 | ⬜ 待验证 |
| 2 | Sidebar 桌面端折叠 | 点击按钮或 Cmd+B 可在展开/收窄间切换 | ⬜ 待验证 |
| 3 | Sidebar 折叠 Tooltip | 收窄状态下 hover 显示 Tooltip 文本 | ⬜ 待验证 |
| 4 | Sidebar 移动端 Drawer | 宽度 < 768px 时，Sidebar 改为 Sheet 抽屉 | ⬜ 待验证 |
| 5 | 导航来自 SoT | Sidebar 只使用 `nav-items.ts` 数据，改 URL 只需改常量 | ⬜ 待验证 |
| 6 | 旧布局隔离 | 旧 Sidebar 已重命名为 `Sidebar.legacy.tsx` | ✅ 完成 |
| 7 | 依赖干净 | 无 `@clerk/*`, `@sentry/*`, `kbar/*` 残留 | ⬜ 待验证 |
| 8 | TypeScript 编译通过 | `npx tsc --noEmit` 无错误 | ⬜ 待验证 |
| 9 | ESLint 无新增 error | `npm run lint` 无新增错误 | ⬜ 待验证 |

**验证命令**：

```bash
cd frontend

# TypeScript 检查
npx tsc --noEmit

# ESLint 检查
npm run lint

# 启动开发服务器
npm run dev

# 访问 http://localhost:3000/dashboard 验证
```

### 4.3 Phase 2 规划（业务模块重构）

Phase 2 目标：将业务页面迁移到 `modules/*` 结构，统一使用 `(dashboard)` 布局。

**主要任务**：

1. **创建 modules 目录结构**
   - `modules/daily-reports/`
   - `modules/topups/`
   - `modules/ledger/`
   - `modules/reconciliation/`
   - `modules/shared/`

2. **迁移业务页面**
   - `app/daily-reports/` → `app/(dashboard)/daily-reports/`
   - `app/topup/` → `app/(dashboard)/topup/`
   - 组件抽取到对应 `modules/*/components/`

3. **清理旧文件**
   - 删除 `AppShell.tsx`
   - 删除 `DashboardLayout.tsx`
   - 删除 `Sidebar.legacy.tsx`
   - 删除 `modern-navigation.tsx`
   - 删除 `optimized-navigation.tsx`

4. **补齐缺失路由**
   - 创建 `app/(dashboard)/projects/page.tsx`
   - 创建 `app/(dashboard)/ad-accounts/page.tsx`
   - 创建 `app/(dashboard)/reconciliation/page.tsx`
   - 创建 `app/(dashboard)/ledger/page.tsx`
   - 创建 `app/(dashboard)/settings/page.tsx`

---

## 5. 风险与回滚策略

### 5.1 主要风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Sidebar 改动导致 Dashboard 不可用 | 高 | 保留 `Sidebar.legacy.tsx` 作为备份 |
| Tailwind v3/v4 样式差异 | 中 | 严格使用 v3 兼容写法 |
| 旧页面未迁移导致布局不一致 | 低 | 分阶段迁移，允许过渡期 |

### 5.2 回滚策略

若新 Sidebar 在集成阶段问题过大：

1. Git 回滚该分支 merge
2. 或仅回滚 `components/ui/sidebar.tsx` + `app/(dashboard)` 相关改动
3. 恢复使用 `Sidebar.legacy.tsx` + 旧布局

---

## 6. 变更说明（v1.2 → v1.3）

基于 v1.2 的优化内容：

1. **更新当前状态快照**：反映 2025-12-04 实际代码状态，大部分 Phase 1 工作已完成
2. **补充已完成文件清单**：标注每个文件的完成状态（✅/⬜）
3. **细化 DoD 验收标准**：增加验证方法和状态追踪列
4. **明确导航 ↔ 路由对应关系**：列出当前 nav-items.ts 与路由目录的对齐状态
5. **强化旧组件退场策略**：补充 `modern-navigation.tsx`、`optimized-navigation.tsx` 的处理方式
6. **精简冗余内容**：移除重复描述，保持文档紧凑可执行

---

**文档摘要**：
- **版本**: v1.3
- **状态**: ready_for_implementation
- **Phase 1 进度**: ~90% 完成（剩余：验收验证 + 旧文件清理）
- **Phase 2 状态**: 规划完成，待启动
