# RLS 方案 A 执行计划（Execution Plan for Strategy A）

## 文档版本信息

- **文档类型**: RLS 方案 A 执行计划 + 执行记录
- **版本**: v2.0
- **创建时间**: 2025-11-20
- **最后更新**: 2025-11-20
- **状态**: 📋 执行计划（待实施）

## 文档定位与关系

### 与其他 RLS 文档的关系

| 文档 | 定位 | 与本文档关系 |
|------|------|-------------|
| `docs/core/RLS_POLICIES.md` | **系统整体 SoT（规划）** - 未来启用数据库 RLS 的目标设计 | 本文档不修改其内容，仅标注其为"规划文档" |
| `docs/security/RLS_POLICIES.md` | **当前实现行为的 Implementation SoT** - 描述应用层权限实现 | 本文档标注其为"当前生效的实现说明" |
| `docs/RLS_STRATEGY_DECISION.md` | 决策记录 - 分析现状并提出方案 A/B | 本文档是方案 A 的具体执行步骤 |
| 本文档 | **方案 A 执行计划** - 详细操作步骤与验证清单 | - |

### SoT 层级说明

**重要**：系统整体的 SoT 仍以 `docs/core/*` 为根。

- `docs/core/RLS_POLICIES.md` 是 **规划级 SoT**（描述"应该如何"）
- `docs/security/RLS_POLICIES.md` 是 **实现级 Implementation SoT**（描述"实际如何"）
- 当两者冲突时，以 `docs/core/*` 为权威来源，但当前实现以 `docs/security/*` 为准

本文档的职责是消除上述冲突，统一为"当前未启用数据库 RLS，规划文档仅作未来参考"。

---

## 一、现状核查结果

### 1.1 迁移文件扫描结果

**✅ 核心结论**：仓库中**不存在任何启用 RLS 的迁移文件**。

扫描了 24 个 Alembic 迁移文件，未发现以下模式的文件：
- `*enable_rls*.py`
- `002_*.py` / `004_*.py` / `006_*.py`（原决策文档提到的迁移编号）

**结论**：数据库层 RLS 从未被启用过，`docs/RLS_STRATEGY_DECISION.md` 中提到的"002/004/006 enable_rls_*.py"是**假设性描述**，不是实际存在的文件。

### 1.2 文档矛盾分析

| 文档 | 关键声明 | 实际状态 |
|------|---------|---------|
| `docs/core/RLS_POLICIES.md` | "✅ 生产就绪（已完成安全修复与代码优化）" | ❌ 误导性标记 - 实际是规划文档 |
| `docs/security/RLS_POLICIES.md` | "⚠️ 当前 RLS 未启用，权限完全在应用层" | ✅ 准确反映现状 |
| 代码层（`backend/models/`） | 有 `RLSAwareMixin` + `__rls_user_field__` 配置 | ✅ 应用层权限过滤，非数据库 RLS |

### 1.3 受影响的表（理论上需要 RLS 的表）

根据 `docs/core/RLS_POLICIES.md` 的规划，以下表**如果启用 RLS** 会受影响：

| 表名 | RLS 字段 | 策略类型 | 当前状态 |
|------|---------|---------|---------|
| `projects` | `created_by` | 用户作用域 | 应用层过滤 |
| `project_members` | `project_id` 关联 | 成员关系 | 应用层过滤 |
| `ad_accounts` | `owner_id` / `created_by` | 分配+作用域 | 应用层过滤 |
| `daily_reports` | `created_by` | 用户作用域 | 应用层过滤 |
| `topup_requests` | `applicant_id` | 用户作用域 | 应用层过滤 |
| `ledger_entries` | `project_id` 关联 | 项目关联 | 应用层过滤 |
| `reconciliation_*` | `created_by` / `project_id` | 混合模式 | 应用层过滤 |
| `audit_logs` | 仅插入，禁止修改/删除 | 审计表 | 应用层控制 |

**但由于数据库层从未启用 RLS**，上述表当前没有任何 RLS 策略。

---

## 二、方案 A 详细操作步骤

### 2.1 需要执行的操作

**核心结论**：**不需要创建任何"disable RLS"迁移**，因为数据库层 RLS 从未启用过。

方案 A 的实际工作重点是**文档修正**，而非数据库操作。

### 2.2 文档修改方案（不执行，仅规划）

