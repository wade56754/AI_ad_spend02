# AI 广告代投系统 - 前端功能任务卡文档

> **文档版本**: v1.0
> **生成日期**: 2026-01-04
> **基准文档**: FRONTEND_PAGE_DESIGN_v2.1.md, TASK_CARDS_v2.md
> **SoT 对齐**: MASTER.md v4.9 | STATE_MACHINE.md v2.9 | DATA_SCHEMA.md v5.11 | BUSINESS_RULES.md v5.2 | API_SOT.md v9.7
> **用途**: 前端开发任务分解与跟踪

---

## 文档目录

1. [SoT 版本对齐表](#sot-版本对齐表)
2. [角色白名单](#角色白名单)
3. [模块依赖关系图](#模块依赖关系图)
4. [Phase 分组视图](#phase-分组视图)
5. [COMMON 通用模块](#common-通用模块)
6. [DASH 驾驶舱模块](#dash-驾驶舱模块)
7. [RPT 日报模块](#rpt-日报模块)
8. [PROJ 项目模块](#proj-项目模块)
9. [ACCT 账户模块](#acct-账户模块)
10. [CHAN 渠道模块](#chan-渠道模块)
11. [TOP 充值模块](#top-充值模块)
12. [FIN 财务模块](#fin-财务模块)
13. [USER 用户模块](#user-用户模块)
14. [SET 设置模块](#set-设置模块)
15. [统计汇总](#统计汇总)

---

## SoT 版本对齐表（任务卡基准）

> **注意**: STATE_MACHINE.md v2.9 内部引用 MASTER.md v4.9，本任务卡使用 MASTER.md v4.9。
> 差异点：v4.9 新增 isCeo() 判断规则说明，其他内容无变化。

| 文档 | 版本 | 路径 | 状态 |
|------|------|------|------|
| MASTER.md | v4.9 | docs/sot/MASTER.md | Frozen |
| STATE_MACHINE.md | v2.9 | docs/sot/STATE_MACHINE.md | Frozen |
| DATA_SCHEMA.md | v5.11 | docs/sot/DATA_SCHEMA.md | Frozen |
| BUSINESS_RULES.md | v5.2 | docs/sot/BUSINESS_RULES.md | Frozen |
| API_SOT.md | v9.7 | docs/sot/API_SOT.md | Frozen |
| ERROR_CODES_SOT.md | v2.2 | docs/sot/ERROR_CODES_SOT.md | Frozen |
| AUTH_SPEC.md | v2.2 | docs/sot/AUTH_SPEC.md | Frozen |
| FRONTEND_PAGE_DESIGN_v2.1.md | v2.1 | docs/design/FRONTEND_PAGE_DESIGN_v2.1.md | Active |

---

## 角色白名单（6 角色）

> **来源**: MASTER.md v4.9 §2.4, DATA_SCHEMA.md v5.11 §1.1

### 技术层角色（4 角色）

| 技术角色 | 数据库值 | 说明 |
|----------|----------|------|
| `admin` | admin | 系统管理员 |
| `finance` | finance | 财务人员 |
| `account_manager` | account_manager | 户管 |
| `media_buyer` | media_buyer | 投手（技术层） |

### 业务层角色映射

| 业务角色 | 技术实现 | 说明 |
|----------|----------|------|
| 老板 (ceo) | `role = 'admin'` + `isCeo()` | CEO 身份通过业务逻辑判断 |
| 项目负责人 (project_owner) | `is_project_owner = true` | 数据库布尔字段 |
| 财务 (finance) | `role = 'finance'` | 直接映射 |
| 投手 (pitcher) | `role = 'media_buyer'` | 业务名→技术名 |
| 户管 (account_manager) | `role = 'account_manager'` | 直接映射 |
| 管理员 (admin) | `role = 'admin'` | 直接映射 |

### 禁止使用的角色

| 角色 | 状态 | 替代方案 |
|------|------|---------|
| `supervisor` | ❌ 已废弃 | 合并到 project_owner |
| `data_operator` | ❌ 已废弃 | 移除 |
| `media_buyer` | ⚠️ 仅技术层 | 业务层使用 pitcher |

---

## 模块依赖关系图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       前端模块依赖关系                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   COMMON (基础设施) ─────────────────────────────────────────────────┐  │
│      │                                                               │  │
│      ├──► DASH (驾驶舱) ◄────────────────────────────────────────────┤  │
│      │                                                               │  │
│      ├──► RPT (日报) ◄─── PROJ (项目)                                │  │
│      │       │              │                                        │  │
│      ├──► PROJ (项目)       │                                        │  │
│      │       │              │                                        │  │
│      ├──► ACCT (账户) ◄─── CHAN (渠道)                               │  │
│      │       │                                                       │  │
│      ├──► CHAN (渠道)                                                │  │
│      │                                                               │  │
│      ├──► TOP (充值) ─────► FIN (财务) ◄─────────────────────────────┤  │
│      │                                                               │  │
│      ├──► USER (用户)                                                │  │
│      │                                                               │  │
│      └──► SET (设置)                                                 │  │
│                                                                         │
│  图例: ──► 强依赖（必须先完成）   ◄── 数据依赖                           │
└─────────────────────────────────────────────────────────────────────────┘
```

**关键路径**: COMMON → PROJ → ACCT → RPT → FIN → DASH

---

## Phase 分组视图

### Phase 1 任务清单（MVP 核心）

> Phase 1 原则：记录事实、展示状态、提示异常，**不强制阻断**

| 模块 | 任务卡 | 任务数 | 工时 | 说明 |
|------|--------|--------|------|------|
| COMMON | TASK-FE-COMMON-001 ~ 005 | 5 | 18h | 基础设施 |
| DASH | TASK-FE-DASH-001 ~ 006 | 6 | 22h | 驾驶舱 |
| RPT | TASK-FE-RPT-001 ~ 007 | 7 | 28h | 日报（3状态） |
| PROJ | TASK-FE-PROJ-001 ~ 007 | 7 | 27h | 项目管理 |
| ACCT | TASK-FE-ACCT-001 ~ 008 | 8 | 30h | 账户管理 |
| CHAN | TASK-FE-CHAN-001 ~ 004 | 4 | 13h | 渠道管理 |
| TOP | TASK-FE-TOP-001 ~ 007 | 7 | 28h | 充值管理 |
| FIN | TASK-FE-FIN-001 ~ 005 | 5 | 22h | 财务中心 |
| USER | TASK-FE-USER-001 ~ 005 | 5 | 18h | 用户管理 |
| SET | TASK-FE-SET-001 ~ 003 | 3 | 10h | 系统设置 |

### 开发优先级说明

| 优先级 | 模块 | 说明 | 任务数 | 工时 |
|--------|------|------|--------|------|
| **P0** | COMMON, DASH, RPT, PROJ, ACCT | MVP 核心 | 33 | 125h |
| **P1** | CHAN, TOP | 业务支撑 | 11 | 41h |
| **P2** | FIN, USER | 管理功能 | 10 | 40h |
| **P3** | SET | 系统配置 | 3 | 10h |

---

## 状态机约束（Phase 1）

> **来源**: STATE_MACHINE.md v2.9, FRONTEND_PAGE_DESIGN_v2.1.md §3

### 日报状态机（3 状态）

```
raw_submitted → trend_ok → final_confirmed
     ↑              ↑              ↑
   投手提交      趋势确认      终态锁定
```

### 账户状态机（6 状态）

```
new → testing → active → suspended → dead
                  ↓
               archived
```

### 充值状态机（7 状态）

```
draft → pending_review → finance_approve → paid → completed
              ↓                              ↓
           rejected                      cancelled
```

### 项目状态机（4 状态）

```
draft → active → suspended → archived
```

---

# COMMON 通用模块

> **优先级**: P0
> **任务数**: 5
> **预估工时**: 18h
> **Phase**: Phase 1

## TASK-FE-COMMON-001: 类型定义与常量

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §2 (双层角色架构)
- FRONTEND_PAGE_DESIGN_v2.1.md §3 (状态机定义)
- FRONTEND_PAGE_DESIGN_v2.1.md §10 (技术实现清单)
- STATE_MACHINE.md v2.9 §7 (状态定义)
- DATA_SCHEMA.md v5.11 §1.1 (角色映射)

### 输入
- 无前置依赖

### 输出
```
frontend/src/types/
├── roles.ts                    # 角色类型定义
├── status.ts                   # 状态枚举定义
├── navigation.ts               # 导航类型定义
├── user.ts                     # 用户模型
└── index.ts                    # 统一导出

frontend/src/lib/constants/
├── roles.ts                    # 角色常量
├── status-config.ts            # 状态配置
└── index.ts                    # 统一导出
```

### 验收标准
- □ 技术层角色枚举仅包含 4 个值: admin, finance, account_manager, media_buyer
- □ 日报状态枚举仅包含 Phase 1 的 3 个状态
- □ 账户状态枚举包含 6 个状态
- □ 充值状态枚举包含 7 个状态
- □ 项目状态枚举包含 4 个状态
- □ User 接口包含 is_project_owner 布尔字段
- □ User 接口不包含 is_ceo 字段

### SoT 对齐验证
- □ 角色枚举与 DATA_SCHEMA.md v5.11 §1.1 一致
- □ 状态枚举与 STATE_MACHINE.md v2.9 §7 一致
- □ 无废弃角色 (supervisor, data_operator)
- □ 无 Phase 2 日报状态 (trend_pending, trend_flagged, final_pending, final_locked)

### 优先级与依赖
- Priority: P0
- Depends: 无
- Phase: Phase 1

### 预估工时
4h

---

## TASK-FE-COMMON-002: 权限检查 Hook (usePermission)

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §10.2 (权限检查 Hook)
- MASTER.md v4.9 §2.4 (权限矩阵)
- DATA_SCHEMA.md v5.11 §1.1 (角色映射规则)
- AUTH_SPEC.md v2.2 (认证授权规范)

### 输入
- TASK-FE-COMMON-001 已完成
- useAuth Hook 已存在

### 输出
```
frontend/src/hooks/
├── usePermission.ts            # 权限检查 Hook
└── index.ts                    # 统一导出

frontend/src/lib/constants/
└── permission-matrix.ts        # 权限矩阵定义

frontend/src/tests/hooks/
└── usePermission.test.ts       # 单元测试
```

### 验收标准
- □ 实现 `getBusinessRole()` 函数，返回业务层角色
- □ 实现 `can(action: string)` 方法，检查操作权限
- □ 实现 `isCeo()` 方法，判断 CEO 身份
  - 规则：`user.role === 'ceo'` 或 特定用户标识匹配（如环境变量 CEO_USER_ID）
- □ 实现 `isProjectOwner()` 方法，判断项目负责人身份
- □ 权限矩阵与 MASTER.md v4.9 §2.4 完全对齐
- □ 测试覆盖：6 业务角色 × 主要操作

### SoT 对齐验证
- □ CEO 身份通过 `isCeo()` 函数判断，非 `is_ceo` 字段
- □ 项目负责人通过 `is_project_owner` 布尔字段判断
- □ media_buyer 映射为 pitcher
- □ 权限矩阵不包含废弃角色

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-COMMON-001
- Phase: Phase 1

### 预估工时
4h

---

## TASK-FE-COMMON-003: 状态配置与 StatusBadge

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §7.2 (StatusBadge 配置)
- STATE_MACHINE.md v2.9 §7 (状态定义)

### 输入
- TASK-FE-COMMON-001 已完成

### 输出
```
frontend/src/components/ui/
└── status-badge.tsx            # 状态标签组件（增强）

frontend/src/lib/constants/
└── status-variants.ts          # 状态变体配置
```

### 验收标准
- □ 支持日报状态 (3 个): raw_submitted, trend_ok, final_confirmed
- □ 支持账户状态 (6 个): new, testing, active, suspended, dead, archived
- □ 支持充值状态 (7 个): draft, pending_review, finance_approve, paid, completed, rejected, cancelled
- □ 支持项目状态 (4 个): draft, active, suspended, archived
- □ 每个状态有对应的颜色和中文标签
- □ 组件支持 size 属性 (sm, md, lg)

### SoT 对齐验证
- □ 状态值与 STATE_MACHINE.md v2.9 完全一致
- □ 日报仅使用 Phase 1 的 3 个状态
- □ 状态中文标签与设计文档一致

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-COMMON-001
- Phase: Phase 1

### 预估工时
3h

---

## TASK-FE-COMMON-004: 导航访问控制 (canAccessNav)

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §5.2 (导航配置)
- MASTER.md v4.9 §2.4 (权限矩阵)

### 输入
- TASK-FE-COMMON-002 已完成

### 输出
```
frontend/src/lib/
├── navigation.ts               # 导航配置
└── access-control.ts           # 访问控制函数

frontend/src/types/
└── navigation.ts               # NavAccess 接口定义
```

### 验收标准
- □ 实现 `NavAccess` 接口（techRoles, requireProjectOwner, requireCeo, allowAll）
- □ 实现 `canAccessNav(user, access)` 函数
- □ 9 个页面路由的访问控制配置正确
- □ 驾驶舱、日报、充值对全部角色开放
- □ 项目管理对 ceo, project_owner, admin 开放
- □ 财务中心对 ceo, finance, admin 开放
- □ 系统设置仅对 admin 开放

### SoT 对齐验证
- □ 权限规则与 MASTER.md v4.9 §2.4 一致
- □ 使用 `isCeo()` 函数判断 CEO 身份
- □ 使用 `is_project_owner` 判断项目负责人

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-COMMON-002
- Phase: Phase 1

### 预估工时
3h

---

## TASK-FE-COMMON-005: 通用列表页模板

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §7.1 (必须使用的组件)
- FRONTEND_PAGE_DESIGN_v2.1.md §8 (API 调用规范)

### 输入
- TASK-FE-COMMON-003 已完成
- DataTable 组件已存在

### 输出
```
frontend/src/components/common/
├── ListPage.tsx                # 通用列表页模板
├── ListFilters.tsx             # 通用筛选器
├── ListPagination.tsx          # 分页组件
└── index.ts                    # 统一导出

frontend/src/hooks/
└── useListQuery.ts             # 列表查询 Hook（TanStack Query）
```

### 验收标准
- □ 封装 DataTable、筛选器、分页的通用模式
- □ 支持 TanStack Query 的 useQuery 模式
- □ 支持筛选条件的 URL 同步
- □ 支持加载状态、空状态、错误状态
- □ 使用 `apiGet` 进行 API 调用（禁止 fetch/axios）

### SoT 对齐验证
- □ API 调用使用 lib/api.ts 中的方法
- □ 错误处理遵循统一模式

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-COMMON-003
- Phase: Phase 1

### 预估工时
4h

---

# DASH 驾驶舱模块

> **优先级**: P0
> **任务数**: 6
> **预估工时**: 22h
> **Phase**: Phase 1

## TASK-FE-DASH-001: 驾驶舱页面框架

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §6.1 (驾驶舱设计)
- FRONTEND_PAGE_DESIGN_v2.1.md §5.1 (页面清单)

### 输入
- TASK-FE-COMMON-002 已完成

### 输出
```
frontend/src/app/dashboard/
└── page.tsx                    # 驾驶舱页面

frontend/src/features/dashboard/
├── components/
│   └── DashboardPage.tsx       # 页面组件
├── hooks/
│   └── useDashboardData.ts     # 数据查询 Hook
└── types/
    └── dashboard.types.ts      # 类型定义
```

### 验收标准
- □ 页面布局包含 KPI 卡片区、趋势图表、待办事项、快捷操作
- □ 根据用户角色显示不同数据
- □ 使用 TanStack Query 获取数据
- □ 响应式布局（桌面/平板）

### SoT 对齐验证
- □ 页面路由为 `/dashboard`
- □ 访问权限对全部角色开放

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-COMMON-002
- Phase: Phase 1

### 预估工时
4h

---

## TASK-FE-DASH-002: KPI 卡片组件

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §6.1.1 (角色视图差异)
- FRONTEND_PAGE_DESIGN_v2.1.md §6.1.2 (核心组件)

### 输入
- TASK-FE-DASH-001 已完成

### 输出
```
frontend/src/features/dashboard/components/
├── KPICards.tsx                # KPI 卡片容器
├── KPICard.tsx                 # 单个 KPI 卡片
└── kpi-config.ts               # KPI 配置

frontend/src/features/dashboard/hooks/
└── useKPIData.ts               # KPI 数据 Hook
```

### 验收标准
- □ CEO 视图：总消耗、总收入、毛利、ROI
- □ 项目负责人视图：项目消耗、项目利润、投手绩效
- □ 财务视图：账户余额、待审充值、月度流水
- □ 投手视图：我的日报、我的账户、我的CPL
- □ 户管视图：账户状态分布、待分配账户
- □ Admin 视图：用户统计、系统健康、操作日志
- □ 支持加载状态和错误状态

### SoT 对齐验证
- □ 角色判断使用 usePermission Hook
- □ CEO 身份使用 isCeo() 判断

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-DASH-001
- Phase: Phase 1

### 预估工时
4h

---

## TASK-FE-DASH-003: 趋势图表组件

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §6.1.2 (核心组件)

### 输入
- TASK-FE-DASH-001 已完成

### 输出
```
frontend/src/features/dashboard/components/
├── TrendCharts.tsx             # 趋势图表容器
├── SpendTrendChart.tsx         # 消耗趋势图
├── ConversionTrendChart.tsx    # 转化趋势图
└── chart-config.ts             # 图表配置

frontend/src/features/dashboard/hooks/
└── useTrendData.ts             # 趋势数据 Hook
```

### 验收标准
- □ 支持日/周/月时间维度切换
- □ 消耗趋势折线图
- □ 转化趋势折线图
- □ 响应式图表尺寸
- □ 使用 recharts 或类似图表库

### SoT 对齐验证
- □ 数据权限按角色过滤

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-DASH-001
- Phase: Phase 1

### 预估工时
5h

---

## TASK-FE-DASH-004: 待办事项卡片

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §6.1.2 (核心组件)

### 输入
- TASK-FE-DASH-001 已完成

### 输出
```
frontend/src/features/dashboard/components/
├── PendingTasks.tsx            # 待办事项容器
└── PendingTaskItem.tsx         # 单个待办项

frontend/src/features/dashboard/hooks/
└── usePendingTasks.ts          # 待办数据 Hook
```

### 验收标准
- □ 显示待审核日报（项目负责人）
- □ 显示待审批充值（财务）
- □ 显示待提交日报（投手）
- □ 点击跳转到对应页面
- □ 显示数量徽章

### SoT 对齐验证
- □ 待办项按角色权限过滤

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-DASH-001
- Phase: Phase 1

### 预估工时
3h

---

## TASK-FE-DASH-005: 快捷操作组件

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §6.1.2 (核心组件)

### 输入
- TASK-FE-DASH-001 已完成

### 输出
```
frontend/src/features/dashboard/components/
├── QuickActions.tsx            # 快捷操作容器
└── QuickActionButton.tsx       # 快捷操作按钮
```

### 验收标准
- □ 投手：提交日报、申请充值
- □ 项目负责人：审核日报、查看项目
- □ 财务：审批充值、查看账本
- □ 户管：分配账户、创建账户
- □ 按钮根据权限显示/隐藏

### SoT 对齐验证
- □ 操作权限与 MASTER.md v4.9 §2.4 一致

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-DASH-001
- Phase: Phase 1

### 预估工时
2h

---

## TASK-FE-DASH-006: 角色视图切换

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §6.1.1 (角色视图差异)

### 输入
- TASK-FE-DASH-002 已完成
- TASK-FE-COMMON-002 已完成

### 输出
```
frontend/src/features/dashboard/components/
├── RoleViewSwitcher.tsx        # 角色视图切换器
└── role-views.ts               # 角色视图配置

frontend/src/features/dashboard/hooks/
└── useRoleView.ts              # 角色视图状态 Hook
```

### 验收标准
- □ 自动检测用户角色并显示对应视图
- □ CEO/Admin 可切换查看其他角色视图
- □ 普通用户仅能查看自己角色视图
- □ 视图切换时数据自动刷新

### SoT 对齐验证
- □ 角色判断使用 usePermission Hook
- □ 视图切换权限符合业务规则

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-DASH-002, TASK-FE-COMMON-002
- Phase: Phase 1

### 预估工时
4h

---

# RPT 日报模块

> **优先级**: P0
> **任务数**: 7
> **预估工时**: 28h
> **Phase**: Phase 1
> **状态机**: 3 状态 (raw_submitted → trend_ok → final_confirmed)

## TASK-FE-RPT-001: 日报列表页

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §6.2 (日报管理)
- FRONTEND_PAGE_DESIGN_v2.1.md §5.1 (页面清单)
- API_SOT.md v9.7 (GET /api/v1/daily-reports)

### 输入
- TASK-FE-COMMON-005 已完成

### 输出
```
frontend/src/app/daily-reports/
└── page.tsx                    # 日报列表页

frontend/src/features/daily-reports/
├── components/
│   └── DailyReportsPage.tsx    # 页面组件
├── hooks/
│   └── useDailyReports.ts      # 列表数据 Hook
├── services/
│   └── dailyReportsApi.ts      # API 调用
└── types/
    └── dailyReport.types.ts    # 类型定义
```

### 验收标准
- □ 使用通用列表页模板
- □ 支持筛选、分页、排序
- □ 投手只能看到自己的日报
- □ 项目负责人可看到项目内全部日报
- □ CEO/Admin 可看到全部日报

### SoT 对齐验证
- □ API 端点使用 /api/v1/daily-reports
- □ 数据权限按角色过滤

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-COMMON-005
- Phase: Phase 1

### 预估工时
5h

---

## TASK-FE-RPT-002: 日报筛选器

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §6.2.1 (页面功能)

### 输入
- TASK-FE-RPT-001 已完成

### 输出
```
frontend/src/features/daily-reports/components/
└── DailyReportsFilters.tsx     # 日报筛选器
```

### 验收标准
- □ 日期范围筛选（默认最近 7 天）
- □ 状态筛选（3 个状态 + 全部）
- □ 项目筛选（根据权限过滤可选项）
- □ 投手筛选（项目负责人可用）
- □ 筛选条件同步到 URL

### SoT 对齐验证
- □ 状态筛选仅包含 Phase 1 的 3 个状态

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-RPT-001
- Phase: Phase 1

### 预估工时
3h

---

## TASK-FE-RPT-003: 日报表格组件

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §7.1 (必须使用的组件)
- STATE_MACHINE.md v2.9 §7.5.1 (日报状态机)

### 输入
- TASK-FE-RPT-001 已完成
- TASK-FE-COMMON-003 已完成

### 输出
```
frontend/src/features/daily-reports/components/
├── DailyReportsTable.tsx       # 日报表格
└── DailyReportRow.tsx          # 表格行组件
```

### 验收标准
- □ 使用 DataTable 组件
- □ 显示字段：日期、项目、投手、账户、消耗、转化、CPL、状态
- □ 状态列使用 StatusBadge 组件
- □ 支持行点击展开详情
- □ 支持列排序

### SoT 对齐验证
- □ 状态显示使用 StatusBadge
- □ 状态值仅使用 Phase 1 的 3 个

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-RPT-001, TASK-FE-COMMON-003
- Phase: Phase 1

### 预估工时
4h

---

## TASK-FE-RPT-004: 日报提交表单（投手）

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §6.2.1 (页面功能)
- API_SOT.md v9.7 (POST /api/v1/daily-reports)
- BUSINESS_RULES.md BR-RPT-001 (日报提交规则)

### 输入
- TASK-FE-RPT-001 已完成

### 输出
```
frontend/src/features/daily-reports/components/
├── DailyReportForm.tsx         # 日报提交表单
└── DailyReportFormSchema.ts    # 表单验证 Schema

frontend/src/features/daily-reports/hooks/
└── useDailyReportMutations.ts  # 变更操作 Hook
```

### 验收标准
- □ 仅投手可提交日报
- □ 必填字段：日期、账户、消耗、转化
- □ 选填字段：备注
- □ 使用 react-hook-form + zod 验证
- □ 提交成功显示 toast 通知
- □ 提交后状态为 raw_submitted

### SoT 对齐验证
- □ 权限检查使用技术层角色 `media_buyer`（对应业务层 pitcher）
- □ 初始状态为 raw_submitted

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-RPT-001
- Phase: Phase 1

### 预估工时
5h

---

## TASK-FE-RPT-005: 日报审核操作（项目负责人）

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §6.2.1 (页面功能)
- FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (权限矩阵)
- API_SOT.md v9.7 (PATCH /api/v1/daily-reports/{id}/status)

### 输入
- TASK-FE-RPT-003 已完成
- TASK-FE-COMMON-002 已完成

### 输出
```
frontend/src/features/daily-reports/components/
├── DailyReportReviewActions.tsx  # 审核操作按钮
└── DailyReportReviewDialog.tsx   # 审核确认弹窗
```

### 验收标准
- □ 仅项目负责人和 Admin 可审核
- □ raw_submitted → trend_ok：确认趋势
- □ trend_ok → final_confirmed：最终确认
- □ 审核前需确认弹窗
- □ 审核后自动刷新列表

### SoT 对齐验证
- □ 审核权限检查使用 usePermission
- □ 状态流转符合 STATE_MACHINE.md v2.9

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-RPT-003, TASK-FE-COMMON-002
- Phase: Phase 1

### 预估工时
4h

---

## TASK-FE-RPT-006: 日报状态流转 UI（Phase 1: 3 状态）

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §3.1 (日报状态机)
- STATE_MACHINE.md v2.9 §7.5.1 (Phase 1 日报状态机)
- BUSINESS_RULES.md BR-RPT-004 (状态流转合法性)

### 输入
- TASK-FE-RPT-005 已完成

### 输出
```
frontend/src/features/daily-reports/components/
├── DailyReportStatusFlow.tsx   # 状态流转可视化
└── DailyReportActions.tsx      # 状态操作按钮（增强）

frontend/src/features/daily-reports/lib/
└── status-transitions.ts       # 状态转换逻辑
```

### 验收标准
- □ Phase 1 仅实现 3 状态: raw_submitted → trend_ok → final_confirmed
- □ 状态流转按钮根据用户权限显示/隐藏
- □ 投手只能查看，项目负责人可操作审核
- □ 终态 (final_confirmed) 无操作按钮，显示"已确认"（Phase 1 无锁定约束）
- □ 状态变更后自动刷新列表
- □ 无自动风控阻断逻辑（Phase 1 约束）

### SoT 对齐验证
- □ 状态枚举仅使用 Phase 1 的 3 个状态
- □ 无 Phase 2 状态 (trend_pending, trend_flagged, final_pending, final_locked)
- □ 审核权限限制为 project_owner 和 admin
- □ 无 TF-001/002/003 风控规则（Phase 2 启用）

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-RPT-005
- Phase: Phase 1

### 预估工时
4h

---

## TASK-FE-RPT-007: 日报详情弹窗

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §7.1 (必须使用的组件)

### 输入
- TASK-FE-RPT-003 已完成

### 输出
```
frontend/src/features/daily-reports/components/
└── DailyReportDetailDialog.tsx # 日报详情弹窗

frontend/src/features/daily-reports/hooks/
└── useDailyReport.ts           # 单条数据 Hook
```

### 验收标准
- □ 使用 Dialog 组件
- □ 显示日报完整信息
- □ 显示状态流转历史
- □ 显示操作按钮（根据权限）

### SoT 对齐验证
- □ 使用 Dialog 组件（非 Modal）

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-RPT-003
- Phase: Phase 1

### 预估工时
3h

---

# PROJ 项目模块

> **优先级**: P0
> **任务数**: 7
> **预估工时**: 27h
> **Phase**: Phase 1
> **状态机**: 4 状态 (draft → active → suspended → archived)

## TASK-FE-PROJ-001: 项目列表页

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §5.1 (页面清单)
- FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (权限矩阵)
- API_SOT.md v9.7 (GET /api/v1/projects)

### 输入
- TASK-FE-COMMON-005 已完成

### 输出
```
frontend/src/app/projects/
└── page.tsx                    # 项目列表页

frontend/src/features/projects/
├── components/
│   └── ProjectsPage.tsx        # 页面组件
├── hooks/
│   └── useProjects.ts          # 列表数据 Hook
├── services/
│   └── projectsApi.ts          # API 调用
└── types/
    └── project.types.ts        # 类型定义
```

### 验收标准
- □ 使用通用列表页模板
- □ 支持筛选、分页、排序
- □ ceo, project_owner, finance（只读）, admin 可访问
- □ 项目负责人只能看到自己负责的项目
- □ 财务可查看项目盈亏数据（只读）

### SoT 对齐验证
- □ 访问权限与 MASTER.md v4.9 §2.4 一致
- □ 页面路由为 `/projects`

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-COMMON-005
- Phase: Phase 1

### 预估工时
4h

---

## TASK-FE-PROJ-002: 项目筛选器

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §3.4 (项目状态机)

### 输入
- TASK-FE-PROJ-001 已完成

### 输出
```
frontend/src/features/projects/components/
└── ProjectsFilters.tsx         # 项目筛选器
```

### 验收标准
- □ 状态筛选（4 个状态 + 全部）
- □ 负责人筛选（仅 CEO/Admin 可用）
- □ 筛选条件同步到 URL

### SoT 对齐验证
- □ 状态筛选包含 4 个项目状态

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-PROJ-001
- Phase: Phase 1

### 预估工时
2h

---

## TASK-FE-PROJ-003: 项目表格组件

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §7.1 (必须使用的组件)
- STATE_MACHINE.md v2.9 §7.3 (项目状态机)

### 输入
- TASK-FE-PROJ-001 已完成
- TASK-FE-COMMON-003 已完成

### 输出
```
frontend/src/features/projects/components/
├── ProjectsTable.tsx           # 项目表格
└── ProjectRow.tsx              # 表格行组件
```

### 验收标准
- □ 使用 DataTable 组件
- □ 显示字段：项目名称、负责人、状态、账户数、创建时间
- □ 状态列使用 StatusBadge 组件
- □ 支持行操作按钮

### SoT 对齐验证
- □ 状态显示使用 StatusBadge
- □ 状态值使用 4 个项目状态

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-PROJ-001, TASK-FE-COMMON-003
- Phase: Phase 1

### 预估工时
4h

---

## TASK-FE-PROJ-004: 项目创建/编辑表单

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (权限矩阵)
- API_SOT.md v9.7 (POST/PUT /api/v1/projects)

### 输入
- TASK-FE-PROJ-001 已完成

### 输出
```
frontend/src/features/projects/components/
├── ProjectForm.tsx             # 项目表单
├── ProjectFormSchema.ts        # 表单验证 Schema
└── ProjectFormDialog.tsx       # 表单弹窗

frontend/src/features/projects/hooks/
└── useProjectMutations.ts      # 变更操作 Hook
```

### 验收标准
- □ 仅 ceo 和 admin 可创建项目
- □ 必填字段：项目名称、负责人
- □ 选填字段：描述、计费模式
- □ 使用 react-hook-form + zod 验证
- □ 创建成功显示 toast 通知

### SoT 对齐验证
- □ 权限检查符合 MASTER.md v4.9 §2.4
- □ 初始状态为 draft

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-PROJ-001
- Phase: Phase 1

### 预估工时
5h

---

## TASK-FE-PROJ-005: 项目详情页

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §5.1 (页面清单)

### 输入
- TASK-FE-PROJ-001 已完成

### 输出
```
frontend/src/app/projects/[id]/
└── page.tsx                    # 项目详情页

frontend/src/features/projects/components/
├── ProjectDetailPage.tsx       # 详情页组件
├── ProjectInfo.tsx             # 基础信息卡片
├── ProjectStats.tsx            # 统计数据卡片
└── ProjectAccounts.tsx         # 关联账户列表

frontend/src/features/projects/hooks/
└── useProject.ts               # 单条数据 Hook
```

### 验收标准
- □ 显示项目基础信息
- □ 显示项目统计数据（消耗、利润等）
- □ 显示关联账户列表
- □ 显示项目成员列表
- □ 支持编辑和状态操作

### SoT 对齐验证
- □ 数据权限按角色过滤

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-PROJ-001
- Phase: Phase 1

### 预估工时
5h

---

## TASK-FE-PROJ-006: 项目成员管理

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (权限矩阵)
- MASTER.md v4.9 §2.4 (管理项目成员权限)

### 输入
- TASK-FE-PROJ-005 已完成
- TASK-FE-USER-001 (可并行)

### 输出
```
frontend/src/features/projects/components/
├── ProjectMembers.tsx          # 成员列表
├── ProjectMemberAdd.tsx        # 添加成员弹窗
└── ProjectMemberRow.tsx        # 成员行组件

frontend/src/features/projects/hooks/
└── useProjectMembers.ts        # 成员数据 Hook
```

### 验收标准
- □ 仅 ceo, project_owner, admin 可管理成员
- □ 显示成员列表（投手为主）
- □ 支持添加/移除成员
- □ 不能移除项目负责人

### SoT 对齐验证
- □ 权限检查符合 MASTER.md v4.9 §2.4

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-PROJ-005
- Phase: Phase 1

### 预估工时
4h

---

## TASK-FE-PROJ-007: 项目状态流转

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §3.4 (项目状态机)
- STATE_MACHINE.md v2.9 §7.3 (项目状态机)

### 输入
- TASK-FE-PROJ-003 已完成

### 输出
```
frontend/src/features/projects/components/
├── ProjectStatusActions.tsx    # 状态操作按钮
└── ProjectStatusDialog.tsx     # 状态确认弹窗

frontend/src/features/projects/lib/
└── status-transitions.ts       # 状态转换逻辑
```

### 验收标准
- □ draft → active：激活项目
- □ active → suspended：暂停项目
- □ suspended → active：恢复项目
- □ active → archived：直接归档项目（需确认弹窗警告）
- □ suspended → archived：归档项目
- □ 状态变更需确认弹窗
- □ 仅项目负责人和 admin 可操作

### SoT 对齐验证
- □ 状态流转符合 STATE_MACHINE.md v2.9

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-PROJ-003
- Phase: Phase 1

### 预估工时
3h

---

# ACCT 账户模块

> **优先级**: P0
> **任务数**: 8
> **预估工时**: 30h
> **Phase**: Phase 1
> **状态机**: 6 状态 (new → testing → active → suspended → dead / archived)

## TASK-FE-ACCT-001: 账户列表页

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §6.3 (账户管理)
- FRONTEND_PAGE_DESIGN_v2.1.md §5.1 (页面清单)
- API_SOT.md v9.7 (GET /api/v1/ad-accounts)

### 输入
- TASK-FE-COMMON-005 已完成

### 输出
```
frontend/src/app/ad-accounts/
└── page.tsx                    # 账户列表页

frontend/src/features/ad-accounts/
├── components/
│   └── AdAccountsPage.tsx      # 页面组件
├── hooks/
│   └── useAdAccounts.ts        # 列表数据 Hook
├── services/
│   └── adAccountsApi.ts        # API 调用
└── types/
    └── adAccount.types.ts      # 类型定义
```

### 验收标准
- □ 使用通用列表页模板
- □ 支持筛选、分页、排序
- □ ceo, project_owner（项目内账户）, account_manager, admin 可访问
- □ 投手可通过日报页面查看自己的账户
- □ 项目负责人可查看项目关联账户以监控投放效果

### SoT 对齐验证
- □ 访问权限与 MASTER.md v4.9 §2.4 一致
- □ 页面路由为 `/ad-accounts`

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-COMMON-005
- Phase: Phase 1

### 预估工时
4h

---

## TASK-FE-ACCT-002: 账户状态看板

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §6.3.1 (账户状态看板)
- STATE_MACHINE.md v2.9 §7.1 (账户状态机)

### 输入
- TASK-FE-ACCT-001 已完成
- TASK-FE-COMMON-003 已完成

### 输出
```
frontend/src/features/ad-accounts/components/
├── AccountStatusBoard.tsx      # 状态看板
└── StatusCard.tsx              # 状态卡片
```

### 验收标准
- □ 显示 6 个状态分组：new, testing, active, suspended, dead, archived
- □ 每个状态显示账户数量
- □ 点击状态卡片筛选列表
- □ 使用对应状态颜色

### SoT 对齐验证
- □ 状态值与 STATE_MACHINE.md v2.9 一致
- □ 颜色与 FRONTEND_PAGE_DESIGN_v2.1.md §3.2 一致

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-ACCT-001, TASK-FE-COMMON-003
- Phase: Phase 1

### 预估工时
4h

---

## TASK-FE-ACCT-003: 账户筛选器

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §6.3 (账户管理)

### 输入
- TASK-FE-ACCT-001 已完成

### 输出
```
frontend/src/features/ad-accounts/components/
└── AdAccountsFilters.tsx       # 账户筛选器
```

### 验收标准
- □ 状态筛选（6 个状态 + 全部）
- □ 渠道筛选
- □ 项目筛选
- □ 投手筛选（户管可用）
- □ 筛选条件同步到 URL

### SoT 对齐验证
- □ 状态筛选包含 6 个账户状态

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-ACCT-001
- Phase: Phase 1

### 预估工时
3h

---

## TASK-FE-ACCT-004: 账户表格组件

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §7.1 (必须使用的组件)
- STATE_MACHINE.md v2.9 §7.1 (账户状态机)

### 输入
- TASK-FE-ACCT-001 已完成

### 输出
```
frontend/src/features/ad-accounts/components/
├── AdAccountsTable.tsx         # 账户表格
└── AdAccountRow.tsx            # 表格行组件
```

### 验收标准
- □ 使用 DataTable 组件
- □ 显示字段：账户ID、渠道、项目、投手、余额、状态
- □ 状态列使用 StatusBadge 组件
- □ 支持行操作按钮

### SoT 对齐验证
- □ 状态显示使用 StatusBadge
- □ 状态值使用 6 个账户状态

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-ACCT-001
- Phase: Phase 1

### 预估工时
4h

---

## TASK-FE-ACCT-005: 账户创建/编辑表单

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §6.3.2 (账户操作权限)
- FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (权限矩阵)
- API_SOT.md v9.7 (POST/PUT /api/v1/ad-accounts)

### 输入
- TASK-FE-ACCT-001 已完成
- TASK-FE-CHAN-001 (可并行)

### 输出
```
frontend/src/features/ad-accounts/components/
├── AdAccountForm.tsx           # 账户表单
├── AdAccountFormSchema.ts      # 表单验证 Schema
└── AdAccountFormDialog.tsx     # 表单弹窗

frontend/src/features/ad-accounts/hooks/
└── useAdAccountMutations.ts    # 变更操作 Hook
```

### 验收标准
- □ 仅 account_manager 和 admin 可创建账户
- □ 必填字段：账户ID、渠道
- □ 选填字段：项目、投手、备注
- □ 使用 react-hook-form + zod 验证
- □ 创建成功显示 toast 通知

### SoT 对齐验证
- □ 权限检查符合 MASTER.md v4.9 §2.4
- □ 初始状态为 new

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-ACCT-001
- Phase: Phase 1

### 预估工时
4h

---

## TASK-FE-ACCT-006: 账户分配操作

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §6.3.2 (账户操作权限)
- FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (分配账户权限)

### 输入
- TASK-FE-ACCT-004 已完成
- TASK-FE-PROJ-001 (可并行)

### 输出
```
frontend/src/features/ad-accounts/components/
├── AccountAssignDialog.tsx     # 分配弹窗
└── AccountAssignForm.tsx       # 分配表单
```

### 验收标准
- □ 仅 account_manager 和 admin 可分配账户
- □ 选择目标项目
- □ 选择目标投手
- □ 分配成功显示 toast 通知
- □ 分配后自动刷新列表

### SoT 对齐验证
- □ 权限检查符合 MASTER.md v4.9 §2.4

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-ACCT-004
- Phase: Phase 1

### 预估工时
4h

---

## TASK-FE-ACCT-007: 账户状态流转（6 状态）

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §3.2 (账户状态机)
- STATE_MACHINE.md v2.9 §7.1 (账户状态机)

### 输入
- TASK-FE-ACCT-004 已完成

### 输出
```
frontend/src/features/ad-accounts/components/
├── AccountStatusActions.tsx    # 状态操作按钮
└── AccountStatusDialog.tsx     # 状态确认弹窗

frontend/src/features/ad-accounts/lib/
└── status-transitions.ts       # 状态转换逻辑
```

### 验收标准
- □ new → testing：开始测试
- □ testing → active：激活账户
- □ active → suspended：暂停账户
- □ suspended → active：恢复账户
- □ suspended → dead：标记死亡
- □ active → archived：归档账户
- □ 状态变更需确认弹窗
- □ 仅 account_manager 和 admin 可操作

### SoT 对齐验证
- □ 状态流转符合 STATE_MACHINE.md v2.9

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-ACCT-004
- Phase: Phase 1

### 预估工时
4h

---

## TASK-FE-ACCT-008: 账户详情弹窗

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §7.1 (必须使用的组件)

### 输入
- TASK-FE-ACCT-004 已完成

### 输出
```
frontend/src/features/ad-accounts/components/
└── AdAccountDetailDialog.tsx   # 账户详情弹窗

frontend/src/features/ad-accounts/hooks/
└── useAdAccount.ts             # 单条数据 Hook
```

### 验收标准
- □ 使用 Dialog 组件
- □ 显示账户完整信息
- □ 显示余额和消耗统计
- □ 显示状态流转历史
- □ 显示操作按钮（根据权限）

### SoT 对齐验证
- □ 使用 Dialog 组件（非 Modal）

### 优先级与依赖
- Priority: P0
- Depends: TASK-FE-ACCT-004
- Phase: Phase 1

### 预估工时
3h

---

# CHAN 渠道模块

> **优先级**: P1
> **任务数**: 4
> **预估工时**: 13h
> **Phase**: Phase 1

## TASK-FE-CHAN-001: 渠道列表页

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §5.1 (页面清单)
- FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (权限矩阵)
- API_SOT.md v9.7 (GET /api/v1/channels)

### 输入
- TASK-FE-COMMON-005 已完成

### 输出
```
frontend/src/app/channels/
└── page.tsx                    # 渠道列表页

frontend/src/features/channels/
├── components/
│   └── ChannelsPage.tsx        # 页面组件
├── hooks/
│   └── useChannels.ts          # 列表数据 Hook
├── services/
│   └── channelsApi.ts          # API 调用
└── types/
    └── channel.types.ts        # 类型定义
```

### 验收标准
- □ 使用通用列表页模板
- □ 支持筛选、分页、排序
- □ 仅 ceo, account_manager, admin 可访问

### SoT 对齐验证
- □ 访问权限与 MASTER.md v4.9 §2.4 一致
- □ 页面路由为 `/channels`

### 优先级与依赖
- Priority: P1
- Depends: TASK-FE-COMMON-005
- Phase: Phase 1

### 预估工时
4h

---

## TASK-FE-CHAN-002: 渠道表格组件

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §7.1 (必须使用的组件)

### 输入
- TASK-FE-CHAN-001 已完成

### 输出
```
frontend/src/features/channels/components/
├── ChannelsTable.tsx           # 渠道表格
└── ChannelRow.tsx              # 表格行组件
```

### 验收标准
- □ 使用 DataTable 组件
- □ 显示字段：渠道名称、平台、账户数、状态
- □ 支持行操作按钮

### SoT 对齐验证
- □ 使用 DataTable 组件

### 优先级与依赖
- Priority: P1
- Depends: TASK-FE-CHAN-001
- Phase: Phase 1

### 预估工时
3h

---

## TASK-FE-CHAN-003: 渠道创建/编辑表单

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (权限矩阵)
- API_SOT.md v9.7 (POST/PUT /api/v1/channels)

### 输入
- TASK-FE-CHAN-001 已完成

### 输出
```
frontend/src/features/channels/components/
├── ChannelForm.tsx             # 渠道表单
├── ChannelFormSchema.ts        # 表单验证 Schema
└── ChannelFormDialog.tsx       # 表单弹窗

frontend/src/features/channels/hooks/
└── useChannelMutations.ts      # 变更操作 Hook
```

### 验收标准
- □ 仅 account_manager 和 admin 可创建渠道
- □ project_owner 和 admin 可审批渠道
- □ 必填字段：渠道名称、平台
- □ 使用 react-hook-form + zod 验证

### SoT 对齐验证
- □ 权限检查符合 MASTER.md v4.9 §2.4

### 优先级与依赖
- Priority: P1
- Depends: TASK-FE-CHAN-001
- Phase: Phase 1

### 预估工时
4h

---

## TASK-FE-CHAN-004: 渠道状态切换

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (权限矩阵)

### 输入
- TASK-FE-CHAN-002 已完成

### 输出
```
frontend/src/features/channels/components/
└── ChannelStatusToggle.tsx     # 状态切换组件
```

### 验收标准
- □ 支持启用/禁用状态切换
- □ 仅 account_manager 和 admin 可操作
- □ 状态变更需确认

### SoT 对齐验证
- □ 权限检查符合 MASTER.md v4.9 §2.4

### 优先级与依赖
- Priority: P1
- Depends: TASK-FE-CHAN-002
- Phase: Phase 1

### 预估工时
2h

---

# TOP 充值模块

> **优先级**: P1
> **任务数**: 7
> **预估工时**: 28h
> **Phase**: Phase 1
> **状态机**: 7 状态 (draft → pending_review → finance_approve → paid → completed / rejected / cancelled)

## TASK-FE-TOP-001: 充值列表页

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §6.4 (充值管理)
- FRONTEND_PAGE_DESIGN_v2.1.md §5.1 (页面清单)
- API_SOT.md v9.7 (GET /api/v1/topups)

### 输入
- TASK-FE-COMMON-005 已完成

### 输出
```
frontend/src/app/topups/
└── page.tsx                    # 充值列表页

frontend/src/features/topups/
├── components/
│   └── TopupsPage.tsx          # 页面组件
├── hooks/
│   └── useTopups.ts            # 列表数据 Hook
├── services/
│   └── topupsApi.ts            # API 调用
└── types/
    └── topup.types.ts          # 类型定义
```

### 验收标准
- □ 使用通用列表页模板
- □ 支持筛选、分页、排序
- □ 全部角色可访问（数据按权限过滤）
- □ 投手只能看到自己申请的充值
- □ 财务可看到全部待审批充值

### SoT 对齐验证
- □ 访问权限对全部角色开放
- □ 页面路由为 `/topups`

### 优先级与依赖
- Priority: P1
- Depends: TASK-FE-COMMON-005
- Phase: Phase 1

### 预估工时
4h

---

## TASK-FE-TOP-002: 充值筛选器

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §6.4 (充值管理)
- FRONTEND_PAGE_DESIGN_v2.1.md §3.3 (充值状态机)

### 输入
- TASK-FE-TOP-001 已完成

### 输出
```
frontend/src/features/topups/components/
└── TopupsFilters.tsx           # 充值筛选器
```

### 验收标准
- □ 状态筛选（7 个状态 + 全部）
- □ 日期范围筛选
- □ 账户筛选
- □ 申请人筛选（财务可用）
- □ 筛选条件同步到 URL

### SoT 对齐验证
- □ 状态筛选包含 7 个充值状态

### 优先级与依赖
- Priority: P1
- Depends: TASK-FE-TOP-001
- Phase: Phase 1

### 预估工时
3h

---

## TASK-FE-TOP-003: 充值表格组件

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §7.1 (必须使用的组件)
- STATE_MACHINE.md v2.9 §7.2 (充值状态机)

### 输入
- TASK-FE-TOP-001 已完成
- TASK-FE-COMMON-003 已完成

### 输出
```
frontend/src/features/topups/components/
├── TopupsTable.tsx             # 充值表格
└── TopupRow.tsx                # 表格行组件
```

### 验收标准
- □ 使用 DataTable 组件
- □ 显示字段：申请日期、账户、金额、申请人、状态
- □ 状态列使用 StatusBadge 组件
- □ 支持行操作按钮

### SoT 对齐验证
- □ 状态显示使用 StatusBadge
- □ 状态值使用 7 个充值状态

### 优先级与依赖
- Priority: P1
- Depends: TASK-FE-TOP-001, TASK-FE-COMMON-003
- Phase: Phase 1

### 预估工时
4h

---

## TASK-FE-TOP-004: 充值申请表单

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §4.2 (充值权限表)
- FRONTEND_PAGE_DESIGN_v2.1.md §6.4.1 (状态流转)
- API_SOT.md v9.7 (POST /api/v1/topups)

### 输入
- TASK-FE-TOP-001 已完成
- TASK-FE-ACCT-001 (可并行)

### 输出
```
frontend/src/features/topups/components/
├── TopupForm.tsx               # 充值申请表单
├── TopupFormSchema.ts          # 表单验证 Schema
└── TopupFormDialog.tsx         # 表单弹窗

frontend/src/features/topups/hooks/
└── useTopupMutations.ts        # 变更操作 Hook
```

### 验收标准
- □ 仅 pitcher 和 account_manager 可申请充值
- □ 必填字段：账户、金额
- □ 选填字段：备注
- □ 金额必须大于 0
- □ 使用 react-hook-form + zod 验证
- □ 申请成功显示 toast 通知
- □ 初始状态为 draft，提交后为 pending_review

### SoT 对齐验证
- □ 权限检查符合 MASTER.md v4.9 §2.4
- □ 金额校验符合 ERROR_CODES_SOT.md (BIZ_100)

### 优先级与依赖
- Priority: P1
- Depends: TASK-FE-TOP-001
- Phase: Phase 1

### 预估工时
5h

---

## TASK-FE-TOP-005: 充值审批操作（7 状态）

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §4.2 (充值权限表)
- FRONTEND_PAGE_DESIGN_v2.1.md §6.4.2 (角色操作)
- STATE_MACHINE.md v2.9 §7.2 (充值状态机)
- API_SOT.md v9.7 (PATCH /api/v1/topups/{id}/status)

### 输入
- TASK-FE-TOP-003 已完成
- TASK-FE-COMMON-002 已完成

### 输出
```
frontend/src/features/topups/components/
├── TopupApprovalActions.tsx    # 审批操作按钮
├── TopupApprovalDialog.tsx     # 审批确认弹窗
└── TopupRejectDialog.tsx       # 拒绝原因弹窗
```

### 验收标准
- □ pending_review → finance_approve：财务批准（日常充值）
- □ pending_review → rejected：财务拒绝
- □ finance_approve → paid：财务标记付款
- □ paid → completed：系统自动完成
- □ 任意非终态 → cancelled：取消充值
- □ 大额充值（>¥50,000）需 CEO 终审
- □ 审批前需确认弹窗
- □ 拒绝需填写原因

### SoT 对齐验证
- □ 审批权限符合 FRONTEND_PAGE_DESIGN_v2.1.md §4.2
- □ 状态流转符合 STATE_MACHINE.md v2.9

### 优先级与依赖
- Priority: P1
- Depends: TASK-FE-TOP-003, TASK-FE-COMMON-002
- Phase: Phase 1

### 预估工时
5h

---

## TASK-FE-TOP-006: 充值详情弹窗

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §7.1 (必须使用的组件)

### 输入
- TASK-FE-TOP-003 已完成

### 输出
```
frontend/src/features/topups/components/
└── TopupDetailDialog.tsx       # 充值详情弹窗

frontend/src/features/topups/hooks/
└── useTopup.ts                 # 单条数据 Hook
```

### 验收标准
- □ 使用 Dialog 组件
- □ 显示充值完整信息
- □ 显示审批流程历史
- □ 显示操作按钮（根据权限和状态）

### SoT 对齐验证
- □ 使用 Dialog 组件（非 Modal）

### 优先级与依赖
- Priority: P1
- Depends: TASK-FE-TOP-003
- Phase: Phase 1

### 预估工时
3h

---

## TASK-FE-TOP-007: 充值状态流转 UI

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §6.4.1 (状态流转)
- STATE_MACHINE.md v2.9 §7.2 (充值状态机)

### 输入
- TASK-FE-TOP-005 已完成

### 输出
```
frontend/src/features/topups/components/
└── TopupStatusFlow.tsx         # 状态流转可视化

frontend/src/features/topups/lib/
└── status-transitions.ts       # 状态转换逻辑
```

### 验收标准
- □ 可视化显示状态流转进度
- □ 高亮当前状态
- □ 显示每个状态的操作人和时间
- □ 终态显示完成/拒绝/取消标记

### SoT 对齐验证
- □ 状态流转符合 STATE_MACHINE.md v2.9

### 优先级与依赖
- Priority: P1
- Depends: TASK-FE-TOP-005
- Phase: Phase 1

### 预估工时
4h

---

# FIN 财务模块

> **优先级**: P2
> **任务数**: 5
> **预估工时**: 22h
> **Phase**: Phase 1

## TASK-FE-FIN-001: 财务中心页面框架

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §6.5 (财务中心)
- FRONTEND_PAGE_DESIGN_v2.1.md §5.1 (页面清单)

### 输入
- TASK-FE-COMMON-002 已完成

### 输出
```
frontend/src/app/finance/
├── page.tsx                    # 财务中心首页（重定向）
├── layout.tsx                  # 财务中心布局
├── ledger/
│   └── page.tsx                # 账本页面
├── reconciliation/
│   └── page.tsx                # 对账页面
└── profit/
    └── page.tsx                # 利润页面

frontend/src/features/finance/
├── components/
│   └── FinanceLayout.tsx       # 财务布局组件
└── types/
    └── finance.types.ts        # 类型定义
```

### 验收标准
- □ 仅 ceo, finance, admin 可访问
- □ 包含三个子页面：账本、对账、利润
- □ 子页面导航

### SoT 对齐验证
- □ 访问权限符合 MASTER.md v4.9 §2.4

### 优先级与依赖
- Priority: P2
- Depends: TASK-FE-COMMON-002
- Phase: Phase 1

### 预估工时
3h

---

## TASK-FE-FIN-002: 账本子页面

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §6.5.1 (子页面)
- API_SOT.md v9.7 (GET /api/v1/ledger)

### 输入
- TASK-FE-FIN-001 已完成

### 输出
```
frontend/src/features/finance/components/
├── LedgerPage.tsx              # 账本页面
├── LedgerTable.tsx             # 账本表格
└── LedgerFilters.tsx           # 账本筛选器

frontend/src/features/finance/hooks/
└── useLedger.ts                # 账本数据 Hook
```

### 验收标准
- □ 显示资金流水记录
- □ 支持日期范围筛选
- □ 支持类型筛选（充值、消耗、红冲）
- □ 显示余额变化

### SoT 对齐验证
- □ 账本记录不可删除（只能红冲）

### 优先级与依赖
- Priority: P2
- Depends: TASK-FE-FIN-001
- Phase: Phase 1

### 预估工时
5h

---

## TASK-FE-FIN-003: 对账子页面

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §6.5.1 (子页面)
- API_SOT.md v9.7 (GET /api/v1/reconciliation)

### 输入
- TASK-FE-FIN-001 已完成

### 输出
```
frontend/src/features/finance/components/
├── ReconciliationPage.tsx      # 对账页面
├── ReconciliationTable.tsx     # 对账表格
└── ReconciliationFilters.tsx   # 对账筛选器

frontend/src/features/finance/hooks/
└── useReconciliation.ts        # 对账数据 Hook
```

### 验收标准
- □ 显示对账记录
- □ 支持日期范围筛选
- □ 高亮差异数据
- □ 支持对账操作

### SoT 对齐验证
- □ 对账规则符合业务流程

### 优先级与依赖
- Priority: P2
- Depends: TASK-FE-FIN-001
- Phase: Phase 1

### 预估工时
6h

---

## TASK-FE-FIN-004: 利润子页面

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §6.5.1 (子页面)
- FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (查看利润权限)
- API_SOT.md v9.7 (GET /api/v1/profit)

### 输入
- TASK-FE-FIN-001 已完成

### 输出
```
frontend/src/features/finance/components/
├── ProfitPage.tsx              # 利润页面
├── ProfitSummary.tsx           # 利润汇总
├── ProfitTable.tsx             # 利润明细表
└── ProfitFilters.tsx           # 利润筛选器

frontend/src/features/finance/hooks/
└── useProfit.ts                # 利润数据 Hook
```

### 验收标准
- □ 仅 ceo, finance, admin 可查看
- □ 显示毛利、收入、成本
- □ 支持按项目/时间维度查看
- □ 支持导出功能

### SoT 对齐验证
- □ 利润公式：毛利 = 收入 - 成本
- □ 权限检查符合 MASTER.md v4.9 §2.4

### 优先级与依赖
- Priority: P2
- Depends: TASK-FE-FIN-001
- Phase: Phase 1

### 预估工时
5h

---

## TASK-FE-FIN-005: 财务权限守卫

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §6.5.2 (访问控制)

### 输入
- TASK-FE-FIN-001 已完成
- TASK-FE-COMMON-002 已完成

### 输出
```
frontend/src/features/finance/components/
└── FinanceGuard.tsx            # 财务权限守卫
```

### 验收标准
- □ 封装财务模块权限检查
- □ 无权限显示 AccessDenied 组件
- □ 支持重定向到首页

### SoT 对齐验证
- □ 权限检查使用 usePermission Hook

### 优先级与依赖
- Priority: P2
- Depends: TASK-FE-FIN-001, TASK-FE-COMMON-002
- Phase: Phase 1

### 预估工时
3h

---

# USER 用户模块

> **优先级**: P2
> **任务数**: 5
> **预估工时**: 18h
> **Phase**: Phase 1

## TASK-FE-USER-001: 用户列表页

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §5.1 (页面清单)
- FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (权限矩阵)
- API_SOT.md v9.7 (GET /api/v1/users)

### 输入
- TASK-FE-COMMON-005 已完成

### 输出
```
frontend/src/app/users/
└── page.tsx                    # 用户列表页

frontend/src/features/users/
├── components/
│   └── UsersPage.tsx           # 页面组件
├── hooks/
│   └── useUsers.ts             # 列表数据 Hook
├── services/
│   └── usersApi.ts             # API 调用
└── types/
    └── user.types.ts           # 类型定义
```

### 验收标准
- □ 使用通用列表页模板
- □ 支持筛选、分页、排序
- □ 仅 ceo 和 admin 可访问

### SoT 对齐验证
- □ 访问权限符合 MASTER.md v4.9 §2.4
- □ 页面路由为 `/users`

### 优先级与依赖
- Priority: P2
- Depends: TASK-FE-COMMON-005
- Phase: Phase 1

### 预估工时
4h

---

## TASK-FE-USER-002: 用户表格组件

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §7.1 (必须使用的组件)

### 输入
- TASK-FE-USER-001 已完成

### 输出
```
frontend/src/features/users/components/
├── UsersTable.tsx              # 用户表格
└── UserRow.tsx                 # 表格行组件
```

### 验收标准
- □ 使用 DataTable 组件
- □ 显示字段：用户名、角色、项目负责人标记、状态
- □ 支持行操作按钮

### SoT 对齐验证
- □ 使用 DataTable 组件

### 优先级与依赖
- Priority: P2
- Depends: TASK-FE-USER-001
- Phase: Phase 1

### 预估工时
3h

---

## TASK-FE-USER-003: 用户创建/编辑表单

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (权限矩阵)
- FRONTEND_PAGE_DESIGN_v2.1.md §2 (双层角色架构)
- API_SOT.md v9.7 (POST/PUT /api/v1/users)

### 输入
- TASK-FE-USER-001 已完成

### 输出
```
frontend/src/features/users/components/
├── UserForm.tsx                # 用户表单
├── UserFormSchema.ts           # 表单验证 Schema
└── UserFormDialog.tsx          # 表单弹窗

frontend/src/features/users/hooks/
└── useUserMutations.ts         # 变更操作 Hook
```

### 验收标准
- □ 仅 ceo 和 admin 可创建用户
- □ 必填字段：用户名、密码、角色
- □ 选填字段：是否项目负责人
- □ 角色选项仅包含 4 个技术层角色
- □ 使用 react-hook-form + zod 验证

### SoT 对齐验证
- □ 权限检查符合 MASTER.md v4.9 §2.4
- □ 角色选项与 DATA_SCHEMA.md v5.11 一致

### 优先级与依赖
- Priority: P2
- Depends: TASK-FE-USER-001
- Phase: Phase 1

### 预估工时
5h

---

## TASK-FE-USER-004: 用户角色分配

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §2 (双层角色架构)

### 输入
- TASK-FE-USER-003 已完成

### 输出
```
frontend/src/features/users/components/
├── UserRoleSelect.tsx          # 角色选择器
└── UserProjectOwnerToggle.tsx  # 项目负责人切换
```

### 验收标准
- □ 技术层角色下拉选择（4 个选项）
- □ 项目负责人切换开关
- □ 角色变更需确认

### SoT 对齐验证
- □ 角色值与 DATA_SCHEMA.md v5.11 一致
- □ 无废弃角色选项

### 优先级与依赖
- Priority: P2
- Depends: TASK-FE-USER-003
- Phase: Phase 1

### 预估工时
4h

---

## TASK-FE-USER-005: 用户停用/启用操作

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (权限矩阵)

### 输入
- TASK-FE-USER-002 已完成

### 输出
```
frontend/src/features/users/components/
└── UserStatusToggle.tsx        # 用户状态切换
```

### 验收标准
- □ 仅 ceo 和 admin 可操作
- □ 停用用户需确认弹窗
- □ 停用后用户无法登录

### SoT 对齐验证
- □ 权限检查符合 MASTER.md v4.9 §2.4

### 优先级与依赖
- Priority: P2
- Depends: TASK-FE-USER-002
- Phase: Phase 1

### 预估工时
2h

---

# SET 设置模块

> **优先级**: P3
> **任务数**: 3
> **预估工时**: 10h
> **Phase**: Phase 1

## TASK-FE-SET-001: 系统设置页面框架

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §5.1 (页面清单)
- FRONTEND_PAGE_DESIGN_v2.1.md §4.1 (权限矩阵)

### 输入
- TASK-FE-COMMON-002 已完成

### 输出
```
frontend/src/app/settings/
└── page.tsx                    # 系统设置页

frontend/src/features/settings/
├── components/
│   └── SettingsPage.tsx        # 页面组件
└── types/
    └── settings.types.ts       # 类型定义
```

### 验收标准
- □ 仅 admin 可访问
- □ Tab 式布局支持多个配置区域

### SoT 对齐验证
- □ 访问权限仅限 admin

### 优先级与依赖
- Priority: P3
- Depends: TASK-FE-COMMON-002
- Phase: Phase 1

### 预估工时
3h

---

## TASK-FE-SET-002: 基础配置表单

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §5.1 (页面清单)

### 输入
- TASK-FE-SET-001 已完成

### 输出
```
frontend/src/features/settings/components/
├── BasicSettings.tsx           # 基础配置
└── BasicSettingsForm.tsx       # 配置表单
```

### 验收标准
- □ 系统名称配置
- □ 日期格式配置
- □ 保存成功显示 toast

### SoT 对齐验证
- □ 配置项符合系统规范

### 优先级与依赖
- Priority: P3
- Depends: TASK-FE-SET-001
- Phase: Phase 1

### 预估工时
4h

---

## TASK-FE-SET-003: 充值阈值配置

### 关联文档
- FRONTEND_PAGE_DESIGN_v2.1.md §4.2 (充值权限表)

### 输入
- TASK-FE-SET-001 已完成

### 输出
```
frontend/src/features/settings/components/
├── TopupThresholdSettings.tsx  # 充值阈值配置
└── TopupThresholdForm.tsx      # 配置表单
```

### 验收标准
- □ 大额充值阈值配置（默认 ¥50,000）
- □ 配置变更需确认
- □ 保存成功显示 toast

### SoT 对齐验证
- □ 默认阈值与 FRONTEND_PAGE_DESIGN_v2.1.md §4.2 一致

### 优先级与依赖
- Priority: P3
- Depends: TASK-FE-SET-001
- Phase: Phase 1

### 预估工时
3h

---

# 统计汇总

## 任务卡统计

| 模块 | 任务卡 | 任务数 | 预估工时 | 优先级 |
|------|--------|--------|---------|--------|
| COMMON | TASK-FE-COMMON-001~005 | 5 | 18h | P0 |
| DASH | TASK-FE-DASH-001~006 | 6 | 22h | P0 |
| RPT | TASK-FE-RPT-001~007 | 7 | 28h | P0 |
| PROJ | TASK-FE-PROJ-001~007 | 7 | 27h | P0 |
| ACCT | TASK-FE-ACCT-001~008 | 8 | 30h | P0 |
| CHAN | TASK-FE-CHAN-001~004 | 4 | 13h | P1 |
| TOP | TASK-FE-TOP-001~007 | 7 | 28h | P1 |
| FIN | TASK-FE-FIN-001~005 | 5 | 22h | P2 |
| USER | TASK-FE-USER-001~005 | 5 | 18h | P2 |
| SET | TASK-FE-SET-001~003 | 3 | 10h | P3 |
| **合计** | - | **57** | **216h** | - |

## 优先级分布

| 优先级 | 模块 | 任务数 | 预估工时 |
|--------|------|--------|---------|
| P0 | COMMON, DASH, RPT, PROJ, ACCT | 33 | 125h |
| P1 | CHAN, TOP | 11 | 41h |
| P2 | FIN, USER | 10 | 40h |
| P3 | SET | 3 | 10h |

## Phase 分布

| Phase | 任务数 | 预估工时 | 说明 |
|-------|--------|---------|------|
| Phase 1 | 57 | 216h | 全部任务均为 Phase 1 |
| Phase 2 | 0 | 0h | 待后续规划 |

---

# 附录

## A. SoT 参考文档

| 文档 | 版本 | 路径 | 用途 |
|------|------|------|------|
| MASTER.md | v4.9 | docs/sot/MASTER.md | 角色权限定义 |
| STATE_MACHINE.md | v2.9 | docs/sot/STATE_MACHINE.md | 状态机定义 |
| DATA_SCHEMA.md | v5.11 | docs/sot/DATA_SCHEMA.md | 数据模型定义 |
| BUSINESS_RULES.md | v5.2 | docs/sot/BUSINESS_RULES.md | 业务规则 |
| API_SOT.md | v9.7 | docs/sot/API_SOT.md | API 定义 |
| ERROR_CODES_SOT.md | v2.2 | docs/sot/ERROR_CODES_SOT.md | 错误码定义 |
| FRONTEND_PAGE_DESIGN_v2.1.md | v2.1 | docs/design/FRONTEND_PAGE_DESIGN_v2.1.md | 页面设计规范 |

## B. 通用测试要求

> 每个任务卡的测试用例必须覆盖以下场景：

```markdown
### 测试要求
- □ 正向场景测试（正常流程）
- □ 负向场景测试（权限拒绝、状态非法、参数错误）
- □ 边界场景测试（空值、极值、特殊字符）
- □ 幂等性测试（重复提交）
```

## C. 防幻觉检查清单

**生成任务卡时必须检查**:

```
□ 任务 ID 符合命名规范 (TASK-FE-{CODE}-{SEQ})
□ 所有 SoT 文档引用都存在（版本号匹配）
□ 输出文件清单完整（组件/Hook/Service/Type）
□ 验收标准可测试（非模糊描述）
□ 没有引入 Phase 2 特性（日报不用 8 状态）
□ 没有禁用角色引用（supervisor/data_operator）
□ API 端点都在 API_SOT.md 中定义
```

---

**文档维护者**: 前端架构团队
**生成日期**: 2026-01-04
**下次审核**: 下个迭代或重大变更时
