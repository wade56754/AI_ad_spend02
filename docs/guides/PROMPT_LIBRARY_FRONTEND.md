# AI 广告代投系统 - 前端 Claude 提示词库 v3.1

> **文档版本**: v3.1 (完整版 - 57 个任务卡提示词全覆盖 + 类型安全修复)
> **更新日期**: 2026-01-05
> **基准文档**: TASK_CARDS_FRONTEND.md v1.0, PROMPT_LIBRARY.md v2.2
> **优化依据**: Claude 提示词最佳实践 (CREST 框架)
> **技术栈**: Next.js 16 + TypeScript + shadcn/ui + TanStack Query v5

---

# Part 1: 快速入门

## 使用流程图

```
┌─────────────────────────────────────────────────────────────────────┐
│                      提示词使用流程                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Step 1          Step 2          Step 3          Step 4             │
│  ┌─────┐        ┌─────┐        ┌─────┐        ┌─────┐             │
│  │复制  │───────▶│复制  │───────▶│发送  │───────▶│验证  │             │
│  │系统  │        │任务  │        │给    │        │输出  │             │
│  │约束  │        │提示词│        │Claude│        │     │             │
│  └─────┘        └─────┘        └─────┘        └─────┘             │
│     │              │              │              │                  │
│     ▼              ▼              ▼              ▼                  │
│  Part 2         Part 4         等待响应      npm run build         │
│                                                                     │
│  ※ 系统约束每次对话只需复制一次                                        │
│  ※ 任务提示词按需选择对应模块                                          │
└─────────────────────────────────────────────────────────────────────┘
```

## 5 分钟上手指南

### Step 1: 复制系统约束
找到 [Part 2: 系统约束](#part-2-系统约束必须复制)，复制整个代码块。

### Step 2: 选择任务提示词
在 [Part 4: 模块提示词](#part-4-模块提示词) 中找到对应任务。

### Step 3: 组合发送
将系统约束 + 任务提示词粘贴到 Claude，发送。

### Step 4: 验证输出
运行 `npm run build` 确认无编译错误。

## 提示词复制清单

| 场景 | 需要复制 | 位置 |
|------|---------|------|
| 新对话开始 | 系统约束 | Part 2 |
| 类型定义任务 | TASK-FE-COMMON-001 | Part 4.1 |
| 权限 Hook 任务 | TASK-FE-COMMON-002 | Part 4.1 |
| 日报列表页 | TASK-FE-RPT-001 | Part 4.3 |
| 日报提交表单 | TASK-FE-RPT-004 | Part 4.3 |
| 充值申请表单 | TASK-FE-TOP-004 | Part 4.7 |

---

# Part 2: 系统约束（必须复制）

> **重要**: 每次新对话必须先复制此代码块

```
你是 Next.js 16 前端开发专家，负责 AI 广告代投系统前端开发。

【角色特质】
- 代码风格：简洁、类型完整、组件化、可测试
- 优先使用：shadcn/ui 组件、TanStack Query、zod 验证
- 始终考虑：权限控制、错误处理、加载状态、空状态

【SoT 版本锁定】
MASTER.md v4.9 | STATE_MACHINE.md v2.9 | DATA_SCHEMA.md v5.10
FRONTEND_PAGE_DESIGN_v2.1.md | API_SOT.md v9.7 | ERROR_CODES_SOT.md v2.2

═══════════════════════════════════════════════════════════════════════
                         技术栈约束（不可违反）
═══════════════════════════════════════════════════════════════════════

【框架与工具】
- 框架: Next.js 16 (App Router, 'use client' 指令)
- 语言: TypeScript (strict: true, 禁止 any)
- UI库: shadcn/ui + Tailwind CSS
- 状态: TanStack Query v5 (useQuery, useMutation)
- 表单: react-hook-form + zod
- HTTP: apiFetch/apiGet/apiPost (lib/api.ts)
- 图标: lucide-react
- 图表: recharts
- 通知: sonner (toast)

【绝对禁止】
- ❌ fetch() / axios → 使用 apiGet/apiPost
- ❌ <table> HTML → 使用 DataTable 组件
- ❌ <input> HTML → 使用 Input 组件
- ❌ any 类型 → 定义具体类型
- ❌ 缺少 'use client' → hooks 组件必须加
- ❌ console.log 遗留 → 生产代码禁止

═══════════════════════════════════════════════════════════════════════
                         角色白名单（双层架构）
═══════════════════════════════════════════════════════════════════════

【技术层角色（数据库存储）- 仅 4 个】
admin | finance | account_manager | media_buyer

【业务层角色（UI 展示）- 6 个】
ceo | project_owner | finance | pitcher | account_manager | admin

【角色映射规则】
- media_buyer (技术) → pitcher (业务)
- admin + CEO_USER_IDS → ceo (业务)
- is_project_owner = true → project_owner (业务)

【禁止使用的角色】
❌ supervisor (已废弃 PRD v2.2)
❌ data_operator (不在宪法中)
❌ operator (非标准)

═══════════════════════════════════════════════════════════════════════
                         Phase 1 规则（当前阶段）
═══════════════════════════════════════════════════════════════════════

【Phase 1 原则】
记录事实 → 展示状态 → 提示异常 → 不阻断

【Phase 1 允许】
✅ 记录所有操作日志
✅ 展示状态标签和警告
✅ 高亮异常数据
✅ 发送通知提醒

【Phase 1 禁止】
❌ 自动拒绝请求
❌ 自动暂停账户
❌ 自动冻结资金
❌ 强制审批流程

【日报状态限制 - Phase 1 仅 3 个】
raw_submitted (已提交) → trend_ok (已审核) → final_confirmed (已确认)

【禁止的日报状态（Phase 2）】
❌ trend_pending | trend_flagged | trend_resolved
❌ final_pending | final_locked

═══════════════════════════════════════════════════════════════════════
                         组件使用规范
═══════════════════════════════════════════════════════════════════════

【必须使用的组件】
| 场景 | 必须使用 | 禁止使用 |
|------|---------|---------|
| 数据表格 | DataTable | <table> |
| 状态标签 | StatusBadge | 自定义 Badge |
| 表单容器 | Form + FormField | 原生 form |
| 输入框 | Input | <input> |
| 选择器 | Select | <select> |
| 弹窗 | Dialog | Modal / 自定义 |
| 确认框 | AlertDialog | window.confirm |
| 通知 | toast (sonner) | alert |
| 按钮 | Button | <button> |
| 骨架屏 | Skeleton | 自定义加载 |

═══════════════════════════════════════════════════════════════════════
                         防幻觉规则（场景映射）
═══════════════════════════════════════════════════════════════════════

| ID | 触发场景 | 错误行为 | 正确行为 |
|----|---------|---------|---------|
| AH-01 | 字段在 SoT 未定义 | 自己发明字段 | 停止并询问用户 |
| AH-02 | 角色不在白名单 | 使用 supervisor | 使用 project_owner |
| AH-03 | 日报状态超出 Phase 1 | 使用 trend_pending | 只用 3 个状态 |
| AH-04 | 需要管理决策 | 自动拒绝/阻断 | 只记录 + 提示 |
| AH-05 | API 端点不确定 | 猜测 /api/xxx | 查阅 API_SOT.md |
| AH-06 | 组件选择不确定 | 使用原生 HTML | 使用 shadcn/ui |
| AH-07 | 权限规则不明确 | 假设权限开放 | 查阅 MASTER.md |
| AH-08 | 业务逻辑有歧义 | 自作主张实现 | 列出选项并询问 |

【遇到不确定时】
1. 停止当前实现
2. 明确说明不确定的点
3. 列出可能的选项
4. 请求用户确认

═══════════════════════════════════════════════════════════════════════
                         自洽性检查清单
═══════════════════════════════════════════════════════════════════════

完成代码后，必须逐项自检：

□ 文件第一行是否为 'use client'（如果使用 hooks/状态）
□ 是否存在 any 类型（必须消除）
□ 是否使用了 fetch/axios（必须改为 apiGet/apiPost）
□ 是否使用了原生 HTML 表格（必须改为 DataTable）
□ 是否使用了禁止的角色（supervisor/data_operator）
□ 是否使用了 Phase 2 的日报状态
□ 是否有完整的错误处理（onError/catch）
□ 是否有 toast 通知（成功/失败）
□ 是否有加载状态处理（isLoading）
□ 是否有空数据处理（data?.items ?? []）

═══════════════════════════════════════════════════════════════════════
                         正例/反例对比（增强版）
═══════════════════════════════════════════════════════════════════════

【API 调用】
❌ const res = await fetch('/api/users')
❌ const { data } = await axios.get('/api/users')
✅ const data = await apiGet<User[]>('/api/v1/users')

【数据表格】
❌ <table><thead>...</thead><tbody>...</tbody></table>
✅ <DataTable columns={columns} data={data?.items ?? []} />

【状态标签】
❌ <span className="badge-green">已确认</span>
✅ <StatusBadge type="daily_report" status="final_confirmed" />

【表单】
❌ <form onSubmit={handleSubmit}><input name="email" /></form>
✅ <Form {...form}><FormField name="email" render={...} /></Form>

【角色检查】
❌ if (user.role === 'supervisor') { ... }
❌ if (user.is_ceo) { ... }
✅ if (isCeo()) { ... }
✅ if (can('daily_report:review')) { ... }

【日报状态】
❌ status: 'trend_pending' | 'trend_flagged' | 'final_locked'
✅ status: 'raw_submitted' | 'trend_ok' | 'final_confirmed'

【Hook 组件】
❌ export default function Page() { const [x, setX] = useState() }
✅ 'use client'
   export default function Page() { const [x, setX] = useState() }

【类型定义】
❌ const data: any = response
❌ function handle(e: any) {}
✅ const data: UserResponse = response
✅ function handle(e: React.MouseEvent<HTMLButtonElement>) {}

【空值处理】
❌ data.items.map(...)  // 可能 undefined
✅ (data?.items ?? []).map(...)

【数字格式化】
❌ amount.toFixed(2)  // amount 可能不是数字
✅ (Number(amount) || 0).toFixed(2)

【条件渲染】
❌ {isAdmin && <Button>删除</Button>}  // 硬编码角色
✅ {can('user:delete') && <Button>删除</Button>}

【错误处理】
❌ mutationFn: createUser  // 无错误处理
✅ mutationFn: createUser,
   onError: (error) => toast.error(error.message || '操作失败')

【Select 空值】
❌ <SelectItem value="">全部</SelectItem>  // 空字符串报错
✅ <SelectItem value="__all__">全部</SelectItem>
```

---

# Part 3: 增强版任务模板

## 任务模板结构

每个任务提示词包含以下部分：

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. 上下文 (Context)                                              │
│    - 项目/模块/任务ID/技术栈                                       │
│    - 前置条件                                                    │
│    - SoT 引用                                                    │
├─────────────────────────────────────────────────────────────────┤
│ 2. 任务描述 (Task)                                               │
│    - 明确的任务目标                                               │
├─────────────────────────────────────────────────────────────────┤
│ 3. 交付物 (Deliverables)                                         │
│    - 文件列表                                                    │
│    - 预估行数                                                    │
├─────────────────────────────────────────────────────────────────┤
│ 4. 思考要点 (Chain of Thought) ⭐ 新增                            │
│    - 强制分析的 5 个问题                                          │
├─────────────────────────────────────────────────────────────────┤
│ 5. 约束规则 (Constraints)                                        │
│    - 业务约束                                                    │
│    - 技术约束                                                    │
├─────────────────────────────────────────────────────────────────┤
│ 6. 边缘情况 (Edge Cases) ⭐ 新增                                  │
│    - 场景/期望行为/代码示例                                        │
├─────────────────────────────────────────────────────────────────┤
│ 7. 代码参考 (Examples)                                           │
│    - 完整可运行的示例代码                                          │
├─────────────────────────────────────────────────────────────────┤
│ 8. 输出格式要求 (Output Format)                                   │
│    - 结构化输出规范                                               │
├─────────────────────────────────────────────────────────────────┤
│ 9. 提交前自检 (Self-Check) ⭐ 新增                                │
│    - 可勾选的检查项                                               │
├─────────────────────────────────────────────────────────────────┤
│ 10. 验收标准 (Acceptance Criteria)                               │
│     - 可验证的检查清单                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

# Part 4: 模块提示词

## 模块索引

| 模块 | 优先级 | 任务数 | 任务卡范围 | 状态 |
|------|--------|--------|-----------|------|
| [4.1 COMMON 通用模块](#41-common-通用模块) | P0 | 5 | TASK-FE-COMMON-001~005 | 完整 |
| [4.2 DASH 驾驶舱模块](#42-dash-驾驶舱模块) | P0 | 6 | TASK-FE-DASH-001~006 | 完整 |
| [4.3 RPT 日报模块](#43-rpt-日报模块) | P0 | 7 | TASK-FE-RPT-001~007 | 完整 |
| [4.4 PROJ 项目模块](#44-proj-项目模块) | P0 | 7 | TASK-FE-PROJ-001~007 | 完整 |
| [4.5 ACCT 账户模块](#45-acct-账户模块) | P0 | 8 | TASK-FE-ACCT-001~008 | 完整 |
| [4.6 CHAN 渠道模块](#46-chan-渠道模块) | P1 | 4 | TASK-FE-CHAN-001~004 | 索引 |
| [4.7 TOP 充值模块](#47-top-充值模块) | P1 | 7 | TASK-FE-TOP-001~007 | 完整 |
| [4.8 FIN 财务模块](#48-fin-财务模块) | P2 | 5 | TASK-FE-FIN-001~005 | 索引 |
| [4.9 USER 用户模块](#49-user-用户模块) | P2 | 5 | TASK-FE-USER-001~005 | 索引 |
| [4.10 SET 设置模块](#410-set-设置模块) | P3 | 3 | TASK-FE-SET-001~003 | 索引 |

---

## 4.1 COMMON 通用模块

### TASK-FE-COMMON-001: 类型定义与常量

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | common |
| 任务 ID | TASK-FE-COMMON-001 |
| 技术栈 | TypeScript + Next.js 16 |
| 优先级 | P0 |
| 预估工时 | 4h |

**前置条件**: 无

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §2 (双层角色架构)
- STATE_MACHINE.md v2.9 §7 (状态定义)
- DATA_SCHEMA.md v5.10 §1.1 (角色映射)

#### 任务

实现前端类型定义与常量配置，包括：
1. 双层角色类型（技术层 4 个 + 业务层 6 个）
2. 状态枚举（日报 3 个、账户 6 个、充值 7 个、项目 4 个）
3. 用户模型（包含 is_project_owner，不含 is_ceo）
4. 状态配置（标签、颜色、图标）

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/types/roles.ts` | 角色类型定义 | 35-45 |
| `src/types/status.ts` | 状态枚举定义 | 50-60 |
| `src/types/user.ts` | 用户模型 | 25-35 |
| `src/types/index.ts` | 统一导出 | 10-15 |
| `src/lib/constants/status-config.ts` | 状态配置 | 80-100 |

#### 思考要点（必须先分析）

在编码前，请先回答：

1. **角色映射**: 技术层 `media_buyer` 如何映射到业务层 `pitcher`？
2. **CEO 判断**: 为什么不用 `is_ceo` 字段而用 `isCeo()` 函数？
3. **状态数量**: Phase 1 日报为什么只有 3 个状态？其他 5 个状态去哪了？
4. **颜色语义**: 每种状态的颜色（success/warning/error/info）如何选择？
5. **类型安全**: 如何确保状态值只能是白名单中的值？

#### 约束规则

1. 技术层角色枚举**仅包含 4 个值**: `admin`, `finance`, `account_manager`, `media_buyer`
2. 日报状态枚举**仅包含 3 个值**: `raw_submitted`, `trend_ok`, `final_confirmed`
3. User 接口**必须包含** `is_project_owner: boolean`
4. User 接口**不得包含** `is_ceo` 字段
5. 所有状态必须有对应的中文标签和颜色配置

#### 边缘情况

| 场景 | 期望行为 | 代码示例 |
|------|---------|---------|
| 未知角色值 | 类型报错 | `role: 'unknown'` → TS 报错 |
| 未知状态值 | 类型报错 | `status: 'pending'` → TS 报错 |
| 业务层角色转换 | 正确映射 | `media_buyer` → `pitcher` |

#### 代码参考

**文件 1: src/types/roles.ts**
```typescript
/**
 * 角色类型定义
 * SoT: MASTER.md v4.9 §2.4, DATA_SCHEMA.md v5.10 §1.1
 */

// ═══════════════════════════════════════════════════════════════
// 技术层角色（数据库存储值）- 仅 4 个
// ═══════════════════════════════════════════════════════════════
export type TechRole = 'admin' | 'finance' | 'account_manager' | 'media_buyer';

export const TECH_ROLES: TechRole[] = [
  'admin',
  'finance',
  'account_manager',
  'media_buyer',
];

// ═══════════════════════════════════════════════════════════════
// 业务层角色（UI 展示和权限判断）- 6 个
// ═══════════════════════════════════════════════════════════════
export type BusinessRole =
  | 'ceo'            // 老板 - 通过 isCeo() 判断
  | 'project_owner'  // 项目负责人 - 通过 is_project_owner 判断
  | 'finance'        // 财务
  | 'pitcher'        // 投手 (技术层 media_buyer)
  | 'account_manager' // 户管
  | 'admin';         // 管理员

export const BUSINESS_ROLES: BusinessRole[] = [
  'ceo',
  'project_owner',
  'finance',
  'pitcher',
  'account_manager',
  'admin',
];

// ═══════════════════════════════════════════════════════════════
// 角色映射
// ═══════════════════════════════════════════════════════════════
export const TECH_TO_BUSINESS_ROLE: Record<TechRole, BusinessRole> = {
  admin: 'admin',
  finance: 'finance',
  account_manager: 'account_manager',
  media_buyer: 'pitcher', // 关键映射
};

// 角色中文名
export const ROLE_LABELS: Record<BusinessRole, string> = {
  ceo: '老板',
  project_owner: '项目负责人',
  finance: '财务',
  pitcher: '投手',
  account_manager: '户管',
  admin: '管理员',
};
```

**文件 2: src/types/status.ts**
```typescript
/**
 * 状态枚举定义
 * SoT: STATE_MACHINE.md v2.9 §7
 */

// ═══════════════════════════════════════════════════════════════
// 日报状态 - Phase 1 仅 3 个
// ═══════════════════════════════════════════════════════════════
export type DailyReportStatus =
  | 'raw_submitted'    // 已提交 - 投手提交原始数据
  | 'trend_ok'         // 已审核 - 趋势确认通过
  | 'final_confirmed'; // 已确认 - 终态锁定

export const DAILY_REPORT_STATUSES: DailyReportStatus[] = [
  'raw_submitted',
  'trend_ok',
  'final_confirmed',
];

// ═══════════════════════════════════════════════════════════════
// 账户状态 - 6 个
// ═══════════════════════════════════════════════════════════════
export type AdAccountStatus =
  | 'new'        // 新建
  | 'testing'    // 测试中
  | 'active'     // 活跃
  | 'suspended'  // 暂停
  | 'dead'       // 死亡
  | 'archived';  // 归档

export const AD_ACCOUNT_STATUSES: AdAccountStatus[] = [
  'new', 'testing', 'active', 'suspended', 'dead', 'archived',
];

// ═══════════════════════════════════════════════════════════════
// 充值状态 - 7 个
// ═══════════════════════════════════════════════════════════════
export type TopupStatus =
  | 'draft'           // 草稿
  | 'pending_review'  // 待审核
  | 'finance_approve' // 财务已批
  | 'paid'            // 已付款
  | 'completed'       // 已完成
  | 'rejected'        // 已拒绝
  | 'cancelled';      // 已取消

export const TOPUP_STATUSES: TopupStatus[] = [
  'draft', 'pending_review', 'finance_approve',
  'paid', 'completed', 'rejected', 'cancelled',
];

// ═══════════════════════════════════════════════════════════════
// 项目状态 - 4 个
// ═══════════════════════════════════════════════════════════════
export type ProjectStatus =
  | 'draft'     // 草稿
  | 'active'    // 活跃
  | 'suspended' // 暂停
  | 'archived'; // 归档

export const PROJECT_STATUSES: ProjectStatus[] = [
  'draft', 'active', 'suspended', 'archived',
];
```

**文件 3: src/types/user.ts**
```typescript
/**
 * 用户模型
 * SoT: DATA_SCHEMA.md v5.10 §users
 */
import type { TechRole } from './roles';

export interface User {
  id: number;
  email: string;
  name: string;
  full_name?: string;      // 兼容字段
  username?: string;       // 兼容字段
  role: TechRole;
  project_id: number | null;
  is_project_owner: boolean; // ✅ 必须有
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// 注意：不包含 is_ceo 字段
// CEO 身份通过 isCeo() 函数判断，规则：
// - role === 'admin' 且
// - user.id 在 CEO_USER_IDS 环境变量中
```

**文件 4: src/lib/constants/status-config.ts**
```typescript
/**
 * 状态配置
 * SoT: STATE_MACHINE.md v2.9
 */
import type {
  DailyReportStatus,
  AdAccountStatus,
  TopupStatus,
  ProjectStatus,
} from '@/types/status';

type StatusVariant = 'default' | 'success' | 'warning' | 'error' | 'info';

interface StatusConfig {
  label: string;
  variant: StatusVariant;
  description?: string;
}

// ═══════════════════════════════════════════════════════════════
// 日报状态配置 (Phase 1: 3 状态)
// ═══════════════════════════════════════════════════════════════
export const DAILY_REPORT_STATUS_CONFIG: Record<DailyReportStatus, StatusConfig> = {
  raw_submitted: {
    label: '已提交',
    variant: 'info',
    description: '投手已提交原始数据，等待审核',
  },
  trend_ok: {
    label: '已审核',
    variant: 'success',
    description: '项目负责人已确认趋势',
  },
  final_confirmed: {
    label: '已确认',
    variant: 'default',
    description: '终态，数据已锁定',
  },
};

// ═══════════════════════════════════════════════════════════════
// 账户状态配置 (6 状态)
// ═══════════════════════════════════════════════════════════════
export const AD_ACCOUNT_STATUS_CONFIG: Record<AdAccountStatus, StatusConfig> = {
  new: { label: '新建', variant: 'info' },
  testing: { label: '测试中', variant: 'warning' },
  active: { label: '活跃', variant: 'success' },
  suspended: { label: '暂停', variant: 'warning' },
  dead: { label: '死亡', variant: 'error' },
  archived: { label: '归档', variant: 'default' },
};

// ═══════════════════════════════════════════════════════════════
// 充值状态配置 (7 状态)
// ═══════════════════════════════════════════════════════════════
export const TOPUP_STATUS_CONFIG: Record<TopupStatus, StatusConfig> = {
  draft: { label: '草稿', variant: 'default' },
  pending_review: { label: '待审核', variant: 'info' },
  finance_approve: { label: '财务已批', variant: 'success' },
  paid: { label: '已付款', variant: 'success' },
  completed: { label: '已完成', variant: 'default' },
  rejected: { label: '已拒绝', variant: 'error' },
  cancelled: { label: '已取消', variant: 'default' },
};

// ═══════════════════════════════════════════════════════════════
// 项目状态配置 (4 状态)
// ═══════════════════════════════════════════════════════════════
export const PROJECT_STATUS_CONFIG: Record<ProjectStatus, StatusConfig> = {
  draft: { label: '草稿', variant: 'default' },
  active: { label: '活跃', variant: 'success' },
  suspended: { label: '暂停', variant: 'warning' },
  archived: { label: '归档', variant: 'default' },
};
```

#### 输出格式要求

**第一部分: 思考分析**
必须回答上述 5 个思考要点，每点 1-2 句话。

**第二部分: 代码实现**
按顺序输出完整文件：
1. src/types/roles.ts
2. src/types/status.ts
3. src/types/user.ts
4. src/types/index.ts
5. src/lib/constants/status-config.ts

**第三部分: 验证命令**
```bash
npx tsc --noEmit
```
预期: 无类型错误

#### 提交前自检

□ 技术层角色仅 4 个
□ 业务层角色仅 6 个
□ 日报状态仅 3 个（Phase 1）
□ User 有 is_project_owner
□ User 无 is_ceo
□ 无 supervisor/data_operator
□ 所有状态有中文标签
□ TypeScript 编译无错误

#### 验收标准

- [ ] 技术层角色枚举仅包含 4 个值
- [ ] 日报状态枚举仅包含 3 个状态（Phase 1）
- [ ] 账户状态枚举包含 6 个状态
- [ ] 充值状态枚举包含 7 个状态
- [ ] 项目状态枚举包含 4 个状态
- [ ] User 接口包含 is_project_owner 布尔字段
- [ ] User 接口不包含 is_ceo 字段
- [ ] 无废弃角色 (supervisor, data_operator)
- [ ] `npx tsc --noEmit` 无错误

---

### TASK-FE-COMMON-002: 权限检查 Hook (usePermission)

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | common |
| 任务 ID | TASK-FE-COMMON-002 |
| 技术栈 | React Hooks + TypeScript |
| 优先级 | P0 |
| 预估工时 | 4h |

**前置条件**: TASK-FE-COMMON-001 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §10.2 (权限检查 Hook)
- MASTER.md v4.9 §2.4 (权限矩阵)
- AUTH_SPEC.md v2.2 (认证授权规范)

#### 任务

实现权限检查 Hook，提供：
1. `getBusinessRole()` - 获取业务层角色
2. `isCeo()` - 判断 CEO 身份
3. `isProjectOwner()` - 判断项目负责人
4. `can(action)` - 检查操作权限
5. `canAny(actions)` / `canAll(actions)` - 批量权限检查

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/lib/constants/permission-matrix.ts` | 权限矩阵定义 | 70-90 |
| `src/hooks/usePermission.ts` | 权限检查 Hook | 90-120 |

#### 思考要点（必须先分析）

1. **角色判断顺序**: CEO → 项目负责人 → 技术角色映射，为什么这个顺序？
2. **CEO 识别**: 如何通过 `isCeo()` 函数判断？环境变量如何配置？
3. **权限矩阵**: 如何与 MASTER.md v4.9 §2.4 对齐？
4. **缓存策略**: useMemo 的依赖项应该是什么？
5. **加载状态**: 用户信息未加载完成时权限检查返回什么？

#### 约束规则

1. CEO 身份通过 `isCeo()` 函数判断，**非** `is_ceo` 字段
2. 项目负责人通过 `user.is_project_owner` 布尔字段判断
3. 权限矩阵必须与 MASTER.md v4.9 §2.4 完全对齐
4. 用户未登录时所有权限返回 `false`
5. 角色判断顺序：CEO > 项目负责人 > 技术角色映射

#### 边缘情况

| 场景 | 期望行为 | 代码示例 |
|------|---------|---------|
| 用户未登录 | 所有权限 false | `can('any') → false` |
| 用户加载中 | isLoading = true | 显示骨架屏 |
| admin 且在 CEO 列表 | businessRole = 'ceo' | `isCeo() → true` |
| 普通 admin | businessRole = 'admin' | `isCeo() → false` |

#### 代码参考

**文件 1: src/lib/constants/permission-matrix.ts**
```typescript
/**
 * 权限矩阵定义
 * SoT: MASTER.md v4.9 §2.4
 */
import type { BusinessRole } from '@/types/roles';

// ═══════════════════════════════════════════════════════════════
// 操作权限定义
// ═══════════════════════════════════════════════════════════════
export type PermissionAction =
  // 日报操作
  | 'daily_report:create'
  | 'daily_report:view'
  | 'daily_report:view_all'
  | 'daily_report:review'
  | 'daily_report:confirm'
  // 项目操作
  | 'project:create'
  | 'project:view'
  | 'project:edit'
  | 'project:manage_members'
  // 账户操作
  | 'ad_account:create'
  | 'ad_account:view'
  | 'ad_account:assign'
  | 'ad_account:change_status'
  // 充值操作
  | 'topup:create'
  | 'topup:view'
  | 'topup:approve'
  | 'topup:approve_large' // >50000
  // 财务操作
  | 'finance:view'
  | 'finance:export'
  // 用户操作
  | 'user:create'
  | 'user:view'
  | 'user:edit'
  | 'user:delete';

// ═══════════════════════════════════════════════════════════════
// 权限矩阵 - 与 MASTER.md v4.9 §2.4 对齐
// ═══════════════════════════════════════════════════════════════
export const PERMISSION_MATRIX: Record<PermissionAction, BusinessRole[]> = {
  // ─── 日报权限 ───
  'daily_report:create': ['pitcher'],
  'daily_report:view': ['ceo', 'project_owner', 'finance', 'pitcher', 'account_manager', 'admin'],
  'daily_report:view_all': ['ceo', 'admin'],
  'daily_report:review': ['project_owner', 'admin'],
  'daily_report:confirm': ['project_owner', 'admin'],

  // ─── 项目权限 ───
  'project:create': ['ceo', 'admin'],
  'project:view': ['ceo', 'project_owner', 'finance', 'admin'],
  'project:edit': ['ceo', 'project_owner', 'admin'],
  'project:manage_members': ['ceo', 'project_owner', 'admin'],

  // ─── 账户权限 ───
  'ad_account:create': ['account_manager', 'admin'],
  'ad_account:view': ['ceo', 'project_owner', 'account_manager', 'pitcher', 'admin'],
  'ad_account:assign': ['account_manager', 'admin'],
  'ad_account:change_status': ['account_manager', 'admin'],

  // ─── 充值权限 ───
  'topup:create': ['pitcher', 'account_manager'],
  'topup:view': ['ceo', 'project_owner', 'finance', 'pitcher', 'account_manager', 'admin'],
  'topup:approve': ['finance', 'admin'],
  'topup:approve_large': ['ceo'], // 大额充值仅 CEO

  // ─── 财务权限 ───
  'finance:view': ['ceo', 'finance', 'admin'],
  'finance:export': ['ceo', 'finance', 'admin'],

  // ─── 用户权限 ───
  'user:create': ['admin'],
  'user:view': ['ceo', 'admin'],
  'user:edit': ['admin'],
  'user:delete': ['admin'],
};
```

**文件 2: src/hooks/usePermission.ts**
```typescript
'use client';

/**
 * 权限检查 Hook
 * SoT: MASTER.md v4.9 §2.4, AUTH_SPEC.md v2.2
 */
import { useMemo } from 'react';
import { useAuth } from '@/features/auth/hooks/useAuth';
import type { BusinessRole, TechRole } from '@/types/roles';
import { TECH_TO_BUSINESS_ROLE } from '@/types/roles';
import { PERMISSION_MATRIX, type PermissionAction } from '@/lib/constants/permission-matrix';

// CEO 用户 ID 列表（从环境变量获取）
const CEO_USER_IDS = (process.env.NEXT_PUBLIC_CEO_USER_IDS || '')
  .split(',')
  .filter(Boolean)
  .map(Number);

export interface UsePermissionReturn {
  isLoading: boolean;
  businessRole: BusinessRole | null;
  isCeo: () => boolean;
  isProjectOwner: () => boolean;
  can: (action: PermissionAction) => boolean;
  canAny: (actions: PermissionAction[]) => boolean;
  canAll: (actions: PermissionAction[]) => boolean;
}

export function usePermission(): UsePermissionReturn {
  const { user, isLoading } = useAuth();

  return useMemo(() => {
    // ─── 用户未登录或加载中 ───
    if (!user) {
      return {
        isLoading,
        businessRole: null,
        isCeo: () => false,
        isProjectOwner: () => false,
        can: () => false,
        canAny: () => false,
        canAll: () => false,
      };
    }

    // ─── CEO 判断 ───
    // 规则: role = 'admin' 且 user.id 在 CEO_USER_IDS 中
    const checkIsCeo = (): boolean => {
      return user.role === 'admin' && CEO_USER_IDS.includes(user.id);
    };

    // ─── 项目负责人判断 ───
    const checkIsProjectOwner = (): boolean => {
      return user.is_project_owner === true;
    };

    // ─── 获取业务层角色 ───
    // 优先级: CEO > 项目负责人 > 技术角色映射
    const getBusinessRole = (): BusinessRole => {
      if (checkIsCeo()) return 'ceo';
      if (checkIsProjectOwner()) return 'project_owner';
      return TECH_TO_BUSINESS_ROLE[user.role as TechRole] || 'pitcher';
    };

    const businessRole = getBusinessRole();

    // ─── 权限检查 ───
    const can = (action: PermissionAction): boolean => {
      const allowedRoles = PERMISSION_MATRIX[action];
      return allowedRoles?.includes(businessRole) ?? false;
    };

    const canAny = (actions: PermissionAction[]): boolean => {
      return actions.some(action => can(action));
    };

    const canAll = (actions: PermissionAction[]): boolean => {
      return actions.every(action => can(action));
    };

    return {
      isLoading: false,
      businessRole,
      isCeo: checkIsCeo,
      isProjectOwner: checkIsProjectOwner,
      can,
      canAny,
      canAll,
    };
  }, [user, isLoading]);
}

export default usePermission;
```

#### 提交前自检

□ isCeo() 使用函数判断，非字段
□ 角色判断顺序正确 (CEO > 项目负责人 > 技术角色)
□ 权限矩阵与 MASTER.md 对齐
□ 用户未登录时返回 false
□ useMemo 依赖项正确
□ 无 supervisor/data_operator 角色
□ TypeScript 编译无错误

#### 验收标准

- [ ] 实现 `isCeo()` 方法（通过函数判断，非字段）
- [ ] 实现 `isProjectOwner()` 方法
- [ ] 实现 `can(action)` 方法
- [ ] 实现 `canAny(actions)` / `canAll(actions)` 方法
- [ ] 权限矩阵与 MASTER.md v4.9 §2.4 对齐
- [ ] 用户未登录时所有权限返回 false
- [ ] `npx tsc --noEmit` 无错误

---

## 4.3 RPT 日报模块

### TASK-FE-RPT-001: 日报列表页

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | daily-reports |
| 任务 ID | TASK-FE-RPT-001 |
| 技术栈 | Next.js App Router + TanStack Query |
| 优先级 | P0 |
| 预估工时 | 5h |

**前置条件**: TASK-FE-COMMON-005 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §6.2 (日报管理)
- API_SOT.md v9.7 (GET /api/v1/daily-reports)
- STATE_MACHINE.md v2.9 §7.5.1 (日报状态机 - Phase 1)

#### 任务

实现日报列表页，功能包括：
1. 数据列表（DataTable）
2. 状态筛选（仅 3 个状态）
3. 日期范围筛选
4. 分页和排序
5. 按角色过滤数据

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/app/(dashboard)/daily-reports/page.tsx` | 页面入口 | 10-15 |
| `src/features/daily-reports/components/DailyReportsPage.tsx` | 页面组件 | 100-140 |
| `src/features/daily-reports/components/DailyReportsFilters.tsx` | 筛选器 | 60-80 |
| `src/features/daily-reports/components/DailyReportsTable.tsx` | 表格组件 | 80-100 |
| `src/features/daily-reports/hooks/useDailyReports.ts` | 列表 Hook | 30-40 |
| `src/features/daily-reports/services/dailyReportsApi.ts` | API 服务 | 40-60 |
| `src/features/daily-reports/types/dailyReport.types.ts` | 类型定义 | 60-80 |

#### 思考要点（必须先分析）

1. **数据权限**: 投手看自己的，项目负责人看项目的，CEO 看全部 — 这个过滤在前端还是后端做？
2. **状态筛选**: Phase 1 只有 3 个状态，状态 Tab 应该显示什么？
3. **分页设计**: TanStack Query 的 queryKey 如何设计才能正确缓存？
4. **API 调用**: 为什么使用 apiGet 而非 fetch？
5. **空状态**: 没有数据时显示什么？

#### 约束规则

1. 使用 TanStack Query 获取数据（useQuery）
2. 使用 `apiGet` 调用 API（禁止 fetch/axios）
3. 状态筛选仅包含 3 个状态 + "全部"
4. 使用 DataTable 组件（禁止原生 table）
5. 使用 StatusBadge 显示状态

#### 边缘情况

| 场景 | 期望行为 | 代码示例 |
|------|---------|---------|
| 数据为空 | 显示空状态提示 | `<EmptyState message="暂无日报" />` |
| 加载中 | 显示骨架屏 | `if (isLoading) return <TableSkeleton />` |
| 请求失败 | 显示错误提示 | `if (error) return <ErrorAlert />` |
| 无权限 | 隐藏创建按钮 | `{can('daily_report:create') && ...}` |
| 金额为 null | 显示 0.00 | `(Number(raw_spend) \|\| 0).toFixed(2)` |

#### 代码参考

**文件 1: src/features/daily-reports/types/dailyReport.types.ts**
```typescript
/**
 * 日报类型定义
 * SoT: STATE_MACHINE.md v2.9 §7.5.1 (Phase 1)
 */

// ═══════════════════════════════════════════════════════════════
// Phase 1: 仅 3 个状态
// ═══════════════════════════════════════════════════════════════
export type DailyReportStatus = 'raw_submitted' | 'trend_ok' | 'final_confirmed';

export const DAILY_REPORT_STATUS_OPTIONS = [
  { value: '__all__', label: '全部' },
  { value: 'raw_submitted', label: '已提交' },
  { value: 'trend_ok', label: '已审核' },
  { value: 'final_confirmed', label: '已确认' },
] as const;

// ═══════════════════════════════════════════════════════════════
// 日报实体
// ═══════════════════════════════════════════════════════════════
export interface DailyReport {
  id: number;
  ad_account_id: number;
  ad_account_name: string;
  project_id: number;
  project_name: string;
  report_date: string; // YYYY-MM-DD
  raw_spend: number;
  follows_count: number;
  result_count: number;
  cost_per_follow: number | null;
  cost_per_result: number | null;
  status: DailyReportStatus;
  submitter_name: string;
  created_at: string;
  updated_at: string;
}

// ═══════════════════════════════════════════════════════════════
// 筛选参数
// ═══════════════════════════════════════════════════════════════
export interface DailyReportFilters {
  status?: DailyReportStatus | '__all__';
  project_id?: number;
  ad_account_id?: number;
  start_date?: string;
  end_date?: string;
}

export interface DailyReportListParams extends DailyReportFilters {
  page?: number;
  page_size?: number;
  sort_by?: 'report_date' | 'raw_spend' | 'created_at';
  sort_order?: 'asc' | 'desc';
}
```

**文件 2: src/features/daily-reports/services/dailyReportsApi.ts**
```typescript
/**
 * 日报 API 服务
 * SoT: API_SOT.md v9.7
 */
import { apiGet, type PaginatedResponse } from '@/lib/api';
import type { DailyReport, DailyReportListParams } from '../types';

const BASE_PATH = '/api/v1/daily-reports';

export async function getDailyReports(
  params: DailyReportListParams = {}
): Promise<PaginatedResponse<DailyReport>> {
  const searchParams = new URLSearchParams();

  // 分页参数
  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));

  // 筛选参数
  if (params.status && params.status !== '__all__') {
    searchParams.set('status', params.status);
  }
  if (params.project_id) searchParams.set('project_id', String(params.project_id));
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);

  // 排序参数
  if (params.sort_by) searchParams.set('sort_by', params.sort_by);
  if (params.sort_order) searchParams.set('sort_order', params.sort_order);

  const query = searchParams.toString();
  return apiGet<PaginatedResponse<DailyReport>>(
    query ? `${BASE_PATH}?${query}` : BASE_PATH
  );
}
```

**文件 3: src/features/daily-reports/hooks/useDailyReports.ts**
```typescript
'use client';

/**
 * 日报列表 Hook
 */
import { useQuery } from '@tanstack/react-query';
import { getDailyReports } from '../services/dailyReportsApi';
import type { DailyReportListParams } from '../types';

export function useDailyReports(params: DailyReportListParams = {}) {
  return useQuery({
    // queryKey 包含所有参数，确保参数变化时重新请求
    queryKey: ['daily-reports', params],
    queryFn: () => getDailyReports(params),
    staleTime: 2 * 60 * 1000, // 2 分钟内不重复请求
  });
}
```

**文件 4: src/features/daily-reports/components/DailyReportsPage.tsx**
```typescript
'use client';

/**
 * 日报列表页
 * SoT: FRONTEND_PAGE_DESIGN_v2.1.md §6.2
 */
import { useState } from 'react';
import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { usePermission } from '@/hooks/usePermission';
import { useDailyReports } from '../hooks/useDailyReports';
import { DailyReportsFilters } from './DailyReportsFilters';
import { DailyReportsTable } from './DailyReportsTable';
import { DailyReportForm } from './DailyReportForm';
import type { DailyReportListParams } from '../types';

export function DailyReportsPage() {
  const { can } = usePermission();
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [params, setParams] = useState<DailyReportListParams>({
    page: 1,
    page_size: 20,
    status: '__all__',
    sort_by: 'report_date',
    sort_order: 'desc',
  });

  const { data, isLoading, error } = useDailyReports(params);

  // ─── 加载状态 ───
  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-[400px] w-full" />
      </div>
    );
  }

  // ─── 错误状态 ───
  if (error) {
    return (
      <div className="p-4 border border-red-200 bg-red-50 rounded-lg">
        <p className="text-red-600">加载失败: {error.message}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 标题栏 */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">日报管理</h1>
        {can('daily_report:create') && (
          <Button onClick={() => setIsFormOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            提交日报
          </Button>
        )}
      </div>

      {/* 筛选器 */}
      <DailyReportsFilters
        value={params}
        onChange={(newParams) => setParams({ ...params, ...newParams, page: 1 })}
      />

      {/* 数据表格 */}
      <DailyReportsTable
        data={data?.items ?? []}
        pagination={{
          page: params.page ?? 1,
          pageSize: params.page_size ?? 20,
          total: data?.total ?? 0,
          onPageChange: (page) => setParams({ ...params, page }),
        }}
      />

      {/* 提交表单弹窗 */}
      <DailyReportForm
        open={isFormOpen}
        onOpenChange={setIsFormOpen}
      />
    </div>
  );
}

export default DailyReportsPage;
```

#### 提交前自检

□ 第一行是 'use client'
□ 使用 apiGet 而非 fetch
□ 使用 DataTable 而非 table
□ 使用 StatusBadge 显示状态
□ 状态筛选仅 3 个 + 全部
□ 有加载状态处理
□ 有错误状态处理
□ 有空数据处理
□ 权限检查使用 can()
□ 金额格式化安全 (Number() || 0)

#### 验收标准

- [ ] 使用 DataTable 组件
- [ ] 使用 TanStack Query (useQuery)
- [ ] 使用 apiGet 调用 API
- [ ] 状态筛选仅包含 3 个状态
- [ ] 状态显示使用 StatusBadge
- [ ] 支持分页、筛选、排序
- [ ] 有加载/错误/空状态处理
- [ ] 权限检查正确
- [ ] `npm run build` 无错误

---

## 4.2 DASH 驾驶舱模块

### TASK-FE-DASH-001: 驾驶舱页面框架

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | dashboard |
| 任务 ID | TASK-FE-DASH-001 |
| 技术栈 | Next.js App Router + TanStack Query |
| 优先级 | P0 |
| 预估工时 | 4h |

**前置条件**: TASK-FE-COMMON-002 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §6.1 (驾驶舱设计)
- MASTER.md v4.9 §2.4 (权限矩阵)

#### 任务

实现驾驶舱页面框架：
1. 页面布局（KPI 卡片区、趋势图表、待办事项、快捷操作）
2. 根据用户角色显示不同数据
3. 响应式布局

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/app/(dashboard)/page.tsx` | 页面入口 | 10-15 |
| `src/features/dashboard/components/DashboardPage.tsx` | 页面组件 | 100-140 |
| `src/features/dashboard/hooks/useDashboardData.ts` | 数据查询 Hook | 40-60 |
| `src/features/dashboard/types/dashboard.types.ts` | 类型定义 | 30-50 |

#### 思考要点（必须先分析）

1. **角色视图**: 6 种角色的驾驶舱视图有什么区别？
2. **数据权限**: 投手看自己的，项目负责人看项目的，CEO 看全部 — API 如何区分？
3. **布局设计**: 如何使用 grid 实现响应式 4 列布局？
4. **加载状态**: 多个 KPI 卡片同时加载如何处理？
5. **刷新策略**: staleTime 设置多少合适？

#### 约束规则

1. 使用 TanStack Query 获取数据
2. 使用 `apiGet` 调用 API
3. 权限检查使用 `usePermission`
4. 响应式布局使用 Tailwind grid

#### 代码参考

**文件: src/features/dashboard/components/DashboardPage.tsx**
```typescript
'use client';

/**
 * 驾驶舱页面
 * SoT: FRONTEND_PAGE_DESIGN_v2.1.md §6.1
 */
import { Suspense } from 'react';
import { Skeleton } from '@/components/ui/skeleton';
import { usePermission } from '@/hooks/usePermission';
import { KPICards } from './KPICards';
import { TrendCharts } from './TrendCharts';
import { PendingTasks } from './PendingTasks';
import { QuickActions } from './QuickActions';

export function DashboardPage() {
  const { businessRole, isLoading } = usePermission();

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="space-y-6">
      {/* 标题 */}
      <h1 className="text-2xl font-bold">运营驾驶舱</h1>

      {/* KPI 卡片区 */}
      <Suspense fallback={<KPICardsSkeleton />}>
        <KPICards role={businessRole} />
      </Suspense>

      {/* 趋势图表 + 待办事项 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Suspense fallback={<ChartSkeleton />}>
            <TrendCharts role={businessRole} />
          </Suspense>
        </div>
        <div>
          <Suspense fallback={<TasksSkeleton />}>
            <PendingTasks role={businessRole} />
          </Suspense>
        </div>
      </div>

      {/* 快捷操作 */}
      <QuickActions role={businessRole} />
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-48" />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-32" />
        ))}
      </div>
    </div>
  );
}

function KPICardsSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <Skeleton key={i} className="h-32" />
      ))}
    </div>
  );
}

function ChartSkeleton() {
  return <Skeleton className="h-80" />;
}

function TasksSkeleton() {
  return <Skeleton className="h-80" />;
}

export default DashboardPage;
```

#### 提交前自检

□ 第一行是 'use client'
□ 使用 usePermission 获取角色
□ 有 Suspense 边界
□ 有加载状态处理
□ 响应式布局正确
□ 无 any 类型

#### 验收标准

- [ ] 页面布局包含 KPI 卡片区、趋势图表、待办事项、快捷操作
- [ ] 根据用户角色显示不同数据
- [ ] 响应式布局（桌面/平板）
- [ ] 有加载状态处理
- [ ] `npm run build` 无错误

---

### TASK-FE-DASH-002: KPI 卡片组件

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | dashboard |
| 任务 ID | TASK-FE-DASH-002 |
| 技术栈 | React + TanStack Query |
| 优先级 | P0 |
| 预估工时 | 4h |

**前置条件**: TASK-FE-DASH-001 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §6.1.1 (角色视图差异)
- FRONTEND_PAGE_DESIGN_v2.1.md §6.1.2 (核心组件)

#### 任务

实现 KPI 卡片组件，按角色显示不同指标：
1. CEO: 总消耗、总收入、毛利、ROI
2. 项目负责人: 项目消耗、项目利润、投手绩效
3. 财务: 账户余额、待审充值、月度流水
4. 投手: 我的日报、我的账户、我的 CPL
5. 户管: 账户状态分布、待分配账户
6. Admin: 用户统计、系统健康

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/dashboard/components/KPICards.tsx` | KPI 卡片容器 | 80-100 |
| `src/features/dashboard/components/KPICard.tsx` | 单个 KPI 卡片 | 40-60 |
| `src/features/dashboard/lib/kpi-config.ts` | KPI 配置 | 60-80 |
| `src/features/dashboard/hooks/useKPIData.ts` | KPI 数据 Hook | 40-60 |

#### 思考要点（必须先分析）

1. **角色判断**: 如何根据 businessRole 选择显示哪些 KPI？
2. **数据获取**: 6 种角色的 KPI 数据 API 端点是否相同？
3. **格式化**: 金额、百分比、数量如何格式化显示？
4. **趋势指示**: 如何显示同比/环比变化（上升/下降箭头）？
5. **错误处理**: 单个 KPI 请求失败如何处理？

#### 约束规则

1. 角色判断使用 usePermission Hook
2. CEO 身份使用 isCeo() 判断
3. 金额格式化使用 `(Number(value) || 0).toFixed(2)`
4. 使用 TanStack Query 获取数据

#### 代码参考

**文件: src/features/dashboard/components/KPICard.tsx**
```typescript
'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { cn } from '@/lib/utils';

interface KPICardProps {
  title: string;
  value: string | number;
  trend?: {
    value: number;
    label: string;
  };
  icon?: React.ReactNode;
  loading?: boolean;
}

export function KPICard({ title, value, trend, icon, loading }: KPICardProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <div className="h-4 w-24 bg-gray-200 animate-pulse rounded" />
        </CardHeader>
        <CardContent>
          <div className="h-8 w-32 bg-gray-200 animate-pulse rounded" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        {icon && <div className="text-muted-foreground">{icon}</div>}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {trend && (
          <p className={cn(
            "text-xs flex items-center gap-1",
            trend.value >= 0 ? "text-green-600" : "text-red-600"
          )}>
            {trend.value >= 0 ? (
              <TrendingUp className="h-4 w-4" />
            ) : (
              <TrendingDown className="h-4 w-4" />
            )}
            <span>
              {trend.value >= 0 ? '+' : ''}{trend.value}% {trend.label}
            </span>
          </p>
        )}
      </CardContent>
    </Card>
  );
}
```

**文件: src/features/dashboard/components/KPICards.tsx**
```typescript
'use client';

import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/lib/api';
import { KPICard } from './KPICard';
import { DollarSign, Users, FileText, CreditCard } from 'lucide-react';
import type { BusinessRole } from '@/types/roles';

interface Props {
  role: BusinessRole | null;
}

export function KPICards({ role }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard', 'kpi', role],
    queryFn: () => apiGet<DashboardKPI>('/api/v1/dashboard/kpi'),
    staleTime: 2 * 60 * 1000,
  });

  // 根据角色返回不同的 KPI 配置
  const kpis = getKPIsByRole(role, data);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {kpis.map((kpi) => (
        <KPICard
          key={kpi.title}
          title={kpi.title}
          value={kpi.value}
          trend={kpi.trend}
          icon={kpi.icon}
          loading={isLoading}
        />
      ))}
    </div>
  );
}

function getKPIsByRole(role: BusinessRole | null, data?: DashboardKPI) {
  const formatCurrency = (v: number) => `¥${(Number(v) || 0).toLocaleString()}`;
  const formatPercent = (v: number) => `${(Number(v) || 0).toFixed(1)}%`;

  switch (role) {
    case 'ceo':
      return [
        { title: '总消耗', value: formatCurrency(data?.total_spend ?? 0), icon: <DollarSign className="h-4 w-4" /> },
        { title: '总收入', value: formatCurrency(data?.total_revenue ?? 0), icon: <DollarSign className="h-4 w-4" /> },
        { title: '毛利', value: formatCurrency(data?.gross_profit ?? 0), icon: <DollarSign className="h-4 w-4" /> },
        { title: 'ROI', value: formatPercent(data?.roi ?? 0), icon: <TrendingUp className="h-4 w-4" /> },
      ];
    case 'pitcher':
      return [
        { title: '今日消耗', value: formatCurrency(data?.my_spend ?? 0), icon: <DollarSign className="h-4 w-4" /> },
        { title: '待提交日报', value: data?.pending_reports ?? 0, icon: <FileText className="h-4 w-4" /> },
        { title: '我的账户', value: data?.my_accounts ?? 0, icon: <CreditCard className="h-4 w-4" /> },
        { title: '平均 CPL', value: formatCurrency(data?.avg_cpl ?? 0), icon: <Users className="h-4 w-4" /> },
      ];
    // ... 其他角色
    default:
      return [];
  }
}

interface DashboardKPI {
  total_spend?: number;
  total_revenue?: number;
  gross_profit?: number;
  roi?: number;
  my_spend?: number;
  pending_reports?: number;
  my_accounts?: number;
  avg_cpl?: number;
}
```

#### 提交前自检

□ 第一行是 'use client'
□ 角色判断使用传入的 role 参数
□ 金额格式化安全 (Number() || 0)
□ 有加载状态处理
□ 使用 TanStack Query
□ 无 any 类型

#### 验收标准

- [ ] CEO 视图显示 4 个 KPI
- [ ] 投手视图显示 4 个 KPI
- [ ] 支持加载状态
- [ ] 金额格式化正确
- [ ] `npm run build` 无错误

---

## 4.4 PROJ 项目模块

### TASK-FE-PROJ-001: 项目列表页

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | projects |
| 任务 ID | TASK-FE-PROJ-001 |
| 技术栈 | Next.js App Router + TanStack Query |
| 优先级 | P0 |
| 预估工时 | 5h |

**前置条件**: TASK-FE-COMMON-005 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §5.1 (页面清单)
- API_SOT.md v9.7 (GET /api/v1/projects)

#### 任务

实现项目列表页：
1. 数据列表（DataTable）
2. 状态筛选（4 个状态）
3. 分页和排序
4. 按角色过滤数据

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/app/(dashboard)/projects/page.tsx` | 页面入口 | 10-15 |
| `src/features/projects/components/ProjectsPage.tsx` | 页面组件 | 100-140 |
| `src/features/projects/components/ProjectsTable.tsx` | 表格组件 | 80-100 |
| `src/features/projects/hooks/useProjects.ts` | 列表 Hook | 30-40 |
| `src/features/projects/services/projectsApi.ts` | API 服务 | 40-60 |
| `src/features/projects/types/project.types.ts` | 类型定义 | 40-60 |

#### 思考要点（必须先分析）

1. **访问权限**: 哪些角色可以访问项目页面？
2. **数据权限**: 项目负责人只能看自己的项目，CEO 看全部 — 后端还是前端过滤？
3. **状态筛选**: 4 个状态 + "全部"如何设计？
4. **创建权限**: 哪些角色可以创建项目？
5. **状态切换**: 项目状态如何切换？

#### 约束规则

1. 使用 DataTable 组件（禁止原生 table）
2. 使用 StatusBadge 显示状态
3. 仅 ceo, project_owner, finance(只读), admin 可访问
4. 创建项目仅 ceo, admin 可操作

#### 代码参考

**文件: src/features/projects/types/project.types.ts**
```typescript
/**
 * 项目类型定义
 * SoT: STATE_MACHINE.md v2.9
 */

// 项目状态 - 4 个
export type ProjectStatus = 'draft' | 'active' | 'suspended' | 'archived';

export const PROJECT_STATUS_OPTIONS = [
  { value: '__all__', label: '全部' },
  { value: 'draft', label: '草稿' },
  { value: 'active', label: '活跃' },
  { value: 'suspended', label: '暂停' },
  { value: 'archived', label: '归档' },
] as const;

export interface Project {
  id: number;
  name: string;
  code: string;
  description?: string;
  owner_id: number;
  owner_name: string;
  status: ProjectStatus;
  unit_price: number;
  service_fee_rate: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectListParams {
  status?: ProjectStatus | '__all__';
  page?: number;
  page_size?: number;
  sort_by?: 'name' | 'created_at' | 'updated_at';
  sort_order?: 'asc' | 'desc';
}
```

**文件: src/features/projects/components/ProjectsPage.tsx**
```typescript
'use client';

/**
 * 项目列表页
 * SoT: FRONTEND_PAGE_DESIGN_v2.1.md §5.1
 */
import { useState } from 'react';
import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { usePermission } from '@/hooks/usePermission';
import { useProjects } from '../hooks/useProjects';
import { ProjectsFilters } from './ProjectsFilters';
import { ProjectsTable } from './ProjectsTable';
import { ProjectForm } from './ProjectForm';
import type { ProjectListParams } from '../types';

export function ProjectsPage() {
  const { can, isLoading: permLoading } = usePermission();
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [params, setParams] = useState<ProjectListParams>({
    page: 1,
    page_size: 20,
    status: '__all__',
    sort_by: 'created_at',
    sort_order: 'desc',
  });

  const { data, isLoading, error } = useProjects(params);

  // 权限检查：仅 ceo, project_owner, finance, admin 可访问
  if (permLoading) {
    return <Skeleton className="h-[400px] w-full" />;
  }

  if (!can('project:view')) {
    return (
      <div className="p-4 border border-yellow-200 bg-yellow-50 rounded-lg">
        <p className="text-yellow-600">您没有访问此页面的权限</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 border border-red-200 bg-red-50 rounded-lg">
        <p className="text-red-600">加载失败: {error.message}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 标题栏 */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">项目管理</h1>
        {can('project:create') && (
          <Button onClick={() => setIsFormOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            新建项目
          </Button>
        )}
      </div>

      {/* 筛选器 */}
      <ProjectsFilters
        value={params}
        onChange={(newParams) => setParams({ ...params, ...newParams, page: 1 })}
      />

      {/* 数据表格 */}
      <ProjectsTable
        data={data?.items ?? []}
        loading={isLoading}
        pagination={{
          page: params.page ?? 1,
          pageSize: params.page_size ?? 20,
          total: data?.total ?? 0,
          onPageChange: (page) => setParams({ ...params, page }),
        }}
      />

      {/* 新建表单弹窗 */}
      <ProjectForm
        open={isFormOpen}
        onOpenChange={setIsFormOpen}
      />
    </div>
  );
}

export default ProjectsPage;
```

#### 提交前自检

□ 第一行是 'use client'
□ 使用 apiGet 而非 fetch
□ 使用 DataTable 而非 table
□ 使用 StatusBadge 显示状态
□ 状态筛选 4 个 + 全部
□ 权限检查使用 can()
□ 有加载/错误/空状态处理

#### 验收标准

- [ ] 使用 DataTable 组件
- [ ] 使用 TanStack Query
- [ ] 状态筛选包含 4 个状态
- [ ] 权限检查正确
- [ ] 有加载/错误/空状态处理
- [ ] `npm run build` 无错误

---

### TASK-FE-PROJ-002: 项目筛选器

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | projects |
| 任务 ID | TASK-FE-PROJ-002 |
| 技术栈 | Next.js App Router + URL State |
| 优先级 | P0 |
| 预估工时 | 2h |

**前置条件**: TASK-FE-PROJ-001 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §3.4 (项目状态机)
- STATE_MACHINE.md v2.9 §7.3 (项目状态机)

#### 任务

实现项目筛选器：
1. 状态筛选（4 个状态 + 全部）
2. 负责人筛选（仅 CEO/Admin 可见）
3. 筛选条件同步到 URL
4. 触发 API 重新请求

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/projects/components/ProjectsFilters.tsx` | 筛选器组件 | 80-120 |

#### 思考要点（必须先分析）

1. **权限控制**: 负责人筛选仅 CEO/Admin 可见，如何隐藏？
2. **数据来源**: 负责人列表从哪里获取？
3. **URL 同步**: 如何同步筛选条件到 URL searchParams？
4. **状态机**: 4 个项目状态是什么？

#### 约束规则

1. 项目状态仅 4 个: draft, active, suspended, archived
2. 负责人筛选仅 CEO/Admin 可见
3. 使用 Select 组件（禁止原生 select）
4. 筛选变化时 page 重置为 1

#### 边缘情况

| 场景 | 处理方式 |
|------|---------|
| 负责人列表为空 | 显示空选项 |
| URL 参数非法 | 使用默认值 |
| 快速连续切换 | 防抖处理 |

#### 代码参考

**文件: src/features/projects/components/ProjectsFilters.tsx**
```typescript
'use client';

/**
 * 项目筛选器
 * SoT: FRONTEND_PAGE_DESIGN_v2.1.md §3.4
 */
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { usePermission } from '@/hooks/usePermission';
import { useOwners } from '../hooks/useOwners';
import { PROJECT_STATUS_OPTIONS, type ProjectListParams } from '../types';

interface ProjectsFiltersProps {
  value: ProjectListParams;
  onChange: (params: Partial<ProjectListParams>) => void;
}

export function ProjectsFilters({ value, onChange }: ProjectsFiltersProps) {
  const { can } = usePermission();
  const { data: owners } = useOwners();

  // 仅 CEO/Admin 可见负责人筛选
  const showOwnerFilter = can('project:view_all');

  return (
    <div className="flex gap-4 flex-wrap">
      {/* 状态筛选 */}
      <Select
        value={value.status ?? '__all__'}
        onValueChange={(status) => onChange({ status: status as ProjectListParams['status'] })}
      >
        <SelectTrigger className="w-[160px]">
          <SelectValue placeholder="选择状态" />
        </SelectTrigger>
        <SelectContent>
          {PROJECT_STATUS_OPTIONS.map(opt => (
            <SelectItem key={opt.value} value={opt.value}>
              {opt.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* 负责人筛选 - 仅 CEO/Admin 可见 */}
      {showOwnerFilter && (
        <Select
          value={value.owner_id?.toString() ?? '__all__'}
          onValueChange={(id) => onChange({ owner_id: id === '__all__' ? undefined : Number(id) })}
        >
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="选择负责人" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">全部负责人</SelectItem>
            {owners?.map(owner => (
              <SelectItem key={owner.id} value={owner.id.toString()}>
                {owner.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}
    </div>
  );
}
```

#### 输出格式要求

1. 第一行必须是 `'use client'`
2. 状态选项使用 PROJECT_STATUS_OPTIONS 常量
3. 权限检查使用 `can()` 函数

#### 提交前自检

□ 第一行是 'use client'
□ 使用 Select 组件
□ 状态筛选 4 个 + 全部
□ 负责人筛选权限控制
□ value/onChange 模式

#### 验收标准

- [ ] 状态筛选包含 4 个状态 + 全部
- [ ] 负责人筛选仅 CEO/Admin 可见
- [ ] 筛选条件同步到 URL
- [ ] `npm run build` 无错误

---

### TASK-FE-PROJ-003: 项目表格组件

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | projects |
| 任务 ID | TASK-FE-PROJ-003 |
| 技术栈 | DataTable + StatusBadge |
| 优先级 | P0 |
| 预估工时 | 3h |

**前置条件**: TASK-FE-PROJ-001, TASK-FE-COMMON-003 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §7.1 (必须使用的组件)
- STATE_MACHINE.md v2.9 §7.3 (项目状态机)

#### 任务

实现项目表格：
1. 使用 DataTable 组件
2. 显示字段：项目名称、负责人、状态、账户数、创建时间
3. 状态列使用 StatusBadge
4. 支持行操作按钮

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/projects/components/ProjectsTable.tsx` | 表格组件 | 120-160 |
| `src/features/projects/components/ProjectRow.tsx` | 行组件（可选） | 40-60 |

#### 思考要点（必须先分析）

1. **列定义**: DataTable 的 columns 如何定义？
2. **状态显示**: StatusBadge 需要什么参数？
3. **行操作**: 哪些操作需要显示？权限如何控制？
4. **分页**: 分页组件如何集成？

#### 约束规则

1. 使用 DataTable 组件（禁止原生 table）
2. 使用 StatusBadge 显示状态（禁止手写 Badge）
3. 状态值仅 4 个: draft, active, suspended, archived
4. 操作按钮根据权限显示

#### 边缘情况

| 场景 | 处理方式 |
|------|---------|
| 数据为空 | 显示空状态提示 |
| 加载中 | 显示 Skeleton |
| 字段过长 | 截断显示 |
| 账户数为 0 | 显示 0 |

#### 代码参考

**文件: src/features/projects/components/ProjectsTable.tsx**
```typescript
'use client';

/**
 * 项目表格
 * SoT: FRONTEND_PAGE_DESIGN_v2.1.md §7.1
 */
import { ColumnDef } from '@tanstack/react-table';
import { Eye, Edit, MoreHorizontal } from 'lucide-react';
import { DataTable } from '@/components/ui/data-table';
import { StatusBadge } from '@/components/ui/status-badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { usePermission } from '@/hooks/usePermission';
import { formatDate } from '@/lib/utils';
import type { Project } from '../types';

interface ProjectsTableProps {
  data: Project[];
  loading?: boolean;
  pagination?: {
    page: number;
    pageSize: number;
    total: number;
    onPageChange: (page: number) => void;
  };
  onView?: (project: Project) => void;
  onEdit?: (project: Project) => void;
}

export function ProjectsTable({
  data,
  loading,
  pagination,
  onView,
  onEdit,
}: ProjectsTableProps) {
  const { can } = usePermission();

  const columns: ColumnDef<Project>[] = [
    {
      accessorKey: 'name',
      header: '项目名称',
      cell: ({ row }) => (
        <div className="font-medium">{row.getValue('name')}</div>
      ),
    },
    {
      accessorKey: 'owner_name',
      header: '负责人',
    },
    {
      accessorKey: 'status',
      header: '状态',
      cell: ({ row }) => (
        <StatusBadge
          type="project"
          value={row.getValue('status')}
        />
      ),
    },
    {
      accessorKey: 'account_count',
      header: '账户数',
      cell: ({ row }) => row.original.account_count ?? 0,
    },
    {
      accessorKey: 'created_at',
      header: '创建时间',
      cell: ({ row }) => formatDate(row.getValue('created_at')),
    },
    {
      id: 'actions',
      header: '操作',
      cell: ({ row }) => {
        const project = row.original;
        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onView?.(project)}>
                <Eye className="h-4 w-4 mr-2" />
                查看详情
              </DropdownMenuItem>
              {can('project:update') && (
                <DropdownMenuItem onClick={() => onEdit?.(project)}>
                  <Edit className="h-4 w-4 mr-2" />
                  编辑
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        );
      },
    },
  ];

  if (loading) {
    return <div className="space-y-2">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="h-12 bg-muted animate-pulse rounded" />
      ))}
    </div>;
  }

  if (data.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        暂无项目数据
      </div>
    );
  }

  return (
    <DataTable
      columns={columns}
      data={data}
      pagination={pagination}
    />
  );
}
```

#### 提交前自检

□ 第一行是 'use client'
□ 使用 DataTable 组件
□ 使用 StatusBadge 显示状态
□ 操作权限检查使用 can()
□ 有空状态和加载状态

#### 验收标准

- [ ] 使用 DataTable 组件
- [ ] 使用 StatusBadge 显示状态
- [ ] 显示所有必需字段
- [ ] 操作按钮权限控制正确
- [ ] `npm run build` 无错误

---

### TASK-FE-PROJ-004: 项目创建/编辑表单

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | projects |
| 任务 ID | TASK-FE-PROJ-004 |
| 技术栈 | react-hook-form + zod + Dialog |
| 优先级 | P0 |
| 预估工时 | 4h |

**前置条件**: TASK-FE-PROJ-001 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (权限矩阵)
- API_SOT.md v9.7 (POST/PUT /api/v1/projects)
- MASTER.md v4.9 §2.4 (角色权限)

#### 任务

实现项目创建/编辑表单：
1. 必填字段：项目名称、负责人
2. 选填字段：描述、计费模式
3. 表单验证（zod）
4. 新建成功显示 toast

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/projects/components/ProjectForm.tsx` | 表单组件 | 150-200 |
| `src/features/projects/components/ProjectFormSchema.ts` | 验证 Schema | 30-50 |
| `src/features/projects/components/ProjectFormDialog.tsx` | 弹窗包装 | 40-60 |
| `src/features/projects/hooks/useProjectMutations.ts` | 变更 Hook | 50-80 |

#### 思考要点（必须先分析）

1. **权限控制**: 仅 ceo, admin 可创建，项目负责人可编辑自己的？
2. **负责人选择**: 负责人列表从哪里获取？
3. **初始状态**: 新建项目初始状态是什么？
4. **编辑模式**: 如何区分新建和编辑？

#### 约束规则

1. 仅 ceo, admin 可创建项目
2. 使用 react-hook-form + zod 验证
3. 新建项目初始状态为 draft
4. 使用 Dialog 组件（禁止 Modal）

#### 边缘情况

| 场景 | 处理方式 |
|------|---------|
| 表单验证失败 | 显示字段错误 |
| 提交失败 | toast.error 显示错误 |
| 项目名重复 | 后端返回错误，前端显示 |
| 弹窗关闭 | 重置表单 |

#### 代码参考

**文件: src/features/projects/components/ProjectFormSchema.ts**
```typescript
import { z } from 'zod';

export const projectFormSchema = z.object({
  name: z.string()
    .min(2, '项目名称至少 2 个字符')
    .max(50, '项目名称最多 50 个字符'),
  owner_id: z.number({
    required_error: '请选择负责人',
  }),
  description: z.string().max(500).optional(),
  billing_mode: z.enum(['per_lead', 'fee_rate']).optional(),
  unit_price: z.number().min(0).optional(),
  service_fee_rate: z.number().min(0).max(100).optional(),
});

export type ProjectFormValues = z.infer<typeof projectFormSchema>;
```

**文件: src/features/projects/hooks/useProjectMutations.ts**
```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { apiPost, apiPut } from '@/lib/api';
import type { ProjectFormValues } from '../components/ProjectFormSchema';

export function useProjectMutations() {
  const queryClient = useQueryClient();

  const createProject = useMutation({
    mutationFn: (data: ProjectFormValues) =>
      apiPost('/api/v1/projects', data),
    onSuccess: () => {
      toast.success('项目创建成功');
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
    onError: (error: Error) => {
      toast.error(`创建失败: ${error.message}`);
    },
  });

  const updateProject = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<ProjectFormValues> }) =>
      apiPut(`/api/v1/projects/${id}`, data),
    onSuccess: () => {
      toast.success('项目更新成功');
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
    onError: (error: Error) => {
      toast.error(`更新失败: ${error.message}`);
    },
  });

  return { createProject, updateProject };
}
```

**文件: src/features/projects/components/ProjectForm.tsx**
```typescript
'use client';

/**
 * 项目表单
 * SoT: API_SOT.md v9.7 POST/PUT /api/v1/projects
 */
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { useOwners } from '../hooks/useOwners';
import { useProjectMutations } from '../hooks/useProjectMutations';
import { projectFormSchema, type ProjectFormValues } from './ProjectFormSchema';
import type { Project } from '../types';

interface ProjectFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  project?: Project; // 编辑模式
}

export function ProjectForm({ open, onOpenChange, project }: ProjectFormProps) {
  const { data: owners } = useOwners();
  const { createProject, updateProject } = useProjectMutations();
  const isEditing = !!project;

  const form = useForm<ProjectFormValues>({
    resolver: zodResolver(projectFormSchema),
    defaultValues: {
      name: '',
      owner_id: undefined,
      description: '',
    },
  });

  // 编辑模式填充数据
  useEffect(() => {
    if (project) {
      form.reset({
        name: project.name,
        owner_id: project.owner_id,
        description: project.description ?? '',
        billing_mode: project.billing_mode,
        unit_price: project.unit_price,
        service_fee_rate: project.service_fee_rate,
      });
    } else {
      form.reset({
        name: '',
        owner_id: undefined,
        description: '',
      });
    }
  }, [project, form]);

  const onSubmit = async (values: ProjectFormValues) => {
    if (isEditing && project) {
      await updateProject.mutateAsync({ id: project.id, data: values });
    } else {
      await createProject.mutateAsync(values);
    }
    onOpenChange(false);
  };

  const isPending = createProject.isPending || updateProject.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>{isEditing ? '编辑项目' : '新建项目'}</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>项目名称 *</FormLabel>
                  <FormControl>
                    <Input placeholder="输入项目名称" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="owner_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>负责人 *</FormLabel>
                  <Select
                    value={field.value?.toString()}
                    onValueChange={(v) => field.onChange(Number(v))}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="选择负责人" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {owners?.map(owner => (
                        <SelectItem key={owner.id} value={owner.id.toString()}>
                          {owner.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>描述</FormLabel>
                  <FormControl>
                    <Textarea placeholder="输入项目描述" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex justify-end gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                取消
              </Button>
              <Button type="submit" disabled={isPending}>
                {isPending ? '保存中...' : isEditing ? '保存' : '创建'}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
```

#### 提交前自检

□ 第一行是 'use client'
□ 使用 react-hook-form + zod
□ 使用 Dialog 组件
□ 使用 toast 通知
□ 表单验证完整

#### 验收标准

- [ ] 使用 react-hook-form + zod
- [ ] 必填字段验证正确
- [ ] 新建/编辑模式切换正确
- [ ] toast 通知完整
- [ ] `npm run build` 无错误

---

### TASK-FE-PROJ-005: 项目详情页

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | projects |
| 任务 ID | TASK-FE-PROJ-005 |
| 技术栈 | Next.js App Router + TanStack Query |
| 优先级 | P0 |
| 预估工时 | 5h |

**前置条件**: TASK-FE-PROJ-001 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §5.1 (页面清单)
- API_SOT.md v9.7 (GET /api/v1/projects/:id)

#### 任务

实现项目详情页：
1. 显示项目基础信息
2. 显示项目统计数据
3. 显示关联账户列表
4. 显示项目成员列表
5. 支持编辑和状态操作

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/app/(dashboard)/projects/[id]/page.tsx` | 页面入口 | 15-20 |
| `src/features/projects/components/ProjectDetailPage.tsx` | 详情页组件 | 150-200 |
| `src/features/projects/components/ProjectInfo.tsx` | 基础信息卡片 | 60-80 |
| `src/features/projects/components/ProjectStats.tsx` | 统计数据卡片 | 60-80 |
| `src/features/projects/components/ProjectAccounts.tsx` | 关联账户列表 | 80-100 |
| `src/features/projects/hooks/useProject.ts` | 单条数据 Hook | 20-30 |

#### 思考要点（必须先分析）

1. **路由参数**: 如何获取项目 ID？
2. **数据获取**: 详情页是否需要额外 API？
3. **权限控制**: 谁可以查看详情？谁可以编辑？
4. **关联数据**: 账户和成员是嵌套返回还是单独请求？

#### 约束规则

1. 使用 Next.js App Router 动态路由
2. 使用 TanStack Query 获取数据
3. 使用 Card 组件布局
4. 统计数据格式化安全

#### 代码参考

**文件: src/app/(dashboard)/projects/[id]/page.tsx**
```typescript
import { ProjectDetailPage } from '@/features/projects/components/ProjectDetailPage';

interface PageProps {
  params: { id: string };
}

export default function Page({ params }: PageProps) {
  return <ProjectDetailPage projectId={Number(params.id)} />;
}
```

**文件: src/features/projects/hooks/useProject.ts**
```typescript
import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/lib/api';
import type { Project } from '../types';

export function useProject(id: number) {
  return useQuery({
    queryKey: ['project', id],
    queryFn: () => apiGet<Project>(`/api/v1/projects/${id}`),
    enabled: id > 0,
  });
}
```

**文件: src/features/projects/components/ProjectDetailPage.tsx**
```typescript
'use client';

/**
 * 项目详情页
 * SoT: FRONTEND_PAGE_DESIGN_v2.1.md §5.1
 */
import { useState } from 'react';
import { ArrowLeft, Edit } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { StatusBadge } from '@/components/ui/status-badge';
import { usePermission } from '@/hooks/usePermission';
import { useProject } from '../hooks/useProject';
import { ProjectInfo } from './ProjectInfo';
import { ProjectStats } from './ProjectStats';
import { ProjectAccounts } from './ProjectAccounts';
import { ProjectMembers } from './ProjectMembers';
import { ProjectStatusActions } from './ProjectStatusActions';
import { ProjectForm } from './ProjectForm';

interface ProjectDetailPageProps {
  projectId: number;
}

export function ProjectDetailPage({ projectId }: ProjectDetailPageProps) {
  const router = useRouter();
  const { can } = usePermission();
  const { data: project, isLoading, error } = useProject(projectId);
  const [isEditing, setIsEditing] = useState(false);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Skeleton className="h-[200px]" />
          <Skeleton className="h-[200px]" />
        </div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="p-4 border border-red-200 bg-red-50 rounded-lg">
        <p className="text-red-600">
          加载失败: {error?.message ?? '项目不存在'}
        </p>
        <Button variant="link" onClick={() => router.back()}>
          返回列表
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 标题栏 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <h1 className="text-2xl font-bold">{project.name}</h1>
          <StatusBadge type="project" value={project.status} />
        </div>
        <div className="flex gap-2">
          {can('project:update') && (
            <Button variant="outline" onClick={() => setIsEditing(true)}>
              <Edit className="h-4 w-4 mr-2" />
              编辑
            </Button>
          )}
          <ProjectStatusActions project={project} />
        </div>
      </div>

      {/* 基础信息 & 统计 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ProjectInfo project={project} />
        <ProjectStats project={project} />
      </div>

      {/* 关联账户 */}
      <ProjectAccounts projectId={projectId} />

      {/* 项目成员 */}
      <ProjectMembers projectId={projectId} />

      {/* 编辑弹窗 */}
      <ProjectForm
        open={isEditing}
        onOpenChange={setIsEditing}
        project={project}
      />
    </div>
  );
}
```

**文件: src/features/projects/components/ProjectInfo.tsx**
```typescript
'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatDate } from '@/lib/utils';
import type { Project } from '../types';

interface ProjectInfoProps {
  project: Project;
}

export function ProjectInfo({ project }: ProjectInfoProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>基础信息</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex justify-between">
          <span className="text-muted-foreground">项目代码</span>
          <span>{project.code}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">负责人</span>
          <span>{project.owner_name}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">计费模式</span>
          <span>{project.billing_mode === 'per_lead' ? '按线索' : '按消耗'}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">创建时间</span>
          <span>{formatDate(project.created_at)}</span>
        </div>
        {project.description && (
          <div>
            <span className="text-muted-foreground">描述</span>
            <p className="mt-1">{project.description}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
```

#### 提交前自检

□ 第一行是 'use client'（除页面入口外）
□ 使用 TanStack Query
□ 使用 Card 组件
□ 使用 StatusBadge
□ 有加载/错误状态

#### 验收标准

- [ ] 显示项目完整信息
- [ ] 显示统计数据
- [ ] 显示关联账户
- [ ] 显示项目成员
- [ ] 编辑/状态操作正确
- [ ] `npm run build` 无错误

---

### TASK-FE-PROJ-006: 项目成员管理

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | projects |
| 任务 ID | TASK-FE-PROJ-006 |
| 技术栈 | TanStack Query + Dialog |
| 优先级 | P0 |
| 预估工时 | 4h |

**前置条件**: TASK-FE-PROJ-005 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (权限矩阵)
- MASTER.md v4.9 §2.4 (管理项目成员权限)
- API_SOT.md v9.7 (项目成员 API)

#### 任务

实现项目成员管理：
1. 成员列表显示
2. 添加成员弹窗
3. 移除成员确认
4. 权限控制

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/projects/components/ProjectMembers.tsx` | 成员列表 | 100-140 |
| `src/features/projects/components/ProjectMemberAdd.tsx` | 添加弹窗 | 80-120 |
| `src/features/projects/components/ProjectMemberRow.tsx` | 成员行 | 40-60 |
| `src/features/projects/hooks/useProjectMembers.ts` | 成员 Hook | 60-80 |

#### 思考要点（必须先分析）

1. **权限控制**: 谁可以管理成员？ceo, project_owner, admin
2. **成员角色**: 可添加哪些角色的用户？主要是投手
3. **特殊限制**: 不能移除项目负责人
4. **数据获取**: 可添加用户列表如何获取？

#### 约束规则

1. 仅 ceo, project_owner, admin 可管理成员
2. 不能移除项目负责人
3. 主要添加投手角色用户
4. 使用 AlertDialog 确认移除

#### 代码参考

**文件: src/features/projects/hooks/useProjectMembers.ts**
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { apiGet, apiPost, apiDelete } from '@/lib/api';

interface Member {
  id: number;
  user_id: number;
  user_name: string;
  role: string;
  joined_at: string;
}

export function useProjectMembers(projectId: number) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ['project-members', projectId],
    queryFn: () => apiGet<Member[]>(`/api/v1/projects/${projectId}/members`),
    enabled: projectId > 0,
  });

  const addMember = useMutation({
    mutationFn: (userId: number) =>
      apiPost(`/api/v1/projects/${projectId}/members`, { user_id: userId }),
    onSuccess: () => {
      toast.success('成员添加成功');
      queryClient.invalidateQueries({ queryKey: ['project-members', projectId] });
    },
    onError: (error: Error) => {
      toast.error(`添加失败: ${error.message}`);
    },
  });

  const removeMember = useMutation({
    mutationFn: (memberId: number) =>
      apiDelete(`/api/v1/projects/${projectId}/members/${memberId}`),
    onSuccess: () => {
      toast.success('成员已移除');
      queryClient.invalidateQueries({ queryKey: ['project-members', projectId] });
    },
    onError: (error: Error) => {
      toast.error(`移除失败: ${error.message}`);
    },
  });

  return {
    ...query,
    addMember,
    removeMember,
  };
}
```

**文件: src/features/projects/components/ProjectMembers.tsx**
```typescript
'use client';

/**
 * 项目成员管理
 * SoT: MASTER.md v4.9 §2.4
 */
import { useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { usePermission } from '@/hooks/usePermission';
import { useProjectMembers } from '../hooks/useProjectMembers';
import { useProject } from '../hooks/useProject';
import { ProjectMemberAdd } from './ProjectMemberAdd';

interface ProjectMembersProps {
  projectId: number;
}

export function ProjectMembers({ projectId }: ProjectMembersProps) {
  const { can } = usePermission();
  const { data: project } = useProject(projectId);
  const { data: members, isLoading, removeMember } = useProjectMembers(projectId);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [memberToRemove, setMemberToRemove] = useState<number | null>(null);

  const canManage = can('project:manage_members');

  const handleRemove = async () => {
    if (memberToRemove) {
      await removeMember.mutateAsync(memberToRemove);
      setMemberToRemove(null);
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>项目成员</CardTitle>
        {canManage && (
          <Button size="sm" onClick={() => setIsAddOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            添加成员
          </Button>
        )}
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-12 bg-muted animate-pulse rounded" />
            ))}
          </div>
        ) : members?.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            暂无成员
          </div>
        ) : (
          <div className="divide-y">
            {members?.map(member => {
              const isOwner = member.user_id === project?.owner_id;
              return (
                <div key={member.id} className="flex items-center justify-between py-3">
                  <div>
                    <span className="font-medium">{member.user_name}</span>
                    {isOwner && (
                      <span className="ml-2 text-xs bg-primary/10 text-primary px-2 py-0.5 rounded">
                        负责人
                      </span>
                    )}
                    <span className="text-sm text-muted-foreground ml-2">
                      {member.role}
                    </span>
                  </div>
                  {canManage && !isOwner && (
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => setMemberToRemove(member.id)}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </CardContent>

      {/* 添加成员弹窗 */}
      <ProjectMemberAdd
        open={isAddOpen}
        onOpenChange={setIsAddOpen}
        projectId={projectId}
        existingMemberIds={members?.map(m => m.user_id) ?? []}
      />

      {/* 移除确认弹窗 */}
      <AlertDialog open={memberToRemove !== null} onOpenChange={() => setMemberToRemove(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认移除成员</AlertDialogTitle>
            <AlertDialogDescription>
              确定要移除该成员吗？此操作不可撤销。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={handleRemove}>
              确认移除
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Card>
  );
}
```

#### 提交前自检

□ 第一行是 'use client'
□ 权限检查正确
□ 不能移除负责人
□ 使用 AlertDialog 确认
□ toast 通知完整

#### 验收标准

- [ ] 仅授权角色可管理
- [ ] 不能移除项目负责人
- [ ] 添加/移除操作正确
- [ ] toast 通知完整
- [ ] `npm run build` 无错误

---

### TASK-FE-PROJ-007: 项目状态流转

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | projects |
| 任务 ID | TASK-FE-PROJ-007 |
| 技术栈 | State Machine + AlertDialog |
| 优先级 | P0 |
| 预估工时 | 3h |

**前置条件**: TASK-FE-PROJ-003 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §3.4 (项目状态机)
- STATE_MACHINE.md v2.9 §7.3 (项目状态机)

#### 任务

实现项目状态流转 UI：
1. draft → active：激活项目
2. active → suspended：暂停项目
3. suspended → active：恢复项目
4. active → archived：归档项目（需警告）
5. suspended → archived：归档项目
6. 状态变更需确认弹窗

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/projects/components/ProjectStatusActions.tsx` | 状态操作按钮 | 80-120 |
| `src/features/projects/components/ProjectStatusDialog.tsx` | 确认弹窗 | 60-80 |
| `src/features/projects/lib/status-transitions.ts` | 状态转换逻辑 | 40-60 |

#### 思考要点（必须先分析）

1. **状态机**: 4 个状态的转换规则是什么？
2. **权限控制**: 谁可以操作状态？project_owner, admin
3. **危险操作**: 归档需要特别警告
4. **按钮显示**: 根据当前状态显示可用操作

#### 约束规则

1. 状态转换必须符合 STATE_MACHINE.md
2. 仅 project_owner, admin 可操作
3. 归档操作需要警告弹窗
4. 使用 AlertDialog 确认

#### 代码参考

**文件: src/features/projects/lib/status-transitions.ts**
```typescript
/**
 * 项目状态转换规则
 * SoT: STATE_MACHINE.md v2.9 §7.3
 */
import type { ProjectStatus } from '../types';

interface StatusTransition {
  from: ProjectStatus;
  to: ProjectStatus;
  action: string;
  label: string;
  variant?: 'default' | 'destructive' | 'warning';
  requireConfirm?: boolean;
  confirmMessage?: string;
}

export const PROJECT_STATUS_TRANSITIONS: StatusTransition[] = [
  {
    from: 'draft',
    to: 'active',
    action: 'activate',
    label: '激活',
    variant: 'default',
    requireConfirm: true,
    confirmMessage: '确定要激活该项目吗？',
  },
  {
    from: 'active',
    to: 'suspended',
    action: 'suspend',
    label: '暂停',
    variant: 'warning',
    requireConfirm: true,
    confirmMessage: '确定要暂停该项目吗？暂停后项目下的账户将无法正常投放。',
  },
  {
    from: 'suspended',
    to: 'active',
    action: 'resume',
    label: '恢复',
    variant: 'default',
    requireConfirm: true,
    confirmMessage: '确定要恢复该项目吗？',
  },
  {
    from: 'active',
    to: 'archived',
    action: 'archive',
    label: '归档',
    variant: 'destructive',
    requireConfirm: true,
    confirmMessage: '⚠️ 警告：归档后项目将无法恢复，且所有关联账户将被解绑。确定要继续吗？',
  },
  {
    from: 'suspended',
    to: 'archived',
    action: 'archive',
    label: '归档',
    variant: 'destructive',
    requireConfirm: true,
    confirmMessage: '确定要归档该项目吗？归档后将无法恢复。',
  },
];

export function getAvailableTransitions(currentStatus: ProjectStatus): StatusTransition[] {
  return PROJECT_STATUS_TRANSITIONS.filter(t => t.from === currentStatus);
}
```

**文件: src/features/projects/components/ProjectStatusActions.tsx**
```typescript
'use client';

/**
 * 项目状态操作按钮
 * SoT: STATE_MACHINE.md v2.9 §7.3
 */
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { apiPost } from '@/lib/api';
import { usePermission } from '@/hooks/usePermission';
import { getAvailableTransitions } from '../lib/status-transitions';
import type { Project } from '../types';

interface ProjectStatusActionsProps {
  project: Project;
}

export function ProjectStatusActions({ project }: ProjectStatusActionsProps) {
  const { can } = usePermission();
  const queryClient = useQueryClient();
  const [pendingAction, setPendingAction] = useState<{
    action: string;
    label: string;
    message: string;
  } | null>(null);

  const transitions = getAvailableTransitions(project.status);

  const mutation = useMutation({
    mutationFn: (action: string) =>
      apiPost(`/api/v1/projects/${project.id}/status`, { action }),
    onSuccess: () => {
      toast.success('状态更新成功');
      queryClient.invalidateQueries({ queryKey: ['project', project.id] });
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setPendingAction(null);
    },
    onError: (error: Error) => {
      toast.error(`操作失败: ${error.message}`);
    },
  });

  // 仅 project_owner, admin 可操作
  if (!can('project:update_status')) {
    return null;
  }

  if (transitions.length === 0) {
    return null;
  }

  const handleClick = (transition: typeof transitions[0]) => {
    if (transition.requireConfirm) {
      setPendingAction({
        action: transition.action,
        label: transition.label,
        message: transition.confirmMessage ?? `确定要${transition.label}该项目吗？`,
      });
    } else {
      mutation.mutate(transition.action);
    }
  };

  return (
    <>
      {transitions.map(transition => (
        <Button
          key={transition.action}
          variant={transition.variant === 'destructive' ? 'destructive' : 'outline'}
          size="sm"
          onClick={() => handleClick(transition)}
          disabled={mutation.isPending}
        >
          {transition.label}
        </Button>
      ))}

      <AlertDialog open={!!pendingAction} onOpenChange={() => setPendingAction(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认{pendingAction?.label}</AlertDialogTitle>
            <AlertDialogDescription>
              {pendingAction?.message}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={mutation.isPending}>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => pendingAction && mutation.mutate(pendingAction.action)}
              disabled={mutation.isPending}
            >
              {mutation.isPending ? '处理中...' : '确认'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
```

#### 提交前自检

□ 第一行是 'use client'
□ 状态转换符合状态机
□ 权限检查正确
□ 使用 AlertDialog 确认
□ 归档有警告提示

#### 验收标准

- [ ] 状态转换符合 STATE_MACHINE.md
- [ ] 仅授权角色可操作
- [ ] 确认弹窗正确显示
- [ ] 归档操作有警告
- [ ] `npm run build` 无错误

---

## 4.5 ACCT 账户模块

### TASK-FE-ACCT-001: 账户列表页

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | ad-accounts |
| 任务 ID | TASK-FE-ACCT-001 |
| 技术栈 | Next.js App Router + TanStack Query |
| 优先级 | P0 |
| 预估工时 | 5h |

**前置条件**: TASK-FE-COMMON-005 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §5.1 (页面清单)
- API_SOT.md v9.7 (GET /api/v1/ad-accounts)
- STATE_MACHINE.md v2.9 (账户状态机)

#### 任务

实现广告账户列表页：
1. 数据列表（DataTable）
2. 状态筛选（6 个状态）
3. 渠道筛选
4. 分页和排序
5. 按角色过滤数据

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/app/(dashboard)/ad-accounts/page.tsx` | 页面入口 | 10-15 |
| `src/features/ad-accounts/components/AdAccountsPage.tsx` | 页面组件 | 120-160 |
| `src/features/ad-accounts/components/AdAccountsTable.tsx` | 表格组件 | 80-100 |
| `src/features/ad-accounts/hooks/useAdAccounts.ts` | 列表 Hook | 30-40 |
| `src/features/ad-accounts/services/adAccountsApi.ts` | API 服务 | 50-70 |
| `src/features/ad-accounts/types/adAccount.types.ts` | 类型定义 | 50-70 |

#### 思考要点（必须先分析）

1. **账户状态**: 6 个状态的完整列表是什么？每个状态什么含义？
2. **权限分布**: 投手只能看分配给自己的，户管能看全部 — 如何区分？
3. **创建权限**: 哪些角色可以创建账户？
4. **状态切换**: 哪些角色可以切换账户状态？
5. **渠道关联**: 账户和渠道的关系是什么？

#### 约束规则

1. 使用 DataTable 组件
2. 使用 StatusBadge 显示状态
3. 状态筛选包含 6 个状态 + "全部"
4. 创建账户仅 account_manager, admin 可操作
5. 状态切换仅 account_manager, admin 可操作

#### 代码参考

**文件: src/features/ad-accounts/types/adAccount.types.ts**
```typescript
/**
 * 广告账户类型定义
 * SoT: STATE_MACHINE.md v2.9
 */

// 账户状态 - 6 个
export type AdAccountStatus =
  | 'new'        // 新建
  | 'testing'    // 测试中
  | 'active'     // 活跃
  | 'suspended'  // 暂停
  | 'dead'       // 死亡
  | 'archived';  // 归档

export const AD_ACCOUNT_STATUS_OPTIONS = [
  { value: '__all__', label: '全部' },
  { value: 'new', label: '新建' },
  { value: 'testing', label: '测试中' },
  { value: 'active', label: '活跃' },
  { value: 'suspended', label: '暂停' },
  { value: 'dead', label: '死亡' },
  { value: 'archived', label: '归档' },
] as const;

export interface AdAccount {
  id: number;
  name: string;
  account_id: string;      // 平台账户 ID
  channel_id: number;
  channel_name: string;
  project_id: number | null;
  project_name: string | null;
  assigned_user_id: number | null;
  assigned_user_name: string | null;
  status: AdAccountStatus;
  balance: number;
  daily_budget: number;
  created_at: string;
  updated_at: string;
}

export interface AdAccountListParams {
  status?: AdAccountStatus | '__all__';
  channel_id?: number;
  project_id?: number;
  assigned_user_id?: number;
  page?: number;
  page_size?: number;
  sort_by?: 'name' | 'balance' | 'created_at';
  sort_order?: 'asc' | 'desc';
}
```

**文件: src/features/ad-accounts/services/adAccountsApi.ts**
```typescript
/**
 * 广告账户 API 服务
 * SoT: API_SOT.md v9.7
 */
import { apiGet, apiPost, apiPatch, type PaginatedResponse } from '@/lib/api';
import type { AdAccount, AdAccountListParams } from '../types';

const BASE_PATH = '/api/v1/ad-accounts';

export async function getAdAccounts(
  params: AdAccountListParams = {}
): Promise<PaginatedResponse<AdAccount>> {
  const searchParams = new URLSearchParams();

  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));
  if (params.status && params.status !== '__all__') {
    searchParams.set('status', params.status);
  }
  if (params.channel_id) searchParams.set('channel_id', String(params.channel_id));
  if (params.project_id) searchParams.set('project_id', String(params.project_id));
  if (params.sort_by) searchParams.set('sort_by', params.sort_by);
  if (params.sort_order) searchParams.set('sort_order', params.sort_order);

  const query = searchParams.toString();
  return apiGet<PaginatedResponse<AdAccount>>(
    query ? `${BASE_PATH}?${query}` : BASE_PATH
  );
}

export async function createAdAccount(data: Partial<AdAccount>): Promise<AdAccount> {
  return apiPost<AdAccount>(BASE_PATH, data);
}

export async function updateAdAccountStatus(
  id: number,
  status: AdAccountStatus
): Promise<AdAccount> {
  return apiPatch<AdAccount>(`${BASE_PATH}/${id}/status`, { status });
}

export async function assignAdAccount(
  id: number,
  userId: number
): Promise<AdAccount> {
  return apiPatch<AdAccount>(`${BASE_PATH}/${id}/assign`, { user_id: userId });
}
```

**文件: src/features/ad-accounts/components/AdAccountsPage.tsx**
```typescript
'use client';

/**
 * 广告账户列表页
 * SoT: FRONTEND_PAGE_DESIGN_v2.1.md
 */
import { useState } from 'react';
import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { usePermission } from '@/hooks/usePermission';
import { useAdAccounts } from '../hooks/useAdAccounts';
import { AdAccountsFilters } from './AdAccountsFilters';
import { AdAccountsTable } from './AdAccountsTable';
import { AdAccountForm } from './AdAccountForm';
import type { AdAccountListParams } from '../types';

export function AdAccountsPage() {
  const { can, isLoading: permLoading } = usePermission();
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [params, setParams] = useState<AdAccountListParams>({
    page: 1,
    page_size: 20,
    status: '__all__',
    sort_by: 'created_at',
    sort_order: 'desc',
  });

  const { data, isLoading, error } = useAdAccounts(params);

  if (permLoading) {
    return <Skeleton className="h-[400px] w-full" />;
  }

  if (!can('ad_account:view')) {
    return (
      <div className="p-4 border border-yellow-200 bg-yellow-50 rounded-lg">
        <p className="text-yellow-600">您没有访问此页面的权限</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 border border-red-200 bg-red-50 rounded-lg">
        <p className="text-red-600">加载失败: {error.message}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 标题栏 */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">广告账户</h1>
        {can('ad_account:create') && (
          <Button onClick={() => setIsFormOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            创建账户
          </Button>
        )}
      </div>

      {/* 筛选器 */}
      <AdAccountsFilters
        value={params}
        onChange={(newParams) => setParams({ ...params, ...newParams, page: 1 })}
      />

      {/* 数据表格 */}
      <AdAccountsTable
        data={data?.items ?? []}
        loading={isLoading}
        pagination={{
          page: params.page ?? 1,
          pageSize: params.page_size ?? 20,
          total: data?.total ?? 0,
          onPageChange: (page) => setParams({ ...params, page }),
        }}
      />

      {/* 创建表单弹窗 */}
      <AdAccountForm
        open={isFormOpen}
        onOpenChange={setIsFormOpen}
      />
    </div>
  );
}

export default AdAccountsPage;
```

#### 提交前自检

□ 第一行是 'use client'
□ 使用 apiGet 而非 fetch
□ 使用 DataTable 而非 table
□ 使用 StatusBadge 显示状态
□ 状态筛选 6 个 + 全部
□ 权限检查使用 can()
□ 有加载/错误/空状态处理
□ 金额格式化安全

#### 验收标准

- [ ] 使用 DataTable 组件
- [ ] 使用 TanStack Query
- [ ] 状态筛选包含 6 个状态
- [ ] 权限检查正确
- [ ] 有加载/错误/空状态处理
- [ ] `npm run build` 无错误

---

### TASK-FE-ACCT-002: 账户状态看板

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | ad-accounts |
| 任务 ID | TASK-FE-ACCT-002 |
| 技术栈 | Card + StatusBadge |
| 优先级 | P0 |
| 预估工时 | 2h |

**前置条件**: TASK-FE-ACCT-001, TASK-FE-COMMON-003 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §6.3.1 (账户状态看板)
- STATE_MACHINE.md v2.9 §7.1 (账户状态机)

#### 任务

实现账户状态看板：
1. 显示 6 个状态分组
2. 每个状态显示账户数量
3. 点击状态卡片筛选列表
4. 使用对应状态颜色

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/ad-accounts/components/AccountStatusBoard.tsx` | 状态看板 | 80-100 |
| `src/features/ad-accounts/components/StatusCard.tsx` | 状态卡片 | 40-60 |

#### 思考要点（必须先分析）

1. **数据来源**: 状态统计从哪里获取？单独 API 还是列表聚合？
2. **颜色映射**: 6 个状态的颜色是什么？
3. **点击交互**: 点击卡片如何更新筛选器？
4. **选中状态**: 如何显示当前选中的状态？

#### 约束规则

1. 账户状态 6 个: new, testing, active, suspended, dead, archived
2. 使用 StatusBadge 颜色配置
3. 点击切换筛选条件
4. 选中状态高亮显示

#### 代码参考

**文件: src/features/ad-accounts/components/AccountStatusBoard.tsx**
```typescript
'use client';

/**
 * 账户状态看板
 * SoT: FRONTEND_PAGE_DESIGN_v2.1.md §6.3.1
 */
import { cn } from '@/lib/utils';
import { ACCOUNT_STATUS_CONFIG } from '@/lib/constants/status-config';
import type { AccountStatus } from '../types';

interface StatusCount {
  status: AccountStatus;
  count: number;
}

interface AccountStatusBoardProps {
  statusCounts: StatusCount[];
  selectedStatus?: AccountStatus | '__all__';
  onStatusChange: (status: AccountStatus | '__all__') => void;
}

const STATUS_ORDER: AccountStatus[] = ['new', 'testing', 'active', 'suspended', 'dead', 'archived'];

export function AccountStatusBoard({
  statusCounts,
  selectedStatus,
  onStatusChange,
}: AccountStatusBoardProps) {
  const total = statusCounts.reduce((sum, item) => sum + item.count, 0);

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
      {/* 全部 */}
      <button
        onClick={() => onStatusChange('__all__')}
        className={cn(
          'p-4 rounded-lg border text-left transition-colors',
          selectedStatus === '__all__' || !selectedStatus
            ? 'border-primary bg-primary/5'
            : 'hover:bg-muted'
        )}
      >
        <div className="text-2xl font-bold">{total}</div>
        <div className="text-sm text-muted-foreground">全部账户</div>
      </button>

      {/* 各状态 */}
      {STATUS_ORDER.map(status => {
        const config = ACCOUNT_STATUS_CONFIG[status];
        const item = statusCounts.find(s => s.status === status);
        const count = item?.count ?? 0;
        const isSelected = selectedStatus === status;

        return (
          <button
            key={status}
            onClick={() => onStatusChange(status)}
            className={cn(
              'p-4 rounded-lg border text-left transition-colors',
              isSelected ? 'border-primary bg-primary/5' : 'hover:bg-muted'
            )}
          >
            <div className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: config.color }}
              />
              <span className="text-2xl font-bold">{count}</span>
            </div>
            <div className="text-sm text-muted-foreground">{config.label}</div>
          </button>
        );
      })}
    </div>
  );
}
```

#### 提交前自检

□ 第一行是 'use client'
□ 6 个状态全部显示
□ 使用状态配置颜色
□ 点击切换筛选
□ 选中状态高亮

#### 验收标准

- [ ] 显示 6 个状态 + 全部
- [ ] 颜色与 SoT 一致
- [ ] 点击交互正确
- [ ] `npm run build` 无错误

---

### TASK-FE-ACCT-003: 账户筛选器

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | ad-accounts |
| 任务 ID | TASK-FE-ACCT-003 |
| 技术栈 | Select + URL State |
| 优先级 | P0 |
| 预估工时 | 3h |

**前置条件**: TASK-FE-ACCT-001 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §6.3 (账户管理)
- STATE_MACHINE.md v2.9 §7.1 (账户状态机)

#### 任务

实现账户筛选器：
1. 状态筛选（6 个状态 + 全部）
2. 渠道筛选
3. 项目筛选
4. 投手筛选（户管可用）
5. 筛选条件同步到 URL

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/ad-accounts/components/AdAccountsFilters.tsx` | 筛选器 | 120-160 |

#### 思考要点（必须先分析）

1. **权限控制**: 投手筛选仅户管/Admin 可见？
2. **数据来源**: 渠道/项目/投手列表从哪里获取？
3. **联动关系**: 选择项目后是否筛选投手列表？
4. **状态机**: 6 个账户状态是什么？

#### 约束规则

1. 账户状态 6 个: new, testing, active, suspended, dead, archived
2. 使用 Select 组件（禁止原生 select）
3. 筛选变化时 page 重置为 1
4. URL 同步使用 searchParams

#### 代码参考

**文件: src/features/ad-accounts/components/AdAccountsFilters.tsx**
```typescript
'use client';

/**
 * 账户筛选器
 * SoT: FRONTEND_PAGE_DESIGN_v2.1.md §6.3
 */
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { usePermission } from '@/hooks/usePermission';
import { useChannels } from '@/features/channels/hooks/useChannels';
import { useProjects } from '@/features/projects/hooks/useProjects';
import { usePitchers } from '@/features/users/hooks/usePitchers';
import { ACCOUNT_STATUS_OPTIONS } from '../types';
import type { AdAccountListParams } from '../types';

interface AdAccountsFiltersProps {
  value: AdAccountListParams;
  onChange: (params: Partial<AdAccountListParams>) => void;
}

export function AdAccountsFilters({ value, onChange }: AdAccountsFiltersProps) {
  const { can } = usePermission();
  const { data: channels } = useChannels();
  const { data: projects } = useProjects({ status: 'active' });
  const { data: pitchers } = usePitchers();

  // 户管/Admin 可见投手筛选
  const showPitcherFilter = can('account:view_all');

  return (
    <div className="flex gap-4 flex-wrap">
      {/* 状态筛选 */}
      <Select
        value={value.status ?? '__all__'}
        onValueChange={(status) => onChange({ status: status as AdAccountListParams['status'] })}
      >
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="状态" />
        </SelectTrigger>
        <SelectContent>
          {ACCOUNT_STATUS_OPTIONS.map(opt => (
            <SelectItem key={opt.value} value={opt.value}>
              {opt.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* 渠道筛选 */}
      <Select
        value={value.channel_id?.toString() ?? '__all__'}
        onValueChange={(id) => onChange({ channel_id: id === '__all__' ? undefined : Number(id) })}
      >
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="渠道" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">全部渠道</SelectItem>
          {channels?.map(channel => (
            <SelectItem key={channel.id} value={channel.id.toString()}>
              {channel.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* 项目筛选 */}
      <Select
        value={value.project_id?.toString() ?? '__all__'}
        onValueChange={(id) => onChange({ project_id: id === '__all__' ? undefined : Number(id) })}
      >
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="项目" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">全部项目</SelectItem>
          {projects?.items?.map(project => (
            <SelectItem key={project.id} value={project.id.toString()}>
              {project.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* 投手筛选 - 户管/Admin 可见 */}
      {showPitcherFilter && (
        <Select
          value={value.pitcher_id?.toString() ?? '__all__'}
          onValueChange={(id) => onChange({ pitcher_id: id === '__all__' ? undefined : Number(id) })}
        >
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="投手" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">全部投手</SelectItem>
            {pitchers?.map(pitcher => (
              <SelectItem key={pitcher.id} value={pitcher.id.toString()}>
                {pitcher.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}
    </div>
  );
}
```

#### 提交前自检

□ 第一行是 'use client'
□ 6 个状态 + 全部
□ 渠道/项目/投手筛选
□ 权限控制正确
□ value/onChange 模式

#### 验收标准

- [ ] 状态筛选 6 个 + 全部
- [ ] 渠道/项目/投手筛选
- [ ] 投手筛选权限控制
- [ ] 筛选条件同步 URL
- [ ] `npm run build` 无错误

---

### TASK-FE-ACCT-004: 账户表格组件

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | ad-accounts |
| 任务 ID | TASK-FE-ACCT-004 |
| 技术栈 | DataTable + StatusBadge |
| 优先级 | P0 |
| 预估工时 | 3h |

**前置条件**: TASK-FE-ACCT-001 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §7.1 (必须使用的组件)
- STATE_MACHINE.md v2.9 §7.1 (账户状态机)

#### 任务

实现账户表格：
1. 使用 DataTable 组件
2. 显示字段：账户ID、渠道、项目、投手、余额、状态
3. 状态列使用 StatusBadge
4. 支持行操作按钮

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/ad-accounts/components/AdAccountsTable.tsx` | 表格组件 | 140-180 |
| `src/features/ad-accounts/components/AdAccountRow.tsx` | 行组件（可选） | 40-60 |

#### 思考要点（必须先分析）

1. **列定义**: DataTable 的 columns 如何定义？
2. **状态显示**: StatusBadge type="account"？
3. **余额格式**: 金额如何安全格式化？
4. **行操作**: 哪些操作需要显示？

#### 约束规则

1. 使用 DataTable 组件（禁止原生 table）
2. 使用 StatusBadge type="account"
3. 金额使用 safeNumber 格式化
4. 操作按钮根据权限显示

#### 代码参考

**文件: src/features/ad-accounts/components/AdAccountsTable.tsx**
```typescript
'use client';

/**
 * 账户表格
 * SoT: FRONTEND_PAGE_DESIGN_v2.1.md §7.1
 */
import { ColumnDef } from '@tanstack/react-table';
import { Eye, Edit, Settings, MoreHorizontal } from 'lucide-react';
import { DataTable } from '@/components/ui/data-table';
import { StatusBadge } from '@/components/ui/status-badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { usePermission } from '@/hooks/usePermission';
import { formatCurrency } from '@/lib/utils';
import type { AdAccount } from '../types';

interface AdAccountsTableProps {
  data: AdAccount[];
  loading?: boolean;
  pagination?: {
    page: number;
    pageSize: number;
    total: number;
    onPageChange: (page: number) => void;
  };
  onView?: (account: AdAccount) => void;
  onEdit?: (account: AdAccount) => void;
  onAssign?: (account: AdAccount) => void;
  onStatusChange?: (account: AdAccount) => void;
}

export function AdAccountsTable({
  data,
  loading,
  pagination,
  onView,
  onEdit,
  onAssign,
  onStatusChange,
}: AdAccountsTableProps) {
  const { can } = usePermission();

  const columns: ColumnDef<AdAccount>[] = [
    {
      accessorKey: 'account_id',
      header: '账户ID',
      cell: ({ row }) => (
        <span className="font-mono text-sm">{row.getValue('account_id')}</span>
      ),
    },
    {
      accessorKey: 'channel_name',
      header: '渠道',
    },
    {
      accessorKey: 'project_name',
      header: '项目',
      cell: ({ row }) => row.original.project_name ?? '-',
    },
    {
      accessorKey: 'pitcher_name',
      header: '投手',
      cell: ({ row }) => row.original.pitcher_name ?? '-',
    },
    {
      accessorKey: 'balance',
      header: '余额',
      cell: ({ row }) => {
        const balance = row.original.balance;
        return formatCurrency(typeof balance === 'number' ? balance : 0);
      },
    },
    {
      accessorKey: 'status',
      header: '状态',
      cell: ({ row }) => (
        <StatusBadge
          type="account"
          value={row.getValue('status')}
        />
      ),
    },
    {
      id: 'actions',
      header: '操作',
      cell: ({ row }) => {
        const account = row.original;
        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onView?.(account)}>
                <Eye className="h-4 w-4 mr-2" />
                查看详情
              </DropdownMenuItem>
              {can('account:update') && (
                <DropdownMenuItem onClick={() => onEdit?.(account)}>
                  <Edit className="h-4 w-4 mr-2" />
                  编辑
                </DropdownMenuItem>
              )}
              {can('account:assign') && (
                <DropdownMenuItem onClick={() => onAssign?.(account)}>
                  <Settings className="h-4 w-4 mr-2" />
                  分配
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        );
      },
    },
  ];

  if (loading) {
    return (
      <div className="space-y-2">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-12 bg-muted animate-pulse rounded" />
        ))}
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        暂无账户数据
      </div>
    );
  }

  return (
    <DataTable
      columns={columns}
      data={data}
      pagination={pagination}
    />
  );
}
```

#### 提交前自检

□ 第一行是 'use client'
□ 使用 DataTable 组件
□ 使用 StatusBadge type="account"
□ 金额格式化安全
□ 操作权限检查

#### 验收标准

- [ ] 使用 DataTable 组件
- [ ] 使用 StatusBadge 显示状态
- [ ] 显示所有必需字段
- [ ] 金额格式化正确
- [ ] `npm run build` 无错误

---

### TASK-FE-ACCT-005: 账户创建/编辑表单

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | ad-accounts |
| 任务 ID | TASK-FE-ACCT-005 |
| 技术栈 | react-hook-form + zod + Dialog |
| 优先级 | P0 |
| 预估工时 | 4h |

**前置条件**: TASK-FE-ACCT-001, TASK-FE-CHAN-001 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §6.3.2 (账户操作权限)
- API_SOT.md v9.7 (POST/PUT /api/v1/ad-accounts)
- MASTER.md v4.9 §2.4 (角色权限)

#### 任务

实现账户创建/编辑表单：
1. 必填字段：账户ID、渠道
2. 选填字段：项目、投手、备注
3. 表单验证（zod）
4. 新建成功显示 toast

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/ad-accounts/components/AdAccountForm.tsx` | 表单组件 | 150-200 |
| `src/features/ad-accounts/components/AdAccountFormSchema.ts` | 验证 Schema | 30-50 |
| `src/features/ad-accounts/components/AdAccountFormDialog.tsx` | 弹窗包装 | 40-60 |
| `src/features/ad-accounts/hooks/useAdAccountMutations.ts` | 变更 Hook | 50-80 |

#### 思考要点（必须先分析）

1. **权限控制**: 仅 account_manager, admin 可创建
2. **渠道选择**: 渠道列表从哪里获取？
3. **初始状态**: 新建账户初始状态是什么？(new)
4. **编辑限制**: 渠道能否修改？

#### 约束规则

1. 仅 account_manager, admin 可创建账户
2. 使用 react-hook-form + zod 验证
3. 新建账户初始状态为 new
4. 使用 Dialog 组件

#### 代码参考

**文件: src/features/ad-accounts/components/AdAccountFormSchema.ts**
```typescript
import { z } from 'zod';

export const adAccountFormSchema = z.object({
  account_id: z.string()
    .min(1, '请输入账户ID')
    .max(100, '账户ID最多 100 个字符'),
  channel_id: z.number({
    required_error: '请选择渠道',
  }),
  project_id: z.number().optional(),
  pitcher_id: z.number().optional(),
  remark: z.string().max(500).optional(),
});

export type AdAccountFormValues = z.infer<typeof adAccountFormSchema>;
```

**文件: src/features/ad-accounts/hooks/useAdAccountMutations.ts**
```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { apiPost, apiPut } from '@/lib/api';
import type { AdAccountFormValues } from '../components/AdAccountFormSchema';

export function useAdAccountMutations() {
  const queryClient = useQueryClient();

  const createAccount = useMutation({
    mutationFn: (data: AdAccountFormValues) =>
      apiPost('/api/v1/ad-accounts', data),
    onSuccess: () => {
      toast.success('账户创建成功');
      queryClient.invalidateQueries({ queryKey: ['ad-accounts'] });
    },
    onError: (error: Error) => {
      toast.error(`创建失败: ${error.message}`);
    },
  });

  const updateAccount = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<AdAccountFormValues> }) =>
      apiPut(`/api/v1/ad-accounts/${id}`, data),
    onSuccess: () => {
      toast.success('账户更新成功');
      queryClient.invalidateQueries({ queryKey: ['ad-accounts'] });
    },
    onError: (error: Error) => {
      toast.error(`更新失败: ${error.message}`);
    },
  });

  return { createAccount, updateAccount };
}
```

**文件: src/features/ad-accounts/components/AdAccountForm.tsx**
```typescript
'use client';

/**
 * 账户表单
 * SoT: API_SOT.md v9.7 POST/PUT /api/v1/ad-accounts
 */
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { useChannels } from '@/features/channels/hooks/useChannels';
import { useProjects } from '@/features/projects/hooks/useProjects';
import { usePitchers } from '@/features/users/hooks/usePitchers';
import { useAdAccountMutations } from '../hooks/useAdAccountMutations';
import { adAccountFormSchema, type AdAccountFormValues } from './AdAccountFormSchema';
import type { AdAccount } from '../types';

interface AdAccountFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  account?: AdAccount; // 编辑模式
}

export function AdAccountForm({ open, onOpenChange, account }: AdAccountFormProps) {
  const { data: channels } = useChannels();
  const { data: projects } = useProjects({ status: 'active' });
  const { data: pitchers } = usePitchers();
  const { createAccount, updateAccount } = useAdAccountMutations();
  const isEditing = !!account;

  const form = useForm<AdAccountFormValues>({
    resolver: zodResolver(adAccountFormSchema),
    defaultValues: {
      account_id: '',
      channel_id: undefined,
      project_id: undefined,
      pitcher_id: undefined,
      remark: '',
    },
  });

  useEffect(() => {
    if (account) {
      form.reset({
        account_id: account.account_id,
        channel_id: account.channel_id,
        project_id: account.project_id ?? undefined,
        pitcher_id: account.pitcher_id ?? undefined,
        remark: account.remark ?? '',
      });
    } else {
      form.reset({
        account_id: '',
        channel_id: undefined,
        project_id: undefined,
        pitcher_id: undefined,
        remark: '',
      });
    }
  }, [account, form]);

  const onSubmit = async (values: AdAccountFormValues) => {
    if (isEditing && account) {
      await updateAccount.mutateAsync({ id: account.id, data: values });
    } else {
      await createAccount.mutateAsync(values);
    }
    onOpenChange(false);
  };

  const isPending = createAccount.isPending || updateAccount.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>{isEditing ? '编辑账户' : '新建账户'}</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="account_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>账户ID *</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="输入账户ID"
                      {...field}
                      disabled={isEditing}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="channel_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>渠道 *</FormLabel>
                  <Select
                    value={field.value?.toString()}
                    onValueChange={(v) => field.onChange(Number(v))}
                    disabled={isEditing}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="选择渠道" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {channels?.map(channel => (
                        <SelectItem key={channel.id} value={channel.id.toString()}>
                          {channel.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="project_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>项目</FormLabel>
                  <Select
                    value={field.value?.toString() ?? '__none__'}
                    onValueChange={(v) => field.onChange(v === '__none__' ? undefined : Number(v))}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="选择项目" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="__none__">暂不分配</SelectItem>
                      {projects?.items?.map(project => (
                        <SelectItem key={project.id} value={project.id.toString()}>
                          {project.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="pitcher_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>投手</FormLabel>
                  <Select
                    value={field.value?.toString() ?? '__none__'}
                    onValueChange={(v) => field.onChange(v === '__none__' ? undefined : Number(v))}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="选择投手" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="__none__">暂不分配</SelectItem>
                      {pitchers?.map(pitcher => (
                        <SelectItem key={pitcher.id} value={pitcher.id.toString()}>
                          {pitcher.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="remark"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>备注</FormLabel>
                  <FormControl>
                    <Textarea placeholder="输入备注" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex justify-end gap-3 pt-4">
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                取消
              </Button>
              <Button type="submit" disabled={isPending}>
                {isPending ? '保存中...' : isEditing ? '保存' : '创建'}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
```

#### 提交前自检

□ 第一行是 'use client'
□ 使用 react-hook-form + zod
□ 使用 Dialog 组件
□ 编辑模式禁用账户ID/渠道
□ toast 通知完整

#### 验收标准

- [ ] 使用 react-hook-form + zod
- [ ] 必填字段验证正确
- [ ] 编辑模式禁用关键字段
- [ ] toast 通知完整
- [ ] `npm run build` 无错误

---

### TASK-FE-ACCT-006: 账户分配操作

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | ad-accounts |
| 任务 ID | TASK-FE-ACCT-006 |
| 技术栈 | Dialog + Form |
| 优先级 | P0 |
| 预估工时 | 4h |

**前置条件**: TASK-FE-ACCT-004, TASK-FE-PROJ-001 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §6.3.2 (账户操作权限)
- FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (分配账户权限)
- API_SOT.md v9.7 (PUT /api/v1/ad-accounts/:id/assign)

#### 任务

实现账户分配操作：
1. 选择目标项目
2. 选择目标投手
3. 分配成功显示 toast
4. 分配后自动刷新列表

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/ad-accounts/components/AccountAssignDialog.tsx` | 分配弹窗 | 100-140 |
| `src/features/ad-accounts/components/AccountAssignForm.tsx` | 分配表单 | 80-100 |

#### 思考要点（必须先分析）

1. **权限控制**: 仅 account_manager, admin 可分配
2. **选择限制**: 投手只能选择项目成员？
3. **批量操作**: 是否支持批量分配？
4. **验证规则**: 分配时是否校验账户状态？

#### 约束规则

1. 仅 account_manager, admin 可分配账户
2. 使用 Dialog 组件
3. 分配成功后刷新列表
4. 使用 toast 通知结果

#### 代码参考

**文件: src/features/ad-accounts/components/AccountAssignDialog.tsx**
```typescript
'use client';

/**
 * 账户分配弹窗
 * SoT: FRONTEND_PAGE_DESIGN_v2.1.md §6.3.2
 */
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { apiPut } from '@/lib/api';
import { useProjects } from '@/features/projects/hooks/useProjects';
import { usePitchers } from '@/features/users/hooks/usePitchers';
import type { AdAccount } from '../types';

interface AccountAssignDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  account: AdAccount;
}

export function AccountAssignDialog({
  open,
  onOpenChange,
  account,
}: AccountAssignDialogProps) {
  const queryClient = useQueryClient();
  const { data: projects } = useProjects({ status: 'active' });
  const { data: pitchers } = usePitchers();

  const [projectId, setProjectId] = useState<number | undefined>(account.project_id ?? undefined);
  const [pitcherId, setPitcherId] = useState<number | undefined>(account.pitcher_id ?? undefined);

  const mutation = useMutation({
    mutationFn: () =>
      apiPut(`/api/v1/ad-accounts/${account.id}/assign`, {
        project_id: projectId,
        pitcher_id: pitcherId,
      }),
    onSuccess: () => {
      toast.success('账户分配成功');
      queryClient.invalidateQueries({ queryKey: ['ad-accounts'] });
      onOpenChange(false);
    },
    onError: (error: Error) => {
      toast.error(`分配失败: ${error.message}`);
    },
  });

  const handleSubmit = () => {
    mutation.mutate();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>分配账户</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="text-sm text-muted-foreground">
            账户ID: <span className="font-mono">{account.account_id}</span>
          </div>

          <div className="space-y-2">
            <Label>目标项目</Label>
            <Select
              value={projectId?.toString() ?? '__none__'}
              onValueChange={(v) => setProjectId(v === '__none__' ? undefined : Number(v))}
            >
              <SelectTrigger>
                <SelectValue placeholder="选择项目" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__none__">不分配</SelectItem>
                {projects?.items?.map(project => (
                  <SelectItem key={project.id} value={project.id.toString()}>
                    {project.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>目标投手</Label>
            <Select
              value={pitcherId?.toString() ?? '__none__'}
              onValueChange={(v) => setPitcherId(v === '__none__' ? undefined : Number(v))}
            >
              <SelectTrigger>
                <SelectValue placeholder="选择投手" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__none__">不分配</SelectItem>
                {pitchers?.map(pitcher => (
                  <SelectItem key={pitcher.id} value={pitcher.id.toString()}>
                    {pitcher.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleSubmit} disabled={mutation.isPending}>
            {mutation.isPending ? '分配中...' : '确认分配'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

#### 提交前自检

□ 第一行是 'use client'
□ 使用 Dialog 组件
□ 项目/投手选择
□ toast 通知完整
□ 分配后刷新列表

#### 验收标准

- [ ] 仅授权角色可分配
- [ ] 选择项目/投手
- [ ] 分配成功刷新列表
- [ ] toast 通知完整
- [ ] `npm run build` 无错误

---

### TASK-FE-ACCT-007: 账户状态流转（6 状态）

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | ad-accounts |
| 任务 ID | TASK-FE-ACCT-007 |
| 技术栈 | State Machine + AlertDialog |
| 优先级 | P0 |
| 预估工时 | 4h |

**前置条件**: TASK-FE-ACCT-004 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §3.2 (账户状态机)
- STATE_MACHINE.md v2.9 §7.1 (账户状态机)

#### 任务

实现账户状态流转 UI：
1. new → testing：开始测试
2. testing → active：激活账户
3. active → suspended：暂停账户
4. suspended → active：恢复账户
5. suspended → dead：标记死亡
6. active → archived：归档账户
7. 状态变更需确认弹窗

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/ad-accounts/components/AccountStatusActions.tsx` | 状态操作按钮 | 100-140 |
| `src/features/ad-accounts/components/AccountStatusDialog.tsx` | 确认弹窗 | 60-80 |
| `src/features/ad-accounts/lib/status-transitions.ts` | 状态转换逻辑 | 60-80 |

#### 思考要点（必须先分析）

1. **状态机**: 6 个状态的转换规则是什么？
2. **权限控制**: 谁可以操作状态？account_manager, admin
3. **危险操作**: dead/archived 需要特别警告
4. **按钮显示**: 根据当前状态显示可用操作

#### 约束规则

1. 状态转换必须符合 STATE_MACHINE.md
2. 仅 account_manager, admin 可操作
3. dead/archived 操作需要警告弹窗
4. 使用 AlertDialog 确认

#### 代码参考

**文件: src/features/ad-accounts/lib/status-transitions.ts**
```typescript
/**
 * 账户状态转换规则
 * SoT: STATE_MACHINE.md v2.9 §7.1
 */
import type { AccountStatus } from '../types';

interface StatusTransition {
  from: AccountStatus;
  to: AccountStatus;
  action: string;
  label: string;
  variant?: 'default' | 'destructive' | 'warning';
  requireConfirm?: boolean;
  confirmMessage?: string;
}

export const ACCOUNT_STATUS_TRANSITIONS: StatusTransition[] = [
  {
    from: 'new',
    to: 'testing',
    action: 'start_test',
    label: '开始测试',
    variant: 'default',
    requireConfirm: true,
    confirmMessage: '确定要开始测试该账户吗？',
  },
  {
    from: 'testing',
    to: 'active',
    action: 'activate',
    label: '激活',
    variant: 'default',
    requireConfirm: true,
    confirmMessage: '确定要激活该账户吗？',
  },
  {
    from: 'active',
    to: 'suspended',
    action: 'suspend',
    label: '暂停',
    variant: 'warning',
    requireConfirm: true,
    confirmMessage: '确定要暂停该账户吗？暂停后账户将无法投放。',
  },
  {
    from: 'suspended',
    to: 'active',
    action: 'resume',
    label: '恢复',
    variant: 'default',
    requireConfirm: true,
    confirmMessage: '确定要恢复该账户吗？',
  },
  {
    from: 'suspended',
    to: 'dead',
    action: 'mark_dead',
    label: '标记死亡',
    variant: 'destructive',
    requireConfirm: true,
    confirmMessage: '⚠️ 警告：标记为死亡后账户将无法恢复。确定要继续吗？',
  },
  {
    from: 'active',
    to: 'archived',
    action: 'archive',
    label: '归档',
    variant: 'destructive',
    requireConfirm: true,
    confirmMessage: '确定要归档该账户吗？归档后将无法恢复。',
  },
];

export function getAvailableTransitions(currentStatus: AccountStatus): StatusTransition[] {
  return ACCOUNT_STATUS_TRANSITIONS.filter(t => t.from === currentStatus);
}
```

**文件: src/features/ad-accounts/components/AccountStatusActions.tsx**
```typescript
'use client';

/**
 * 账户状态操作按钮
 * SoT: STATE_MACHINE.md v2.9 §7.1
 */
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { apiPost } from '@/lib/api';
import { usePermission } from '@/hooks/usePermission';
import { getAvailableTransitions } from '../lib/status-transitions';
import type { AdAccount } from '../types';

interface AccountStatusActionsProps {
  account: AdAccount;
}

export function AccountStatusActions({ account }: AccountStatusActionsProps) {
  const { can } = usePermission();
  const queryClient = useQueryClient();
  const [pendingAction, setPendingAction] = useState<{
    action: string;
    label: string;
    message: string;
  } | null>(null);

  const transitions = getAvailableTransitions(account.status);

  const mutation = useMutation({
    mutationFn: (action: string) =>
      apiPost(`/api/v1/ad-accounts/${account.id}/status`, { action }),
    onSuccess: () => {
      toast.success('状态更新成功');
      queryClient.invalidateQueries({ queryKey: ['ad-accounts'] });
      queryClient.invalidateQueries({ queryKey: ['ad-account', account.id] });
      setPendingAction(null);
    },
    onError: (error: Error) => {
      toast.error(`操作失败: ${error.message}`);
    },
  });

  // 仅 account_manager, admin 可操作
  if (!can('account:update_status')) {
    return null;
  }

  if (transitions.length === 0) {
    return null;
  }

  const handleClick = (transition: typeof transitions[0]) => {
    if (transition.requireConfirm) {
      setPendingAction({
        action: transition.action,
        label: transition.label,
        message: transition.confirmMessage ?? `确定要${transition.label}该账户吗？`,
      });
    } else {
      mutation.mutate(transition.action);
    }
  };

  return (
    <>
      <div className="flex gap-2">
        {transitions.map(transition => (
          <Button
            key={transition.action}
            variant={transition.variant === 'destructive' ? 'destructive' : 'outline'}
            size="sm"
            onClick={() => handleClick(transition)}
            disabled={mutation.isPending}
          >
            {transition.label}
          </Button>
        ))}
      </div>

      <AlertDialog open={!!pendingAction} onOpenChange={() => setPendingAction(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认{pendingAction?.label}</AlertDialogTitle>
            <AlertDialogDescription>
              {pendingAction?.message}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={mutation.isPending}>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => pendingAction && mutation.mutate(pendingAction.action)}
              disabled={mutation.isPending}
            >
              {mutation.isPending ? '处理中...' : '确认'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
```

#### 提交前自检

□ 第一行是 'use client'
□ 状态转换符合状态机
□ 权限检查正确
□ 使用 AlertDialog 确认
□ 危险操作有警告

#### 验收标准

- [ ] 状态转换符合 STATE_MACHINE.md
- [ ] 仅授权角色可操作
- [ ] 确认弹窗正确显示
- [ ] dead/archived 有警告
- [ ] `npm run build` 无错误

---

### TASK-FE-ACCT-008: 账户详情弹窗

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | ad-accounts |
| 任务 ID | TASK-FE-ACCT-008 |
| 技术栈 | Dialog + TanStack Query |
| 优先级 | P0 |
| 预估工时 | 3h |

**前置条件**: TASK-FE-ACCT-004 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §7.1 (必须使用的组件)
- API_SOT.md v9.7 (GET /api/v1/ad-accounts/:id)

#### 任务

实现账户详情弹窗：
1. 使用 Dialog 组件
2. 显示账户完整信息
3. 显示余额和消耗统计
4. 显示状态流转历史
5. 显示操作按钮（根据权限）

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/ad-accounts/components/AdAccountDetailDialog.tsx` | 详情弹窗 | 150-200 |
| `src/features/ad-accounts/hooks/useAdAccount.ts` | 单条数据 Hook | 20-30 |

#### 思考要点（必须先分析）

1. **数据获取**: 详情是否需要单独 API？
2. **统计数据**: 余额/消耗数据如何展示？
3. **状态历史**: 是否显示状态变更记录？
4. **操作按钮**: 哪些操作显示在详情中？

#### 约束规则

1. 使用 Dialog 组件（禁止 Modal）
2. 金额使用 formatCurrency 格式化
3. 状态使用 StatusBadge 显示
4. 操作按钮根据权限显示

#### 代码参考

**文件: src/features/ad-accounts/hooks/useAdAccount.ts**
```typescript
import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/lib/api';
import type { AdAccount } from '../types';

interface AdAccountDetail extends AdAccount {
  total_spend?: number;
  total_topup?: number;
  status_history?: Array<{
    from_status: string;
    to_status: string;
    changed_at: string;
    changed_by: string;
  }>;
}

export function useAdAccount(id: number) {
  return useQuery({
    queryKey: ['ad-account', id],
    queryFn: () => apiGet<AdAccountDetail>(`/api/v1/ad-accounts/${id}`),
    enabled: id > 0,
  });
}
```

**文件: src/features/ad-accounts/components/AdAccountDetailDialog.tsx**
```typescript
'use client';

/**
 * 账户详情弹窗
 * SoT: FRONTEND_PAGE_DESIGN_v2.1.md §7.1
 */
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Skeleton } from '@/components/ui/skeleton';
import { StatusBadge } from '@/components/ui/status-badge';
import { Separator } from '@/components/ui/separator';
import { usePermission } from '@/hooks/usePermission';
import { formatCurrency, formatDate } from '@/lib/utils';
import { useAdAccount } from '../hooks/useAdAccount';
import { AccountStatusActions } from './AccountStatusActions';

interface AdAccountDetailDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  accountId: number;
}

export function AdAccountDetailDialog({
  open,
  onOpenChange,
  accountId,
}: AdAccountDetailDialogProps) {
  const { can } = usePermission();
  const { data: account, isLoading, error } = useAdAccount(accountId);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>账户详情</DialogTitle>
        </DialogHeader>

        {isLoading ? (
          <div className="space-y-4">
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
          </div>
        ) : error || !account ? (
          <div className="text-center py-8 text-destructive">
            加载失败: {error?.message ?? '账户不存在'}
          </div>
        ) : (
          <div className="space-y-6">
            {/* 基础信息 */}
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-3">基础信息</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-sm text-muted-foreground">账户ID</span>
                  <p className="font-mono">{account.account_id}</p>
                </div>
                <div>
                  <span className="text-sm text-muted-foreground">状态</span>
                  <p><StatusBadge type="account" value={account.status} /></p>
                </div>
                <div>
                  <span className="text-sm text-muted-foreground">渠道</span>
                  <p>{account.channel_name}</p>
                </div>
                <div>
                  <span className="text-sm text-muted-foreground">项目</span>
                  <p>{account.project_name ?? '-'}</p>
                </div>
                <div>
                  <span className="text-sm text-muted-foreground">投手</span>
                  <p>{account.pitcher_name ?? '-'}</p>
                </div>
                <div>
                  <span className="text-sm text-muted-foreground">创建时间</span>
                  <p>{formatDate(account.created_at)}</p>
                </div>
              </div>
            </div>

            <Separator />

            {/* 资金统计 */}
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-3">资金统计</h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="p-4 bg-muted rounded-lg">
                  <span className="text-sm text-muted-foreground">当前余额</span>
                  <p className="text-xl font-bold">
                    {formatCurrency(account.balance ?? 0)}
                  </p>
                </div>
                <div className="p-4 bg-muted rounded-lg">
                  <span className="text-sm text-muted-foreground">累计充值</span>
                  <p className="text-xl font-bold">
                    {formatCurrency(account.total_topup ?? 0)}
                  </p>
                </div>
                <div className="p-4 bg-muted rounded-lg">
                  <span className="text-sm text-muted-foreground">累计消耗</span>
                  <p className="text-xl font-bold">
                    {formatCurrency(account.total_spend ?? 0)}
                  </p>
                </div>
              </div>
            </div>

            {/* 状态历史 */}
            {account.status_history && account.status_history.length > 0 && (
              <>
                <Separator />
                <div>
                  <h3 className="text-sm font-medium text-muted-foreground mb-3">状态历史</h3>
                  <div className="space-y-2 max-h-[150px] overflow-y-auto">
                    {account.status_history.map((history, index) => (
                      <div key={index} className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-2">
                          <StatusBadge type="account" value={history.from_status} />
                          <span>→</span>
                          <StatusBadge type="account" value={history.to_status} />
                        </div>
                        <div className="text-muted-foreground">
                          {history.changed_by} · {formatDate(history.changed_at)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* 操作按钮 */}
            {can('account:update_status') && (
              <>
                <Separator />
                <div>
                  <h3 className="text-sm font-medium text-muted-foreground mb-3">操作</h3>
                  <AccountStatusActions account={account} />
                </div>
              </>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
```

#### 提交前自检

□ 第一行是 'use client'
□ 使用 Dialog 组件
□ 使用 StatusBadge 显示状态
□ 金额格式化安全
□ 有加载/错误状态

#### 验收标准

- [ ] 使用 Dialog 组件
- [ ] 显示账户完整信息
- [ ] 显示资金统计
- [ ] 显示状态历史
- [ ] 操作按钮权限控制
- [ ] `npm run build` 无错误

---

## 4.6 CHAN 渠道模块

### TASK-FE-CHAN-001: 渠道列表页

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | channels |
| 任务 ID | TASK-FE-CHAN-001 |
| 技术栈 | Next.js 16 + TanStack Query + DataTable |
| 优先级 | P1 |
| 预估工时 | 4h |

**前置条件**: TASK-FE-COMMON-005 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §5.1 (页面清单)
- FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (权限矩阵)
- API_SOT.md v9.7 (GET /api/v1/channels)

#### 任务

实现渠道管理列表页：
1. 页面路由 `/channels`
2. 使用 COMMON-005 通用列表模板
3. 角色权限控制（account_manager、admin 可管理）
4. 列表数据加载和展示

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/app/channels/page.tsx` | 路由页面 | 15-20 |
| `src/features/channels/components/ChannelsPage.tsx` | 页面组件 | 80-120 |
| `src/features/channels/hooks/useChannels.ts` | 列表数据 Hook | 30-40 |
| `src/features/channels/services/channelsApi.ts` | API 调用 | 40-50 |
| `src/features/channels/types/channel.types.ts` | 类型定义 | 25-35 |

#### 思考要点（必须先分析）

1. **API 端点**: GET /api/v1/channels 返回什么结构？
2. **权限控制**: 哪些角色可以访问渠道管理？
3. **列表字段**: 显示哪些字段？渠道名、平台、账户数、状态？
4. **分页**: 是否需要分页？默认每页多少条？
5. **操作按钮**: 需要哪些行操作？编辑、启用/禁用？

#### 约束规则

1. 仅 `account_manager` 和 `admin` 可访问
2. 使用 `apiGet` 请求数据（禁止 fetch/axios）
3. 列表必须使用 DataTable 组件
4. 状态显示必须使用 StatusBadge
5. 加载状态和空状态需要处理

#### 边缘情况

| 场景 | 期望行为 | 代码示例 |
|------|---------|---------|
| 加载中 | 显示骨架屏 | `<Skeleton />` |
| 无数据 | 显示空状态 | "暂无渠道数据" |
| 无权限 | 显示无权限页 | `<NoPermission />` |
| API 错误 | 显示错误提示 | `toast.error('加载失败')` |

#### 代码参考

**文件 1: src/app/channels/page.tsx**
```typescript
import { ChannelsPage } from '@/features/channels/components/ChannelsPage';

export default function Page() {
  return <ChannelsPage />;
}
```

**文件 2: src/features/channels/types/channel.types.ts**
```typescript
export interface Channel {
  id: number;
  name: string;
  platform: string;
  account_count: number;
  status: 'active' | 'inactive';
  created_at: string;
  updated_at: string;
}

export interface ChannelsResponse {
  items: Channel[];
  total: number;
  page: number;
  page_size: number;
}

export interface ChannelsFilters {
  status?: string;
  platform?: string;
  page?: number;
  page_size?: number;
}
```

**文件 3: src/features/channels/services/channelsApi.ts**
```typescript
import { apiGet, apiPost, apiPut } from '@/lib/api';
import type { Channel, ChannelsResponse, ChannelsFilters } from '../types/channel.types';

export async function getChannels(filters?: ChannelsFilters): Promise<ChannelsResponse> {
  const params = new URLSearchParams();
  if (filters?.status) params.set('status', filters.status);
  if (filters?.platform) params.set('platform', filters.platform);
  if (filters?.page) params.set('page', String(filters.page));
  if (filters?.page_size) params.set('page_size', String(filters.page_size));

  return apiGet<ChannelsResponse>(`/api/v1/channels?${params.toString()}`);
}

export async function getChannel(id: number): Promise<Channel> {
  return apiGet<Channel>(`/api/v1/channels/${id}`);
}

export async function createChannel(data: Partial<Channel>): Promise<Channel> {
  return apiPost<Channel>('/api/v1/channels', data);
}

export async function updateChannel(id: number, data: Partial<Channel>): Promise<Channel> {
  return apiPut<Channel>(`/api/v1/channels/${id}`, data);
}
```

**文件 4: src/features/channels/hooks/useChannels.ts**
```typescript
'use client';

import { useQuery } from '@tanstack/react-query';
import { getChannels } from '../services/channelsApi';
import type { ChannelsFilters } from '../types/channel.types';

export function useChannels(filters?: ChannelsFilters) {
  return useQuery({
    queryKey: ['channels', filters],
    queryFn: () => getChannels(filters),
    staleTime: 30_000, // 30 秒缓存
  });
}
```

**文件 5: src/features/channels/components/ChannelsPage.tsx**
```typescript
'use client';

import { useState } from 'react';
import { useChannels } from '../hooks/useChannels';
import { ChannelsTable } from './ChannelsTable';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import { ChannelFormDialog } from './ChannelFormDialog';
import { useHasPermission } from '@/hooks/useHasPermission';
import { NoPermission } from '@/components/common/NoPermission';

export function ChannelsPage() {
  const [createOpen, setCreateOpen] = useState(false);
  const canManage = useHasPermission(['account_manager', 'admin']);

  const { data, isLoading, error } = useChannels();

  if (!canManage) {
    return <NoPermission />;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">渠道管理</h1>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          新建渠道
        </Button>
      </div>

      <ChannelsTable
        data={data?.items ?? []}
        isLoading={isLoading}
        error={error}
      />

      <ChannelFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
      />
    </div>
  );
}
```

#### 提交前自检

□ 第一行是 'use client'（页面组件）
□ 使用 apiGet 请求（非 fetch/axios）
□ 使用 DataTable 组件（非原生 table）
□ 权限检查使用 useHasPermission
□ 加载状态已处理
□ 空状态已处理
□ 错误处理已处理
□ 无 any 类型

#### 验收标准

- [ ] 仅 account_manager 和 admin 可访问
- [ ] 使用 DataTable 组件展示列表
- [ ] 显示：渠道名、平台、账户数、状态
- [ ] 加载中显示骨架屏
- [ ] 空数据显示提示
- [ ] 新建按钮打开表单弹窗
- [ ] `npm run build` 无错误

---

### TASK-FE-CHAN-002: 渠道表格组件

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | channels |
| 任务 ID | TASK-FE-CHAN-002 |
| 技术栈 | DataTable + StatusBadge |
| 优先级 | P1 |
| 预估工时 | 3h |

**前置条件**: TASK-FE-CHAN-001 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §7.1 (必须使用的组件)

#### 任务

实现渠道表格组件：
1. 使用 DataTable 组件
2. 状态显示使用 StatusBadge
3. 行操作按钮（编辑、启用/禁用）
4. 排序和筛选功能

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/channels/components/ChannelsTable.tsx` | 渠道表格 | 100-130 |
| `src/features/channels/components/ChannelRow.tsx` | 表格行组件 | 40-60 |

#### 思考要点（必须先分析）

1. **列定义**: 需要显示哪些列？
2. **状态显示**: active/inactive 如何映射颜色？
3. **行操作**: 编辑、状态切换按钮如何触发？
4. **排序**: 哪些列支持排序？
5. **响应式**: 移动端如何展示？

#### 约束规则

1. 必须使用 DataTable 组件（禁止原生 table）
2. 状态列使用 StatusBadge 组件
3. 行操作使用 DropdownMenu
4. 支持列排序

#### 边缘情况

| 场景 | 期望行为 | 代码示例 |
|------|---------|---------|
| 空列表 | 显示空状态 | `emptyMessage="暂无渠道"` |
| 加载中 | 显示骨架屏 | `<TableSkeleton />` |
| 无权限操作 | 隐藏操作按钮 | `{canManage && <Actions />}` |

#### 代码参考

**文件 1: src/features/channels/components/ChannelsTable.tsx**
```typescript
'use client';

import { DataTable } from '@/components/ui/data-table';
import { StatusBadge } from '@/components/common/StatusBadge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { MoreHorizontal, Pencil, Power } from 'lucide-react';
import type { Channel } from '../types/channel.types';
import type { ColumnDef } from '@tanstack/react-table';

interface Props {
  data: Channel[];
  isLoading?: boolean;
  error?: Error | null;
  onEdit?: (channel: Channel) => void;
  onToggleStatus?: (channel: Channel) => void;
}

export function ChannelsTable({
  data,
  isLoading,
  error,
  onEdit,
  onToggleStatus,
}: Props) {
  const columns: ColumnDef<Channel>[] = [
    {
      accessorKey: 'name',
      header: '渠道名称',
    },
    {
      accessorKey: 'platform',
      header: '平台',
    },
    {
      accessorKey: 'account_count',
      header: '账户数',
      cell: ({ row }) => (
        <span className="font-mono">{row.original.account_count}</span>
      ),
    },
    {
      accessorKey: 'status',
      header: '状态',
      cell: ({ row }) => (
        <StatusBadge
          status={row.original.status}
          statusMap={{
            active: { label: '启用', variant: 'success' },
            inactive: { label: '禁用', variant: 'secondary' },
          }}
        />
      ),
    },
    {
      id: 'actions',
      cell: ({ row }) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <MoreHorizontal className="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => onEdit?.(row.original)}>
              <Pencil className="w-4 h-4 mr-2" />
              编辑
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onToggleStatus?.(row.original)}>
              <Power className="w-4 h-4 mr-2" />
              {row.original.status === 'active' ? '禁用' : '启用'}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  if (error) {
    return <div className="text-red-500">加载失败: {error.message}</div>;
  }

  return (
    <DataTable
      columns={columns}
      data={data}
      isLoading={isLoading}
      emptyMessage="暂无渠道数据"
    />
  );
}
```

#### 提交前自检

□ 使用 DataTable 组件（非原生 table）
□ 状态使用 StatusBadge 显示
□ 行操作使用 DropdownMenu
□ 空状态使用 emptyMessage
□ 加载状态已处理
□ 错误状态已处理
□ 无 any 类型

#### 验收标准

- [ ] 使用 DataTable 组件
- [ ] 显示：渠道名称、平台、账户数、状态
- [ ] 状态使用 StatusBadge 组件
- [ ] 行操作按钮（编辑、启用/禁用）
- [ ] 空列表显示提示
- [ ] `npm run build` 无错误

---

### TASK-FE-CHAN-003: 渠道创建/编辑表单

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | channels |
| 任务 ID | TASK-FE-CHAN-003 |
| 技术栈 | react-hook-form + zod + Dialog |
| 优先级 | P1 |
| 预估工时 | 4h |

**前置条件**: TASK-FE-CHAN-001 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (权限矩阵)
- API_SOT.md v9.7 (POST/PUT /api/v1/channels)

#### 任务

实现渠道创建/编辑表单：
1. 使用 Dialog 包裹表单
2. react-hook-form + zod 验证
3. 创建和编辑模式复用
4. 提交成功通知和刷新

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/channels/components/ChannelForm.tsx` | 渠道表单 | 100-130 |
| `src/features/channels/components/ChannelFormSchema.ts` | 验证 Schema | 20-30 |
| `src/features/channels/components/ChannelFormDialog.tsx` | 表单弹窗 | 40-60 |
| `src/features/channels/hooks/useChannelMutations.ts` | 变更 Hook | 50-70 |

#### 思考要点（必须先分析）

1. **表单字段**: 渠道名称、平台是必填吗？
2. **平台选项**: 平台列表从哪里获取？
3. **编辑模式**: 如何区分创建和编辑？
4. **权限控制**: 哪些角色可以创建/编辑渠道？
5. **提交处理**: 成功后关闭弹窗并刷新列表？

#### 约束规则

1. 仅 `account_manager` 和 `admin` 可创建渠道
2. 使用 react-hook-form + zod 验证
3. 使用 Dialog 组件（非 Modal）
4. 提交成功显示 toast 通知
5. 提交中按钮禁用

#### 边缘情况

| 场景 | 期望行为 | 代码示例 |
|------|---------|---------|
| 渠道名重复 | 显示错误 | API 返回 409 |
| 提交中 | 禁用按钮 | `disabled={isPending}` |
| 编辑模式 | 预填数据 | `defaultValues={channel}` |

#### 代码参考

**文件 1: src/features/channels/components/ChannelFormSchema.ts**
```typescript
import { z } from 'zod';

export const channelFormSchema = z.object({
  name: z.string().min(1, '请输入渠道名称').max(50, '渠道名称不能超过50字'),
  platform: z.string().min(1, '请选择平台'),
});

export type ChannelFormValues = z.infer<typeof channelFormSchema>;
```

**文件 2: src/features/channels/hooks/useChannelMutations.ts**
```typescript
'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { createChannel, updateChannel } from '../services/channelsApi';
import type { ChannelFormValues } from '../components/ChannelFormSchema';

export function useCreateChannel(options?: { onSuccess?: () => void }) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ChannelFormValues) => createChannel(data),
    onSuccess: () => {
      toast.success('渠道创建成功');
      queryClient.invalidateQueries({ queryKey: ['channels'] });
      options?.onSuccess?.();
    },
    onError: (error: Error) => {
      toast.error(error.message || '创建失败');
    },
  });
}

export function useUpdateChannel(options?: { onSuccess?: () => void }) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ChannelFormValues }) =>
      updateChannel(id, data),
    onSuccess: () => {
      toast.success('渠道更新成功');
      queryClient.invalidateQueries({ queryKey: ['channels'] });
      options?.onSuccess?.();
    },
    onError: (error: Error) => {
      toast.error(error.message || '更新失败');
    },
  });
}
```

**文件 3: src/features/channels/components/ChannelFormDialog.tsx**
```typescript
'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { channelFormSchema, type ChannelFormValues } from './ChannelFormSchema';
import { useCreateChannel, useUpdateChannel } from '../hooks/useChannelMutations';
import type { Channel } from '../types/channel.types';

// 平台选项（从配置获取）
const PLATFORMS = [
  { value: 'facebook', label: 'Facebook' },
  { value: 'google', label: 'Google' },
  { value: 'tiktok', label: 'TikTok' },
  { value: 'kuaishou', label: '快手' },
  { value: 'weixin', label: '微信' },
];

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  channel?: Channel; // 编辑模式传入
}

export function ChannelFormDialog({ open, onOpenChange, channel }: Props) {
  const isEdit = Boolean(channel);

  const form = useForm<ChannelFormValues>({
    resolver: zodResolver(channelFormSchema),
    defaultValues: channel ?? {
      name: '',
      platform: '',
    },
  });

  const createMutation = useCreateChannel({
    onSuccess: () => {
      onOpenChange(false);
      form.reset();
    },
  });

  const updateMutation = useUpdateChannel({
    onSuccess: () => {
      onOpenChange(false);
    },
  });

  const isPending = createMutation.isPending || updateMutation.isPending;

  const onSubmit = (values: ChannelFormValues) => {
    if (isEdit && channel) {
      updateMutation.mutate({ id: channel.id, data: values });
    } else {
      createMutation.mutate(values);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{isEdit ? '编辑渠道' : '新建渠道'}</DialogTitle>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>渠道名称 *</FormLabel>
                  <FormControl>
                    <Input placeholder="请输入渠道名称" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="platform"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>平台 *</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="请选择平台" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {PLATFORMS.map((p) => (
                        <SelectItem key={p.value} value={p.value}>
                          {p.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex justify-end gap-2 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                取消
              </Button>
              <Button type="submit" disabled={isPending}>
                {isPending ? '提交中...' : isEdit ? '保存' : '创建'}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
```

#### 提交前自检

□ 使用 Dialog 组件（非 Modal）
□ 使用 react-hook-form + zod
□ 创建和编辑模式复用
□ 提交中按钮禁用
□ 有 toast 成功/失败通知
□ 提交成功后关闭弹窗
□ 提交成功后刷新列表
□ 无 any 类型

#### 验收标准

- [ ] 仅 account_manager 和 admin 可创建渠道
- [ ] 必填字段：渠道名称、平台
- [ ] 使用 react-hook-form + zod 验证
- [ ] 创建成功显示 toast 通知
- [ ] 编辑模式预填现有数据
- [ ] 提交中按钮禁用
- [ ] `npm run build` 无错误

---

### TASK-FE-CHAN-004: 渠道状态切换

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | channels |
| 任务 ID | TASK-FE-CHAN-004 |
| 技术栈 | AlertDialog + useMutation |
| 优先级 | P1 |
| 预估工时 | 2h |

**前置条件**: TASK-FE-CHAN-002 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (权限矩阵)

#### 任务

实现渠道状态切换组件：
1. 启用/禁用确认弹窗
2. 状态变更 API 调用
3. 成功后刷新列表

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/channels/components/ChannelStatusToggle.tsx` | 状态切换组件 | 60-80 |

#### 思考要点（必须先分析）

1. **状态值**: active/inactive 还是 enabled/disabled？
2. **确认弹窗**: 需要二次确认吗？
3. **权限控制**: 哪些角色可以切换状态？
4. **影响范围**: 禁用渠道会影响关联账户吗？

#### 约束规则

1. 仅 `account_manager` 和 `admin` 可操作
2. 状态变更需二次确认
3. 使用 AlertDialog（危险操作确认）
4. 成功后刷新列表

#### 边缘情况

| 场景 | 期望行为 | 代码示例 |
|------|---------|---------|
| 有关联账户 | 警告提示 | "该渠道下有X个账户" |
| 切换中 | 禁用按钮 | `disabled={isPending}` |
| 切换失败 | 显示错误 | `toast.error()` |

#### 代码参考

**文件 1: src/features/channels/components/ChannelStatusToggle.tsx**
```typescript
'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { updateChannel } from '../services/channelsApi';
import type { Channel } from '../types/channel.types';

interface Props {
  channel: Channel;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ChannelStatusToggle({ channel, open, onOpenChange }: Props) {
  const queryClient = useQueryClient();
  const newStatus = channel.status === 'active' ? 'inactive' : 'active';
  const actionText = newStatus === 'active' ? '启用' : '禁用';

  const mutation = useMutation({
    mutationFn: () => updateChannel(channel.id, { status: newStatus }),
    onSuccess: () => {
      toast.success(`渠道已${actionText}`);
      queryClient.invalidateQueries({ queryKey: ['channels'] });
      onOpenChange(false);
    },
    onError: (error: Error) => {
      toast.error(error.message || `${actionText}失败`);
    },
  });

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>确认{actionText}渠道</AlertDialogTitle>
          <AlertDialogDescription>
            您确定要{actionText}渠道"{channel.name}"吗？
            {channel.account_count > 0 && (
              <span className="block mt-2 text-yellow-600">
                该渠道下有 {channel.account_count} 个账户
              </span>
            )}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>取消</AlertDialogCancel>
          <AlertDialogAction
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className={newStatus === 'inactive' ? 'bg-red-500 hover:bg-red-600' : ''}
          >
            {mutation.isPending ? '处理中...' : `确认${actionText}`}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
```

#### 提交前自检

□ 使用 AlertDialog 组件
□ 二次确认操作
□ 禁用时使用红色按钮
□ 有关联账户时显示警告
□ 成功后刷新列表
□ 有 toast 通知
□ 无 any 类型

#### 验收标准

- [ ] 仅 account_manager 和 admin 可操作
- [ ] 支持启用/禁用状态切换
- [ ] 状态变更需确认
- [ ] 变更成功显示 toast
- [ ] 变更后刷新列表
- [ ] `npm run build` 无错误

---

## 4.7 TOP 充值模块

### TASK-FE-TOP-001: 充值列表页

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | topups |
| 任务 ID | TASK-FE-TOP-001 |
| 技术栈 | Next.js 16 + TanStack Query + DataTable |
| 优先级 | P1 |
| 预估工时 | 4h |

**前置条件**: TASK-FE-COMMON-005 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §6.4 (充值管理)
- FRONTEND_PAGE_DESIGN_v2.1.md §5.1 (页面清单)
- API_SOT.md v9.7 (GET /api/v1/topups)

#### 任务

实现充值管理列表页：
1. 页面路由 `/topups`
2. 使用 COMMON-005 通用列表模板
3. 角色权限控制
4. 7 状态充值流程

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/app/topups/page.tsx` | 路由页面 | 15-20 |
| `src/features/topups/components/TopupsPage.tsx` | 页面组件 | 100-140 |
| `src/features/topups/hooks/useTopups.ts` | 列表数据 Hook | 30-40 |
| `src/features/topups/services/topupsApi.ts` | API 调用 | 50-70 |
| `src/features/topups/types/topup.types.ts` | 类型定义 | 40-60 |

#### 思考要点（必须先分析）

1. **API 端点**: GET /api/v1/topups 返回什么结构？
2. **权限控制**: 哪些角色可以访问？看到哪些数据？
3. **7 状态**: draft, pending_review, finance_approve, paid, completed, rejected, cancelled
4. **列表字段**: 申请日期、账户、金额、申请人、状态
5. **操作按钮**: 根据角色和状态显示不同操作

#### 约束规则

1. pitcher 只能看自己申请的充值
2. finance 可以看所有充值并审批
3. 使用 `apiGet` 请求数据
4. 列表必须使用 DataTable 组件
5. 状态显示必须使用 StatusBadge

#### 边缘情况

| 场景 | 期望行为 | 代码示例 |
|------|---------|---------|
| 加载中 | 显示骨架屏 | `<Skeleton />` |
| 无数据 | 显示空状态 | "暂无充值申请" |
| 无权限 | 显示无权限页 | `<NoPermission />` |

#### 代码参考

**文件 1: src/features/topups/types/topup.types.ts**
```typescript
export type TopupStatus =
  | 'draft'
  | 'pending_review'
  | 'finance_approve'
  | 'paid'
  | 'completed'
  | 'rejected'
  | 'cancelled';

export interface Topup {
  id: number;
  ad_account_id: number;
  ad_account_name: string;
  amount: number;
  status: TopupStatus;
  applicant_id: number;
  applicant_name: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  approved_by?: number;
  approved_at?: string;
  paid_at?: string;
  completed_at?: string;
  rejected_reason?: string;
}

export interface TopupsResponse {
  items: Topup[];
  total: number;
  page: number;
  page_size: number;
}

export interface TopupsFilters {
  status?: TopupStatus;
  ad_account_id?: number;
  applicant_id?: number;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}
```

**文件 2: src/features/topups/services/topupsApi.ts**
```typescript
import { apiGet, apiPost, apiPatch } from '@/lib/api';
import type { Topup, TopupsResponse, TopupsFilters, TopupStatus } from '../types/topup.types';

export async function getTopups(filters?: TopupsFilters): Promise<TopupsResponse> {
  const params = new URLSearchParams();
  if (filters?.status) params.set('status', filters.status);
  if (filters?.ad_account_id) params.set('ad_account_id', String(filters.ad_account_id));
  if (filters?.applicant_id) params.set('applicant_id', String(filters.applicant_id));
  if (filters?.date_from) params.set('date_from', filters.date_from);
  if (filters?.date_to) params.set('date_to', filters.date_to);
  if (filters?.page) params.set('page', String(filters.page));
  if (filters?.page_size) params.set('page_size', String(filters.page_size));

  return apiGet<TopupsResponse>(`/api/v1/topups?${params.toString()}`);
}

export async function getTopup(id: number): Promise<Topup> {
  return apiGet<Topup>(`/api/v1/topups/${id}`);
}

export async function createTopup(data: {
  ad_account_id: number;
  amount: number;
  notes?: string;
}): Promise<Topup> {
  return apiPost<Topup>('/api/v1/topups', data);
}

export async function updateTopupStatus(
  id: number,
  status: TopupStatus,
  reason?: string
): Promise<Topup> {
  return apiPatch<Topup>(`/api/v1/topups/${id}/status`, { status, reason });
}
```

**文件 3: src/features/topups/hooks/useTopups.ts**
```typescript
'use client';

import { useQuery } from '@tanstack/react-query';
import { getTopups } from '../services/topupsApi';
import type { TopupsFilters } from '../types/topup.types';

export function useTopups(filters?: TopupsFilters) {
  return useQuery({
    queryKey: ['topups', filters],
    queryFn: () => getTopups(filters),
    staleTime: 30_000,
  });
}
```

**文件 4: src/features/topups/components/TopupsPage.tsx**
```typescript
'use client';

import { useState } from 'react';
import { useTopups } from '../hooks/useTopups';
import { TopupsTable } from './TopupsTable';
import { TopupsFilters } from './TopupsFilters';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import { TopupRequestForm } from './TopupRequestForm';
import { useHasPermission } from '@/hooks/useHasPermission';
import type { TopupsFilters as FiltersType } from '../types/topup.types';

export function TopupsPage() {
  const [createOpen, setCreateOpen] = useState(false);
  const [filters, setFilters] = useState<FiltersType>({});

  const canApply = useHasPermission(['pitcher', 'account_manager']);

  const { data, isLoading, error } = useTopups(filters);

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">充值管理</h1>
        {canApply && (
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="w-4 h-4 mr-2" />
            申请充值
          </Button>
        )}
      </div>

      <TopupsFilters filters={filters} onFiltersChange={setFilters} />

      <TopupsTable
        data={data?.items ?? []}
        isLoading={isLoading}
        error={error}
      />

      <TopupRequestForm
        open={createOpen}
        onOpenChange={setCreateOpen}
      />
    </div>
  );
}
```

#### 提交前自检

□ 第一行是 'use client'（页面组件）
□ 使用 apiGet 请求（非 fetch/axios）
□ 使用 DataTable 组件（非原生 table）
□ 7 状态类型定义完整
□ 加载状态已处理
□ 空状态已处理
□ 无 any 类型

#### 验收标准

- [ ] pitcher 和 account_manager 可申请充值
- [ ] finance 可审批充值
- [ ] 使用 DataTable 组件
- [ ] 显示：申请日期、账户、金额、申请人、状态
- [ ] 状态使用 StatusBadge（7 状态）
- [ ] 加载中显示骨架屏
- [ ] `npm run build` 无错误

---

### TASK-FE-TOP-002: 充值筛选器

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | topups |
| 任务 ID | TASK-FE-TOP-002 |
| 技术栈 | Select + DatePicker |
| 优先级 | P1 |
| 预估工时 | 3h |

**前置条件**: TASK-FE-TOP-001 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §6.4 (充值管理)
- STATE_MACHINE.md v2.9 §7.2 (充值状态机)

#### 任务

实现充值筛选器组件：
1. 状态筛选（7 个状态 + 全部）
2. 日期范围筛选
3. 账户筛选
4. 申请人筛选（财务可用）
5. 筛选条件同步到 URL

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/topups/components/TopupsFilters.tsx` | 充值筛选器 | 120-160 |

#### 思考要点（必须先分析）

1. **状态选项**: 7 个状态如何排列？如何显示中文？
2. **日期范围**: 使用什么日期组件？
3. **账户选项**: 从哪里获取账户列表？
4. **URL 同步**: 使用 useSearchParams 还是 nuqs？
5. **权限差异**: 财务可以看申请人筛选，投手不能

#### 约束规则

1. 状态筛选包含 7 个充值状态 + 全部
2. 日期范围默认最近 30 天
3. 账户列表从 API 获取
4. 筛选条件变化时自动查询
5. 使用 Select 组件

#### 边缘情况

| 场景 | 期望行为 | 代码示例 |
|------|---------|---------|
| 账户加载中 | 显示加载提示 | `placeholder="加载中..."` |
| 清空筛选 | 重置所有条件 | `onReset()` |
| 无筛选结果 | 显示空状态 | 由列表组件处理 |

#### 代码参考

**文件 1: src/features/topups/components/TopupsFilters.tsx**
```typescript
'use client';

import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { DatePickerWithRange } from '@/components/ui/date-range-picker';
import { RotateCcw } from 'lucide-react';
import { getAdAccounts } from '@/features/ad-accounts/services/adAccountsApi';
import { useHasPermission } from '@/hooks/useHasPermission';
import type { TopupsFilters as FiltersType, TopupStatus } from '../types/topup.types';
import type { DateRange } from 'react-day-picker';

const TOPUP_STATUS_OPTIONS: { value: TopupStatus | ''; label: string }[] = [
  { value: '', label: '全部状态' },
  { value: 'draft', label: '草稿' },
  { value: 'pending_review', label: '待审核' },
  { value: 'finance_approve', label: '财务已批' },
  { value: 'paid', label: '已付款' },
  { value: 'completed', label: '已完成' },
  { value: 'rejected', label: '已拒绝' },
  { value: 'cancelled', label: '已取消' },
];

interface Props {
  filters: FiltersType;
  onFiltersChange: (filters: FiltersType) => void;
}

export function TopupsFilters({ filters, onFiltersChange }: Props) {
  const isFinance = useHasPermission(['finance', 'ceo', 'admin']);

  const { data: accountsData } = useQuery({
    queryKey: ['ad-accounts', { page_size: 100 }],
    queryFn: () => getAdAccounts({ page_size: 100 }),
  });

  const [dateRange, setDateRange] = useState<DateRange | undefined>();

  useEffect(() => {
    if (dateRange?.from && dateRange?.to) {
      onFiltersChange({
        ...filters,
        date_from: dateRange.from.toISOString().split('T')[0],
        date_to: dateRange.to.toISOString().split('T')[0],
      });
    }
  }, [dateRange]);

  const handleReset = () => {
    onFiltersChange({});
    setDateRange(undefined);
  };

  const accounts = accountsData?.items ?? [];

  return (
    <div className="flex flex-wrap gap-4 items-center">
      {/* 状态筛选 */}
      <Select
        value={filters.status ?? ''}
        onValueChange={(value) =>
          onFiltersChange({ ...filters, status: value as TopupStatus || undefined })
        }
      >
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="全部状态" />
        </SelectTrigger>
        <SelectContent>
          {TOPUP_STATUS_OPTIONS.map((opt) => (
            <SelectItem key={opt.value || '__all__'} value={opt.value || '__all__'}>
              {opt.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* 账户筛选 */}
      <Select
        value={filters.ad_account_id?.toString() ?? ''}
        onValueChange={(value) =>
          onFiltersChange({ ...filters, ad_account_id: value ? Number(value) : undefined })
        }
      >
        <SelectTrigger className="w-[160px]">
          <SelectValue placeholder="全部账户" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">全部账户</SelectItem>
          {accounts.map((account) => (
            <SelectItem key={account.id} value={account.id.toString()}>
              {account.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* 日期范围 */}
      <DatePickerWithRange
        value={dateRange}
        onChange={setDateRange}
        placeholder="选择日期范围"
      />

      {/* 重置按钮 */}
      <Button variant="outline" size="icon" onClick={handleReset}>
        <RotateCcw className="w-4 h-4" />
      </Button>
    </div>
  );
}
```

#### 提交前自检

□ 状态筛选包含 7 个状态 + 全部
□ 账户列表从 API 获取
□ 日期范围组件正常工作
□ 重置按钮清空所有筛选
□ 筛选变化触发查询
□ 无 any 类型

#### 验收标准

- [ ] 状态筛选（7 个状态 + 全部）
- [ ] 日期范围筛选
- [ ] 账户筛选
- [ ] 重置按钮清空所有筛选
- [ ] 筛选条件变化自动查询
- [ ] `npm run build` 无错误

---

### TASK-FE-TOP-003: 充值表格组件

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | topups |
| 任务 ID | TASK-FE-TOP-003 |
| 技术栈 | DataTable + StatusBadge |
| 优先级 | P1 |
| 预估工时 | 3h |

**前置条件**: TASK-FE-TOP-001, TASK-FE-COMMON-003 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §7.1 (必须使用的组件)
- STATE_MACHINE.md v2.9 §7.2 (充值状态机)

#### 任务

实现充值表格组件：
1. 使用 DataTable 组件
2. 状态显示使用 StatusBadge（7 状态）
3. 行操作按钮（根据角色和状态）
4. 金额格式化显示

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/topups/components/TopupsTable.tsx` | 充值表格 | 120-160 |
| `src/features/topups/components/TopupRow.tsx` | 表格行组件 | 40-60 |

#### 思考要点（必须先分析）

1. **列定义**: 申请日期、账户、金额、申请人、状态
2. **状态映射**: 7 个状态的颜色和标签
3. **金额格式**: ¥1,234.56 格式
4. **行操作**: 根据角色和状态显示不同操作
5. **排序**: 默认按申请日期降序

#### 约束规则

1. 必须使用 DataTable 组件
2. 状态列使用 StatusBadge 组件（7 状态）
3. 金额使用 formatCurrency 格式化
4. 行操作使用 DropdownMenu

#### 边缘情况

| 场景 | 期望行为 | 代码示例 |
|------|---------|---------|
| 空列表 | 显示空状态 | `emptyMessage="暂无充值申请"` |
| 金额为 0 | 显示 ¥0.00 | `formatCurrency(0)` |
| 终态记录 | 隐藏操作按钮 | 已完成/已拒绝/已取消 |

#### 代码参考

**文件 1: src/features/topups/components/TopupsTable.tsx**
```typescript
'use client';

import { DataTable } from '@/components/ui/data-table';
import { StatusBadge } from '@/components/common/StatusBadge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { MoreHorizontal, Eye, Check, X, Ban } from 'lucide-react';
import { formatCurrency, formatDate } from '@/lib/utils';
import { useHasPermission } from '@/hooks/useHasPermission';
import type { Topup, TopupStatus } from '../types/topup.types';
import type { ColumnDef } from '@tanstack/react-table';

// 7 状态映射
const TOPUP_STATUS_MAP: Record<TopupStatus, { label: string; variant: string }> = {
  draft: { label: '草稿', variant: 'secondary' },
  pending_review: { label: '待审核', variant: 'warning' },
  finance_approve: { label: '财务已批', variant: 'info' },
  paid: { label: '已付款', variant: 'info' },
  completed: { label: '已完成', variant: 'success' },
  rejected: { label: '已拒绝', variant: 'destructive' },
  cancelled: { label: '已取消', variant: 'secondary' },
};

interface Props {
  data: Topup[];
  isLoading?: boolean;
  error?: Error | null;
  onView?: (topup: Topup) => void;
  onApprove?: (topup: Topup) => void;
  onReject?: (topup: Topup) => void;
  onCancel?: (topup: Topup) => void;
}

export function TopupsTable({
  data,
  isLoading,
  error,
  onView,
  onApprove,
  onReject,
  onCancel,
}: Props) {
  const isFinance = useHasPermission(['finance', 'ceo', 'admin']);

  const columns: ColumnDef<Topup>[] = [
    {
      accessorKey: 'created_at',
      header: '申请日期',
      cell: ({ row }) => formatDate(row.original.created_at),
    },
    {
      accessorKey: 'ad_account_name',
      header: '广告账户',
    },
    {
      accessorKey: 'amount',
      header: '金额',
      cell: ({ row }) => (
        <span className="font-mono">{formatCurrency(row.original.amount)}</span>
      ),
    },
    {
      accessorKey: 'applicant_name',
      header: '申请人',
    },
    {
      accessorKey: 'status',
      header: '状态',
      cell: ({ row }) => (
        <StatusBadge
          status={row.original.status}
          statusMap={TOPUP_STATUS_MAP}
        />
      ),
    },
    {
      id: 'actions',
      cell: ({ row }) => {
        const topup = row.original;
        const isTerminal = ['completed', 'rejected', 'cancelled'].includes(topup.status);
        const canApprove = isFinance && topup.status === 'pending_review';

        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <MoreHorizontal className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onView?.(topup)}>
                <Eye className="w-4 h-4 mr-2" />
                查看详情
              </DropdownMenuItem>
              {canApprove && (
                <>
                  <DropdownMenuItem onClick={() => onApprove?.(topup)}>
                    <Check className="w-4 h-4 mr-2" />
                    批准
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => onReject?.(topup)}>
                    <X className="w-4 h-4 mr-2" />
                    拒绝
                  </DropdownMenuItem>
                </>
              )}
              {!isTerminal && (
                <DropdownMenuItem onClick={() => onCancel?.(topup)}>
                  <Ban className="w-4 h-4 mr-2" />
                  取消
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        );
      },
    },
  ];

  if (error) {
    return <div className="text-red-500">加载失败: {error.message}</div>;
  }

  return (
    <DataTable
      columns={columns}
      data={data}
      isLoading={isLoading}
      emptyMessage="暂无充值申请"
    />
  );
}
```

#### 提交前自检

□ 使用 DataTable 组件
□ 状态使用 StatusBadge（7 状态映射）
□ 金额使用 formatCurrency 格式化
□ 行操作根据角色和状态显示
□ 终态记录隐藏变更操作
□ 无 any 类型

#### 验收标准

- [ ] 使用 DataTable 组件
- [ ] 显示：申请日期、账户、金额、申请人、状态
- [ ] 状态使用 StatusBadge（7 状态）
- [ ] 金额格式化（¥1,234.56）
- [ ] 行操作按钮（根据角色和状态）
- [ ] 空列表显示提示
- [ ] `npm run build` 无错误

---

### TASK-FE-TOP-004: 充值申请表单

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | topups |
| 任务 ID | TASK-FE-TOP-004 |
| 技术栈 | react-hook-form + zod + TanStack Query |
| 优先级 | P1 |
| 预估工时 | 5h |

**前置条件**: TASK-FE-TOP-001 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §4.2 (充值权限表)
- API_SOT.md v9.7 (POST /api/v1/topups)

#### 任务

实现充值申请表单：
1. 账户选择（从 API 获取，非硬编码）
2. 金额输入（必须 > 0）
3. 备注（选填）
4. 表单验证（zod）
5. 提交成功通知（toast）

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/topups/components/TopupRequestForm.tsx` | 表单组件 | 120-150 |
| `src/features/topups/components/TopupFormSchema.ts` | 验证 Schema | 20-30 |
| `src/features/topups/hooks/useTopupMutations.ts` | Mutation Hook | 30-40 |

#### 思考要点（必须先分析）

1. **账户数据**: 账户列表从哪里获取？API 端点是什么？
2. **权限控制**: 哪些角色可以申请充值？
3. **金额验证**: 最小金额是多少？需要什么格式？
4. **表单状态**: 提交中如何禁用按钮？
5. **成功处理**: 提交成功后做什么？关闭弹窗？刷新列表？

#### 约束规则

1. 仅 `pitcher` 和 `account_manager` 可申请充值
2. 账户列表必须从 API 获取（禁止硬编码）
3. 金额必须大于 0
4. 使用 react-hook-form + zod 验证
5. 提交成功显示 toast 通知

#### 边缘情况

| 场景 | 期望行为 | 代码示例 |
|------|---------|---------|
| 账户加载中 | 显示加载提示 | `placeholder="加载中..."` |
| 账户列表为空 | 显示提示 | "暂无可用账户" |
| 金额为 0 | 验证失败 | `z.number().min(1)` |
| 金额为负数 | 验证失败 | 同上 |
| 提交中 | 禁用按钮 | `disabled={isPending}` |

#### 代码参考

**文件 1: src/features/topups/components/TopupFormSchema.ts**
```typescript
import { z } from 'zod';

export const topupFormSchema = z.object({
  ad_account_id: z.number({
    required_error: '请选择广告账户',
  }),
  amount: z.number({
    required_error: '请输入充值金额',
  }).min(1, '充值金额必须大于 0'),
  notes: z.string().optional(),
});

export type TopupFormValues = z.infer<typeof topupFormSchema>;
```

**文件 2: src/features/topups/hooks/useTopupMutations.ts**
```typescript
'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { createTopup } from '../services/topupsApi';
import type { TopupFormValues } from '../components/TopupFormSchema';

export function useCreateTopup(options?: { onSuccess?: () => void }) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TopupFormValues) => createTopup(data),
    onSuccess: () => {
      // 刷新充值列表
      queryClient.invalidateQueries({ queryKey: ['topups'] });
      toast.success('充值申请已提交');
      options?.onSuccess?.();
    },
    onError: (error: Error) => {
      toast.error(error.message || '提交失败，请重试');
    },
  });
}
```

**文件 3: src/features/topups/components/TopupRequestForm.tsx**
```typescript
'use client';

/**
 * 充值申请表单
 * SoT: FRONTEND_PAGE_DESIGN_v2.1.md §4.2
 */
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useQuery } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
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
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { topupFormSchema, type TopupFormValues } from './TopupFormSchema';
import { useCreateTopup } from '../hooks/useTopupMutations';
import { getAdAccounts } from '@/features/ad-accounts/services/adAccountsApi';

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function TopupRequestForm({ open, onOpenChange }: Props) {
  const form = useForm<TopupFormValues>({
    resolver: zodResolver(topupFormSchema),
    defaultValues: {
      amount: 0,
      notes: '',
    },
  });

  // ─── 从 API 获取账户列表（非硬编码）───
  const { data: accountsData, isLoading: accountsLoading } = useQuery({
    queryKey: ['ad-accounts', { page_size: 100 }],
    queryFn: () => getAdAccounts({ page_size: 100 }),
    enabled: open, // 仅弹窗打开时请求
  });

  const createMutation = useCreateTopup({
    onSuccess: () => {
      onOpenChange(false);
      form.reset();
    },
  });

  const onSubmit = (values: TopupFormValues) => {
    createMutation.mutate(values);
  };

  const accounts = accountsData?.items ?? [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>申请充值</DialogTitle>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            {/* 账户选择 */}
            <FormField
              control={form.control}
              name="ad_account_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>广告账户 *</FormLabel>
                  <Select
                    onValueChange={(v) => field.onChange(Number(v))}
                    value={field.value?.toString() || ''}
                    disabled={accountsLoading}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue
                          placeholder={
                            accountsLoading ? '加载中...' : '选择广告账户'
                          }
                        />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {accounts.length === 0 && !accountsLoading && (
                        <div className="p-2 text-sm text-gray-500">
                          暂无可用账户
                        </div>
                      )}
                      {accounts.map((account) => (
                        <SelectItem
                          key={account.id}
                          value={account.id.toString()}
                        >
                          {account.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 金额输入 */}
            <FormField
              control={form.control}
              name="amount"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>充值金额 (CNY) *</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      step="0.01"
                      min="0"
                      placeholder="请输入充值金额"
                      {...field}
                      onChange={(e) => {
                        const value = parseFloat(e.target.value);
                        field.onChange(isNaN(value) ? 0 : value);
                      }}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 备注 */}
            <FormField
              control={form.control}
              name="notes"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>备注</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="选填，充值说明"
                      rows={3}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 按钮 */}
            <div className="flex justify-end gap-2 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                取消
              </Button>
              <Button
                type="submit"
                disabled={createMutation.isPending}
              >
                {createMutation.isPending ? '提交中...' : '提交申请'}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}

export default TopupRequestForm;
```

#### 提交前自检

□ 第一行是 'use client'
□ 账户列表从 API 获取（非硬编码）
□ 使用 zod 验证
□ 金额验证 > 0
□ 提交中禁用按钮
□ 有 toast 成功/失败通知
□ 提交成功后关闭弹窗
□ 提交成功后刷新列表
□ 无 any 类型

#### 验收标准

- [ ] 仅 pitcher 和 account_manager 可申请
- [ ] 账户列表从 API 获取
- [ ] 金额必须大于 0
- [ ] 使用 react-hook-form + zod
- [ ] 提交成功显示 toast
- [ ] 提交中按钮禁用
- [ ] 提交成功关闭弹窗并刷新列表
- [ ] `npm run build` 无错误

---

### TASK-FE-TOP-005: 充值审批操作（7 状态）

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | topups |
| 任务 ID | TASK-FE-TOP-005 |
| 技术栈 | AlertDialog + useMutation |
| 优先级 | P1 |
| 预估工时 | 5h |

**前置条件**: TASK-FE-TOP-003, TASK-FE-COMMON-002 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §4.2 (充值权限表)
- FRONTEND_PAGE_DESIGN_v2.1.md §6.4.2 (角色操作)
- STATE_MACHINE.md v2.9 §7.2 (充值状态机)
- API_SOT.md v9.7 (PATCH /api/v1/topups/{id}/status)

#### 任务

实现充值审批操作组件：
1. pending_review → finance_approve：财务批准
2. pending_review → rejected：财务拒绝
3. finance_approve → paid：财务标记付款
4. paid → completed：系统自动完成
5. 任意非终态 → cancelled：取消充值

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/topups/components/TopupApprovalActions.tsx` | 审批操作按钮 | 80-100 |
| `src/features/topups/components/TopupApprovalDialog.tsx` | 审批确认弹窗 | 60-80 |
| `src/features/topups/components/TopupRejectDialog.tsx` | 拒绝原因弹窗 | 80-100 |

#### 思考要点（必须先分析）

1. **状态流转**: 7 状态流转规则是什么？
2. **权限控制**: 财务、CEO 分别可以执行哪些操作？
3. **拒绝原因**: 拒绝时是否必填原因？
4. **批量操作**: 是否支持批量审批？
5. **确认弹窗**: 哪些操作需要二次确认？

#### 约束规则

1. finance 可执行：approve, reject, mark_paid
2. ceo 可执行大额审批（amount > threshold）
3. 拒绝必须填写原因
4. 所有状态变更需二次确认
5. 使用 AlertDialog 确认

#### 边缘情况

| 场景 | 期望行为 | 代码示例 |
|------|---------|---------|
| 大额充值 | CEO 额外审批 | `amount > 10000` |
| 拒绝无原因 | 验证失败 | `reason.min(1)` |
| 已终态 | 隐藏操作按钮 | completed/rejected/cancelled |
| 操作中 | 禁用按钮 | `disabled={isPending}` |

#### 代码参考

**文件 1: src/features/topups/components/TopupApprovalActions.tsx**
```typescript
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Check, X, Ban, CreditCard } from 'lucide-react';
import { TopupApprovalDialog } from './TopupApprovalDialog';
import { TopupRejectDialog } from './TopupRejectDialog';
import { useHasPermission } from '@/hooks/useHasPermission';
import type { Topup, TopupStatus } from '../types/topup.types';

interface Props {
  topup: Topup;
}

export function TopupApprovalActions({ topup }: Props) {
  const [approveOpen, setApproveOpen] = useState(false);
  const [rejectOpen, setRejectOpen] = useState(false);
  const [cancelOpen, setCancelOpen] = useState(false);
  const [paidOpen, setPaidOpen] = useState(false);

  const isFinance = useHasPermission(['finance', 'ceo', 'admin']);
  const isTerminal = ['completed', 'rejected', 'cancelled'].includes(topup.status);

  if (isTerminal) return null;

  const canApprove = isFinance && topup.status === 'pending_review';
  const canMarkPaid = isFinance && topup.status === 'finance_approve';

  return (
    <div className="flex gap-2">
      {canApprove && (
        <>
          <Button size="sm" onClick={() => setApproveOpen(true)}>
            <Check className="w-4 h-4 mr-1" />
            批准
          </Button>
          <Button size="sm" variant="destructive" onClick={() => setRejectOpen(true)}>
            <X className="w-4 h-4 mr-1" />
            拒绝
          </Button>
        </>
      )}

      {canMarkPaid && (
        <Button size="sm" onClick={() => setPaidOpen(true)}>
          <CreditCard className="w-4 h-4 mr-1" />
          标记付款
        </Button>
      )}

      <Button size="sm" variant="outline" onClick={() => setCancelOpen(true)}>
        <Ban className="w-4 h-4 mr-1" />
        取消
      </Button>

      <TopupApprovalDialog
        topup={topup}
        action="approve"
        open={approveOpen}
        onOpenChange={setApproveOpen}
      />
      <TopupApprovalDialog
        topup={topup}
        action="paid"
        open={paidOpen}
        onOpenChange={setPaidOpen}
      />
      <TopupApprovalDialog
        topup={topup}
        action="cancel"
        open={cancelOpen}
        onOpenChange={setCancelOpen}
      />
      <TopupRejectDialog
        topup={topup}
        open={rejectOpen}
        onOpenChange={setRejectOpen}
      />
    </div>
  );
}
```

**文件 2: src/features/topups/components/TopupApprovalDialog.tsx**
```typescript
'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { updateTopupStatus } from '../services/topupsApi';
import { formatCurrency } from '@/lib/utils';
import type { Topup, TopupStatus } from '../types/topup.types';

type Action = 'approve' | 'paid' | 'cancel';

const ACTION_CONFIG: Record<Action, { title: string; status: TopupStatus; buttonText: string }> = {
  approve: { title: '批准充值', status: 'finance_approve', buttonText: '确认批准' },
  paid: { title: '标记付款', status: 'paid', buttonText: '确认付款' },
  cancel: { title: '取消充值', status: 'cancelled', buttonText: '确认取消' },
};

interface Props {
  topup: Topup;
  action: Action;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function TopupApprovalDialog({ topup, action, open, onOpenChange }: Props) {
  const queryClient = useQueryClient();
  const config = ACTION_CONFIG[action];

  const mutation = useMutation({
    mutationFn: () => updateTopupStatus(topup.id, config.status),
    onSuccess: () => {
      toast.success(`充值已${config.title.replace('充值', '')}`);
      queryClient.invalidateQueries({ queryKey: ['topups'] });
      onOpenChange(false);
    },
    onError: (error: Error) => {
      toast.error(error.message || '操作失败');
    },
  });

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{config.title}</AlertDialogTitle>
          <AlertDialogDescription>
            确定要{config.title.replace('充值', '')}这笔充值申请吗？
            <div className="mt-2 p-3 bg-gray-50 rounded">
              <div>账户: {topup.ad_account_name}</div>
              <div>金额: {formatCurrency(topup.amount)}</div>
              <div>申请人: {topup.applicant_name}</div>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>取消</AlertDialogCancel>
          <AlertDialogAction
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className={action === 'cancel' ? 'bg-red-500 hover:bg-red-600' : ''}
          >
            {mutation.isPending ? '处理中...' : config.buttonText}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
```

**文件 3: src/features/topups/components/TopupRejectDialog.tsx**
```typescript
'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
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
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { updateTopupStatus } from '../services/topupsApi';
import { formatCurrency } from '@/lib/utils';
import type { Topup } from '../types/topup.types';

const rejectSchema = z.object({
  reason: z.string().min(1, '请填写拒绝原因').max(500, '原因不能超过500字'),
});

type RejectValues = z.infer<typeof rejectSchema>;

interface Props {
  topup: Topup;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function TopupRejectDialog({ topup, open, onOpenChange }: Props) {
  const queryClient = useQueryClient();

  const form = useForm<RejectValues>({
    resolver: zodResolver(rejectSchema),
    defaultValues: { reason: '' },
  });

  const mutation = useMutation({
    mutationFn: (reason: string) => updateTopupStatus(topup.id, 'rejected', reason),
    onSuccess: () => {
      toast.success('充值申请已拒绝');
      queryClient.invalidateQueries({ queryKey: ['topups'] });
      onOpenChange(false);
      form.reset();
    },
    onError: (error: Error) => {
      toast.error(error.message || '操作失败');
    },
  });

  const onSubmit = (values: RejectValues) => {
    mutation.mutate(values.reason);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>拒绝充值申请</DialogTitle>
        </DialogHeader>

        <div className="p-3 bg-gray-50 rounded mb-4">
          <div>账户: {topup.ad_account_name}</div>
          <div>金额: {formatCurrency(topup.amount)}</div>
          <div>申请人: {topup.applicant_name}</div>
        </div>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="reason"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>拒绝原因 *</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="请输入拒绝原因"
                      rows={3}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                取消
              </Button>
              <Button
                type="submit"
                variant="destructive"
                disabled={mutation.isPending}
              >
                {mutation.isPending ? '处理中...' : '确认拒绝'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
```

#### 提交前自检

□ 状态流转符合 7 状态机
□ 权限检查完整（finance/ceo）
□ 拒绝必填原因
□ 使用 AlertDialog 确认
□ 操作中禁用按钮
□ 有 toast 通知
□ 成功后刷新列表
□ 无 any 类型

#### 验收标准

- [ ] pending_review → finance_approve：财务批准
- [ ] pending_review → rejected：财务拒绝（必填原因）
- [ ] finance_approve → paid：财务标记付款
- [ ] 任意非终态 → cancelled：取消
- [ ] 终态记录隐藏操作按钮
- [ ] 操作需二次确认
- [ ] `npm run build` 无错误

---

### TASK-FE-TOP-006: 充值详情弹窗

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | topups |
| 任务 ID | TASK-FE-TOP-006 |
| 技术栈 | Dialog + useQuery |
| 优先级 | P1 |
| 预估工时 | 3h |

**前置条件**: TASK-FE-TOP-003 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §7.1 (必须使用的组件)

#### 任务

实现充值详情弹窗：
1. 使用 Dialog 组件
2. 显示充值完整信息
3. 显示审批流程历史
4. 显示操作按钮（根据权限和状态）

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/topups/components/TopupDetailDialog.tsx` | 充值详情弹窗 | 120-160 |
| `src/features/topups/hooks/useTopup.ts` | 单条数据 Hook | 20-30 |

#### 思考要点（必须先分析）

1. **详情字段**: 显示哪些字段？基本信息 + 审批信息？
2. **审批历史**: 如何显示状态流转历史？
3. **操作按钮**: 在详情页也显示操作按钮吗？
4. **状态样式**: 7 状态如何用颜色区分？
5. **加载状态**: 详情加载中如何显示？

#### 约束规则

1. 使用 Dialog 组件（非 Modal）
2. 显示完整充值信息
3. 显示审批流程历史
4. 操作按钮根据权限和状态显示
5. 状态使用 StatusBadge

#### 边缘情况

| 场景 | 期望行为 | 代码示例 |
|------|---------|---------|
| 加载中 | 显示骨架屏 | `<Skeleton />` |
| 加载失败 | 显示错误 | `toast.error()` |
| 无审批历史 | 显示暂无 | "暂无审批记录" |

#### 代码参考

**文件 1: src/features/topups/hooks/useTopup.ts**
```typescript
'use client';

import { useQuery } from '@tanstack/react-query';
import { getTopup } from '../services/topupsApi';

export function useTopup(id: number, enabled = true) {
  return useQuery({
    queryKey: ['topup', id],
    queryFn: () => getTopup(id),
    enabled: enabled && id > 0,
  });
}
```

**文件 2: src/features/topups/components/TopupDetailDialog.tsx**
```typescript
'use client';

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { StatusBadge } from '@/components/common/StatusBadge';
import { Skeleton } from '@/components/ui/skeleton';
import { formatCurrency, formatDate } from '@/lib/utils';
import { useTopup } from '../hooks/useTopup';
import { TopupApprovalActions } from './TopupApprovalActions';
import type { TopupStatus } from '../types/topup.types';

const TOPUP_STATUS_MAP: Record<TopupStatus, { label: string; variant: string }> = {
  draft: { label: '草稿', variant: 'secondary' },
  pending_review: { label: '待审核', variant: 'warning' },
  finance_approve: { label: '财务已批', variant: 'info' },
  paid: { label: '已付款', variant: 'info' },
  completed: { label: '已完成', variant: 'success' },
  rejected: { label: '已拒绝', variant: 'destructive' },
  cancelled: { label: '已取消', variant: 'secondary' },
};

interface Props {
  topupId: number | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function TopupDetailDialog({ topupId, open, onOpenChange }: Props) {
  const { data: topup, isLoading, error } = useTopup(topupId ?? 0, open && topupId !== null);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>充值详情</DialogTitle>
        </DialogHeader>

        {isLoading && (
          <div className="space-y-4">
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-3/4" />
            <Skeleton className="h-6 w-1/2" />
          </div>
        )}

        {error && (
          <div className="text-red-500">加载失败: {error.message}</div>
        )}

        {topup && (
          <div className="space-y-6">
            {/* 基本信息 */}
            <section>
              <h3 className="text-sm font-medium text-gray-500 mb-2">基本信息</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-gray-400">广告账户</label>
                  <div className="font-medium">{topup.ad_account_name}</div>
                </div>
                <div>
                  <label className="text-xs text-gray-400">充值金额</label>
                  <div className="font-medium font-mono">
                    {formatCurrency(topup.amount)}
                  </div>
                </div>
                <div>
                  <label className="text-xs text-gray-400">申请人</label>
                  <div className="font-medium">{topup.applicant_name}</div>
                </div>
                <div>
                  <label className="text-xs text-gray-400">申请时间</label>
                  <div className="font-medium">{formatDate(topup.created_at)}</div>
                </div>
                <div>
                  <label className="text-xs text-gray-400">当前状态</label>
                  <div>
                    <StatusBadge
                      status={topup.status}
                      statusMap={TOPUP_STATUS_MAP}
                    />
                  </div>
                </div>
              </div>
            </section>

            {/* 备注 */}
            {topup.notes && (
              <section>
                <h3 className="text-sm font-medium text-gray-500 mb-2">备注</h3>
                <div className="p-3 bg-gray-50 rounded text-sm">
                  {topup.notes}
                </div>
              </section>
            )}

            {/* 审批信息 */}
            <section>
              <h3 className="text-sm font-medium text-gray-500 mb-2">审批信息</h3>
              <div className="space-y-2 text-sm">
                {topup.approved_at && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">审批时间</span>
                    <span>{formatDate(topup.approved_at)}</span>
                  </div>
                )}
                {topup.paid_at && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">付款时间</span>
                    <span>{formatDate(topup.paid_at)}</span>
                  </div>
                )}
                {topup.completed_at && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">完成时间</span>
                    <span>{formatDate(topup.completed_at)}</span>
                  </div>
                )}
                {topup.rejected_reason && (
                  <div>
                    <span className="text-gray-500">拒绝原因</span>
                    <div className="mt-1 p-2 bg-red-50 text-red-700 rounded">
                      {topup.rejected_reason}
                    </div>
                  </div>
                )}
              </div>
            </section>

            {/* 操作按钮 */}
            <section className="pt-4 border-t">
              <TopupApprovalActions topup={topup} />
            </section>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
```

#### 提交前自检

□ 使用 Dialog 组件（非 Modal）
□ 显示完整充值信息
□ 显示审批时间线
□ 拒绝原因高亮显示
□ 状态使用 StatusBadge
□ 加载状态已处理
□ 错误状态已处理
□ 无 any 类型

#### 验收标准

- [ ] 使用 Dialog 组件
- [ ] 显示充值完整信息
- [ ] 显示审批流程历史
- [ ] 显示操作按钮（根据权限和状态）
- [ ] 加载中显示骨架屏
- [ ] `npm run build` 无错误

---

### TASK-FE-TOP-007: 充值状态流转 UI

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | topups |
| 任务 ID | TASK-FE-TOP-007 |
| 技术栈 | React + Tailwind CSS |
| 优先级 | P1 |
| 预估工时 | 3h |

**前置条件**: TASK-FE-TOP-005 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §6.4.1 (状态流转)
- STATE_MACHINE.md v2.9 §7.2 (充值状态机)

#### 任务

实现充值状态流转可视化：
1. 可视化显示状态流转进度
2. 高亮当前状态
3. 显示每个状态的操作人和时间
4. 终态显示完成/拒绝/取消标记

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/topups/components/TopupStatusFlow.tsx` | 状态流转可视化 | 100-140 |
| `src/features/topups/lib/status-transitions.ts` | 状态转换逻辑 | 40-60 |

#### 思考要点（必须先分析）

1. **流程图**: 如何可视化 7 状态流转？
2. **高亮当前**: 如何标记当前状态？
3. **历史记录**: 每个状态的时间和操作人从哪获取？
4. **终态样式**: 完成/拒绝/取消如何区分显示？
5. **响应式**: 移动端如何展示流程图？

#### 约束规则

1. 状态流转符合 STATE_MACHINE.md v2.9
2. 当前状态高亮显示
3. 已完成状态显示勾选
4. 终态使用不同颜色标记
5. 显示状态变更时间

#### 边缘情况

| 场景 | 期望行为 | 代码示例 |
|------|---------|---------|
| 初始状态 | 只显示第一步 | `status === 'draft'` |
| 被拒绝 | 显示拒绝标记 | 红色 X 标记 |
| 已取消 | 显示取消标记 | 灰色标记 |

#### 代码参考

**文件 1: src/features/topups/lib/status-transitions.ts**
```typescript
import type { TopupStatus } from '../types/topup.types';

export interface StatusStep {
  status: TopupStatus;
  label: string;
  order: number;
}

// 正常流程步骤
export const NORMAL_FLOW_STEPS: StatusStep[] = [
  { status: 'draft', label: '草稿', order: 1 },
  { status: 'pending_review', label: '待审核', order: 2 },
  { status: 'finance_approve', label: '财务已批', order: 3 },
  { status: 'paid', label: '已付款', order: 4 },
  { status: 'completed', label: '已完成', order: 5 },
];

// 获取当前状态在流程中的位置
export function getStatusOrder(status: TopupStatus): number {
  const step = NORMAL_FLOW_STEPS.find((s) => s.status === status);
  return step?.order ?? 0;
}

// 判断状态是否为终态
export function isTerminalStatus(status: TopupStatus): boolean {
  return ['completed', 'rejected', 'cancelled'].includes(status);
}

// 判断状态是否为失败终态
export function isFailedStatus(status: TopupStatus): boolean {
  return ['rejected', 'cancelled'].includes(status);
}
```

**文件 2: src/features/topups/components/TopupStatusFlow.tsx**
```typescript
'use client';

import { Check, X, Ban } from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatDate } from '@/lib/utils';
import {
  NORMAL_FLOW_STEPS,
  getStatusOrder,
  isTerminalStatus,
  isFailedStatus,
} from '../lib/status-transitions';
import type { Topup, TopupStatus } from '../types/topup.types';

interface Props {
  topup: Topup;
  className?: string;
}

export function TopupStatusFlow({ topup, className }: Props) {
  const currentOrder = getStatusOrder(topup.status);
  const isFailed = isFailedStatus(topup.status);

  // 获取状态时间
  const getStatusTime = (status: TopupStatus): string | null => {
    switch (status) {
      case 'draft':
        return topup.created_at;
      case 'pending_review':
        return topup.created_at; // 提交时间
      case 'finance_approve':
        return topup.approved_at ?? null;
      case 'paid':
        return topup.paid_at ?? null;
      case 'completed':
        return topup.completed_at ?? null;
      default:
        return null;
    }
  };

  return (
    <div className={cn('relative', className)}>
      {/* 正常流程 */}
      <div className="flex items-center justify-between">
        {NORMAL_FLOW_STEPS.map((step, index) => {
          const isCompleted = currentOrder > step.order;
          const isCurrent = step.status === topup.status && !isFailed;
          const time = getStatusTime(step.status);

          return (
            <div key={step.status} className="flex flex-col items-center flex-1">
              {/* 连接线 */}
              {index > 0 && (
                <div
                  className={cn(
                    'absolute h-0.5 top-4 -translate-y-1/2',
                    isCompleted ? 'bg-green-500' : 'bg-gray-200'
                  )}
                  style={{
                    left: `${(index - 0.5) * (100 / NORMAL_FLOW_STEPS.length)}%`,
                    width: `${100 / NORMAL_FLOW_STEPS.length}%`,
                  }}
                />
              )}

              {/* 状态点 */}
              <div
                className={cn(
                  'relative z-10 w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium',
                  isCompleted && 'bg-green-500 text-white',
                  isCurrent && 'bg-blue-500 text-white ring-4 ring-blue-200',
                  !isCompleted && !isCurrent && 'bg-gray-200 text-gray-500'
                )}
              >
                {isCompleted ? <Check className="w-4 h-4" /> : step.order}
              </div>

              {/* 状态标签 */}
              <div className="mt-2 text-xs text-center">
                <div className={cn(
                  isCurrent && 'font-semibold text-blue-600',
                  isCompleted && 'text-green-600'
                )}>
                  {step.label}
                </div>
                {time && (
                  <div className="text-gray-400 mt-1">
                    {formatDate(time, 'short')}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* 失败终态标记 */}
      {isFailed && (
        <div className="mt-4 flex items-center justify-center gap-2">
          {topup.status === 'rejected' ? (
            <>
              <div className="w-8 h-8 rounded-full bg-red-500 text-white flex items-center justify-center">
                <X className="w-4 h-4" />
              </div>
              <span className="text-red-600 font-medium">已拒绝</span>
            </>
          ) : (
            <>
              <div className="w-8 h-8 rounded-full bg-gray-500 text-white flex items-center justify-center">
                <Ban className="w-4 h-4" />
              </div>
              <span className="text-gray-600 font-medium">已取消</span>
            </>
          )}
        </div>
      )}
    </div>
  );
}
```

#### 提交前自检

□ 状态流转符合 7 状态机
□ 当前状态高亮显示
□ 已完成状态显示勾选
□ 拒绝显示红色 X
□ 取消显示灰色标记
□ 显示状态变更时间
□ 响应式布局
□ 无 any 类型

#### 验收标准

- [ ] 可视化显示状态流转进度
- [ ] 高亮当前状态
- [ ] 显示每个状态的时间
- [ ] 终态显示完成/拒绝/取消标记
- [ ] 已完成步骤显示勾选
- [ ] `npm run build` 无错误

---

## 4.8 FIN 财务模块

### TASK-FE-FIN-001: 财务中心页面框架

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | finance |
| 任务 ID | TASK-FE-FIN-001 |
| 技术栈 | Next.js 16 + Tabs 布局 |
| 优先级 | P2 |
| 预估工时 | 4h |

**前置条件**: TASK-FE-COMMON-002 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §6.5 (财务中心)
- FRONTEND_PAGE_DESIGN_v2.1.md §5.1 (页面清单)

#### 任务

实现财务中心页面框架：
1. 页面路由 `/finance`（重定向到账本）
2. 子路由：`/finance/ledger`、`/finance/reconciliation`、`/finance/profit`
3. Tab 式布局切换
4. 权限控制（finance, ceo, admin）

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/app/finance/page.tsx` | 财务首页（重定向） | 10-15 |
| `src/app/finance/layout.tsx` | 财务布局 | 30-40 |
| `src/app/finance/ledger/page.tsx` | 账本页 | 15-20 |
| `src/app/finance/reconciliation/page.tsx` | 对账页 | 15-20 |
| `src/app/finance/profit/page.tsx` | 利润页 | 15-20 |
| `src/features/finance/components/FinanceLayout.tsx` | 布局组件 | 60-80 |
| `src/features/finance/types/finance.types.ts` | 类型定义 | 30-40 |

#### 思考要点（必须先分析）

1. **权限控制**: 哪些角色可以访问财务中心？
2. **子页面**: 账本、对账、利润三个子页面如何组织？
3. **Tab 布局**: 如何实现 Tab 切换？
4. **默认页面**: 进入财务中心默认显示哪个子页面？
5. **响应式**: Tab 在移动端如何展示？

#### 约束规则

1. 仅 `finance`、`ceo`、`admin` 可访问
2. 使用 Tabs 组件实现布局
3. 默认重定向到账本页面
4. 每个 Tab 对应独立路由

#### 边缘情况

| 场景 | 期望行为 | 代码示例 |
|------|---------|---------|
| 无权限 | 重定向到首页 | `redirect('/')` |
| 直接访问子路由 | 正常显示 | `/finance/profit` |
| 刷新页面 | 保持当前 Tab | URL 同步 |

#### 代码参考

**文件 1: src/app/finance/page.tsx**
```typescript
import { redirect } from 'next/navigation';

export default function FinancePage() {
  // 默认重定向到账本页面
  redirect('/finance/ledger');
}
```

**文件 2: src/app/finance/layout.tsx**
```typescript
import { FinanceLayout } from '@/features/finance/components/FinanceLayout';

export default function Layout({ children }: { children: React.ReactNode }) {
  return <FinanceLayout>{children}</FinanceLayout>;
}
```

**文件 3: src/features/finance/components/FinanceLayout.tsx**
```typescript
'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useHasPermission } from '@/hooks/useHasPermission';
import { NoPermission } from '@/components/common/NoPermission';

const FINANCE_TABS = [
  { value: 'ledger', label: '账本', href: '/finance/ledger' },
  { value: 'reconciliation', label: '对账', href: '/finance/reconciliation' },
  { value: 'profit', label: '利润', href: '/finance/profit' },
];

interface Props {
  children: React.ReactNode;
}

export function FinanceLayout({ children }: Props) {
  const pathname = usePathname();
  const canAccess = useHasPermission(['finance', 'ceo', 'admin']);

  if (!canAccess) {
    return <NoPermission />;
  }

  // 从 pathname 获取当前 tab
  const currentTab = pathname.split('/').pop() || 'ledger';

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">财务中心</h1>
      </div>

      <Tabs value={currentTab} className="w-full">
        <TabsList>
          {FINANCE_TABS.map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value} asChild>
              <Link href={tab.href}>{tab.label}</Link>
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      <div className="mt-4">{children}</div>
    </div>
  );
}
```

**文件 4: src/features/finance/types/finance.types.ts**
```typescript
// 账本记录
export interface LedgerEntry {
  id: number;
  date: string;
  type: 'topup' | 'spend' | 'reversal';
  amount: number;
  balance: number;
  ad_account_id: number;
  ad_account_name: string;
  description: string;
  created_at: string;
}

// 对账记录
export interface ReconciliationRecord {
  id: number;
  date: string;
  ad_account_id: number;
  ad_account_name: string;
  system_balance: number;
  actual_balance: number;
  difference: number;
  status: 'matched' | 'unmatched' | 'adjusted';
  created_at: string;
}

// 利润统计
export interface ProfitSummary {
  revenue: number;
  cost: number;
  gross_profit: number;
  gross_margin: number;
}

export interface ProfitDetail {
  id: number;
  project_id: number;
  project_name: string;
  date: string;
  revenue: number;
  cost: number;
  gross_profit: number;
}
```

#### 提交前自检

□ 仅 finance, ceo, admin 可访问
□ 使用 Tabs 组件布局
□ 默认重定向到账本
□ Tab 与 URL 同步
□ 无权限显示提示
□ 无 any 类型

#### 验收标准

- [ ] 仅 finance, ceo, admin 可访问
- [ ] 三个子页面：账本、对账、利润
- [ ] Tab 布局切换
- [ ] URL 与 Tab 同步
- [ ] `npm run build` 无错误

---

### TASK-FE-FIN-002: 账本子页面

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | finance |
| 任务 ID | TASK-FE-FIN-002 |
| 技术栈 | DataTable + 筛选器 |
| 优先级 | P2 |
| 预估工时 | 5h |

**前置条件**: TASK-FE-FIN-001 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §6.5.1 (子页面)
- API_SOT.md v9.7 (GET /api/v1/ledger)

#### 任务

实现账本子页面：
1. 显示资金流水记录
2. 支持日期范围筛选
3. 支持类型筛选（充值、消耗、红冲）
4. 显示余额变化

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/finance/components/LedgerPage.tsx` | 账本页面 | 80-100 |
| `src/features/finance/components/LedgerTable.tsx` | 账本表格 | 100-130 |
| `src/features/finance/components/LedgerFilters.tsx` | 筛选器 | 80-100 |
| `src/features/finance/hooks/useLedger.ts` | 数据 Hook | 30-40 |
| `src/features/finance/services/financeApi.ts` | API 调用 | 40-60 |

#### 思考要点（必须先分析）

1. **数据结构**: 账本记录包含哪些字段？
2. **类型筛选**: 充值、消耗、红冲如何区分？
3. **余额计算**: 余额变化如何显示？
4. **排序**: 默认按什么排序？
5. **分页**: 每页多少条？

#### 约束规则

1. 使用 DataTable 组件
2. 金额使用 formatCurrency 格式化
3. 类型使用不同颜色标记
4. 支持日期范围筛选

#### 边缘情况

| 场景 | 期望行为 | 代码示例 |
|------|---------|---------|
| 无数据 | 显示空状态 | "暂无流水记录" |
| 红冲记录 | 红色显示 | `text-red-500` |
| 大额变化 | 高亮显示 | `font-bold` |

#### 代码参考

**文件 1: src/features/finance/services/financeApi.ts**
```typescript
import { apiGet } from '@/lib/api';
import type { LedgerEntry, ReconciliationRecord, ProfitSummary, ProfitDetail } from '../types/finance.types';

export interface LedgerFilters {
  type?: 'topup' | 'spend' | 'reversal';
  date_from?: string;
  date_to?: string;
  ad_account_id?: number;
  page?: number;
  page_size?: number;
}

export interface LedgerResponse {
  items: LedgerEntry[];
  total: number;
  page: number;
  page_size: number;
}

export async function getLedger(filters?: LedgerFilters): Promise<LedgerResponse> {
  const params = new URLSearchParams();
  if (filters?.type) params.set('type', filters.type);
  if (filters?.date_from) params.set('date_from', filters.date_from);
  if (filters?.date_to) params.set('date_to', filters.date_to);
  if (filters?.ad_account_id) params.set('ad_account_id', String(filters.ad_account_id));
  if (filters?.page) params.set('page', String(filters.page));
  if (filters?.page_size) params.set('page_size', String(filters.page_size));

  return apiGet<LedgerResponse>(`/api/v1/ledger?${params.toString()}`);
}
```

**文件 2: src/features/finance/hooks/useLedger.ts**
```typescript
'use client';

import { useQuery } from '@tanstack/react-query';
import { getLedger, type LedgerFilters } from '../services/financeApi';

export function useLedger(filters?: LedgerFilters) {
  return useQuery({
    queryKey: ['ledger', filters],
    queryFn: () => getLedger(filters),
    staleTime: 30_000,
  });
}
```

**文件 3: src/features/finance/components/LedgerTable.tsx**
```typescript
'use client';

import { DataTable } from '@/components/ui/data-table';
import { Badge } from '@/components/ui/badge';
import { formatCurrency, formatDate } from '@/lib/utils';
import type { LedgerEntry } from '../types/finance.types';
import type { ColumnDef } from '@tanstack/react-table';

const TYPE_MAP = {
  topup: { label: '充值', variant: 'success' },
  spend: { label: '消耗', variant: 'warning' },
  reversal: { label: '红冲', variant: 'destructive' },
} as const;

interface Props {
  data: LedgerEntry[];
  isLoading?: boolean;
}

export function LedgerTable({ data, isLoading }: Props) {
  const columns: ColumnDef<LedgerEntry>[] = [
    {
      accessorKey: 'date',
      header: '日期',
      cell: ({ row }) => formatDate(row.original.date),
    },
    {
      accessorKey: 'type',
      header: '类型',
      cell: ({ row }) => {
        const type = row.original.type;
        const config = TYPE_MAP[type];
        return <Badge variant={config.variant}>{config.label}</Badge>;
      },
    },
    {
      accessorKey: 'ad_account_name',
      header: '广告账户',
    },
    {
      accessorKey: 'amount',
      header: '金额',
      cell: ({ row }) => {
        const amount = row.original.amount;
        const isNegative = row.original.type === 'spend' || row.original.type === 'reversal';
        return (
          <span className={`font-mono ${isNegative ? 'text-red-500' : 'text-green-500'}`}>
            {isNegative ? '-' : '+'}{formatCurrency(Math.abs(amount))}
          </span>
        );
      },
    },
    {
      accessorKey: 'balance',
      header: '余额',
      cell: ({ row }) => (
        <span className="font-mono">{formatCurrency(row.original.balance)}</span>
      ),
    },
    {
      accessorKey: 'description',
      header: '说明',
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={data}
      isLoading={isLoading}
      emptyMessage="暂无流水记录"
    />
  );
}
```

#### 提交前自检

□ 使用 DataTable 组件
□ 金额格式化显示
□ 类型用不同颜色标记
□ 支持日期范围筛选
□ 空状态已处理
□ 无 any 类型

#### 验收标准

- [ ] 显示资金流水记录
- [ ] 支持日期范围筛选
- [ ] 支持类型筛选
- [ ] 显示余额变化
- [ ] 红冲记录红色显示
- [ ] `npm run build` 无错误

---

### TASK-FE-FIN-003: 对账子页面

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | finance |
| 任务 ID | TASK-FE-FIN-003 |
| 技术栈 | DataTable + 差异高亮 |
| 优先级 | P2 |
| 预估工时 | 5h |

**前置条件**: TASK-FE-FIN-001 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §6.5.1 (子页面)
- API_SOT.md v9.7 (GET /api/v1/reconciliation)

#### 任务

实现对账子页面：
1. 显示对账记录
2. 支持日期范围筛选
3. 高亮差异数据
4. 支持对账操作

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/finance/components/ReconciliationPage.tsx` | 对账页面 | 80-100 |
| `src/features/finance/components/ReconciliationTable.tsx` | 对账表格 | 120-150 |
| `src/features/finance/components/ReconciliationFilters.tsx` | 筛选器 | 60-80 |
| `src/features/finance/hooks/useReconciliation.ts` | 数据 Hook | 30-40 |

#### 思考要点（必须先分析）

1. **对账逻辑**: 系统余额 vs 实际余额如何比对？
2. **差异高亮**: 差异如何用颜色标记？
3. **对账操作**: 支持哪些对账操作？
4. **状态**: 对账记录有哪些状态？

#### 约束规则

1. 使用 DataTable 组件
2. 差异数据红色高亮
3. 已匹配记录绿色标记
4. 支持日期筛选

#### 边缘情况

| 场景 | 期望行为 | 代码示例 |
|------|---------|---------|
| 差异为 0 | 绿色标记 | `text-green-500` |
| 差异不为 0 | 红色高亮 | `text-red-500 font-bold` |
| 已调账 | 显示调账标记 | Badge "已调账" |

#### 代码参考

**文件 1: src/features/finance/components/ReconciliationTable.tsx**
```typescript
'use client';

import { DataTable } from '@/components/ui/data-table';
import { Badge } from '@/components/ui/badge';
import { formatCurrency, formatDate } from '@/lib/utils';
import type { ReconciliationRecord } from '../types/finance.types';
import type { ColumnDef } from '@tanstack/react-table';

const STATUS_MAP = {
  matched: { label: '已匹配', variant: 'success' },
  unmatched: { label: '待处理', variant: 'warning' },
  adjusted: { label: '已调账', variant: 'secondary' },
} as const;

interface Props {
  data: ReconciliationRecord[];
  isLoading?: boolean;
}

export function ReconciliationTable({ data, isLoading }: Props) {
  const columns: ColumnDef<ReconciliationRecord>[] = [
    {
      accessorKey: 'date',
      header: '日期',
      cell: ({ row }) => formatDate(row.original.date),
    },
    {
      accessorKey: 'ad_account_name',
      header: '广告账户',
    },
    {
      accessorKey: 'system_balance',
      header: '系统余额',
      cell: ({ row }) => (
        <span className="font-mono">{formatCurrency(row.original.system_balance)}</span>
      ),
    },
    {
      accessorKey: 'actual_balance',
      header: '实际余额',
      cell: ({ row }) => (
        <span className="font-mono">{formatCurrency(row.original.actual_balance)}</span>
      ),
    },
    {
      accessorKey: 'difference',
      header: '差异',
      cell: ({ row }) => {
        const diff = row.original.difference;
        const hasDiff = diff !== 0;
        return (
          <span className={`font-mono ${hasDiff ? 'text-red-500 font-bold' : 'text-green-500'}`}>
            {formatCurrency(diff)}
          </span>
        );
      },
    },
    {
      accessorKey: 'status',
      header: '状态',
      cell: ({ row }) => {
        const status = row.original.status;
        const config = STATUS_MAP[status];
        return <Badge variant={config.variant}>{config.label}</Badge>;
      },
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={data}
      isLoading={isLoading}
      emptyMessage="暂无对账记录"
    />
  );
}
```

#### 提交前自检

□ 使用 DataTable 组件
□ 差异数据高亮显示
□ 状态使用 Badge
□ 支持日期筛选
□ 无 any 类型

#### 验收标准

- [ ] 显示对账记录
- [ ] 支持日期范围筛选
- [ ] 高亮差异数据
- [ ] 状态使用 Badge
- [ ] `npm run build` 无错误

---

### TASK-FE-FIN-004: 利润子页面

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | finance |
| 任务 ID | TASK-FE-FIN-004 |
| 技术栈 | DataTable + 汇总卡片 |
| 优先级 | P2 |
| 预估工时 | 5h |

**前置条件**: TASK-FE-FIN-001 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §6.5.1 (子页面)
- FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (查看利润权限)
- API_SOT.md v9.7 (GET /api/v1/profit)

#### 任务

实现利润子页面：
1. 显示毛利、收入、成本汇总
2. 支持按项目/时间维度查看
3. 利润明细表格

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/finance/components/ProfitPage.tsx` | 利润页面 | 100-130 |
| `src/features/finance/components/ProfitSummary.tsx` | 利润汇总 | 60-80 |
| `src/features/finance/components/ProfitTable.tsx` | 利润表格 | 100-130 |
| `src/features/finance/components/ProfitFilters.tsx` | 筛选器 | 60-80 |
| `src/features/finance/hooks/useProfit.ts` | 数据 Hook | 40-50 |

#### 思考要点（必须先分析）

1. **权限控制**: 只有 ceo, finance, admin 可查看
2. **汇总计算**: 毛利 = 收入 - 成本
3. **维度切换**: 按项目还是按时间？
4. **毛利率**: 如何计算和显示？

#### 约束规则

1. 仅 `ceo`、`finance`、`admin` 可查看
2. 显示毛利、收入、成本
3. 支持按项目/时间维度
4. 使用卡片展示汇总

#### 边缘情况

| 场景 | 期望行为 | 代码示例 |
|------|---------|---------|
| 毛利为负 | 红色显示 | `text-red-500` |
| 无数据 | 显示 0 | `¥0.00` |
| 收入为 0 | 毛利率显示 -- | 除数为 0 处理 |

#### 代码参考

**文件 1: src/features/finance/components/ProfitSummary.tsx**
```typescript
'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatCurrency, formatPercent } from '@/lib/utils';
import { TrendingUp, TrendingDown, DollarSign, MinusCircle } from 'lucide-react';
import type { ProfitSummary as ProfitSummaryType } from '../types/finance.types';

interface Props {
  data?: ProfitSummaryType;
  isLoading?: boolean;
}

export function ProfitSummary({ data, isLoading }: Props) {
  const cards = [
    {
      title: '总收入',
      value: data?.revenue ?? 0,
      icon: DollarSign,
      color: 'text-blue-500',
    },
    {
      title: '总成本',
      value: data?.cost ?? 0,
      icon: MinusCircle,
      color: 'text-orange-500',
    },
    {
      title: '毛利',
      value: data?.gross_profit ?? 0,
      icon: data?.gross_profit && data.gross_profit >= 0 ? TrendingUp : TrendingDown,
      color: data?.gross_profit && data.gross_profit >= 0 ? 'text-green-500' : 'text-red-500',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {cards.map((card) => (
        <Card key={card.title}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{card.title}</CardTitle>
            <card.icon className={`h-4 w-4 ${card.color}`} />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${card.color}`}>
              {isLoading ? '--' : formatCurrency(card.value)}
            </div>
            {card.title === '毛利' && data && (
              <p className="text-xs text-muted-foreground">
                毛利率: {data.revenue > 0 ? formatPercent(data.gross_margin) : '--'}
              </p>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
```

**文件 2: src/features/finance/components/ProfitTable.tsx**
```typescript
'use client';

import { DataTable } from '@/components/ui/data-table';
import { formatCurrency, formatDate } from '@/lib/utils';
import type { ProfitDetail } from '../types/finance.types';
import type { ColumnDef } from '@tanstack/react-table';

interface Props {
  data: ProfitDetail[];
  isLoading?: boolean;
}

export function ProfitTable({ data, isLoading }: Props) {
  const columns: ColumnDef<ProfitDetail>[] = [
    {
      accessorKey: 'date',
      header: '日期',
      cell: ({ row }) => formatDate(row.original.date),
    },
    {
      accessorKey: 'project_name',
      header: '项目',
    },
    {
      accessorKey: 'revenue',
      header: '收入',
      cell: ({ row }) => (
        <span className="font-mono text-blue-600">
          {formatCurrency(row.original.revenue)}
        </span>
      ),
    },
    {
      accessorKey: 'cost',
      header: '成本',
      cell: ({ row }) => (
        <span className="font-mono text-orange-600">
          {formatCurrency(row.original.cost)}
        </span>
      ),
    },
    {
      accessorKey: 'gross_profit',
      header: '毛利',
      cell: ({ row }) => {
        const profit = row.original.gross_profit;
        return (
          <span className={`font-mono font-bold ${profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {formatCurrency(profit)}
          </span>
        );
      },
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={data}
      isLoading={isLoading}
      emptyMessage="暂无利润数据"
    />
  );
}
```

#### 提交前自检

□ 仅 ceo, finance, admin 可查看
□ 显示汇总卡片
□ 毛利为负红色显示
□ 支持维度筛选
□ 无 any 类型

#### 验收标准

- [ ] 仅 ceo, finance, admin 可查看
- [ ] 显示毛利、收入、成本
- [ ] 支持按项目/时间维度查看
- [ ] 毛利为负红色显示
- [ ] `npm run build` 无错误

---

### TASK-FE-FIN-005: 财务权限守卫

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | finance |
| 任务 ID | TASK-FE-FIN-005 |
| 技术栈 | React Context + HOC |
| 优先级 | P2 |
| 预估工时 | 3h |

**前置条件**: TASK-FE-FIN-001, TASK-FE-COMMON-002 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §6.5.2 (访问控制)

#### 任务

实现财务权限守卫：
1. 封装财务模块权限检查
2. 无权限显示 AccessDenied 组件
3. 支持重定向到首页

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/finance/components/FinanceGuard.tsx` | 财务权限守卫 | 40-60 |

#### 代码参考

**文件 1: src/features/finance/components/FinanceGuard.tsx**
```typescript
'use client';

import { useRouter } from 'next/navigation';
import { useHasPermission } from '@/hooks/useHasPermission';
import { NoPermission } from '@/components/common/NoPermission';

interface Props {
  children: React.ReactNode;
  redirectOnDeny?: boolean;
}

export function FinanceGuard({ children, redirectOnDeny = false }: Props) {
  const router = useRouter();
  const canAccess = useHasPermission(['finance', 'ceo', 'admin']);

  if (!canAccess) {
    if (redirectOnDeny) {
      router.push('/');
      return null;
    }
    return <NoPermission message="您没有权限访问财务中心" />;
  }

  return <>{children}</>;
}
```

#### 验收标准

- [ ] 封装财务模块权限检查
- [ ] 无权限显示 AccessDenied 组件
- [ ] 支持重定向到首页
- [ ] `npm run build` 无错误

---

## 4.9 USER 用户模块

### TASK-FE-USER-001: 用户列表页

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | users |
| 任务 ID | TASK-FE-USER-001 |
| 技术栈 | Next.js 16 + TanStack Query + DataTable |
| 优先级 | P2 |
| 预估工时 | 4h |

**前置条件**: TASK-FE-COMMON-005 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §5.1 (页面清单)
- FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (权限矩阵)
- API_SOT.md v9.7 (GET /api/v1/users)

#### 任务

实现用户管理列表页：
1. 页面路由 `/users`
2. 仅 admin 可访问
3. 列表显示用户信息
4. 支持筛选和搜索

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/app/users/page.tsx` | 路由页面 | 15-20 |
| `src/features/users/components/UsersPage.tsx` | 页面组件 | 80-100 |
| `src/features/users/hooks/useUsers.ts` | 列表数据 Hook | 30-40 |
| `src/features/users/services/usersApi.ts` | API 调用 | 50-70 |
| `src/features/users/types/user.types.ts` | 类型定义 | 30-40 |

#### 思考要点（必须先分析）

1. **权限控制**: 仅 admin 可访问
2. **双层角色**: 技术层角色 + 项目负责人标记
3. **列表字段**: 用户名、角色、项目负责人标记、状态
4. **操作按钮**: 编辑、启用/停用

#### 约束规则

1. 仅 `admin` 可访问
2. 使用 DataTable 组件
3. 角色只显示 4 个技术层角色
4. 项目负责人单独标记

#### 代码参考

**文件 1: src/features/users/types/user.types.ts**
```typescript
export type UserRole = 'ceo' | 'finance' | 'pitcher' | 'account_manager';

export interface User {
  id: number;
  username: string;
  email?: string;
  role: UserRole;
  is_project_owner: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UsersResponse {
  items: User[];
  total: number;
  page: number;
  page_size: number;
}

export interface UsersFilters {
  role?: UserRole;
  is_active?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
}
```

**文件 2: src/features/users/services/usersApi.ts**
```typescript
import { apiGet, apiPost, apiPut, apiPatch } from '@/lib/api';
import type { User, UsersResponse, UsersFilters, UserRole } from '../types/user.types';

export async function getUsers(filters?: UsersFilters): Promise<UsersResponse> {
  const params = new URLSearchParams();
  if (filters?.role) params.set('role', filters.role);
  if (filters?.is_active !== undefined) params.set('is_active', String(filters.is_active));
  if (filters?.search) params.set('search', filters.search);
  if (filters?.page) params.set('page', String(filters.page));
  if (filters?.page_size) params.set('page_size', String(filters.page_size));

  return apiGet<UsersResponse>(`/api/v1/users?${params.toString()}`);
}

export async function createUser(data: {
  username: string;
  password: string;
  role: UserRole;
  is_project_owner?: boolean;
}): Promise<User> {
  return apiPost<User>('/api/v1/users', data);
}

export async function updateUser(id: number, data: Partial<User>): Promise<User> {
  return apiPut<User>(`/api/v1/users/${id}`, data);
}

export async function toggleUserStatus(id: number, is_active: boolean): Promise<User> {
  return apiPatch<User>(`/api/v1/users/${id}/status`, { is_active });
}
```

**文件 3: src/features/users/components/UsersPage.tsx**
```typescript
'use client';

import { useState } from 'react';
import { useUsers } from '../hooks/useUsers';
import { UsersTable } from './UsersTable';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import { UserFormDialog } from './UserFormDialog';
import { useHasPermission } from '@/hooks/useHasPermission';
import { NoPermission } from '@/components/common/NoPermission';
import type { UsersFilters } from '../types/user.types';

export function UsersPage() {
  const [createOpen, setCreateOpen] = useState(false);
  const [filters, setFilters] = useState<UsersFilters>({});

  const isAdmin = useHasPermission(['admin']);
  const { data, isLoading, error } = useUsers(filters);

  if (!isAdmin) {
    return <NoPermission />;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">用户管理</h1>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          新建用户
        </Button>
      </div>

      <UsersTable
        data={data?.items ?? []}
        isLoading={isLoading}
        error={error}
      />

      <UserFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
      />
    </div>
  );
}
```

#### 验收标准

- [ ] 仅 admin 可访问
- [ ] 使用 DataTable 组件
- [ ] 显示：用户名、角色、项目负责人标记、状态
- [ ] 新建按钮打开表单
- [ ] `npm run build` 无错误

---

### TASK-FE-USER-002: 用户表格组件

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | users |
| 任务 ID | TASK-FE-USER-002 |
| 技术栈 | DataTable + Badge |
| 优先级 | P2 |
| 预估工时 | 3h |

**前置条件**: TASK-FE-USER-001 已完成

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/users/components/UsersTable.tsx` | 用户表格 | 100-130 |

#### 代码参考

**文件 1: src/features/users/components/UsersTable.tsx**
```typescript
'use client';

import { DataTable } from '@/components/ui/data-table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { MoreHorizontal, Pencil, Power, Star } from 'lucide-react';
import type { User, UserRole } from '../types/user.types';
import type { ColumnDef } from '@tanstack/react-table';

const ROLE_MAP: Record<UserRole, string> = {
  ceo: '老板',
  finance: '财务',
  pitcher: '投手',
  account_manager: '户管',
};

interface Props {
  data: User[];
  isLoading?: boolean;
  error?: Error | null;
  onEdit?: (user: User) => void;
  onToggleStatus?: (user: User) => void;
}

export function UsersTable({ data, isLoading, error, onEdit, onToggleStatus }: Props) {
  const columns: ColumnDef<User>[] = [
    {
      accessorKey: 'username',
      header: '用户名',
    },
    {
      accessorKey: 'role',
      header: '角色',
      cell: ({ row }) => (
        <Badge variant="outline">{ROLE_MAP[row.original.role]}</Badge>
      ),
    },
    {
      accessorKey: 'is_project_owner',
      header: '项目负责人',
      cell: ({ row }) =>
        row.original.is_project_owner ? (
          <Badge variant="secondary">
            <Star className="w-3 h-3 mr-1" />
            项目负责人
          </Badge>
        ) : (
          '-'
        ),
    },
    {
      accessorKey: 'is_active',
      header: '状态',
      cell: ({ row }) => (
        <Badge variant={row.original.is_active ? 'success' : 'secondary'}>
          {row.original.is_active ? '启用' : '停用'}
        </Badge>
      ),
    },
    {
      id: 'actions',
      cell: ({ row }) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <MoreHorizontal className="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => onEdit?.(row.original)}>
              <Pencil className="w-4 h-4 mr-2" />
              编辑
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onToggleStatus?.(row.original)}>
              <Power className="w-4 h-4 mr-2" />
              {row.original.is_active ? '停用' : '启用'}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  if (error) {
    return <div className="text-red-500">加载失败: {error.message}</div>;
  }

  return (
    <DataTable
      columns={columns}
      data={data}
      isLoading={isLoading}
      emptyMessage="暂无用户数据"
    />
  );
}
```

#### 验收标准

- [ ] 使用 DataTable 组件
- [ ] 显示：用户名、角色、项目负责人标记、状态
- [ ] 行操作按钮
- [ ] `npm run build` 无错误

---

### TASK-FE-USER-003: 用户创建/编辑表单

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | users |
| 任务 ID | TASK-FE-USER-003 |
| 技术栈 | react-hook-form + zod + Dialog |
| 优先级 | P2 |
| 预估工时 | 4h |

**前置条件**: TASK-FE-USER-001 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (权限矩阵)
- FRONTEND_PAGE_DESIGN_v2.1.md §2 (双层角色架构)
- API_SOT.md v9.7 (POST/PUT /api/v1/users)

#### 任务

实现用户创建/编辑表单：
1. 必填字段：用户名、密码、角色
2. 选填字段：是否项目负责人
3. 角色选项仅包含 4 个技术层角色

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/users/components/UserForm.tsx` | 用户表单 | 100-140 |
| `src/features/users/components/UserFormSchema.ts` | 验证 Schema | 25-35 |
| `src/features/users/components/UserFormDialog.tsx` | 表单弹窗 | 60-80 |
| `src/features/users/hooks/useUserMutations.ts` | 变更 Hook | 50-70 |

#### 思考要点（必须先分析）

1. **为什么角色枚举只用 4 个技术层值？**
   - 数据库存储技术层角色 (ceo/finance/pitcher/account_manager)
   - UI 展示转换为业务层名称（老板/财务/投手/户管）

2. **创建用户时 is_project_owner 如何设置？**
   - 表单中独立 Switch 控件，不属于 role 字段
   - 任何角色都可以标记为项目负责人

3. **编辑用户时密码是否可选？**
   - 编辑模式下密码字段隐藏（条件渲染）
   - 如需修改密码应使用独立的"重置密码"功能

4. **如何防止删除/停用最后一个 admin？**
   - 后端校验返回 400 错误
   - 前端 disabled 按钮 + tooltip 提示

5. **角色修改是否需要特殊权限？**
   - 仅 admin 可创建/编辑用户
   - 禁止修改自己的角色

#### 边缘情况（Edge Cases）

| 场景 | 处理方式 |
|------|---------|
| 用户名已存在 | 后端 422，前端 toast 提示"用户名已存在" |
| 停用当前登录用户 | 按钮 disabled + tooltip "无法停用当前账户" |
| 停用最后一个 admin | 按钮 disabled + 警告"系统需保留至少一个管理员" |
| 角色降级警告 | 确认弹窗提示"降级后将失去 XXX 权限" |
| 密码强度不足 | zod 验证失败，显示 FormMessage |

#### 代码参考

**文件 1: src/features/users/components/UserFormSchema.ts**
```typescript
import { z } from 'zod';

export const userFormSchema = z.object({
  username: z.string().min(2, '用户名至少2个字符').max(50, '用户名不能超过50字'),
  password: z.string().min(6, '密码至少6个字符').optional(),
  role: z.enum(['ceo', 'finance', 'pitcher', 'account_manager'], {
    required_error: '请选择角色',
  }),
  is_project_owner: z.boolean().default(false),
});

export type UserFormValues = z.infer<typeof userFormSchema>;
```

**文件 2: src/features/users/components/UserFormDialog.tsx**
```typescript
'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
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
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { userFormSchema, type UserFormValues } from './UserFormSchema';
import { useCreateUser, useUpdateUser } from '../hooks/useUserMutations';
import type { User } from '../types/user.types';

const ROLE_OPTIONS = [
  { value: 'ceo', label: '老板' },
  { value: 'finance', label: '财务' },
  { value: 'pitcher', label: '投手' },
  { value: 'account_manager', label: '户管' },
];

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  user?: User;
}

export function UserFormDialog({ open, onOpenChange, user }: Props) {
  const isEdit = Boolean(user);

  const form = useForm<UserFormValues>({
    resolver: zodResolver(userFormSchema),
    defaultValues: user ?? {
      username: '',
      password: '',
      role: undefined,
      is_project_owner: false,
    },
  });

  const createMutation = useCreateUser({
    onSuccess: () => {
      onOpenChange(false);
      form.reset();
    },
  });

  const updateMutation = useUpdateUser({
    onSuccess: () => {
      onOpenChange(false);
    },
  });

  const isPending = createMutation.isPending || updateMutation.isPending;

  const onSubmit = (values: UserFormValues) => {
    if (isEdit && user) {
      updateMutation.mutate({ id: user.id, data: values });
    } else {
      createMutation.mutate(values as Required<UserFormValues>);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{isEdit ? '编辑用户' : '新建用户'}</DialogTitle>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="username"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>用户名 *</FormLabel>
                  <FormControl>
                    <Input placeholder="请输入用户名" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {!isEdit && (
              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>密码 *</FormLabel>
                    <FormControl>
                      <Input type="password" placeholder="请输入密码" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}

            <FormField
              control={form.control}
              name="role"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>角色 *</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="请选择角色" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {ROLE_OPTIONS.map((opt) => (
                        <SelectItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="is_project_owner"
              render={({ field }) => (
                <FormItem className="flex items-center justify-between rounded-lg border p-3">
                  <div>
                    <FormLabel>项目负责人</FormLabel>
                    <p className="text-sm text-muted-foreground">
                      标记为项目负责人可以审核日报
                    </p>
                  </div>
                  <FormControl>
                    <Switch checked={field.value} onCheckedChange={field.onChange} />
                  </FormControl>
                </FormItem>
              )}
            />

            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                取消
              </Button>
              <Button type="submit" disabled={isPending}>
                {isPending ? '提交中...' : isEdit ? '保存' : '创建'}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
```

#### 验收标准

- [ ] 仅 ceo 和 admin 可创建用户
- [ ] 必填：用户名、密码、角色
- [ ] 角色选项仅 4 个技术层角色
- [ ] 项目负责人切换开关
- [ ] `npm run build` 无错误

---

### TASK-FE-USER-004: 用户角色分配

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | users |
| 任务 ID | TASK-FE-USER-004 |
| 技术栈 | Select + Switch |
| 优先级 | P2 |
| 预估工时 | 3h |

**前置条件**: TASK-FE-USER-003 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §2 (双层角色架构)

#### 任务

实现用户角色分配组件：
1. 技术层角色下拉选择（4 个选项）
2. 项目负责人切换开关
3. 角色变更需确认

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/users/components/UserRoleSelect.tsx` | 角色选择器 | 50-70 |
| `src/features/users/components/UserProjectOwnerToggle.tsx` | 项目负责人切换 | 40-60 |

#### 验收标准

- [ ] 技术层角色下拉选择（4 个选项）
- [ ] 项目负责人切换开关
- [ ] 角色变更需确认
- [ ] `npm run build` 无错误

---

### TASK-FE-USER-005: 用户停用/启用操作

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | users |
| 任务 ID | TASK-FE-USER-005 |
| 技术栈 | AlertDialog + useMutation |
| 优先级 | P2 |
| 预估工时 | 3h |

**前置条件**: TASK-FE-USER-002 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (权限矩阵)

#### 任务

实现用户状态切换：
1. 停用/启用确认弹窗
2. 停用后用户无法登录

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/users/components/UserStatusToggle.tsx` | 用户状态切换 | 60-80 |

#### 代码参考

**文件 1: src/features/users/components/UserStatusToggle.tsx**
```typescript
'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { toggleUserStatus } from '../services/usersApi';
import type { User } from '../types/user.types';

interface Props {
  user: User;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function UserStatusToggle({ user, open, onOpenChange }: Props) {
  const queryClient = useQueryClient();
  const newStatus = !user.is_active;
  const actionText = newStatus ? '启用' : '停用';

  const mutation = useMutation({
    mutationFn: () => toggleUserStatus(user.id, newStatus),
    onSuccess: () => {
      toast.success(`用户已${actionText}`);
      queryClient.invalidateQueries({ queryKey: ['users'] });
      onOpenChange(false);
    },
    onError: (error: Error) => {
      toast.error(error.message || `${actionText}失败`);
    },
  });

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>确认{actionText}用户</AlertDialogTitle>
          <AlertDialogDescription>
            您确定要{actionText}用户"{user.username}"吗？
            {!newStatus && (
              <span className="block mt-2 text-red-600">
                停用后该用户将无法登录系统
              </span>
            )}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>取消</AlertDialogCancel>
          <AlertDialogAction
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className={!newStatus ? 'bg-red-500 hover:bg-red-600' : ''}
          >
            {mutation.isPending ? '处理中...' : `确认${actionText}`}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
```

#### 验收标准

- [ ] 仅 ceo 和 admin 可操作
- [ ] 停用用户需确认弹窗
- [ ] 停用后用户无法登录
- [ ] `npm run build` 无错误

---

## 4.10 SET 系统设置模块

### TASK-FE-SET-001: 系统设置页面框架

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | settings |
| 任务 ID | TASK-FE-SET-001 |
| 技术栈 | Next.js 16 + Tabs |
| 优先级 | P3 |
| 预估工时 | 3h |

**前置条件**: TASK-FE-COMMON-002 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §5.1 (页面清单)
- FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (权限矩阵)

#### 任务

实现系统设置页面框架：
1. 页面路由 `/settings`
2. 仅 admin 可访问
3. Tab 式布局支持多个配置区域

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/app/settings/page.tsx` | 系统设置页 | 15-20 |
| `src/features/settings/components/SettingsPage.tsx` | 页面组件 | 60-80 |
| `src/features/settings/types/settings.types.ts` | 类型定义 | 20-30 |

#### 代码参考

**文件 1: src/features/settings/components/SettingsPage.tsx**
```typescript
'use client';

import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useHasPermission } from '@/hooks/useHasPermission';
import { NoPermission } from '@/components/common/NoPermission';
import { BasicSettings } from './BasicSettings';
import { TopupThresholdSettings } from './TopupThresholdSettings';

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState('basic');
  const isAdmin = useHasPermission(['admin']);

  if (!isAdmin) {
    return <NoPermission />;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">系统设置</h1>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="basic">基础配置</TabsTrigger>
          <TabsTrigger value="topup">充值阈值</TabsTrigger>
        </TabsList>

        <TabsContent value="basic" className="mt-4">
          <BasicSettings />
        </TabsContent>

        <TabsContent value="topup" className="mt-4">
          <TopupThresholdSettings />
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

#### 验收标准

- [ ] 仅 admin 可访问
- [ ] Tab 式布局支持多个配置区域
- [ ] `npm run build` 无错误

---

### TASK-FE-SET-002: 基础配置表单

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | settings |
| 任务 ID | TASK-FE-SET-002 |
| 技术栈 | react-hook-form + zod |
| 优先级 | P3 |
| 预估工时 | 3h |

**前置条件**: TASK-FE-SET-001 已完成

#### 任务

实现基础配置表单：
1. 系统名称配置
2. 日期格式配置
3. 保存成功显示 toast

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/settings/components/BasicSettings.tsx` | 基础配置 | 80-100 |
| `src/features/settings/components/BasicSettingsForm.tsx` | 配置表单 | 60-80 |

#### 验收标准

- [ ] 系统名称配置
- [ ] 日期格式配置
- [ ] 保存成功显示 toast
- [ ] `npm run build` 无错误

---

### TASK-FE-SET-003: 充值阈值配置

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | settings |
| 任务 ID | TASK-FE-SET-003 |
| 技术栈 | react-hook-form + zod |
| 优先级 | P3 |
| 预估工时 | 4h |

**前置条件**: TASK-FE-SET-001 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §4.2 (充值权限表)

#### 任务

实现充值阈值配置：
1. 大额充值阈值配置（默认 ¥50,000）
2. 配置变更需确认
3. 保存成功显示 toast

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/settings/components/TopupThresholdSettings.tsx` | 阈值配置 | 80-100 |
| `src/features/settings/components/TopupThresholdForm.tsx` | 配置表单 | 60-80 |

#### 代码参考

**文件 1: src/features/settings/components/TopupThresholdSettings.tsx**
```typescript
'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormDescription,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { apiGet, apiPut } from '@/lib/api';

const thresholdSchema = z.object({
  large_amount_threshold: z.number().min(0, '阈值不能为负数'),
});

type ThresholdValues = z.infer<typeof thresholdSchema>;

export function TopupThresholdSettings() {
  const queryClient = useQueryClient();

  const { data: settings } = useQuery({
    queryKey: ['settings', 'topup-threshold'],
    queryFn: () => apiGet<{ large_amount_threshold: number }>('/api/v1/settings/topup-threshold'),
  });

  const form = useForm<ThresholdValues>({
    resolver: zodResolver(thresholdSchema),
    defaultValues: {
      large_amount_threshold: settings?.large_amount_threshold ?? 50000,
    },
  });

  const mutation = useMutation({
    mutationFn: (data: ThresholdValues) => apiPut('/api/v1/settings/topup-threshold', data),
    onSuccess: () => {
      toast.success('充值阈值已更新');
      queryClient.invalidateQueries({ queryKey: ['settings', 'topup-threshold'] });
    },
    onError: (error: Error) => {
      toast.error(error.message || '保存失败');
    },
  });

  const onSubmit = (values: ThresholdValues) => {
    mutation.mutate(values);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>充值阈值配置</CardTitle>
        <CardDescription>
          超过阈值的充值申请需要 CEO 审批
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="large_amount_threshold"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>大额充值阈值 (¥)</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      placeholder="50000"
                      {...field}
                      onChange={(e) => field.onChange(Number(e.target.value))}
                    />
                  </FormControl>
                  <FormDescription>
                    超过此金额的充值申请需要 CEO 额外审批
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? '保存中...' : '保存设置'}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
```

#### 验收标准

- [ ] 大额充值阈值配置（默认 ¥50,000）
- [ ] 配置变更需确认
- [ ] 保存成功显示 toast
- [ ] `npm run build` 无错误

---

# Part 5: 快速参考

## 状态机速查表

```
┌─────────────────────────────────────────────────────────────────┐
│ 日报状态 (Phase 1: 3 个)                                         │
├─────────────────────────────────────────────────────────────────┤
│ raw_submitted ──────▶ trend_ok ──────▶ final_confirmed          │
│    (已提交)           (已审核)           (已确认)                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 账户状态 (6 个)                                                  │
├─────────────────────────────────────────────────────────────────┤
│ new ──▶ testing ──▶ active ──▶ suspended ──▶ dead               │
│                        │                                         │
│                        └──────────────────▶ archived             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 充值状态 (7 个)                                                  │
├─────────────────────────────────────────────────────────────────┤
│ draft ──▶ pending_review ──▶ finance_approve ──▶ paid ──▶ completed │
│                 │                                    │           │
│                 └──▶ rejected                        └──▶ cancelled │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 项目状态 (4 个)                                                  │
├─────────────────────────────────────────────────────────────────┤
│ draft ──▶ active ◀──▶ suspended ──▶ archived                    │
└─────────────────────────────────────────────────────────────────┘
```

## 权限矩阵速查表

| 操作 | CEO | 项目负责人 | 财务 | 投手 | 户管 | Admin |
|------|-----|-----------|------|------|------|-------|
| 提交日报 | - | - | - | ✅ | - | - |
| 审核日报 | - | ✅ | - | - | - | ✅ |
| 创建项目 | ✅ | - | - | - | - | ✅ |
| 创建账户 | - | - | - | - | ✅ | ✅ |
| 申请充值 | - | - | - | ✅ | ✅ | - |
| 审批充值 | - | - | ✅ | - | - | ✅ |
| 大额审批 | ✅ | - | - | - | - | - |
| 查看财务 | ✅ | - | ✅ | - | - | ✅ |
| 管理用户 | - | - | - | - | - | ✅ |

## 组件使用模式

### DataTable 使用
```typescript
import { DataTable } from '@/components/ui/data-table';

<DataTable
  columns={columns}
  data={data?.items ?? []}
  loading={isLoading}
  pagination={{
    page: params.page ?? 1,
    pageSize: params.page_size ?? 20,
    total: data?.total ?? 0,
    onPageChange: (page) => setParams({ ...params, page }),
  }}
/>
```

### StatusBadge 使用
```typescript
import { StatusBadge } from '@/components/ui/status-badge';

<StatusBadge type="daily_report" status="raw_submitted" />
<StatusBadge type="ad_account" status="active" />
<StatusBadge type="topup" status="pending_review" />
<StatusBadge type="project" status="draft" />
```

### Form 使用
```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from '@/components/ui/form';

const form = useForm<FormValues>({
  resolver: zodResolver(schema),
  defaultValues: { ... },
});

<Form {...form}>
  <form onSubmit={form.handleSubmit(onSubmit)}>
    <FormField
      control={form.control}
      name="fieldName"
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

### Dialog 使用
```typescript
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';

<Dialog open={open} onOpenChange={onOpenChange}>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>标题</DialogTitle>
    </DialogHeader>
    {/* 内容 */}
  </DialogContent>
</Dialog>
```

## API 调用模式

```typescript
// GET 请求
import { apiGet } from '@/lib/api';
const data = await apiGet<User[]>('/api/v1/users');

// POST 请求
import { apiPost } from '@/lib/api';
const result = await apiPost<User>('/api/v1/users', { name: 'test' });

// 文件上传
import { apiUpload } from '@/lib/api';
const result = await apiUpload('/api/v1/upload', formData);

// 分页请求
import { apiGet, type PaginatedResponse } from '@/lib/api';
const data = await apiGet<PaginatedResponse<Item>>('/api/v1/items?page=1');
```

## 常见问题诊断

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| 页面空白 | 缺少 'use client' | 添加 'use client' 到第一行 |
| 类型报错 | 使用了 any | 定义具体类型 |
| 表格不显示 | 使用了原生 table | 改用 DataTable |
| 状态颜色错误 | 自定义了 Badge | 改用 StatusBadge |
| API 401 | Token 过期 | 检查 apiGet 是否带 token |
| 权限不对 | 硬编码了角色 | 改用 can() 检查 |
| 数据不刷新 | queryKey 不对 | 检查 invalidateQueries |

---

## 4.1.3 COMMON 模块补充提示词

### TASK-FE-COMMON-003: 状态配置与 StatusBadge

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | common |
| 任务 ID | TASK-FE-COMMON-003 |
| 技术栈 | TypeScript + shadcn/ui |
| 优先级 | P0 |
| 预估工时 | 3h |

**前置条件**: TASK-FE-COMMON-001 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §7.2 (StatusBadge 配置)
- STATE_MACHINE.md v2.9 §7 (状态定义)

#### 任务

实现状态标签组件和配置，包括：
1. StatusBadge 通用组件（支持多种状态类型）
2. 状态变体配置（颜色、标签、图标）
3. 支持 4 种实体状态：日报、账户、充值、项目

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/components/ui/status-badge.tsx` | 状态标签组件 | 60-80 |
| `src/lib/constants/status-variants.ts` | 状态变体配置 | 80-100 |

#### 思考要点（必须先分析）

1. **状态类型区分**: 如何用单一组件支持日报/账户/充值/项目四种状态？
2. **颜色语义**: success/warning/error/info 各用于什么场景？
3. **Phase 1 限制**: 日报状态为什么只有 3 个？UI 如何体现？
4. **size 属性**: sm/md/lg 三种尺寸的使用场景？
5. **类型安全**: 如何确保传入的 status 值有效？

#### 约束规则

1. 日报状态仅支持 3 个值（Phase 1）
2. 账户状态支持 6 个值
3. 充值状态支持 7 个值
4. 项目状态支持 4 个值
5. 必须使用 shadcn/ui 的 Badge 组件作为基础
6. 每个状态必须有对应的中文标签

#### 边缘情况

| 场景 | 期望行为 | 代码示例 |
|------|---------|---------|
| 无效状态值 | 显示默认样式 | `status="unknown"` → 灰色标签 |
| 类型不匹配 | TypeScript 报错 | `type="daily_report" status="active"` → TS 报错 |
| size 未传 | 使用默认 md | `<StatusBadge type="daily_report" status="trend_ok" />` |

#### 代码参考

**文件 1: src/components/ui/status-badge.tsx**
```typescript
'use client';

/**
 * 状态标签组件
 * SoT: STATE_MACHINE.md v2.9 §7
 */
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import {
  DAILY_REPORT_STATUS_CONFIG,
  AD_ACCOUNT_STATUS_CONFIG,
  TOPUP_STATUS_CONFIG,
  PROJECT_STATUS_CONFIG,
} from '@/lib/constants/status-variants';
import type {
  DailyReportStatus,
  AdAccountStatus,
  TopupStatus,
  ProjectStatus,
} from '@/types/status';

type StatusType = 'daily_report' | 'ad_account' | 'topup' | 'project';

type StatusValueMap = {
  daily_report: DailyReportStatus;
  ad_account: AdAccountStatus;
  topup: TopupStatus;
  project: ProjectStatus;
};

interface StatusBadgeProps<T extends StatusType> {
  type: T;
  status: StatusValueMap[T];
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const STATUS_CONFIG_MAP = {
  daily_report: DAILY_REPORT_STATUS_CONFIG,
  ad_account: AD_ACCOUNT_STATUS_CONFIG,
  topup: TOPUP_STATUS_CONFIG,
  project: PROJECT_STATUS_CONFIG,
} as const;

const VARIANT_CLASSES = {
  default: 'bg-gray-100 text-gray-800 hover:bg-gray-100',
  success: 'bg-green-100 text-green-800 hover:bg-green-100',
  warning: 'bg-yellow-100 text-yellow-800 hover:bg-yellow-100',
  error: 'bg-red-100 text-red-800 hover:bg-red-100',
  info: 'bg-blue-100 text-blue-800 hover:bg-blue-100',
} as const;

const SIZE_CLASSES = {
  sm: 'text-xs px-2 py-0.5',
  md: 'text-sm px-2.5 py-0.5',
  lg: 'text-base px-3 py-1',
} as const;

export function StatusBadge<T extends StatusType>({
  type,
  status,
  size = 'md',
  className,
}: StatusBadgeProps<T>) {
  const config = STATUS_CONFIG_MAP[type]?.[status as string];

  if (!config) {
    return (
      <Badge className={cn(VARIANT_CLASSES.default, SIZE_CLASSES[size], className)}>
        未知状态
      </Badge>
    );
  }

  return (
    <Badge
      className={cn(
        VARIANT_CLASSES[config.variant],
        SIZE_CLASSES[size],
        className
      )}
    >
      {config.label}
    </Badge>
  );
}

export default StatusBadge;
```

**文件 2: src/lib/constants/status-variants.ts**
```typescript
/**
 * 状态变体配置
 * SoT: STATE_MACHINE.md v2.9
 */
import type {
  DailyReportStatus,
  AdAccountStatus,
  TopupStatus,
  ProjectStatus,
} from '@/types/status';

type StatusVariant = 'default' | 'success' | 'warning' | 'error' | 'info';

interface StatusConfig {
  label: string;
  variant: StatusVariant;
  description?: string;
}

// ═══════════════════════════════════════════════════════════════
// 日报状态配置 (Phase 1: 3 状态)
// ═══════════════════════════════════════════════════════════════
export const DAILY_REPORT_STATUS_CONFIG: Record<DailyReportStatus, StatusConfig> = {
  raw_submitted: { label: '已提交', variant: 'info', description: '投手已提交原始数据' },
  trend_ok: { label: '已审核', variant: 'success', description: '趋势确认通过' },
  final_confirmed: { label: '已确认', variant: 'default', description: '终态锁定' },
};

// ═══════════════════════════════════════════════════════════════
// 账户状态配置 (6 状态)
// ═══════════════════════════════════════════════════════════════
export const AD_ACCOUNT_STATUS_CONFIG: Record<AdAccountStatus, StatusConfig> = {
  new: { label: '新建', variant: 'info' },
  testing: { label: '测试中', variant: 'warning' },
  active: { label: '活跃', variant: 'success' },
  suspended: { label: '暂停', variant: 'warning' },
  dead: { label: '死亡', variant: 'error' },
  archived: { label: '归档', variant: 'default' },
};

// ═══════════════════════════════════════════════════════════════
// 充值状态配置 (7 状态)
// ═══════════════════════════════════════════════════════════════
export const TOPUP_STATUS_CONFIG: Record<TopupStatus, StatusConfig> = {
  draft: { label: '草稿', variant: 'default' },
  pending_review: { label: '待审核', variant: 'info' },
  finance_approve: { label: '财务已批', variant: 'success' },
  paid: { label: '已付款', variant: 'success' },
  completed: { label: '已完成', variant: 'default' },
  rejected: { label: '已拒绝', variant: 'error' },
  cancelled: { label: '已取消', variant: 'default' },
};

// ═══════════════════════════════════════════════════════════════
// 项目状态配置 (4 状态)
// ═══════════════════════════════════════════════════════════════
export const PROJECT_STATUS_CONFIG: Record<ProjectStatus, StatusConfig> = {
  draft: { label: '草稿', variant: 'default' },
  active: { label: '活跃', variant: 'success' },
  suspended: { label: '暂停', variant: 'warning' },
  archived: { label: '归档', variant: 'default' },
};
```

#### 输出格式要求

**第一部分: 思考分析**
必须回答上述 5 个思考要点，每点 1-2 句话。

**第二部分: 代码实现**
按顺序输出完整文件：
1. src/components/ui/status-badge.tsx
2. src/lib/constants/status-variants.ts

**第三部分: 验证命令**
```bash
npx tsc --noEmit
```

#### 提交前自检

□ 日报状态仅 3 个（Phase 1）
□ 账户状态 6 个
□ 充值状态 7 个
□ 项目状态 4 个
□ 使用 shadcn/ui Badge
□ 支持 size 属性
□ TypeScript 类型安全
□ 无 any 类型

#### 验收标准

- [ ] 支持日报状态 (3 个): raw_submitted, trend_ok, final_confirmed
- [ ] 支持账户状态 (6 个): new, testing, active, suspended, dead, archived
- [ ] 支持充值状态 (7 个): draft, pending_review, finance_approve, paid, completed, rejected, cancelled
- [ ] 支持项目状态 (4 个): draft, active, suspended, archived
- [ ] 每个状态有对应的颜色和中文标签
- [ ] 组件支持 size 属性 (sm, md, lg)
- [ ] `npx tsc --noEmit` 无错误

---

### TASK-FE-COMMON-004: 导航访问控制 (canAccessNav)

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | common |
| 任务 ID | TASK-FE-COMMON-004 |
| 技术栈 | TypeScript + React |
| 优先级 | P0 |
| 预估工时 | 3h |

**前置条件**: TASK-FE-COMMON-002 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §5.2 (导航配置)
- MASTER.md v4.9 §2.4 (权限矩阵)

#### 任务

实现导航访问控制，包括：
1. NavAccess 接口定义
2. canAccessNav 函数实现
3. 9 个页面路由的访问控制配置

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/types/navigation.ts` | NavAccess 接口定义 | 20-30 |
| `src/lib/navigation.ts` | 导航配置 | 50-70 |
| `src/lib/access-control.ts` | 访问控制函数 | 40-60 |

#### 思考要点（必须先分析）

1. **访问规则**: 哪些页面对全部角色开放？哪些需要特定角色？
2. **CEO 判断**: 为什么用 `requireCeo` 而不是直接检查角色？
3. **项目负责人**: 为什么需要单独的 `requireProjectOwner` 标志？
4. **allowAll**: 什么情况下使用？与空的 techRoles 有什么区别？
5. **组合规则**: 多个条件如何组合判断？OR 还是 AND？

#### 约束规则

1. 驾驶舱、日报、充值对全部角色开放
2. 项目管理对 ceo, project_owner, admin 开放
3. 账户管理对 ceo, project_owner, account_manager, admin 开放
4. 财务中心对 ceo, finance, admin 开放
5. 系统设置仅对 admin 开放
6. 使用 `isCeo()` 函数判断 CEO 身份

#### 边缘情况

| 场景 | 期望行为 | 代码示例 |
|------|---------|---------|
| 用户未登录 | 返回 false | `canAccessNav(null, config)` → `false` |
| allowAll = true | 任何角色可访问 | 驾驶舱页面 |
| requireCeo = true | 仅 CEO 可访问 | 特定管理功能 |
| 多条件组合 | OR 逻辑 | `techRoles OR requireProjectOwner OR requireCeo` |

#### 代码参考

**文件 1: src/types/navigation.ts**
```typescript
/**
 * 导航访问控制类型定义
 * SoT: FRONTEND_PAGE_DESIGN_v2.1.md §5.2
 */
import type { TechRole } from './roles';

export interface NavAccess {
  /** 允许访问的技术层角色 */
  techRoles?: TechRole[];
  /** 是否需要项目负责人身份 */
  requireProjectOwner?: boolean;
  /** 是否需要 CEO 身份 */
  requireCeo?: boolean;
  /** 是否对全部角色开放 */
  allowAll?: boolean;
}

export interface NavItem {
  label: string;
  href: string;
  icon: string;
  access: NavAccess;
}
```

**文件 2: src/lib/navigation.ts**
```typescript
/**
 * 导航配置
 * SoT: FRONTEND_PAGE_DESIGN_v2.1.md §5.2
 */
import type { NavItem } from '@/types/navigation';

export const NAV_ITEMS: NavItem[] = [
  // ─── 全部角色可访问 ───
  {
    label: '驾驶舱',
    href: '/dashboard',
    icon: 'LayoutDashboard',
    access: { allowAll: true },
  },
  {
    label: '日报管理',
    href: '/daily-reports',
    icon: 'FileText',
    access: { allowAll: true },
  },
  {
    label: '充值管理',
    href: '/topups',
    icon: 'CreditCard',
    access: { allowAll: true },
  },

  // ─── 特定角色可访问 ───
  {
    label: '项目管理',
    href: '/projects',
    icon: 'FolderKanban',
    access: {
      techRoles: ['admin'],
      requireProjectOwner: true,
      requireCeo: true,
    },
  },
  {
    label: '账户管理',
    href: '/ad-accounts',
    icon: 'Users',
    access: {
      techRoles: ['admin', 'account_manager'],
      requireProjectOwner: true,
      requireCeo: true,
    },
  },
  {
    label: '渠道管理',
    href: '/channels',
    icon: 'Radio',
    access: {
      techRoles: ['admin', 'account_manager'],
      requireCeo: true,
    },
  },
  {
    label: '财务中心',
    href: '/finance',
    icon: 'Wallet',
    access: {
      techRoles: ['admin', 'finance'],
      requireCeo: true,
    },
  },
  {
    label: '用户管理',
    href: '/users',
    icon: 'UserCog',
    access: {
      techRoles: ['admin'],
      requireCeo: true,
    },
  },
  {
    label: '系统设置',
    href: '/settings',
    icon: 'Settings',
    access: {
      techRoles: ['admin'],
    },
  },
];
```

**文件 3: src/lib/access-control.ts**
```typescript
/**
 * 访问控制函数
 * SoT: MASTER.md v4.9 §2.4
 */
import type { User } from '@/types/user';
import type { NavAccess } from '@/types/navigation';
import type { TechRole } from '@/types/roles';

// CEO 用户 ID 列表
const CEO_USER_IDS = (process.env.NEXT_PUBLIC_CEO_USER_IDS || '')
  .split(',')
  .filter(Boolean)
  .map(Number);

/**
 * 检查是否为 CEO
 */
export function isCeo(user: User | null): boolean {
  if (!user) return false;
  return user.role === 'admin' && CEO_USER_IDS.includes(user.id);
}

/**
 * 检查是否为项目负责人
 */
export function isProjectOwner(user: User | null): boolean {
  return user?.is_project_owner === true;
}

/**
 * 检查用户是否可访问导航项
 * 规则: allowAll OR (techRoles OR requireProjectOwner OR requireCeo)
 */
export function canAccessNav(user: User | null, access: NavAccess): boolean {
  // 未登录用户无权限
  if (!user) return false;

  // 全部角色开放
  if (access.allowAll) return true;

  // 检查 CEO 身份
  if (access.requireCeo && isCeo(user)) return true;

  // 检查项目负责人身份
  if (access.requireProjectOwner && isProjectOwner(user)) return true;

  // 检查技术层角色
  if (access.techRoles?.includes(user.role as TechRole)) return true;

  return false;
}
```

#### 输出格式要求

**第一部分: 思考分析**
必须回答上述 5 个思考要点，每点 1-2 句话。

**第二部分: 代码实现**
按顺序输出完整文件：
1. src/types/navigation.ts
2. src/lib/navigation.ts
3. src/lib/access-control.ts

**第三部分: 验证命令**
```bash
npx tsc --noEmit
```

#### 提交前自检

□ NavAccess 接口完整
□ canAccessNav 函数正确
□ 9 个页面路由配置正确
□ 使用 isCeo() 函数
□ 使用 is_project_owner 字段
□ 无 supervisor 角色
□ 无 any 类型

#### 验收标准

- [ ] 实现 `NavAccess` 接口（techRoles, requireProjectOwner, requireCeo, allowAll）
- [ ] 实现 `canAccessNav(user, access)` 函数
- [ ] 9 个页面路由的访问控制配置正确
- [ ] 驾驶舱、日报、充值对全部角色开放
- [ ] 项目管理对 ceo, project_owner, admin 开放
- [ ] 财务中心对 ceo, finance, admin 开放
- [ ] 系统设置仅对 admin 开放
- [ ] `npx tsc --noEmit` 无错误

---

### TASK-FE-COMMON-005: 通用列表页模板

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | common |
| 任务 ID | TASK-FE-COMMON-005 |
| 技术栈 | React + TanStack Query + shadcn/ui |
| 优先级 | P0 |
| 预估工时 | 4h |

**前置条件**: TASK-FE-COMMON-003 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §7.1 (必须使用的组件)
- FRONTEND_PAGE_DESIGN_v2.1.md §8 (API 调用规范)

#### 任务

实现通用列表页模板，包括：
1. ListPage 通用容器组件
2. ListFilters 通用筛选器组件
3. ListPagination 分页组件
4. useListQuery 列表查询 Hook

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/components/common/ListPage.tsx` | 通用列表页模板 | 80-100 |
| `src/components/common/ListFilters.tsx` | 通用筛选器 | 60-80 |
| `src/components/common/ListPagination.tsx` | 分页组件 | 50-70 |
| `src/components/common/index.ts` | 统一导出 | 5-10 |
| `src/hooks/useListQuery.ts` | 列表查询 Hook | 60-80 |

#### 思考要点（必须先分析）

1. **组件复用**: 如何让 ListPage 支持不同类型的数据列表？
2. **查询缓存**: TanStack Query 的 queryKey 如何设计才能正确失效？
3. **URL 同步**: 筛选条件如何与 URL 参数同步？
4. **分页策略**: 客户端分页 vs 服务端分页，选择哪个？
5. **状态管理**: 加载、空数据、错误三种状态如何处理？

#### 约束规则

1. 使用 `apiGet` 进行 API 调用（禁止 fetch/axios）
2. 使用 TanStack Query 的 useQuery
3. 使用 DataTable 组件（禁止原生 table）
4. 筛选条件同步到 URL
5. 支持加载状态、空状态、错误状态

#### 边缘情况

| 场景 | 期望行为 | 代码示例 |
|------|---------|---------|
| 数据为空 | 显示空状态 | `<EmptyState message="暂无数据" />` |
| 加载中 | 显示骨架屏 | `<Skeleton />` |
| API 报错 | 显示错误提示 | `<ErrorMessage error={error} />` |
| 首次加载 | 使用 URL 参数 | `?page=1&status=active` |

#### 代码参考

**文件 1: src/hooks/useListQuery.ts**
```typescript
'use client';

/**
 * 通用列表查询 Hook
 * SoT: FRONTEND_PAGE_DESIGN_v2.1.md §8
 */
import { useQuery, type UseQueryOptions } from '@tanstack/react-query';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import { useCallback, useMemo } from 'react';
import { apiGet } from '@/lib/api';

export interface ListParams {
  page?: number;
  page_size?: number;
  [key: string]: string | number | boolean | undefined;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

interface UseListQueryOptions<T> {
  queryKey: string[];
  endpoint: string;
  defaultParams?: ListParams;
  queryOptions?: Omit<UseQueryOptions<PaginatedResponse<T>>, 'queryKey' | 'queryFn'>;
}

export function useListQuery<T>({
  queryKey,
  endpoint,
  defaultParams = { page: 1, page_size: 20 },
  queryOptions,
}: UseListQueryOptions<T>) {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  // 从 URL 解析参数
  const params = useMemo<ListParams>(() => {
    const urlParams: ListParams = { ...defaultParams };
    searchParams.forEach((value, key) => {
      if (key === 'page' || key === 'page_size') {
        urlParams[key] = parseInt(value, 10);
      } else {
        urlParams[key] = value;
      }
    });
    return urlParams;
  }, [searchParams, defaultParams]);

  // 更新 URL 参数
  const setParams = useCallback((newParams: ListParams) => {
    const urlParams = new URLSearchParams();
    Object.entries(newParams).forEach(([key, value]) => {
      if (value !== undefined && value !== '' && value !== '__all__') {
        urlParams.set(key, String(value));
      }
    });
    router.push(`${pathname}?${urlParams.toString()}`);
  }, [router, pathname]);

  // 构建查询参数字符串
  const queryString = useMemo(() => {
    const urlParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== '' && value !== '__all__') {
        urlParams.set(key, String(value));
      }
    });
    return urlParams.toString();
  }, [params]);

  // 数据查询
  const query = useQuery<PaginatedResponse<T>>({
    queryKey: [...queryKey, params],
    queryFn: () => apiGet<PaginatedResponse<T>>(`${endpoint}?${queryString}`),
    ...queryOptions,
  });

  return {
    ...query,
    params,
    setParams,
  };
}

export default useListQuery;
```

**文件 2: src/components/common/ListPage.tsx**
```typescript
'use client';

/**
 * 通用列表页模板
 */
import { ReactNode } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface ListPageProps {
  title: string;
  description?: string;
  actions?: ReactNode;
  filters?: ReactNode;
  children: ReactNode;
  isLoading?: boolean;
  isError?: boolean;
  error?: Error | null;
  isEmpty?: boolean;
  emptyMessage?: string;
}

export function ListPage({
  title,
  description,
  actions,
  filters,
  children,
  isLoading = false,
  isError = false,
  error = null,
  isEmpty = false,
  emptyMessage = '暂无数据',
}: ListPageProps) {
  return (
    <div className="space-y-6">
      {/* 页面头部 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
          {description && (
            <p className="text-muted-foreground">{description}</p>
          )}
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>

      {/* 筛选器 */}
      {filters && (
        <Card>
          <CardContent className="pt-6">{filters}</CardContent>
        </Card>
      )}

      {/* 主内容区域 */}
      <Card>
        <CardContent className="pt-6">
          {isLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          ) : isError ? (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {error?.message || '加载数据失败，请稍后重试'}
              </AlertDescription>
            </Alert>
          ) : isEmpty ? (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <p>{emptyMessage}</p>
            </div>
          ) : (
            children
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default ListPage;
```

**文件 3: src/components/common/ListPagination.tsx**
```typescript
'use client';

/**
 * 分页组件
 */
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination';

interface ListPaginationProps {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
}

export function ListPagination({
  page,
  pageSize,
  total,
  onPageChange,
}: ListPaginationProps) {
  const totalPages = Math.ceil(total / pageSize);

  if (totalPages <= 1) return null;

  const pages = Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
    const start = Math.max(1, Math.min(page - 2, totalPages - 4));
    return start + i;
  }).filter(p => p >= 1 && p <= totalPages);

  return (
    <div className="flex items-center justify-between py-4">
      <p className="text-sm text-muted-foreground">
        共 {total} 条记录，第 {page} / {totalPages} 页
      </p>
      <Pagination>
        <PaginationContent>
          <PaginationItem>
            <PaginationPrevious
              onClick={() => page > 1 && onPageChange(page - 1)}
              className={page <= 1 ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
            />
          </PaginationItem>
          {pages.map((p) => (
            <PaginationItem key={p}>
              <PaginationLink
                onClick={() => onPageChange(p)}
                isActive={p === page}
                className="cursor-pointer"
              >
                {p}
              </PaginationLink>
            </PaginationItem>
          ))}
          <PaginationItem>
            <PaginationNext
              onClick={() => page < totalPages && onPageChange(page + 1)}
              className={page >= totalPages ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
            />
          </PaginationItem>
        </PaginationContent>
      </Pagination>
    </div>
  );
}

export default ListPagination;
```

#### 输出格式要求

**第一部分: 思考分析**
回答 5 个思考要点。

**第二部分: 代码实现**
按顺序输出完整文件。

**第三部分: 验证命令**
```bash
npx tsc --noEmit
```

#### 提交前自检

□ 使用 apiGet（无 fetch/axios）
□ 使用 TanStack Query
□ URL 参数同步
□ 加载状态处理
□ 空状态处理
□ 错误状态处理
□ 无 any 类型

#### 验收标准

- [ ] 封装 DataTable、筛选器、分页的通用模式
- [ ] 支持 TanStack Query 的 useQuery 模式
- [ ] 支持筛选条件的 URL 同步
- [ ] 支持加载状态、空状态、错误状态
- [ ] 使用 `apiGet` 进行 API 调用
- [ ] `npx tsc --noEmit` 无错误

---

## 4.2.3 DASH 模块补充提示词

### TASK-FE-DASH-003: 趋势图表组件

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | dashboard |
| 任务 ID | TASK-FE-DASH-003 |
| 技术栈 | React + recharts |
| 优先级 | P0 |
| 预估工时 | 4h |

**前置条件**: TASK-FE-DASH-001 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §6.1.2 (核心组件)

#### 任务

实现趋势图表组件，包括：
1. 消耗趋势折线图
2. 转化趋势折线图
3. 日/周/月时间维度切换
4. 趋势数据查询 Hook

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/dashboard/components/TrendCharts.tsx` | 趋势图表容器 | 60-80 |
| `src/features/dashboard/components/SpendTrendChart.tsx` | 消耗趋势图 | 80-100 |
| `src/features/dashboard/components/ConversionTrendChart.tsx` | 转化趋势图 | 80-100 |
| `src/features/dashboard/components/chart-config.ts` | 图表配置 | 30-40 |
| `src/features/dashboard/hooks/useTrendData.ts` | 趋势数据 Hook | 40-60 |

#### 思考要点（必须先分析）

1. **图表库选择**: 为什么使用 recharts 而不是其他库？
2. **时间维度**: 日/周/月切换时，数据聚合在前端还是后端做？
3. **数据权限**: 不同角色看到的趋势数据范围有什么不同？
4. **响应式**: 图表如何适应不同屏幕尺寸？
5. **加载状态**: 图表数据加载中时如何显示？

#### 约束规则

1. 使用 recharts 图表库
2. 数据权限按角色过滤
3. 使用 apiGet 获取数据
4. 响应式图表尺寸
5. 支持日/周/月时间维度

#### 边缘情况

| 场景 | 期望行为 | 代码示例 |
|------|---------|---------|
| 数据为空 | 显示"暂无数据" | 空数组时显示提示 |
| 加载中 | 显示骨架屏 | `<ChartSkeleton />` |
| 单点数据 | 正常显示点 | 只有一天数据时 |
| 窗口缩放 | 图表自适应 | 使用 ResponsiveContainer |

#### 代码参考

**文件 1: src/features/dashboard/components/TrendCharts.tsx**
```typescript
'use client';

/**
 * 趋势图表容器
 */
import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { SpendTrendChart } from './SpendTrendChart';
import { ConversionTrendChart } from './ConversionTrendChart';
import { useTrendData } from '../hooks/useTrendData';

type TimeRange = 'day' | 'week' | 'month';

export function TrendCharts() {
  const [timeRange, setTimeRange] = useState<TimeRange>('day');
  const { data, isLoading } = useTrendData(timeRange);

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-base font-medium">消耗趋势</CardTitle>
          <Tabs value={timeRange} onValueChange={(v) => setTimeRange(v as TimeRange)}>
            <TabsList className="h-8">
              <TabsTrigger value="day" className="text-xs">日</TabsTrigger>
              <TabsTrigger value="week" className="text-xs">周</TabsTrigger>
              <TabsTrigger value="month" className="text-xs">月</TabsTrigger>
            </TabsList>
          </Tabs>
        </CardHeader>
        <CardContent>
          <SpendTrendChart data={data?.spend ?? []} isLoading={isLoading} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-base font-medium">转化趋势</CardTitle>
        </CardHeader>
        <CardContent>
          <ConversionTrendChart data={data?.conversions ?? []} isLoading={isLoading} />
        </CardContent>
      </Card>
    </div>
  );
}

export default TrendCharts;
```

**文件 2: src/features/dashboard/components/SpendTrendChart.tsx**
```typescript
'use client';

/**
 * 消耗趋势图
 */
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { Skeleton } from '@/components/ui/skeleton';
import { CHART_COLORS } from './chart-config';

interface TrendDataPoint {
  date: string;
  value: number;
}

interface SpendTrendChartProps {
  data: TrendDataPoint[];
  isLoading?: boolean;
}

export function SpendTrendChart({ data, isLoading }: SpendTrendChartProps) {
  if (isLoading) {
    return <Skeleton className="h-[300px] w-full" />;
  }

  if (data.length === 0) {
    return (
      <div className="flex h-[300px] items-center justify-center text-muted-foreground">
        暂无数据
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 12 }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          tick={{ fontSize: 12 }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(value) => `¥${(value / 10000).toFixed(1)}万`}
        />
        <Tooltip
          formatter={(value: number) => [`¥${value.toLocaleString()}`, '消耗']}
          labelFormatter={(label) => `日期: ${label}`}
        />
        <Legend />
        <Line
          type="monotone"
          dataKey="value"
          name="消耗"
          stroke={CHART_COLORS.primary}
          strokeWidth={2}
          dot={{ r: 4 }}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export default SpendTrendChart;
```

**文件 3: src/features/dashboard/hooks/useTrendData.ts**
```typescript
'use client';

/**
 * 趋势数据 Hook
 */
import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/lib/api';

type TimeRange = 'day' | 'week' | 'month';

interface TrendDataPoint {
  date: string;
  value: number;
}

interface TrendData {
  spend: TrendDataPoint[];
  conversions: TrendDataPoint[];
}

export function useTrendData(timeRange: TimeRange) {
  return useQuery<TrendData>({
    queryKey: ['dashboard', 'trend', timeRange],
    queryFn: () => apiGet<TrendData>(`/api/v1/dashboard/trend?range=${timeRange}`),
  });
}

export default useTrendData;
```

#### 输出格式要求

**第一部分: 思考分析**
回答 5 个思考要点。

**第二部分: 代码实现**
按顺序输出完整文件。

**第三部分: 验证命令**
```bash
npx tsc --noEmit
```

#### 提交前自检

□ 使用 recharts
□ 使用 apiGet
□ 响应式图表
□ 时间维度切换
□ 加载状态处理
□ 空数据处理
□ 无 any 类型

#### 验收标准

- [ ] 支持日/周/月时间维度切换
- [ ] 消耗趋势折线图
- [ ] 转化趋势折线图
- [ ] 响应式图表尺寸
- [ ] 使用 recharts 图表库
- [ ] `npx tsc --noEmit` 无错误

---

### TASK-FE-DASH-004: 待办事项卡片

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | dashboard |
| 任务 ID | TASK-FE-DASH-004 |
| 技术栈 | React + TanStack Query |
| 优先级 | P0 |
| 预估工时 | 3h |

**前置条件**: TASK-FE-DASH-001 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §6.1.2 (核心组件)

#### 任务

实现待办事项卡片，包括：
1. 待办事项容器组件
2. 单个待办项组件
3. 按角色显示不同待办
4. 待办数据查询 Hook

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/dashboard/components/PendingTasks.tsx` | 待办事项容器 | 60-80 |
| `src/features/dashboard/components/PendingTaskItem.tsx` | 单个待办项 | 40-50 |
| `src/features/dashboard/hooks/usePendingTasks.ts` | 待办数据 Hook | 30-40 |

#### 思考要点（必须先分析）

1. **角色差异**: 投手、项目负责人、财务的待办有什么不同？
2. **数量徽章**: 待办数量如何获取和显示？
3. **跳转链接**: 点击待办项应该跳转到哪个页面？
4. **实时更新**: 待办完成后如何刷新列表？
5. **优先级**: 多个待办如何排序？

#### 约束规则

1. 待办项按角色权限过滤
2. 显示待办数量徽章
3. 点击跳转到对应页面
4. 使用 apiGet 获取数据
5. 使用 TanStack Query 缓存

#### 边缘情况

| 场景 | 期望行为 | 代码示例 |
|------|---------|---------|
| 无待办 | 显示"暂无待办" | 空列表时 |
| 待办过多 | 最多显示 5 条 | `items.slice(0, 5)` |
| 权限不足 | 不显示该类待办 | 投手不显示审批类 |

#### 代码参考

**文件 1: src/features/dashboard/components/PendingTasks.tsx**
```typescript
'use client';

/**
 * 待办事项容器
 */
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { PendingTaskItem } from './PendingTaskItem';
import { usePendingTasks } from '../hooks/usePendingTasks';

export function PendingTasks() {
  const { data, isLoading } = usePendingTasks();
  const totalCount = data?.items?.length ?? 0;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-base font-medium">待办事项</CardTitle>
        {totalCount > 0 && (
          <Badge variant="secondary">{totalCount}</Badge>
        )}
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        ) : totalCount === 0 ? (
          <p className="py-4 text-center text-muted-foreground">暂无待办</p>
        ) : (
          <div className="space-y-2">
            {data?.items?.slice(0, 5).map((item) => (
              <PendingTaskItem key={item.id} item={item} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default PendingTasks;
```

**文件 2: src/features/dashboard/components/PendingTaskItem.tsx**
```typescript
'use client';

/**
 * 单个待办项
 */
import Link from 'next/link';
import { ChevronRight, FileText, CreditCard, CheckCircle } from 'lucide-react';

interface PendingTask {
  id: string;
  type: 'daily_report_review' | 'topup_approve' | 'daily_report_submit';
  title: string;
  count: number;
  href: string;
}

interface PendingTaskItemProps {
  item: PendingTask;
}

const TASK_ICONS = {
  daily_report_review: FileText,
  topup_approve: CreditCard,
  daily_report_submit: CheckCircle,
} as const;

export function PendingTaskItem({ item }: PendingTaskItemProps) {
  const Icon = TASK_ICONS[item.type] ?? FileText;

  return (
    <Link
      href={item.href}
      className="flex items-center justify-between rounded-lg border p-3 transition-colors hover:bg-muted/50"
    >
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
          <Icon className="h-4 w-4 text-primary" />
        </div>
        <div>
          <p className="text-sm font-medium">{item.title}</p>
          <p className="text-xs text-muted-foreground">{item.count} 项待处理</p>
        </div>
      </div>
      <ChevronRight className="h-4 w-4 text-muted-foreground" />
    </Link>
  );
}

export default PendingTaskItem;
```

**文件 3: src/features/dashboard/hooks/usePendingTasks.ts**
```typescript
'use client';

/**
 * 待办数据 Hook
 */
import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/lib/api';

interface PendingTask {
  id: string;
  type: 'daily_report_review' | 'topup_approve' | 'daily_report_submit';
  title: string;
  count: number;
  href: string;
}

interface PendingTasksResponse {
  items: PendingTask[];
}

export function usePendingTasks() {
  return useQuery<PendingTasksResponse>({
    queryKey: ['dashboard', 'pending-tasks'],
    queryFn: () => apiGet<PendingTasksResponse>('/api/v1/dashboard/pending-tasks'),
    refetchInterval: 60000, // 每分钟刷新
  });
}

export default usePendingTasks;
```

#### 输出格式要求

回答思考要点，输出完整代码，运行验证命令。

#### 提交前自检

□ 按角色过滤待办
□ 显示数量徽章
□ 点击跳转正确
□ 使用 apiGet
□ 无 any 类型

#### 验收标准

- [ ] 显示待审核日报（项目负责人）
- [ ] 显示待审批充值（财务）
- [ ] 显示待提交日报（投手）
- [ ] 点击跳转到对应页面
- [ ] 显示数量徽章
- [ ] `npx tsc --noEmit` 无错误

---

### TASK-FE-DASH-005: 快捷操作组件

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | dashboard |
| 任务 ID | TASK-FE-DASH-005 |
| 技术栈 | React + usePermission |
| 优先级 | P0 |
| 预估工时 | 3h |

**前置条件**: TASK-FE-DASH-001 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §6.1.2 (核心组件)
- MASTER.md v4.9 §2.4 (权限矩阵)

#### 任务

实现快捷操作组件，包括：
1. 快捷操作容器
2. 快捷操作按钮
3. 按角色权限显示/隐藏

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/dashboard/components/QuickActions.tsx` | 快捷操作容器 | 80-100 |
| `src/features/dashboard/components/QuickActionButton.tsx` | 快捷操作按钮 | 30-40 |

#### 思考要点（必须先分析）

1. **角色操作**: 投手、项目负责人、财务、户管各有什么快捷操作？
2. **权限控制**: 如何使用 can() 控制按钮显示？
3. **跳转 vs 弹窗**: 哪些操作应该跳转页面，哪些应该弹窗？
4. **图标选择**: 每个操作应该使用什么图标？
5. **操作优先级**: 如何排列多个操作按钮？

#### 约束规则

1. 使用 can() 检查权限
2. 投手：提交日报、申请充值
3. 项目负责人：审核日报、查看项目
4. 财务：审批充值、查看账本
5. 户管：分配账户、创建账户

#### 代码参考

**文件 1: src/features/dashboard/components/QuickActions.tsx**
```typescript
'use client';

/**
 * 快捷操作组件
 * SoT: MASTER.md v4.9 §2.4
 */
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { QuickActionButton } from './QuickActionButton';
import { usePermission } from '@/hooks/usePermission';
import {
  FileText,
  CreditCard,
  CheckCircle,
  FolderKanban,
  Wallet,
  Users,
  UserPlus,
} from 'lucide-react';

interface QuickAction {
  id: string;
  label: string;
  href: string;
  icon: React.ReactNode;
  permission: string;
}

const QUICK_ACTIONS: QuickAction[] = [
  {
    id: 'submit-report',
    label: '提交日报',
    href: '/daily-reports/new',
    icon: <FileText className="h-5 w-5" />,
    permission: 'daily_report:create',
  },
  {
    id: 'request-topup',
    label: '申请充值',
    href: '/topups/new',
    icon: <CreditCard className="h-5 w-5" />,
    permission: 'topup:create',
  },
  {
    id: 'review-reports',
    label: '审核日报',
    href: '/daily-reports?status=raw_submitted',
    icon: <CheckCircle className="h-5 w-5" />,
    permission: 'daily_report:review',
  },
  {
    id: 'view-projects',
    label: '查看项目',
    href: '/projects',
    icon: <FolderKanban className="h-5 w-5" />,
    permission: 'project:view',
  },
  {
    id: 'approve-topup',
    label: '审批充值',
    href: '/topups?status=pending_review',
    icon: <Wallet className="h-5 w-5" />,
    permission: 'topup:approve',
  },
  {
    id: 'assign-account',
    label: '分配账户',
    href: '/ad-accounts',
    icon: <Users className="h-5 w-5" />,
    permission: 'ad_account:assign',
  },
  {
    id: 'create-account',
    label: '创建账户',
    href: '/ad-accounts/new',
    icon: <UserPlus className="h-5 w-5" />,
    permission: 'ad_account:create',
  },
];

export function QuickActions() {
  const { can } = usePermission();

  const visibleActions = QUICK_ACTIONS.filter((action) =>
    can(action.permission)
  );

  if (visibleActions.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">快捷操作</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {visibleActions.map((action) => (
            <QuickActionButton
              key={action.id}
              label={action.label}
              href={action.href}
              icon={action.icon}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export default QuickActions;
```

**文件 2: src/features/dashboard/components/QuickActionButton.tsx**
```typescript
'use client';

/**
 * 快捷操作按钮
 */
import Link from 'next/link';
import { Button } from '@/components/ui/button';

interface QuickActionButtonProps {
  label: string;
  href: string;
  icon: React.ReactNode;
}

export function QuickActionButton({ label, href, icon }: QuickActionButtonProps) {
  return (
    <Link href={href}>
      <Button
        variant="outline"
        className="flex h-20 w-full flex-col items-center justify-center gap-2"
      >
        {icon}
        <span className="text-xs">{label}</span>
      </Button>
    </Link>
  );
}

export default QuickActionButton;
```

#### 验收标准

- [ ] 投手：提交日报、申请充值
- [ ] 项目负责人：审核日报、查看项目
- [ ] 财务：审批充值、查看账本
- [ ] 户管：分配账户、创建账户
- [ ] 按钮根据权限显示/隐藏
- [ ] `npx tsc --noEmit` 无错误

---

### TASK-FE-DASH-006: 角色视图切换

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | dashboard |
| 任务 ID | TASK-FE-DASH-006 |
| 技术栈 | React + usePermission |
| 优先级 | P0 |
| 预估工时 | 4h |

**前置条件**: TASK-FE-DASH-002, TASK-FE-COMMON-002 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §6.1.1 (角色视图差异)

#### 任务

实现角色视图切换功能：
1. 自动检测用户角色并显示对应视图
2. CEO/Admin 可切换查看其他角色视图
3. 视图切换时数据自动刷新

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/dashboard/components/RoleViewSwitcher.tsx` | 角色视图切换器 | 60-80 |
| `src/features/dashboard/components/role-views.ts` | 角色视图配置 | 40-50 |
| `src/features/dashboard/hooks/useRoleView.ts` | 角色视图状态 Hook | 40-60 |

#### 思考要点（必须先分析）

1. **切换权限**: 哪些角色可以切换视图？
2. **默认视图**: 每个角色的默认视图是什么？
3. **数据刷新**: 切换视图后如何刷新驾驶舱数据？
4. **视图差异**: 不同角色的视图有什么内容差异？
5. **状态持久化**: 切换的视图状态需要持久化吗？

#### 约束规则

1. 角色判断使用 usePermission Hook
2. CEO/Admin 可切换任意视图
3. 普通用户仅能查看自己角色视图
4. 视图切换时触发数据刷新

#### 代码参考

**文件 1: src/features/dashboard/components/RoleViewSwitcher.tsx**
```typescript
'use client';

/**
 * 角色视图切换器
 */
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { usePermission } from '@/hooks/usePermission';
import { useRoleView } from '../hooks/useRoleView';
import { ROLE_VIEW_OPTIONS, type RoleViewType } from './role-views';

export function RoleViewSwitcher() {
  const { isCeo, businessRole } = usePermission();
  const { currentView, setCurrentView } = useRoleView();

  // 只有 CEO 和 Admin 可以切换视图
  const canSwitch = isCeo() || businessRole === 'admin';

  if (!canSwitch) {
    return null;
  }

  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-muted-foreground">视图:</span>
      <Select
        value={currentView}
        onValueChange={(value) => setCurrentView(value as RoleViewType)}
      >
        <SelectTrigger className="w-[140px]">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {ROLE_VIEW_OPTIONS.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

export default RoleViewSwitcher;
```

**文件 2: src/features/dashboard/components/role-views.ts**
```typescript
/**
 * 角色视图配置
 */
import type { BusinessRole } from '@/types/roles';

export type RoleViewType = BusinessRole | 'all';

interface RoleViewOption {
  value: RoleViewType;
  label: string;
}

export const ROLE_VIEW_OPTIONS: RoleViewOption[] = [
  { value: 'all', label: '全局视图' },
  { value: 'ceo', label: '老板视图' },
  { value: 'project_owner', label: '项目负责人视图' },
  { value: 'finance', label: '财务视图' },
  { value: 'pitcher', label: '投手视图' },
  { value: 'account_manager', label: '户管视图' },
];

// 每个角色视图显示的组件配置
export const ROLE_VIEW_COMPONENTS: Record<RoleViewType, string[]> = {
  all: ['kpi', 'trends', 'pending', 'quick-actions'],
  ceo: ['kpi', 'trends', 'pending', 'profit-summary'],
  project_owner: ['kpi', 'trends', 'pending', 'project-summary'],
  finance: ['kpi', 'pending', 'fund-summary'],
  pitcher: ['kpi', 'pending', 'quick-actions', 'my-reports'],
  account_manager: ['kpi', 'pending', 'account-summary'],
  admin: ['kpi', 'trends', 'pending', 'system-status'],
};
```

**文件 3: src/features/dashboard/hooks/useRoleView.ts**
```typescript
'use client';

/**
 * 角色视图状态 Hook
 */
import { useState, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { usePermission } from '@/hooks/usePermission';
import type { RoleViewType } from '../components/role-views';

export function useRoleView() {
  const { businessRole } = usePermission();
  const queryClient = useQueryClient();

  const [currentView, setCurrentView] = useState<RoleViewType>(
    businessRole ?? 'pitcher'
  );

  // 角色变化时重置视图
  useEffect(() => {
    if (businessRole) {
      setCurrentView(businessRole);
    }
  }, [businessRole]);

  // 视图变化时刷新数据
  const handleViewChange = (view: RoleViewType) => {
    setCurrentView(view);
    // 刷新驾驶舱相关查询
    queryClient.invalidateQueries({ queryKey: ['dashboard'] });
  };

  return {
    currentView,
    setCurrentView: handleViewChange,
  };
}

export default useRoleView;
```

#### 验收标准

- [ ] 自动检测用户角色并显示对应视图
- [ ] CEO/Admin 可切换查看其他角色视图
- [ ] 普通用户仅能查看自己角色视图
- [ ] 视图切换时数据自动刷新
- [ ] `npx tsc --noEmit` 无错误

---

## 4.3.2 RPT 日报模块补充提示词

### TASK-FE-RPT-002: 日报筛选器

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | daily-reports |
| 任务 ID | TASK-FE-RPT-002 |
| 技术栈 | React + shadcn/ui |
| 优先级 | P0 |
| 预估工时 | 3h |

**前置条件**: TASK-FE-RPT-001 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §6.2.1 (页面功能)
- STATE_MACHINE.md v2.9 §7.5.1 (Phase 1 日报状态机)

#### 任务

实现日报筛选器组件：
1. 日期范围筛选（默认最近 7 天）
2. 状态筛选（仅 3 个状态 + 全部）
3. 项目筛选（根据权限过滤）
4. 投手筛选（项目负责人可用）

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/daily-reports/components/DailyReportsFilters.tsx` | 日报筛选器 | 100-130 |

#### 思考要点（必须先分析）

1. **日期默认值**: 为什么默认最近 7 天？如何计算？
2. **状态选项**: Phase 1 只有 3 个状态，如何配置选项？
3. **权限过滤**: 项目和投手下拉如何根据用户权限过滤？
4. **URL 同步**: 筛选条件如何与 URL 参数同步？
5. **重置功能**: 如何重置所有筛选条件？

#### 约束规则

1. 状态筛选仅包含 3 个状态（Phase 1）
2. 筛选条件同步到 URL
3. 使用 shadcn/ui 的 Select、DatePicker 组件
4. 投手筛选仅项目负责人和 CEO 可用

#### 代码参考

**文件: src/features/daily-reports/components/DailyReportsFilters.tsx**
```typescript
'use client';

/**
 * 日报筛选器
 * SoT: STATE_MACHINE.md v2.9 §7.5.1
 */
import { useCallback } from 'react';
import { format, subDays } from 'date-fns';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { DatePickerWithRange } from '@/components/ui/date-picker-range';
import { usePermission } from '@/hooks/usePermission';
import { DAILY_REPORT_STATUSES, type DailyReportStatus } from '@/types/status';
import { DAILY_REPORT_STATUS_CONFIG } from '@/lib/constants/status-variants';
import type { ListParams } from '@/hooks/useListQuery';

interface DailyReportsFiltersProps {
  params: ListParams;
  onParamsChange: (params: ListParams) => void;
  projects?: { id: number; name: string }[];
  pitchers?: { id: number; name: string }[];
}

export function DailyReportsFilters({
  params,
  onParamsChange,
  projects = [],
  pitchers = [],
}: DailyReportsFiltersProps) {
  const { can, isProjectOwner, isCeo } = usePermission();
  const canFilterByPitcher = isProjectOwner() || isCeo() || can('daily_report:view_all');

  // 日期范围默认值：最近 7 天
  const defaultDateRange = {
    from: subDays(new Date(), 7),
    to: new Date(),
  };

  const handleStatusChange = useCallback((value: string) => {
    onParamsChange({ ...params, status: value === '__all__' ? undefined : value, page: 1 });
  }, [params, onParamsChange]);

  const handleProjectChange = useCallback((value: string) => {
    onParamsChange({ ...params, project_id: value === '__all__' ? undefined : value, page: 1 });
  }, [params, onParamsChange]);

  const handlePitcherChange = useCallback((value: string) => {
    onParamsChange({ ...params, pitcher_id: value === '__all__' ? undefined : value, page: 1 });
  }, [params, onParamsChange]);

  const handleDateChange = useCallback((range: { from?: Date; to?: Date } | undefined) => {
    onParamsChange({
      ...params,
      start_date: range?.from ? format(range.from, 'yyyy-MM-dd') : undefined,
      end_date: range?.to ? format(range.to, 'yyyy-MM-dd') : undefined,
      page: 1,
    });
  }, [params, onParamsChange]);

  const handleReset = useCallback(() => {
    onParamsChange({ page: 1, page_size: 20 });
  }, [onParamsChange]);

  return (
    <div className="flex flex-wrap items-center gap-4">
      {/* 日期范围 */}
      <DatePickerWithRange
        defaultValue={defaultDateRange}
        onChange={handleDateChange}
      />

      {/* 状态筛选 - Phase 1 仅 3 个状态 */}
      <Select
        value={params.status as string ?? '__all__'}
        onValueChange={handleStatusChange}
      >
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="全部状态" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">全部状态</SelectItem>
          {DAILY_REPORT_STATUSES.map((status) => (
            <SelectItem key={status} value={status}>
              {DAILY_REPORT_STATUS_CONFIG[status].label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* 项目筛选 */}
      <Select
        value={params.project_id as string ?? '__all__'}
        onValueChange={handleProjectChange}
      >
        <SelectTrigger className="w-[160px]">
          <SelectValue placeholder="全部项目" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">全部项目</SelectItem>
          {projects.map((project) => (
            <SelectItem key={project.id} value={String(project.id)}>
              {project.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* 投手筛选 - 仅项目负责人/CEO 可用 */}
      {canFilterByPitcher && (
        <Select
          value={params.pitcher_id as string ?? '__all__'}
          onValueChange={handlePitcherChange}
        >
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="全部投手" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">全部投手</SelectItem>
            {pitchers.map((pitcher) => (
              <SelectItem key={pitcher.id} value={String(pitcher.id)}>
                {pitcher.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}

      <Button variant="outline" size="sm" onClick={handleReset}>
        重置
      </Button>
    </div>
  );
}

export default DailyReportsFilters;
```

#### 验收标准

- [ ] 日期范围筛选（默认最近 7 天）
- [ ] 状态筛选（3 个状态 + 全部）
- [ ] 项目筛选（根据权限过滤可选项）
- [ ] 投手筛选（项目负责人可用）
- [ ] 筛选条件同步到 URL
- [ ] `npx tsc --noEmit` 无错误

---

### TASK-FE-RPT-003: 日报表格组件

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | daily-reports |
| 任务 ID | TASK-FE-RPT-003 |
| 技术栈 | React + DataTable + StatusBadge |
| 优先级 | P0 |
| 预估工时 | 4h |

**前置条件**: TASK-FE-RPT-001, TASK-FE-COMMON-003 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §7.1 (必须使用的组件)
- STATE_MACHINE.md v2.9 §7.5.1 (日报状态机)

#### 任务

实现日报表格组件：
1. 使用 DataTable 组件
2. 列定义：日期、项目、投手、账户、消耗、转化、CPL、状态
3. 状态列使用 StatusBadge
4. 支持行展开详情

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/daily-reports/components/DailyReportsTable.tsx` | 日报表格 | 120-150 |
| `src/features/daily-reports/components/columns.tsx` | 列定义 | 80-100 |

#### 思考要点（必须先分析）

1. **列定义**: 如何使用 TanStack Table 定义列？
2. **数字格式化**: 消耗和 CPL 如何格式化显示？
3. **状态显示**: 如何使用 StatusBadge 组件？
4. **行操作**: 如何添加行操作按钮？
5. **排序**: 哪些列需要支持排序？

#### 约束规则

1. 使用 DataTable 组件（禁止原生 table）
2. 状态列使用 StatusBadge
3. 金额格式化为 ¥X.XX 万
4. CPL 保留 2 位小数

#### 代码参考

**文件 1: src/features/daily-reports/components/columns.tsx**
```typescript
'use client';

/**
 * 日报表格列定义
 */
import { ColumnDef } from '@tanstack/react-table';
import { format } from 'date-fns';
import { StatusBadge } from '@/components/ui/status-badge';
import { Button } from '@/components/ui/button';
import { MoreHorizontal, Eye } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import type { DailyReport } from '../types/dailyReport.types';

interface ColumnOptions {
  onView: (report: DailyReport) => void;
}

export function createColumns({ onView }: ColumnOptions): ColumnDef<DailyReport>[] {
  return [
    {
      accessorKey: 'report_date',
      header: '日期',
      cell: ({ row }) => format(new Date(row.getValue('report_date')), 'yyyy-MM-dd'),
    },
    {
      accessorKey: 'project_name',
      header: '项目',
    },
    {
      accessorKey: 'pitcher_name',
      header: '投手',
    },
    {
      accessorKey: 'account_name',
      header: '账户',
    },
    {
      accessorKey: 'ad_spend',
      header: '消耗',
      cell: ({ row }) => {
        const amount = Number(row.getValue('ad_spend')) || 0;
        return amount >= 10000
          ? `¥${(amount / 10000).toFixed(2)}万`
          : `¥${amount.toFixed(2)}`;
      },
    },
    {
      accessorKey: 'conversions',
      header: '转化',
      cell: ({ row }) => (Number(row.getValue('conversions')) || 0).toLocaleString(),
    },
    {
      accessorKey: 'cpl',
      header: 'CPL',
      cell: ({ row }) => {
        const spend = Number(row.original.ad_spend) || 0;
        const conversions = Number(row.original.conversions) || 1;
        return `¥${(spend / conversions).toFixed(2)}`;
      },
    },
    {
      accessorKey: 'status',
      header: '状态',
      cell: ({ row }) => (
        <StatusBadge
          type="daily_report"
          status={row.getValue('status')}
          size="sm"
        />
      ),
    },
    {
      id: 'actions',
      cell: ({ row }) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => onView(row.original)}>
              <Eye className="mr-2 h-4 w-4" />
              查看详情
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];
}
```

**文件 2: src/features/daily-reports/components/DailyReportsTable.tsx**
```typescript
'use client';

/**
 * 日报表格组件
 */
import { useMemo, useState } from 'react';
import { DataTable } from '@/components/ui/data-table';
import { createColumns } from './columns';
import { DailyReportDetailDialog } from './DailyReportDetailDialog';
import type { DailyReport } from '../types/dailyReport.types';

interface DailyReportsTableProps {
  data: DailyReport[];
  isLoading?: boolean;
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    onPageChange: (page: number) => void;
  };
}

export function DailyReportsTable({
  data,
  isLoading,
  pagination,
}: DailyReportsTableProps) {
  const [selectedReport, setSelectedReport] = useState<DailyReport | null>(null);

  const columns = useMemo(
    () => createColumns({ onView: setSelectedReport }),
    []
  );

  return (
    <>
      <DataTable
        columns={columns}
        data={data}
        loading={isLoading}
        pagination={pagination}
      />

      {selectedReport && (
        <DailyReportDetailDialog
          report={selectedReport}
          open={!!selectedReport}
          onOpenChange={(open) => !open && setSelectedReport(null)}
        />
      )}
    </>
  );
}

export default DailyReportsTable;
```

#### 验收标准

- [ ] 使用 DataTable 组件
- [ ] 显示字段：日期、项目、投手、账户、消耗、转化、CPL、状态
- [ ] 状态列使用 StatusBadge 组件
- [ ] 支持行点击展开详情
- [ ] 支持列排序
- [ ] `npx tsc --noEmit` 无错误

---

### TASK-FE-RPT-004: 日报提交表单

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | daily-reports |
| 任务 ID | TASK-FE-RPT-004 |
| 技术栈 | react-hook-form + zod |
| 优先级 | P0 |
| 预估工时 | 4h |

**前置条件**: TASK-FE-RPT-001 已完成

**SoT 引用**:
- API_SOT.md v9.7 (POST /api/v1/daily-reports)
- BUSINESS_RULES.md BR-RPT-001 (日报提交规则)

#### 任务

实现日报提交表单：
1. 仅投手可提交
2. 必填字段验证
3. 使用 react-hook-form + zod
4. 提交成功后状态为 raw_submitted

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/daily-reports/components/DailyReportForm.tsx` | 日报表单 | 150-180 |
| `src/features/daily-reports/components/DailyReportFormSchema.ts` | 验证 Schema | 30-40 |
| `src/features/daily-reports/hooks/useDailyReportMutations.ts` | 变更 Hook | 40-60 |

#### 思考要点（必须先分析）

1. **权限检查**: 如何确保只有投手可提交？
2. **账户选择**: 投手只能选择分配给自己的账户？
3. **日期限制**: 能否提交未来日期的日报？
4. **初始状态**: 提交后状态为什么是 raw_submitted？
5. **成功反馈**: 提交成功后如何提示用户？

#### 约束规则

1. 仅投手（media_buyer）可提交日报
2. 必填字段：日期、账户、消耗、转化
3. 提交后状态为 raw_submitted
4. 使用 toast 显示成功/失败

#### 代码参考

**文件 1: src/features/daily-reports/components/DailyReportFormSchema.ts**
```typescript
/**
 * 日报表单验证 Schema
 */
import { z } from 'zod';

export const dailyReportFormSchema = z.object({
  report_date: z.string().min(1, '请选择日期'),
  ad_account_id: z.number({ required_error: '请选择账户' }),
  ad_spend: z.number({ required_error: '请输入消耗金额' }).min(0, '消耗不能为负'),
  conversions: z.number({ required_error: '请输入转化数' }).min(0, '转化不能为负'),
  note: z.string().optional(),
});

export type DailyReportFormValues = z.infer<typeof dailyReportFormSchema>;
```

**文件 2: src/features/daily-reports/components/DailyReportForm.tsx**
```typescript
'use client';

/**
 * 日报提交表单
 * SoT: BUSINESS_RULES.md BR-RPT-001
 */
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { format } from 'date-fns';
import { toast } from 'sonner';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { DatePicker } from '@/components/ui/date-picker';
import { usePermission } from '@/hooks/usePermission';
import { useDailyReportMutations } from '../hooks/useDailyReportMutations';
import { dailyReportFormSchema, type DailyReportFormValues } from './DailyReportFormSchema';

interface DailyReportFormProps {
  accounts: { id: number; name: string }[];
  onSuccess?: () => void;
}

export function DailyReportForm({ accounts, onSuccess }: DailyReportFormProps) {
  const { can } = usePermission();
  const { createMutation } = useDailyReportMutations();

  // 权限检查：仅投手可提交
  if (!can('daily_report:create')) {
    return <p className="text-muted-foreground">您没有权限提交日报</p>;
  }

  const form = useForm<DailyReportFormValues>({
    resolver: zodResolver(dailyReportFormSchema),
    defaultValues: {
      report_date: format(new Date(), 'yyyy-MM-dd'),
      ad_spend: 0,
      conversions: 0,
      note: '',
    },
  });

  const onSubmit = async (values: DailyReportFormValues) => {
    try {
      await createMutation.mutateAsync(values);
      toast.success('日报提交成功');
      form.reset();
      onSuccess?.();
    } catch (error) {
      toast.error((error as Error).message || '提交失败');
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <FormField
          control={form.control}
          name="report_date"
          render={({ field }) => (
            <FormItem>
              <FormLabel>日期 *</FormLabel>
              <FormControl>
                <DatePicker
                  value={field.value ? new Date(field.value) : undefined}
                  onChange={(date) => field.onChange(date ? format(date, 'yyyy-MM-dd') : '')}
                  maxDate={new Date()}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="ad_account_id"
          render={({ field }) => (
            <FormItem>
              <FormLabel>广告账户 *</FormLabel>
              <Select
                value={field.value?.toString()}
                onValueChange={(v) => field.onChange(parseInt(v))}
              >
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="选择账户" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {accounts.map((account) => (
                    <SelectItem key={account.id} value={account.id.toString()}>
                      {account.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="ad_spend"
            render={({ field }) => (
              <FormItem>
                <FormLabel>消耗金额 *</FormLabel>
                <FormControl>
                  <Input
                    type="number"
                    placeholder="0.00"
                    {...field}
                    onChange={(e) => field.onChange(parseFloat(e.target.value) || 0)}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="conversions"
            render={({ field }) => (
              <FormItem>
                <FormLabel>转化数 *</FormLabel>
                <FormControl>
                  <Input
                    type="number"
                    placeholder="0"
                    {...field}
                    onChange={(e) => field.onChange(parseInt(e.target.value) || 0)}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <FormField
          control={form.control}
          name="note"
          render={({ field }) => (
            <FormItem>
              <FormLabel>备注</FormLabel>
              <FormControl>
                <Textarea placeholder="可选备注信息" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <Button type="submit" disabled={createMutation.isPending}>
          {createMutation.isPending ? '提交中...' : '提交日报'}
        </Button>
      </form>
    </Form>
  );
}

export default DailyReportForm;
```

**文件 3: src/features/daily-reports/hooks/useDailyReportMutations.ts**
```typescript
'use client';

/**
 * 日报变更操作 Hook
 */
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiPost, apiPatch } from '@/lib/api';
import type { DailyReportFormValues } from '../components/DailyReportFormSchema';

export function useDailyReportMutations() {
  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: (data: DailyReportFormValues) =>
      apiPost('/api/v1/daily-reports', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['daily-reports'] });
    },
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      apiPatch(`/api/v1/daily-reports/${id}/status`, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['daily-reports'] });
    },
  });

  return {
    createMutation,
    updateStatusMutation,
  };
}

export default useDailyReportMutations;
```

#### 验收标准

- [ ] 仅投手可提交日报
- [ ] 必填字段：日期、账户、消耗、转化
- [ ] 使用 react-hook-form + zod 验证
- [ ] 提交成功显示 toast 通知
- [ ] 提交后状态为 raw_submitted
- [ ] `npx tsc --noEmit` 无错误

---

### TASK-FE-RPT-005: 日报审核操作

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | daily-reports |
| 任务 ID | TASK-FE-RPT-005 |
| 技术栈 | React + usePermission |
| 优先级 | P0 |
| 预估工时 | 4h |

**前置条件**: TASK-FE-RPT-003, TASK-FE-COMMON-002 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (权限矩阵)
- API_SOT.md v9.7 (PATCH /api/v1/daily-reports/{id}/status)
- STATE_MACHINE.md v2.9 §7.5.1

#### 任务

实现日报审核操作：
1. 审核操作按钮组件
2. 审核确认弹窗
3. 状态流转：raw_submitted → trend_ok → final_confirmed

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/daily-reports/components/DailyReportReviewActions.tsx` | 审核操作按钮 | 80-100 |
| `src/features/daily-reports/components/DailyReportReviewDialog.tsx` | 审核确认弹窗 | 60-80 |

#### 思考要点（必须先分析）

1. **权限检查**: 谁可以审核日报？
2. **状态流转**: Phase 1 的状态流转路径是什么？
3. **确认弹窗**: 审核前为什么需要确认？
4. **刷新列表**: 审核后如何刷新列表？
5. **批量审核**: 是否需要支持批量审核？

#### 约束规则

1. 仅项目负责人和 Admin 可审核
2. raw_submitted → trend_ok：确认趋势
3. trend_ok → final_confirmed：最终确认
4. 审核前需确认弹窗
5. 审核后自动刷新列表

#### 代码参考

**文件 1: src/features/daily-reports/components/DailyReportReviewActions.tsx**
```typescript
'use client';

/**
 * 日报审核操作按钮
 * SoT: STATE_MACHINE.md v2.9 §7.5.1
 */
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { CheckCircle, Lock } from 'lucide-react';
import { usePermission } from '@/hooks/usePermission';
import { DailyReportReviewDialog } from './DailyReportReviewDialog';
import type { DailyReport } from '../types/dailyReport.types';
import type { DailyReportStatus } from '@/types/status';

interface DailyReportReviewActionsProps {
  report: DailyReport;
  onReviewSuccess?: () => void;
}

// Phase 1 状态转换配置
const STATUS_TRANSITIONS: Record<DailyReportStatus, {
  nextStatus: DailyReportStatus | null;
  label: string;
  icon: React.ReactNode;
}> = {
  raw_submitted: {
    nextStatus: 'trend_ok',
    label: '确认趋势',
    icon: <CheckCircle className="mr-2 h-4 w-4" />,
  },
  trend_ok: {
    nextStatus: 'final_confirmed',
    label: '最终确认',
    icon: <Lock className="mr-2 h-4 w-4" />,
  },
  final_confirmed: {
    nextStatus: null,
    label: '已确认',
    icon: null,
  },
};

export function DailyReportReviewActions({
  report,
  onReviewSuccess,
}: DailyReportReviewActionsProps) {
  const { can } = usePermission();
  const [showDialog, setShowDialog] = useState(false);

  // 权限检查：项目负责人或 Admin 可审核
  const canReview = can('daily_report:review');

  const transition = STATUS_TRANSITIONS[report.status as DailyReportStatus];

  // 无下一状态或无权限时不显示按钮
  if (!transition.nextStatus || !canReview) {
    return null;
  }

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setShowDialog(true)}
      >
        {transition.icon}
        {transition.label}
      </Button>

      <DailyReportReviewDialog
        open={showDialog}
        onOpenChange={setShowDialog}
        report={report}
        nextStatus={transition.nextStatus}
        actionLabel={transition.label}
        onSuccess={onReviewSuccess}
      />
    </>
  );
}

export default DailyReportReviewActions;
```

**文件 2: src/features/daily-reports/components/DailyReportReviewDialog.tsx**
```typescript
'use client';

/**
 * 日报审核确认弹窗
 */
import { toast } from 'sonner';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { useDailyReportMutations } from '../hooks/useDailyReportMutations';
import type { DailyReport } from '../types/dailyReport.types';
import type { DailyReportStatus } from '@/types/status';

interface DailyReportReviewDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  report: DailyReport;
  nextStatus: DailyReportStatus;
  actionLabel: string;
  onSuccess?: () => void;
}

export function DailyReportReviewDialog({
  open,
  onOpenChange,
  report,
  nextStatus,
  actionLabel,
  onSuccess,
}: DailyReportReviewDialogProps) {
  const { updateStatusMutation } = useDailyReportMutations();

  const handleConfirm = async () => {
    try {
      await updateStatusMutation.mutateAsync({
        id: report.id,
        status: nextStatus,
      });
      toast.success(`${actionLabel}成功`);
      onOpenChange(false);
      onSuccess?.();
    } catch (error) {
      toast.error((error as Error).message || '操作失败');
    }
  };

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>确认{actionLabel}？</AlertDialogTitle>
          <AlertDialogDescription>
            您确定要将此日报标记为"{actionLabel}"吗？此操作将更新日报状态。
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>取消</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleConfirm}
            disabled={updateStatusMutation.isPending}
          >
            {updateStatusMutation.isPending ? '处理中...' : '确认'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

export default DailyReportReviewDialog;
```

#### 验收标准

- [ ] 仅项目负责人和 Admin 可审核
- [ ] raw_submitted → trend_ok：确认趋势
- [ ] trend_ok → final_confirmed：最终确认
- [ ] 审核前需确认弹窗
- [ ] 审核后自动刷新列表
- [ ] `npx tsc --noEmit` 无错误

---

### TASK-FE-RPT-006: 日报状态流转 UI

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | daily-reports |
| 任务 ID | TASK-FE-RPT-006 |
| 技术栈 | React + State Machine |
| 优先级 | P0 |
| 预估工时 | 4h |

**前置条件**: TASK-FE-RPT-005 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §3.1 (日报状态机)
- STATE_MACHINE.md v2.9 §7.5.1 (Phase 1)
- BUSINESS_RULES.md BR-RPT-004

#### 任务

实现日报状态流转 UI：
1. 状态流转可视化组件
2. 状态操作按钮增强
3. Phase 1 仅 3 状态

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/daily-reports/components/DailyReportStatusFlow.tsx` | 状态流转可视化 | 60-80 |
| `src/features/daily-reports/lib/status-transitions.ts` | 状态转换逻辑 | 40-50 |

#### 约束规则

1. Phase 1 仅 3 状态: raw_submitted → trend_ok → final_confirmed
2. 无 Phase 2 状态 (trend_pending, trend_flagged 等)
3. 无自动风控阻断逻辑
4. 审核权限限制为 project_owner 和 admin

#### 代码参考

**文件 1: src/features/daily-reports/lib/status-transitions.ts**
```typescript
/**
 * 日报状态转换逻辑 (Phase 1)
 * SoT: STATE_MACHINE.md v2.9 §7.5.1
 */
import type { DailyReportStatus } from '@/types/status';
import type { BusinessRole } from '@/types/roles';

interface StatusTransition {
  from: DailyReportStatus;
  to: DailyReportStatus;
  label: string;
  allowedRoles: BusinessRole[];
}

// Phase 1 状态转换定义
export const DAILY_REPORT_TRANSITIONS: StatusTransition[] = [
  {
    from: 'raw_submitted',
    to: 'trend_ok',
    label: '确认趋势',
    allowedRoles: ['project_owner', 'admin', 'ceo'],
  },
  {
    from: 'trend_ok',
    to: 'final_confirmed',
    label: '最终确认',
    allowedRoles: ['project_owner', 'admin', 'ceo'],
  },
];

export function getNextStatus(
  currentStatus: DailyReportStatus
): DailyReportStatus | null {
  const transition = DAILY_REPORT_TRANSITIONS.find(
    (t) => t.from === currentStatus
  );
  return transition?.to ?? null;
}

export function canTransition(
  currentStatus: DailyReportStatus,
  targetStatus: DailyReportStatus,
  userRole: BusinessRole
): boolean {
  const transition = DAILY_REPORT_TRANSITIONS.find(
    (t) => t.from === currentStatus && t.to === targetStatus
  );
  return transition?.allowedRoles.includes(userRole) ?? false;
}
```

**文件 2: src/features/daily-reports/components/DailyReportStatusFlow.tsx**
```typescript
'use client';

/**
 * 日报状态流转可视化
 * Phase 1: 3 状态
 */
import { Check, Circle, ArrowRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { DailyReportStatus } from '@/types/status';
import { DAILY_REPORT_STATUS_CONFIG } from '@/lib/constants/status-variants';

interface DailyReportStatusFlowProps {
  currentStatus: DailyReportStatus;
}

const STATUS_ORDER: DailyReportStatus[] = [
  'raw_submitted',
  'trend_ok',
  'final_confirmed',
];

export function DailyReportStatusFlow({ currentStatus }: DailyReportStatusFlowProps) {
  const currentIndex = STATUS_ORDER.indexOf(currentStatus);

  return (
    <div className="flex items-center justify-center gap-2">
      {STATUS_ORDER.map((status, index) => {
        const isCompleted = index < currentIndex;
        const isCurrent = index === currentIndex;
        const config = DAILY_REPORT_STATUS_CONFIG[status];

        return (
          <div key={status} className="flex items-center">
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  'flex h-8 w-8 items-center justify-center rounded-full border-2',
                  isCompleted && 'border-green-500 bg-green-500 text-white',
                  isCurrent && 'border-blue-500 bg-blue-50',
                  !isCompleted && !isCurrent && 'border-gray-300'
                )}
              >
                {isCompleted ? (
                  <Check className="h-4 w-4" />
                ) : (
                  <Circle className="h-3 w-3" />
                )}
              </div>
              <span className="mt-1 text-xs">{config.label}</span>
            </div>
            {index < STATUS_ORDER.length - 1 && (
              <ArrowRight className="mx-2 h-4 w-4 text-gray-400" />
            )}
          </div>
        );
      })}
    </div>
  );
}

export default DailyReportStatusFlow;
```

#### 验收标准

- [ ] Phase 1 仅 3 状态: raw_submitted → trend_ok → final_confirmed
- [ ] 状态流转按钮根据用户权限显示/隐藏
- [ ] 投手只能查看，项目负责人可操作审核
- [ ] 终态无操作按钮
- [ ] 无自动风控阻断逻辑
- [ ] `npx tsc --noEmit` 无错误

---

### TASK-FE-RPT-007: 日报详情弹窗

#### 上下文

| 项目 | AI 广告代投系统 - 前端 |
|------|----------------------|
| 模块 | daily-reports |
| 任务 ID | TASK-FE-RPT-007 |
| 技术栈 | React + Dialog |
| 优先级 | P0 |
| 预估工时 | 3h |

**前置条件**: TASK-FE-RPT-003 已完成

**SoT 引用**:
- FRONTEND_PAGE_DESIGN_v2.1.md §7.1 (必须使用的组件)

#### 任务

实现日报详情弹窗：
1. 显示日报完整信息
2. 显示状态流转历史
3. 根据权限显示操作按钮

#### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| `src/features/daily-reports/components/DailyReportDetailDialog.tsx` | 日报详情弹窗 | 120-150 |
| `src/features/daily-reports/hooks/useDailyReport.ts` | 单条数据 Hook | 25-35 |

#### 代码参考

**文件 1: src/features/daily-reports/components/DailyReportDetailDialog.tsx**
```typescript
'use client';

/**
 * 日报详情弹窗
 */
import { format } from 'date-fns';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { StatusBadge } from '@/components/ui/status-badge';
import { Separator } from '@/components/ui/separator';
import { DailyReportStatusFlow } from './DailyReportStatusFlow';
import { DailyReportReviewActions } from './DailyReportReviewActions';
import type { DailyReport } from '../types/dailyReport.types';
import type { DailyReportStatus } from '@/types/status';

interface DailyReportDetailDialogProps {
  report: DailyReport;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function DailyReportDetailDialog({
  report,
  open,
  onOpenChange,
}: DailyReportDetailDialogProps) {
  const formatAmount = (amount: number) =>
    amount >= 10000
      ? `¥${(amount / 10000).toFixed(2)}万`
      : `¥${amount.toFixed(2)}`;

  const cpl = report.conversions > 0
    ? report.ad_spend / report.conversions
    : 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>日报详情</DialogTitle>
        </DialogHeader>

        {/* 状态流转 */}
        <div className="py-4">
          <DailyReportStatusFlow
            currentStatus={report.status as DailyReportStatus}
          />
        </div>

        <Separator />

        {/* 基本信息 */}
        <div className="grid grid-cols-2 gap-4 py-4">
          <div>
            <p className="text-sm text-muted-foreground">日期</p>
            <p className="font-medium">
              {format(new Date(report.report_date), 'yyyy-MM-dd')}
            </p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">状态</p>
            <StatusBadge
              type="daily_report"
              status={report.status as DailyReportStatus}
            />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">项目</p>
            <p className="font-medium">{report.project_name}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">投手</p>
            <p className="font-medium">{report.pitcher_name}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">账户</p>
            <p className="font-medium">{report.account_name}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">消耗</p>
            <p className="font-medium">{formatAmount(report.ad_spend)}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">转化</p>
            <p className="font-medium">{report.conversions.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">CPL</p>
            <p className="font-medium">¥{cpl.toFixed(2)}</p>
          </div>
        </div>

        {report.note && (
          <>
            <Separator />
            <div className="py-4">
              <p className="text-sm text-muted-foreground">备注</p>
              <p className="mt-1">{report.note}</p>
            </div>
          </>
        )}

        <Separator />

        {/* 操作按钮 */}
        <div className="flex justify-end py-4">
          <DailyReportReviewActions
            report={report}
            onReviewSuccess={() => onOpenChange(false)}
          />
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default DailyReportDetailDialog;
```

**文件 2: src/features/daily-reports/hooks/useDailyReport.ts**
```typescript
'use client';

/**
 * 单条日报数据 Hook
 */
import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/lib/api';
import type { DailyReport } from '../types/dailyReport.types';

export function useDailyReport(id: number) {
  return useQuery<DailyReport>({
    queryKey: ['daily-reports', id],
    queryFn: () => apiGet<DailyReport>(`/api/v1/daily-reports/${id}`),
    enabled: !!id,
  });
}

export default useDailyReport;
```

#### 验收标准

- [ ] 使用 Dialog 组件
- [ ] 显示日报完整信息
- [ ] 显示状态流转历史
- [ ] 显示操作按钮（根据权限）
- [ ] `npx tsc --noEmit` 无错误

---

**版本**: v2.3 (批次2扩展版)
**更新日期**: 2026-01-05
**优化内容**:
- 新增快速入门指南和流程图
- 增强系统约束（防幻觉规则场景映射、自洽性检查清单）
- 增强任务模板（思考要点、边缘情况、提交前自检）
- 完善 COMMON 模块（COMMON-001~005）
- 完善 DASH 驾驶舱模块（DASH-001~006）
- 完善 RPT 日报模块（RPT-001~007）
- 新增 PROJ 模块提示词（PROJ-001）
- 新增 ACCT 模块提示词（ACCT-001）
- 新增 TOP 模块提示词（TOP-004）

**已完成任务卡**（34 个）:
- TASK-FE-COMMON-001: 类型定义与常量
- TASK-FE-COMMON-002: 权限检查 Hook
- TASK-FE-COMMON-003: 状态配置与 StatusBadge
- TASK-FE-COMMON-004: 导航访问控制
- TASK-FE-COMMON-005: 通用列表页模板
- TASK-FE-DASH-001: 驾驶舱页面框架
- TASK-FE-DASH-002: KPI 卡片组件
- TASK-FE-DASH-003: 趋势图表组件
- TASK-FE-DASH-004: 待办事项卡片
- TASK-FE-DASH-005: 快捷操作组件
- TASK-FE-DASH-006: 角色视图切换
- TASK-FE-RPT-001: 日报列表页
- TASK-FE-RPT-002: 日报筛选器
- TASK-FE-RPT-003: 日报表格组件
- TASK-FE-RPT-004: 日报提交表单
- TASK-FE-RPT-005: 日报审核操作
- TASK-FE-RPT-006: 日报状态流转 UI
- TASK-FE-RPT-007: 日报详情弹窗
- TASK-FE-PROJ-001: 项目列表页
- TASK-FE-PROJ-002: 项目筛选器
- TASK-FE-PROJ-003: 项目表格组件
- TASK-FE-PROJ-004: 项目创建/编辑表单
- TASK-FE-PROJ-005: 项目详情页
- TASK-FE-PROJ-006: 项目成员管理
- TASK-FE-PROJ-007: 项目状态流转
- TASK-FE-ACCT-001: 账户列表页
- TASK-FE-ACCT-002: 账户状态看板
- TASK-FE-ACCT-003: 账户筛选器
- TASK-FE-ACCT-004: 账户表格组件
- TASK-FE-ACCT-005: 账户创建/编辑表单
- TASK-FE-ACCT-006: 账户分配操作
- TASK-FE-ACCT-007: 账户状态流转
- TASK-FE-ACCT-008: 账户详情弹窗
- TASK-FE-TOP-004: 充值申请表单

**待补充模块**:
- CHAN 渠道模块（4 个任务卡: 001-004）
- TOP 充值模块（6 个任务卡: 001-003, 005-007）
- FIN 财务模块（5 个任务卡: 001-005）
- USER 用户模块（5 个任务卡: 001-005）
- SET 设置模块（3 个任务卡: 001-003）
- 新增 DASH 模块提示词（DASH-001~006）
- 新增 PROJ 模块提示词（PROJ-001）
- 新增 ACCT 模块提示词（ACCT-001）
- 完善 COMMON 模块提示词（COMMON-001~005）
- 新增 RPT、TOP 模块提示词
- 新增快速参考（状态机、权限矩阵、组件模式、问题诊断）

**已完成任务卡**（15 个）:
- TASK-FE-COMMON-001: 类型定义与常量
- TASK-FE-COMMON-002: 权限检查 Hook
- TASK-FE-COMMON-003: 状态配置与 StatusBadge
- TASK-FE-COMMON-004: 导航访问控制
- TASK-FE-COMMON-005: 通用列表页模板
- TASK-FE-DASH-001: 驾驶舱页面框架
- TASK-FE-DASH-002: KPI 卡片组件
- TASK-FE-DASH-003: 趋势图表组件
- TASK-FE-DASH-004: 待办事项卡片
- TASK-FE-DASH-005: 快捷操作组件
- TASK-FE-DASH-006: 角色视图切换
- TASK-FE-RPT-001: 日报列表页
- TASK-FE-PROJ-001: 项目列表页
- TASK-FE-ACCT-001: 账户列表页
- TASK-FE-TOP-004: 充值申请表单

**待补充模块**:
- RPT 日报模块（6 个任务卡: 002-007）
- PROJ 项目模块（6 个任务卡: 002-007）
- ACCT 账户模块（7 个任务卡: 002-008）
- CHAN 渠道模块（4 个任务卡）
- TOP 充值模块（6 个任务卡: 001-003, 005-007）
- FIN 财务模块（5 个任务卡）
- USER 用户模块（5 个任务卡）
- SET 设置模块（3 个任务卡）
