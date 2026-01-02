# DATA_SCHEMA.md · 数据结构唯一事实来源 (SoT-Data)

> **版本**: v5.9
> **status**: active
> **owner**: wade
> **last_reviewed**: 2026-01-02
> **更新日期**: 2026-01-02
> **维护团队**: 系统架构团队（数据库规范守门人）
> **定位**: 描述 AI 广告代投系统全部已落地/规划中的数据库表结构、字段、索引与约束，是数据层唯一事实来源。若其他文档与此冲突，以本文件为准。
> **互锁 SoT**:
> - 实现规范 → `./MASTER.md` v4.8（系统宪法，最高优先级）
> - 需求文档 → `PRD_AI_v1.0.md` v1.1（AI 友好格式，与 MASTER 6 角色完全对齐）
> - 状态机 → `STATE_MACHINE.md` v2.8（任何状态字段必须引用对应状态机）
> - 业务规则 → `BUSINESS_RULES.md` v5.0（履约状态字段来源，三本账体系）
> - 错误码 → `ERROR_CODES_SOT.md` v2.2
> - 认证授权 → `AUTH_SPEC.md` v2.1（角色权限映射）
> - 业务需求 → `BRD_chapter1_v3.1.md` (BRD v3.1基线)

---

## 1. 通用约定

### 1.1 技术栈

- **数据库**: PostgreSQL 15（Supabase 托管）
- **ORM / 迁移**: SQLAlchemy（同步版）+ Alembic
- **权限**: 当前版本仅在应用层（Service + `@require_role`）执行 RBAC，数据库 RLS 规划中未启用  
- **时间字段**: 统一使用 `TIMESTAMPTZ`，默认 `NOW()`，应用层使用 UTC  
- **金额字段**: 一律 `DECIMAL(15,2)`，默认 `0.00`，借方为正、贷方为负值  
- **角色枚举**:
  - **业务层角色**（6个，存储在 `users.role` 字段）：`ceo`, `project_owner`, `finance`, `pitcher`, `account_manager`, `admin`（MASTER.md v4.8 §2.4, PRD v5.2 §2.2.1）
  - **角色职责**（PRD_AI_v1.0.md §2.1）：
    - `ceo`（老板）：资金安全、公司盈亏、最终决策、大额支出、月度锁账
    - `project_owner`（项目负责人）：项目盈亏、日报审核、有效线索确认、定价、争议裁定
    - `finance`（财务）：资金出入准确、对账、收入录入、充值审批（限额内）
    - `pitcher`（投手）：CPL 达标、日报准确、执行投放、投放策略（预算内）
    - `account_manager`（户管）：账户管理、环境分配、实际消耗录入、账户分配
    - `admin`（管理员）：系统配置、用户管理
  - **技术层角色**（4个，用于应用层 RBAC CHECK 约束）：`admin`, `finance`, `account_manager`, `media_buyer`
  - **业务层 → 技术层映射**：
    - `ceo` → `admin`（系统最高权限）
    - `project_owner` → 通过 `users.is_project_owner=true` 业务属性判断（日报审核等）
    - `finance` → `finance`（直接映射）
    - `pitcher` → `media_buyer`（业务名→技术名，同一角色的两种称呼）
    - `account_manager` → `account_manager`（直接映射）
    - `admin` → `admin`（直接映射）
  - 详细映射规则见 AUTH_SPEC.md v2.1 §2.2, MASTER.md v4.8 §INV-007

> ⚠️ **废弃角色** (MASTER v4.8, PRD v5.2 已对齐)：以下角色已废弃，新代码禁止使用
> - `supervisor` → 职责合并到 `project_owner`
> - `data_operator` → 按场景分配到 `project_owner`（日报审核）或 `finance`（充值/对账）

> 📝 **说明**：`pitcher` 和 `media_buyer` 是**同一角色的两种称呼**：
> - `pitcher`（投手）：业务文档和用户界面使用
> - `media_buyer`：代码层 RBAC CHECK 约束使用
> - 这不是废弃关系，而是命名映射关系  
- **状态字段**: 仅引用 `STATE_MACHINE.md` 中的定义，禁止在本文件重复列举或扩展新枚举  
- **主键/外键**:  
  - 用户、渠道等跨系统实体：主键使用 UUID（对齐 Supabase/外部系统 ID）  
  - 核心业务表（项目、账户、日报、充值、账本、对账等）：主键统一使用 BIGSERIAL  
  - 所有外键字段类型必须与被引用主键完全一致（如引用 `users.id` 必须是 UUID，引用 `projects.id` 必须是 BIGINT）

### 1.2 字段命名规则

1. 主键统一命名为 `id`。  
2. 外键统一命名为 `<实体名>_id`（如 `project_id`, `ad_account_id`, `user_id`, `channel_id`）。  
3. 日志/审计类表必须包含 `created_at`，需要表示最近更新时间的表应包含 `updated_at`。  
4. 布尔字段使用 `is_*` / `has_*` 前缀（如 `is_active`, `has_pending_risk`）。  
5. JSONB 字段若用于扩展信息需以 `_data`、`_settings`、`_metadata` 等结尾。  
6. 状态相关字段在说明中需指出"枚举值以 STATE_MACHINE.md 为准"。

### 1.3 索引命名规范

| 前缀 | 用途 | 命名格式 | 示例 |
|------|------|---------|------|
| `idx_` | 普通索引 | `idx_<表名>_<列名>` | `idx_users_role` |
| `uq_` | 唯一索引 | `uq_<表名>_<列1>_<列2>` | `uq_project_members_project_user` |
| `pk_` | 主键索引 | `pk_<表名>` | `pk_users`（PostgreSQL 默认） |
| `fk_` | 外键约束 | `fk_<表名>_<列名>` | `fk_daily_reports_ad_account_id` |

**命名原则**:
1. 表名使用**单数缩写**，如 `users` → `user`，`daily_reports` → `daily_reports`（复合词保留）
2. 组合索引列名按**查询优先级**排序，如 `idx_daily_reports_date_status`
3. 部分索引添加 `_partial` 后缀或 WHERE 条件说明，如 `idx_users_is_project_owner`（WHERE is_project_owner = true）
4. 所有索引定义需同时更新到**迁移文件**和**本文档**

---

## 2. 表清单（实现状态）

| 表名 | 说明 | 主键 | 状态 |
| --- | --- | --- | --- |
| `users` | 业务用户表（与 Supabase Auth 同步） | UUID | implemented |
| `teams` | 团队表（投手归属） | UUID | implemented |
| `roles` | 历史角色表/兼容视图 | UUID | legacy |
| `user_sessions` | 登录会话与安全审计 | BIGSERIAL | implemented |
| `audit_logs` | 系统级审计日志 | BIGSERIAL | implemented |
| `projects` | 项目主表 | BIGSERIAL | implemented |
| `project_members` | 项目成员/权限 | BIGSERIAL | implemented |
| `project_expenses` | 项目费用记录 | BIGSERIAL | implemented |
| `channels` | 渠道主数据 | UUID | implemented |
| `channel_contacts` | 渠道联系人 | UUID | implemented |
| `channel_reviews` | 渠道评审记录 | UUID | implemented |
| `channel_account_requests` | 渠道开户申请 | UUID | implemented |
| `channel_performance` | 渠道表现统计 | UUID | implemented |
| `ad_accounts` | 广告账户 | BIGSERIAL | implemented |
| `account_status_history` | 账户状态流水 | BIGSERIAL | implemented |
| `account_alerts` | 账户预警 | BIGSERIAL | implemented |
| `account_documents` | 账户附件/凭证 | BIGSERIAL | implemented |
| `account_notes` | 账户备注 | BIGSERIAL | implemented |
| `daily_reports` | 日报 | BIGSERIAL | implemented |
| `daily_report_audit_logs` | 日报审计日志 | BIGSERIAL | implemented |
| `ad_spend_daily` | 外部导入日消耗 | UUID | implemented |
| `weekly_briefs` | 周度简报 | BIGSERIAL | implemented |
| `topup_requests` | 充值申请 | BIGSERIAL | implemented |
| `topup_transactions` | 充值到账流水 | BIGSERIAL | implemented |
| `topup_approval_logs` | 充值审批操作记录 | BIGSERIAL | implemented |
| `ledger_entries` | 资金总账 | BIGSERIAL | implemented |
| `suppliers` | 供应商主表 | UUID | implemented |
| `transfer_requests` | 死号余额迁移申请 | BIGSERIAL | implemented |
| `reconciliation_batches` | 对账批次 | BIGSERIAL | implemented |
| `reconciliation_details` | 对账明细 | BIGSERIAL | implemented |
| `reconciliation_adjustments` | 对账调整 | BIGSERIAL | implemented |
| `reconciliation_reports` | 对账报告 | BIGSERIAL | implemented |
| `balance_snapshots` | 余额/押款快照 | BIGSERIAL | implemented |
| `reconciliation_issues` | 对账差异单 | BIGSERIAL | implemented |
| `settlement_rules` | 结算规则配置 | BIGSERIAL | implemented |
| `profit_aggregates` | 利润聚合（L2汇总层） | BIGSERIAL | planned |
| `profit_report_snapshots` | 利润报表快照 | BIGSERIAL | planned |
| `monthly_settlements` | 月度结算表 | BIGSERIAL | implemented |
| `receivable` | 回款记录表（SoT：已回款） | BIGSERIAL | implemented |
| `company_expenses` | 公司运营支出（不进账本） | BIGSERIAL | implemented |

