---
title: AI_DEV_FACTORY_OVERVIEW
version: v1.1.1
status: Ready
last_reviewed: 2025-12-06
owner: AI Factory / AI_ad_spend02
scope: "AI 辅助下的后端 API、前端页面、文档、测试一体化生产流水线"
baseline:
  - MASTER.md v3.6
  - SoT Freeze v2.6
  - API_DEVELOPMENT_FLOW.md v2.3
  - AI_CODE_DEV_ORCHESTRATION_SOT_v1.0
  - BACKEND_REGRESSION_FREEZE_REPORT_v1.1
  - FRONTEND_DEVELOPMENT_FLOW_v1.0 (规划中，占位引用；当前仅在 OVERVIEW 中预留挂载点，实际 Flow 文档尚未成型)
---

# AI_DEV_FACTORY_OVERVIEW v1.1.1
AI_ad_spend02 · AI 代码工厂总览

## 0. 文档级别与 SoT 优先级

### 0.1 本文档的定位

本文档属于 **Dev Guide / Factory Overview 层级**，不是业务 SoT（Single Source of Truth）。

**文档类型**：
- ✅ **描述性文档**：描述 AI 代码工厂的架构、生产线、运行模式
- ✅ **使用指南**：说明如何使用这些生产线和 Skill
- ❌ **不是业务规则定义**：不定义状态机、数据模型、API 契约、错误码等业务规则

### 0.2 SoT 优先级链

当遇到冲突时，按以下优先级链裁决（从高到低）：

```
1. MASTER.md v3.6（项目宪法）
   ↓
2. 业务 SoT（规则层）
   - STATE_MACHINE.md v2.6（状态机定义）
   - DATA_SCHEMA.md v5.2（数据模型）
   - BUSINESS_RULES.md v3.1（业务规则）
   - API_SOT.md v9.0（API 契约）
   - ERROR_CODES_SOT.md v2.1（错误码）
   - AUTH_SPEC.md v2.0（权限模型）
   - 各模块 SOT（如 PROFIT_SOT.md v1.1）
   ↓
3. 编排 SoT（系统层）
   - AI_CODE_DEV_ORCHESTRATION_SOT_v1.0（AI 编排宪法）
   ↓
4. 流程规范（Flow 层）
   - API_DEVELOPMENT_FLOW.md v2.3（API 开发流程）
   - FRONTEND_DEVELOPMENT_FLOW_v1.0（前端开发流程，如存在）
   ↓
5. 基线与金样本（Baseline 层）
   - BACKEND_REGRESSION_FREEZE_REPORT_v1.1（回归基线）
   - AI_CODE_DEV_ORCHESTRATION_SOT 附录 C.1（Golden Pipelines 登记）
   ↓
6. 本文档（AI_DEV_FACTORY_OVERVIEW v1.1.1）
   - 仅作为总览和使用说明，不定义业务规则
```

**重要约束**：
- 本文档只能描述/约束"如何使用这些生产线"，**不能修改具体业务规则和状态机**
- 所有业务规则变更必须通过对应的 SoT 文档（如 API_SOT.md、STATE_MACHINE.md）进行
- 本文档的变更不影响业务 SoT 的权威性

---

## 1. 定义与目标

### 1.1 什么是“AI 代码工厂”

在本项目中，“AI 代码工厂”指一套完整的、可重复的开发生产流水线：

- 以 **SoT 文档** 为最高裁判（Single Source of Truth）；
- 由一组 **Claude Skill / agents + MCP 工具** 驱动；
- 自动/半自动地产出：
  - 后端 API 代码 + 测试；
  - 前端页面代码 + 测试；
  - 对应的文档变更；
  - 回归基线与金样本（Golden Pipelines）记录。

### 1.2 工厂的核心目标

1. **稳定性**：任何改动都能走完“规划 → 实现 → 测试 → 审查 → 文档同步”闭环。
2. **可追溯**：每条流水线都有 run_id / 报告 / 基线记录。
3. **可扩展**：可以增加新的模块、新的技术栈，但不破坏现有流程。
4. **可复用**：后续项目可以直接抄走这套工厂（改 SoT + Skill 即可）。

---

## 2. 总体架构

### 2.1 分层视图

从上到下分 5 层：

