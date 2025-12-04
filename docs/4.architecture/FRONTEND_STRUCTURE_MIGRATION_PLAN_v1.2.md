version: v1.2
status: ready_for_implementation
layer: architecture
owner: wade
last_reviewed: 2025-12-04
baseline:
  - FRONTEND_STRUCTURE_SPEC.md v1.0
  - MASTER.md v3.5
  - API_SOT_v3.x (路由与权限部分)
template_source: Kiranism/next-shadcn-dashboard-starter

# 前端结构迁移计划 v1.2

## 1. 文档说明

### 1.1 目的

本计划文档定义：如何在不动后端、不动业务逻辑的前提下，将 AI_ad_spend02 现有前端结构，迁移到一套更统一的 **Dashboard 布局 + Sidebar + 通用 UI 模式**，参考 `next-shadcn-dashboard-starter`，为后续模块化开发（ledger / daily-reports / profit 等）打好壳子。

本轮只做两件事：

1. 统一布局：一套 `(dashboard)` 布局 + 新 Sidebar。
2. 补齐通用 UI 基础设施：scroll-area / sheet / tooltip / collapsible 等。

业务模块（daily-reports/topups/ledger 等）迁移到 `modules/*` 放在 Phase 2，不在本轮大动。

### 1.2 范围边界

| 范围     | 包含                                                     | 不包含                                                      |
|----------|----------------------------------------------------------|-------------------------------------------------------------|
| 布局     | Dashboard 布局、Sidebar、Header、PageContainer           | 任何具体业务页面内容                                        |
| 组件     | 通用 UI 基础设施：sidebar.tsx、scroll-area、sheet、tooltip、collapsible | 业务组件（Product、Kanban、profit 业务页面）                |
| 模式     | 导航配置（nav-items.ts）、折叠逻辑、响应式处理           | 第三方鉴权（Clerk）、APM（Sentry）、Cmd+K 命令面板          |
| Hooks    | use-mobile、use-sidebar、（可选）use-media-query         | 与具体业务强绑定的 Hooks                                    |
| SoT 对齐 | 路由结构 ↔ nav-items.ts 的同步规则                       | 改动 API_SOT / 后端 SoT 文档本身                            |

> 硬约束：本轮所有改动只能发生在 `frontend/` 下，禁止修改 `backend/` 任何文件。

### 1.3 术语约定

- **模板项目**：`D:\git\playground\front-templates`（Kiranism/next-shadcn-dashboard-starter）
- **目标项目**：`D:\git\1108\AI_ad_spend02\frontend`
- **FRONTEND_STRUCTURE_SPEC**：现有前端结构 SoT（v1.0）
- **API_SOT**：后端 API SoT（用于约束路由与模块划分）
- **Phase 1**：基础设施迁移（布局壳子可用）
- **Phase 2**：业务模块重构（迁移到 `modules/*`）

---

## 2. 前端现状与目标结构

### 2.1 当前状态（快照）

**技术栈（已验证）：**

| 依赖          | 版本     | 备注                |
|---------------|----------|---------------------|
| Next.js       | 16.0.2   | App Router          |
| React         | 18.3.1   |                     |
| TanStack Query| 5.59.x   |                     |
| Tailwind CSS  | 3.4.x    | 模板使用 v4，本项目暂不升级 |
| shadcn/ui     | 已安装   | `components/ui/` 下有约 20 个组件 |
| Zustand       | 4.5.x    |                     |

**现有结构（简化）：**

