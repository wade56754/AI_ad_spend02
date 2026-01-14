# BUSINESS_RULES.md - 业务规则索引（SoT Index）

> **文档版本**: v5.2
> **status**: active
> **owner**: wade
> **last_reviewed**: 2026-01-12
> **文档类型**: 业务规则唯一真相源索引（SoT Index）
> **规范级别**: 强制执行
> **基准**: PRD v5.2, MASTER.md v4.9（PRD v5.2 已与 MASTER 6 角色模型完全对齐）
> **业务参考**: 各 BR-*.md 子模块（业务逻辑框架已拆分到各规则子模块）

---

## 互锁 SoT 引用

> **本文档是业务规则的索引层，不承载具体实现逻辑。**
> 所有规则的具体定义必须由子模块（BR-*.md）实现。

| SoT 文档 | 版本 | 职责 | 引用关系 |
|----------|------|------|----------|
| MASTER.md | v4.9 | 架构宪法 | 本文档的上游约束 |
| STATE_MACHINE.md | v2.9 | 状态机规范 | BR-RPT/BR-FIN/BR-RECON 依赖 |
| DATA_SCHEMA.md | v5.7 | 数据模型 | 所有 BR-* 字段定义依赖，账本规则见 §3.4.4 |
| ERROR_CODES_SOT.md | v2.2 | 错误码规范 | 规则违反时的错误码映射 |
| AUTH_SPEC.md | v2.2 | 权限规范 | BR-AUTH/BR-USER 依赖 |
| API_SOT.md | v9.6 | API 规范 | 规则的 API 层实现 |

---

## ASDD 链路元数据

```yaml
asdd_version: "1.0"
document_type: "sot_index"
upstream:
  - path: "docs/MASTER.md"
    version: "v4.9"
    relation: "constrained_by"
downstream:
  - path: "docs/sot/STATE_MACHINE.md"
    version: "v2.9"
    relation: "implements"
  - path: "docs/sot/DATA_SCHEMA.md"
    version: "v5.7"
    relation: "implements"
  - path: "docs/sot/ERROR_CODES_SOT.md"
    version: "v2.2"
    relation: "implements"
  - path: "docs/sot/AUTH_SPEC.md"
    version: "v2.1"
    relation: "implements"
modules:
  - id: "BR-AUTH"
    name: "认证授权"
    path: "docs/sot/BR-AUTH.md"
    version: "v1.1"
  - id: "BR-USER"
    name: "用户角色"
    path: "docs/sot/BR-USER.md"
    version: "v1.1"
  - id: "BR-PROJ"
    name: "项目管理"
    path: "docs/sot/BR-PROJ.md"
    version: "v1.1"
  - id: "BR-ACCT"
    name: "广告账户"
    path: "docs/sot/BR-ACCT.md"
    version: "v1.1"
  - id: "BR-FIN"
    name: "财务流程"
    path: "docs/sot/BR-FIN.md"
    version: "v1.1"
  - id: "BR-RPT"
    name: "日报管理"
    path: "docs/sot/BR-RPT.md"
    version: "v1.1"
  - id: "BR-RECON"
    name: "对账流程"
    path: "docs/sot/BR-RECON.md"
    version: "v1.1"
  - id: "BR-DATA"
    name: "数据完整性"
    path: "docs/sot/BR-DATA.md"
    version: "v1.1"
  - id: "BR-PROFIT"
    name: "利润统计"
    path: "docs/sot/BR-PROFIT.md"
    version: "v1.2"
```

---

## 第一章 开发铁律

> **引用**: MASTER.md v4.9 §7 AI 防幻觉原则

以下 5 条铁律必须在所有业务规则实现中严格遵守：

| 编号 | 铁律 | 违反后果 |
|------|------|----------|
| **DEV-001** | 禁止假设数据一致：遇到缺失必须标记「待确认」 | P0 缺陷 |
| **DEV-002** | 禁止自动做管理裁决：不得生成自动拒绝/暂停代码 | 代码回滚 |
| **DEV-003** | 禁止引入 SoT 未定义概念：发现缺失必须停止并询问 | PR 拒绝 |
| **DEV-004** | 必须遵循 Phase 1 软性原则：仅提示+高亮+记录 | P0 缺陷 |
| **DEV-005** | 遇到歧义必须停止并询问：禁止自行推断 | PR 拒绝 |

