---
version: v4.6
status: frozen
layer: sot
owner: wade
last_reviewed: 2025-12-26
baseline:
  - MASTER.md v4.4
  - STATE_MACHINE.md v2.6
  - DATA_SCHEMA.md v5.2
  - LEDGER_SOT.md v1.1
  - ERROR_CODES_SOT.md v2.1
patch_type: constitutional
---

# 业务规则大全 (Business Rules)

> **版本**: v4.6 (宪法级增量补丁)
> **基准**: MASTER.md v4.4, STATE_MACHINE.md v2.6, DATA_SCHEMA.md v5.2
> **最后更新**: 2025-12-26
> **补丁性质**: 预收款·履约·结算模型统一补丁

---

## 第1章 文档说明

### 1.1 定位

本文档是 **AI 广告代投系统的业务规则唯一真相源 (SoT)**，定义：

- 开发铁律（不可违反的技术约束）
- 业务规则索引（按模块组织）
- Phase 边界（照亮 vs 问责）
- 术语表（业务与技术对照）

### 1.2 裁判链优先级

当文档间存在冲突时，按以下优先级裁决：

```
MASTER.md v4.4 > STATE_MACHINE.md v2.6 > DATA_SCHEMA.md v5.2
> BUSINESS_RULES.md v4.6 > API_SOT.md v9.1 > ERROR_CODES_SOT.md v2.1
```

### 1.3 角色定义 (7 角色)

来源：MASTER.md v4.4 §2.4

| 角色 | 系统值 | 职责 |
|------|--------|------|
| 老板 | `ceo` | 资金安全、公司盈亏、最终决策 |
| 项目负责人 | `project_owner` | 项目盈亏、资金使用效率 |
| 财务 | `finance` | 资金出入准确、数据真实、对账 |
| 主管 | `supervisor` | 团队产出、投手管理、日常监督 |
| 投手 | `pitcher` | CPL 达标、日报准确、执行投放 |
| 户管 | `account_manager` | 账户分配、账户状态监控 |
| 管理员 | `admin` | 系统配置（不参与业务） |

### 1.4 Phase 边界说明

来源：MASTER.md v4.4 §4

| 阶段 | 代号 | 行为原则 | 典型操作 |
|------|------|----------|----------|
| Phase 1 | 照亮 | 记录 + 提示 + 高亮 | 警告、标记、统计 |
| Phase 2 | 问责 | 强制 + 审批 + 考核 | 阻断、拒绝、惩罚 |

**Phase 1 禁止行为**：
- ❌ 自动阻断 / 自动拒绝 / 自动暂停 / 自动冻结
- ❌ 自动惩罚机制（扣分、禁用账户等）
- ❌ 强制审批流程

**Phase 1 允许行为**：
- ✅ 记录事实、展示状态、提示异常
- ✅ 高亮警告、数据统计、趋势分析

### 1.5 系统不变量 (Business Invariants)

来源：BUSINESS_RULES.md v4.6（宪法级补丁）

系统不变量是跨模块的核心约束，任何代码实现都必须遵守。

| 编号 | 名称 | 级别 | 说明 |
|------|------|------|------|
| BI-05 | 履约完成前不得确认收入 | P0 | 客户打款一律记为预收款，履约完成后才确认收入 |
| BI-06 | 履约完成的唯一判定条件 | P0 | 广告费消耗完 OR 甲方明确喊停 |
| BI-07 | 预收款不足的 Phase 1 处理 | P0 | 只提示风险，不自动阻断 |

#### 1.5.1 BI-05 履约完成前不得确认收入

**核心规则**：

```
┌─────────────────────────────────────────────────────────────────┐
│                    收入确认时序约束                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   客户打款 ────────────────────────────────────────────→        │
│        │                                                        │
│        ↓                                                        │
│   ┌──────────────┐                                              │
│   │   预收款      │  ← 履约完成前，所有入金都是预收款            │
│   │ (Prepayment) │                                              │
│   └──────────────┘                                              │
│        │                                                        │
│        │ 履约完成 (fulfilled = true)                            │
│        ↓                                                        │
│   ┌──────────────┐                                              │
│   │  已确认收入   │  ← 按结算规则计算，进入利润表                │
│   │  (Revenue)   │                                              │
│   └──────────────┘                                              │
│                                                                 │
│   不变量：预收款 ≠ 收入                                         │
│   利润只能在履约完成并确认收入后计算                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**实现约束**：
- 履约完成前：客户入金 → `ledger_entry.type = PREPAYMENT_RECEIVED`
- 履约完成后：按结算规则 → `ledger_entry.type = REVENUE_CONFIRMED`
- 公司收支表是现金流 SoT，不是利润表

#### 1.5.2 BI-06 履约完成的唯一判定条件

**判定规则**：

项目履约完成（`fulfilled = true`）当且仅当满足以下任一条件：

| 条件 | 履约结束原因 | 说明 |
|------|-------------|------|
| 广告费消耗完 | `spend_exhausted` | 预算全部投放完毕 |
| 甲方明确喊停 | `client_stopped` | 客户主动终止投放 |

**必须记录的字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `fulfillment_status` | enum | `running` / `fulfilled` |
| `fulfillment_reason` | enum | `spend_exhausted` / `client_stopped` |
| `fulfilled_at` | TIMESTAMPTZ | 履约完成时间 (UTC) |

**终态约束**：`fulfilled` 状态不可回退。

#### 1.5.3 BI-07 预收款不足的 Phase 1 处理

**处理规则**：

当预收款余额低于安全阈值时：

| Phase | 系统行为 | 管理动作 |
|-------|---------|---------|
| Phase 1 | 只提示风险（警告标记） | 提前与甲方沟通补款 |
| Phase 2 | 自动阻断投放（未实现） | 触发补款流程 |

**Phase 1 禁止行为**：
- ❌ 自动停投
- ❌ 自动阻断履约
- ❌ 自动拒绝充值申请

---

## 第2章 管理核心目标

### 2.1 三权清晰

来源：MASTER.md v4.4 §3

```
┌─────────────────────────────────────────────────────────────────┐
│                        三权清晰                                  │
├─────────────────────────────────────────────────────────────────┤
│  谁对钱负责：项目负责人申请 → 财务审核 → 老板批准                   │
│  谁对结果负责：项目负责人对盈亏负责                                │
│  谁能纠偏：日级主管、周级项目负责人、月级老板                       │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 资金管控链

来源：MASTER.md v4.4 §2.1

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          资金责任链                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   项目负责人申请 → 财务审核 → 老板批准 → 户管分配 → 投手使用            │
│        │              │           │          │          │               │
│    提交理由      检查预算     承担风险    账户调配    消耗资金           │
│                                                                         │
│   Phase 1：有流程，可紧急绕行                                           │
│   Phase 2：无批准不打款                                                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**职责边界**：

| 角色 | 职责 | 资金环节权限 |
|------|------|-------------|
| 项目负责人 (project_owner) | 提交充值申请，对资金使用效率负责 | 申请 |
| 财务 (finance) | 审核合规性，复核数据 | 审核 |
| 老板 (ceo) | 最终批准，承担资金风险 | 批准 |
| 户管 (account_manager) | 账户调配，状态监控 | 分配 |
| 投手 (pitcher) | 消耗资金，提交日报 | 使用 |

### 2.3 结果责任链

来源：MASTER.md v4.4 §2.2

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          结果责任链                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   投手执行 → 主管监督 → 项目负责人对盈亏负责 → 老板最终决策             │
│      │           │              │                  │                    │
│   CPL达标    团队产出       项目盈亏          公司盈亏                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**考核周期与后果**：

