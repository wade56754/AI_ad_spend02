# 文档架构审计报告

> **版本**: v1.0
> **审计日期**: 2025-12-22
> **审计类型**: 全量文档盘点 + SoT 对齐检查
> **最高优先级规范**: `docs/AI_ANTI_HALLUCINATION_GUARD.md` v1.0 (MANDATORY)
> **审计状态**: 发现关键冲突，需要决策

---

## Executive Summary

本次审计发现 **AI_ANTI_HALLUCINATION_GUARD.md** (用户指定的"宪法级"规范) 与 **冻结的 SoT v2.6 文档集** 之间存在 **根本性冲突**。两者定义了完全不同的状态值、角色、表名等核心规范。

**关键发现**:
- **P0 冲突**: 5 项（状态机、角色、表名、账户状态、项目状态）
- **P1 冲突**: 3 项（字段命名、API 端点、审计字段）
- **决策需求**: 必须选择一个规范作为真正的唯一真相源

---

## Step A: 文档清单盘点 (Document Inventory)

### A.1 核心规范文档 (SoT Layer)

| 文档路径 | 版本 | 状态 | 模块归属 | 说明 |
|---------|------|------|---------|------|
| `docs/2.sot/STATE_MACHINE.md` | v2.6 | frozen | 全局 | 状态机定义（8状态日报） |
| `docs/2.sot/DATA_SCHEMA.md` | v5.2 | frozen | 全局 | 数据结构定义 |
| `docs/2.sot/BUSINESS_RULES.md` | v3.2 | frozen | 全局 | 业务规则索引 |
| `docs/2.sot/API_SOT.md` | v9.0 | frozen | 全局 | API 契约 |
| `docs/2.sot/ERROR_CODES_SOT.md` | v2.1 | frozen | 全局 | 错误码定义 |
| `docs/2.sot/AUTH_SPEC.md` | v2.0 | frozen | 全局 | 认证授权规范 |
| `docs/2.sot/LEDGER_SOT.md` | v1.1 | frozen | 财务 | 双账本规范 |
| `docs/2.sot/DAILY_REPORT_SOT.md` | v1.0 | frozen | 投手 | 日报规范 |
| `docs/2.sot/TOPUP_SOT.md` | - | active | 财务 | 充值规范 |
| `docs/2.sot/TRANSFER_SOT.md` | v1.0 | frozen | 财务 | 死号迁移规范 |
| `docs/2.sot/RECONCILIATION_SOT.md` | v1.0 | frozen | 财务 | 对账规范 |
| `docs/2.sot/PROFIT_SOT.md` | v1.1 | active | 财务 | 利润表规范 |
| `docs/2.sot/SOT_FREEZE_MANIFEST_v2.6.md` | v2.6 | frozen | 全局 | 冻结清单 |

### A.2 系统概览文档 (Overview Layer)

| 文档路径 | 版本 | 状态 | 说明 |
|---------|------|------|------|
| `docs/1.overview/MASTER_USAGE_GUIDE.md` | - | active | 主规范使用指南 |
| `docs/1.overview/ARCHITECTURE.md` | - | active | 系统架构 |
| `docs/1.overview/DEPLOYMENT.md` | - | active | 部署指南 |
| `docs/1.overview/TESTING.md` | - | active | 测试策略 |
| `docs/1.overview/PATTERNS.md` | - | active | 设计模式 |
| `docs/1.overview/ASDD_FREEZE_v1.0.md` | v1.0 | frozen | ASDD 冻结 |
| `docs/1.overview/FREEZE_MANIFEST_v1.0.md` | v1.0 | frozen | 概览层冻结 |

### A.3 AI 护栏文档 (用户指定的"宪法")

| 文档路径 | 版本 | 状态 | 说明 |
|---------|------|------|------|
| `docs/AI_ANTI_HALLUCINATION_GUARD.md` | v1.0 | **MANDATORY** | AI 防幻觉护栏（用户指定最高优先级） |

### A.4 Claude Code 配置文档

| 文档路径 | 版本 | 状态 | 说明 |
|---------|------|------|------|
| `CLAUDE.md` | v3.3 | active | 项目指令（已引用 GUARD） |
| `.claude/PROJECT_RULES.md` | v3.5 | active | 完整规则 |
| `.claude/skills/**/SKILL.md` | 多版本 | active | AI Skill 定义 |

### A.5 开发指南文档 (Dev-Guides Layer)

