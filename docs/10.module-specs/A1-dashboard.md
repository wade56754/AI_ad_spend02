# A1 老板驾驶舱 - 模块规格书

> **模块编号**: A1
> **优先级**: P0
> **版本**: v1.0
> **更新日期**: 2025-12-22
> **基准**: MASTER.md v4.4 §6.5

---

## 1. 模块概述

### 1.1 业务目标

**一句话定义**: 让老板在 5 秒内掌握"今天公司怎么样"

**核心价值**:
- 全局视角：一眼看到公司今日核心 KPI
- 趋势洞察：发现异常趋势，提前预警
- 行动闭环：从数据 → 归因对象 → 操作入口

**解决的问题**:
| 老板问题 | 系统答案 |
|---------|---------|
| 今天花了多少钱？ | 今日消耗 KPI |
| 今天进了多少粉？ | 今日粉数 KPI |
| 整体 CPL 怎么样？ | CPL 指标 + 趋势图 |
| 预计今天赚还是亏？ | 预计毛利 KPI |
| 哪些项目需要关注？ | 异常项目数 + Top 列表 |
| 有什么待处理？ | 待审批充值数 |

### 1.2 用户角色

| 角色 | 访问权限 | 数据范围 |
|------|---------|---------|
| `ceo` | 全部功能 | 全公司数据 |
| `project_owner` | 只读 | 自己负责的项目 |
| `finance` | 只读 | 全公司数据 |
| `supervisor` | 只读 | 自己团队数据 |
| `pitcher` | 只读 | 自己的数据 |
| `account_manager` | 只读 | 账户相关数据 |
| `admin` | 只读 | 全公司数据 |

### 1.3 核心用例

```
UC-A1-01: 查看今日概览
  前置: 用户已登录
  主流程:
    1. 用户打开驾驶舱页面
    2. 系统展示 4 个核心 KPI 卡片
    3. 系统展示趋势图
    4. 系统展示 Top 列表
  后置: 用户了解今日整体情况

UC-A1-02: 切换时间范围
  前置: 驾驶舱页面已加载
  主流程:
    1. 用户点击时间筛选器
    2. 选择：今日/7日/30日/自定义
    3. 系统重新加载对应时间范围数据
    4. KPI 和趋势图同步更新
  后置: 数据刷新到新的时间范围

UC-A1-03: 联动趋势图
  前置: 驾驶舱页面已加载
  主流程:
    1. 用户点击某个 KPI 卡片（如"今日消耗"）
    2. 主趋势图切换到对应指标
    3. KPI 卡片显示选中状态
  后置: 趋势图展示选中指标的详细趋势

UC-A1-04: 快速跳转异常处理
  前置: 存在待处理事项
  主流程:
    1. 用户查看待处理卡片
    2. 点击"待审批充值 (3)"
    3. 跳转到充值审批页面（已筛选待审批）
  后置: 进入详情页面处理
```

---

## 2. 数据需求

### 2.1 数据源 (SoT)

| 数据 | SoT 表 | SoT 字段 | 说明 |
|------|--------|---------|------|
| 消耗 | `ad_spend_daily` | `spend` | Phase 1 消耗 SoT |
| 进粉 | `daily_report` | `conversions` | Phase 1 进粉 SoT |
| 充值 | `topup_record` | `amount` | 充值 SoT |
| 项目 | `project` | `status`, `owner_id` | 项目信息 |
| 待审批 | `topup_request` | `status='pending'` | 待处理数 |

### 2.2 字段清单 (MASTER.md §6.5)

**页面 1：老板驾驶舱 - 必须字段**

| 字段 | 来源 | 口径 | 必须 | 当前状态 |
|------|------|------|------|---------|
| 本月总消耗 | ad_spend_daily | `SUM(spend)` | :white_check_mark: | :white_check_mark: 已实现 |
| 本月总进粉 | daily_report | `SUM(conversions)` | :white_check_mark: | :white_check_mark: 已实现 |
| 整体 CPL | 计算 | `总消耗/总进粉` (§4.5.2 规则) | :white_check_mark: | :white_check_mark: 已实现 |
| 预计毛利 | 计算 | §4.5.4 公式 | :white_check_mark: | :white_check_mark: 已实现 |
| 活跃项目数 | project | `COUNT(status='active')` | :white_check_mark: | :white_check_mark: 已实现 |
| 异常项目数 | 计算 | `CPL > target × 1.3` | :white_check_mark: | :white_check_mark: 已实现 |
| 待审批充值数 | topup_request | `COUNT(status='pending')` | :white_check_mark: | :white_check_mark: 已实现 |

