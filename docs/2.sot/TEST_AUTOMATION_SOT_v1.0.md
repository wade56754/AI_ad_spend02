---
version: "1.0.1"
status: ready_for_production
layer: sot
owner: wade
last_reviewed: 2025-12-06
baseline:
  - MASTER.md v3.5
  - SOT_FREEZE_MANIFEST_v2.6.md
  - BACKEND_REGRESSION_FREEZE_REPORT_v1.0.md
  - AI_CODE_DEV_ORCHESTRATION_SOT_v1.0.md
---

# TEST_AUTOMATION_SOT v1.0.1

> **测试自动化域 Source of Truth 文档**
>
> 本文档定义项目测试自动化 Skill 的拓扑结构、职责边界、合并关系及使用规范。

---

## §1 Scope & Goals

### 1.1 文档范围

本 SoT 涵盖以下测试自动化领域：

| 领域 | 描述 | 入口 Skill |
|------|------|-----------|
| API 测试线 | backend API / 状态机 / ledger 的 pytest/Newman 测试 | ai-ad-api-automation-test v1.5 |
| Agents 测试线 | agents/ 与 .claude/skills/ 的静态一致性检查 | ai-ad-agents-test-orchestrator v2.4 |

### 1.2 目标

1. **统一入口**：将测试域 4 个 Skill 合并为 2 个入口 Skill
2. **职责清晰**：明确 API 测试线与 Agents 测试线的边界
3. **废弃追踪**：记录已废弃 Skill 的迁移路径
4. **规范执行**：定义上线前必做的测试检查项

### 1.3 文档状态说明

> **关于 `status: ready_for_production`**
>
> 本 SoT 文档（TEST_AUTOMATION_SOT v1.0.1）的 `ready_for_production` 状态表示：
> - 文档结构、Skill 拓扑、职责边界、使用规范已稳定，可用于生产环境的测试自动化治理；
> - 文档内容受 SoT 裁判链保护，修改需遵循 RFC 流程。
>
> **Skill 演进状态**（文档约束下的独立演进）：
> - 各入口 Skill 仍有独立的 `status` 字段（如 `beta` / `ready_for_production`）；
> - Skill 状态演进不影响本 SoT 文档的生产就绪状态；
> - 本 SoT 约束 Skill 的行为边界与升级路径，确保演进符合规范。

---

## §2 Test Skill Topology (4→2)

### 2.1 合并前后映射表

| 合并前 Skill | 版本 | 合并后 Skill | 合并模式 |
|-------------|------|-------------|---------|
| ai-ad-api-automation-test | v1.4 | ai-ad-api-automation-test | 保留（升级至 v1.5） |
| ai-ad-test-regression-orchestrator | v1.2.1 | ai-ad-api-automation-test | `mode=REGRESSION` |
| ai-ad-agents-test-orchestrator | v2.3 | ai-ad-agents-test-orchestrator | 保留（升级至 v2.4） |
| ai-ad-agents-test-runner | v2.2.1 | ai-ad-agents-test-orchestrator | `internal_runner_module` |

### 2.2 拓扑图

