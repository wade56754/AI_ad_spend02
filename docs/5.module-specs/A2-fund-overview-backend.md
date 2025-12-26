# A2 资金总览 - 后端模块规格书

> **版本**: v1.0
> **更新日期**: 2025-12-23
> **SoT 基准**: DATA_SCHEMA.md v5.3, LEDGER_SOT.md v1.2, MASTER.md v4.4 §4.5.5
> **对应前端**: A2-fund-overview.md

---

## §1 模块概述

### 1.1 业务目标
让老板在 5 秒内掌握"钱在哪里？能收回多少？"，提供公司资金全貌的聚合视图。

### 1.2 涉及角色
| 角色 | 系统角色名 | 本模块权限 |
|------|------------|------------|
| 老板 | ceo | 查看全公司资金、导出报表 |
| 财务 | finance | 查看全公司资金、导出报表 |
| 项目负责人 | project_owner | 查看自己项目资金 |
| 户管 | account_manager | 仅查看账户余额 |
| 管理员 | admin | 查看全公司资金（只读） |
| 主管 | supervisor | 禁止访问 |
| 投手 | pitcher | 禁止访问 |

### 1.3 模块边界
**本模块负责：**
- 聚合计算 5 个核心资金指标（累计充值、累计消耗、当前余额、应收款、资金占用）
- 按项目/渠道维度展示资金分布
- 应收款明细和回款记录查询
- 资金预警（资金占用率 > 80%）

**本模块不负责：**
- 充值申请/审批流程（由 C1 充值审批模块负责）
- 回款录入（由财务模块负责）
- 账本流水明细（由 ledger 模块负责）

### 1.4 SoT 引用清单 (AI 防幻觉)
| SoT 文档 | 版本 | 引用章节 | 用途 |
|---------|------|---------|------|
| DATA_SCHEMA.md | v5.3 | §3.4.1, §3.4.5 | topup_requests, receivable 表结构 |
| LEDGER_SOT.md | v1.2 | §2.4 | 余额唯一真相源原则 |
| BUSINESS_RULES.md | v4.1 | BR-FIN-* | 资金计算规则 |
| ERROR_CODES_SOT.md | v2.1 | FUND_*, AUTH_* | 错误码 |
| API_SOT.md | v9.3 | §5 | API 规范 |
| AUTH_SPEC.md | v2.0 | §3 | 权限矩阵 |
| MASTER.md | v4.4 | §4.5.5, §6.5 | 资金口径定义、页面字段集 |

---

## §2 数据模型

### 2.1 数据源定义
**来源**: DATA_SCHEMA.md v5.3, MASTER.md v4.4 §4.5.5

| 数据 | SoT 表 | SoT 字段 | 计算口径 |
|------|--------|---------|----------|
| 累计充值 | `topup_requests` | `amount` | `SUM(amount WHERE status='completed')` |
| 累计消耗 | `ad_spend_daily` | `spend` | `SUM(spend)` |
| 当前余额 | 计算 | - | `累计充值 - 累计消耗` |
| 应收总额 | `daily_reports` + `projects` | `conversions`, `unit_price` | `SUM(conversions × unit_price)` |
| 累计回款 | `receivable` | `amount` | `SUM(amount WHERE status='received')` |
| 应收款 | 计算 | - | `应收总额 - 累计回款` |
| 资金占用 | 计算 | - | `累计充值 - 累计回款` |

### 2.2 相关表结构

#### topup_requests (充值申请表)
```sql
-- 来源: DATA_SCHEMA.md v5.3 §3.4.1
CREATE TABLE topup_requests (
  id              BIGSERIAL PRIMARY KEY,
  ad_account_id   BIGINT NOT NULL REFERENCES ad_accounts(id),
  requested_by    UUID NOT NULL REFERENCES users(id),
  amount          DECIMAL(15,2) NOT NULL,
  status          VARCHAR(20) NOT NULL DEFAULT 'draft',
  -- 状态: draft, pending_review, finance_approve, paid, completed, rejected, cancelled
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_topup_requests_status ON topup_requests(status);
CREATE INDEX idx_topup_requests_ad_account_id ON topup_requests(ad_account_id);
```