| 层级 | 责任人 | 负责什么 | 考核周期 | Phase 1 后果 | Phase 2 后果 |
|------|--------|----------|----------|-------------|-------------|
| 个人 | 投手 | CPL 达标 | 日度 | 沟通/记录 | 警告/暂停 |
| 团队 | 主管 | 投手产出 | 周度 | 沟通/记录 | 调整分工 |
| 项目 | 项目负责人 | 项目盈亏 | 月度 | 复盘/沟通 | 复盘/调整/更换 |
| 公司 | 老板 | 公司盈亏 | 月度 | 自由裁决 | 按规则执行 |

> **Phase 1 说明**：不达标后果仅为「沟通与记录」，不触发任何惩罚性措施。

### 2.4 纠偏机制

| 异常类型 | 发现周期 | 纠偏责任人 | Phase 1 行为 |
|----------|----------|------------|--------------|
| CPL 超标 | 日 | 主管 | 高亮提示 |
| 预算超支 | 周 | 项目负责人 | 警告通知 |
| 盈亏异常 | 月 | 老板 | 趋势报告 |

### 2.5 角色输入输出矩阵 (v4.6 新增)

> **重要**: 本节定义各角色在系统中的数据输入职责和输出查看权限。

#### 2.5.1 投手 (pitcher) - 日报填报

**输入职责**：

| 输入项 | 频率 | 数据字段 | 说明 |
|--------|------|----------|------|
| 日报 | 每日 | `daily_reports` | T+0 提交 |
| ├─ 消耗金额 | 每日 | `raw_spend` | 当日广告消耗 (Decimal) |
| ├─ 进粉数 | 每日 | `conversions` | 当日转化数量 |
| ├─ 所属项目 | 每日 | `project_id` | 通过 ad_account 关联 |
| └─ 所属账户 | 每日 | `ad_account_id` | 投放账户 |

**输出查看**：

| 输出项 | 说明 |
|--------|------|
| 我的日报列表 | 仅本人提交的日报 |
| 我的 CPL 趋势 | 个人效率指标 |
| 账户余额 | 所分配账户的余额 |

#### 2.5.2 项目负责人 (project_owner) - 项目与履约管理

**输入职责**：

| 输入项 | 频率 | 数据字段 | 说明 |
|--------|------|----------|------|
| 创建项目 | 按需 | `projects` | 项目基础信息 |
| ├─ 项目名称 | - | `name` | 必填 |
| ├─ 地区 | - | `region` | 投放地区 |
| ├─ 单价 | - | `unit_price` | 按粉结算单价 (Decimal) |
| ├─ 结算规则 | - | `price_rules` | fixed/tiered/markup |
| └─ 阶梯定价 | - | `price_rules.tiers` | JSON 结构（可选） |
| 甲方确认进粉 | 每日 | `conversions_final` | 甲方核对过的实际进粉数 |
| 项目预算 | 按需 | `daily_budget`, `monthly_budget` | 预算控制 |
| 履约状态变更 | 按需 | `fulfillment_status` | running → fulfilled |

**输出查看**：

| 输出项 | 说明 |
|--------|------|
| 项目盈亏报表 | 项目维度的收入/成本/利润 |
| 项目进粉趋势 | 投手 vs 甲方确认数对比 |
| 项目预收款余额 | 项目级资金状态 |
| 团队成员绩效 | 项目下投手的 CPL 排名 |

#### 2.5.3 财务 (finance) - 资金与对账

**输入职责**：

| 输入项 | 频率 | 数据字段 | 说明 |
|--------|------|----------|------|
| 核对实际消耗 | 每日 | `real_spend` | 平台导出的真实消耗 |
| 代理商充值 | 按需 | `topup_requests` | 给代理商/平台的充值 |
| ├─ 充值金额 | - | `amount` | 充值金额 (Decimal) |
| ├─ 代理商/渠道 | - | `channel_id` | 哪个代理商 |
| └─ 手续费 | - | `service_fee` | 手续费/返点 |
| 账户类型 | 按需 | `ad_accounts.account_type` | 账户分类 |
| ├─ 账户类型 | - | `account_type` | 信用/预付/授权 |
| └─ 手续费率 | - | `fee_rate` | 渠道手续费率 |
| 客户回款 | 按需 | `prepayments` | 客户入金记录 |
| ├─ 回款金额 | - | `amount` | 入金金额 |
| └─ 回款来源 | - | `source` | 银行转账/支付宝等 |
| 结算单确认 | 每月 | `settlements` | 月度结算 |

**输出查看**：

| 输出项 | 说明 |
|--------|------|
| 资金总览 | 累计预收款、预收款余额、未履约负债 |
| 充值审批列表 | 待审核的充值申请 |
| 对账报表 | 消耗差异、手续费统计 |
| 公司收支表 | 现金流 SoT |

#### 2.5.4 户管 (account_manager) - 账户分配与监控

**输入职责**：

| 输入项 | 频率 | 数据字段 | 说明 |
|--------|------|----------|------|
| 下户记录 | 每日 | `ad_accounts` | 新增账户 |
| ├─ 代理商来源 | - | `channel_id` | 从哪个代理商下户 |
| ├─ 账户数量 | - | (批量创建) | 当日下了多少户 |
| └─ 账户 ID | - | `account_id` | 平台账户 ID |
| 账户分配 | 每日 | `ad_accounts.pitcher_id` | 分配给哪个投手 |
| 死户登记 | 每日 | `ad_accounts.status` | active → dead |
| ├─ 死户数量 | - | (状态变更) | 当日死了几个户 |
| └─ 死亡原因 | - | `death_reason` | 封禁/欠费/其他 |
| 账户余额更新 | 每日 | `ad_accounts.balance` | 通过 ledger_entries |
| 充值申请 | 每日 | `topup_requests` | 提交广告费充值 |
| ├─ 充值账户 | - | `ad_account_id` | 给哪个户充值 |
| └─ 充值金额 | - | `amount` | 需要充多少 |

**输出查看**：

| 输出项 | 说明 |
|--------|------|
| 账户列表 | 所有账户状态、余额、分配情况 |
| 账户余额预警 | 余额不足提示 |
| 死户统计 | 各渠道死户率 |
| 下户趋势 | 每日新增/死亡账户数 |

#### 2.5.5 主管 (supervisor) - 团队监督

**输入职责**：

| 输入项 | 频率 | 数据字段 | 说明 |
|--------|------|----------|------|
| 日报审核 | 每日 | `daily_reports.status` | trend_ok / trend_flagged |
| 异常标记 | 按需 | `daily_reports.flags` | 标记异常日报 |

**输出查看**：

| 输出项 | 说明 |
|--------|------|
| 团队日报总览 | 团队下所有投手的日报 |
| CPL 排名 | 投手效率排名 |
| 日报填报率 | 团队日报提交情况 |
| 异常日报列表 | 需关注的异常记录 |

#### 2.5.6 老板 (ceo) - 全局决策

**输入职责**：

| 输入项 | 频率 | 数据字段 | 说明 |
|--------|------|----------|------|
| 充值终审 | 按需 | `topup_requests.status` | finance_approve → paid |
| 战略决策 | 按需 | - | 人工干预 |

**输出查看**：

| 输出项 | 说明 |
|--------|------|
| CEO 驾驶舱 | 全公司 KPI 概览 |
| ├─ 今日消耗 | 全公司消耗汇总 |
| ├─ 今日进粉 | 全公司进粉汇总 |
| ├─ 公司 CPL | 整体效率指标 |
| ├─ 项目利润排名 | Top 5 盈利/亏损项目 |
| ├─ 预收款余额 | 关键风控指标 |
| └─ 未履约负债 | 财务健康指标 |
| 公司盈亏报表 | 月度/年度利润表 |
| 项目 ROI 分析 | 各项目投资回报率 |

