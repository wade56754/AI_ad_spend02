# D1 月度结算 - 模块规格书

> **版本**: v1.0
> **更新日期**: 2025-12-22
> **优先级**: P2
> **基准**: MASTER.md v4.4 §6.2 页面 10, LEDGER_SOT.md v1.1

---

## 1. 模块概述

### 1.1 业务目标

**核心问题**: 这个月赚了还是亏了？

月度结算模块解决项目盈亏确认与锁定问题：
- 本月各项目的总消耗、总进粉是多少？
- 毛利多少？与预期相比如何？
- 结算锁定后是否还能修改？

### 1.2 用户角色

| 角色 | 职责 | 典型操作 |
|------|------|----------|
| `ceo` | 老板 | 查看月度盈亏、确认结算、锁定结算 |
| `finance` | 财务 | 生成结算报表、核对数据、锁定结算 |
| `project_owner` | 项目负责人 | 查看项目月度盈亏 |
| `admin` | 管理员 | 全权限（系统维护） |

### 1.3 核心用例

| 用例 | 描述 | 主要角色 |
|------|------|----------|
| UC-D1-01 | 查看月度结算列表 | finance, ceo |
| UC-D1-02 | 生成月度结算报表 | finance |
| UC-D1-03 | 核对结算数据 | finance |
| UC-D1-04 | 确认月度结算 | finance |
| UC-D1-05 | 锁定月度结算 | ceo, finance |
| UC-D1-06 | 查看结算明细 | finance, ceo |
| UC-D1-07 | 导出结算报表 | finance |

### 1.4 Phase 约束

| Phase | 约束 | 说明 |
|-------|------|------|
| **Phase 1 (照亮)** | 可修改 | 结算数据可修改，用于观察 |
| **Phase 2 (问责)** | 锁定后不可修改 | 启用结算锁定机制 |

**Phase 1 特别说明**:
- 盈亏用于「观察」，不用于「正式结算」
- Phase 1 盈亏用于「让老板看到趋势」，不用于「月度锁定结算」
- Phase 2 盈亏用于「月度锁定结算」，需财务确认

---

## 2. 数据需求

### 2.1 数据源 (SoT)

| 数据源 | 表/模型 | 用途 |
|--------|---------|------|
| monthly_settlements | 月度结算表 | 结算主表 |
| settlement_details | 结算明细表 | 项目级明细 |
| ad_spend_daily | 日消耗表 | 消耗 SoT |
| daily_reports | 日报表 | 进粉 SoT |
| projects | 项目表 | 项目信息 |
| ledger_entries | 账本表 | 资金流水 |

### 2.2 字段清单 (MASTER.md §6.2 页面 10)

**必须字段**:

| 字段 | 来源 | 说明 |
|------|------|------|
| `total_spend` | ad_spend_daily (SUM) | 总消耗 |
| `total_conversions` | daily_reports (SUM) | 总进粉 |
| `gross_profit` | 计算字段 | 毛利 |
| `is_locked` | monthly_settlements | 锁定状态 |

**扩展字段**:

| 字段 | 来源 | 说明 |
|------|------|------|
| `settlement_month` | monthly_settlements | 结算月份 |
| `project_count` | 计算字段 | 项目数 |
| `avg_cpl` | 计算字段 | 平均 CPL |
| `revenue` | 计算字段 | 预计收入 |
| `profit_rate` | 计算字段 | 毛利率 |
| `status` | monthly_settlements | 结算状态 |
| `confirmed_by` | users (JOIN) | 确认人 |
| `confirmed_at` | monthly_settlements | 确认时间 |
| `locked_by` | users (JOIN) | 锁定人 |
| `locked_at` | monthly_settlements | 锁定时间 |

### 2.3 计算公式 (MASTER.md §4.5.4)

**Phase 1 公式（观察用）**:

| 指标 | 公式 | 说明 |
|------|------|------|
| 总消耗 | `SUM(ad_spend_daily.spend)` | 月度总消耗 |
| 总进粉 | `SUM(daily_reports.conversions)` | 月度总进粉 |
| 预计收入 | `总进粉 × 项目单价` | 按项目 unit_price 计算 |
| 预计毛利 | `预计收入 - 总消耗` | 简化毛利 |
| 平均 CPL | `总消耗 / 总进粉` | 整体 CPL |