| 文档路径 | 说明 |
|---------|------|
| `docs/3.dev-guides/API_DEVELOPMENT_FLOW.md` | API 开发流程 |
| `docs/3.dev-guides/FRONTEND_DEVELOPMENT_RULES.md` | 前端开发规则 |
| `docs/3.dev-guides/TESTING_STRATEGY.md` | 测试策略 |
| `docs/3.dev-guides/UI_FLOW_SPEC.md` | UI 流程规范 |
| `docs/3.dev-guides/TROUBLESHOOTING.md` | 问题排查 |

### A.6 架构视图文档 (Architecture Layer)

| 文档路径 | 说明 |
|---------|------|
| `docs/4.architecture/SYSTEM_CONTEXT_VIEW.md` | C4-L1 系统上下文 |
| `docs/4.architecture/SERVICE_COMPONENT_VIEW.md` | C4-L3 组件视图 |
| `docs/4.architecture/DATA_FLOW_VIEW.md` | 数据流视图 |
| `docs/4.architecture/BOUNDED_CONTEXT_MAP.md` | 限界上下文 |
| `docs/4.architecture/ERROR_HANDLING_STRATEGY.md` | 错误处理策略 |
| `docs/4.architecture/FRONTEND_STRUCTURE_SPEC.md` | 前端结构规范 |

### A.7 文档统计

| 类别 | 文件数 | 状态 |
|------|-------|------|
| SoT 核心 | 13 | 10 frozen, 3 active |
| Overview | 7 | 2 frozen, 5 active |
| Dev-Guides | 12 | all active |
| Architecture | 10 | all active |
| Infrastructure | 6 | all active |
| Testing | 5 | all active |
| Appendix | 8 | all active |
| Archive | 30+ | archived |
| **总计** | **90+** | - |

---

## Step B: 按 4 核心模块归档 (Module Filing)

### B.1 投手管理模块 (Pitcher Management)

**GUARD 定义的 SoT 表**:
- `pitchers` 表
- `daily_reports` 表
- `account_ownership_history` 表（只读）

**实际 SoT (STATE_MACHINE v2.6 + DATA_SCHEMA v5.2) 定义**:
- `users` 表 (包含 `role = 'media_buyer'`)
- `daily_reports` 表
- 无 `account_ownership_history` 表

**归属文档**:
| 文档 | 来源 |
|------|------|
| `DAILY_REPORT_SOT.md` | SoT |
| `STATE_MACHINE.md` 第 8 章 | SoT |
| `DATA_SCHEMA.md` 第 3.3 节 | SoT |
| `BR-RPT.md` | 业务规则 |

### B.2 财务管理模块 (Finance Management)

**GUARD 定义的 SoT 表**:
- `ledger` 表（只追加不修改）
- `period_locks` 表
- `recon_*` 表族

**实际 SoT 定义**:
- `ledger_entries` 表
- `topup_requests` / `topup_transactions` 表
- `reconciliation_*` 表族
- 无 `period_locks` 表

**归属文档**:
| 文档 | 来源 |
|------|------|
| `LEDGER_SOT.md` v1.1 | SoT |
| `TOPUP_SOT.md` | SoT |
| `RECONCILIATION_SOT.md` v1.0 | SoT |
| `TRANSFER_SOT.md` v1.0 | SoT |
| `PROFIT_SOT.md` v1.1 | SoT |
| `BR-FIN.md` | 业务规则 |
| `BR-RECON.md` | 业务规则 |

### B.3 广告账号管理模块 (Ad Account Management)

**GUARD 定义的 SoT 表**:
- `ad_accounts` 表
- `agencies` 表
- `account_ownership_history` 表（写入权限）
- `attribution_runs` 表
- `spend_attributions` 表

**实际 SoT 定义**:
- `ad_accounts` 表
- `channels` 表（非 agencies）
- `account_status_history` 表
- 无 `agencies`, `attribution_runs`, `spend_attributions` 表

**归属文档**:
| 文档 | 来源 |
|------|------|
| `DATA_SCHEMA.md` 第 3.2 节 | SoT |
| `STATE_MACHINE.md` 第 7 章 | SoT |
| `BR-ACCT.md` | 业务规则 |
| `BR-CHAN.md` | 业务规则 |

### B.4 项目管理模块 (Project Management)

**GUARD 定义的 SoT 表**:
- `projects` 表
- `clients` 表

**实际 SoT 定义**:
- `projects` 表
- 无 `clients` 表（客户信息在 projects 表内）

