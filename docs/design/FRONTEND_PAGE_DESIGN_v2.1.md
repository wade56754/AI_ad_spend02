# 前端页面设计方案 v2.1

> **版本**: v2.1
> **日期**: 2026-01-04
> **状态**: SoT 合规修复版
> **SoT 对齐**: MASTER.md v4.9 | STATE_MACHINE.md v2.9 | DATA_SCHEMA.md v5.11

---

## 1. 设计原则

### 1.1 Phase 1 约束（照亮阶段）

| 允许 | 禁止 |
|------|------|
| ✅ 记录事实 | ❌ 自动阻断 |
| ✅ 展示状态 | ❌ 强制审批流程 |
| ✅ 提示异常 | ❌ 自动惩罚机制 |
| ✅ 高亮警告 | ❌ 拒绝/暂停/冻结功能 |

> **Phase 1 特别说明**：不达标后果仅为「沟通与记录」，不触发任何惩罚性措施。

### 1.2 SoT 裁判链（10 级优先级）

> **来源**: MASTER.md v4.9 §8.1

| 优先级 | 文档 | 版本 | 说明 |
|--------|------|------|------|
| 0 | MASTER.md | v4.9 | 架构宪法，最高优先级 |
| 1 | PRD | v5.2 | 产品需求文档 |
| 2 | docs/archive/BUSINESS_FLOW_MANAGEMENT.md | archived | 业务流程与责任模型（归档参考） |
| 3 | docs/archive/MVP_PHASE_DESIGN.md | archived | Phase 边界与页面定义（归档参考） |
| 4 | STATE_MACHINE.md | v2.9 | 状态定义与转换 |
| 5 | DATA_SCHEMA.md | v5.11 | 表结构与字段 |
| 6 | BUSINESS_RULES.md | v5.2 | 业务规则 |
| 7 | API_SOT.md | v9.7 | API 定义 |
| 8 | ERROR_CODES_SOT.md | v2.2 | 错误码 |
| 9 | AUTH_SPEC.md | v2.2 | 认证授权 |

---

## 2. 双层角色架构

### 2.1 技术层角色（4 角色）

> **来源**: STATE_MACHINE.md v2.9 §2, DATA_SCHEMA.md v5.11 §1.1

| 技术角色 | 数据库值 | 说明 |
|----------|----------|------|
| `admin` | admin | 系统管理员 |
| `finance` | finance | 财务人员 |
| `account_manager` | account_manager | 户管 |
| `media_buyer` | media_buyer | 投手（技术层） |

### 2.2 业务属性（布尔标记）

> **来源**: DATA_SCHEMA.md v5.11 §3.1.1

| 属性 | 说明 | 适用场景 |
|------|------|----------|
| `is_project_owner` | 是否为项目负责人 | 管理项目、审核日报、团队管理 |

> **重要**: DATA_SCHEMA.md v5.11 中仅定义 `is_project_owner` 布尔字段，未定义 `is_ceo` 字段。CEO 身份通过角色映射规则判断。

### 2.3 完整用户模型

```typescript
interface User {
  id: string
  username: string
  role: 'admin' | 'finance' | 'account_manager' | 'media_buyer'
  is_project_owner: boolean
  project_ids?: string[]  // is_project_owner=true 时关联的项目
}

/**
 * CEO 身份判断
 * 来源: DATA_SCHEMA.md v5.11 §1.1 角色映射规则
 * ceo → admin (技术层)，CEO 身份通过应用层业务逻辑判断
 */
function isCeo(user: User): boolean {
  // CEO 通常是 admin 角色 + 特定用户标识（如固定 user_id 或配置表）
  return user.role === 'admin' && checkCeoIdentity(user.id)
}

/**
 * 项目负责人判断
 * 来源: DATA_SCHEMA.md v5.11 §3.1.1
 */
function isProjectOwner(user: User): boolean {
  return user.is_project_owner === true
}
```

### 2.4 技术层到业务层映射

> **来源**: DATA_SCHEMA.md v5.11 §1.1, MASTER.md v4.9 §2.4

