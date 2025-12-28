# BUSINESS_RULES.md - 业务规则索引（SoT Index）

> **文档版本**: v4.7
> **status**: active
> **owner**: wade
> **last_reviewed**: 2025-12-27
> **文档类型**: 业务规则唯一真相源索引（SoT Index）
> **规范级别**: 强制执行
> **基准**: PRD v2.2, MASTER.md v4.6

---

## 互锁 SoT 引用

> **本文档是业务规则的索引层，不承载具体实现逻辑。**
> 所有规则的具体定义必须由子模块（BR-*.md）实现。

| SoT 文档 | 版本 | 职责 | 引用关系 |
|----------|------|------|----------|
| MASTER.md | v4.6 | 架构宪法 | 本文档的上游约束 |
| STATE_MACHINE.md | v2.7 | 状态机规范 | BR-RPT/BR-FIN/BR-RECON 依赖 |
| DATA_SCHEMA.md | v5.6 | 数据模型 | 所有 BR-* 字段定义依赖 |
| ERROR_CODES.md | v2.3 | 错误码规范 | 规则违反时的错误码映射 |
| LEDGER_SOT.md | v1.2 | 账本规则 | BR-FIN/BR-RECON 依赖 |
| AUTH_SPEC.md | v2.2 | 权限规范 | BR-AUTH/BR-USER 依赖 |
| API_SOT.md | v9.4 | API 规范 | 规则的 API 层实现 |

---

## ASDD 链路元数据

```yaml
asdd_version: "1.0"
document_type: "sot_index"
upstream:
  - path: "docs/MASTER.md"
    version: "v4.6"
    relation: "constrained_by"
downstream:
  - path: "docs/sot/STATE_MACHINE.md"
    version: "v2.7"
    relation: "implements"
  - path: "docs/sot/DATA_SCHEMA.md"
    version: "v5.6"
    relation: "implements"
  - path: "docs/sot/ERROR_CODES.md"
    version: "v2.3"
    relation: "implements"
  - path: "docs/sot/AUTH_SPEC.md"
    version: "v2.2"
    relation: "implements"
  - path: "docs/sot/LEDGER_SOT.md"
    version: "v1.2"
    relation: "implements"
modules:
  - id: "BR-AUTH"
    name: "认证授权"
    path: "docs/sot/BR-AUTH.md"
    version: "v1.0"
  - id: "BR-USER"
    name: "用户角色"
    path: "docs/sot/BR-USER.md"
    version: "v1.0"
  - id: "BR-PROJ"
    name: "项目管理"
    path: "docs/sot/BR-PROJ.md"
    version: "v1.0"
  - id: "BR-ACCT"
    name: "广告账户"
    path: "docs/sot/BR-ACCT.md"
    version: "v1.0"
  - id: "BR-FIN"
    name: "财务流程"
    path: "docs/sot/BR-FIN.md"
    version: "v1.0"
  - id: "BR-RPT"
    name: "日报管理"
    path: "docs/sot/BR-RPT.md"
    version: "v1.0"
  - id: "BR-RECON"
    name: "对账流程"
    path: "docs/sot/BR-RECON.md"
    version: "v1.0"
  - id: "BR-DATA"
    name: "数据完整性"
    path: "docs/sot/BR-DATA.md"
    version: "v1.0"
  - id: "BR-PROFIT"
    name: "利润统计"
    path: "docs/sot/BR-PROFIT.md"
    version: "v1.0"
```

---

## 第一章 开发铁律

> **引用**: MASTER.md v4.6 §7 AI 防幻觉原则

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

> **PRD v2.2 变更**: 移除 supervisor 角色，其职责合并到 project_owner

| 角色ID | 中文名 | 职责范围 | 权限级别 |
|--------|--------|----------|----------|
| `ceo` | 老板 | 资金安全、公司盈亏、最终决策 | L6 (最高) |
| `project_owner` | 项目负责人 | 项目盈亏、资金使用效率、日报审核 | L5 |
| `finance` | 财务 | 资金出入准确、数据真实、对账 | L4 |
| `pitcher` | 投手 | CPL 达标、日报准确、执行投放 | L2 |
| `account_manager` | 户管 | 账户分配、账户状态监控 | L3 |
| `admin` | 管理员 | 系统配置（不参与业务） | L6 (系统) |

