# BR-PROJ - 项目管理规则

> **文档版本**: v1.0
> **status**: active
> **owner**: wade
> **last_reviewed**: 2025-12-27
> **父文档**: BUSINESS_RULES.md v4.6
> **关联 SoT**: STATE_MACHINE.md v2.7 §5, DATA_SCHEMA.md v5.6 §3.2.1

---

## 互锁 SoT 引用

| SoT 文档 | 版本 | 引用章节 | 引用内容 |
|----------|------|----------|----------|
| BUSINESS_RULES.md | v4.6 | §4.3 | 规则索引定义 |
| STATE_MACHINE.md | v2.7 | §5, §4A.3 | 项目状态机（4 状态）、Phase 边界 |
| DATA_SCHEMA.md | v5.6 | §3.2.1 | projects 表结构、字段定义 |
| ERROR_CODES.md | v2.3 | §3-4 | 错误码映射 |
| AUTH_SPEC.md | v2.2 | §2.2, §3 | 角色权限 |
| MASTER.md | v4.6 | §2.4, §3 | 角色定义、Phase 边界 |

---

## 规则总览

| 规则ID | 规则名称 | 优先级 | 测试状态 |
|--------|----------|--------|----------|
| BR-PROJ-001 | 项目必须有负责人 | P0 | ✅ |
| BR-PROJ-002 | 结算模式不可变 | P0 | ✅ |
| BR-PROJ-003 | 状态流转合法性 | P0 | ✅ |
| BR-PROJ-004 | 归档不可逆 | P0 | ✅ |
| BR-PROJ-005 | 冷启动期定义 | P1 | 🟡 |
| BR-PROJ-006 | 预算必须大于零 | P0 | ✅ |
| BR-PROJ-007 | 单粉价格必须大于零 | P0 | ✅ |
| BR-PROJ-008 | 服务费率范围 | P0 | ✅ |

---

## 规则详细定义

### BR-PROJ-001: 项目必须有负责人

#### 业务场景
项目是广告投放的核心业务单元，每个项目必须有明确的负责人（project_owner）。项目负责人对项目盈亏负责，是日报审核、资金使用的第一责任人。

#### 详细约束
- 📌 **强制**: 每个项目必须关联一个 `owner_id`（project_owner）
- 📌 **强制**: `owner_id` 必须引用有效的用户（`users.id`）
- ❌ **禁止**: 创建无负责人的项目
- ❌ **禁止**: 将项目负责人设为 `pitcher` 角色
- ✅ **允许**: 项目负责人变更（需审计记录）

#### 前置条件
- 用户角色: `admin` 或 `ceo` 创建项目
- 数据状态: 指定的负责人用户状态为 active
- 引用: DATA_SCHEMA.md v5.6 §3.2.1, AUTH_SPEC.md v2.2 §2.2

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 缺少 owner_id | `BIZ_002` | 400 | 项目必须指定负责人 |
| 负责人不存在 | `BIZ_002` | 404 | 指定的负责人不存在 |
| 负责人角色无效 | `BIZ_001` | 400 | 负责人必须是 project_owner 角色 |

