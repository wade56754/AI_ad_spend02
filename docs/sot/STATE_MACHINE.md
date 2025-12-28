# AI广告代投系统 - 状态机定义文档（SoT-State）

> **版本**: v2.7
> **status**: active
> **owner**: wade
> **last_reviewed**: 2025-12-27
> **更新日期**: 2025-12-27
> **类型**: 状态与合法流转的唯一事实来源（SoT-State）
> **互锁文档**
> - 实现规范 → `./MASTER.md` v4.6
> - 数据结构 → `./DATA_SCHEMA.md`（CHECK/枚举必须完全复制本文件，不得自创）
> - API 流程 → `../2.dev-guides/API_DEVELOPMENT_FLOW.md`
> - 技术层角色 → `admin/finance/data_operator/account_manager/media_buyer`
> - 业务层角色（6角色）→ §2.1 映射表，PRD v2.2 已移除 supervisor

---

## 1. 定位与优先级

- 本文件定义所有状态枚举与合法流转，**其他文档如有冲突，以本文件为准**。  
- `DATA_SCHEMA` 中的 CHECK 约束、枚举类、前后端常量必须从本文件同步；禁止自行扩展或裁剪状态集合。  
- 业务流程、权限细节以实现规范为准；本文件中的权限描述仅用于约束状态流转。  
- 规划内容统一放在《Planned 扩展》章节，当前版本禁止实现。

---

## 2. 角色与操作者

- 技术层合法角色：`admin`, `finance`, `data_operator`, `account_manager`, `media_buyer`。  
- **system（虚拟操作者）**：用于定时任务/事件驱动的自动流转，不参与 RBAC，仅可出现在审计日志（`operator_role = 'system'`）。业务授权只看 5 个合法角色。  
- 审批分离：提交者不能审批自身请求；终态回退仅 `admin`（需审计理由）。

### 2.1 业务层角色映射（MASTER v4.6 对齐）

> **引用**: MASTER.md v4.6 §2.4
> **PRD v2.2 变更**: 移除 supervisor 角色，职责合并到 project_owner

技术层维持 5 角色 CHECK 约束，业务层通过以下映射对齐 MASTER 定义：

| MASTER 业务角色 | 技术层角色 | 说明 |
|----------------|-----------|------|
| ceo | admin | 系统最高权限，资金审批 |
| project_owner | (users.is_project_owner=true) | 项目负责人，**日报审核**，复用现有用户 |
| finance | finance | 财务，资金对账 |
| pitcher | media_buyer | 投手，日报填报 |
| account_manager | account_manager | 户管，账户分配 |
| admin | admin | 系统管理员 |

> **注意**：
> - `project_owner` 通过 users 表的业务属性或 `project_members` 表实现，不新增角色枚举。
> - 日报审核流程中的"运营"指代 `project_owner` 角色。
> - PRD v2.2 已移除 supervisor 角色，其职责（日报审核、数据统计）合并到 project_owner。
> - 禁止新增角色枚举，必须复用 5 个技术层角色 + project_owner 业务属性。

---

## 3. 命名与类型规则

- 状态名/动作名：小写 snake_case。  
- 初始态 / 过渡态 / 终态：终态默认不可回退，除非表格中显式允许且需审计。  
- 所有状态变更必须通过业务动作，不得直接 UPDATE `status`。  
- 标记 [AUDIT] 的流转必须记录操作者、时间、旧/新状态、理由。  

---

## 4. 全局状态一览表（当前实现）

| 表/字段 | 合法取值 | 终态 | 备注 |
| --- | --- | --- | --- |
| projects.status | draft, active, suspended, archived | archived | 项目生命周期 |
| channels.status | active, inactive | inactive | 渠道 |
| channel_reviews.review_status | draft, pending, approved, rejected | approved/rejected | 渠道评审 |
| channel_account_requests.status | draft, pending, approved, rejected | approved/rejected | 渠道开户申请 |
| channel_performance.* | 无状态 | - | 统计表 |
| ad_accounts.status | new, testing, active, suspended, dead, archived | dead/archived | 账户生命周期 |
| account_alerts.status | open, ack, resolved | resolved | 账户预警 |
| daily_reports.status | raw_submitted, trend_pending, trend_ok, trend_flagged, trend_resolved, final_pending, final_confirmed, final_locked | final_locked | 日报(粉数确认状态机) |
| topup_requests.status | draft, pending_review, finance_approve, paid, completed, rejected, cancelled | completed/rejected/cancelled | 充值 |
| reconciliation_batches.status | draft, pending_review, approved, needs_adjustment, completed | completed | 对账批次状态机 |
| reconciliation_details.status | pending, confirmed, adjusted | confirmed/adjusted | 对账明细 |
| transfer_requests.status | draft, pending_approval, approved, rejected, completed | approved/rejected/completed | 死号余额迁移 |
| ledger_entries | 无状态 | - | 资金总账 |
| ad_spend_daily | 无状态 | - | 导入数据 |

> Planned/历史状态见第 15 章，不得在当前实现使用。

---

## 4A. Phase 边界说明

> **引用**: MASTER.md v4.6 §2.5（Phase 1/Phase 2 执行边界）、§9 INV-003

### 4A.1 日报状态机 Phase 边界

| Phase | 可用状态 | 说明 |
|-------|---------|------|
| Phase 1 | `raw_submitted`, `trend_ok`, `final_confirmed` | 简化 3 状态；跳过 trend_pending/trend_flagged/trend_resolved/final_pending |
| Phase 2 | 全部 8 状态 | 启用完整审核流程 |

**Phase 1 约束**：
- 日报从 `raw_submitted` 可直接跳转 `trend_ok`（项目负责人快速确认）
- `trend_ok` 可直接跳转 `final_confirmed`（财务快速确认）
- 禁止任何系统自动阻断或惩罚性状态转换

**Phase 2 启用条件**：
- Phase 1 稳定运行 2 个月
- Feature Flag `ENABLE_FULL_DAILY_REPORT_SM=true`

### 4A.2 充值状态机 Phase 边界

| Phase | 行为差异 |
|-------|---------|
| Phase 1 | 所有状态可用，但无自动阻断/惩罚 |
| Phase 2 | 可启用预算检查、超额阻断等约束 |

### 4A.3 项目状态机 Phase 边界

| Phase | 行为差异 |
|-------|---------|
| Phase 1 | `suspended` 仅标记状态，不阻断投放 |
| Phase 2 | `suspended` 可联动阻断账户投放（需 Feature Flag） |

> **核心原则**：Phase 1 只做「照亮」，不做「阻断」；Phase 2 通过 Feature Flag 逐步启用强约束。

---

## 5. 项目状态机（projects.status）

状态：`draft` → `active` → `suspended` → `archived`（终态）  
- 触发：account_manager, admin  
- 终态回退：仅 admin，[AUDIT]

---

## 6. 渠道与开户

### 6.1 渠道（channels.status）  
合法取值：`active`, `inactive`（终态：inactive）  
- 切换需记录原因，[AUDIT]

### 6.2 渠道评审（channel_reviews.review_status）  
合法取值：`draft`, `pending`, `approved`, `rejected`（终态：approved/rejected）  
- 提交：account_manager/data_operator  
- 审核：data_operator/admin，[AUDIT]

### 6.3 渠道开户申请（channel_account_requests.status）  
合法取值：`draft`, `pending`, `approved`, `rejected`（终态：approved/rejected）  
- 提交：account_manager/media_buyer  
- 审批：account_manager/admin，[AUDIT]

### 6.4 渠道表现（channel_performance）  
无状态机，统计表。

---

## 7. 广告账户

### 7.1 账户生命周期（ad_accounts.status）  
合法取值：`new`, `testing`, `active`, `suspended`, `dead`, `archived`（终态：dead/archived）  
- 暂停/恢复：account_manager/admin，[AUDIT]  
- 终态回退：仅 admin，[AUDIT]

### 7.2 账户状态历史（account_status_history）  
记录所有状态变更，操作者、时间、原因必填。

### 7.3 账户预警（account_alerts.status）  
合法取值：`open`, `ack`, `resolved`（终态：resolved）  
- 创建：system/data_operator  
- 确认/解决：account_manager/admin，[AUDIT]

---

## 7.5 Phase 1 / Phase 2 日报状态机边界（重要）

> **依据**: MASTER.md v4.4 §3（Phase 1/Phase 2 执行边界）、§9 INV-003（简化vs完整流程）

### 7.5.1 Phase 1 简化版（3 状态快速流转）

**目标**: 照亮问题，不阻断流程（"不问责、不阻断、不强制"）

**可用状态**: `raw_submitted`, `trend_ok`, `final_confirmed`

**合法流转** (跳过中间审核状态):
```
raw_submitted → trend_ok → final_confirmed
```

**字段使用**:
- 进粉 SoT: 仅使用 `daily_report.conversions`（投手自报值）
- 消耗 SoT: 仅使用 `ad_spend_daily.spend`（外部导入）
- **不使用** Phase 2 字段: `conversions_raw`, `conversions_final`, `raw_spend`, `real_spend`

**Phase 1 特性**:
- ✅ 无趋势风控（不触发 `trend_flagged` / `trend_pending`）
- ✅ 无强制终审（不使用 `final_pending` 等待态）
- ✅ 数据可见但不阻断（`trend_ok` 状态仅标记，不影响后续流程）
- ✅ 锁定仅用于归档（`final_confirmed` 后不再修改，但无强制约束）

**业务约束**:
- 投手提交日报后，项目负责人快速确认（`raw_submitted` → `trend_ok`）
- 财务快速确认计费（`trend_ok` → `final_confirmed`）
- 无自动拒绝、无自动暂停、无自动冻结

### 7.5.2 Phase 2 完整版（8 状态全流程）

**目标**: 问责与强制约束，启用趋势风控与多级审核

**状态枚举**: 见第 8 章完整定义（8 个状态）

**启用条件** (MASTER.md v4.4 §3.4):
1. Phase 1 稳定运行 2 个月
2. 日报填报率 ≥ 90%
3. 老板批准启用
4. Feature Flag: `PHASE2_DAILY_REPORT_REQUIRED=true`

**Phase 2 新增特性**:
- 趋势风控（TF-001/002/003 规则，触发 `trend_flagged`）
- 三数据流分离（`conversions_raw` / `conversions_final` / `real_spend`）
- 多级审核（运营复核 `final_pending` → 财务终审 `final_confirmed`）
- 计费锁定（`final_locked` 后仅可红冲，不可直接修改）

---

## 8. 粉数确认状态机（daily_reports.status - 8状态流程）

> **业务背景**: 基于BRD v3.1第4章"粉数确认状态机",系统采用三数据流(raw/real/final)分离设计,
> final_conversions需经过趋势风控检查后方可锁定进入计费。

### 8.1 状态枚举定义

合法取值: `raw_submitted`, `trend_pending`, `trend_ok`, `trend_flagged`, `trend_resolved`, `final_pending`, `final_confirmed`, `final_locked`
终态: `final_locked`

**状态详解**:

| 状态 | 说明 | 触发条件 | 角色权限 | 可修改字段 |
|-----|------|---------|---------| -----------|
| **raw_submitted** | 投手提交原始粉数 | 投手提交daily_report | `media_buyer` | `conversions_raw`, `raw_spend` |
| **trend_pending** | 等待趋势风控检查 | 自动触发(raw提交后) | 系统自动 | 无 |
| **trend_ok** | 趋势正常 | 风控规则通过 | 系统自动 | 无 |
| **trend_flagged** | 趋势异常,需人工复核 | 风控规则触发异常 | 系统自动 | `trend_flag_reason` |
| **trend_resolved** | 运营确认异常已解决 | 运营复核后确认 | `data_operator` | `trend_resolution_note` |
| **final_pending** | 等待最终粉数确认 | 运营录入real_spend后 | `data_operator` | `conversions_final`, `real_spend` |
| **final_confirmed** | 最终粉数已确认 | 运营确认final | `data_operator` | 无 |
| **final_locked** | 已进入计费,锁定 | 系统计费后锁定 | 系统自动 | 无(仅可红冲) |

### 8.2 状态流转规则

```
T+0日 23:59前: 投手提交raw
├─ raw_submitted → trend_pending (系统自动)
├─ trend_pending → trend_ok (风控通过,系统自动)
├─ trend_pending → trend_flagged (风控异常,系统自动)

运营复核:
├─ trend_flagged → trend_resolved (运营确认正常)
├─ trend_flagged → raw_submitted (运营要求投手重新提交)

T+1日 12:00前: 运营录入real_spend
├─ trend_ok → final_pending (运营录入real_spend)
├─ trend_resolved → final_pending (运营录入real_spend)

T+1日 14:00前: 运营确认final
├─ final_pending → final_confirmed (运营确认final)

计费锁定:
├─ final_confirmed → final_locked (系统计费锁定,不可逆)
```

**合法流转白名单** (基于第14.5章):

```python
"daily_reports.status": {
    "raw_submitted": ["trend_pending"],
    "trend_pending": ["trend_ok", "trend_flagged"],
    "trend_ok": ["final_pending"],
    "trend_flagged": ["trend_resolved", "raw_submitted"],
    "trend_resolved": ["final_pending"],
    "final_pending": ["final_confirmed"],
    "final_confirmed": ["final_locked"],
    "final_locked": []  # 终态,仅可通过红冲修正
}
```

### 8.3 趋势风控规则 (Trend Risk Control)

