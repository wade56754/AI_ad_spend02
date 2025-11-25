# AI 广告代投系统 - 数据库不变量测试用例文档

> **文档版本**: v2.0
> **文档性质**: SoT 级测试规范
> **基于**: DATA_SCHEMA.md v5.2, MASTER.md v3.4, STATE_MACHINE.md v2.6, LEDGER_SOT.md v1.1, PATTERNS.md v1.0
> **对应脚本**: `db_invariants_test_v2.sql`
> **创建日期**: 2025-11-25
> **更新日期**: 2025-11-25

---

## 1. 测试范围

### 1.1 测试目标

本测试套件验证数据库层面的所有业务不变量 (Invariants) 和约束条件：

- **数据完整性**: 所有外键、唯一约束、CHECK 约束正确生效
- **业务规则**: 双账本隔离、账本不可变性、余额只读等核心规则
- **状态机一致性**: 所有状态枚举值与 STATE_MACHINE.md v2.6 定义一致
- **流程正确性**: 充值流程、日报流程、死号迁移流程、对账流程

### 1.2 覆盖模块

| 模块 | 优先级 | 测试表 | 用例数 |
|------|--------|--------|--------|
| 账本系统 | P0 | `ledger_entries` | 8 |
| 供应商余额 | P0 | `suppliers` | 2 |
| 日报状态机 | P0 | `daily_reports` | 3 |
| 用户角色 | P1 | `users`, `project_members` | 2 |
| 充值流程 | P1 | `topup_requests`, `topup_transactions` | 2 |
| 广告账户 | P1 | `ad_accounts`, `account_alerts` | 2 |
| 死号迁移 | P1 | `transfer_requests` | 2 |
| 对账模块 | P2 | `reconciliation_*` | 2 |
| 视图验证 | P2 | `v_project_balance`, `v_supplier_balance` | 3 |

---

## 2. 测试方法

### 2.1 测试策略

- **约束测试**: 验证 CHECK/UNIQUE/FK 约束
- **触发器测试**: 验证 UPDATE/DELETE 保护触发器
- **流程测试**: 验证完整业务流程的状态流转与数据一致性
- **负面测试**: 验证非法操作被正确拒绝

### 2.2 测试环境

- **数据库**: PostgreSQL 14+ / Supabase
- **执行方式**: 通过 `psql` 或 Supabase SQL Editor 执行
- **隔离策略**: 所有测试数据使用特定前缀，测试后自动清理

### 2.3 测试约定

> **重要**: 本测试套件为**顺序执行的单文件测试套件**，测试用例之间存在依赖关系。

- 测试用户 UUID 使用 `00000000-0000-0000-0000-00000000****` 格式
- 测试数据使用 `_test_` 前缀便于识别和清理
- 预期失败的测试使用 `EXCEPTION` 捕获验证
- 清理阶段使用 `BEGIN...EXCEPTION...END` 确保触发器恢复

---

## 3. P0 测试用例 (核心不变量)

### 3.1 账本不可变性测试

#### TC-LED-001: 禁止 UPDATE ledger_entries

| 项目 | 内容 |
|------|------|
| **编号** | TC-LED-001 |
| **目标** | 验证 ledger_entries 表禁止 UPDATE 操作 |
| **SoT 依据** | MASTER.md INV-001, PATTERNS.md AP-LED-001 |
| **前置条件** | ledger_entries 存在有效记录 |
| **步骤** | 1. 插入一条合法 PROJECT 账本记录<br>2. 尝试 UPDATE 该记录的 amount 字段 |
| **预期结果** | 抛出异常: `LEDGER_IMMUTABLE: ledger_entries 禁止 UPDATE/DELETE 操作` |
| **SQL 对应** | Section 2: TC-LED-001 |

#### TC-LED-002: 禁止 DELETE ledger_entries