#### ad_spend_daily (日消耗表)
```sql
-- 来源: DATA_SCHEMA.md v5.3 §3.3.3
CREATE TABLE ad_spend_daily (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ad_account_code VARCHAR(100) NOT NULL,
  spend_date      DATE NOT NULL,
  spend_amount    DECIMAL(15,2) NOT NULL,
  currency        VARCHAR(10) DEFAULT 'CNY',
  imported_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ad_spend_daily_date ON ad_spend_daily(spend_date);
```

#### receivable (回款记录表 - planned)
```sql
-- 来源: DATA_SCHEMA.md v5.3 §3.4.5
CREATE TABLE receivable (
  id              BIGSERIAL PRIMARY KEY,
  project_id      BIGINT NOT NULL REFERENCES projects(id),
  amount          DECIMAL(15,2) NOT NULL,
  expected_date   DATE,
  received_at     TIMESTAMPTZ,
  status          VARCHAR(20) NOT NULL DEFAULT 'pending',
  -- 状态: pending, partial, received
  notes           TEXT,
  created_by      UUID REFERENCES users(id),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_receivable_project ON receivable(project_id);
CREATE INDEX idx_receivable_status ON receivable(status);
```

### 2.3 字段说明
| 字段 | 类型 | 必填 | 说明 | 计算公式 |
|------|------|------|------|----------|
| total_topup | DECIMAL(15,2) | ✅ | 累计充值 | SUM(topup_requests.amount WHERE status='completed') |
| total_spend | DECIMAL(15,2) | ✅ | 累计消耗 | SUM(ad_spend_daily.spend_amount) |
| current_balance | DECIMAL(15,2) | ✅ | 当前余额 | total_topup - total_spend |
| total_receivable | DECIMAL(15,2) | ✅ | 应收款 | 应收总额 - 累计回款 |
| total_received | DECIMAL(15,2) | ✅ | 累计回款 | SUM(receivable.amount WHERE status='received') |
| fund_occupied | DECIMAL(15,2) | ✅ | 资金占用 | total_topup - total_received |
| occupy_rate | DECIMAL(5,2) | ✅ | 资金占用率 | fund_occupied / total_topup × 100% |

### 2.4 关联关系
```
fund_overview (聚合视图)
    ├──→ topup_requests (累计充值)
    │       └──→ ad_accounts → projects
    ├──→ ad_spend_daily (累计消耗)
    │       └──→ ad_accounts → projects
    ├──→ daily_reports (应收计算)
    │       └──→ projects (unit_price)
    └──→ receivable (回款记录)
            └──→ projects
```

---

## §3 API 设计

### 3.1 端点清单
**来源**: A2-fund-overview.md §5.1, API_SOT.md v9.3

| 方法 | 端点 | 描述 | 权限 |
|------|------|------|------|
| GET | /api/v1/fund/overview | 获取资金概览（5个核心指标） | ceo, finance, admin |
| GET | /api/v1/fund/distribution/projects | 按项目查看资金分布 | ceo, finance, project_owner |
| GET | /api/v1/fund/distribution/channels | 按渠道查看资金分布 | ceo, finance |
| GET | /api/v1/fund/receivables | 获取应收款明细 | ceo, finance |
| GET | /api/v1/fund/payments | 获取回款记录 | ceo, finance |

### 3.2 请求/响应格式

#### GET /api/v1/fund/overview

**请求参数**:
```typescript
interface FundOverviewParams {
  date_from?: string;     // 开始日期 (YYYY-MM-DD)，可选
  date_to?: string;       // 结束日期 (YYYY-MM-DD)，可选
}
```