**Phase 2 公式（结算用）**:

| 指标 | 公式 | 说明 |
|------|------|------|
| 总消耗 | `SUM(daily_reports.real_spend)` | 确认后消耗 |
| 总进粉 | `SUM(daily_reports.conversions_final)` | 确认后进粉 |
| 确认收入 | `总进粉 × 项目单价` | 按确认数计算 |
| 确认毛利 | `确认收入 - 总消耗 - 手续费` | 含手续费 |

### 2.4 状态机

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        月度结算状态机                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌───────────┐    生成     ┌───────────┐    确认     ┌───────────┐        │
│   │  pending  │ ─────────→ │   draft   │ ─────────→ │ confirmed │        │
│   │ (待生成)  │            │  (草稿)   │            │  (已确认)  │        │
│   └───────────┘            └───────────┘            └─────┬─────┘        │
│                                                           │ 锁定          │
│                                                           ↓               │
│                                                     ┌───────────┐        │
│                                                     │  locked   │        │
│                                                     │  (已锁定)  │ ← 终态 │
│                                                     └───────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

| 状态 | 说明 | 可操作 |
|------|------|--------|
| `pending` | 月份结束，待生成结算 | 生成结算 |
| `draft` | 结算草稿，可修改 | 编辑、确认 |
| `confirmed` | 已确认，待锁定 | 锁定、撤销确认 |
| `locked` | 已锁定，不可修改 | 仅查看 |

---

## 3. UI 规范

### 3.1 页面布局

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [页面头部]                                                                   │
│ 月度结算                                              [刷新] [导出]          │
│ 项目月度盈亏结算与锁定                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ [筛选区]                                                                     │
│ ┌───────────────────────────────────────────────────────────────────────┐  │
│ │ 结算月份: [2025-12 ▼]  项目: [全部 ▼]  状态: [全部 ▼]                 │  │
│ └───────────────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────────┤
│ [KPI 卡片区]                                                                 │
│ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ │
│ │ 结算月份   │ │ 总消耗     │ │ 总进粉     │ │ 预计毛利   │ │ 毛利率     │ │
│ │ 2025-12    │ │ ¥2,856,800 │ │ 72,580     │ │ ¥568,000   │ │ 19.9%      │ │
│ └────────────┘ └────────────┘ └────────────┘ └────────────┘ └────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ [项目明细表格]                                                               │
│ ┌──────┬────────┬──────────┬────────┬────────┬──────────┬────────┬───────┐ │
│ │ 项目 │ 负责人 │ 总消耗   │ 总进粉 │ CPL    │ 预计毛利 │ 状态   │ 操作  │ │
│ ├──────┼────────┼──────────┼────────┼────────┼──────────┼────────┼───────┤ │
│ │项目A │ 张三   │ ¥856,000 │ 21,500 │ ¥39.81 │ ¥215,000 │ 草稿   │[确认] │ │
│ │项目B │ 李四   │ ¥650,000 │ 18,200 │ ¥35.71 │ ¥182,000 │ 已确认 │[锁定] │ │
│ │项目C │ 王五   │ ¥480,000 │ 13,500 │ ¥35.56 │ ¥135,000 │ 已锁定 │[查看] │ │
│ └──────┴────────┴──────────┴────────┴────────┴──────────┴────────┴───────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ [汇总行]                                                                     │
│ 合计: 12 个项目 | 总消耗: ¥2,856,800 | 总进粉: 72,580 | 预计毛利: ¥568,000  │
├─────────────────────────────────────────────────────────────────────────────┤
│ [分页]                                                    第 1/2 页 [< >]   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 组件清单

| 组件 | 代码块 | 用途 |
|------|--------|------|
| MonthlySettlementPage | 页面容器 | 主页面组件 |
| MonthPicker | 月份选择器 | 选择结算月份 |
| StatCard × 5 | KPI 卡片 | 汇总统计 |
| SettlementTable | DataTable | 项目明细表格 |
| SettlementDetailDrawer | DetailDrawer | 明细抽屉 |
| ConfirmDialog | 确认对话框 | 确认/锁定操作 |
| StatusBadge | 状态徽章 | 状态展示 |
| ExportButton | 导出按钮 | 导出报表 |

