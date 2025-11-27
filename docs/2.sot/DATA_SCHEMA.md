# DATA_SCHEMA.md · 数据结构唯一事实来源 (SoT-Data)

> **版本**: v5.2
> **status**: active
> **owner**: wade
> **last_reviewed**: 2025-11-27
> **更新日期**: 2025‑11‑22
> **维护团队**: 系统架构团队（数据库规范守门人）
> **定位**: 描述 AI 广告代投系统全部已落地/规划中的数据库表结构、字段、索引与约束，是数据层唯一事实来源。若其他文档与此冲突，以本文件为准。
> **互锁 SoT**:
> - 实现规范 → `../1.overview/MASTER_SPEC.md` v1.1
> - 状态机 → `STATE_MACHINE.md` v2.6（任何状态字段必须引用对应状态机）
> - 业务规则 → `BUSINESS_RULES.md` v3.1
> - 错误码 → `ERROR_CODES_SOT.md` v2.1
> - 业务需求 → `BRD_chapter1_v3.1.md` (BRD v3.1基线)

---

## 1. 通用约定

### 1.1 技术栈

- **数据库**: PostgreSQL 15（Supabase 托管）
- **ORM / 迁移**: SQLAlchemy（同步版）+ Alembic
- **权限**: 当前版本仅在应用层（Service + `@require_role`）执行 RBAC，数据库 RLS 规划中未启用  
- **时间字段**: 统一使用 `TIMESTAMPTZ`，默认 `NOW()`，应用层使用 UTC  
- **金额字段**: 一律 `DECIMAL(15,2)`，默认 `0.00`，借方为正、贷方为负值  
- **角色枚举**: 仅允许 `admin`, `finance`, `data_operator`, `account_manager`, `media_buyer`；旧角色名只允许出现在“历史兼容”说明  
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
6. 状态相关字段在说明中需指出“枚举值以 STATE_MACHINE.md 为准”。

---

## 2. 表清单（实现状态）

| 表名 | 说明 | 主键 | 状态 |
| --- | --- | --- | --- |
| `users` | 业务用户表（与 Supabase Auth 同步） | UUID | implemented |
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

---

## 3. 详细表结构

> 说明：凡是包含 `status`/`review_status`/`urgency_level` 等状态字段，均在字段描述中注明所属状态机或固定枚举。

### 3.1 用户与权限

#### 3.1.1 `users`（implemented）