---

## 3. 详细表结构

> 说明：凡是包含 `status`/`review_status`/`urgency_level` 等状态字段，均在字段描述中注明所属状态机或固定枚举。

### 3.1 用户与权限

#### 3.1.1 `users`（implemented）

**说明**：
- `users` 表是业务层的用户资料表，主键为 UUID
- 主键 `id` 外键关联 `auth.users(id)`（Supabase Auth 内置用户表），ON DELETE CASCADE 确保同步删除
- **认证与业务分离**：
  - `auth.users` 用于认证（Supabase Auth 管理邮箱、密码、会话等）
  - `users` 用于业务逻辑（角色、权限、扩展信息等）
- **字段同步关系**：
  - `email` 字段与 `auth.users.email` 保持同步（通过应用层或触发器）
  - `password_hash` 字段为可空，仅用于本地 JWT 认证场景（如开发环境），生产环境使用 Supabase Auth
- `role` 字段存储**业务层角色**（6个：ceo/project_owner/finance/pitcher/account_manager/admin）
- 技术层角色映射在应用层处理（见 §1.1 角色枚举说明）

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | UUID | PK, FK → `auth.users(id)` ON DELETE CASCADE | 与 Supabase Auth 同步 |
| `username` | VARCHAR(50) | UNIQUE, NOT NULL | 用户名 |
| `full_name` | VARCHAR(100) | 可空 | 真实姓名 |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | 邮箱地址（与 `auth.users.email` 同步，Supabase Auth 为主数据源） |
| `password_hash` | VARCHAR(255) | 可空 | 密码哈希(bcrypt)，仅用于本地 JWT 认证场景（开发环境），生产环境使用 Supabase Auth，此字段可为空 |
| `role` | VARCHAR(20) | NOT NULL, CHECK（合法角色） | 6 个标准角色：`ceo/project_owner/finance/pitcher/account_manager/admin`（MASTER.md v4.8 §2.4）|
| `is_project_owner` | BOOLEAN | DEFAULT false | 是否为项目负责人，用于 project_owner 身份判断（MASTER.md v4.8 §2.4, STATE_MACHINE.md v2.8 §2.1）|
| `department` | VARCHAR(100) | 可空 | 部门 |
| `position` | VARCHAR(100) | 可空 | 职位 |
| `team_id` | UUID | FK → `teams.id` ON DELETE SET NULL, 可空 | 所属团队ID，投手直接归属团队 |
| `account_manager_id` | UUID | FK → `users.id`, 可空 | 投手关联户管 |
| `is_active` | BOOLEAN | DEFAULT true | 账号可用性 |
| `is_verified` | BOOLEAN | DEFAULT false | 资料验证状态 |
| `last_login_at` | TIMESTAMPTZ | 可空 | 最后登录时间 |
| `last_login_ip` | VARCHAR(45) | 可空 | 最后登录IP |
| `preferences` | JSONB | DEFAULT `{}` | 用户偏好设置 |
| `notification_settings` | JSONB | DEFAULT `{}` | 通知设置 |
| `profile_metadata` | JSONB | DEFAULT `{}` | 扩展元数据 |
| `timezone` | VARCHAR(50) | DEFAULT `'UTC'` | 时区 |
| `language` | VARCHAR(10) | DEFAULT `'zh-CN'` | 语言 |
| `created_at` / `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | |
| `created_by` / `updated_by` | UUID | FK → `users.id`, 可空 | |

索引：`idx_users_username`, `idx_users_role`, `idx_users_account_manager`, `idx_users_created_at`, `idx_users_last_login`, `idx_users_team`, `idx_users_is_project_owner`（部分索引，WHERE is_project_owner = true）.

#### 3.1.2 `teams`（implemented）

**说明**：团队表，用于投手归属管理。投手通过 `users.team_id` 关联到团队。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | UUID | PK | 团队唯一标识 |
| `name` | VARCHAR(100) | NOT NULL, UNIQUE | 团队名称 |
| `description` | TEXT | 可空 | 团队描述 |
| `leader_id` | UUID | FK → `users.id`, 可空 | 团队负责人 |
| `is_active` | BOOLEAN | DEFAULT true | 是否激活 |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |
| `created_by` | UUID | FK → `users.id`, 可空 | 创建人 |

索引：`idx_teams_name`, `idx_teams_leader`, `idx_teams_is_active`.

#### 3.1.3 `roles`（legacy）

**说明**：历史角色表，用于旧系统兼容。**新功能禁止引用此表**，应直接使用 `users.role` 字段。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | UUID | PK | 角色ID |
| `name` | VARCHAR(50) | UNIQUE, NOT NULL | 角色名称 |
| `description` | TEXT | 可空 | 角色描述 |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |

> ⚠️ **废弃警告**：此表为 legacy 状态，仅用于迁移兼容。当前系统的角色定义直接存储在 `users.role` 字段中，遵循 MASTER.md v4.8 §2.4 的 6 角色模型。

#### 3.1.4 `user_sessions`（implemented）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` BIGSERIAL PK | |
| `user_id` UUID FK → `users.id` | |
| `session_id` UUID UNIQUE | Supabase Session ID |
| `ip_address` INET | |
| `user_agent` TEXT | |
| `expires_at` TIMESTAMPTZ | |
| `created_at` TIMESTAMPTZ DEFAULT NOW() | |
| `invalidated_at` TIMESTAMPTZ 可空 | 手动失效时间 |

索引：`idx_user_sessions_user_id`, `idx_user_sessions_session_id`.

#### 3.1.5 `audit_logs`（implemented）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` BIGSERIAL PK | |
| `module` VARCHAR(100) | 业务模块名 |
| `action` VARCHAR(50) | `create/update/delete/approve/...` |
| `entity_id` VARCHAR(64) | 关联实体主键或编号 |
| `performed_by` UUID FK → `users.id` | |
| `role` VARCHAR(20) | 操作者角色 |
| `ip_address` INET / `user_agent` TEXT | | |
| `payload_before` / `payload_after` JSONB | | |
| `created_at` TIMESTAMPTZ DEFAULT NOW() | | |

---

### 3.2 项目 / 渠道 / 账户