| 项目 | 内容 |
|------|------|
| **编号** | TC-LED-002 |
| **目标** | 验证 ledger_entries 表禁止 DELETE 操作 |
| **SoT 依据** | MASTER.md INV-001, PATTERNS.md AP-LED-001 |
| **前置条件** | ledger_entries 存在有效记录 |
| **步骤** | 1. 插入一条合法 PROJECT 账本记录<br>2. 尝试 DELETE 该记录 |
| **预期结果** | 抛出异常: `LEDGER_IMMUTABLE: ledger_entries 禁止 UPDATE/DELETE 操作` |
| **SQL 对应** | Section 2: TC-LED-002 |

### 3.2 双账本隔离测试

#### TC-LED-003: PROJECT 账本必须关联 project_id

| 项目 | 内容 |
|------|------|
| **编号** | TC-LED-003 |
| **目标** | 验证 PROJECT 类型账本必须填写 project_id |
| **SoT 依据** | MASTER.md INV-001, DATA_SCHEMA.md §3.4.4 |
| **前置条件** | projects 表存在有效项目 |
| **步骤** | 1. 尝试插入 ledger_type='PROJECT' 且 project_id=NULL 的记录 |
| **预期结果** | 违反 CHECK 约束 `chk_ledger_type_entity` |
| **SQL 对应** | Section 3: TC-LED-003 |

#### TC-LED-004: PROJECT 账本禁止关联 supplier_id

| 项目 | 内容 |
|------|------|
| **编号** | TC-LED-004 |
| **目标** | 验证 PROJECT 类型账本 supplier_id 必须为空 |
| **SoT 依据** | MASTER.md INV-001 "双账本隔离" |
| **前置条件** | projects 和 suppliers 表存在有效记录 |
| **步骤** | 1. 尝试插入 ledger_type='PROJECT' 且同时设置 project_id 和 supplier_id 的记录 |
| **预期结果** | 违反 CHECK 约束 `chk_ledger_type_entity` |
| **SQL 对应** | Section 3: TC-LED-004 |

#### TC-LED-005: SUPPLIER 账本必须关联 supplier_id

| 项目 | 内容 |
|------|------|
| **编号** | TC-LED-005 |
| **目标** | 验证 SUPPLIER 类型账本必须填写 supplier_id |
| **SoT 依据** | MASTER.md INV-001, DATA_SCHEMA.md §3.4.4 |
| **前置条件** | suppliers 表存在有效供应商 |
| **步骤** | 1. 尝试插入 ledger_type='SUPPLIER' 且 supplier_id=NULL 的记录 |
| **预期结果** | 违反 CHECK 约束 `chk_ledger_type_entity` |
| **SQL 对应** | Section 3: TC-LED-005 |

#### TC-LED-006: SUPPLIER 账本禁止关联 project_id

| 项目 | 内容 |
|------|------|
| **编号** | TC-LED-006 |
| **目标** | 验证 SUPPLIER 类型账本 project_id 必须为空 |
| **SoT 依据** | MASTER.md INV-001 "双账本隔离" |
| **前置条件** | projects 和 suppliers 表存在有效记录 |
| **步骤** | 1. 尝试插入 ledger_type='SUPPLIER' 且同时设置 project_id 和 supplier_id 的记录 |
| **预期结果** | 违反 CHECK 约束 `chk_ledger_type_entity` |
| **SQL 对应** | Section 3: TC-LED-006 |

### 3.3 账本类型与条目类型匹配测试

#### TC-LED-007: PROJECT 账本只允许 REVENUE/TOPUP/REVERSAL

| 项目 | 内容 |
|------|------|
| **编号** | TC-LED-007 |
| **目标** | 验证 PROJECT 账本的 entry_type 限制 |
| **SoT 依据** | DATA_SCHEMA.md §3.4.4, LEDGER_SOT.md v1.1 |
| **前置条件** | projects 表存在有效项目 |
| **步骤** | 1. 尝试插入 ledger_type='PROJECT' 且 entry_type='COST' 的记录 |
| **预期结果** | 违反 CHECK 约束 `chk_ledger_entry_type_by_ledger` |
| **SQL 对应** | Section 3: TC-LED-007 |