**规则编号**: TF-001/002/003 (定义于 MASTER_SPEC v2.2 第2.3.1节)

| 规则编号 | 规则名称 | 判断逻辑 | 触发后果 |
|---------|---------|---------| ---------|
| **TF-001** | 粉数骤降检查 | `conversions_raw < 昨日最大值 × 0.5` | `trend_flagged` |
| **TF-002** | 粉数骤增检查 | `conversions_raw > 昨日最大值 × 3` | `trend_flagged` |
| **TF-003** | 消耗异常检查 | `raw_spend > 昨日 × 2` | `trend_flagged` |

**触发后处理**:
1. 系统自动将状态设为 `trend_flagged`
2. 填充 `trend_flag_reason` 字段 (如 "TF-001: 粉数骤降50%")
3. 通知 `data_operator` 进行人工复核
4. 运营复核后填写 `trend_resolution_note`
5. 运营确认后流转至 `trend_resolved`

### 8.4 三数据流字段定义

**新增字段** (对齐 MASTER_SPEC v2.2 第2.2节):

| 字段名 | 类型 | 说明 | 提交者 | 时效性 | 用途 |
|-------|------|------|--------|--------|------|
| **conversions_raw** | INTEGER | 投手提交的原始粉数 | `media_buyer` | T+0 23:59前 | 趋势风控 |
| **raw_spend** | DECIMAL(15,2) | 投手提交的原始消耗 | `media_buyer` | T+0 23:59前 | 趋势风控 |
| **conversions_final** | INTEGER | 运营确认的最终粉数 | `data_operator` | T+1 14:00前 | 计费基准 |
| **real_spend** | DECIMAL(15,2) | 真实消耗(运营录入) | `data_operator` | T+1 12:00前 | 成本核算 |
| **trend_flag** | VARCHAR(20) | 趋势异常标记 | 系统自动 | - | `normal`/`flagged`/`resolved` |
| **trend_flag_reason** | TEXT | 异常原因 | 系统自动 | - | 如"TF-001: 粉数骤降" |
| **trend_resolution_note** | TEXT | 运营复核说明 | `data_operator` | - | 运营填写 |
| **final_locked_at** | TIMESTAMPTZ | 锁定时间 | 系统自动 | - | 计费锁定时间戳 |
| **unit_price** | DECIMAL(15,2) | 单粉价格 | 系统自动 | - | 从项目继承 |

### 8.5 业务约束

1. **三数据流分离原则**:
   - ✅ `conversions_raw` 不计费,仅用于趋势风控
   - ✅ `conversions_final` 计费,公式:`revenue = conversions_final × unit_price`
   - ✅ `real_spend` 用于成本核算,公式:`cost = real_spend + fee`
   - ❌ 禁止使用`raw_spend`计算成本
   - ❌ 禁止跳过final直接计费

2. **状态流转约束**:
   - ✅ `conversions_raw` ≠ `conversions_final` (允许运营调整)
   - ✅ `conversions_final` 一旦确认,除红冲外不可修改
   - ✅ `final_locked` 状态后,修正必须通过Ledger红冲(`entry_type=REVERSAL`)
   - ❌ 禁止跳过趋势风控直接确认final
   - ❌ 禁止在`final_locked`后直接修改数据库

3. **趋势风控约束**:
   - ✅ trend_flagged状态下,禁止进入final_pending
   - ✅ 运营必须填写`trend_resolution_note`
   - ✅ 风控检查自动执行,运营可手动重新检查
   - ❌ 禁止关闭风控检查

### 8.6 角色权限

| 操作 | 允许角色 | 说明 |
|-----|---------|------|
| 提交raw粉数 | `media_buyer` | raw_submitted状态 |
| 趋势风控检查 | 系统自动 | trend_pending → trend_ok/flagged |
| 趋势风控复核 | `data_operator`, `admin` | trend_flagged → trend_resolved |
| 录入real_spend | `data_operator`, `admin` | 填充real_spend字段 |
| 确认final粉数 | `data_operator`, `admin` | final_pending → final_confirmed |
| 计费锁定 | 系统自动 | final_confirmed → final_locked |
| 红冲修正 | `admin` | final_locked后的唯一修正方式 |

### 8.7 API端点映射 (参考第16章)

| API端点 | HTTP方法 | 当前状态 | 目标状态 | 允许角色 | 审计 |
|---------|---------|---------|---------|---------|------|
| `POST /daily-reports` | POST | - | raw_submitted | media_buyer | [AUDIT] |
| `POST /daily-reports/{id}/trend-check` | POST | raw_submitted | trend_pending | system | [AUDIT] |
| `PUT /daily-reports/{id}/final-confirm` | PUT | final_pending | final_confirmed | data_operator, admin | [AUDIT] |
| `POST /daily-reports/{id}/final-lock` | POST | final_confirmed | final_locked | system | [AUDIT] |
| `POST /daily-reports/{id}/reversal` | POST | final_locked | - (红冲) | admin | [AUDIT]强制 |

### 8.8 red冲修正机制 (final_locked后的修正)

**核心原则**: `final_locked`状态后,所有修正必须通过**红冲机制**完成。

**红冲流程**:
```
1. 发现final_locked数据错误
2. 创建REVERSAL记录 (entry_type=REVERSAL, amount=-原金额)
3. 冲销原Ledger记录
4. 生成新的正确Ledger记录
5. 更新项目余额
6. 记录审计日志
```

**示例**:
```
原始数据:
├─ conversions_final = 100
├─ revenue = 100 × 50 = 5000
└─ Ledger记录: entry_type=REVENUE, amount=5000

发现错误(应为95粉):
├─ Step1: 创建红冲记录
│   ├─ entry_type = REVERSAL
│   ├─ amount = -5000
│   └─ notes = "红冲原记录#12345,粉数错误"
├─ Step2: 生成新记录
│   ├─ entry_type = REVENUE
│   ├─ amount = 95 × 50 = 4750
│   └─ notes = "修正后的正确记录"
└─ Step3: 更新项目余额
    └─ balance = balance + 5000 - 4750 = balance + 250
```

**业务规则**:
- ✅ 红冲金额 = -原金额
- ✅ 红冲后重新生成正确的Ledger记录
- ✅ 审计日志记录完整链条
- ❌ 禁止直接UPDATE daily_reports的conversions_final
- ❌ 禁止直接DELETE Ledger记录

### 8.9 CHECK约束定义 (参考第15章)

```sql
ALTER TABLE daily_reports
ADD CONSTRAINT chk_daily_reports_status
CHECK (status IN (
    'raw_submitted',
    'trend_pending',
    'trend_ok',
    'trend_flagged',
    'trend_resolved',
    'final_pending',
    'final_confirmed',
    'final_locked'
));

ALTER TABLE daily_reports
ALTER COLUMN status SET DEFAULT 'raw_submitted';

ALTER TABLE daily_reports
ALTER COLUMN status SET NOT NULL;
```

### 8.10 审计日志要求

所有状态变更必须记录 `daily_report_audit_logs`:
- 必填字段: `old_status`, `new_status`, `audit_user_id`, `audit_time`, `audit_notes`
- 特殊场景:
  - `trend_flagged`: 记录触发规则 (TF-001/002/003)
  - `trend_resolved`: 记录运营复核说明
  - `final_locked`: 记录计费金额和Ledger Entry ID
  - 红冲修正: 记录原记录ID、红冲记录ID、修正原因

---

## 9. 充值申请（topup_requests.status）

合法取值（与 DATA_SCHEMA 对齐）：`draft`, `pending_review`, `finance_approve`, `paid`, `completed`, `rejected`, `cancelled`  
- 提交：media_buyer/account_manager（draft→pending_review）  
- 数据复核：data_operator（pending_review→finance_approve/rejected）  
- 财务终审：finance（finance_approve→paid/rejected）  
- 入账确认：finance/system（paid→completed）  
- 终态回退：仅 admin，[AUDIT]  
> 说明：去掉独立“approved”中间态，保持与数据 SoT 一致。

---

## 10. 日消耗导入（ad_spend_daily）

无状态机；导入即生效，异常标记由业务逻辑处理。

---

## 11. 对账模块

### 11.1 对账批次（reconciliation_batches.status）

**合法取值**：`draft`, `pending_review`, `approved`, `needs_adjustment`, `completed`（终态：completed）

**状态流转规则**：
```
draft → pending_review → approved → completed
                        ↓
                   needs_adjustment → approved → completed
```

**状态详解**：

| 状态 | 说明 | 触发条件 | 角色权限 |
|-----|------|---------|---------|
| `draft` | 草稿 | 初始创建 | finance, data_operator |
| `pending_review` | 待审核 | 提交审核 | finance, data_operator |
| `approved` | 已批准 | 审核通过 | finance, admin |
| `needs_adjustment` | 需调整 | 发现差异需调整 | finance, admin |
| `completed` | 已完成 | 对账完成并锁定 | finance, admin |

**合法流转白名单**：
```python
"reconciliation_batches.status": {
    "draft": ["pending_review"],
    "pending_review": ["approved", "needs_adjustment"],
    "approved": ["completed"],
    "needs_adjustment": ["approved"],
    "completed": []  # 终态
}
```

**业务约束**：
- 创建：finance/data_operator
- 提交审核：finance/data_operator（draft → pending_review）
- 审批：finance/admin（pending_review → approved/needs_adjustment）
- 完成：finance/admin（approved → completed），[AUDIT]
- 终态回退：仅 admin，[AUDIT]

### 11.2 对账明细（reconciliation_details.status）
合法取值：`pending`, `confirmed`, `adjusted`（终态：confirmed/adjusted）
- 调整：finance/data_operator，[AUDIT]
- 终态回退：仅 admin，[AUDIT]

### 11.3 调整/报告
无独立状态机，依附批次/明细状态。

---

## 12. 死号余额迁移（transfer_requests.status）

**合法取值**：`draft`, `pending_approval`, `approved`, `rejected`, `completed`（终态：approved/rejected/completed）

**状态流转规则**：
```
draft → pending_approval → approved → completed
                         ↓
                      rejected (终态)
```

**状态详解**：

| 状态 | 说明 | 触发条件 | 角色权限 |
|-----|------|---------|---------|
| `draft` | 草稿 | 初始创建迁移申请 | account_manager, finance |
| `pending_approval` | 待审批 | 提交审批 | account_manager, finance |
| `approved` | 已批准 | 审批通过，准备执行 | finance, admin |
| `rejected` | 已拒绝 | 审批拒绝 | finance, admin |
| `completed` | 已完成 | 迁移执行完成，生成 Ledger Entry | system, admin |

**合法流转白名单**：
```python
"transfer_requests.status": {
    "draft": ["pending_approval", "rejected"],
    "pending_approval": ["approved", "rejected"],
    "approved": ["completed"],
    "rejected": [],  # 终态
    "completed": []  # 终态
}
```

**业务约束**：
- 创建：account_manager/finance（死号余额需迁出时）
- 提交审批：account_manager/finance（draft → pending_approval）
- 审批：finance/admin（pending_approval → approved/rejected），[AUDIT]
- 执行完成：system/admin（approved → completed），生成 TRANSFER_OUT/TRANSFER_IN Ledger 记录，[AUDIT]
- 终态回退：仅 admin，[AUDIT]

**迁移规则**（引用 TRANSFER_SOT.md）：
- 同供应商账户间迁移：允许（TRANSFER_OUT/TRANSFER_IN）
- 跨供应商账户间迁移：禁止（需特殊审批）
- 迁移金额不得超过源账户余额
- 迁移完成后更新 suppliers.balance

---

## 13. 总账（ledger_entries）

无状态机；按业务类型写入，审计由 `audit_logs` 负责。

---

### 13.1 月度结算状态机（monthly_settlements.status）

**合法取值**：`pending`, `confirmed`, `locked`, `archived`（终态：locked/archived）

**状态流转规则**：
```
pending → confirmed → locked → archived
   ↑          ↓
   └──────────┘ (退回修正)
```

**状态详解**：

| 状态 | 说明 | 触发条件 | 角色权限 |
|-----|------|---------|---------|
| `pending` | 待确认 | 系统自动汇总生成 | system |
| `confirmed` | 已确认 | 财务确认数据正确 | finance, admin |
| `locked` | 已锁定 | 老板最终确认锁定 | ceo, admin |
| `archived` | 已归档 | 年度归档（可选） | system, admin |

**合法流转白名单**：
```python
"monthly_settlements.status": {
    "pending": ["confirmed"],
    "confirmed": ["locked", "pending"],  # 可退回修正
    "locked": ["archived"],
    "archived": []  # 终态
}
```

**业务约束**：
- 生成：system（每月 1 日自动汇总上月数据）
- 确认：finance/admin（pending → confirmed），[AUDIT]
- 退回：ceo/admin（confirmed → pending），需填写退回原因，[AUDIT]
- 锁定：ceo/admin（confirmed → locked），[AUDIT]
- 归档：system/admin（locked → archived），[AUDIT]
- 终态回退：仅 admin，[AUDIT]

**Phase 约束**：
- Phase 1（照亮）：locked 状态可由 admin 解锁（软性锁定）
- Phase 2（问责）：locked 后不可解锁，需走冲正流程

**汇总规则**（引用 BUSINESS_RULES.md）：
- 汇总范围：上月 1 日至月末的 `final_locked` 状态日报
- 计算字段：total_spend, total_conversions, total_revenue, gross_profit, average_cpl

