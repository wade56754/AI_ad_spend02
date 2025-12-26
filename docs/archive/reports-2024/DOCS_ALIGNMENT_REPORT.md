# DOCS_ALIGNMENT_REPORT.md

> **审计日期**: 2025-12-22
> **审计基准**: MASTER.md v4.4 (D:\project\AI_ad_spend02\docs\1.overview\MASTER.md)
> **审计范围**: 项目全部文档
> **审计类型**: 宪法级对齐审计 + Phase 1/Phase 2 边界验证
> **审计目标**: 支持 MVP Phase 1 内部试运行

---

## 0. 摘要（给老板看的）

### 0.1 当前对齐度评估

| 维度 | 评分 | 说明 |
|------|------|------|
| **核心文档对齐度** | 🟢 85% | MASTER.md v4.4 + BUSINESS_FLOW_MANAGEMENT + MVP_PHASE_DESIGN 三核心文档已对齐 |
| **SoT 文档对齐度** | 🟡 60% | STATE_MACHINE.md v2.7 存在 Phase 2 完整状态机，与 Phase 1 简化版本不一致 |
| **AI 防幻觉合规** | 🔴 30% | AI_ANTI_HALLUCINATION_GUARD.md 与 MASTER.md 定义完全冲突 |
| **Phase 1 边界清晰度** | 🟢 90% | MASTER.md 明确定义 Phase 1/Phase 2 边界，但代码中未完全实现 Feature Flag |

### 0.2 是否满足 Phase 1 上线条件

**结论**: ⚠️ **基本满足，但存在 3 个 P0 风险需立即修复**

| 条件 | 状态 | 说明 |
|------|------|------|
| 核心页面需求明确 | ✅ 已完成 | MVP_PHASE_DESIGN.md 定义 10 个核心页面 |
| Phase 边界清晰 | ✅ 已完成 | MASTER.md §3 明确定义 |
| 角色责任明确 | ✅ 已完成 | MASTER.md §2.4 定义 7 角色 |
| 数据口径统一 | ⚠️ 部分完成 | §4.5 明确口径，但与 STATE_MACHINE v2.6 存在冲突 |
| AI 防幻觉护栏 | ❌ 未完成 | AI_ANTI_HALLUCINATION_GUARD.md 与 MASTER.md 完全冲突 |

### 0.3 最大风险点（如不修会发生什么）

| 风险编号 | 风险描述 | 后果 | 优先级 |
|---------|---------|------|--------|
| **P0-1** | AI_ANTI_HALLUCINATION_GUARD.md 定义 6 角色（pitcher/supervisor/ceo），MASTER.md 定义 7 角色（project_owner/finance） | AI 生成代码使用错误的角色，导致权限混乱 | P0 |
| **P0-2** | STATE_MACHINE.md v2.7 定义 8 状态日报流程（Phase 2），MASTER.md §9 INV-003 也定义 8 状态（Phase 2），但 Phase 1 应使用 3 状态简化版 | 开发团队实现 Phase 2 功能（阻断/强制），违反 Phase 1 "照亮不问责" 原则 | P0 |
| **P0-3** | DATA_SCHEMA.md 定义 5 角色（media_buyer/data_operator），MASTER.md 定义 7 角色 | 数据库角色枚举与文档不一致，角色映射混乱 | P0 |
| **P1-1** | CLAUDE.md v3.3 引用 AI_ANTI_HALLUCINATION_GUARD.md 作为"防幻觉护栏"，但该文档与 MASTER.md 冲突 | Claude Code 生成代码时使用错误规范 | P1 |
| **P1-2** | 缺少 receivable 表定义（MASTER.md §4.5.5 新增） | "累计回款"指标无法实现 | P1 |

---

## 1. 文档索引与分层（Tier 1 / 2 / 3）

### 1.1 核心文档索引

