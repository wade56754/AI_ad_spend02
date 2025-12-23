# B1 充值审批 - 模块规格书

> **版本**: v1.0
> **更新日期**: 2025-12-22
> **优先级**: P1
> **基准**: MASTER.md v4.4 §6.2 页面 4, STATE_MACHINE.md v2.6 §9

---

## 1. 模块概述

### 1.1 业务目标

**核心问题**: 该不该批这笔钱？

充值审批模块解决资金出入的责任闭环问题：
- 谁申请的钱？为什么申请？
- 当前账户余额多少？是否真的需要充值？
- 审批到哪一步了？谁批准/拒绝的？

### 1.2 用户角色

| 角色 | 职责 | 典型操作 |
|------|------|----------|
| `pitcher` / `account_manager` | 申请人 | 创建充值申请、提交、取消 |
| `data_operator` | 数据复核 | 核对申请信息、通过/拒绝 |
| `finance` | 财务终审 | 终审批准/拒绝、标记已支付、确认入账 |
| `ceo` | 老板 | 查看审批状态、了解资金流向 |
| `admin` | 管理员 | 全权限（系统维护） |

### 1.3 核心用例

| 用例 | 描述 | 主要角色 |
|------|------|----------|
| UC-B1-01 | 创建充值申请 | pitcher, account_manager |
| UC-B1-02 | 提交申请进入审批流程 | pitcher, account_manager |
| UC-B1-03 | 数据复核（通过/拒绝） | data_operator |
| UC-B1-04 | 财务终审（批准/拒绝） | finance |
| UC-B1-05 | 标记已支付 | finance |
| UC-B1-06 | 确认入账完成 | finance, system |
| UC-B1-07 | 取消申请 | 申请人（仅限特定状态） |

### 1.4 Phase 约束

| Phase | 约束 | 说明 |
|-------|------|------|
| **Phase 1 (照亮)** | 有流程，可绕行 | 记录审批过程，允许紧急绕行 |
| **Phase 2 (问责)** | 无批准不打款 | 强制审批，财务系统联动 |

---

## 2. 数据需求

### 2.1 数据源 (SoT)

| 数据源 | 表/模型 | 用途 |
|--------|---------|------|
| topup_request | 充值申请表 | 申请信息、状态、审批记录 |
| ad_account | 广告账户表 | 当前余额、账户信息 |
| project | 项目表 | 关联项目、预算信息 |
| user | 用户表 | 申请人、审批人信息 |

### 2.2 字段清单 (MASTER.md §6.2 页面 4)

**必须字段**:

| 字段 | 来源 | 说明 |
|------|------|------|
| `amount` | topup_request | 申请金额 |
| `reason` | topup_request | 申请理由 |
| `current_balance` | ad_account.balance | 当前余额 |
| `status` | topup_request | 审批状态 (7 状态) |
| `applicant_name` | user (JOIN) | 申请人姓名 |
| `project_name` | project (JOIN) | 关联项目名称 |
| `ad_account_name` | ad_account (JOIN) | 账户名称 |

**扩展字段**:

| 字段 | 来源 | 说明 |
|------|------|------|
| `created_at` | topup_request | 申请时间 |
| `reviewed_at` | topup_request | 复核时间 |
| `approved_at` | topup_request | 终审时间 |
| `paid_at` | topup_request | 支付时间 |
| `completed_at` | topup_request | 完成时间 |
| `reviewer_name` | user (JOIN) | 数据复核人 |
| `approver_name` | user (JOIN) | 财务终审人 |
| `reject_reason` | topup_request | 拒绝原因 |

### 2.3 计算公式

| 指标 | 公式 | 说明 |
|------|------|------|
| 待复核数 | `COUNT(status='pending_review')` | 待数据复核的申请数 |
| 待终审数 | `COUNT(status='finance_approve')` | 待财务终审的申请数 |
| 本月申请总额 | `SUM(amount) WHERE created_at IN month` | 本月申请总金额 |
| 本月批准总额 | `SUM(amount) WHERE status='completed'` | 本月已完成总金额 |
| 平均审批时长 | `AVG(completed_at - created_at)` | 从申请到完成的平均时长 |