#### 3.2.1 `projects`（implemented）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` BIGSERIAL PK | |
| `name` VARCHAR(200) NOT NULL | |
| `client_name` / `client_company` VARCHAR(200) NOT NULL | 客户联系人/公司 |
| `description` TEXT | |
| `status` VARCHAR(20) | 参考“项目状态机”，典型值如 draft/active/suspended/archived，具体枚举以 STATE_MACHINE.md 为准 |
| `account_manager_id` UUID FK → `users.id` | |
| `budget_total` DECIMAL(15,2) | DEFAULT 0.00 |
| `budget_currency` VARCHAR(10) | DEFAULT 'CNY' |
| `unit_price` DECIMAL(15,2) | DEFAULT 0.00, 项目单粉价格(Per Lead),用于计算粉数收入,公式: `revenue = conversions_final × unit_price` |
| `settlement_type` VARCHAR(20) | DEFAULT 'fixed', CHECK IN ('fixed', 'tiered', 'markup'), 结算类型：fixed使用unit_price，tiered/markup使用settlement_rules |
| `settlement_rules_id` BIGINT | FK → `settlement_rules.id`, 可空, 非fixed结算时关联的结算规则 |
| `fulfillment_status` VARCHAR(20) | NOT NULL DEFAULT 'running', CHECK IN ('running', 'fulfilled'), 履约状态 (SoT: BUSINESS_RULES.md v4.7 BR-PROJ-006) |
| `fulfillment_reason` VARCHAR(30) | 可空, CHECK IN ('spend_exhausted', 'client_stopped'), 履约结束原因 (SoT: BI-06) |
| `fulfilled_at` TIMESTAMPTZ | 可空, 履约完成时间 (UTC) |
| `start_date` / `end_date` DATE | | |
| `created_by` / `updated_by` UUID FK → `users.id` | |
| `created_at` / `updated_at` TIMESTAMPTZ | DEFAULT NOW() | |

索引：`idx_projects_name`, `idx_projects_status`, `idx_projects_account_manager`, `idx_projects_settlement_type`, `idx_projects_fulfillment_status`.

#### 3.2.2 `project_members`（implemented）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` BIGSERIAL PK | |
| `project_id` BIGINT FK → `projects.id` ON DELETE CASCADE | |
| `user_id` UUID FK → `users.id` | |
| `role` VARCHAR(20) | 项目内角色，与全局角色一致 |
| `permissions` JSONB DEFAULT `{}` | 扩展权限 |
| `joined_at` TIMESTAMPTZ DEFAULT NOW() | |
| `notes` TEXT | |

索引：`uq_project_members_project_user`.

#### 3.2.3 `project_expenses`（implemented）

**说明**：项目级别费用记录，用于跟踪项目产生的非广告消耗支出。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGSERIAL | PK | 费用记录ID |
| `project_id` | BIGINT | FK → `projects.id` ON DELETE CASCADE, NOT NULL | 所属项目 |
| `expense_type` | VARCHAR(50) | NOT NULL | 费用类型（如 setup_fee/service_fee/other） |
| `amount` | DECIMAL(15,2) | NOT NULL, CHECK >= 0 | 费用金额 |
| `currency` | VARCHAR(10) | DEFAULT 'CNY' | 币种 |
| `occurred_at` | DATE | NOT NULL | 费用发生日期 |
| `description` | TEXT | 可空 | 费用描述 |
| `created_by` | UUID | FK → `users.id`, NOT NULL | 创建人 |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |

索引：`idx_project_expenses_project`, `idx_project_expenses_type`, `idx_project_expenses_occurred_at`.

#### 3.2.4 `channels`（implemented）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` UUID PK | |
| `name` VARCHAR(200) | 渠道名称 |
| `platform` VARCHAR(50) | 平台（如 Facebook/Google） |
| `status` VARCHAR(20) | 参考“渠道状态机”，具体枚举以 STATE_MACHINE.md 为准 |
| `risk_level` VARCHAR(20) | 固定枚举 `low/medium/high` |
| `created_by` UUID FK → `users.id` | |
| `created_at` / `updated_at` TIMESTAMPTZ | | |
| `metadata` JSONB | | |

#### 3.2.5 `channel_contacts`（implemented）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` UUID PK | |
| `channel_id` UUID FK → `channels.id` ON DELETE CASCADE | |
| `full_name` VARCHAR(100) | 联系人姓名 |
| `email` / `phone` VARCHAR | 可空 |
| `contact_role` VARCHAR(50) | 若存在历史值 `manager`，在应用层映射为 `account_manager` |
| `notes` TEXT | |
| `created_at` / `updated_at` TIMESTAMPTZ | | |

#### 3.2.6 `channel_reviews`（implemented）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` UUID PK | |
| `channel_id` UUID FK → `channels.id` | |
| `reviewer_id` UUID FK → `users.id` | |
| `review_status` VARCHAR(20) | 参考“渠道评审状态机”，典型值如 draft/pending/approved/rejected，具体枚举以 STATE_MACHINE.md 为准 |
| `score` JSONB | 评估分项 |
| `comments` TEXT | |
| `created_at` / `updated_at` TIMESTAMPTZ | | |

#### 3.2.7 `channel_account_requests`（implemented）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` UUID PK | |
| `channel_id` UUID FK → `channels.id` | |
| `requested_by` UUID FK → `users.id` | |
| `approved_by` UUID FK → `users.id`, 可空 | |
| `status` VARCHAR(20) | 参考“账户申请状态机”，具体枚举以 STATE_MACHINE.md 为准 |
| `request_payload` JSONB | 申请内容 |
| `created_at` / `updated_at` TIMESTAMPTZ | | |

#### 3.2.8 `channel_performance`（implemented）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` UUID PK | |
| `channel_id` UUID FK → `channels.id` ON DELETE CASCADE | |
| `metric_date` DATE | |
| `impressions` DECIMAL(15,2) | 可记录曝光量等整数值（若需整数可在模型中转换） |
| `clicks` DECIMAL(15,2) | |
| `spend` DECIMAL(15,2) | |
| `conversion_rate` DECIMAL(12,4) | 可空 |
| `created_at` TIMESTAMPTZ | DEFAULT NOW() |

> 仅用于辅助分析，核心决策仍以 `ad_accounts`/`daily_reports` 为准。

#### 3.2.9 `ad_accounts`（implemented）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` BIGSERIAL PK | |
| `project_id` BIGINT FK → `projects.id` | |
| `channel_id` UUID FK → `channels.id` | |
| `supplier_id` UUID | 可空, 所属供应商ID(用于死号迁移规则判断:同供应商vs跨供应商),FK → `suppliers.id` |
| `owner_id` UUID FK → `users.id` | 账户负责人，通常应为 `account_manager` 或 `pitcher`，由 Service 层校验 |
| `name` VARCHAR(200) | 账户别名 |
| `account_code` VARCHAR(100) | 平台编号，UNIQUE |
| `status` VARCHAR(20) | 参考"账户生命周期状态机"，典型值如 new/testing/active/suspended/dead/archived，具体枚举以 STATE_MACHINE.md 为准 |
| `status_reason` TEXT | |
| `spend_limit` DECIMAL(15,2) | DEFAULT 0.00 |
| `currency` VARCHAR(10) | DEFAULT 'CNY' |
| `timezone` VARCHAR(50) | DEFAULT 'Asia/Shanghai' |
| `deposit` DECIMAL(15,2) | DEFAULT 0.00, CHECK >= 0, 押款金额（代理商未消耗余额，计算公式：押款 = Σ历史充值 - Σ历史消耗，引用 PRD v5.1 §3.3, MASTER.md v4.8 §术语定义） |
| `deposit_updated_at` TIMESTAMPTZ | 可空, 押款最后更新时间 |
| `created_by` / `updated_by` UUID | FK → `users.id` |
| `created_at` / `updated_at` TIMESTAMPTZ | | |

索引：`idx_ad_accounts_project`, `idx_ad_accounts_channel`, `idx_ad_accounts_status`, `idx_ad_accounts_deposit`.

##### `account_status_history`

字段：`id`, `ad_account_id`, `from_status`, `to_status`, `changed_by`, `changed_at`, `notes`。状态枚举以“账户状态机”为准。

##### `account_alerts`

字段：`id`, `ad_account_id`, `alert_type`, `severity`（固定 `info/warning/critical`）、`status`（参考“账户预警状态机”），`message`, `created_at`, `resolved_at`, `resolved_by`.

##### `account_documents`

字段：`id`, `ad_account_id`, `document_type`, `storage_path`, `file_name`, `uploaded_by`, `uploaded_at`, `notes`.