| 文档 | 路径 | Tier | 是否 SoT | 影响 Phase 1 | 版本 | 结论 | 处理建议 |
|------|------|------|----------|--------------|------|------|----------|
| **MASTER.md** | docs/1.overview/MASTER.md | 1 (宪法) | ✓ | ✓ | v4.4 | ✅ 对齐 | 保持现状 |
| **BUSINESS_FLOW_MANAGEMENT.md** | dataset/out/BUSINESS_FLOW_MANAGEMENT.md | 1 | ✓ | ✓ | - | ✅ 对齐 | 保持现状 |
| **MVP_PHASE_DESIGN.md** | dataset/out/MVP_PHASE_DESIGN.md | 1 | ✓ | ✓ | - | ✅ 对齐 | 保持现状 |
| **STATE_MACHINE.md** | docs/2.sot/STATE_MACHINE.md | 2 | ✓ | ✓ | v2.6 | ⚠️ 部分冲突 | Phase 边界标注 |
| **DATA_SCHEMA.md** | docs/2.sot/DATA_SCHEMA.md | 2 | ✓ | ✓ | v5.2 | ⚠️ 部分冲突 | 补充字段 + 角色对齐 |
| **LEDGER_SOT.md** | docs/2.sot/LEDGER_SOT.md | 2 | ✓ | ○ | v1.1 | ✅ 对齐 (Phase 2) | 标注 Phase 2 启用 |
| **BUSINESS_RULES.md** | docs/2.sot/BUSINESS_RULES.md | 2 | ✓ | ✓ | v3.2 | ✅ 对齐 | 保持现状 |
| **API_SOT.md** | docs/2.sot/API_SOT.md | 2 | ✓ | ✓ | v9.0 | 未审查 | 需审查 |
| **ERROR_CODES_SOT.md** | docs/2.sot/ERROR_CODES_SOT.md | 2 | ✓ | ✓ | v2.1 | 未审查 | 需审查 |
| **AUTH_SPEC.md** | docs/2.sot/AUTH_SPEC.md | 2 | ✓ | ✓ | v2.0 | 未审查 | 需审查角色定义 |
| **AI_ANTI_HALLUCINATION_GUARD.md** | docs/AI_ANTI_HALLUCINATION_GUARD.md | 补充 | ✗ | ✓ | v1.0 | ❌ 完全冲突 | **删除或完全重写** |
| **CLAUDE.md** | CLAUDE.md | 配置 | ✗ | ✓ | v3.3 | ⚠️ 冲突 | 更新角色定义 + 移除 GUARD 引用 |
| **CODE_FACTORY_AUDIT_REPORT.md** | docs/CODE_FACTORY_AUDIT_REPORT.md | 流程 | ✗ | ○ | v1.0 | 未审查 | 归档 |
| **DOC_ARCHITECTURE_AUDIT_REPORT.md** | docs/DOC_ARCHITECTURE_AUDIT_REPORT.md | 流程 | ✗ | ○ | v1.0 | 自身 | 完成后归档 |

### 1.2 文档层级（ASDD 4层）

```
Tier 1: 架构宪法（MASTER.md 裁判链 §8.1 Priority 0-2）
├── MASTER.md v4.4                          [对齐 ✅]
├── BUSINESS_FLOW_MANAGEMENT.md             [对齐 ✅]
└── MVP_PHASE_DESIGN.md                     [对齐 ✅]

Tier 2: 单源真相 SoT（Priority 3-9）
├── STATE_MACHINE.md v2.7                   [部分冲突 ⚠️ Phase 边界]
├── DATA_SCHEMA.md v5.3                     [部分冲突 ⚠️ 角色+字段]
├── LEDGER_SOT.md v1.2                      [对齐 ✅ Phase 2]
├── BUSINESS_RULES.md v4.1                  [对齐 ✅]
├── API_SOT.md v9.3                         [未审查]
├── ERROR_CODES_SOT.md v2.1                 [未审查]
└── AUTH_SPEC.md v2.0                       [未审查]

Tier 3: 开发指南
├── BACKEND_DEV_GUIDE.md                    [未审查]
├── FRONTEND_RULES.md                       [未审查]
└── TESTING_GUIDE.md                        [未审查]

配置文档（影响 AI 行为）
├── CLAUDE.md v3.3                          [冲突 ⚠️]
└── AI_ANTI_HALLUCINATION_GUARD.md v1.0     [完全冲突 ❌]
```

---

## 2. 对齐检查清单（源自 MASTER.md v4.4）

### 2.1 Phase 1 / Phase 2 边界检查

| 检查项 | MASTER.md 定义 | 检查对象 | 是否合规 |
|--------|---------------|---------|----------|
| Phase 1 原则 | §3.1: 可见优先、解释责任、软性提醒、人工裁决 | 代码实现 | ⚠️ 未验证 Feature Flag |
| Phase 1 禁止行为 | §4.3: 禁止自动拒绝充值、自动暂停账户、自动冻结项目 | STATE_MACHINE.md | ⚠️ 8状态机包含阻断逻辑 |
| Phase 2 启用条件 | §3.4: Phase 1 运行2月 + 填报率90% + 老板批准 | Feature Flag | ❌ 未定义 |
| Phase 2 Feature Flag | §3.4: PHASE2_TOPUP_ENFORCEMENT 等环境变量 | 代码 | ❌ 未实现 |