---

## 第二章 角色定义

### 2.1 业务层角色（6 角色）

> **架构决策（MASTER v4.6+）**: 移除 supervisor 角色，其职责合并到 project_owner。
>
> **来源**: MASTER.md v4.9 §2.4（已对齐6角色架构）

| 角色ID | 中文名 | 核心职责 | 关键指标 | 决策权限 |
|--------|--------|----------|----------|----------|
| `ceo` | 老板 | 战略决策、资金安全、最终审批 | 公司利润、资金周转 | 全部 |
| `project_owner` | 项目负责人 | 客户对接、项目盈亏、日报审核、有效线索确认 | 项目毛利率、日报及时率 | 项目范围内 |
| `finance` | 财务 | 资金审批、转账执行、利润核算 | 资金准确性 | 资金操作 |
| `pitcher` | 投手 | 广告投放、日报填写、充值申请 | 个人CPL、进粉数 | 无 |
| `account_manager` | 户管 | 账户管理、环境分配、代理商对接 | 账户存活率 | 账户操作 |
| `admin` | 管理员 | 系统配置、用户管理 | 系统稳定性 | 系统配置 |

### 2.2 角色职能详细描述

> **来源**: MASTER.md v4.9 §2.4（角色职能定义）

**老板（CEO）**
- 战略层：公司发展方向、新市场开拓决策、重大合作审批
- 财务层：大额资金审批、月度锁账确认、利润分成审批
- 管理层：高层人事任免、绩效考核最终确认、重大异常处理

**项目负责人（Project Owner）**
- 客户管理：客户洽谈与签约、定价谈判、客户关系维护、争议处理
- 项目管理：项目盈亏监控、有效线索确认、结算数据审核、预付款余额监控
- 日报管理：日报审核（通过/标记异常）、异常数据处理、投放效果监控
- 团队协调：投手资源调配、问题反馈收集

**财务（Finance）**
- 资金管理：充值申请审批、转账执行、预付款入账、退款处理
- 核算统计：利润计算、押款统计、月度报表、合伙人分成
- 对账：预付款余额核对、代理商押款核对、银行流水核对

**投手（Pitcher）**
- 投放执行：广告创建与优化、预算分配、效果监控、素材测试
- 数据报告：日报填写、异常说明、问题反馈
- 账户维护：账户状态监控、充值申请、问题上报

**户管（Account Manager）**
- 账户管理：新账户入库、账户分配、账户转移、死号处理
- 代理商对接：下户申请、充值协调、问题沟通
- 环境管理：环境分配、环境维护、环境回收

### 2.3 权限矩阵

> **来源**: AUTH_SPEC.md v2.2（权限矩阵定义）

**数据查看权限**

| 数据范围 | 老板 | 项目负责人 | 财务 | 投手 | 户管 |
|---------|:---:|:---------:|:---:|:---:|:---:|
| 全公司数据 | ✅ | ❌ | ✅ | ❌ | ❌ |
| 所有项目 | ✅ | ❌ | ✅ | ❌ | ❌ |
| 本人项目 | ✅ | ✅ | ✅ | ❌ | ❌ |
| 本人数据 | ✅ | ✅ | ✅ | ✅ | ❌ |
| 所有账户 | ✅ | ❌ | ❌ | ❌ | ✅ |

**操作权限**

| 操作 | 老板 | 项目负责人 | 财务 | 投手 | 户管 |
|------|:---:|:---------:|:---:|:---:|:---:|
| 创建客户/项目 | ✅ | ✅ | ❌ | ❌ | ❌ |
| 填写日报 | ❌ | ❌ | ❌ | ✅ | ❌ |
| 审核日报 | ❌ | ✅ | ❌ | ❌ | ❌ |
| 确认有效线索 | ❌ | ✅ | ❌ | ❌ | ❌ |
| 申请充值 | ❌ | ❌ | ❌ | ✅ | ❌ |
| 审批充值 | ❌ | ❌ | ✅ | ❌ | ❌ |
| 执行转账 | ❌ | ❌ | ✅ | ❌ | ❌ |
| 分配账户 | ❌ | ❌ | ❌ | ❌ | ✅ |
| 月度锁账 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 解锁修正 | ✅ | ❌ | ❌ | ❌ | ❌ |

