# AI 广告代投管理系统 - AI 友好 PRD

> **版本**: v1.1 (基于 PRD v5.1 优化)
> **状态**: ACTIVE
> **last_reviewed**: 2026-01-01
> **兼容性**: Claude Code, Cursor, Windsurf, Copilot

---

## PART 0: AI 执行指南

> 本章节专为 AI 编程助手设计，人类可跳过

### 0.1 SoT 裁判链（优先级从高到低）

```
1. MASTER.md v4.9          → 系统宪法，最高优先级
2. PRD v5.1                → 需求文档（已与 MASTER 6 角色完全对齐）
3. STATE_MACHINE.md v2.9   → 状态机定义
4. DATA_SCHEMA.md v5.11     → 数据模型 + 账本规则
5. BUSINESS_RULES.md v5.2  → 业务规则
6. API_SOT.md v9.7         → API 契约
7. ERROR_CODES_SOT.md v2.2 → 错误码
8. AUTH_SPEC.md v2.2       → 认证授权
9. PRD_AI_v1.0.md          → 本文档（AI 友好格式）
```

**冲突处理**: 高层文档覆盖低层文档。遇到冲突先查 MASTER.md。

### 0.2 Phase 边界（当前 Phase 1）

| 允许 | 禁止 |
|------|------|
| 记录事实 | 自动阻断 |
| 展示状态 | 自动惩罚 |
| 提示异常 | 强制审批 |
| 高亮警告 | 冻结账户 |

```python
# ✅ Phase 1 正确做法
if cpl > threshold:
    logger.warning(f"CPL异常: {cpl}")  # 记录
    return {"warning": "CPL超标，请关注"}  # 提示

# ❌ Phase 1 禁止做法
if cpl > threshold:
    raise BusinessError("CPL超标，禁止提交")  # 阻断
    user.is_active = False  # 自动惩罚
```

### 0.3 防幻觉检查清单

在生成代码前，AI 必须确认：

```
□ 角色是否在 6 角色白名单内？
□ 状态是否在对应状态机内？
□ 错误码是否来自 ERROR_CODES_SOT.md？
□ API 端点是否在 API_SOT.md 中定义？
□ 是否符合 Phase 1 约束（不阻断）？
```

---

## PART 1: 执行摘要

### 1.1 一句话定位

**广告投放业务的"人、账户、项目、钱"管理系统，让账目清清楚楚、有据可查。**

### 1.2 核心问题

| ID | 问题 | 现状 | 目标 | 数据 |
|----|------|------|------|------|
| P1 | 项目盈亏不透明 | 月底手工汇总 | T+1 可见 | 发现延迟 15 天 |
| P2 | 投手管理低效 | 微信群/Excel | 系统统一 | 35% 日报有错 |
| P3 | 账户状态混乱 | 微信群沟通 | 系统追溯 | 转移无记录 |
| P4 | 押款不清晰 | 财务手工统计 | 实时计算 | 滞后 7 天 |
| P5 | 收支核算耗时 | 月底集中 | 1 天完成 | 原需 5-7 天 |

### 1.3 成功指标

| 指标 | 基线 | Phase 1 目标 | 衡量方式 |
|------|------|--------------|---------|
| 项目盈亏可见性 | 月度 | T+1 | 系统仪表盘 |
| 日报错误率 | 35% | <15% | 系统校验 |
| 提成计算时间 | 3 天 | 10 分钟 | 一键计算 |
| 押款统计时效 | T+7 | 实时 | 自动计算 |

### 1.4 不变量（绝对不能违反）

```python
# INV-01: 预收款 ≠ 收入
assert prepayment.type == "LIABILITY"  # 履约前是负债

# INV-02: 平台消耗不含手续费
cost = ad_spend + platform_fee  # 分开核算
cost != ad_spend * (1 + fee_rate)  # ❌ 错误

# INV-03: 可用资金公式
available = opening_balance + sum(topups) - sum(ad_spends)

# INV-04: 锁定后不可改
if ledger_entry.is_locked:
    raise BusinessError("BIZ-LED-001")  # 只能红冲

# INV-05: 数据域隔离
pitcher.can_see(account) == (account.pitcher_id == pitcher.id)
```