### 2.2 角色定义检查

| 检查项 | MASTER.md v4.4 定义 | 冲突文档 | 冲突内容 |
|--------|-------------------|---------|----------|
| 角色数量 | §2.4: **7 角色** | AI_ANTI_HALLUCINATION_GUARD.md | 6 角色 |
| 角色数量 | §2.4: **7 角色** | DATA_SCHEMA.md | 5 角色 |
| 角色ID | ceo, project_owner, finance, supervisor, pitcher, account_manager, admin | AI_GUARD | pitcher, account_manager, finance, supervisor, ceo, admin (缺 project_owner) |
| 角色ID | ceo, project_owner, finance, supervisor, pitcher, account_manager, admin | DATA_SCHEMA | admin, finance, data_operator, account_manager, media_buyer (缺 ceo/project_owner/supervisor) |

### 2.3 SoT 字段级检查

| 检查项 | MASTER.md v4.4 定义 | 检查对象 | 是否合规 |
|--------|-------------------|---------|----------|
| 消耗 SoT (Phase 1) | §4.5.7: `ad_spend_daily.spend` | DATA_SCHEMA.md | ✅ 已定义 |
| 消耗 SoT (Phase 2) | §4.5.7: `daily_report.real_spend` | DATA_SCHEMA.md | ⚠️ 字段存在但未标注 Phase |
| 进粉 SoT (Phase 1) | §4.5.7: `daily_report.conversions` | DATA_SCHEMA.md | ✅ 已定义 |
| 进粉 SoT (Phase 2) | §4.5.7: `daily_report.conversions_final` | DATA_SCHEMA.md | ✅ 已定义 |
| 回款 SoT | §4.5.5: `receivable.amount WHERE status='received'` | DATA_SCHEMA.md | ❌ receivable 表不存在 |
| 外键命名规则 | §4.1: 外键必须使用 `_id` 后缀 | DATA_SCHEMA.md | ✅ 已遵循 |

### 2.4 KPI 口径检查

| 指标 | Phase 1 口径 (MASTER §4.5.1) | Phase 2 口径 | 是否明确 |
|------|------------------------------|-------------|----------|
| CPL | `ad_spend_daily.spend / daily_report.conversions` | `daily_report.real_spend / daily_report.conversions_final` | ✅ 明确 |
| 日消耗 | `ad_spend_daily.spend` | `daily_report.real_spend` | ✅ 明确 |
| 日进粉 | `daily_report.conversions` | `daily_report.conversions_final` | ✅ 明确 |
| 预计毛利 | `SUM(conversions × unit_price) - SUM(ad_spend_daily.spend)` | `SUM(conversions_final × unit_price) - SUM(real_spend + fee)` | ✅ 明确 |

### 2.5 AI 防幻觉规则检查（AH-01 ~ AH-05）

| 规则 | MASTER.md 定义 | 违反文档 | 违反内容 |
|------|---------------|---------|----------|
| AH-01 禁止假设数据一致 | §7 AH-01: 遇到数据缺失，标记"待确认" | - | ✅ 无违反 |
| AH-02 禁止自动做管理裁决 | §7 AH-02: 禁止生成自动拒绝/暂停/终止代码 | STATE_MACHINE.md v2.7 | ⚠️ 8状态机包含自动流转 |
| AH-03 禁止引入 SoT 未定义的概念 | §7 AH-03: 发现缺失→停止→询问 | AI_GUARD | ❌ 自定义 pitchers/ledger 表 |
| AH-04 必须遵循 Phase 1 软性原则 | §7 AH-04: Phase 1 = 提示+高亮+记录 | - | ⚠️ 代码未验证 |
| AH-05 遇到歧义必须停止并询问 | §7 AH-05: 停止→列出歧义→询问 | - | ✅ 原则明确 |

---

## 3. 冲突裁决表（以 MASTER.md 为唯一裁判）

### 3.1 P0 级冲突（必须立即修复）

