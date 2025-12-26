# B3 周度简报 - 模块规格书

> **版本**: v1.0
> **更新日期**: 2025-12-22
> **优先级**: P2
> **基准**: MASTER.md v4.4 §6.2 页面 6, §3.1/§3.2 Phase 约束
> **实现状态**: 待开发

---

## 1. 模块概述

### 1.1 业务目标

**核心问题**: 项目这周进展如何？

周度简报模块解决项目周度运营复盘问题：
- 本周各项目消耗、进粉情况如何？
- 遇到了什么问题？如何解决？
- 下周的计划是什么？

### 1.2 用户角色

| 角色 | 职责 | 典型操作 |
|------|------|----------|
| `project_owner` | 项目负责人 | 提交周报、编辑周报 |
| `ceo` | 老板 | 查看所有项目周报 |
| `finance` | 财务 | 查看周报（了解项目进展） |
| `supervisor` | 主管 | 查看团队项目周报 |
| `admin` | 管理员 | 全权限（系统维护） |

### 1.3 核心用例

| 用例 | 描述 | 主要角色 |
|------|------|----------|
| UC-B3-01 | 查看周报列表 | ceo, project_owner |
| UC-B3-02 | 创建周报 | project_owner |
| UC-B3-03 | 编辑周报 | project_owner |
| UC-B3-04 | 提交周报 | project_owner |
| UC-B3-05 | 查看周报详情 | ceo, finance, supervisor |
| UC-B3-06 | 查看项目周报历史 | project_owner, ceo |
| UC-B3-07 | 导出周报 | project_owner, ceo |

### 1.4 Phase 约束 (MASTER.md §3.1/§3.2)

| Phase | 约束 | 说明 |
|-------|------|------|
| **Phase 1 (照亮)** | 可选提交 | 周报非强制，用于观察习惯 |
| **Phase 2 (问责)** | 必须提交 + 考核关联 | 周五下班前必须提交 |

**Phase 1 特别说明**:
- 周报用于「项目负责人主动沟通」
- 不强制要求填写周报
- 系统记录填报率，用于观察
- 不与考核挂钩

**Phase 2 启用条件** (MASTER.md §3.3):
```
- Phase 1 已稳定运行至少 2 个月
- 周报提交率 > 80%
- 老板明确批准启动 Phase 2
```

**环境变量控制**:
```python
PHASE2_WEEKLY_BRIEF_REQUIRED = false  # 周报必须提交
```

---

## 2. 数据需求

### 2.1 数据源 (SoT)

| 数据源 | 表/模型 | 用途 |
|--------|---------|------|
| weekly_briefs | 周报表 (新建) | 周报主表 |
| projects | 项目表 | 关联项目 |
| users | 用户表 | 提交人 |
| ad_spend_daily | 日消耗表 | 周消耗统计 |
| daily_reports | 日报表 | 周进粉统计 |

### 2.2 数据模型设计 (新建)

#### weekly_briefs 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | BIGSERIAL | PK | 主键 |
| `project_id` | BIGINT | FK → projects.id, NOT NULL | 关联项目 |
| `week_start` | DATE | NOT NULL | 周开始日期（周一） |
| `week_end` | DATE | NOT NULL | 周结束日期（周日） |
| `submitter_id` | UUID | FK → users.id, NOT NULL | 提交人 |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'draft' | 状态 |
| `weekly_spend` | DECIMAL(15,2) | DEFAULT 0.00 | 周消耗（自动汇总） |
| `weekly_conversions` | INTEGER | DEFAULT 0 | 周进粉（自动汇总） |
| `weekly_cpl` | DECIMAL(10,2) | DEFAULT 0.00 | 周 CPL（计算） |
| `achievements` | TEXT | 可空 | 本周成果 |
| `issues` | TEXT | 可空 | 遇到问题 |
| `solutions` | TEXT | 可空 | 解决方案 |
| `next_week_plan` | TEXT | 可空 | 下周计划 |
| `submitted_at` | TIMESTAMPTZ | 可空 | 提交时间 |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