---

## PART 2: 角色与权限

### 2.1 角色定义（6 角色）

> **来源**: MASTER.md v4.9 §2.4, PRD v5.1 §2.2.1
> **对齐状态**: PRD v5.1 已与 MASTER 6 角色模型完全对齐（删除 Supervisor，合并到 project_owner）

| 角色 ID | 中文名 | 核心职责 | 关键决策 |
|---------|--------|---------|---------|
| `ceo` | 老板 | 资金安全、公司盈亏、最终决策 | 大额支出、月度锁账 |
| `project_owner` | 项目负责人 | 项目盈亏、日报审核、有效线索确认 | 定价、争议裁定 |
| `finance` | 财务 | 资金出入准确、对账、收入录入 | 充值审批（限额内） |
| `pitcher` | 投手 | CPL 达标、日报准确、执行投放 | 投放策略（预算内） |
| `account_manager` | 户管 | 账户管理、环境分配、实际消耗录入 | 账户分配 |
| `admin` | 管理员 | 系统配置、用户管理 | 系统设置 |

### 2.1.1 技术层角色映射

> **来源**: MASTER.md v4.9 §2.4, PRD v5.1 §2.2.2

| 业务角色 | `user.role` 字段值 | 说明 |
|----------|-------------------|------|
| 老板 | `ceo` | 系统最高权限 |
| 项目负责人 | `project_owner` | 管理项目和投手 |
| 财务 | `finance` | 资金和结算管理 |
| 投手 | `pitcher` | 执行投放，提交日报 |
| 户管 | `account_manager` | 账户环境管理 |
| 管理员 | `admin` | 系统配置 |

**汇报关系**: 投手 → 项目负责人 → 老板（无中间层 supervisor）

### 2.2 废弃角色（禁止使用）

> **来源**: MASTER.md v4.9 INV-007, PRD v5.1 §2.2.1

| 角色 | 状态 | 替代方案 | 废弃原因 |
|------|------|---------|---------|
| `supervisor` | ❌ 废弃 | `project_owner` | PRD v5.1 架构决策，职责合并 |
| `data_operator` | ❌ 废弃 | `project_owner`/`finance` | 不在宪法定义中 |
| `media_buyer` | ⚠️ 技术别名 | `pitcher` | 非规范名称，应使用 pitcher |

```python
# ❌ 错误
if user.role == "supervisor":
    pass

# ✅ 正确
if user.role == "project_owner":
    pass
```

### 2.3 权限矩阵

| 功能 | ceo | project_owner | finance | pitcher | account_manager | admin |
|------|:---:|:-------------:|:-------:|:-------:|:---------------:|:-----:|
| 项目-查看全部 | ✓ | - | ✓ | - | - | ✓ |
| 项目-查看负责的 | - | ✓Own | - | - | - | - |
| 日报-填写 | - | - | - | ✓ | - | - |
| 日报-审核趋势 | - | ✓Team | - | - | - | - |
| 日报-确认有效线索 | - | ✓Own | - | - | - | - |
| 充值-申请 | - | - | - | ✓ | - | - |
| 充值-审批 | ✓ | - | ✓ | - | - | - |
| 账户-管理 | R | R | R | R | ✓ | ✓ |
| 实际消耗-录入 | - | - | - | - | ✓ | - |
| 收入-录入 | - | - | ✓ | - | - | - |
| 月度锁账 | ✓ | - | - | - | - | - |

**图例**: ✓=全部, Own=仅负责的, Team=仅团队, R=只读, -=无权限

---

## PART 3: 核心业务规则

### 3.1 收入计算规则

| ID | 规则 | 公式 | 示例 |
|----|------|------|------|
| BR-REV-001 | 固定单价收入 | `revenue = conversions_final × unit_price` | 100线索 × $80 = $8,000 |
| BR-REV-002 | 阶梯定价收入 | `revenue = Σ(档位线索数 × 该档单价)` | 见下方示例 |
| BR-REV-003 | 服务费收入 | `revenue = ad_spend × (1 + fee_rate)` | $10,000 × 1.1 = $11,000 |