#### 2.5.7 输入输出汇总图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          系统输入输出总览                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   投手                                                                      │
│   ├─ 输入: 日报(消耗、进粉、账户)                                           │
│   └─ 输出: 个人日报、CPL趋势                                                │
│                                                                             │
│   户管                                                                      │
│   ├─ 输入: 下户、分配、死户、余额、充值申请                                  │
│   └─ 输出: 账户列表、余额预警、死户统计                                      │
│                                                                             │
│   主管                                                                      │
│   ├─ 输入: 日报审核、异常标记                                               │
│   └─ 输出: 团队日报、CPL排名、填报率                                        │
│                                                                             │
│   项目负责人                                                                │
│   ├─ 输入: 项目(名称、地区、单价、结算规则)、甲方确认进粉                    │
│   └─ 输出: 项目盈亏、进粉趋势、预收款余额                                    │
│                                                                             │
│   财务                                                                      │
│   ├─ 输入: 实际消耗、代理商充值、手续费、客户回款、结算单                    │
│   └─ 输出: 资金总览、对账报表、收支表                                        │
│                                                                             │
│   老板                                                                      │
│   ├─ 输入: 充值终审、战略决策                                               │
│   └─ 输出: CEO驾驶舱、公司盈亏、项目ROI                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 第3章 开发铁律 (6 条)

### DEV-001 金额必须用 Decimal

**规则描述**：所有金额字段必须使用 Decimal(15,2) 类型存储，禁止使用 Float。

**原因**：Float 存在精度丢失问题，财务数据必须精确。

**后端实现**：
```python
from decimal import Decimal
from sqlalchemy import Column, Numeric

class AdAccount(Base):
    # 正确：使用 Numeric
    balance = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))

    # 错误：使用 Float
    # balance = Column(Float)

# 正确：Decimal 计算
new_balance = account.balance + Decimal("1000.00")

# 错误：浮点数计算
# new_balance = account.balance + 1000.0
```

**前端实现**：
```typescript
// 正确：使用字符串传输，前端转换显示
interface Amount {
  value: string;  // "1234.56"
}

const formatAmount = (value: string): string => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(parseFloat(value));
};

// 错误：直接用 number 计算
// const total = amount1 + amount2;
```

**违规检测**：
```bash
# 检测后端 Float 用于金额
grep -rn "Column(Float" backend/models/ | grep -i "balance\|amount\|cost\|spend"
```

---

### DEV-002 时间必须用 UTC

**规则描述**：所有时间字段使用 TIMESTAMPTZ 存储，统一使用 UTC 时区。

**后端实现**：
```python
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime

class BaseModel(Base):
    # 正确：TIMESTAMPTZ + UTC
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    # 错误：不带时区
    # created_at = Column(DateTime, default=datetime.now)

# 正确：获取当前 UTC 时间
now = datetime.now(timezone.utc)

# 错误：使用本地时间
# now = datetime.now()
```

**前端处理**：
```typescript
// 正确：UTC 传输，本地显示
const formatDateTime = (utcString: string): string => {
  const date = new Date(utcString);
  return date.toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' });
};

// API 传输格式：ISO 8601
// "2025-12-24T08:00:00Z"
```

**违规检测**：
```bash
# 检测不带时区的 DateTime
grep -rn "DateTime(" backend/models/ | grep -v "timezone=True"
```

---

### DEV-003 禁止物理删除核心数据

**规则描述**：核心业务数据（日报、充值、账户）禁止物理删除，必须使用软删除。

**核心数据定义**：
- `daily_reports` - 日报记录
- `topup_requests` - 充值申请
- `ledger_entries` - 账本记录
- `ad_accounts` - 广告账户

**后端实现**：
```python
from sqlalchemy import Column, Boolean, DateTime

class SoftDeleteMixin:
    """软删除混入"""
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID, nullable=True)

class DailyReport(Base, SoftDeleteMixin):
    # 正确：软删除
    def soft_delete(self, user_id: UUID):
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by = user_id

    # 禁止：物理删除
    # def delete(self):
    #     session.delete(self)

# 查询时过滤已删除
def get_reports(db: Session):
    return db.query(DailyReport).filter(DailyReport.is_deleted == False).all()
```

**例外情况**：
- `draft` 状态的日报可物理删除（由创建者本人删除）
- 测试数据可物理删除

**违规检测**：
```bash
# 检测直接 delete 操作
grep -rn "\.delete(" backend/services/ | grep -v "soft_delete"
```

---

### DEV-004 角色不可变更

**规则描述**：用户角色在创建后不可修改，只能通过 admin 账户操作。

**设计原因**：
- 防止权限提升攻击
- 保证审计追溯完整性
- 简化权限模型

**后端实现**：
```python
class UserService:
    def update_user(self, user_id: UUID, update_data: dict):
        # 正确：禁止修改角色
        if "role" in update_data:
            raise BusinessError(
                code="AUTH-003",
                message="角色不可修改，请联系管理员"
            )

        # 正常更新其他字段
        return self.repo.update(user_id, update_data)

    def admin_change_role(self, admin_id: UUID, user_id: UUID, new_role: str):
        """仅 admin 可调用"""
        # 记录审计日志
        self.audit_log.record(
            action="change_role",
            operator_id=admin_id,
            target_id=user_id,
            old_value=user.role,
            new_value=new_role
        )
        return self.repo.update_role(user_id, new_role)
```

**API 层保护**：
```python
@router.patch("/users/{user_id}")
def update_user(
    user_id: UUID,
    update: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    # Schema 层面排除 role 字段
    if hasattr(update, 'role'):
        raise HTTPException(403, "Role modification not allowed via this endpoint")
```

---

### DEV-005 终态不可回退

**规则描述**：状态机的终态不可回退到任何前置状态，修正只能通过红冲机制。

**终态定义**（来源：STATE_MACHINE.md v2.6）：

| 实体 | 终态 | 说明 |
|------|------|------|
| 日报 (daily_reports) | `final_locked` | 计费锁定，不可修改 |
| 充值 (topup_requests) | `completed` | 充值完成 |
| 充值 (topup_requests) | `rejected` | 审核拒绝 |
| 充值 (topup_requests) | `cancelled` | 申请取消 |
| 对账 (reconciliation_batches) | `completed` | 对账完成 |
| 项目 (projects) | `archived` | 项目归档 |
| 账户 (ad_accounts) | `archived` | 账户归档 |

> **修正机制**：终态数据错误只能通过 REVERSAL（红冲）进行修正，不可直接回退状态。

**后端实现**：
```python
TERMINAL_STATES = {
    "daily_reports": ["final_locked"],
    "topup_requests": ["completed", "rejected", "cancelled"],
    "reconciliation_batches": ["completed"],
    "projects": ["archived"],
    "ad_accounts": ["archived"]
}

def validate_transition(entity: str, current: str, target: str):
    if current in TERMINAL_STATES.get(entity, []):
        raise BusinessError(
            code="STATE-002",
            message=f"{entity} 已处于终态 {current}，不可转换到 {target}"
        )
```

**违规检测**：
```python
def test_terminal_state_protection():
    """终态保护测试"""
    report = DailyReport(status="final_locked")

    with pytest.raises(BusinessError) as exc:
        service.transition(report.id, "final_confirmed")

    assert exc.value.code == "STATE-002"
```

---

### DEV-006 账务只追加不修改

**规则描述**：账本记录 (ledger_entries) 只能追加，禁止修改或删除已有记录。

**来源**：MASTER.md v4.4 INV-001, LEDGER_SOT.md v1.1

