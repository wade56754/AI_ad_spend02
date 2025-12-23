# A3 项目盈亏 - 后端模块规格书

> **版本**: v1.0
> **更新日期**: 2025-12-23
> **SoT 基准**: DATA_SCHEMA.md v5.2, BUSINESS_RULES.md v4.1, MASTER.md v4.4 §4.5.4
> **对应前端**: A3-project-pnl.md

---

## §1 模块概述

### 1.1 业务目标
让老板在 30 秒内掌握"哪个项目赚/亏？谁负责？"，提供项目级盈亏分析和异常识别能力。

### 1.2 涉及角色
| 角色 | 系统角色名 | 本模块权限 |
|------|------------|------------|
| 老板 | ceo | 查看全部项目、导出 |
| 财务 | finance | 查看全部项目、导出 |
| 项目负责人 | project_owner | 查看自己负责的项目 |
| 主管 | supervisor | 查看管辖投手参与的项目 |
| 管理员 | admin | 查看全部项目（只读） |
| 户管 | account_manager | 禁止访问 |
| 投手 | pitcher | 禁止访问 |

### 1.3 模块边界
**本模块负责：**
- 多维度盈亏聚合（按项目/账户/渠道）
- 盈亏趋势分析（日/周/月粒度）
- CPL 计算与异常标记
- 项目负责人关联展示
- TOP 利润项目排名

**本模块不负责：**
- 日报原始数据管理（由日报模块负责）
- 消耗数据导入（由消耗明细模块负责）
- 月度结算锁定（由月度结算模块负责）

### 1.4 SoT 引用清单 (AI 防幻觉)
| SoT 文档 | 版本 | 引用章节 | 用途 |
|---------|------|---------|------|
| DATA_SCHEMA.md | v5.2 | §3.2, §3.3 | projects, daily_reports, ad_spend_daily 表结构 |
| BUSINESS_RULES.md | v4.1 | BR-FIN-* | 盈亏计算规则 |
| ERROR_CODES_SOT.md | v2.1 | PROFIT_*, BIZ_* | 错误码 |
| API_SOT.md | v9.3 | §6 | API 规范 |
| AUTH_SPEC.md | v2.0 | §3 | 权限矩阵 |
| MASTER.md | v4.4 | §4.5.1, §4.5.4, §6.5 | CPL 计算、盈亏公式、页面字段集 |

---

## §2 数据模型

### 2.1 数据源定义
**来源**: DATA_SCHEMA.md v5.2, MASTER.md v4.4 §4.5.4

| 数据 | SoT 表 | SoT 字段 | 计算口径 |
|------|--------|---------|----------|
| 项目信息 | `projects` | `id`, `name`, `owner_id`, `unit_price`, `target_cpl` | 直接读取 |
| 项目负责人 | `users` | `id`, `username`, `full_name` | JOIN projects.owner_id |
| 累计消耗 | `ad_spend_daily` | `spend_amount` | `SUM(spend_amount)` |
| 累计进粉 | `daily_reports` | `conversions` | `SUM(conversions)` |
| 预计收入 | 计算 | - | `SUM(conversions × unit_price)` |
| 预计成本 | `ad_spend_daily` | `spend_amount` | `SUM(spend_amount)` |
| 毛利 | 计算 | - | `预计收入 - 预计成本` |

### 2.2 相关表结构

#### projects (项目表)
```sql
-- 来源: DATA_SCHEMA.md v5.2 §3.2.1
CREATE TABLE projects (
  id              BIGSERIAL PRIMARY KEY,
  name            VARCHAR(100) NOT NULL,
  owner_id        UUID REFERENCES users(id),
  unit_price      DECIMAL(10,2),          -- 单价（元/粉）
  target_cpl      DECIMAL(10,2),          -- 目标 CPL
  status          VARCHAR(20) NOT NULL DEFAULT 'active',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_projects_owner ON projects(owner_id);
CREATE INDEX idx_projects_status ON projects(status);
```

#### daily_reports (日报表)
```sql
-- 来源: DATA_SCHEMA.md v5.2 §3.3.1
CREATE TABLE daily_reports (
  id              BIGSERIAL PRIMARY KEY,
  project_id      BIGINT NOT NULL REFERENCES projects(id),
  ad_account_id   BIGINT NOT NULL REFERENCES ad_accounts(id),
  report_date     DATE NOT NULL,
  conversions     INTEGER NOT NULL DEFAULT 0,
  status          VARCHAR(30) NOT NULL DEFAULT 'raw_submitted',
  submitted_by    UUID REFERENCES users(id),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_daily_reports_project ON daily_reports(project_id);
CREATE INDEX idx_daily_reports_date ON daily_reports(report_date);
```