### 2.2 技术层角色映射

> **引用**: AUTH_SPEC.md v2.2 §2.2, DATA_SCHEMA.md v5.6

| 技术层角色 | 业务层角色 | 说明 |
|-----------|-----------|------|
| `admin` | `ceo`, `admin` | 系统管理权限 |
| `finance` | `finance` | 财务权限 |
| `data_operator` | `project_owner` | PRD v2.2: 原 supervisor 已移除 |
| `account_manager` | `account_manager` | 账户管理权限 |
| `media_buyer` | `pitcher` | 投放执行权限 |

### 2.3 旧角色兼容映射

| 旧角色 | 新角色 | 变更版本 |
|--------|--------|----------|
| `supervisor` | `project_owner` | PRD v2.2 |
| `media_buyer` | `pitcher` | v4.0 |
| `data_operator` | `project_owner` | PRD v2.2 |

---

## 第三章 规则模块导航

| 模块ID | 模块名称 | 规则数量 | 子模块文档 | 关联 SoT | 状态 |
|--------|----------|----------|------------|----------|------|
| BR-AUTH | 认证授权 | 6 | [BR-AUTH.md](BR-AUTH.md) | AUTH_SPEC.md v2.2 | active |
| BR-USER | 用户角色 | 5 | [BR-USER.md](BR-USER.md) | MASTER.md v4.6 §2.4 | active |
| BR-PROJ | 项目管理 | 8 | [BR-PROJ.md](BR-PROJ.md) | STATE_MACHINE.md v2.7 §5 | active |
| BR-ACCT | 广告账户 | 6 | [BR-ACCT.md](BR-ACCT.md) | DATA_SCHEMA.md v5.6 | active |
| BR-FIN | 财务流程 | 10 | [BR-FIN.md](BR-FIN.md) | LEDGER_SOT.md v1.2 | active |
| BR-RPT | 日报管理 | 9 | [BR-RPT.md](BR-RPT.md) | STATE_MACHINE.md v2.7 §8 | active |
| BR-RECON | 对账流程 | 7 | [BR-RECON.md](BR-RECON.md) | STATE_MACHINE.md v2.7 §10 | active |
| BR-DATA | 数据完整性 | 5 | [BR-DATA.md](BR-DATA.md) | DATA_SCHEMA.md v5.6 | active |
| BR-PROFIT | 利润统计 | 6 | [BR-PROFIT.md](BR-PROFIT.md) | LEDGER_SOT.md v1.2 | active |

> **子模块文档说明**: 每个 BR-*.md 子模块包含该模块的完整规则定义，包括：
> - 业务场景、详细约束、前置条件
> - 错误码映射（对齐 ERROR_CODES.md v2.3）
> - Test Intent（测试意图）
> - 规则依赖关系

---

## 第四章 规则模块概览

### 4.1 BR-AUTH（认证授权） → [详细规则](BR-AUTH.md)

> **关联 SoT**: AUTH_SPEC.md v2.2

| 规则ID | 规则名称 | 约束描述 | 违反错误码 |
|--------|----------|----------|-----------|
| BR-AUTH-001 | 登录必须验证 | 所有 API 请求必须携带有效 JWT Token | `AUTH_400` |
| BR-AUTH-002 | Token 有效期 | Access Token 有效期不得超过 24 小时 | `AUTH_401` |
| BR-AUTH-003 | 角色唯一性 | 每个用户在同一项目中仅能拥有一个角色 | `AUTH_403` |
| BR-AUTH-004 | 权限继承禁止 | 角色权限不得跨层级继承 | `AUTH_500` |
| BR-AUTH-005 | 密码强度 | 密码必须满足最小 8 位，含大小写字母和数字 | `AUTH_101` |
| BR-AUTH-006 | 职责分离 | 日报提交者不得同时是审核者 | `BIZ_001` |

### 4.2 BR-USER（用户角色） → [详细规则](BR-USER.md)

> **关联 SoT**: MASTER.md v4.6 §2.4

