# BR-RPT - 日报管理规则

> **文档版本**: v1.0
> **status**: active
> **owner**: wade
> **last_reviewed**: 2025-12-27
> **父文档**: BUSINESS_RULES.md v4.6
> **关联 SoT**: STATE_MACHINE.md v2.7 §7, §16.3

---

## 互锁 SoT 引用

| SoT 文档 | 版本 | 引用章节 | 引用内容 |
|----------|------|----------|----------|
| BUSINESS_RULES.md | v4.6 | §4.6 | 规则索引定义 |
| STATE_MACHINE.md | v2.7 | §7, §7.5, §16.3 | 日报状态机（8 状态）、Phase 边界 |
| DATA_SCHEMA.md | v5.6 | daily_reports 表 | 字段定义、外键约束 |
| ERROR_CODES.md | v2.3 | §3-4 | 错误码映射 |
| AUTH_SPEC.md | v2.2 | §2.2, §3 | 角色权限、职责分离 |
| MASTER.md | v4.6 | §2.4, §3 | 角色定义、Phase 边界 |

---

## 规则总览

| 规则ID | 规则名称 | 优先级 | 测试状态 |
|--------|----------|--------|----------|
| BR-RPT-001 | 日报提交人 | P0 | ✅ |
| BR-RPT-002 | 日报审核人 | P0 | ✅ |
| BR-RPT-003 | 提交审核分离 | P0 | ✅ |
| BR-RPT-004 | 状态流转合法性 | P0 | ✅ |
| BR-RPT-005 | 三数据流定义 | P0 | ✅ |
| BR-RPT-006 | raw 数据提交者 | P0 | ✅ |
| BR-RPT-007 | real 数据提交者 | P0 | ✅ |
| BR-RPT-008 | final 数据提交者 | P0 | 🟡 |
| BR-RPT-009 | final 数据不可改 | P0 | ✅ |

---

## 规则详细定义

### BR-RPT-001: 日报提交人

#### 业务场景
日报是投手每日工作成果的核心记录，包含广告消耗、进粉数等关键指标。只有实际执行投放的投手才能提交日报，确保数据来源的真实性和责任归属的明确性。

#### 详细约束
- ✅ **允许**: `pitcher` 角色提交日报
- ❌ **禁止**: 非 `pitcher` 角色提交日报
- ❌ **禁止**: 投手提交非自己负责账户的日报
- 📌 **强制**: 日报必须关联有效的 `ad_account_id` 和 `project_id`

#### 前置条件
- 用户角色: `pitcher`（技术层: `media_buyer`）
- 数据状态: 日报创建时，关联账户状态不得为 `dead` 或 `archived`
- 引用: AUTH_SPEC.md v2.2 §3, STATE_MACHINE.md v2.7 §7

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 非 pitcher 角色提交 | `AUTH_500` | 403 | 仅投手可提交日报 |
| 提交非自己账户的日报 | `AUTH_500` | 403 | 无权操作此账户 |
| 账户状态无效 | `STATE_402` | 400 | 账户状态不允许提交日报 |

#### 代码引用
- Service: `backend/services/daily_report_service.py`
- 方法: `create_daily_report()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | pitcher 提交自己账户日报 | pitcher + 有效账户 | 成功，状态为 `raw_submitted` |
| T2 | project_owner 尝试提交日报 | project_owner | `AUTH_500` |
| T3 | pitcher 提交他人账户日报 | pitcher + 非分配账户 | `AUTH_500` |
| T4 | pitcher 提交 dead 账户日报 | pitcher + dead 账户 | `STATE_402` |

---

### BR-RPT-002: 日报审核人

#### 业务场景
日报审核是确保数据准确性的关键环节。项目负责人对项目盈亏负责，因此必须由项目负责人审核日报，确保消耗与效果数据的合理性。

> **PRD v2.2 变更**: 日报审核人由原 supervisor 变更为 project_owner

#### 详细约束
- ✅ **允许**: `project_owner` 角色审核日报
- ✅ **允许**: `admin` 角色审核日报（紧急情况）
- ❌ **禁止**: `pitcher` 审核自己提交的日报
- ❌ **禁止**: `finance` 角色审核日报
- 📌 **强制**: 审核人必须是日报所属项目的负责人或 admin

#### 前置条件
- 用户角色: `project_owner`（技术层: `users.is_project_owner=true` 或 `project_members` 表关联）
- 数据状态: 日报状态必须为待审核状态（`trend_pending`, `final_pending`）
- 引用: AUTH_SPEC.md v2.2 §2.2, MASTER.md v4.6 §2.4

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 非 project_owner 审核 | `AUTH_500` | 403 | 仅项目负责人可审核日报 |
| 审核非自己项目的日报 | `AUTH_500` | 403 | 无权审核此项目日报 |
| 日报状态非待审核 | `STATE_400` | 400 | 当前状态不允许审核 |

#### 代码引用
- Service: `backend/services/daily_report_service.py`
- 方法: `review_daily_report()`, `approve_trend()`, `confirm_final()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | project_owner 审核自己项目日报 | project_owner + 待审核日报 | 成功 |
| T2 | pitcher 尝试审核日报 | pitcher | `AUTH_500` |
| T3 | project_owner 审核他人项目日报 | project_owner + 非负责项目 | `AUTH_500` |
| T4 | admin 紧急审核日报 | admin + 待审核日报 | 成功 |

