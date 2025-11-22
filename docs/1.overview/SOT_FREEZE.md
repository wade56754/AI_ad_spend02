# SoT Freeze v1.0 Declaration
#
# AI广告代投系统 SoT 文档体系冻结声明

> **版本**: v1.0
> **发布日期**: 2025-01-23
> **状态**: ✅ 正式冻结（Production Freeze）
> **生效范围**: 14 个 SoT 文档
> **维护团队**: 系统架构团队

---

## 📌 执行摘要

本文档宣布 AI广告代投系统 SoT 文档体系 v1.0 进入**正式冻结状态**。所有业务逻辑、技术规范、状态机定义已完成一致性校验，可作为生产环境开发与上线的唯一真相源。

**核心结论**:
- ✅ 14个SoT文档已完成版本对齐
- ✅ 所有跨文档引用已消除版本冲突
- ✅ 核心业务规则已建立仲裁链
- ✅ 状态机、数据模型、API规范达成内部一致
- ✅ 可进入生产环境开发阶段

---

## 1. 冻结范围（Freeze Scope）

### 1.1 冻结的 SoT 文档清单（14个）

以下文档自本声明发布之日起进入**冻结状态（Frozen）**，任何变更需遵循 RFC（Request For Change）流程：

#### Tier 1: 系统全局视图（3个文档）

| 文档名称 | 最终版本 | 路径 | 状态 |
|---------|---------|------|------|
| MASTER_SPEC.md | v1.1 | `docs/1.overview/MASTER_SPEC.md` | ✅ Frozen |
| SYSTEM_OVERVIEW.md | v1.1 | `docs/1.overview/SYSTEM_OVERVIEW.md` | ✅ Frozen |
| PROJECT_RULES.md | v3.0 | `docs/1.overview/PROJECT_RULES.md` | ✅ Frozen |

#### Tier 2: SoT 文档（11个文档）

| 文档名称 | 最终版本 | 路径 | 状态 |
|---------|---------|------|------|
| DATA_SCHEMA.md | v5.2 | `docs/2.sot/DATA_SCHEMA.md` | ✅ Frozen |
| STATE_MACHINE.md | v2.6 | `docs/2.sot/STATE_MACHINE.md` | ✅ Frozen |
| API_SOT.md | v3.0 | `docs/2.sot/API_SOT.md` | ✅ Frozen |
| AUTH_SPEC.md | v2.0 | `docs/2.sot/AUTH_SPEC.md` | ✅ Frozen |
| BUSINESS_RULES.md | v3.1 | `docs/2.sot/BUSINESS_RULES.md` | ✅ Frozen |
| ERROR_CODES_SOT.md | v2.1 | `docs/2.sot/ERROR_CODES_SOT.md` | ✅ Frozen |
| LEDGER_SOT.md | v2.0 | `docs/2.sot/LEDGER_SOT.md` | ✅ Frozen |
| DAILY_REPORT_SOT.md | v1.0 | `docs/2.sot/DAILY_REPORT_SOT.md` | ✅ Frozen |
| TRANSFER_SOT.md | v1.0 | `docs/2.sot/TRANSFER_SOT.md` | ✅ Frozen |
| RECONCILIATION_SOT.md | v1.0 | `docs/2.sot/RECONCILIATION_SOT.md` | ✅ Frozen |
| RLS_POLICIES_SOT.md | v2.1 | `docs/2.sot/RLS_POLICIES_SOT.md` | ✅ Frozen |

### 1.2 冻结基准日期

**基准日期**: 2025-01-23
**Git Commit**: 待提交
**基准分支**: `master`

---

## 2. SoT 仲裁链（Arbitration Chain）

### 2.1 文档优先级层级

根据 MASTER_SPEC.md v1.1 定义，当跨文档规则冲突时，按以下优先级仲裁：

