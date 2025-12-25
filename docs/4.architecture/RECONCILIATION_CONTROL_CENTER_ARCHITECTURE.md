# 公司运营与对账中控系统（MVP）- 系统架构方案

> **版本**: v2.1
> **基于**: PRD v1.0 + RECONCILIATION_CONTROL_CENTER_SOT v2.0 + RECONCILIATION_SOT v1.0
> **编制**: 架构设计文档
> **状态**: Review
> **对齐**: MASTER.md v4.4 | STATE_MACHINE.md v2.6 | LEDGER_SOT.md v1.1 | DATA_SCHEMA.md v5.2

---

## 1. 架构概览

本系统是面向广告代运营公司的内部运营与财务对账中控平台，核心闭环为「**三本账 → 双账本 → 日清对账 → 差异单闭环 → 月结利润输出**」。

**核心设计原则**：
- **口径宪法**：同一数字只有一个来源，不允许多头计算
- **双账本体系**：PROJECT 账本（项目收入）+ SUPPLIER 账本（供应商成本）
- **Phase 1 软性原则**：记录事实、展示状态、提示异常，**不强制阻断**
- **7 角色权限隔离**：ceo/project_owner/finance/supervisor/pitcher/account_manager/admin

**核心管理目标**（三权清晰）：
```
谁对钱负责：project_owner 申请 → finance 审核 → ceo 批准
谁对结果负责：project_owner 对盈亏负责
谁能纠偏：日级 supervisor、周级 project_owner、月级 ceo
```

---

## 2. 模块职责与边界

| 模块 | 职责 | 主要读写数据 | SoT 引用 |
|------|------|-------------|----------|
| **A. 主数据** | 代理商/客户/项目/账户/人员/地区 + 别名映射 | `agents`, `clients`, `projects`, `ad_accounts`, `users`, `regions` | DATA_SCHEMA.md v5.2 |
| **B. 项目中心** | 项目规则、结算配置、甲方确认进粉、结账锁数 | `projects`, `settlement_rules`, `daily_reports.conversions_final`, `locking_periods` | §6 结算规则 |
| **C. 账户中心** | 账户台账、分配、状态、余额/押款快照 | `ad_accounts`, `balance_snapshots` | §3.1, §3.5 |
| **D. 充值流程** | 申请→审批→打款→到账 全链路 | `topup_requests` | STATE_MACHINE.md §10 |
| **E. 对账中心** | 三本账守恒校验、差异单闭环 | `ledger_entries`, `balance_snapshots`, `reconciliation_batches`, `reconciliation_issues` | §2.3 守恒公式, §4 状态机 |
| **F. 月度报表** | 项目利润表、公司汇总、应收未收 | 聚合 `ledger_entries` | §6 结算规则 |
| **G. 老板驾驶舱** | 一页经营概览 | 聚合各模块数据 | PRD §5.7 |
| **H. 导入/校验** | CSV 批量导入、待认领队列 | `import_logs`, `pending_queue` | PRD §8 |
| **I. 权限与审计** | 7角色权限、审计留痕 | `users`, `audit_logs` | AUTH_SPEC.md v2.0 |

---

## 3. 架构图（Mermaid）

### 3.1 A. System Context Diagram（系统上下文图）

```mermaid
C4Context
    title 系统上下文图 - 对账中控系统（对齐7角色）

    Person(ceo, "老板 ceo", "查看驾驶舱<br/>审批大额充值<br/>只看输出")
    Person(project_owner, "项目负责人", "管理项目规则<br/>录入确认进粉<br/>查看项目盈亏")
    Person(finance, "财务", "确认到账/消耗<br/>处理差异单<br/>生成月报")
    Person(supervisor, "主管", "审核团队日报<br/>查看团队绩效")
    Person(pitcher, "投手", "提交日报<br/>查看个人绩效")
    Person(account_manager, "户管", "维护账户<br/>录入余额快照")

    System(sys, "对账中控系统", "三本账对账<br/>双账本记录<br/>差异单闭环<br/>月结利润输出")

    System_Ext(agent, "代理商/供应商", "提供到账回执<br/>账户余额")
    System_Ext(client, "甲方/客户", "确认进粉数据")
    System_Ext(adPlatform, "广告平台", "消耗/余额来源<br/>MVP通过导入")

    Rel(ceo, sys, "查看驾驶舱")
    Rel(project_owner, sys, "管理项目/确认进粉")
    Rel(finance, sys, "对账/差异单/月报")
    Rel(supervisor, sys, "审核日报")
    Rel(pitcher, sys, "提交日报")
    Rel(account_manager, sys, "账户/快照")

    Rel(sys, agent, "到账回执(导入)")
    Rel(sys, client, "确认进粉(录入)")
    Rel(sys, adPlatform, "消耗/余额(导入)")
```

