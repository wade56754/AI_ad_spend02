# 业务规则索引 (Business Rules Index)

> **文档版本**: v3.2  
> **status**: frozen  
> **owner**: wade  
> **last_reviewed**: 2025-12-07  
> **发布日期**: 2025-01-21  
> **文档状态**: ✅ 规则已模块化拆分；当前文件为索引  
> **维护团队**: 业务架构团队

---

## 📋 ASDD 链路元数据

### ASDD 层级定位

| 元数据项 | 值 |
|---------|-----|
| **asdd_layer** | `business_rules` |
| **layer_position** | Tier 2: Single Source of Truth (SoT) |
| **document_type** | SoT Index (索引文档) |
| **rules_sot_dir** | `docs/archive/old_core/rules/BR-*.md` (过渡模式，见下方说明) |

### 上游文档依赖 (Upstream SoT)

| 文档 | 版本 | 路径 | 引用关系 |
|------|------|------|---------|
| **MASTER.md** | v3.6 | `docs/1.overview/MASTER.md` | 架构宪法，业务规则必须遵循系统不变量 |
| **STATE_MACHINE.md** | v2.6 | `docs/2.sot/STATE_MACHINE.md` | 状态流转规则，业务规则需引用状态机定义 |
| **DATA_SCHEMA.md** | v5.2 | `docs/2.sot/DATA_SCHEMA.md` | 数据模型约束，业务规则需引用字段定义 |
| **ERROR_CODES_SOT.md** | v2.1 | `docs/2.sot/ERROR_CODES_SOT.md` | 错误码映射，业务规则需引用错误码定义 |
| **LEDGER_SOT.md** | v1.1 | `docs/2.sot/LEDGER_SOT.md` | 双账本规则，财务相关业务规则需引用 |
| **AUTH_SPEC.md** | v2.0 | `docs/2.sot/AUTH_SPEC.md` | 权限规范，认证授权相关业务规则需引用 |

### 下游目标 (Downstream Targets)

| 目标类型 | 路径/说明 | 用途 |
|---------|---------|------|
| **Service 层实现** | `backend/services/*` | 业务规则在 Service 层强制执行 |
| **API 路由层** | `backend/routers/*` | API 端点需遵循业务规则约束 |
| **测试用例** | `backend/tests/**/*.py` | 测试需覆盖业务规则验证 |
| **静态检查** | 代码审查、Linter 规则 | 开发铁律可通过静态检查工具验证 |
| **Freeze 报告** | `docs/4.testing/*_FREEZE_REPORT*.md` | 测试冻结报告需记录业务规则覆盖率 |

---

## 🔄 规则正文存储位置说明（过渡模式）

### 当前状态

**规则正文文件位置**: `docs/archive/old_core/rules/BR-*.md`

> **⚠️ 重要说明**: 虽然路径中包含 `archive/old_core`，但**这些规则文件是现行有效的业务规则正文**，并非废弃内容。当前处于**过渡模式**：
> - 规则正文暂时存放在 `docs/archive/old_core/rules/` 目录
> - 未来计划迁移至 `docs/2.sot/business_rules/BR-*.md` 或类似位置
> - 迁移完成后，本索引将同步更新路径引用

### 规则文件清单

| 模块代码 | 规则文件 | 状态 |
|---------|---------|------|
| BR-AUTH | `docs/archive/old_core/rules/BR-AUTH.md` | ✅ 现行有效 |
| BR-USER | `docs/archive/old_core/rules/BR-USER.md` | ✅ 现行有效 |
| BR-PROJ | `docs/archive/old_core/rules/BR-PROJ.md` | ✅ 现行有效 |
| BR-CHAN | `docs/archive/old_core/rules/BR-CHAN.md` | ✅ 现行有效 |
| BR-ACCT | `docs/archive/old_core/rules/BR-ACCT.md` | ✅ 现行有效 |
| BR-FIN | `docs/archive/old_core/rules/BR-FIN.md` | ✅ 现行有效 |
| BR-RECON | `docs/archive/old_core/rules/BR-RECON.md` | ✅ 现行有效 |
| BR-RPT | `docs/archive/old_core/rules/BR-RPT.md` | ✅ 现行有效 |
| BR-DATA | `docs/archive/old_core/rules/BR-DATA.md` | ✅ 现行有效 |