1. **SoT 层（规则层）**  
   - MASTER.md v3.6（项目宪法）  
   - 业务 SoT：STATE_MACHINE.md v2.6, DATA_SCHEMA.md v5.2, BUSINESS_RULES.md v3.1, API_SOT.md v9.0, ERROR_CODES_SOT.md v2.1, AUTH_SPEC.md v2.0  
   - 各模块 SOT（如 PROFIT_SOT.md v1.1）  
   - AI_CODE_DEV_ORCHESTRATION_SOT_v1.0（编排宪法）

2. **Flow 层（开发/测试流程规范）**  
   - API_DEVELOPMENT_FLOW.md v2.3（API 开发 6 步流程）  
   - FRONTEND_DEVELOPMENT_FLOW_v1.0（前端开发流程，如存在）

3. **Baseline & Golden Pipelines 层（基线与金样本登记）**  
   - BACKEND_REGRESSION_FREEZE_REPORT_v1.1（回归基线，213 tests）  
   - AI_CODE_DEV_ORCHESTRATION_SOT_v1.0 附录 C.1（Golden Pipelines 唯一权威登记入口）

4. **AI Skill 层（执行层）**  
   - API 开发流水线：  
     - ai-ad-api-dev-orchestrator v1.1.1（总控）  
     - ai-ad-api-dev-planner v1.0.1  
     - ai-ad-api-dev-impl v1.0  
     - ai-ad-api-dev-reviewer v1.1  
     - ai-ad-api-dev-doc-sync v1.0  
   - 文档治理流水线：  
     - ai-ad-spec-governor  
     - ai-ad-doc-fixer  
     - ai-project-doc-writer  
     - ai-master-architect  
   - 测试流水线：  
     - ai-ad-api-automation-test v1.5（REGRESSION 支持）  
     - ai-ad-agents-test-orchestrator v2.3  
   - 平台工具：  
     - agent-platform-orchestrator

5. **运行环境层（MCP / CLI / IDE）**  
   - Claude Desktop + skills（use context7）  
   - Cursor / VSCode 中的 Claude Code / MCP 服务  
   - 本地 CLI：`python -m agent_platform.cli orch ...`  
   - pytest / npm / supabase 等实际命令行工具

### 2.2 高层结构示意

（逻辑示意，不要求与当前代码 100% 一致）