#### TC-LED-008: SUPPLIER 账本只允许 COST/TOPUP/TRANSFER_*/REVERSAL

| 项目 | 内容 |
|------|------|
| **编号** | TC-LED-008 |
| **目标** | 验证 SUPPLIER 账本的 entry_type 限制 |
| **SoT 依据** | DATA_SCHEMA.md §3.4.4, LEDGER_SOT.md v1.1 |
| **前置条件** | suppliers 表存在有效供应商 |
| **步骤** | 1. 尝试插入 ledger_type='SUPPLIER' 且 entry_type='REVENUE' 的记录 |
| **预期结果** | 违反 CHECK 约束 `chk_ledger_entry_type_by_ledger` |
| **SQL 对应** | Section 3: TC-LED-008 |

### 3.4 供应商余额只读测试

#### TC-SUP-001: 禁止直接修改 suppliers.balance

| 项目 | 内容 |
|------|------|
| **编号** | TC-SUP-001 |
| **目标** | 验证 suppliers.balance 字段禁止直接 UPDATE |
| **SoT 依据** | PATTERNS.md AP-LED-002 |
| **前置条件** | suppliers 表存在有效供应商 |
| **步骤** | 1. 尝试 UPDATE balance 为新值 |
| **预期结果** | 抛出异常: `BALANCE_READONLY: suppliers.balance 禁止直接修改` |
| **SQL 对应** | Section 4: TC-SUP-001 |

#### TC-SUP-002: 允许修改 suppliers 其他字段

| 项目 | 内容 |
|------|------|
| **编号** | TC-SUP-002 |
| **目标** | 验证 suppliers 的非 balance 字段可正常修改 |
| **SoT 依据** | PATTERNS.md AP-LED-002 (仅保护 balance) |
| **前置条件** | suppliers 表存在有效供应商 |
| **步骤** | 1. UPDATE name 和 status 字段 |
| **预期结果** | 更新成功，balance 保持不变 |
| **SQL 对应** | Section 4: TC-SUP-002 |

### 3.5 日报唯一约束与状态机测试

#### TC-RPT-001: daily_reports 日期+账户唯一约束

| 项目 | 内容 |
|------|------|
| **编号** | TC-RPT-001 |
| **目标** | 验证同一广告账户同一日期只能有一条日报 |
| **SoT 依据** | DATA_SCHEMA.md §3.3.1 |
| **前置条件** | ad_accounts 存在有效账户 |
| **步骤** | 1. 插入 report_date='2025-01-01' 的日报<br>2. 再次插入相同日期的日报 |
| **预期结果** | 违反唯一约束 `uq_daily_reports_date_account` |
| **SQL 对应** | Section 5: TC-RPT-001 |

#### TC-RPT-002: daily_reports 8 状态枚举约束

| 项目 | 内容 |
|------|------|
| **编号** | TC-RPT-002 |
| **目标** | 验证 daily_reports.status 只接受 8 个合法状态 |
| **SoT 依据** | STATE_MACHINE.md §8 |
| **前置条件** | ad_accounts 存在有效账户 |
| **步骤** | 1. 尝试插入 status='invalid_status' 的日报 |
| **预期结果** | 违反 CHECK 约束 |
| **SQL 对应** | Section 5: TC-RPT-002 |

#### TC-RPT-003: daily_reports 合法状态值验证

| 项目 | 内容 |
|------|------|
| **编号** | TC-RPT-003 |
| **目标** | 验证所有 8 个合法状态均可插入 |
| **SoT 依据** | STATE_MACHINE.md §8 |
| **前置条件** | ad_accounts 存在有效账户 |
| **步骤** | 依次插入 8 种状态的日报: raw_submitted, trend_pending, trend_ok, trend_flagged, trend_resolved, final_pending, final_confirmed, final_locked |
| **预期结果** | 全部插入成功 |
| **SQL 对应** | Section 5: TC-RPT-003 |

---