---

### 3.2 B. Container / Component Diagram（容器/组件图）

```mermaid
C4Container
    title 容器图 - 系统组成（对齐双账本体系）

    Person(users, "系统用户", "7角色")

    Container_Boundary(frontend, "前端层") {
        Container(webApp, "Web应用", "Next.js 14", "PC端后台<br/>红绿状态可视化")
    }

    Container_Boundary(backend, "后端层") {
        Container(api, "API服务", "FastAPI", "业务逻辑<br/>权限控制")
        Container(reconEngine, "对账引擎", "Python", "守恒公式计算<br/>差异检测")
        Container(ledgerService, "账本服务", "Python", "双账本记录<br/>PROJECT/SUPPLIER")
        Container(reportGen, "报表生成器", "Python", "结算计算<br/>利润表输出")
        Container(importJob, "导入任务", "Python", "CSV解析<br/>待认领队列")
    }

    Container_Boundary(data, "数据层") {
        ContainerDb(db, "PostgreSQL", "Supabase", "业务数据<br/>双账本<br/>审计日志")
        ContainerDb(storage, "文件存储", "Supabase Storage", "导入文件<br/>凭证附件")
    }

    Rel(users, webApp, "HTTPS")
    Rel(webApp, api, "REST API")
    Rel(api, reconEngine, "对账校验")
    Rel(api, ledgerService, "账本记录")
    Rel(api, reportGen, "报表生成")
    Rel(api, db, "读写")
    Rel(ledgerService, db, "ledger_entries")
    Rel(importJob, db, "批量写入")
    Rel(importJob, storage, "读取文件")
```

---

#### 3.2.1 后端组件详图（对齐 SoT 引用）

```mermaid
flowchart TB
    subgraph "API Gateway (FastAPI)"
        AUTH[认证中间件<br/>Supabase Auth]
        PERM[权限中间件<br/>7角色检查<br/>AUTH_SPEC.md v2.0]
    end

    subgraph "业务路由层 (Routers)"
        R_MASTER[主数据路由<br/>/api/v1/master/*]
        R_PROJECT[项目路由<br/>/api/v1/projects/*]
        R_ACCOUNT[账户路由<br/>/api/v1/accounts/*]
        R_TOPUP[充值路由<br/>/api/v1/topups/*]
        R_RECON[对账路由<br/>/api/v1/reconciliation/*]
        R_REPORT[报表路由<br/>/api/v1/reports/*]
        R_SNAPSHOT[快照路由<br/>/api/v1/balance-snapshots/*]
    end

    subgraph "服务层 (Services)"
        S_MASTER[主数据服务<br/>别名映射]
        S_PROJECT[项目服务<br/>结算规则]
        S_ACCOUNT[账户服务<br/>快照管理]
        S_TOPUP[充值服务<br/>STATE_MACHINE §10]
        S_RECON[对账服务<br/>守恒公式]
        S_REPORT[报表服务<br/>BR-SET-*]
        S_AUDIT[审计服务<br/>AuditLog]
    end

    subgraph "核心引擎"
        ENG_LEDGER[双账本引擎<br/>LEDGER_SOT v1.1<br/>PROJECT/SUPPLIER]
        ENG_RECON[对账引擎<br/>Σ充值-Σ消耗=Δ余额+Δ押款]
        ENG_DIFF[差异检测器<br/>红灯>¥100 黄灯¥1-100]
        ENG_SETTLE[结算引擎<br/>fixed/tiered/markup]
    end

    AUTH --> PERM
    PERM --> R_MASTER & R_PROJECT & R_ACCOUNT & R_TOPUP & R_RECON & R_REPORT & R_SNAPSHOT

    R_RECON --> S_RECON --> ENG_RECON --> ENG_DIFF
    S_RECON --> ENG_LEDGER
    R_REPORT --> S_REPORT --> ENG_SETTLE

    S_MASTER & S_PROJECT & S_ACCOUNT & S_TOPUP & S_RECON & S_REPORT --> S_AUDIT
```

