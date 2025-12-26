# B2 日报审核 - 模块规格书

> **版本**: v1.0
> **更新日期**: 2025-12-22
> **优先级**: P1
> **基准**: MASTER.md v4.4 §6.2 页面 5, STATE_MACHINE.md v2.7 §8

---

## 1. 模块概述

### 1.1 业务目标

**核心问题**: 投手今天干得怎样？

日报审核模块解决投放效果监控与责任追踪问题：
- 投手今天消耗了多少？进了多少粉？
- CPL 是否达标？有无异常趋势？
- 需要主管介入调整吗？

### 1.2 用户角色

| 角色 | 职责 | 典型操作 |
|------|------|----------|
| `pitcher` | 投手 | 提交日报、查看自己数据 |
| `supervisor` | 主管 | 审核日报、标记异常、趋势复核、查看团队 |
| `project_owner` | 项目负责人 | 查看项目日报、确认最终数据 |
| `finance` | 财务 | 终审确认、锁定计费 |
| `ceo` | 老板 | 查看整体概况、关注异常 |
| `admin` | 管理员 | 全权限（系统维护） |

### 1.3 核心用例

| 用例 | 描述 | 主要角色 |
|------|------|----------|
| UC-B2-01 | 投手提交日报 | pitcher |
| UC-B2-02 | 趋势待审（自动触发） | system |
| UC-B2-03 | 趋势通过/标记异常 | supervisor |
| UC-B2-04 | 处理异常 | supervisor |
| UC-B2-05 | 终审待审 | project_owner |
| UC-B2-06 | 终审确认 | finance, admin |
| UC-B2-07 | 锁定入账 | system, admin |

### 1.4 Phase 约束

| Phase | 约束 | 说明 |
|-------|------|------|
| **Phase 1 (照亮)** | 可选审核 + 高亮 | 记录异常，展示趋势，不强制阻断 |
| **Phase 2 (问责)** | 必须审核 + 暂停建议 | 连续异常触发暂停建议，主管必须每日审核 |

**Phase 1 简化流程**:
- 日报从 `raw_submitted` 可直接跳转 `trend_ok`（主管快速确认）
- 财务快速确认计费（`trend_ok` → `final_confirmed`）
- 无自动拒绝、无自动暂停、无自动冻结

---

## 2. 数据需求

### 2.1 数据源 (SoT)

| 数据源 | 表/模型 | 用途 |
|--------|---------|------|
| daily_reports | 日报表 | 日报数据、状态、审核记录 |
| ad_spend_daily | 广告消耗表 | 消耗 SoT（Phase 1）|
| ad_account | 广告账户表 | 账户信息 |
| project | 项目表 | 关联项目、目标 CPL |
| user | 用户表 | 投手、审核人信息 |

### 2.2 字段清单 (MASTER.md §6.2 页面 5)

**必须字段**:

| 字段 | 来源 | 说明 |
|------|------|------|
| `report_date` | daily_reports | 日报日期 |
| `pitcher_name` | user (JOIN) | 投手姓名 |
| `project_name` | project (JOIN) | 项目名称 |
| `spend` | daily_reports.raw_spend | 消耗金额 |
| `conversions` | daily_reports.follows_count | 进粉数 |
| `cpl` | 计算字段 | spend / conversions |
| `is_abnormal` | 计算字段 | CPL > target × 1.3 |
| `status` | daily_reports | 审核状态 (8 状态) |

**扩展字段 (v2.0)**:

| 字段 | 来源 | 说明 |
|------|------|------|
| `region` | daily_reports | 投放地区 |
| `platform` | daily_reports | 广告平台 (FB/Google/TikTok) |
| `result_count` | daily_reports | 成效数 |
| `cost_per_follow` | 计算字段 | 单粉成本 |
| `cost_per_result` | 计算字段 | 单次成效费用 |
| `trend_flag` | daily_reports | 趋势标记 |
| `trend_flag_reason` | daily_reports | 异常原因 |
| `team_name` | team (JOIN) | 团队名称 |
| `submitter_name` | user (JOIN) | 提交人姓名 |