## 4. P1 测试用例 (枚举与流程)

### 4.1 用户角色枚举测试

#### TC-USR-001: users.role 5 角色枚举约束

| 项目 | 内容 |
|------|------|
| **编号** | TC-USR-001 |
| **目标** | 验证 users.role 只接受 5 个合法角色 |
| **SoT 依据** | AUTH_SPEC.md §2.2 |
| **前置条件** | 无 |
| **步骤** | 1. 尝试插入 role='superadmin' 的用户 |
| **预期结果** | 违反 CHECK 约束 |
| **SQL 对应** | Section 6: TC-USR-001 |

#### TC-USR-002: users.role 合法值验证

| 项目 | 内容 |
|------|------|
| **编号** | TC-USR-002 |
| **目标** | 验证所有 5 个合法角色均可插入 |
| **SoT 依据** | AUTH_SPEC.md §2.2 |
| **前置条件** | 无 |
| **步骤** | 依次插入 5 种角色: admin, finance, data_operator, account_manager, media_buyer |
| **预期结果** | 全部插入成功 |
| **SQL 对应** | Section 6: TC-USR-002 |

### 4.2 充值状态枚举测试

#### TC-TOP-001: topup_requests.status 7 状态枚举约束

| 项目 | 内容 |
|------|------|
| **编号** | TC-TOP-001 |
| **目标** | 验证 topup_requests.status 只接受 7 个合法状态 |
| **SoT 依据** | STATE_MACHINE.md §9 |
| **前置条件** | projects 和 users 存在有效记录 |
| **步骤** | 1. 尝试插入 status='processing' 的充值申请 |
| **预期结果** | 违反 CHECK 约束 |
| **SQL 对应** | Section 7: TC-TOP-001 |

#### TC-TOP-002: topup_requests.status 合法值验证

| 项目 | 内容 |
|------|------|
| **编号** | TC-TOP-002 |
| **目标** | 验证所有 7 个合法状态均可插入 |
| **SoT 依据** | STATE_MACHINE.md §9 |
| **前置条件** | projects 和 users 存在有效记录 |
| **步骤** | 依次插入 7 种状态: draft, pending_review, finance_approve, paid, completed, rejected, cancelled |
| **预期结果** | 全部插入成功 |
| **SQL 对应** | Section 7: TC-TOP-002 |

### 4.3 广告账户状态枚举测试

#### TC-ACC-001: ad_accounts.status 6 状态枚举约束

| 项目 | 内容 |
|------|------|
| **编号** | TC-ACC-001 |
| **目标** | 验证 ad_accounts.status 只接受 6 个合法状态 |
| **SoT 依据** | STATE_MACHINE.md §7.1 |
| **前置条件** | projects 存在有效项目 |
| **步骤** | 1. 尝试插入 status='deleted' 的广告账户 |
| **预期结果** | 违反 CHECK 约束 |
| **SQL 对应** | Section 8: TC-ACC-001 |

#### TC-ACC-002: ad_accounts.status 合法值验证

| 项目 | 内容 |
|------|------|
| **编号** | TC-ACC-002 |
| **目标** | 验证所有 6 个合法状态均可插入 |
| **SoT 依据** | STATE_MACHINE.md §7.1 |
| **前置条件** | projects 存在有效项目 |
| **步骤** | 依次插入 6 种状态: new, testing, active, suspended, dead, archived |
| **预期结果** | 全部插入成功 |
| **SQL 对应** | Section 8: TC-ACC-002 |

### 4.4 死号迁移状态测试

#### TC-TRF-001: transfer_requests.status 5 状态枚举约束

| 项目 | 内容 |
|------|------|
| **编号** | TC-TRF-001 |
| **目标** | 验证 transfer_requests.status 只接受 5 个合法状态 |
| **SoT 依据** | STATE_MACHINE.md §12 |
| **前置条件** | ad_accounts 存在有效账户 |
| **步骤** | 1. 尝试插入 status='processing' 的迁移申请 |
| **预期结果** | 违反 CHECK 约束 |
| **SQL 对应** | Section 9: TC-TRF-001 |