```
┌─────────────────────────────────────────────────────────────────┐
│                    TEST AUTOMATION DOMAIN                        │
├─────────────────────────────────┬───────────────────────────────┤
│      API 测试线 (Backend)       │     Agents 测试线 (Static)     │
├─────────────────────────────────┼───────────────────────────────┤
│                                 │                               │
│  ┌─────────────────────────┐   │   ┌─────────────────────────┐ │
│  │ ai-ad-api-automation-   │   │   │ ai-ad-agents-test-      │ │
│  │ test v1.5 (ACTIVE)      │   │   │ orchestrator v2.4       │ │
│  │                         │   │   │ (ACTIVE)                │ │
│  │ modes:                  │   │   │                         │ │
│  │ - GENERATE              │   │   │ test_scope:             │ │
│  │ - RUN                   │   │   │ - auto                  │ │
│  │ - NEWMAN                │   │   │ - all                   │ │
│  │ - REPORT                │   │   │ - smoke                 │ │
│  │ - REGRESSION ◄──────────┼───┼───┼─────────────────────┐   │ │
│  └─────────────────────────┘   │   │                     │   │ │
│            ▲                   │   │ internal modules:   │   │ │
│            │ merged as         │   │ - DISCOVERY         │   │ │
│            │ mode=REGRESSION   │   │ - RUN-ONE           │   │ │
│  ┌─────────┴───────────────┐   │   │ - SUMMARY           │   │ │
│  │ ai-ad-test-regression-  │   │   │ - RUN-PYTEST (v2.4) │   │ │
│  │ orchestrator v1.2.1     │   │   │ - RUN-SUITE (v2.4)  │   │ │
│  │ ⚠️ DEPRECATED           │   │   └─────────▲───────────┘   │ │
│  └─────────────────────────┘   │             │               │ │
│                                │             │ merged as     │ │
│                                │             │ internal      │ │
│                                │   ┌─────────┴───────────────┐ │
│                                │   │ ai-ad-agents-test-      │ │
│                                │   │ runner v2.2.1           │ │
│                                │   │ ⚠️ DEPRECATED           │ │
│                                │   │ (internal-only)         │ │
│                                │   └─────────────────────────┘ │
└─────────────────────────────────┴───────────────────────────────┘
```

---

## §3 API Test Line (automation-test v1.5)

### 3.1 Skill 元信息

| 属性 | 值 |
|------|-----|
| Name | ai-ad-api-automation-test |
| Version | 1.5 |
| Status | beta |
| Owner | wade |
| Last Reviewed | 2025-12-06 |

### 3.2 职责边界

**覆盖范围**：
- `backend/` 目录下的 API 端点测试
- 状态机流转测试（8-state DailyReport, 7-state Topup, 5-state Reconciliation）
- Ledger 分录测试（双账本隔离、余额计算）
- Newman/Postman Collection 契约测试

**不覆盖**：
- `agents/` 目录下的代码测试
- `.claude/skills/` 静态一致性检查

### 3.3 支持模式

| Mode | 描述 | 典型用途 |
|------|------|---------|
| GENERATE | 生成 pytest 测试代码 | 新模块测试生成 |
| RUN | 执行 pytest 测试 | 本地/CI 测试执行 |
| NEWMAN | 执行 Newman 契约测试 | API 契约验证 |
| REPORT | 生成测试报告 | 覆盖率与 SoT 对齐报告 |
| REGRESSION | 回归测试编排 (v1.5 新增) | CI 门禁 / OpenSpec 任务生成 |

### 3.4 REGRESSION 子模式详情

REGRESSION 模式包含 3 个子模式（合并自 ai-ad-test-regression-orchestrator v1.2）：

| 子模式 | 参数 | 输出 |
|--------|------|------|
| `module_test` | module_name, change_scope | 测试覆盖计划 + JSON payload + pytest 命令 |
| `change_tasks` | change_id, affected_modules | OpenSpec tasks.md 片段 |
| `ci_helper` | ci_provider | CI YAML job 片段 |

### 3.5 回归基线

| 基线 | 版本 | 结果 | 报告路径 |
|------|------|------|---------|
| Backend Regression Baseline | v1.0 | 198 passed, 0 failed | `docs/4.testing/BACKEND_REGRESSION_FREEZE_REPORT_v1.0.md` |

---

## §4 Agents Test Line (agents-test-orchestrator v2.4)

### 4.1 Skill 元信息

| 属性 | 值 |
|------|-----|
| Name | ai-ad-agents-test-orchestrator |
| Version | 2.4 |
| Status | ready_for_production |
| Owner | wade |
| Last Reviewed | 2025-12-06 |

### 4.2 职责边界

