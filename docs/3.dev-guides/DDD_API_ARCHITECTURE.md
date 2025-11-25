# AI 广告代投系统 - DDD + API 优先架构设计

> **文档版本**: v1.1
> **发布日期**: 2025-11-23
> **文档类型**: 🟢 架构设计指南 (DDD + API-First Approach)
> **适用范围**: 系统架构设计、模块重构、新功能开发
> **Architect Persona**: System Architect + Domain Expert
>
> **⚠️ SoT 引用声明**:
> - **数据模型**: 严格遵循 `DATA_SCHEMA.md` v5.2
> - **状态机**: 严格遵循 `STATE_MACHINE.md` v2.6（禁止重复定义状态）
> - **API 规范**: 实际路径以 `API_SOT.md` v2.2 为准（本文档为架构设计参考）
> - **业务规则**: 参考 `BUSINESS_RULES.md` v3.1
> - **错误码**: 引用 `ERROR_CODES_SOT.md` v2.1
>
> **文档定位**: 本文档为 DDD 架构设计指南，展示理想的领域建模方式。
> 实际实现时，数据字段、状态枚举、API 路径必须以对应 SoT 文档为准。

---

## 📌 文档定位

本文档基于 **Domain-Driven Design (DDD)** 和 **API-First** 原则，重新审视 AI 广告代投系统的架构设计，提供：

- ✅ **战略设计 (Strategic Design)**：领域划分、边界上下文、上下文映射
- ✅ **战术设计 (Tactical Design)**：聚合、实体、值对象、领域服务、领域事件
- ✅ **API 架构**：RESTful API 设计、端点规范、资源建模
- ✅ **分层架构**：清晰的职责边界、依赖关系、反腐败层
- ✅ **实施路线图**：从现有架构到 DDD 架构的迁移策略

---

## 1. 战略设计：领域与边界上下文

### 1.1 核心领域 (Core Domain)

**AI 广告代投系统的核心价值主张**：
- **三数据流风控体系** (Raw → Real → Final)：防止投手数据造假
- **双账本财务管理** (PROJECT/SUPPLIER)：精确成本与收入核算
- **状态机驱动审批** (State Machine)：确保数据可审计与终态保护

**核心领域识别**：
1. **Daily Report Management** (日报管理) - 🔴 Core Domain
2. **Ledger & Financial Management** (账本与财务管理) - 🔴 Core Domain
3. **Reconciliation** (对账管理) - 🟡 Supporting Domain

### 1.2 支撑领域 (Supporting Domains)

- **Project Management** (项目管理) - 🟡 Supporting
- **Channel & Account Management** (渠道与账户管理) - 🟡 Supporting
- **Topup Management** (充值管理) - 🟡 Supporting

### 1.3 通用领域 (Generic Subdomains)

- **Authentication & Authorization** (认证授权) - 🔵 Generic (Supabase Auth)
- **Audit Logging** (审计日志) - 🔵 Generic
- **Notification** (通知系统) - 🔵 Generic

---

## 2. 边界上下文 (Bounded Contexts)

### 2.1 边界上下文映射图

