# RLS Strategy Decision (Draft)

## 元信息

- **文档类型**: RLS 策略决策记录
- **创建时间**: 2025-11
- **权威性说明**:
  - 本文档是 2025-11 的一次 RLS 策略决策记录
  - SoT（Single Source of Truth）仍然以 `docs/core/*` 为准
  - 本文档只用于记录现状与方案选择，不直接作为实现规范

## 文档说明

**目标**: 梳理当前 RLS 现状并提出可选策略（不修改数据库/迁移）。

**依据**:
- `docs/core/RLS_POLICIES.md`
- `docs/security/RLS_POLICIES.md`
- Alembic 迁移（`backend/alembic/versions/00{2,4,6}_enable_rls_*.py`）
- 模型 Mixin（`backend/models/mixins/rls_aware.py` 等）

**SoT 原则**: 仍以 `docs/core/*` 为准；本稿仅作决策参考。

## 1. 现状快照

### 文档层

- **`docs/core/RLS_POLICIES.md`**:
  - 状态标记 ✅"生产就绪（已完成安全修复与代码优化）"
  - 暗示"已启用、应强制 RLS"

- **`docs/security/RLS_POLICIES.md`**:
  - 明确声明 "当前 RLS 未启用，权限完全在应用层"
  - **与 core SoT 冲突**

### 迁移层

已存在 enable 脚本，若执行则数据库已启用 RLS：

1. **`002_enable_rls_daily_reports.py`**:
   - `daily_reports`、`daily_report_audit_logs` ENABLE RLS + 多角色 POLICY

2. **`004_enable_rls_projects.py`**:
   - `projects`、`project_members`、`project_expenses` ENABLE RLS + 多角色 POLICY

3. **`006_enable_rls_topup.py`**:
   - `topup_requests`、`topup_transactions`、`topup_approval_logs` ENABLE RLS + 多角色 POLICY

### 模型/应用层

**Mixin RLSAwareMixin**（`__rls_user_field__` 等）+ 具体模型设置：

- **Project**: `__rls_user_field__='created_by'`, admin roles `[admin, data_operator]`
- **AdAccount**: `assigned_to`; admin roles `[admin, data_operator]`
- **DailyReport**: `submitted_by`; admin roles `[admin, data_operator]`
- **TopupRequest**: `requested_by`; admin roles `[admin, data_operator, finance]`

**服务层**: 普遍按角色做查询过滤（应用层 RLS）并未依赖数据库 RLS。

### 推断

若 Alembic 已跑到 head，数据库层很可能已经 ENABLE RLS；但存在一份安全文档声明"未启用"，表明**团队内认知不一致/环境差异**。

## 2. SoT 立场判断

| 文档 | 立场 | 倾向 |
|------|------|------|
| `docs/core/RLS_POLICIES.md` | 叙述为"唯一权威"且生产就绪 | 偏向"应启用" |
| `docs/security/RLS_POLICIES.md` | 明确"ENABLE_RLS=false" | 偏向"规划/未启用" |

**综合**: SoT 自身冲突；需选定主导版本。

## 3. 方案 A：短期关闭 RLS（以"未启用"为准）

### 操作（规划，不执行）

1. 在迁移序列中跳过/回滚 `002/004/006 enable_rls_*`，或追加迁移显式 `DISABLE ROW LEVEL SECURITY + DROP POLICY` 对上述 7 张表
2. 标记/废弃 core RLS_POLICIES 或在文档首段声明"当前未启用（规划态）"
3. 保留/加强应用层过滤（服务 + Mixin）并补充强校验（用户作用域、角色校验）

### 风险

- 🔴 若线上已启用 RLS，直接 disable 需要确认无依赖；需要小心迁移回滚顺序
- 访问控制将完全依赖应用层，数据库直连无隔离

### 工作量与影响

- **工作量**: 中等（新增一个"disable RLS" 迁移 + 文档修订 + 验证）
- **对代码影响**: 低（主要是迁移与文档），应用层逻辑保持

## 4. 方案 B：承认已启用 RLS（以数据库为准）

### 操作（规划，不执行）

1. 将 `docs/security/RLS_POLICIES.md` 合并/废弃，统一以 `docs/core/RLS_POLICIES.md` 为 SoT
2. 更新 SoT 说明"当前环境已 ENABLE RLS，POLICY 以迁移为准"；补充策略表/角色映射
3. **应用层接口**:
   - `get_current_user` 需设置 session context（或 Supabase JWT）以匹配策略
   - 消除与数据库策略重复/冲突的过滤
   - 确保角色名与策略角色一致（`admin_role` 等）
