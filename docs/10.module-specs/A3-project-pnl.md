# A3: 项目盈亏看板 (Project P&L)

> **模块类型**: 老板视角模块
> **优先级**: P0
> **源码位置**: `frontend/src/features/finance-profit/`
> **最后更新**: 2025-12-22
> **状态**: :construction: 需对齐 MASTER.md §6.5

---

## 1. 业务目标

### 1.1 核心问题

**"哪个项目赚/亏？谁负责？"**

老板需要在 30 秒内：
1. 看到所有项目的盈亏排名
2. 定位亏损最严重的项目
3. 找到项目负责人进行沟通
4. 识别 CPL 异常的项目

### 1.2 用例清单

| 用例ID | 用例名 | Actor | 触发条件 | 预期结果 |
|--------|--------|-------|---------|---------|
| UC-A3-01 | 查看项目盈亏排名 | ceo, project_owner | 进入页面 | 按利润降序显示项目列表 |
| UC-A3-02 | 识别亏损项目 | ceo | 进入页面 | 亏损项目红色高亮，排在可见区域 |
| UC-A3-03 | 定位异常 CPL | ceo, supervisor | 筛选异常 | 显示 CPL > target × 1.3 的项目 |
| UC-A3-04 | 查看负责人 | ceo | 查看列表 | 每行显示项目负责人姓名 |
| UC-A3-05 | 多维度分析 | ceo | 切换维度 | 按项目/账户/渠道维度查看 |
| UC-A3-06 | 时间范围筛选 | ceo | 选择日期 | 按指定时间范围统计 |

### 1.3 Phase 1 vs Phase 2

| 功能 | Phase 1 | Phase 2 |
|------|---------|---------|
| 盈亏展示 | ✓ 全功能 | - |
| 异常标记 | 高亮显示 | 强制标记 + 通知 |
| 负责人追溯 | 展示 | 关联考核 |
| 数据锁定 | 可修改 | 月度锁定后不可改 |

---

## 2. 数据需求

### 2.1 数据源 (SoT)

| 数据 | SoT 表 | SoT 字段 | 说明 |
|------|--------|---------|------|
| 项目信息 | `project` | `id`, `name`, `owner_id`, `target_cpl` | 项目基础 |
| 项目负责人 | `user` | `id`, `full_name` | 通过 owner_id 关联 |
| 消耗 | `ad_spend_daily` | `spend` | Phase 1 消耗 SoT |
| 进粉 | `daily_report` | `conversions` | Phase 1 进粉 SoT |
| 单价 | `project` | `unit_price` | 用于计算收入 |

### 2.2 字段清单 (MASTER.md §6.5)

**页面 3：项目盈亏看板 - 必须字段**

| 字段 | 来源 | 口径 | 必须 | 当前状态 |
|------|------|------|------|---------|
| 项目名 | project | `name` | :white_check_mark: | :white_check_mark: 已实现 |
| 项目负责人 | project → user | `owner_id → user.full_name` | :white_check_mark: | :x: 缺失 |
| 累计消耗 | ad_spend_daily | `SUM(spend)` | :white_check_mark: | :white_check_mark: 已实现 |
| 累计进粉 | daily_report | `SUM(conversions)` | :white_check_mark: | :white_check_mark: 已实现 |
| CPL | 计算 | `消耗/进粉` (§4.5.1) | :white_check_mark: | :x: 缺失 |
| 预计毛利 | 计算 | §4.5.4 公式 | :white_check_mark: | :white_check_mark: 已实现 |
| 异常标记 | 计算 | `CPL > target × 1.3` | :yellow_circle: | :x: 缺失 |

> :white_check_mark: = 必须字段，:yellow_circle: = 可选字段

### 2.3 计算公式 (MASTER.md §4.5.4)