---

## 3. 状态机 (STATE_MACHINE.md v2.6 §9)

### 3.1 状态定义 (7 状态)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        充值申请状态机 (7 状态)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────┐    提交     ┌────────────────┐                               │
│   │  draft  │ ──────────→ │ pending_review │                               │
│   │ (草稿)  │             │  (待数据复核)   │                               │
│   └────┬────┘             └───────┬────────┘                               │
│        │                          │                                         │
│        │ 取消                     │ 数据复核通过                             │
│        ↓                          ↓                                         │
│   ┌──────────┐            ┌────────────────┐                               │
│   │cancelled │            │finance_approve │                               │
│   │ (已取消) │            │ (待财务终审)   │                               │
│   └──────────┘            └───────┬────────┘                               │
│                                   │                                         │
│                                   │ 财务批准                                │
│                                   ↓                                         │
│                           ┌──────────┐    入账确认    ┌───────────┐        │
│                           │   paid   │ ─────────────→ │ completed │        │
│                           │ (已支付) │                │  (已完成)  │        │
│                           └──────────┘                └───────────┘        │
│                                                                             │
│   拒绝分支 (任意审批节点):                                                   │
│   pending_review/finance_approve ──拒绝──→ rejected (已拒绝)               │
│                                                                             │
│   取消分支:                                                                  │
│   draft/pending_review/finance_approve ──取消──→ cancelled (已取消)        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 状态转换规则

| 当前状态 | 目标状态 | 操作 | 允许角色 |
|----------|----------|------|----------|
| `draft` | `pending_review` | 提交申请 | media_buyer, account_manager, admin |
| `draft` | `cancelled` | 取消申请 | media_buyer, account_manager, admin |
| `pending_review` | `finance_approve` | 数据复核通过 | data_operator, admin |
| `pending_review` | `rejected` | 数据复核拒绝 | data_operator, admin |
| `pending_review` | `cancelled` | 取消申请 | media_buyer, account_manager, admin |
| `finance_approve` | `paid` | 财务终审批准 | finance, admin |
| `finance_approve` | `rejected` | 财务终审拒绝 | finance, admin |
| `finance_approve` | `cancelled` | 取消申请 | media_buyer, account_manager, admin |
| `paid` | `completed` | 入账确认 | finance, system, admin |

### 3.3 终态

| 状态 | 类型 | 说明 |
|------|------|------|
| `completed` | 成功终态 | 充值完成，资金已入账 |
| `rejected` | 失败终态 | 申请被拒绝 |
| `cancelled` | 失败终态 | 申请被取消 |

---

## 4. UI 规范

### 4.1 页面布局

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [页面头部]                                                                   │
│ 充值审批                                              [新建申请] [导出]      │
├─────────────────────────────────────────────────────────────────────────────┤
│ [统计卡片区]                                                                 │
│ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐                │
│ │ 待复核     │ │ 待终审     │ │ 本月申请   │ │ 本月完成   │                │
│ │ 5          │ │ 3          │ │ ¥125,000   │ │ ¥98,000    │                │
│ └────────────┘ └────────────┘ └────────────┘ └────────────┘                │
├─────────────────────────────────────────────────────────────────────────────┤
│ [标签页筛选]                                                                 │
│ [全部] [待复核] [待终审] [已支付] [已完成] [已拒绝]                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ [筛选器]                                                                     │
│ 项目: [全部 ▼]  账户: [全部 ▼]  申请人: [全部 ▼]  日期: [____] - [____]    │
├─────────────────────────────────────────────────────────────────────────────┤
│ [数据表格]                                                                   │
│ ┌──────┬────────┬────────┬──────────┬──────────┬────────┬────────┬───────┐ │
│ │ 编号 │ 项目   │ 账户   │ 申请金额 │ 当前余额 │ 状态   │ 申请人 │ 操作  │ │
│ ├──────┼────────┼────────┼──────────┼──────────┼────────┼────────┼───────┤ │
│ │ T001 │ 项目A  │ 账户1  │ ¥50,000  │ ¥2,500   │ 待复核 │ 张三   │ [审批]│ │
│ │ T002 │ 项目B  │ 账户2  │ ¥30,000  │ ¥8,000   │ 待终审 │ 李四   │ [审批]│ │
│ │ T003 │ 项目A  │ 账户3  │ ¥20,000  │ ¥1,200   │ 已完成 │ 王五   │ [查看]│ │
│ └──────┴────────┴────────┴──────────┴──────────┴────────┴────────┴───────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ [分页]                                                    第 1/5 页 [< >]   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 组件清单