**设计原因**：
- 保证财务数据完整性和可追溯性
- 支持审计合规
- 符合会计准则（账务不可篡改）

**后端实现**：
```python
class LedgerService:
    def add_entry(
        self,
        account_id: UUID,
        amount: Decimal,
        entry_type: str,
        reference_id: UUID = None
    ) -> LedgerEntry:
        """正确：只追加新记录"""
        current_balance = self.get_balance(account_id)

        entry = LedgerEntry(
            account_id=account_id,
            amount=amount,
            entry_type=entry_type,
            balance_after=current_balance + amount,
            reference_id=reference_id,
            created_at=datetime.now(timezone.utc)
        )
        db.add(entry)
        db.commit()
        return entry

    def correct_error(
        self,
        original_entry_id: UUID,
        reason: str,
        operator_id: UUID
    ) -> LedgerEntry:
        """正确：通过红冲修正错误"""
        original = self.get_entry(original_entry_id)

        # 创建反向记录（红冲）
        reversal = LedgerEntry(
            account_id=original.account_id,
            amount=-original.amount,  # 反向金额
            entry_type="REVERSAL",
            reference_id=original.id,
            reason=reason,
            created_by=operator_id
        )
        db.add(reversal)
        db.commit()
        return reversal

    # 禁止：直接修改
    # def update_entry(self, entry_id: UUID, new_amount: Decimal):
    #     entry = self.get_entry(entry_id)
    #     entry.amount = new_amount  # 违反 INV-001

    # 禁止：直接删除
    # def delete_entry(self, entry_id: UUID):
    #     entry = self.get_entry(entry_id)
    #     db.delete(entry)  # 违反 INV-001
```

**绑定规则**: INV-001, BR-FIN-005

**错误码**: `LEDGER-001`（账本记录不可修改）

**违规检测**：
```bash
# 检测直接 update/delete ledger_entries
grep -rn "\.amount\s*=" backend/services/ | grep -i ledger
grep -rn "db\.delete" backend/services/ | grep -i ledger
```

---

## 第4章 业务规则模块索引 (11 模块)

### 4.0 模块总览

| 模块编号 | 模块名称 | 规则数 | 优先级 | SoT 来源 |
|----------|----------|--------|--------|----------|
| BR-AUTH | 认证授权 | 5 | P0 | AUTH_SPEC.md v2.0 |
| BR-USER | 用户管理 | 4 | P1 | DATA_SCHEMA.md §2.1 |
| BR-PROJ | 项目管理 | 6 | P0 | DATA_SCHEMA.md §2.2 |
| BR-CHAN | 渠道管理 | 3 | P1 | DATA_SCHEMA.md §2.3 |
| BR-ACCT | 账户管理 | 6 | P0 | DATA_SCHEMA.md §2.4 |
| BR-FIN | 财务管理 | 7 | P0 | LEDGER_SOT.md v1.1 |
| BR-RECON | 对账管理 | 4 | P1 | STATE_MACHINE.md §4 |
| BR-RPT | 日报管理 | 8 | P0 | STATE_MACHINE.md §2 |
| BR-DATA | 数据规则 | 6 | P0 | DATA_SCHEMA.md v5.2 |
| BR-STL | 结算与履约（宪法级） | 8 | P0 | BUSINESS_RULES.md v4.6 |
| BR-AR | 预收款与回款（宪法级） | 5 | P0 | BUSINESS_RULES.md v4.6 |

---

### 4.1 BR-AUTH 认证授权模块

来源：AUTH_SPEC.md v2.0

| 编号 | 规则名称 | 级别 | 说明 |
|------|----------|------|------|
| BR-AUTH-001 | Supabase JWT 验证 | P0 | 所有 API 必须验证 JWT |
| BR-AUTH-002 | 角色不可变 | P0 | 见 DEV-004 |
| BR-AUTH-003 | 7 角色定义 | P0 | ceo/project_owner/finance/supervisor/pitcher/account_manager/admin |
| BR-AUTH-004 | 数据权限隔离 | P0 | 投手只能看自己的日报 |
| BR-AUTH-005 | API 权限矩阵 | P1 | 参考 API_SOT.md §7 |

---

### 4.2 BR-USER 用户管理模块

来源：DATA_SCHEMA.md v5.2 §2.1

| 编号 | 规则名称 | 级别 | 说明 |
|------|----------|------|------|
| BR-USER-001 | 用户唯一性 | P0 | email 全局唯一 |
| BR-USER-002 | 用户软删除 | P1 | 禁止物理删除，使用 deleted_at |
| BR-USER-003 | 用户-角色关联 | P1 | 一个用户一个角色（当前版本） |
| BR-USER-004 | 用户-项目关联 | P1 | 通过 project_members 表 |

---

### 4.3 BR-PROJ 项目管理模块

来源：DATA_SCHEMA.md v5.2 §2.2

| 编号 | 规则名称 | 级别 | 说明 |
|------|----------|------|------|
| BR-PROJ-001 | 项目唯一性 | P0 | project_code 唯一 |
| BR-PROJ-002 | 项目成员角色 | P1 | pitcher/project_owner/supervisor |
| BR-PROJ-003 | 项目状态机 | P1 | draft → active → suspended → archived（终态: archived）|
| BR-PROJ-004 | 项目负责人 | P0 | owner_id 指向 project_owner 角色 |
| BR-PROJ-005 | 项目预算控制 | P1 | daily_budget / monthly_budget |
| BR-PROJ-006 | 履约状态字段 | P0 | 必须记录 fulfillment_status/fulfillment_reason/fulfilled_at |

#### 4.3.1 BR-PROJ-006 履约状态字段（v4.6 宪法级）

来源：BUSINESS_RULES.md v4.6（宪法级补丁），关联 BI-06

**字段定义**：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `fulfillment_status` | enum | `running` / `fulfilled` |
| `fulfillment_reason` | enum | `spend_exhausted` / `client_stopped` |
| `fulfilled_at` | TIMESTAMPTZ | 履约完成时间 (UTC) |

**状态定义**：

| 状态 | 中文 | 说明 | 是否终态 |
|------|------|------|---------|
| `running` | 履约中 | 项目正在投放 | ❌ |
| `fulfilled` | 已履约 | 履约完成，可确认收入 | ✅ |

**履约结束原因**：

| 原因 | 中文 | 触发条件 |
|------|------|---------|
| `spend_exhausted` | 消耗完毕 | 广告费消耗完 |
| `client_stopped` | 客户喊停 | 甲方明确终止投放 |

**触发条件** (BI-06)：
项目履约完成当且仅当满足以下任一条件：
1. 广告费消耗完 (`spend_exhausted`)
2. 甲方明确喊停 (`client_stopped`)

**终态约束**：
- `fulfilled` 状态不可回退
- `fulfilled` 是结算、收入确认、归档的前置条件

**用途**：
- 驾驶舱"已履约项目数"指标
- 收入确认的前置校验
- 月度结算报表过滤

---

### 4.4 BR-CHAN 渠道管理模块

来源：DATA_SCHEMA.md v5.2 §2.3

| 编号 | 规则名称 | 级别 | 说明 |
|------|----------|------|------|
| BR-CHAN-001 | 渠道唯一性 | P0 | channel_code 唯一 |
| BR-CHAN-002 | 渠道状态 | P1 | active / inactive |
| BR-CHAN-003 | 渠道-账户关联 | P1 | 一个账户属于一个渠道 |

---

### 4.5 BR-ACCT 账户管理模块

来源：DATA_SCHEMA.md v5.2 §2.4