**约束**:
- `UNIQUE (project_id, week_start)` - 每项目每周一份周报
- `CHECK (week_end >= week_start)` - 周期合法性
- `CHECK (status IN ('draft', 'submitted'))` - 状态枚举

### 2.3 字段清单 (MASTER.md §6.2 页面 6)

**必须字段**:

| 字段 | 来源 | 说明 |
|------|------|------|
| `weekly_spend` | ad_spend_daily (SUM) | 周消耗 |
| `weekly_conversions` | daily_reports (SUM) | 周进粉 |
| `issues` | weekly_briefs | 遇到问题 |
| `next_week_plan` | weekly_briefs | 下周计划 |

**扩展字段**:

| 字段 | 来源 | 说明 |
|------|------|------|
| `weekly_cpl` | 计算字段 | 周 CPL |
| `achievements` | weekly_briefs | 本周成果 |
| `solutions` | weekly_briefs | 解决方案 |
| `target_cpl` | projects | 目标 CPL |
| `cpl_trend` | 计算字段 | CPL 趋势（环比） |
| `status` | weekly_briefs | 周报状态 |
| `submitter_name` | users (JOIN) | 提交人姓名 |

### 2.4 计算公式

| 指标 | 公式 | 说明 |
|------|------|------|
| 周消耗 | `SUM(ad_spend_daily.spend WHERE date BETWEEN week_start AND week_end)` | 按项目账户汇总 |
| 周进粉 | `SUM(daily_reports.conversions WHERE date BETWEEN week_start AND week_end)` | 按项目汇总 |
| 周 CPL | `周消耗 / 周进粉` | 周进粉 = 0 时显示 "-" |
| CPL 环比 | `(本周 CPL - 上周 CPL) / 上周 CPL × 100%` | 上周无数据时显示 "-" |

### 2.5 状态机

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        周报状态机 (简化版)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌───────────┐    提交     ┌───────────┐                                  │
│   │   draft   │ ─────────→ │ submitted │ ← 终态                            │
│   │  (草稿)   │            │  (已提交)  │                                  │
│   └─────┬─────┘            └───────────┘                                  │
│         │ 编辑                    ↑ 重新提交                               │
│         └────────────────────────┘ (Phase 2: 周五前可撤回修改)             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

| 状态 | 说明 | 可操作 |
|------|------|--------|
| `draft` | 草稿，可编辑 | 编辑、提交 |
| `submitted` | 已提交，不可修改 | 仅查看 |

**Phase 2 扩展**:
- 周五 18:00 前可撤回修改
- 周五 18:00 后自动锁定
- 未提交触发提醒

---

## 3. UI 规范