| 业务角色 | 技术实现 | 说明 |
|----------|----------|------|
| 老板 (ceo) | `role = 'admin'` + 业务判断 | CEO 身份通过应用层逻辑判断 |
| 项目负责人 (project_owner) | `is_project_owner = true` | 数据库布尔字段 |
| 财务 (finance) | `role = 'finance'` | 直接映射 |
| 投手 (pitcher) | `role = 'media_buyer'` | 业务名→技术名 |
| 户管 (account_manager) | `role = 'account_manager'` | 直接映射 |
| 管理员 (admin) | `role = 'admin'` | 直接映射 |

---

## 3. 状态机定义

### 3.1 日报状态机（Phase 1: 3 状态）

> **来源**: STATE_MACHINE.md v2.9 §7.5.1, PRD_AI_v1.0.md §4.1

```
raw_submitted → trend_ok → final_confirmed
     ↑              ↑              ↑
   投手提交      趋势确认      终态锁定
```

**Phase 1 特性**:
- 无自动风控阻断
- 项目负责人手动审核
- 终态为 `final_confirmed`（非 `final_locked`）
- 不触发 TF-001/002/003 风控规则（Phase 2 启用）

```typescript
type DailyReportStatus = 'raw_submitted' | 'trend_ok' | 'final_confirmed'

const DAILY_REPORT_STATUS_CONFIG = {
  raw_submitted: {
    label: '已提交',
    color: 'blue',
    next: ['trend_ok'],
    description: '投手 T+0 23:59 前提交'
  },
  trend_ok: {
    label: '趋势确认',
    color: 'yellow',
    next: ['final_confirmed'],
    description: '项目负责人确认趋势正常'
  },
  final_confirmed: {
    label: '已确认',
    color: 'green',
    next: [],  // 终态
    description: 'Phase 1 终态，数据可用于统计'
  }
}

// Phase 1 状态流转 UI 示例
function DailyReportActions({ report, user }: Props) {
  const { status } = report
  const canReview = isProjectOwner(user) || user.role === 'admin'

  // Phase 1: 只有3个状态，无风控阻断
  if (status === 'raw_submitted' && canReview) {
    return (
      <Button onClick={() => transition('trend_ok')}>
        确认趋势
      </Button>
    )
  }

  if (status === 'trend_ok' && canReview) {
    return (
      <Button onClick={() => transition('final_confirmed')}>
        最终确认
      </Button>
    )
  }

  if (status === 'final_confirmed') {
    return <Badge variant="success">已锁定</Badge>  // 终态，无操作
  }

  return null
}
```

### 3.2 账户状态机（6 状态）

> **来源**: STATE_MACHINE.md v2.9 §7.1

```
new → testing → active → suspended → dead
                  ↓
               archived
```

```typescript
type AdAccountStatus = 'new' | 'testing' | 'active' | 'suspended' | 'dead' | 'archived'

const AD_ACCOUNT_STATUS_CONFIG = {
  new: { label: '新建', color: 'gray' },
  testing: { label: '测试中', color: 'blue' },
  active: { label: '活跃', color: 'green' },
  suspended: { label: '暂停', color: 'yellow' },
  dead: { label: '死亡', color: 'red' },
  archived: { label: '归档', color: 'gray' }
}
```

### 3.3 充值状态机（7 状态）

> **来源**: STATE_MACHINE.md v2.9 §7.2

```
draft → pending_review → finance_approve → paid → completed
              ↓                              ↓
           rejected                      cancelled
```

```typescript
type TopupStatus = 'draft' | 'pending_review' | 'finance_approve' | 'paid' | 'completed' | 'rejected' | 'cancelled'

const TOPUP_STATUS_CONFIG = {
  draft: { label: '草稿', color: 'gray' },
  pending_review: { label: '待审核', color: 'blue' },
  finance_approve: { label: '财务已批', color: 'yellow' },
  paid: { label: '已付款', color: 'orange' },
  completed: { label: '已完成', color: 'green' },
  rejected: { label: '已拒绝', color: 'red' },
  cancelled: { label: '已取消', color: 'gray' }
}
```

### 3.4 项目状态机（4 状态）