```python
# Phase 1 盈亏计算公式（观察用）
预计收入 = conversions × unit_price
预计成本 = SUM(ad_spend_daily.spend)
预计毛利 = 预计收入 - 预计成本
毛利率 = 毛利 / 收入 × 100%  # revenue=0 时 margin=0

# CPL 计算 (§4.5.1)
CPL = ad_spend_daily.spend / daily_report.conversions
# 特殊处理:
#   conversions = 0 → 显示 "--"
#   conversions < 5 → 显示 "{CPL} (低量)"

# 异常判定
is_abnormal = CPL > project.target_cpl × 1.3
```

### 2.4 数据刷新策略

| 数据类型 | 刷新频率 | 实现方式 |
|---------|---------|---------|
| 概览卡片 | 页面加载 | React Query |
| 项目列表 | 页面加载 + 筛选变化 | React Query |
| 趋势图 | 时间/粒度变化 | React Query + 依赖 |

---

## 3. UI 规范

### 3.1 页面布局

```
┌─────────────────────────────────────────────────────────────────────────┐
│ [PageHeader: 项目盈亏看板]                            [刷新按钮]         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  【筛选区】                                                              │
│  [日期范围: 开始 - 结束]  [清除筛选]                                    │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  【概览卡片】                                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                   │
│  │ 今日利润  │ │ 本周利润  │ │ 本月利润  │ │ 整体利润率│                   │
│  │ ¥36.8k   │ │ ¥256.7k  │ │ ¥568.0k  │ │  19.8%   │                   │
│  │ +15.2%   │ │ +8.5%    │ │ +12.3%   │ │          │                   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘                   │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  【趋势图】                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │ [ProfitTrendChart]                          粒度: [日|周|月]        ││
│  │ 收入 vs 成本 vs 利润 趋势                                            ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  【TOP 利润项目】                                                        │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                               │
│  │ #1  │ │ #2  │ │ #3  │ │ #4  │ │ #5  │ ← 快速定位盈利最好的项目       │
│  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘                               │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  【项目盈亏明细】 ← MASTER.md §6.5 核心表格                              │
│  维度切换: [项目] [账户] [渠道]                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐
│  │ # │ 项目名   │ 负责人 │ 消耗    │ 进粉  │ CPL   │ 利润    │ 利润率 │ 异常 │
│  ├───┼─────────┼────────┼─────────┼───────┼───────┼─────────┼────────┼──────┤
│  │ 1 │ 项目A   │ 张三   │ ¥285.7k │ 7,258 │ ¥39.4 │ ¥56.8k  │ 19.9%  │      │
│  │ 2 │ 项目B   │ 李四   │ ¥156.3k │ 3,125 │ ¥50.0 │ -¥12.3k │ -7.3%  │ ⚠️   │
│  │ 3 │ 项目C   │ 王五   │ ¥98.5k  │ 2,463 │ ¥40.0 │ ¥24.6k  │ 25.0%  │      │
│  └──────────────────────────────────────────────────────────────────────┘
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 组件清单

| 组件 | 位置 | 职责 | 当前状态 |
|------|------|------|---------|
| `FinanceProfitPage` | 主容器 | 页面整体布局和状态管理 | :white_check_mark: 已实现 |
| `ProfitOverviewCard` | 概览区 | 多时间维度利润概览 | :white_check_mark: 已实现 |
| `ProfitTrendChart` | 趋势区 | 收入/成本/利润趋势图 | :white_check_mark: 已实现 |
| `ProfitTable` | 明细区 | 多维度利润明细表 | :construction: 需增强 |

### 3.3 ProfitTable 增强需求

当前缺失的列（需要添加）：

| 列名 | 字段 | 对齐 | 格式化 | 状态 |
|------|------|------|--------|------|
| 负责人 | `owner_name` | 左 | 文本 | :x: 缺失 |
| CPL | `cpl` | 右 | `¥{value}` + 低量标记 | :x: 缺失 |
| 异常 | `is_abnormal` | 中 | ⚠️ 图标 | :x: 缺失 |

### 3.4 交互规则

| 交互 | 触发 | 行为 |
|------|------|------|
| 切换维度 | 点击维度按钮 | 重新加载对应维度数据 |
| 排序 | 点击表头 | 按该列升序/降序排列 |
| 筛选日期 | 选择日期范围 | 重新计算所有数据 |
| 点击项目行 | 单击 | 跳转到项目详情页 |
| 刷新 | 点击刷新按钮 | 重新加载所有数据 |

### 3.5 颜色规则

| 场景 | 条件 | 颜色 |
|------|------|------|
| 利润正 | profit >= 0 | green-600 |
| 利润负 | profit < 0 | red-600 |
| 利润率优 | margin >= 20% | green (bg-green-100) |
| 利润率中 | 10% <= margin < 20% | yellow (bg-yellow-100) |
| 利润率差 | margin < 10% | red (bg-red-100) |
| CPL 正常 | CPL <= target × 1.3 | 默认 |
| CPL 异常 | CPL > target × 1.3 | red + ⚠️ 图标 |

---

## 4. API 接口

### 4.1 现有接口

| 端点 | 方法 | 说明 | 状态 |
|------|------|------|------|
| `/api/v1/profit/overview` | GET | 利润概览 | :white_check_mark: |
| `/api/v1/profit/by-project` | GET | 按项目维度 | :white_check_mark: |
| `/api/v1/profit/by-account` | GET | 按账户维度 | :white_check_mark: |
| `/api/v1/profit/by-channel` | GET | 按渠道维度 | :white_check_mark: |
| `/api/v1/profit/trend` | GET | 利润趋势 | :white_check_mark: |

### 4.2 需要增强的接口

#### GET `/api/v1/profit/by-project`

**当前返回:**
```json
{
  "items": [
    {
      "project_id": 1,
      "project_name": "项目A",
      "total_conversions": 7258,
      "total_revenue": 362900,
      "total_cost": 285700,
      "total_profit": 77200,
      "profit_margin": 21.27
    }
  ],
  "total_profit": 568000,
  "overall_profit_margin": 19.8
}
```

**需要增强为:**
```json
{
  "items": [
    {
      "project_id": 1,
      "project_name": "项目A",
      "owner_id": 5,
      "owner_name": "张三",           // 新增: 项目负责人
      "total_spend": 285700,          // 重命名: total_cost → total_spend
      "total_conversions": 7258,
      "cpl": 39.36,                    // 新增: CPL
      "cpl_target": 35.00,            // 新增: CPL 目标
      "is_abnormal": true,            // 新增: 异常标记
      "total_revenue": 362900,
      "total_profit": 77200,
      "profit_margin": 21.27
    }
  ],
  "total_profit": 568000,
  "overall_profit_margin": 19.8,
  "abnormal_count": 3                 // 新增: 异常项目数
}
```

### 4.3 后端服务增强

```python
# backend/services/finance/profit_service.py