### 2.4 技术层角色映射

> **引用**: AUTH_SPEC.md v2.2 §2.2, DATA_SCHEMA.md v5.7

| 技术层角色 | 业务层角色 | 说明 |
|-----------|-----------|------|
| `admin` | `ceo`, `admin` | 系统管理权限 |
| `finance` | `finance` | 财务权限 |
| `account_manager` | `account_manager`, `project_owner` | 账户管理 + 项目负责人权限 |
| `media_buyer` | `pitcher` | 投放执行权限 |

> **注**: `project_owner` 通过 `users.is_project_owner=true` 或 `project_members` 表判断，不是技术层枚举角色。

### 2.5 旧角色兼容映射

| 旧角色 | 新角色 | 变更版本 |
|--------|--------|----------|
| `supervisor` | `project_owner` | MASTER v4.6+（已在 Framework v2.1 中移除） |
| `media_buyer` | `pitcher` | v4.0 |
| `data_operator` | `project_owner` | MASTER v4.6+（已在 Framework v2.1 中移除） |

---

## 第三章 规则模块导航

| 模块ID | 模块名称 | 规则数量 | 子模块文档 | 关联 SoT | 状态 |
|--------|----------|----------|------------|----------|------|
| BR-AUTH | 认证授权 | 6 | [BR-AUTH.md](BR-AUTH.md) | AUTH_SPEC.md v2.2 | active |
| BR-USER | 用户角色 | 5 | [BR-USER.md](BR-USER.md) | MASTER.md v4.9 §2.4 | active |
| BR-PROJ | 项目管理 | 8 | [BR-PROJ.md](BR-PROJ.md) | STATE_MACHINE.md v2.9 §5 | active |
| BR-ACCT | 广告账户 | 6 | [BR-ACCT.md](BR-ACCT.md) | DATA_SCHEMA.md v5.7 | active |
| BR-FIN | 财务流程 | 10 | [BR-FIN.md](BR-FIN.md) | DATA_SCHEMA.md v5.7 §3.4.4 | active |
| BR-RPT | 日报管理 | 9 | [BR-RPT.md](BR-RPT.md) | STATE_MACHINE.md v2.9 §8 | active |
| BR-RECON | 对账流程 | 7 | [BR-RECON.md](BR-RECON.md) | STATE_MACHINE.md v2.9 §10 | active |
| BR-DATA | 数据完整性 | 5 | [BR-DATA.md](BR-DATA.md) | DATA_SCHEMA.md v5.7 | active |
| BR-PROFIT | 利润统计 | 7 | [BR-PROFIT.md](BR-PROFIT.md) | DATA_SCHEMA.md v5.7 §3.4.4, §3.6 | active |

> **子模块文档说明**: 每个 BR-*.md 子模块包含该模块的完整规则定义，包括：
> - 业务场景、详细约束、前置条件
> - 错误码映射（对齐 ERROR_CODES_SOT.md v2.2）
> - Test Intent（测试意图）
> - 规则依赖关系

---

## 第四章 规则模块概览

### 4.1 BR-AUTH（认证授权） → [详细规则](BR-AUTH.md)

> **关联 SoT**: AUTH_SPEC.md v2.1

| 规则ID | 规则名称 | 约束描述 | 违反错误码 |
|--------|----------|----------|-----------|
| BR-AUTH-001 | 登录必须验证 | 所有 API 请求必须携带有效 JWT Token | `AUTH_400` |
| BR-AUTH-002 | Token 有效期 | Access Token 有效期不得超过 24 小时 | `AUTH_401` |
| BR-AUTH-003 | 角色唯一性 | 每个用户在同一项目中仅能拥有一个角色 | `AUTH_403` |
| BR-AUTH-004 | 权限继承禁止 | 角色权限不得跨层级继承 | `AUTH_500` |
| BR-AUTH-005 | 密码强度 | 密码必须满足最小 8 位，含大小写字母和数字 | `AUTH_101` |
| BR-AUTH-006 | 职责分离 | 日报提交者不得同时是审核者 | `BIZ_001` |