> **来源**: STATE_MACHINE.md v2.9 §7.3

```
draft → active → suspended → archived
```

```typescript
type ProjectStatus = 'draft' | 'active' | 'suspended' | 'archived'

const PROJECT_STATUS_CONFIG = {
  draft: { label: '草稿', color: 'gray' },
  active: { label: '活跃', color: 'green' },
  suspended: { label: '暂停', color: 'yellow' },
  archived: { label: '归档', color: 'gray' }
}
```

---

## 4. 权限矩阵

### 4.1 基础操作权限表

> **来源**: MASTER.md v4.9 §2.4

| 操作 | ceo | project_owner | finance | pitcher | account_manager | admin |
|------|-----|---------------|---------|---------|-----------------|-------|
| 创建用户 | ✓ | - | - | - | - | ✓ |
| 创建项目 | ✓ | - | - | - | - | ✓ |
| 管理项目成员 | ✓ | ✓ | - | - | - | ✓ |
| 创建渠道 | - | - | - | - | ✓ | ✓ |
| 审批渠道 | - | ✓ | - | - | - | ✓ |
| 创建账户 | - | - | - | - | ✓ | ✓ |
| 分配账户 | - | - | - | - | ✓ | ✓ |
| 提交日报 | - | - | - | ✓ | - | - |
| 审核日报 | - | ✓ | - | - | - | ✓ |
| 查看利润 | ✓ | - | ✓ | - | - | ✓ |
| 红冲操作 | - | - | - | - | - | ✓ |

### 4.2 充值权限表

> **来源**: MASTER.md v4.9 §2.1, PRD v5.1 §6.1

| 操作 | pitcher | account_manager | finance | ceo | admin |
|------|---------|-----------------|---------|-----|-------|
| **申请充值** | ✓ | ✓ | - | - | - |
| **审批充值（日常）** | - | - | ✓ | - | ✓ |
| **审批充值（大额）** | - | - | ✓ 初审 | ✓ 终审 | ✓ |
| **执行转账** | - | - | ✓ | - | - |
| **查看充值记录** | ✓ (自己) | ✓ (负责账户) | ✓ (全部) | ✓ (全部) | ✓ (全部) |

**充值审批链说明**:

| 充值类型 | 审批流程 | 阈值（系统配置） |
|----------|----------|------------------|
| 日常充值 | pitcher/account_manager 申请 → finance 审批 | ≤ ¥50,000 |
| 大额充值 | pitcher/account_manager 申请 → finance 初审 → ceo 终审 | > ¥50,000 |

> **Phase 1 说明**：审批流程为建议流程，不强制阻断。老板可随时查看资金状态并介入。

---

## 5. 页面架构

### 5.1 页面清单

| 路由 | 页面名称 | 可访问角色 | 功能说明 |
|------|----------|-----------|----------|
| `/dashboard` | 驾驶舱 | 全部 | 数据概览（按角色过滤） |
| `/daily-reports` | 日报管理 | 全部 | 日报列表、提交、审核 |
| `/projects` | 项目管理 | ceo, project_owner, admin | 项目CRUD |
| `/ad-accounts` | 账户管理 | ceo, account_manager, admin | 账户分配、状态管理 |
| `/channels` | 渠道管理 | ceo, account_manager, admin | 渠道CRUD |
| `/topups` | 充值管理 | 全部 | 充值申请、审批 |
| `/finance` | 财务中心 | ceo, finance, admin | 账本、对账、利润 |
| `/users` | 用户管理 | ceo, admin | 用户CRUD |
| `/settings` | 系统设置 | admin | 系统配置 |

### 5.2 导航配置

> **修复**: 使用 `NavAccess` 接口，基于技术层角色 + 业务属性组合判断