**响应格式**:
```typescript
interface FundOverviewResponse {
  success: true;
  data: {
    // 核心指标 (MASTER.md §6.5 必须字段)
    total_topup: number;           // 累计充值
    total_spend: number;           // 累计消耗
    current_balance: number;       // 当前余额
    total_receivable: number;      // 应收款
    total_received: number;        // 累计回款
    fund_occupied: number;         // 资金占用

    // 变化率 (环比)
    topup_change: number | null;   // 充值环比变化%
    spend_change: number | null;   // 消耗环比变化%
    balance_change: number | null; // 余额环比变化%

    // 衍生指标
    occupy_rate: number;           // 资金占用率%
    pending_receivable_count: number; // 待收款笔数

    // 预警
    has_warning: boolean;          // 是否有预警 (occupy_rate > 80)
    warning_message: string | null; // 预警信息
  };
  message: string;
}
```

#### GET /api/v1/fund/distribution/projects

**请求参数**:
```typescript
interface FundDistributionParams {
  page?: number;          // 页码，默认 1
  page_size?: number;     // 每页数量，默认 20，最大 100
  sort_by?: 'topup' | 'spend' | 'balance'; // 排序字段
  order?: 'asc' | 'desc'; // 排序方向，默认 desc
  project_id?: number;    // 项目ID过滤（project_owner 使用）
}
```

**响应格式**:
```typescript
interface FundByProjectResponse {
  success: true;
  data: {
    items: Array<{
      project_id: number;
      project_name: string;
      owner_id: number;
      owner_name: string;
      total_topup: number;    // 项目累计充值
      total_spend: number;    // 项目累计消耗
      balance: number;        // 项目余额
      receivable: number;     // 项目应收
      received: number;       // 项目已回款
    }>;
    pagination: {
      page: number;
      page_size: number;
      total: number;
      total_pages: number;
    };
  };
  message: string;
}
```

#### GET /api/v1/fund/distribution/channels

**请求参数**:
```typescript
interface FundByChannelParams {
  page?: number;
  page_size?: number;
  sort_by?: 'topup' | 'spend' | 'balance';
  order?: 'asc' | 'desc';
}
```

**响应格式**:
```typescript
interface FundByChannelResponse {
  success: true;
  data: {
    items: Array<{
      channel_id: number;
      channel_name: string;
      total_accounts: number;  // 账户数
      total_topup: number;
      total_spend: number;
      balance: number;
    }>;
    pagination: {
      page: number;
      page_size: number;
      total: number;
      total_pages: number;
    };
  };
  message: string;
}
```

#### GET /api/v1/fund/receivables

**请求参数**:
```typescript
interface ReceivablesParams {
  page?: number;
  page_size?: number;
  status?: 'pending' | 'partial' | 'received';
  project_id?: number;
}
```

**响应格式**:
```typescript
interface ReceivablesResponse {
  success: true;
  data: {
    items: Array<{
      id: number;
      project_id: number;
      project_name: string;
      amount: number;
      days_pending: number;    // 待收天数
      status: 'pending' | 'partial' | 'received';
      expected_date: string | null;
      created_at: string;
    }>;
    total_amount: number;      // 应收总额
    pending_count: number;     // 待收笔数
  };
  message: string;
}
```

#### GET /api/v1/fund/payments

**请求参数**:
```typescript
interface PaymentsParams {
  page?: number;
  page_size?: number;
  date_from?: string;
  date_to?: string;
  project_id?: number;
}
```

**响应格式**:
```typescript
interface PaymentsResponse {
  success: true;
  data: {
    items: Array<{
      id: number;
      project_id: number;
      project_name: string;
      amount: number;
      received_at: string;
      status: 'received' | 'processing';
    }>;
    total_amount: number;      // 回款总额
  };
  message: string;
}
```

### 3.3 错误码定义
**来源**: ERROR_CODES_SOT.md v2.1

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| AUTH_401 | 401 | 未登录 |
| AUTH_500 | 403 | 无权限访问资金数据 |
| BIZ_001 | 400 | 日期范围无效 |
| SYS_001 | 500 | 资金聚合计算失败 |
| VALIDATION_001 | 400 | 请求参数验证失败 |

