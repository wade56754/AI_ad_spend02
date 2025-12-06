# MASTER.md - AI 广告代投系统架构宪法

> **文档性质**: 系统唯一入口，所有代码实现的最高裁决依据
> **约束级别**: 强制执行，违反本文档定义的不变量视为 P0 缺陷
> **裁判优先级**: 本文档 > 所有 SoT 文档 > 所有开发指南
> **版本**: v3.6
> **status**: frozen
> **基准**: SoT Freeze v2.6, Dev-Guides Freeze vFinal, Architecture Freeze v1.0, Infrastructure Freeze v1.0, Agent Layer Freeze v1.0, PROJECT.md v1.2, OpenSpec v1.0
> **owner**: wade
> **last_reviewed**: 2025-12-01

---

## 术语定义

| 术语 | 定义 |
|------|------|
| 终态 | `final_locked` 状态，数据冻结，不可逆转 |
| 红冲 | REVERSAL，通过反向账务事件修正错误，不修改历史 |
| 镜像记录 | 同一业务事件在 PROJECT 与 SUPPLIER 账本各产生一笔记录 |
| 业务不可变量 | 无论系统如何演进，永远为真的业务事实 |
| Freeze | 治理机制，禁止在冻结期间修改受保护内容 |

---

## 第一章 系统哲学

### 1.1 业务问题

AI 广告代投系统管理三方资金流转：
- **客户** → 充值至项目账户 → 按粉数计费扣款
- **平台** → 管理项目账本（收入侧）与供应商账本（成本侧）
- **供应商** → 接收充值 → 按真实消耗扣款

### 1.2 核心风险

| 风险类型 | 风险描述 | 后果 |
|---------|---------|------|
| 数据篡改 | 投手虚报粉数 | 虚增收入 |
| 账务混乱 | 收入与成本混记 | 无法对账 |
| 审计断裂 | 直接修改已锁定数据 | 审计链不可追溯 |

### 1.3 解决方案

本系统通过以下五大机制防止风险：

**1. 双账本架构 (Dual-Ledger)**
- PROJECT 账本：仅记录收入（客户充值、粉数计费）
- SUPPLIER 账本：仅记录成本（供应商充值、真实消耗）
- 禁止混合：任何角色不得在单一账本中同时记录收入与成本

**2. 三数据流分离 (Triple-Stream)**
- Raw 数据流：投手提交，用于趋势风控，永不计费/计成本
- Real 数据流：运营录入，用于成本核算
- Final 数据流：运营确认，用于计费
- 禁止反向：程序禁止从 final 反推 raw

**3. 8 状态机强制流转 (State Machine)**
- 每个状态对应唯一权限边界
- 终态 `final_locked` 后数据冻结
- 禁止逆转：任何角色不得绕过状态机直接修改

**4. 审计不可逆 (Immutable Audit Trail)**
- 账本余额 = SUM(所有 ledger_entries.amount)
- 禁止 UPDATE 任何 ledger_entries 记录
- 禁止 DELETE 任何 ledger_entries 记录
- 修正唯一方式：REVERSAL（红冲），产生反向事件
- 数学不变量：`净值 = SUM(原事件) + SUM(REVERSAL事件)`

**5. 职责分离 (Separation of Duties)**
- 投手：仅可提交 raw 数据
- 运营：仅可录入 real/final 数据
- 财务：仅可执行 REVERSAL/TRANSFER
- 禁止越权：任何角色不得修改上游数据

---

## 第二章 系统不可变量

### INV-001: 双账本独立核算

**PROJECT 账本** (收入侧)

计费公式：
```
revenue = conversions_final × projects.unit_price
```
- `conversions_final` 来源: `daily_reports.conversions_final`
- `unit_price` 来源: `projects.unit_price`（`final_locked` 后冻结）

计费触发条件：
- 状态流转至终态
- `conversions_final > 0`

计费账本记录：
- `ledger_entries.type = REVENUE`
- `ledger_entries.category = PROJECT`
- `ledger_entries.amount = +revenue`（正值，增加余额）

充值：客户充值时创建账本记录：
- `ledger_entries.type = RECHARGE`
- `ledger_entries.category = PROJECT`
- `ledger_entries.amount = +充值金额`