---

### 3.3 C. Data Flow Diagram（数据流图）

```mermaid
flowchart LR
    subgraph "输入层 (按角色)"
        I1[/"pitcher<br/>日报(raw_spend+conversions_raw)"/]
        I2[/"account_manager<br/>余额/押款快照<br/>账户分配/死户"/]
        I3[/"project_owner<br/>项目规则<br/>甲方确认进粉(conversions_final)"/]
        I4[/"finance<br/>到账确认<br/>消耗确认(real_spend)"/]
        I5[/"CSV导入<br/>批量数据"/]
    end

    subgraph "处理层 (双账本)"
        P1[主数据校验<br/>别名映射]
        P2[日报状态机<br/>STATE_MACHINE §8<br/>8状态流转]
        P3[双账本记录<br/>LEDGER_SOT v1.1]
        P3A[PROJECT账本<br/>项目收入REVENUE]
        P3B[SUPPLIER账本<br/>供应商成本COST]
        P4[对账引擎<br/>守恒公式校验]
        P5{红/黄/绿判定}
        P6[差异单生成<br/>reconciliation_issues]
        P7[差异单处理<br/>5状态流转]
        P8[月结聚合<br/>结算规则计算]
    end

    subgraph "输出层 (按角色)"
        O1[/"对账看板<br/>红灯/黄灯/绿灯"/]
        O2[/"差异单看板<br/>待处理/已关闭"/]
        O3[/"项目利润表<br/>收入-成本=利润"/]
        O4[/"公司汇总<br/>月度经营"/]
        O5[/"老板驾驶舱<br/>一页概览"/]
    end

    I1 --> P2
    I2 --> P1
    I3 --> P1
    I4 --> P1 --> P3
    I5 --> P1

    P2 -->|final_locked| P3
    P3 --> P3A & P3B
    P3A & P3B --> P4
    I2 -->|balance_snapshots| P4

    P4 --> P5
    P5 -- "差异≤¥1 绿灯" --> P8
    P5 -- "¥1<差异≤¥100 黄灯" --> P6
    P5 -- "差异>¥100 红灯" --> P6
    P6 --> O2 --> P7 --> P8

    P8 --> O3 --> O4 --> O5
    P4 --> O1
    O1 & O2 --> O5
```

---

#### 3.3.1 守恒公式详图（对齐 SoT §2.3）

```mermaid
flowchart TB
    subgraph "三本账输入"
        B1["充值到账账<br/>ledger_entries<br/>WHERE entry_type='TOPUP'<br/>AND ledger_type='SUPPLIER'"]
        B2["消耗账<br/>ledger_entries<br/>WHERE entry_type='COST'<br/>AND ledger_type='SUPPLIER'"]
        B3["余额/押款快照<br/>balance_snapshots<br/>balance + deposit"]
    end

    subgraph "守恒公式 (SoT §2.3)"
        F1["Σ(充值到账) - Σ(实际消耗) = Δ(余额) + Δ(押款)"]
        F2["差异Δ = |左边 - 右边|"]
    end

    subgraph "阈值判定"
        T1["≤ ¥1.00<br/>✅ 绿灯通过<br/>(浮点精度容差)"]
        T2["> ¥1.00 且 ≤ ¥100.00<br/>🟡 黄灯<br/>SLA: T+5工作日"]
        T3["> ¥100.00<br/>🔴 红灯<br/>SLA: T+2工作日"]
    end

    subgraph "差异单类型 (issue_type)"
        D1[topup_mismatch<br/>充值差异]
        D2[spend_mismatch<br/>消耗差异]
        D3[deposit_change<br/>押款变化]
        D4[balance_anomaly<br/>余额异常]
        D5[snapshot_missing<br/>快照缺失]
        D6[conservation_failed<br/>守恒校验失败]
    end

    B1 & B2 & B3 --> F1 --> F2
    F2 --> T1 & T2 & T3
    T2 & T3 --> D1 & D2 & D3 & D4 & D5 & D6
```