### 3.4 分页/筛选规范
```yaml
分页:
  页码: 从 1 开始
  默认每页: 20 条
  最大每页: 100 条

筛选:
  日期范围: date_from, date_to (闭区间)
  排序: sort_by + order
  默认排序: balance DESC (余额降序)
```

---

## §4 权限控制

### 4.1 角色权限矩阵 (7 角色)
**来源**: AUTH_SPEC.md v2.0, MASTER.md v4.4 §2.4

| 操作 | ceo | project_owner | finance | supervisor | pitcher | account_manager | admin |
|------|-----|---------------|---------|------------|---------|-----------------|-------|
| 查看全公司资金概览 | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅(只读) |
| 查看全部项目资金分布 | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅(只读) |
| 查看自己项目资金 | N/A | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 查看渠道资金分布 | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅(只读) |
| 查看应收款明细 | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅(只读) |
| 查看回款记录 | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅(只读) |
| 导出资金报表 | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |

### 4.2 数据权限规则
```python
def get_fund_data_scope(user: User) -> dict:
    """
    获取用户可访问的资金数据范围
    """
    if user.role in ['ceo', 'finance', 'admin']:
        # 可以看所有数据
        return {'scope': 'all', 'project_ids': None}

    if user.role == 'project_owner':
        # 只能看自己负责的项目
        project_ids = get_user_owned_projects(user.id)
        return {'scope': 'owned', 'project_ids': project_ids}

    if user.role == 'account_manager':
        # 只能看账户余额，不能看其他资金数据
        return {'scope': 'account_balance_only', 'project_ids': None}

    # supervisor, pitcher: 禁止访问
    return {'scope': 'none', 'project_ids': []}
```

### 4.3 接口级权限
| 端点 | 允许角色 | 数据范围 |
|------|---------|---------|
| /fund/overview | ceo, finance, admin | 全公司 |
| /fund/distribution/projects | ceo, finance, project_owner, admin | ceo/finance/admin: 全部; project_owner: 自己项目 |
| /fund/distribution/channels | ceo, finance, admin | 全公司 |
| /fund/receivables | ceo, finance, admin | 全公司 |
| /fund/payments | ceo, finance, admin | 全公司 |

---

## §5 业务逻辑

### 5.1 无状态机
本模块为聚合服务，不涉及状态机。

### 5.2 计算逻辑
**来源**: MASTER.md v4.4 §4.5.5