#### ad_spend_daily (日消耗表)
```sql
-- 来源: DATA_SCHEMA.md v5.2 §3.3.3
CREATE TABLE ad_spend_daily (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ad_account_code VARCHAR(100) NOT NULL,
  spend_date      DATE NOT NULL,
  spend_amount    DECIMAL(15,2) NOT NULL,
  currency        VARCHAR(10) DEFAULT 'CNY',
  imported_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ad_spend_daily_date ON ad_spend_daily(spend_date);
CREATE INDEX idx_ad_spend_daily_account ON ad_spend_daily(ad_account_code);
```

### 2.3 字段说明
**来源**: MASTER.md v4.4 §6.5 页面 3 必须字段

| 字段 | 类型 | 必填 | 说明 | 计算公式 |
|------|------|------|------|----------|
| project_id | BIGINT | ✅ | 项目ID | 直接读取 |
| project_name | VARCHAR | ✅ | 项目名称 | 直接读取 |
| owner_id | UUID | ✅ | 负责人ID | projects.owner_id |
| owner_name | VARCHAR | ✅ | 负责人姓名 | users.full_name |
| total_spend | DECIMAL | ✅ | 累计消耗 | SUM(ad_spend_daily.spend_amount) |
| total_conversions | INTEGER | ✅ | 累计进粉 | SUM(daily_reports.conversions) |
| cpl | DECIMAL | ✅ | 平均 CPL | total_spend / total_conversions |
| cpl_target | DECIMAL | ○ | 目标 CPL | projects.target_cpl |
| is_abnormal | BOOLEAN | ○ | 异常标记 | CPL > target_cpl × 1.3 |
| total_revenue | DECIMAL | ✅ | 预计收入 | SUM(conversions × unit_price) |
| total_profit | DECIMAL | ✅ | 预计毛利 | total_revenue - total_spend |
| profit_margin | DECIMAL | ✅ | 毛利率 | total_profit / total_revenue × 100 |

### 2.4 关联关系
```
profit_by_project (聚合视图)
    ├──→ projects (项目信息 + unit_price + target_cpl)
    │       └──→ users (owner_id → 负责人)
    ├──→ daily_reports (进粉数据)
    │       └──→ ad_accounts → projects
    └──→ ad_spend_daily (消耗数据)
            └──→ ad_accounts → projects
```

---

## §3 API 设计

### 3.1 端点清单
**来源**: A3-project-pnl.md §4, API_SOT.md v9.3

| 方法 | 端点 | 描述 | 权限 |
|------|------|------|------|
| GET | /api/v1/finance/profit/overview | 利润概览（今日/本周/本月） | ceo, finance, admin |
| GET | /api/v1/finance/profit/by-project | 按项目统计利润 | ceo, finance, project_owner, admin |
| GET | /api/v1/finance/profit/by-account | 按账户统计利润 | ceo, finance, admin |
| GET | /api/v1/finance/profit/by-channel | 按渠道统计利润 | ceo, finance, admin |
| GET | /api/v1/finance/profit/trend | 利润趋势（日/周/月） | ceo, finance, admin |
| POST | /api/v1/finance/profit/compare | 多项目利润对比 | ceo, finance, admin |

### 3.2 请求/响应格式

#### GET /api/v1/finance/profit/overview

**响应格式**:
```typescript
interface ProfitOverviewResponse {
  success: true;
  data: {
    // 今日数据
    today_revenue: number;
    today_cost: number;
    today_profit: number;
    today_profit_margin: number;
    // 本周数据
    week_revenue: number;
    week_cost: number;
    week_profit: number;
    week_profit_margin: number;
    // 本月数据
    month_revenue: number;
    month_cost: number;
    month_profit: number;
    month_profit_margin: number;
    // 环比变化
    profit_change_from_yesterday: number | null;
    profit_change_from_last_week: number | null;
    profit_change_from_last_month: number | null;
    // TOP 项目
    top_profit_projects: Array<{
      project_id: number;
      project_name: string;
      profit: number;
    }>;
  };
  message: string;
}
```

#### GET /api/v1/finance/profit/by-project (核心端点)

**请求参数**:
```typescript
interface ProfitByProjectParams {
  start_date?: string;      // 开始日期 (YYYY-MM-DD)
  end_date?: string;        // 结束日期 (YYYY-MM-DD)
  limit?: number;           // 返回数量，默认 20，最大 100
  sort_by?: 'profit' | 'margin' | 'spend' | 'cpl';  // 排序字段
  order?: 'asc' | 'desc';   // 排序方向，默认 desc
  abnormal_only?: boolean;  // 仅显示异常项目
}
```