**阶梯定价示例**:
```python
# 配置: 1-100: $80, 101-300: $90, 301+: $100
# 线索数: 250

revenue = 100 * 80 + 150 * 90  # 前100个 + 后150个
       = 8000 + 13500
       = 21500  # $21,500
```

### 3.2 成本计算规则

| ID | 规则 | 说明 |
|----|------|------|
| BR-COST-001 | 成本 SoT = `ad_spend_daily.spend` | 实际消耗，非投手申报 |
| BR-COST-002 | 总成本 = 实际消耗 + 平台手续费 | 分开核算 |
| BR-COST-003 | 押款 = Σ充值 - Σ实际消耗 | 实时计算 |

```python
# ✅ 正确：使用实际消耗
cost = sum(ad_spend_daily.spend for record in period)

# ❌ 错误：使用投手申报
cost = sum(daily_report.spend for report in period)  # 违反 BR-COST-001
```

### 3.3 提成计算规则

| ID | 规则 | 说明 |
|----|------|------|
| BR-COM-001 | 提成基于 `conversions_final` | 已确认有效线索 |
| BR-COM-002 | 阶梯提成按月累计 | 每月从 0 开始 |
| BR-COM-003 | 跨项目分别计算 | 不合并 |
| BR-COM-004 | 状态必须为 `final_confirmed` | 未确认不计入 |

**提成计算示例**:
```python
# 项目配置: 1-50: $1, 51-100: $1.5, 101+: $2
# 投手本月确认线索: 120 个

commission = 50 * 1.0 + 50 * 1.5 + 20 * 2.0
          = 50 + 75 + 40
          = 165  # $165
```

### 3.4 数据三层架构

| 层级 | 数据源 | 字段 | 用途 | 准确性 |
|------|--------|------|------|--------|
| 行为记录层 | 投手自报 | `daily_report.spend` | 趋势监控 | 参考值 |
| 实际数据层 | 平台拉取 | `ad_spend_daily.spend` | **成本 SoT** | 高 |
| 结算数据层 | 甲方确认 | `conversions_final` | **收入 SoT** | 最终 |

---

## PART 4: 状态机定义

### 4.1 日报状态机

> **来源**: STATE_MACHINE.md v2.9 §8
> **重要**: Phase 1 使用 3 状态简化模型，Phase 2 启用完整 8 状态

#### Phase 1 日报状态机（3 状态）- 当前生效

```
raw_submitted → trend_ok → final_confirmed
```

| 状态 | 中文 | 触发动作 | 可转换到 |
|------|------|---------|---------|
| `raw_submitted` | 已提交 | 投手提交日报 | `trend_ok` |
| `trend_ok` | 趋势正常 | 项目负责人审核通过 | `final_confirmed` |
| `final_confirmed` | 已确认 | 项目负责人确认有效线索 | (终态) |

**Phase 1 简化说明**:
- 无自动风控阻断（符合 Phase 1 约束）
- 项目负责人手动审核趋势
- 异常通过高亮提示，不阻断流程

#### Phase 2 日报状态机（8 状态）- 未来启用

```
raw_submitted → trend_pending → trend_ok ────────────────────┐
                              ↘ trend_flagged → trend_resolved ┤
                                                               ↓
                                              final_pending → final_confirmed → final_locked
```

| 状态 | 中文 | 触发动作 | 可转换到 |
|------|------|---------|---------|
| `raw_submitted` | 已提交 | 投手提交日报 | `trend_pending` |
| `trend_pending` | 趋势审核中 | 系统自动/手动触发 | `trend_ok`, `trend_flagged` |
| `trend_ok` | 趋势正常 | 系统风控通过 | `final_pending` |
| `trend_flagged` | 趋势异常 | 系统风控标记 | `trend_resolved`, `raw_submitted` |
| `trend_resolved` | 异常已处理 | project_owner 确认 | `final_pending` |
| `final_pending` | 待最终确认 | 趋势审核完成 | `final_confirmed` |
| `final_confirmed` | 已确认 | project_owner 确认有效线索 | `final_locked` |
| `final_locked` | 已锁定 | 系统计费锁定 | (终态) |