def get_profit_by_project(
    self,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 20,
) -> Dict:
    """
    按项目维度获取利润数据

    增强: 添加 owner_name, cpl, cpl_target, is_abnormal
    """
    # 1. 联表查询 project + user (owner)
    # 2. 聚合消耗和进粉
    # 3. 计算 CPL = spend / conversions
    # 4. 判断异常 = CPL > target_cpl × 1.3
    # 5. 返回完整数据
```

---

## 5. 权限控制

### 5.1 权限矩阵

| 角色 | 查看全部 | 查看自己项目 | 导出 | 说明 |
|------|---------|------------|------|------|
| ceo | :white_check_mark: | :white_check_mark: | :white_check_mark: | 全部权限 |
| project_owner | :x: | :white_check_mark: | :white_check_mark: | 仅自己负责的项目 |
| finance | :white_check_mark: | - | :white_check_mark: | 财务审计用 |
| supervisor | :x: | :white_check_mark: | :x: | 仅管辖投手的项目 |
| pitcher | :x: | :x: | :x: | 无权限 |

### 5.2 数据过滤规则

```python
# project_owner 只能看自己负责的项目
if user.role == 'project_owner':
    query = query.filter(Project.owner_id == user.id)

# supervisor 只能看自己管辖投手参与的项目
if user.role == 'supervisor':
    query = query.filter(
        Project.id.in_(
            select(DailyReport.project_id)
            .where(DailyReport.pitcher_id.in_(
                select(User.id).where(User.supervisor_id == user.id)
            ))
        )
    )