**响应格式** (增强版):
```typescript
interface ProfitByProjectResponse {
  success: true;
  data: {
    items: Array<{
      project_id: number;
      project_name: string;
      // MASTER.md §6.5 必须字段 (新增)
      owner_id: number;
      owner_name: string;
      cpl: number | null;       // CPL = spend / conversions
      cpl_target: number | null;  // 目标 CPL
      is_abnormal: boolean;     // 异常标记
      // 原有字段
      total_conversions: number;
      avg_unit_price: number;
      total_revenue: number;
      total_spend: number;      // 重命名: total_cost → total_spend
      total_profit: number;
      profit_margin: number;
      report_count: number;
    }>;
    // 汇总
    total_projects: number;
    total_conversions: number;
    total_revenue: number;
    total_cost: number;
    total_profit: number;
    overall_profit_margin: number;
    abnormal_count: number;     // 异常项目数 (新增)
  };
  message: string;
}
```

#### GET /api/v1/finance/profit/trend

**请求参数**:
```typescript
interface ProfitTrendParams {
  granularity: 'daily' | 'weekly' | 'monthly';  // 粒度
  project_id?: number;      // 项目ID过滤
  start_date?: string;
  end_date?: string;
}
```

**响应格式**:
```typescript
interface ProfitTrendResponse {
  success: true;
  data: {
    items: Array<{
      period: string;           // 周期标识 (如 "2024-12-23", "2024-W52", "2024-12")
      period_start: string;
      period_end: string;
      total_conversions: number;
      total_revenue: number;
      total_cost: number;
      total_profit: number;
      profit_margin: number;
      profit_change: number | null;       // 环比变化
      profit_change_rate: number | null;  // 环比变化率%
    }>;
    granularity: string;
    period_count: number;
    avg_profit: number;
    max_profit: number;
    min_profit: number;
  };
  message: string;
}
```

### 3.3 错误码定义
**来源**: ERROR_CODES_SOT.md v2.1

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| AUTH_401 | 401 | 未登录 |
| AUTH_403 | 403 | 无权限访问 |
| BIZ_001 | 400 | 日期参数无效 |
| BIZ_002 | 404 | 项目不存在 |
| PROFIT_001 | 400 | 周期参数无效 |
| PROFIT_003 | 404 | 项目不存在 |
| PROFIT_008 | 400 | 日期范围超出限制 (>366天) |

### 3.4 分页/筛选规范
```yaml
分页:
  页码: 从 1 开始
  默认每页: 20 条
  最大每页: 100 条

筛选:
  日期范围: start_date, end_date (闭区间)
  排序: sort_by + order
  默认排序: profit DESC (利润降序)
  异常过滤: abnormal_only=true 仅返回 is_abnormal=true 的项目

日期范围限制:
  最大跨度: 366 天
  默认范围: 本月
```

---

## §4 权限控制

### 4.1 角色权限矩阵 (7 角色)
**来源**: AUTH_SPEC.md v2.0, MASTER.md v4.4 §2.4

| 操作 | ceo | project_owner | finance | supervisor | pitcher | account_manager | admin |
|------|-----|---------------|---------|------------|---------|-----------------|-------|
| 查看全公司盈亏概览 | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅(只读) |
| 按项目统计(全部) | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅(只读) |
| 按项目统计(自己) | N/A | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| 按账户统计 | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅(只读) |
| 按渠道统计 | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅(只读) |
| 查看利润趋势 | ✅ | ✅(自己项目) | ✅ | ✅(管辖项目) | ❌ | ❌ | ✅(只读) |
| 多项目对比 | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅(只读) |
| 导出报表 | ✅ | ✅(自己项目) | ✅ | ❌ | ❌ | ❌ | ❌ |

### 4.2 数据权限规则
```python
def get_profit_data_scope(user: User, db: Session) -> dict:
    """
    获取用户可访问的盈亏数据范围
    """
    if user.role in ['ceo', 'finance', 'admin']:
        # 可以看所有数据
        return {'scope': 'all', 'project_ids': None}

    if user.role == 'project_owner':
        # 只能看自己负责的项目
        project_ids = db.query(Project.id).filter(
            Project.owner_id == user.id
        ).all()
        return {'scope': 'owned', 'project_ids': [p.id for p in project_ids]}

    if user.role == 'supervisor':
        # 只能看管辖投手参与的项目
        subordinate_ids = db.query(User.id).filter(
            User.supervisor_id == user.id
        ).all()
        project_ids = db.query(DailyReport.project_id).filter(
            DailyReport.submitted_by.in_([s.id for s in subordinate_ids])
        ).distinct().all()
        return {'scope': 'supervised', 'project_ids': [p.project_id for p in project_ids]}

    # pitcher, account_manager: 禁止访问
    return {'scope': 'none', 'project_ids': []}
```