---

### 13.2 周报状态机（weekly_briefs.status）

**合法取值**：`draft`, `submitted`（终态：submitted）

**状态流转规则**：
```
draft → submitted
  ↑        ↓
  └────────┘ (项目负责人退回，Phase 2 可选)
```

**状态详解**：

| 状态 | 说明 | 触发条件 | 角色权限 |
|-----|------|---------|---------|
| `draft` | 草稿 | 投手创建或系统自动创建 | pitcher, system |
| `submitted` | 已提交 | 投手提交周报 | pitcher |

**合法流转白名单**：
```python
"weekly_briefs.status": {
    "draft": ["submitted"],
    "submitted": ["draft"]  # Phase 2 可选：项目负责人退回
}
```

**业务约束**：
- 创建：pitcher/system（手动创建或周一自动创建）
- 保存：pitcher（draft → draft），可多次编辑
- 提交：pitcher（draft → submitted），[AUDIT]
- 退回：project_owner/admin（submitted → draft），Phase 2 可选，[AUDIT]

**时间约束**：
- 周报周期：周一 00:00 至周日 23:59
- 提交截止：下周一 12:00 前
- 自动创建：每周一 08:00 为有日报数据的投手自动创建草稿

**自动汇总字段**（周报创建/更新时自动计算）：

| 周报字段 | 计算公式 | 数据源 |
|----------|----------|--------|
| weekly_spend | SUM(raw_spend) | daily_reports (本周) |
| weekly_conversions | SUM(conversions_raw) | daily_reports (本周) |
| weekly_cpl | weekly_spend / weekly_conversions | 计算 |

---

## 14. 权限视角提示（非仲裁）

- 本表仅为状态流转视角的快速参考；**真正的权限规则以 MASTER_SPEC 为准**。
- 若冲突，以实现规范为准，并需同步更新本文件。

| 模块 | 关键动作 | 允许角色 |
| --- | --- | --- |
| 日报提交raw粉数 | →raw_submitted | media_buyer |
| 趋势风控检查 | trend_pending→trend_ok/flagged | system (自动) |
| 趋势风控复核 | trend_flagged→trend_resolved | data_operator (admin 兜底) |
| 录入real_spend | trend_ok/resolved→final_pending | data_operator (admin 兜底) |
| 确认final粉数 | final_pending→final_confirmed | data_operator (admin 兜底) |
| 计费锁定 | final_confirmed→final_locked | system (自动) |
| 充值提交 | draft→pending_review | media_buyer/account_manager |
| 充值复核 | pending_review→finance_approve/rejected | data_operator |
| 充值终审/支付 | finance_approve→paid | finance |
| 充值完成 | paid→completed | finance/system |
| 对账批次完成 | approved→completed | finance/admin |
| 项目激活/归档 | draft/active/suspended 变更 | account_manager/admin |

---

## 14. 审计与系统操作者

- [AUDIT] 变化必须写入 `audit_logs`：包含操作者（可为 system）、旧/新状态、时间、理由。
- system 流转仅限自动任务（如支付回调、定时结算），不得替代人工审批。
- 提交者与审批者必须不同；终态解封由 admin 且需要理由。

---

## 14.1 【P0 必须补充】System 自动状态流转规则

### 14.1.1 允许的 System 自动流转

**定义**：`system` 为虚拟操作者，代表后端定时任务、外部回调、事件驱动流程。

**允许的自动流转列表**（白名单机制）：

| 模块 | 状态流转 | 触发来源 | 前置条件 | 审计要求 |
|------|---------|---------|---------|---------|
| **充值申请** | `paid` → `completed` | 支付回调确认到账 | 1. Topup Transaction 已创建<br>2. 支付凭证已验证<br>3. 金额匹配 | [AUDIT] 必须记录：回调时间、支付流水号、金额 |
| **账户预警** | `open` → `ack` | 定时任务自动确认 | 1. 预警已触发超过 1 小时<br>2. 相关账户状态正常 | [AUDIT] 必须记录：触发时间、预警类型 |
| **对账批次** | 无自动流转 | - | system 不得自动关闭批次 | - |
| **日报** | 无自动流转 | - | system 不得自动审批日报 | - |
| **项目** | 无自动流转 | - | system 不得修改项目状态 | - |

### 14.1.2 触发来源分类

| 触发来源 | 说明 | 示例 | 安全要求 |
|---------|------|------|---------|
| **支付回调** | 外部支付平台回调（支付宝/微信/银行） | 充值到账通知 | 1. 验证签名<br>2. 验证金额<br>3. 幂等性检查 |
| **定时任务** | Cron 或调度器触发 | 每日自动对账、预警检查 | 1. 执行时间窗口限制<br>2. 防止重复执行 |
| **事件驱动** | 内部事件总线触发 | 日报审核通过后自动创建 Ledger Entry | 1. 事件幂等性<br>2. 事务一致性 |

### 14.1.3 禁止的 System 动作（黑名单）

以下操作**严格禁止** system 自动执行，必须由人工角色操作：

1. **审批类流转**
   - ❌ 充值申请审批（`pending_review` → `finance_approve`）
   - ❌ 日报审核（`pending` → `approved`）
   - ❌ 渠道评审（`pending` → `approved`）

2. **财务敏感流转**
   - ❌ 充值拒绝（任意状态 → `rejected`）
   - ❌ 对账批次完成（`approved` → `completed`）
   - ❌ 金额调整（Ledger Entry 创建 `adjustment` 类型）

3. **终态回退**
   - ❌ 任何终态 → 非终态的流转（仅 admin 人工操作）

4. **账户生命周期**
   - ❌ 账户暂停/恢复（`active` ↔ `suspended`）
   - ❌ 账户标记为死账（任意状态 → `dead`）

### 14.1.4 System 流转审计要求

所有 system 自动流转必须满足：

```sql
INSERT INTO audit_logs (
    module, action, entity_id,
    performed_by, role,
    payload_before, payload_after,
    trigger_source,  -- 新增字段
    created_at
) VALUES (
    'topup_requests', 'auto_complete', '12345',
    NULL,  -- performed_by 为 NULL 表示 system
    'system',
    '{"status": "paid"}',
    '{"status": "completed"}',
    'payment_callback_alipay',  -- 触发来源
    NOW()
);
```

**必填字段**：
- `role = 'system'`
- `performed_by = NULL`（区别于真实用户）
- `trigger_source`：明确触发来源（callback/cron/event）
- `payload_before` / `payload_after`：记录完整状态变化

### 14.1.5 违规处理

若 system 尝试执行禁止的流转：

1. **立即阻止**：抛出异常，回滚事务
2. **记录日志**：
   ```python
   logger.critical(
       "FORBIDDEN_SYSTEM_TRANSITION",
       extra={
           "entity": "topup_requests",
           "entity_id": 12345,
           "from_status": "pending_review",
           "to_status": "finance_approve",  # 禁止的自动审批
           "trigger_source": "cron_job"
       }
   )
   ```
3. **安全告警**：发送告警通知 admin
4. **错误码**：返回 `STATE_403`（系统无权限执行此流转）

---

## 14.2 【P0 必须补充】终态回退规则

### 14.2.1 终态定义

根据第 4 章"全局状态一览表"，以下状态为终态（不可流转）：

| 模块 | 终态 | 说明 |
|------|------|------|
| `projects.status` | `archived` | 项目归档 |
| `channels.status` | `inactive` | 渠道停用 |
| `channel_reviews.review_status` | `approved`, `rejected` | 渠道评审终态 |
| `channel_account_requests.status` | `approved`, `rejected` | 开户申请终态 |
| `ad_accounts.status` | `dead`, `archived` | 账户死亡/归档 |
| `account_alerts.status` | `resolved` | 预警已解决 |
| `daily_reports.status` | `approved`, `rejected` | 日报审核终态 |
| `topup_requests.status` | `completed`, `rejected`, `cancelled` | 充值终态 |
| `reconciliation_batches.status` | `completed` | 对账批次完成 |
| `reconciliation_details.status` | `confirmed`, `adjusted` | 对账明细终态 |

### 14.2.2 终态回退允许条件

**唯一合法路径**：终态 → 非终态回退仅在以下条件下允许：

1. **执行者**：必须且仅能由 `admin` 角色执行
2. **理由必填**：必须提供文字说明（最少 10 字符）
3. **审计记录**：必须写入 `audit_logs` 并包含以下字段：
   - `performed_by`：admin 用户 ID
   - `role`：`admin`
   - `action`：`rollback_from_final_state`
   - `payload_before`：包含旧状态、实体完整数据
   - `payload_after`：包含新状态
   - `reason`：回退理由（必填）
   - `ip_address`：操作者 IP
   - `user_agent`：操作者客户端
   - `created_at`：操作时间

### 14.2.3 禁止的终态回退场景

以下终态回退**绝对禁止**，即使 admin 也不得执行：

| 模块 | 禁止的回退 | 原因 | 替代方案 |
|------|-----------|------|---------|
| `topup_requests` | `completed` → 任意状态 | 资金已到账，Ledger Entry 已创建 | 创建新的 Adjustment Entry |
| `daily_reports` | `approved` → `draft` | 已生成 Ledger Entry，影响账本 | 创建冲正 Entry |
| `ledger_entries` | 无状态机，但禁止 DELETE | 账本不可修改 | 创建负数 Entry 冲正 |
| `reconciliation_details` | `adjusted` → `pending` | 调整已生效，账本已变更 | 创建新的调整记录 |

### 14.2.4 终态回退实施流程

**前置检查**（Service 层）：

```python
def rollback_from_final_state(
    entity_type: str,
    entity_id: int,
    target_status: str,
    reason: str,
    operator: AuthenticatedUser
) -> Result:
    # 1. 权限校验
    if operator.role != "admin":
        raise PermissionDeniedError(
            "终态回退仅允许 admin 执行",
            error_code="STATE_403"
        )

    # 2. 理由校验
    if len(reason.strip()) < 10:
        raise ValidationError(
            "回退理由至少 10 个字符",
            error_code="VALIDATION_001"
        )

    # 3. 检查是否为禁止回退的场景
    if entity_type == "topup_requests" and current_status == "completed":
        raise BusinessLogicError(
            "已完成的充值申请不可回退，请创建调整记录",
            error_code="STATE_405"
        )

    # 4. 检查关联数据完整性
    if entity_type == "daily_reports" and has_ledger_entries(entity_id):
        raise BusinessLogicError(
            "已生成账本分录的日报不可回退，请创建冲正分录",
            error_code="STATE_406"
        )

    # 5. 执行回退 + 审计
    with transaction():
        update_status(entity_type, entity_id, target_status)
        audit_log(
            module=entity_type,
            action="rollback_from_final_state",
            entity_id=entity_id,
            performed_by=operator.id,
            role="admin",
            payload_before={"status": current_status, ...},
            payload_after={"status": target_status},
            reason=reason,
            ip_address=request.client_ip,
            user_agent=request.user_agent
        )
```

### 14.2.5 终态回退错误码

| 错误码 | 说明 | HTTP | 触发条件 |
|--------|------|------|---------|
| `STATE_403` | 终态回退权限不足 | 403 | 非 admin 尝试回退 |
| `STATE_404` | 实体不存在或非终态 | 404 | 回退的实体不在终态 |
| `STATE_405` | 禁止回退的终态 | 400 | 尝试回退已完成充值等 |
| `STATE_406` | 回退影响关联数据 | 400 | 已生成 Ledger Entry |
| `VALIDATION_001` | 回退理由缺失或过短 | 400 | reason 少于 10 字符 |

---

## 14.3 【P0 必须补充】充值申请金额锁定规则

### 14.3.1 金额锁定时机

**核心原则**：金额字段 `topup_requests.amount` 在进入审批流程后锁定，禁止修改。

**锁定节点**：

| 状态 | 金额可编辑 | 说明 |
|------|-----------|------|
| `draft` | ✅ 可修改 | 申请人草稿阶段 |
| `pending_review` | ❌ 锁定 | 已提交，等待数据复核 |
| `finance_approve` | ❌ 锁定 | 财务已批准 |
| `paid` | ❌ 锁定 | 已支付 |
| `completed` | ❌ 锁定（终态） | 已完成 |
| `rejected` | ❌ 锁定（终态） | 已拒绝，金额不归零 |
| `cancelled` | ❌ 锁定（终态） | 已取消 |

### 14.3.2 金额修改权限矩阵

| 操作 | draft | pending_review | finance_approve | paid | completed/rejected/cancelled |
|------|-------|---------------|----------------|------|------------------------------|
| **申请人修改** | ✅ 允许 | ❌ 禁止 | ❌ 禁止 | ❌ 禁止 | ❌ 禁止 |
| **data_operator 修改** | ✅ 允许（协助申请人） | ❌ 禁止 | ❌ 禁止 | ❌ 禁止 | ❌ 禁止 |
| **finance 修改** | ✅ 允许（协助申请人） | ❌ 禁止 | ❌ 禁止 | ❌ 禁止 | ❌ 禁止 |
| **admin 强制修改** | ✅ 允许 | ⚠️ 允许（需审计） | ⚠️ 允许（需审计） | ❌ 禁止 | ❌ 禁止 |

### 14.3.3 Admin 强制修改金额规则

**场景**：申请提交后发现金额错误，但已进入审批流程。