```
MASTER_SPEC.md v1.1 (P0 - 系统架构总纲)
    ↓
├─ STATE_MACHINE.md v2.6 (P1 - 状态流转唯一来源)
├─ DATA_SCHEMA.md v5.2 (P1 - 数据模型唯一来源)
├─ BUSINESS_RULES.md v3.1 (P1 - 业务规则唯一来源)
    ↓
├─ API_SOT.md v3.0 (P1 - API 规范唯一来源)
├─ AUTH_SPEC.md v2.0 (P1 - 认证授权唯一来源)
├─ ERROR_CODES_SOT.md v2.1 (P1 - 错误码唯一来源)
    ↓
├─ LEDGER_SOT.md v2.0 (P2 - 账本模块唯一来源)
├─ DAILY_REPORT_SOT.md v1.0 (P2 - 日报模块唯一来源)
├─ TRANSFER_SOT.md v1.0 (P2 - 充值迁移模块唯一来源)
├─ RECONCILIATION_SOT.md v1.0 (P2 - 对账模块唯一来源)
├─ RLS_POLICIES_SOT.md v2.1 (P2 - RLS 策略唯一来源)
    ↓
└─ 代码实现（遵循以上全部 SoT）
```

### 2.2 核心仲裁规则

| 领域 | 唯一真相源 | 冲突处理原则 |
|-----|-----------|-------------|
| **系统架构设计** | MASTER_SPEC.md v1.1 | 最高优先级，其他文档必须对齐 |
| **状态机定义** | STATE_MACHINE.md v2.6 | 所有状态枚举、流转规则以此为准 |
| **数据库字段** | DATA_SCHEMA.md v5.2 | 所有表结构、字段类型以此为准 |
| **业务规则** | BUSINESS_RULES.md v3.1 | 所有 BR-* 规则以此为准 |
| **API 路由** | API_SOT.md v3.0 | 所有端点、Schema 定义以此为准 |
| **角色权限** | AUTH_SPEC.md v2.0 | 所有角色、权限矩阵以此为准 |
| **错误码** | ERROR_CODES_SOT.md v2.1 | 所有错误码编号、HTTP状态以此为准 |
| **账本规则** | LEDGER_SOT.md v2.0 | 双账本、红冲逻辑以此为准 |
| **日报流程** | DAILY_REPORT_SOT.md v1.0 | 三数据流、风控规则以此为准 |
| **充值流程** | TRANSFER_SOT.md v1.0 | 充值/迁移逻辑以此为准 |
| **对账流程** | RECONCILIATION_SOT.md v1.0 | 对账批次、差异处理以此为准 |
| **RLS 策略** | RLS_POLICIES_SOT.md v2.1 | Row-Level Security 规则以此为准 |

---

## 3. 核心版本对齐清单

### 3.1 状态机版本统一（STATE_MACHINE v2.6）

✅ **所有文档引用 STATE_MACHINE 版本已统一为 v2.6**

| 文档 | 引用位置 | 版本 | 状态 |
|-----|---------|------|------|
| MASTER_SPEC.md | § 3.2.4 | v2.6 | ✅ |
| API_SOT.md | § 2.3, § 13.1.2 | v2.6 | ✅ |
| DAILY_REPORT_SOT.md | § 1.2, § 5.1 | v2.6 | ✅ |
| TRANSFER_SOT.md | § 1.2 | v2.6 | ✅ |
| RECONCILIATION_SOT.md | § 头部引用 | v2.6 | ✅ |
| LEDGER_SOT.md | § 1.2 | v2.6 | ✅ |
| ERROR_CODES_SOT.md | § 4.6 | v2.6 | ✅ |
| RLS_POLICIES_SOT.md | § 头部引用 | v2.6 | ✅ |

**关键内容**:
- 8状态粉数确认状态机（日报）
- 5状态充值审批状态机（充值）
- 5状态对账批次状态机（对账）
- 5状态迁移流程状态机（死号迁移）

### 3.2 数据模型版本统一（DATA_SCHEMA v5.2）