### 4.3 接口级权限
| 端点 | 允许角色 | 数据范围 |
|------|---------|---------|
| /finance/profit/overview | ceo, finance, admin | 全公司 |
| /finance/profit/by-project | ceo, finance, project_owner, supervisor, admin | 按角色过滤 |
| /finance/profit/by-account | ceo, finance, admin | 全公司 |
| /finance/profit/by-channel | ceo, finance, admin | 全公司 |
| /finance/profit/trend | ceo, finance, project_owner, supervisor, admin | 按角色过滤 |
| /finance/profit/compare | ceo, finance, admin | 全公司 |

---

## §5 业务逻辑

### 5.1 无状态机
本模块为聚合服务，不涉及状态机。

### 5.2 计算逻辑
**来源**: MASTER.md v4.4 §4.5.1 (CPL), §4.5.4 (盈亏)

```python
# profit_service.py

from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import func
from backend.models import Project, DailyReport, AdSpendDaily, AdAccount, User

class ProfitService:
    """盈亏聚合服务"""

    CPL_ABNORMAL_THRESHOLD = Decimal('1.3')  # CPL 超标阈值

    def calculate_cpl(self, spend: Decimal, conversions: int) -> Decimal | None:
        """
        计算 CPL (Cost Per Lead)

        公式来源: MASTER.md §4.5.1
        CPL = ad_spend_daily.spend / daily_report.conversions

        特殊处理:
        - conversions = 0 → 返回 None (前端显示 "--")
        - conversions < 5 → 返回 CPL 值 (前端标记 "低量")
        """
        if conversions == 0:
            return None
        cpl = spend / Decimal(conversions)
        return cpl.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def is_cpl_abnormal(self, cpl: Decimal | None, target_cpl: Decimal | None) -> bool:
        """
        判断 CPL 是否异常

        公式来源: MASTER.md §4.5.1
        异常条件: CPL > target_cpl × 1.3
        """
        if cpl is None or target_cpl is None:
            return False
        threshold = target_cpl * self.CPL_ABNORMAL_THRESHOLD
        return cpl > threshold

    def calculate_profit(
        self,
        conversions: int,
        unit_price: Decimal | None,
        spend: Decimal
    ) -> dict:
        """
        计算盈亏

        公式来源: MASTER.md §4.5.4
        预计收入 = conversions × unit_price
        预计成本 = SUM(ad_spend_daily.spend)
        预计毛利 = 预计收入 - 预计成本
        毛利率 = 毛利 / 收入 × 100% (revenue=0 时 margin=0)
        """
        if unit_price is None:
            # 单价未设置，无法计算收入
            return {
                'revenue': None,
                'profit': None,
                'profit_margin': None,
            }

        revenue = Decimal(conversions) * unit_price
        profit = revenue - spend
        profit_margin = (profit / revenue * 100) if revenue > 0 else Decimal('0')

        return {
            'revenue': float(revenue.quantize(Decimal('0.01'))),
            'profit': float(profit.quantize(Decimal('0.01'))),
            'profit_margin': float(profit_margin.quantize(Decimal('0.01'))),
        }

    def get_profit_by_project(
        self,
        start_date: date = None,
        end_date: date = None,
        limit: int = 20,
        project_ids: list[int] = None,  # 权限过滤
        abnormal_only: bool = False,
        sort_by: str = 'profit',
        order: str = 'desc',
    ) -> dict:
        """
        按项目统计利润

        返回: MASTER.md §6.5 页面 3 必须字段
        """
        # 子查询: 项目消耗
        spend_subq = self.db.query(
            AdAccount.project_id,
            func.sum(AdSpendDaily.spend_amount).label('total_spend')
        ).join(
            AdSpendDaily, AdSpendDaily.ad_account_code == AdAccount.account_code
        )
        if start_date:
            spend_subq = spend_subq.filter(AdSpendDaily.spend_date >= start_date)
        if end_date:
            spend_subq = spend_subq.filter(AdSpendDaily.spend_date <= end_date)
        spend_subq = spend_subq.group_by(AdAccount.project_id).subquery()

        # 子查询: 项目进粉
        conv_subq = self.db.query(
            DailyReport.project_id,
            func.sum(DailyReport.conversions).label('total_conversions'),
            func.count(DailyReport.id).label('report_count')
        )
        if start_date:
            conv_subq = conv_subq.filter(DailyReport.report_date >= start_date)
        if end_date:
            conv_subq = conv_subq.filter(DailyReport.report_date <= end_date)
        conv_subq = conv_subq.group_by(DailyReport.project_id).subquery()

        # 主查询
        query = self.db.query(
            Project.id.label('project_id'),
            Project.name.label('project_name'),
            Project.owner_id,
            User.full_name.label('owner_name'),
            Project.unit_price,
            Project.target_cpl,
            func.coalesce(spend_subq.c.total_spend, 0).label('total_spend'),
            func.coalesce(conv_subq.c.total_conversions, 0).label('total_conversions'),
            func.coalesce(conv_subq.c.report_count, 0).label('report_count'),
        ).outerjoin(
            User, Project.owner_id == User.id
        ).outerjoin(
            spend_subq, Project.id == spend_subq.c.project_id
        ).outerjoin(
            conv_subq, Project.id == conv_subq.c.project_id
        ).filter(
            Project.status == 'active'
        )

        # 权限过滤
        if project_ids:
            query = query.filter(Project.id.in_(project_ids))

        # 执行查询
        results = query.all()

        # 计算衍生字段
        items = []
        abnormal_count = 0
        total_revenue = Decimal('0')
        total_cost = Decimal('0')
        total_profit = Decimal('0')
        total_conversions = 0

        for row in results:
            spend = Decimal(str(row.total_spend))
            conversions = row.total_conversions
            unit_price = row.unit_price

            # CPL 计算
            cpl = self.calculate_cpl(spend, conversions)

            # 异常判断
            is_abnormal = self.is_cpl_abnormal(cpl, row.target_cpl)
            if is_abnormal:
                abnormal_count += 1

            # 跳过非异常项目（如果只看异常）
            if abnormal_only and not is_abnormal:
                continue

            # 盈亏计算
            profit_data = self.calculate_profit(conversions, unit_price, spend)

            item = {
                'project_id': row.project_id,
                'project_name': row.project_name,
                'owner_id': str(row.owner_id) if row.owner_id else None,
                'owner_name': row.owner_name or '',
                'total_conversions': conversions,
                'avg_unit_price': float(unit_price) if unit_price else None,
                'total_spend': float(spend),
                'cpl': float(cpl) if cpl else None,
                'cpl_target': float(row.target_cpl) if row.target_cpl else None,
                'is_abnormal': is_abnormal,
                'total_revenue': profit_data['revenue'],
                'total_profit': profit_data['profit'],
                'profit_margin': profit_data['profit_margin'],
                'report_count': row.report_count,
            }
            items.append(item)

            # 累加汇总
            if profit_data['revenue']:
                total_revenue += Decimal(str(profit_data['revenue']))
            total_cost += spend
            if profit_data['profit']:
                total_profit += Decimal(str(profit_data['profit']))
            total_conversions += conversions

        # 排序
        sort_key = {
            'profit': lambda x: x['total_profit'] or 0,
            'margin': lambda x: x['profit_margin'] or 0,
            'spend': lambda x: x['total_spend'],
            'cpl': lambda x: x['cpl'] or float('inf'),
        }.get(sort_by, lambda x: x['total_profit'] or 0)

        items.sort(key=sort_key, reverse=(order == 'desc'))

        # 限制返回数量
        items = items[:limit]

        # 计算整体毛利率
        overall_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else Decimal('0')

        return {
            'items': items,
            'total_projects': len(items),
            'total_conversions': total_conversions,
            'total_revenue': float(total_revenue),
            'total_cost': float(total_cost),
            'total_profit': float(total_profit),
            'overall_profit_margin': float(overall_margin.quantize(Decimal('0.01'))),
            'abnormal_count': abnormal_count,
        }
```