**归属文档**:
| 文档 | 来源 |
|------|------|
| `DATA_SCHEMA.md` 第 3.2.1-3.2.3 节 | SoT |
| `STATE_MACHINE.md` 第 5 章 | SoT |
| `BR-PROJ.md` | 业务规则 |

---

## Step C: SoT 索引对齐表

### C.1 状态值对照表

| 实体 | GUARD 定义 | STATE_MACHINE v2.6 定义 | 冲突级别 |
|------|-----------|------------------------|---------|
| **日报状态** | `DRAFT, SUBMITTED, PLATFORM_MATCHED, DIFF_FLAGGED, CONFIRMED, REJECTED, REVISED` (7个) | `raw_submitted, trend_pending, trend_ok, trend_flagged, trend_resolved, final_pending, final_confirmed, final_locked` (8个) | **P0** |
| **账户状态** | `active, idle, suspended, banned` (4个) | `new, testing, active, suspended, dead, archived` (6个) | **P1** |
| **项目状态** | `active, paused, completed, cancelled` (4个) | `draft, active, suspended, archived` (4个) | **P1** |
| **Ledger状态** | `PENDING, APPROVED, EXECUTED, CONFIRMED, REJECTED` (5个) | 无状态机（ledger_entries 无状态字段） | **P1** |
| **Ledger FX状态** | `PENDING, ESTIMATED, LOCKED` (3个) | 无此字段 | **P1** |

### C.2 角色对照表

| GUARD 定义 | STATE_MACHINE v2.6 定义 | 映射关系 | 冲突级别 |
|-----------|------------------------|---------|---------|
| `pitcher` | `media_buyer` | 同义词 | **P0** |
| `account_manager` | `account_manager` | 一致 | - |
| `finance` | `finance` | 一致 | - |
| `supervisor` | `data_operator` | 同义词? | **P0** |
| `ceo` | - | **GUARD 独有** | **P0** |
| `admin` | `admin` | 一致 | - |

**GUARD 定义 6 个角色，SoT 定义 5 个角色**

### C.3 表名对照表

| GUARD 定义 | 实际 SoT 定义 | 冲突级别 |
|-----------|--------------|---------|
| `pitchers` | `users` (role='media_buyer') | **P0** |
| `ledger` | `ledger_entries` | **P0** |
| `period_locks` | 不存在 | **P0** |
| `recon_*` | `reconciliation_*` | **P1** |
| `agencies` | `channels` | **P1** |
| `clients` | `projects.client_name/client_company` | **P1** |
| `attribution_runs` | 不存在 | **P1** |
| `spend_attributions` | 不存在 | **P1** |
| `account_ownership_history` | `account_status_history` | **P1** |

---

## Step D: 冲突报告 (Conflict Report)

### D.1 P0 冲突（必须立即解决）

#### P0-1: 日报状态机根本性冲突

| 维度 | GUARD | SoT v2.6 |
|-----|-------|----------|
| 状态数量 | 7 | 8 |
| 初始状态 | `DRAFT` | `raw_submitted` |
| 终态 | `CONFIRMED` | `final_locked` |
| 状态命名风格 | 大写 | 小写snake_case |
| 趋势风控 | 无 | 有（trend_*系列） |
| 平台匹配 | `PLATFORM_MATCHED` | 无 |

**影响范围**: 整个日报流程、前后端代码、数据库 CHECK 约束

#### P0-2: 角色定义冲突

| GUARD | SoT v2.6 | 说明 |
|-------|----------|------|
| `pitcher` | `media_buyer` | 名称不同 |
| `supervisor` | `data_operator` | 语义可能不同 |
| `ceo` | 不存在 | GUARD 独有 |
| - | `data_operator` | SoT 独有 |

**影响范围**: RBAC、权限检查、用户管理

#### P0-3: 表名/Schema 根本性差异

GUARD 假设的数据库结构与实际 DATA_SCHEMA.md v5.2 定义的结构不匹配：
- `pitchers` vs `users`
- `ledger` vs `ledger_entries`
- `period_locks` 不存在
- `agencies` vs `channels`

**影响范围**: 所有模块边界定义、可写/只读表限制

#### P0-4: Ledger 状态机不存在于 SoT

GUARD 定义了 `ledger.txn_status` 和 `ledger.fx_status` 状态机，但 SoT 中 `ledger_entries` 表没有状态字段。

**影响范围**: 财务模块流程、汇率锁定机制

