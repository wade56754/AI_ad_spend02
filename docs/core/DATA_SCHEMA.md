# DATA_SCHEMA.md · 数据结构唯一事实来源 (SoT-Data)

> **版本**: v5.0  
> **更新日期**: 2025‑11‑17  
> **维护团队**: 系统架构团队（数据库规范守门人）  
> **定位**: 描述 AI 广告代投系统全部已落地/规划中的数据库表结构、字段、索引与约束，是数据层唯一事实来源。若其他文档与此冲突，以本文件为准。  
> **互锁 SoT**:  
> - 实现规范 → `docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md`  
> - 状态机 → `docs/core/STATE_MACHINE.md`（任何状态字段必须引用对应状态机）  
> - API 流程 → `docs/core/API_DEVELOPMENT_FLOW.md`  
> - 错误码 → `docs/ERROR_CODES.md`

---

## 1. 通用约定

### 1.1 技术栈

- **数据库**: PostgreSQL 15（Supabase 托管）  
- **ORM / 迁移**: SQLAlchemy（同步版）+ Alembic  
- **权限**: 当前版本仅在应用层（Service + `@require_role`）执行 RBAC，数据库 RLS 默认关闭  
- **时间字段**: 统一使用 `TIMESTAMPTZ`，默认 `NOW()`，应用层使用 UTC  
- **金额字段**: 一律 `DECIMAL(15,2)`，默认 `0.00`，借方为正、贷方为负值  
- **角色枚举**: 仅允许 `admin`, `finance`, `data_operator`, `account_manager`, `media_buyer`；旧角色名只允许出现在“历史兼容”说明  
- **状态字段**: 仅引用 `STATE_MACHINE.md` 中的定义，禁止在本文件重复列举或扩展新枚举  
- **主键/外键**:  
  - 用户、渠道等跨系统实体：主键使用 UUID（对齐 Supabase/外部系统 ID）  
  - 核心业务表（项目、账户、日报、充值、账本、对账等）：主键统一使用 BIGSERIAL  
  - 所有外键字段类型必须与被引用主键完全一致（如引用 `user_profiles.id` 必须是 UUID，引用 `projects.id` 必须是 BIGINT）

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
| `user_profiles` | Supabase Auth 业务扩展档案 | UUID | implemented |
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
| `reconciliation_batches` | 对账批次 | BIGSERIAL | implemented |
| `reconciliation_details` | 对账明细 | BIGSERIAL | implemented |
| `reconciliation_adjustments` | 对账调整 | BIGSERIAL | implemented |
| `reconciliation_reports` | 对账报告 | BIGSERIAL | implemented |

---

## 3. 详细表结构

> 说明：凡是包含 `status`/`review_status`/`urgency_level` 等状态字段，均在字段描述中注明所属状态机或固定枚举。

### 3.1 用户与权限

#### 3.1.1 `user_profiles`（implemented）

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | UUID | PK, FK → `auth.users(id)` ON DELETE CASCADE | 与 Supabase Auth 同步 |
| `username` | VARCHAR(50) | UNIQUE | 用户名 |
| `full_name` | VARCHAR(100) | | 真实姓名 |
| `email` | VARCHAR(255) | 可空 | 冗余字段，方便联查 |
| `role` | VARCHAR(20) | NOT NULL, CHECK（合法角色） | 仅 `admin/finance/data_operator/account_manager/media_buyer` |
| `department` / `position` | VARCHAR(100) | | 组织信息 |
| `account_manager_id` | UUID | FK → `user_profiles.id` | 投手关联户管 |
| `is_active` | BOOLEAN | DEFAULT true | 账号可用性 |
| `is_verified` | BOOLEAN | DEFAULT false | 资料验证状态 |
| `last_login_at` / `last_login_ip` | TIMESTAMPTZ / VARCHAR(45) | | |
| `preferences`, `notification_settings`, `profile_metadata` | JSONB | DEFAULT `{}` | 扩展配置 |
| `timezone`, `language` | VARCHAR | DEFAULT `'UTC'` / `'zh-CN'` | |
| `created_at` / `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | |
| `created_by` / `updated_by` | UUID | FK → `user_profiles.id`, 可空 | |

索引：`idx_user_profiles_username`, `idx_user_profiles_role`, `idx_user_profiles_account_manager`, `idx_user_profiles_created_at`, `idx_user_profiles_last_login`.

#### 3.1.2 `roles`（legacy）

字段：`id`, `name`, `description`, `created_at`。仅用于旧系统兼容，新功能禁止引用。

#### 3.1.3 `user_sessions`（implemented）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` BIGSERIAL PK | |
| `user_id` UUID FK → `user_profiles.id` | |
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
| `performed_by` UUID FK → `user_profiles.id` | |
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
| `account_manager_id` UUID FK → `user_profiles.id` | |
| `budget_total` DECIMAL(15,2) | DEFAULT 0.00 |
| `budget_currency` VARCHAR(10) | DEFAULT 'CNY' |
| `start_date` / `end_date` DATE | | |
| `created_by` / `updated_by` UUID FK → `user_profiles.id` | |
| `created_at` / `updated_at` TIMESTAMPTZ | DEFAULT NOW() | |