```
┌──────────────────────────────────────────────────────────────────────┐
│                        AI 广告代投系统                                 │
└──────────────────────────────────────────────────────────────────────┘

┌─────────────────────────┐         ┌─────────────────────────┐
│  Identity & Access      │◄────────│  User Management        │
│  Context (IAM)          │  ACL    │  Context                │
│                         │         │                         │
│  - Supabase Auth        │         │  - Users                │
│  - JWT Tokens           │         │  - Roles (5 fixed)      │
│  - RBAC                 │         │  - Permissions          │
└─────────────────────────┘         └─────────────────────────┘
           │                                    │
           │ Shared Kernel: User ID (UUID)     │
           ▼                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Campaign Management Context                        │
│  - Projects (国家/地区)                                               │
│  - Channels (渠道)                                                   │
│  - Ad Accounts (广告账户)                                            │
└─────────────────────────────────────────────────────────────────────┘
           │                                    │
           │ Published Language: ProjectID,     │
           │ AdAccountID                        │
           ▼                                    ▼
┌──────────────────────────┐         ┌──────────────────────────┐
│  Daily Report Context    │         │  Financial Context       │
│  (核心领域)               │─────────│  (核心领域)               │
│                          │  OHS    │                          │
│  - DailyReports          │         │  - Ledger                │
│  - Trend Detection       │         │  - Topup Requests        │
│  - State Machine (8)     │         │  - Dual Accounting       │
│  - Three Data Flows      │         │  - Reversal (红冲)       │
│                          │         │                          │
│  Aggregates:             │         │  Aggregates:             │
│  - DailyReport           │         │  - Project (balance)     │
│                          │         │  - LedgerEntry           │
└──────────────────────────┘         └──────────────────────────┘
           │                                    │
           │ Conformist: DailyReport triggers   │
           │ Ledger entry creation              │
           ▼                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│                   Reconciliation Context                              │
│  (支撑领域)                                                            │
│  - Reconciliation Batches                                             │
│  - Reconciliation Details                                             │
│  - Adjustments                                                        │
│                                                                       │
│  Aggregates:                                                          │
│  - ReconciliationBatch                                                │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.2 上下文关系模式

| Context A | Context B | Relationship Pattern | 描述 |
|-----------|-----------|---------------------|------|
| **IAM Context** | User Management | ACL (Anti-Corruption Layer) | IAM 通过 ACL 转换 Supabase Auth 概念到业务用户模型 |
| **Campaign Management** | Daily Report | Published Language | Campaign 发布标准化的 ProjectID, AdAccountID |
| **Campaign Management** | Financial | Published Language | Campaign 发布 ProjectID 供财务上下文使用 |
| **Daily Report** | Financial | OHS (Open Host Service) | Daily Report 提供标准化事件：`DailyReportLocked` |
| **Financial** | Reconciliation | Customer/Supplier | Financial 为上游，Reconciliation 为下游消费者 |

### 2.3 关键术语对照 (Ubiquitous Language)

| 领域术语 | 英文 | 上下文 | 定义 |
|---------|------|--------|------|
| **投手** | Media Buyer | Campaign, Daily Report | 负责广告投放的操作人员 |
| **户管** | Account Manager | Campaign | 负责客户项目管理的人员 |
| **运营** | Data Operator | Daily Report, Financial | 负责数据审核与财务操作的人员 |
| **粉数** | Conversions | Daily Report | 广告转化用户数（新增粉丝数） |
| **原始粉数** | Raw Conversions | Daily Report | 投手提交的未审核粉数 |
| **真实消耗** | Real Spend | Daily Report, Financial | 运营从供应商后台获取的实际消耗金额 |
| **最终粉数** | Final Conversions | Daily Report, Financial | 经过审核确认的计费粉数 |
| **红冲** | Reversal | Financial | 对已锁定数据的冲销修正机制 |
| **趋势风控** | Trend Detection | Daily Report | 检测粉数异常波动的风控机制 |
| **双账本** | Dual Ledger | Financial | PROJECT（收入）和 SUPPLIER（成本）独立核算 |
| **终态保护** | Final State Protection | Daily Report, Financial | 终态数据不可回退，仅可红冲 |
| **职责分离** | Separation of Duties (SOD) | All Contexts | 申请人、审核人、审批人必须不同 |

---

## 3. 战术设计：聚合与实体

### 3.1 Daily Report Context（日报上下文）

#### 3.1.1 聚合：DailyReport

**聚合根**：`DailyReport`

**职责**：
- 管理日报的完整生命周期 (8 状态流转)
- 确保三数据流 (raw/real/final) 的一致性
- 执行趋势风控逻辑
- 防止非法状态流转

**实体与值对象**：

```python
# Aggregate Root
class DailyReport:
    """日报聚合根 - 管理完整的粉数确认流程

    ⚠️ 字段定义严格遵循 DATA_SCHEMA.md v5.2 第3.3.1节
    所有字段与数据库表 daily_reports 完全对齐
    """

    # Identity
    id: DailyReportId (Entity)
    ad_account_id: AdAccountId (Reference)
    report_date: ReportDate (Value Object)

    # Campaign Metadata (Optional - 广告系列元数据)
    campaign_name: Optional[str]
    ad_group_name: Optional[str]
    ad_creative_name: Optional[str]

    # Performance Metrics (Optional - 性能指标)
    impressions: int  # DEFAULT 0
    clicks: int  # DEFAULT 0
    conversions: int  # DEFAULT 0
    new_follows: int  # DEFAULT 0

    # Three Data Flows (Value Objects - 三数据流)
    raw_data_flow: RawDataFlow
        ├─ conversions_raw: int  # 投手提交的原始粉数
        └─ raw_spend: Money  # 投手提交的原始消耗

    real_data_flow: RealDataFlow
        ├─ real_spend: Money  # 运营录入的真实消耗

    final_data_flow: FinalDataFlow
        ├─ conversions_final: int  # 运营确认的最终粉数
        └─ unit_price: Money  # 单粉价格（从项目继承）

    # Calculated Metrics (Optional - 计算指标)
    cpc: Optional[Money]  # Cost Per Click
    cpa: Optional[Money]  # Cost Per Acquisition
    ctr: Optional[float]  # Click-Through Rate (DECIMAL 12,4)
    roi: Optional[float]  # Return on Investment (DECIMAL 12,4)

    # State Machine (状态机 - 严格遵循 STATE_MACHINE.md v2.6 第8章)
    status: DailyReportStatus (Value Object)
        ├─ current_state: Literal[
            "raw_submitted",
            "trend_pending",
            "trend_ok",
            "trend_flagged",
            "trend_resolved",
            "final_pending",
            "final_confirmed",
            "final_locked"
        ]
        ├─ can_transition_to(target_state) -> bool
        └─ validate_transition(target_state) -> Result

    # Trend Detection (趋势风控)
    trend_flag: TrendFlag (Value Object)
        ├─ is_flagged: bool  # DEFAULT 'normal'
        ├─ flag_reason: Optional[str]  # 风控规则触发原因（如"TF-001: 粉数骤降50%"）
        └─ resolution_note: Optional[str]  # 运营复核说明

    # Extended Attributes (扩展属性)
    notes: Optional[str]  # TEXT
    attachments: dict  # JSONB - 附件元数据

    # Audit Trail (审计字段)
    audit_trail: AuditTrail (Entity Collection)
    created_by: UserId  # UUID FK → users.id
    updated_by: UserId  # UUID FK → users.id
    submitted_by: UserId  # UUID FK → users.id
    audit_user_id: Optional[UserId]  # UUID FK → users.id

    created_at: datetime  # TIMESTAMPTZ
    updated_at: datetime  # TIMESTAMPTZ
    submitted_at: Optional[datetime]  # TIMESTAMPTZ
    approved_at: Optional[datetime]  # TIMESTAMPTZ
    final_locked_at: Optional[datetime]  # 计费锁定时间戳

    # Domain Methods
    def submit_raw_data(
        self,
        conversions_raw: int,
        raw_spend: Money,
        submitted_by: UserId
    ) -> Result[DomainEvent]

    def perform_trend_detection(
        self,
        trend_rule: TrendDetectionRule
    ) -> Result[TrendDetectionResult]

    def record_real_spend(
        self,
        real_spend: Money,
        recorded_by: UserId
    ) -> Result[DomainEvent]

    def confirm_final_conversions(
        self,
        conversions_final: int,
        confirmed_by: UserId
    ) -> Result[DomainEvent]

    def lock_for_billing(
        self,
        locked_by: UserId
    ) -> Result[DomainEvent]  # Emits: DailyReportLockedEvent