**SUPPLIER 账本** (成本侧)

成本公式：
```
cost = real_spend × (1 + suppliers.fee_rate)
```
- `real_spend` 来源: `daily_reports.real_spend`
- `fee_rate` 来源: `suppliers.fee_rate`

成本触发条件：
- 状态流转至终态
- `real_spend > 0`

成本账本记录：
- `ledger_entries.type = COST`
- `ledger_entries.category = SUPPLIER`
- `ledger_entries.amount = -cost`（负值，扣减余额）

充值：财务充值时创建账本记录：
- `ledger_entries.type = RECHARGE`
- `ledger_entries.category = SUPPLIER`
- `ledger_entries.amount = +充值金额`

**余额计算公式（唯一）**
```
projects.balance = SUM(ledger_entries.amount) WHERE category = 'PROJECT'
suppliers.balance = SUM(ledger_entries.amount) WHERE category = 'SUPPLIER'
```

**日报计费/计成本触发规则**

终态触发时，分别判断：
- 若 `conversions_final > 0`：产生 `type = REVENUE, category = PROJECT`
- 若 `real_spend > 0`：产生 `type = COST, category = SUPPLIER`
- 两笔记录引用同一 `daily_report_id`（若两者皆触发）
- 若两者皆为零：不产生任何账本记录，禁止流转至终态

**账本隔离约束**
- 禁止在 PROJECT 账本记录 COST 类型
- 禁止在 SUPPLIER 账本记录 REVENUE 类型
- 禁止跨 category 进行余额聚合查询

**来源**: `LEDGER_SOT.md` v1.1

---

### INV-002: 三数据流职责分离

**数据流定义**

| 数据流 | 字段 | 录入角色 | 用途 | 计费/计成本 | 冻结时机 |
|--------|------|----------|------|-------------|----------|
| Raw | `conversions_raw`, `raw_spend` | 投手 | 趋势风控 | 永不参与 | `trend_ok` 后冻结 |
| Real | `real_spend` | 运营 | 成本核算 | 仅计成本 | `final_locked` 后冻结 |
| Final | `conversions_final` | 运营 | 计费 | 仅计收入 | `final_locked` 后冻结 |

**单向流动约束**
- 允许：运营人工参考 raw 数据录入 real 数据
- 允许：运营人工参考 real 数据确认 final 数据
- 禁止：程序自动从 final 反推 raw
- 禁止：程序自动从 real 反推 raw

**计费/计成本约束**
- 禁止使用 `conversions_raw` 计费
- 禁止使用 `raw_spend` 计成本
- 禁止在 `state < final_confirmed` 时触发计费
- 禁止在 `state < final_pending` 时触发计成本
- 禁止 `conversions_final = 0` 时触发计费
- 禁止 `real_spend = 0` 时触发计成本

**来源**: `DAILY_REPORT_SOT.md` v1.0

---

### INV-003: 8 状态机强制流转

**状态机哲学**
- 状态 = 权限边界
- 状态 = 账务触发条件
- 状态 = 审计锚点

**标准流转路径**
```
null → raw_submitted → trend_pending → trend_ok → final_pending
     → final_confirmed → final_locked
```

**异常流转路径**
```
trend_pending → trend_flagged → trend_resolved → final_pending
```

**前置条件与触发规则**

| 目标状态 | 前置状态 | 必要条件 | 触发者 |
|---------|---------|---------|--------|
| `raw_submitted` | `null` | `conversions_raw IS NOT NULL AND raw_spend IS NOT NULL` | 投手 |
| `trend_pending` | `raw_submitted` | 无 | 系统 |
| `trend_ok` | `trend_pending` | 趋势检查通过（参见 BUSINESS_RULES.md BR-TREND-001） | 系统 |
| `trend_flagged` | `trend_pending` | 趋势检查异常（参见 BUSINESS_RULES.md BR-TREND-002） | 系统 |
| `trend_resolved` | `trend_flagged` | 人工审核通过 | 运营 |
| `final_pending` | `trend_ok` 或 `trend_resolved` | 无 | 系统 |
| `final_confirmed` | `final_pending` | `conversions_final IS NOT NULL AND real_spend IS NOT NULL` | 运营 |
| `final_locked` | `final_confirmed` | `conversions_final > 0 OR real_spend > 0` | 系统（触发计费/计成本） |