| 编号 | 规则名称 | 级别 | 说明 |
|------|----------|------|------|
| BR-ACCT-001 | 账户唯一性 | P0 | account_id（平台账户ID）唯一 |
| BR-ACCT-002 | 账户分配 | P1 | 户管分配给投手 |
| BR-ACCT-003 | 账户状态机 | P0 | new → testing → active → suspended → dead → archived |
| BR-ACCT-004 | 账户余额 | P0 | 只能通过 ledger_entries 更新 |
| BR-ACCT-005 | 账户-项目关联 | P1 | 多对一 |
| BR-ACCT-006 | 负余额警告 | P1 | Phase 1: 警告不阻断 |

#### 4.5.1 BR-ACCT-003 账户状态机（6 状态）

来源：STATE_MACHINE.md v2.6 §7.1

**状态定义**：

| 状态 | 中文 | 说明 | 是否终态 |
|------|------|------|---------|
| `new` | 新建 | 账户初始状态 | ❌ |
| `testing` | 测试中 | 账户测试阶段 | ❌ |
| `active` | 活跃 | 正常投放中 | ❌ |
| `suspended` | 暂停 | 临时停用 | ❌ |
| `dead` | 死号 | 不可恢复状态 | ✅ |
| `archived` | 已归档 | 历史归档 | ✅ |

**状态流转**：
```
new → testing → active → suspended → dead → archived
                  ↑          ↓
                  ←──────────←
```

> **注意**：dead 状态不可恢复，业务可通过死号迁移 (TRANSFER_SOT.md) 转移至新账户。

---

### 4.6 BR-FIN 财务管理模块

来源：LEDGER_SOT.md v1.1, STATE_MACHINE.md v2.6 §3

| 编号 | 规则名称 | 级别 | 说明 |
|------|----------|------|------|
| BR-FIN-001 | 账本只追加 | P0 | INV-001, 禁止 UPDATE/DELETE |
| BR-FIN-002 | 金额精度 | P0 | Decimal(15,2) |
| BR-FIN-003 | 资金审批流程 | P0 | 项目负责人 → 财务 → 老板 |
| BR-FIN-004 | 充值状态机 | P0 | 7 状态，见下文 |
| BR-FIN-005 | 充值终态 | P0 | completed/rejected/cancelled |
| BR-FIN-006 | 月度锁定 | P1 | 锁定后禁止修改 |
| BR-FIN-007 | 利润计算 | P1 | 收入 - 消耗 - 返点 |

#### 4.6.1 BR-FIN-004 充值状态机 (7 状态)

来源：STATE_MACHINE.md v2.6 §3

```
┌────────────────────────────────────────────────────────────────────────┐
│                        充值状态机 (7 状态)                              │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│   ┌─────────┐  提交   ┌────────────────┐  财务审核  ┌────────────────┐ │
│   │  draft  │ ──────→ │ pending_review │ ─────────→ │ finance_approve│ │
│   └─────────┘         └────────────────┘            └────────────────┘ │
│        │                      │                            │           │
│        │                      │ 拒绝                       │ 老板批准  │
│        │                      ↓                            ↓           │
│        │              ┌────────────┐                ┌──────────┐       │
│        │              │  rejected  │ ← 拒绝 ───────│   paid   │       │
│        │              └────────────┘                └──────────┘       │
│        │                                                   │           │
│        │ 取消                                              │ 确认到账  │
│        ↓                                                   ↓           │
│   ┌────────────┐                                   ┌────────────┐      │
│   │ cancelled  │                                   │ completed  │      │
│   └────────────┘                                   └────────────┘      │
│                                                                        │
│   终态：completed, rejected, cancelled                                 │
└────────────────────────────────────────────────────────────────────────┘
```

**状态说明**：

| 状态 | 中文 | 触发角色 | 说明 |
|------|------|----------|------|
| draft | 草稿 | 投手/户管 | 初始状态，可提交或取消 |
| pending_review | 待数据复核 | - | 等待主管 (data_operator) 复核 |
| finance_approve | 复核通过 | 主管 | 等待财务 (finance) 支付 |
| paid | 已支付 | 财务 | 等待入账确认 |
| completed | 已完成 | 财务/系统 | 终态，已创建账本记录 |
| rejected | 已拒绝 | 主管/财务 | 终态，审核被拒绝 |
| cancelled | 已取消 | 申请人 | 终态，申请人主动取消 |

**角色权限矩阵**：

| 状态转换 | 业务角色 | 技术角色 |
|---------|---------|---------|
| 创建申请 (→ draft) | 投手、户管 | media_buyer, account_manager |
| 提交申请 (draft → pending_review) | 申请人 | 申请人本人 |
| 数据复核 (pending_review → finance_approve/rejected) | 主管 | data_operator |
| 财务支付 (finance_approve → paid/rejected) | 财务 | finance |
| 入账确认 (paid → completed) | 财务/系统 | finance, system |
| 取消申请 (draft/pending_review → cancelled) | 申请人 | 申请人本人, admin |

**职责分离 (SOD)**：
- 申请人 ≠ 复核人（投手/户管不能复核自己的申请）
- 复核人 ≠ 终审人（主管不能执行财务支付）

#### 4.6.2 BR-FIN-008 职责分离原则 (SOD)

来源：MASTER.md v4.4 INV-004, AUTH_SPEC.md v2.0 §5

**核心原则**：

| 原则 | 说明 | 适用场景 |
|------|------|---------|
| 申请人 ≠ 复核人 | 提交申请者不能自我审批 | 充值申请、日报审核 |
| 复核人 ≠ 终审人 | 数据复核与财务终审必须分离 | 充值流程 |
| 操作人 ≠ 审计人 | 执行操作与审计查询需分离 | 审计日志访问 |

**实现代码**：
```python
def validate_sod(applicant_id: UUID, operator_id: UUID, action: str):
    """职责分离校验"""
    if action == "review" and applicant_id == operator_id:
        raise BusinessError(
            code="AUTH-SOD-001",
            message="申请人不能复核自己的申请"
        )
```

---

### 4.7 BR-RECON 对账管理模块

来源：STATE_MACHINE.md v2.6 §4

| 编号 | 规则名称 | 级别 | 说明 |
|------|----------|------|------|
| BR-RECON-001 | 对账批次唯一性 | P0 | 同账户同月唯一 |
| BR-RECON-002 | 对账批次状态机 | P1 | draft → pending_review → approved/needs_adjustment → completed |
| BR-RECON-003 | 对账差异处理 | P1 | Phase 1: 记录不阻断 |
| BR-RECON-004 | 对账锁定 | P0 | completed 后不可修改 |

#### 4.7.1 BR-RECON-002 对账批次状态机（5 状态）

来源：STATE_MACHINE.md v2.6 §11.1

**状态定义**：

| 状态 | 中文 | 触发角色 | 是否终态 |
|------|------|----------|---------|
| `draft` | 草稿 | finance, data_operator | ❌ |
| `pending_review` | 待审核 | finance, data_operator | ❌ |
| `approved` | 已批准 | finance, admin | ❌ |
| `needs_adjustment` | 需调整 | finance, admin | ❌ |
| `completed` | 已完成 | finance, admin | ✅ |

**状态流转**：
```
draft → pending_review → approved → completed
                ↓
          needs_adjustment → approved → completed
```

---

### 4.8 BR-RPT 日报管理模块

来源：STATE_MACHINE.md v2.6 §2