```

**领域事件**：

```python
@dataclass(frozen=True)
class DailyReportLockedEvent(DomainEvent):
    """日报锁定事件 - 触发账本记录创建

    ⚠️ 状态流转严格遵循 STATE_MACHINE.md v2.6 第8章
    触发条件: status = 'final_confirmed' → 'final_locked'
    参考: STATE_MACHINE.md 第8.2节 - 状态流转规则
    """
    daily_report_id: DailyReportId
    ad_account_id: AdAccountId
    project_id: ProjectId
    report_date: date

    # Revenue Calculation
    conversions_final: int
    unit_price: Money
    revenue_amount: Money  # = conversions_final × unit_price

    # Cost Calculation
    real_spend: Money
    fee: Money
    cost_amount: Money  # = real_spend + fee

    locked_at: datetime
    locked_by: UserId
```

#### 3.1.2 领域服务：TrendDetectionService

```python
class TrendDetectionService:
    """趋势风控领域服务"""

    def detect_trend_anomaly(
        self,
        daily_report: DailyReport,
        historical_reports: List[DailyReport],
        rules: TrendDetectionRules
    ) -> TrendDetectionResult:
        """
        执行三大风控规则：
        - TF-001: 连续下降检测
        - TF-002: 单日异常波动
        - TF-003: 低转化率预警
        """
        pass
```

---

### 3.2 Financial Context（财务上下文）

#### 3.2.1 聚合：Project (Balance Management)

**聚合根**：`Project`

**职责**：
- 管理项目余额 (PROJECT Ledger)
- 防止余额不足
- 记录充值与计费操作

```python
class Project:
    """项目聚合根 - 管理项目余额"""

    # Identity
    id: ProjectId
    name: ProjectName
    country: Country

    # Balance (核心不变量)
    balance: Money  # 必须 >= 0

    # Status
    status: ProjectStatus  # draft → active → suspended → archived

    # Domain Methods
    def topup(
        self,
        amount: Money,
        topup_request_id: TopupRequestId,
        approved_by: UserId
    ) -> Result[DomainEvent]:
        """充值 - 创建 RECHARGE 类型 Ledger Entry"""
        if amount <= Money.zero():
            return Err("充值金额必须大于0")

        self.balance += amount
        return Ok(ProjectTopupEvent(...))

    def deduct_revenue(
        self,
        revenue_amount: Money,
        daily_report_id: DailyReportId,
        billing_at: datetime
    ) -> Result[DomainEvent]:
        """扣费 - 创建 REVENUE 类型 Ledger Entry"""
        self.balance -= revenue_amount
        return Ok(ProjectRevenueDeductedEvent(...))

    def reverse_transaction(
        self,
        original_entry_id: LedgerEntryId,
        reversal_amount: Money,
        reversal_reason: str,
        reversed_by: UserId
    ) -> Result[DomainEvent]:
        """红冲 - 创建 REVERSAL 类型 Ledger Entry"""
        pass
```

#### 3.2.2 聚合：Supplier (Cost Management)

```python
class Supplier:
    """供应商聚合根 - 管理供应商余额"""

    # Identity
    id: SupplierId
    name: SupplierName

    # Balance (核心不变量)
    balance: Money  # 可以为负数（欠款）

    # Domain Methods
    def topup(
        self,
        amount: Money,
        topup_request_id: TopupRequestId
    ) -> Result[DomainEvent]:
        """充值 - 创建 RECHARGE 类型 Ledger Entry"""
        pass

    def deduct_cost(
        self,
        cost_amount: Money,
        daily_report_id: DailyReportId
    ) -> Result[DomainEvent]:
        """扣费 - 创建 COST 类型 Ledger Entry"""
        pass

    def transfer_balance(
        self,
        to_supplier: 'Supplier',
        transfer_amount: Money,
        transfer_request_id: TransferRequestId
    ) -> Result[DomainEvent]:
        """迁移余额 - 创建 TRANSFER_OUT 和 TRANSFER_IN"""
        if self.id != to_supplier.id:
            return Err("仅支持同供应商内迁移")

        self.balance -= transfer_amount
        to_supplier.balance += transfer_amount
        return Ok(SupplierBalanceTransferredEvent(...))
```

#### 3.2.3 实体：LedgerEntry

**注意**：`LedgerEntry` 是 **实体**，不是聚合根。它通过 `Project` 或 `Supplier` 聚合根创建。

```python
class LedgerEntry:
    """账本记录实体 - 不可变记录"""

    # Identity
    id: LedgerEntryId

    # Ledger Type (核心分类)
    ledger_type: LedgerType  # PROJECT | SUPPLIER

    # Entry Type
    entry_type: EntryType
        # PROJECT: RECHARGE, REVENUE, REVERSAL
        # SUPPLIER: RECHARGE, COST, TRANSFER_IN, TRANSFER_OUT, REVERSAL

    # Ownership
    project_id: Optional[ProjectId]  # ledger_type=PROJECT 时必填
    supplier_id: Optional[SupplierId]  # ledger_type=SUPPLIER 时必填

    # Transaction
    amount: Money  # 借方为正，贷方为负
    balance_before: Money
    balance_after: Money

    # Traceability
    related_entity_type: str  # DailyReport, TopupRequest, TransferRequest
    related_entity_id: str

    # Immutability
    created_at: datetime
    created_by: UserId