### 2.3 计算公式

```python
# CPL 计算 (MASTER.md §4.5.1)
def calculate_cpl(spend: Decimal, conversions: int) -> str | Decimal:
    if conversions == 0:
        return "--"  # 显示占位符
    if conversions < 5:
        return f"{spend / conversions:.2f} (低量)"
    return spend / conversions

# 预计毛利 (MASTER.md §4.5.4 Phase 1 口径)
预计收入 = conversions × unit_price
预计成本 = SUM(ad_spend_daily.spend)
预计毛利 = 预计收入 - 预计成本

# 异常项目判定
异常 = CPL > target_cpl × 1.3
```

### 2.4 数据刷新策略

| 数据类型 | 刷新频率 | 实现方式 |
|---------|---------|---------|
| KPI 卡片 | 页面加载 + 手动刷新 | React Query |
| 趋势图 | 时间范围变化时 | React Query + 依赖 |
| Top 列表 | 页面加载 | React Query |
| 待处理数 | 实时 (5 分钟轮询) | React Query refetchInterval |

---

## 3. UI 规范

### 3.1 页面布局

```
┌─────────────────────────────────────────────────────────────────────────┐
│ [DashboardHeader]                          [GlobalDateFilter: 7d ▼]    │
├─────────────────────────────────────────────────────────────────────────┤
│ [AlertBanner: 风险告警条] (可选)                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ [QuickActions: 创建计划 | 查看报表 | 财务中心]                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  【本月概览】 ← MASTER.md §6.5 必须字段                                  │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐               │
│  │本月总消耗  │ │本月总进粉  │ │ 整体 CPL  │ │ 预计毛利  │ StatCard × 4   │
│  │ ¥285.7w  │ │  72,580   │ │  ¥39.36   │ │ ¥56.8w   │               │
│  │ +12.5%   │ │ +8.3%     │ │ -5.2%     │ │ +15.2%   │               │
│  │今日¥12.6k│ │ 今日3,256 │ │目标¥35.00 │ │今日¥3.7w │               │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘               │
│                                                                         │
│  【运营状态】 ← MASTER.md §6.5 必须字段                                  │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐                             │
│  │活跃项目数  │ │异常项目数  │ │待审批充值  │ StatCard × 3               │
│  │    12    │ │    3     │ │    3     │                             │
│  │          │ │CPL超标30%+│ │需老板审批  │                             │
│  └───────────┘ └───────────┘ └───────────┘                             │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  【趋势分析】                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │ [MainTrendChart: 多指标趋势图]                                      ││
│  │ 指标切换: 消耗 | 收入 | 利润 | 转化                                 ││
│  │ 自动总结: "近7日消耗稳定上升，日均增长2.3%"                          ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  【归因列表】                                                            │
│  ┌─────────────────────────────┐ ┌─────────────────────────────┐        │
│  │ [TopList: 消耗 Top 5]      │ │ [TopList: ROAS 最差 Top 5] │        │
│  └─────────────────────────────┘ └─────────────────────────────┘        │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  【待处理事项】                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │ [PendingTasksCard]                                                  ││
│  │ 待审批充值(3) | 待结算项目(2) | 待对账(5) | 待处理导入(1)            ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────┐ ┌─────────────────────────────┐        │
│  │ [AccountOverviewCard]      │ │ [SystemStatusCard]          │        │
│  │ 活跃项目: 12               │ │ 系统状态: 正常               │        │
│  │ 活跃账户: 45               │ │ 最后同步: 5分钟前            │        │
│  └─────────────────────────────┘ └─────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 组件清单

| 组件 | 位置 | 职责 | 代码块文档 |
|------|------|------|-----------|
| `DashboardHeader` | 顶部 | 页面标题、刷新按钮 | - |
| `GlobalDateFilter` | 右上 | 全局时间范围筛选 | [global-date-filter.md](../9.code-blocks/frontend/workflow/global-date-filter.md) |
| `AlertBanner` | 顶部下 | 风险告警横幅 | - |
| `StatCard` | KPI 区 | 单个 KPI 展示 | [stat-card.md](../9.code-blocks/frontend/core/stat-card.md) |
| `MainTrendChart` | 趋势区 | 多指标趋势图 | [trend-chart.md](../9.code-blocks/frontend/chart/trend-chart.md) |
| `TopLists` | 归因区 | Top N 列表 | [top-list.md](../9.code-blocks/frontend/chart/top-list.md) |
| `PendingTasksCard` | 待处理区 | 待处理事项入口 | - |
| `AccountOverviewCard` | 底部 | 账户/项目概览 | - |
| `SystemStatusCard` | 底部 | 系统状态 | - |

### 3.3 交互规则

| 交互 | 触发 | 行为 |
|------|------|------|
| 点击 StatCard | 单击 | 切换趋势图指标，卡片高亮 |
| 切换时间范围 | 下拉选择 | 全局刷新 KPI + 趋势图 |
| 点击待处理项 | 单击 | 跳转到对应页面（带筛选参数） |
| 点击 Top 列表项 | 单击 | 跳转到项目详情页 |
| 手动刷新 | 点击刷新按钮 | 重新获取所有数据 |

### 3.4 响应式布局

| 断点 | KPI 卡片 | 趋势图 | Top 列表 |
|------|---------|--------|---------|
| Desktop (lg+) | 4 列 | 全宽 | 2 列 |
| Tablet (md) | 2 列 | 全宽 | 1 列 |
| Mobile (sm) | 1 列 | 全宽 | 1 列 |

---

## 4. 代码块组合

### 4.1 前端代码块

| 代码块 | 使用位置 | 数量 | Props 传递 |
|--------|---------|------|-----------|
| `StatCard` | KPI 区 | 4 | title, value, change, icon, color, onClick, isActive |
| `TrendChart` | 趋势区 | 1 | data, activeMetric, onMetricChange, summary |
| `TopList` | 归因区 | 2 | campaigns, sortBy |
| `DataState` | 全局 | 1 | loading, error, empty |

### 4.2 后端代码块

| 代码块 | 使用位置 | 说明 |
|--------|---------|------|
| `kpi-calculator` | 聚合接口 | 计算 CPL、毛利 |
| `permission-filter` | 数据查询 | 按角色过滤数据 |
| `response-envelope` | API 响应 | 标准化响应格式 |

### 4.3 组合图

```
                    ┌─────────────────────┐
                    │   DashboardPage     │
                    └─────────┬───────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ StatCard × 4  │   │ MainTrendChart  │   │   TopLists      │
