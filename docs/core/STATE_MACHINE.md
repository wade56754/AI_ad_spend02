# AI广告代投系统 - 状态机定义文档（SoT-State）

> **版本**: v2.3  
> **更新日期**: 2025‑11‑17  
> **类型**: 状态与合法流转的唯一事实来源（SoT-State）  
> **互锁文档**  
> - 实现规范 → `docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md`  
> - 数据结构 → `docs/core/DATA_SCHEMA.md`（CHECK/枚举必须完全复制本文件，不得自创）  
> - API 流程 → `docs/core/API_DEVELOPMENT_FLOW.md`  
> - 角色定义 → 仅 `admin/finance/data_operator/account_manager/media_buyer`（无其他角色）

---

## 1. 定位与优先级

- 本文件定义所有状态枚举与合法流转，**其他文档如有冲突，以本文件为准**。  
- `DATA_SCHEMA` 中的 CHECK 约束、枚举类、前后端常量必须从本文件同步；禁止自行扩展或裁剪状态集合。  
- 业务流程、权限细节以实现规范为准；本文件中的权限描述仅用于约束状态流转。  
- 规划内容统一放在《Planned 扩展》章节，当前版本禁止实现。

---

## 2. 角色与操作者

- 合法业务角色：`admin`, `finance`, `data_operator`, `account_manager`, `media_buyer`。  
- **system（虚拟操作者）**：用于定时任务/事件驱动的自动流转，不参与 RBAC，仅可出现在审计日志（`operator_role = 'system'`）。业务授权只看 5 个合法角色。  
- 审批分离：提交者不能审批自身请求；终态回退仅 `admin`（需审计理由）。

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
| daily_reports.status | draft, pending, approved, rejected | approved/rejected | 日报 |
| topup_requests.status | draft, pending_review, finance_approve, paid, completed, rejected, cancelled | completed/rejected/cancelled | 充值 |
| reconciliation_batches.status | draft, pending, reviewing, closed | closed | `archived` 为 planned |
| reconciliation_details.status | pending, confirmed, adjusted | confirmed/adjusted | 对账明细 |
| ledger_entries | 无状态 | - | 资金总账 |
| ad_spend_daily | 无状态 | - | 导入数据 |

> Planned/历史状态见第 15 章，不得在当前实现使用。

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

## 8. 日报状态机（daily_reports.status）

合法取值：`draft`, `pending`, `approved`, `rejected`（终态：approved/rejected）  
- 提交：media_buyer（自动 draft→pending）  
- 审核：仅 data_operator（admin 兜底）  
- 回退：终态→draft 仅 admin，[AUDIT]

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
当前合法取值：`draft`, `pending`, `reviewing`, `closed`（终态：closed）  
- `archived` 为 planned，当前禁止使用。  
- 创建：finance/data_operator  
- 审核/关闭：finance/admin，[AUDIT]

### 11.2 对账明细（reconciliation_details.status）  
合法取值：`pending`, `confirmed`, `adjusted`（终态：confirmed/adjusted）  
- 调整：finance/data_operator，[AUDIT]  
- 终态回退：仅 admin，[AUDIT]

### 11.3 调整/报告  
无独立状态机，依附批次/明细状态。

---

## 12. 总账（ledger_entries）

无状态机；按业务类型写入，审计由 `audit_logs` 负责。

---

## 13. 权限视角提示（非仲裁）

- 本表仅为状态流转视角的快速参考；**真正的权限规则以 AI_AD_SYSTEM_MAIN_DOCUMENT 为准**。  
- 若冲突，以实现规范为准，并需同步更新本文件。

| 模块 | 关键动作 | 允许角色 |
| --- | --- | --- |
| 日报提交 | draft→pending | media_buyer |
| 日报审核 | pending→approved/rejected | data_operator（admin 兜底） |
| 充值提交 | draft→pending_review | media_buyer/account_manager |
| 充值复核 | pending_review→finance_approve/rejected | data_operator |
| 充值终审/支付 | finance_approve→paid | finance |
| 充值完成 | paid→completed | finance/system |
| 对账批次关闭 | reviewing→closed | finance/admin |
| 项目激活/归档 | draft/active/suspended 变更 | account_manager/admin |

---

## 14. 审计与系统操作者

- [AUDIT] 变化必须写入 `audit_logs`：包含操作者（可为 system）、旧/新状态、时间、理由。  
- system 流转仅限自动任务（如支付回调、定时结算），不得替代人工审批。  
- 提交者与审批者必须不同；终态解封由 admin 且需要理由。

---

## 15. Planned 扩展（当前版本禁止实现，AI 不得据此生成代码）

> 以下为规划状态/自动化，当前禁止在代码、CHECK、接口中实现。需启用时先更新本文件与 DATA_SCHEMA。

- 项目：`reviewing`（项目审批）  
- 账户：`warming`（养号）  
- 充值：`partial_paid`（部分支付）  
- 对账批次：`archived` 终态  
- 对账：`disputed`（争议）  
- 自动化：账户养护 `new`→`warming`→`testing`；异常预警自动暂停；AI 智能对账标记 `reviewing`

---

## 16. 变更流程与兼容

1. 增删状态或调整流转：先改本文件，再改 DATA_SCHEMA CHECK、模型枚举、API 校验。  
2. Legacy 映射：  
   - 旧角色：`manager` → `account_manager`，`data_clerk` → `data_operator`。  
   - 旧充值状态：`pending` → `pending_review`；`posted` → `completed`。  
3. 所有变更需审计记录与评审通过后发布。

---

## 17. 开发/改状态前自检 Checklist

- [ ] 本文件中已有对应状态字段的章节与枚举，未自行添加新状态。  
- [ ] DATA_SCHEMA 的 CHECK/模型枚举/前后端常量均从本文件复制。  
- [ ] 新增/修改状态前，同步计划：本文件 + DATA_SCHEMA + 代码 + 迁移 + 测试。  
- [ ] 已区分当前实现与 Planned，未在代码中使用 Planned 状态。  
- [ ] 未在代码中直接 UPDATE status，所有变更通过业务动作并记录审计。  
- [ ] 提交者与审批者分离，终态回退仅 admin 且需审计。  
- [ ] 若涉及 system 自动流转，已限定在回调/定时等自动任务，不替代人工审批。

---

## 18. 版本历史

| 版本 | 日期 | 主要变更 |
| --- | --- | --- |
| v2.3 | 2025‑11‑17 | 新增全局状态一览表；补全各模块合法取值；新增自检 Checklist；强化 SoT 边界与 Planned 分层。 |
| v2.2 | 2025‑11‑17 | 对齐实现/数据 SoT：日报仅 data_operator 审核；充值状态收敛为 7 个；批次 `archived` 标记 planned；新增 system 虚拟操作者说明；规划集中到 Planned 章节。 |
| v2.1 | 2025‑11‑17 | 补齐渠道评审/账户预警等状态机，标注自动化实现状态。 |
| v2.0 | 2025‑11‑17 | 对齐 AI_AD_SYSTEM_MAIN_DOCUMENT v3.0 与 DATA_SCHEMA v5.0，统一角色与状态枚举。 |

---

**注意**：本文件为状态和值的唯一事实来源。任何状态定义、流转规则、权限要求的修改，必须先更新本文件，再同步其它 SoT 与代码、迁移。