**禁止的状态转换**
- 禁止 `trend_flagged` → `final_pending`（必须经过 `trend_resolved`）
- 禁止 `raw_submitted` → `final_pending`（必须经过趋势检查）
- 禁止 `final_locked` → 任何其他状态（终态不可逆）
- 禁止任何状态 → `null`（禁止重置）

**终态保护**

终态后，以下字段冻结：
- `daily_reports.conversions_final`
- `daily_reports.real_spend`
- `daily_reports.conversions_raw`
- `projects.unit_price`（关联项目）
- `suppliers.fee_rate`（关联供应商）

**修正机制（红冲）**

触发条件：发现终态日报数据错误

执行角色：财务（FINANCE）

执行约束：
- 必须提供外部审批单号（`approval_ref`，非空、不可重复）
- 必须全额红冲（不允许部分红冲）
- 必须同时红冲两个账本（若原日报同时产生了两笔记录）

执行步骤：
1. 若原日报产生了 REVENUE 记录：创建 `ledger_entries.type = REVERSAL, category = PROJECT, amount = -revenue`
2. 若原日报产生了 COST 记录：创建 `ledger_entries.type = REVERSAL, category = SUPPLIER, amount = +cost`
3. 更新 `daily_reports.reversal_id`
4. 保持 `daily_reports.state = final_locked`（状态不变）
5. 如需重新计费，创建新 `daily_report` 记录

**红冲符号约束**
- REVENUE 红冲：`amount = -revenue`（负值，抵消原正值）
- COST 红冲：`amount = +cost`（正值，抵消原负值）
- 数学验证：`原 REVENUE + REVERSAL = 0`，`原 COST + REVERSAL = 0`

**红冲禁止条款**
- 禁止对 REVERSAL 记录再次执行 REVERSAL
- 禁止删除 REVERSAL 记录
- 禁止修改 REVERSAL 记录

**来源**: `STATE_MACHINE.md` v2.6

---

### INV-004: 职责分离

**角色权限矩阵**

| 角色 | 允许操作 | 禁止操作 |
|------|---------|---------|
| 投手 (AD_OPERATOR) | 创建日报、填写 raw 数据、提交至 `raw_submitted` | 修改 final/real 数据、修改状态至 final_*、查看他人日报 |
| 运营 (OPERATIONS) | 录入 real_spend、确认 conversions_final、审核 trend_flagged | 修改 raw 数据、修改状态至 raw_submitted、删除日报 |
| 财务 (FINANCE) | 执行 REVERSAL、执行 TRANSFER、查看账本、导出报表 | 修改日报任何字段、修改日报状态、删除账本记录 |
| 管理员 (ADMIN) | 查看所有数据、导出审计报表、配置系统参数 | 绕过状态机、删除 final_locked 记录、执行 REVERSAL |

**跨角色约束**
- 禁止单一用户同时拥有 AD_OPERATOR 和 OPERATIONS 角色
- 禁止单一用户同时拥有 OPERATIONS 和 FINANCE 角色
- 财务执行 REVERSAL 必须提供外部审批单号

**权限边界强制执行**
- 禁止投手修改 `conversions_final`
- 禁止运营修改 `conversions_raw`
- 禁止财务修改 `daily_reports.state`
- 禁止任何角色在终态后直接 UPDATE 日报

**越权 = 合规违规 = 账务风险**

**来源**: `AUTH_SPEC.md` v2.0, `RLS_POLICIES_SOT.md` v1.0

---

## 第三章 业务不可变量 (Business Invariants)

业务不可变量来源于 PROJECT.md v1.2，作为系统级约束强制执行。

### BI-01 账务记录不可篡改

已锁定（final_locked）的账务记录：
- 不可修改金额
- 不可修改归属
- 不可删除

错误修正唯一方式：红冲（REVERSAL）。

**映射**: INV-001「审计不可逆」

---

### BI-02 广告账户生命周期不可回溯

广告账户状态变化是单向的：
- 正常 → 受限 → 死号
- 死号永远是死号

死号业务可迁移至新账户，原账户不可复活。