```

---

### 3.3 Reconciliation Context（对账上下文）

#### 3.3.1 聚合：ReconciliationBatch

```python
class ReconciliationBatch:
    """对账批次聚合根"""

    # Identity
    id: ReconciliationBatchId
    batch_no: BatchNumber

    # Period
    reconciliation_period: ReconciliationPeriod (Value Object)
        ├─ start_date: date
        └─ end_date: date

    # Details (Entity Collection)
    details: List[ReconciliationDetail]

    # Status
    status: ReconciliationStatus
        # draft → pending_review → approved → needs_adjustment → completed

    # Domain Methods
    def add_detail(
        self,
        ad_account_id: AdAccountId,
        report_date: date,
        system_spend: Money,
        external_spend: Money
    ) -> Result:
        """添加对账明细"""
        detail = ReconciliationDetail.create(...)
        self.details.append(detail)
        return Ok()

    def submit_for_review(
        self,
        submitted_by: UserId
    ) -> Result[DomainEvent]:
        """提交审核 - SOD 检查"""
        pass

    def approve(
        self,
        approved_by: UserId
    ) -> Result[DomainEvent]:
        """批准对账 - 创建调整单"""
        if any(d.has_difference() for d in self.details):
            return Err("存在差异明细，需要调整")
        return Ok(ReconciliationBatchApprovedEvent(...))
```

---

## 4. API 架构设计

### 4.1 RESTful API 设计原则

#### 4.1.1 资源建模

**核心原则**：
1. **资源即聚合根**：每个 API 资源对应一个聚合根或实体
2. **子资源嵌套**：聚合内的实体通过嵌套路由访问
3. **操作即领域方法**：POST/PUT/PATCH 对应聚合的领域方法

**资源层级**：

```
/api/v1/projects/{project_id}
    └─ /ledger-entries           # 项目账本记录（只读）
    └─ /topup-requests            # 充值申请

/api/v1/ad-accounts/{ad_account_id}
    └─ /daily-reports              # 日报（聚合根）
        └─ /{report_date}/submit-raw        # 领域方法
        └─ /{report_date}/record-real       # 领域方法
        └─ /{report_date}/confirm-final     # 领域方法
        └─ /{report_date}/lock              # 领域方法

/api/v1/suppliers/{supplier_id}
    └─ /ledger-entries             # 供应商账本记录（只读）
    └─ /transfer-requests          # 余额迁移申请

/api/v1/reconciliation-batches
    └─ /{batch_id}/details          # 对账明细
    └─ /{batch_id}/submit           # 提交审核
    └─ /{batch_id}/approve          # 批准
```

#### 4.1.2 HTTP 方法映射

| HTTP Method | Idempotent | 用途 | 聚合操作 |
|-------------|-----------|------|---------|
| **GET** | ✅ Yes | 查询聚合状态 | 无副作用 |
| **POST** | ❌ No | 创建聚合、执行领域方法 | 创建新聚合根或触发领域方法 |
| **PUT** | ✅ Yes | 完整替换资源 | 少用（DDD 中不推荐） |
| **PATCH** | ❌ No | 部分更新资源 | 触发聚合的领域方法 |
| **DELETE** | ✅ Yes | 删除资源 | 归档/软删除（禁止物理删除） |

#### 4.1.3 端点命名规范

**领域方法端点**：

| 领域方法 | HTTP Method | 端点 | 请求体 |
|---------|------------|------|--------|
| 提交原始粉数 | POST | `/ad-accounts/{ad_account_id}/daily-reports/{report_date}/submit-raw` | `{conversions_raw, raw_spend}` |
| 录入真实消耗 | POST | `/ad-accounts/{ad_account_id}/daily-reports/{report_date}/record-real` | `{real_spend}` |
| 确认最终粉数 | POST | `/ad-accounts/{ad_account_id}/daily-reports/{report_date}/confirm-final` | `{conversions_final}` |
| 锁定计费 | POST | `/ad-accounts/{ad_account_id}/daily-reports/{report_date}/lock` | `{}` |

**查询端点**：

| 查询目的 | HTTP Method | 端点 | 查询参数 |
|---------|------------|------|---------|
| 获取单个日报 | GET | `/ad-accounts/{ad_account_id}/daily-reports/{report_date}` | - |
| 获取日报列表 | GET | `/ad-accounts/{ad_account_id}/daily-reports` | `?status=final_locked&page=1` |
| 获取项目余额 | GET | `/projects/{project_id}` | - |
| 获取账本流水 | GET | `/projects/{project_id}/ledger-entries` | `?entry_type=REVENUE&page=1` |

### 4.2 API 端点设计 (Domain-Driven)

> **⚠️ 重要说明**:
> 本节展示的是 **DDD 理想架构设计** 中的嵌套路由风格（资源层级化）。
> **实际项目的 API 路径规范以 `API_SOT.md` v2.2 为准**（采用平面化路由）。
>
> **路径对照表**:
> | DDD 理想设计 | API_SOT.md 实际路径 |
> |-------------|-------------------|
> | `POST /api/v1/ad-accounts/{id}/daily-reports/{date}/submit-raw` | `POST /api/v1/daily-reports` |
> | `POST /api/v1/ad-accounts/{id}/daily-reports/{date}/record-real` | `PUT /api/v1/daily-reports/{report_id}/real-spend` |
> | `POST /api/v1/ad-accounts/{id}/daily-reports/{date}/confirm-final` | `POST /api/v1/daily-reports/{report_id}/final-confirm` |
> | `POST /api/v1/ad-accounts/{id}/daily-reports/{date}/lock` | `POST /api/v1/daily-reports/{report_id}/final-lock` |
>
> 如需采用嵌套路由，需同步更新 API_SOT.md 并重新发版。

#### 4.2.1 Daily Report API

**聚合：DailyReport**

```yaml
# 提交原始粉数（投手操作）
# DDD 设计路径（示例）- 实际路径见 API_SOT.md
POST /api/v1/ad-accounts/{ad_account_id}/daily-reports/{report_date}/submit-raw
Authorization: Bearer {token}
X-Require-Role: media_buyer