### 3.1 页面布局

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [页面头部]                                                                   │
│ 周度简报                                              [创建周报] [导出]      │
│ 项目周度进展复盘                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ [筛选区]                                                                     │
│ ┌───────────────────────────────────────────────────────────────────────┐  │
│ │ 周次: [2025-W51 ▼]  项目: [全部 ▼]  状态: [全部 ▼]                    │  │
│ └───────────────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────────┤
│ [KPI 卡片区]                                                                 │
│ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ │
│ │ 本周项目数 │ │ 已提交     │ │ 待提交     │ │ 提交率     │ │ 本周总消耗 │ │
│ │ 12         │ │ 10         │ │ 2          │ │ 83.3%      │ │ ¥856,000   │ │
│ └────────────┘ └────────────┘ └────────────┘ └────────────┘ └────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ [周报列表表格]                                                               │
│ ┌──────┬────────┬──────────┬────────┬────────┬────────────┬───────┬──────┐ │
│ │ 项目 │ 负责人 │ 周消耗   │ 周进粉 │ CPL    │ 提交时间   │ 状态  │ 操作 │ │
│ ├──────┼────────┼──────────┼────────┼────────┼────────────┼───────┼──────┤ │
│ │项目A │ 张三   │ ¥156,000 │ 4,200  │ ¥37.14 │ 12-20 17:30│ 已提交│[查看]│ │
│ │项目B │ 李四   │ ¥120,000 │ 3,500  │ ¥34.29 │ -          │ 草稿  │[编辑]│ │
│ │项目C │ 王五   │ ¥98,000  │ 2,800  │ ¥35.00 │ 12-20 16:45│ 已提交│[查看]│ │
│ └──────┴────────┴──────────┴────────┴────────┴────────────┴───────┴──────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ [分页]                                                    第 1/2 页 [< >]   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 周报详情/编辑页面

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [页面头部]                                                                   │
│ ← 返回列表    项目A - 2025年第51周周报                     [保存] [提交]     │
├─────────────────────────────────────────────────────────────────────────────┤
│ [数据统计区 - 自动汇总]                                                      │
│ ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐        │
│ │ 周消耗             │ │ 周进粉             │ │ 周 CPL             │        │
│ │ ¥156,000           │ │ 4,200              │ │ ¥37.14             │        │
│ │ ↑ 8.3% vs 上周     │ │ ↑ 12.5% vs 上周   │ │ ↓ 3.8% vs 上周    │        │
│ └────────────────────┘ └────────────────────┘ └────────────────────┘        │
├─────────────────────────────────────────────────────────────────────────────┤
│ [周报内容区]                                                                 │
│                                                                             │
│ 本周成果                                                                     │
│ ┌───────────────────────────────────────────────────────────────────────┐  │
│ │ 1. 完成抖音渠道新账户测试，CPL 达标                                   │  │
│ │ 2. 优化落地页，转化率提升 5%                                          │  │
│ │ 3. ...                                                               │  │
│ └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│ 遇到问题 *                                                                   │
│ ┌───────────────────────────────────────────────────────────────────────┐  │
│ │ 1. 快手渠道审核变严，过审率下降                                       │  │
│ │ 2. 周末流量波动较大                                                   │  │
│ └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│ 解决方案                                                                     │
│ ┌───────────────────────────────────────────────────────────────────────┐  │
│ │ 1. 调整素材风格，预计下周过审率恢复                                   │  │
│ │ 2. 周末降低预算，避免无效消耗                                         │  │
│ └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│ 下周计划 *                                                                   │
│ ┌───────────────────────────────────────────────────────────────────────┐  │
│ │ 1. 测试视频号渠道                                                     │  │
│ │ 2. 提升日均消耗到 25,000                                              │  │
│ │ 3. CPL 目标控制在 35 以内                                             │  │
│ └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 组件清单

| 组件 | 代码块 | 用途 |
|------|--------|------|
| WeeklyBriefPage | 页面容器 | 主页面组件 |
| WeekPicker | 周选择器 | 选择周次 |
| StatCard × 5 | KPI 卡片 | 汇总统计 |
| WeeklyBriefTable | DataTable | 周报列表 |
| WeeklyBriefForm | 表单组件 | 创建/编辑周报 |
| WeeklyBriefDetail | 详情组件 | 查看周报 |
| StatusBadge | 状态徽章 | 状态展示 |
| TrendIndicator | 趋势指标 | 环比展示 |
| TextArea | 文本域 | 输入问题/计划 |

### 3.4 状态颜色规范

| 状态 | 颜色 | Tailwind Class |
|------|------|----------------|
| `draft` | 灰色 | `bg-gray-100 text-gray-600` |
| `submitted` | 绿色 | `bg-green-100 text-green-700` |

### 3.5 交互规则