### 5.3 验证规则
```python
from pydantic import BaseModel, Field, validator
from datetime import date

class ProfitByProjectParams(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    limit: int = Field(default=20, ge=1, le=100)
    sort_by: str = Field(default='profit', pattern='^(profit|margin|spend|cpl)$')
    order: str = Field(default='desc', pattern='^(asc|desc)$')
    abnormal_only: bool = False

    @validator('end_date')
    def date_range_valid(cls, v, values):
        if v and values.get('start_date') and v < values['start_date']:
            raise ValueError('end_date 不能早于 start_date')
        return v

    @validator('end_date')
    def date_range_limit(cls, v, values):
        if v and values.get('start_date'):
            if (v - values['start_date']).days > 366:
                raise ValueError('日期范围不能超过 366 天')
        return v
```

### 5.4 业务约束 + Phase 1 规则
```yaml
计算约束:
  - CPL 计算: conversions=0 时返回 null
  - 毛利率计算: revenue=0 时返回 0
  - 单价未设置: 收入/利润/毛利率均返回 null
  - CPL 异常阈值: target_cpl × 1.3

数据一致性:
  - 消耗来自 ad_spend_daily（导入数据）
  - 进粉来自 daily_reports（手工录入）
  - 两者可能存在时间差，属于正常情况

Phase 1 规则 (照亮阶段):
  ❌ 禁止: CPL 超标自动冻结项目
  ❌ 禁止: 亏损项目自动发送告警邮件
  ❌ 禁止: 强制要求负责人填写说明
  ✅ 允许: CPL 异常项目高亮显示 + ⚠️ 图标
  ✅ 允许: 亏损项目红色显示
  ✅ 允许: 记录异常到审计日志
  ✅ 允许: 展示异常项目数量统计

颜色规则 (仅展示用):
  - 利润 >= 0: 绿色
  - 利润 < 0: 红色
  - 毛利率 >= 20%: 绿色背景
  - 10% <= 毛利率 < 20%: 黄色背景
  - 毛利率 < 10%: 红色背景
  - CPL 异常: 红色 + ⚠️ 图标
```