### 2.3 计算公式

| 指标 | 公式 | 说明 |
|------|------|------|
| CPL | `raw_spend / follows_count` | 单粉成本 |
| 异常标记 | `CPL > target_cpl × 1.3` | 超标 30% 为异常 |
| 待审核数 | `COUNT(status IN ('trend_pending', 'final_pending'))` | 待审核日报数 |
| 异常数 | `COUNT(status = 'trend_flagged')` | 异常待处理数 |
| 已锁定数 | `COUNT(status = 'final_locked')` | 已完成日报数 |

### 2.4 SoT 字段边界 (MASTER.md §4.5.7)

| Phase | 消耗 SoT | 进粉 SoT |
|-------|----------|----------|
| Phase 1 | `ad_spend_daily.spend` | `daily_reports.conversions` (follows_count) |
| Phase 2 | `daily_reports.real_spend` | `daily_reports.conversions_final` |

**强制约束**: Phase 1 的消耗 SoT 只能是 `ad_spend_daily.spend`，禁止使用 `daily_reports.spend` 作为消耗来源。

---

## 3. 状态机 (STATE_MACHINE.md v2.7 §8)

### 3.1 状态定义 (8 状态)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        日报状态机 (8 状态)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   投手提交                                                                   │
│   ┌───────────────┐                                                         │
│   │ raw_submitted │  ──────────────────────────────────────┐               │
│   │  (原始提交)    │                                        │               │
│   └───────┬───────┘                                        │               │
│           │ 自动触发                                        │ Phase 1 快速  │
│           ↓                                                │               │
│   ┌───────────────┐    趋势正常     ┌─────────────┐        │               │
│   │ trend_pending │ ─────────────→ │  trend_ok   │ ←──────┘               │
│   │  (趋势待审)   │                │ (趋势通过)  │                         │
│   └───────┬───────┘                └──────┬──────┘                         │
│           │ 趋势异常                       │                                │
│           ↓                               │                                │
│   ┌───────────────┐    处理完成           │                                │
│   │ trend_flagged │ ──────────────┐      │                                │
│   │  (趋势异常)   │               │      │                                │
│   └───────────────┘               ↓      ↓                                │
│                           ┌───────────────────┐                            │
│                           │  trend_resolved   │                            │
│                           │   (异常已处理)     │                            │
│                           └─────────┬─────────┘                            │
│                                     │                                       │
│                                     ↓                                       │
│                           ┌───────────────────┐                            │
│                           │   final_pending   │                            │
│                           │    (终审待审)      │                            │
│                           └─────────┬─────────┘                            │
│                                     │ 财务确认                              │
│                                     ↓                                       │
│                           ┌───────────────────┐                            │
│                           │  final_confirmed  │                            │
│                           │   (终审确认)       │                            │
│                           └─────────┬─────────┘                            │
│                                     │ 系统锁定                              │
│                                     ↓                                       │
│                           ┌───────────────────┐                            │
│                           │   final_locked    │                            │
│                           │    (已锁定)        │  ← 终态                    │
│                           └───────────────────┘                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 状态转换规则

| 当前状态 | 目标状态 | 操作 | 允许角色 | 触发条件 |
|----------|----------|------|----------|----------|
| `raw_submitted` | `trend_pending` | submit_for_trend | system | 自动触发 |
| `trend_pending` | `trend_ok` | approve_trend | supervisor, project_owner, admin | 趋势正常 |
| `trend_pending` | `trend_flagged` | flag_trend | supervisor, project_owner, admin | 趋势异常 |
| `trend_flagged` | `trend_resolved` | resolve_flag | supervisor, project_owner, admin | 处理完成 |
| `trend_ok` | `final_pending` | submit_for_final | project_owner, admin | 提交终审 |
| `trend_resolved` | `final_pending` | submit_for_final | project_owner, admin | 提交终审 |
| `final_pending` | `final_confirmed` | confirm_final | finance, admin | 财务确认 |
| `final_confirmed` | `final_locked` | lock | system, admin | 锁定入账 |

### 3.3 趋势风控规则 (TF-xxx)