**映射**: STATE_MACHINE.md §7.1

---

### BI-03 收益归属不可重分配

投手已确认的收益归属：
- 不因事后协商而改变
- 不因团队调整而转移
- 不因项目变更而重算

对账错误唯一修正方式：红冲后重新归属。

**映射**: BUSINESS_RULES.md BR-RPT-005

---

### BI-04 账务必须源于日报

账务记录的唯一合法来源是已锁定（final_locked）的日报。

以下不能直接成为账务：
- Excel 导入数据
- 截图或口头描述
- 第三方平台打款通知

**映射**: DAILY_REPORT_SOT.md §1, INV-001

---

### BI-05 角色职责不可越界

每个角色只能操作其职责范围内的业务对象。
职责边界由 INV-004 定义，不可局部覆盖。

**映射**: INV-004, AUTH_SPEC.md §5

---

## 第四章 永久禁止行为 (Prohibited)

本章定义业务宇宙维度的禁止行为，不因版本迭代而改变。
违反任一条 = 合规违规 = 审计风险。

### D-01 手动改写账务历史

禁止：
- 修改已有 LedgerEntry
- 人工覆盖账务
- 删除账务记录

**映射**: INV-001, BI-01

---

### D-02 跳过日报直入账本

禁止：
- 绕过 DailyReport 直接写 Ledger
- Excel 导入自动生成 entry

**映射**: BI-04

---

### D-03 将死号标记为恢复

禁止：
- 关闭迁移流程直接复用原账号
- 直接在原账号上继续业务

**映射**: BI-02

---

### D-04 未审计数据做决策

禁止：
- 根据截图/口头信息修改收益
- 用非系统数据触发结算

**映射**: INV-002

---

### D-05 事后重分配收益

禁止：
- 项目层面强制改投手收益
- 事后佣金策略修订影响历史记录

**映射**: BI-03

---

### D-06 业务试验进入正式账本

禁止：
- A/B 实验直接写 final ledger
- 非生产数据进入结算闭环

**映射**: INV-003「终态保护」

---

## 第五章 Freeze 机制

Freeze 是治理机制，不是建议。

### FZ-01 文档冻结

当 PROJECT.md 与 MASTER.md 同步锁定版本后：
- 任何新增目标/业务范围变更 = 新版本
- 禁止在当前版本中追加业务能力

---

### FZ-02 开发冻结

当 ARCHITECTURE.md / DOMAIN.md 进入版本合并阶段：
- 禁止删除功能
- 禁止扩大范围
- 禁止引入新业务逻辑

解冻条件：新 STATE_MACHINE vX.Y 正式发布。

---

### FZ-03 发布冻结

当部署进入生产候补阶段：
- 仅允许 BUGFIX
- 禁止新增功能
- 禁止指标增强
- 禁止策略实验

---

## 第五章附录 规范变更管理 (OpenSpec)

### OS-01 OpenSpec 唯一变更通道

涉及以下内容的变更，**必须**先通过 OpenSpec change 流程（PROPOSE → IMPLEMENT → ARCHIVE）：

| 变更类型 | 示例 | 必须走 OpenSpec |
|---------|------|-----------------|
| 状态机修改 | 新增状态、修改流转规则 | ✅ 强制 |
| 错误码变更 | 新增/修改错误码定义 | ✅ 强制 |
| 账本规则变更 | 分录类型、余额计算公式 | ✅ 强制 |
| API 契约变更 | 新增端点、修改请求/响应格式 | ✅ 强制 |
| 数据库结构变更 | 新增/修改表、字段、约束 | ✅ 强制 |
| 业务规则变更 | 新增/修改 BR-* 规则 | ✅ 强制 |
| Bug 修复 | 恢复到既有 spec 行为 | ❌ 可跳过 |
| 文档 typo | 拼写错误、格式调整 | ❌ 可跳过 |
| 依赖更新 | 非破坏性版本升级 | ❌ 可跳过 |

### OS-02 SoT 投影与禁止直接编辑

**禁止操作**：
- ❌ 直接编辑 `openspec/specs/` 目录下的任何文件
- ❌ 在 commit 中不包含 change-id 而修改 SoT 文档