**允许条件**：
1. 仅 `admin` 可执行
2. 仅在 `pending_review` 或 `finance_approve` 状态
3. 必须提供修改理由（最少 10 字符）
4. 必须记录审计日志（包含旧金额、新金额、理由）
5. 修改后状态回退至 `draft`（重新审批）

**实施代码**：

```python
def admin_force_update_topup_amount(
    topup_id: int,
    new_amount: Decimal,
    reason: str,
    operator: AuthenticatedUser
) -> Result:
    # 1. 权限校验
    if operator.role != "admin":
        raise PermissionDeniedError(
            "仅 admin 可修改审批中的充值金额",
            error_code="AUTH_500"
        )

    # 2. 状态校验
    topup = get_topup_request(topup_id)
    if topup.status not in ["pending_review", "finance_approve"]:
        raise BusinessLogicError(
            f"当前状态 {topup.status} 不允许修改金额",
            error_code="STATE_400"
        )

    # 3. 金额校验
    if new_amount <= 0:
        raise ValidationError("金额必须大于 0", error_code="BIZ_100")

    # 4. 理由校验
    if len(reason.strip()) < 10:
        raise ValidationError(
            "修改理由至少 10 个字符",
            error_code="VALIDATION_001"
        )

    # 5. 执行修改 + 状态回退 + 审计
    with transaction():
        old_amount = topup.amount
        topup.amount = new_amount
        topup.status = "draft"  # 回退至草稿，重新审批
        topup.updated_by = operator.id
        db.commit()

        audit_log(
            module="topup_requests",
            action="admin_force_update_amount",
            entity_id=topup_id,
            performed_by=operator.id,
            role="admin",
            payload_before={"amount": old_amount, "status": topup.status},
            payload_after={"amount": new_amount, "status": "draft"},
            reason=f"Admin 强制修改金额：{reason}",
            ip_address=request.client_ip
        )
```

### 14.3.4 Rejected 状态金额处理

**规则**：`rejected` 状态的充值申请**不归零金额**，保留原申请金额用于审计。

**理由**：
1. 保留完整的申请记录供审计追溯
2. 拒绝原因可能与金额无关（如时机不合适）
3. 申请人可基于原金额创建新申请

**禁止**：
- ❌ 将 `rejected` 申请的金额设为 0
- ❌ 删除 `rejected` 申请记录

**允许**：
- ✅ 查询 `rejected` 申请的原始金额
- ✅ 基于 `rejected` 申请创建新申请（复制金额）

### 14.3.5 金额修改错误码

| 错误码 | 说明 | HTTP | 触发条件 |
|--------|------|------|---------|
| `STATE_400` | 当前状态不允许修改金额 | 400 | 在锁定状态下尝试修改 |
| `AUTH_500` | 无权限修改金额 | 403 | 非 admin 尝试强制修改 |
| `BIZ_100` | 金额无效 | 400 | 金额 ≤ 0 或格式错误 |
| `VALIDATION_001` | 修改理由缺失 | 400 | admin 修改但未提供理由 |

---

## 14.4 【P0 必须补充】对账批次完成条件

### 14.4.1 完成前置条件

对账批次 `reconciliation_batches` 从 `approved` 流转至 `completed` 必须满足：

**强制前置条件**（缺一不可）：

1. **所有明细已处理完毕**
   ```sql
   -- 必须满足：该批次下无 pending 状态的明细
   SELECT COUNT(*) FROM reconciliation_details
   WHERE batch_id = ? AND status = 'pending';
   -- 结果必须为 0
   ```

2. **明细状态分布合法**
   ```sql
   -- 所有明细必须处于终态
   SELECT status, COUNT(*) FROM reconciliation_details
   WHERE batch_id = ?
   GROUP BY status;
   -- 仅允许返回 'confirmed' 和 'adjusted'
   ```

3. **调整金额已生成 Ledger Entry**
   ```sql
   -- 所有 status='adjusted' 的明细必须有对应的 adjustment 类型 LedgerEntry
   SELECT d.id
   FROM reconciliation_details d
   LEFT JOIN ledger_entries l
       ON l.reference_id = d.id
       AND l.entry_type = 'adjustment'
   WHERE d.batch_id = ?
       AND d.status = 'adjusted'
       AND l.id IS NULL;
   -- 结果必须为空
   ```

4. **批次报告已生成**
   ```sql
   -- 必须存在对应的 reconciliation_report
   SELECT COUNT(*) FROM reconciliation_reports
   WHERE batch_id = ?;
   -- 结果必须 > 0
   ```

5. **执行者权限**
   - 必须为 `finance` 或 `admin` 角色

### 14.4.2 完成操作实施流程

```python
def complete_reconciliation_batch(
    batch_id: int,
    operator: AuthenticatedUser
) -> Result:
    # 1. 权限校验
    if operator.role not in ["finance", "admin"]:
        raise PermissionDeniedError(
            "仅 finance 或 admin 可完成对账批次",
            error_code="AUTH_500"
        )

    batch = get_reconciliation_batch(batch_id)

    # 2. 状态校验
    if batch.status != "approved":
        raise BusinessLogicError(
            f"当前状态 {batch.status} 不允许完成",
            error_code="STATE_400"
        )

    # 3. 前置条件检查
    pending_count = db.query(ReconciliationDetail).filter(
        ReconciliationDetail.batch_id == batch_id,
        ReconciliationDetail.status == "pending"
    ).count()

    if pending_count > 0:
        raise BusinessLogicError(
            f"仍有 {pending_count} 条明细未处理（pending 状态）",
            error_code="RECON_001"
        )

    # 4. 检查调整是否已生成 Ledger
    adjusted_details = db.query(ReconciliationDetail.id).filter(
        ReconciliationDetail.batch_id == batch_id,
        ReconciliationDetail.status == "adjusted"
    ).all()

    for detail_id in adjusted_details:
        ledger_exists = db.query(LedgerEntry).filter(
            LedgerEntry.reference_id == detail_id,
            LedgerEntry.entry_type == "adjustment"
        ).count() > 0

        if not ledger_exists:
            raise BusinessLogicError(
                f"明细 {detail_id} 的调整尚未生成账本分录",
                error_code="RECON_002"
            )

    # 5. 检查报告是否已生成
    report_exists = db.query(ReconciliationReport).filter(
        ReconciliationReport.batch_id == batch_id
    ).count() > 0

    if not report_exists:
        raise BusinessLogicError(
            "批次报告尚未生成，请先生成报告",
            error_code="RECON_003"
        )

    # 6. 执行完成 + 审计
    with transaction():
        batch.status = "completed"
        batch.updated_by = operator.id
        batch.completed_at = datetime.utcnow()
        db.commit()

        audit_log(
            module="reconciliation_batches",
            action="close_batch",
            entity_id=batch_id,
            performed_by=operator.id,
            role=operator.role,
            payload_before={"status": "approved"},
            payload_after={"status": "completed"},
            created_at=datetime.utcnow()
        )
```

### 14.4.3 禁止的完成场景

以下场景**严格禁止**完成对账批次：

| 场景 | 禁止原因 | 错误码 |
|------|---------|--------|
| 批次状态为 `draft` 或 `pending_review` 或 `needs_adjustment` | 未进入 approved 阶段 | `STATE_400` |
| 存在 `pending` 状态明细 | 明细未处理完毕 | `RECON_001` |
| `adjusted` 明细无对应 Ledger | 调整未入账 | `RECON_002` |
| 未生成批次报告 | 缺少审计依据 | `RECON_003` |
| 非 finance/admin 角色 | 权限不足 | `AUTH_500` |

### 14.4.4 强制完成机制（Admin 特权）

**场景**：紧急情况下需强制完成批次（如系统故障、数据迁移）。

**允许条件**：
1. 仅 `admin` 可执行
2. 必须提供强制完成理由（最少 20 字符）
3. 必须记录安全审计日志
4. 强制完成后批次状态标记为 `completed`（force_completed 标记为 True）

**实施代码**：

```python
def admin_force_complete_batch(
    batch_id: int,
    reason: str,
    operator: AuthenticatedUser
) -> Result:
    if operator.role != "admin":
        raise PermissionDeniedError(
            "仅 admin 可强制完成批次",
            error_code="AUTH_500"
        )

    if len(reason.strip()) < 20:
        raise ValidationError(
            "强制完成理由至少 20 个字符",
            error_code="VALIDATION_001"
        )

    with transaction():
        batch = get_reconciliation_batch(batch_id)
        batch.status = "completed"
        batch.force_completed = True  # 新增标记字段
        batch.force_complete_reason = reason
        batch.updated_by = operator.id
        db.commit()

        audit_log(
            module="reconciliation_batches",
            action="admin_force_complete",
            entity_id=batch_id,
            performed_by=operator.id,
            role="admin",
            reason=reason,
            payload_after={"status": "completed", "force_completed": True}
        )

        # 发送安全告警
        send_security_alert(
            level="HIGH",
            message=f"Admin {operator.username} 强制完成对账批次 {batch_id}",
            reason=reason
        )
```

### 14.4.5 对账完成错误码

| 错误码 | 说明 | HTTP | 触发条件 |
|--------|------|------|---------|
| `RECON_001` | 存在未处理明细 | 400 | pending 状态明细数 > 0 |
| `RECON_002` | 调整未生成账本分录 | 400 | adjusted 明细无 Ledger |
| `RECON_003` | 批次报告未生成 | 400 | reconciliation_report 不存在 |
| `STATE_400` | 当前状态不允许完成 | 400 | 状态非 approved |
| `AUTH_500` | 权限不足 | 403 | 非 finance/admin 角色 |

---

## 14.5 【P0 必须补充】禁止流转机制（Forbidden Transitions）

### 14.5.1 白名单机制定义

**核心原则**：除本文档明确列出的合法流转外，所有其他状态流转均视为**非法流转**。

**实施策略**：

```python
# 定义合法流转白名单（基于本文档第 4-11 章）
ALLOWED_TRANSITIONS = {
    "projects.status": {
        "draft": ["active", "suspended", "archived"],
        "active": ["suspended", "archived"],
        "suspended": ["active", "archived"],
        "archived": []  # 终态，无合法流转
    },
    "daily_reports.status": {
        "raw_submitted": ["trend_pending"],
        "trend_pending": ["trend_ok", "trend_flagged"],
        "trend_ok": ["final_pending"],
        "trend_flagged": ["trend_resolved", "raw_submitted"],
        "trend_resolved": ["final_pending"],
        "final_pending": ["final_confirmed"],
        "final_confirmed": ["final_locked"],
        "final_locked": []  # 终态,仅可通过红冲修正
    },
    "topup_requests.status": {
        "draft": ["pending_review", "cancelled"],
        "pending_review": ["finance_approve", "rejected"],
        "finance_approve": ["paid", "rejected"],
        "paid": ["completed"],
        "completed": [],  # 终态
        "rejected": [],  # 终态
        "cancelled": []  # 终态
    },
    "ad_accounts.status": {
        "new": ["testing", "active", "suspended", "dead", "archived"],
        "testing": ["active", "suspended", "dead", "archived"],
        "active": ["suspended", "dead", "archived"],
        "suspended": ["active", "dead", "archived"],
        "dead": ["archived"],  # dead 只能归档，不可恢复
        "archived": []  # 终态
    },
    "reconciliation_batches.status": {
        "draft": ["pending_review"],
        "pending_review": ["approved", "needs_adjustment"],
        "approved": ["completed"],
        "needs_adjustment": ["approved"],
        "completed": []  # 终态
    },
    "reconciliation_details.status": {
        "pending": ["confirmed", "adjusted"],
        "confirmed": [],  # 终态
        "adjusted": []  # 终态
    },
    "transfer_requests.status": {
        "draft": ["pending_approval", "rejected"],
        "pending_approval": ["approved", "rejected"],
        "approved": ["completed"],
        "rejected": [],  # 终态
        "completed": []  # 终态
    },
    # 其他模块省略，完整定义见各章节
}

def validate_state_transition(
    entity_type: str,
    current_status: str,
    target_status: str
) -> bool:
    """验证状态流转是否合法"""
    allowed = ALLOWED_TRANSITIONS.get(entity_type, {})
    allowed_targets = allowed.get(current_status, [])

    if target_status not in allowed_targets:
        return False
    return True
```

### 14.5.2 非法流转处理流程

当检测到非法流转时：

**1. 立即阻止**
```python
if not validate_state_transition(entity_type, current_status, target_status):
    raise ForbiddenTransitionError(
        f"非法流转：{entity_type}.{current_status} → {target_status}",
        error_code="STATE_400",
        details={
            "entity_type": entity_type,
            "current_status": current_status,
            "attempted_status": target_status,
            "allowed_transitions": ALLOWED_TRANSITIONS[entity_type][current_status]
        }
    )
```

**2. 记录审计日志**
```python
audit_log(
    module=entity_type,
    action="forbidden_transition_attempt",
    entity_id=entity_id,
    performed_by=operator.id if operator else None,
    role=operator.role if operator else "system",
    payload_before={"status": current_status},
    payload_after={"attempted_status": target_status, "blocked": True},
    ip_address=request.client_ip,
    severity="WARNING"
)
```

**3. 安全告警**

对于严重的非法流转尝试（如终态 → 非终态、跨越多个状态跳转），触发安全告警：