| 编号 | 规则名称 | 级别 | 说明 |
|------|----------|------|------|
| BR-RPT-001 | 日报唯一性 | P0 | 同投手+同账户+同日期唯一 |
| BR-RPT-002 | 日报 8 状态机 | P0 | 见 STATE_MACHINE.md §2.1 |
| BR-RPT-003 | CPL 计算 | P0 | spend / conversions，0转化=null |
| BR-RPT-004 | 零转化处理 | P1 | Phase 1: 警告标记 |
| BR-RPT-005 | 日报锁定 | P0 | final_locked 终态不可回退 |
| BR-RPT-006 | 三数据流 | P0 | raw/real/final 分阶段 |
| BR-RPT-007 | 提交时间 | P1 | T+0 提交 raw 数据 |
| BR-RPT-008 | 审核时间 | P1 | T+1 前完成 trend 审核 |

#### 4.8.1 BR-RPT-003 CPL 计算公式

```
CPL = spend / conversions

边界条件：
- conversions = 0 → CPL = null（非 Infinity）
- spend = 0 → CPL = 0
- 保留 2 位小数
```

**实现代码**：
```python
def calculate_cpl(spend: Decimal, conversions: int) -> Decimal | None:
    if conversions == 0:
        return None  # 不是 float('inf')
    if spend == 0:
        return Decimal("0.00")
    return (spend / conversions).quantize(Decimal("0.01"))
```

#### 4.8.2 BR-RPT-006 三数据流定义

来源：MASTER.md v4.4 §4, DATA_SCHEMA.md v5.2 §3.3.1

**数据流定义**：

| 数据流 | 字段 | 提交者 | 时效性 | 用途 |
|-------|------|--------|--------|------|
| raw | `conversions_raw`, `raw_spend` | 投手 | T+0 23:59前 | 趋势监控、风控检查 |
| real | `real_spend` | 主管 | T+1 12:00前 | 成本核算 |
| final | `conversions_final` | 主管 | T+1 14:00前 | 计费基准 |

**计算公式**：
```
收入 = conversions_final × unit_price
成本 = real_spend + fee
利润 = 收入 - 成本
```

**Phase 1 简化模式**：
- 进粉 SoT：仅使用 `daily_report.conversions`（投手自报值）
- 消耗 SoT：仅使用 `ad_spend_daily.spend`（外部导入）
- 不使用 Phase 2 字段：`conversions_raw`, `conversions_final`, `raw_spend`, `real_spend`

#### 4.8.3 BR-RPT-009 Phase 1 简化模式

来源：STATE_MACHINE.md v2.6 §7.5

**Phase 1 简化版（3 状态快速流转）**：
```
raw_submitted → trend_ok → final_confirmed
```

**特性**：
- ✅ 跳过 trend_pending/trend_flagged/trend_resolved/final_pending
- ✅ 无趋势风控自动阻断
- ✅ 无强制终审（不使用 final_pending 等待态）
- ✅ 数据可见但不阻断

**Phase 2 完整版（8 状态全流程）**：
```
raw_submitted → trend_pending → trend_ok/trend_flagged
→ trend_resolved → final_pending → final_confirmed → final_locked
```

**启用条件**（MASTER.md v4.4 §3.4）：
1. Phase 1 稳定运行 2 个月
2. 日报填报率 ≥ 90%
3. 老板批准启用
4. Feature Flag: `PHASE2_DAILY_REPORT_REQUIRED=true`

---

### 4.9 BR-DATA 数据规则模块

来源：DATA_SCHEMA.md v5.2

| 编号 | 规则名称 | 级别 | 说明 |
|------|----------|------|------|
| BR-DATA-001 | 金额类型 | P0 | Decimal(15,2), 禁止 Float |
| BR-DATA-002 | 时间类型 | P0 | TIMESTAMPTZ, UTC 存储 |
| BR-DATA-003 | 软删除 | P1 | deleted_at 标记 |
| BR-DATA-004 | 审计字段 | P1 | created_at/updated_at/created_by |
| BR-DATA-005 | 主键类型 | P0 | UUID v4 |
| BR-DATA-006 | 明细字段可计算性 | P0 | 汇总字段不落库，由明细聚合 |

#### 4.9.1 BR-DATA-006 明细字段可计算性规则

来源：BUSINESS_RULES.md v4.2（模块补丁）

**核心原则**：不在数据库中存储可由明细计算的汇总字段。

**禁止字段**（汇总字段不落库）：

| 禁止字段 | 正确做法 |
|----------|----------|
| `project.total_revenue` | `SUM(settlement.confirmed_revenue)` |
| `project.total_spend` | `SUM(daily_report.raw_spend)` |
| `settlement.pre_tax_profit` | `confirmed_revenue - total_cost` |

**允许字段**（独立录入）：

| 允许字段 | 说明 |
|----------|------|
| `daily_report.raw_spend` | 投手填报 |
| `settlement.confirmed_revenue` | 财务确认 |
| `ad_spend_daily.spend` | 外部导入 |

**实现建议**：
- 使用 PostgreSQL VIEW 或 SQLAlchemy `@hybrid_property` 计算汇总值
- API 层通过 JOIN + GROUP BY 返回聚合数据

---

### 4.10 BR-STL 结算与履约规则模块（宪法级）

来源：BUSINESS_RULES.md v4.6（宪法级补丁）

> **重要**: 本模块定义系统唯一结算口径，所有收入计算必须基于 `price_rules.type`。

| 编号 | 规则名称 | 级别 | 说明 |
|------|----------|------|------|
| BR-STL-001 | 结算周期 | P0 | 自然月，不跨月 |
| BR-STL-002 | 结算单唯一性 | P0 | project_id + month 唯一 |
| BR-STL-003 | 结算单状态机 | P0 | draft → pending → confirmed → paid |
| BR-STL-004 | 结算定价模式（SoT） | P0 | `price_rules.type` = fixed / tiered / markup |
| BR-STL-005 | 结算收入计算 | P0 | 按模式计算，必须可追溯 |
| BR-STL-006 | 履约完成条件 | P0 | spend_exhausted OR client_stopped |
| BR-STL-007 | 利润计算公式 | P0 | 收入 - 消耗 - 返点 - 服务费 |
| BR-STL-008 | billing_type 废弃 | P0 | 仅作展示映射，不参与计算或审计 |

#### 4.10.1 BR-STL-003 结算单状态机（4 状态）

**状态定义**：

| 状态 | 中文 | 触发角色 | 是否终态 |
|------|------|----------|---------|
| `draft` | 草稿 | finance | ❌ |
| `pending` | 待确认 | finance | ❌ |
| `confirmed` | 已确认 | project_owner | ❌ |
| `paid` | 已回款 | finance | ✅ |

**状态流转**：
```
draft → pending → confirmed → paid
          ↓
       rejected（终态，可选）
```

#### 4.10.2 BR-STL-004 结算定价模式（宪法化）

**唯一结算口径**: `price_rules.type`

> **不变量**: 任何收入计算，必须可追溯到 `price_rules.type` 与其参数版本。

| 模式 | 中文 | 计算公式 | 适用场景 |
|------|------|----------|----------|
| `fixed` | 固定单价 | `conversions_final × unit_price` | 按粉结算 |
| `tiered` | 阶梯定价 | `Σ(区间内 conversions × 对应单价)` | 大客户激励 |
| `markup` | 加价模式 | `real_spend × (1 + markup_rate)` | 服务费模式 |

##### 1️⃣ 固定单价 (fixed)

```
revenue = conversions_final × unit_price
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `unit_price` | Decimal | 单粉价格 |
| `conversions_final` | int | Phase 1: 投手确认数（需标注来源）<br>Phase 2: 必须支持客户确认或规则升级 |

##### 2️⃣ 阶梯定价 (tiered)

```
revenue = Σ(区间内 conversions × 对应单价)
```

**约束**：
- 阶梯区间必须结构化存储（JSON / 表结构）
- ❌ 禁止自然语言或自由文本描述区间

**数据结构示例**：
```json
{
  "type": "tiered",
  "tiers": [
    {"min": 0, "max": 1000, "price": 30.00},
    {"min": 1001, "max": 5000, "price": 28.00},
    {"min": 5001, "max": null, "price": 25.00}
  ]
}
```

##### 3️⃣ 加价模式 (markup)

```
revenue = real_spend × (1 + markup_rate)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `real_spend` | Decimal | SoT 只能来自平台消耗导入 |
| `markup_rate` | Decimal | 加价比例（如 0.20 = 20%） |