##### `account_notes`（implemented）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` BIGSERIAL PK | |
| `ad_account_id` BIGINT FK → `ad_accounts.id` ON DELETE CASCADE | |
| `author_id` UUID FK → `users.id` | |
| `note_type` VARCHAR(20) | 固定枚举，如 `general`, `risk`, `finance` |
| `content` TEXT | |
| `created_at` TIMESTAMPTZ | DEFAULT NOW() |

---

### 3.3 日报与投放数据

#### 3.3.1 `daily_reports`（implemented）

**说明**：
- 日报表记录每日投放数据，遵循**日报三层数据**架构（BR-RPT.md v1.1, PRD v5.2 §1.3）：

| 数据层 | 来源 | 内容 | 性质 | 字段映射 |
|--------|------|------|------|----------|
| **申报数据** | 投手填报 | 消耗、成效、进粉 | 参考值（可能有误差） | `conversions_raw`, `raw_spend` |
| **实际数据** | 平台拉取 + PM核对 | 真实消耗、真实成效 | 成本计算依据 | `real_spend` |
| **结算数据** | PM确认（与客户对账后） | 有效线索数、结算金额 | 收入计算依据 | `conversions_final` |

- **字段详解**：
  - **行为记录层**：投手日报（参考值，非财务依据）
    - `conversions_raw`：投手上报进粉数，用于趋势监控
    - `raw_spend`：投手上报消耗，用于趋势风控
  - **实际数据层**：平台拉取/项目经理统计（成本 SoT）
    - `real_spend`：实际消耗，成本核算基准
  - **结算数据层**：甲方确认（收入 SoT）
    - `conversions_final`：甲方确认有效粉数，计费基准

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` BIGSERIAL PK | |
| `report_date` DATE NOT NULL | |
| `ad_account_id` BIGINT FK → `ad_accounts.id` | |
| `campaign_name`, `ad_group_name`, `ad_creative_name` VARCHAR(200) | 可空 |
| `impressions`, `clicks`, `conversions`, `new_follows` INTEGER | DEFAULT 0 |
| `conversions_raw` INTEGER | DEFAULT 0, 投手提交的原始粉数(T+0 23:59前),用于趋势风控(TF-001/002/003规则),不参与计费（行为记录层） |
| `conversions_final` INTEGER | DEFAULT 0, 运营确认的最终粉数(T+1 14:00前),计费基准,公式: `revenue = conversions_final × unit_price`（结算数据层，收入 SoT） |
| `raw_spend` DECIMAL(15,2) | DEFAULT 0.00, 投手提交的原始消耗(T+0 23:59前),用于趋势风控(TF-003规则),不计成本（行为记录层） |
| `real_spend` DECIMAL(15,2) | DEFAULT 0.00, 运营录入的真实消耗(T+1 12:00前),成本核算基准,公式: `cost = real_spend + fee`（实际数据层，成本 SoT） |
| `unit_price` DECIMAL(15,2) | DEFAULT 0.00, 单粉价格,从项目继承(`projects.unit_price`),用于计算收入 |
| `cpc`, `cpa`, `ctr`, `roi` DECIMAL(12,4) | 可空 |
| `status` VARCHAR(20) | 日报状态（STATE_MACHINE.md v2.8 §8, PRD_AI_v1.0.md §4.1）。**Phase 1（当前生效）**: 3 状态简化模型 `raw_submitted → trend_ok → final_confirmed`，无自动风控阻断，项目负责人手动审核。**Phase 2（未来启用）**: 8 状态完整模型 `raw_submitted → trend_pending → trend_ok/trend_flagged → trend_resolved → final_pending → final_confirmed → final_locked`。终态为 `final_locked`（计费锁定）。|
| `trend_flag` VARCHAR(20) | DEFAULT 'normal', 趋势异常标记, 固定枚举: `normal/flagged/resolved` |
| `trend_flag_reason` TEXT | 可空, 风控规则触发原因(如"TF-001: 粉数骤降50%") |
| `trend_resolution_note` TEXT | 可空, 运营复核说明(`project_owner`填写) |
| `final_locked_at` TIMESTAMPTZ | 可空, 计费锁定时间戳(系统自动设置,`status=final_locked`时) |
| `notes` TEXT | |
| `attachments` JSONB | |
| `created_by`, `updated_by`, `submitted_by`, `audit_user_id` UUID | FK → `users.id` |
| `created_at`, `updated_at`, `submitted_at`, `approved_at` TIMESTAMPTZ | | |

约束：`UNIQUE (report_date, ad_account_id)`。索引：`idx_daily_reports_date`, `idx_daily_reports_account`, `idx_daily_reports_status`, `idx_daily_reports_created_by`.

#### 3.3.2 `daily_report_audit_logs`（implemented）

字段：`id`, `daily_report_id (FK)`, `action`, `old_status`, `new_status`, `audit_user_id`, `audit_time`, `audit_notes`, `ip_address`, `user_agent`。状态枚举以“日报状态机”为准。

#### 3.3.3 `ad_spend_daily`（implemented）

字段：`id` (UUID PK), `source_platform`, `ad_account_code`, `spend_date`, `spend_amount DECIMAL(15,2)`, `currency`, `raw_payload JSONB`, `imported_by`, `imported_at`。

#### 3.3.4 `weekly_briefs`（implemented）

周度简报表，记录项目周度汇报。状态机：draft → submitted (终态)。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` BIGSERIAL PK | | 周报ID |
| `project_id` BIGINT FK → `projects.id` | NOT NULL | 项目ID |
| `week_start` DATE | NOT NULL | 周开始日期（周一） |
| `week_end` DATE | NOT NULL | 周结束日期（周日） |
| `submitter_id` UUID FK → `users.id` | | 提交人ID |
| `status` VARCHAR(20) | NOT NULL DEFAULT 'draft' | 状态（draft/submitted） |
| `weekly_spend` DECIMAL(15,2) | NOT NULL DEFAULT 0.00 | 周消耗 |
| `weekly_conversions` INTEGER | NOT NULL DEFAULT 0 | 周进粉 |
| `weekly_cpl` DECIMAL(10,2) | NOT NULL DEFAULT 0.00 | 周CPL |
| `achievements` TEXT | | 本周成果 |
| `issues` TEXT | | 遇到问题 |
| `solutions` TEXT | | 解决方案 |
| `next_week_plan` TEXT | | 下周计划 |
| `submitted_at` TIMESTAMPTZ | | 提交时间 |
| `created_at` / `updated_at` TIMESTAMPTZ | | 时间戳 |

约束：`UNIQUE (project_id, week_start)`，`CHECK (status IN ('draft', 'submitted'))`，`CHECK (week_end >= week_start)`。

索引：`idx_weekly_briefs_project`, `idx_weekly_briefs_week`, `idx_weekly_briefs_submitter`, `idx_weekly_briefs_status`, `idx_weekly_briefs_project_week`.

SoT Reference: B3-weekly-brief.md §2.2, STATE_MACHINE.md v2.8 §4（周报状态机）

---

### 3.4 充值与资金

#### 3.4.1 `topup_requests`（implemented）