```python
CRITICAL_FORBIDDEN_TRANSITIONS = [
    # 终态回退（非 admin）
    ("topup_requests.completed", "*"),
    ("daily_reports.approved", "*"),
    ("reconciliation_batches.completed", "*"),

    # 跳过审批
    ("topup_requests.draft", "paid"),
    ("topup_requests.draft", "completed"),
    ("daily_reports.draft", "approved"),

    # 财务敏感
    ("topup_requests.pending_review", "completed"),
]

if is_critical_forbidden_transition(entity_type, current_status, target_status):
    send_security_alert(
        level="CRITICAL",
        message=f"检测到严重非法流转尝试",
        details={
            "operator": operator.username if operator else "system",
            "entity": f"{entity_type}#{entity_id}",
            "transition": f"{current_status} → {target_status}",
            "ip": request.client_ip,
            "timestamp": datetime.utcnow()
        }
    )
```

### 14.5.3 非法流转错误码体系

| 错误码 | 说明 | HTTP | 触发场景 |
|--------|------|------|---------|
| `STATE_400` | 非法状态流转 | 400 | 不在白名单的流转 |
| `STATE_401` | 跳过必要步骤 | 400 | 如 draft → completed |
| `STATE_402` | 终态非法回退 | 400 | 终态 → 非终态（非 admin） |
| `STATE_403` | 系统无权限流转 | 403 | system 尝试禁止的流转 |
| `STATE_404` | 实体状态不存在 | 404 | 当前状态不在枚举中 |
| `STATE_405` | 绝对禁止的流转 | 400 | 如 completed 充值回退 |

### 14.5.4 非法流转监控与报告

**实时监控指标**：

```python
# Prometheus metrics
forbidden_transition_attempts_total = Counter(
    "forbidden_transition_attempts_total",
    "非法流转尝试次数",
    ["entity_type", "from_status", "to_status", "operator_role"]
)

forbidden_transition_attempts_total.labels(
    entity_type="topup_requests",
    from_status="draft",
    to_status="completed",
    operator_role="media_buyer"
).inc()
```

**日报告**：

每日生成非法流转尝试报告，包含：
- 尝试次数最多的流转路径
- 尝试者角色分布
- 尝试时间分布（识别是否为自动化攻击）
- 关联的 IP 地址

### 14.5.5 合法流转白名单更新流程

当需要新增合法流转时：

1. **更新本文档**：在对应章节（第 5-11 章）明确新增的流转路径
2. **更新 DATA_SCHEMA**：同步更新 CHECK 约束
3. **更新代码白名单**：更新 `ALLOWED_TRANSITIONS` 常量
4. **更新测试用例**：新增流转路径的正向/反向测试
5. **版本发布**：在第 18 章"版本历史"中记录变更

**禁止**：
- ❌ 仅修改代码白名单而不更新本文档
- ❌ 绕过白名单机制直接 UPDATE status
- ❌ 使用"临时"白名单（如 `TEMP_ALLOWED_TRANSITIONS`）

---

## 15. 【P0 增强】数据库 CHECK 约束同步清单

### 15.1 CHECK 约束 vs ENUM 类型规范

**技术选型决策**：AI_ad_spend 系统统一使用 **VARCHAR + CHECK 约束**，不使用 PostgreSQL ENUM 类型。

**理由**：
1. **灵活性**：CHECK 约束可通过 ALTER TABLE 修改，ENUM 类型修改需要复杂的迁移
2. **版本控制**：CHECK 约束变更可通过 Alembic 迁移清晰追溯
3. **跨库兼容**：VARCHAR + CHECK 可移植到其他数据库（MySQL, SQLite）
4. **性能影响**：VARCHAR(20) vs ENUM 性能差异可忽略（< 1%）

**强制规范**：
```sql
-- ✅ 正确示例（使用 VARCHAR + CHECK）
ALTER TABLE projects
ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'draft'
CHECK (status IN ('draft', 'active', 'suspended', 'archived'));

-- ❌ 禁止示例（使用 ENUM）
CREATE TYPE project_status_enum AS ENUM ('draft', 'active', 'suspended', 'archived');
ALTER TABLE projects ADD COLUMN status project_status_enum;
```

### 15.2 状态字段 CHECK 约束模板库

以下模板必须与第 4 章"全局状态一览表"**严格同步**，任何状态变更必须同步更新。

#### 15.2.1 项目状态（projects.status）

```sql
-- 迁移文件：backend/alembic/versions/YYYYMMDD_projects_status_check.py

ALTER TABLE projects
ADD CONSTRAINT chk_projects_status
CHECK (status IN ('draft', 'active', 'suspended', 'archived'));

-- 默认值约束
ALTER TABLE projects
ALTER COLUMN status SET DEFAULT 'draft';

-- 非空约束
ALTER TABLE projects
ALTER COLUMN status SET NOT NULL;
```

**同步要求**：
- 与第 5 章"项目状态机"的合法取值一致
- 与 `backend/models/core/project.py` 的 ProjectStatus 枚举一致
- 与 `backend/schemas/project.py` 的 Pydantic 验证一致

#### 15.2.2 日报状态（daily_reports.status）

```sql
ALTER TABLE daily_reports
ADD CONSTRAINT chk_daily_reports_status
CHECK (status IN (
    'raw_submitted',
    'trend_pending',
    'trend_ok',
    'trend_flagged',
    'trend_resolved',
    'final_pending',
    'final_confirmed',
    'final_locked'
));

ALTER TABLE daily_reports
ALTER COLUMN status SET DEFAULT 'raw_submitted';

ALTER TABLE daily_reports
ALTER COLUMN status SET NOT NULL;
```

**同步要求**:
- 与第 8 章"粉数确认状态机"的8个状态一致
- 与 `backend/models/workflow/daily_report.py` 一致
- 与 BRD v3.1 第4章粉数确认流程对齐

#### 15.2.3 充值申请状态（topup_requests.status）

```sql
ALTER TABLE topup_requests
ADD CONSTRAINT chk_topup_requests_status
CHECK (status IN (
    'draft',
    'pending_review',
    'finance_approve',
    'paid',
    'completed',
    'rejected',
    'cancelled'
));

ALTER TABLE topup_requests
ALTER COLUMN status SET DEFAULT 'draft';
```

**同步要求**：
- 与第 9 章"充值申请"一致
- 必须包含所有 7 个状态，不得遗漏

#### 15.2.4 广告账户状态（ad_accounts.status）

```sql
ALTER TABLE ad_accounts
ADD CONSTRAINT chk_ad_accounts_status
CHECK (status IN (
    'new',
    'testing',
    'active',
    'suspended',
    'dead',
    'archived'
));

ALTER TABLE ad_accounts
ALTER COLUMN status SET DEFAULT 'new';
```

**同步要求**：
- 与第 7.1 章"账户生命周期"一致
- 终态包含 'dead' 和 'archived'

#### 15.2.5 对账批次状态（reconciliation_batches.status）

```sql
ALTER TABLE reconciliation_batches
ADD CONSTRAINT chk_reconciliation_batches_status
CHECK (status IN ('draft', 'pending_review', 'approved', 'needs_adjustment', 'completed'));

-- 注意：'archived' 为 planned 状态，当前禁止使用

ALTER TABLE reconciliation_batches
ALTER COLUMN status SET DEFAULT 'draft';
```

**同步要求**：
- 与第 11.1 章"对账批次"一致
- 禁止使用 'archived'（planned 状态）

#### 15.2.6 对账明细状态（reconciliation_details.status）

```sql
ALTER TABLE reconciliation_details
ADD CONSTRAINT chk_reconciliation_details_status
CHECK (status IN ('pending', 'confirmed', 'adjusted'));

ALTER TABLE reconciliation_details
ALTER COLUMN status SET DEFAULT 'pending';
```

#### 15.2.7 渠道状态（channels.status）

```sql
ALTER TABLE channels
ADD CONSTRAINT chk_channels_status
CHECK (status IN ('active', 'inactive'));

ALTER TABLE channels
ALTER COLUMN status SET DEFAULT 'active';
```

#### 15.2.8 渠道评审状态（channel_reviews.review_status）

```sql
ALTER TABLE channel_reviews
ADD CONSTRAINT chk_channel_reviews_review_status
CHECK (review_status IN ('draft', 'pending', 'approved', 'rejected'));

ALTER TABLE channel_reviews
ALTER COLUMN review_status SET DEFAULT 'draft';
```

#### 15.2.9 渠道开户申请状态（channel_account_requests.status）

```sql
ALTER TABLE channel_account_requests
ADD CONSTRAINT chk_channel_account_requests_status
CHECK (status IN ('draft', 'pending', 'approved', 'rejected'));

ALTER TABLE channel_account_requests
ALTER COLUMN status SET DEFAULT 'draft';
```

#### 15.2.10 账户预警状态（account_alerts.status）

```sql
ALTER TABLE account_alerts
ADD CONSTRAINT chk_account_alerts_status
CHECK (status IN ('open', 'ack', 'resolved'));

ALTER TABLE account_alerts
ALTER COLUMN status SET DEFAULT 'open';
```

### 15.3 与 DATA_SCHEMA.md 的同步流程

**强制同步规则**：

1. **状态变更必经路径**（按顺序执行）：
   ```
   1. 修改 STATE_MACHINE.md（本文件）
      ├─ 更新第 4 章"全局状态一览表"
      ├─ 更新对应章节的合法取值
      └─ 更新第 15 章 CHECK 约束模板

   2. 修改 DATA_SCHEMA.md
      ├─ 更新表结构定义
      └─ 复制本文件的 CHECK 约束

   3. 创建 Alembic 迁移文件
      ├─ 文件名：YYYYMMDD_add_xxx_status_check.py
      ├─ upgrade()：添加 CHECK 约束
      └─ downgrade()：删除 CHECK 约束

   4. 更新 SQLAlchemy 模型
      ├─ 定义枚举类（如 ProjectStatus）
      ├─ 在 Column 定义中使用枚举
      └─ 添加 validate_status() 方法

   5. 更新 Pydantic 模型
      ├─ 在 Schema 中定义 Literal 或 Enum
      └─ 添加 @validator 进行额外验证

   6. 更新测试用例
      ├─ 正向测试：合法状态值
      └─ 反向测试：非法状态值（触发 CHECK 约束）
   ```

2. **禁止的操作**：
   - ❌ 仅修改数据库而不更新本文件
   - ❌ 仅修改模型枚举而不更新 CHECK 约束
   - ❌ 跳过 Alembic 迁移直接执行 SQL
   - ❌ 在本文件之外定义新状态值

### 15.4 CHECK 约束违反错误处理

**数据库级错误**：

当应用尝试写入非法状态值时，PostgreSQL 将抛出：

```
sqlalchemy.exc.IntegrityError: (psycopg2.errors.CheckViolation)
new row for relation "projects" violates check constraint "chk_projects_status"
DETAIL:  Failing row contains (1, "Test Project", "invalid_status", ...).
```

**应用层处理**：

```python
from sqlalchemy.exc import IntegrityError
from psycopg2.errors import CheckViolation

try:
    project.status = "invalid_status"
    db.commit()
except IntegrityError as e:
    if isinstance(e.orig, CheckViolation):
        # 捕获 CHECK 约束违反
        raise BusinessLogicError(
            f"状态值 'invalid_status' 不在合法枚举中",
            error_code="VALIDATION_006",  # 枚举值无效
            details={
                "field": "status",
                "value": "invalid_status",
                "allowed_values": ["draft", "active", "suspended", "archived"]
            }
        )
    else:
        raise
```

### 15.5 CHECK 约束变更迁移示例

**场景**：需要新增一个状态值（如 topup_requests 新增 'partial_paid'）

**步骤**：

```python
# 1. 创建迁移文件：backend/alembic/versions/20250119_add_partial_paid_status.py

"""add partial_paid status to topup_requests

Revision ID: abc123
Revises: def456
Create Date: 2025-01-19 10:00:00
"""

from alembic import op

def upgrade():
    # 删除旧 CHECK 约束
    op.drop_constraint(
        'chk_topup_requests_status',
        'topup_requests',
        type_='check'
    )

    # 创建新 CHECK 约束（包含新状态）
    op.create_check_constraint(
        'chk_topup_requests_status',
        'topup_requests',
        "status IN ('draft', 'pending_review', 'finance_approve', 'paid', 'partial_paid', 'completed', 'rejected', 'cancelled')"
    )

def downgrade():
    # 回滚：删除新约束
    op.drop_constraint(
        'chk_topup_requests_status',
        'topup_requests',
        type_='check'
    )

    # 恢复旧约束（不包含新状态）
    op.create_check_constraint(
        'chk_topup_requests_status',
        'topup_requests',
        "status IN ('draft', 'pending_review', 'finance_approve', 'paid', 'completed', 'rejected', 'cancelled')"
    )
```

### 15.6 CHECK 约束审计清单

在每次发布前，必须执行以下审计：

- [ ] 所有状态字段均有对应的 CHECK 约束
- [ ] CHECK 约束的合法值与本文件第 4 章严格一致
- [ ] DATA_SCHEMA.md 已同步更新
- [ ] SQLAlchemy 模型的枚举类已同步
- [ ] Pydantic Schema 的验证已同步
- [ ] Alembic 迁移文件已创建且可回滚
- [ ] 测试用例覆盖合法值和非法值
- [ ] 前端常量已同步更新（如适用）

---

## 16. 【P0 增强】API → 状态流转映射表

### 16.1 映射表说明