```

---

## 6. 代码块依赖

### 6.1 前端代码块

| 代码块 | 来源 | 用途 |
|--------|------|------|
| `ProfitOverviewCard` | 本模块 | 概览卡片 |
| `ProfitTrendChart` | 本模块 | 趋势图 |
| `ProfitTable` | 本模块 | 利润明细表 |
| `LoadingSpinner` | shared | 加载状态 |
| `ErrorDisplay` | shared | 错误展示 |

### 6.2 后端代码块

| 代码块 | 来源 | 用途 |
|--------|------|------|
| `ProfitService` | finance | 利润聚合服务 |
| `pagination_helper` | core | 分页 |
| `permission_filter` | core | 权限过滤 |

---

## 7. 测试要点

### 7.1 测试用例清单

- [ ] 页面加载：显示概览卡片和列表
- [ ] 维度切换：切换项目/账户/渠道正常
- [ ] 排序功能：点击表头排序正确
- [ ] 日期筛选：选择日期范围后数据更新
- [ ] 负责人显示：列表显示项目负责人
- [ ] CPL 计算：正确显示 CPL 值
- [ ] 异常标记：CPL 超标项目显示警告
- [ ] 权限过滤：project_owner 只看到自己项目
- [ ] 空数据：无数据时显示友好提示
- [ ] 错误处理：API 失败时显示错误信息

### 7.2 边界条件

| 场景 | 处理方式 |
|------|---------|
| conversions = 0 | CPL 显示 "--" |
| conversions < 5 | CPL 显示 "¥X.XX (低量)" |
| unit_price = null | 收入显示 "待定" |
| profit < 0 | 红色显示，排在亏损区 |
| target_cpl = null | 不显示异常标记 |

---

## 8. 对齐任务清单

### 8.1 前端任务

- [ ] ProfitTable 增加"负责人"列
- [ ] ProfitTable 增加"CPL"列
- [ ] ProfitTable 增加"异常"列
- [ ] CPL 异常项目红色高亮
- [ ] 添加异常筛选开关

### 8.2 后端任务

- [ ] `/profit/by-project` 返回 `owner_name`
- [ ] `/profit/by-project` 返回 `cpl`
- [ ] `/profit/by-project` 返回 `cpl_target`
- [ ] `/profit/by-project` 返回 `is_abnormal`
- [ ] 添加 `abnormal_count` 统计

### 8.3 优先级

| 任务 | 优先级 | 原因 |
|------|--------|------|
| 添加负责人列 | P0 | MASTER.md §6.5 必须字段 |
| 添加 CPL 列 | P0 | MASTER.md §6.5 必须字段 |
| 添加异常标记 | P1 | MASTER.md §6.5 可选字段，但老板强需求 |

---

## 9. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-22 | 初始版本，基于现有实现分析 |

---

## 10. 相关文档

- [MASTER.md §4.5.4 盈亏计算公式](../sot/MASTER.md)
- [MASTER.md §6.5 页面 3 字段集](../sot/MASTER.md)
- [BUSINESS_RULES.md](../sot/BUSINESS_RULES.md)
- [A1-dashboard 模块规格书](./A1-dashboard.md)
- [A2-fund-overview 模块规格书](./A2-fund-overview.md)
