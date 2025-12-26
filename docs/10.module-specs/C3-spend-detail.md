# C3 消耗明细 - 模块规格书

> **版本**: v1.0
> **更新日期**: 2025-12-22
> **优先级**: P1
> **基准**: MASTER.md v4.4 §6.2 页面 9, DATA_SCHEMA.md v5.3

---

## 1. 模块概述

### 1.1 业务目标

**核心问题**: 某天/某账户消耗多少？

消耗明细模块解决广告消耗数据查询与分析问题：
- 某个账户/项目某天消耗了多少？
- 消耗趋势如何？环比变化如何？
- 哪个账户/渠道消耗效率最高？

### 1.2 用户角色

| 角色 | 职责 | 典型操作 |
|------|------|----------|
| `pitcher` | 投手 | 查看自己负责账户的消耗 |
| `supervisor` | 主管 | 查看团队消耗、分析效率 |
| `finance` | 财务 | 核对消耗数据、导出报表 |
| `ceo` | 老板 | 查看整体消耗概况 |
| `admin` | 管理员 | 导入消耗数据、全权限 |

### 1.3 核心用例

| 用例 | 描述 | 主要角色 |
|------|------|----------|
| UC-C3-01 | 查看消耗列表 | 所有角色 |
| UC-C3-02 | 按日期范围筛选 | 所有角色 |
| UC-C3-03 | 按项目/账户/渠道筛选 | 所有角色 |
| UC-C3-04 | 查看消耗趋势图 | supervisor, ceo |
| UC-C3-05 | 导出消耗数据 | finance, admin |
| UC-C3-06 | 导入消耗数据 | admin |

### 1.4 SoT 约束

**消耗的唯一事实源** (MASTER.md §4.5.7):

| Phase | 消耗 SoT | 来源 | 说明 |
|-------|----------|------|------|
| Phase 1 | `ad_spend_daily.spend` | Excel 导入 / 手工录入 | 代理商后台数据 |
| Phase 2 | `daily_report.real_spend` | supervisor/finance 确认 | 成本核算、结算 |

**强制约束**: Phase 1 的消耗 SoT 只能是 `ad_spend_daily.spend`，禁止使用 `daily_report.spend` 作为消耗来源。

---

## 2. 数据需求

### 2.1 数据源 (SoT)

| 数据源 | 表/模型 | 用途 |
|--------|---------|------|
| ad_spend_daily | 日消耗表 | 消耗 SoT（Phase 1）|
| daily_reports | 日报表 | 进粉数据 |
| ad_account | 广告账户表 | 账户信息 |
| project | 项目表 | 项目信息 |
| channel | 渠道表 | 渠道信息 |

### 2.2 字段清单 (MASTER.md §6.2 页面 9)

**必须字段**:

| 字段 | 来源 | 说明 |
|------|------|------|
| `report_date` | ad_spend_daily.spend_date | 日期 |
| `ad_account_name` | ad_account (JOIN) | 账户名称 |
| `spend` | ad_spend_daily.spend_amount | 消耗金额 |
| `conversions` | daily_reports (JOIN) | 进粉数 |
| `cpl` | 计算字段 | spend / conversions |

**扩展字段**:

| 字段 | 来源 | 说明 |
|------|------|------|
| `project_name` | project (JOIN) | 项目名称 |
| `channel_name` | channel (JOIN) | 渠道名称 |
| `impressions` | ad_spend_daily | 曝光数 |
| `clicks` | ad_spend_daily | 点击数 |
| `ctr` | 计算字段 | clicks / impressions |
| `cpc` | 计算字段 | spend / clicks |
| `source_platform` | ad_spend_daily | 来源平台 |
| `currency` | ad_spend_daily | 货币类型 |

### 2.3 计算公式