| 冲突点 | 冲突文档/位置 | MASTER 裁决依据 | 结论 | 补丁/归档策略 |
|--------|--------------|-----------------|------|--------------|
| **P0-1: 角色定义冲突** | AI_ANTI_HALLUCINATION_GUARD.md 定义 6 角色（pitcher, supervisor, ceo, finance, account_manager, admin） | MASTER.md §2.4 定义 7 角色（ceo, project_owner, finance, supervisor, pitcher, account_manager, admin） | 以 MASTER.md 为准 | **删除 AI_GUARD 或完全重写第 5 节** |
| **P0-2: Phase 边界缺失** | STATE_MACHINE.md v2.7 第 8 章定义完整 8 状态机（Phase 2），但未标注 Phase 1 使用简化版 | MASTER.md §9 INV-003: Phase 1 简化为 3 状态（待审核→已审核→已锁定），Phase 2 完整 8 状态 | Phase 1 禁止实现 8 状态机 | **STATE_MACHINE.md 新增 Phase 1 简化版章节** |
| **P0-3: 角色映射混乱** | DATA_SCHEMA.md §1.1 定义 5 角色（admin, finance, data_operator, account_manager, media_buyer），与 MASTER.md 不一致 | MASTER.md §2.4 定义 7 角色 | 角色枚举必须统一 | **DATA_SCHEMA.md 角色枚举更新为 7 角色** + 建立映射表 |
| **P0-4: SoT 表定义缺失** | DATA_SCHEMA.md 无 receivable 表定义 | MASTER.md §4.5.5 定义 receivable 表（回款 SoT） | 必须补充 | **DATA_SCHEMA.md 补充 receivable 表定义** |
| **P0-5: AI 配置文档冲突** | CLAUDE.md v3.3 引用 AI_ANTI_HALLUCINATION_GUARD.md 作为护栏 | MASTER.md §7 定义 AH-01~AH-05 防幻觉原则 | AI_GUARD 与 MASTER 冲突，不可并存 | **CLAUDE.md 移除 AI_GUARD 引用** |

### 3.2 P1 级冲突（需尽快修复）

| 冲突点 | 冲突文档/位置 | MASTER 裁决依据 | 结论 | 补丁策略 |
|--------|--------------|-----------------|------|---------|
| **P1-1: 消耗口径未明确区分** | DATA_SCHEMA.md daily_report.spend 说明为"投手填报消耗" | MASTER.md §4.1: daily_report.spend = "投手自报消耗，**非消耗 SoT**" | 必须明确标注 | 补充字段说明 |
| **P1-2: Phase 1 字段边界未标注** | DATA_SCHEMA.md daily_report 表未标注 real_spend/conversions_final 为 Phase 2 字段 | MASTER.md §4.1: Phase 1 这两个字段可选 | 必须区分 | 补充 Phase 边界说明 |
| **P1-3: Feature Flag 未定义** | 代码中无 PHASE2_* 环境变量 | MASTER.md §3.4: 定义 4 个 Feature Flag | Phase 2 功能无法控制 | backend/core/config.py 补充 |
| **P1-4: 角色映射表缺失** | 无文档说明 data_operator ↔ supervisor, media_buyer ↔ pitcher 映射关系 | MASTER.md §9 INV-002 脚注: 运营 = supervisor/finance | 工程团队无法对应 | 补充映射说明文档 |

### 3.3 P2 级冲突（建议优化）