```mermaid
flowchart TD
    SoT[SoT 文档层\nMASTER / STATE_MACHINE / API_SOT / ...]
    Flow[开发流程文档\nAPI_DEVELOPMENT_FLOW / FRONTEND_DEVELOPMENT_FLOW / ...]
    Skills[AI Skills 层\napi-dev / fe-dev / doc / test]
    Runtime[MCP / CLI / IDE\nClaude Desktop / Cursor / agent_platform]

    SoT --> Flow
    Flow --> Skills
    Skills --> Runtime
    Runtime --> Skills
    Skills --> Code[代码 / 测试 / 文档仓库]
    Code --> Regression[回归基线\nBACKEND_REGRESSION_FREEZE_REPORT / Golden Samples]
    Regression --> SoT
## 3. 核心生产线一览

### 3.1 后端 API 开发流水线

**流水线摘要表**：

| 字段 | 值 |
|------|-----|
| **流水线名** | Backend API Development Pipeline |
| **当前状态** | ✅ 已投入使用 |
| **主 Orchestrator** | `ai-ad-api-dev-orchestrator v1.1.1` |
| **关键子 Skill** | planner v1.0.1, impl v1.0, reviewer v1.1, doc-sync v1.0 |
| **输入契约概要** | `module`, `endpoint`, `change_type`, `mode`, `description`, `auto_write`, `run_tests`, `constraints` |
| **输出概要** | JSON 报告（run_id, pytest_summary, review_result, doc_sync）+ Markdown 摘要 |
| **是否写代码** | ✅ 是（当 `auto_write=true` 时） |
| **是否写文档** | ❌ 否（仅生成建议，需人工确认） |
| **是否触发测试** | ✅ 是（当 `run_tests=true` 时，通过 impl 执行 pytest） |
| **规范来源** | API_DEVELOPMENT_FLOW.md v2.3 + API_SOT.md v9.0 + AI_CODE_DEV_ORCHESTRATION_SOT_v1.0 |

**Skill 组合（5 步）**：

ai-ad-api-dev-planner

只读 SoT + 代码 → 给出 files_to_touch / dev_steps / review_checklist

ai-ad-api-dev-impl

根据 plan 修改 schema / service / router / tests

支持 auto_write / run_tests

pytest（通过 MCP 或本地命令执行）

如：python -m pytest backend/tests/api/...

ai-ad-api-dev-reviewer

按 SoT 检查：Envelope、错误码、权限、状态机、不变量

ai-ad-api-dev-doc-sync

决定要改哪些文档 / 是否要 OpenSpec Proposal

Orchestrator：ai-ad-api-dev-orchestrator

负责：一次性串起 planner → impl → 测试 → reviewer → doc-sync

输出：统一 JSON + Markdown 报告

支持 dry-run / full-run 模式

### 3.2 前端开发流水线

**流水线摘要表**：

| 字段 | 值 |
|------|-----|
| **流水线名** | Frontend Development Pipeline |
| **当前状态** | ⏳ 部分可用（规范已定，Skill 规划中） |
| **主 Orchestrator** | `ai-ad-fe-dev-orchestrator`（规划中） |
| **关键子 Skill** | planner / impl / reviewer（规划中） |
| **输入契约概要** | 待定义 |
| **输出概要** | 待定义 |
| **是否写代码** | 规划中 |
| **是否写文档** | 规划中 |
| **是否触发测试** | 规划中 |
| **规范来源** | FRONTEND_DEVELOPMENT_FLOW_v1.0（如存在） |

#### 3.2.1 已经生效的前端约束

以下约束来自 `FRONTEND_DEVELOPMENT_FLOW_v1.0`（如存在）或前端 SoT 文档，**当前已生效**：

- ✅ **Page Shell 模式**：页面入口（page.tsx）只负责路由与编排，Shell 组件负责模块内部布局与数据组合
- ✅ **统一数据访问层**：API 响应必须使用 Envelope 解包（`success`/`data`/`error` 结构）
- ✅ **Loading/Error/Empty 状态**：所有数据获取场景必须处理这三种状态
- ✅ **目录结构规范**：`frontend/app/(dashboard)/` 路由结构，`frontend/src/modules/{module}/` 模块结构
- ✅ **UI Token 规范**：使用 `FRONTEND_STYLE_GUIDE_v2.3.md` 定义的颜色 Token、间距、圆角等

**说明**：这些约束是**手动开发时必须遵守的规范**，即使自动化 Skill 尚未实现。

#### 3.2.2 规划中的自动化能力

以下 Skill 和自动化能力**尚未实现**，属于规划目标：

- ⏳ **ai-ad-fe-dev-orchestrator**：负责前端页面从"需求"到"代码 + 测试 + 文档"的整条线
- ⏳ **ai-ad-fe-dev-planner**：规划 Page Shell / 组件树 / API 依赖 / files_to_touch
- ⏳ **ai-ad-fe-dev-impl**：生成/修改 TSX + hooks，自动遵守上述约束
- ⏳ **ai-ad-fe-dev-reviewer**：检查目录结构、数据流、错误处理、一致性、可维护性

**状态标注**：`status: planned / not implemented`

**说明**：前端生产线目前处于"规范已起草、Skill 规划中"的状态，不影响后端工厂上线；属于下一阶段扩展。

### 3.3 文档治理流水线

**流水线摘要表**：

| 字段 | 值 |
|------|-----|
| **流水线名** | Documentation Governance Pipeline |
| **当前状态** | ✅ 部分可用（Skill 已存在，合并规划中） |
| **主 Orchestrator** | `ai-ad-spec-governor`（规划中，将合并多个 Skill） |
| **关键子 Skill** | spec-governor, doc-fixer, project-doc-writer, master-architect |
| **输入契约概要** | 待统一 |
| **输出概要** | 文档修改建议 / OpenSpec Proposal 提示 |
| **是否写代码** | ❌ 否 |
| **是否写文档** | ✅ 是（doc-fixer 执行修改） |
| **是否触发测试** | ❌ 否 |
| **规范来源** | 各 SoT 文档的版本管理规范 |

**目的**：让文档也有生产线，而不是散养。

**核心 Skill（合并后的目标结构）**：

ai-ad-spec-governor

文档治理总调度器（取代本地 doc-orchestrator / sot-pipeline / system-auditor）

决策：哪些文档要改 / 改动类型 / 是否需要 OpenSpec Proposal

ai-ad-doc-fixer

具体执行修改：修正格式 / 版本引用 / SoT 链

ai-project-doc-writer

生成新的开发指南 / 模块文档

ai-master-architect

宪法级裁决：遇到冲突时决定谁听谁

**目标状态总结**：

文档治理域收敛为 4 个核心 Skill：`ai-ad-spec-governor`（治理/编排）、`ai-ad-doc-fixer`（修复执行）、`ai-project-doc-writer`（文档生成）、`ai-master-architect`（宪法级裁决）；其余历史 Skill 仅在 Skill 审计报告中保留为 deprecated 记录。

### 3.4 测试自动化流水线

**流水线摘要表**：

| 字段 | 值 |
|------|-----|
| **流水线名** | Test Automation Pipeline |
| **当前状态** | ✅ 已投入使用（Phase 2 已完成） |
| **主 Orchestrator** | 无统一 orchestrator（各测试线独立） |
| **关键子 Skill** | api-automation-test v1.5, agents-test-orchestrator v2.3 |
| **输入契约概要** | `mode` (GENERATE/RUN/NEWMAN/REPORT/REGRESSION), `target_module`, `test_level` |
| **输出概要** | pytest 测试代码 / 测试报告 / 回归建议 |
| **是否写代码** | ✅ 是（GENERATE 模式生成测试代码） |
| **是否写文档** | ❌ 否 |
| **是否触发测试** | ✅ 是（RUN / REGRESSION 模式执行 pytest） |
| **规范来源** | AUTOMATION_TEST_SPEC_v1.4.md, BACKEND_REGRESSION_FREEZE_REPORT_v1.1 |

**API 测试线**：

- **ai-ad-api-automation-test v1.5**
  - mode: GENERATE / RUN / NEWMAN / REPORT / REGRESSION
  - REGRESSION 模式吸收了原 ai-ad-test-regression-orchestrator
  - 基线：BACKEND_REGRESSION_FREEZE_REPORT_v1.1（213 tests）

**Agents 测试线**：

- **ai-ad-agents-test-orchestrator v2.3**
  - 内嵌 _static_test_executor（原 runner）
  - 只做静态巡检：不直接跑 pytest

## 4. 一条完整业务变更的“工厂流水线”

本节定义：一个真实需求从提出到落地，在 AI 工厂里的标准路径。

### 4.1 典型场景：新增/增强一个 API + 对应前端页面

**需求输入**

在 OpenSpec / tasks.md / 设计文档中，写清：

- 目标模块：如 `finance_profit`
- 端点：如 `GET /api/v1/finance/profit/summary`
- 业务要求：过滤条件、聚合方式、权限要求

**API 开发流水线（Backend）**

调用 `ai-ad-api-dev-orchestrator`：

- Step 1: planner → files_to_touch / dev_steps
- Step 2: impl → 生成或修改 schema / service / router / tests
- Step 3: pytest → 本地或 MCP 执行
- Step 4: reviewer → P0/P1/P2 问题清单
- Step 5: doc-sync → 建议修改 API_SOT / 模块 SOT / OpenSpec

**前端开发流水线（Frontend）**（规划目标）

调用 `ai-ad-fe-dev-orchestrator`（规划中）：

- Step 1: SoT + API 报告 → 规划 Page Shell + 组件
- Step 2: 生成/修改 TSX + hooks
- Step 3: 执行前端测试 / lint
- Step 4: 审查 UI 实现与 FRONTEND_DEVELOPMENT_FLOW 一致性

**回归与金样本**

- API 端：使用 `ai-ad-api-automation-test` 的 REGRESSION 模式
- 如果需要，将新的测试文件纳入 `BACKEND_REGRESSION_FREEZE_REPORT_v1.x`
- 整体流水线：将 run_id、模块、端点、结果记录进 `AI_CODE_DEV_ORCHESTRATION_SOT` 附录 C.1

### 4.2 典型调用示例

#### 4.2.1 Claude Desktop / Cursor 中调用

在 Claude 对话中，通过 Skill 调用方式触发：

```json
{
  "module": "finance_profit",
  "change_type": "api",
  "mode": "feature",
  "endpoint": "GET /api/v1/finance/profit/summary",
  "description": "对 Finance Profit Summary 接口执行完整流水线验证",
  "auto_write": true,
  "run_tests": true,
  "constraints": {
    "touch_only_listed_files": true,
    "respect_sot": true
  }
}
```

**说明**：上述 JSON 结构为示例，实际调用时需根据 `ai-ad-api-dev-orchestrator v1.1.1` 的输入契约调整字段。

#### 4.2.2 CLI 调用（如支持）

```bash
# 示例命令（占位符，实际路径需根据项目配置调整）
python -m agent_platform.cli orch \
  --module finance_profit \
  --endpoint "GET /api/v1/finance/profit/summary" \
  --change-type api \
  --mode feature \
  --auto-write \
  --run-tests