| 指标 | 公式 | 说明 |
|------|------|------|
| CPL/CPA | `spend / conversions` | 单粉成本 |
| CTR | `clicks / impressions × 100%` | 点击率 |
| CPC | `spend / clicks` | 单次点击成本 |
| 总消耗 | `SUM(spend)` | 汇总消耗 |
| 日均消耗 | `SUM(spend) / 天数` | 平均每日消耗 |
| 环比变化 | `(本期 - 上期) / 上期 × 100%` | 消耗变化率 |

### 2.4 ad_spend_daily 表结构 (DATA_SCHEMA.md v5.3)

```sql
CREATE TABLE ad_spend_daily (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_platform VARCHAR(50),       -- 来源平台
  ad_account_code VARCHAR(100),      -- 账户代码
  spend_date DATE NOT NULL,          -- 消耗日期
  spend_amount DECIMAL(15,2) NOT NULL, -- 消耗金额
  currency VARCHAR(10) DEFAULT 'CNY', -- 货币
  raw_payload JSONB,                 -- 原始数据
  imported_by UUID,                  -- 导入人
  imported_at TIMESTAMP DEFAULT NOW() -- 导入时间
);
```

---

## 3. UI 规范

### 3.1 页面布局

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [页面头部]                                                                   │
│ 广告消耗                                              [导出] [刷新]          │
│ 查看和分析广告投放消耗数据                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ [筛选区]                                                                     │
│ ┌───────────────────────────────────────────────────────────────────────┐  │
│ │ [日期: ____ - ____]  [项目▼]  [渠道▼]  [账户▼]                        │  │
│ └───────────────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────────┤
│ [KPI 卡片区]                                                                 │
│ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐                │
│ │ 总消耗     │ │ 总粉数     │ │ 平均CPA    │ │ 平均CTR    │                │
│ │ ¥125,680   │ │ 1,560      │ │ ¥80.56     │ │ 2.56%      │                │
│ │ ↑8.5%      │ │ ↑12.3%     │ │            │ │            │                │
│ └────────────┘ └────────────┘ └────────────┘ └────────────┘                │
├─────────────────────────────────────────────────────────────────────────────┤
│ [数据表格]                                                                   │
│ ┌────────┬────────┬────────┬────────┬────────┬──────┬──────┬──────┬──────┐ │
│ │ 账户   │ 项目   │ 渠道   │ 日期   │ 消耗   │ 曝光 │ 点击 │ 粉数 │ CPA  │ │
│ ├────────┼────────┼────────┼────────┼────────┼──────┼──────┼──────┼──────┤ │
│ │账户A   │项目Alpha│抖音   │12-08   │¥15,680 │125K  │3,200 │156   │¥100.5│ │
│ │账户B   │项目Beta │快手   │12-08   │¥12,350 │98K   │2,800 │134   │¥92.2 │ │
│ │账户C   │项目Gamma│百度   │12-08   │¥8,920  │76K   │1,900 │89    │¥100.2│ │
│ └────────┴────────┴────────┴────────┴────────┴──────┴──────┴──────┴──────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ [分页]                          显示 1-20 共 156 条          [< 1 2 3 ... >]│
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 组件清单

| 组件 | 代码块 | 用途 |
|------|--------|------|
| AdSpendPage | 页面容器 | 主页面组件 |
| StatCard × 4 | KPI 卡片 | 统计卡片区 |
| DateRangePicker | 日期筛选 | 日期范围选择 |
| SelectProject | 项目筛选 | 项目下拉 |
| SelectChannel | 渠道筛选 | 渠道下拉 |
| SelectAccount | 账户筛选 | 账户下拉 |
| SpendTable | DataTable | 消耗明细表格 |
| SpendTrendChart | TrendChart | 消耗趋势图（可选） |
| Pagination | 分页组件 | 分页控制 |

### 3.3 交互规则