---

## 📌 文档说明

本文档是 **AI 广告代投系统** 业务规则的**索引导航文档**（Business Rules SoT Index）。

**核心规则已模块化拆分**到 `docs/archive/old_core/rules/BR-*.md` 文件中，每个模块一个文件。本文档仅作为导航入口，**不包含规则详细内容**。

如需查阅具体规则，请通过下方的**规则导航表**跳转到对应的模块文件。

---

## ⚡ 开发者必读：5大开发铁律

以下 5 条开发铁律是系统核心约束，违反将导致 P0 级别缺陷。所有开发人员必须严格遵守。

| 铁律 ID | 描述 | 绑定规则 ID | 下游检查 | 典型错误码 |
|---------|------|------------|---------|-----------|
| **DEV-001** | **金额必用 Decimal**：严禁使用 Float/Double，必须保留 2 位小数 | BR-FIN-003 | 静态检查：类型注解、数据库约束 | `VALIDATION_001` |
| **DEV-002** | **时间必用 UTC**：数据库存 TIMESTAMPTZ，后端用 `datetime.now(timezone.utc)` | BR-DATA-002 | 测试：时间字段时区验证 | `VALIDATION_002` |
| **DEV-003** | **核心数据禁删**：项目/账户/资金记录严禁物理删除，必须走归档/取消流程 | BR-DATA-001 | 测试：删除操作验证、数据库约束 | `BIZ_301` |
| **DEV-004** | **角色不可混用**：用户角色一旦创建，非 Admin 不可变更 | BR-AUTH-001 | 测试：角色变更权限验证 | `AUTH_500` |
| **DEV-005** | **终态不可回退**：充值/日报/对账一旦进入终态(Completed/final_locked/Closed)，数据即锁定，仅可通过红冲修正 | BR-RPT-004, BR-RPT-005, BR-FIN-002 | 测试：状态机流转验证、终态保护测试 | `STATE_400`, `BIZ_301` |

**检查方式**：
- **静态检查**: 代码审查、类型检查工具（mypy）、Linter 规则
- **测试验证**: 单元测试、集成测试、状态机测试
- **数据库约束**: CHECK 约束、外键约束、触发器

---

## 🗂️ 规则导航

### 核心业务模块

| 模块代码 | 模块名称 | 规则文件路径 | 优先级 | 状态 |
|---------|---------|-------------|-------|------|
| **BR-AUTH** | 认证与授权 | [docs/archive/old_core/rules/BR-AUTH.md](../archive/old_core/rules/BR-AUTH.md) | P0 | ✅ 归档版（现行有效） |
| **BR-USER** | 用户与角色 | [docs/archive/old_core/rules/BR-USER.md](../archive/old_core/rules/BR-USER.md) | P0 | ✅ 归档版（现行有效） |
| **BR-PROJ** | 项目管理 | [docs/archive/old_core/rules/BR-PROJ.md](../archive/old_core/rules/BR-PROJ.md) | P1 | ✅ 归档版（现行有效） |
| **BR-CHAN** | 渠道管理 | [docs/archive/old_core/rules/BR-CHAN.md](../archive/old_core/rules/BR-CHAN.md) | P1 | ✅ 归档版（现行有效） |
| **BR-ACCT** | 广告账户 | [docs/archive/old_core/rules/BR-ACCT.md](../archive/old_core/rules/BR-ACCT.md) | P1 | ✅ 归档版（现行有效） |
| **BR-FIN** | 财务流程 | [docs/archive/old_core/rules/BR-FIN.md](../archive/old_core/rules/BR-FIN.md) | P0 | ✅ 归档版（现行有效） |
| **BR-RECON** | 对账流程 | [docs/archive/old_core/rules/BR-RECON.md](../archive/old_core/rules/BR-RECON.md) | P1 | ✅ 归档版（现行有效） |
| **BR-RPT** | 日报管理 | [docs/archive/old_core/rules/BR-RPT.md](../archive/old_core/rules/BR-RPT.md) | P1 | ✅ 归档版（现行有效） |
| **BR-DATA** | 数据完整性 | [docs/archive/old_core/rules/BR-DATA.md](../archive/old_core/rules/BR-DATA.md) | P0 | ✅ 归档版（现行有效） |