**强制路径**：
1. 创建 OpenSpec change（`openspec/changes/<change-id>/`）
2. 编写 spec deltas（使用 `## ADDED|MODIFIED|REMOVED Requirements`）
3. 验证通过（`openspec validate <change-id> --strict`）
4. 获得审批后实施
5. 归档变更（`openspec archive <change-id>`）→ 自动更新 `openspec/specs/`

### OS-03 裁判链与 OpenSpec 对齐

OpenSpec 的 spec deltas 必须与 SoT 裁判链保持一致：

```
MASTER.md (本文档) > STATE_MACHINE.md > DATA_SCHEMA.md > API_SOT.md
> ERROR_CODES_SOT.md > BUSINESS_RULES.md > AUTH_SPEC.md > LEDGER_SOT.md
```

**约束**：
- OpenSpec change 不得违反高优先级文档的定义
- 若需修改高优先级文档，必须同时更新所有受影响的下游文档
- 冲突解决：以裁判链高优先级文档为准

### OS-04 变更追溯要求

**每次 SoT 变更必须包含**：
- `change-id`：OpenSpec 变更标识（如 `add-topup-v2`）
- `affected_specs`：受影响的 SoT 文档列表
- `commit message`：包含 `[change-id]` 标记

**违规检测**：
- 发现直接修改 SoT 且 commit 中无 change-id → 视为违规变更
- 违规变更将被 revert，需重新走 OpenSpec 流程

---

## 第六章 SoT 裁判链

当多份文档对同一概念有不同定义时，按以下优先级解决冲突：

```
0. MASTER.md (本文档)           → 架构宪法，最高优先级
1. STATE_MACHINE.md            → 状态定义与转换
2. DATA_SCHEMA.md              → 表结构与字段
3. LEDGER_SOT.md               → 账本规则
4. BUSINESS_RULES.md           → 业务规则
5. API_SOT.md                  → API 定义
6. ERROR_CODES_SOT.md          → 错误码
7. AUTH_SPEC.md                → 认证授权
8. DAILY_REPORT_SOT.md         → 日报规则
9. RECONCILIATION_SOT.md       → 对账规则
10. TRANSFER_SOT.md            → 转账规则
11. SUBAGENT_PROTOCOL.md       → AI Agent 协议定义
12. AGENT_SECURITY_SPEC.md     → AI Agent 安全规范
13. AGENT_ORCHESTRATION_PIPELINE.md → AI Agent 编排流程
```

**冲突解决规则**
1. 高优先级文档的定义覆盖低优先级文档
2. 发现冲突时，必须在代码中标注冲突及解决方案
3. 同优先级文档冲突时，由系统架构师裁决（需提交 RFC）
4. 无法解决时，停止生成代码并询问用户

**裁判链强制执行**
- 禁止引用低优先级文档覆盖高优先级文档
- 禁止"灵活处理"或"自行判断"

**来源**: `CLAUDE.md` v3.0

---

## 第七章 代码约束

### 7.1 禁止事项

参见第二章 INV-001 至 INV-004 的所有禁止条款。

**额外禁止事项**
- 禁止创建 SoT 未定义的字段、状态、角色、API
- 禁止在代码中硬编码状态枚举（必须引用 STATE_MACHINE.md）
- 禁止自定义错误码（必须来自 ERROR_CODES_SOT.md）

### 7.2 强制要求

**TypeScript strict mode**
- `tsconfig.json` 必须设置 `strict: true`
- 禁止使用 `any` 类型
- 所有 API 响应必须定义 Zod schema

**Result 模式错误处理**
- 业务逻辑禁止 `throw Error`
- 必须返回 `Result<T, E>`

**禁止魔法数字**
- 硬编码数值必须定义为命名常量
- 常量必须注释来源业务规则编号

**测试覆盖率 80%+**
- 新增功能必须包含单元测试
- 状态机转换必须测试所有允许和禁止的路径
- 账本操作必须测试所有类型

---

## 第八章 关键决策条款

### 8.1 开发新功能

