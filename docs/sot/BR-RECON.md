# BR-RECON - 对账流程规则

> **文档版本**: v1.0
> **status**: active
> **owner**: wade
> **last_reviewed**: 2025-12-27
> **父文档**: BUSINESS_RULES.md v4.6
> **关联 SoT**: STATE_MACHINE.md v2.7 §11, DATA_SCHEMA.md v5.6 §3.5

---

## 互锁 SoT 引用

| SoT 文档 | 版本 | 引用章节 | 引用内容 |
|----------|------|----------|----------|
| BUSINESS_RULES.md | v4.6 | §4.7 | 规则索引定义 |
| STATE_MACHINE.md | v2.7 | §11, §14.4 | 对账批次状态机（5 状态）、对账明细状态机（3 状态） |
| DATA_SCHEMA.md | v5.6 | §3.5 | reconciliation_batches, reconciliation_details, reconciliation_issues 表结构 |
| ERROR_CODES.md | v2.3 | §3-4 | 错误码映射 |
| AUTH_SPEC.md | v2.2 | §2.2, §3 | 角色权限、审批流程 |
| MASTER.md | v4.6 | §2.4, §3 | 角色定义、Phase 边界 |

---

## 规则总览

| 规则ID | 规则名称 | 优先级 | 测试状态 |
|--------|----------|--------|----------|
| BR-RECON-001 | 对账周期 | P0 | ✅ |
| BR-RECON-002 | 对账发起人 | P0 | ✅ |
| BR-RECON-003 | 差异阈值 | P0 | ✅ |
| BR-RECON-004 | 对账状态流转 | P0 | ✅ |
| BR-RECON-005 | 完成后不可逆 | P0 | ✅ |
| BR-RECON-006 | 差异必须记录 | P0 | 🟡 |
| BR-RECON-007 | 调整必须审批 | P0 | ✅ |

---

## 规则详细定义

### BR-RECON-001: 对账周期

#### 业务场景
对账是确保系统数据与外部平台数据一致的关键流程。为保证对账的完整性和可操作性，对账必须按月执行，以自然月为周期。

#### 详细约束
- 📌 **强制**: 对账批次必须指定 `period_start` 和 `period_end`
- 📌 **强制**: `period_start` 和 `period_end` 必须在同一自然月内
- 📌 **强制**: 默认周期为当月 1 日至当月最后一天
- ❌ **禁止**: 创建跨月对账批次
- ❌ **禁止**: 对未结束的月份进行对账

#### 前置条件
- 用户角色: `finance` 或 `admin`
- 数据状态: 当前日期大于对账月份最后一天
- 引用: DATA_SCHEMA.md v5.6 §3.5.1

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 跨月对账 | `BIZ_001` | 400 | 对账周期不得跨月 |
| 对未结束月份对账 | `BIZ_001` | 400 | 不得对未结束的月份进行对账 |
| 缺少周期参数 | `BIZ_001` | 400 | 对账批次必须指定周期 |

#### 代码引用
- Service: `backend/services/reconciliation_service.py`
- 方法: `create_reconciliation_batch()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 正常月度对账 | period=2025-11 | 成功，状态为 `draft` |
| T2 | 跨月对账 | start=2025-11-15, end=2025-12-15 | `BIZ_001` |
| T3 | 对当前月份对账 | period=当前月 | `BIZ_001` |
| T4 | 缺少周期参数 | 无 period | `BIZ_001` |

---

### BR-RECON-002: 对账发起人

#### 业务场景
对账涉及资金核对和数据调整，必须由财务人员发起和管理，确保对账过程的专业性和合规性。

#### 详细约束
- ✅ **允许**: `finance` 角色创建对账批次
- ✅ **允许**: `admin` 角色创建对账批次（紧急情况）
- ❌ **禁止**: `pitcher` 发起对账
- ❌ **禁止**: `project_owner` 发起对账
- 📌 **强制**: 对账批次必须记录 `created_by`

#### 前置条件
- 用户角色: `finance`（技术层: `finance`）或 `admin`
- 引用: AUTH_SPEC.md v2.2 §2.2, MASTER.md v4.6 §2.4

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 非 finance 发起 | `AUTH_500` | 403 | 仅财务可发起对账 |
| 缺少 created_by | `BIZ_001` | 400 | 对账批次必须记录创建人 |

#### 代码引用
- Service: `backend/services/reconciliation_service.py`
- 方法: `create_reconciliation_batch()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | finance 发起对账 | finance 用户 | 成功 |
| T2 | pitcher 尝试发起 | pitcher 用户 | `AUTH_500` |
| T3 | project_owner 尝试发起 | project_owner | `AUTH_500` |
| T4 | admin 紧急发起 | admin 用户 | 成功 |