| 交互 | 触发 | 行为 |
|------|------|------|
| 日期筛选 | 选择日期范围 | 刷新表格数据 |
| 项目筛选 | 选择项目 | 筛选该项目的消耗 |
| 渠道筛选 | 选择渠道 | 筛选该渠道的消耗 |
| 导出 | 点击导出按钮 | 下载 Excel 文件 |
| 刷新 | 点击刷新按钮 | 重新加载数据 |
| 分页 | 点击页码 | 切换分页 |
| 排序 | 点击表头 | 按列排序 |

---

## 4. API 接口

### 4.1 接口清单

| 方法 | 路径 | 用途 | 权限 |
|------|------|------|------|
| GET | `/api/v1/ad-spend` | 获取消耗列表 | 登录用户 |
| GET | `/api/v1/ad-spend/summary` | 获取汇总统计 | 登录用户 |
| GET | `/api/v1/ad-spend/trend` | 获取趋势数据 | 登录用户 |
| GET | `/api/v1/ad-spend/by-project` | 按项目汇总 | 登录用户 |
| GET | `/api/v1/ad-spend/by-account` | 按账户汇总 | 登录用户 |
| GET | `/api/v1/ad-spend/export` | 导出数据 | finance, admin |
| POST | `/api/v1/ad-spend/import` | 导入数据 | admin |

### 4.2 请求/响应示例

**获取消耗列表**:
```http
GET /api/v1/ad-spend?start_date=2025-12-01&end_date=2025-12-22&project_id=1&page=1&page_size=20
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
        "ad_account_id": 101,
        "ad_account_name": "账户A-抖音",
        "project_id": 201,
        "project_name": "项目Alpha",
        "channel_id": 301,
        "channel_name": "抖音",
        "report_date": "2025-12-22",
        "spend": 15680.50,
        "impressions": 125000,
        "clicks": 3200,
        "conversions": 156,
        "ctr": 2.56,
        "cpc": 4.90,
        "cpa": 100.52,
        "created_at": "2025-12-22T10:00:00Z"
      }
    ],
    "total": 156,
    "page": 1,
    "page_size": 20,
    "summary": {
      "total_spend": 125680.50,
      "total_impressions": 1250000,
      "total_clicks": 32000,
      "total_conversions": 1560,
      "avg_ctr": 2.56,
      "avg_cpc": 3.93,
      "avg_cpa": 80.56,
      "record_count": 156
    }
  }
}
```

**获取趋势数据**:
```http
GET /api/v1/ad-spend/trend?start_date=2025-12-01&end_date=2025-12-22&project_id=1
Authorization: Bearer {token}
```

```json
{
  "code": "SUCCESS",
  "message": "获取成功",
  "data": {
    "items": [
      { "date": "2025-12-01", "spend": 12500.00, "conversions": 145, "cpa": 86.21 },
      { "date": "2025-12-02", "spend": 13200.00, "conversions": 152, "cpa": 86.84 },
      { "date": "2025-12-03", "spend": 11800.00, "conversions": 138, "cpa": 85.51 }
    ],
    "total_spend": 125680.50,
    "total_conversions": 1560,
    "avg_cpa": 80.56
  }
}
```

**导入消耗数据**:
```http
POST /api/v1/ad-spend/import
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: [Excel 文件]
source_platform: "代理商A"
```

```json
{
  "code": "SUCCESS",
  "message": "导入成功",
  "data": {
    "imported_count": 156,
    "skipped_count": 3,
    "error_count": 0,
    "import_job_id": "job-123"
  }
}
```

---

## 5. 权限矩阵

### 5.1 功能权限

| 功能 | ceo | finance | supervisor | pitcher | admin |
|------|-----|---------|------------|---------|-------|
| 查看列表 | ✓ | ✓ | ✓ | ○ | ✓ |
| 筛选数据 | ✓ | ✓ | ✓ | ○ | ✓ |
| 查看趋势 | ✓ | ✓ | ✓ | - | ✓ |
| 导出数据 | ✓ | ✓ | - | - | ✓ |
| 导入数据 | - | - | - | - | ✓ |