### 4.2 BR-USER（用户角色） → [详细规则](BR-USER.md)

> **关联 SoT**: MASTER.md v4.9 §2.4

| 规则ID | 规则名称 | 约束描述 | 违反错误码 |
|--------|----------|----------|-----------|
| BR-USER-001 | 角色枚举固定 | 系统仅允许 6 个业务角色 | `AUTH_403` |
| BR-USER-002 | 角色不可为空 | 用户必须分配至少一个角色 | `BIZ_002` |
| BR-USER-003 | 角色变更审计 | 角色变更必须记录操作人和时间戳 | `SYS_500` |
| BR-USER-004 | 禁止自我提权 | 用户不得修改自己的角色 | `AUTH_500` |
| BR-USER-005 | admin 角色限制 | admin 角色仅用于系统配置，不得参与业务操作 | `AUTH_403` |

### 4.3 BR-PROJ（项目管理） → [详细规则](BR-PROJ.md)

> **关联 SoT**: STATE_MACHINE.md v2.9 §5

| 规则ID | 规则名称 | 约束描述 | 违反错误码 |
|--------|----------|----------|-----------|
| BR-PROJ-001 | 项目必须有负责人 | 每个项目必须关联一个 project_owner | `BIZ_002` |
| BR-PROJ-002 | 结算模式不可变 | 项目创建后结算模式（per_lead/fee_rate）不得修改 | `BIZ_001` |
| BR-PROJ-003 | 状态流转合法性 | 项目状态流转必须符合 STATE_MACHINE.md v2.9 §5 | `BIZ_301` |
| BR-PROJ-004 | 归档不可逆 | 项目状态为 archived 后不得变更 | `BIZ_302` |
| BR-PROJ-005 | 冷启动期定义 | 新项目上线前 7 天为冷启动期 | - |
| BR-PROJ-006 | 预算必须大于零 | 项目预算字段必须为正数 | `BIZ_001` |
| BR-PROJ-007 | 单粉价格必须大于零 | per_lead 模式下单粉价格必须为正数 | `BIZ_001` |
| BR-PROJ-008 | 服务费率范围 | fee_rate 模式下服务费率必须在 0-100% 之间 | `BIZ_001` |

### 4.4 BR-ACCT（广告账户） → [详细规则](BR-ACCT.md)

> **关联 SoT**: DATA_SCHEMA.md v5.7

| 规则ID | 规则名称 | 约束描述 | 违反错误码 |
|--------|----------|----------|-----------|
| BR-ACCT-001 | 账户必须归属渠道 | 每个广告账户必须关联一个渠道 | `BIZ_002` |
| BR-ACCT-002 | 账户分配唯一性 | 同一时间点，一个账户仅能分配给一个投手 | `BIZ_003` |
| BR-ACCT-003 | 账户状态同步 | 账户状态必须与平台实际状态保持同步 | `SYS_500` |
| BR-ACCT-004 | 余额不可为负 | 账户余额不得为负数 | `BIZ_100` |
| BR-ACCT-005 | 分配记录审计 | 账户分配变更必须记录操作人和时间戳 | `SYS_500` |
| BR-ACCT-006 | 停用账户禁止操作 | 状态为 disabled 的账户不得进行消耗操作 | `BIZ_301` |

### 4.5 BR-FIN（财务流程） → [详细规则](BR-FIN.md)

> **关联 SoT**: DATA_SCHEMA.md v5.7 §3.4.4（账本规则）, STATE_MACHINE.md v2.9 §9
> **业务参考**: BR-FIN.md v1.1（三本账体系）

**三本账体系**（来源: BR-FIN.md v1.1）：

| 账本 | 记录内容 | 余额含义 |
|------|----------|----------|
| 预付款账本 | 客户付给我们的钱 | 还"欠"客户多少（待消耗） |
| 充值账本 | 我们充给代理商的钱 | 累计投入多少 |
| 押款账本 | 充值 - 消耗 | 押在代理商的钱（资金占用） |