---

### BR-RECON-003: 差异阈值

#### 业务场景
对账过程中发现的差异需要根据金额大小采取不同的处理方式。小额差异可自动确认，超过阈值的差异必须人工确认，防止重大差异被忽略。

#### 详细约束
- 📌 **强制**: 差异阈值通过系统配置 `RECON_DIFF_THRESHOLD` 设定
- 📌 **强制**: 默认阈值为 100 CNY
- ✅ **允许**: 差异 ≤ 阈值时可自动确认（Phase 2）
- 📌 **强制**: 差异 > 阈值时必须人工确认
- 📌 **强制**: 超阈值差异必须创建 `reconciliation_issues` 记录

#### 前置条件
- 数据状态: 对账明细已生成差异金额
- 引用: DATA_SCHEMA.md v5.6 §3.5.6

#### Phase 边界
| Phase | 行为 |
|-------|------|
| Phase 1 | 所有差异均需人工确认，仅提示+高亮 |
| Phase 2 | 小额差异可自动确认 |

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 超阈值未人工确认 | `BIZ_001` | 400 | 差异超过阈值，需人工确认 |
| 阈值配置无效 | `BIZ_001` | 400 | 差异阈值配置无效 |

#### 代码引用
- Service: `backend/services/reconciliation_service.py`
- 方法: `_check_difference_threshold()`, `confirm_detail()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 小额差异确认 | diff=50, threshold=100 | 成功 |
| T2 | 超阈值自动确认 | diff=150, 自动确认 | `BIZ_001`（Phase 1） |
| T3 | 超阈值人工确认 | diff=150, 人工确认 | 成功 |
| T4 | 差异创建 issue | diff=500 | reconciliation_issues 有记录 |

---

### BR-RECON-004: 对账状态流转

#### 业务场景
对账批次状态机定义了对账从创建到完成的完整生命周期。所有状态变更必须遵循预定义的合法流转路径，确保对账流程的一致性和可追溯性。

#### 详细约束
- ✅ **允许**: 仅 STATE_MACHINE.md v2.7 §11 定义的合法流转
- ❌ **禁止**: 直接 UPDATE `reconciliation_batches.status` 字段
- ❌ **禁止**: 跳过中间状态
- 📌 **强制**: 状态变更必须通过业务动作触发
- 📌 **强制**: 终态 `completed` 不可回退

#### 前置条件
- 数据状态: 当前状态必须在合法流转表中
- 引用: STATE_MACHINE.md v2.7 §11

#### 对账批次状态机（5 状态）
```
draft → pending_review → approved → completed
                       ↘ needs_adjustment ↗
```

| 当前状态 | 目标状态 | 触发动作 | 允许角色 |
|----------|----------|----------|----------|
| - | `draft` | 创建批次 | finance, admin |
| `draft` | `pending_review` | 提交审核 | finance |
| `pending_review` | `approved` | 审核通过 | finance, admin |
| `pending_review` | `needs_adjustment` | 发现差异 | finance, admin |
| `needs_adjustment` | `approved` | 调整完成 | finance, admin |
| `approved` | `completed` | 完成对账 | finance, admin |

#### 对账明细状态机（3 状态）
```
pending → confirmed
        ↘ adjusted