#### 代码引用
- Service: `backend/services/project_service.py`
- 方法: `create_project()`, `update_project_owner()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 创建有负责人的项目 | owner_id=有效用户 | 成功 |
| T2 | 创建无负责人的项目 | owner_id=null | `BIZ_002` |
| T3 | 负责人不存在 | owner_id=无效 ID | `BIZ_002` |
| T4 | pitcher 作为负责人 | owner_id=pitcher 用户 | `BIZ_001` |

---

### BR-PROJ-002: 结算模式不可变

#### 业务场景
项目的结算模式决定了收入计算方式，是合同的核心条款。一旦项目创建，结算模式不得修改，确保财务计算的一致性和合同的严肃性。

#### 详细约束
- 📌 **强制**: 项目创建时必须指定 `settlement_type`
- ❌ **禁止**: 项目创建后修改 `settlement_type`
- ❌ **禁止**: 修改已有日报的项目的结算模式
- ✅ **允许**: 归档项目后创建新项目使用不同结算模式

#### 结算模式枚举
| settlement_type | 业务名称 | 收入公式 | 说明 |
|-----------------|----------|----------|------|
| `fixed` | 按粉计费（per_lead） | `revenue = conversions_final × unit_price` | 使用 `projects.unit_price` |
| `tiered` | 阶梯计价 | 按 `settlement_rules` 配置 | 关联 `settlement_rules_id` |
| `markup` | 加成计价（fee_rate） | `revenue = ad_spend × (1 + markup_rate)` | 关联 `settlement_rules_id` |

#### 前置条件
- 数据状态: 项目已创建（`projects.id` 存在）
- 引用: DATA_SCHEMA.md v5.6 §3.2.1

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 修改结算模式 | `BIZ_001` | 400 | 项目结算模式不可修改 |
| 缺少结算模式 | `BIZ_001` | 400 | 项目必须指定结算模式 |
| 无效结算模式 | `BIZ_001` | 400 | 无效的结算模式 |

#### 代码引用
- Service: `backend/services/project_service.py`
- 方法: `create_project()`, `update_project()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 创建 fixed 模式项目 | settlement_type=fixed | 成功 |
| T2 | 修改已有项目结算模式 | UPDATE settlement_type | `BIZ_001` |
| T3 | 创建无结算模式项目 | settlement_type=null | `BIZ_001` |
| T4 | 使用无效结算模式 | settlement_type=invalid | `BIZ_001` |

---

### BR-PROJ-003: 状态流转合法性

#### 业务场景
项目状态机定义了项目从创建到归档的完整生命周期。所有状态变更必须遵循预定义的合法流转路径，确保项目管理的规范性和可追溯性。

#### 详细约束
- ✅ **允许**: 仅 STATE_MACHINE.md v2.7 §5 定义的合法流转
- ❌ **禁止**: 直接 UPDATE `projects.status` 字段
- ❌ **禁止**: 跳过中间状态
- 📌 **强制**: 状态变更必须通过业务动作触发
- 📌 **强制**: 终态 `archived` 不可回退

#### 前置条件
- 数据状态: 当前状态必须在合法流转表中
- 引用: STATE_MACHINE.md v2.7 §5

#### 项目状态机（4 状态）
```
draft → active → suspended → archived
      ↘        ↗           ↗
```

| 当前状态 | 目标状态 | 触发动作 | 允许角色 |
|----------|----------|----------|----------|
| - | `draft` | 创建项目 | admin, ceo |
| `draft` | `active` | 激活项目 | admin, account_manager |
| `draft` | `suspended` | 暂停项目 | admin |
| `draft` | `archived` | 归档项目 | admin |
| `active` | `suspended` | 暂停项目 | admin, account_manager |
| `active` | `archived` | 归档项目 | admin |
| `suspended` | `active` | 恢复项目 | admin, account_manager |
| `suspended` | `archived` | 归档项目 | admin |

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 非法状态流转 | `STATE_400` | 400 | 不允许从 {from} 转换到 {to} |
| 终态回退 | `STATE_402` | 400 | 终态不可回退 |

#### 代码引用
- Service: `backend/services/project_service.py`
- 方法: `_validate_status_transition()`, `activate_project()`, `suspend_project()`, `archive_project()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 合法流转 draft → active | 有效状态转换 | 成功 |
| T2 | 非法流转 draft → archived（跳过） | 非合法路径 | 成功（draft 允许直接归档） |
| T3 | 终态回退 archived → active | 回退终态 | `STATE_402` |
| T4 | suspended → active | 恢复项目 | 成功 |

---

### BR-PROJ-004: 归档不可逆

#### 业务场景
项目归档是项目生命周期的终点。归档后的项目数据用于历史查询和审计，不得再进行任何业务操作，确保数据的完整性和不可篡改性。

#### 详细约束
- ✅ **允许**: `archived` 状态下查看项目数据
- ❌ **禁止**: `archived` 状态后修改项目信息
- ❌ **禁止**: `archived` 状态后回退到其他状态
- ❌ **禁止**: 归档项目进行充值、日报等操作
- 📌 **强制**: 如需继续业务，必须创建新项目

#### 前置条件
- 数据状态: 项目状态为 `archived`
- 引用: STATE_MACHINE.md v2.7 §14.2

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 归档后修改 | `BIZ_001` | 400 | 已归档项目不可修改 |
| 归档后回退 | `STATE_402` | 400 | 终态不可回退 |
| 归档项目充值 | `STATE_400` | 400 | 已归档项目不可充值 |
| 归档项目提交日报 | `STATE_400` | 400 | 已归档项目不可提交日报 |

#### 代码引用
- Service: `backend/services/project_service.py`
- 方法: `_check_archived_status()`, `update_project()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 查看归档项目 | status=archived, GET | 成功 |
| T2 | 修改归档项目 | status=archived, UPDATE | `BIZ_001` |
| T3 | 归档项目回退 | archived → active | `STATE_402` |
| T4 | 归档项目充值 | status=archived, 充值 | `STATE_400` |

