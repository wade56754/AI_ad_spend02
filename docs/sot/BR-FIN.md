# BR-FIN - 财务流程规则

> **文档版本**: v1.1
> **status**: active
> **owner**: wade
> **last_reviewed**: 2026-01-02
> **父文档**: BUSINESS_RULES.md v5.1
> **关联 SoT**: STATE_MACHINE.md v2.9 §9, DATA_SCHEMA.md v5.7 §3.4
> **业务参考**: 见本文档 §三本账体系（历史参考: BUSINESS_LOGIC_FRAMEWORK v2.1 已废弃）

---

## 互锁 SoT 引用

| SoT 文档 | 版本 | 引用章节 | 引用内容 |
|----------|------|----------|----------|
| BUSINESS_RULES.md | v5.0 | §4.5 | 规则索引定义 |
| STATE_MACHINE.md | v2.9 | §9, §16.4 | 充值状态机（7 状态）、Phase 边界 |
| DATA_SCHEMA.md | v5.7 | §3.4 | topup_requests, ledger_entries 表结构 |
| ERROR_CODES.md | v2.3 | §3-4 | 错误码映射 |
| AUTH_SPEC.md | v2.2 | §2.2, §3 | 角色权限、审批流程 |
| MASTER.md | v4.8 | §2.4, §3 | 角色定义、不变量 |

---

## 规则总览

| 规则ID | 规则名称 | 优先级 | 测试状态 |
|--------|----------|--------|----------|
| BR-FIN-001 | 充值必须申请 | P0 | ✅ |
| BR-FIN-002 | 充值审批人 | P0 | ✅ |
| BR-FIN-003 | 大额充值 | P0 | ✅ |
| BR-FIN-004 | 预收款非收入 | P0 | ✅ |
| BR-FIN-005 | 消耗不含手续费 | P0 | ✅ |
| BR-FIN-006 | 可用资金公式 | P0 | ✅ |
| BR-FIN-007 | 锁定后不可改 | P0 | ✅ |
| BR-FIN-008 | 红冲必须有理由 | P0 | ✅ |
| BR-FIN-009 | 三本账体系 | P0 | ✅ |
| BR-FIN-010 | 资金流水审计 | P0 | 🟡 |

---

## 规则详细定义

### BR-FIN-001: 充值必须申请

#### 业务场景
充值是资金流入的唯一合法途径。为确保资金来源可追溯、审批流程完整，所有充值必须通过申请流程，禁止直接向账户注入资金。

#### 详细约束
- ✅ **允许**: 通过 `topup_requests` 表发起充值申请
- ❌ **禁止**: 直接向 `ledger_entries` 插入 TOPUP 类型记录
- ❌ **禁止**: 绕过状态机直接修改账户余额
- 📌 **强制**: 充值申请必须关联有效的 `project_id` 和 `ad_account_id`
- 📌 **强制**: 充值申请状态必须从 `draft` 开始

#### 前置条件
- 用户角色: `pitcher`（技术层: `media_buyer`）或 `account_manager`
- 数据状态: 关联项目状态为 `active`
- 引用: STATE_MACHINE.md v2.8 §9, DATA_SCHEMA.md v5.6 §3.4.1

#### 充值状态机（7 状态）
```
draft → pending_review → finance_approve → paid → completed
                       ↘ rejected
       ↘ cancelled
```

| 当前状态 | 目标状态 | 触发动作 | 允许角色 |
|----------|----------|----------|----------|
| - | `draft` | 创建申请 | pitcher, account_manager |
| `draft` | `pending_review` | 提交申请 | pitcher, account_manager |
| `draft` | `cancelled` | 取消申请 | pitcher, account_manager |
| `pending_review` | `finance_approve` | 复核通过 | project_owner |
| `pending_review` | `rejected` | 复核拒绝 | project_owner |
| `finance_approve` | `paid` | 支付确认 | finance |
| `paid` | `completed` | 到账确认 | finance, system |

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 直接插入账本 | `BIZ_001` | 400 | 充值必须通过申请流程 |
| 项目状态无效 | `STATE_400` | 400 | 项目状态不允许充值 |
| 缺少必填字段 | `BIZ_001` | 400 | 充值申请必须关联项目和账户 |