```typescript
// lib/navigation.ts
import {
  LayoutDashboard, FileText, FolderKanban,
  CreditCard, Landmark, Users, Settings, Building2, Wallet
} from 'lucide-react'

// 技术层角色类型
type TechRole = 'admin' | 'finance' | 'account_manager' | 'media_buyer'

// 导航访问控制接口
interface NavAccess {
  techRoles?: TechRole[]           // 允许的技术层角色
  requireProjectOwner?: boolean    // 是否需要项目负责人身份
  requireCeo?: boolean             // 是否需要 CEO 身份
  allowAll?: boolean               // 是否允许所有角色
}

interface NavItem {
  title: string
  href: string
  icon: React.ComponentType
  access: NavAccess
}

export const navItems: NavItem[] = [
  {
    title: '驾驶舱',
    href: '/dashboard',
    icon: LayoutDashboard,
    access: { allowAll: true }
  },
  {
    title: '日报管理',
    href: '/daily-reports',
    icon: FileText,
    access: { allowAll: true }
  },
  {
    title: '项目管理',
    href: '/projects',
    icon: FolderKanban,
    access: {
      techRoles: ['admin'],
      requireProjectOwner: true,
      requireCeo: true
    }
  },
  {
    title: '账户管理',
    href: '/ad-accounts',
    icon: CreditCard,
    access: {
      techRoles: ['admin', 'account_manager'],
      requireCeo: true
    }
  },
  {
    title: '渠道管理',
    href: '/channels',
    icon: Building2,
    access: {
      techRoles: ['admin', 'account_manager'],
      requireCeo: true
    }
  },
  {
    title: '充值管理',
    href: '/topups',
    icon: Wallet,
    access: { allowAll: true }
  },
  {
    title: '财务中心',
    href: '/finance',
    icon: Landmark,
    access: {
      techRoles: ['admin', 'finance'],
      requireCeo: true
    }
  },
  {
    title: '用户管理',
    href: '/users',
    icon: Users,
    access: {
      techRoles: ['admin'],
      requireCeo: true
    }
  },
  {
    title: '系统设置',
    href: '/settings',
    icon: Settings,
    access: {
      techRoles: ['admin']
    }
  }
]

// 导航访问检查函数
function canAccessNav(user: User, access: NavAccess): boolean {
  if (access.allowAll) return true

  // 检查技术层角色
  if (access.techRoles?.includes(user.role)) return true

  // 检查项目负责人身份
  if (access.requireProjectOwner && user.is_project_owner) return true

  // 检查 CEO 身份
  if (access.requireCeo && isCeo(user)) return true

  return false
}
```

---

## 6. 核心页面设计

### 6.1 驾驶舱 `/dashboard`

#### 6.1.1 角色视图差异

| 角色 | 可见数据 |
|------|----------|
| ceo | 全公司数据：总消耗、总收入、毛利、ROI |
| project_owner | 负责项目数据：项目消耗、项目利润、投手绩效 |
| finance | 资金数据：账户余额、待审充值、月度流水 |
| pitcher | 个人数据：我的日报、我的账户、我的CPL |
| account_manager | 账户数据：账户状态分布、待分配账户 |
| admin | 系统数据：用户统计、系统健康、操作日志 |

#### 6.1.2 核心组件

```typescript
// 驾驶舱页面结构
export default function DashboardPage() {
  const { user } = useAuth()

  return (
    <div className="space-y-6">
      {/* KPI 卡片区 - 按角色显示不同指标 */}
      <KPICards
        role={user.role}
        isProjectOwner={user.is_project_owner}
        isCeo={isCeo(user)}
      />

      {/* 趋势图表 */}
      <TrendCharts />

      {/* 待办事项 */}
      <PendingTasks />

      {/* 快捷操作 */}
      <QuickActions role={user.role} />
    </div>
  )
}
```

### 6.2 日报管理 `/daily-reports`

#### 6.2.1 页面功能

| 功能 | 投手 | 项目负责人 | 其他角色 |
|------|------|-----------|----------|
| 查看日报列表 | 仅自己的 | 项目内全部 | 按角色权限 |
| 提交日报 | ✓ | - | - |
| 审核日报 | - | ✓ | admin ✓ |
| 导出日报 | - | ✓ | ceo/finance ✓ |

#### 6.2.2 状态流转 UI