---

### BR-RPT-003: 提交审核分离

#### 业务场景
职责分离（Separation of Duties）是内控的核心原则。日报提交者不得同时是审核者，确保数据的双重校验和防止舞弊。

#### 详细约束
- ✅ **允许**: A 提交，B 审核（A ≠ B）
- ❌ **禁止**: 同一用户既提交又审核同一份日报
- 📌 **强制**: 系统必须在审核时校验 `submitted_by ≠ current_user_id`

#### 前置条件
- 用户角色: 审核操作触发时
- 数据状态: 日报已有 `submitted_by` 记录
- 引用: AUTH_SPEC.md v2.2 §3.2（SOD 规则）, MASTER.md v4.6 §2.4

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 提交者尝试审核自己日报 | `BIZ_001` | 400 | 提交者不得审核自己的日报 |

#### 代码引用
- Service: `backend/services/daily_report_service.py`
- 方法: `_check_separation_of_duties()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | A 提交，B 审核 | user_a 提交, user_b 审核 | 成功 |
| T2 | A 提交，A 审核 | user_a 提交, user_a 审核 | `BIZ_001` |
| T3 | admin 审核自己提交的日报 | admin 提交+审核 | `BIZ_001` |

---

### BR-RPT-004: 状态流转合法性

#### 业务场景
日报状态机定义了日报从创建到锁定的完整生命周期。所有状态变更必须遵循预定义的合法流转路径，确保业务流程的一致性和可追溯性。

#### 详细约束
- ✅ **允许**: 仅 STATE_MACHINE.md v2.7 §7 定义的合法流转
- ❌ **禁止**: 直接 UPDATE `daily_reports.status` 字段
- ❌ **禁止**: 跳过中间状态（Phase 2）
- 📌 **强制**: 状态变更必须通过业务动作触发
- 📌 **强制**: 终态 `final_locked` 不可回退

#### 前置条件
- 数据状态: 当前状态必须在合法流转表中
- 引用: STATE_MACHINE.md v2.7 §7, §7.5

#### 日报状态机（8 状态，Phase 2 完整版）
```
raw_submitted → trend_pending → trend_ok → final_pending → final_confirmed → final_locked
                              ↘ trend_flagged → trend_resolved ↗
```

| 当前状态 | 目标状态 | 触发动作 | 允许角色 |
|----------|----------|----------|----------|
| - | `raw_submitted` | 提交日报 | pitcher |
| `raw_submitted` | `trend_pending` | 触发趋势检查 | system |
| `trend_pending` | `trend_ok` | 趋势正常 | system |
| `trend_pending` | `trend_flagged` | 趋势异常 | system |
| `trend_flagged` | `trend_resolved` | 解决异常 | project_owner |
| `trend_ok`/`trend_resolved` | `final_pending` | 提交粉数确认 | project_owner |
| `final_pending` | `final_confirmed` | 确认粉数 | project_owner |
| `final_confirmed` | `final_locked` | 锁定 | finance, admin |

#### Phase 1 简化版（3 状态）
| 当前状态 | 目标状态 | 说明 |
|----------|----------|------|
| - | `raw_submitted` | 提交日报 |
| `raw_submitted` | `trend_ok` | 跳过趋势审核 |
| `trend_ok` | `final_confirmed` | 跳过粉数待确认 |

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 非法状态流转 | `STATE_400` | 400 | 不允许从 {from} 转换到 {to} |
| 终态回退 | `STATE_402` | 400 | 终态不可回退 |

#### 代码引用
- Service: `backend/services/daily_report_service.py`
- 方法: `_validate_status_transition()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 合法流转 raw_submitted → trend_pending | 有效状态转换 | 成功 |
| T2 | 非法流转 raw_submitted → final_locked | 跳过中间状态 | `STATE_400` |
| T3 | 终态回退 final_locked → final_confirmed | 回退终态 | `STATE_402` |
| T4 | Phase 1 简化流转 | raw_submitted → trend_ok | 成功（Phase 1） |