#### 代码引用
- Service: `backend/services/topup_service.py`
- 方法: `create_topup_request()`, `submit_topup_request()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | pitcher 创建充值申请 | pitcher + 有效项目 | 成功，状态为 `draft` |
| T2 | 直接插入 ledger_entries | INSERT TOPUP | 被拦截/触发器拒绝 |
| T3 | 对 archived 项目充值 | 状态=archived | `STATE_400` |
| T4 | 缺少 project_id | 无 project_id | `BIZ_001` |

---

### BR-FIN-002: 充值审批人

#### 业务场景
充值涉及资金安全，必须经过多级审批。复核由项目负责人执行（确认业务需要），终审由财务执行（确认资金合规）。

> **架构决策（MASTER v4.6+）变更**: 充值复核由原 supervisor 变更为 project_owner

#### 详细约束
- ✅ **允许**: `project_owner` 复核充值申请（`pending_review` → `finance_approve` / `rejected`）
- ✅ **允许**: `finance` 终审并支付（`finance_approve` → `paid`）
- ❌ **禁止**: `pitcher` 审批充值申请
- ❌ **禁止**: 申请人审批自己的申请
- 📌 **强制**: 复核人必须是申请所属项目的负责人或 admin

#### 前置条件
- 用户角色: 复核 `project_owner`，终审 `finance`
- 数据状态: 申请状态为 `pending_review`（复核）或 `finance_approve`（终审）
- 引用: AUTH_SPEC.md v2.1 §2.2, MASTER.md v4.8 §2.4

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 非 project_owner 复核 | `AUTH_500` | 403 | 仅项目负责人可复核充值申请 |
| 非 finance 终审 | `AUTH_500` | 403 | 仅财务可终审充值申请 |
| 申请人自审 | `BIZ_001` | 400 | 申请人不得审批自己的申请 |
| 状态不允许审批 | `STATE_400` | 400 | 当前状态不允许审批 |

#### 代码引用
- Service: `backend/services/topup_service.py`
- 方法: `review_topup_request()`, `approve_topup_request()`, `pay_topup_request()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | project_owner 复核通过 | project_owner + pending_review | 成功，状态→ `finance_approve` |
| T2 | pitcher 尝试复核 | pitcher | `AUTH_500` |
| T3 | 申请人自审 | created_by=current_user | `BIZ_001` |
| T4 | finance 终审支付 | finance + finance_approve | 成功，状态→ `paid` |

---

### BR-FIN-003: 大额充值

#### 业务场景
超过一定金额阈值的充值涉及重大资金风险，需要 CEO 最终批准。阈值由系统配置，默认为 50,000 CNY。

#### 详细约束
- ✅ **允许**: 普通充值由 finance 终审
- 📌 **强制**: 超过阈值的充值必须由 `ceo` 或 `admin` 最终批准
- 📌 **强制**: 大额阈值通过系统配置 `LARGE_TOPUP_THRESHOLD` 设定
- ❌ **禁止**: finance 绕过 ceo 直接批准大额充值

#### 前置条件
- 用户角色: `ceo` 或 `admin`（大额），`finance`（普通）
- 数据状态: 申请金额超过阈值
- 引用: MASTER.md v4.8 §2.4（ceo 职责）

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 大额未经 ceo 批准 | `AUTH_500` | 403 | 大额充值需 CEO 批准 |
| 阈值配置无效 | `BIZ_001` | 400 | 大额阈值配置无效 |

#### 代码引用
- Service: `backend/services/topup_service.py`
- 方法: `_check_large_topup_approval()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 普通充值 finance 终审 | amount=10000, finance | 成功 |
| T2 | 大额充值 finance 终审 | amount=100000, finance | `AUTH_500` |
| T3 | 大额充值 ceo 批准 | amount=100000, ceo | 成功 |
| T4 | 刚好阈值边界 | amount=50000, finance | 成功（不含边界） |

---

### BR-FIN-004: 预收款非收入

#### 业务场景
广告代投业务中，客户预付的资金在履约完成前属于负债（预收账款），不得确认为收入。只有当广告消耗完成且粉数确认后，才能按计费公式确认收入。

> **不变量**: CLAUDE.md - "预收款≠收入：履约完成前是负债"

#### 详细约束
- 📌 **强制**: 充值到账后计入 `ledger_entries.entry_type=TOPUP`，不计入 REVENUE
- 📌 **强制**: 收入仅在 `daily_reports.status=final_locked` 后确认
- ❌ **禁止**: 充值时直接计入收入
- ❌ **禁止**: 在粉数未确认前计算利润

#### 前置条件
- 数据状态: 充值已到账（`topup_requests.status=completed`）
- 引用: CLAUDE.md 不变量, DATA_SCHEMA.md v5.6 §3.4.4

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 充值计入收入 | `BIZ_001` | 400 | 充值不得直接计入收入 |
| 未确认粉数计算利润 | `BIZ_001` | 400 | 仅 final_locked 状态可计算利润 |

#### 代码引用
- Service: `backend/services/ledger_service.py`
- 方法: `create_topup_entry()`, `create_revenue_entry()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 充值创建 TOPUP entry | 充值完成 | entry_type=TOPUP |
| T2 | 尝试创建 REVENUE for 充值 | 充值+REVENUE | `BIZ_001` |
| T3 | final_locked 后创建 REVENUE | final_locked 日报 | 成功 |
| T4 | final_pending 计算利润 | 状态=final_pending | `BIZ_001` |