**状态转换代码示例**:
```python
# ✅ Phase 1 合法转换
report.transition("raw_submitted", "trend_ok")
report.transition("trend_ok", "final_confirmed")

# ❌ Phase 1 非法转换（使用 Phase 2 状态）
report.transition("raw_submitted", "trend_pending")  # Phase 1 不存在 trend_pending
```

### 4.2 充值状态机（7 状态）

> **来源**: STATE_MACHINE.md v2.9 §10, PRD v5.1 §2.3.3

```
draft → pending_review → finance_approve → paid → completed
  ↓           ↓                ↓
cancelled   rejected        rejected
```

| 状态 | 中文 | 可转换到 |
|------|------|---------|
| `draft` | 草稿 | `pending_review`, `cancelled` |
| `pending_review` | 待审核 | `finance_approve`, `rejected` |
| `finance_approve` | 财务已批 | `paid`, `rejected` |
| `paid` | 已转账 | `completed` |
| `completed` | 已完成 | (终态) |
| `rejected` | 已拒绝 | (终态) |
| `cancelled` | 已取消 | (终态) |

**充值审批链说明**:
| 充值类型 | 审批流程 | 说明 |
|---------|---------|------|
| 日常充值 | 投手申请 → 财务审批 → 转账完成 | 无需老板逐笔审批 |
| 大额充值 | 投手申请 → 财务初审 → 老板终审 → 转账完成 | 超阈值需老板审批 |
| 紧急充值 | 投手申请 → 项目负责人确认 → 财务快速处理 | 特殊通道 |

### 4.3 账户状态机（6 状态）

```
new → testing → active ←→ suspended → dead → archived
  ↓      ↓        ↓           ↓         ↓
  └──────┴────────┴───────────┴─────────┴─→ archived
```

| 状态 | 中文 | 说明 |
|------|------|------|
| `new` | 新建 | 刚录入 |
| `testing` | 测试中 | 测试投放 |
| `active` | 在用 | 正常使用 |
| `suspended` | 暂停 | 临时停用 |
| `dead` | 死号 | 永久失效 |
| `archived` | 归档 | 终态 |

### 4.4 项目状态机（4 状态）

```
draft → active ←→ suspended → archived
  ↓        ↓           ↓
  └────────┴───────────┴──→ archived
```

---

## PART 5: 核心公式速查

```python
# ==================== 收入公式 ====================

# 固定单价
revenue = conversions_final * unit_price

# 阶梯定价
revenue = sum(tier.count * tier.price for tier in tiers)

# 服务费
revenue = ad_spend * (1 + service_fee_rate)

# ==================== 成本公式 ====================

# 项目成本
cost = real_spend + platform_fee

# 押款
deposit = sum(topups) - sum(real_spends)

# ==================== 利润公式 ====================

# 项目毛利
gross_profit = revenue - cost

# 毛利率
gross_margin = gross_profit / revenue * 100

# CPL (单线索成本)
cpl = ad_spend / conversions_final

# ==================== 提成公式 ====================

# 阶梯提成
commission = sum(tier.count * tier.rate for tier in tiers)
```

---

## PART 6: 任务卡索引

### 6.1 模块 M0: 基础设施

| 任务卡 | 功能 | 优先级 | SoT 引用 |
|--------|------|--------|---------|
| TASK-AUTH-001 | 用户登录/登出 | P0 | AUTH_SPEC §2 |
| TASK-AUTH-002 | 忘记密码 | P1 | AUTH_SPEC §3 |
| TASK-USR-001 | 用户 CRUD | P0 | DATA_SCHEMA §3.1 |
| TASK-CLT-001 | 客户 CRUD | P0 | DATA_SCHEMA §3.2 |

### 6.2 模块 M1: 项目管理

| 任务卡 | 功能 | 优先级 | SoT 引用 |
|--------|------|--------|---------|
| TASK-PRJ-001 | 项目 CRUD | P0 | DATA_SCHEMA §3.3 |
| TASK-PRJ-002 | 定价配置 | P0 | BUSINESS_RULES BR-PROJ-* |
| TASK-PRJ-003 | 提成配置 | P0 | BUSINESS_RULES BR-COM-* |
| TASK-PRJ-004 | 项目仪表盘 | P0 | API_SOT §5.1 |
| TASK-PRJ-005 | 预付款管理 | P0 | DATA_SCHEMA §3.4 |