```text
frontend/
├── app/
│   ├── layout.tsx          # 根布局（极简，无 Providers）
│   ├── page.tsx            # 首页
│   ├── providers.tsx       # 存在但未在 layout 中使用
│   ├── daily-reports/      # 业务页面
│   ├── topup/              # 业务页面
│   └── ...
├── components/
│   ├── ui/                 # shadcn 基础组件（~20 个）
│   ├── layout/
│   │   ├── AppShell.tsx    # ⚠️ deprecated 标记但仍存在
│   │   ├── DashboardLayout.tsx
│   │   ├── AppLayout.tsx
│   │   ├── Sidebar.tsx     # 自己写的，无折叠
│   │   └── Header.tsx
│   └── dashboard/          # Dashboard 相关组件
├── hooks/
│   ├── useTheme.ts
│   └── use-theme.ts        # ⚠️ 命名重复
├── lib/
│   └── utils.ts            # cn() 等工具函数
└── styles/
2.2 问题诊断（按优先级）
问题	影响	优先级
布局组件存在 3 套实现（AppShell/DashboardLayout/AppLayout）	新人不知道该用哪套；重构难度上升	P0
Sidebar 不可折叠，缺少移动端 Drawer	桌面端体验一般，移动端几乎不可用	P1
无 SidebarProvider	折叠状态不能跨组件共享，逻辑会越写越乱	P1
Hooks 命名不规范（useTheme vs use-theme）	导入时容易踩坑，未来难以统一	P2
业务代码直接写在 app/ 下，未按 modules/ 拆分	不符合 FRONTEND_STRUCTURE_SPEC v1.0	P2
app/layout.tsx 未集成 providers.tsx	主题 / Query 等 Provider 没生效	P1

2.3 目标目录结构（布局 + 基础设施完成后）
说明：以下为 Phase 1 + Phase 2 的目标形态，本轮仅落地 Phase 1 部分。

text
复制代码
frontend/
├── app/                          # Next.js App Router
│   ├── layout.tsx               # 根布局（集成 Providers）
│   ├── globals.css
│   ├── (dashboard)/             # ⭐ Dashboard 路由组（本轮重点）
│   │   ├── layout.tsx          # SidebarProvider + Header + PageContainer
│   │   ├── page.tsx            # Dashboard 首页
│   │   ├── projects/
│   │   ├── ad-accounts/
│   │   ├── daily-reports/
│   │   ├── topup/
│   │   ├── reconciliation/
│   │   ├── ledger/
│   │   └── settings/
│   └── auth/                   # 鉴权 UI（与后端 Auth 对齐）
│
├── components/
│   ├── ui/                      # shadcn / Radix 封装
│   │   ├── sidebar.tsx         # ⭐ 新 Sidebar（从模板迁移）
│   │   ├── scroll-area.tsx     # ⭐ 新增
│   │   ├── sheet.tsx           # ⭐ 新增
│   │   ├── tooltip.tsx         # ⭐ 新增
│   │   ├── collapsible.tsx     # ⭐ 新增（子菜单）
│   │   ├── button.tsx
│   │   └── ...
│   ├── layout/
│   │   ├── app-sidebar.tsx     # ⭐ 使用 nav-items.ts 的业务 Sidebar
│   │   ├── header.tsx          # ⭐ Header + Breadcrumb + 预留右侧区域
│   │   ├── page-container.tsx  # ⭐ 页面容器
│   │   └── providers.tsx       # ⭐ 整合 ThemeProvider / QueryProvider 等
│   └── forms/                  # 表单组件库（Phase 2 可补）
│
├── constants/
│   └── nav-items.ts            # ⭐ 导航配置 SoT（与 app/(dashboard) 路由 1:1 对应）
│
├── hooks/
│   ├── use-mobile.ts           # ⭐ 新增（移动端检测）
│   └── use-sidebar.ts          # ⭐ 从 sidebar.tsx 导出
│
├── lib/
│   ├── utils.ts                # cn() 等工具（统一实现）
│   └── api/                    # API 客户端层（与 API_SOT 对齐）
│
├── modules/                    # 业务模块（Phase 2）
│   ├── shared/                 # 共享业务组件（不直接用 Radix）
│   ├── daily-reports/
│   ├── topups/
│   ├── ledger/
│   └── reconciliation/
│
├── stores/                     # Zustand stores
├── types/
│   └── nav.types.ts            # ⭐ NavItem / NavGroup 类型
└── styles/
3. 迁移计划 v1.2（Phase 1）
3.1 布局与 Sidebar 迁移
3.1.1 来源 → 目标 映射（布局相关）
模板文件	目标文件	操作	说明
src/components/ui/sidebar.tsx	components/ui/sidebar.tsx	复制 + 清理	核心 Sidebar 组件（720 行左右），按安全规则清理依赖
src/components/layout/app-sidebar.tsx	components/layout/app-sidebar.tsx	改写	移除 Clerk/UserNav，改为使用 nav-items.ts
src/components/layout/header.tsx	components/layout/header.tsx	改写	移除 UserNav/ThemeSelector/CtaGithub 等
src/components/layout/page-container.tsx	components/layout/page-container.tsx	复制	通用 Page 容器，适配 Tailwind v3
src/app/dashboard/layout.tsx	app/(dashboard)/layout.tsx	改写	移除 KBar 等，接入本项目前端 Providers

3.1.2 Sidebar 迁移安全规则
从模板复制 sidebar.tsx 时，必须满足：

强制删除/替换：

删除所有：

@clerk/* 相关导入与调用（useUser、UserButton 等）

@sentry/* 导入

kbar 相关导入与组件

demo 数据（tenants、company 等硬编码）

图标库：

优先改用项目中已经使用的 lucide-react，不要混用 Tabler Icons。

必须保留：

SidebarProvider / useSidebar 及其 Context

折叠模式实现（包括 collapsible="icon" 等）

移动端 Sheet 抽屉（配合 sheet.tsx）

键盘快捷键 Cmd+B 切换 Sidebar 折叠

禁止新增：

任何新引入的第三方 SaaS 依赖（Clerk/Sentry/Stripe 等）

3.1.3 旧布局组件退场策略
组件	Phase 1 处理	Phase 2 处理	备注
AppShell.tsx	保留文件，顶部新增 // DEPRECATED 注释	删除	已标 deprecated
DashboardLayout.tsx	保留，暂时服务存量页面	将页面迁移到 (dashboard) 后删除	
AppLayout.tsx	保留，不改动	视用途决定保留/合并	可能有独立场景
Sidebar.tsx（旧）	重命名为 Sidebar.legacy.tsx	删除	避免与新 sidebar.tsx 冲突

迁移中间态：

新页面 / 新模块 → 一律走 (dashboard)/layout.tsx + app-sidebar.tsx

老页面 → 逐步迁入 (dashboard) 路由组后，统一切换到新布局

3.2 UI 组件迁移
3.2.1 必须新增组件
组件文件	依赖方	来源
components/ui/scroll-area.tsx	PageContainer / Sidebar	模板复制
components/ui/sheet.tsx	Sidebar 移动端 Drawer	模板复制
components/ui/tooltip.tsx	Sidebar 折叠 tooltip	模板复制
components/ui/collapsible.tsx	Sidebar 子菜单	模板复制

迁移时需注意：

Radix 版本与现有依赖是否一致；

Tailwind v4 的类名适度调整为 v3 兼容写法（保守一点写）。

3.2.2 已有组件兼容性检查
组件	现状	操作
button.tsx	已存在	检查 variant 是否满足模板需求
separator.tsx	已存在	无需修改
skeleton.tsx	已存在	无需修改

3.3 工具函数与 Hooks 合并策略
3.3.1 Hook 命名统一
功能	规范文件名	函数名	现状	操作
主题切换	use-theme.ts	useTheme()	有 useTheme.ts 和 use-theme.ts	保留一个文件，合并实现
移动端	use-mobile.ts	useMobile()	不存在	从模板复制或改写
Sidebar	use-sidebar.ts	useSidebar()	不存在	从 sidebar.tsx 抽出导出
媒体查询	use-media-query.ts	useMediaQuery()	如需要可添加	可参考模板 Hook 实现

规则：

文件名统一 kebab-case：use-xxx.ts

导出函数统一 camelCase：useXxx

每个功能只保留一个官方 Hook，禁止平行版本。

3.3.2 lib/utils.ts 合并
统一使用标准 cn() 实现：

ts
复制代码
// lib/utils.ts
import type { ClassValue } from "clsx";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
检查所有引用点，确保：

没有旧版 cn 存在于其他文件；

所有 cn 都从 lib/utils 导入。

3.4 导航配置与路由 SoT
3.4.1 导航配置（单一事实源）
文件：frontend/constants/nav-items.ts

作为 Dashboard 导航的唯一数据来源；

所有 Sidebar / 顶部导航组件只从这里取数据，不允许写死 URL。

示例结构（节选）：

ts
复制代码
// constants/nav-items.ts
import type { LucideIcon } from "lucide-react";
import {
  LayoutDashboard,
  Users,
  FileText,
  DollarSign,
  CheckSquare,
  BookOpen,
  Settings,
} from "lucide-react";

export interface NavItem {
  title: string;
  url: string;
  icon: LucideIcon;
  isActive?: boolean;
  shortcut?: string[];
  items?: NavItem[];
}

export const navItems: NavItem[] = [
  {
    title: "概览",
    url: "/dashboard",
    icon: LayoutDashboard,
    shortcut: ["d", "d"],
  },
  {
    title: "项目管理",
    url: "/dashboard/projects",
    icon: LayoutDashboard,
  },
  {
    title: "渠道账户",
    url: "/dashboard/ad-accounts",
    icon: Users,
  },
  {
    title: "日报管理",
    url: "/dashboard/daily-reports",
    icon: FileText,
  },
  {
    title: "充值管理",
    url: "/dashboard/topup",
    icon: DollarSign,
  },
  {
    title: "对账管理",
    url: "/dashboard/reconciliation",
    icon: CheckSquare,
  },
  {
    title: "账本查询",
    url: "/dashboard/ledger",
    icon: BookOpen,
  },
  {
    title: "系统设置",
    url: "/dashboard/settings",
    icon: Settings,
  },
];
3.4.2 导航 ↔ 路由 同步规则
强制：navItems[].url 必须与 app/(dashboard)/ 下的实际路由目录一一对应。

变更流程：

新增路由：

先在 app/(dashboard)/xxx 下建立页面；

再在 nav-items.ts 里增加对应项。

删除路由：

先从 nav-items.ts 删除导航项；

再删除路由目录。

路由重命名：

同时修改目录名和 nav-items.ts 里的 URL。

3.4.3 类型定义
文件：frontend/types/nav.types.ts

ts
复制代码
import type { LucideIcon } from "lucide-react";

export interface NavItem {
  title: string;
  url: string;
  icon: LucideIcon;
  isActive?: boolean;
  shortcut?: string[];
  items?: NavItem[];
  badge?: number;
}

export interface NavGroup {
  label: string;
  items: NavItem[];
}
3.5 不迁移清单
这些内容一律不迁入 AI_ad_spend02：

第三方依赖：

@clerk/*

@sentry/*

kbar/*

任意 SaaS 计费相关代码（Stripe 等）

模板业务模块：

features/products/*

features/kanban/*

其他 UI：

org-switcher.tsx

user-avatar-profile.tsx（强依赖 Clerk）

theme-selector.tsx

cta-github.tsx

使用方式：
只当“模式示例”学习交互，不复制字段/API/业务命名。

4. 代码改动摘要（Phase 1）
4.1 文件级清单
#	文件路径	操作	职责/说明
1	components/ui/sidebar.tsx	新建	新版 Sidebar（迁移自模板，清理依赖）
2	components/ui/scroll-area.tsx	新建	ScrollArea 封装，PageContainer / Sidebar 用
3	components/ui/sheet.tsx	新建	移动端 Drawer 容器
4	components/ui/tooltip.tsx	新建	折叠 Sidebar 的 Tooltip
5	components/ui/collapsible.tsx	新建	子菜单折叠
6	hooks/use-mobile.ts	新建	移动端检测 hook
7	hooks/use-sidebar.ts	新建	从 Sidebar Context 导出
8	constants/nav-items.ts	新建	导航配置 SoT
9	types/nav.types.ts	新建	NavItem / NavGroup 类型
10	components/layout/page-container.tsx	新建	页面容器
11	components/layout/app-sidebar.tsx	新建	应用侧边栏（组装 Sidebar + navItems）
12	components/layout/header.tsx	改写/新建	Header + SidebarTrigger + Breadcrumb
13	components/layout/providers.tsx	新建/整合	ThemeProvider + QueryProvider 等
14	app/(dashboard)/layout.tsx	新建	Dashboard 布局壳子
15	app/(dashboard)/page.tsx	新建	Dashboard 首页占位
16	app/layout.tsx	改写	引入 components/layout/providers.tsx
17	components/layout/Sidebar.tsx	重命名	→ components/layout/Sidebar.legacy.tsx
18	hooks/useTheme.ts / use-theme.ts	合并	保留一个官方版本，删除另一个
19	lib/utils.ts	校验/微调	统一 cn() 实现

4.2 Phase 1 完成判定标准（DoD）
满足以下全部条件，Phase 1 才视为完成：

Dashboard 正常渲染

访问 /dashboard：出现 Sidebar + Header + 主内容区；

页面无红色错误、无模块找不到警告。

Sidebar 行为正常

桌面端可通过按钮或 Cmd+B 在展开/收窄间切换；

在收窄状态下，hover 显示 Tooltip 文本。

移动端行为正常

宽度 < 768px 时，Sidebar 不常驻，改为 Sheet 抽屉；

抽屉可通过按钮弹出/收起。

导航来自 SoT

Sidebar 只使用 nav-items.ts 提供的数据；

任意导航 URL 变更只需改 nav-items.ts。

旧布局隔离

旧 Sidebar 文件已重命名为 Sidebar.legacy.tsx；

文档中有明确计划在 Phase 2 统一删除旧 AppShell / DashboardLayout。

依赖干净

无 @clerk/*, @sentry/*, kbar/* 等依赖残留；

package.json 无新增无关依赖。

5. 风险与回滚策略（简版）
5.1 主要风险
Sidebar 大改导致 /dashboard 整体不可用；

Tailwind v3/v4 差异导致样式错乱；

重命名旧 Sidebar 影响现有页面渲染。

5.2 降低风险策略
先在单独分支完成所有改动：feat/frontend-dashboard-shell；

保持旧布局文件存在（只重命名，不马上删）；

保持 app/page.tsx 不依赖新布局，先只改 (dashboard) 路由。

5.3 回滚策略
若新 Sidebar 在集成阶段问题过大：

Git 直接回滚该分支 merge；

或仅回滚 components/ui/sidebar.tsx / app/(dashboard) 相关改动；

保证旧 Sidebar.legacy.tsx 与旧布局仍能在紧急情况下切回。

6. 变更说明（v1.1 → v1.2）
在 Claude 版 v1.1 的基础上，本 v1.2 做了这些调整：

保留所有关键执行细节（文件清单、Sidebar 安全规则、DoD），避免“减配”；

加强了 SoT 视角：明确 nav-items.ts 为导航 SoT，并约定路由 ↔ 导航同步流程；

加强了模块化视角：明确 modules/ 的目标形态和 Phase 2 的路径；

增补了 Hooks 命名规范和 utils 合并策略，防止多版本函数并存；

补充了一个简短的“风险与回滚”章节，让这次布局级大改有退路；

精简了少量重复描述，使文档结构更清晰（1 说明 → 2 现状/目标 → 3 计划 → 4 DoD → 5 风险）。