---

### BR-FIN-005: 消耗不含手续费

#### 业务场景
平台消耗（`ad_spend`）是纯广告费用，不包含渠道手续费。手续费单独核算，计入成本但不计入消耗。这确保了消耗数据与平台对账一致。

> **不变量**: CLAUDE.md - "平台消耗不含手续费：广告费和手续费分开核算"

#### 详细约束
- 📌 **强制**: `daily_reports.ad_spend` 仅包含纯广告消耗
- 📌 **强制**: 手续费通过 `daily_reports.platform_fee` 单独记录
- 📌 **强制**: 成本公式: `cost = ad_spend + platform_fee`
- ❌ **禁止**: 将手续费计入 `ad_spend` 字段

#### 前置条件
- 数据状态: 日报录入时
- 引用: CLAUDE.md 不变量, DATA_SCHEMA.md v5.6 daily_reports 表

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| ad_spend 包含手续费 | `BIZ_001` | 400 | 平台消耗不得包含手续费 |
| 手续费为负 | `BIZ_100` | 400 | 手续费不得为负数 |

#### 代码引用
- Service: `backend/services/daily_report_service.py`
- 方法: `_validate_spend_fields()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 分开录入消耗和手续费 | ad_spend=1000, fee=50 | 成功，cost=1050 |
| T2 | 消耗包含手续费（业务校验） | 人工审核发现 | 业务层拒绝 |
| T3 | 手续费为负数 | fee=-10 | `BIZ_100` |
| T4 | 成本计算验证 | ad_spend=1000, fee=50 | cost=1050 |

---

### BR-FIN-006: 可用资金公式

#### 业务场景
可用资金是项目当前可用于投放的金额，必须按统一公式计算，确保资金使用的准确性和一致性。

> **不变量**: CLAUDE.md - "可用资金公式：opening_balance + Σtopup - Σad_spend"

#### 详细约束
- 📌 **强制**: 可用资金 = `opening_balance + Σtopup - Σad_spend`
- 📌 **强制**: 计算必须基于 `ledger_entries` 表的记录
- ❌ **禁止**: 使用缓存值或估算值
- ❌ **禁止**: 可用资金为负时继续投放（Phase 2）

#### 前置条件
- 数据状态: ledger_entries 数据完整
- 引用: CLAUDE.md 不变量, DATA_SCHEMA.md v5.6 §3.4.4

#### 可用资金计算逻辑
```sql
SELECT
    COALESCE(opening_balance, 0)
    + COALESCE(SUM(CASE WHEN entry_type = 'TOPUP' THEN amount ELSE 0 END), 0)
    - COALESCE(SUM(CASE WHEN entry_type = 'COST' THEN ABS(amount) ELSE 0 END), 0)
AS available_balance
FROM ledger_entries
WHERE project_id = :project_id AND ledger_type = 'PROJECT';
```

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 公式计算错误 | `BIZ_001` | 400 | 可用资金计算错误 |
| 余额不足 | `BIZ_101` | 400 | 可用资金不足 |
| 账本数据缺失 | `BIZ_604` | 500 | 余额查询失败 |

#### 代码引用
- Service: `backend/services/ledger_service.py`
- 方法: `get_available_balance()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 正常计算 | opening=0, topup=10000, spend=3000 | available=7000 |
| T2 | 无充值记录 | opening=5000, topup=0 | available=5000 |
| T3 | 消耗超充值 | topup=5000, spend=6000 | available=-1000 |
| T4 | 空项目 | 无 ledger_entries | available=0 |

---

### BR-FIN-007: 锁定后不可改