**说明**: ✓ = 全部可见, ○ = 仅自己相关, - = 无权限

### 5.2 数据权限

| 角色 | 数据范围 |
|------|----------|
| `ceo` | 全部消耗数据 |
| `finance` | 全部消耗数据 |
| `supervisor` | 所管辖团队的消耗 |
| `pitcher` | 仅自己负责账户的消耗 |
| `admin` | 全部消耗数据 |

---

## 6. 代码块组合

### 6.1 前端代码块

```
AdSpendPage
├── 页头组件
│   ├── PageTitle
│   └── ActionButtons (导出, 刷新)
├── 筛选区
│   ├── DateRangePicker
│   ├── SelectProject
│   ├── SelectChannel
│   └── SelectAccount
├── StatCard × 4
│   ├── 总消耗
│   ├── 总粉数
│   ├── 平均CPA
│   └── 平均CTR
├── SpendTable
│   ├── DataTable
│   └── Pagination
└── SpendTrendChart (可选)
```

### 6.2 后端代码块

```
AdSpendRouter
├── ad_spend_service
│   ├── list_spend()
│   ├── get_summary()
│   ├── get_trend()
│   ├── get_by_project()
│   └── get_by_account()
├── import_service
│   ├── parse_excel()
│   ├── validate_data()
│   └── bulk_insert()
├── export_service
│   └── generate_excel()
└── permission_filter
```

### 6.3 组合图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           消耗明细模块组合图                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [前端]                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ AdSpendPage                                                         │   │
│  │  ├── useAdSpendList() ────────────────────────┐                     │   │
│  │  ├── useAdSpendSummary() ─────────────────────┤                     │   │
│  │  └── useAdSpendTrend() ───────────────────────┤                     │   │
│  └───────────────────────────────────────────────┼─────────────────────┘   │
│                                                  │                          │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┼ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │
│                                                  │                          │
│  [后端]                                          ↓                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ AdSpendRouter (/api/v1/ad-spend)                                    │   │
│  │  ├── GET /           → ad_spend_service.list()                      │   │
│  │  ├── GET /summary    → ad_spend_service.get_summary()               │   │
│  │  ├── GET /trend      → ad_spend_service.get_trend()                 │   │
│  │  ├── GET /export     → export_service.generate_excel()              │   │
│  │  └── POST /import    → import_service.bulk_insert()                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  [数据源]                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ad_spend_daily (消耗 SoT)                                           │   │
│  │   ↓ JOIN                                                            │   │
│  │ ad_account, project, channel (关联表)                               │   │
│  │   ↓ LEFT JOIN                                                       │   │
│  │ daily_reports (进粉数据)                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. 测试检查点

### 7.1 功能测试

| 检查点 | 预期结果 |
|--------|----------|
| 列表加载 | 正确展示消耗记录 |
| 日期筛选 | 按日期范围过滤 |
| 项目筛选 | 按项目过滤 |
| 渠道筛选 | 按渠道过滤 |
| 分页 | 正确分页展示 |
| 排序 | 按列正确排序 |
| 导出 | 生成正确的 Excel |
| 导入 | 正确解析并入库 |

### 7.2 计算测试

| 检查点 | 预期结果 |
|--------|----------|
| CPA 计算 | spend / conversions 正确 |
| CTR 计算 | clicks / impressions × 100% 正确 |
| CPC 计算 | spend / clicks 正确 |
| 汇总统计 | SUM 计算正确 |
| 环比变化 | 变化率计算正确 |

### 7.3 权限测试

| 检查点 | 预期结果 |
|--------|----------|
| pitcher 查看 | 仅看到自己负责账户 |
| supervisor 查看 | 看到团队数据 |
| finance 导出 | 可以导出 |
| pitcher 导出 | 被拒绝 |
| admin 导入 | 可以导入 |

---

## 8. 源码位置