```typescript
// 日报状态操作按钮（Phase 1 版本）
function DailyReportActions({ report, user }: Props) {
  const { status } = report
  const canReview = isProjectOwner(user) || user.role === 'admin'

  // Phase 1: 只有3个状态，无自动风控阻断
  if (status === 'raw_submitted' && canReview) {
    return (
      <Button onClick={() => transition('trend_ok')}>
        确认趋势
      </Button>
    )
  }

  if (status === 'trend_ok' && canReview) {
    return (
      <Button onClick={() => transition('final_confirmed')}>
        最终确认
      </Button>
    )
  }

  if (status === 'final_confirmed') {
    return <Badge variant="success">已锁定</Badge>
  }

  return null
}
```

### 6.3 账户管理 `/ad-accounts`

#### 6.3.1 账户状态看板

```typescript
// 状态分布卡片
const statusGroups = [
  { status: 'new', label: '新建', color: 'gray' },
  { status: 'testing', label: '测试中', color: 'blue' },
  { status: 'active', label: '活跃', color: 'green' },
  { status: 'suspended', label: '暂停', color: 'yellow' },
  { status: 'dead', label: '死亡', color: 'red' },
  { status: 'archived', label: '归档', color: 'gray' }
]

function AccountStatusBoard() {
  return (
    <div className="grid grid-cols-6 gap-4">
      {statusGroups.map(group => (
        <StatusCard key={group.status} {...group} />
      ))}
    </div>
  )
}
```

#### 6.3.2 账户操作权限

| 操作 | account_manager | admin | 其他 |
|------|-----------------|-------|------|
| 创建账户 | ✓ | ✓ | - |
| 分配账户 | ✓ | ✓ | - |
| 修改状态 | ✓ | ✓ | - |
| 归档账户 | ✓ | ✓ | - |
| 查看账户 | ✓ | ✓ | ceo ✓ |

### 6.4 充值管理 `/topups`

#### 6.4.1 状态流转

```
[投手/户管] 创建 → draft
                    ↓
[自动] 提交 → pending_review
                    ↓
[财务/admin] 审批 → finance_approve / rejected
                    ↓
[财务] 付款 → paid
                    ↓
[系统] 完成 → completed / cancelled
```

#### 6.4.2 角色操作

| 状态 | 可操作角色 | 可执行操作 |
|------|-----------|-----------|
| draft | 创建者 | 编辑、提交、删除 |
| pending_review | finance, admin | 审批、拒绝 |
| finance_approve | finance | 标记付款 |
| paid | 系统 | 自动完成 |
| completed | - | 终态 |

### 6.5 财务中心 `/finance`

#### 6.5.1 子页面

| 子路由 | 页面 | 功能 |
|--------|------|------|
| `/finance/ledger` | 账本 | 资金流水记录 |
| `/finance/reconciliation` | 对账 | 数据核对 |
| `/finance/profit` | 利润 | 利润统计报表 |

#### 6.5.2 访问控制

```typescript
// 财务中心权限检查
function FinanceGuard({ children }: Props) {
  const { user } = useAuth()

  const canAccess =
    isCeo(user) ||
    user.role === 'finance' ||
    user.role === 'admin'

  if (!canAccess) {
    return <AccessDenied />
  }

  return children
}
```

---

## 7. 通用组件规范

### 7.1 必须使用的组件

| 场景 | 组件 | 来源 |
|------|------|------|
| 数据列表 | `DataTable` | @/components/ui/data-table |
| 状态标签 | `StatusBadge` | @/components/ui/status-badge |
| 表单 | `Form` + `FormField` | @/components/ui/form |
| 弹窗 | `Dialog` / `AlertDialog` | @/components/ui/dialog |
| 通知 | `toast` | sonner |

### 7.2 StatusBadge 配置