1. 查询对应 SoT 文档（按裁判链优先级）
2. 确认所有字段来自 `DATA_SCHEMA.md`
3. 确认所有状态转换符合 `STATE_MACHINE.md`
4. 确认所有错误码来自 `ERROR_CODES_SOT.md`
5. 涉及账本操作，必须先读 `LEDGER_SOT.md`
6. 涉及权限控制，必须先读 `AUTH_SPEC.md`
7. 涉及三数据流，必须先读 `DAILY_REPORT_SOT.md`

### 8.2 修改现有代码

1. 定位相关 SoT 文档
2. 检查修改是否违反 INV-001 至 INV-004
3. 检查是否需要更新测试
4. 检查是否需要 Alembic 迁移
5. 检查是否需要更新 API 文档
6. 检查是否需要更新 RLS 策略

### 8.3 SoT 未覆盖场景

1. 标注缺失信息
2. 停止生成代码
3. 询问用户是否提交 RFC
4. 扩展 SoT 必须经系统架构师审批

---

## 第九章 文档索引

### Tier 1: 架构宪法

- **docs/1.overview/MASTER.md** v3.5 - 系统唯一入口（本文档）
- **docs/1.overview/PROJECT.md** v1.2 - 业务定义与边界声明

### Tier 2: 单源真相 (docs/2.sot/)

**首次开发必读（按优先级顺序）**
1. **docs/2.sot/STATE_MACHINE.md** - 状态定义与转换规则
2. **docs/2.sot/DATA_SCHEMA.md** - 数据库表结构与字段定义
3. **docs/2.sot/LEDGER_SOT.md** - 双账本规则与计费公式
4. **docs/2.sot/BUSINESS_RULES.md** - 业务规则与约束

**核心 SoT**
- **docs/2.sot/API_SOT.md** - API 端点定义与规范
- **docs/2.sot/ERROR_CODES_SOT.md** - 错误码定义
- **docs/2.sot/AUTH_SPEC.md** - 认证授权规范
- **docs/2.sot/RLS_POLICIES_SOT.md** - 行级安全策略

**领域 SoT**
- **docs/2.sot/DAILY_REPORT_SOT.md** - 日报数据流规则
- **docs/2.sot/RECONCILIATION_SOT.md** - 对账规则
- **docs/2.sot/TRANSFER_SOT.md** - 转账规则

**测试自动化 SoT**
- **docs/2.sot/TEST_AUTOMATION_SOT_v1.0.1.md** v1.0.1 - 测试自动化规范（API Test Line + Agents Test Line）

### Tier 3: 实施指南 (docs/3.dev-guides/)

**架构与设计**
- **docs/3.dev-guides/DDD_API_ARCHITECTURE.md** - DDD 架构设计
- **docs/3.dev-guides/API_DEVELOPMENT_FLOW.md** - API 开发流程
- **docs/3.dev-guides/API_RULEBOOK.md** - API 规则手册

**开发指南**
- **docs/3.dev-guides/BACKEND_DEV_GUIDE.md** - 后端开发指南
- **docs/3.dev-guides/BACKEND_SETUP.md** - 后端环境设置
- **docs/3.dev-guides/FRONTEND_RULES.md** - 前端开发规则
- **docs/3.dev-guides/FRONTEND_SETUP.md** - 前端环境设置
- **docs/3.dev-guides/DEVELOPMENT_STANDARDS.md** - 开发标准

**质量保证**
- **docs/3.dev-guides/TESTING_GUIDE.md** - 测试指南

### Tier 4: 架构层 (docs/4.architecture/)

**系统架构视图**
- **docs/4.architecture/ARCH_LAYER_OVERVIEW.md** - 架构层总览
- **docs/4.architecture/SYSTEM_CONTEXT_VIEW.md** - 系统上下文视图（C4 Level 1）
- **docs/4.architecture/BOUNDED_CONTEXT_MAP.md** - DDD 限界上下文映射
- **docs/4.architecture/SERVICE_COMPONENT_VIEW.md** - 服务组件视图（C4 Level 2/3）
- **docs/4.architecture/DATA_FLOW_VIEW.md** - 数据流视图
- **docs/4.architecture/ERROR_HANDLING_STRATEGY.md** - 错误处理策略
- **docs/4.architecture/PERFORMANCE_AND_CAPACITY_GUIDE.md** - 性能与容量规划

### Tier 5: 基础设施层 (docs/5.infrastructure/)