| 组件 | 代码块 | 用途 |
|------|--------|------|
| TopupsStatsOverview | StatCard × 4 | 统计卡片区 |
| TopupsTable | DataTable | 申请列表 |
| TopupRequestForm | FormDialog | 新建/编辑申请 |
| TopupApprovalDialog | ApprovalDialog | 审批对话框 |
| TopupDetailDrawer | DetailDrawer | 申请详情抽屉 |
| TopupTimeline | ApprovalTimeline | 审批时间线 |
| StatusBadge | StatusBadge | 状态徽章 |

### 4.3 状态颜色规范

| 状态 | 颜色 | Tailwind Class |
|------|------|----------------|
| `draft` | 灰色 | `bg-gray-100 text-gray-800` |
| `pending_review` | 蓝色 | `bg-blue-100 text-blue-800` |
| `finance_approve` | 橙色 | `bg-orange-100 text-orange-800` |
| `paid` | 紫色 | `bg-purple-100 text-purple-800` |
| `completed` | 绿色 | `bg-green-100 text-green-800` |
| `rejected` | 红色 | `bg-red-100 text-red-800` |
| `cancelled` | 灰色 | `bg-gray-100 text-gray-500` |

### 4.4 交互规则

| 交互 | 触发 | 行为 |
|------|------|------|
| 点击行 | 单击表格行 | 打开详情抽屉 |
| 审批按钮 | 点击操作列按钮 | 打开审批对话框 |
| 新建申请 | 点击头部按钮 | 打开申请表单对话框 |
| 切换标签 | 点击标签页 | 筛选对应状态的申请 |
| 筛选器变更 | 选择筛选项 | 实时过滤表格数据 |

---

## 5. API 接口

### 5.1 接口清单

| 方法 | 路径 | 用途 | 权限 |
|------|------|------|------|
| GET | `/api/v1/topups` | 获取充值申请列表 | 登录用户 |
| GET | `/api/v1/topups/{id}` | 获取申请详情 | 登录用户 |
| POST | `/api/v1/topups` | 创建充值申请 | media_buyer, account_manager |
| PUT | `/api/v1/topups/{id}` | 更新申请信息 | 申请人（draft 状态） |
| POST | `/api/v1/topups/{id}/submit` | 提交申请 | 申请人 |
| POST | `/api/v1/topups/{id}/review` | 数据复核 | data_operator |
| POST | `/api/v1/topups/{id}/approve` | 财务终审 | finance |
| POST | `/api/v1/topups/{id}/mark-paid` | 标记已支付 | finance |
| POST | `/api/v1/topups/{id}/complete` | 确认入账 | finance |
| POST | `/api/v1/topups/{id}/cancel` | 取消申请 | 申请人 |
| GET | `/api/v1/topups/stats` | 获取统计数据 | 登录用户 |

### 5.2 请求/响应示例

**获取列表**:
```http
GET /api/v1/topups?status=pending_review&page=1&page_size=20
Authorization: Bearer {token}
```