---

## §6 前后端接口契约

### 6.1 字段映射
| 后端字段 (snake_case) | 前端字段 (camelCase) | 说明 |
|----------------------|---------------------|------|
| project_id | projectId | 项目ID |
| project_name | projectName | 项目名称 |
| owner_id | ownerId | 负责人ID |
| owner_name | ownerName | 负责人姓名 |
| total_conversions | totalConversions | 累计进粉 |
| total_spend | totalSpend | 累计消耗 (原 total_cost) |
| total_revenue | totalRevenue | 预计收入 |
| total_profit | totalProfit | 预计毛利 |
| profit_margin | profitMargin | 毛利率 |
| cpl | cpl | 平均 CPL |
| cpl_target | cplTarget | 目标 CPL |
| is_abnormal | isAbnormal | 异常标记 |
| abnormal_count | abnormalCount | 异常项目数 |

### 6.2 枚举值对照
```typescript
// 趋势粒度
type TrendGranularity = 'daily' | 'weekly' | 'monthly';

// 排序字段
type SortBy = 'profit' | 'margin' | 'spend' | 'cpl';

// 前端中文映射
const GRANULARITY_LABELS: Record<TrendGranularity, string> = {
  daily: '按日',
  weekly: '按周',
  monthly: '按月',
};
```

### 6.3 数字/金额格式约定
```yaml
金额格式:
  后端: Decimal 类型，保留 2 位小数
  传输: JSON number 类型
  前端: formatCurrency() 格式化显示

百分比格式:
  后端: Decimal 类型 (如 21.27 表示 21.27%)
  传输: JSON number 类型
  前端: formatPercent() 格式化显示

CPL 格式:
  后端: Decimal 类型，保留 2 位小数
  传输: JSON number | null
  前端: null 显示 "--", 低量标记 "(低量)"

空值处理:
  conversions=0: cpl=null, 前端显示 "--"
  unit_price=null: revenue/profit/margin=null, 前端显示 "待定"
```

---

## §7 测试要点

### 7.1 单元测试
```python
class TestProfitService:
    def test_calculate_cpl_normal(self):
        """正常 CPL 计算"""
        cpl = service.calculate_cpl(Decimal('1000'), 25)
        assert cpl == Decimal('40.00')

    def test_calculate_cpl_zero_conversions(self):
        """进粉为零时 CPL 返回 None"""
        cpl = service.calculate_cpl(Decimal('1000'), 0)
        assert cpl is None

    def test_is_cpl_abnormal_true(self):
        """CPL 超标判定"""
        # target=30, threshold=30*1.3=39, cpl=40 > 39 → 异常
        assert service.is_cpl_abnormal(Decimal('40'), Decimal('30')) == True

    def test_is_cpl_abnormal_false(self):
        """CPL 正常判定"""
        # target=30, threshold=30*1.3=39, cpl=35 < 39 → 正常
        assert service.is_cpl_abnormal(Decimal('35'), Decimal('30')) == False

    def test_calculate_profit(self):
        """盈亏计算"""
        result = service.calculate_profit(
            conversions=100,
            unit_price=Decimal('50'),
            spend=Decimal('4000')
        )
        assert result['revenue'] == 5000.00    # 100 × 50
        assert result['profit'] == 1000.00     # 5000 - 4000
        assert result['profit_margin'] == 20.00  # 1000/5000 × 100

    def test_calculate_profit_no_unit_price(self):
        """单价未设置时返回 None"""
        result = service.calculate_profit(
            conversions=100,
            unit_price=None,
            spend=Decimal('4000')
        )
        assert result['revenue'] is None
        assert result['profit'] is None

    def test_get_by_project_includes_owner(self):
        """按项目统计包含负责人"""
        result = service.get_profit_by_project()
        for item in result['items']:
            assert 'owner_id' in item
            assert 'owner_name' in item

    def test_get_by_project_includes_cpl(self):
        """按项目统计包含 CPL"""
        result = service.get_profit_by_project()
        for item in result['items']:
            assert 'cpl' in item
            assert 'cpl_target' in item
            assert 'is_abnormal' in item
```

