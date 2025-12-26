# E1 月度结算 - 后端模块规格书

> **版本**: v1.1
> **更新日期**: 2025-12-24
> **SoT 基准**: DATA_SCHEMA.md v5.3, STATE_MACHINE.md v2.7, LEDGER_SOT.md v1.2
> **参考指南**: docs/2.dev-guides/BACKEND_MODULE_SPEC_GUIDE.md
> **前端规格书**: docs/5.module-specs/D1-monthly-settlement.md

---

## 目录

- [§1 模块概述](#1-模块概述)
- [§2 数据模型](#2-数据模型)
- [§3 API 设计](#3-api-设计)
- [§4 权限控制](#4-权限控制)
- [§5 业务逻辑](#5-业务逻辑)
- [§6 前后端接口契约](#6-前后端接口契约)
- [§7 测试要点](#7-测试要点)
- [§8 性能要求](#8-性能要求)
- [§9 安全规范](#9-安全规范)

---

## §1 模块概述

### 1.1 业务目标

本模块实现项目月度盈亏结算与锁定，解答核心管理问题：**"这个月赚了还是亏了？"**。通过汇总消耗、进粉数据，计算项目月度盈亏，并支持财务确认与锁定。

**与通用结算模块的区别**:

| 维度 | 通用结算 (Settlement) | 月度结算 (MonthlySettlement) |
|------|----------------------|------------------------------|
| 用途 | 供应商付款、客户账单、退款 | 项目月度盈亏核算 |
| 状态机 | 7 状态 (draft → completed) | 4 状态 (pending → locked) |
| 粒度 | 单据级 | 项目+月份级 |
| 触发方式 | 手工创建 | 自动汇总生成 |

### 1.2 涉及角色

| 角色 | 系统角色名 | 本模块权限 |
|------|------------|------------|
| 老板 | ceo | 查看所有结算、锁定结算 |
| 财务 | finance | **核心角色**: 生成、确认、锁定、导出 |
| 项目负责人 | project_owner | 查看自己项目结算 |
| 管理员 | admin | **超级权限**: 所有操作含解锁 |

### 1.3 模块边界

**本模块负责：**
- 月度结算数据汇总生成
- 结算状态流转 (4 状态)
- 结算确认与锁定
- 月度盈亏计算
- 结算报表导出

**本模块不负责：**
- 日报数据管理（由 B1/B2 模块负责）
- 消耗数据导入（由 C3 模块负责）
- 供应商付款结算（由通用结算模块负责）

### 1.4 SoT 引用清单 (AI 防幻觉)

| SoT 文档 | 版本 | 引用章节 | 用途 |
|---------|------|---------|------|
| DATA_SCHEMA.md | v5.3 | §3.7.1 monthly_settlements | 表结构定义 |
| STATE_MACHINE.md | v2.7 | §13.1 月度结算状态机 | 4 状态流转规则 |
| LEDGER_SOT.md | v1.2 | §4 结算分录 | 锁定时账本规则 |
| BUSINESS_RULES.md | v4.1 | BR-SET-* | 结算业务规则 |
| ERROR_CODES_SOT.md | v2.1 | BIZ_600-699 | 结算相关错误码 |
| API_SOT.md | v9.3 | §8 Settlements | API 端点规范 |
| AUTH_SPEC.md | v2.0 | §3 权限矩阵 | 角色权限 |
| MASTER.md | v4.4 | §4.5.4 | 盈亏计算公式 |

### 1.5 Phase 约束

**来源**: D1-monthly-settlement.md §1.4

| Phase | 约束 | 说明 |
|-------|------|------|
| Phase 1 (照亮) | 可修改 | 结算数据可修改，用于观察 |
| Phase 2 (问责) | 锁定后不可修改 | 启用结算锁定机制 |

**Phase 1 配置**:
```python
PHASE2_SETTLEMENT_LOCK = False  # 锁定机制软性
```

---

## §2 数据模型

### 2.1 表结构定义

**来源**: DATA_SCHEMA.md v5.3 §4.6 (待新增)

```sql
CREATE TABLE monthly_settlements (
  -- 主键
  id              BIGSERIAL PRIMARY KEY,

  -- 业务键
  settlement_month VARCHAR(7) NOT NULL,           -- 结算月份 YYYY-MM
  project_id      BIGINT NOT NULL REFERENCES projects(id),

  -- 聚合数据
  total_spend     DECIMAL(15,2) NOT NULL DEFAULT 0,   -- 总消耗
  total_conversions INTEGER NOT NULL DEFAULT 0,       -- 总进粉
  avg_cpl         DECIMAL(10,4),                      -- 平均 CPL
  unit_price      DECIMAL(10,4),                      -- 项目单价 (快照)
  revenue         DECIMAL(15,2),                      -- 预计收入
  gross_profit    DECIMAL(15,2),                      -- 毛利
  profit_rate     DECIMAL(8,4),                       -- 毛利率

  -- 状态
  status          VARCHAR(20) NOT NULL DEFAULT 'pending',

  -- 确认信息
  confirmed_by    UUID REFERENCES users(id),
  confirmed_at    TIMESTAMPTZ,

  -- 锁定信息
  is_locked       BOOLEAN NOT NULL DEFAULT FALSE,
  locked_by       UUID REFERENCES users(id),
  locked_at       TIMESTAMPTZ,

  -- 备注
  notes           TEXT,

  -- 审计字段
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by      UUID REFERENCES users(id),

  -- 约束
  CONSTRAINT uk_monthly_settlement UNIQUE (settlement_month, project_id),
  CONSTRAINT chk_monthly_settlement_status
    CHECK (status IN ('pending', 'draft', 'confirmed', 'locked')),
  CONSTRAINT chk_monthly_settlement_month
    CHECK (settlement_month ~ '^\d{4}-(0[1-9]|1[0-2])$')
);

-- 索引
CREATE INDEX idx_monthly_settlements_month ON monthly_settlements(settlement_month);
CREATE INDEX idx_monthly_settlements_project ON monthly_settlements(project_id);
CREATE INDEX idx_monthly_settlements_status ON monthly_settlements(status);
CREATE INDEX idx_monthly_settlements_locked ON monthly_settlements(is_locked);
```

### 2.2 字段说明

| 字段 | 类型 | 必填 | 说明 | 验证规则 |
|------|------|------|------|----------|
| id | BIGSERIAL | 自动 | 主键 | 系统生成 |
| settlement_month | VARCHAR(7) | ✅ | 结算月份 | YYYY-MM 格式 |
| project_id | BIGINT | ✅ | 项目ID | 外键 projects.id |
| total_spend | DECIMAL(15,2) | 自动 | 总消耗 | ≥ 0 |
| total_conversions | INTEGER | 自动 | 总进粉 | ≥ 0 |
| avg_cpl | DECIMAL(10,4) | 自动 | 平均 CPL | spend / conversions |
| unit_price | DECIMAL(10,4) | 自动 | 项目单价快照 | 生成时从 projects 取 |
| revenue | DECIMAL(15,2) | 自动 | 预计收入 | conversions × unit_price |
| gross_profit | DECIMAL(15,2) | 自动 | 毛利 | revenue - spend |
| profit_rate | DECIMAL(8,4) | 自动 | 毛利率 | profit / revenue |
| status | VARCHAR(20) | 自动 | 状态 | 见状态机 |
| is_locked | BOOLEAN | 自动 | 是否锁定 | locked 状态时 true |

### 2.3 索引设计

| 索引名 | 字段 | 类型 | 用途 |
|--------|------|------|------|
| uk_monthly_settlement | (settlement_month, project_id) | UNIQUE | 唯一性约束 |
| idx_monthly_settlements_month | settlement_month | B-tree | 按月份查询 |
| idx_monthly_settlements_project | project_id | B-tree | 按项目查询 |
| idx_monthly_settlements_status | status | B-tree | 按状态筛选 |
| idx_monthly_settlements_locked | is_locked | B-tree | 按锁定状态筛选 |

### 2.4 关联关系

```
monthly_settlements
    ├──→ projects (project_id → id) 多对一
    ├──→ users (confirmed_by → id) 多对一
    ├──→ users (locked_by → id) 多对一
    └──→ users (created_by → id) 多对一

数据聚合来源:
    ├── ad_spend_daily → SUM(spend) WHERE month = settlement_month
    └── daily_reports → SUM(conversions) WHERE month = settlement_month
```

---

## §3 API 设计

### 3.1 端点清单

**来源**: D1-monthly-settlement.md §4, API_SOT.md v9.3 §8

| 方法 | 端点 | 描述 | 权限 |
|------|------|------|------|
| GET | /api/v1/settlements/monthly | 月度结算列表 | finance, ceo |
| GET | /api/v1/settlements/monthly/:id | 结算详情 | finance, ceo |
| POST | /api/v1/settlements/monthly/generate | 生成月度结算 | finance |
| PUT | /api/v1/settlements/monthly/:id | 更新结算 | finance (draft) |
| POST | /api/v1/settlements/monthly/:id/confirm | 确认结算 | finance |
| POST | /api/v1/settlements/monthly/:id/lock | 锁定结算 | ceo, finance |
| POST | /api/v1/settlements/monthly/:id/unlock | 解锁结算 | admin |
| GET | /api/v1/settlements/monthly/:id/details | 项目明细 | finance, ceo |
| GET | /api/v1/settlements/monthly/summary | 汇总统计 | finance, ceo |
| GET | /api/v1/settlements/monthly/export | 导出报表 | finance |

### 3.2 请求/响应格式

**列表查询参数**:
```typescript
interface MonthlySettlementListQuery {
  month?: string;           // 结算月份 YYYY-MM
  project_id?: number;      // 项目ID
  status?: 'pending' | 'draft' | 'confirmed' | 'locked';
  page?: number;            // 页码，默认 1
  page_size?: number;       // 每页数量，默认 20，最大 100
}
```

**生成结算请求**:
```typescript
interface GenerateMonthlySettlementRequest {
  month: string;            // 结算月份 YYYY-MM
  project_ids?: number[];   // 可选，不传则全部项目
}
```

**生成结算响应**:
```typescript
interface GenerateMonthlySettlementResponse {
  data: {
    month: string;
    generated_count: number;
    skipped_count: number;  // 已存在跳过
    total_spend: number;
    total_conversions: number;
  };
  message: string;
}
```

**月度结算响应**:
```typescript
interface MonthlySettlementResponse {
  id: number;
  settlement_month: string;
  project_id: number;
  project_name: string;
  owner_name: string;           // 项目负责人
  total_spend: number;
  total_conversions: number;
  avg_cpl: number | null;
  unit_price: number;
  revenue: number;
  gross_profit: number;
  profit_rate: number;          // 百分比，如 25.6
  status: 'pending' | 'draft' | 'confirmed' | 'locked';
  confirmed_by: number | null;
  confirmed_by_name: string | null;
  confirmed_at: string | null;
  is_locked: boolean;
  locked_by: number | null;
  locked_by_name: string | null;
  locked_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}
```

**汇总统计响应**:
```typescript
interface MonthlySettlementSummaryResponse {
  settlement_month: string;
  total_spend: number;
  total_conversions: number;
  total_revenue: number;
  total_profit: number;
  avg_profit_rate: number;
  project_count: number;
  confirmed_count: number;
  locked_count: number;
}
```

### 3.3 错误码定义

**来源**: ERROR_CODES_SOT.md v2.1 (待扩展)

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| BIZ_600 | 400 | 结算月份格式无效 |
| BIZ_601 | 400 | 结算已存在 |
| BIZ_602 | 400 | 无效的状态转换 |
| BIZ_603 | 400 | 结算已锁定，不可修改 |
| BIZ_604 | 400 | 结算未确认，不可锁定 |
| BIZ_605 | 400 | 月份数据不完整，无法生成 |
| BIZ_606 | 403 | 只有 admin 可解锁 |

### 3.4 分页/筛选规范

```yaml
分页:
  页码: 从 1 开始
  默认每页: 20 条
  最大每页: 100 条

筛选:
  月份: settlement_month (精确匹配)
  项目: project_id (精确匹配)
  状态: status (精确匹配)

排序:
  默认: settlement_month DESC, project_name ASC
```

---

## §4 权限控制

### 4.1 角色权限矩阵 (7 角色)

**来源**: AUTH_SPEC.md v2.0, D1-monthly-settlement.md §5

| 操作 | ceo | project_owner | finance | supervisor | pitcher | account_manager | admin |
|------|-----|---------------|---------|------------|---------|-----------------|-------|
| 查看所有 | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 查看自己项目 | N/A | ✅ | N/A | ❌ | ❌ | ❌ | N/A |
| 生成结算 | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 编辑(draft) | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 确认结算 | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 锁定结算 | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 解锁结算 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 导出报表 | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |

### 4.2 数据权限规则

```python
def can_view_settlement(user: User, settlement: MonthlySettlement) -> bool:
    """判断用户是否可查看结算"""
    # CEO/Finance/Admin 可以看所有
    if user.role in ['ceo', 'finance', 'admin']:
        return True

    # project_owner 只能看自己项目
    if user.role == 'project_owner':
        project = get_project(settlement.project_id)
        return project.owner_id == user.id

    return False

def can_lock_settlement(user: User, settlement: MonthlySettlement) -> bool:
    """判断用户是否可锁定结算"""
    # 必须是 confirmed 状态
    if settlement.status != 'confirmed':
        return False

    # CEO/Finance/Admin 可锁定
    return user.role in ['ceo', 'finance', 'admin']

def can_unlock_settlement(user: User) -> bool:
    """判断用户是否可解锁结算"""
    # 只有 admin 可解锁
    return user.role == 'admin'
```

### 4.3 字段级权限

| 字段 | 生成时 | finance 编辑 | 锁定后 |
|------|--------|-------------|--------|
| settlement_month | ✅ 自动 | ❌ 不可改 | ❌ |
| project_id | ✅ 自动 | ❌ 不可改 | ❌ |
| total_spend | ✅ 汇总 | ❌ 不可改 | ❌ |
| total_conversions | ✅ 汇总 | ❌ 不可改 | ❌ |
| unit_price | ✅ 快照 | ✅ 可修正 | ❌ |
| notes | ❌ | ✅ 可添加 | ❌ |

---

## §5 业务逻辑

### 5.1 状态机定义

**来源**: D1-monthly-settlement.md §2.4, STATE_MACHINE.md v2.7 §10

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        月度结算状态机 (4 状态)                               │
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
│                                                           │               │
│                                                           │ 解锁(admin)   │
│                                                           ↓               │
│                                                     ┌───────────┐        │
│                                                     │ confirmed │        │
│                                                     └───────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**状态转换表**:

| 当前状态 | 目标状态 | 触发条件 | 操作者 |
|----------|----------|----------|--------|
| pending | draft | 执行生成 | finance |
| draft | confirmed | 确认数据准确 | finance |
| confirmed | locked | 锁定结算 | ceo/finance |
| locked | confirmed | 解锁 | admin |

**代码实现**:
```python
class MonthlySettlementStatus(str, Enum):
    PENDING = "pending"
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    LOCKED = "locked"

ALLOWED_TRANSITIONS = {
    MonthlySettlementStatus.PENDING: [MonthlySettlementStatus.DRAFT],
    MonthlySettlementStatus.DRAFT: [MonthlySettlementStatus.CONFIRMED],
    MonthlySettlementStatus.CONFIRMED: [MonthlySettlementStatus.LOCKED],
    MonthlySettlementStatus.LOCKED: [MonthlySettlementStatus.CONFIRMED],  # admin only
}
```

### 5.2 计算逻辑

**来源**: MASTER.md v4.4 §4.5.4, D1-monthly-settlement.md §2.3

**Phase 1 公式（观察用）**:

```python
def calculate_monthly_settlement(project_id: int, month: str) -> dict:
    """计算项目月度结算数据"""

    # 1. 汇总消耗 (Phase 1: ad_spend_daily)
    total_spend = db.query(
        func.sum(AdSpendDaily.spend)
    ).filter(
        AdSpendDaily.project_id == project_id,
        func.to_char(AdSpendDaily.date, 'YYYY-MM') == month
    ).scalar() or Decimal('0')

    # 2. 汇总进粉 (daily_reports)
    total_conversions = db.query(
        func.sum(DailyReport.conversions)
    ).filter(
        DailyReport.project_id == project_id,
        func.to_char(DailyReport.date, 'YYYY-MM') == month
    ).scalar() or 0

    # 3. 获取项目单价
    project = db.query(Project).get(project_id)
    unit_price = project.unit_price or Decimal('0')

    # 4. 计算指标
    avg_cpl = None
    if total_conversions > 0:
        avg_cpl = total_spend / total_conversions

    revenue = Decimal(total_conversions) * unit_price
    gross_profit = revenue - total_spend

    profit_rate = None
    if revenue > 0:
        profit_rate = (gross_profit / revenue) * 100

    return {
        'total_spend': total_spend,
        'total_conversions': total_conversions,
        'avg_cpl': avg_cpl,
        'unit_price': unit_price,
        'revenue': revenue,
        'gross_profit': gross_profit,
        'profit_rate': profit_rate,
    }
```

**Phase 2 公式（结算用）**:

```python
# Phase 2: 使用确认后数据
total_spend = db.query(
    func.sum(DailyReport.real_spend)  # 确认后消耗
).filter(...)

total_conversions = db.query(
    func.sum(DailyReport.conversions_final)  # 确认后进粉
).filter(...)
```

### 5.3 生成结算流程

```python
def generate_monthly_settlements(month: str, project_ids: list = None) -> dict:
    """生成月度结算"""

    # 1. 验证月份格式
    if not re.match(r'^\d{4}-(0[1-9]|1[0-2])$', month):
        raise BusinessError(code='BIZ_600', message='结算月份格式无效')

    # 2. 获取项目列表
    if project_ids:
        projects = db.query(Project).filter(Project.id.in_(project_ids)).all()
    else:
        projects = db.query(Project).filter(Project.status == 'active').all()

    generated = 0
    skipped = 0
    total_spend = Decimal('0')
    total_conversions = 0

    for project in projects:
        # 3. 检查是否已存在
        existing = db.query(MonthlySettlement).filter(
            MonthlySettlement.settlement_month == month,
            MonthlySettlement.project_id == project.id
        ).first()

        if existing:
            skipped += 1
            continue

        # 4. 计算结算数据
        data = calculate_monthly_settlement(project.id, month)

        # 5. 创建结算记录
        settlement = MonthlySettlement(
            settlement_month=month,
            project_id=project.id,
            status='draft',
            **data
        )
        db.add(settlement)

        generated += 1
        total_spend += data['total_spend']
        total_conversions += data['total_conversions']

    db.commit()

    return {
        'month': month,
        'generated_count': generated,
        'skipped_count': skipped,
        'total_spend': total_spend,
        'total_conversions': total_conversions,
    }
```

### 5.4 业务约束 + Phase 1 规则

```yaml
约束规则:
  唯一性约束:
    - (settlement_month, project_id) 必须唯一

  状态约束:
    - 只能按状态机定义的路径转换
    - locked 是终态，仅 admin 可解锁
    - 只有 draft 状态可以编辑

  锁定约束:
    - 锁定后所有数据字段不可修改
    - 锁定后 is_locked = true
    - 解锁需记录审计日志

Phase 1 规则 (照亮阶段):
  ✅ 允许:
    - 生成结算后可修改 unit_price
    - 锁定后仍可查看
    - 未锁定月份可多次重新生成 (覆盖)

  ❌ 禁止:
    - 不自动阻断未完成日报的月份生成
    - 不强制要求所有日报已确认才能生成

  异常处理:
    - 月份数据不完整: 警告但允许生成
    - 进粉为 0: 显示 CPL 为 null，不报错
    - 消耗为 0: 正常生成，显示为 0
```

---

## §6 前后端接口契约

### 6.1 字段映射

| 后端字段 (snake_case) | 前端字段 (camelCase) | 说明 |
|----------------------|---------------------|------|
| settlement_month | settlementMonth | YYYY-MM 字符串 |
| project_id | projectId | number |
| project_name | projectName | string (JOIN) |
| owner_name | ownerName | string (JOIN) |
| total_spend | totalSpend | number |
| total_conversions | totalConversions | number |
| avg_cpl | avgCpl | number | null |
| unit_price | unitPrice | number |
| gross_profit | grossProfit | number |
| profit_rate | profitRate | number (百分比) |
| confirmed_by | confirmedBy | number | null |
| confirmed_by_name | confirmedByName | string | null |
| confirmed_at | confirmedAt | ISO 8601 字符串 | null |
| is_locked | isLocked | boolean |
| locked_by | lockedBy | number | null |
| locked_by_name | lockedByName | string | null |
| locked_at | lockedAt | ISO 8601 字符串 | null |

### 6.2 枚举值对照

```typescript
// 后端和前端使用相同值
type MonthlySettlementStatus = 'pending' | 'draft' | 'confirmed' | 'locked';

// 前端中文映射
const STATUS_LABELS: Record<MonthlySettlementStatus, string> = {
  pending: '待生成',
  draft: '草稿',
  confirmed: '已确认',
  locked: '已锁定',
};

// 状态颜色
const STATUS_COLORS: Record<MonthlySettlementStatus, string> = {
  pending: 'gray',
  draft: 'blue',
  confirmed: 'orange',
  locked: 'green',
};
```

### 6.3 时区/格式约定

```yaml
时间格式:
  月份: YYYY-MM (不含时区)
  时间戳: ISO 8601 (含时区，如 2024-12-23T10:00:00Z)

时区处理:
  存储: UTC
  传输: UTC
  显示: 前端转换为本地时区

数字格式:
  金额: 数字类型，保留2位小数
  CPL: 数字类型，保留4位小数
  百分比: 数字类型，如 25.6 表示 25.6%

空值:
  avg_cpl: 进粉为 0 时返回 null
  profit_rate: 收入为 0 时返回 null
```

---

## §7 测试要点

### 7.1 单元测试

```python
describe('MonthlySettlementService', () => {

    describe('calculate_monthly_settlement', () => {
        it('正确计算消耗汇总', async () => {
            # 准备测试数据: 3 条 ad_spend_daily
            result = calculate_monthly_settlement(project_id=1, month='2025-12')
            expect(result['total_spend']).toBe(Decimal('15000.00'))

        it('进粉为 0 时 avg_cpl 返回 null', async () => {
            result = calculate_monthly_settlement(project_id=2, month='2025-12')
            expect(result['avg_cpl']).toBeNull()

        it('正确计算毛利率', async () => {
            result = calculate_monthly_settlement(project_id=1, month='2025-12')
            # 收入 10000, 消耗 7500, 毛利 2500, 毛利率 25%
            expect(result['profit_rate']).toBe(Decimal('25.00'))

    describe('状态转换', () => {
        it('draft → confirmed 允许', () => {
            expect(can_transition('draft', 'confirmed')).toBe(True)

        it('draft → locked 不允许', () => {
            expect(can_transition('draft', 'locked')).toBe(False)

        it('locked 只有 admin 可解锁', () => {
            expect(can_unlock(role='finance')).toBe(False)
            expect(can_unlock(role='admin')).toBe(True)
})
```

### 7.2 集成测试

```python
describe('POST /api/v1/settlements/monthly/generate', () => {

    it('finance 可以生成结算', async () => {
        response = await request(app)
            .post('/api/v1/settlements/monthly/generate')
            .set('Authorization', f'Bearer {finance_token}')
            .send({'month': '2025-12'})

        expect(response.status).toBe(201)
        expect(response.body.data.generated_count).toBeGreaterThan(0)

    it('pitcher 不能生成结算', async () => {
        response = await request(app)
            .post('/api/v1/settlements/monthly/generate')
            .set('Authorization', f'Bearer {pitcher_token}')
            .send({'month': '2025-12'})

        expect(response.status).toBe(403)

    it('重复生成已存在月份跳过', async () => {
        # 第一次生成
        await generate_settlement('2025-12')

        # 第二次生成
        response = await request(app)
            .post('/api/v1/settlements/monthly/generate')
            .send({'month': '2025-12'})

        expect(response.body.data.skipped_count).toBeGreaterThan(0)
})

describe('POST /api/v1/settlements/monthly/:id/lock', () => {

    it('confirmed 状态可锁定', async () => {
        settlement = await create_confirmed_settlement()

        response = await request(app)
            .post(f'/api/v1/settlements/monthly/{settlement.id}/lock')
            .set('Authorization', f'Bearer {ceo_token}')

        expect(response.status).toBe(200)
        expect(response.body.data.is_locked).toBe(True)

    it('draft 状态不可锁定', async () => {
        settlement = await create_draft_settlement()

        response = await request(app)
            .post(f'/api/v1/settlements/monthly/{settlement.id}/lock')

        expect(response.status).toBe(400)
        expect(response.body.error.code).toBe('BIZ_604')
})
```

### 7.3 权限测试矩阵

```python
test_cases = [
    # [角色, 操作, 预期结果]
    ['ceo', 'list_all', 200],
    ['ceo', 'generate', 403],
    ['ceo', 'lock_confirmed', 200],
    ['finance', 'list_all', 200],
    ['finance', 'generate', 201],
    ['finance', 'confirm_draft', 200],
    ['finance', 'lock_confirmed', 200],
    ['finance', 'unlock_locked', 403],
    ['project_owner', 'list_all', 403],
    ['project_owner', 'list_own', 200],
    ['project_owner', 'generate', 403],
    ['admin', 'unlock_locked', 200],
]

@pytest.mark.parametrize("role,action,expected", test_cases)
def test_permissions(role, action, expected):
    response = execute_action(role, action)
    assert response.status == expected
```

---

## §8 性能要求

### 8.1 响应时间要求

| API | 目标 | 最大容忍 |
|-----|------|----------|
| 列表查询 | < 200ms | < 500ms |
| 详情查询 | < 100ms | < 300ms |
| 生成结算 (10 项目) | < 2s | < 5s |
| 汇总统计 | < 300ms | < 1s |
| 导出 Excel | < 5s | < 10s |

### 8.2 索引要求

必须为以下查询场景建立索引:
- 按月份查询: `idx_monthly_settlements_month`
- 按项目查询: `idx_monthly_settlements_project`
- 按状态筛选: `idx_monthly_settlements_status`
- 唯一性约束: `uk_monthly_settlement`

### 8.3 批量操作限制

| 操作 | 单次上限 | 说明 |
|------|----------|------|
| 生成结算 | 100 项目 | 超出分批 |
| 批量锁定 | 50 条 | 超出分批 |
| 导出 | 1000 条 | 超出走异步 |

---

## §9 安全规范

### 9.1 认证授权

- 所有 API 需要 JWT Token
- 每个 API 校验角色权限
- project_owner 只能访问自己项目
- 解锁操作需要 admin 角色

### 9.2 输入验证

- [ ] 月份格式验证 (YYYY-MM)
- [ ] project_id 存在性验证
- [ ] 状态转换合法性验证
- [ ] 金额字段非负验证

### 9.3 审计日志

必须记录以下操作:

| 操作类型 | 记录内容 |
|----------|----------|
| 生成 | 操作人、月份、生成数量 |
| 确认 | 操作人、时间、结算ID |
| 锁定 | 操作人、时间、结算ID |
| 解锁 | **必须记录**: 操作人、时间、原因 |

---

## 附录 A: 与通用结算模块的关系

### A.1 现有通用结算模块

**文件位置**:
- Model: `backend/models/finance/settlement.py`
- Schema: `backend/schemas/settlement.py`
- Service: `backend/services/settlement_service.py`
- Router: `backend/routers/settlements.py`

**7 状态机**:
```
draft → pending → approved → processing → completed
          ↓
       rejected → draft

draft/approved → cancelled
```

### A.2 月度结算与通用结算的关系

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          结算模块架构                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 通用结算 (Settlement)                                               │   │
│  │ - 供应商付款 (supplier_payment)                                     │   │
│  │ - 客户账单 (client_billing)                                         │   │
│  │ - 内部转账 (internal_transfer)                                      │   │
│  │ - 退款 (refund)                                                     │   │
│  │ 状态: 7 状态机                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 月度结算 (MonthlySettlement) [本规格书]                              │   │
│  │ - 项目月度盈亏汇总                                                   │   │
│  │ - 自动聚合生成                                                       │   │
│  │ 状态: 4 状态机 (pending → draft → confirmed → locked)                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  关联:                                                                      │
│  - 月度结算锁定后，可触发创建供应商付款 Settlement                          │
│  - 两者共用 ledger_entries 记录资金流水                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 附录 B: AI 代码工厂禁止行为清单

### B.1 禁止行为

| 禁止行为 | 正确做法 | 检查方式 |
|---------|---------|---------|
| 使用 7 状态机 | 使用 4 状态机 | 枚举对比 |
| 自定义错误码 | 使用 BIZ_600-699 | grep 检查 |
| 直接修改锁定结算 | 检查 is_locked | 代码审查 |
| 非 admin 解锁 | 检查 role == 'admin' | 代码审查 |
| 硬编码月份格式 | 使用正则验证 | 代码审查 |
| 跳过权限检查 | Service 层必须检查 | 代码审查 |

### B.2 SoT 追溯验证 Checklist

生成代码后必须验证:
- [ ] 状态值来自 4 状态枚举 (pending/draft/confirmed/locked)
- [ ] 计算公式来自 MASTER.md §4.5.4
- [ ] 错误码来自 ERROR_CODES_SOT.md
- [ ] 角色来自 MASTER.md v4.4 §2.4 (7 个)
- [ ] 金额字段使用 Decimal 类型
- [ ] 时间字段使用 TIMESTAMPTZ + UTC

---

## 源码位置

| 层 | 文件路径 | 状态 |
|----|---------|------|
| Model | `backend/models/finance/monthly_settlement.py` | 待创建 |
| Schema | `backend/schemas/monthly_settlement.py` | 待创建 |
| Service | `backend/services/monthly_settlement_service.py` | 待创建 |
| Router | `backend/routers/monthly_settlements.py` | 待创建 |
| Test | `backend/tests/settlements/test_monthly_settlement_service.py` | 待创建 |

**现有通用结算** (已实现):
| 层 | 文件路径 |
|----|---------|
| Model | `backend/models/finance/settlement.py` |
| Schema | `backend/schemas/settlement.py` |
| Service | `backend/services/settlement_service.py` |
| Router | `backend/routers/settlements.py` |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-23 | 初始版本 |

---

**维护者**: AI 广告代投系统开发团队
**关联文档**:
- D1-monthly-settlement.md (前端规格书)
- MASTER.md v4.4 §4.5.4 (盈亏计算公式)
- LEDGER_SOT.md v1.2 (账本规则)
- settlement.types.ts (前端类型定义)