---

### BR-RPT-005: 三数据流定义

#### 业务场景
日报包含三类数据流，分别由不同角色在不同阶段录入，确保数据采集的完整性和职责的清晰性。

#### 详细约束
- 📌 **强制**: 日报必须区分以下三数据流：

| 数据流 | 字段 | 提交者 | 用途 | 时间点 |
|--------|------|--------|------|--------|
| **raw** | `conversions_raw` | pitcher | 投手上报进粉 | T+1 10:00前 |
| **real** | `real_spend` | project_owner | 实际消耗核算 | T+1 12:00前 |
| **final** | `conversions_final` | project_owner | 甲方确认进粉 | T+1 14:00前 |

- ❌ **禁止**: 混淆三数据流的提交角色
- ❌ **禁止**: 使用非定义字段存储数据流

#### 前置条件
- 引用: DATA_SCHEMA.md v5.6 daily_reports 表, API_SOT.md v9.4 §6

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 数据流字段缺失 | `BIZ_001` | 400 | 必须提供 {field} 数据 |
| 数据流类型错误 | `BIZ_001` | 400 | 数据流类型无效 |

#### 代码引用
- Service: `backend/services/daily_report_service.py`
- 方法: `submit_raw_data()`, `submit_real_data()`, `submit_final_data()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 提交完整三数据流 | raw + real + final | 成功 |
| T2 | 缺少 raw 数据 | real + final only | `BIZ_001` |
| T3 | 错误角色提交 real | pitcher 提交 real | `AUTH_500` |

---

### BR-RPT-006: raw 数据提交者

#### 业务场景
raw 数据（`conversions_raw`）是投手每日上报的进粉数，反映投放执行的即时效果。仅投手可提交此数据，确保数据来源的第一手性。

#### 详细约束
- ✅ **允许**: `pitcher` 提交 `conversions_raw`
- ❌ **禁止**: 非 `pitcher` 角色提交 raw 数据
- 📌 **强制**: raw 数据必须在日报创建时提交

#### 前置条件
- 用户角色: `pitcher`（技术层: `media_buyer`）
- 数据状态: 日报状态为 `raw_submitted` 或创建中
- 引用: AUTH_SPEC.md v2.2 §3, DATA_SCHEMA.md v5.6

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 非 pitcher 提交 raw | `AUTH_500` | 403 | 仅投手可提交 raw 数据 |
| raw 数据为空 | `BIZ_001` | 400 | raw 数据不得为空 |

#### 代码引用
- Service: `backend/services/daily_report_service.py`
- 方法: `submit_raw_data()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | pitcher 提交 raw 数据 | pitcher + conversions_raw=100 | 成功 |
| T2 | project_owner 提交 raw | project_owner + raw | `AUTH_500` |
| T3 | pitcher 提交空 raw | pitcher + conversions_raw=null | `BIZ_001` |

---

### BR-RPT-007: real 数据提交者

#### 业务场景
real 数据（`real_spend`）是项目负责人核算的实际广告消耗，用于成本计算。项目负责人对项目盈亏负责，因此必须由其录入实际消耗。

> **PRD v2.2 变更**: real 数据提交者由原 supervisor 变更为 project_owner

#### 详细约束
- ✅ **允许**: `project_owner` 录入 `real_spend`
- ✅ **允许**: `admin` 录入 `real_spend`（紧急情况）
- ❌ **禁止**: `pitcher` 录入 real 数据
- ❌ **禁止**: `finance` 录入 real 数据
- 📌 **强制**: real_spend 必须大于等于 0

#### 前置条件
- 用户角色: `project_owner`（技术层: `users.is_project_owner=true`）
- 数据状态: 日报状态为 `trend_ok` 或 `trend_resolved`
- 引用: AUTH_SPEC.md v2.2 §2.2, MASTER.md v4.6 §2.4

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 非 project_owner 录入 real | `AUTH_500` | 403 | 仅项目负责人可录入实际消耗 |
| real_spend 为负数 | `BIZ_001` | 400 | 实际消耗不得为负 |
| 状态不允许录入 | `STATE_400` | 400 | 当前状态不允许录入实际消耗 |