│ (KPI 展示)    │   │ (趋势分析)      │   │ (Top N 归因)    │
└───────┬───────┘   └────────┬────────┘   └────────┬────────┘
        │                    │                     │
        └────────────────────┼─────────────────────┘
                             │
                    ┌────────▼────────┐
                    │ FilterContext   │
                    │ (全局筛选状态)  │
                    └─────────────────┘
```

---

## 5. API 接口

### 5.1 接口清单

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 获取驾驶舱数据 | GET | `/api/v1/dashboard/overview` | 聚合 KPI |
| 获取趋势数据 | GET | `/api/v1/dashboard/trend` | 趋势图数据 |
| 获取 Top 列表 | GET | `/api/v1/dashboard/top-projects` | Top N 项目 |
| 获取待处理数 | GET | `/api/v1/dashboard/pending-counts` | 各类待处理数 |

### 5.2 接口详情

#### GET /api/v1/dashboard/overview

**请求参数**:
```
date_from: string (YYYY-MM-DD)
date_to: string (YYYY-MM-DD)
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "total_spend": 125680.50,
    "total_conversions": 3256,
    "total_revenue": 162500.00,
    "total_profit": 36819.50,
    "cpl": 38.61,
    "spend_change": 12.5,
    "conversions_change": 8.3,
    "revenue_change": 10.8,
    "profit_change": 15.2,
    "active_projects": 12,
    "abnormal_projects": 3,
    "pending_topups": 3
  },
  "message": "success"
}
```

#### GET /api/v1/dashboard/trend

**请求参数**:
```
date_from: string
date_to: string
metrics: string[] (spend, revenue, profit, conversions)
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "points": [
      {
        "date": "2025-12-15",
        "spend": 120000,
        "revenue": 160000,
        "profit": 40000,
        "conversions": 3000
      }
    ],
    "summary": {
      "trend": "up",
      "change_percent": 2.3,
      "description": "近7日消耗稳定上升"
    }
  }
}
```

---

## 6. 状态与权限

### 6.1 状态管理

| 状态 | 类型 | 管理方式 | 说明 |
|------|------|---------|------|
| 全局日期范围 | `DateRangePreset` | useState | 今日/7日/30日/自定义 |
| 选中指标 | `MetricType` | useState | spend/revenue/profit/conversions |
| 告警列表 | `Alert[]` | useState | 可关闭的告警 |
| 数据加载 | 自动 | React Query | isLoading, isError |

### 6.2 权限矩阵

| 功能 | ceo | project_owner | finance | supervisor | pitcher |
|------|-----|---------------|---------|------------|---------|
| 查看全公司 KPI | :white_check_mark: | :x: | :white_check_mark: | :x: | :x: |
| 查看自己项目 KPI | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| 查看 Top 列表 | :white_check_mark: | 部分 | :white_check_mark: | 部分 | :x: |
| 手动刷新 | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| 跳转审批页 | :white_check_mark: | :x: | :white_check_mark: | :x: | :x: |

---

## 7. 测试检查点

### 7.1 功能测试

- [ ] KPI 卡片显示正确数值
- [ ] KPI 变化百分比计算正确
- [ ] 时间范围切换后数据刷新
- [ ] 点击 KPI 卡片联动趋势图
- [ ] Top 列表排序正确
- [ ] 待处理数显示正确
- [ ] 跳转链接参数正确

### 7.2 边界测试

- [ ] 零转化时 CPL 显示 "--"
- [ ] 低量 (conversions < 5) 标记 "(低量)"
- [ ] 空数据状态展示
- [ ] 加载状态 Skeleton
- [ ] 错误状态处理

### 7.3 权限测试

- [ ] ceo 可见全公司数据
- [ ] pitcher 只能看自己数据
- [ ] project_owner 只能看自己项目

---

## 8. 源码位置

### 8.1 前端

| 类型 | 路径 |
|------|------|
| 页面入口 | `frontend/src/app/(dashboard)/page.tsx` |
| 主组件 | `frontend/src/features/dashboard/components/DashboardPage.tsx` |
| StatCard | `frontend/src/features/dashboard/components/StatCard.tsx` |
| TrendChart | `frontend/src/features/dashboard/components/MainTrendChart.tsx` |
| TopLists | `frontend/src/features/dashboard/components/TopLists.tsx` |
| 筛选器 | `frontend/src/features/dashboard/components/GlobalDateFilter.tsx` |
| 类型定义 | `frontend/src/features/dashboard/types/index.ts` |
| 工具函数 | `frontend/src/features/dashboard/utils/formatters.ts` |

### 8.2 后端

| 类型 | 路径 |
|------|------|
| Router | `backend/routers/dashboard.py` (待创建) |
| Service | `backend/services/dashboard_service.py` (待创建) |
| 聚合查询 | `backend/services/finance/profit_service.py` |

---

## 9. 待完成事项

### 9.1 对齐 MASTER.md §6.5

| 字段 | 当前状态 | 行动 |
|------|---------|------|
| 整体 CPL | 使用模拟数据 | 对接真实 API |
| 异常项目数 | 未实现 | 新增计算逻辑 |

### 9.2 API 实现

| 接口 | 当前状态 | 行动 |
|------|---------|------|
| `/dashboard/overview` | 前端模拟 | 创建后端 API |
| `/dashboard/trend` | 前端模拟 | 创建后端 API |
| `/dashboard/top-projects` | 前端模拟 | 创建后端 API |

### 9.3 代码块文档

| 代码块 | 文档状态 |
|--------|---------|
| StatCard | :construction: 待编写 |
| TrendChart | :construction: 待编写 |
| TopList | :construction: 待编写 |

---

## 10. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-22 | 初始版本 |

---

**关联文档**:
- [MASTER.md §6.5](../sot/MASTER.md)
- [代码块索引](../9.code-blocks/README.md)
- [StatCard 代码块](../9.code-blocks/frontend/core/stat-card.md)