**优先级说明**:
- **P0 (关键)**: 违反将导致系统安全风险、数据不一致或核心业务无法运行
- **P1 (重要)**: 违反将导致业务流程错误或用户体验严重下降
- **P2 (一般)**: 违反将导致数据质量问题或次要功能异常

---

## 📖 各模块规则概览

### BR-AUTH: 认证与授权规则
- BR-AUTH-001: 用户角色唯一性
- BR-AUTH-002: 密码强度要求
- BR-AUTH-003: 会话超时与续期
- BR-AUTH-004: 最小权限原则

**查看详情**: [docs/archive/old_core/rules/BR-AUTH.md](../archive/old_core/rules/BR-AUTH.md)

---

### BR-USER: 用户与角色管理规则
- BR-USER-001: 用户名唯一性
- BR-USER-002: 邮箱唯一性与验证
- BR-USER-003: 户管分配规则

**查看详情**: [docs/archive/old_core/rules/BR-USER.md](../archive/old_core/rules/BR-USER.md)

---

### BR-PROJ: 项目管理规则
- BR-PROJ-001: 项目创建权限约束
- BR-PROJ-003: 项目状态机流转规则
- BR-PROJ-004: 项目删除级联检查

**查看详情**: [docs/archive/old_core/rules/BR-PROJ.md](../archive/old_core/rules/BR-PROJ.md)

---

### BR-CHAN: 渠道管理规则
- BR-CHAN-001: 渠道创建与唯一性约束

**查看详情**: [docs/archive/old_core/rules/BR-CHAN.md](../archive/old_core/rules/BR-CHAN.md)

---

### BR-ACCT: 广告账户规则
- BR-ACCT-001: 账户创建与唯一性约束
- BR-ACCT-002: 账户状态机流转规则

**查看详情**: [docs/archive/old_core/rules/BR-ACCT.md](../archive/old_core/rules/BR-ACCT.md)

---

### BR-FIN: 财务管理规则
- BR-FIN-001: Topup 请求创建权限
- BR-FIN-002: 审批职责分离原则
- BR-FIN-003: 金额字段合规性约束
- BR-FIN-005: Topup 与 Ledger 双写一致性

**查看详情**: [docs/archive/old_core/rules/BR-FIN.md](../archive/old_core/rules/BR-FIN.md)

---

### BR-RECON: 对账管理规则
- BR-RECON-001: 对账批次创建约束
- BR-RECON-003: 差异处理与调账

**查看详情**: [docs/archive/old_core/rules/BR-RECON.md](../archive/old_core/rules/BR-RECON.md)

---

### BR-RPT: 日报管理规则
- BR-RPT-001: 日报提交约束
- BR-RPT-002: 日报审核权限
- BR-RPT-004: 日报终态保护规则
- BR-RPT-005: 粉数确认流程规则 ⭐ **NEW** (BRD v3.1对齐)

**查看详情**: [docs/archive/old_core/rules/BR-RPT.md](../archive/old_core/rules/BR-RPT.md)

---

### BR-DATA: 数据完整性规则
- BR-DATA-001: 外键约束与删除策略
- BR-DATA-002: 时间字段时区一致性

**查看详情**: [docs/archive/old_core/rules/BR-DATA.md](../archive/old_core/rules/BR-DATA.md)

---

## 📊 规则覆盖与测试状态

### 规则实施进度总览