#### P0-5: 模块边界定义基于不存在的表

GUARD 第 2 节的模块边界定义（可写表/只读表/禁止表）引用了多个不存在的表名。

**影响范围**: AI 代码生成的模块边界验证

### D.2 P1 冲突（需要尽快解决）

| 编号 | 冲突描述 | GUARD | SoT |
|------|---------|-------|-----|
| P1-1 | 账户状态值差异 | 4个状态 | 6个状态 |
| P1-2 | 项目状态值差异 | `paused, completed, cancelled` | `draft, suspended, archived` |
| P1-3 | 金额符号规则 | 定义在 GUARD | 定义在 LEDGER_SOT |
| P1-4 | 期间锁机制 | 明确定义 | 不存在 |
| P1-5 | 归因相关表 | `attribution_runs`, `spend_attributions` | 不存在 |

---

## Step E: 对齐后的文档结构 (IA)

### E.1 建议的规范层次

```
Level 0: 宪法级 (MANDATORY)
├── [待定: GUARD vs SoT 二选一]

Level 1: SoT 核心 (frozen)
├── STATE_MACHINE.md v2.6
├── DATA_SCHEMA.md v5.2
├── BUSINESS_RULES.md v3.2
├── API_SOT.md v9.0
├── ERROR_CODES_SOT.md v2.1
├── AUTH_SPEC.md v2.0
└── LEDGER_SOT.md v1.1

Level 2: 模块 SoT (frozen)
├── DAILY_REPORT_SOT.md v1.0
├── TOPUP_SOT.md
├── TRANSFER_SOT.md v1.0
├── RECONCILIATION_SOT.md v1.0
└── PROFIT_SOT.md v1.1

Level 3: 开发指南 (active)
├── API_DEVELOPMENT_FLOW.md
├── FRONTEND_DEVELOPMENT_RULES.md
└── ...

Level 4: 架构视图 (active)
├── C4 视图
└── 数据流图
```

### E.2 按模块的文档导航

```
投手管理 (Pitcher)
├── SoT: DAILY_REPORT_SOT.md, STATE_MACHINE.md#8章
├── Schema: DATA_SCHEMA.md#3.3节
├── Rules: BR-RPT.md
└── Tests: backend/tests/test_daily_report_*.py

财务管理 (Finance)
├── SoT: LEDGER_SOT.md, TOPUP_SOT.md, RECONCILIATION_SOT.md
├── Schema: DATA_SCHEMA.md#3.4节
├── Rules: BR-FIN.md, BR-RECON.md
└── Tests: backend/tests/ledger/*, backend/tests/test_topup_*.py

广告账号 (AdAccount)
├── SoT: STATE_MACHINE.md#7章
├── Schema: DATA_SCHEMA.md#3.2.9节
├── Rules: BR-ACCT.md, BR-CHAN.md
└── Tests: backend/tests/ad_accounts/*

项目管理 (Project)
├── SoT: STATE_MACHINE.md#5章
├── Schema: DATA_SCHEMA.md#3.2.1节
├── Rules: BR-PROJ.md
└── Tests: backend/tests/test_project_*.py
```

---

## Step F: 最小补丁计划 (Minimal Patch Plan)

### 决策点: 选择规范基准

**选项 A**: 以 **SoT v2.6** 为准，更新 GUARD
- 优点: SoT 已 frozen，代码已实现，影响最小
- 缺点: GUARD 需要大幅重写
- 工作量: 中等（仅更新 GUARD 文档）

**选项 B**: 以 **GUARD** 为准，更新 SoT + 代码
- 优点: GUARD 设计可能更合理（用户指定为"宪法"）
- 缺点: 需要 unfreeze SoT，修改代码，工作量巨大
- 工作量: 极大（涉及数据库迁移、代码重构）

**选项 C**: 融合两者，创建新版本
- 优点: 取长补短
- 缺点: 复杂度高，可能引入新问题
- 工作量: 大

### 建议: 选项 A（最小影响）

**理由**:
1. SoT v2.6 已 frozen 且代码已实现
2. 8 状态日报流程已经过测试验证
3. 5 角色体系与 Supabase Auth 集成
4. GUARD 可以作为"补充规范"而非"替代规范"

### 补丁任务清单

#### 阶段 1: 文档对齐 (P0 修复)