### 3.3 状态颜色规范

| 状态 | 颜色 | Tailwind Class |
|------|------|----------------|
| `pending` | 灰色 | `bg-gray-100 text-gray-600` |
| `draft` | 蓝色 | `bg-blue-100 text-blue-700` |
| `confirmed` | 橙色 | `bg-orange-100 text-orange-700` |
| `locked` | 绿色 | `bg-green-100 text-green-700` |

### 3.4 交互规则

| 交互 | 触发 | 行为 |
|------|------|------|
| 选择月份 | 点击月份选择器 | 加载该月结算数据 |
| 生成结算 | 点击生成按钮 | 汇总该月数据，生成结算单 |
| 确认结算 | 点击确认按钮 | 确认数据准确，状态变更 |
| 锁定结算 | 点击锁定按钮 | 锁定数据，不可修改 |
| 查看明细 | 点击行 | 打开明细抽屉 |
| 导出 | 点击导出按钮 | 下载 Excel 报表 |

---

## 4. API 接口

### 4.1 接口清单

| 方法 | 路径 | 用途 | 权限 |
|------|------|------|------|
| GET | `/api/v1/settlements/monthly` | 获取月度结算列表 | finance, ceo |
| GET | `/api/v1/settlements/monthly/{id}` | 获取结算详情 | finance, ceo |
| POST | `/api/v1/settlements/monthly/generate` | 生成月度结算 | finance |
| PUT | `/api/v1/settlements/monthly/{id}` | 更新结算数据 | finance (draft) |
| POST | `/api/v1/settlements/monthly/{id}/confirm` | 确认结算 | finance |
| POST | `/api/v1/settlements/monthly/{id}/lock` | 锁定结算 | ceo, finance |
| POST | `/api/v1/settlements/monthly/{id}/unlock` | 解锁结算 (admin) | admin |
| GET | `/api/v1/settlements/monthly/{id}/details` | 获取项目明细 | finance, ceo |
| GET | `/api/v1/settlements/monthly/export` | 导出结算报表 | finance |
| GET | `/api/v1/settlements/monthly/summary` | 获取汇总统计 | finance, ceo |

### 4.2 请求/响应示例

**获取月度结算列表**:
```http
GET /api/v1/settlements/monthly?month=2025-12&page=1&page_size=20
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
        "settlement_month": "2025-12",
        "project_id": 101,
        "project_name": "项目A",
        "owner_name": "张三",
        "total_spend": 856000.00,
        "total_conversions": 21500,
        "avg_cpl": 39.81,
        "revenue": 1075000.00,
        "gross_profit": 219000.00,
        "profit_rate": 25.6,
        "status": "draft",
        "confirmed_by": null,
        "confirmed_at": null,
        "is_locked": false,
        "created_at": "2025-12-22T00:00:00Z"
      }
    ],
    "total": 12,
    "page": 1,
    "page_size": 20,
    "summary": {
      "total_spend": 2856800.00,
      "total_conversions": 72580,
      "total_revenue": 3629000.00,
      "total_profit": 772200.00,
      "avg_profit_rate": 27.0
    }
  }
}
```

**生成月度结算**:
```http
POST /api/v1/settlements/monthly/generate
Authorization: Bearer {token}
Content-Type: application/json

{
  "month": "2025-12",
  "project_ids": [101, 102, 103]  // 可选，不传则全部项目
}
```

```json
{
  "code": "SUCCESS",
  "message": "结算生成成功",
  "data": {
    "month": "2025-12",
    "generated_count": 12,
    "total_spend": 2856800.00,
    "total_conversions": 72580
  }
}
```

**锁定结算**:
```http
POST /api/v1/settlements/monthly/1/lock
Authorization: Bearer {token}
Content-Type: application/json

{
  "confirm": true,
  "notes": "2025年12月结算确认锁定"
}
```

```json
{
  "code": "SUCCESS",
  "message": "结算已锁定",
  "data": {
    "id": 1,
    "status": "locked",
    "locked_by": "财务张",
    "locked_at": "2025-12-22T15:00:00Z"
  }
}
```

---

## 5. 权限矩阵