---

### 3.4 D. ER Diagram（实体关系图 - 对齐 DATA_SCHEMA.md v5.2）

```mermaid
erDiagram
    %% ===== 主数据域 =====
    agents ||--o{ ad_accounts : "代理商拥有账户"
    agents ||--o{ topup_requests : "代理商收款"
    clients ||--o{ projects : "客户拥有项目"
    projects ||--o{ ad_accounts : "项目包含账户"
    projects ||--o{ daily_reports : "项目日报"
    users ||--o{ ad_accounts : "投手操作账户"
    users ||--o{ projects : "PM负责项目"

    %% ===== 日报与账本域 =====
    ad_accounts ||--o{ daily_reports : "账户日报"
    daily_reports ||--o{ ledger_entries : "final_locked生成账本"

    %% ===== 账户域 =====
    ad_accounts ||--o{ balance_snapshots : "账户余额快照"
    ad_accounts ||--o{ topup_requests : "账户充值申请"

    %% ===== 充值流程域 =====
    topup_requests ||--o{ ledger_entries : "paid生成账本"

    %% ===== 对账域 =====
    reconciliation_batches ||--o{ reconciliation_issues : "批次包含差异单"
    ad_accounts ||--o{ reconciliation_issues : "账户差异单"
    reconciliation_issues ||--o{ adjustments : "差异单调整"

    %% ===== 结算域 =====
    projects ||--o| settlement_rules : "项目结算规则"
    projects ||--o{ locking_periods : "项目锁数周期"

    %% ===== 双账本 =====
    ledger_entries {
        uuid id PK
        uuid reference_id FK "关联日报/充值"
        string reference_type "daily_report/topup_request"
        enum ledger_type "PROJECT/SUPPLIER"
        enum entry_type "TOPUP/COST/REVENUE/FEE"
        decimal amount "金额(有符号)"
        date occurred_at
        uuid created_by FK
        timestamp created_at
    }

    %% ===== 新增表定义 =====
    balance_snapshots {
        uuid id PK
        uuid ad_account_id FK
        date snapshot_date
        decimal balance "当日余额"
        decimal deposit "当日押款"
        decimal remaining_balance "GENERATED(balance-deposit)"
        enum source "manual/api/import"
        uuid created_by FK
        timestamp created_at
    }

    reconciliation_batches {
        uuid id PK
        string batch_no "RECON-YYYYMM-NNN"
        uuid supplier_id FK
        uuid channel_id FK
        date period_start
        date period_end
        enum status "draft/pending_review/approved/needs_adjustment/completed"
        decimal our_total_spend
        decimal supplier_total_spend
        decimal difference
        uuid created_by FK
        timestamp created_at
    }

    reconciliation_issues {
        uuid id PK
        string issue_no "ISSUE-YYYYMMDD-NNN"
        uuid batch_id FK
        uuid ad_account_id FK
        date issue_date
        enum issue_type "topup_mismatch/spend_mismatch/deposit_change/balance_anomaly/snapshot_missing/conservation_failed"
        enum alert_level "green/yellow/red"
        decimal expected_amount
        decimal actual_amount
        decimal difference_amount "GENERATED"
        enum status "open/assigned/investigating/resolved/closed"
        uuid assigned_to FK
        enum resolution_type "data_correction/ledger_adjustment/external_confirm/write_off/false_positive"
        text resolution_note
        timestamp sla_deadline
        boolean sla_breached
        integer version "乐观锁"
        uuid created_by FK
        timestamp created_at
    }

    adjustments {
        uuid id PK
        uuid issue_id FK
        enum type "add_spend/reduce_spend/add_topup/reduce_topup/deposit_adjust"
        decimal amount
        text reason
        uuid created_by FK
        uuid approved_by FK
        timestamp created_at
    }

    settlement_rules {
        uuid id PK
        string name
        enum rule_type "tiered/markup"
        jsonb config "阶梯参数/加成比例"
        date effective_from
        date effective_to
        uuid created_by FK
        timestamp created_at
    }

    projects {
        uuid id PK
        uuid client_id FK
        uuid pm_user_id FK
        string name
        decimal unit_price "fixed单价"
        enum settlement_type "fixed/tiered/markup"
        uuid settlement_rules_id FK
        enum status "active/paused/closed"
        timestamp created_at
    }

    ad_accounts {
        uuid id PK
        uuid agent_id FK
        uuid project_id FK
        uuid pitcher_user_id FK
        string platform
        string account_no
        decimal balance "当前余额"
        decimal deposit "当前押款"
        enum status "normal/restricted/dead"
        timestamp created_at
    }

    daily_reports {
        uuid id PK
        uuid project_id FK
        uuid ad_account_id FK
        uuid pitcher_user_id FK
        date report_date
        decimal raw_spend "投手填报消耗"
        int conversions_raw "投手填报进粉"
        decimal real_spend "财务确认消耗"
        int conversions_final "甲方确认进粉"
        enum status "raw_submitted/trend_pending/trend_ok/trend_flagged/trend_resolved/final_pending/final_confirmed/final_locked"
        timestamp created_at
    }

    users {
        uuid id PK
        string name
        string email
        enum role "ceo/project_owner/finance/supervisor/pitcher/account_manager/admin"
        timestamp created_at
    }

    audit_logs {
        uuid id PK
        uuid user_id FK
        string entity_type
        uuid entity_id
        string action
        jsonb old_value
        jsonb new_value
        timestamp created_at
    }
```