### 8.1 前端

| 文件 | 路径 |
|------|------|
| 页面组件 | `frontend/src/features/ad-spend/components/AdSpendPage.tsx` |
| 类型定义 | `frontend/src/features/ad-spend/types/adSpend.types.ts` |
| 索引导出 | `frontend/src/features/ad-spend/index.ts` |

### 8.2 后端

| 文件 | 路径 |
|------|------|
| 路由 | `backend/routers/ad_spend.py` |
| 服务 | `backend/services/ad_spend_service.py` |
| 模型 | `backend/models/ad_spend_daily.py` |
| Schema | `backend/schemas/ad_spend.py` |

---

## 9. 实现状态 & Gap 分析

### 9.1 当前实现状态

| 功能点 | 状态 | 说明 |
|--------|------|------|
| 页面布局 | ⚠️ 基础实现 | 使用 Mock 数据 |
| 类型定义 | ✅ 已实现 | adSpend.types.ts 完整 |
| 筛选功能 | ⚠️ 基础实现 | 日期、项目、渠道筛选 |
| KPI 卡片 | ✅ 已实现 | StatCard 组件 |
| 数据表格 | ⚠️ 基础实现 | 静态表格 |
| 分页 | ⚠️ UI 存在 | 功能未接入 |
| 导出 | ❌ 未实现 | alert 占位 |
| 导入 | ❌ 未实现 | 缺失 |
| API 对接 | ❌ 未实现 | 使用 Mock 数据 |

### 9.2 Gap 分析

| Gap | 优先级 | 说明 |
|-----|--------|------|
| API 对接 | P0 | 需接入真实后端 API |
| 分页功能 | P0 | 需实现分页逻辑 |
| 导出功能 | P1 | 需实现 Excel 导出 |
| 导入功能 | P1 | 需实现 Excel 导入 |
| React Query | P1 | 需使用 TanStack Query |
| 趋势图表 | P2 | 可选，增加可视化 |
| 权限过滤 | P1 | 按角色过滤数据 |

### 9.3 后续开发任务

| 任务 | 优先级 | 预计工作量 |
|------|--------|------------|
| 创建 useAdSpend hooks | P0 | 2h |
| 对接后端 API | P0 | 4h |
| 实现分页排序 | P0 | 2h |
| 实现导出功能 | P1 | 3h |
| 实现导入功能 | P1 | 4h |
| 添加趋势图表 | P2 | 3h |
| 权限过滤 | P1 | 2h |

---

## 10. 数据导入规范

### 10.1 Excel 模板

| 列名 | 必填 | 类型 | 说明 |
|------|------|------|------|
| 日期 | ✓ | Date | YYYY-MM-DD |
| 账户代码 | ✓ | String | 广告账户标识 |
| 消耗金额 | ✓ | Decimal | 保留2位小数 |
| 货币 | - | String | 默认 CNY |
| 曝光数 | - | Integer | 可选 |
| 点击数 | - | Integer | 可选 |
| 转化数 | - | Integer | 可选 |

### 10.2 导入验证规则

| 规则 | 说明 |
|------|------|
| 日期校验 | 必须是有效日期，不能是未来 |
| 账户校验 | 账户代码必须存在于系统中 |
| 金额校验 | 必须大于等于 0 |
| 重复检测 | 同一账户同一日期不能重复导入 |

### 10.3 导入错误处理

| 错误类型 | 处理方式 |
|----------|----------|
| 格式错误 | 跳过该行，记录错误 |
| 账户不存在 | 跳过该行，记录错误 |
| 重复数据 | 可选：覆盖 / 跳过 |
| 批量失败 | 回滚整批，返回错误列表 |

---

## 11. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-22 | 初始版本 |

---

**维护者**: AI 广告代投系统开发团队
**关联文档**: MASTER.md v4.4, DATA_SCHEMA.md v5.3, adSpend.types.ts