| 交互 | 触发 | 行为 |
|------|------|------|
| 选择周次 | 点击周选择器 | 加载该周周报数据 |
| 创建周报 | 点击创建按钮 | 打开空白周报表单 |
| 编辑周报 | 点击编辑按钮 | 打开已有周报表单 |
| 保存草稿 | 点击保存按钮 | 保存不提交，状态保持 draft |
| 提交周报 | 点击提交按钮 | 状态变更为 submitted |
| 查看详情 | 点击行/查看按钮 | 打开只读详情页 |
| 导出 | 点击导出按钮 | 下载周报 PDF/Excel |

---

## 4. API 接口

### 4.1 接口清单

| 方法 | 路径 | 用途 | 权限 |
|------|------|------|------|
| GET | `/api/v1/weekly-briefs` | 获取周报列表 | project_owner, ceo, supervisor |
| GET | `/api/v1/weekly-briefs/{id}` | 获取周报详情 | project_owner, ceo, supervisor |
| POST | `/api/v1/weekly-briefs` | 创建周报 | project_owner |
| PUT | `/api/v1/weekly-briefs/{id}` | 更新周报 | project_owner (draft) |
| POST | `/api/v1/weekly-briefs/{id}/submit` | 提交周报 | project_owner |
| GET | `/api/v1/weekly-briefs/stats` | 获取周报统计 | ceo, supervisor |
| GET | `/api/v1/weekly-briefs/export` | 导出周报 | project_owner, ceo |
| GET | `/api/v1/projects/{id}/weekly-summary` | 获取项目周数据汇总 | project_owner |

### 4.2 请求/响应示例

**获取周报列表**:
```http
GET /api/v1/weekly-briefs?week=2025-W51&project_id=101&page=1&page_size=20
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
        "week_start": "2025-12-16",
        "week_end": "2025-12-22",
        "week_label": "2025年第51周",
        "submitter_id": "uuid-xxx",
        "submitter_name": "张三",
        "status": "submitted",
        "weekly_spend": 156000.00,
        "weekly_conversions": 4200,
        "weekly_cpl": 37.14,
        "cpl_trend": -3.8,
        "achievements": "1. 完成抖音渠道新账户测试...",
        "issues": "1. 快手渠道审核变严...",
        "solutions": "1. 调整素材风格...",
        "next_week_plan": "1. 测试视频号渠道...",
        "submitted_at": "2025-12-20T17:30:00Z",
        "created_at": "2025-12-20T10:00:00Z"
      }
    ],
    "total": 12,
    "page": 1,
    "page_size": 20,
    "stats": {
      "total_projects": 12,
      "submitted_count": 10,
      "draft_count": 2,
      "submission_rate": 83.3,
      "total_weekly_spend": 856000.00
    }
  }
}
```

**创建周报**:
```http
POST /api/v1/weekly-briefs
Authorization: Bearer {token}
Content-Type: application/json

{
  "project_id": 101,
  "week_start": "2025-12-16",
  "achievements": "1. 完成抖音渠道新账户测试...",
  "issues": "1. 快手渠道审核变严...",
  "solutions": "1. 调整素材风格...",
  "next_week_plan": "1. 测试视频号渠道..."
}
```

```json
{
  "code": "SUCCESS",
  "message": "周报创建成功",
  "data": {
    "id": 1,
    "project_id": 101,
    "week_start": "2025-12-16",
    "week_end": "2025-12-22",
    "status": "draft",
    "weekly_spend": 156000.00,
    "weekly_conversions": 4200,
    "weekly_cpl": 37.14
  }
}
```

**提交周报**:
```http
POST /api/v1/weekly-briefs/1/submit
Authorization: Bearer {token}
```

```json
{
  "code": "SUCCESS",
  "message": "周报提交成功",
  "data": {
    "id": 1,
    "status": "submitted",
    "submitted_at": "2025-12-20T17:30:00Z"
  }
}
```

**获取项目周数据汇总**:
```http
GET /api/v1/projects/101/weekly-summary?week_start=2025-12-16
Authorization: Bearer {token}
```