```python
# fund_service.py

from decimal import Decimal
from sqlalchemy import func
from backend.models import TopupRequest, AdSpendDaily, DailyReport, Project, Receivable

class FundService:
    """资金聚合服务"""

    def calculate_fund_overview(
        self,
        date_from: date = None,
        date_to: date = None,
        project_ids: list[int] = None  # 权限过滤
    ) -> dict:
        """
        计算资金概览

        公式来源: MASTER.md §4.5.5
        """
        # 累计充值 = SUM(topup_requests.amount WHERE status='completed')
        topup_query = self.db.query(
            func.coalesce(func.sum(TopupRequest.amount), Decimal('0'))
        ).filter(
            TopupRequest.status == 'completed'
        )

        # 累计消耗 = SUM(ad_spend_daily.spend_amount)
        spend_query = self.db.query(
            func.coalesce(func.sum(AdSpendDaily.spend_amount), Decimal('0'))
        )

        # 应收总额 = SUM(daily_reports.conversions × projects.unit_price)
        gross_receivable_query = self.db.query(
            func.coalesce(
                func.sum(DailyReport.conversions * Project.unit_price),
                Decimal('0')
            )
        ).join(Project, DailyReport.project_id == Project.id)

        # 累计回款 = SUM(receivable.amount WHERE status='received')
        received_query = self.db.query(
            func.coalesce(func.sum(Receivable.amount), Decimal('0'))
        ).filter(
            Receivable.status == 'received'
        )

        # 待收款笔数
        pending_count_query = self.db.query(
            func.count(Receivable.id)
        ).filter(
            Receivable.status.in_(['pending', 'partial'])
        )

        # 应用日期过滤
        if date_from:
            topup_query = topup_query.filter(TopupRequest.created_at >= date_from)
            spend_query = spend_query.filter(AdSpendDaily.spend_date >= date_from)

        if date_to:
            topup_query = topup_query.filter(TopupRequest.created_at <= date_to)
            spend_query = spend_query.filter(AdSpendDaily.spend_date <= date_to)

        # 应用项目权限过滤
        if project_ids:
            # TODO: 通过 ad_accounts 关联过滤
            pass

        # 执行查询
        total_topup = topup_query.scalar() or Decimal('0')
        total_spend = spend_query.scalar() or Decimal('0')
        gross_receivable = gross_receivable_query.scalar() or Decimal('0')
        total_received = received_query.scalar() or Decimal('0')
        pending_count = pending_count_query.scalar() or 0

        # 计算衍生指标
        current_balance = total_topup - total_spend
        total_receivable = gross_receivable - total_received
        fund_occupied = total_topup - total_received
        occupy_rate = (fund_occupied / total_topup * 100) if total_topup > 0 else Decimal('0')

        # 预警判断
        has_warning = occupy_rate > 80
        warning_message = "资金占用率超过 80%，请关注回款进度" if has_warning else None

        return {
            'total_topup': float(total_topup),
            'total_spend': float(total_spend),
            'current_balance': float(current_balance),
            'total_receivable': float(total_receivable),
            'total_received': float(total_received),
            'fund_occupied': float(fund_occupied),
            'occupy_rate': float(occupy_rate),
            'pending_receivable_count': pending_count,
            'has_warning': has_warning,
            'warning_message': warning_message,
            # 环比变化率 (需要前期数据计算)
            'topup_change': None,
            'spend_change': None,
            'balance_change': None,
        }

    def get_fund_by_project(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = 'balance',
        order: str = 'desc',
        project_ids: list[int] = None
    ) -> dict:
        """按项目查看资金分布"""
        # 子查询: 项目充值
        topup_subq = self.db.query(
            AdAccount.project_id,
            func.sum(TopupRequest.amount).label('total_topup')
        ).join(
            TopupRequest, TopupRequest.ad_account_id == AdAccount.id
        ).filter(
            TopupRequest.status == 'completed'
        ).group_by(AdAccount.project_id).subquery()

        # 子查询: 项目消耗
        spend_subq = self.db.query(
            AdAccount.project_id,
            func.sum(AdSpendDaily.spend_amount).label('total_spend')
        ).join(
            AdSpendDaily, AdSpendDaily.ad_account_code == AdAccount.account_code
        ).group_by(AdAccount.project_id).subquery()

        # 主查询
        query = self.db.query(
            Project.id.label('project_id'),
            Project.name.label('project_name'),
            User.id.label('owner_id'),
            User.username.label('owner_name'),
            func.coalesce(topup_subq.c.total_topup, 0).label('total_topup'),
            func.coalesce(spend_subq.c.total_spend, 0).label('total_spend'),
            (func.coalesce(topup_subq.c.total_topup, 0) -
             func.coalesce(spend_subq.c.total_spend, 0)).label('balance')
        ).outerjoin(
            topup_subq, Project.id == topup_subq.c.project_id
        ).outerjoin(
            spend_subq, Project.id == spend_subq.c.project_id
        ).outerjoin(
            User, Project.owner_id == User.id
        )

        # 权限过滤
        if project_ids:
            query = query.filter(Project.id.in_(project_ids))

        # 排序
        sort_column = {
            'topup': 'total_topup',
            'spend': 'total_spend',
            'balance': 'balance'
        }.get(sort_by, 'balance')

        if order == 'desc':
            query = query.order_by(text(f'{sort_column} DESC NULLS LAST'))
        else:
            query = query.order_by(text(f'{sort_column} ASC NULLS FIRST'))

        # 分页
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            'items': [dict(row._mapping) for row in items],
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': (total + page_size - 1) // page_size
            }
        }
```