```

**说明**：CLI 调用方式取决于 `agent_platform` 的实际实现，此处仅为示例。

### 4.3 各阶段通过标准

| 阶段 | Pass 条件 | 不通过条件 |
|------|----------|-----------|
| **Planner** | 成功生成 `files_to_touch` / `dev_steps` / `review_checklist` | 无法识别模块/端点，或 SoT 冲突无法解决 |
| **Impl** | 代码生成/修改完成，`files_changed` 非空 | 代码生成失败，或违反 SoT 约束（如发明新错误码） |
| **Pytest** | `executed=true` 且 `failed=0` 且 `errors=0` | `executed=false` 或 `failed>0` 或 `errors>0` |
| **Reviewer** | `status=pass` 且 `p0_count=0` 且 `p1_count=0` | `status=fail` 或 `p0_count>0` 或 `p1_count>0` |
| **Doc Sync** | 生成文档更新建议（P2 问题可接受） | 无输出或严重文档冲突 |

**整体流水线通过标准**：

- ✅ `pytest_summary.executed=true` 且 `failed=0` 且 `errors=0`
- ✅ `review_result.status=pass` 且 `p0_count=0` 且 `p1_count=0`
- ✅ `review_result.recommend_deploy=true`
- ✅ `doc_sync.doc_desync_risk` 为 `low` 或 `medium`（P2 可接受）

**不通过情况**：
- ❌ pytest 失败或有 errors>0 → **不能**直接往下当"成功流水线"记入 Golden Pipelines
- ❌ 存在 P0/P1 审查问题 → **不能**视为通过，需修复后重新运行

## 5. Golden Pipelines（金样本流水线）

### 5.1 定义

金样本流水线指：

- 在**完整工厂流程**下跑通的真实业务场景；
- 满足：
  - API + 测试 + 审查 + 文档同步全部通过；
  - 回归基线中有明确记录；
  - Orchestrator 报告无 P0/P1。

### 5.2 登记机制

**唯一权威登记位置**：`AI_CODE_DEV_ORCHESTRATION_SOT_v1.0` 的 **附录 C.1：Golden Pipeline Samples**

**本文档的作用**：仅作为索引与摘要，详细记录请查阅上述 SoT 文档。

**登记流程**：
1. 完成完整流水线（planner → impl → pytest → reviewer → doc-sync）
2. 满足通过标准（见 4.3 节）
3. 将 run_id、模块、端点、结果记录到 `AI_CODE_DEV_ORCHESTRATION_SOT` 附录 C.1
4. 如需纳入回归基线，更新 `BACKEND_REGRESSION_FREEZE_REPORT_v1.x`

### 5.3 当前已登记样本

#### Sample #1: Finance Profit Summary API

**索引信息**：
- **登记文档**：`AI_CODE_DEV_ORCHESTRATION_SOT_v1.0` 附录 C.1 Sample #1
- **回归基线**：`BACKEND_REGRESSION_FREEZE_REPORT_v1.1` 第 2.7 节
- **run_id**: `orch-20251206-finance-profit-summary-002`

**摘要**：
- **模块**：`finance_profit`
- **端点**：`GET /api/v1/finance/profit/summary`
- **Orchestrator**：`ai-ad-api-dev-orchestrator v1.1.1`
- **测试结果**：15/15 passed, 0 failed, 0 errors
- **审查结果**：status=pass, p0_count=0, p1_count=0, recommend_deploy=true
- **回归基线**：BACKEND_REGRESSION_FREEZE_REPORT_v1.1（213 tests，含 finance_profit 15 tests）
- **状态**：✅ 已纳入 Golden Pipelines

**后续计划**：计划新增至少 1–2 条包含"状态机 + 写操作"的金样本流水线，例如：
- Topup 请求流转
- Reconciliation Batches 对账流程

## 6. 环境与运行模式

### 6.1 运行环境

**本地开发环境**：
- Python venv + FastAPI 后端
- Node.js + pnpm / npm 前端
- pytest / npm test / supabase 等命令

**AI 运行环境**：
- Claude Desktop（skills + context7）
- Cursor / VSCode（Claude Code + MCP）
- agent_platform CLI（`python -m agent_platform.cli orch ...`）

### 6.2 运行模式

**Dry-Run 模式**：
- 不写文件、不跑真实测试
- 只输出 plan / files_to_touch / 风险评估
- 适用于方案评审、code review 之前

**Full-Run 模式**：
- 允许 auto_write / 运行 pytest / 写文档草案
- 适用于：开发阶段 + 自测阶段

### 6.3 命令速查表

| 场景 | 命令示例（占位符） | 说明 |
|------|------------------|------|
| **单模块回归测试** | `python -m pytest backend/tests/api/test_{module}_flow_generated.py -v` | 运行指定模块的完整测试套件 |
| **API 开发 Full Run** | 通过 Claude 调用 `ai-ad-api-dev-orchestrator`，传入 JSON 参数（见 4.2.1） | 执行完整 API 开发流水线 |
| **回归测试建议** | 通过 Claude 调用 `ai-ad-api-automation-test`，`mode=REGRESSION`, `regression_mode=module_test` | 生成模块回归测试建议 |
| **全量回归基线** | `python run_tests.py --type regression` | 运行全量回归测试（Baseline v1.1: 213 tests） |
| **查看 Golden Pipelines** | 查阅 `docs/2.sot/AI_CODE_DEV_ORCHESTRATION_SOT_v1.0.md` 附录 C.1 | 查看已登记的金样本流水线 |
| **前端模块回归（规划中）** | `# TODO: 前端回归命令将在 FRONTEND_DEVELOPMENT_FLOW_v1.x 中定义` | 当前前端流水线的自动化命令尚未确定，本行仅为未来扩展预留挂点 |