**基础设施规范**
- **docs/5.infrastructure/INFRA_OVERVIEW.md** - 基础设施层总览
- **docs/5.infrastructure/CI_PIPELINE_SPEC.md** - CI/CD 流水线规范
- **docs/5.infrastructure/DEPLOYMENT_PIPELINE_SPEC.md** - 部署流水线规范
- **docs/5.infrastructure/ENVIRONMENT_VARIABLES_GUIDE.md** - 环境变量指南
- **docs/5.infrastructure/OBSERVABILITY_GUIDE.md** - 可观测性指南

### Tier 6: AI Agent 层 (docs/6.agent-layer/)

**AI Agent 系统规范**
- **docs/6.agent-layer/AGENT_LAYER_OVERVIEW.md** - Agent 层总览与定位
- **docs/6.agent-layer/SUBAGENT_PROTOCOL.md** - Sub-Agent 协议定义（裁判链优先级 #11）
- **docs/6.agent-layer/AGENT_SECURITY_SPEC.md** - Agent 安全规范（裁判链优先级 #12）
- **docs/6.agent-layer/AGENT_ORCHESTRATION_PIPELINE.md** - Agent 编排流程（裁判链优先级 #13）
- **docs/6.agent-layer/CODEX_LOOP_SPEC.md** - Codex Loop 规范（代码级 Agent 操作）
- **docs/6.agent-layer/AGENT_VERSIONING_RULES.md** - Agent 版本管理规则
- **docs/6.agent-layer/AGENT_SKILL_REGISTRY.md** - Agent Skill 注册表

### 快速导航

**在 Cursor 中使用**:
- 使用 `@file:docs/1.overview/MASTER.md` 引用本文档
- 使用 `@codebase docs/2.sot/` 搜索 SoT 文档
- 使用 `@file:docs/2.sot/STATE_MACHINE.md` 引用特定 SoT 文档

---

## 第十章 最终裁决

1. **信息不在 SoT 中** → 停止生成代码 → 标注缺失 → 询问用户
2. **发现文档冲突** → 引用裁判链 → 标注冲突 → 无法解决则提交 RFC
3. **禁止直接修改 models/** → 必须检查 DATA_SCHEMA.md → Alembic 迁移 → DBA 审核
4. **禁止绕过状态机** → 状态变更必须遵循前置条件
5. **禁止混合账本** → PROJECT 与 SUPPLIER 独立
6. **禁止终态直接修改** → 终态后唯一方式为红冲
7. **禁止违反 BI-01 至 BI-05** → 业务不可变量强制执行
8. **禁止违反 D-01 至 D-06** → 永久禁止行为不可豁免
9. **禁止违反 FZ-01 至 FZ-03** → Freeze 期间不可修改受保护内容

---

## 附录 A: 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v3.0 | 2025-11-24 | 初始版本，基于 SoT Freeze v1.0 | 系统架构师 |
| v3.1 | 2025-11-24 | 修复红冲符号错误，添加余额计算公式 | 系统架构师 |
| v3.2 | 2025-11-24 | 补充日报计费触发规则 | 系统架构师 |
| v3.3 | 2025-11-25 | 对齐 CLAUDE.md v3.0，完善裁判链 | 系统架构师 |
| v3.4 | 2025-11-25 | 整合 PROJECT.md v1.2：业务不可变量、永久禁止行为、Freeze 机制 | Master Architect |
| v3.5 | 2025-11-27 | 扩展至 6 层架构：新增 Agent Layer（第 6 层），扩展裁判链至 13 项，更新文档索引 | Master Architect |
| v3.6 | 2025-12-01 | 新增第五章附录「规范变更管理 (OpenSpec)」：OS-01 至 OS-04，确立 OpenSpec 为唯一变更通道 | Master Architect |

---

**文档版本**: v3.6
**最后更新**: 2025-12-01
**对齐文档**: PROJECT.md v1.2, SoT Freeze v2.6, Dev-Guides Freeze vFinal, Architecture Freeze v1.0, Infrastructure Freeze v1.0, Agent Layer Freeze v1.0, CLAUDE.md v3.0
**维护者**: 系统架构师
**变更审批**: 所有修改必须经过 RFC 流程