#### 4.10.3 BR-STL-008 billing_type 废弃声明

**废弃口径**：
- ❌ `billing_type = per_lead / fee_rate` 不再作为 SoT

**兼容处理**：
- 如需保留 `billing_type`，仅允许作为展示映射字段
- ❌ 禁止参与计算或审计

**映射关系**（仅展示用）：

| billing_type (废弃) | price_rules.type (SoT) |
|--------------------|------------------------|
| `per_lead` | `fixed` |
| `fee_rate` | `markup` |

#### 4.10.4 BR-STL-007 利润计算公式

```
┌─────────────────────────────────────────────────────────────────┐
│                   利润计算公式（v4.6 宪法化）                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   收入 (Revenue) - 基于 price_rules.type                        │
│   ├── fixed:  conversions_final × unit_price                    │
│   ├── tiered: Σ(区间内 conversions × 对应单价)                  │
│   └── markup: real_spend × (1 + markup_rate)                    │
│                                                                 │
│   成本 (Cost)                                                   │
│   ├── 消耗: real_spend（平台导入）                              │
│   ├── 返点: rebate_amount（负数抵扣成本）                       │
│   └── 服务费: service_fee（第三方代理费等）                      │
│                                                                 │
│   毛利 = 收入 - 成本                                            │
│   毛利率 = (毛利 / 收入) × 100%                                 │
│                                                                 │
│   前置条件:                                                     │
│   - 必须履约完成 (fulfilled = true)                             │
│   - 必须收入已确认 (revenue_confirmed = true)                   │
│                                                                 │
│   边界条件:                                                     │
│   - 收入 = 0 时，利润率 = null（显示 '--'）                     │
│   - 成本 > 收入 时，利润率为负（显示红色）                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### 4.11 BR-AR 预收款与回款规则模块（宪法级）

来源：BUSINESS_RULES.md v4.6（宪法级补丁），关联 BI-05

> **重要**: 预收款 ≠ 收入。客户打款在履约完成前一律记为预收款。

| 编号 | 规则名称 | 级别 | 说明 |
|------|----------|------|------|
| BR-AR-001 | 预收款记录 | P0 | 记录客户预付金额，关联 project_id |
| BR-AR-002 | 预收款余额 | P0 | 余额 = 累计预收 - 已履约金额 |
| BR-AR-003 | 回款核销 | P0 | 回款优先冲抵预收款，履约后确认收入 |
| BR-AR-004 | 履约负债 | P0 | 预收款余额 > 0 时存在未履约负债 |
| BR-AR-005 | 预收不足处理 | P0 | Phase 1: 只提示风险（关联 BI-07） |

#### 4.11.1 BR-AR-001 预收款记录

**数据模型**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `project_id` | UUID | 关联项目 |
| `amount` | Decimal(15,2) | 预收金额 |
| `received_at` | TIMESTAMPTZ | 收款日期 |
| `source` | string | 来源（银行转账/支付宝等） |
| `note` | string | 备注 |

**账本记录规则**：
- 入账时创建 `ledger_entry`，类型 = `PREPAYMENT_RECEIVED`
- 关联 `reference_type = 'advance_receipt'`

**核心约束** (BI-05)：
- 履约完成前：客户入金 → `PREPAYMENT_RECEIVED`
- 履约完成后：按结算规则 → `REVENUE_CONFIRMED`

#### 4.11.2 BR-AR-002 预收款余额计算

**核心指标定义** (v4.6)：

| 指标 | 定义 | 说明 |
|------|------|------|
| 累计预收款 | 客户入金事件累计 | `SUM(PREPAYMENT_RECEIVED)` |
| 已履约金额 | Phase 1: 累计平台广告消耗 | `SUM(real_spend)` |
| 预收款余额 | 累计预收款 − 已履约金额 | 关键风控指标 |
| 未履约负债 | 预收款余额（或 预收 − 已确认收入） | 财务报表指标 |

```sql
-- 预收款余额 = 累计预收 - 已履约金额
SELECT
    project_id,
    SUM(CASE WHEN entry_type = 'PREPAYMENT_RECEIVED' THEN amount ELSE 0 END) AS total_prepaid,
    SUM(CASE WHEN entry_type = 'REVENUE_CONFIRMED' THEN amount ELSE 0 END) AS total_confirmed,
    SUM(CASE WHEN entry_type = 'PREPAYMENT_RECEIVED' THEN amount ELSE 0 END)
    - SUM(CASE WHEN entry_type = 'REVENUE_CONFIRMED' THEN amount ELSE 0 END) AS prepayment_balance