## 7. 度量与阶段性目标

### 7.1 工厂健康度指标（示例）

- 已登记 Golden Pipelines 数量
- 纳入回归基线的模块覆盖率（后端 / 前端）
- Skill 资产数量（总数 / 核心 / 废弃）
- 手动开发 vs AI 工厂执行的比率

### 7.2 当前阶段进度快照（v1.1 视角）

| 模块/能力 | 进度 | 依据说明 |
|----------|------|---------|
| **SoT 体系** | ~85% | 核心业务 SoT（STATE_MACHINE, DATA_SCHEMA, API_SOT, ERROR_CODES_SOT, AUTH_SPEC）已冻结，部分模块 SOT 待完善 |
| **Backend API 工厂** | ~90% | 已投入使用，已有 1 条 Golden Pipeline（finance_profit /summary），写操作样本尚缺 |
| **测试流水线** | ~80% | 结构已简化（4 → 2），REGRESSION 模式已集成，基线 v1.1（213 tests）已冻结 |
| **文档治理** | ~70% | 有完整 Skill 组合，合并规划已出，但统一 orchestrator 尚未实现 |
| **前端工厂** | ~30% | 规范已起草（FRONTEND_DEVELOPMENT_FLOW），但 Skill 套件处于规划中，仅约束生效 |