---

## 4. 状态机（对齐 STATE_MACHINE.md v2.6）

### 4.1 对账批次状态机（对齐 RECONCILIATION_SOT.md v1.0 §5.1）

```mermaid
stateDiagram-v2
    [*] --> draft: 创建对账批次
    draft --> pending_review: 提交审核 [finance/account_manager]
    pending_review --> approved: 审核通过 [finance/admin]
    pending_review --> needs_adjustment: 需要调整 [finance/admin]
    approved --> completed: 确认完成 [finance/admin]
    approved --> needs_adjustment: 发现问题需调整 [finance/admin]
    needs_adjustment --> approved: 调整完成重新审批 [finance]
    completed --> [*]

    note right of draft: 初始态
    note right of completed: 终态，不可回退
```

**5 状态定义**：
| 状态 | 英文 | 含义 | 可执行操作 |
|-----|------|------|-----------|
| 草稿 | `draft` | 批次创建但未提交 | 编辑、删除、提交审核 |
| 待审核 | `pending_review` | 已提交等待审核 | 通过、打回 |
| 已通过 | `approved` | 审核通过可完成 | 确认完成、发现问题打回 |
| 需调整 | `needs_adjustment` | 需要修正后重审 | 调整后重新审批 |
| 已完成 | `completed` | 终态，对账已闭环 | 仅查看 |

**状态流转白名单**：
```python
RECONCILIATION_BATCH_TRANSITIONS = {
    "draft": ["pending_review"],
    "pending_review": ["approved", "needs_adjustment"],
    "approved": ["completed", "needs_adjustment"],
    "needs_adjustment": ["approved"],
    "completed": []  # 终态
}
```

### 4.2 差异单状态机

```mermaid
stateDiagram-v2
    [*] --> open: 系统自动创建
    open --> assigned: 分配责任人 [finance/admin]
    assigned --> investigating: 开始调查 [assigned_to]
    investigating --> resolved: 处理完成 [assigned_to]
    investigating --> assigned: 重新分配 [finance/admin]
    resolved --> closed: 关闭确认 [finance/admin]
    resolved --> investigating: 重新调查 [finance/admin]
    closed --> [*]
```

**状态流转白名单**：
```python
RECONCILIATION_ISSUE_TRANSITIONS = {
    "open": ["assigned"],
    "assigned": ["investigating"],
    "investigating": ["resolved", "assigned"],
    "resolved": ["closed", "investigating"],
    "closed": []  # 终态
}
```

---

## 5. 7 角色权限矩阵（对齐 AUTH_SPEC.md v2.0）

### 5.1 角色定义