#### TC-TRF-002: transfer_requests.status 合法值验证

| 项目 | 内容 |
|------|------|
| **编号** | TC-TRF-002 |
| **目标** | 验证所有 5 个合法状态均可插入 |
| **SoT 依据** | STATE_MACHINE.md §12 |
| **前置条件** | ad_accounts 存在有效账户 |
| **步骤** | 依次插入 5 种状态: draft, pending_approval, approved, rejected, completed |
| **预期结果** | 全部插入成功 |
| **SQL 对应** | Section 9: TC-TRF-002 |

---

## 5. P2 测试用例 (视图与对账)

### 5.1 项目余额视图测试

> **视图定义**: `v_project_balance` 定义于 `init_schema.sql` §10.1
> **计算公式**: `balance = COALESCE(SUM(ledger_entries.amount), 0.00) WHERE ledger_type = 'PROJECT'`
> **用途**: 实时计算项目余额，符合 MASTER.md INV-001 "余额 = SUM(entries)" 原则

#### TC-VW-001: v_project_balance 与 ledger_entries 聚合一致性

| 项目 | 内容 |
|------|------|
| **编号** | TC-VW-001 |
| **目标** | 验证 v_project_balance 视图正确聚合 PROJECT 账本金额 |
| **SoT 依据** | MASTER.md INV-001 "余额 = SUM(entries)" |
| **前置条件** | projects 存在有效项目 |
| **步骤** | 1. 插入 3 笔 PROJECT 账本记录 (100, 200, -50)<br>2. 查询 v_project_balance 视图 |
| **预期结果** | 视图返回 balance = 250 |
| **SQL 对应** | Section 10: TC-VW-001 |

#### TC-VW-002: v_project_balance 空项目返回 0

| 项目 | 内容 |
|------|------|
| **编号** | TC-VW-002 |
| **目标** | 验证无账本记录的项目余额为 0 |
| **SoT 依据** | MASTER.md INV-001 |
| **前置条件** | 无 |
| **步骤** | 1. 创建测试项目 (无任何账本记录)<br>2. 查询 v_project_balance 视图 |
| **预期结果** | 视图返回 balance = 0.00 |
| **SQL 对应** | Section 10: TC-VW-002 |

### 5.2 供应商余额视图测试

> **视图定义**: `v_supplier_balance` 定义于 `init_schema.sql` §10.2
> **计算公式**: `calculated_balance = COALESCE(SUM(ledger_entries.amount), 0.00) WHERE ledger_type = 'SUPPLIER'`
> **用途**: 验证 suppliers.balance 与账本聚合值一致性，current_balance 为表字段，calculated_balance 为聚合计算值

#### TC-VW-003: v_supplier_balance 计算值验证

| 项目 | 内容 |
|------|------|
| **编号** | TC-VW-003 |
| **目标** | 验证 v_supplier_balance 正确计算 SUPPLIER 账本聚合值 |
| **SoT 依据** | LEDGER_SOT.md v1.1 |
| **前置条件** | suppliers 存在有效供应商 |
| **步骤** | 1. 插入 SUPPLIER 账本记录<br>2. 查询 v_supplier_balance 视图 |
| **预期结果** | calculated_balance 与账本聚合值一致 |
| **SQL 对应** | Section 10: TC-VW-003 |

### 5.3 对账模块测试

#### TC-REC-001: reconciliation_batches.status 5 状态枚举约束

| 项目 | 内容 |
|------|------|
| **编号** | TC-REC-001 |
| **目标** | 验证 reconciliation_batches.status 只接受 5 个合法状态 |
| **SoT 依据** | STATE_MACHINE.md §11.1 |
| **前置条件** | projects 存在有效项目 |
| **步骤** | 1. 尝试插入 status='invalid' 的对账批次 |
| **预期结果** | 违反 CHECK 约束 |
| **SQL 对应** | Section 11: TC-REC-001 |