## 8. 路线图（Roadmap 草稿）

### 短期（当前迭代）

- 再做 1–2 条"含状态机 + 写操作"的 API 金样本流水线
- 将更多测试纳入回归基线（v1.2+）

### 中期（前端线打通）

- 完成 `ai-ad-fe-dev-*` Skill 套件
- 产出 FE Golden Pipeline Sample #1

### 长期（CI 集成）

- 将回归流水线命令固化进 CI（GitHub Actions / GitLab CI）
- 实现"合并前自动跑关键流水线"的门禁机制

---

## 9. Change Log

| Version | Date | Changes |
|---------|------|---------|
| v1.1.1 | 2025-12-06 | P2 微调优化：澄清 FRONTEND_DEVELOPMENT_FLOW 引用语义（规划中/占位引用）；在命令速查表中为前端流水线预留挂点；文档治理流水线补充目标结构（4 Skill 收敛） |
| v1.1 | 2025-12-06 | 精修升级：新增文档级别与 SoT 优先级说明；分层结构从 4 层扩展为 5 层（Flow vs Baseline 分离）；核心生产线章节统一化（添加摘要表）；完整业务变更流水线增加调用示例和通过标准表；Golden Pipelines 与 AI_CODE_DEV_ORCHESTRATION_SOT_v1.0 强绑定；前端工厂拆分已定 vs 未定；进度评估表格化；新增命令速查表；status 从 Draft 升级为 Ready |
| v1.0 | 2025-12-06 | 初始版本 |