| 任务 | 文件 | 变更 |
|-----|------|------|
| PATCH-01 | `AI_ANTI_HALLUCINATION_GUARD.md` | 更新 `REPORT_STATUS` 为 8 状态 |
| PATCH-02 | `AI_ANTI_HALLUCINATION_GUARD.md` | 更新 `USER_ROLE` 为 5 角色 |
| PATCH-03 | `AI_ANTI_HALLUCINATION_GUARD.md` | 更新表名对照 (pitchers→users, ledger→ledger_entries) |
| PATCH-04 | `AI_ANTI_HALLUCINATION_GUARD.md` | 更新模块边界定义（使用正确的表名） |
| PATCH-05 | `AI_ANTI_HALLUCINATION_GUARD.md` | 更新账户/项目状态枚举 |
| PATCH-06 | `AI_ANTI_HALLUCINATION_GUARD.md` | 移除不存在的表 (period_locks, agencies, clients, attribution_runs) |

#### 阶段 2: CLAUDE.md 同步

| 任务 | 文件 | 变更 |
|-----|------|------|
| PATCH-07 | `CLAUDE.md` | 确认角色定义与 SoT 一致（当前 v3.3 已有冲突） |
| PATCH-08 | `CLAUDE.md` | 更新 SoT 裁判链版本引用 |

#### 阶段 3: Skill 文档同步

| 任务 | 文件 | 变更 |
|-----|------|------|
| PATCH-09 | `ai-ad-code-factory/SKILL.md` | 确认状态白名单与 SoT 一致 |
| PATCH-10 | `ai-ad-code-verifier/SKILL.md` | 确认验证规则与 SoT 一致 |

---

## Step G: 验收检查清单 (Acceptance Checklist)

### G.1 文档对齐验收

| 检查项 | 验收标准 | 状态 |
|-------|---------|------|
| 日报状态白名单 | GUARD 与 STATE_MACHINE v2.6 第 8 章一致 | [ ] |
| 角色白名单 | GUARD 与 STATE_MACHINE v2.6 第 2 节一致 | [ ] |
| 表名引用 | GUARD 中所有表名均存在于 DATA_SCHEMA v5.2 | [ ] |
| 模块边界 | 可写/只读/禁止表均使用正确表名 | [ ] |
| 账户状态 | GUARD 与 STATE_MACHINE v2.6 第 7 章一致 | [ ] |
| 项目状态 | GUARD 与 STATE_MACHINE v2.6 第 5 章一致 | [ ] |

### G.2 版本引用验收

| 文档 | 应引用版本 | 状态 |
|-----|-----------|------|
| CLAUDE.md | STATE_MACHINE v2.6, DATA_SCHEMA v5.2, BUSINESS_RULES v3.2 | [ ] |
| GUARD | STATE_MACHINE v2.6, DATA_SCHEMA v5.2 | [ ] |
| Skill 文档 | 与 CLAUDE.md 一致 | [ ] |

### G.3 代码兼容性验收

| 检查项 | 验收标准 | 状态 |
|-------|---------|------|
| 状态枚举 | `backend/models/` 中的枚举与 GUARD 一致 | [ ] |
| 角色常量 | `backend/core/` 中的角色与 GUARD 一致 | [ ] |
| 前端类型 | `frontend/src/features/*/types/` 与 GUARD 一致 | [ ] |

---

## Appendix: 关键决策记录

### 决策 1: 规范优先级

**问题**: GUARD vs SoT v2.6 冲突时，以谁为准？

**用户指令**: GUARD 是"宪法级"规范

**实际情况**: SoT v2.6 已 frozen，代码已实现

**建议决策**: 更新 GUARD 以对齐 SoT v2.6，保持系统一致性

**决策状态**: 待用户确认

### 决策 2: GUARD 文档定位

**建议**: 将 GUARD 定位为"AI 防幻觉补充规范"，而非"替代 SoT"

**内容调整**:
- 保留模块边界检查逻辑
- 保留幻觉风险清单
- 保留自检清单
- 更新所有枚举值/表名以对齐 SoT

---

## 审计结论

1. **发现关键冲突**: GUARD 与 SoT v2.6 存在 5 项 P0 级根本性冲突
2. **建议方案**: 更新 GUARD 以对齐 SoT v2.6（选项 A）
3. **预估工作量**: 6 个 PATCH 任务（文档更新）
4. **待用户决策**: 确认规范优先级

---

**审计完成时间**: 2025-12-22
**审计工具**: Claude Code + doc-architect agent
**下一步**: 等待用户确认决策后执行补丁计划