**说明**：
- 充值申请表，遵循**充值审批链**（PRD v5.1 §6.1）：投手申请 → 户管收集 → 财务审批 → 转账
- 日常充值不需要老板逐笔审批，老板可随时查看资金状态并介入
- 手续费已包含在充值金额中，不单独记录

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` BIGSERIAL PK | |
| `request_no` VARCHAR(50) UNIQUE | |
| `project_id` BIGINT FK → `projects.id` | |
| `ad_account_id` BIGINT FK → `ad_accounts.id`, 可空 | |
| `applicant_id` UUID FK → `users.id` | 申请人（通常为投手） |
| `amount` DECIMAL(15,2) NOT NULL | 充值金额（含手续费） |
| `currency` VARCHAR(10) | DEFAULT 'CNY' |
| `urgency_level` VARCHAR(20) | 固定枚举 `low/normal/high/urgent`（非状态机） |
| `status` VARCHAR(20) | 参考"充值状态机"，典型值如 draft/pending_review/finance_approve/paid/completed/rejected/cancelled，具体枚举以 STATE_MACHINE.md 为准 |
| `status_reason` TEXT | |
| `expected_pay_date` DATE | |
| `voucher_url` TEXT | |
| `created_by` / `updated_by` UUID | |
| `created_at` / `updated_at` TIMESTAMPTZ | | |

索引：`idx_topup_requests_project`, `idx_topup_requests_status`, `idx_topup_requests_applicant`.

#### 3.4.2 `topup_transactions`（implemented）

字段：`id`, `topup_request_id (FK)`, `paid_amount`, `paid_currency`, `payment_method`, `payment_reference`, `paid_at`, `receipt_url`, `created_by`, `notes`。`payment_method` 固定枚举 `bank_transfer/alipay/wechat/paypal/credit_card/other`.

#### 3.4.3 `topup_approval_logs`（implemented）

字段：`id`, `topup_request_id`, `action`, `from_status`, `to_status`, `operator_id`, `comments`, `created_at`。状态枚举以“充值状态机”为准。

#### 3.4.4 `ledger_entries`（implemented）

**说明**：三本账体系核心表，记录所有资金流水（来源: BR-FIN.md v1.1 §BR-FIN-009）。

**三本账体系**：
| 账本 | 对应 ledger_type | 记录内容 | 余额含义 |
|------|-----------------|----------|----------|
| 预付款账本 | PROJECT | 客户付给我们的钱 | 还"欠"客户多少（待消耗） |
| 充值账本 | SUPPLIER | 我们充给代理商的钱 | 累计投入多少 |
| 押款账本 | (计算值) | 充值 - 消耗 | 押在代理商的钱（资金占用） |

> ⚠️ **注意**：押款账本是计算值（`SUM(TOPUP) - SUM(COST)`），不是独立的 ledger_type。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGSERIAL | PK | 账目ID |
| `ledger_type` | VARCHAR(20) | NOT NULL, CHECK | 账本类型：`PROJECT`（项目收入）/ `SUPPLIER`（供应商成本） |
| `project_id` | BIGINT | FK → `projects.id`, 条件必填 | 项目ID（PROJECT 账本必填） |
| `supplier_id` | UUID | FK → `suppliers.id`, 条件必填 | 供应商ID（SUPPLIER 账本必填） |
| `ad_account_id` | BIGINT | FK → `ad_accounts.id`, 可空 | 关联广告账户 |
| `entry_type` | VARCHAR(20) | NOT NULL, CHECK | 条目类型（见下方枚举） |
| `amount` | DECIMAL(15,2) | NOT NULL | 金额：借方为正，贷方为负，红冲为负 |
| `currency` | VARCHAR(10) | DEFAULT 'CNY' | 币种 |
| `reference_id` | BIGINT | 可空 | 关联ID（充值/日报/原账目） |
| `occurred_at` | TIMESTAMPTZ | NOT NULL | 发生时间 |
| `created_by` | UUID | FK → `users.id`, NOT NULL | 创建人 |
| `notes` | TEXT | 可空 | 备注 |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |

**entry_type 枚举**（6种）：

| 类型 | 说明 | 允许账本 |
|------|------|----------|
| `REVENUE` | 粉数计费收入 | PROJECT |
| `COST` | 真实消耗成本 | SUPPLIER |
| `TOPUP` | 充值入账 | PROJECT, SUPPLIER |
| `TRANSFER_OUT` | 死号余额迁出 | SUPPLIER |
| `TRANSFER_IN` | 死号余额迁入 | SUPPLIER |
| `REVERSAL` | 红冲修正（final_locked 后） | PROJECT, SUPPLIER |

**CHECK 约束**（SQL）：
```sql
-- 账本类型约束
CHECK (ledger_type IN ('PROJECT', 'SUPPLIER'))

-- 条目类型约束
CHECK (entry_type IN ('REVENUE', 'COST', 'TOPUP', 'TRANSFER_OUT', 'TRANSFER_IN', 'REVERSAL'))

-- 账本与必填字段关联约束
CHECK (
  (ledger_type = 'PROJECT' AND project_id IS NOT NULL) OR
  (ledger_type = 'SUPPLIER' AND supplier_id IS NOT NULL)
)