| 模块 | 定义规则数 | 已测试 | 测试覆盖率 | 优先级 | 状态 |
|-----|----------|-------|----------|--------|------|
| BR-AUTH | 4 | 4 | 100% | P0 | ✅ 完成 |
| BR-USER | 3 | 3 | 100% | P0 | ✅ 完成 |
| BR-PROJ | 3 | 2 | 67% | P1 | 🟡 进行中 |
| BR-CHAN | 1 | 1 | 100% | P1 | ✅ 完成 |
| BR-ACCT | 2 | 2 | 100% | P1 | ✅ 完成 |
| BR-FIN | 4 | 3 | 75% | P0 | 🟡 进行中 |
| BR-RECON | 2 | 1 | 50% | P1 | 🟡 进行中 |
| BR-RPT | 4 | 3 | 75% | P1 | 🟡 进行中 |
| BR-DATA | 2 | 2 | 100% | P0 | ✅ 完成 |
| **总计** | **25** | **21** | **84%** | - | **🟢 良好** |

### 模块 → 测试文件映射

| 业务规则模块 | 主要测试文件 | 测试类型 | 说明 |
|------------|------------|---------|------|
| **BR-AUTH** | `backend/tests/test_authentication_api.py`<br>`backend/tests/test_auth_service.py`<br>`backend/tests/test_permissions.py`<br>`backend/tests/test_rbac_permissions.py` | API + Service + 权限 | 认证授权规则测试 |
| **BR-USER** | `backend/tests/test_permissions.py` | 权限 | 用户角色管理规则测试 |
| **BR-PROJ** | `backend/tests/test_project_api.py`<br>`backend/tests/test_project_service.py`<br>`backend/tests/test_project_permissions.py` | API + Service + 权限 | 项目管理规则测试 |
| **BR-CHAN** | `backend/tests/test_api_endpoints.py` | API | 渠道管理规则测试（集成在其他测试中） |
| **BR-ACCT** | `backend/tests/ad_accounts/test_ad_account_api.py`<br>`backend/tests/ad_accounts/test_ad_account_service.py` | API + Service | 广告账户规则测试 |
| **BR-FIN** | `backend/tests/test_topup_api.py`<br>`backend/tests/test_topup_service.py`<br>`backend/tests/test_topup_permissions.py`<br>`backend/tests/ledger/test_ledger_service.py`<br>`backend/tests/ledger/test_ledger_invariants.py` | API + Service + 权限 + 账本 | 财务流程规则测试（含双账本一致性） |
| **BR-RECON** | `backend/tests/test_reconciliation_api.py`<br>`backend/tests/test_reconciliation_service.py`<br>`backend/tests/test_reconciliation_permissions.py` | API + Service + 权限 | 对账流程规则测试 |
| **BR-RPT** | `backend/tests/test_daily_report_api.py`<br>`backend/tests/test_daily_report_service.py`<br>`backend/tests/test_daily_report_permissions.py`<br>`backend/tests/api/test_daily_report_flow_generated.py`<br>`backend/tests/api/test_trend_risk_flow_generated.py` | API + Service + 权限 + 流程 | 日报管理规则测试（含状态机流转） |
| **BR-DATA** | `backend/tests/test_models_crud.py`<br>`backend/tests/test_state_machine_transitions.py` | 数据完整性 + 状态机 | 数据完整性规则测试 |

**测试执行方式**:
```bash
# 执行特定模块的测试
python -m pytest backend/tests/test_topup_api.py -v  # BR-FIN
python -m pytest backend/tests/test_daily_report_api.py -v  # BR-RPT
python -m pytest backend/tests/test_authentication_api.py -v  # BR-AUTH

# 执行所有业务规则相关测试
python -m pytest backend/tests/ -k "topup or daily_report or auth or project or reconciliation" -v
```

### 规则引用链完整性

```
BR-{模块}-{序号} (业务规则定义)
    ↓ 引用架构设计
MASTER.md v3.6
    ↓ 引用状态机定义
STATE_MACHINE.md v2.6
    ↓ 引用数据结构
DATA_SCHEMA.md v5.2
    ↓ 引用错误码
ERROR_CODES_SOT.md v2.1
    ↓ 实现代码
backend/services/*
    ↓ 测试验证
backend/tests/**
```