| 规则ID | 规则名称 | 约束描述 | 违反错误码 |
|--------|----------|----------|-----------|
| BR-USER-001 | 角色枚举固定 | 系统仅允许 6 个业务角色 | `AUTH_403` |
| BR-USER-002 | 角色不可为空 | 用户必须分配至少一个角色 | `BIZ_002` |
| BR-USER-003 | 角色变更审计 | 角色变更必须记录操作人和时间戳 | `SYS_500` |
| BR-USER-004 | 禁止自我提权 | 用户不得修改自己的角色 | `AUTH_500` |
| BR-USER-005 | admin 角色限制 | admin 角色仅用于系统配置，不得参与业务操作 | `AUTH_403` |

### 4.3 BR-PROJ（项目管理） → [详细规则](BR-PROJ.md)

> **关联 SoT**: STATE_MACHINE.md v2.7 §5

| 规则ID | 规则名称 | 约束描述 | 违反错误码 |
|--------|----------|----------|-----------|
| BR-PROJ-001 | 项目必须有负责人 | 每个项目必须关联一个 project_owner | `BIZ_002` |
| BR-PROJ-002 | 结算模式不可变 | 项目创建后结算模式（per_lead/fee_rate）不得修改 | `BIZ_101` |
| BR-PROJ-003 | 状态流转合法性 | 项目状态流转必须符合 STATE_MACHINE.md v2.7 §5 | `STATE_001` |
| BR-PROJ-004 | 归档不可逆 | 项目状态为 archived 后不得变更 | `STATE_002` |
| BR-PROJ-005 | 冷启动期定义 | 新项目上线前 7 天为冷启动期 | - |
| BR-PROJ-006 | 预算必须大于零 | 项目预算字段必须为正数 | `BIZ_001` |
| BR-PROJ-007 | 单粉价格必须大于零 | per_lead 模式下单粉价格必须为正数 | `BIZ_001` |
| BR-PROJ-008 | 服务费率范围 | fee_rate 模式下服务费率必须在 0-100% 之间 | `BIZ_001` |

### 4.4 BR-ACCT（广告账户） → [详细规则](BR-ACCT.md)

> **关联 SoT**: DATA_SCHEMA.md v5.6

| 规则ID | 规则名称 | 约束描述 | 违反错误码 |
|--------|----------|----------|-----------|
| BR-ACCT-001 | 账户必须归属渠道 | 每个广告账户必须关联一个渠道 | `BIZ_002` |
| BR-ACCT-002 | 账户分配唯一性 | 同一时间点，一个账户仅能分配给一个投手 | `BIZ_101` |
| BR-ACCT-003 | 账户状态同步 | 账户状态必须与平台实际状态保持同步 | `SYS_500` |
| BR-ACCT-004 | 余额不可为负 | 账户余额不得为负数 | `BIZ_001` |
| BR-ACCT-005 | 分配记录审计 | 账户分配变更必须记录操作人和时间戳 | `SYS_500` |
| BR-ACCT-006 | 停用账户禁止操作 | 状态为 disabled 的账户不得进行消耗操作 | `STATE_002` |

### 4.5 BR-FIN（财务流程） → [详细规则](BR-FIN.md)

> **关联 SoT**: LEDGER_SOT.md v1.2, STATE_MACHINE.md v2.7 §9

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
| BR-FIN-009 | 双账本原则 | 项目账本与供应商账本必须分开记录 | `BIZ_403` |
| BR-FIN-010 | 资金流水审计 | 所有资金变动必须记录完整审计轨迹 | `SYS_500` |

### 4.6 BR-RPT（日报管理） → [详细规则](BR-RPT.md)

> **关联 SoT**: STATE_MACHINE.md v2.7 §8

| 规则ID | 规则名称 | 约束描述 | 违反错误码 |
|--------|----------|----------|-----------|
| BR-RPT-001 | 日报提交人 | 日报必须由 pitcher 提交 | `AUTH_500` |
| BR-RPT-002 | 日报审核人 | 日报必须由 project_owner 审核 | `AUTH_500` |
| BR-RPT-003 | 提交审核分离 | 日报提交者不得同时是审核者 | `BIZ_001` |
| BR-RPT-004 | 状态流转合法性 | 日报状态流转必须符合 STATE_MACHINE.md v2.7 §8 | `STATE_001` |
| BR-RPT-005 | 三数据流定义 | 日报必须区分 raw/real/final 三数据流 | `BIZ_501` |
| BR-RPT-006 | raw 数据提交者 | raw 数据（conversions_raw）由 pitcher 填报 | `AUTH_500` |
| BR-RPT-007 | real 数据提交者 | real 数据（real_spend）由 project_owner 录入 | `AUTH_500` |
| BR-RPT-008 | final 数据提交者 | final 数据（conversions_final）由 project_owner 录入 | `AUTH_500` |
| BR-RPT-009 | final 数据不可改 | conversions_final 锁定后不得修改 | `BIZ_401` |