✅ **所有文档引用 DATA_SCHEMA 版本已统一为 v5.2**

| 文档 | 引用位置 | 版本 | 状态 |
|-----|---------|------|------|
| MASTER_SPEC.md | § 3.2.3 | v5.2 | ✅ |
| API_SOT.md | § 2.3 | v5.2 | ✅ |
| DAILY_REPORT_SOT.md | § 1.2, § 3.1 | v5.2 | ✅ |
| TRANSFER_SOT.md | § 1.2, § 3 | v5.2 | ✅ |
| RECONCILIATION_SOT.md | § 头部引用, § 3.1 | v5.2 | ✅ |
| LEDGER_SOT.md | § 1.2, § 3 | v5.2 | ✅ |
| AUTH_SPEC.md | § 1.3, § 2.1 | v5.2 | ✅ |
| RLS_POLICIES_SOT.md | § 头部引用 | v5.2 | ✅ |
| BUSINESS_RULES.md | § 规则维护指南 | v5.2 | ✅ |

**关键表结构**（共25+表）:
- `daily_reports` (raw_spend字段已统一)
- `ledger_entries` (双账本结构)
- `topup_requests` (充值申请)
- `reconciliation_batches` (对账批次)
- `users`, `projects`, `ad_accounts`, `channels`, `suppliers`

### 3.3 核心业务规则版本（BUSINESS_RULES v3.1）

✅ **所有业务规则索引指向归档路径已统一标注**

| 规则模块 | 文件路径 | 状态标注 |
|---------|---------|---------|
| BR-AUTH | `docs/archive/old_core/rules/BR-AUTH.md` | ✅ 归档版（现行有效） |
| BR-USER | `docs/archive/old_core/rules/BR-USER.md` | ✅ 归档版（现行有效） |
| BR-PROJ | `docs/archive/old_core/rules/BR-PROJ.md` | ✅ 归档版（现行有效） |
| BR-CHAN | `docs/archive/old_core/rules/BR-CHAN.md` | ✅ 归档版（现行有效） |
| BR-ACCT | `docs/archive/old_core/rules/BR-ACCT.md` | ✅ 归档版（现行有效） |
| BR-FIN | `docs/archive/old_core/rules/BR-FIN.md` | ✅ 归档版（现行有效） |
| BR-RECON | `docs/archive/old_core/rules/BR-RECON.md` | ✅ 归档版（现行有效） |
| BR-RPT | `docs/archive/old_core/rules/BR-RPT.md` | ✅ 归档版（现行有效） |
| BR-DATA | `docs/archive/old_core/rules/BR-DATA.md` | ✅ 归档版（现行有效） |

**说明**: 归档规则当前仍为有效业务规则，未来迁移至现行 SoT 目录时需同步更新 BUSINESS_RULES.md 索引。

### 3.4 状态机枚举完整定义

✅ **API_SOT.md 已补充所有状态机枚举定义**

| 状态机 | Python Literal | 引用来源 |
|-------|---------------|---------|
| TopupStatus | `Literal["draft", "pending_review", ...]` | STATE_MACHINE.md § 4 |
| ReconciliationStatus | `Literal["draft", "pending_review", ...]` | STATE_MACHINE.md § 5 |
| TransferStatus | `Literal["draft", "approved", ...]` | STATE_MACHINE.md § 6 |
| DailyReportStatus | `Literal["raw_submitted", "trend_pending", ...]` | STATE_MACHINE.md § 8 |

---

## 4. 冻结原则（Freeze Principles）

### 4.1 变更禁止规则

从 2025-01-23 起，以下变更**严格禁止**，除非通过 RFC 流程：