| 规则编号 | 规则描述 | 触发条件 | 结果 |
|----------|----------|----------|------|
| TF-001 | CPL 突增 | CPL > 7 日均值 × 1.5 | trend_flagged |
| TF-002 | 消耗突增 | spend > 7 日均值 × 2.0 | trend_flagged |
| TF-003 | 进粉骤降 | conversions < 7 日均值 × 0.5 | trend_flagged |

### 3.4 Phase 1 简化流程

```python
# Phase 1 允许跳过 trend_pending/trend_flagged/trend_resolved/final_pending
PHASE1_ALLOWED_SHORTCUTS = {
    "raw_submitted": ["trend_ok"],       # 主管快速确认
    "trend_ok": ["final_confirmed"],     # 财务快速确认
}
```

---

## 4. UI 规范

### 4.1 页面布局 (v3.0 视觉重构)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [页面头部]                                                                   │
│ 日报管理                                          [刷新] [导入] [导出]       │
│ 广告消耗日报数据及审批流程                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ [KPI 卡片区] (去边框+投影+色块图标)                                          │
│ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐                │
│ │ 总日报     │ │ 待审核     │ │ 异常待处理 │ │ 已锁定     │                │
│ │ 1,234      │ │ 56         │ │ 12         │ │ 890        │                │
│ └────────────┘ └────────────┘ └────────────┘ └────────────┘                │
├─────────────────────────────────────────────────────────────────────────────┤
│ [统一筛选面板] (白色容器)                                                    │
│ ┌───────────────────────────────────────────────────────────────────────┐  │
│ │ [搜索框]  [日期范围]  [团队▼]  [投手▼]  [高级筛选▼]  [清除]  [表/图]  │  │
│ ├───────────────────────────────────────────────────────────────────────┤  │
│ │ [全部|待审核|异常|已完成] (状态Tab)                                    │  │
│ └───────────────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────────┤
│ [数据表格]                                                                   │
│ ┌────┬────────┬────────┬────────┬──────┬──────┬────────┬────────┬───────┐ │
│ │日期│ 项目   │ 投手   │ 账户   │ 消耗 │ 进粉 │ CPL    │ 状态   │ 操作  │ │
│ ├────┼────────┼────────┼────────┼──────┼──────┼────────┼────────┼───────┤ │
│ │12-22│项目A  │张三    │账户1   │¥5000 │120   │¥41.67  │趋势异常│[审批] │ │
│ │12-22│项目B  │李四    │账户2   │¥3000 │100   │¥30.00  │趋势通过│[确认] │ │
│ │12-21│项目A  │张三    │账户1   │¥4500 │150   │¥30.00  │已锁定  │[查看] │ │
│ └────┴────────┴────────┴────────┴──────┴──────┴────────┴────────┴───────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ [分页]                                                    第 1/50 页 [< >]  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 组件清单

| 组件 | 代码块 | 用途 |
|------|--------|------|
| DailyReportsPage | 页面容器 | 主页面组件 |
| StatCard × 4 | KPI 卡片 | 统计卡片区 |
| StatusTabs | 状态标签 | 状态快速筛选 |
| DailyReportsTable | DataTable | 日报列表 |
| ActionButtons | 操作按钮 | 状态转换操作 |
| StatusBadge | 状态徽章 | 状态展示 |
| FlagTrendDialog | 对话框 | 标记异常 |
| ResolveFlagDialog | 对话框 | 处理异常 |
| ConfirmFinalDialog | 对话框 | 终审确认 |
| DailyReportDetail | 详情抽屉 | 日报详情 |
| DailyReportForm | 表单 | 新建/编辑日报 |

### 4.3 状态颜色规范