```

| 当前状态 | 目标状态 | 触发动作 | 允许角色 |
|----------|----------|----------|----------|
| - | `pending` | 创建明细 | system |
| `pending` | `confirmed` | 确认无差异 | finance |
| `pending` | `adjusted` | 调整差异 | finance |

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 非法状态流转 | `STATE_400` | 400 | 不允许从 {from} 转换到 {to} |
| 终态回退 | `STATE_402` | 400 | 终态不可回退 |
| 未满足前置条件 | `BIZ_001` | 400 | 状态变更未满足前置条件 |

#### 代码引用
- Service: `backend/services/reconciliation_service.py`
- 方法: `_validate_status_transition()`, `submit_for_review()`, `approve_batch()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 合法流转 draft → pending_review | 有效状态转换 | 成功 |
| T2 | 非法流转 draft → completed | 跳过中间状态 | `STATE_400` |
| T3 | 终态回退 completed → approved | 回退终态 | `STATE_402` |
| T4 | needs_adjustment → approved | 调整完成 | 成功 |

---

### BR-RECON-005: 完成后不可逆

#### 业务场景
对账完成后数据已锁定，账本可能已生成调整记录。为确保财务数据的一致性和审计合规性，已完成的对账批次不得回退或修改。

#### 详细约束
- ✅ **允许**: `completed` 状态下查看对账数据
- ❌ **禁止**: `completed` 状态后修改对账批次
- ❌ **禁止**: `completed` 状态后修改对账明细
- ❌ **禁止**: 回退 `completed` 状态
- 📌 **强制**: 如需修正，必须创建新的调整批次

#### 前置条件
- 数据状态: 对账批次状态为 `completed`
- 引用: STATE_MACHINE.md v2.7 §14.2

#### 完成前置条件（STATE_MACHINE.md §14.4）
对账批次从 `approved` 流转至 `completed` 必须满足：
1. 无 pending 状态的明细
2. 所有明细处于终态（`confirmed` 或 `adjusted`）
3. 所有 `adjusted` 明细已生成对应的 LedgerEntry

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 完成后修改 | `BIZ_001` | 400 | 已完成的对账不可修改 |
| 终态回退 | `STATE_402` | 400 | 终态不可回退 |
| 存在 pending 明细 | `BIZ_001` | 400 | 存在未处理的对账明细 |

#### 代码引用
- Service: `backend/services/reconciliation_service.py`
- 方法: `complete_batch()`, `_check_completion_prerequisites()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 完成状态查看 | status=completed | 成功 |
| T2 | 完成后修改 | status=completed, UPDATE | `BIZ_001` |
| T3 | 完成后回退 | completed → approved | `STATE_402` |
| T4 | 有 pending 明细时完成 | 存在 pending 明细 | `BIZ_001` |

---

### BR-RECON-006: 差异必须记录

#### 业务场景
对账过程中发现的所有差异必须完整记录，包括差异类型、金额、原因等。这是问题追溯和财务审计的基础。

#### 详细约束
- 📌 **强制**: 差异必须记录到 `reconciliation_issues` 表
- 📌 **强制**: 差异记录必须包含 `issue_type`、`expected_amount`、`actual_amount`
- 📌 **强制**: 差异处理后必须记录 `resolution_type` 和 `resolution_notes`
- ❌ **禁止**: 删除差异记录
- ❌ **禁止**: 修改已关闭差异的金额

#### 前置条件
- 数据状态: 对账明细存在差异（`difference_amount ≠ 0`）
- 引用: DATA_SCHEMA.md v5.6 §3.5.6

#### 差异类型枚举
| issue_type | 说明 |
|------------|------|
| `topup_mismatch` | 充值差异 |
| `spend_mismatch` | 消耗差异 |
| `deposit_change` | 押款变化 |
| `balance_anomaly` | 余额异常 |
| `snapshot_missing` | 快照缺失 |
| `conservation_failed` | 守恒校验失败 |
| `other` | 其他 |

#### 处理类型枚举
| resolution_type | 说明 |
|-----------------|------|
| `data_correction` | 数据修正 |
| `ledger_adjustment` | 账本调整 |
| `external_confirm` | 外部确认（代理商/甲方） |
| `write_off` | 核销 |
| `false_positive` | 误报 |

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 差异未记录 | `BIZ_001` | 400 | 差异必须记录到差异单 |
| 缺少必填字段 | `BIZ_001` | 400 | 差异记录缺少必填字段 |
| 删除差异记录 | `BIZ_001` | 400 | 差异记录不可删除 |
| 修改已关闭差异 | `BIZ_001` | 400 | 已关闭的差异不可修改 |

#### 代码引用
- Service: `backend/services/reconciliation_service.py`
- 方法: `create_issue()`, `resolve_issue()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 创建差异记录 | 完整字段 | 成功 |
| T2 | 缺少 issue_type | 无 issue_type | `BIZ_001` |
| T3 | 删除差异记录 | DELETE issue | `BIZ_001` |
| T4 | 处理后记录 resolution | resolve issue | resolution_type 非空 |