**必须引用的 SoT 文档**:
- **MASTER.md** v3.6 - 架构宪法，系统不变量
- **STATE_MACHINE.md** v2.6 - 状态流转规则（如涉及状态字段）
- **DATA_SCHEMA.md** v5.2 - 数据模型和字段定义
- **ERROR_CODES_SOT.md** v2.1 - 错误码定义
- **LEDGER_SOT.md** v1.1 - 双账本规则（财务相关规则）
- **AUTH_SPEC.md** v2.0 - 权限规范（认证授权相关规则）

**引用格式示例**:
```markdown
**引用**: `MASTER.md` v3.6 第 1.3 节 - 双账本架构规范
**引用**: `STATE_MACHINE.md` v2.6 第 8 章 - 粉数确认状态机
**引用**: `DATA_SCHEMA.md` v5.2 第 3.3.1 节 - `daily_reports` 表
**引用**: `ERROR_CODES_SOT.md` v2.1 - STATE_400, TREND_001
**引用**: `LEDGER_SOT.md` v1.1 第 3 节 - 双账本隔离规则
```

### 下一步行动

- [ ] BR-PROJ-002: 补充测试用例（项目归档级联检查）
- [ ] BR-FIN-004: 补充测试用例（Ledger 双写一致性）
- [ ] BR-RECON-002: 补充测试用例（差异处理与调账）
- [ ] BR-RPT-003: 补充测试用例（日报数据完整性）

---

## 🛠️ 规则维护指南

### 如何新增业务规则

**规则正文维护**: 请直接编辑对应的 `docs/archive/old_core/rules/BR-{模块}.md` 文件。

**本索引文档更新**: 新增规则后，请在本索引的对应模块概览中添加新规则编号和名称，并更新规则数量统计。

#### 1. 确定规则所属模块

根据业务领域选择对应的模块代码:
- 认证授权相关 → `BR-AUTH`
- 用户角色相关 → `BR-USER`
- 项目管理相关 → `BR-PROJ`
- 渠道管理相关 → `BR-CHAN`
- 广告账户相关 → `BR-ACCT`
- 财务流程相关 → `BR-FIN`
- 对账流程相关 → `BR-RECON`
- 日报管理相关 → `BR-RPT`
- 数据完整性相关 → `BR-DATA`

#### 2. 编辑对应的规则文件

打开 `docs/archive/old_core/rules/BR-{模块}.md` 文件，按照 v2.0 规则模板新增规则:

```markdown
## BR-{模块}-{序号}: {规则名称}

### 业务场景
{规则的业务背景}

### 详细约束
{具体的约束条件}

### 错误码映射
{违反规则时的错误码}

### Test Intent
{测试用例描述}
```

#### 3. 确保 SoT 引用链完整

新增规则时必须遵循完整的 SoT 引用链（见上方"规则引用链完整性"章节）。

#### 4. 更新本索引文档

在对应模块的规则列表中添加新规则编号和名称，并更新规则数量统计。

### 如何修改现有规则

1. 直接编辑 `docs/archive/old_core/rules/BR-{模块}.md` 文件
2. 更新规则内容，保持模板结构完整
3. 同步更新 `ERROR_CODES_SOT.md` 和 `DATA_SCHEMA.md`（如有变更）
4. 更新或新增测试用例
5. 如规则数量或测试覆盖率发生变化，更新本索引的统计信息

### 规则文档模板

每个规则文件都遵循统一的 v2.0 模板结构:

- **规则总览**: 规则列表表格
- **规则详细内容**: 每条规则包含
  - 业务场景
  - 详细约束
  - 代码示例（Python + FastAPI）
  - 错误码映射
  - Test Intent（测试用例）
- **参考文档**: 引用的 SoT 文档链接

### 本索引文档的维护范围

**可以更新**:
- ✅ 规则模块概览（新增规则编号和名称）
- ✅ 规则数量统计
- ✅ 测试覆盖率信息
- ✅ 模块 → 测试文件映射
- ✅ 元数据（版本号、最后更新日期等）
- ✅ 导航链接和说明文字

**不应包含**:
- ❌ 具体业务规则的详细定义（规则正文在 BR-*.md 中）
- ❌ 字段级别的详细定义（字段定义在 DATA_SCHEMA.md 中）