| 禁止变更类型 | 说明 | 违规后果 |
|------------|------|---------|
| **修改字段名称** | DATA_SCHEMA.md v5.2 所有字段名锁定 | PR 自动拒绝 |
| **修改状态枚举** | STATE_MACHINE.md v2.6 所有状态值锁定 | PR 自动拒绝 |
| **修改错误码** | ERROR_CODES_SOT.md v2.1 所有错误码锁定 | PR 自动拒绝 |
| **修改 API 路由** | API_SOT.md v3.0 所有端点路径锁定 | PR 自动拒绝 |
| **修改角色定义** | AUTH_SPEC.md v2.0 角色枚举锁定 | PR 自动拒绝 |
| **修改业务规则** | BUSINESS_RULES.md v3.1 所有 BR-* 规则锁定 | 需产品审批 |

### 4.2 允许的变更类型

以下变更**允许**，但需记录变更日志：

| 允许变更类型 | 审批流程 | 变更记录 |
|------------|---------|---------|
| **新增字段** | 架构师审批 + RFC | DATA_SCHEMA.md 变更日志 |
| **新增状态** | 架构师审批 + RFC | STATE_MACHINE.md 变更日志 |
| **新增错误码** | Tech Lead 审批 | ERROR_CODES_SOT.md 变更日志 |
| **新增 API 端点** | 架构师审批 + RFC | API_SOT.md 变更日志 |
| **新增业务规则** | 产品负责人审批 + RFC | BUSINESS_RULES.md 变更日志 |
| **文档勘误** | Tech Lead 审批 | Git commit message |

### 4.3 RFC（Request For Change）流程

所有 SoT 文档变更必须遵循以下流程：

```
1. 创建 RFC 文档
   ├─ 变更原因（业务需求/技术债务/bug修复）
   ├─ 变更范围（影响哪些 SoT 文档）
   ├─ 兼容性影响（是否 Breaking Change）
   ├─ 迁移计划（数据库迁移/代码重构）
   └─ 回滚方案

2. 团队评审
   ├─ 架构师审批（P0/P1文档）
   ├─ Tech Lead 审批（P2文档）
   ├─ 产品负责人审批（业务规则变更）
   └─ 安全审计（涉及权限/RLS变更）

3. 执行变更
   ├─ 更新 SoT 文档
   ├─ 更新相关引用文档
   ├─ 生成数据库迁移脚本（如需）
   ├─ 更新测试用例
   └─ 更新变更日志

4. 验证与发布
   ├─ 运行全量测试
   ├─ Code Review
   ├─ 合并到 master 分支
   └─ 更新文档版本号
```

---

## 5. 版本升级路径

### 5.1 文档版本号规则

采用 **语义化版本（Semantic Versioning）** 规则：

```
<MAJOR>.<MINOR>.<PATCH>

MAJOR: 重大架构变更（Breaking Change）
MINOR: 新增功能、新增字段、新增状态（向后兼容）
PATCH: 文档勘误、说明优化（无功能变更）
```

**示例**:
- `v5.2 → v5.3`: 新增字段 (MINOR)
- `v5.3 → v6.0`: 修改主键策略 (MAJOR)
- `v5.3 → v5.3.1`: 修正拼写错误 (PATCH)

### 5.2 下一版本规划（v1.1）

**预计发布时间**: 2025-Q2

**计划变更**:
- [ ] RLS_POLICIES_SOT.md: 启用 RLS（`ENABLE_RLS=true`）
- [ ] API_SOT.md: 补充分页性能优化规范
- [ ] LEDGER_SOT.md: 增强红冲审计规则
- [ ] DAILY_REPORT_SOT.md: 新增趋势风控算法参数配置

**变更类型**: MINOR（向后兼容）

---

## 6. 风险清单与现状

### 6.1 已知风险（已缓解）