---

### BR-RECON-007: 调整必须审批

#### 业务场景
对账调整涉及账本变更，必须由财务审批确认。调整记录必须完整，包括调整类型、金额和原因，确保每笔调整都有据可查。

#### 详细约束
- ✅ **允许**: `finance` 审批对账调整
- ✅ **允许**: `admin` 审批对账调整（紧急情况）
- ❌ **禁止**: 未审批的调整生效
- 📌 **强制**: 调整必须提供 `adjustment_type` 和 `reason`
- 📌 **强制**: 调整必须关联对账明细（`detail_id`）
- 📌 **强制**: 调整生效后必须创建对应的 LedgerEntry

#### 前置条件
- 用户角色: `finance` 或 `admin`
- 数据状态: 对账明细状态为 `pending`
- 引用: AUTH_SPEC.md v2.2 §2.2, DATA_SCHEMA.md v5.6 §3.5.3

#### 调整类型枚举
| adjustment_type | 说明 |
|-----------------|------|
| `increase` | 增加（补录） |
| `decrease` | 减少（冲减） |
| `writeoff` | 核销 |

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 非 finance 审批 | `AUTH_500` | 403 | 仅财务可审批对账调整 |
| 缺少调整理由 | `BIZ_001` | 400 | 调整必须提供理由 |
| 缺少调整类型 | `BIZ_001` | 400 | 调整必须指定类型 |
| 未关联明细 | `BIZ_001` | 400 | 调整必须关联对账明细 |

#### 代码引用
- Service: `backend/services/reconciliation_service.py`
- 方法: `create_adjustment()`, `approve_adjustment()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | finance 审批调整 | finance + 完整字段 | 成功 |
| T2 | pitcher 尝试审批 | pitcher | `AUTH_500` |
| T3 | 缺少 reason | 无 reason | `BIZ_001` |
| T4 | 调整后创建 LedgerEntry | 调整生效 | ledger_entries 有记录 |

---

## 规则依赖关系

```
BR-RECON-001 (对账周期)
    ↓
BR-RECON-002 (对账发起人)
    ↓
BR-RECON-004 (状态流转) ←── BR-RECON-003 (差异阈值)
    ↓
BR-RECON-006 (差异记录) ←── BR-RECON-007 (调整审批)
    ↓
BR-RECON-005 (完成不可逆)
```

---

## 对账守恒公式

> **引用**: DATA_SCHEMA.md v5.6 §3.5.5

对账的核心是验证资金守恒：

```
期末余额 = 期初余额 + 充值 - 消耗 ± 押款变化
```

对应字段：
```sql
balance_snapshots.balance =
    prev.balance
    + SUM(topup_transactions.amount)
    - SUM(daily_reports.ad_spend)
    + (current.deposit - prev.deposit)
```

---

## 变更历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0 | 2025-12-27 | 初始版本，对齐 BUSINESS_RULES.md v4.6；所有错误码对齐 ERROR_CODES.md v2.3 |

---

**文档性质**: 业务规则子模块
**执行级别**: 强制执行
**父文档**: BUSINESS_RULES.md v4.6
**关联 SoT**: STATE_MACHINE.md v2.7 §11, DATA_SCHEMA.md v5.6 §3.5
**版本**: v1.0