Request:
{
  "conversions_raw": 150,
  "raw_spend": "1200.00"
}

Response (201 Created):
{
  "success": true,
  "data": {
    "id": 12345,
    "ad_account_id": 1001,
    "report_date": "2025-11-22",
    "status": "trend_pending",
    "conversions_raw": 150,
    "raw_spend": "1200.00",
    "conversions_final": null,
    "real_spend": null,
    "created_at": "2025-11-22T23:58:00Z",
    "updated_at": "2025-11-22T23:58:00Z"
  }
}

Domain Event Emitted:
- RawDataSubmittedEvent
```

```yaml
# 录入真实消耗（运营操作）
POST /api/v1/ad-accounts/{ad_account_id}/daily-reports/{report_date}/record-real
Authorization: Bearer {token}
X-Require-Role: data_operator

Request:
{
  "real_spend": "1150.00"
}

Response (200 OK):
{
  "success": true,
  "data": {
    "id": 12345,
    "status": "final_pending",
    "real_spend": "1150.00",
    "updated_at": "2025-11-23T10:30:00Z"
  }
}

Domain Event Emitted:
- RealSpendRecordedEvent
```

```yaml
# 确认最终粉数（运营操作）
POST /api/v1/ad-accounts/{ad_account_id}/daily-reports/{report_date}/confirm-final
Authorization: Bearer {token}
X-Require-Role: data_operator

Request:
{
  "conversions_final": 148
}

Response (200 OK):
{
  "success": true,
  "data": {
    "id": 12345,
    "status": "final_confirmed",
    "conversions_final": 148,
    "updated_at": "2025-11-23T13:45:00Z"
  }
}

Domain Event Emitted:
- FinalConversionsConfirmedEvent
```

```yaml
# 锁定计费（系统自动或运营手动）
POST /api/v1/ad-accounts/{ad_account_id}/daily-reports/{report_date}/lock
Authorization: Bearer {token}
X-Require-Role: data_operator, admin

Request: {}

Response (200 OK):
{
  "success": true,
  "data": {
    "id": 12345,
    "status": "final_locked",
    "final_locked_at": "2025-11-23T14:00:00Z",
    "ledger_entries_created": {
      "project_revenue_entry_id": 5001,
      "supplier_cost_entry_id": 5002
    }
  }
}

Domain Event Emitted:
- DailyReportLockedEvent (触发 Financial Context)
```

#### 4.2.2 Financial API

**聚合：Project, Supplier**

```yaml
# 项目充值
POST /api/v1/projects/{project_id}/topup
Authorization: Bearer {token}
X-Require-Role: finance

Request:
{
  "topup_request_id": "uuid-1234",
  "amount": "50000.00",
  "payment_method": "BANK_TRANSFER",
  "payment_proof_url": "https://..."
}

Response (201 Created):
{
  "success": true,
  "data": {
    "project_id": 101,
    "balance_before": "10000.00",
    "balance_after": "60000.00",
    "ledger_entry_id": 6001,
    "created_at": "2025-11-23T15:00:00Z"
  }
}

Domain Event Emitted:
- ProjectToppedUpEvent
```

```yaml
# 供应商余额迁移
POST /api/v1/suppliers/{supplier_id}/transfer
Authorization: Bearer {token}
X-Require-Role: account_manager, admin

Request:
{
  "from_ad_account_id": 2001,
  "to_ad_account_id": 2002,
  "transfer_amount": "5000.00",
  "transfer_reason": "死号迁移",
  "request_no": "TR-20251123-001"
}

Response (201 Created):
{
  "success": true,
  "data": {
    "transfer_request_id": "uuid-5678",
    "status": "draft",
    "from_balance": "15000.00",
    "to_balance": "3000.00",
    "created_at": "2025-11-23T16:00:00Z"
  }
}

Domain Event Emitted:
- TransferRequestCreatedEvent
```

```yaml
# 红冲（Reversal）
POST /api/v1/ledger-entries/{entry_id}/reverse
Authorization: Bearer {token}
X-Require-Role: finance, admin

Request:
{
  "reversal_reason": "粉数统计错误",
  "reversal_amount": "1480.00"
}

Response (201 Created):
{
  "success": true,
  "data": {
    "original_entry_id": 5001,
    "reversal_entry_id": 5003,
    "reversal_type": "REVERSAL",
    "amount": "-1480.00",
    "balance_after_reversal": "58520.00",
    "created_at": "2025-11-23T17:00:00Z"
  }
}