| 状态 | 颜色 | Tailwind Class | 说明 |
|------|------|----------------|------|
| `raw_submitted` | 灰色 | `bg-gray-100 text-gray-800` | 原始提交 |
| `trend_pending` | 蓝色 | `bg-blue-100 text-blue-800` | 趋势待审 |
| `trend_ok` | 绿色 | `bg-green-100 text-green-800` | 趋势通过 |
| `trend_flagged` | 橙色 | `bg-amber-100 text-amber-800` | 趋势异常 |
| `trend_resolved` | 蓝色 | `bg-blue-100 text-blue-800` | 异常已处理 |
| `final_pending` | 蓝色 | `bg-blue-100 text-blue-800` | 终审待审 |
| `final_confirmed` | 绿色 | `bg-green-100 text-green-800` | 终审确认 |
| `final_locked` | 灰色 | `bg-gray-100 text-gray-600` | 已锁定 |

### 4.4 交互规则

| 交互 | 触发 | 行为 |
|------|------|------|
| 点击 KPI 卡片 | 单击卡片 | 筛选对应状态 |
| 点击状态 Tab | 点击标签 | 切换状态筛选 |
| 点击行 | 单击表格行 | 打开详情抽屉 |
| 审批操作 | 点击操作按钮 | 打开对应对话框 |
| 高级筛选 | 点击展开 | 显示地区、平台筛选 |
| 视图切换 | 点击图标 | 表格/统计视图切换 |

---

## 5. API 接口

### 5.1 接口清单

| 方法 | 路径 | 用途 | 权限 |
|------|------|------|------|
| GET | `/api/v1/daily-reports` | 获取日报列表 | 登录用户 |
| GET | `/api/v1/daily-reports/{id}` | 获取日报详情 | 登录用户 |
| POST | `/api/v1/daily-reports` | 创建日报 | pitcher |
| PUT | `/api/v1/daily-reports/{id}` | 更新日报 | pitcher (raw_submitted) |
| POST | `/api/v1/daily-reports/{id}/submit-for-trend` | 提交趋势审核 | supervisor, project_owner |
| POST | `/api/v1/daily-reports/{id}/approve-trend` | 趋势通过 | supervisor, project_owner |
| POST | `/api/v1/daily-reports/{id}/flag-trend` | 标记异常 | supervisor, project_owner |
| POST | `/api/v1/daily-reports/{id}/resolve-flag` | 处理异常 | supervisor, project_owner |
| POST | `/api/v1/daily-reports/{id}/confirm-final` | 终审确认 | finance, admin |
| POST | `/api/v1/daily-reports/{id}/lock` | 锁定入账 | admin, system |
| GET | `/api/v1/daily-reports/stats` | 获取统计数据 | 登录用户 |
| GET | `/api/v1/daily-reports/export` | 导出数据 | 登录用户 |
| GET | `/api/v1/daily-reports/filter-options/teams` | 团队筛选选项 | 登录用户 |
| GET | `/api/v1/daily-reports/filter-options/submitters` | 投手筛选选项 | 登录用户 |

### 5.2 请求/响应示例

**获取日报列表**:
```http
GET /api/v1/daily-reports?status=trend_flagged&page=1&page_size=20
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
        "report_date": "2025-12-22",
        "ad_account_id": 101,
        "ad_account_name": "账户1",
        "project_id": 201,
        "project_name": "项目A",
        "raw_spend": 5000.00,
        "follows_count": 120,
        "result_count": 150,
        "cost_per_follow": 41.67,
        "region": "Turkey",
        "platform": "FB",
        "status": "trend_flagged",
        "trend_flag": "flagged",
        "trend_flag_reason": "CPL 超标 30%",
        "submitter_name": "张三",
        "team_name": "A组",
        "created_at": "2025-12-22T10:00:00Z"
      }
    ],
    "meta": {
      "pagination": {
        "total": 12,
        "page": 1,
        "page_size": 20
      }
    }
  }
}
```

**标记异常**:
```http
POST /api/v1/daily-reports/1/flag-trend
Authorization: Bearer {token}
Content-Type: application/json

{
  "reason": "CPL 超标 30%，需要调整投放策略",
  "flag_type": "TF-001"
}
```

**处理异常**:
```http
POST /api/v1/daily-reports/1/resolve-flag
Authorization: Bearer {token}
Content-Type: application/json

{
  "trend_notes": "已与投手沟通，明天调整出价策略",
  "resolution_action": "accept"
}
```

---