```typescript
// components/ui/status-badge.tsx
const statusVariants = {
  // 日报状态（Phase 1: 3 状态）
  raw_submitted: { label: '已提交', variant: 'blue' },
  trend_ok: { label: '趋势确认', variant: 'yellow' },
  final_confirmed: { label: '已确认', variant: 'green' },

  // 账户状态（6 状态）
  new: { label: '新建', variant: 'gray' },
  testing: { label: '测试中', variant: 'blue' },
  active: { label: '活跃', variant: 'green' },
  suspended: { label: '暂停', variant: 'yellow' },
  dead: { label: '死亡', variant: 'red' },
  archived: { label: '归档', variant: 'gray' },

  // 充值状态（7 状态）
  draft: { label: '草稿', variant: 'gray' },
  pending_review: { label: '待审核', variant: 'blue' },
  finance_approve: { label: '财务已批', variant: 'yellow' },
  paid: { label: '已付款', variant: 'orange' },
  completed: { label: '已完成', variant: 'green' },
  rejected: { label: '已拒绝', variant: 'red' },
  cancelled: { label: '已取消', variant: 'gray' },

  // 项目状态（4 状态）
  // draft, active, suspended, archived 已在上面定义
}
```

---

## 8. API 调用规范

### 8.1 HTTP 客户端

```typescript
// 必须使用 lib/api.ts 中的 apiFetch
import { apiGet, apiPost, apiPut, apiDelete } from '@/lib/api'

// ✅ 正确
const reports = await apiGet('/api/v1/daily-reports')

// ❌ 禁止
fetch('/api/daily-reports')  // 禁止直接 fetch
axios.get('/api/...')        // 禁止使用 axios
```

### 8.2 数据获取

```typescript
// 使用 TanStack Query
import { useQuery, useMutation } from '@tanstack/react-query'

function useDailyReports(filters: Filters) {
  return useQuery({
    queryKey: ['daily-reports', filters],
    queryFn: () => apiGet('/api/v1/daily-reports', { params: filters })
  })
}
```

---

## 9. 错误处理

### 9.1 错误码映射

> **来源**: ERROR_CODES_SOT.md v2.2

| 错误码 | HTTP | 用户提示 | 使用场景 |
|--------|------|----------|----------|
| AUTH_401 | 401 | 登录已过期，请重新登录 | Token 无效或过期 |
| AUTH_403 | 403 | 您没有权限执行此操作 | 角色权限不足 |
| BIZ_001 | 400 | 操作无效 | 业务规则验证失败 |
| BIZ_002 | 404 | 资源不存在 | 根据 ID 查询未找到 |
| BIZ_100 | 400 | 金额必须大于0 | 金额校验失败 |
| BIZ_301 | 400 | 状态转换不允许 | 违反状态机规则 |
| BIZ_302 | 400 | 终态禁止回退 | 终态→非终态（非admin） |

### 9.2 错误处理模式

```typescript
// 统一错误处理
function handleApiError(error: ApiError) {
  const message = ERROR_MESSAGES[error.code] || '操作失败，请稍后重试'

  toast.error(message)

  if (error.code === 'AUTH_401') {
    router.push('/login')
  }
}
```

---

## 10. 技术实现清单

### 10.1 类型定义

```typescript
// types/index.ts

// 技术层角色
export type TechRole = 'admin' | 'finance' | 'account_manager' | 'media_buyer'

// 日报状态 (Phase 1: 3 状态)
export type DailyReportStatus = 'raw_submitted' | 'trend_ok' | 'final_confirmed'

// 账户状态 (6 状态)
export type AdAccountStatus = 'new' | 'testing' | 'active' | 'suspended' | 'dead' | 'archived'

// 充值状态 (7 状态)
export type TopupStatus = 'draft' | 'pending_review' | 'finance_approve' | 'paid' | 'completed' | 'rejected' | 'cancelled'

// 项目状态 (4 状态)
export type ProjectStatus = 'draft' | 'active' | 'suspended' | 'archived'

// 用户模型（对齐 DATA_SCHEMA.md v5.11）
export interface User {
  id: string
  username: string
  role: TechRole
  is_project_owner: boolean  // 数据库字段
  project_ids?: string[]
}
```

### 10.2 权限检查 Hook