本章节列出所有涉及状态变更的 API 端点，明确：
- 当前状态前置条件
- 目标状态
- 执行角色
- 审计要求
- 错误码

### 16.2 项目状态流转 API

| API 端点 | HTTP 方法 | 当前状态 | 目标状态 | 允许角色 | 审计 | 错误码 |
|---------|---------|---------|---------|---------|------|--------|
| `POST /projects` | POST | - | draft | admin, account_manager | [AUDIT] | AUTH_500, BIZ_003 |
| `PUT /projects/{id}/activate` | PUT | draft, suspended | active | admin, account_manager | [AUDIT] | STATE_400, AUTH_500 |
| `PUT /projects/{id}/suspend` | PUT | active | suspended | admin, account_manager | [AUDIT] | STATE_400, AUTH_500 |
| `PUT /projects/{id}/resume` | PUT | suspended | active | admin, account_manager | [AUDIT] | STATE_400, AUTH_500 |
| `PUT /projects/{id}/archive` | PUT | draft, active, suspended | archived | admin | [AUDIT] | STATE_400, AUTH_500 |
| `PUT /projects/{id}/unarchive` | PUT | archived | draft | admin | [AUDIT] 强制 | STATE_402, AUTH_500 |

**实施规范**：

```python
# backend/routers/projects.py

@router.put("/projects/{project_id}/activate")
async def activate_project(
    project_id: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: ProjectService = Depends()
):
    # 1. 权限校验
    if current_user.role not in ["admin", "account_manager"]:
        raise PermissionDeniedError(
            "仅 admin 或 account_manager 可激活项目",
            error_code="AUTH_500"
        )

    # 2. 状态流转
    try:
        project = await service.transition_status(
            project_id=project_id,
            target_status="active",
            operator=current_user,
            reason=None  # 可选
        )
        return success_response(data=project)
    except ForbiddenTransitionError as e:
        return error_response(
            code="STATE_400",
            message=str(e),
            status_code=400
        )
```

### 16.3 日报状态流转 API (粉数确认6状态流程)

| API 端点 | HTTP 方法 | 当前状态 | 目标状态 | 允许角色 | 审计 | 错误码 |
|---------|---------|---------|---------|---------|------|--------|
| `POST /daily-reports` | POST | - | raw_submitted | media_buyer | [AUDIT] | AUTH_500, BIZ_003 |
| `POST /daily-reports/{id}/trend-check` | POST | raw_submitted | trend_pending | system | [AUDIT] | STATE_400 |
| `PUT /daily-reports/{id}/trend-resolve` | PUT | trend_flagged | trend_resolved | data_operator, admin | [AUDIT] | STATE_400, AUTH_500 |
| `PUT /daily-reports/{id}/update-real-spend` | PUT | trend_ok, trend_resolved | final_pending | data_operator, admin | [AUDIT] | STATE_400, AUTH_500 |
| `PUT /daily-reports/{id}/final-confirm` | PUT | final_pending | final_confirmed | data_operator, admin | [AUDIT] | STATE_400, AUTH_500 |
| `POST /daily-reports/{id}/final-lock` | POST | final_confirmed | final_locked | system | [AUDIT] | STATE_400 |
| `POST /daily-reports/{id}/reversal` | POST | final_locked | - (红冲) | admin | [AUDIT]强制 | STATE_402, AUTH_500 |

**审计要求**:
- 所有状态变更必须记录 `daily_report_audit_logs`
- 必填字段: old_status, new_status, audit_user_id, audit_time, audit_notes
- 特殊场景:
  - `trend_flagged`: 记录触发规则 (TF-001/002/003)
  - `trend_resolved`: 记录运营复核说明 (`trend_resolution_note`)
  - `final_locked`: 记录计费金额和Ledger Entry ID
  - 红冲修正: 记录原记录ID、红冲记录ID、修正原因

### 16.4 充值申请状态流转 API

| API 端点 | HTTP 方法 | 当前状态 | 目标状态 | 允许角色 | 审计 | 错误码 |
|---------|---------|---------|---------|---------|------|--------|
| `POST /topup-requests` | POST | - | draft | media_buyer, account_manager | [AUDIT] | AUTH_500, BIZ_100 |
| `PUT /topup-requests/{id}/submit` | PUT | draft | pending_review | applicant | [AUDIT] | STATE_400, BIZ_100 |
| `PUT /topup-requests/{id}/review` | PUT | pending_review | finance_approve, rejected | data_operator | [AUDIT] | STATE_400, AUTH_500 |
| `PUT /topup-requests/{id}/approve` | PUT | finance_approve | paid | finance | [AUDIT] | STATE_400, AUTH_500 |
| `PUT /topup-requests/{id}/reject` | PUT | pending_review, finance_approve | rejected | data_operator, finance | [AUDIT] | STATE_400, AUTH_500 |
| `PUT /topup-requests/{id}/complete` | PUT | paid | completed | finance, system | [AUDIT] | STATE_400, RECON_002 |
| `PUT /topup-requests/{id}/cancel` | PUT | draft, pending_review | cancelled | applicant, admin | [AUDIT] | STATE_400, AUTH_500 |

**金额锁定规则**（参考 14.3 章节）：
- draft → pending_review 时，金额锁定
- 仅 admin 可在 pending_review/finance_approve 状态强制修改金额（需理由）

### 16.5 广告账户状态流转 API

| API 端点 | HTTP 方法 | 当前状态 | 目标状态 | 允许角色 | 审计 | 错误码 |
|---------|---------|---------|---------|---------|------|--------|
| `POST /ad-accounts` | POST | - | new | admin, account_manager, data_operator | [AUDIT] | AUTH_500, BIZ_003 |
| `PUT /ad-accounts/{id}/activate` | PUT | new, testing, suspended | active | account_manager, admin | [AUDIT] | STATE_400, AUTH_500 |
| `PUT /ad-accounts/{id}/suspend` | PUT | active, testing | suspended | account_manager, admin | [AUDIT] | STATE_400, AUTH_500 |
| `PUT /ad-accounts/{id}/mark-dead` | PUT | any (non-terminal) | dead | admin | [AUDIT] | STATE_400, AUTH_500 |
| `PUT /ad-accounts/{id}/archive` | PUT | dead, suspended | archived | admin | [AUDIT] | STATE_400, AUTH_500 |

**状态历史记录**：
- 所有状态变更必须自动写入 `account_status_history`
- 字段：ad_account_id, from_status, to_status, changed_by, changed_at, notes

### 16.6 对账批次状态流转 API

| API 端点 | HTTP 方法 | 当前状态 | 目标状态 | 允许角色 | 审计 | 错误码 |
|---------|---------|---------|---------|---------|------|--------|
| `POST /reconciliation-batches` | POST | - | draft | finance, admin | [AUDIT] | AUTH_500, BIZ_003 |
| `PUT /reconciliation-batches/{id}/submit` | PUT | draft | pending_review | finance, data_operator | [AUDIT] | STATE_400, AUTH_500 |
| `PUT /reconciliation-batches/{id}/approve` | PUT | pending_review | approved | finance, admin | [AUDIT] | STATE_400, AUTH_500 |
| `PUT /reconciliation-batches/{id}/request-adjustment` | PUT | pending_review | needs_adjustment | finance, admin | [AUDIT] | STATE_400, AUTH_500 |
| `PUT /reconciliation-batches/{id}/complete` | PUT | approved | completed | finance, admin | [AUDIT] | STATE_400, RECON_001/002/003 |
| `PUT /reconciliation-batches/{id}/force-complete` | PUT | any (non-completed) | completed | admin | [AUDIT] 强制 | STATE_400, AUTH_500 |

**完成前置条件**（参考 14.4 章节）：
- 必须检查所有明细已处理（无 pending 状态）
- 必须检查调整已生成 Ledger Entry
- 必须检查批次报告已生成

### 16.7 对账明细状态流转 API

| API 端点 | HTTP 方法 | 当前状态 | 目标状态 | 允许角色 | 审计 | 错误码 |
|---------|---------|---------|---------|---------|------|--------|
| `POST /reconciliation-details` | POST | - | pending | finance, data_operator | [AUDIT] | AUTH_500 |
| `PUT /reconciliation-details/{id}/confirm` | PUT | pending | confirmed | finance, data_operator | [AUDIT] | STATE_400, AUTH_500 |
| `PUT /reconciliation-details/{id}/adjust` | PUT | pending | adjusted | finance, data_operator | [AUDIT] | STATE_400, BIZ_100 |

**调整记录要求**：
- adjusted 状态必须有对应的 `reconciliation_adjustments` 记录
- 必须提供 adjustment_type, amount, reason

### 16.8 渠道评审状态流转 API

| API 端点 | HTTP 方法 | 当前状态 | 目标状态 | 允许角色 | 审计 | 错误码 |
|---------|---------|---------|---------|---------|------|--------|
| `POST /channel-reviews` | POST | - | draft | account_manager, data_operator | [AUDIT] | AUTH_500 |
| `PUT /channel-reviews/{id}/submit` | PUT | draft | pending | account_manager, data_operator | [AUDIT] | STATE_400 |
| `PUT /channel-reviews/{id}/approve` | PUT | pending | approved | data_operator, admin | [AUDIT] | STATE_400, AUTH_500 |
| `PUT /channel-reviews/{id}/reject` | PUT | pending | rejected | data_operator, admin | [AUDIT] | STATE_400, AUTH_500 |

### 16.9 渠道开户申请状态流转 API

| API 端点 | HTTP 方法 | 当前状态 | 目标状态 | 允许角色 | 审计 | 错误码 |
|---------|---------|---------|---------|---------|------|--------|
| `POST /channel-account-requests` | POST | - | draft | account_manager, media_buyer | [AUDIT] | AUTH_500 |
| `PUT /channel-account-requests/{id}/submit` | PUT | draft | pending | account_manager, media_buyer | [AUDIT] | STATE_400 |
| `PUT /channel-account-requests/{id}/approve` | PUT | pending | approved | account_manager, admin | [AUDIT] | STATE_400, AUTH_500 |
| `PUT /channel-account-requests/{id}/reject` | PUT | pending | rejected | account_manager, admin | [AUDIT] | STATE_400, AUTH_500 |

### 16.10 账户预警状态流转 API

| API 端点 | HTTP 方法 | 当前状态 | 目标状态 | 允许角色 | 审计 | 错误码 |
|---------|---------|---------|---------|---------|------|--------|
| `POST /account-alerts` | POST | - | open | system, data_operator | [AUDIT] | - |
| `PUT /account-alerts/{id}/acknowledge` | PUT | open | ack | account_manager, admin | [AUDIT] | STATE_400 |
| `PUT /account-alerts/{id}/resolve` | PUT | ack | resolved | account_manager, admin | [AUDIT] | STATE_400 |

**System 自动流转**（参考 14.1 章节）：
- system 可自动创建预警（open 状态）
- system 可自动确认预警（open → ack，条件：超时 1 小时）

---

## 17. 【P0 增强】并发冲突处理规范（Optimistic Locking）

### 17.1 并发冲突场景

**典型场景**：

1. **双审批冲突**：
   - 用户 A 和用户 B 同时打开同一份日报（status=pending）
   - 用户 A 点击"审批通过"（pending → approved）
   - 用户 B 也点击"审批通过"（pending → approved，但实际已是 approved）
   - 结果：用户 B 的操作应被拒绝（STATE_409）

2. **状态竞争**：
   - 用户 A 执行充值审批（pending_review → finance_approve）
   - 同时用户 B 执行充值取消（pending_review → cancelled）
   - 结果：仅一个操作成功，另一个应返回冲突错误

3. **金额并发修改**：
   - 用户 A 修改充值金额为 1000
   - 用户 B 同时修改充值金额为 2000
   - 结果：后执行的操作应被拒绝，提示数据已变更

### 17.2 Optimistic Locking 实施方案

**方案 A：version 字段（推荐）**

```sql
-- 在所有需要并发控制的表中添加 version 字段
ALTER TABLE topup_requests
ADD COLUMN version INTEGER NOT NULL DEFAULT 1;

ALTER TABLE daily_reports
ADD COLUMN version INTEGER NOT NULL DEFAULT 1;

ALTER TABLE reconciliation_batches
ADD COLUMN version INTEGER NOT NULL DEFAULT 1;

-- 索引（可选，提升查询性能）
CREATE INDEX idx_topup_requests_version ON topup_requests(id, version);
```

**方案 B：updated_at 比较（次选）**

如果表已有 `updated_at` 字段，可直接使用：

```sql
-- 无需额外字段，使用现有的 updated_at
-- 但精度要求：TIMESTAMPTZ（微秒级）
```

**推荐**：使用方案 A（version 字段）
- 优点：语义清晰、避免时间戳精度问题、性能更好
- 缺点：需要额外字段（4 字节 INTEGER）

### 17.3 Service 层实现模式

#### 17.3.1 基于 version 字段的实现