## 6. 权限矩阵

### 6.1 功能权限

| 功能 | ceo | project_owner | finance | supervisor | pitcher | account_manager | admin |
|------|-----|---------------|---------|------------|---------|-----------------|-------|
| 查看列表 | ✓ | ✓ | ✓ | ✓ | ○ | ✓ | ✓ |
| 创建日报 | - | - | - | - | ✓ | - | ✓ |
| 修改日报 | - | - | - | - | ○ | - | ✓ |
| 趋势审核 | - | ✓ | - | ✓ | - | - | ✓ |
| 标记异常 | - | ✓ | - | ✓ | - | - | ✓ |
| 处理异常 | - | ✓ | - | ✓ | - | - | ✓ |
| 终审确认 | - | - | ✓ | - | - | - | ✓ |
| 锁定入账 | - | - | - | - | - | - | ✓ |
| 导出数据 | ✓ | ✓ | ✓ | ✓ | - | - | ✓ |

**说明**: ✓ = 全部可见, ○ = 仅自己相关, - = 无权限

### 6.2 数据权限

| 角色 | 数据范围 |
|------|----------|
| `ceo` | 全部日报 |
| `project_owner` | 所负责项目的日报 |
| `finance` | 全部日报 |
| `supervisor` | 所管辖团队的日报 |
| `pitcher` | 仅自己的日报 |
| `account_manager` | 所管理账户的日报 |
| `admin` | 全部日报 |

---

## 7. 代码块组合

### 7.1 前端代码块

```
DailyReportsPage
├── StatCard × 4
├── StatusTabs
├── 筛选器组件
│   ├── SearchInput
│   ├── DateRangePicker
│   ├── SelectTeam
│   ├── SelectSubmitter
│   └── AdvancedFilters (Region, Platform)
├── DailyReportsTable
│   ├── DataTable
│   ├── StatusBadge
│   └── ActionButtons
├── FlagTrendDialog
├── ResolveFlagDialog
├── ConfirmFinalDialog
└── DailyReportDetail
```

### 7.2 后端代码块

```
DailyReportRouter
├── daily_report_service
│   ├── state_machine_transition
│   ├── permission_filter
│   ├── trend_risk_control_service
│   └── audit_log_writer
├── kpi_calculator (CPL计算)
└── export_service
```

### 7.3 组合图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           日报审核模块组合图                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [前端]                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ DailyReportsPage                                                    │   │
│  │  ├── useDailyReports() ───────────────────────┐                     │   │
│  │  ├── useDailyReportStats() ───────────────────┤                     │   │
│  │  └── useDailyReportActions() ─────────────────┤                     │   │
│  └───────────────────────────────────────────────┼─────────────────────┘   │
│                                                  │                          │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┼ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │
│                                                  │                          │
│  [后端]                                          ↓                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ DailyReportRouter (/api/v1/daily-reports)                           │   │
│  │  ├── GET /           → daily_report_service.list()                  │   │
│  │  ├── POST /          → daily_report_service.create()                │   │
│  │  ├── POST /{id}/flag-trend → trend_risk_control + audit_log         │   │
│  │  ├── POST /{id}/resolve-flag → state_machine.transition()           │   │
│  │  ├── POST /{id}/confirm-final → state_machine.transition()          │   │
│  │  └── POST /{id}/lock → state_machine.transition() + ledger_entry    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  [外部依赖]                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ad_spend_daily (消耗 SoT) ──→ CPL 计算                              │   │
│  │ daily_report_audit_logs ──→ 审计日志                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. 测试检查点

### 8.1 功能测试

| 检查点 | 预期结果 |
|--------|----------|
| 投手创建日报 | pitcher 可创建，其他角色不可 |
| 趋势自动触发 | raw_submitted → trend_pending 自动转换 |
| 趋势通过 | trend_pending → trend_ok |
| 标记异常 | trend_pending → trend_flagged |
| 处理异常 | trend_flagged → trend_resolved |
| 终审确认 | final_pending → final_confirmed |
| 锁定入账 | final_confirmed → final_locked |
| 权限校验 | 非授权角色操作被拒绝 |