---

## 📚 关联文档

本业务规则索引与以下文档形成完整的知识网络:

```
业务规则索引 (本文档)
    ├─→ 规则子模块      (docs/archive/old_core/rules/BR-*.md)   - 规则详细定义
    ├─→ 架构宪法        (MASTER.md v3.6)                        - 系统不变量
    ├─→ 状态机 SoT      (STATE_MACHINE.md v2.6)                 - 状态流转规则
    ├─→ 数据模型 SoT    (DATA_SCHEMA.md v5.2)                   - 数据约束基础
    ├─→ 错误码 SoT      (ERROR_CODES_SOT.md v2.1)               - 错误码映射基础
    ├─→ 账本 SoT        (LEDGER_SOT.md v1.1)                    - 双账本规则
    └─→ 权限策略 SoT    (AUTH_SPEC.md v2.0)                     - 权限控制规则
```

---

## 📖 术语词汇表

本节定义文档中使用的关键业务术语，确保术语一致性。

> **注**: 本术语表为快速参考，**字段定义的唯一真相源请查阅 DATA_SCHEMA.md**，**状态流转请查阅 STATE_MACHINE.md**。

### 通用业务术语

| 中文术语 | 英文术语 | 使用场景 | 说明 |
|---------|---------|---------|------|
| 用户 | User | 泛指系统用户 | 通用指代，无特定技术含义 |
| 角色 | Role | 泛指用户角色 | 通用指代，无特定技术含义 |

### 业务流程术语

| 英文术语 | 中文名称 | 说明 |
|---------|---------|------|
| `Topup Request` | 充值申请 | 向广告账户充值的申请流程 |
| `Reconciliation Batch` | 对账批次 | 定期对账的批次单位 |
| `Daily Report` | 日报 | 每日广告消费报告 |
| `Ad Account` | 广告账户 | 广告投放平台账户 |
| `Channel` | 渠道 | 广告投放平台（如 Meta、Google Ads） |
| `Project` | 项目 | 广告投放项目 |
| `Ledger Entry` | 账本记录 | 财务账本条目 |
| `Separation of Duties (SOD)` | 职责分离 | 申请人、审核人、批准人必须不同 |
| `Dual-write` | 双写 | 同时写入两个表以保持一致性 |
| `Trend Risk Control` | 趋势风控 | 粉数确认过程中的异常趋势检查 |
| `Reversal` | 红冲 | final_locked 后的修正机制 |
| `PROJECT Ledger` | 项目账本 | 记录项目收入的账本（粉数计费） |
| `SUPPLIER Ledger` | 供应商账本 | 记录供应商成本的账本（真实消耗） |
| `Three Data Flows` | 三数据流 | raw/real/final 数据流分离设计 |

### 状态术语（快速参考）

| 状态值 | 中文名称 | 适用实体 | 说明 |
|-------|---------|---------|------|
| `draft` | 草稿 | 项目/充值/对账批次 | 未提交状态 |
| `active` | 活跃/激活 | 项目/账户/渠道 | 正常运行状态 |
| `suspended` | 暂停 | 项目/账户 | 临时暂停 |
| `archived` | 已归档 | 项目/渠道/账户 | 历史数据归档 |
| `completed` | 已完成 | 充值 | 充值完成（终态） |
| `rejected` | 已拒绝 | 充值 | 充值拒绝（终态） |
| `cancelled` | 已取消 | 充值 | 充值取消（终态） |
| `testing` | 测试中 | 账户 | 账户测试阶段 |
| `dead` | 死亡/不可用 | 账户 | 不可恢复状态 |
| `inactive` | 未激活 | 渠道 | 停用状态 |
| `reviewing` | 复核中 | 对账批次 | 复核中 |
| `closed` | 已关闭 | 对账批次 | 对账批次关闭（终态） |
| `pending_review` | 待复核 | 充值 | 等待数据复核 |
| `finance_approve` | 财务批准 | 充值 | 财务已批准 |
| `paid` | 已支付 | 充值 | 支付完成 |
| `raw_submitted` | 已提交原始粉数 | 日报 | 投手提交 raw 粉数 |
| `trend_pending` | 趋势检查中 | 日报 | 等待风控检查 |
| `trend_ok` | 趋势正常 | 日报 | 风控通过 |
| `trend_flagged` | 趋势异常 | 日报 | 需人工复核 |
| `trend_resolved` | 趋势已复核 | 日报 | 运营确认正常 |
| `final_pending` | 待确认 final | 日报 | 等待 final 粉数确认 |
| `final_confirmed` | final 已确认 | 日报 | 最终粉数已确认 |
| `final_locked` | 计费锁定 | 日报 | 已进入计费（终态） |