-- 账本与条目类型匹配约束
CHECK (
  (ledger_type = 'PROJECT' AND entry_type IN ('REVENUE', 'TOPUP', 'REVERSAL')) OR
  (ledger_type = 'SUPPLIER' AND entry_type IN ('COST', 'TOPUP', 'TRANSFER_OUT', 'TRANSFER_IN', 'REVERSAL'))
)
```

**计费公式** (BRD v3.1 第7-8章, PRD_AI_v1.0.md §5):
- PROJECT 账本收入: `revenue = conversions_final × unit_price`（固定单价，BR-REV-001）
- PROJECT 账本收入: `revenue = Σ(档位线索数 × 该档单价)`（阶梯定价，BR-REV-002）
- PROJECT 账本收入: `revenue = ad_spend × (1 + service_fee_rate)`（服务费收入，BR-REV-003）
- SUPPLIER 账本成本: `cost = real_spend + fee`
- 项目毛利: `profit = revenue - cost`
- 押款: `deposit = Σtopups - Σreal_spends`（实时计算，BR-COST-003）
- CPL: `cpl = ad_spend / conversions_final`

**索引**：`idx_ledger_project`, `idx_ledger_supplier`, `idx_ledger_entry_type`, `idx_ledger_type`, `idx_ledger_occurred_at`.

#### 3.4.5 `receivable`（implemented）

> **引用**: MASTER.md v4.8 §4.5.5 —— `receivable.amount WHERE status='received'` 为「已回款」的唯一事实源
>
> ✅ **已实现**: 迁移文件 `20260102_add_receivable_table.py`

**说明**：回款记录表，记录项目的客户回款信息。是"已回款"数据的唯一事实源。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGSERIAL | PK | 回款记录唯一标识 |
| `project_id` | BIGINT | FK → `projects.id` ON DELETE RESTRICT, NOT NULL | 所属项目 |
| `amount` | DECIMAL(15,2) | NOT NULL, CHECK > 0 | 回款金额（必须为正数） |
| `status` | VARCHAR(20) | NOT NULL DEFAULT 'pending', CHECK | 回款状态：`pending`（待确认）/ `received`（已到账）/ `cancelled`（已取消） |
| `received_at` | TIMESTAMPTZ | 可空 | 实际到账时间（status='received'时必填） |
| `source` | VARCHAR(50) | 可空 | 回款来源（客户名/渠道等） |
| `invoice_no` | VARCHAR(100) | 可空 | 发票编号 |
| `notes` | TEXT | 可空 | 备注说明 |
| `recorded_by` | UUID | FK → `users.id`, NOT NULL | 记录人 |
| `confirmed_by` | UUID | FK → `users.id`, 可空 | 确认人（status='received'时填充） |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

**约束**:
- `status` CHECK 约束：`status IN ('pending', 'received', 'cancelled')`
- `amount` CHECK 约束：`amount > 0`
- 业务约束：`status='received'` 时 `received_at` 不能为空

**已回款 SoT 计算公式**:
```sql
SELECT SUM(amount) FROM receivable WHERE status = 'received' AND project_id = ?
```

索引：`idx_receivable_project`, `idx_receivable_status`, `idx_receivable_received_at`, `idx_receivable_created_at`.

#### 3.4.6 `suppliers`（implemented）

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | UUID | PK | 供应商唯一标识 |
| `name` | TEXT | NOT NULL | 供应商名称 |
| `code` | TEXT | UNIQUE NOT NULL | 供应商编码 |
| `balance` | NUMERIC(15,2) | DEFAULT 0.00 | 供应商账户余额 |
| `status` | VARCHAR(20) | NOT NULL | 供应商状态, 参考"供应商状态机"，具体枚举以 STATE_MACHINE.md 为准 |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

索引：`idx_suppliers_code`, `idx_suppliers_status`.

#### 3.4.7 `transfer_requests`（implemented）

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGSERIAL | PK | 迁移申请唯一标识 |
| `request_no` | VARCHAR(50) | UNIQUE NOT NULL | 迁移申请编号 |
| `source_ad_account_id` | BIGINT | FK → `ad_accounts.id` NOT NULL | 源账户(死号) |
| `target_ad_account_id` | BIGINT | FK → `ad_accounts.id` NOT NULL | 目标账户(接收方) |
| `transfer_amount` | NUMERIC(15,2) | NOT NULL | 迁移金额 |
| `status` | VARCHAR(20) | NOT NULL | 迁移状态, 参考"死号余额迁移状态机"，典型值如 draft/pending_approval/approved/rejected/completed，具体枚举以 STATE_MACHINE.md 为准 |
| `version` | INTEGER | DEFAULT 1 | 乐观锁版本号 |
| `created_by` | UUID | FK → `users.id` | 申请人 |
| `approved_by` | UUID | FK → `users.id`, 可空 | 审批人 |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |
| `approved_at` | TIMESTAMPTZ | 可空 | 审批时间 |

索引：`idx_transfer_requests_request_no`, `idx_transfer_requests_source_account`, `idx_transfer_requests_target_account`, `idx_transfer_requests_status`.

---

### 3.5 对账模块

#### 3.5.1 `reconciliation_batches`（implemented）

字段：`id`, `batch_no` (UNIQUE), `project_id`, `status`（参考"对账批次状态机"，合法值: `draft/pending_review/approved/needs_adjustment/completed`，具体枚举以 STATE_MACHINE.md v2.8 为准）, `source`, `period_start`, `period_end`, `created_by`, `approved_by`, `created_at`, `updated_at`.

#### 3.5.2 `reconciliation_details`（implemented）

字段：`id`, `batch_id (FK)`, `ad_account_id`, `report_date`, `system_spend`, `external_spend`, `difference_amount`, `status`（参考“对账明细状态机”，典型值如 pending/confirmed/adjusted，具体枚举以 STATE_MACHINE.md 为准）, `notes`, `created_at`.

#### 3.5.3 `reconciliation_adjustments`（implemented）

字段：`id`, `detail_id (FK)`, `adjustment_type`（固定 `increase/decrease/writeoff`）, `amount DECIMAL(15,2)`, `reason`, `created_by`, `created_at`.

#### 3.5.4 `reconciliation_reports`（implemented）

字段：`id`, `batch_id (FK)`, `generated_at`, `generated_by`, `report_url`, `metrics JSONB`.

#### 3.5.5 `balance_snapshots`（implemented）

> **OpenSpec Change**: `add-reconciliation-control-center`
> **用途**: 广告账户每日余额/押款快照，用于对账守恒公式校验

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGSERIAL | PK | 主键 |
| `ad_account_id` | BIGINT | FK → `ad_accounts.id`, NOT NULL | 关联账户 |
| `snapshot_date` | DATE | NOT NULL | 快照日期 |
| `balance` | DECIMAL(15,2) | NOT NULL | 当日余额 |
| `deposit` | DECIMAL(15,2) | NOT NULL, DEFAULT 0 | 当日押款 |
| `remaining_balance` | DECIMAL(15,2) | NOT NULL | 当日剩余可用 = balance - deposit |
| `source` | VARCHAR(20) | NOT NULL, DEFAULT 'manual', CHECK | 数据来源：manual/api/import |
| `created_by` | UUID | FK → `users.id`, NOT NULL | 创建人 |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| `notes` | TEXT | 可空 | 备注 |

**约束**:
- UNIQUE (`ad_account_id`, `snapshot_date`) - 每账户每日仅一条快照
- CHECK (`source` IN ('manual', 'api', 'import'))

**索引**: `idx_balance_snapshots_date`, `idx_balance_snapshots_account`, `idx_balance_snapshots_account_date`.

**业务规则引用**: BR-REC-001 对账守恒公式, BR-REC-003 快照缺失处理

#### 3.5.6 `reconciliation_issues`（implemented）

> **OpenSpec Change**: `add-reconciliation-control-center`
> **用途**: 对账差异单表，追踪对账发现的差异及其处理过程

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGSERIAL | PK | 主键 |
| `reconciliation_batch_id` | BIGINT | FK → `reconciliation_batches.id`, 可空 | 关联批次 |
| `ad_account_id` | BIGINT | FK → `ad_accounts.id`, 可空 | 关联账户 |
| `issue_date` | DATE | NOT NULL | 差异日期 |
| `issue_type` | VARCHAR(30) | NOT NULL, CHECK | 差异类型 |
| `expected_amount` | DECIMAL(15,2) | 可空 | 预期金额 |
| `actual_amount` | DECIMAL(15,2) | 可空 | 实际金额 |
| `difference_amount` | DECIMAL(15,2) | GENERATED | 差异金额 = actual - expected |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'open' | 参考"对账差异单状态机"(STATE_MACHINE.md v2.8 §11.4) |
| `assigned_to` | UUID | FK → `users.id`, 可空 | 责任人 |
| `assigned_at` | TIMESTAMPTZ | 可空 | 分配时间 |
| `resolution_type` | VARCHAR(30) | CHECK, 可空 | 处理类型 |
| `resolution_note` | TEXT | 可空 | 处理说明 |
| `resolved_at` | TIMESTAMPTZ | 可空 | 处理时间 |
| `resolved_by` | UUID | FK → `users.id`, 可空 | 处理人 |
| `attachments` | JSONB | DEFAULT '[]'::jsonb | 附件 |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| `created_by` | UUID | FK → `users.id`, NOT NULL | 创建人 |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |
| `sla_deadline` | TIMESTAMPTZ | 可空 | SLA 截止时间 |
| `sla_breached` | BOOLEAN | DEFAULT FALSE | SLA 超时标记 |

**issue_type 枚举值**:
- `topup_mismatch` - 充值差异
- `spend_mismatch` - 消耗差异
- `deposit_change` - 押款变化
- `balance_anomaly` - 余额异常
- `snapshot_missing` - 快照缺失
- `conservation_failed` - 守恒校验失败
- `other` - 其他

**resolution_type 枚举值**:
- `data_correction` - 数据修正
- `ledger_adjustment` - 账本调整
- `external_confirm` - 外部确认（代理商/甲方）
- `write_off` - 核销
- `false_positive` - 误报

**约束**:
- CHECK (`issue_type` IN ('topup_mismatch', 'spend_mismatch', 'deposit_change', 'balance_anomaly', 'snapshot_missing', 'conservation_failed', 'other'))
- CHECK (`status` IN ('open', 'assigned', 'investigating', 'resolved', 'closed'))
- CHECK (`resolution_type` IS NULL OR `resolution_type` IN ('data_correction', 'ledger_adjustment', 'external_confirm', 'write_off', 'false_positive'))

**索引**: `idx_rec_issues_status`, `idx_rec_issues_date`, `idx_rec_issues_assigned`, `idx_rec_issues_batch`.

**状态机引用**: STATE_MACHINE.md v2.8 §11.4 对账差异单状态机

#### 3.5.7 `settlement_rules`（implemented）

> **OpenSpec Change**: `add-reconciliation-control-center`
> **用途**: 结算规则配置表，支持阶梯计价(tiered)和加成计价(markup)

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGSERIAL | PK | 主键 |
| `name` | VARCHAR(100) | NOT NULL | 规则名称 |
| `rule_type` | VARCHAR(20) | NOT NULL, CHECK | 规则类型：tiered/markup |
| `config` | JSONB | NOT NULL | 规则配置（JSON Schema 校验） |
| `effective_from` | DATE | NOT NULL | 生效开始日 |
| `effective_to` | DATE | 可空 | 生效结束日 |
| `created_by` | UUID | FK → `users.id`, NOT NULL | 创建人 |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

**rule_type 枚举值**:
- `tiered` - 阶梯计价
- `markup` - 加成计价

**config JSON Schema (tiered)**:
```json
{
  "tiers": [
    {"min": 0, "max": 1000, "price": 50},
    {"min": 1001, "max": 5000, "price": 45},
    {"min": 5001, "max": null, "price": 40}
  ],
  "calculation_basis": "cumulative" | "incremental"
}
```

**config JSON Schema (markup)**:
```json
{
  "base_cost_field": "real_spend" | "raw_spend",
  "markup_type": "percentage" | "fixed",
  "markup_value": 15
}
```

**约束**:
- CHECK (`rule_type` IN ('tiered', 'markup'))
- CHECK (`effective_to` IS NULL OR `effective_to` > `effective_from`)

**索引**: `idx_settlement_rules_type`, `idx_settlement_rules_effective`.

**业务规则引用**: BR-SET-001 Fixed 结算规则, BR-SET-002 Tiered 结算规则, BR-SET-003 Markup 结算规则

---

### 3.6 利润表模块

> **设计来源**: `PROFIT_SOT.md` v1.1
> **OpenSpec Change**: `finance-profit-v1`
> **依赖 SoT**: DATA_SCHEMA.md v5.6 §3.4.4（账本规则，双账本模型）, STATE_MACHINE.md v2.8（粉数确认状态机）

#### 3.6.1 `profit_aggregates`（planned）

**说明**：L2 汇总层核心表，存储按周期/维度聚合的利润数据。聚合来源为 `daily_reports`（仅 `final_locked` 状态）和 `ledger_entries`。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGSERIAL | PK | 主键 |
| `period_type` | VARCHAR(20) | NOT NULL, CHECK IN ('daily', 'weekly', 'monthly') | 周期类型 |
| `period_start` | TIMESTAMPTZ | NOT NULL | 周期开始时间 |
| `period_end` | TIMESTAMPTZ | NOT NULL | 周期结束时间 |
| `project_id` | BIGINT | FK → `projects.id`, 可空 | 项目ID，NULL 表示全局汇总 |
| `ad_account_id` | BIGINT | FK → `ad_accounts.id`, 可空 | 账户ID，NULL 表示项目级汇总 |
| `total_revenue` | DECIMAL(18,2) | NOT NULL, DEFAULT 0.00 | 总收入，派生字段：`SUM(ledger_entries.amount WHERE entry_type='REVENUE')` |
| `total_cost` | DECIMAL(18,2) | NOT NULL, DEFAULT 0.00 | 总成本，派生字段：`ABS(SUM(ledger_entries.amount WHERE entry_type='COST'))` |
| `gross_profit` | DECIMAL(18,2) | NOT NULL, DEFAULT 0.00 | 毛利，派生字段：`total_revenue - total_cost` |
| `gross_margin_pct` | DECIMAL(5,2) | 可空 | 毛利率(%)，派生字段：`(gross_profit / total_revenue) × 100`，HALF_UP 四舍五入，revenue=0 时为 NULL |
| `total_conversions` | INTEGER | DEFAULT 0 | 转化数，派生字段：`SUM(daily_reports.conversions_final WHERE status='final_locked')` |
| `total_real_spend` | DECIMAL(18,2) | DEFAULT 0.00 | 实际消耗，派生字段：`SUM(daily_reports.real_spend WHERE status='final_locked')` |
| `total_topup` | DECIMAL(18,2) | DEFAULT 0.00 | 充值金额，⚠️ 仅用于资金流入统计，不参与毛利计算 |
| `transfer_in` | DECIMAL(18,2) | DEFAULT 0.00 | 转入金额，派生字段：`SUM(ledger_entries.amount WHERE entry_type='TRANSFER_IN')` |
| `transfer_out` | DECIMAL(18,2) | DEFAULT 0.00 | 转出金额，派生字段：`ABS(SUM(ledger_entries.amount WHERE entry_type='TRANSFER_OUT'))` |
| `is_locked` | BOOLEAN | DEFAULT FALSE | 是否锁定，锁定后不可重新生成 |
| `locked_at` | TIMESTAMPTZ | 可空 | 锁定时间 |
| `locked_by` | UUID | FK → `users.id`, 可空 | 锁定人 |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

**约束**：
- UNIQUE (`period_type`, `period_start`, `project_id`, `ad_account_id`) - 防止重复聚合

**索引**：`idx_profit_agg_period_type`, `idx_profit_agg_period_start`, `idx_profit_agg_project`, `idx_profit_agg_account`, `idx_profit_agg_locked`.

**业务规则引用**：
- BR-PROFIT-001: `gross_profit = total_revenue - total_cost`
- BR-PROFIT-002: `total_topup` 不参与利润计算
- BR-PROFIT-003: 仅聚合 `daily_reports.status = 'final_locked'` 的数据
- BR-PROFIT-005: `is_locked = TRUE` 时禁止重新生成

#### 3.6.2 `profit_report_snapshots`（planned）

**说明**：报表快照层，存储生成的利润报表 JSON 数据，支持 draft/confirmed/locked 三态管理。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGSERIAL | PK | 主键 |
| `report_type` | VARCHAR(30) | NOT NULL, CHECK IN ('monthly_summary', 'project_detail', 'account_detail') | 报表类型 |
| `period_month` | VARCHAR(7) | NOT NULL | 月份，格式 YYYY-MM |
| `project_id` | BIGINT | FK → `projects.id`, 可空 | 项目ID，NULL 表示全局报表 |
| `report_data` | JSONB | NOT NULL | 报表数据，包含聚合指标和明细 |
| `status` | VARCHAR(20) | NOT NULL, CHECK IN ('draft', 'confirmed', 'locked'), DEFAULT 'draft' | 报表状态 |
| `generated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 生成时间 |
| `generated_by` | UUID | FK → `users.id`, NOT NULL | 生成人 |
| `confirmed_at` | TIMESTAMPTZ | 可空 | 确认时间 |
| `confirmed_by` | UUID | FK → `users.id`, 可空 | 确认人 |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |

**约束**：
- UNIQUE (`report_type`, `period_month`, `project_id`) - 同类型同月份同项目仅一份报表

**索引**：`idx_profit_snap_report_type`, `idx_profit_snap_period_month`, `idx_profit_snap_project`, `idx_profit_snap_status`.

**业务规则引用**：
- BR-PROFIT-006: 月度报表基于 L2 聚合层 (`profit_aggregates`) 生成

---

### 3.7 月度结算模块

#### 3.7.1 monthly_settlements (月度结算表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | BIGSERIAL | PK | 主键 |
| `project_id` | BIGINT | FK → `projects.id`, NOT NULL | 项目ID |
| `settlement_month` | DATE | NOT NULL, CHECK (DAY = 1) | 结算月份 (YYYY-MM-01) |
| `total_spend` | DECIMAL(15,2) | NOT NULL, DEFAULT 0, CHECK >= 0 | 月消耗总额 |
| `total_conversions` | INTEGER | NOT NULL, DEFAULT 0, CHECK >= 0 | 月进粉总数 |
| `total_revenue` | DECIMAL(15,2) | NOT NULL, DEFAULT 0 | 月收入（粉数 × 单价） |
| `gross_profit` | DECIMAL(15,2) | NOT NULL, DEFAULT 0 | 月毛利（收入 - 消耗） |
| `average_cpl` | DECIMAL(10,2) | 可空 | 月均 CPL |
| `status` | VARCHAR(20) | NOT NULL, CHECK IN ('pending', 'confirmed', 'locked', 'archived'), DEFAULT 'pending' | 状态 (STATE_MACHINE.md v2.8 §13.1) |
| `confirmed_at` | TIMESTAMPTZ | 可空 | 财务确认时间 |
| `confirmed_by` | UUID | FK → `users.id`, 可空 | 确认人 |
| `locked_at` | TIMESTAMPTZ | 可空 | 锁定时间 |
| `locked_by` | UUID | FK → `users.id`, 可空 | 锁定人 |
| `notes` | TEXT | 可空 | 结算备注 |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

**约束**：
- UNIQUE (`project_id`, `settlement_month`) - 每个项目每月仅一条结算记录
- CHECK (`settlement_month` 的 DAY 部分必须为 1)

**索引**：`idx_monthly_settlements_project`, `idx_monthly_settlements_month`, `idx_monthly_settlements_status`.

**状态机引用**：STATE_MACHINE.md v2.8 §13.1 月度结算状态机