### 5.3 验证规则
```python
from pydantic import BaseModel, Field, validator
from datetime import date

class FundOverviewParams(BaseModel):
    date_from: date | None = None
    date_to: date | None = None

    @validator('date_to')
    def date_range_valid(cls, v, values):
        if v and values.get('date_from') and v < values['date_from']:
            raise ValueError('date_to 不能早于 date_from')
        return v

class FundDistributionParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str = Field(default='balance', pattern='^(topup|spend|balance)$')
    order: str = Field(default='desc', pattern='^(asc|desc)$')
```

### 5.4 业务约束 + Phase 1 规则
```yaml
计算约束:
  - 累计充值只计算 status='completed' 的充值申请
  - 累计消耗来自 ad_spend_daily 导入数据，不依赖日报
  - 应收计算依赖项目 unit_price，unit_price 为空的项目不计入
  - 资金占用率计算时，如分母为 0，返回 0%

数据一致性:
  - 余额计算使用 topup_requests + ad_spend_daily 聚合
  - 不直接依赖 projects.balance 字段（聚合服务独立计算）
  - 历史余额查询通过日期范围过滤实现

Phase 1 规则 (照亮阶段):
  ❌ 禁止: 资金不足自动阻断充值
  ❌ 禁止: 资金占用率超标自动冻结项目
  ✅ 允许: 资金占用率 > 80% 显示警告横幅
  ✅ 允许: 余额为负高亮显示
  ✅ 允许: 记录资金异常到审计日志

预警规则:
  - 资金占用率 > 80%: 显示橙色预警
  - 余额为负: 红色高亮
  - 应收款逾期 > 30 天: 标记"逾期"
```

---

## §6 前后端接口契约

### 6.1 字段映射
| 后端字段 (snake_case) | 前端字段 (camelCase) | 说明 |
|----------------------|---------------------|------|
| total_topup | totalTopup | 累计充值 |
| total_spend | totalSpend | 累计消耗 |
| current_balance | currentBalance | 当前余额 |
| total_receivable | totalReceivable | 应收款 |
| total_received | totalReceived | 累计回款 |
| fund_occupied | fundOccupied | 资金占用 |
| occupy_rate | occupyRate | 资金占用率 |
| pending_receivable_count | pendingReceivableCount | 待收款笔数 |
| project_id | projectId | 项目ID |
| owner_name | ownerName | 负责人姓名 |

### 6.2 枚举值对照
```typescript
// 应收款状态
type ReceivableStatus = 'pending' | 'partial' | 'received';

// 前端中文映射
const RECEIVABLE_STATUS_LABELS: Record<ReceivableStatus, string> = {
  pending: '待收',
  partial: '部分收回',
  received: '已收',
};

// 排序字段
type SortBy = 'topup' | 'spend' | 'balance';
```

### 6.3 数字/金额格式约定
```yaml
金额格式:
  后端: Decimal 类型，保留 2 位小数
  传输: JSON number 类型
  前端: formatCurrency() 格式化显示 (如 ¥856万)

百分比格式:
  后端: Decimal 类型 (如 67.3 表示 67.3%)
  传输: JSON number 类型
  前端: formatPercent() 格式化显示

空值处理:
  无数据: 返回 0，不返回 null
  环比无法计算: 返回 null
```

---

## §7 测试要点