### 4.7 BR-RECON（对账流程） → [详细规则](BR-RECON.md)

> **关联 SoT**: STATE_MACHINE.md v2.7 §10

| 规则ID | 规则名称 | 约束描述 | 违反错误码 |
|--------|----------|----------|-----------|
| BR-RECON-001 | 对账周期 | 对账必须按月执行 | `BIZ_601` |
| BR-RECON-002 | 对账发起人 | 对账必须由 finance 发起 | `AUTH_500` |
| BR-RECON-003 | 差异阈值 | 差异超过阈值必须人工确认 | `BIZ_602` |
| BR-RECON-004 | 对账状态流转 | 对账状态流转必须符合 STATE_MACHINE.md v2.7 §10 | `STATE_001` |
| BR-RECON-005 | 完成后不可逆 | 对账状态为 completed 后不得变更 | `STATE_002` |
| BR-RECON-006 | 差异必须记录 | 对账差异必须记录明细和原因 | `SYS_500` |
| BR-RECON-007 | 调整必须审批 | 对账调整必须由 finance 审批 | `AUTH_500` |

### 4.8 BR-DATA（数据完整性） → [详细规则](BR-DATA.md)

> **关联 SoT**: DATA_SCHEMA.md v5.6

| 规则ID | 规则名称 | 约束描述 | 违反错误码 |
|--------|----------|----------|-----------|
| BR-DATA-001 | 外键完整性 | 所有外键引用必须指向存在的记录 | `SYS_001` |
| BR-DATA-002 | 时间戳必填 | created_at 和 updated_at 必须自动填充 | `SYS_002` |
| BR-DATA-003 | 金额精度 | 金额字段必须使用 DECIMAL(15,2) | `BIZ_001` |
| BR-DATA-004 | 软删除原则 | 业务数据仅允许软删除（deleted_at） | `SYS_003` |
| BR-DATA-005 | 枚举值校验 | 所有枚举字段必须校验合法性 | `BIZ_001` |

### 4.9 BR-PROFIT（利润统计） → [详细规则](BR-PROFIT.md)

> **关联 SoT**: LEDGER_SOT.md v1.2, DATA_SCHEMA.md v5.6 §3.6

| 规则ID | 规则名称 | 约束描述 | 违反错误码 |
|--------|----------|----------|-----------|
| BR-PROFIT-001 | 收入公式（per_lead） | 收入 = conversions_final × 单粉价格 | `BIZ_701` |
| BR-PROFIT-002 | 收入公式（fee_rate） | 收入 = 广告消耗 × 服务费率 | `BIZ_701` |
| BR-PROFIT-003 | 成本公式 | 成本 = ad_spend + 手续费 | `BIZ_702` |
| BR-PROFIT-004 | 毛利公式 | 毛利 = 收入 - 成本 | `BIZ_703` |
| BR-PROFIT-005 | CPL 公式 | CPL = 消耗 / 进粉 | `BIZ_704` |
| BR-PROFIT-006 | 低量标记 | 进粉数 < 5 时，CPL 必须标记为「低量不稳定」 | - |

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
| BR-PROFIT | 6 | 4 | 2 | 33% |
| **合计** | **62** | **56** | **44** | **71%** |

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

- **角色对齐 PRD v2.2**: 业务层 7→6 角色（移除 supervisor，职责合并到 project_owner）
- BR-RPT-002: 日报审核人由 supervisor 变更为 project_owner
- BR-RPT-007/008: real/final 数据提交者由 supervisor 变更为 project_owner
- 更新技术层角色映射：data_operator → project_owner
- 新增旧角色兼容映射表
- 对齐互锁 SoT 版本：MASTER v4.6, STATE_MACHINE v2.7, DATA_SCHEMA v5.6, ERROR_CODES v2.3

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
**最后更新**: 2025-12-27
**版本**: v4.7 (新增子模块链接，对齐 MASTER.md v4.6, PRD v2.2)