#### 业务场景
财务数据一旦锁定（`final_locked` 或 `is_locked=true`），不得直接修改，确保财务数据的不可篡改性和审计合规性。如需修正，必须通过红冲机制。

> **不变量**: CLAUDE.md - "锁定后不可改：只能红冲（ref_id + reason）"

#### 详细约束
- ✅ **允许**: 锁定前修改数据
- ❌ **禁止**: 锁定后直接 UPDATE 任何金额字段
- ❌ **禁止**: DELETE 任何 `ledger_entries` 记录
- 📌 **强制**: 修正必须创建 `entry_type=REVERSAL` 记录
- 📌 **强制**: 红冲记录必须引用原记录（`reference_id`）

#### 前置条件
- 数据状态: `daily_reports.status=final_locked` 或 `ledger_entries.is_locked=true`
- 引用: CLAUDE.md 不变量, STATE_MACHINE.md v2.8 §8

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 锁定后修改 | `BIZ_001` | 400 | 已锁定数据不可修改 |
| 删除账本记录 | `BIZ_001` | 400 | 账本记录不可删除 |
| 终态回退 | `STATE_402` | 400 | 终态不可回退 |

#### 代码引用
- Service: `backend/services/ledger_service.py`
- 方法: `_check_locked_status()`, `update_ledger_entry()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 锁定前修改 | is_locked=false | 成功 |
| T2 | 锁定后修改金额 | is_locked=true, UPDATE amount | `BIZ_001` |
| T3 | 删除账本记录 | DELETE ledger_entries | `BIZ_001` |
| T4 | 通过红冲修正 | 创建 REVERSAL entry | 成功 |

---

### BR-FIN-008: 红冲必须有理由

#### 业务场景
红冲是财务修正的唯一合法途径。为确保审计可追溯，红冲操作必须提供原记录引用和修正原因。

#### 详细约束
- 📌 **强制**: 红冲必须提供 `reference_id`（原记录 ID）
- 📌 **强制**: 红冲必须提供 `notes`（修正原因）
- 📌 **强制**: 红冲金额必须为负数（冲销原记录）
- ❌ **禁止**: 空理由的红冲操作
- ❌ **禁止**: 正数金额的红冲

#### 前置条件
- 用户角色: `finance` 或 `admin`
- 数据状态: 原记录存在且已锁定
- 引用: CLAUDE.md 不变量, DATA_SCHEMA.md v5.6 §3.4.4

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 红冲缺少 reference_id | `BIZ_001` | 400 | 红冲必须引用原记录 |
| 红冲缺少理由 | `BIZ_001` | 400 | 红冲必须提供理由 |
| 红冲金额为正 | `BIZ_100` | 400 | 红冲金额必须为负数 |
| 原记录不存在 | `BIZ_602` | 404 | 原记录不存在 |

#### 代码引用
- Service: `backend/services/ledger_service.py`
- 方法: `create_reversal_entry()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 完整红冲 | ref_id + reason + amount<0 | 成功 |
| T2 | 缺少 reference_id | reason only | `BIZ_001` |
| T3 | 缺少理由 | ref_id only | `BIZ_001` |
| T4 | 正数红冲 | amount=100 | `BIZ_100` |

---

### BR-FIN-009: 三本账体系

#### 业务场景
系统采用三本账体系：
1. **预付款账本（PROJECT）**：记录客户付给我们的钱，余额表示还"欠"客户多少（待消耗）
2. **充值账本（SUPPLIER）**：记录我们充给代理商的钱，余额表示累计投入多少
3. **押款账本（计算值）**：充值 - 消耗 = 押在代理商的钱（资金占用）

三本账必须分开记录，确保收入、成本、资金占用的独立核算。

#### 详细约束
- 📌 **强制**: `ledger_type=PROJECT` 时 `project_id` 必填
- 📌 **强制**: `ledger_type=SUPPLIER` 时 `supplier_id` 必填
- 📌 **强制**: PROJECT 账本允许: `REVENUE`, `TOPUP`, `REVERSAL`
- 📌 **强制**: SUPPLIER 账本允许: `COST`, `TOPUP`, `TRANSFER_OUT`, `TRANSFER_IN`, `REVERSAL`
- ❌ **禁止**: COST 类型进入 PROJECT 账本
- ❌ **禁止**: REVENUE 类型进入 SUPPLIER 账本

#### 前置条件
- 数据状态: 创建 ledger_entries 时
- 引用: DATA_SCHEMA.md v5.6 §3.4.4