| 规则ID | 规则名称 | 约束描述 | 违反错误码 |
|--------|----------|----------|-----------|
| BR-FIN-001 | 充值必须申请 | 所有充值必须通过申请流程 | `BIZ_201` |
| BR-FIN-002 | 充值审批人 | 充值申请必须由 finance 审批 | `AUTH_500` |
| BR-FIN-003 | 大额充值 | 超过阈值的充值必须由 ceo 最终批准 | `AUTH_500` |
| BR-FIN-004 | 预收款非收入 | 预收款在履约完成前必须记为负债 | `BIZ_301` |
| BR-FIN-005 | 消耗不含手续费 | 平台消耗金额不得包含手续费 | `BIZ_302` |
| BR-FIN-006 | 可用资金公式 | 可用资金 = opening_balance + Σtopup - Σad_spend | `BIZ_303` |
| BR-FIN-007 | 锁定后不可改 | 账本锁定后不得修改，仅能红冲 | `BIZ_401` |
| BR-FIN-008 | 红冲必须有理由 | 红冲操作必须提供 ref_id 和 reason | `BIZ_402` |
| BR-FIN-009 | 三本账原则 | 预付款/充值/押款账本必须分开记录 | `BIZ_403` |
| BR-FIN-010 | 资金流水审计 | 所有资金变动必须记录完整审计轨迹 | `SYS_500` |

### 4.6 BR-RPT（日报管理） → [详细规则](BR-RPT.md)

> **关联 SoT**: STATE_MACHINE.md v2.9 §8
> **业务参考**: BR-RPT.md v1.1（日报数据流与状态机）

**日报三层数据**（来源: BR-RPT.md v1.1）：

| 数据层 | 来源 | 内容 | 性质 |
|--------|------|------|------|
| 申报数据 | 投手填报 | 消耗、成效、进粉 | 参考值 |
| 实际数据 | 平台拉取 + PM核对 | 真实消耗、真实成效 | 成本计算依据 |
| 结算数据 | PM确认（与客户对账后） | 有效线索数、结算金额 | 收入计算依据 |

**日报状态机**（来源: STATE_MACHINE.md v2.9 §8）：

```
raw_submitted → trend_pending → trend_ok/trend_flagged
                                        ↓
                               trend_resolved
                                        ↓
                               final_pending → final_confirmed → final_locked
```

| 规则ID | 规则名称 | 约束描述 | 违反错误码 |
|--------|----------|----------|-----------|
| BR-RPT-001 | 日报提交人 | 日报必须由 pitcher 提交 | `AUTH_500` |
| BR-RPT-002 | 日报审核人 | 日报必须由 project_owner 审核 | `AUTH_500` |
| BR-RPT-003 | 提交审核分离 | 日报提交者不得同时是审核者 | `BIZ_001` |
| BR-RPT-004 | 状态流转合法性 | 日报状态流转必须符合 STATE_MACHINE.md v2.9 §8 | `BIZ_301` |
| BR-RPT-005 | 三数据流定义 | 日报必须区分 raw/real/final 三数据流 | `BIZ_001` |
| BR-RPT-006 | raw 数据提交者 | raw 数据（conversions_raw）由 pitcher 填报 | `AUTH_500` |
| BR-RPT-007 | real 数据提交者 | real 数据（real_spend）由 project_owner 录入 | `AUTH_500` |
| BR-RPT-008 | final 数据提交者 | final 数据（conversions_final）由 project_owner 录入 | `AUTH_500` |
| BR-RPT-009 | final 数据不可改 | conversions_final 锁定后不得修改 | `BIZ_301` |

### 4.7 BR-RECON（对账流程） → [详细规则](BR-RECON.md)

> **关联 SoT**: STATE_MACHINE.md v2.9 §10

| 规则ID | 规则名称 | 约束描述 | 违反错误码 |
|--------|----------|----------|-----------|
| BR-RECON-001 | 对账周期 | 对账必须按月执行 | `BIZ_601` |
| BR-RECON-002 | 对账发起人 | 对账必须由 finance 发起 | `AUTH_500` |
| BR-RECON-003 | 差异阈值 | 差异超过阈值必须人工确认 | `BIZ_602` |
| BR-RECON-004 | 对账状态流转 | 对账状态流转必须符合 STATE_MACHINE.md v2.9 §10 | `BIZ_301` |
| BR-RECON-005 | 完成后不可逆 | 对账状态为 completed 后不得变更 | `BIZ_301` |
| BR-RECON-006 | 差异必须记录 | 对账差异必须记录明细和原因 | `SYS_500` |
| BR-RECON-007 | 调整必须审批 | 对账调整必须由 finance 审批 | `AUTH_500` |