#### TC-REC-002: reconciliation_details.status 3 状态枚举约束

| 项目 | 内容 |
|------|------|
| **编号** | TC-REC-002 |
| **目标** | 验证 reconciliation_details.status 只接受 3 个合法状态 |
| **SoT 依据** | STATE_MACHINE.md §11.2 |
| **前置条件** | reconciliation_batches 存在有效批次 |
| **步骤** | 1. 尝试插入 status='invalid' 的对账明细 |
| **预期结果** | 违反 CHECK 约束 |
| **SQL 对应** | Section 11: TC-REC-002 |

---

## 6. 集成测试用例 (流程级)

### 6.1 充值流程测试

#### TC-FLOW-001: 完整充值流程

| 项目 | 内容 |
|------|------|
| **编号** | TC-FLOW-001 |
| **目标** | 验证充值从申请到完成的完整流程 |
| **SoT 依据** | STATE_MACHINE.md §9, LEDGER_SOT.md |
| **前置条件** | 存在有效项目、用户 |
| **步骤** | 1. 创建 topup_request (draft)<br>2. 更新状态为 pending_review<br>3. 更新状态为 finance_approve<br>4. 更新状态为 paid<br>5. 插入 ledger_entry (TOPUP)<br>6. 更新状态为 completed<br>7. 验证 v_project_balance |
| **预期结果** | 项目余额正确增加 |
| **SQL 对应** | Section 12: TC-FLOW-001 |

### 6.2 日报流程测试

#### TC-FLOW-002: 日报 8 状态流转

| 项目 | 内容 |
|------|------|
| **编号** | TC-FLOW-002 |
| **目标** | 验证日报状态从 raw_submitted 到 final_locked 的完整流转 |
| **SoT 依据** | STATE_MACHINE.md §8 |
| **前置条件** | 存在有效广告账户 |
| **步骤** | 1. 创建日报 (raw_submitted)<br>2. 更新为 trend_pending<br>3. 更新为 trend_ok<br>4. 更新为 final_pending<br>5. 更新为 final_confirmed<br>6. 更新为 final_locked<br>7. 设置 final_locked_at |
| **预期结果** | 所有状态转换成功，final_locked_at 有值 |
| **SQL 对应** | Section 13: TC-FLOW-002 |

### 6.3 死号余额迁移流程测试

#### TC-FLOW-003: 死号余额迁移流程

| 项目 | 内容 |
|------|------|
| **编号** | TC-FLOW-003 |
| **目标** | 验证死号账户余额迁移到新账户的完整流程 |
| **SoT 依据** | STATE_MACHINE.md §12, TRANSFER_SOT.md |
| **前置条件** | 存在源账户 (dead) 和目标账户 (active)，两个不同的 supplier |
| **步骤** | 1. 创建 transfer_request (draft)<br>2. 更新为 pending_approval<br>3. 更新为 approved，设置 approved_by<br>4. 插入 TRANSFER_OUT 账本记录 (源供应商)<br>5. 插入 TRANSFER_IN 账本记录 (目标供应商)<br>6. 更新为 completed<br>7. 验证 v_supplier_balance |
| **预期结果** | 源供应商 calculated_balance 减少，目标供应商 calculated_balance 增加 |
| **SQL 对应** | Section 14: TC-FLOW-003 |

### 6.4 对账流程测试

#### TC-FLOW-004: 对账批次完整流程

| 项目 | 内容 |
|------|------|
| **编号** | TC-FLOW-004 |
| **目标** | 验证对账批次从创建到完成的完整流程 |
| **SoT 依据** | STATE_MACHINE.md §11 |
| **前置条件** | 存在有效项目、广告账户 |
| **步骤** | 1. 创建 reconciliation_batch (draft)<br>2. 创建 reconciliation_detail<br>3. 更新批次状态为 pending_review<br>4. 更新批次状态为 approved<br>5. 更新批次状态为 completed |
| **预期结果** | 所有状态转换成功 |
| **SQL 对应** | Section 15: TC-FLOW-004 |