### 7.1 单元测试
```python
class TestFundService:
    def test_calculate_overview_no_data(self):
        """无数据时返回全零"""
        result = fund_service.calculate_fund_overview()
        assert result['total_topup'] == 0
        assert result['total_spend'] == 0
        assert result['current_balance'] == 0
        assert result['occupy_rate'] == 0

    def test_calculate_overview_with_data(self):
        """有数据时计算正确"""
        # Setup: 创建测试数据
        create_topup(amount=100000, status='completed')
        create_spend(amount=80000)
        create_receivable(amount=20000, status='received')

        result = fund_service.calculate_fund_overview()

        assert result['total_topup'] == 100000
        assert result['total_spend'] == 80000
        assert result['current_balance'] == 20000  # 100000 - 80000
        assert result['fund_occupied'] == 80000    # 100000 - 20000

    def test_occupy_rate_warning(self):
        """资金占用率 > 80% 触发预警"""
        create_topup(amount=100000, status='completed')
        create_receivable(amount=10000, status='received')  # 占用率 90%

        result = fund_service.calculate_fund_overview()

        assert result['occupy_rate'] == 90
        assert result['has_warning'] == True
        assert '80%' in result['warning_message']

    def test_only_completed_topup_counted(self):
        """只计算 completed 状态的充值"""
        create_topup(amount=100000, status='completed')
        create_topup(amount=50000, status='pending_review')
        create_topup(amount=30000, status='rejected')

        result = fund_service.calculate_fund_overview()

        assert result['total_topup'] == 100000  # 只计算 completed
```

### 7.2 集成测试
```python
class TestFundAPI:
    def test_get_overview_as_ceo(self, ceo_client):
        """CEO 可以获取全公司资金概览"""
        response = ceo_client.get('/api/v1/fund/overview')

        assert response.status_code == 200
        assert response.json()['success'] == True
        assert 'total_topup' in response.json()['data']

    def test_get_overview_as_pitcher_forbidden(self, pitcher_client):
        """投手不能访问资金概览"""
        response = pitcher_client.get('/api/v1/fund/overview')

        assert response.status_code == 403
        assert response.json()['error']['code'] == 'AUTH_500'

    def test_get_distribution_project_owner_filter(self, project_owner_client):
        """项目负责人只能看自己项目"""
        response = project_owner_client.get('/api/v1/fund/distribution/projects')

        assert response.status_code == 200
        # 验证只返回自己负责的项目
        for item in response.json()['data']['items']:
            assert item['owner_id'] == project_owner_client.user_id

    def test_date_range_filter(self, ceo_client):
        """日期范围过滤生效"""
        response = ceo_client.get('/api/v1/fund/overview', params={
            'date_from': '2024-01-01',
            'date_to': '2024-12-31'
        })

        assert response.status_code == 200
```

### 7.3 权限测试矩阵
```python
PERMISSION_TEST_CASES = [
    # (角色, 端点, 预期状态码)
    ('ceo', '/api/v1/fund/overview', 200),
    ('finance', '/api/v1/fund/overview', 200),
    ('admin', '/api/v1/fund/overview', 200),
    ('project_owner', '/api/v1/fund/overview', 403),
    ('supervisor', '/api/v1/fund/overview', 403),
    ('pitcher', '/api/v1/fund/overview', 403),
    ('account_manager', '/api/v1/fund/overview', 403),

    ('ceo', '/api/v1/fund/distribution/projects', 200),
    ('project_owner', '/api/v1/fund/distribution/projects', 200),  # 只能看自己的
    ('pitcher', '/api/v1/fund/distribution/projects', 403),

    ('ceo', '/api/v1/fund/distribution/channels', 200),
    ('project_owner', '/api/v1/fund/distribution/channels', 403),

    ('ceo', '/api/v1/fund/receivables', 200),
    ('pitcher', '/api/v1/fund/receivables', 403),
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
| /fund/overview | < 300ms | < 1s | 需聚合多表数据 |
| /fund/distribution/projects | < 200ms | < 500ms | 带分页 |
| /fund/distribution/channels | < 200ms | < 500ms | 带分页 |
| /fund/receivables | < 150ms | < 300ms | 简单查询 |
| /fund/payments | < 150ms | < 300ms | 简单查询 |

### 8.2 索引要求
必须建立以下索引以保证性能：
```sql
-- topup_requests 表
CREATE INDEX idx_topup_requests_status ON topup_requests(status);
CREATE INDEX idx_topup_requests_created_at ON topup_requests(created_at);