**说明**：
- `users` 表是业务层的用户资料表，主键为 UUID
- 主键 `id` 外键关联 `auth.users(id)`（Supabase Auth 内置用户表）
- `auth.users` 用于认证，`users` 用于业务逻辑（角色、权限等）

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | UUID | PK, FK → `auth.users(id)` ON DELETE CASCADE | 与 Supabase Auth 同步 |
| `username` | VARCHAR(50) | UNIQUE | 用户名 |
| `full_name` | VARCHAR(100) | | 真实姓名 |
| `email` | VARCHAR(255) | 可空 | 冗余字段，方便联查 |
| `role` | VARCHAR(20) | NOT NULL, CHECK（合法角色） | 仅 `admin/finance/data_operator/account_manager/media_buyer` |
| `department` / `position` | VARCHAR(100) | | 组织信息 |
| `account_manager_id` | UUID | FK → `users.id` | 投手关联户管 |
| `is_active` | BOOLEAN | DEFAULT true | 账号可用性 |
| `is_verified` | BOOLEAN | DEFAULT false | 资料验证状态 |
| `last_login_at` / `last_login_ip` | TIMESTAMPTZ / VARCHAR(45) | | |
| `preferences`, `notification_settings`, `profile_metadata` | JSONB | DEFAULT `{}` | 扩展配置 |
| `timezone`, `language` | VARCHAR | DEFAULT `'UTC'` / `'zh-CN'` | |
| `created_at` / `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | |
| `created_by` / `updated_by` | UUID | FK → `users.id`, 可空 | |

索引：`idx_users_username`, `idx_users_role`, `idx_users_account_manager`, `idx_users_created_at`, `idx_users_last_login`.

#### 3.1.2 `roles`（legacy）

字段：`id`, `name`, `description`, `created_at`。仅用于旧系统兼容，新功能禁止引用。

#### 3.1.3 `user_sessions`（implemented）

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

#### 3.1.4 `audit_logs`（implemented）

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
| `start_date` / `end_date` DATE | | |
| `created_by` / `updated_by` UUID FK → `users.id` | |
| `created_at` / `updated_at` TIMESTAMPTZ | DEFAULT NOW() | |

索引：`idx_projects_name`, `idx_projects_status`, `idx_projects_account_manager`.

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

字段：`id`, `project_id`, `expense_type`, `amount DECIMAL(15,2)`, `currency`, `occurred_at`, `description`, `created_by`, `created_at`。`project_id` FK → `projects.id`.

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
| `owner_id` UUID FK → `users.id` | 账户负责人，通常应为 `account_manager` 或 `media_buyer`，由 Service 层校验 |
| `name` VARCHAR(200) | 账户别名 |
| `account_code` VARCHAR(100) | 平台编号，UNIQUE |
| `status` VARCHAR(20) | 参考"账户生命周期状态机"，典型值如 new/testing/active/suspended/dead/archived，具体枚举以 STATE_MACHINE.md 为准 |
| `status_reason` TEXT | |
| `spend_limit` DECIMAL(15,2) | DEFAULT 0.00 |
| `currency` VARCHAR(10) | DEFAULT 'CNY' |
| `timezone` VARCHAR(50) | DEFAULT 'Asia/Shanghai' |
| `created_by` / `updated_by` UUID | FK → `users.id` |
| `created_at` / `updated_at` TIMESTAMPTZ | | |

索引：`idx_ad_accounts_project`, `idx_ad_accounts_channel`, `idx_ad_accounts_status`.

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

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` BIGSERIAL PK | |
| `report_date` DATE NOT NULL | |
| `ad_account_id` BIGINT FK → `ad_accounts.id` | |
| `campaign_name`, `ad_group_name`, `ad_creative_name` VARCHAR(200) | 可空 |
| `impressions`, `clicks`, `conversions`, `new_follows` INTEGER | DEFAULT 0 |
| `conversions_raw` INTEGER | DEFAULT 0, 投手提交的原始粉数(T+0 23:59前),用于趋势风控(TF-001/002/003规则),不参与计费 |
| `conversions_final` INTEGER | DEFAULT 0, 运营确认的最终粉数(T+1 14:00前),计费基准,公式: `revenue = conversions_final × unit_price` |
| `raw_spend` DECIMAL(15,2) | DEFAULT 0.00, 投手提交的原始消耗(T+0 23:59前),用于趋势风控(TF-003规则),不计成本 |
| `real_spend` DECIMAL(15,2) | DEFAULT 0.00, 运营录入的真实消耗(T+1 12:00前),成本核算基准,公式: `cost = real_spend + fee` |
| `unit_price` DECIMAL(15,2) | DEFAULT 0.00, 单粉价格,从项目继承(`projects.unit_price`),用于计算收入 |
| `cpc`, `cpa`, `ctr`, `roi` DECIMAL(12,4) | 可空 |
| `status` VARCHAR(20) | 参考"粉数确认状态机"(STATE_MACHINE.md 第8章)，合法取值: `raw_submitted/trend_pending/trend_ok/trend_flagged/trend_resolved/final_pending/final_confirmed/final_locked`，终态为 `final_locked` |
| `trend_flag` VARCHAR(20) | DEFAULT 'normal', 趋势异常标记, 固定枚举: `normal/flagged/resolved` |
| `trend_flag_reason` TEXT | 可空, 风控规则触发原因(如"TF-001: 粉数骤降50%") |
| `trend_resolution_note` TEXT | 可空, 运营复核说明(`data_operator`填写) |
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

---

### 3.4 充值与资金