```json
{
  "code": "SUCCESS",
  "message": "获取成功",
  "data": {
    "project_id": 101,
    "project_name": "项目A",
    "week_start": "2025-12-16",
    "week_end": "2025-12-22",
    "weekly_spend": 156000.00,
    "weekly_conversions": 4200,
    "weekly_cpl": 37.14,
    "target_cpl": 40.00,
    "cpl_vs_target": -7.2,
    "last_week": {
      "spend": 144000.00,
      "conversions": 3750,
      "cpl": 38.40
    },
    "trends": {
      "spend_change": 8.3,
      "conversions_change": 12.0,
      "cpl_change": -3.3
    },
    "daily_breakdown": [
      {"date": "2025-12-16", "spend": 22000.00, "conversions": 600},
      {"date": "2025-12-17", "spend": 23500.00, "conversions": 620}
    ]
  }
}
```

---

## 5. 权限矩阵

### 5.1 功能权限

| 功能 | ceo | project_owner | finance | supervisor | admin |
|------|-----|---------------|---------|------------|-------|
| 查看列表 | ✓ | ○ | ✓ | ○ | ✓ |
| 创建周报 | - | ✓ | - | - | ✓ |
| 编辑周报 | - | ○ | - | - | ✓ |
| 提交周报 | - | ○ | - | - | ✓ |
| 查看详情 | ✓ | ○ | ✓ | ○ | ✓ |
| 查看统计 | ✓ | - | ✓ | ○ | ✓ |
| 导出周报 | ✓ | ○ | - | - | ✓ |

**说明**: ✓ = 全部可见, ○ = 仅自己项目/团队, - = 无权限

### 5.2 数据权限

| 角色 | 数据范围 |
|------|----------|
| `ceo` | 全部周报 |
| `project_owner` | 仅自己负责项目 |
| `finance` | 全部周报（只读） |
| `supervisor` | 团队项目周报 |
| `admin` | 全部周报 |

---

## 6. 代码块组合

### 6.1 前端代码块

```
WeeklyBriefPage (新建)
├── 页头组件
│   ├── PageTitle
│   └── ActionButtons (创建, 导出)
├── 筛选区
│   ├── WeekPicker
│   ├── SelectProject
│   └── SelectStatus
├── StatCard × 5
│   ├── 本周项目数
│   ├── 已提交
│   ├── 待提交
│   ├── 提交率
│   └── 本周总消耗
├── WeeklyBriefTable
│   ├── DataTable
│   ├── StatusBadge
│   └── ActionButtons
├── WeeklyBriefForm
│   ├── WeeklySummaryCard (自动汇总)
│   ├── TextArea × 4
│   └── SubmitButton
└── WeeklyBriefDetail
    ├── WeeklySummaryCard
    └── ContentSections
```

### 6.2 后端代码块

```
WeeklyBriefRouter (新建)
├── weekly_brief_service
│   ├── create_weekly_brief()
│   ├── update_weekly_brief()
│   ├── submit_weekly_brief()
│   ├── get_weekly_summary()
│   └── calculate_stats()
├── aggregation_service
│   ├── aggregate_weekly_spend()
│   └── aggregate_weekly_conversions()
└── export_service
    └── generate_brief_report()
```

### 6.3 组合图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           周度简报模块组合图                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [前端]                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ WeeklyBriefPage                                                     │   │
│  │  ├── useWeeklyBriefs() ─────────────────────────┐                   │   │
│  │  ├── useWeeklySummary() ────────────────────────┤                   │   │
│  │  └── useSubmitBrief() ──────────────────────────┤                   │   │
│  └─────────────────────────────────────────────────┼───────────────────┘   │
│                                                    │                        │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┼ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │
│                                                    │                        │
│  [后端]                                            ↓                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ WeeklyBriefRouter (/api/v1/weekly-briefs)                           │   │
│  │  ├── GET /              → brief_service.list()                      │   │
│  │  ├── POST /             → brief_service.create()                    │   │
│  │  ├── PUT /{id}          → brief_service.update()                    │   │
│  │  ├── POST /{id}/submit  → brief_service.submit()                    │   │
│  │  └── GET /stats         → brief_service.stats()                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  [数据聚合]                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ad_spend_daily ──→ SUM(spend) WHERE date BETWEEN week_start/end     │   │
│  │ daily_reports ──→ SUM(conversions) WHERE date BETWEEN week_start/end│   │
│  │ projects ──→ target_cpl for comparison                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. 业务规则