#### 修改 1: `docs/core/RLS_POLICIES.md`

**目标**：在文件开头明确声明当前未启用 RLS

**修改位置**：第 1-10 行（文件头部元信息）

**修改内容**：
```markdown
# AI_AD_SPEND 系统行级安全策略规范（RLS Policies）

**文档版本**：v1.3 🔒 规划文档（未启用）
**最后更新**：2025-11-20
**维护者**：Backend Team
**状态**：⚠️ **当前未启用 - 本文档描述的是规划目标策略**

---

## ⚠️ 重要声明

**当前 RLS 实施状态**：
- ❌ **数据库层 RLS 未启用**：PostgreSQL Row Level Security 功能关闭
- ✅ **应用层权限控制已启用**：通过 Service 层 + ORM Mixin 实现
- 📋 **本文档定位**：未来启用数据库 RLS 的规划蓝图和参考设计

**如需了解当前实际权限实现，请参考**：
- `docs/security/RLS_POLICIES.md` - 应用层权限实现说明（当前实现行为的 Implementation SoT）
- `backend/core/permissions.py` - RBAC 权限系统
- `backend/models/mixins/rls_aware.py` - ORM 层权限过滤

**SoT 层级说明**：
- 本文档（`docs/core/RLS_POLICIES.md`）是系统整体 SoT 的规划部分
- `docs/security/RLS_POLICIES.md` 描述当前实现行为
- 两者冲突时以本文档为权威，但当前实现以 security 文档为准

---
```

**修改范围**：
1. 将"✅ 生产就绪"改为"⚠️ 当前未启用 - 规划文档"
2. 在第 10-35 行之间插入"重要声明"段落
3. 在第 58 节（"RLS 全局原则"）开头增加一段说明：
   ```markdown
   ## 1. RLS 全局原则

   **⚠️ 本节描述的是未来启用数据库 RLS 时应遵循的原则**
   **当前数据库 RLS 未启用，以下策略仅作为规划参考**

   ### 1.1 Deny-by-Default 原则
   ...
   ```

#### 修改 2: `docs/security/RLS_POLICIES.md`

**目标**：保留该文档，并标记为"当前实现行为的 Implementation SoT"

**修改位置**：第 1-10 行

