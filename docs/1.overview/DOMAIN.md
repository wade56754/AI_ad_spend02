# DOMAIN.md - AI 广告代投系统领域索引

> **文档性质**: 领域索引与 SoT 导航
> **约束级别**: 项目级，作为开发者查阅 SoT 的入口
> **版本**: v1.0
> **status**: frozen
> **基准**: MASTER.md v3.4, PROJECT.md v1.2
> **owner**: wade
> **last_reviewed**: 2025-11-27

---

## 第一章 文档定位与约束

### 1.1 本文档职责

DOMAIN.md 是 SoT 体系的导航入口，职责如下：

- 定义领域边界与归属
- 索引所有 SoT 文档
- 指导开发者「先查哪份文档」
- 建立实体与规则的映射关系

> 引用: MASTER.md 第九章 文档索引

### 1.2 本文档不做

本文档不承担以下职责：

- 不定义业务规则正文（属于 BUSINESS_RULES.md）
- 不定义数据结构（属于 DATA_SCHEMA.md）
- 不定义状态机（属于 STATE_MACHINE.md）
- 不定义 API 接口（属于 API_SOT.md）
- 不定义账本公式（属于 LEDGER_SOT.md）

### 1.3 使用场景

| 场景 | 动作 |
|-----|------|
| 不知道该查哪份 SoT | 查阅第三章 SoT 导航索引 |
| 想了解某实体属于哪个领域 | 查阅第四章 领域实体清单 |
| 想查某能力涉及哪些规则 | 查阅第五章 领域规则索引 |
| 想确认跨域调用是否合法 | 查阅第六章 跨域依赖约束 |

---

## 第二章 领域边界定义

### 2.1 核心领域

本系统包含以下核心领域：

| 领域 | 职责 | 主 SoT |
|-----|------|-------|
| 日报领域 | 投放数据采集与状态流转 | DAILY_REPORT_SOT.md, STATE_MACHINE.md |
| 账本领域 | 收入与成本记录 | LEDGER_SOT.md |
| 对账领域 | 账务核对与修正 | RECONCILIATION_SOT.md |

### 2.2 支撑领域

| 领域 | 职责 | 主 SoT |
|-----|------|-------|
| 项目领域 | 项目与单价管理 | DATA_SCHEMA.md (projects) |
| 供应商领域 | 供应商与费率管理 | DATA_SCHEMA.md (suppliers) |
| 账户领域 | 广告账户生命周期 | STATE_MACHINE.md §7 |
| 认证领域 | 用户与角色权限 | AUTH_SPEC.md |

### 2.3 领域边界约束

- 日报领域是账本领域的唯一数据来源
- 账本领域不可直接接收外部数据
- 对账领域只能通过红冲修正账本

> 引用: MASTER.md BI-04「账务必须源于日报」

---

## 第三章 SoT 导航索引

### 3.1 按优先级索引

```
0. MASTER.md                → 架构宪法，最高优先级
1. STATE_MACHINE.md         → 状态定义与转换
2. DATA_SCHEMA.md           → 表结构与字段
3. LEDGER_SOT.md            → 账本规则
4. BUSINESS_RULES.md        → 业务规则
5. API_SOT.md               → API 定义
6. ERROR_CODES_SOT.md       → 错误码
7. AUTH_SPEC.md             → 认证授权
8. DAILY_REPORT_SOT.md      → 日报规则
9. RECONCILIATION_SOT.md    → 对账规则
10. TRANSFER_SOT.md         → 转账规则
```

> 引用: MASTER.md 第六章 SoT 裁判链

### 3.2 按领域索引

| 领域 | 首选 SoT | 次选 SoT |
|-----|---------|---------|
| 日报 | STATE_MACHINE.md §8 | DAILY_REPORT_SOT.md |
| 账本 | LEDGER_SOT.md | MASTER.md INV-001 |
| 对账 | RECONCILIATION_SOT.md | LEDGER_SOT.md §3 |
| 项目 | DATA_SCHEMA.md (projects) | BUSINESS_RULES.md BR-PROJ |
| 账户 | STATE_MACHINE.md §7 | DATA_SCHEMA.md (ad_accounts) |
| 权限 | AUTH_SPEC.md | RLS_POLICIES_SOT.md |
| API | API_SOT.md | ERROR_CODES_SOT.md |

### 3.3 查阅决策树