**覆盖范围**：
- `agents/` 目录下的代码静态测试
- `agents/agent_core/` 各 Agent 实现
- `agents/skills/` 各 Skill 实现
- `agents/tools/` 工具层实现
- `.claude/skills/` Skill 定义文件一致性检查

**不覆盖**：
- `backend/` 目录下的 API 测试

**pytest 执行模式说明**：
- **静态模式**（DISCOVERY / RUN-ONE / SUMMARY）：不调用 pytest，仅基于代码静态分析推理测试结果
- **真实执行模式**（RUN-PYTEST / RUN-SUITE，v2.4 新增）：可选启用，调用 pytest 执行实际测试

### 4.3 测试范围参数

| test_scope | 描述 | 典型用途 |
|------------|------|---------|
| auto | 根据 changed_files 自动映射测试 | PR 审查前快速检查 |
| all | 执行 agents/tests/ 下所有测试 | 完整回归 |
| smoke | 最小测试集（关键 config 测试） | 快速烟雾测试 |

### 4.4 内部模块 (v2.3 合并自 test-runner)

| 模块 | 模式 | 描述 |
|------|------|------|
| 静态分析 | DISCOVERY | 扫描测试清单，不执行 |
| 静态分析 | RUN-ONE | 单测试静态推理 |
| 静态分析 | SUMMARY | 最终汇总 |
| 真实执行 (v2.4) | RUN-PYTEST | 调用 pytest 执行单个测试 |
| 真实执行 (v2.4) | RUN-SUITE | 调用 pytest 执行测试套件 |

### 4.5 执行策略

| 策略 | 描述 | 适用场景 |
|------|------|---------|
| static_first | 优先静态分析，UNCERTAIN 时升级 | 快速 PR 审查 |
| hybrid | 静态 + 真实执行混合 | CI/CD 前置闸门 |
| full_execution | 跳过静态，直接 pytest | 发布前回归 |

---

## §5 Deprecated Skills & Migration Rules

### 5.1 已废弃 Skill 列表

| Skill | 版本 | 废弃日期 | 替代方案 | 状态 |
|-------|------|---------|---------|------|
| ai-ad-test-regression-orchestrator | 1.2.1 | 2025-12-06 | ai-ad-api-automation-test (mode=REGRESSION) | deprecated |
| ai-ad-agents-test-runner | 2.2.1 | 2025-12-06 | ai-ad-agents-test-orchestrator (internal module) | deprecated, internal-only |

### 5.2 迁移指南

#### ai-ad-test-regression-orchestrator → ai-ad-api-automation-test

| 原调用方式 | 新调用方式 |
|-----------|-----------|
| `mode=module_test` | `mode=REGRESSION, regression_mode=module_test` |
| `mode=change_tasks` | `mode=REGRESSION, regression_mode=change_tasks` |
| `mode=ci_helper` | `mode=REGRESSION, regression_mode=ci_helper` |

#### ai-ad-agents-test-runner → ai-ad-agents-test-orchestrator

| 原调用方式 | 新调用方式 |
|-----------|-----------|
| 直接调用 test-runner | 不再支持，由 orchestrator 内部处理 |
| `mode=DISCOVERY` | orchestrator 内部 INIT-DISCOVERY 阶段 |
| `mode=RUN-ONE` | orchestrator 内部 RUN-LOOP 阶段 |
| `mode=SUMMARY` | orchestrator 输出 SUMMARY 阶段 |

### 5.3 废弃 Skill 使用限制

**强制规则**：

1. ❌ **禁止**将废弃 Skill 作为入口调用
2. ✅ **允许**作为历史参考和迁移记录查阅
3. ❌ **禁止**在新代码中引用废弃 Skill
4. ⚠️ **警告**：废弃 Skill 的 SKILL.md 文件保留但不再更新

---

## §6 Required Checks Before Deploy

### 6.1 上线前必做检查清单