**修改内容**：
```markdown
# 行级安全策略（Row Level Security Policies）

**版本**：v1.1
**最后更新**：2025-11-20
**文档状态**：✅ **当前实现行为的 Implementation SoT**

---

## 文档定位说明

### 与 `docs/core/RLS_POLICIES.md` 的关系

- **本文档（security/RLS_POLICIES.md）**：描述当前生效的**应用层权限实现**
  - 定位：**Implementation SoT**（实现行为的真相源）
  - 描述：实际如何实现权限控制

- **`docs/core/RLS_POLICIES.md`**：描述未来**数据库层 RLS 的规划**
  - 定位：**规划级 SoT**（系统整体真相源的规划部分）
  - 描述：应该如何实现权限控制

### SoT 层级

**重要**：系统整体 SoT 仍以 `docs/core/*` 为根。

- 当规划与实现冲突时，以 `docs/core/*` 为权威来源
- 但当前运行的系统行为以本文档描述为准

**如需修改权限逻辑，以本文档为实现参考**。

---
```

**修改范围**：
1. 版本号保持 v1.1
2. 修改文档状态为"当前实现行为的 Implementation SoT"
3. 在开头插入清晰的文档定位与 SoT 层级说明
4. 保持 1.1 节的"⚠️ 重要声明：当前系统 **RLS 未在数据库层启用**"不变

#### 修改 3: `docs/RLS_STRATEGY_DECISION.md`

**目标**：追加"执行记录"章节

**修改位置**：文件末尾追加

**修改内容**：
```markdown
---

## 7. 执行记录（2025-11-20）

### 7.1 决策确认

**已选方案**：方案 A（短期关闭 RLS，统一 SoT 为"当前未启用，规划中"）

**决策日期**：2025-11-20

**决策依据**：
1. 现状核查结果：数据库层 RLS 从未启用过
2. 应用层权限控制已实现且运行稳定
3. 避免引入不必要的复杂性

**详细执行计划**：见 `docs/RLS_STRATEGY_EXEC_PLAN_A.md`

### 7.2 实际执行结果

#### 7.2.1 数据库核查

**检查项**：是否存在启用 RLS 的迁移文件

**检查命令**：
```bash
find backend/alembic/versions/ -name "*enable_rls*.py"
find backend/alembic/versions/ -name "002_*.py" -o -name "004_*.py" -o -name "006_*.py"
```

**检查结果**：
- ❌ 未发现任何启用 RLS 的迁移文件
- ✅ 确认数据库层 RLS 从未启用过

**结论**：**不需要创建"disable RLS"迁移**，原文档中提到的"002/004/006 enable_rls_*.py"是假设性描述。

#### 7.2.2 文档修正状态

**计划修正文档**：
1. ⏳ `docs/core/RLS_POLICIES.md` - 标记为"规划文档（未启用）"
2. ⏳ `docs/security/RLS_POLICIES.md` - 标记为"当前实现行为的 Implementation SoT"
3. ⏳ `docs/RLS_STRATEGY_DECISION.md` - 追加执行记录

**未修改部分**：
- 应用层代码（`backend/services/*.py`）- 无需修改，继续使用现有权限过滤
- 模型层（`backend/models/`）- 保留 `RLSAwareMixin`，作为应用层权限抽象

---

**文档版本**：Draft v1.1 - 执行记录已追加
**执行者**：Backend Team
**审核者**：[待填写]
```

---

## 三、不需要的操作（重要说明）

### 3.1 不需要创建 Alembic 迁移

**原因**：数据库层 RLS 从未启用，不存在需要 DISABLE 的策略。

**原文档中提到的迁移**（已确认不存在）：
- ❌ `002_enable_rls_daily_reports.py`
- ❌ `004_enable_rls_projects.py`
- ❌ `006_enable_rls_topup.py`

这些文件名在原决策文档中是**假设性描述**，实际仓库中从未创建过。

### 3.2 不需要执行的 SQL

**以下操作都不需要执行**：

```sql
-- ❌ 不需要：表从未启用 RLS
ALTER TABLE daily_reports DISABLE ROW LEVEL SECURITY;
ALTER TABLE projects DISABLE ROW LEVEL SECURITY;
-- ...

-- ❌ 不需要：策略从未创建
DROP POLICY IF EXISTS "daily_reports_select_admin" ON daily_reports;
DROP POLICY IF EXISTS "projects_select_member" ON projects;
-- ...
```

### 3.3 不需要修改的代码

**应用层代码保持不变**：
- ✅ `backend/services/*.py` - 继续使用 `_apply_rls_filter` 方法
- ✅ `backend/models/mixins/rls_aware.py` - 保留 Mixin 作为权限抽象
- ✅ `backend/core/permissions.py` - 权限系统不需修改

---

## 四、风险与验证

### 4.1 风险评估

| 风险项 | 风险级别 | 缓解措施 |
|-------|---------|---------|
| 文档修正后开发人员仍误解 RLS 状态 | 🟡 中 | 在开发者文档首页增加"权限实现概览"章节 |
| 应用层权限过滤遗漏导致越权访问 | 🔴 高 | 补充单元测试 + 代码审查清单 |
| 未来启用 RLS 时与现有代码冲突 | 🟢 低 | 保留 `RLSAwareMixin` 作为适配层 |

### 4.2 验证步骤（建议在测试环境执行）

#### 步骤 1：确认数据库无 RLS 策略

```sql
-- 连接到数据库
psql $DATABASE_URL

-- 检查是否有表启用了 RLS
SELECT
  schemaname,
  tablename,
  rowsecurity AS rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
  AND rowsecurity = true;

-- 预期结果：空结果集（无表启用 RLS）
```

#### 步骤 2：检查是否有 RLS 策略

```sql
-- 检查是否存在任何策略
SELECT
  schemaname,
  tablename,
  policyname,
  cmd AS operation,
  qual AS using_clause
FROM pg_policies
WHERE schemaname = 'public';

-- 预期结果：空结果集（无策略定义）
```

#### 步骤 3：验证应用层权限仍然生效

```bash
# 运行现有的权限测试
cd backend
pytest tests/test_rbac_permissions.py -v
pytest tests/test_daily_report_permissions.py -v

# 预期结果：所有测试通过
```

### 4.3 回滚计划

**如果文档修改后发现问题**：

1. **立即回滚**：
   ```bash
   git revert <commit_hash>
   git push
   ```

2. **紧急沟通**：
   - 通知团队当前权限实现状态
   - 更新内部 Wiki 或 Confluence 文档

3. **根因分析**：
   - 检查是否有依赖 `docs/core/RLS_POLICIES.md` 的自动化脚本
   - 确认是否有开发人员基于错误理解编写了代码

---

## 五、执行清单（待确认后实装）

### 5.1 文档修改 TODO

- [ ] **T1**：修改 `docs/core/RLS_POLICIES.md`
  - [ ] 第 1-10 行：修改文档版本和状态标记
  - [ ] 插入"重要声明"段落（包含 SoT 层级说明）
  - [ ] 在各主要章节开头增加"规划性质"说明

- [ ] **T2**：修改 `docs/security/RLS_POLICIES.md`
  - [ ] 第 1-10 行：修改文档状态为"Implementation SoT"
  - [ ] 插入文档定位与 SoT 层级说明
  - [ ] 保持"未启用"声明不变

- [ ] **T3**：追加 `docs/RLS_STRATEGY_DECISION.md`
  - [ ] 在文件末尾追加"执行记录"章节
  - [ ] 记录核查结果和决策过程

### 5.2 测试补充 TODO（可选，推荐）

- [ ] **T4**：补充应用层权限单元测试
  - [ ] `tests/test_project_permissions.py` - 项目访问权限
  - [ ] `tests/test_ad_account_permissions.py` - 账户访问权限
  - [ ] `tests/test_topup_permissions.py` - 充值申请权限

- [ ] **T5**：创建权限审计脚本
  - [ ] `backend/scripts/audit_rls_filters.py` - 扫描未应用权限过滤的查询

### 5.3 代码审查清单更新 TODO

- [x] **T6**：更新 `.github/PULL_REQUEST_TEMPLATE.md` ✅ **已完成**
  - [x] 创建 PR 模板文件
  - [x] 增加"权限与安全检查"章节，包含：
    - 数据库查询权限检查（6 项）
    - 资源访问权限检查（3 项）
    - 敏感操作检查（3 项）
    - 参考文档链接

---

## 六、长期规划与再评估触发条件

### 6.1 短期工作（1-3 个月）

**应用层权限加固**：
1. 补充应用层权限测试覆盖率至 80% 以上
2. 编写权限审计脚本，定期扫描未应用 RLS 过滤的查询
3. 在代码审查中强制检查权限过滤逻辑

### 6.2 长期规划（6-12 个月，可选）

**何时再次评估启用数据库层 RLS**：

评估启用 DB RLS 的**触发条件**：

| 触发条件 | 当前状态 | 目标状态 |
|---------|---------|---------|
| **应用层权限测试覆盖率** | [待评估] | ≥ 80% 覆盖核心权限路径 |
| **RBAC 权限矩阵稳定性** | [待评估] | 连续 3 个月无重大权限变更 |
| **Schema 重构风险** | [待评估] | 未来 6 个月内无大规模表结构重构计划 |
| **Session Context 方案** | ❌ 未实现 | 已有清晰的 JWT/session context 注入方案（用于 `auth.uid()` 等函数） |
| **多租户需求** | ❌ 未启用 | 明确的 SaaS 化或多租户隔离需求 |
| **合规要求** | ❌ 无强制要求 | GDPR/SOC2 等合规审计要求数据库层隔离 |

**满足以下条件组合时，应启动 DB RLS 迁移评估**：
- ✅ 应用层测试覆盖率 ≥ 80%
- ✅ RBAC 矩阵稳定（3 个月无重大变更）
- ✅ 无即将发生的 Schema 重构
- ✅ 已有 Session Context 注入方案
- ✅ 满足以下任一条件：
  - 出现多租户 SaaS 化需求
  - 监管合规要求数据库层隔离
  - 引入第三方工具需直接访问数据库

**迁移执行参考**：
- 如业务需要，再评估是否启用数据库层 RLS
- 参考 `docs/core/RLS_POLICIES.md` 中的策略设计
- 按照该文档 8.2 节的迁移步骤执行

---

## 七、执行前置条件

### 执行前需在工单/PR 中确认：

**前置条件清单**：

1. **✅ 数据库操作确认**：
   - [ ] 确认不创建任何 Alembic 迁移
   - [ ] 确认不执行任何 `ALTER TABLE ... DISABLE RLS` 或 `DROP POLICY` SQL

2. **✅ 文档修改范围确认**：
   - [ ] 仅修改文档（T1-T3），不修改应用层代码
   - [ ] 保留 `docs/security/RLS_POLICIES.md` 作为当前实现行为的 Implementation SoT
   - [ ] 标注 `docs/core/RLS_POLICIES.md` 为规划文档（未启用）

3. **✅ 测试补充确认**：
   - [ ] 明确是否在本次改动中同时补充权限测试（T4-T5）
   - [ ] 如不在本次执行，需创建后续工单跟踪

4. **✅ 验证环境准备**：
   - [ ] 测试环境可用于执行 4.2 节的 SQL 验证
   - [ ] 现有权限测试可正常运行

5. **✅ 沟通与审批**：
   - [ ] 团队内部已沟通文档修改意图
   - [ ] Tech Lead 或 DBA 已审核本执行计划

**风险接受声明**：
- [ ] 理解本次修改不涉及数据库变更，仅为文档修正
- [ ] 理解应用层权限逻辑保持不变
- [ ] 理解未来如需启用 DB RLS，需另行评估与迁移

---

## 八、与原计划的差异对比

| 原计划内容 | 实际情况 | 调整说明 |
|-----------|---------|---------|
| "新增迁移 DISABLE RLS for 7 张表" | ❌ 不需要 | 数据库层 RLS 从未启用 |
| "DROP POLICY for daily_reports/projects 等" | ❌ 不需要 | 策略从未创建 |
| "迁移文件命名：20251120_disable_rls_*.py" | ❌ 不需要 | 无需创建迁移 |
| "docs/core/RLS_POLICIES.md 标记为规划" | ✅ 需要 | 核心工作，避免误导 |
| "docs/security/RLS_POLICIES.md 归档/废弃" | ❌ 改为保留 | 标记为"Implementation SoT" |
| "补强应用层权限测试" | ✅ 推荐 | 可选但强烈推荐 |

---

## 九、工作量评估与执行建议

### 9.1 工作量评估

| 工作项 | 预计时间 | 优先级 |
|-------|---------|-------|
| 文档修改（T1-T3） | 1-2 小时 | **P0 - 必须** |
| 数据库验证（SQL 检查） | 30 分钟 | **P0 - 必须** |
| 测试补充（T4-T5） | 4-8 小时 | P1 - 推荐 |
| 代码审查清单更新（T6） | 1 小时 | P1 - 推荐 |
| **总计** | **1.5-11.5 小时** | - |

### 9.2 推荐执行顺序

**第 1 步：立即执行**（30 分钟）
- 在测试环境执行 SQL 检查（4.2 节）
- 确认数据库无 RLS 策略

**第 2 步：第 1 天**（1-2 小时）
- 执行文档修改（T1-T3）
- 创建 Git 分支 `docs/rls-strategy-a-execution`
- 提交 PR 供团队审核

**第 3 步：第 2-3 天**（可选，4-9 小时）
- 补充权限单元测试（T4-T5）
- 更新代码审查清单（T6）

---

## 十、附录

### 10.1 相关文档索引

- [RLS 策略决策记录](./RLS_STRATEGY_DECISION.md) - 方案选择与分析
- [核心 RLS 策略（规划）](./core/RLS_POLICIES.md) - 未来数据库 RLS 设计
- [当前权限实现（Implementation SoT）](./security/RLS_POLICIES.md) - 应用层权限实现
- [数据模型 SoT](./core/DATA_SCHEMA.md) - 表结构和字段定义
- [权限系统代码](../backend/core/permissions.py) - RBAC 权限矩阵

### 10.2 变更日志

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| v2.0 | 2025-11-20 | **根据全局 SoT 规则调整**：<br>• 修正 SoT 层级表述，明确 core 为根<br>• security 文档定位为 Implementation SoT<br>• 补充"何时再评估 DB RLS"触发条件<br>• 将问句改为"执行前置条件"清单 | Backend Team |
| v1.0 | 2025-11-20 | 初始版本 - 方案 A 执行计划 | Backend Team |

---

**文档维护者**：Backend Team
**最后审核**：2025-11-20
**下次审核**：执行完成后或方案调整时