> **完整状态定义**: 请查阅 `STATE_MACHINE.md` v2.6 获取所有状态的完整定义、合法流转和约束条件。

### 金额/数值术语（快速参考）

| 术语 | 中文 | 字段名 | 数据类型 | 说明 |
|-----|------|-------|---------|------|
| `amount` | 金额 | `topup_requests.amount`, `ledger_entries.amount` | DECIMAL(15,2) | 通用金额字段 |
| `balance` | 余额 | `projects.balance` | DECIMAL(15,2) | 项目余额 |
| `spend` | 原始消耗 | `daily_reports.spend` | DECIMAL(15,2) | 投手提交的原始消耗（raw_spend） |
| `real_spend` | 真实消耗 | `daily_reports.real_spend` | DECIMAL(15,2) | 运营录入的真实消耗（成本核算基准） |
| `conversions` | 转化次数 | `daily_reports.conversions` | INTEGER | 通用转化次数 |
| `conversions_raw` | 原始粉数 | `daily_reports.conversions_raw` | INTEGER | 投手提交的原始粉数（趋势风控用） |
| `conversions_final` | 最终粉数 | `daily_reports.conversions_final` | INTEGER | 运营确认的最终粉数（计费基准） |
| `unit_price` | 单粉价格 | `projects.unit_price`, `daily_reports.unit_price` | DECIMAL(15,2) | 项目单粉价格（Per Lead） |
| `budget_total` | 项目预算 | `projects.budget_total` | DECIMAL(15,2) | 项目总预算 |
| `spend_limit` | 消耗限额 | `ad_accounts.spend_limit` | DECIMAL(15,2) | 账户消耗限额 |

> **完整字段定义**: 请查阅 `DATA_SCHEMA.md` v5.2 获取所有字段的完整定义、约束条件和数据类型。

### 角色术语

| 英文角色 | 中文名称 | 代码值 | 权限级别 |
|---------|---------|-------|---------|
| `admin` | 系统管理员 | `"admin"` | 最高权限 |
| `finance` | 财务 | `"finance"` | 财务审批权限 |
| `data_operator` | 户管/数据操作员 | `"data_operator"` | 数据审核权限 |
| `account_manager` | 客户经理 | `"account_manager"` | 账户管理权限 |
| `media_buyer` | 投手/媒体采购 | `"media_buyer"` | 基础操作权限 |

> **完整权限定义**: 请查阅 `AUTH_SPEC.md` v2.0 获取所有角色的完整权限矩阵和 RBAC 规则。

**术语使用原则**:
1. **数据模型/表名/字段名**: 必须使用英文代码格式（如 `users.role`）
2. **业务概念说明**: 使用中文（如"用户角色必须唯一"）
3. **混合场景**: 优先英文，中文解释（如"User（用户）表"）
4. **代码示例**: 严格使用英文代码

---

## 🤖 给 Agents 的使用说明

### 如何查找业务规则

当需要查询业务规则时，请按以下路径获取信息：

1. **从本索引开始**: 查看 `BUSINESS_RULES.md` 的"规则导航"章节，确定规则所属模块
2. **跳转到规则正文**: 根据模块代码（如 BR-FIN），打开对应的 `docs/archive/old_core/rules/BR-{模块}.md` 文件
3. **查阅相关 SoT**: 规则正文中会引用相关 SoT 文档，根据需要查阅：
   - 状态相关 → `STATE_MACHINE.md` v2.6
   - 字段相关 → `DATA_SCHEMA.md` v5.2
   - 错误码相关 → `ERROR_CODES_SOT.md` v2.1
   - 账本相关 → `LEDGER_SOT.md` v1.1
   - 权限相关 → `AUTH_SPEC.md` v2.0