### 5.1 功能权限

| 功能 | ceo | finance | project_owner | admin |
|------|-----|---------|---------------|-------|
| 查看列表 | ✓ | ✓ | ○ | ✓ |
| 生成结算 | - | ✓ | - | ✓ |
| 编辑结算 | - | ✓ | - | ✓ |
| 确认结算 | - | ✓ | - | ✓ |
| 锁定结算 | ✓ | ✓ | - | ✓ |
| 解锁结算 | - | - | - | ✓ |
| 导出报表 | ✓ | ✓ | - | ✓ |

**说明**: ✓ = 全部可见, ○ = 仅自己项目, - = 无权限

### 5.2 数据权限

| 角色 | 数据范围 |
|------|----------|
| `ceo` | 全部结算 |
| `finance` | 全部结算 |
| `project_owner` | 仅自己负责项目 |
| `admin` | 全部结算 |

---

## 6. 代码块组合

### 6.1 前端代码块

```
MonthlySettlementPage (需从 SettlementsPage 改造)
├── 页头组件
│   ├── PageTitle
│   └── ActionButtons (刷新, 导出, 生成)
├── 筛选区
│   ├── MonthPicker
│   ├── SelectProject
│   └── SelectStatus
├── StatCard × 5
│   ├── 结算月份
│   ├── 总消耗
│   ├── 总进粉
│   ├── 预计毛利
│   └── 毛利率
├── SettlementTable
│   ├── DataTable
│   ├── StatusBadge
│   └── ActionButtons
├── ConfirmDialog
├── LockDialog
└── SettlementDetailDrawer
```

### 6.2 后端代码块

```
MonthlySettlementRouter (需新建或扩展)
├── monthly_settlement_service
│   ├── generate_monthly_settlement()
│   ├── confirm_settlement()
│   ├── lock_settlement()
│   └── get_settlement_details()
├── ledger_service (锁定时)
│   └── create_settlement_entry()
└── export_service
    └── generate_settlement_report()
```

### 6.3 组合图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           月度结算模块组合图                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [前端]                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ MonthlySettlementPage                                               │   │
│  │  ├── useMonthlySettlements() ─────────────────────┐                 │   │
│  │  ├── useSettlementSummary() ──────────────────────┤                 │   │
│  │  └── useLockSettlement() ─────────────────────────┤                 │   │
│  └───────────────────────────────────────────────────┼─────────────────┘   │
│                                                      │                      │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┼ ─ ─ ─ ─ ─ ─ ─ ─ ─   │
│                                                      │                      │
│  [后端]                                              ↓                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ MonthlySettlementRouter (/api/v1/settlements/monthly)               │   │
│  │  ├── GET /              → settlement_service.list()                 │   │
│  │  ├── POST /generate     → settlement_service.generate()             │   │
│  │  ├── POST /{id}/confirm → settlement_service.confirm()              │   │
│  │  ├── POST /{id}/lock    → settlement_service.lock() + ledger_entry  │   │
│  │  └── GET /export        → export_service.generate_report()          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  [数据聚合]                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ad_spend_daily (消耗 SoT) ──→ SUM(spend) GROUP BY month, project    │   │
│  │ daily_reports (进粉 SoT) ──→ SUM(conversions) GROUP BY month, project│   │
│  │ projects (单价) ──→ unit_price for revenue calculation              │   │
│  │ ledger_entries ──→ 锁定时写入                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. 测试检查点

### 7.1 功能测试

| 检查点 | 预期结果 |
|--------|----------|
| 生成结算 | 正确汇总月度数据 |
| 查看列表 | 按月份展示结算记录 |
| 确认结算 | 状态变更为 confirmed |
| 锁定结算 | 状态变更为 locked，数据不可修改 |
| 导出报表 | 生成正确的 Excel |

### 7.2 计算测试

| 检查点 | 预期结果 |
|--------|----------|
| 总消耗 | SUM(ad_spend_daily.spend) 正确 |
| 总进粉 | SUM(daily_reports.conversions) 正确 |
| 预计收入 | 总进粉 × unit_price 正确 |
| 毛利 | 收入 - 消耗 正确 |
| 毛利率 | (毛利 / 收入) × 100% 正确 |

### 7.3 锁定测试