FROM ledger_entries
WHERE reference_type IN ('advance_receipt', 'settlement')
GROUP BY project_id;
```

#### 4.11.3 BR-AR-004 履约负债说明

**业务含义**：

| 预收款余额 | 含义 | 说明 |
|-----------|------|------|
| > 0 | 未履约负债 | 客户已付款但服务未完成，存在履约义务 |
| = 0 | 已完成履约 | 无负债 |
| < 0 | 应收账款 | 客户欠款 |

**驾驶舱指标**：
- "累计预收款" = SUM(所有项目的 total_prepaid)
- "预收款余额" = SUM(所有项目的 prepayment_balance)（关键风控）
- "未履约负债" = SUM(预收款余额 > 0 的项目)
- "已确认收入" = SUM(所有项目的 total_confirmed)

#### 4.11.4 BR-AR-005 预收不足处理

来源：BI-07

**Phase 1 处理规则**：

当预收款余额低于安全阈值时：

| 行为 | 允许/禁止 | 说明 |
|------|----------|------|
| 提示风险 | ✅ 允许 | 高亮警告、通知相关人员 |
| 自动停投 | ❌ 禁止 | Phase 1 不阻断 |
| 自动阻断履约 | ❌ 禁止 | Phase 1 不阻断 |
| 自动拒绝充值 | ❌ 禁止 | Phase 1 不阻断 |

**管理动作**：提前与甲方沟通补款

**说明**：
- 公司收支表是现金流 SoT，不是利润表
- 利润只能在履约完成并确认收入后计算

---

## 第5章 规则与测试映射

### 5.1 映射表

| 规则编号 | 测试文件 | 测试用例 |
|----------|----------|----------|
| DEV-001 | `test_models.py` | `test_amount_decimal_precision` |
| DEV-002 | `test_models.py` | `test_datetime_timezone` |
| DEV-003 | `test_services.py` | `test_soft_delete_only` |
| DEV-004 | `test_auth.py` | `test_role_immutable` |
| DEV-005 | `test_state_machine.py` | `test_final_state_no_transition` |
| DEV-006 | `test_ledger.py` | `test_ledger_append_only` |
| BR-RPT-003 | `test_daily_report.py` | `test_cpl_calculation` |
| BR-ACCT-004 | `test_ledger.py` | `test_balance_via_ledger` |

### 5.2 测试覆盖要求

| 规则级别 | 单元测试 | 集成测试 | E2E 测试 |
|----------|----------|----------|----------|
| P0 | 必须 | 必须 | 推荐 |
| P1 | 必须 | 推荐 | 可选 |
| P2 | 推荐 | 可选 | 可选 |

---

## 第6章 术语表

### 6.1 核心业务术语

| 业务术语 | 技术实现 | 说明 |
|----------|----------|------|
| 投手 | `pitcher` | 执行广告投放的操作员 |
| 主管 | `supervisor` | 管理投手的团队负责人 |
| 日报 | `daily_reports` | 每日消耗数据记录 |
| 充值 | `topup_requests` | 账户资金补充申请 |
| CPL | `cost_per_lead` | 每线索成本 = 消耗 / 转化数 |
| ROAS | `return_on_ad_spend` | 广告支出回报率 = 收入 / 消耗 |
| 账本 | `ledger_entries` | 资金流水记录 |
| 草稿 | `draft` | 未提交状态（仅前端使用） |
| 终态 | `final_locked` | 不可回退的最终状态 |

### 6.2 预收款与履约术语 (v4.6 新增)

| 业务术语 | 技术实现 | 说明 |
|----------|----------|------|
| 预收款 | `prepayment` | 甲方在履约完成前支付给公司的资金，性质为未履约负债 |
| 预收款余额 | `prepayment_balance` | 尚未被履约消耗的预收资金 = 累计预收 - 已履约金额 |
| 履约完成 | `fulfilled` | 广告费消耗完 OR 甲方明确喊停 |
| 履约结束原因 | `fulfillment_reason` | `spend_exhausted`（消耗完毕）/ `client_stopped`（客户喊停） |
| 已确认收入 | `confirmed_revenue` | 履约完成后，按结算规则确认的收入 |
| 未履约负债 | `unearned_liability` | 预收款中尚未完成履约的部分 |
| 履约中 | `running` | 项目正在投放，尚未完成履约 |

### 6.3 结算术语 (v4.6 宪法化)

| 业务术语 | 技术实现 | 说明 |
|----------|----------|------|
| 结算定价类型 | `price_rules.type` | 唯一 SoT：`fixed` / `tiered` / `markup` |
| 固定单价 | `fixed` | revenue = conversions × unit_price |
| 阶梯定价 | `tiered` | revenue = Σ(区间内 conversions × 对应单价) |
| 加价模式 | `markup` | revenue = spend × (1 + markup_rate) |

### 6.4 废弃术语 (v4.6)

| 废弃术语 | 原实现 | 替代方案 | 说明 |
|----------|--------|---------|------|
| billing_type | `per_lead` / `fee_rate` | `price_rules.type` | 仅作展示映射，不参与计算或审计 |

---

## 第7章 维护指南

### 7.1 规则变更流程

```
1. 提交 RFC → 2. 技术评审 → 3. 更新 SoT 文档 → 4. 实现 + 测试 → 5. 发布
```

### 7.2 版本兼容性

| 本文档版本 | 兼容的 MASTER.md | 兼容的 STATE_MACHINE.md | 补丁类型 |
|------------|------------------|-------------------------|---------|
| v4.6 | v4.4 | v2.6 | 宪法级 |
| v4.2 | v4.4 | v2.6 | 增量 |
| v4.1 | v4.4 | v2.6 | 增量 |
| v4.0 | v4.4 | v2.6 | 重构 |
| v3.2 | v3.6 | v2.5 | 增量 |

### 7.3 AI 防幻觉原则

来源：MASTER.md v4.4 §7

| 编号 | 原则 | 说明 |
|------|------|------|
| AH-01 | 禁止假设数据一致 | 遇到数据缺失，标记"待确认" |
| AH-02 | 禁止自动做管理裁决 | 禁止生成自动拒绝/暂停/终止代码 |
| AH-03 | 禁止引入 SoT 未定义概念 | 发现缺失 → 停止 → 询问 |
| AH-04 | 必须遵循 Phase 1 软性原则 | Phase 1 = 提示 + 高亮 + 记录 |
| AH-05 | 遇到歧义必须停止并询问 | 停止 → 列出歧义 → 询问 |

---

## 附录 A：页面字段集补丁 (v4.6)

来源：BUSINESS_RULES.md v4.6（宪法级补丁）

> Phase 1 展示层必看字段定义

### A.1 资金总览页面

| 字段 | 类型 | 说明 | 优先级 |
|------|------|------|--------|
| 累计预收款 | Decimal | 客户入金事件累计 | P0 |
| 预收款余额 | Decimal | 累计预收 − 已履约金额（关键风控） | P0 |
| 未履约负债 | Decimal | 预收款余额 > 0 的汇总 | P0 |
| 预收不足提示 | Badge | 仅提示，不阻断（Phase 1） | P1 |

### A.2 项目盈亏/状态页面

| 字段 | 类型 | 说明 | 优先级 |
|------|------|------|--------|
| price_rules.type | enum | 结算定价类型（固定/阶梯/加价） | P0 |
| 履约状态 | enum | `running` / `fulfilled` | P0 |
| 履约结束原因 | enum | `spend_exhausted` / `client_stopped` | P0 |
| 已履约金额 | Decimal | Phase 1: 累计平台广告消耗 | P0 |
| 预收款余额（项目维度） | Decimal | 项目级预收款 − 已履约金额 | P0 |

### A.3 v4.5 兼容说明

| v4.5 概念 | v4.6 定位 | 说明 |
|----------|----------|------|
| 充值/账户余额模型 | 内部资金执行层 | 不再作为经营主线 |
| billing_type | 展示映射字段 | 不参与计算或审计 |

---

## 附录 B：变更历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v4.6 | 2025-12-26 | **宪法级增量补丁**：(1) 统一结算口径为 `price_rules.type` = fixed/tiered/markup；(2) 废弃 `billing_type` 作为 SoT；(3) 新增系统不变量 BI-05/BI-06/BI-07（预收款→履约→收入确认）；(4) 重构 BR-PROJ-006 履约状态字段（running/fulfilled）；(5) 重构 BR-STL 模块宪法化（8 条规则）；(6) 扩展 BR-AR 模块（5 条规则）；(7) 新增页面字段集附录；(8) 术语表分类重组 |
| v4.2 | 2025-12-26 | 新增结算与财务规则：(1) 新增 BR-STL 结算与履约模块（7 条规则）；(2) 新增 BR-AR 预收款与回款模块（4 条规则）；(3) 新增 BR-PROJ-006 履约终态字段规则；(4) 新增 BR-DATA-006 明细字段可计算性规则；(5) 扩展术语表（预收款/预收款余额/履约完成/已确认收入/未履约负债）；(6) 模块总数从 9 扩展到 11 |
| v4.1 | 2025-12-24 | 终审对齐修复：(1) 充值状态机角色描述对齐 STATE_MACHINE.md；(2) 账户状态枚举修正为 6 状态；(3) 项目状态添加 draft，修正 paused→suspended；(4) 对账状态流转对齐 5 状态；(5) 裁判链版本号修正；(6) 新增 SOD 职责分离原则；(7) 新增三数据流详细定义；(8) 新增 Phase 1 简化模式说明 |
| v4.0 | 2025-12-24 | 重构：从索引文档升级为完整业务规则大全；升级 7 角色；添加完整铁律定义 |
| v3.2 | 2025-12-20 | 对齐 MASTER.md v3.6，更新裁判链 |
| v3.1 | 2025-12-15 | 添加 BR-STL 结算模块规则 |
| v3.0 | 2025-12-10 | 初始版本，作为规则索引 |

---

**维护者**: AI 广告代投系统技术团队
**关联文档**:
- `docs/sot/MASTER.md` - 系统宪法
- `docs/sot/STATE_MACHINE.md` - 状态机规范
- `docs/sot/DATA_SCHEMA.md` - 数据模型
- `docs/sot/LEDGER_SOT.md` - 账本规则