```python
# backend/services/topup_service.py

from sqlalchemy.orm import Session
from sqlalchemy.exc import StaleDataError

class TopupService:
    def transition_status(
        self,
        topup_id: int,
        target_status: str,
        expected_version: int,  # 客户端传入的版本号
        operator: AuthenticatedUser,
        db: Session
    ) -> TopupRequest:
        # 1. 查询当前记录（加行锁）
        topup = db.query(TopupRequest).filter(
            TopupRequest.id == topup_id
        ).with_for_update().first()

        if not topup:
            raise ResourceNotFoundError(
                f"充值申请 {topup_id} 不存在",
                error_code="BIZ_002"
            )

        # 2. 版本号校验（Optimistic Locking）
        if topup.version != expected_version:
            raise ConcurrencyConflictError(
                f"数据已被其他用户修改（当前版本：{topup.version}，期望版本：{expected_version}）",
                error_code="STATE_409",
                details={
                    "current_version": topup.version,
                    "expected_version": expected_version,
                    "current_status": topup.status
                }
            )

        # 3. 状态流转验证
        if not validate_state_transition(
            "topup_requests.status",
            topup.status,
            target_status
        ):
            raise ForbiddenTransitionError(
                f"非法流转：{topup.status} → {target_status}",
                error_code="STATE_400"
            )

        # 4. 执行状态变更 + 版本号递增
        old_status = topup.status
        topup.status = target_status
        topup.version += 1  # 关键：版本号递增
        topup.updated_by = operator.id
        topup.updated_at = datetime.utcnow()

        # 5. 审计日志
        audit_log(
            module="topup_requests",
            action="transition_status",
            entity_id=topup_id,
            performed_by=operator.id,
            payload_before={"status": old_status, "version": expected_version},
            payload_after={"status": target_status, "version": topup.version}
        )

        # 6. 提交事务
        try:
            db.commit()
            db.refresh(topup)
            return topup
        except Exception as e:
            db.rollback()
            raise
```

#### 17.3.2 基于 updated_at 的实现

```python
def transition_status_by_timestamp(
    self,
    topup_id: int,
    target_status: str,
    expected_updated_at: datetime,  # 客户端传入的时间戳
    operator: AuthenticatedUser,
    db: Session
) -> TopupRequest:
    topup = db.query(TopupRequest).filter(
        TopupRequest.id == topup_id
    ).with_for_update().first()

    if not topup:
        raise ResourceNotFoundError(...)

    # 时间戳精度校验（允许 1 秒误差）
    time_diff = abs((topup.updated_at - expected_updated_at).total_seconds())
    if time_diff > 1.0:
        raise ConcurrencyConflictError(
            "数据已被其他用户修改",
            error_code="STATE_409",
            details={
                "current_updated_at": topup.updated_at.isoformat(),
                "expected_updated_at": expected_updated_at.isoformat()
            }
        )

    # 后续逻辑同上...
```

### 17.4 API 层实现模式

```python
# backend/routers/topup.py

from pydantic import BaseModel

class TopupTransitionRequest(BaseModel):
    target_status: str
    version: int  # 客户端必须提供当前版本号
    reason: Optional[str] = None

@router.put("/topup-requests/{topup_id}/transition")
async def transition_topup_status(
    topup_id: int,
    request: TopupTransitionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: TopupService = Depends()
):
    try:
        topup = service.transition_status(
            topup_id=topup_id,
            target_status=request.target_status,
            expected_version=request.version,  # 传递版本号
            operator=current_user
        )

        return success_response(data={
            "id": topup.id,
            "status": topup.status,
            "version": topup.version,  # 返回新版本号
            "updated_at": topup.updated_at
        })

    except ConcurrencyConflictError as e:
        return error_response(
            code="STATE_409",
            message=str(e),
            status_code=409,
            details=e.details
        )

    except ForbiddenTransitionError as e:
        return error_response(
            code="STATE_400",
            message=str(e),
            status_code=400
        )
```

### 17.5 前端处理规范

```typescript
// frontend/src/services/topupService.ts

interface TopupTransitionRequest {
  target_status: string;
  version: number;  // 必须从列表/详情接口获取
  reason?: string;
}

async function transitionTopupStatus(
  topupId: number,
  request: TopupTransitionRequest
): Promise<TopupResponse> {
  try {
    const response = await api.put(
      `/topup-requests/${topupId}/transition`,
      request
    );
    return response.data;

  } catch (error) {
    if (error.response?.status === 409) {
      // 并发冲突处理
      const conflictDetails = error.response.data.details;

      // 提示用户刷新数据
      alert(
        `数据已被其他用户修改，请刷新页面后重试。\n` +
        `当前状态：${conflictDetails.current_status}\n` +
        `当前版本：${conflictDetails.current_version}`
      );

      // 自动刷新数据
      await fetchTopupDetails(topupId);

    } else {
      throw error;
    }
  }
}
```

### 17.6 并发冲突错误码

| 错误码 | 说明 | HTTP | 触发条件 | 客户端处理 |
|--------|------|------|---------|-----------|
| `STATE_409` | 并发冲突 | 409 | version 不匹配 | 提示用户刷新数据 |
| `STATE_410` | 数据已删除 | 410 | 记录不存在 | 提示用户数据已删除 |
| `STATE_400` | 非法流转 | 400 | 状态已变更，不允许当前流转 | 提示用户操作失败 |

### 17.7 并发冲突测试用例

```python
# backend/tests/test_concurrency.py

import pytest
from concurrent.futures import ThreadPoolExecutor

def test_concurrent_status_transition_conflict():
    """测试并发状态流转冲突"""
    # 1. 创建充值申请
    topup = create_topup_request(status="pending_review", version=1)

    # 2. 模拟两个用户同时审批
    def user_a_approve():
        return service.transition_status(
            topup_id=topup.id,
            target_status="finance_approve",
            expected_version=1,  # 使用相同版本号
            operator=user_a
        )

    def user_b_approve():
        return service.transition_status(
            topup_id=topup.id,
            target_status="finance_approve",
            expected_version=1,  # 使用相同版本号
            operator=user_b
        )

    # 3. 并发执行
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(user_a_approve)
        future_b = executor.submit(user_b_approve)

        results = []
        for future in [future_a, future_b]:
            try:
                result = future.result()
                results.append(("success", result))
            except ConcurrencyConflictError as e:
                results.append(("conflict", e))

    # 4. 验证结果：仅一个成功，另一个冲突
    successes = [r for r in results if r[0] == "success"]
    conflicts = [r for r in results if r[0] == "conflict"]

    assert len(successes) == 1, "应该仅有一个操作成功"
    assert len(conflicts) == 1, "应该有一个操作触发冲突"
    assert conflicts[0][1].error_code == "STATE_409"

    # 5. 验证数据库状态
    refreshed_topup = get_topup_request(topup.id)
    assert refreshed_topup.status == "finance_approve"
    assert refreshed_topup.version == 2  # 版本号递增
```

---

## 18. 【P0 增强】状态机测试用例规范

### 18.1 测试用例分类

所有状态机必须覆盖以下 5 类测试：

1. **正向流转测试**：验证合法的状态流转路径
2. **非法流转测试**：验证非法流转被正确阻止
3. **终态回退测试**：验证终态回退的权限和审计
4. **System 流转测试**：验证 system 自动流转的规则
5. **并发冲突测试**：验证 Optimistic Locking 机制

### 18.2 正向流转测试

**目标**：验证白名单中的所有合法流转路径。

#### 18.2.1 项目状态机正向测试

```python
# backend/tests/test_project_state_machine.py

import pytest
from backend.services.project_service import ProjectService

class TestProjectStateMachine:
    """项目状态机测试"""

    def test_project_lifecycle_happy_path(
        self,
        db_session,
        admin_user,
        account_manager_user
    ):
        """测试项目完整生命周期（正向路径）"""
        service = ProjectService(db_session)

        # 1. 创建项目（初始状态：draft）
        project = service.create_project(
            name="Test Project",
            operator=account_manager_user
        )
        assert project.status == "draft"
        assert project.version == 1

        # 2. draft → active
        project = service.transition_status(
            project_id=project.id,
            target_status="active",
            expected_version=1,
            operator=account_manager_user
        )
        assert project.status == "active"
        assert project.version == 2

        # 3. active → suspended
        project = service.transition_status(
            project_id=project.id,
            target_status="suspended",
            expected_version=2,
            operator=admin_user
        )
        assert project.status == "suspended"
        assert project.version == 3

        # 4. suspended → active（恢复）
        project = service.transition_status(
            project_id=project.id,
            target_status="active",
            expected_version=3,
            operator=admin_user
        )
        assert project.status == "active"
        assert project.version == 4

        # 5. active → archived（终态）
        project = service.transition_status(
            project_id=project.id,
            target_status="archived",
            expected_version=4,
            operator=admin_user
        )
        assert project.status == "archived"
        assert project.version == 5

#### 18.2.2 充值申请状态机正向测试

```python
def test_topup_approval_workflow_happy_path(
    self,
    db_session,
    media_buyer_user,
    data_operator_user,
    finance_user
):
    """测试充值审批完整流程（正向路径）"""
    service = TopupService(db_session)

    # 1. 创建充值申请（draft）
    topup = service.create_topup_request(
        project_id=1,
        amount=Decimal("1000.00"),
        operator=media_buyer_user
    )
    assert topup.status == "draft"

    # 2. draft → pending_review（提交）
    topup = service.submit_topup_request(
        topup_id=topup.id,
        expected_version=topup.version,
        operator=media_buyer_user
    )
    assert topup.status == "pending_review"

    # 3. pending_review → finance_approve（数据复核）
    topup = service.review_topup_request(
        topup_id=topup.id,
        approved=True,
        expected_version=topup.version,
        operator=data_operator_user
    )
    assert topup.status == "finance_approve"

    # 4. finance_approve → paid（财务确认支付）
    topup = service.mark_topup_paid(
        topup_id=topup.id,
        expected_version=topup.version,
        operator=finance_user,
        payment_reference="PAY123456"
    )
    assert topup.status == "paid"

    # 5. paid → completed（入账确认）
    topup = service.complete_topup_request(
        topup_id=topup.id,
        expected_version=topup.version,
        operator=finance_user
    )
    assert topup.status == "completed"
```

### 18.3 非法流转测试

**目标**：验证不在白名单中的流转被正确拒绝，返回 STATE_400 错误码。

```python
def test_forbidden_transitions_blocked(
    self,
    db_session,
    media_buyer_user
):
    """测试非法流转被阻止"""
    service = TopupService(db_session)

    topup = service.create_topup_request(
        project_id=1,
        amount=Decimal("1000.00"),
        operator=media_buyer_user
    )

    # 测试 1：跳过审批（draft → completed）
    with pytest.raises(ForbiddenTransitionError) as exc_info:
        service.transition_status(
            topup_id=topup.id,
            target_status="completed",  # 非法：跳过审批
            expected_version=topup.version,
            operator=media_buyer_user
        )

    assert exc_info.value.error_code == "STATE_400"
    assert "非法流转" in str(exc_info.value)

    # 测试 2：跳过 pending_review（draft → finance_approve）
    with pytest.raises(ForbiddenTransitionError) as exc_info:
        service.transition_status(
            topup_id=topup.id,
            target_status="finance_approve",  # 非法
            expected_version=topup.version,
            operator=media_buyer_user
        )

    assert exc_info.value.error_code == "STATE_400"

    # 测试 3：终态非法流转（completed → draft）
    topup = complete_topup_workflow(topup)  # 执行到 completed
    assert topup.status == "completed"

    with pytest.raises(ForbiddenTransitionError) as exc_info:
        service.transition_status(
            topup_id=topup.id,
            target_status="draft",  # 非法：终态回退
            expected_version=topup.version,
            operator=media_buyer_user  # 非 admin
        )

    assert exc_info.value.error_code == "STATE_402"  # 终态回退权限不足
```

### 18.4 终态回退测试

**目标**：验证终态回退的权限控制和审计记录。

```python
def test_final_state_rollback_requires_admin(
    self,
    db_session,
    admin_user,
    media_buyer_user
):
    """测试终态回退权限控制"""
    service = DailyReportService(db_session)

    # 1. 创建并审批通过一份日报（终态：approved）
    report = create_and_approve_daily_report(db_session)
    assert report.status == "approved"

    # 2. 非 admin 尝试回退（应失败）
    with pytest.raises(PermissionDeniedError) as exc_info:
        service.rollback_from_final_state(
            report_id=report.id,
            target_status="draft",
            reason="需要修改数据",
            operator=media_buyer_user  # 非 admin
        )

    assert exc_info.value.error_code == "STATE_403"

    # 3. admin 回退（应成功）
    report = service.rollback_from_final_state(
        report_id=report.id,
        target_status="draft",
        reason="财务要求重新核对曝光数据，原因：数据异常",  # ≥10字符
        operator=admin_user
    )

    assert report.status == "draft"

    # 4. 验证审计日志
    audit_logs = db_session.query(AuditLog).filter(
        AuditLog.module == "daily_reports",
        AuditLog.entity_id == str(report.id),
        AuditLog.action == "rollback_from_final_state"
    ).all()

    assert len(audit_logs) == 1
    log = audit_logs[0]
    assert log.performed_by == admin_user.id
    assert log.role == "admin"
    assert log.reason is not None
    assert len(log.reason) >= 10
    assert log.payload_before["status"] == "approved"
    assert log.payload_after["status"] == "draft"