| 角色ID | 中文名 | 职责范围 |
|--------|-------|---------|
| **ceo** | 老板 | 资金安全、公司盈亏、最终决策 |
| **project_owner** | 项目负责人 | 项目盈亏、资金使用效率 |
| **finance** | 财务 | 资金出入准确、数据真实、对账 |
| **supervisor** | 主管 | 团队产出、投手管理、日常监督 |
| **pitcher** | 投手 | CPL 达标、日报准确、执行投放 |
| **account_manager** | 户管 | 账户分配、账户状态监控、余额快照 |
| **admin** | 管理员 | 系统配置（不参与业务） |

### 5.2 对账模块权限矩阵

| 操作 | ceo | project_owner | finance | supervisor | pitcher | account_manager | admin |
|-----|-----|--------------|---------|------------|---------|-----------------|-------|
| 查看对账批次 | ✅全局 | ✅自己项目 | ✅全局 | ✅团队 | ❌ | ✅全局 | ✅全局 |
| 创建对账批次 | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ |
| 关闭对账批次 | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 查看差异单 | ✅全局 | ✅自己项目 | ✅全局 | ✅团队 | ❌ | ✅全局 | ✅全局 |
| 分配差异单 | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 处理差异单 | ❌ | ❌ | ✅ | ❌ | ❌ | ✅快照类 | ✅ |
| 关闭差异单 | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 录入余额快照 | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ |
| 配置结算规则 | ❌ | ✅自己项目 | ✅ | ❌ | ❌ | ❌ | ✅ |
| 查看利润表 | ✅全局 | ✅自己项目 | ✅全局 | ❌ | ❌ | ❌ | ✅ |

---

## 6. 业务规则引用（BUSINESS_RULES.md v3.2）

### 6.1 对账规则（BR-REC-*）

| 规则ID | 规则名称 | 级别 | 说明 |
|--------|---------|------|------|
| BR-REC-001 | 对账守恒公式 | 🔴强制 | Σ充值-Σ消耗=Δ余额+Δ押款 |
| BR-REC-002 | 差异单SLA规则 | 🟡Phase2 | 红灯T+2，黄灯T+5 |
| BR-REC-003 | 快照缺失处理 | 🟡警告 | 自动生成snapshot_missing差异单 |
| BR-REC-004 | 押款变化记录 | 🔴强制 | 押款变化必须记录原因 |
| BR-REC-005 | 对账批次唯一性 | 🔴强制 | (supplier_id,channel_id,period)唯一 |

### 6.2 结算规则（BR-SET-*）

| 规则ID | 规则名称 | 公式 |
|--------|---------|------|
| BR-SET-001 | Fixed结算 | revenue = conversions_final × unit_price |
| BR-SET-002 | Tiered结算 | 按阶梯累计/增量计算 |
| BR-SET-003 | Markup结算 | revenue = real_spend × (1 + markup_rate) |

---

## 7. 错误码（ERROR_CODES_SOT.md v2.1）

### 7.1 对账模块错误码（E-RECON-*）

| 错误码 | 消息 | HTTP | 触发场景 |
|--------|------|------|----------|
| E-RECON-001 | 对账批次已存在 | 409 | 违反唯一约束 |
| E-RECON-002 | 对账周期无效 | 400 | period_end < period_start |
| E-RECON-003 | 非法状态流转 | 400 | 不在白名单的状态流转 |
| E-RECON-004 | 审批人与创建人相同 | 403 | 违反职责分离(SOD) |
| E-RECON-005 | 终态批次禁止修改 | 403 | 尝试修改closed批次 |
| E-RECON-006 | 差异单未全部关闭 | 400 | 批次下存在未关闭差异单 |
| E-RECON-007 | 余额快照缺失 | 400 | 对账期间账户缺少快照 |
| E-RECON-008 | 守恒校验失败 | 400 | 守恒公式校验不通过 |

### 7.2 结算模块错误码（E-SET-*）

| 错误码 | 消息 | HTTP | 触发场景 |
|--------|------|------|----------|
| E-SET-001 | 结算规则配置无效 | 400 | 规则配置格式错误 |
| E-SET-002 | 结算类型不支持 | 400 | settlement_type不在枚举范围 |
| E-SET-003 | 阶梯配置重叠 | 400 | tiered规则区间重叠 |
| E-SET-004 | 加成比例无效 | 400 | markup_rate < 0 或 > 1 |
| E-SET-005 | 结算规则未生效 | 400 | 当前日期不在规则有效期内 |