### 7.1 周报创建规则

| 规则编号 | 规则名称 | 详细约束 |
|---------|---------|---------|
| BR-BRIEF-001 | 周报唯一性 | 每项目每周只能有一份周报 |
| BR-BRIEF-002 | 周报创建权限 | 只有 project_owner 可创建 |
| BR-BRIEF-003 | 周次合法性 | week_start 必须是周一 |
| BR-BRIEF-004 | 自动汇总 | 创建时自动汇总周消耗/进粉 |

### 7.2 周报提交规则

| 规则编号 | 规则名称 | 详细约束 |
|---------|---------|---------|
| BR-BRIEF-010 | 提交必填项 | Phase 1: 无强制必填; Phase 2: issues + next_week_plan 必填 |
| BR-BRIEF-011 | 提交后锁定 | 提交后状态变为 submitted，不可修改 |
| BR-BRIEF-012 | 提交时间记录 | 提交时记录 submitted_at |

### 7.3 Phase 2 强制规则

| 规则编号 | 规则名称 | 详细约束 |
|---------|---------|---------|
| BR-BRIEF-020 | 周五截止 | Phase 2: 周五 18:00 前必须提交 |
| BR-BRIEF-021 | 未提交提醒 | Phase 2: 周五 15:00 发送提醒 |
| BR-BRIEF-022 | 考核关联 | Phase 2: 未提交计入考核 |

---

## 8. 测试检查点

### 8.1 功能测试

| 检查点 | 预期结果 |
|--------|----------|
| 创建周报 | 成功创建，状态为 draft |
| 编辑草稿 | 可修改内容 |
| 提交周报 | 状态变更为 submitted |
| 已提交编辑 | 被拒绝 |
| 重复创建 | 被拒绝（唯一性约束） |

### 8.2 数据汇总测试

| 检查点 | 预期结果 |
|--------|----------|
| 周消耗汇总 | SUM(ad_spend_daily.spend) 正确 |
| 周进粉汇总 | SUM(daily_reports.conversions) 正确 |
| 周 CPL 计算 | 消耗 / 进粉 正确 |
| 环比计算 | (本周 - 上周) / 上周 × 100% 正确 |

### 8.3 权限测试

| 检查点 | 预期结果 |
|--------|----------|
| project_owner 创建自己项目 | 成功 |
| project_owner 创建他人项目 | 被拒绝 |
| ceo 查看全部 | 成功 |
| supervisor 查看团队 | 仅看到团队项目 |

---

## 9. 源码位置

### 9.1 前端 (待创建)

| 文件 | 路径 | 状态 |
|------|------|------|
| 页面组件 | `frontend/src/features/weekly-briefs/components/WeeklyBriefsPage.tsx` | ❌ 待创建 |
| 表单组件 | `frontend/src/features/weekly-briefs/components/WeeklyBriefForm.tsx` | ❌ 待创建 |
| 类型定义 | `frontend/src/features/weekly-briefs/types/weeklyBrief.types.ts` | ❌ 待创建 |
| Hooks | `frontend/src/features/weekly-briefs/hooks/useWeeklyBriefs.ts` | ❌ 待创建 |
| API 服务 | `frontend/src/features/weekly-briefs/services/weeklyBriefsApi.ts` | ❌ 待创建 |