#### 6.1.1 Backend/API 变更

当修改以下目录时，**必须**执行 API 测试线检查：

- `backend/routers/*.py`
- `backend/services/*.py`
- `backend/models/*.py`

**必做步骤**：

```markdown
- [ ] 调用 ai-ad-api-automation-test (mode=RUN, target_module=<affected>)
- [ ] 执行回归测试：`python run_tests.py --type regression`
- [ ] 对比基线：198 passed, 0 failed
- [ ] 若失败数 > 0，修复后重新执行
```

**推荐命令**：

```powershell
# 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 执行模块测试
python -m pytest backend/tests/api/test_<module>_flow_generated.py -v --tb=short

# 执行完整回归
python run_tests.py --type regression
```

#### 6.1.2 Agents/Skills 变更

当修改以下目录时，**必须**执行 Agents 测试线检查：

- `agents/agent_core/*.py`
- `agents/skills/*.py`
- `agents/tools/*.py`
- `.claude/skills/*/SKILL.md`

**必做步骤**：

```markdown
- [ ] 调用 ai-ad-agents-test-orchestrator (test_scope=auto, changed_files=[...])
- [ ] 检查 verdict：ALLOW / WARN / BLOCK
- [ ] 若 verdict=BLOCK，根据失败列表修复
- [ ] 若 verdict=WARN，在 CI 中执行真实 pytest 验证
```

### 6.2 CI/CD 集成要求

| 变更类型 | 必须通过的检查 | 阻塞条件 |
|---------|---------------|---------|
| Backend API | 回归测试 (198 passed) | failed > 0 |
| Agents/Skills | orchestrator verdict | verdict = BLOCK |
| SoT 文档 | N/A (只读) | N/A |

---

## §7 Change Log

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| 1.0 | 2025-12-06 | 初始版本创建 | wade |
| | | - 测试域 Skill 4→2 合并记录 | |
| | | - API 测试线 (automation-test v1.5) 规范 | |
| | | - Agents 测试线 (orchestrator v2.4) 规范 | |
| | | - 废弃 Skill 迁移指南 | |
| | | - 上线前必做检查清单 | |
| 1.0.1 | 2025-12-06 | Wording & baseline 精修 (Phase 2c) | wade |
| | | - 修正 baseline 引用：SoT Freeze v2.6 → SOT_FREEZE_MANIFEST_v2.6.md | |
| | | - 新增 §1.3 文档状态说明：澄清文档 vs Skill 状态关系 | |
| | | - 修正 §4.2 pytest 执行歧义：区分静态模式与真实执行模式 | |
| | | - 验证 run_tests.py --type regression 命令有效 | |

---

## 附录 A：Skill 文件位置

| Skill | 文件路径 |
|-------|---------|
| ai-ad-api-automation-test | `.claude/skills/ai-ad-api-automation-test/SKILL.md` |
| ai-ad-agents-test-orchestrator | `.claude/skills/ai-ad-agents-test-orchestrator/SKILL.md` |
| ai-ad-test-regression-orchestrator (deprecated) | `.claude/skills/ai-ad-test-regression-orchestrator/SKILL.md` |
| ai-ad-agents-test-runner (deprecated) | `.claude/skills/ai-ad-agents-test-runner/SKILL.md` |

## 附录 B：相关 SoT 文档

| 文档 | 版本 | 用途 |
|------|------|------|
| STATE_MACHINE.md | v2.6 | 状态机定义（8-state DailyReport 等） |
| DATA_SCHEMA.md | v5.2 | 数据结构约束 |
| API_SOT.md | v9.0 | API 端点契约 |
| ERROR_CODES_SOT.md | v2.1 | 错误码定义 |
| LEDGER_SOT.md | v1.1 | 账本分录规则 |
| AI_CODE_DEV_ORCHESTRATION_SOT_v1.0.md | v1.0 | 代码开发编排规范 |