```json
{
  "code": "SUCCESS",
  "message": "获取成功",
  "data": {
    "items": [
      {
        "id": 1,
        "project_id": 101,
        "project_name": "项目A",
        "ad_account_id": 201,
        "ad_account_name": "账户1",
        "amount": 50000.00,
        "current_balance": 2500.00,
        "reason": "账户余额不足，需要充值继续投放",
        "status": "pending_review",
        "applicant_id": 301,
        "applicant_name": "张三",
        "created_at": "2025-12-22T10:00:00Z",
        "reviewed_at": null,
        "reviewer_id": null,
        "reviewer_name": null
      }
    ],
    "total": 5,
    "page": 1,
    "page_size": 20
  }
}
```

**数据复核**:
```http
POST /api/v1/topups/1/review
Authorization: Bearer {token}
Content-Type: application/json

{
  "action": "approve",
  "comment": "信息核实无误，通过复核"
}
```

```json
{
  "code": "SUCCESS",
  "message": "复核通过",
  "data": {
    "id": 1,
    "status": "finance_approve",
    "reviewed_at": "2025-12-22T11:00:00Z",
    "reviewer_id": 401,
    "reviewer_name": "数据员A"
  }
}
```

**财务终审**:
```http
POST /api/v1/topups/1/approve
Authorization: Bearer {token}
Content-Type: application/json

{
  "action": "approve",
  "comment": "批准充值"
}
```

---

## 6. 权限矩阵

### 6.1 功能权限

| 功能 | ceo | finance | data_operator | supervisor | pitcher | account_manager | admin |
|------|-----|---------|---------------|------------|---------|-----------------|-------|
| 查看列表 | ✓ | ✓ | ✓ | ✓ | ○ | ○ | ✓ |
| 创建申请 | - | - | - | - | ✓ | ✓ | ✓ |
| 数据复核 | - | - | ✓ | - | - | - | ✓ |
| 财务终审 | - | ✓ | - | - | - | - | ✓ |
| 标记支付 | - | ✓ | - | - | - | - | ✓ |
| 确认入账 | - | ✓ | - | - | - | - | ✓ |
| 取消申请 | - | - | - | - | ✓ | ✓ | ✓ |
| 导出数据 | ✓ | ✓ | ✓ | ✓ | - | - | ✓ |

**说明**: ✓ = 全部可见, ○ = 仅自己相关, - = 无权限

### 6.2 数据权限

| 角色 | 数据范围 |
|------|----------|
| `ceo` | 全部申请 |
| `finance` | 全部申请 |
| `data_operator` | 全部申请 |
| `supervisor` | 所管辖投手的申请 |
| `pitcher` | 仅自己的申请 |
| `account_manager` | 所管理账户的申请 |
| `admin` | 全部申请 |

---

## 7. 代码块组合

### 7.1 前端代码块

```
TopupsPage
├── TopupsStatsOverview
│   └── StatCard × 4
├── TopupsTable
│   ├── DataTable
│   ├── StatusBadge
│   └── ActionButtons
├── TopupRequestForm
│   └── FormDialog
├── TopupApprovalDialog
│   ├── ApprovalDialog
│   └── ApprovalTimeline
└── TopupDetailDrawer
    ├── DetailDrawer
    └── ApprovalTimeline
```

### 7.2 后端代码块

```
TopupRouter
├── topup_service
│   ├── state_machine_transition
│   ├── permission_filter
│   └── audit_log_writer
├── ledger_service (入账时)
│   └── ledger_entry_writer
└── notification_service (可选)
    └── approval_notification
```

### 7.3 组合图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           充值审批模块组合图                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [前端]                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ TopupsPage                                                          │   │
│  │  ├── useTopups() ─────────────────────────────┐                     │   │
│  │  ├── useTopupStats() ─────────────────────────┤                     │   │
│  │  └── useTopupMutations() ─────────────────────┤                     │   │
│  └───────────────────────────────────────────────┼─────────────────────┘   │
│                                                  │                          │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┼ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │
│                                                  │                          │
│  [后端]                                          ↓                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ TopupRouter (/api/v1/topups)                                        │   │
│  │  ├── GET /           → topup_service.list()                         │   │
│  │  ├── POST /          → topup_service.create()                       │   │
│  │  ├── POST /{id}/review → state_machine.transition() + audit_log     │   │
│  │  ├── POST /{id}/approve → state_machine.transition() + audit_log    │   │
│  │  └── POST /{id}/complete → ledger_service.write_entry()             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. 测试检查点