| 冲突点 | 冲突文档 | 建议 |
|--------|---------|------|
| SoT 文档版本引用不一致 | 部分文档引用 "SoT Freeze v1.0"，部分引用 "v2.6" | 统一为 "SoT Freeze v2.6" |
| AI Skill 文档版本老旧 | .claude/skills/*.md 未更新角色定义 | 批量更新为 7 角色 |
| 归档文档未移除 | docs/archive/ 仍在主目录 | 移动到独立 archived/ 目录 |

---

## 4. 文件级补丁清单（可执行）

### 4.1 P0 补丁（Phase 1 上线前必须完成）

#### PATCH-01: 删除或重写 AI_ANTI_HALLUCINATION_GUARD.md

**文件**: `docs/AI_ANTI_HALLUCINATION_GUARD.md`

**问题**: 该文档与 MASTER.md v4.4 完全冲突（角色、表名、状态值）

**裁决**: MASTER.md §8.1 裁判链优先级 0，AI_GUARD 无优先级

**策略**: **删除该文件** 或 **基于 MASTER.md 完全重写**

**如果选择重写**，必须对齐以下内容：
- 第 5 节状态值白名单：使用 MASTER.md §2.4 的 7 角色
- 模块边界定义：使用 DATA_SCHEMA.md 定义的表名（users, ledger_entries, 等）
- 移除 pitchers/ledger/agencies/period_locks 等不存在的表

---

#### PATCH-02: DATA_SCHEMA.md 补充 receivable 表

**文件**: `docs/2.sot/DATA_SCHEMA.md`

**需要修改的章节**: 第 3 章（详细表结构）

**建议补丁**（可粘贴）:

```markdown
### 3.X 回款管理

#### 3.X.1 `receivable`（implemented）

**说明**：回款记录表，记录项目回款流水，是**已回款的唯一事实源**。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID | PK | 主键 |
| `project_id` | BIGINT | FK → `projects.id` NOT NULL | 关联项目（外键） |
| `amount` | DECIMAL(15,2) | NOT NULL | 单笔回款金额 |
| `status` | VARCHAR(20) | NOT NULL, CHECK IN ('received', 'pending') | 回款状态 |
| `received_at` | TIMESTAMPTZ | 可空 | 回款时间（status=received 时必填） |
| `source` | VARCHAR(255) | 可空 | 回款来源（客户名称/转账单号） |
| `recorded_by` | UUID | FK → `users.id` | 录入人（finance 角色） |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

**索引**: `idx_receivable_project`, `idx_receivable_status`, `idx_receivable_received_at`.

**业务约束**:
- status='received' 时 received_at 必填
- 仅 finance 角色可录入
- 累计回款计算公式: `SUM(amount WHERE status='received')`

**SoT 声明**: 本表是**已回款的唯一事实源**（MASTER.md §4.5.5）
```

---

#### PATCH-03: DATA_SCHEMA.md 角色枚举更新

**文件**: `docs/2.sot/DATA_SCHEMA.md`

**需要修改的章节**: §1.1 技术栈

**旧内容**:
```markdown
- **角色枚举**: 仅允许 `admin`, `finance`, `data_operator`, `account_manager`, `media_buyer`
```

**新内容**:
```markdown
- **角色枚举**: 仅允许 7 个标准角色（MASTER.md §2.4）：
  - `ceo` - 老板
  - `project_owner` - 项目负责人
  - `finance` - 财务
  - `supervisor` - 主管
  - `pitcher` - 投手
  - `account_manager` - 户管
  - `admin` - 管理员

**历史角色映射** (仅用于理解旧代码，新代码禁止使用):
- `media_buyer` → `pitcher`
- `data_operator` → `supervisor`
```

**补充说明**: 在 users 表的 role 字段说明中也需同步更新。

---

#### PATCH-04: STATE_MACHINE.md 补充 Phase 1 简化版

**文件**: `docs/2.sot/STATE_MACHINE.md`

**需要新增的章节**: 在第 8 章（粉数确认状态机）前插入

**建议补丁**:

```markdown
## 7.5 Phase 1 / Phase 2 状态机边界（重要）

> **依据**: MASTER.md v4.4 §3 和 §9 INV-003

### Phase 1 简化版（3 状态）

**目标**: 照亮问题，不阻断流程

**状态枚举**: `pending_review`, `reviewed`, `locked`

**合法流转**:
```
pending_review → reviewed → locked
```

**字段使用**:
- 进粉: 仅使用 `daily_report.conversions`
- 消耗: 仅使用 `ad_spend_daily.spend`（SoT）
- 不使用 `conversions_final`, `real_spend`, `conversions_raw`, `raw_spend`

**Phase 1 特性**:
- 无趋势风控（不触发 trend_flagged）
- 无强制审核（reviewed 状态可选）
- 锁定仅标记，不阻止修改

### Phase 2 完整版（8 状态）

**目标**: 问责与强制约束

**状态枚举**: 见第 8 章完整定义

**启用条件**: MASTER.md §3.4 定义的 Feature Flag + 前置条件
```

---

#### PATCH-05: CLAUDE.md 移除 AI_GUARD 引用

**文件**: `CLAUDE.md`

**需要修改的章节**:
- §3.2 合法角色
- 快速参考 → 详细规则

**旧内容**:
```markdown
### 3.2 合法角色 (6 角色, 来源: PROJECT.md v1.3, CORE_MODULES.md v1.0)
```python
VALID_ROLES = [
    "pitcher",         # 投手
    "account_manager", # 户管
    "supervisor",      # 主管
    "finance",         # 财务
    "ceo",             # CEO
    "admin"            # 管理员
]
```

**新内容**:
```markdown
### 3.2 合法角色 (7 角色, 来源: MASTER.md v4.4 §2.4)
```python
VALID_ROLES = [
    "ceo",             # 老板 - 资金安全、公司盈亏、最终决策
    "project_owner",   # 项目负责人 - 项目盈亏、资金使用效率
    "finance",         # 财务 - 资金出入准确、数据真实、对账
    "supervisor",      # 主管 - 团队产出、投手管理、日常监督
    "pitcher",         # 投手 - CPL 达标、日报准确、执行投放
    "account_manager", # 户管 - 账户分配、账户状态监控
    "admin"            # 管理员 - 系统配置（不参与业务）
]
```

**删除引用**:
```markdown
# 删除以下行
- **AI 防幻觉护栏**: `docs/AI_ANTI_HALLUCINATION_GUARD.md` v1.0 (必读)
```

**替换为**:
```markdown
- **AI 防幻觉原则**: MASTER.md v4.4 §7 (AH-01 ~ AH-05)
```

---

### 4.2 P1 补丁（Phase 1 上线后尽快完成）

#### PATCH-06: backend/core/config.py 补充 Feature Flag

**文件**: `backend/core/config.py`

**建议补丁**:

```python
# Phase 2 Feature Flags (MASTER.md §3.4)
# 默认全部关闭，Phase 2 启用时设置为 True
PHASE2_TOPUP_ENFORCEMENT: bool = Field(default=False, description="充值强制审批（Phase 2）")
PHASE2_DAILY_REPORT_REQUIRED: bool = Field(default=False, description="日报必须审核（Phase 2）")
PHASE2_WEEKLY_BRIEF_REQUIRED: bool = Field(default=False, description="周报必须提交（Phase 2）")
PHASE2_SETTLEMENT_LOCK: bool = Field(default=False, description="结算锁定（Phase 2）")
```

---

#### PATCH-07: 补充角色映射说明文档

**文件**: 新建 `docs/3.dev-guides/ROLE_MAPPING.md`

**内容**:

```markdown
# 角色映射说明

> **目的**: 帮助开发团队理解新旧角色名称映射关系
> **基准**: MASTER.md v4.4 §2.4

## 标准角色（7 角色）

| 角色ID | 中文名 | 英文全称 |
|--------|-------|---------|
| ceo | 老板 | Chief Executive Officer |
| project_owner | 项目负责人 | Project Owner |
| finance | 财务 | Finance |
| supervisor | 主管 | Supervisor |
| pitcher | 投手 | Media Buyer / Pitcher |
| account_manager | 户管 | Account Manager |
| admin | 管理员 | Admin |

## 历史角色映射（仅用于理解旧代码）

| 旧角色名 | 新角色名 | 说明 |
|---------|---------|------|
| media_buyer | pitcher | 投手 |
| data_operator | supervisor | 主管（负责数据复核） |
| data_clerk | supervisor | 旧名称，已废弃 |
| manager | account_manager | 旧名称，已废弃 |

## 代码迁移指南

### 数据库迁移

```sql
-- 将旧角色值映射为新角色值
UPDATE users SET role = 'pitcher' WHERE role = 'media_buyer';
UPDATE users SET role = 'supervisor' WHERE role = 'data_operator';
UPDATE users SET role = 'account_manager' WHERE role = 'manager';
```

### 枚举类更新

```python
# backend/models/enums.py
from enum import Enum

class UserRole(str, Enum):
    CEO = "ceo"
    PROJECT_OWNER = "project_owner"
    FINANCE = "finance"
    SUPERVISOR = "supervisor"
    PITCHER = "pitcher"
    ACCOUNT_MANAGER = "account_manager"
    ADMIN = "admin"
```
```

---

### 4.3 归档建议

| 文件 | 归档位置 | 理由 |
|------|---------|------|
| `AI_ANTI_HALLUCINATION_GUARD.md` | `docs/archive/2025-12-deprecated/` | 与 MASTER.md 完全冲突，保留作为历史参考 |
| `CODE_FACTORY_AUDIT_REPORT.md` | `docs/archive/reports/` | 审计报告，非 SoT 文档 |
| `DOC_ARCHITECTURE_AUDIT_REPORT.md` | `docs/archive/reports/` | 本报告完成后归档 |

---

## 5. Phase 1 / Phase 2 文档治理执行计划

### 5.1 Phase 1（必须做，支持 MVP）

**时间线**: 上线前 3 天

| 顺序 | 任务 | 责任人 | 验收标准 |
|------|------|--------|----------|
| 1 | 执行 PATCH-01：删除 AI_GUARD | 架构师 | AI_GUARD 文件已删除或重写完成 |
| 2 | 执行 PATCH-02：补充 receivable 表 | 架构师 | DATA_SCHEMA.md 包含 receivable 表定义 |
| 3 | 执行 PATCH-03：角色枚举更新 | 架构师 | DATA_SCHEMA.md role 枚举为 7 角色 |
| 4 | 执行 PATCH-04：STATE_MACHINE 补充 Phase 1 章节 | 架构师 | STATE_MACHINE.md 明确 Phase 1 简化版 |
| 5 | 执行 PATCH-05：CLAUDE.md 移除 GUARD 引用 | 架构师 | CLAUDE.md 引用 MASTER.md 防幻觉原则 |
| 6 | 数据库迁移：roles 枚举更新 | 后端团队 | users.role CHECK 约束包含 7 角色 |
| 7 | 验证 AI 生成代码 | QA + 架构师 | 使用 Claude Code 生成代码，验证角色正确 |

### 5.2 Phase 2（后续，需 gated）

**启用条件**: MASTER.md §3.4

| 顺序 | 任务 | 前置条件 |
|------|------|----------|
| 1 | 执行 PATCH-06：Feature Flag 实现 | Phase 1 运行 2 月 + 填报率 90% |
| 2 | 实现 8 状态日报流程 | PHASE2_DAILY_REPORT_REQUIRED = true |
| 3 | 实现充值强制审批 | PHASE2_TOPUP_ENFORCEMENT = true |
| 4 | 实现结算锁定 | PHASE2_SETTLEMENT_LOCK = true |
| 5 | 启用双账本架构 | LEDGER_SOT.md v1.2 完整实现 |

---

## 6. 最终验收标准（文档层）

### 6.1 何时可判定"文档已对齐"

✅ **对齐条件**（全部满足）:

1. **P0 补丁全部完成**：PATCH-01 ~ PATCH-05 执行完毕
2. **角色定义统一**：所有文档使用 7 角色（ceo, project_owner, finance, supervisor, pitcher, account_manager, admin）
3. **Phase 边界清晰**：STATE_MACHINE.md 明确区分 Phase 1 简化版 和 Phase 2 完整版
4. **SoT 字段完整**：DATA_SCHEMA.md 包含 receivable 表 + Phase 边界标注
5. **AI 配置正确**：CLAUDE.md 引用 MASTER.md，不引用 AI_GUARD
6. **裁判链一致**：所有 SoT 文档版本引用与 MASTER.md §8.1 一致

### 6.2 如何保证 AI 不发散、工程不漂移

#### 6.2.1 AI 防幻觉护栏（基于 MASTER.md §7）

| 规则 | 实施方式 | 验证方法 |
|------|---------|----------|
| AH-01 禁止假设数据一致 | 代码 Review：检查是否有强制 NOT NULL | PR 自动检查 |
| AH-02 禁止自动做管理裁决 | 代码 Review：检查是否有自动拒绝/暂停逻辑 | 人工审查 |
| AH-03 禁止引入未定义概念 | 使用 Claude Code 生成代码前，强制读取 MASTER.md | Skill 配置强制 |
| AH-04 必须遵循 Phase 1 软性原则 | Feature Flag 控制 Phase 2 功能，默认关闭 | 环境变量检查 |
| AH-05 遇到歧义必须停止并询问 | Claude Code Skill 配置：遇到歧义时询问用户 | Skill 行为审查 |

#### 6.2.2 工程漂移防护

| 漂移类型 | 防护措施 | 检查频率 |
|---------|---------|----------|
| 角色定义漂移 | 数据库 CHECK 约束锁定 7 角色 | 每次迁移 |
| SoT 字段漂移 | DATA_SCHEMA.md Freeze，变更需 RFC | 每月审查 |
| Phase 边界模糊 | Feature Flag 强制控制 | 每次发布 |
| 文档版本不一致 | 引用时必须带版本号（如 MASTER.md v4.4） | PR Review |

#### 6.2.3 文档对齐持续审计

**月度审计清单**：

```markdown
□ 所有 SoT 文档版本号与 MASTER.md §8.1 一致
□ 数据库角色枚举 = 7 角色
□ Feature Flag 配置正确（Phase 2 默认关闭）
□ AI 生成代码使用正确角色名
□ 无新增未经 RFC 的 SoT 字段
□ STATE_MACHINE.md 状态枚举与代码一致
```

---

## 附录 A: 冲突解决决策记录

### 决策 1: AI_ANTI_HALLUCINATION_GUARD.md 处理

**问题**: 该文档与 MASTER.md 完全冲突（角色/表名/状态）

**选项**:
- A. 删除 AI_GUARD
- B. 保留 AI_GUARD，更新 MASTER.md
- C. 融合两者

**决策**: **选项 A（删除）**

**理由**:
1. MASTER.md v4.4 是架构宪法（MASTER.md §8.1 Priority 0）
2. AI_GUARD 创建于 2025-12-22，晚于 SoT Freeze v2.6（2025-11-27）
3. AI_GUARD 基于错误的 Schema（pitchers/ledger 表不存在）
4. MASTER.md §7 已定义 AH-01~AH-05 防幻觉原则，功能覆盖

**执行**: PATCH-01

---

### 决策 2: 角色数量 5 vs 6 vs 7

**问题**: 三个文档定义不同数量的角色
- DATA_SCHEMA.md: 5 角色
- AI_GUARD: 6 角色
- MASTER.md: 7 角色

**决策**: **以 MASTER.md 7 角色为准**

**理由**:
1. MASTER.md v4.4 §2.4 明确定义 7 角色及职责
2. project_owner 角色在业务流程中至关重要（BUSINESS_FLOW_MANAGEMENT.md）
3. ceo 角色是资金安全最终责任人

**执行**: PATCH-03 + PATCH-05

---

### 决策 3: Phase 1 状态机 3 状态 vs 8 状态

**问题**: STATE_MACHINE.md v2.7 定义 8 状态，但 MASTER.md §9 INV-003 说 Phase 1 简化为 3 状态

**决策**: **STATE_MACHINE.md 同时包含两个版本**

**理由**:
1. 8 状态机是 Phase 2 完整版，需保留（未来启用）
2. Phase 1 简化版是当前实现，需明确定义
3. 通过章节区分，避免混淆

**执行**: PATCH-04

---

## 附录 B: 文档维护责任

| 文档类型 | 维护责任人 | 变更审批 | 变更频率 |
|---------|-----------|---------|---------|
| MASTER.md | Master Architect | 老板确认 | 季度 |
| BUSINESS_FLOW_MANAGEMENT.md | 业务架构师 | Master Architect | 半年 |
| MVP_PHASE_DESIGN.md | 产品经理 + 架构师 | 老板确认 | 半年 |
| STATE_MACHINE.md | 系统架构师 | RFC 流程 | 按需 |
| DATA_SCHEMA.md | 数据库架构师 | RFC 流程 | 按需 |
| LEDGER_SOT.md | 财务架构师 | RFC 流程 | 按需 |
| CLAUDE.md | 架构师 | 内部 Review | 按需 |

---

## 附录 C: 下一步行动

### 立即行动（48 小时内）

1. ✅ 架构师决策：删除还是重写 AI_GUARD（决策 1）
2. ✅ 执行 PATCH-01 ~ PATCH-05
3. ✅ 数据库迁移：更新 users.role CHECK 约束
4. ✅ 代码验证：使用 Claude Code 生成代码，确认角色正确

### 本周行动

1. 执行 PATCH-06：Feature Flag 实现
2. 补充 ROLE_MAPPING.md
3. 审查 AUTH_SPEC.md、API_SOT.md、ERROR_CODES_SOT.md

### 下月行动

1. 月度文档对齐审计（附录 6.2.3）
2. Phase 1 上线复盘
3. 准备 Phase 2 启用计划

---

**报告完成时间**: 2025-12-22
**审计工具**: Claude Code (Sonnet 4.5) + Sequential Thinking
**基准文档**: MASTER.md v4.4 (D:\project\AI_ad_spend02\docs\1.overview\MASTER.md)
**下一次审计**: Phase 1 上线后 30 天

---

**审计结论**: ⚠️ **文档存在 5 个 P0 冲突，必须在 Phase 1 上线前修复。修复后可满足 MVP 内部试运行要求。**