### 7.2 集成测试
```python
class TestProfitAPI:
    def test_get_overview_as_ceo(self, ceo_client):
        """CEO 可以获取利润概览"""
        response = ceo_client.get('/api/v1/finance/profit/overview')
        assert response.status_code == 200
        assert 'today_profit' in response.json()['data']
        assert 'top_profit_projects' in response.json()['data']

    def test_get_by_project_as_ceo(self, ceo_client):
        """CEO 可以看所有项目盈亏"""
        response = ceo_client.get('/api/v1/finance/profit/by-project')
        assert response.status_code == 200
        assert 'abnormal_count' in response.json()['data']

    def test_get_by_project_as_project_owner(self, project_owner_client):
        """项目负责人只能看自己项目"""
        response = project_owner_client.get('/api/v1/finance/profit/by-project')
        assert response.status_code == 200
        # 验证只返回自己负责的项目
        for item in response.json()['data']['items']:
            assert item['owner_id'] == str(project_owner_client.user_id)

    def test_get_by_project_as_pitcher_forbidden(self, pitcher_client):
        """投手不能访问盈亏数据"""
        response = pitcher_client.get('/api/v1/finance/profit/by-project')
        assert response.status_code == 403

    def test_abnormal_filter(self, ceo_client):
        """异常项目过滤"""
        response = ceo_client.get('/api/v1/finance/profit/by-project', params={
            'abnormal_only': True
        })
        assert response.status_code == 200
        for item in response.json()['data']['items']:
            assert item['is_abnormal'] == True
```

### 7.3 权限测试矩阵
```python
PERMISSION_TEST_CASES = [
    # (角色, 端点, 预期状态码)
    ('ceo', '/api/v1/finance/profit/overview', 200),
    ('finance', '/api/v1/finance/profit/overview', 200),
    ('admin', '/api/v1/finance/profit/overview', 200),
    ('project_owner', '/api/v1/finance/profit/overview', 403),
    ('supervisor', '/api/v1/finance/profit/overview', 403),
    ('pitcher', '/api/v1/finance/profit/overview', 403),
    ('account_manager', '/api/v1/finance/profit/overview', 403),

    ('ceo', '/api/v1/finance/profit/by-project', 200),
    ('project_owner', '/api/v1/finance/profit/by-project', 200),
    ('supervisor', '/api/v1/finance/profit/by-project', 200),
    ('pitcher', '/api/v1/finance/profit/by-project', 403),

    ('ceo', '/api/v1/finance/profit/by-channel', 200),
    ('project_owner', '/api/v1/finance/profit/by-channel', 403),
]

@pytest.mark.parametrize('role,endpoint,expected_status', PERMISSION_TEST_CASES)
def test_permission_matrix(role, endpoint, expected_status, clients):
    client = clients[role]
    response = client.get(endpoint)
    assert response.status_code == expected_status
```

---

## §8 性能要求

### 8.1 响应时间要求
| API | 目标 | 最大容忍 | 说明 |
|-----|------|----------|------|
| /finance/profit/overview | < 300ms | < 1s | 需聚合多时间维度 |
| /finance/profit/by-project | < 200ms | < 500ms | 带分页 |
| /finance/profit/by-account | < 200ms | < 500ms | 带分页 |
| /finance/profit/by-channel | < 200ms | < 500ms | 带分页 |
| /finance/profit/trend | < 300ms | < 1s | 需按粒度聚合 |

### 8.2 索引要求
必须建立以下索引以保证性能：
```sql
-- daily_reports 表
CREATE INDEX idx_daily_reports_project_date ON daily_reports(project_id, report_date);
CREATE INDEX idx_daily_reports_submitted_by ON daily_reports(submitted_by);

-- ad_spend_daily 表
CREATE INDEX idx_ad_spend_daily_account_date ON ad_spend_daily(ad_account_code, spend_date);

-- projects 表
CREATE INDEX idx_projects_owner ON projects(owner_id);
CREATE INDEX idx_projects_status ON projects(status);
```