### 6.3 模块 M2: 日报管理

| 任务卡 | 功能 | 优先级 | SoT 引用 |
|--------|------|--------|---------|
| TASK-RPT-001 | 日报填写 | P0 | STATE_MACHINE §8 |
| TASK-RPT-002 | 日报审核（趋势） | P0 | STATE_MACHINE §8 |
| TASK-RPT-003 | 有效线索确认 | P0 | BUSINESS_RULES BR-RPT-* |
| TASK-RPT-004 | 提成计算 | P0 | BUSINESS_RULES BR-COM-* |
| TASK-RPT-005 | 投手工作台 | P1 | API_SOT §6 |

### 6.4 模块 M3: 账户管理

| 任务卡 | 功能 | 优先级 | SoT 引用 |
|--------|------|--------|---------|
| TASK-ACC-001 | 账户 CRUD | P0 | DATA_SCHEMA §3.5 |
| TASK-ACC-002 | 账户分配 | P0 | STATE_MACHINE §14 |
| TASK-ACC-003 | 账户转移 | P1 | BUSINESS_RULES BR-ACCT-* |
| TASK-ACC-004 | 死号处理 | P1 | STATE_MACHINE §14 |

### 6.5 模块 M4: 充值管理

| 任务卡 | 功能 | 优先级 | SoT 引用 |
|--------|------|--------|---------|
| TASK-TOP-001 | 充值申请 | P0 | STATE_MACHINE §10 |
| TASK-TOP-002 | 充值审批 | P0 | STATE_MACHINE §10 |
| TASK-TOP-003 | 实际消耗录入 | P0 | BUSINESS_RULES BR-FIN-* |

### 6.6 模块 M5: 财务管理

| 任务卡 | 功能 | 优先级 | SoT 引用 |
|--------|------|--------|---------|
| TASK-FIN-001 | 收入录入 | P0 | DATA_SCHEMA §3.4.4 |
| TASK-FIN-002 | 押款统计 | P0 | BUSINESS_RULES BR-FIN-* |
| TASK-FIN-003 | 月度锁账 | P1 | STATE_MACHINE §11 |
| TASK-FIN-004 | 财务仪表盘 | P1 | API_SOT §7 |

---

## PART 7: 验收标准模板

### 7.1 示例: 日报提交 (TASK-RPT-001)

**Given** (前置条件):
- 用户角色为 `pitcher`
- 用户已分配广告账户
- 账户关联的项目状态为 `active`

**When** (触发动作):
```http
POST /api/v1/daily-reports
Authorization: Bearer <token>
Content-Type: application/json

{
  "ad_account_id": "uuid",
  "date": "2025-12-31",
  "spend": 1000.00,
  "conversions": 50
}
```

**Then** (预期结果):
- [ ] 返回 HTTP 201
- [ ] `response.data.status` = `"raw_submitted"`
- [ ] 创建 `audit_log` 记录
- [ ] CPL 自动计算: `1000 / 50 = 20`

**边界情况**:
| 条件 | 预期错误码 | 说明 |
|------|-----------|------|
| spend < 0 | `BIZ-VAL-001` | 消耗不能为负 |
| 同日已存在日报 | `BIZ-RPT-002` | 重复提交 |
| 项目状态非 active | `BIZ-PRJ-003` | 项目已暂停 |
| spend=0 且无备注 | `BIZ-VAL-002` | 需说明原因 |

---

## PART 8: 禁止行为清单

### 8.1 角色禁止

| ID | 禁止行为 | 正确做法 |
|----|---------|---------|
| F-ROLE-001 | 使用 `supervisor` 角色 | 使用 `project_owner` |
| F-ROLE-002 | 使用 `data_operator` 角色 | 使用 `project_owner`/`finance` |
| F-ROLE-003 | 使用 `manager` 角色 | 使用 `project_owner` |

### 8.2 数据禁止