**计算公式**（引用 BUSINESS_RULES.md，遵循三层数据架构）：
- `total_spend`: SUM(daily_reports.real_spend) WHERE status = 'final_locked' AND 月份匹配（**成本 SoT**，使用实际数据层）
- `total_conversions`: SUM(daily_reports.conversions_final) WHERE status = 'final_locked' AND 月份匹配（**收入 SoT**，使用结算数据层）
- `total_revenue`: total_conversions × projects.unit_price
- `gross_profit`: total_revenue - total_spend
- `average_cpl`: total_spend / total_conversions (若 total_conversions > 0)

> ⚠️ **重要**：禁止使用 `raw_spend` 或 `conversions_raw` 进行结算计算，这些字段仅用于趋势风控（行为记录层）。

---

### 3.8 公司运营支出

#### 3.8.1 `company_expenses`（implemented）

**说明**：公司级运营支出记录，不进入项目账本（见 DATA_SCHEMA.md v5.6 §3.4.4 账本规则）。用于记录工资、服务费、汇率损益等非广告业务支出。

**成本分类**（PRD v5.1 §2.1）：
- **ad_topup**：广告费充值（含手续费），分摊到项目
- **ad_support**：广告配套（BM/IP/主页/个号等），公司统一记账，**不分摊到项目**
- **overhead**：后勤支出（工资/房租/日常等），公司统一记账，**不分摊到项目**

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGSERIAL | PK | 支出ID |
| `expense_type` | VARCHAR(50) | NOT NULL | 支出类型：`ad_topup`/`ad_support`/`overhead`（PRD v5.1 §2.1 成本分类）或 salary/setup_fee/service_fee/exchange/reimbursement/other |
| `category` | VARCHAR(50) | NOT NULL, CHECK | 分类：operation/hr/infrastructure/tools/other |
| `amount` | DECIMAL(15,2) | NOT NULL | 金额 |
| `currency` | VARCHAR(10) | DEFAULT 'USD' | 币种 |
| `occurred_at` | DATE | NOT NULL | 发生日期 |
| `description` | TEXT | 可空 | 描述 |
| `receipt_url` | TEXT | 可空 | 收据URL |
| `status` | VARCHAR(20) | DEFAULT 'pending', CHECK | 状态：pending/approved/rejected/paid |
| `created_by` | UUID | FK → `users.id` | 创建人 |
| `approved_by` | UUID | FK → `users.id`, 可空 | 审批人 |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

**约束**：
- CHECK (category IN ('operation', 'hr', 'infrastructure', 'tools', 'other'))
- CHECK (status IN ('pending', 'approved', 'rejected', 'paid'))

**索引**：`idx_company_expenses_category`, `idx_company_expenses_occurred_at`, `idx_company_expenses_status`, `idx_company_expenses_created_by`.

**SoT Reference**: DATA_SCHEMA.md v5.6 §3.4.4 (不进入账本，见账本规则)


---

## 4. 索引与约束策略

1. **唯一性**：`request_no`, `account_code`, `(report_date, ad_account_id)` 等必须建唯一索引并在模型层校验。  
2. **组合索引**：针对高频过滤场景建立，如 `daily_reports(report_date, status)`、`topup_requests(project_id, status)`、`ledger_entries(project_id, occurred_at)`。  
3. **CHECK 约束**：角色字段仅允许 4 个技术层角色值（admin/finance/account_manager/media_buyer），`project_owner` 通过 `is_project_owner=true` 业务属性判断；业务层角色到技术层的映射见 AUTH_SPEC.md v2.1 §2.2, MASTER.md v4.8 §INV-007；状态字段 CHECK 应引用相应状态机；金额字段若允许负值需在说明写明。  
4. **外键一致性**：外键字段类型必须与被引用主键一致，迁移旧字段时需同步更新 FK 定义与索引。  
5. **触发器**：`users` 使用 `update_users_updated_at`；其他表如需类似逻辑必须在本文件登记。

---

## 5. 历史兼容与规划说明

- **`users` 表**：业务层用户资料表，主键为 UUID，外键关联 `auth.users(id)`。`auth.users` 用于认证（Supabase Auth 内置用户表），`users` 用于业务逻辑（角色、权限、扩展信息等）。
- **历史兼容**：旧代码中可能使用 `user_profiles` 表名，已统一改为 `users`。如发现遗留的 `user_profiles` 引用，请更新为 `users`。所有外键必须指向 `users.id`（UUID），不再使用 `user_profiles`。  
- **旧角色名**：`manager` = `account_manager`，`data_clerk` = `finance`，`data_operator` = `project_owner`/`finance`（MASTER v4.8 废弃，PRD v5.2 已对齐）。历史数据可读，新增逻辑禁止使用旧名。  
- **`roles` 表**：标记为 `status: legacy`，仅用于兼容查询。  
- **RLS**：部分迁移脚本包含 `ENABLE ROW LEVEL SECURITY`，当前版本规划中未启用（`ENABLE_RLS=false`），仅应用层RBAC；若未来启用须同步更新本文件与实现 SoT。  
- **规划表**：如需新增表/字段，必须先在本文件创建 `status: planned` 条目并描述字段，再提交迁移。未登记的变更不予实施。

---

## 6. 使用指南与自检

1. **Schema 变更流程**：  
   - 编写 Alembic 迁移  
   - 更新 SQLAlchemy 模型  
   - 更新本文件  
   - 通知 API/前端/QA  
2. **AI 使用要求**：prompt 中必须包含本文件及所有互锁 SoT，AI 禁止自创字段/状态/角色。  
3. **自检清单**：  
   - [ ] 主键/外键类型一致
   - [ ] 金额字段使用 `DECIMAL(15,2)` 并说明借贷规则
   - [ ] 状态字段引用 `STATE_MACHINE.md` 对应状态机
   - [ ] 角色字段只出现 6 个业务层合法值（MASTER.md v4.8 §2.4）或 4 个技术层合法值（admin/finance/account_manager/media_buyer）
   - [ ] 索引/约束在迁移与本文件中都有记录  
4. **审阅频率**：每次数据库结构变更后立即更新本文件；若长期无变更也需至少每季度审查一次。

---

## 7. 变更历史

### v5.9 (2026-01-02)

- **实现 receivable 表（已回款 SoT）**:
  - 新增迁移文件：`20260102_add_receivable_table.py`
  - 新增模型文件：`backend/models/finance/receivable.py`
  - 表状态：planned → implemented
  - 引用：MASTER.md v4.8 §4.5.5（已回款公式唯一事实源）

### v5.8 (2026-01-02)

- **对齐 PRD_AI_v1.0.md v1.1**:
  - 更新互锁 SoT：MASTER.md v4.7 → v4.8（系统宪法），新增 PRD_AI_v1.0.md v1.1
  - 角色定义：新增角色职责说明表（PRD_AI_v1.0.md §2.1），添加 PRD v5.2 引用
  - 日报状态机：明确 Phase 1（3状态简化模型）vs Phase 2（8状态完整模型）边界
  - 计费公式：扩展公式定义，添加阶梯定价(BR-REV-002)、服务费收入(BR-REV-003)、押款公式(BR-COST-003)、CPL 公式
  - 修正日报状态字段引用：STATE_MACHINE.md v2.9 → v2.8

### v5.7 (2026-01-02)

- **对齐 BR-FIN.md v1.1 三本账体系**:
  - 更新互锁引用：BUSINESS_RULES.md v4.7 → v5.0
  - ledger_entries：「双账本模型」→「三本账体系」（预付款账本、充值账本、押款账本）
  - daily_reports：添加「日报三层数据」架构表（申报数据、实际数据、结算数据）
  - daily_reports.status：更新日报状态机描述，引用 Framework v2.1 §6.3

### v5.6 (2025-12-31)

- 初始 ASDD 元数据规范化
- 角色枚举对齐 MASTER.md v4.8

---

**文档版本**: v5.9
**最后审阅**: 2026-01-02
**维护责任**: 数据库规范守门人（与系统架构团队共管）  
**附注**: 若实现规范、状态机或 API 流程更新，必须同步更新本文件；否则任何生成代码/Schema 迁移将被拒绝。