### 9.2 后端 (待创建)

| 文件 | 路径 | 状态 |
|------|------|------|
| 路由 | `backend/routers/weekly_briefs.py` | ❌ 待创建 |
| 服务 | `backend/services/weekly_brief_service.py` | ❌ 待创建 |
| 模型 | `backend/models/weekly_brief.py` | ❌ 待创建 |
| Schema | `backend/schemas/weekly_brief.py` | ❌ 待创建 |
| 迁移 | `backend/alembic/versions/xxx_add_weekly_briefs.py` | ❌ 待创建 |

---

## 10. 实现状态 & Gap 分析

### 10.1 当前实现状态

| 功能点 | 状态 | 说明 |
|--------|------|------|
| 数据模型 | ❌ 待创建 | weekly_briefs 表 |
| 后端 API | ❌ 待创建 | CRUD + 提交 |
| 前端页面 | ❌ 待创建 | 列表 + 表单 + 详情 |
| 周数据汇总 | ❌ 待创建 | 聚合服务 |
| 导出功能 | ❌ 待创建 | PDF/Excel 导出 |

### 10.2 开发任务清单

| 任务 | 优先级 | 预计工作量 | 依赖 |
|------|--------|------------|------|
| 创建 weekly_briefs 表 | P0 | 1h | - |
| 创建 Alembic 迁移 | P0 | 0.5h | 表设计 |
| 实现 weekly_brief_service | P0 | 4h | 表 |
| 实现 WeeklyBriefRouter | P0 | 3h | Service |
| 创建前端类型定义 | P0 | 1h | API |
| 创建前端 hooks | P0 | 2h | 类型 |
| 实现 WeeklyBriefsPage | P1 | 4h | Hooks |
| 实现 WeeklyBriefForm | P1 | 3h | Hooks |
| 实现周数据汇总 API | P1 | 2h | Service |
| 添加单元测试 | P1 | 3h | 全部 |
| 实现导出功能 | P2 | 3h | 全部 |

### 10.3 与其他模块关联

| 关联模块 | 关联方式 | 说明 |
|----------|----------|------|
| C1 项目管理 | 读取 | 获取项目信息 |
| B2 日报审核 | 读取 | 汇总周进粉 |
| C3 消耗明细 | 读取 | 汇总周消耗 |
| A1 驾驶舱 | 输出 | 周报提交率统计 |

---

## 11. Phase 约束详细说明

### 11.1 Phase 1 行为

```python
# Phase 1 配置
PHASE2_WEEKLY_BRIEF_REQUIRED = False

# 周报可选提交
def submit_weekly_brief(id, user):
    brief = get_brief(id)
    # Phase 1: 不强制必填项
    brief.status = 'submitted'
    brief.submitted_at = datetime.now()
    # 不检查截止时间
```

### 11.2 Phase 2 行为

```python
# Phase 2 配置
PHASE2_WEEKLY_BRIEF_REQUIRED = True

# 周报必须提交
def submit_weekly_brief(id, user):
    brief = get_brief(id)
    # Phase 2: 强制必填项
    if not brief.issues or not brief.next_week_plan:
        raise BusinessError("遇到问题和下周计划为必填项")
    brief.status = 'submitted'
    brief.submitted_at = datetime.now()

# 周五截止检查（定时任务）
def check_weekly_brief_deadline():
    friday_18 = get_friday_18()
    if datetime.now() > friday_18:
        unsubmitted = get_unsubmitted_briefs()
        for brief in unsubmitted:
            send_reminder(brief.submitter)
            record_missing(brief)  # 记录未提交，用于考核
```

---

## 12. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-22 | 初始版本，完整规格设计 |

---

**维护者**: AI 广告代投系统开发团队
**关联文档**: MASTER.md v4.4, DATA_SCHEMA.md v5.3
**实现状态**: 待开发 - 功能尚未实现，本规格书为开发指导文档