| 风险编号 | 风险描述 | 影响范围 | 缓解措施 | 当前状态 |
|---------|---------|---------|---------|---------|
| R001 | DATA_SCHEMA 字段名历史不一致 | 日报模块 | 已统一为 `raw_spend` | ✅ 已解决 |
| R002 | STATE_MACHINE 版本引用不一致 | 全局 | 已统一为 v2.6 | ✅ 已解决 |
| R003 | BUSINESS_RULES 归档路径模糊 | 业务规则 | 已明确标注"归档版（现行有效）" | ✅ 已解决 |
| R004 | API_SOT 缺少状态机枚举定义 | API 模块 | 已补充所有状态机 Literal | ✅ 已解决 |
| R005 | SYSTEM_OVERVIEW Ledger 示例错误 | 文档示例 | 已修正 COST 金额方向为负 | ✅ 已解决 |

### 6.2 接受的技术债务

| 债务编号 | 债务描述 | 影响范围 | 计划解决版本 |
|---------|---------|---------|-------------|
| TD001 | RLS 策略尚未启用（`ENABLE_RLS=false`） | 权限控制 | v1.1 |
| TD002 | `transfer_requests` 表未在 DATA_SCHEMA 定义 | 死号迁移 | v1.1 |
| TD003 | BUSINESS_RULES 归档规则待迁移至现行目录 | 业务规则 | v2.0 |
| TD004 | 部分模块缺少性能基准测试 | 全局 | v1.2 |

---

## 7. 影响评估

### 7.1 对开发流程的影响

| 影响维度 | 影响说明 | 应对措施 |
|---------|---------|---------|
| **后端开发** | 所有 API 必须严格遵循 API_SOT.md v3.0 | 代码审查时强制检查 SoT 对齐 |
| **前端开发** | 所有 Schema 定义必须从 API_SOT.md 生成 | 使用 OpenAPI Generator 自动生成 |
| **数据库变更** | 所有迁移脚本必须对齐 DATA_SCHEMA.md v5.2 | 迁移脚本生成前必须读取 DATA_SCHEMA |
| **测试用例** | 所有状态流转测试必须覆盖 STATE_MACHINE.md v2.6 | 测试矩阵自动生成工具 |
| **文档维护** | 任何 SoT 变更需通过 RFC 流程 | 文档变更清单 + 审批记录 |

### 7.2 对生产环境的影响

| 影响维度 | 影响说明 | 风险等级 |
|---------|---------|---------|
| **数据库层** | 无影响（文档冻结不影响已有数据） | 🟢 低 |
| **API 层** | 无影响（API 路由无变更） | 🟢 低 |
| **业务逻辑** | 无影响（业务规则无变更） | 🟢 低 |
| **权限控制** | 无影响（RLS 当前未启用） | 🟢 低 |

**结论**: 本次 SoT Freeze 为**文档层冻结**，对现有生产环境**无任何影响**。

---

## 8. 上线检查清单

### 8.1 SoT 对齐检查