-- ad_spend_daily 表
CREATE INDEX idx_ad_spend_daily_date ON ad_spend_daily(spend_date);
CREATE INDEX idx_ad_spend_daily_account ON ad_spend_daily(ad_account_code);

-- receivable 表
CREATE INDEX idx_receivable_status ON receivable(status);
CREATE INDEX idx_receivable_project ON receivable(project_id);
CREATE INDEX idx_receivable_received_at ON receivable(received_at);
```

### 8.3 缓存策略
```yaml
缓存对象:
  资金概览: 缓存 5 分钟（数据不实时更新）
  项目资金分布: 缓存 5 分钟
  渠道资金分布: 缓存 5 分钟

缓存失效:
  - 新充值完成时
  - 新消耗数据导入时
  - 回款状态变更时

实现方式:
  Phase 1: 不启用缓存，直接查询
  Phase 2: 引入 Redis 缓存
```

---

## §9 安全规范

### 9.1 认证授权
- 所有 API 需要 JWT Token
- 每个 API 校验角色权限
- project_owner 只能访问自己负责的项目数据

### 9.2 输入验证
- [x] 使用 Pydantic 验证所有输入
- [x] 日期参数验证格式和范围
- [x] page/page_size 参数验证范围
- [x] 使用参数化查询，禁止拼接 SQL

### 9.3 审计日志
必须记录以下操作：
| 操作类型 | 记录内容 |
|----------|----------|
| 查询资金概览 | 操作人、时间、查询参数 |
| 导出资金报表 | 操作人、时间、导出范围、记录数 |

---

## 附录: AI 代码工厂禁止行为清单

### A.1 禁止行为
| 禁止行为 | 正确做法 | 检查方式 |
|---------|---------|---------|
| 自定义资金计算公式 | 使用 MASTER.md §4.5.5 定义 | 代码审查 |
| 直接修改 projects.balance | 只读聚合，不修改 | 代码审查 |
| 跳过权限检查 | 每个接口必须检查角色 | 单元测试 |
| 自动阻断/冻结 | 只记录+预警 (Phase 1) | 逻辑审查 |
| 使用 Float 存金额 | 使用 Decimal | 类型检查 |
| 拼接 SQL 查询 | 使用参数化查询 | 代码扫描 |

### A.2 SoT 追溯验证 Checklist
生成代码后必须验证：
- [ ] 累计充值公式符合 MASTER.md §4.5.5
- [ ] 累计消耗公式符合 MASTER.md §4.5.5
- [ ] 应收款公式符合 MASTER.md §4.5.5
- [ ] 资金占用率公式正确
- [ ] 所有角色来自 MASTER.md v4.4 §2.4 (7 个)
- [ ] 错误码来自 ERROR_CODES_SOT.md
- [ ] 金额字段使用 Decimal 类型

---

## 源码位置

| 层 | 文件路径 |
|----|---------|
| Router | `backend/routers/fund.py` (待创建) |
| Service | `backend/services/fund_service.py` (待创建) |
| Schema | `backend/schemas/fund.py` (待创建) |
| Test | `backend/tests/services/test_fund_service.py` (待创建) |
| 复用 | `backend/routers/ledger.py` (余额查询参考) |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-23 | 初始版本，定义资金聚合 API + 权限过滤 |

---

**关联文档**:
- [A2-fund-overview.md](A2-fund-overview.md) - 前端模块规格书
- [MASTER.md §4.5.5](../sot/MASTER.md) - 资金口径定义
- [LEDGER_SOT.md](../sot/LEDGER_SOT.md) - 账本规范
- [DATA_SCHEMA.md §3.4](../sot/DATA_SCHEMA.md) - 表结构定义