```typescript
// hooks/usePermission.ts
export function usePermission() {
  const { user } = useAuth()

  /**
   * 获取业务层角色
   * 映射规则来源: DATA_SCHEMA.md v5.11 §1.1
   */
  const getBusinessRole = (): string => {
    if (isCeo(user)) return 'ceo'
    if (user.is_project_owner) return 'project_owner'
    if (user.role === 'media_buyer') return 'pitcher'
    return user.role
  }

  /**
   * 检查操作权限
   * 权限矩阵来源: MASTER.md v4.9 §2.4
   */
  const can = (action: string): boolean => {
    const role = getBusinessRole()
    return PERMISSION_MATRIX[action]?.includes(role) ?? false
  }

  /**
   * 检查是否为 CEO
   * CEO 身份通过业务逻辑判断
   */
  const checkIsCeo = (): boolean => isCeo(user)

  /**
   * 检查是否为项目负责人
   */
  const checkIsProjectOwner = (): boolean => user.is_project_owner

  return {
    can,
    getBusinessRole,
    isCeo: checkIsCeo,
    isProjectOwner: checkIsProjectOwner
  }
}
```

---

## 11. 修订历史

| 版本 | 日期 | 修订内容 |
|------|------|----------|
| v1.0 | 2026-01-04 | 初始设计 |
| v2.0 | 2026-01-04 | 修复 P0/P1 缺陷，对齐 SoT |
| v2.1 | 2026-01-04 | SoT 合规修复：裁判链、版本号、权限矩阵、错误码、用户模型 |

### v2.0 修复清单

| 编号 | 级别 | 问题 | 修复 |
|------|------|------|------|
| P0-1 | P0 | 日报使用 Phase 2 的 8 状态 | 改用 Phase 1 的 3 状态 |
| P0-2 | P0 | 账户状态枚举错误 | 改用 SoT 定义的 6 状态 |
| P0-3 | P0 | 技术层/业务层角色混淆 | 建立双层角色体系 |
| P1-1 | P1 | 充值状态枚举不完整 | 改用 7 状态 |
| P1-2 | P1 | 项目状态缺少 draft | 添加 draft 状态 |
| P1-3 | P1 | 充值审批权限错误 | finance/admin 审批 |
| P1-4 | P1 | 渠道创建权限错误 | account_manager/admin 创建 |
| P1-5 | P1 | pitcher 技术映射未说明 | 说明 media_buyer 映射 |

---

## 附录 A: SoT 参考文档

| 文档 | 版本 | 路径 |
|------|------|------|
| MASTER.md | v4.9 | docs/sot/MASTER.md |
| DATA_SCHEMA.md | v5.11 | docs/sot/DATA_SCHEMA.md |
| STATE_MACHINE.md | v2.9 | docs/sot/STATE_MACHINE.md |
| BUSINESS_RULES.md | v5.2 | docs/sot/BUSINESS_RULES.md |
| API_SOT.md | v9.7 | docs/sot/API_SOT.md |
| ERROR_CODES_SOT.md | v2.2 | docs/sot/ERROR_CODES_SOT.md |
| AUTH_SPEC.md | v2.2 | docs/sot/AUTH_SPEC.md |

---

## 附录 B: v2.1 修复清单

| 编号 | 级别 | 修复内容 | 状态 |
|------|------|---------|------|
| P1-1 | P1 | 移除 `is_ceo` 布尔字段，改用函数 `isCeo()` 判断 | ✅ |
| P1-2 | P1 | 更新 SoT 裁判链为完整 10 级（§1.2） | ✅ |
| P1-3 | P1 | 更新版本号：DATA_SCHEMA v5.10→v5.7, BUSINESS_RULES v5.0, API_SOT v9.6 | ✅ |
| P1-4 | P1 | 权限矩阵拆分为基础权限表（§4.1）+ 充值权限表（§4.2） | ✅ |
| P2-1 | P2 | 错误码使用 BIZ_301、BIZ_302 格式（§9.1） | ✅ |
| P2-2 | P2 | 日报状态机添加 Phase 1 特性说明和代码示例（§3.1） | ✅ |
| P2-3 | P2 | 驾驶舱角色视图添加 admin 行（§6.1.1） | ✅ |
| P2-4 | P2 | 导航配置改用 `NavAccess` 接口 + `canAccessNav()` 函数（§5.2） | ✅ |

---

**文档维护者**: 前端架构团队
**最后审核**: 2026-01-04
**下次审核**: 下个迭代或重大变更时