---

### BR-PROJ-005: 冷启动期定义

#### 业务场景
新项目上线初期数据波动较大，不适合进行严格的趋势风控。冷启动期内系统对异常数据采取宽容策略，仅记录不阻断。

#### 详细约束
- 📌 **强制**: 新项目上线前 7 天为冷启动期
- 📌 **强制**: 冷启动期从项目 `active` 状态开始计算
- ✅ **允许**: 冷启动期内趋势异常仅记录不阻断（Phase 1 行为）
- ✅ **允许**: 冷启动期后启用完整趋势风控（Phase 2）
- 📌 **强制**: 冷启动期天数通过系统配置 `COLD_START_DAYS` 设定

#### 前置条件
- 数据状态: 项目状态为 `active`
- 引用: STATE_MACHINE.md v2.7 §4A.3

#### Phase 边界
| Phase | 冷启动期行为 |
|-------|--------------|
| Phase 1 | 所有项目均为宽容模式（与冷启动期行为一致） |
| Phase 2 | 冷启动期后启用完整风控规则 |

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| - | - | - | 冷启动期无阻断错误 |

#### 代码引用
- Service: `backend/services/daily_report_service.py`
- 方法: `_is_in_cold_start_period()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 冷启动期内异常 | 激活后第 3 天，异常数据 | 记录但不阻断 |
| T2 | 冷启动期后异常 | 激活后第 10 天，异常数据 | Phase 2: 触发风控 |
| T3 | 冷启动期判断 | 激活后第 7 天 | 仍在冷启动期 |
| T4 | 冷启动期结束 | 激活后第 8 天 | 冷启动期结束 |

---

### BR-PROJ-006: 预算必须大于零

#### 业务场景
项目预算是资金管控的基础。有效的预算必须为正数，用于预算预警和超额控制（Phase 2）。

#### 详细约束
- 📌 **强制**: `budget_total` 必须大于 0
- ❌ **禁止**: 预算为零或负数
- ✅ **允许**: 预算在项目激活后调整（需审计）
- 📌 **强制**: 预算精度为 DECIMAL(15,2)
- 📌 **强制**: 预算货币默认为 CNY

#### 前置条件
- 数据状态: 项目创建或更新时
- 引用: DATA_SCHEMA.md v5.6 §3.2.1

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 预算为零 | `BIZ_100` | 400 | 项目预算必须大于零 |
| 预算为负 | `BIZ_100` | 400 | 项目预算不得为负数 |

#### 代码引用
- Service: `backend/services/project_service.py`
- 方法: `_validate_budget()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 正数预算 | budget_total=100000 | 成功 |
| T2 | 零预算 | budget_total=0 | `BIZ_100` |
| T3 | 负数预算 | budget_total=-1000 | `BIZ_100` |
| T4 | 预算调整 | budget_total: 100000 → 150000 | 成功 |

---

### BR-PROJ-007: 单粉价格必须大于零

#### 业务场景
单粉价格（unit_price）是按粉计费模式的核心参数，决定了项目收入计算。有效的单粉价格必须为正数。

#### 详细约束
- 📌 **强制**: `settlement_type=fixed` 时，`unit_price` 必须大于 0
- ✅ **允许**: `settlement_type=tiered/markup` 时，`unit_price` 可为 0（使用 settlement_rules）
- ❌ **禁止**: fixed 模式下单粉价格为零或负数
- 📌 **强制**: 单粉价格精度为 DECIMAL(15,2)