---

## 8. API 规范（API_SOT.md v9.0）

### 8.1 对账批次 API

| 端点 | 方法 | 说明 | 权限 |
|------|------|------|------|
| GET /api/v1/reconciliation/batches | GET | 获取批次列表 | finance,admin,account_manager |
| POST /api/v1/reconciliation/batches | POST | 创建批次 | finance,admin,account_manager |
| POST /api/v1/reconciliation/batches/{id}/submit | POST | 提交审核 | finance,admin,account_manager |
| POST /api/v1/reconciliation/batches/{id}/review | POST | 开始审核 | finance,admin |
| POST /api/v1/reconciliation/batches/{id}/close | POST | 关闭批次 | finance,admin |

### 8.2 差异单 API

| 端点 | 方法 | 说明 | 权限 |
|------|------|------|------|
| GET /api/v1/reconciliation/issues | GET | 获取差异单列表 | finance,admin,account_manager |
| POST /api/v1/reconciliation/issues/{id}/assign | POST | 分配责任人 | finance,admin |
| POST /api/v1/reconciliation/issues/{id}/start | POST | 开始调查 | assigned_to |
| POST /api/v1/reconciliation/issues/{id}/resolve | POST | 处理完成 | assigned_to |
| POST /api/v1/reconciliation/issues/{id}/close | POST | 关闭差异单 | finance,admin |

### 8.3 余额快照 API

| 端点 | 方法 | 说明 | 权限 |
|------|------|------|------|
| GET /api/v1/balance-snapshots | GET | 获取快照列表 | finance,admin,account_manager |
| POST /api/v1/balance-snapshots | POST | 创建快照 | finance,admin,account_manager |
| POST /api/v1/balance-snapshots/bulk | POST | 批量导入 | finance,admin,account_manager |

---

## 9. P0 架构决策清单

| # | 决策 | 说明 | SoT引用 |
|---|------|------|---------|
| **D-01** | **口径宪法** | 收入=conversions_final, 成本=real_spend, 充值=ledger TOPUP, 快照=balance_snapshots | SoT §2.1 |
| **D-02** | **双账本体系** | PROJECT账本(项目收入) + SUPPLIER账本(供应商成本) | LEDGER_SOT v1.1 |
| **D-03** | **三本账齐备** | 缺任意一本账→对账结果「不可判定」→生成补录待办 | SoT §2.2 |
| **D-04** | **守恒公式** | Σ充值-Σ消耗=Δ余额+Δ押款, 阈值: ≤¥1绿灯, ¥1-100黄灯, >¥100红灯 | SoT §2.3 |
| **D-05** | **差异单必须闭环** | 红灯→差异单→指派→处理→关闭(留痕), 未闭环不进月报 | SoT §4.2 |
| **D-06** | **7角色权限** | ceo/project_owner/finance/supervisor/pitcher/account_manager/admin | AUTH_SPEC v2.0 |
| **D-07** | **Phase 1 软性原则** | 记录事实、展示状态、提示异常，不强制阻断 | MASTER.md v4.4 |
| **D-08** | **主数据唯一+别名** | 唯一ID + alias_list 映射历史写法 | SoT §3 |
| **D-09** | **系统开始日策略** | 开始日后强制闭环, 开始日前仅查询参考 | SoT §2.5 |
| **D-10** | **审计留痕** | 关键操作写入 audit_logs (谁/何时/什么/原因) | SoT §8 |

---

## 10. 里程碑拆分（Phase 0/1/2）

### Phase 0：试点准备

| 交付物 | 验收点 | SoT引用 |
|--------|--------|---------|
| 主数据表结构 + CRUD | 代理商/客户/项目/账户/人员可创建 | DATA_SCHEMA.md |
| 别名映射功能 | 历史写法可映射唯一实体 | SoT §3 |
| balance_snapshots 表 | 余额/押款/剩余可用 | SoT §3.1 |
| settlement_rules 表 | tiered/markup 规则可配置 | SoT §3.3 |
| 7角色权限框架 | 登录+权限隔离 | AUTH_SPEC v2.0 |
| CSV 导入通路 | 错误行报告 + 待认领队列 | PRD §8 |