```
开发新功能？
├─ 涉及状态变更 → STATE_MACHINE.md
├─ 涉及数据库字段 → DATA_SCHEMA.md
├─ 涉及账本操作 → LEDGER_SOT.md
├─ 涉及权限控制 → AUTH_SPEC.md
├─ 涉及 API 设计 → API_SOT.md
└─ 涉及错误处理 → ERROR_CODES_SOT.md

修复 Bug？
├─ 状态流转错误 → STATE_MACHINE.md
├─ 金额计算错误 → LEDGER_SOT.md INV-001
├─ 权限拒绝错误 → AUTH_SPEC.md + RLS_POLICIES_SOT.md
└─ 业务规则违反 → BUSINESS_RULES.md
```

---

## 第四章 领域实体清单

### 4.1 核心实体

| 实体 | 所属领域 | 定义来源 |
|-----|---------|---------|
| daily_reports | 日报领域 | DATA_SCHEMA.md, STATE_MACHINE.md §8 |
| ledger_entries | 账本领域 | DATA_SCHEMA.md, LEDGER_SOT.md |
| projects | 项目领域 | DATA_SCHEMA.md |
| suppliers | 供应商领域 | DATA_SCHEMA.md |
| ad_accounts | 账户领域 | DATA_SCHEMA.md, STATE_MACHINE.md §7 |
| users | 认证领域 | DATA_SCHEMA.md, AUTH_SPEC.md |

### 4.2 实体归属

```
日报领域
├─ daily_reports        (核心聚合根)
└─ daily_report_history (审计日志)

账本领域
├─ ledger_entries       (核心聚合根)
└─ balance_snapshots    (余额快照) *

> *注：该表将作为未来版本（DATA_SCHEMA v5.3）加入正式 SoT，目前为规划中的领域对象。

项目领域
├─ projects             (核心聚合根)
└─ project_members      (关联)

供应商领域
├─ suppliers            (核心聚合根)
└─ supplier_accounts    (关联)

账户领域
├─ ad_accounts          (核心聚合根)
├─ account_alerts       (预警)
└─ account_status_history (状态历史)

认证领域
├─ users                (核心聚合根)
├─ roles                (角色)
└─ permissions          (权限)
```

> 引用: DATA_SCHEMA.md v5.2

---

## 第五章 领域规则索引

### 5.1 按业务能力索引

| 能力 | 相关规则 | 来源 |
|-----|---------|------|
| C-01 日报提交 | BR-RPT-001, BR-RPT-002 | BUSINESS_RULES.md |
| C-02 趋势风控 | BR-TREND-001, BR-TREND-002 | BUSINESS_RULES.md |
| C-03 日报确认 | BR-RPT-003, BR-RPT-004 | BUSINESS_RULES.md |
| C-04 账务生成 | INV-001 | MASTER.md, LEDGER_SOT.md |
| C-05 红冲修正 | INV-003 红冲机制 | MASTER.md, LEDGER_SOT.md §3 |
| C-06 死号迁移 | BI-02 | MASTER.md, TRANSFER_SOT.md |

> 引用: PROJECT.md 第三章 业务能力

### 5.2 按实体索引

| 实体 | 状态机规则 | 业务规则 | 账本规则 |
|-----|-----------|---------|---------|
| daily_reports | STATE_MACHINE.md §8 | BR-RPT-* | LEDGER_SOT.md §4 |
| ledger_entries | - | - | LEDGER_SOT.md §2-3 |
| projects | STATE_MACHINE.md §5 | BR-PROJ-* | LEDGER_SOT.md INV-001 |
| ad_accounts | STATE_MACHINE.md §7 | BR-ACCT-* | - |
| users | - | BR-AUTH-*, BR-USER-* | - |

---

## 第六章 跨域依赖约束

### 6.1 依赖方向约束

```
认证领域 ← 所有领域（权限校验）

日报领域 → 账本领域（触发账务生成）
日报领域 → 项目领域（读取 unit_price）
日报领域 → 供应商领域（读取 fee_rate）
日报领域 → 账户领域（读取账户状态）

对账领域 → 账本领域（执行红冲）
对账领域 → 日报领域（标记 reversal_id）
```

### 6.2 禁止的依赖

| 禁止方向 | 原因 | 引用 |
|---------|------|------|
| 账本领域 → 外部数据 | 账务必须源于日报 | MASTER.md BI-04 |
| 任意领域 → 终态数据直接修改 | 终态不可逆 | MASTER.md INV-003 |
| 日报领域 ← 账本领域 | 账本不可反推日报 | MASTER.md INV-002 |
| 跨角色越权操作 | 职责分离 | MASTER.md INV-004 |

> 引用: MASTER.md 第四章 永久禁止行为

---

## 附录 A: 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2025-11-25 | 初始版本 | AI Doc Orchestrator |

---

**文档版本**: v1.0
**最后更新**: 2025-11-25
**对齐文档**: MASTER.md v3.4, PROJECT.md v1.2
**维护者**: 系统架构师