### 开发铁律检查

在生成代码时，必须遵守"开发者必读：5大开发铁律"章节中的约束：
- 金额字段使用 `Decimal` 类型
- 时间字段使用 UTC 时区
- 核心数据禁止物理删除
- 角色变更权限检查
- 终态数据保护

### 测试文件定位

根据业务规则模块，可在"模块 → 测试文件映射"章节中找到对应的测试文件，用于：
- 理解规则的实际实现
- 查看测试用例示例
- 验证规则覆盖情况

### 规则引用格式

在代码注释或文档中引用业务规则时，使用格式：
```
Ref: BR-{模块}-{序号}
例如: Ref: BR-FIN-003 (金额字段合规性约束)
```

---

## 📝 变更历史

### v3.2 (2025-12-07)
**ASDD 链路对齐优化**
- ✅ 新增 ASDD 链路元数据（asdd_layer, upstream_docs, downstream_targets）
- ✅ 明确规则正文存储位置的"过渡模式"说明
- ✅ 将开发铁律重构为结构化表格（含铁律 ID、绑定规则、下游检查、错误码）
- ✅ 新增"模块 → 测试文件映射"表格，提供可追踪的测试入口
- ✅ 精简术语表，明确字段定义以 DATA_SCHEMA.md 为准
- ✅ 更新维护指南，明确本索引文档的可更新范围
- ✅ 统一 SoT 文档引用名称（MASTER.md, STATE_MACHINE.md, DATA_SCHEMA.md, ERROR_CODES_SOT.md）
- ✅ 新增"给 Agents 的使用说明"章节
- ✅ 更新规则引用链，包含完整的上游 SoT 文档

### v3.1 (2025-01-21)
**上线级优化** - MASTER_SPEC v2.2 对齐
- ✅ 替换所有 AI_AD_SYSTEM_MAIN_DOCUMENT.md 引用为 AI_AD_SYSTEM_MASTER_SPEC_v2.2.md
- ✅ 更新状态术语表: 删除旧日报/充值状态，新增 8 状态粉数确认状态机
- ✅ 扩展金额术语表: 新增 conversions_raw/final, real_spend, unit_price 等 10 个字段
- ✅ 扩展业务流程术语: 新增趋势风控、红冲、双账本、三数据流等 4 个概念
- ✅ 新增规则覆盖与测试状态总表
- ✅ 验证 5 条开发铁律对应的规则引用完整性

### v3.0 (2025-01-20)
**重大重构** - 规则模块化拆分
- ✅ 将 BUSINESS_RULES.md 重构为轻量级索引文档
- ✅ 核心规则拆分到 `docs/archive/old_core/rules/` 目录下的独立文件
- ✅ 完成 9 个模块文件创建（BR-AUTH, BR-USER, BR-PROJ, BR-CHAN, BR-ACCT, BR-FIN, BR-RECON, BR-RPT, BR-DATA）
- ✅ 保留术语词汇表作为全局参考
- ✅ 新增规则维护指南

### v2.0 (2025-01-19)
**规则优化版本** - 核心规则完整定义
- ✅ 完成 BR-AUTH-001~004 核心认证规则
- ✅ 完成 BR-USER-001~003 用户管理规则
- ✅ 建立规则模板 v2.0 标准
- ✅ 建立术语词汇表

### v1.0 (2025-01-15)
- 初始化规则框架和模板体系

---

## 📧 联系方式

**维护团队**: 业务架构团队  
**文档仓库**: `docs/2.sot/BUSINESS_RULES.md`  
**规则目录**: `docs/archive/old_core/rules/`（过渡模式，未来将迁移）

---

> **版权声明**: 本文档为 AI 广告代投系统的内部技术文档，仅供授权人员使用。