### 4.8 BR-DATA（数据完整性） → [详细规则](BR-DATA.md)

> **关联 SoT**: DATA_SCHEMA.md v5.7

| 规则ID | 规则名称 | 约束描述 | 违反错误码 |
|--------|----------|----------|-----------|
| BR-DATA-001 | 外键完整性 | 所有外键引用必须指向存在的记录 | `SYS_001` |
| BR-DATA-002 | 时间戳必填 | created_at 和 updated_at 必须自动填充 | `SYS_002` |
| BR-DATA-003 | 金额精度 | 金额字段必须使用 DECIMAL(15,2) | `BIZ_001` |
| BR-DATA-004 | 软删除原则 | 业务数据仅允许软删除（deleted_at） | `SYS_003` |
| BR-DATA-005 | 枚举值校验 | 所有枚举字段必须校验合法性 | `BIZ_001` |

### 4.9 BR-PROFIT（利润统计） → [详细规则](BR-PROFIT.md)

> **关联 SoT**: DATA_SCHEMA.md v5.7 §3.4.4（账本规则）, §3.6（利润统计表）
> **业务参考**: BR-PROFIT.md v1.2（三种定价模式）
> **v5.2 更新**: 成本公式新增开户费，新增公司利润规则

| 规则ID | 规则名称 | 约束描述 | 违反错误码 |
|--------|----------|----------|-----------|
| BR-PROFIT-001 | 收入公式（per_lead） | 收入 = conversions_final × 单粉价格 | `BIZ_701` |
| BR-PROFIT-002 | 收入公式（fee_rate） | 收入 = 广告消耗 × 服务费率 | `BIZ_701` |
| BR-PROFIT-003 | 收入公式（tiered） | 收入 = Σ(各档位线索数 × 该档单价) | `BIZ_701` |
| BR-PROFIT-004 | 项目成本公式 | **项目总支出 = ad_spend × (1+代理商费率) + 开户费** | `BIZ_702` |
| BR-PROFIT-005 | 项目毛利公式 | **项目毛利 = 收入 - 项目总支出（含手续费）** | `BIZ_703` |
| BR-PROFIT-006 | CPL 公式 | CPL = 消耗 / 进粉 | `BIZ_704` |
| BR-PROFIT-007 | 低量标记 | 进粉数 < 5 时，CPL 必须标记为「低量不稳定」 | - |
| BR-PROFIT-008 | 公司利润公式 | **公司利润 = Σ项目毛利 - 运营成本(含广告配套) - 投手提成** | `BIZ_705` |

**定价模式说明**（来源: BR-PROFIT.md v1.2）：
| 模式 | 公式 | 适用场景 |
|------|------|----------|
| 固定单价 (per_lead) | 收入 = 线索数 × 单价 | 标准化市场、稳定客户 |
| 阶梯定价 (tiered) | 收入 = Σ(档位线索 × 档位单价) | 高价值市场、大客户 |
| 服务费 (fee_rate) | 收入 = 消耗 × (1 + 费率) | 测试期、低风险偏好客户 |