- [x] ✅ 所有 STATE_MACHINE 引用已统一为 v2.6
- [x] ✅ 所有 DATA_SCHEMA 引用已统一为 v5.2
- [x] ✅ 所有 BUSINESS_RULES 路径已标注归档状态
- [x] ✅ API_SOT 已补充所有状态机枚举定义
- [x] ✅ SYSTEM_OVERVIEW 示例金额方向已修正
- [x] ✅ 无 docs/core/* 旧路径引用
- [x] ✅ 所有跨文档引用版本一致

### 8.2 代码对齐检查（生产环境上线前必查）

- [ ] 🔲 `backend/models/*.py` 字段名对齐 DATA_SCHEMA.md v5.2
- [ ] 🔲 `backend/enums.py` 状态枚举对齐 STATE_MACHINE.md v2.6
- [ ] 🔲 `backend/core/error_codes.py` 错误码对齐 ERROR_CODES_SOT.md v2.1
- [ ] 🔲 `backend/routers/*.py` 路由对齐 API_SOT.md v3.0
- [ ] 🔲 `frontend/types/*.ts` Schema 对齐 API_SOT.md v3.0
- [ ] 🔲 数据库迁移脚本对齐 DATA_SCHEMA.md v5.2

### 8.3 测试覆盖检查

- [ ] 🔲 单元测试覆盖率 > 80%
- [ ] 🔲 状态机流转测试覆盖 STATE_MACHINE.md 所有白名单
- [ ] 🔲 API 集成测试覆盖 API_SOT.md 所有端点
- [ ] 🔲 业务规则测试覆盖 BUSINESS_RULES.md 核心规则

---

## 9. 维护责任与联系方式

### 9.1 文档维护责任人

| 文档类别 | 负责团队 | 联系方式 |
|---------|---------|---------|
| MASTER_SPEC, SYSTEM_OVERVIEW | 架构团队 | architecture@team |
| DATA_SCHEMA, STATE_MACHINE | 后端团队 | backend@team |
| API_SOT, AUTH_SPEC | 全栈团队 | fullstack@team |
| BUSINESS_RULES | 产品 + 架构 | product@team |
| 业务模块 SoT | 业务开发团队 | dev@team |

### 9.2 RFC 提交渠道

- **GitHub Issue**: 创建 Issue 并打上 `RFC` 标签
- **邮件讨论**: 发送至 architecture@team
- **周会讨论**: 每周一 10:00 架构评审会

---

## 10. 附录

### 10.1 修复清单（v1.0 Freeze前）

本次冻结前完成的关键修复：

| 修复编号 | 修复内容 | 影响文档 | 提交日期 |
|---------|---------|---------|---------|
| FIX-001 | DATA_SCHEMA `spend` → `raw_spend` 字段名统一 | DATA_SCHEMA, SYSTEM_OVERVIEW | 2025-01-22 |
| FIX-002 | SYSTEM_OVERVIEW Ledger COST 金额方向修正为负 | SYSTEM_OVERVIEW | 2025-01-22 |
| FIX-003 | BUSINESS_RULES 归档路径标注"现行有效" | BUSINESS_RULES | 2025-01-22 |
| FIX-004 | API_SOT 补充 TRANSFER_STATUS 枚举定义 | API_SOT | 2025-01-22 |
| FIX-005 | 所有 STATE_MACHINE v2.5 → v2.6 统一 | 全局 8 个文档 | 2025-01-23 |
| FIX-006 | 所有 DATA_SCHEMA v5.0/v5.1 → v5.2 统一 | 全局 11 个文档 | 2025-01-23 |

### 10.2 Git Commit 记录

**Freeze基准 Commit**:
```bash
# 待提交
git add docs/1.overview/SOT_FREEZE.md
git add docs/2.sot/*.md
git commit -m "docs: SoT Freeze v1.0 - 完成版本对齐与一致性校验

- 统一 STATE_MACHINE 引用为 v2.6
- 统一 DATA_SCHEMA 引用为 v5.2
- 修正 BUSINESS_RULES 归档路径标注
- 补充 API_SOT 状态机枚举定义
- 创建 SOT_FREEZE.md 冻结声明

Refs: #SoT-Freeze-v1.0"
```

### 10.3 相关文档链接

| 文档名称 | 路径 |
|---------|------|
| 文档中心导航 | `docs/README.md` |
| 系统根规范 | `docs/1.overview/MASTER_SPEC.md` |
| 项目开发规则 | `docs/1.overview/PROJECT_RULES.md` |
| 状态机定义 | `docs/2.sot/STATE_MACHINE.md` |
| 数据模型 | `docs/2.sot/DATA_SCHEMA.md` |

---

## 🎯 结论

**AI广告代投系统 SoT 文档体系 v1.0 正式冻结**。

所有业务逻辑、技术规范已完成一致性校验，可作为生产环境开发与上线的唯一真相源。后续任何变更需遵循 RFC 流程，确保文档体系的稳定性与可追溯性。

**冻结生效日期**: 2025-01-23
**下次审查日期**: 2025-Q2（v1.1规划）
**反馈渠道**: GitHub Issue + architecture@team

---

**END OF DECLARATION**