```

### 18.5 System 流转测试

**目标**：验证 system 自动流转的规则和审计记录。

```python
def test_system_auto_complete_topup_request(
    self,
    db_session
):
    """测试 system 自动完成充值（paid → completed）"""
    service = TopupService(db_session)

    # 1. 创建已支付的充值申请
    topup = create_topup_request(status="paid", db_session=db_session)

    # 2. 模拟支付回调（system 触发）
    topup = service.auto_complete_topup(
        topup_id=topup.id,
        trigger_source="payment_callback_alipay",
        payment_transaction_id="TXN123456"
    )

    assert topup.status == "completed"

    # 3. 验证审计日志
    audit_logs = db_session.query(AuditLog).filter(
        AuditLog.module == "topup_requests",
        AuditLog.entity_id == str(topup.id),
        AuditLog.action == "auto_complete"
    ).all()

    assert len(audit_logs) == 1
    log = audit_logs[0]
    assert log.performed_by is None  # system 操作
    assert log.role == "system"
    assert log.trigger_source == "payment_callback_alipay"
    assert log.payload_before["status"] == "paid"
    assert log.payload_after["status"] == "completed"


def test_system_forbidden_transitions_blocked(
    self,
    db_session
):
    """测试 system 禁止执行的流转被阻止"""
    service = TopupService(db_session)

    topup = create_topup_request(status="pending_review", db_session=db_session)

    # system 尝试审批（禁止）
    with pytest.raises(SystemPermissionDeniedError) as exc_info:
        service.auto_approve_topup(  # 假设有此方法
            topup_id=topup.id,
            trigger_source="cron_job"
        )

    assert exc_info.value.error_code == "STATE_403"
    assert "system 无权限" in str(exc_info.value).lower()
```

### 18.6 并发冲突测试

**目标**：验证 Optimistic Locking 机制的有效性。

```python
def test_concurrent_status_transition_conflict(
    self,
    db_session,
    data_operator_user_a,
    data_operator_user_b
):
    """测试并发状态流转冲突"""
    from concurrent.futures import ThreadPoolExecutor

    service = DailyReportService(db_session)

    # 1. 创建待审核日报
    report = create_daily_report(status="pending", db_session=db_session)
    initial_version = report.version

    # 2. 模拟两个用户同时审批
    def user_a_approve():
        return service.approve_daily_report(
            report_id=report.id,
            expected_version=initial_version,
            operator=data_operator_user_a
        )

    def user_b_approve():
        import time
        time.sleep(0.01)  # 稍微延迟，确保 A 先执行
        return service.approve_daily_report(
            report_id=report.id,
            expected_version=initial_version,  # 使用相同版本号
            operator=data_operator_user_b
        )

    # 3. 并发执行
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(user_a_approve)
        future_b = executor.submit(user_b_approve)

        results = []
        for future in [future_a, future_b]:
            try:
                result = future.result()
                results.append(("success", result))
            except ConcurrencyConflictError as e:
                results.append(("conflict", e))

    # 4. 验证结果
    successes = [r for r in results if r[0] == "success"]
    conflicts = [r for r in results if r[0] == "conflict"]

    assert len(successes) == 1, "应该仅有一个操作成功"
    assert len(conflicts) == 1, "应该有一个操作触发冲突"

    conflict_error = conflicts[0][1]
    assert conflict_error.error_code == "STATE_409"
    assert conflict_error.details["expected_version"] == initial_version
    assert conflict_error.details["current_version"] == initial_version + 1

    # 5. 验证数据库最终状态
    refreshed_report = db_session.query(DailyReport).get(report.id)
    assert refreshed_report.status == "approved"
    assert refreshed_report.version == initial_version + 1
```

### 18.7 测试用例结构模板

```python
# backend/tests/test_{module}_state_machine.py

import pytest
from backend.services.{module}_service import {Module}Service
from backend.exceptions import (
    ForbiddenTransitionError,
    PermissionDeniedError,
    ConcurrencyConflictError,
    SystemPermissionDeniedError
)

@pytest.mark.state_machine
class Test{Module}StateMachine:
    """
    {Module} 状态机测试套件

    覆盖范围：
    - 正向流转测试（所有合法路径）
    - 非法流转测试（白名单外的流转）
    - 终态回退测试（权限和审计）
    - System 流转测试（自动流转规则）
    - 并发冲突测试（Optimistic Locking）
    """

    # ========== Fixtures ==========

    @pytest.fixture
    def service(self, db_session):
        return {Module}Service(db_session)

    @pytest.fixture
    def sample_{module}(self, db_session, media_buyer_user):
        """创建测试用的{module}实例"""
        return create_{module}(
            db_session=db_session,
            operator=media_buyer_user
        )

    # ========== 正向流转测试 ==========

    def test_happy_path_workflow(self, service, ...):
        """测试完整的正向流转路径"""
        pass

    def test_alternative_path_workflow(self, service, ...):
        """测试备选的正向流转路径（如拒绝后重新提交）"""
        pass

    # ========== 非法流转测试 ==========

    @pytest.mark.parametrize("from_status,to_status", [
        ("draft", "completed"),  # 跳过审批
        ("draft", "rejected"),   # 跳过提交
        ("approved", "pending"), # 终态回退（非admin）
    ])
    def test_forbidden_transitions(
        self,
        service,
        sample_{module},
        from_status,
        to_status
    ):
        """测试非法流转被阻止"""
        pass

    # ========== 终态回退测试 ==========

    def test_final_state_rollback_requires_admin(self, service, ...):
        """测试终态回退权限控制"""
        pass

    def test_final_state_rollback_requires_reason(self, service, ...):
        """测试终态回退必须提供理由"""
        pass

    def test_final_state_rollback_audit_log(self, service, ...):
        """测试终态回退的审计日志"""
        pass

    # ========== System 流转测试 ==========

    def test_system_auto_transition(self, service, ...):
        """测试 system 允许的自动流转"""
        pass

    def test_system_forbidden_transition(self, service, ...):
        """测试 system 禁止的流转被阻止"""
        pass

    # ========== 并发冲突测试 ==========

    def test_concurrent_transition_conflict(self, service, ...):
        """测试并发状态流转冲突"""
        pass

    def test_concurrent_update_conflict(self, service, ...):
        """测试并发数据更新冲突"""
        pass
```

### 18.8 测试覆盖率要求

| 测试类型 | 覆盖率要求 | 说明 |
|---------|-----------|------|
| **正向流转测试** | 100% | 所有白名单中的流转路径必须测试 |
| **非法流转测试** | ≥ 80% | 覆盖典型的非法流转场景 |
| **终态回退测试** | 100% | 所有终态的回退规则必须测试 |
| **System 流转测试** | 100% | 所有 system 自动流转必须测试 |
| **并发冲突测试** | ≥ 50% | 覆盖关键的并发场景 |

### 18.9 测试执行命令

```bash
# 运行所有状态机测试
pytest -m state_machine

# 运行特定模块的状态机测试
pytest backend/tests/test_topup_state_machine.py -v

# 运行并发测试（需要多线程）
pytest -m state_machine -k "concurrent" --workers=4

# 生成覆盖率报告
pytest -m state_machine --cov=backend/services --cov-report=html
```

---

## 19. Planned 扩展（当前版本禁止实现，AI 不得据此生成代码）

> 以下为规划状态/自动化，当前禁止在代码、CHECK、接口中实现。需启用时先更新本文件与 DATA_SCHEMA。

- 项目：`reviewing`（项目审批）
- 账户：`warming`（养号）
- 充值：`partial_paid`（部分支付）
- 对账批次：`archived` 终态
- 对账：`disputed`（争议）
- 自动化：账户养护 `new`→`warming`→`testing`；异常预警自动暂停；AI 智能对账标记 `reviewing`

**【v2.5 补充说明】**：
- Planned 状态的实施必须遵循 14.5 章节的白名单更新流程
- 任何 Planned 状态的启用必须先完成：本文档更新 → DATA_SCHEMA 更新 → CHECK 约束更新（第 15 章）→ 代码白名单更新 → 测试覆盖
- 禁止在当前版本中使用 Planned 状态，违规将触发 STATE_404 错误

---

## 20. 变更流程与兼容

1. 增删状态或调整流转：先改本文件，再改 DATA_SCHEMA CHECK、模型枚举、API 校验。
2. Legacy 映射：
   - 旧角色：`manager` → `account_manager`，`data_clerk` → `data_operator`。
   - 旧充值状态：`pending` → `pending_review`；`posted` → `completed`。
3. 所有变更需审计记录与评审通过后发布。

---

## 21. 开发/改状态前自检 Checklist

- [ ] 本文件中已有对应状态字段的章节与枚举，未自行添加新状态。
- [ ] DATA_SCHEMA 的 CHECK/模型枚举/前后端常量均从本文件复制。
- [ ] 新增/修改状态前，同步计划：本文件 + DATA_SCHEMA + 代码 + 迁移 + 测试。
- [ ] 已区分当前实现与 Planned，未在代码中使用 Planned 状态。
- [ ] 未在代码中直接 UPDATE status，所有变更通过业务动作并记录审计。
- [ ] 提交者与审批者分离，终态回退仅 admin 且需审计。
- [ ] 若涉及 system 自动流转，已限定在回调/定时等自动任务，不替代人工审批。
- [ ] **【v2.4 新增】** 若新增 system 自动流转，已在 14.1 章节登记并说明触发来源。
- [ ] **【v2.4 新增】** 若涉及终态回退，已遵循 14.2 章节的权限和审计要求。
- [ ] **【v2.4 新增】** 若涉及充值金额修改，已遵循 14.3 章节的锁定规则。
- [ ] **【v2.4 新增】** 若涉及对账批次关闭，已检查 14.4 章节的前置条件。
- [ ] **【v2.4 新增】** 所有状态流转已在 14.5 章节的白名单中登记。
- [ ] **【v2.5 新增】** 所有状态字段已添加 CHECK 约束（第 15 章模板）。
- [ ] **【v2.5 新增】** 所有状态变更 API 已在第 16 章映射表中登记。
- [ ] **【v2.5 新增】** 涉及状态流转的表已添加 version 字段（第 17 章）。
- [ ] **【v2.5 新增】** 所有状态机已编写测试用例（第 18 章规范）。

---

## 22. 版本历史

| 版本 | 日期 | 主要变更 |
| --- | --- | --- |
| **v2.6** | **2025‑01‑21** | **【BRD v3.1 对齐】粉数确认状态机重大更新**：<br>**第4章 全局状态一览表**：daily_reports.status更新为8状态粉数确认状态机(raw_submitted/trend_pending/trend_ok/trend_flagged/trend_resolved/final_pending/final_confirmed/final_locked)<br>**第8章 完全重写**：替换旧日报状态机为"粉数确认状态机(6状态流程)",新增8个小节(状态枚举/流转规则/趋势风控规则TF-001/002/003/三数据流字段定义/业务约束/角色权限/API端点映射/红冲修正机制/CHECK约束/审计日志要求)<br>**第13章 权限视角提示**：新增6个日报相关操作(提交raw粉数/趋势风控检查/复核/录入real_spend/确认final/计费锁定)<br>**第14.5章 白名单机制**：更新daily_reports.status流转白名单为8状态流转<br>**第15.2.2章 CHECK约束**：更新为8状态CHECK约束,默认值改为raw_submitted<br>**第16.3章 API映射表**：更新为7个粉数确认流程API端点(trend-check/trend-resolve/update-real-spend/final-confirm/final-lock/reversal)<br>**对齐依据**：MASTER_SPEC v2.2 第2.3.1节 + BRD v3.1第4章粉数确认状态机 |
| **v2.5** | **2025‑01‑19** | **【P0 增强版】新增 4 个关键章节**：<br>**15. 数据库 CHECK 约束同步清单**：10 个状态字段的 CHECK 模板、ENUM vs TEXT 规范、与 DATA_SCHEMA 同步流程、约束变更迁移示例<br>**16. API → 状态流转映射表**：10 个模块、50+ API 端点的完整映射（当前状态、目标状态、角色、审计、错误码）<br>**17. 并发冲突处理规范**：Optimistic Locking 实施方案（version 字段 vs updated_at）、Service/API/前端实现模式、STATE_409 错误码<br>**18. 状态机测试用例规范**：5 类测试（正向/非法/终态/System/并发）、测试模板、覆盖率要求<br>**文档定位升级**：可直接作为后端实现与测试的唯一事实来源 |
| **v2.4** | **2025‑01‑19** | **【P0 上线前补充】新增 5 个关键章节**：<br>14.1 System 自动状态流转规则（白名单、黑名单、审计要求）<br>14.2 终态回退规则（权限、禁止场景、错误码）<br>14.3 充值金额锁定规则（锁定时机、修改权限矩阵、Admin 强制修改）<br>14.4 对账批次关闭条件（前置条件、强制关闭机制）<br>14.5 禁止流转机制（白名单机制、非法流转处理、监控报告）<br>所有新增内容均可直接驱动后端开发，无模糊描述。 |
| v2.3 | 2025‑11‑17 | 新增全局状态一览表；补全各模块合法取值；新增自检 Checklist；强化 SoT 边界与 Planned 分层。 |
| v2.2 | 2025‑11‑17 | 对齐实现/数据 SoT：日报仅 data_operator 审核；充值状态收敛为 7 个；批次 `archived` 标记 planned；新增 system 虚拟操作者说明；规划集中到 Planned 章节。 |
| v2.1 | 2025‑11‑17 | 补齐渠道评审/账户预警等状态机，标注自动化实现状态。 |
| v2.0 | 2025‑11‑17 | 对齐 MASTER_SPEC v3.0 与 DATA_SCHEMA v5.0，统一角色与状态枚举。 |

---

**注意**：本文件为状态和值的唯一事实来源。任何状态定义、流转规则、权限要求的修改，必须先更新本文件，再同步其它 SoT 与代码、迁移。