索引：`idx_projects_name`, `idx_projects_status`, `idx_projects_account_manager`.

#### 3.2.2 `project_members`（implemented）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` BIGSERIAL PK | |
| `project_id` BIGINT FK → `projects.id` ON DELETE CASCADE | |
| `user_id` UUID FK → `user_profiles.id` | |
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
| `created_by` UUID FK → `user_profiles.id` | |
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
| `reviewer_id` UUID FK → `user_profiles.id` | |
| `review_status` VARCHAR(20) | 参考“渠道评审状态机”，典型值如 draft/pending/approved/rejected，具体枚举以 STATE_MACHINE.md 为准 |
| `score` JSONB | 评估分项 |
| `comments` TEXT | |
| `created_at` / `updated_at` TIMESTAMPTZ | | |

#### 3.2.7 `channel_account_requests`（implemented）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` UUID PK | |
| `channel_id` UUID FK → `channels.id` | |
| `requested_by` UUID FK → `user_profiles.id` | |
| `approved_by` UUID FK → `user_profiles.id`, 可空 | |
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
| `owner_id` UUID FK → `user_profiles.id` | 账户负责人，通常应为 `account_manager` 或 `media_buyer`，由 Service 层校验 |
| `name` VARCHAR(200) | 账户别名 |
| `account_code` VARCHAR(100) | 平台编号，UNIQUE |
| `status` VARCHAR(20) | 参考“账户生命周期状态机”，典型值如 new/testing/active/suspended/dead/archived，具体枚举以 STATE_MACHINE.md 为准 |
| `status_reason` TEXT | |
| `spend_limit` DECIMAL(15,2) | DEFAULT 0.00 |
| `currency` VARCHAR(10) | DEFAULT 'CNY' |
| `timezone` VARCHAR(50) | DEFAULT 'Asia/Shanghai' |
| `created_by` / `updated_by` UUID | FK → `user_profiles.id` |
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
| `author_id` UUID FK → `user_profiles.id` | |
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
| `spend` DECIMAL(15,2) | DEFAULT 0.00 |
| `cpc`, `cpa`, `ctr`, `roi` DECIMAL(12,4) | 可空 |
| `status` VARCHAR(20) | 参考“日报状态机”，典型值如 draft/pending/approved/rejected，具体枚举以 STATE_MACHINE.md 为准 |
| `notes` TEXT | |
| `attachments` JSONB | |
| `created_by`, `updated_by`, `submitted_by`, `audit_user_id` UUID | FK → `user_profiles.id` |
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
| `applicant_id` UUID FK → `user_profiles.id` | |
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
| `project_id` BIGINT FK → `projects.id` | |
| `ad_account_id` BIGINT FK → `ad_accounts.id`, 可空 | |
| `entry_type` VARCHAR(20) | 固定枚举 `topup_received/spend/adjustment/...` |
| `amount` DECIMAL(15,2) | 金额，借方为正，贷方直接记录负数 |
| `currency` VARCHAR(10) | |
| `reference_id` BIGINT | 关联 `topup_transactions` 或 `daily_reports` |
| `occurred_at` TIMESTAMPTZ | |
| `created_by` UUID FK → `user_profiles.id` | |
| `notes` TEXT | |

索引：`idx_ledger_project`, `idx_ledger_account`, `idx_ledger_entry_type`.

---

### 3.5 对账模块

#### 3.5.1 `reconciliation_batches`（implemented）

字段：`id`, `batch_no` (UNIQUE), `project_id`, `status`（参考“对账批次状态机”，典型值如 draft/pending/reviewing/closed，具体枚举以 STATE_MACHINE.md 为准）, `source`, `period_start`, `period_end`, `created_by`, `approved_by`, `created_at`, `updated_at`.

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
5. **触发器**：`user_profiles` 使用 `update_user_profiles_updated_at`；其他表如需类似逻辑必须在本文件登记。

---

## 5. 历史兼容与规划说明

- **`users` 表/视图**：迁移至 Supabase Auth 后不再直接写入，旧代码通过视图映射到 `user_profiles`，并逐步移除。  
- **旧角色名**：`manager` = `account_manager`，`data_clerk` = `data_operator`。历史数据可读，新增逻辑禁止使用旧名。  
- **`roles` 表**：标记为 `status: legacy`，仅用于兼容查询。  
- **RLS**：部分迁移脚本包含 `ENABLE ROW LEVEL SECURITY`，当前部署统一关闭（`ENABLE_RLS=false`）；若未来启用须同步更新本文件与实现 SoT。  
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

**文档版本**: v5.0（最终微调版）  
**最后审阅**: 2025‑11‑17  
**维护责任**: 数据库规范守门人（与系统架构团队共管）  
**附注**: 若实现规范、状态机或 API 流程更新，必须同步更新本文件；否则任何生成代码/Schema 迁移将被拒绝。