Domain Event Emitted:
- LedgerEntryReversedEvent
```

#### 4.2.3 Reconciliation API

```yaml
# 创建对账批次
POST /api/v1/reconciliation-batches
Authorization: Bearer {token}
X-Require-Role: data_operator

Request:
{
  "batch_no": "RECON-202511-001",
  "reconciliation_period": {
    "start_date": "2025-11-01",
    "end_date": "2025-11-22"
  },
  "channel_id": "uuid-channel-1"
}

Response (201 Created):
{
  "success": true,
  "data": {
    "id": 1001,
    "batch_no": "RECON-202511-001",
    "status": "draft",
    "total_system_spend": "0.00",
    "total_external_spend": "0.00",
    "total_difference": "0.00",
    "created_at": "2025-11-23T18:00:00Z"
  }
}
```

```yaml
# 批准对账批次
POST /api/v1/reconciliation-batches/{batch_id}/approve
Authorization: Bearer {token}
X-Require-Role: data_operator, admin

Request: {}

Response (200 OK):
{
  "success": true,
  "data": {
    "id": 1001,
    "status": "completed",
    "approved_by": "uuid-user-1",
    "approved_at": "2025-11-23T19:00:00Z",
    "adjustments_created": 0
  }
}

Domain Event Emitted:
- ReconciliationBatchApprovedEvent
```

### 4.3 API 响应格式（Envelope Pattern）

**成功响应**：

```json
{
  "success": true,
  "data": {
    // 聚合根状态或查询结果
  },
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 150,
    "total_pages": 8
  }
}
```

**错误响应**：

```json
{
  "success": false,
  "error": {
    "code": "DAILY_REPORT_404",
    "message": "指定日期的日报不存在",
    "details": {
      "ad_account_id": 1001,
      "report_date": "2025-11-22"
    }
  },
  "request_id": "uuid-request-1234",
  "timestamp": "2025-11-23T20:00:00Z"
}
```

---

## 5. 分层架构

### 5.1 洋葱架构 (Onion Architecture)

```
┌────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                     │
│  - FastAPI Routers (HTTP)                                   │
│  - SQLAlchemy ORM                                           │
│  - Supabase Auth Client                                     │
│  - Redis (Cache)                                            │
└────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│  - Application Services (Use Cases)                         │
│  - DTO Transformers (Schema → Domain, Domain → DTO)        │
│  - Event Handlers                                           │
│  - Command Handlers                                         │
└────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────┐
│                      Domain Layer                           │
│  - Aggregates (DailyReport, Project, Supplier, etc.)       │
│  - Entities (LedgerEntry, AuditLog, etc.)                  │
│  - Value Objects (Money, ReportDate, Status, etc.)         │
│  - Domain Services (TrendDetectionService, etc.)           │
│  - Domain Events                                            │
│  - Repository Interfaces (Port)                             │
└────────────────────────────────────────────────────────────┘
```

### 5.2 依赖规则

1. **Domain Layer** 不依赖任何外层（Pure Python，无框架依赖）
2. **Application Layer** 仅依赖 Domain Layer
3. **Infrastructure Layer** 实现 Domain Layer 定义的接口（Repository）

**示例：Repository Pattern**

```python
# domain/repositories/daily_report_repository.py (Port)
from abc import ABC, abstractmethod
from typing import Optional
from domain.aggregates.daily_report import DailyReport, DailyReportId

class DailyReportRepository(ABC):
    """日报仓储接口 - 由 Infrastructure Layer 实现"""

    @abstractmethod
    def get_by_id(self, daily_report_id: DailyReportId) -> Optional[DailyReport]:
        pass

    @abstractmethod
    def get_by_account_and_date(
        self,
        ad_account_id: int,
        report_date: date
    ) -> Optional[DailyReport]:
        pass

    @abstractmethod
    def save(self, daily_report: DailyReport) -> None:
        pass

    @abstractmethod
    def get_historical_reports(
        self,
        ad_account_id: int,
        start_date: date,
        end_date: date
    ) -> List[DailyReport]:
        pass
```

```python
# infrastructure/repositories/sqlalchemy_daily_report_repository.py (Adapter)
from sqlalchemy.orm import Session
from domain.repositories.daily_report_repository import DailyReportRepository
from domain.aggregates.daily_report import DailyReport
from backend.models.workflow.daily_report import DailyReportModel  # ORM Model