### 8.3 缓存策略
```yaml
缓存对象:
  利润概览: 缓存 5 分钟
  按项目统计: 缓存 5 分钟
  利润趋势: 缓存 10 分钟

缓存失效:
  - 日报提交/审核时
  - 消耗数据导入时
  - 项目配置变更时 (unit_price, target_cpl)

实现方式:
  Phase 1: 不启用缓存，直接查询
  Phase 2: 引入 Redis 缓存
```

---

## §9 安全规范

### 9.1 认证授权
- 所有 API 需要 JWT Token
- 每个 API 校验角色权限
- project_owner/supervisor 只能访问自己关联的项目数据

### 9.2 输入验证
- [x] 使用 Pydantic 验证所有输入
- [x] 日期参数验证格式和范围 (最大 366 天)
- [x] limit 参数验证范围 (1-100)
- [x] 使用参数化查询，禁止拼接 SQL

### 9.3 审计日志
必须记录以下操作：
| 操作类型 | 记录内容 |
|----------|----------|
| 查询盈亏概览 | 操作人、时间 |
| 查询项目盈亏 | 操作人、时间、查询参数、返回项目数 |
| 导出报表 | 操作人、时间、导出范围、记录数 |

---

## 附录: AI 代码工厂禁止行为清单

### A.1 禁止行为
| 禁止行为 | 正确做法 | 检查方式 |
|---------|---------|---------|
| 自定义盈亏计算公式 | 使用 MASTER.md §4.5.4 定义 | 代码审查 |
| 自定义 CPL 异常阈值 | 使用 MASTER.md §4.5.1 (1.3 倍) | 代码审查 |
| 自动冻结异常项目 | 只高亮显示 (Phase 1) | 逻辑审查 |
| 跳过权限检查 | 每个接口必须检查角色 | 单元测试 |
| 使用 Float 存金额 | 使用 Decimal | 类型检查 |
| 拼接 SQL 查询 | 使用参数化查询 | 代码扫描 |

### A.2 SoT 追溯验证 Checklist
生成代码后必须验证：
- [ ] CPL 公式符合 MASTER.md §4.5.1
- [ ] 盈亏公式符合 MASTER.md §4.5.4
- [ ] CPL 异常阈值 = target × 1.3
- [ ] 返回字段包含 MASTER.md §6.5 页面 3 必须字段
- [ ] 所有角色来自 MASTER.md v4.4 §2.4 (7 个)
- [ ] 错误码来自 ERROR_CODES_SOT.md
- [ ] 金额字段使用 Decimal 类型

---

## 源码位置

| 层 | 文件路径 |
|----|---------|
| Router | `backend/routers/finance_profit.py` (已实现) |
| Service | `backend/services/finance_service.py` (需增强) |
| Service | `backend/services/finance/profit_service.py` (已实现) |
| Schema | `backend/schemas/finance.py` (需增强) |
| Schema | `backend/schemas/profit.py` (已实现) |
| Test | `backend/tests/services/test_finance_profit_service.py` (待创建) |

---

## 待增强项 (对齐 MASTER.md §6.5)

### 后端增强
- [ ] `/finance/profit/by-project` 返回 `owner_id`, `owner_name`
- [ ] `/finance/profit/by-project` 返回 `cpl`, `cpl_target`, `is_abnormal`
- [ ] `/finance/profit/by-project` 返回 `abnormal_count`
- [ ] 重命名 `total_cost` → `total_spend` (保持一致性)
- [ ] 添加 `abnormal_only` 过滤参数

### 前端增强
- [ ] ProfitTable 增加"负责人"列
- [ ] ProfitTable 增加"CPL"列
- [ ] ProfitTable 增加"异常"列 (⚠️ 图标)
- [ ] CPL 异常项目红色高亮

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-23 | 初始版本，定义盈亏聚合 API + CPL 异常标记 |

---

**关联文档**:
- [A3-project-pnl.md](A3-project-pnl.md) - 前端模块规格书
- [MASTER.md §4.5.1](../1.overview/MASTER.md) - CPL 计算公式
- [MASTER.md §4.5.4](../1.overview/MASTER.md) - 盈亏计算公式
- [MASTER.md §6.5](../1.overview/MASTER.md) - 页面 3 必须字段
- [BUSINESS_RULES.md](../2.sot/BUSINESS_RULES.md) - 业务规则