#### 3.4.1 `topup_requests`（implemented）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` BIGSERIAL PK | |
| `request_no` VARCHAR(50) UNIQUE | |
| `project_id` BIGINT FK → `projects.id` | |
| `ad_account_id` BIGINT FK → `ad_accounts.id`, 可空 | |
| `applicant_id` UUID FK → `users.id` | |
| `amount` DECIMAL(15,2) NOT NULL | |
| `currency` VARCHAR(10) | DEFAULT 'CNY' |
| `urgency_level` VARCHAR(20) | 固定枚举 `low/normal/high/urgent`（非状态机） |
| `status` VARCHAR(20) | 参考“充值状态机”，典型值如 draft/pending_review/finance_approve/paid/completed/rejected/cancelled，具体枚举以 STATE_MACHINE.md 为准 |
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

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` BIGSERIAL PK | |
| `ledger_type` VARCHAR(20) | 账本类型, 固定枚举 `PROJECT/SUPPLIER`, PROJECT账本记录项目收入(粉数计费), SUPPLIER账本记录供应商成本(真实消耗) |
| `project_id` BIGINT FK → `projects.id` | PROJECT账本必填, SUPPLIER账本可空 |
| `supplier_id` UUID FK → `suppliers.id` | SUPPLIER账本必填, PROJECT账本可空, 所属供应商ID |
| `ad_account_id` BIGINT FK → `ad_accounts.id`, 可空 | |
| `entry_type` VARCHAR(20) | 固定枚举(6种): `REVENUE`(粉数计费收入,PROJECT账本), `COST`(真实消耗成本,SUPPLIER账本), `TOPUP`(充值入账,两账本均可), `TRANSFER_OUT`(死号余额迁出,SUPPLIER账本), `TRANSFER_IN`(死号余额迁入,SUPPLIER账本), `REVERSAL`(红冲修正,final_locked后修正); PROJECT账本允许: REVENUE/TOPUP/REVERSAL; SUPPLIER账本允许: COST/TOPUP/TRANSFER_OUT/TRANSFER_IN/REVERSAL |
| `amount` DECIMAL(15,2) | 金额，借方为正，贷方直接记录负数, 红冲时为负数 |
| `currency` VARCHAR(10) | |
| `reference_id` BIGINT | 关联 `topup_transactions` 或 `daily_reports` 或原Ledger记录ID(红冲时) |
| `occurred_at` TIMESTAMPTZ | |
| `created_by` UUID FK → `users.id` | |
| `notes` TEXT | |

**约束**: `ledger_type=PROJECT`时`project_id`必填, `ledger_type=SUPPLIER`时`supplier_id`必填

**计费公式** (BRD v3.1第7-8章):
- PROJECT账本收入: `revenue = conversions_final × unit_price`
- SUPPLIER账本成本: `cost = real_spend + fee`
- 项目毛利: `profit = revenue - cost`

索引：`idx_ledger_project`, `idx_ledger_supplier`, `idx_ledger_entry_type`, `idx_ledger_type`.

#### 3.4.5 `suppliers`（implemented）

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

#### 3.4.6 `transfer_requests`（implemented）

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

字段：`id`, `batch_no` (UNIQUE), `project_id`, `status`（参考"对账批次状态机"，合法值: `draft/pending_review/approved/needs_adjustment/completed`，具体枚举以 STATE_MACHINE.md v2.6 为准）, `source`, `period_start`, `period_end`, `created_by`, `approved_by`, `created_at`, `updated_at`.

#### 3.5.2 `reconciliation_details`（implemented）

字段：`id`, `batch_id (FK)`, `ad_account_id`, `report_date`, `system_spend`, `external_spend`, `difference_amount`, `status`（参考“对账明细状态机”，典型值如 pending/confirmed/adjusted，具体枚举以 STATE_MACHINE.md 为准）, `notes`, `created_at`.

#### 3.5.3 `reconciliation_adjustments`（implemented）

字段：`id`, `detail_id (FK)`, `adjustment_type`（固定 `increase/decrease/writeoff`）, `amount DECIMAL(15,2)`, `reason`, `created_by`, `created_at`.

#### 3.5.4 `reconciliation_reports`（implemented）

字段：`id`, `batch_id (FK)`, `generated_at`, `generated_by`, `report_url`, `metrics JSONB`.

---

## 4. 索引与约束策略

1. **唯一性**：`request_no`, `account_code`, `(report_date, ad_account_id)` 等必须建唯一索引并在模型层校验。  
2. **组合索引**：针对高频过滤场景建立，如 `daily_reports(report_date, status)`、`topup_requests(project_id, status)`、`ledger_entries(project_id, occurred_at)`。  
3. **CHECK 约束**：角色字段仅允许 5 个合法值；状态字段 CHECK 应引用相应状态机；金额字段若允许负值需在说明写明。  
4. **外键一致性**：外键字段类型必须与被引用主键一致，迁移旧字段时需同步更新 FK 定义与索引。  
5. **触发器**：`users` 使用 `update_users_updated_at`；其他表如需类似逻辑必须在本文件登记。

---

## 5. 历史兼容与规划说明

- **`users` 表**：业务层用户资料表，主键为 UUID，外键关联 `auth.users(id)`。`auth.users` 用于认证（Supabase Auth 内置用户表），`users` 用于业务逻辑（角色、权限、扩展信息等）。
- **历史兼容**：旧代码中可能使用 `user_profiles` 表名，已统一改为 `users`。如发现遗留的 `user_profiles` 引用，请更新为 `users`。所有外键必须指向 `users.id`（UUID），不再使用 `user_profiles`。  
- **旧角色名**：`manager` = `account_manager`，`data_clerk` = `data_operator`。历史数据可读，新增逻辑禁止使用旧名。  
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
   - [ ] 角色字段只出现 5 个合法值  
   - [ ] 索引/约束在迁移与本文件中都有记录  
4. **审阅频率**：每次数据库结构变更后立即更新本文件；若长期无变更也需至少每季度审查一次。

---

**文档版本**: v5.2
**最后审阅**: 2025-01-22
**维护责任**: 数据库规范守门人（与系统架构团队共管）  
**附注**: 若实现规范、状态机或 API 流程更新，必须同步更新本文件；否则任何生成代码/Schema 迁移将被拒绝。