#### 账本类型与 entry_type 对应关系
| ledger_type | 允许的 entry_type | 用途 |
|-------------|-------------------|------|
| PROJECT | REVENUE | 粉数计费收入 |
| PROJECT | TOPUP | 项目充值 |
| PROJECT | REVERSAL | 项目红冲 |
| SUPPLIER | COST | 真实消耗成本 |
| SUPPLIER | TOPUP | 供应商充值 |
| SUPPLIER | TRANSFER_OUT | 死号余额迁出 |
| SUPPLIER | TRANSFER_IN | 死号余额迁入 |
| SUPPLIER | REVERSAL | 供应商红冲 |

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| PROJECT 账本缺 project_id | `BIZ_001` | 400 | PROJECT 账本必须关联项目 |
| SUPPLIER 账本缺 supplier_id | `BIZ_001` | 400 | SUPPLIER 账本必须关联供应商 |
| entry_type 与 ledger_type 不匹配 | `BIZ_001` | 400 | 账本类型与条目类型不匹配 |
| COST 进入 PROJECT 账本 | `BIZ_001` | 400 | COST 类型不得进入 PROJECT 账本 |

#### 代码引用
- Service: `backend/services/ledger_service.py`
- 方法: `_validate_ledger_entry()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | PROJECT 账本 REVENUE | ledger_type=PROJECT, entry_type=REVENUE | 成功 |
| T2 | PROJECT 账本 COST | ledger_type=PROJECT, entry_type=COST | `BIZ_001` |
| T3 | SUPPLIER 账本无 supplier_id | ledger_type=SUPPLIER, supplier_id=null | `BIZ_001` |
| T4 | SUPPLIER 账本 TRANSFER | ledger_type=SUPPLIER, entry_type=TRANSFER_OUT | 成功 |

---

### BR-FIN-010: 资金流水审计

#### 业务场景
所有资金变动必须记录完整的审计轨迹，包括操作人、操作时间、变动前后值等。这是财务合规和问题追溯的基础。

#### 详细约束
- 📌 **强制**: 充值申请状态变更记录到 `topup_approval_logs`
- 📌 **强制**: 账本变动记录 `created_by`、`created_at`
- 📌 **强制**: 支付记录 `payment_reference`、`paid_at`
- ❌ **禁止**: 匿名（无 created_by）的资金变动
- ❌ **禁止**: 无时间戳的资金变动

#### 前置条件
- 数据状态: 任何资金相关操作
- 引用: DATA_SCHEMA.md v5.6 §3.4

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 缺少操作人 | `SYS_001` | 500 | 资金变动必须记录操作人 |
| 缺少时间戳 | `SYS_001` | 500 | 资金变动必须记录时间戳 |
| 审计日志写入失败 | `SYS_001` | 500 | 审计日志写入失败 |

#### 代码引用
- Service: `backend/services/topup_service.py`, `backend/services/ledger_service.py`
- 方法: `_create_approval_log()`, `_audit_ledger_change()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 充值审批记录 | 状态变更 | topup_approval_logs 有记录 |
| T2 | 账本变动记录 | 创建 ledger_entry | created_by 非空 |
| T3 | 无操作人变动 | created_by=null | `SYS_001` |
| T4 | 支付记录完整 | 支付完成 | payment_reference 非空 |

---

## 规则依赖关系

```
BR-FIN-001 (充值必须申请)
    ↓
BR-FIN-002 (充值审批人)
    ↓
BR-FIN-003 (大额充值)
    ↓
BR-FIN-004 (预收款非收入) ←── BR-FIN-009 (三本账体系)
    ↓
BR-FIN-005 (消耗不含手续费)
    ↓
BR-FIN-006 (可用资金公式)
    ↓
BR-FIN-007 (锁定后不可改) ←── BR-FIN-008 (红冲必须有理由)
    ↓
BR-FIN-010 (资金流水审计)
```

---

## 变更历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0 | 2025-12-27 | 初始版本，对齐 BUSINESS_RULES.md v4.8；BR-FIN-002 充值复核由 supervisor 变更为 project_owner（MASTER v4.6+）；所有错误码对齐 ERROR_CODES.md v2.2 |

---

**文档性质**: 业务规则子模块
**执行级别**: 强制执行
**父文档**: BUSINESS_RULES.md v4.6
**关联 SoT**: STATE_MACHINE.md v2.8 §9, DATA_SCHEMA.md v5.6 §3.4
**版本**: v1.0