class SqlAlchemyDailyReportRepository(DailyReportRepository):
    """SQLAlchemy 实现的日报仓储"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_account_and_date(
        self,
        ad_account_id: int,
        report_date: date
    ) -> Optional[DailyReport]:
        orm_model = self.db.query(DailyReportModel).filter_by(
            ad_account_id=ad_account_id,
            report_date=report_date
        ).first()

        if not orm_model:
            return None

        # ORM Model → Domain Aggregate
        return self._to_domain(orm_model)

    def save(self, daily_report: DailyReport) -> None:
        # Domain Aggregate → ORM Model
        orm_model = self._to_orm(daily_report)
        self.db.merge(orm_model)
        self.db.commit()

    def _to_domain(self, orm_model: DailyReportModel) -> DailyReport:
        """ORM Model 转换为 Domain Aggregate"""
        pass

    def _to_orm(self, daily_report: DailyReport) -> DailyReportModel:
        """Domain Aggregate 转换为 ORM Model"""
        pass
```

### 5.3 Application Service Example

```python
# application/services/daily_report_service.py
from domain.repositories.daily_report_repository import DailyReportRepository
from domain.aggregates.daily_report import DailyReport
from domain.services.trend_detection_service import TrendDetectionService
from domain.events.domain_events import DomainEvent
from application.dto.daily_report_dto import SubmitRawDataRequest

class DailyReportApplicationService:
    """日报应用服务 - 协调领域对象完成用例"""

    def __init__(
        self,
        daily_report_repo: DailyReportRepository,
        trend_detection_service: TrendDetectionService,
        event_publisher: EventPublisher
    ):
        self.daily_report_repo = daily_report_repo
        self.trend_detection_service = trend_detection_service
        self.event_publisher = event_publisher

    def submit_raw_data(
        self,
        ad_account_id: int,
        report_date: date,
        request: SubmitRawDataRequest,
        submitted_by: UUID
    ) -> Result[DailyReport]:
        """提交原始粉数 - Use Case"""

        # 1. 查找或创建聚合
        daily_report = self.daily_report_repo.get_by_account_and_date(
            ad_account_id, report_date
        )

        if not daily_report:
            daily_report = DailyReport.create_new(
                ad_account_id=ad_account_id,
                report_date=report_date
            )

        # 2. 执行领域方法
        result = daily_report.submit_raw_data(
            conversions_raw=request.conversions_raw,
            raw_spend=Money(request.raw_spend),
            submitted_by=submitted_by
        )

        if result.is_err():
            return result

        # 3. 趋势检测（领域服务）
        historical_reports = self.daily_report_repo.get_historical_reports(
            ad_account_id,
            report_date - timedelta(days=7),
            report_date - timedelta(days=1)
        )

        trend_result = self.trend_detection_service.detect_trend_anomaly(
            daily_report,
            historical_reports,
            TrendDetectionRules.default()
        )

        if trend_result.is_flagged:
            daily_report.mark_as_flagged(trend_result.reason)

        # 4. 持久化聚合
        self.daily_report_repo.save(daily_report)

        # 5. 发布领域事件
        domain_event = result.unwrap()
        self.event_publisher.publish(domain_event)

        return Ok(daily_report)
```

---

## 6. 领域事件与事件驱动架构

### 6.1 领域事件定义

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import uuid4

class DomainEvent(Protocol):
    """领域事件基类"""
    event_id: str
    occurred_at: datetime
    aggregate_id: str

@dataclass(frozen=True)
class DailyReportLockedEvent(DomainEvent):
    """日报锁定事件 - 核心业务事件"""
    event_id: str
    occurred_at: datetime

    # Aggregate Identity
    daily_report_id: int
    ad_account_id: int
    project_id: int
    report_date: date

    # Revenue Data
    conversions_final: int
    unit_price: str  # Money as string
    revenue_amount: str

    # Cost Data
    real_spend: str
    fee: str
    cost_amount: str

    # Audit
    locked_by: str  # UUID

    @classmethod
    def create(cls, daily_report: DailyReport) -> 'DailyReportLockedEvent':
        return cls(
            event_id=str(uuid4()),
            occurred_at=datetime.utcnow(),
            daily_report_id=daily_report.id,
            ad_account_id=daily_report.ad_account_id,
            project_id=daily_report.project_id,
            report_date=daily_report.report_date,
            conversions_final=daily_report.conversions_final,
            unit_price=str(daily_report.unit_price),
            revenue_amount=str(daily_report.calculate_revenue()),
            real_spend=str(daily_report.real_spend),
            fee=str(daily_report.fee),
            cost_amount=str(daily_report.calculate_cost()),
            locked_by=str(daily_report.locked_by)
        )
```

### 6.2 事件处理器

```python
# application/event_handlers/daily_report_locked_handler.py
from domain.events.daily_report_events import DailyReportLockedEvent
from domain.repositories.ledger_repository import LedgerRepository
from domain.aggregates.project import Project
from domain.aggregates.supplier import Supplier

class DailyReportLockedEventHandler:
    """日报锁定事件处理器 - 创建账本记录"""

    def __init__(
        self,
        project_repo: ProjectRepository,
        supplier_repo: SupplierRepository,
        ledger_repo: LedgerRepository
    ):
        self.project_repo = project_repo
        self.supplier_repo = supplier_repo
        self.ledger_repo = ledger_repo

    def handle(self, event: DailyReportLockedEvent) -> None:
        """处理日报锁定事件"""

        # 1. 获取项目聚合
        project = self.project_repo.get_by_id(event.project_id)

        # 2. 执行扣费（领域方法）
        revenue_amount = Money(event.revenue_amount)
        project.deduct_revenue(
            revenue_amount=revenue_amount,
            daily_report_id=event.daily_report_id,
            billing_at=event.occurred_at
        )

        # 3. 持久化项目聚合
        self.project_repo.save(project)

        # 4. 获取供应商聚合
        ad_account = self.ad_account_repo.get_by_id(event.ad_account_id)
        supplier = self.supplier_repo.get_by_id(ad_account.supplier_id)

        # 5. 执行成本扣费（领域方法）
        cost_amount = Money(event.cost_amount)
        supplier.deduct_cost(
            cost_amount=cost_amount,
            daily_report_id=event.daily_report_id
        )

        # 6. 持久化供应商聚合
        self.supplier_repo.save(supplier)
```

---

## 7. 实施路线图

### 7.1 Phase 1: 基础设施准备（1-2 周）

**目标**：建立 DDD 基础设施

- ✅ 创建 `domain/` 目录结构
- ✅ 定义值对象基类 (`Money`, `Status`, etc.)
- ✅ 定义聚合根基类 (`AggregateRoot`)
- ✅ 定义仓储接口 (`Repository` Protocol)
- ✅ 实现事件发布器 (`EventPublisher`)

**产出**：
- `backend/domain/value_objects/`
- `backend/domain/aggregates/`
- `backend/domain/repositories/`
- `backend/domain/events/`

### 7.2 Phase 2: Daily Report 重构（2-3 周）

**目标**：将 Daily Report 模块重构为 DDD 架构

- ✅ 创建 `DailyReport` 聚合根
- ✅ 实现8状态状态机领域逻辑
- ✅ 实现趋势检测领域服务
- ✅ 创建 `DailyReportRepository` 接口与实现
- ✅ 重构 API 端点（从 CRUD 到领域方法）
- ✅ 实现领域事件发布

**产出**：
- `backend/domain/aggregates/daily_report.py`
- `backend/domain/services/trend_detection_service.py`
- `backend/application/services/daily_report_service.py`
- `backend/infrastructure/repositories/sqlalchemy_daily_report_repository.py`

### 7.3 Phase 3: Financial Context 重构（2-3 周）

**目标**：重构账本与财务管理为 DDD 架构

- ✅ 创建 `Project` 和 `Supplier` 聚合根
- ✅ 实现双账本逻辑
- ✅ 实现红冲机制
- ✅ 实现 `DailyReportLockedEvent` 事件处理
- ✅ 重构 Topup API
- ✅ 重构 Transfer API

**产出**：
- `backend/domain/aggregates/project.py`
- `backend/domain/aggregates/supplier.py`
- `backend/domain/entities/ledger_entry.py`
- `backend/application/event_handlers/daily_report_locked_handler.py`

### 7.4 Phase 4: Reconciliation & Other Contexts（1-2 周）

**目标**：重构对账与其他支撑模块

- ✅ 创建 `ReconciliationBatch` 聚合根
- ✅ 重构对账 API
- ✅ 重构 Campaign Management Context（Projects, Channels, AdAccounts）

### 7.5 Phase 5: 优化与测试（1-2 周）

**目标**：完善测试与性能优化

- ✅ 编写领域模型单元测试
- ✅ 编写应用服务集成测试
- ✅ 编写 API E2E 测试
- ✅ 性能优化（Repository 缓存、Event 批处理）
- ✅ 文档更新

---

## 8. DDD 实践建议

### 8.1 领域模型纯粹性

**DO**：
- ✅ Domain Layer 不依赖框架（FastAPI, SQLAlchemy, etc.）
- ✅ 使用原生 Python 类型（`dataclass`, `Enum`, `Protocol`）
- ✅ 领域逻辑封装在聚合根与领域服务中

**DON'T**：
- ❌ 不要在领域模型中导入 ORM 模型
- ❌ 不要在领域模型中使用 Pydantic `BaseModel`
- ❌ 不要在领域模型中直接访问数据库

### 8.2 聚合边界设计

**核心原则**：
1. **一个聚合一个事务边界**：聚合内的修改在单个事务中完成
2. **聚合间通过ID引用**：不要在聚合中嵌套其他聚合对象
3. **小聚合原则**：聚合尽可能小，包含必须保证一致性的最小单元

**示例**：

```python
# ✅ Good: 聚合间通过 ID 引用
class DailyReport:
    id: int
    ad_account_id: int  # Reference to AdAccount Aggregate
    project_id: int     # Reference to Project Aggregate

# ❌ Bad: 聚合中嵌套其他聚合
class DailyReport:
    id: int
    ad_account: AdAccount  # 违反聚合边界
    project: Project       # 违反聚合边界
```

### 8.3 领域事件使用场景

**何时使用领域事件**：
1. ✅ 跨聚合的最终一致性（如 `DailyReportLocked` → 创建 Ledger Entry）
2. ✅ 跨边界上下文的集成（如 Daily Report Context → Financial Context）
3. ✅ 审计日志记录

**何时不使用领域事件**：
1. ❌ 聚合内部的状态变更（直接调用领域方法即可）
2. ❌ 简单的 CRUD 操作

---

## 9. 附录

### 9.1 DDD 术语对照表

| DDD Term | 中文 | AI 广告系统示例 |
|----------|------|----------------|
| **Bounded Context** | 边界上下文 | Daily Report Context, Financial Context |
| **Aggregate** | 聚合 | DailyReport, Project, Supplier |
| **Aggregate Root** | 聚合根 | DailyReport (管理粉数确认流程) |
| **Entity** | 实体 | LedgerEntry, AuditLog |
| **Value Object** | 值对象 | Money, ReportDate, Status |
| **Domain Service** | 领域服务 | TrendDetectionService |
| **Domain Event** | 领域事件 | DailyReportLockedEvent |
| **Repository** | 仓储 | DailyReportRepository |
| **Application Service** | 应用服务 | DailyReportApplicationService |
| **Ubiquitous Language** | 通用语言 | 粉数、真实消耗、双账本 |
| **Anti-Corruption Layer** | 防腐层 | IAM Context ACL (Supabase Auth → User Model) |

### 9.2 推荐阅读

- **《领域驱动设计》** - Eric Evans
- **《实现领域驱动设计》** - Vaughn Vernon
- **《Clean Architecture》** - Robert C. Martin

---

**文档结束**

如有疑问，请联系系统架构团队或查阅 [MASTER_SPEC.md](../1.overview/MASTER_SPEC.md)