| 检查点 | 预期结果 |
|--------|----------|
| 锁定后编辑 | 被拒绝 |
| 锁定后删除 | 被拒绝 |
| admin 解锁 | 状态变回 confirmed |

### 7.4 权限测试

| 检查点 | 预期结果 |
|--------|----------|
| project_owner 查看 | 仅看到自己项目 |
| project_owner 锁定 | 被拒绝 |
| finance 锁定 | 成功 |
| ceo 锁定 | 成功 |

---

## 8. 源码位置

### 8.1 前端

| 文件 | 路径 | 状态 |
|------|------|------|
| 页面组件 | `frontend/src/features/settlements/components/SettlementsPage.tsx` | ⚠️ 通用结算页面 |
| 表格组件 | `frontend/src/features/settlements/components/SettlementsTable.tsx` | ✅ 已实现 |
| 类型定义 | `frontend/src/features/settlements/types/settlement.types.ts` | ⚠️ 需扩展月度结算 |
| Hooks | `frontend/src/features/settlements/hooks/useSettlements.ts` | ✅ 已实现 |
| API 服务 | `frontend/src/features/settlements/services/settlementsApi.ts` | ✅ 已实现 |

### 8.2 后端

| 文件 | 路径 |
|------|------|
| 路由 | `backend/routers/settlements.py` |
| 服务 | `backend/services/settlement_service.py` |
| 模型 | `backend/models/settlement.py` |
| Schema | `backend/schemas/settlement.py` |

---

## 9. 实现状态 & Gap 分析

### 9.1 当前实现状态

| 功能点 | 状态 | 说明 |
|--------|------|------|
| 结算列表 | ✅ 已实现 | 通用结算管理 |
| 结算状态 | ✅ 已实现 | 7 状态机 |
| 统计卡片 | ✅ 已实现 | 5 个 KPI 卡片 |
| 审批流程 | ✅ 已实现 | 确认/拒绝 |
| React Query | ✅ 已实现 | hooks 完整 |

### 9.2 Gap 分析

| Gap | 优先级 | 说明 |
|-----|--------|------|
| 月度维度改造 | P1 | 当前是通用结算，需改造为月度项目结算 |
| 自动汇总生成 | P1 | 需实现按月汇总消耗/进粉数据 |
| 锁定机制 | P1 | Phase 2 锁定后不可修改 |
| 盈亏计算 | P1 | 需对齐 MASTER.md §4.5.4 公式 |
| 与项目关联 | P1 | 需按项目维度展示 |
| 月份选择器 | P2 | 需添加月份筛选 |
| 导出功能 | P2 | 需实现月度报表导出 |

### 9.3 后续开发任务

| 任务 | 优先级 | 预计工作量 |
|------|--------|------------|
| 改造为月度项目结算 | P1 | 6h |
| 实现自动汇总 API | P1 | 4h |
| 实现锁定机制 | P1 | 3h |
| 对接盈亏计算公式 | P1 | 2h |
| 添加月份选择器 | P2 | 1h |
| 实现导出功能 | P2 | 3h |

---

## 10. Phase 约束详细说明

### 10.1 Phase 1 行为

```python
# Phase 1 配置
PHASE2_SETTLEMENT_LOCK = False  # 锁定机制关闭

# 结算可修改
def update_settlement(id, data):
    # Phase 1: 允许修改，用于观察和调整
    settlement = get_settlement(id)
    settlement.update(data)
    # 不检查锁定状态
```

### 10.2 Phase 2 行为

```python
# Phase 2 配置
PHASE2_SETTLEMENT_LOCK = True  # 锁定机制开启

# 锁定后不可修改
def update_settlement(id, data):
    settlement = get_settlement(id)
    if settlement.is_locked:
        raise BusinessError("结算已锁定，不可修改")
    settlement.update(data)
```

### 10.3 锁定后的处理

- 锁定后如需修改，需 admin 先解锁
- 解锁需记录审计日志
- 重大修改建议创建红冲记录而非直接修改

---

## 11. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-22 | 初始版本 |

---

**维护者**: AI 广告代投系统开发团队
**关联文档**: MASTER.md v4.4, LEDGER_SOT.md v1.1, settlement.types.ts