---

## 7. 测试执行

### 7.1 执行方式

```bash
# 方式 1: psql 直接执行
psql -U postgres -d ai_ad_spend -f backend/db/db_invariants_test_v2.sql

# 方式 2: Supabase SQL Editor
# 将脚本内容粘贴到 SQL Editor 执行
```

### 7.2 结果判读

- **PASS**: 测试函数正常返回，输出 `PASS: <测试编号>`
- **FAIL**: 抛出 `TEST_FAILED` 异常，包含具体失败原因

### 7.3 清理策略

测试脚本使用安全的清理机制：

- 清理阶段使用 `BEGIN...EXCEPTION...END` 块包裹
- 即使清理过程出错，也确保触发器被恢复
- 最终 COMMIT 确保所有测试数据被清理

---

## 8. 附录

### 8.1 SoT 文档引用

| 文档 | 版本 | 用途 |
|------|------|------|
| DATA_SCHEMA.md | v5.2 | 字段类型、约束定义 |
| MASTER.md | v3.4 | 核心不变量 (INV-001) |
| STATE_MACHINE.md | v2.6 | 状态枚举定义 |
| PATTERNS.md | v1.0 | 反模式规则 (AP-LED-*) |
| AUTH_SPEC.md | v2.0 | 角色枚举定义 |
| LEDGER_SOT.md | v1.1 | 双账本规则 |

### 8.2 状态枚举对照表

| 表名 | 字段 | 合法值 | SoT 引用 |
|------|------|--------|----------|
| users | role | admin, finance, data_operator, account_manager, media_buyer | AUTH_SPEC.md §2.2 |
| projects | status | draft, active, suspended, archived | STATE_MACHINE.md §5 |
| channels | status | active, inactive | STATE_MACHINE.md §6.1 |
| ad_accounts | status | new, testing, active, suspended, dead, archived | STATE_MACHINE.md §7.1 |
| daily_reports | status | raw_submitted, trend_pending, trend_ok, trend_flagged, trend_resolved, final_pending, final_confirmed, final_locked | STATE_MACHINE.md §8 |
| topup_requests | status | draft, pending_review, finance_approve, paid, completed, rejected, cancelled | STATE_MACHINE.md §9 |
| transfer_requests | status | draft, pending_approval, approved, rejected, completed | STATE_MACHINE.md §12 |
| reconciliation_batches | status | draft, pending_review, approved, needs_adjustment, completed | STATE_MACHINE.md §11.1 |
| reconciliation_details | status | pending, confirmed, adjusted | STATE_MACHINE.md §11.2 |
| ledger_entries | ledger_type | PROJECT, SUPPLIER | DATA_SCHEMA.md §3.4.4 |
| ledger_entries | entry_type | REVENUE, COST, TOPUP, TRANSFER_OUT, TRANSFER_IN, REVERSAL | DATA_SCHEMA.md §3.4.4 |

### 8.3 测试用例统计

| 优先级 | 用例数 | 覆盖范围 |
|--------|--------|----------|
| P0 | 13 | 账本不可变性、双账本隔离、余额只读、日报唯一约束 |
| P1 | 8 | 用户角色、充值状态、账户状态、迁移状态 |
| P2 | 5 | 余额视图验证、对账模块 |
| 集成 | 4 | 充值流程、日报流程、迁移流程、对账流程 |
| **总计** | **30** | |

---

## 9. 变更记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0 | 2025-11-25 | 初始版本 |
| v2.0 | 2025-11-25 | P0: 修复 v_supplier_balance 视图测试对齐<br>P0: 新增 TC-FLOW-003/004 对账与迁移流程<br>P0: 新增 TC-REC-001/002 对账模块测试<br>P0: 新增 TC-TRF-002 迁移状态合法值<br>P1: 修正测试约定为"顺序执行"<br>P1: SQL 清理阶段使用安全机制<br>P2: 标注视图定义来源与用途 |

---

*文档结束*