#### 代码引用
- Service: `backend/services/daily_report_service.py`
- 方法: `submit_real_data()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | project_owner 录入 real | project_owner + real_spend=1000 | 成功 |
| T2 | pitcher 尝试录入 real | pitcher + real_spend | `AUTH_500` |
| T3 | 录入负数 real_spend | project_owner + real_spend=-100 | `BIZ_001` |
| T4 | 在 raw_submitted 状态录入 | 状态=raw_submitted | `STATE_400` |

---

### BR-RPT-008: final 数据提交者

#### 业务场景
final 数据（`conversions_final`）是甲方确认的有效进粉数，是计费的最终依据。项目负责人负责与甲方沟通确认，因此必须由其录入。

> **PRD v2.2 变更**: final 数据提交者由原 supervisor 变更为 project_owner

#### 详细约束
- ✅ **允许**: `project_owner` 录入 `conversions_final`
- ✅ **允许**: `admin` 录入 `conversions_final`（紧急情况）
- ❌ **禁止**: `pitcher` 录入 final 数据
- ❌ **禁止**: `finance` 录入 final 数据
- 📌 **强制**: conversions_final 必须小于等于 conversions_raw
- 📌 **强制**: 录入后触发状态变更为 `final_confirmed`

#### 前置条件
- 用户角色: `project_owner`（技术层: `users.is_project_owner=true`）
- 数据状态: 日报状态为 `final_pending`（Phase 2）或 `trend_ok`（Phase 1）
- 引用: AUTH_SPEC.md v2.2 §2.2, MASTER.md v4.6 §2.4

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 非 project_owner 录入 final | `AUTH_500` | 403 | 仅项目负责人可录入甲方确认进粉 |
| final > raw | `BIZ_001` | 400 | 甲方确认进粉不得大于上报进粉 |
| 状态不允许录入 | `STATE_400` | 400 | 当前状态不允许录入甲方确认 |

#### 代码引用
- Service: `backend/services/daily_report_service.py`
- 方法: `submit_final_data()`, `confirm_final()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | project_owner 录入 final | project_owner + conversions_final=90 | 成功，状态→final_confirmed |
| T2 | pitcher 尝试录入 final | pitcher + conversions_final | `AUTH_500` |
| T3 | final > raw | raw=100, final=110 | `BIZ_001` |
| T4 | 在 raw_submitted 状态录入 | 状态=raw_submitted | `STATE_400` |

---

### BR-RPT-009: final 数据不可改

#### 业务场景
final 数据是计费依据，一旦锁定不得修改，确保财务结算的准确性和不可篡改性。如需修正，必须通过红冲机制。

#### 详细约束
- ✅ **允许**: `final_confirmed` 状态下查看 final 数据
- ❌ **禁止**: `final_locked` 状态后修改 `conversions_final`
- ❌ **禁止**: 直接 UPDATE `conversions_final` 字段绕过状态机
- 📌 **强制**: 修正必须通过红冲机制（Phase 2）
- 📌 **强制**: 红冲必须提供 `ref_id` 和 `reason`

#### 前置条件
- 数据状态: 日报状态为 `final_locked`
- 引用: STATE_MACHINE.md v2.7 §7, LEDGER_SOT.md v1.2（红冲机制）

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 锁定后修改 final | `BIZ_001` | 400 | 已锁定数据不可修改 |
| 红冲缺少理由 | `BIZ_001` | 400 | 红冲必须提供理由 |

#### 代码引用
- Service: `backend/services/daily_report_service.py`
- 方法: `_check_locked_status()`, `create_reversal()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | final_confirmed 状态修改 | 状态=final_confirmed | 成功（允许修改） |
| T2 | final_locked 状态修改 | 状态=final_locked | `BIZ_001` |
| T3 | 红冲有理由 | ref_id + reason | 成功 |
| T4 | 红冲无理由 | ref_id only | `BIZ_001` |

---

## 规则依赖关系

```
BR-RPT-001 (提交人)
    ↓
BR-RPT-006 (raw 数据) ──→ BR-RPT-005 (三数据流)
    ↓
BR-RPT-004 (状态流转)
    ↓
BR-RPT-002 (审核人) ←── BR-RPT-003 (提交审核分离)
    ↓
BR-RPT-007 (real 数据) ──→ BR-RPT-005 (三数据流)
    ↓
BR-RPT-008 (final 数据) ──→ BR-RPT-005 (三数据流)
    ↓
BR-RPT-009 (final 不可改)
```

---

## 变更历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0 | 2025-12-27 | 初始版本，对齐 BUSINESS_RULES.md v4.6；BR-RPT-002/007/008 角色由 supervisor 变更为 project_owner（PRD v2.2） |

---

**文档性质**: 业务规则子模块
**执行级别**: 强制执行
**父文档**: BUSINESS_RULES.md v4.6
**关联 SoT**: STATE_MACHINE.md v2.7
**版本**: v1.0