### 8.2 趋势风控测试

| 检查点 | 预期结果 |
|--------|----------|
| TF-001 CPL 突增 | CPL > 7 日均值 × 1.5 触发 trend_flagged |
| TF-002 消耗突增 | spend > 7 日均值 × 2.0 触发 trend_flagged |
| TF-003 进粉骤降 | conversions < 7 日均值 × 0.5 触发 trend_flagged |

### 8.3 数据完整性测试

| 检查点 | 预期结果 |
|--------|----------|
| CPL 计算 | raw_spend / follows_count 正确 |
| 状态统计 | stats 接口返回各状态正确数量 |
| 审计日志 | 每次状态变更有审计记录 |
| 锁定后不可修改 | final_locked 状态禁止修改 |

---

## 9. 源码位置

### 9.1 前端

| 文件 | 路径 |
|------|------|
| 页面组件 | `frontend/src/features/daily-reports/components/DailyReportsPage.tsx` |
| 表格组件 | `frontend/src/features/daily-reports/components/DailyReportsTable.tsx` |
| 操作按钮 | `frontend/src/features/daily-reports/components/ActionButtons.tsx` |
| 状态徽章 | `frontend/src/features/daily-reports/components/StatusBadge.tsx` |
| 标记异常对话框 | `frontend/src/features/daily-reports/components/FlagTrendDialog.tsx` |
| 处理异常对话框 | `frontend/src/features/daily-reports/components/ResolveFlagDialog.tsx` |
| 终审确认对话框 | `frontend/src/features/daily-reports/components/ConfirmFinalDialog.tsx` |
| 类型定义 | `frontend/src/features/daily-reports/types/dailyReport.types.ts` |
| API 服务 | `frontend/src/features/daily-reports/services/dailyReportsApi.ts` |
| React Query Hooks | `frontend/src/features/daily-reports/hooks/useDailyReports.ts` |
| Actions Hook | `frontend/src/features/daily-reports/hooks/useDailyReportActions.ts` |

### 9.2 后端

| 文件 | 路径 |
|------|------|
| 路由 | `backend/routers/daily_reports.py` |
| 服务 | `backend/services/daily_report_service.py` |
| 趋势风控 | `backend/services/trend_risk_control_service.py` |
| 模型 | `backend/models/workflow/daily_report.py` |
| Schema | `backend/schemas/daily_report.py` |

---

## 10. 实现状态 & Gap 分析

### 10.1 当前实现状态

| 功能点 | 状态 | 说明 |
|--------|------|------|
| 8 状态机 | ✅ 已实现 | 完整的状态定义和转换 |
| 状态转换操作 | ✅ 已实现 | ActionButtons + 对应 Dialog |
| KPI 卡片 | ✅ 已实现 | StatCard (v3.0 去边框+投影) |
| 状态 Tab | ✅ 已实现 | StatusTabs 组件 |
| 筛选功能 | ✅ 已实现 | 日期、团队、投手、地区、平台 |
| 导出功能 | ✅ 已实现 | XLSX 导出 |
| v2.0 字段 | ✅ 已实现 | region, platform, follows_count, result_count |

### 10.2 Gap 分析

| Gap | 优先级 | 说明 |
|-----|--------|------|
| 趋势风控自动触发 | P1 | TF-001/002/003 规则需后端实现 |
| 与 ad_spend_daily 联动 | P1 | 消耗 SoT 应从 ad_spend_daily 读取 |

### 10.3 后续优化建议

| 建议 | 优先级 | 说明 |
|------|--------|------|
| 批量审批 | P2 | 支持批量趋势通过/标记异常 |
| 审批通知 | P2 | 状态变更时通知相关人员 |
| 趋势图表 | P2 | 可视化展示 CPL/消耗趋势 |
| 异常统计报表 | P3 | 按投手/项目统计异常次数 |

---

## 11. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-22 | 初始版本 |

---

**维护者**: AI 广告代投系统开发团队
**关联文档**: MASTER.md v4.4, STATE_MACHINE.md v2.7, dailyReport.types.ts