**v5.2 利润计算说明**：
```
┌─────────────────────────────────────────────────────────────────┐
│  【项目层面】                                                    │
│  项目总支出 = 平台广告消耗 × (1 + 代理商费率) + 开户费           │
│  项目毛利 = 客户实际收款 - 项目总支出                            │
│                                                                 │
│  【公司层面】                                                    │
│  公司毛利 = Σ 各项目毛利                                        │
│  运营成本 = 人力 + 办公 + 广告配套 + 其他                       │
│  公司净利润 = 公司毛利 - 运营成本 - 投手提成                    │
│                                                                 │
│  ⚠️ 关键：手续费已在项目总支出中，不再单独从公司利润扣除        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 第五章 规则覆盖与测试状态

| 模块ID | 规则总数 | 已实现 | 已测试 | 覆盖率 |
|--------|----------|--------|--------|--------|
| BR-AUTH | 6 | 6 | 6 | 100% |
| BR-USER | 5 | 5 | 5 | 100% |
| BR-PROJ | 8 | 8 | 6 | 75% |
| BR-ACCT | 6 | 6 | 4 | 67% |
| BR-FIN | 10 | 8 | 6 | 60% |
| BR-RPT | 9 | 9 | 7 | 78% |
| BR-RECON | 7 | 5 | 3 | 43% |
| BR-DATA | 5 | 5 | 5 | 100% |
| BR-PROFIT | 8 | 6 | 2 | 25% |
| **合计** | **64** | **58** | **44** | **69%** |

---

## 第六章 Agents 使用说明

> **引用**: AGENTS.md v1.1

### 6.1 可用 Agents

| Agent ID | 名称 | 用途 | 关联规则模块 |
|----------|------|------|--------------|
| `daily_report_agent` | 日报处理 | 自动汇总日报数据 | BR-RPT |
| `reconciliation_agent` | 对账处理 | 辅助对账流程 | BR-RECON |
| `profit_calc_agent` | 利润计算 | 执行利润统计 | BR-PROFIT |
| `alert_agent` | 异常告警 | 监控规则违反 | BR-DATA |

### 6.2 Agent 调用约束

| 约束ID | 约束描述 |
|--------|----------|
| AGENT-001 | Agent 不得自动做管理裁决 |
| AGENT-002 | Agent 执行结果必须记录审计日志 |
| AGENT-003 | Agent 发现异常必须通知人工处理 |
| AGENT-004 | Agent 不得绕过权限校验 |

---

## 第七章 变更历史

### v5.2 (2026-01-12)

- **BR-PROFIT 利润计算规则更新**（对齐 PRD v5.2 财务模块修正）：
  - BR-PROFIT-004: 成本公式 → 项目成本公式（含开户费）
    - 旧: `成本 = ad_spend + 手续费`
    - 新: `项目总支出 = ad_spend × (1+代理商费率) + 开户费`
  - BR-PROFIT-005: 毛利公式 → 项目毛利公式（明确含手续费）
    - 旧: `毛利 = 收入 - 成本`
    - 新: `项目毛利 = 收入 - 项目总支出（含手续费）`
  - BR-PROFIT-008: **新增** 公司利润公式
    - `公司利润 = Σ项目毛利 - 运营成本(含广告配套) - 投手提成`
- **规则数量更新**: BR-PROFIT 7→8 条，合计 63→64 条
- **新增利润计算说明框图**: 明确项目层/公司层分离

### v5.1 (2026-01-02)

- **SoT 版本对齐**: 修复所有互锁引用版本不一致
  - MASTER.md v4.8 → v4.9
  - STATE_MACHINE.md v2.8 → v2.9
  - DATA_SCHEMA.md v5.6 → v5.7
  - AUTH_SPEC.md v2.1 → v2.2
  - API_SOT.md v9.4 → v9.6
- **断链引用修复**: 移除不存在的 BUSINESS_LOGIC_FRAMEWORK.md 引用
  - §2.1-2.3 角色章节：Framework → MASTER.md v4.9 / AUTH_SPEC.md v2.2
  - §4.5 BR-FIN：Framework §5.2 → BR-FIN.md v1.1
  - §4.6 BR-RPT：Framework §6.2-6.3 → BR-RPT.md v1.1 / STATE_MACHINE.md v2.9
  - §4.9 BR-PROFIT：Framework §1.3 → BR-PROFIT.md v1.2

### v5.0 (2026-01-02)

- **完全对齐 BUSINESS_LOGIC_FRAMEWORK.md v2.1**:
  - Framework v2.1 已对齐系统 6 角色架构（移除 supervisor，日报审核归 project_owner）
- **§2 角色与权限章节重构**:
  - §2.1 角色表新增「核心职责」「关键指标」「决策权限」列
  - 新增 §2.2 角色职能详细描述（CEO、项目负责人、财务、投手、户管）
  - 新增 §2.3 权限矩阵（数据可见性 + 操作权限表）
- **BR-FIN 更新**:
  - 「双账本原则」升级为「三本账体系」（预付款账本、充值账本、押款账本）
  - BR-FIN-009 名称变更：双账本原则 → 三本账原则
- **BR-RPT 更新**:
  - 新增「日报三层数据」表（申报数据、实际数据、结算数据）
  - 新增「日报状态机」完整流程图（8 状态 + Phase 1 简化说明）
- 元数据业务参考版本更新：Framework v2.0 → v2.1

### v4.9 (2026-01-02)

- **部分对齐 BUSINESS_LOGIC_FRAMEWORK.md v2.0**:
  - 新增 BR-PROFIT-003: 阶梯定价模式 (tiered pricing)
  - BR-PROFIT 规则数 6→7
  - 添加三种定价模式说明表（来源: Framework §1.3）
- **Framework 历史参考说明**:
  - 在角色定义章节添加 Framework 历史参考说明
  - 明确 Framework 为业务逻辑抽象框架，系统实现以 SoT 6 角色为准
- 元数据新增 `业务参考` 字段

### v4.8 (2025-12-31)

- **SoT 版本对齐**: 修复所有互锁引用版本不一致问题
  - STATE_MACHINE.md v2.7 → v2.8
  - DATA_SCHEMA.md v5.6（保持，未升级到 v5.7）
  - AUTH_SPEC.md v2.2 → v2.1
  - ERROR_CODES_SOT.md v2.3 → v2.2（并统一文件名）
- **移除 LEDGER_SOT.md 引用**: 账本规则已整合到 DATA_SCHEMA.md v5.6 §3.4.4
- **错误码对齐 ERROR_CODES_SOT.md v2.2**:
  - `STATE_001`/`STATE_002` → `BIZ_301`/`BIZ_302`（状态转换错误）
  - `BIZ_101`（语义冲突）→ `BIZ_001`/`BIZ_003`/`BIZ_100`（按场景区分）
  - `BIZ_501` → `BIZ_001`（三数据流定义）
  - `BIZ_401` → `BIZ_301`（锁定后不可改）
- ASDD 元数据同步更新

### v4.7 (2025-12-27)

- **新增子模块文档链接**: 所有 9 个 BR-*.md 子模块已生成并链接
- 第三章规则模块导航表增加「子模块文档」列
- 第四章各模块标题增加详细规则链接
- ASDD 元数据增加子模块 path 和 version 字段
- 子模块清单：
  - BR-AUTH.md v1.0（6 规则）
  - BR-USER.md v1.0（5 规则）
  - BR-PROJ.md v1.0（8 规则）
  - BR-ACCT.md v1.0（6 规则）
  - BR-FIN.md v1.0（10 规则）
  - BR-RPT.md v1.0（9 规则）
  - BR-RECON.md v1.0（7 规则）
  - BR-DATA.md v1.0（5 规则）
  - BR-PROFIT.md v1.0（6 规则）

### v4.6 (2025-12-27)

- **角色对齐 PRD v5.1 + MASTER v4.6+**: 业务层 7→6 角色（移除 supervisor，职责合并到 project_owner）。
- BR-RPT-002: 日报审核人由 supervisor 变更为 project_owner
- BR-RPT-007/008: real/final 数据提交者由 supervisor 变更为 project_owner
- 更新技术层角色映射：data_operator → project_owner
- 新增旧角色兼容映射表
- 对齐互锁 SoT 版本：MASTER v4.7, STATE_MACHINE v2.8, DATA_SCHEMA v5.6, ERROR_CODES v2.2

### v4.5 (2025-12-26)

- 新增 BR-PROFIT 模块（利润统计规则）
- 更新 BR-FIN 模块：新增双账本原则（BR-FIN-009）
- 新增 Agents 使用说明章节

### v4.1 (2025-12-24)

- 更新 BR-RPT 模块：三数据流定义
- 新增 BR-DATA 模块（数据完整性规则）
- 完善规则覆盖与测试状态

### v4.0 (2025-12-20)

- 初始版本
- 定义 9 个规则模块
- 建立 SoT 互锁引用体系

---

**文档性质**: 项目强制规范
**执行级别**: 强制执行
**违规处理**: PR 拒绝 / 代码回滚
**最后更新**: 2026-01-12
**版本**: v5.2 (BR-PROFIT 利润公式更新，对齐 PRD v5.2)