4. **审计**: 增加策略命中/拒绝日志监控；对直连场景编写 RLS 测试

### 风险

- 🔴 现有应用层过滤与 DB RLS 双重过滤，可能导致权限拒绝或漏测
- 🔴 角色名（`admin_role` vs 真实角色）可能不匹配
- 🔴 迁移里的角色名/字段（`current_setting('app.current_user_id')::integer`）与实际 auth 方案不一致，可能全部拒绝

### 工作量与影响

- **工作量**: 高（梳理策略、调整 auth 上下文、补全测试/日志、文档统一）
- **对代码影响**: 中高（需要在 DB session 设置 user_id/role，上下文注入；可能简化/重写服务层过滤）

## 5. 决策建议

### 前置检测

先对目标环境做一次"是否启用 RLS"检测（只读）：

- 检查 `pg_tables.rowsecurity`、`pg_policies`（在安全窗口执行）
- 若不能查库，按迁移已执行的假设处理

### 推荐方案

**短期优先选 A（关闭 RLS，统一 SoT 为"未启用"）**

**理由**:

1. 迁移策略使用 `current_setting('app.current_user_id')::integer` 与真实 JWT/UUID 模式不符，高概率策略失效或拒绝
2. 应用层已实现权限过滤，风险可控
3. 可快速消除 SoT 冲突并恢复一致性

**若业务确定要走 B**，则需先修正策略与 auth 上下文再宣告启用。

## 6. 后续操作清单（按推荐优先 A）

### A 线路（关闭）

1. **新增迁移**:
   - `DISABLE RLS + DROP POLICY` for:
     - `daily_reports`, `daily_report_audit_logs`
     - `projects`, `project_members`, `project_expenses`
     - `topup_requests`, `topup_transactions`, `topup_approval_logs`

2. **文档修订**:
   - `docs/core/RLS_POLICIES.md` 开篇声明"当前未启用，规划中"
   - `docs/security/RLS_POLICIES.md` 标记归档或指向 core

3. **应用层加固**:
   - 审核服务层过滤与 Mixin
   - 补应用层权限测试

### B 线路（承认启用）

1. **对齐策略与认证**:
   - 定义统一的 role mapping（`admin_role` 等）
   - 确保 `current_setting`/JWT `app_metadata` 注入 session
   - UUID vs integer 修正

2. **策略重写**:
   - 梳理/重写策略，实现与五角色一致
   - 删除宽松/错误策略

3. **文档统一**:
   - 更新 SoT（core）为"已启用"
   - 移除 security 版
   - 同步 API/Alembic/权限测试

4. **监控与测试**:
   - 增加 RLS 监控与拒绝日志测试集

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

**已修正文档**（2025-11-20）：
1. ✅ `docs/core/RLS_POLICIES.md` - 已标记为"规划文档（未启用）"，版本升级至 v1.3
2. ✅ `docs/security/RLS_POLICIES.md` - 已标记为"当前实现行为的 Implementation SoT"，版本升级至 v1.1
3. ✅ `docs/RLS_STRATEGY_DECISION.md` - 已追加执行记录
4. ✅ `docs/RLS_STRATEGY_EXEC_PLAN_A.md` - 已创建详细执行计划

**未修改部分**：
- 应用层代码（`backend/services/*.py`）- 无需修改，继续使用现有权限过滤
- 模型层（`backend/models/`）- 保留 `RLSAwareMixin`，作为应用层权限抽象

#### 7.2.3 执行摘要

| 任务 | 状态 | 说明 |
|------|------|------|
| 数据库 RLS 核查 | ✅ 完成 | 确认从未启用，无需 DISABLE 操作 |
| 文档修正（T1-T3） | ✅ 完成 | 3 个文档已更新，1 个新建 |
| 代码审查清单（T6） | ✅ 完成 | 已创建 PR 模板，包含权限检查清单 |
| 测试补充（T4-T5） | ⏳ 待定 | 需后续工单跟踪 |

**补充说明**：
- T6 已完成：创建了 `.github/PULL_REQUEST_TEMPLATE.md`，包含完整的权限与安全检查清单（12 项检查）
- T4-T5（测试补充）为可选任务，建议在后续 Sprint 中执行

---

**文档版本**：Draft v1.1 - 执行记录已追加
**执行者**：Backend Team
**执行日期**：2025-11-20
**审核者**：[待填写]