### 8.1 功能测试

| 检查点 | 预期结果 |
|--------|----------|
| 创建申请 | pitcher/account_manager 可创建，其他角色不可 |
| 提交申请 | draft → pending_review 状态转换正确 |
| 数据复核通过 | pending_review → finance_approve |
| 数据复核拒绝 | pending_review → rejected |
| 财务终审通过 | finance_approve → paid |
| 标记入账 | paid → completed |
| 取消申请 | 仅 draft/pending_review/finance_approve 可取消 |
| 权限校验 | 非授权角色操作被拒绝 |

### 8.2 边界测试

| 检查点 | 预期结果 |
|--------|----------|
| 金额为 0 | 创建失败，提示金额必须大于 0 |
| 金额超过限额 | 创建成功，标记为大额申请 |
| 重复提交 | 拒绝，提示已提交 |
| 终态操作 | 拒绝，提示申请已结束 |

### 8.3 数据完整性测试

| 检查点 | 预期结果 |
|--------|----------|
| 入账后余额 | ad_account.balance 正确增加 |
| 账本记录 | ledger_entries 正确记录 |
| 审计日志 | 每次状态变更有审计记录 |

---

## 9. 源码位置

### 9.1 前端

| 文件 | 路径 |
|------|------|
| 页面组件 | `frontend/src/features/topups/components/TopupsPage.tsx` |
| 表格组件 | `frontend/src/features/topups/components/TopupsTable.tsx` |
| 申请表单 | `frontend/src/features/topups/components/TopupRequestForm.tsx` |
| 审批对话框 | `frontend/src/features/topups/components/TopupApprovalDialog.tsx` |
| 类型定义 | `frontend/src/features/topups/types/topup.types.ts` |
| API 服务 | `frontend/src/features/topups/services/topupsApi.ts` |
| React Query Hooks | `frontend/src/features/topups/hooks/useTopups.ts` |

### 9.2 后端

| 文件 | 路径 |
|------|------|
| 路由 | `backend/routers/topup.py` |
| 服务 | `backend/services/topup_service.py` |
| 模型 | `backend/models/topup.py` |
| Schema | `backend/schemas/topup.py` |

---

## 10. 实现状态 & Gap 分析

### 10.1 当前实现状态

| 功能点 | 状态 | 说明 |
|--------|------|------|
| 7 状态机 | ✅ 已实现 | 完整的状态定义和转换 |
| 双重审批流程 | ✅ 已实现 | data_operator + finance |
| 角色权限 | ✅ 已实现 | TOPUP_ACTION_ROLES 定义完整 |
| 统计卡片 | ✅ 已实现 | TopupsStatsOverview |
| 表格筛选 | ✅ 已实现 | 标签页 + 筛选器 |
| 审批对话框 | ✅ 已实现 | TopupApprovalDialog |
| 审批时间线 | ✅ 已实现 | ApprovalTimeline |

### 10.2 Gap 分析

| Gap | 优先级 | 说明 |
|-----|--------|------|
| ~~无明显 Gap~~ | - | 前端实现与 MASTER.md 基本对齐 |

**结论**: 充值审批模块实现完善，与 MASTER.md 和 STATE_MACHINE.md 高度对齐。

### 10.3 后续优化建议

| 建议 | 优先级 | 说明 |
|------|--------|------|
| 大额申请标记 | P2 | 超过阈值的申请高亮显示 |
| 批量审批 | P2 | 支持批量通过/拒绝 |
| 审批通知 | P2 | 状态变更时通知相关人员 |
| 审批统计报表 | P3 | 审批效率、通过率等统计 |

---

## 11. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-22 | 初始版本 |

---

**维护者**: AI 广告代投系统开发团队
**关联文档**: MASTER.md v4.4, STATE_MACHINE.md v2.6, topup.types.ts