| ID | 禁止行为 | 正确做法 |
|----|---------|---------|
| F-DATA-001 | 用投手申报消耗计算成本 | 用 `ad_spend_daily.spend` |
| F-DATA-002 | 用未确认线索计算收入 | 用 `conversions_final` |
| F-DATA-003 | 直接修改余额字段 | 通过 ledger_entries |

### 8.3 状态禁止

| ID | 禁止行为 | 正确做法 |
|----|---------|---------|
| F-STATE-001 | 跳过日报状态 | 按状态机流转 |
| F-STATE-002 | 修改已锁定数据 | 只能红冲 |
| F-STATE-003 | 使用 Phase 2 状态 | Phase 1 使用 3 状态机 |

### 8.4 Phase 1 禁止

| ID | 禁止行为 | Phase 2 可用 |
|----|---------|-------------|
| F-PH1-001 | 自动阻断提交 | ✓ |
| F-PH1-002 | 自动冻结账户 | ✓ |
| F-PH1-003 | 自动扣分惩罚 | ✓ |
| F-PH1-004 | 强制审批流程 | ✓ |

---

## PART 9: 术语表

| 术语 | 英文 | 定义 | 示例 |
|------|------|------|------|
| 投手 | Pitcher | 执行广告投放的员工 | media_buyer |
| 进粉 | Conversions | 获取的线索数 | 100 个 |
| CPL | Cost Per Lead | 单线索成本 | $20/线索 |
| 押款 | Deposit | 充值未消耗余额 | $5,000 |
| 履约 | Fulfillment | 项目完成交付 | status=fulfilled |
| SoT | Source of Truth | 真相源 | 单一数据源 |
| 红冲 | Reversal | 用负数冲销错误记录 | ref_id 关联 |

---

## PART 10: 变更日志

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.1 | 2026-01-01 | 与 PRD v5.1 / MASTER v4.8 对齐 | Claude |
| v1.0 | 2025-12-31 | 基于 PRD_v5.1 重构为 AI 友好格式 | Claude |

### v1.1 主要变更（2026-01-01）

1. **SoT 裁判链更新**: 添加 PRD v5.1 到优先级 2，更新各文档版本号
2. **角色定义完善**: 确认 PRD v5.1 已与 MASTER 6 角色完全对齐
3. **技术层角色映射**: 新增 §2.1.1 技术层角色映射表
4. **日报状态机澄清**: 明确 Phase 1 使用 3 状态，Phase 2 使用 8 状态
5. **充值审批链**: 新增日常/大额/紧急充值审批流程说明
6. **快速参考卡片**: 更新为 Phase 1 三状态模型

### v1.0 与 PRD_v5.1 主要差异

1. **角色精简**: 7 角色 → 6 角色（移除 supervisor）
2. **结构重组**: 按 AI 友好最佳实践重构
3. **增加内容**:
   - SoT 裁判链
   - 防幻觉检查清单
   - 禁止行为清单
   - 代码示例
4. **验收标准**: Given-When-Then 格式
5. **公式集中**: 所有公式集中在 PART 5

---

## 快速参考卡片

```
┌─────────────────────────────────────────────────────────────┐
│                    AI 编程快速参考                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  角色 (6个):                                                 │
│  ceo | project_owner | finance | pitcher | account_manager | admin │
│                                                              │
│  废弃角色: supervisor, data_operator, media_buyer           │
│                                                              │
│  日报状态 (Phase 1: 3个):                                    │
│  raw_submitted → trend_ok → final_confirmed                 │
│                                                              │
│  日报状态 (Phase 2: 8个，未来启用):                          │
│  raw_submitted → trend_pending → trend_ok/trend_flagged     │
│  → trend_resolved → final_pending → final_confirmed → final_locked │
│                                                              │
│  充值状态 (7个):                                             │
│  draft → pending_review → finance_approve → paid → completed │
│                                                              │
│  成本 SoT: ad_spend_daily.spend                             │
│  收入 SoT: conversions_final × unit_price                   │
│                                                              │
│  Phase 1: 只提示、不阻断、不问责                            │
│                                                              │
│  SoT 版本: MASTER v4.8, PRD v5.1, DATA_SCHEMA v5.7          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

*文档结束 | 版本 v1.1 | 2026-01-01*