**验收标准**：试点主数据可统一建模；历史数据可导入无重复。

---

### Phase 1：试点闭环（日清日结）

| 交付物 | 验收点 | SoT引用 |
|--------|--------|---------|
| 余额快照批量导入 | 户管可批量导入每日快照 | SoT §3.1 |
| 双账本引擎 | PROJECT/SUPPLIER 账本记录 | LEDGER_SOT v1.1 |
| **对账引擎** | 守恒公式计算，红/黄/绿输出 | SoT §2.3 |
| reconciliation_batches | 对账批次 5 状态流转 | RECONCILIATION_SOT v1.0 §5.1 |
| reconciliation_issues | 差异单 5 状态流转 | SoT §4.2 |
| 差异单分类 | 6 种 issue_type 自动识别 | SoT §3.2 |
| 对账看板 | 红灯/黄灯清单，按账户×日期定位 | PRD §5.5 |
| 审计日志 | 关键操作可追溯 | SoT §8 |

**验收标准**：
- 任一红灯可定位到「账户×日期×差异项」
- 差异单可闭环关闭且留痕
- 对账耗时较基线降低 ≥50%

---

### Phase 2：试点月结

| 交付物 | 验收点 | SoT引用 |
|--------|--------|---------|
| 结算规则管理 | fixed/tiered/markup 可配置 | SoT §6 |
| 结算计算引擎 | 按规则计算收入 | BR-SET-001~003 |
| 甲方确认进粉录入 | PM 可录入 conversions_final | DATA_SCHEMA.md |
| 月结锁数 | locking_periods 锁定周期数据 | PRD §5.2 |
| 调整单 | adjustments 表，审批+留痕 | SoT §3.2 |
| 项目利润表 | 收入-成本=利润 一键生成 | PRD §5.6 |
| 公司汇总表 | 月度经营汇总 | PRD §5.6 |
| 老板驾驶舱 v2 | 利润、红灯、风险项目 | PRD §5.7 |

**验收标准**：
- 试点项目月底可一键生成利润表
- 利润表与人工结果一致（或差异可解释可追溯）
- 月报只使用「通过对账」的数据

---

## 11. 参考文档索引

| SoT 文档 | 版本 | 引用章节 |
|---------|------|---------|
| MASTER.md | v4.4 | §2.4 7角色, §3 Phase边界 |
| STATE_MACHINE.md | v2.6 | §5 对账批次状态机 |
| DATA_SCHEMA.md | v5.2 | 表结构定义 |
| LEDGER_SOT.md | v1.1 | §2 双账本模型 |
| BUSINESS_RULES.md | v3.2 | BR-REC-*, BR-SET-* |
| ERROR_CODES_SOT.md | v2.1 | E-RECON-*, E-SET-* |
| AUTH_SPEC.md | v2.0 | §3 角色权限 |
| API_SOT.md | v9.0 | §12 对账管理API |
| RECONCILIATION_CONTROL_CENTER_SOT.md | v2.0 | 对账管控完整规范 |

---

## 变更记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v2.1 | 2025-12-26 | **状态机修正**：对齐 RECONCILIATION_SOT.md v1.0 §5.1<br/>- 对账批次状态从 4 状态改为 5 状态<br/>- 状态名：`draft/pending_review/approved/needs_adjustment/completed`<br/>- 终态从 `closed` 改为 `completed`<br/>- 新增状态定义表<br/>- 更新 ER 图枚举值 |
| v2.0 | 2025-12-26 | **重大更新**：对齐 RECONCILIATION_CONTROL_CENTER_SOT v2.0<br/>- 对齐 7 角色体系<br/>- 对齐双账本结构<br/>- 对齐状态机定义<br/>- 统一错误码格式<br/>- 完善守恒公式与阈值<br/>- 添加 SoT 引用索引 |
| v1.0 | 2025-12-26 | 初始版本，基于 PRD v1.0 |

---

**文档性质**: 对账中控系统架构方案
**对齐基准**: RECONCILIATION_CONTROL_CENTER_SOT v2.0
**最后更新**: 2025-12-26