#### 收入公式
```
revenue = conversions_final × unit_price
```

#### 前置条件
- 数据状态: 项目 `settlement_type=fixed`
- 引用: DATA_SCHEMA.md v5.6 §3.2.1, BR-PROFIT-001

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| fixed 模式单价为零 | `BIZ_100` | 400 | 按粉计费模式单价必须大于零 |
| 单价为负 | `BIZ_100` | 400 | 单粉价格不得为负数 |

#### 代码引用
- Service: `backend/services/project_service.py`
- 方法: `_validate_unit_price()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | fixed 模式正数单价 | settlement_type=fixed, unit_price=50 | 成功 |
| T2 | fixed 模式零单价 | settlement_type=fixed, unit_price=0 | `BIZ_100` |
| T3 | tiered 模式零单价 | settlement_type=tiered, unit_price=0 | 成功 |
| T4 | 负数单价 | unit_price=-10 | `BIZ_100` |

---

### BR-PROJ-008: 服务费率范围

#### 业务场景
服务费率（fee_rate/markup_rate）是加成计价模式的核心参数。费率必须在合理范围内（0-100%），确保业务可行性。

#### 详细约束
- 📌 **强制**: `settlement_type=markup` 时，费率必须在 0-100% 之间
- ❌ **禁止**: 费率为负数
- ❌ **禁止**: 费率超过 100%
- 📌 **强制**: 费率通过 `settlement_rules` 配置
- ✅ **允许**: 费率为 0（纯成本模式，Phase 2）

#### 收入公式（markup 模式）
```
revenue = ad_spend × (1 + markup_rate)
```
其中 `markup_rate` 来自 `settlement_rules.config`

#### 前置条件
- 数据状态: 项目 `settlement_type=markup`
- 引用: DATA_SCHEMA.md v5.6 §3.5.7

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 费率为负 | `BIZ_100` | 400 | 服务费率不得为负数 |
| 费率超 100% | `BIZ_100` | 400 | 服务费率不得超过 100% |

#### 代码引用
- Service: `backend/services/project_service.py`
- 方法: `_validate_fee_rate()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 正常费率 | markup_rate=0.15 (15%) | 成功 |
| T2 | 零费率 | markup_rate=0 | 成功（纯成本模式） |
| T3 | 负数费率 | markup_rate=-0.1 | `BIZ_100` |
| T4 | 超限费率 | markup_rate=1.5 (150%) | `BIZ_100` |

---

## 规则依赖关系

```
BR-PROJ-001 (必须有负责人)
    ↓
BR-PROJ-002 (结算模式不可变) ←── BR-PROJ-007 (单粉价格)
    │                         ←── BR-PROJ-008 (服务费率)
    ↓
BR-PROJ-006 (预算大于零)
    ↓
BR-PROJ-003 (状态流转) ←── BR-PROJ-005 (冷启动期)
    ↓
BR-PROJ-004 (归档不可逆)
```

---

## 项目生命周期

```
┌─────────┐      激活       ┌─────────┐      暂停       ┌───────────┐
│  draft  │ ──────────────→ │  active │ ──────────────→ │ suspended │
│ (草稿)  │                 │ (激活)  │ ←────────────── │  (暂停)   │
└────┬────┘                 └────┬────┘      恢复       └─────┬─────┘
     │                           │                            │
     │         归档              │          归档              │
     └───────────────────────────┴────────────────────────────┘
                                 ↓
                          ┌──────────┐
                          │ archived │
                          │  (归档)  │
                          └──────────┘
                             终态
```

---

## 变更历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0 | 2025-12-27 | 初始版本，对齐 BUSINESS_RULES.md v4.6；所有错误码对齐 ERROR_CODES.md v2.3；settlement_type 对齐 DATA_SCHEMA.md v5.6 |

---

**文档性质**: 业务规则子模块
**执行级别**: 强制执行
**父文档**: BUSINESS_RULES.md v4.6
**关联 SoT**: STATE_MACHINE.md v2.7 §5, DATA_SCHEMA.md v5.6 §3.2.1
**版本**: v1.0
