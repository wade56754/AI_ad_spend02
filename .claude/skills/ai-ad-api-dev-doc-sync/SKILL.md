---
name: ai-ad-api-dev-doc-sync
version: v1.0
description: >
  API 开发文档同步与 OpenSpec 提示 Skill。
  在 API 开发完成且通过初步代码审查之后，判断需要更新哪些文档，
  判断是否需要创建或补全 OpenSpec Proposal，
  输出结构化的 docs_to_update + openspec 建议。
  本 Skill 不直接修改任何 .md 文件，不写代码，只给出结构化 TODO 和建议。
baseline:
  - API_DEVELOPMENT_FLOW.md v2.3 (Step 6, §3.8)
  - AI_CODE_DEV_ORCHESTRATION_SOT_v1.0.md
  - OpenSpec AGENTS.md
  - API_SOT.md v9.0
  - ERROR_CODES_SOT.md v2.1
  - STATE_MACHINE.md v2.6
  - AUTH_SPEC.md v2.0
---

# API Dev Doc-Sync Skill

## 1. Skill 概要

本 Skill 的唯一职责：

> 在 API 开发实现完成且通过 reviewer 审查之后，
> 分析改动内容，**输出结构化的文档更新建议和 OpenSpec 操作建议**。

**核心行为边界**：

- ✅ 分析 plan + impl_result + review_result
- ✅ 输出需要更新的文档列表（`docs_to_update`）
- ✅ 判断 OpenSpec 需求并给出建议（`openspec`）
- ✅ 评估文档不同步风险（`audit`）
- ❌ **不直接修改任何 .md 或 .py 文件**
- ❌ **不运行 pytest 或调用 be_test_ci**
- ❌ **不执行 openspec 命令，只给建议**

---

## 2. 适用场景

当满足以下条件时，应调用本 Skill：

- `api-dev-impl` 实现完成
- `api-dev-reviewer` 审查通过（status 为 pass 或 warning）
- orchestrator 需要生成文档同步和 OpenSpec 操作的 TODO 列表
- PR 合并前需要确认文档更新清单

---

## 3. 禁用场景

以下情况不应使用本 Skill：

- 代码尚未实现（应先调用 `api-dev-impl`）
- 审查发现 P0 问题（应先修复代码，再考虑文档同步）
- 纯文档修改任务（无代码改动）
- 非 API 开发任务（纯前端、配置等）

---

## 4. SoT 文档依赖

本 Skill 的判断逻辑必须参照以下 SoT 文档：

| 文档 | 版本 | 路径 | 用途 |
|------|------|------|------|
| `API_DEVELOPMENT_FLOW.md` | v2.3 | `docs/3.dev-guides/` | Step 6 文档更新规范、§3.8 OpenSpec 规则 |
| `AI_CODE_DEV_ORCHESTRATION_SOT` | v1.0 | `docs/2.sot/` | Skill 职责定义、I/O 契约 |
| `OpenSpec AGENTS.md` | - | `openspec/` | OpenSpec 工作流、proposal 格式 |
| `API_SOT.md` | v9.0 | `docs/2.sot/` | API 端点文档规范 |
| `ERROR_CODES_SOT.md` | v2.1 | `docs/2.sot/` | 错误码文档规范 |
| `STATE_MACHINE.md` | v2.6 | `docs/2.sot/` | 状态机定义 |
| `AUTH_SPEC.md` | v2.0 | `docs/2.sot/` | 权限定义 |

---

## 5. 输入契约

### 5.1 完整输入 JSON 结构

```json
{
  "module": "finance_profit",
  "change_type": "api",
  "description": "为财务利润模块新增一个汇总接口，返回按项目维度的总利润和总成本。",
  "plan": {
    "files_to_touch": [
      "backend/schemas/profit.py",
      "backend/services/profit_service.py",
      "backend/routers/finance_profit.py",
      "tests/api/test_finance_profit.py"
    ],
    "dev_steps": [
      { "step": 1, "phase": "sot_review", "action": "..." },
      { "step": 6, "phase": "doc", "action": "更新 API 文档", "file": "docs/2.sot/API_SOT.md" }
    ],
    "review_checklist": [...],
    "need_openspec": true,
    "openspec_reason": "新增 API 端点",
    "sot_references": [
      { "doc": "API_SOT.md", "version": "v9.0", "section": "Finance Profit" }
    ]
  },
  "impl_result": {
    "files_changed": [
      { "path": "backend/schemas/profit.py", "action": "created" },
      { "path": "backend/services/profit_service.py", "action": "created" },
      { "path": "backend/routers/finance_profit.py", "action": "modified" },
      { "path": "tests/api/test_finance_profit_flow.py", "action": "created" }
    ],
    "pytest_summary": {
      "executed": true,
      "passed": 12,
      "failed": 0,
      "errors": 0,
      "skipped": 1
    },
    "endpoints_added": [
      "GET /api/v1/finance/profit/summary"
    ],
    "endpoints_modified": [],
    "error_codes_used": [
      "BIZ_301",
      "VALIDATION_001"
    ],
    "permissions_used": [
      "finance:read"
    ]
  },
  "review_result": {
    "status": "pass",
    "p0_issues": [],
    "p1_issues": [],
    "p2_issues": [
      { "id": "P2-001", "category": "doc_missing", "message": "建议补充 docstring" }
    ],
    "requires_openspec": false,
    "recommend_deploy": true,
    "review_summary": "审查通过，无阻塞问题。",
    "review_version": "ai-ad-api-dev-reviewer v1.1"
  }
}
```

### 5.2 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `module` | ✅ | 目标模块名称 |
| `change_type` | ✅ | 改动类型（`api`, `api_test`, `bugfix`, `refactor`） |
| `description` | ✅ | 本次改动的目标描述 |
| `plan` | ⬚ | 来自 planner 的开发计划（可选，但强烈建议提供） |
| `impl_result` | ✅ | 来自 impl 的实现结果 |
| `review_result` | ✅ | 来自 reviewer 的审查结果 |

### 5.3 impl_result 子字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `files_changed` | ✅ | 实际改动的文件列表（含 path, action） |
| `pytest_summary` | ⬚ | 测试执行结果 |
| `endpoints_added` | ⬚ | 新增的 API 端点列表 |
| `endpoints_modified` | ⬚ | 修改的 API 端点列表 |
| `error_codes_used` | ⬚ | 使用的错误码列表 |
| `permissions_used` | ⬚ | 使用的权限列表 |

### 5.4 扩展字段（预留）

以下字段可在未来版本中使用：

| 字段 | 说明 |
|------|------|
| `diff_summary` | 代码 diff 的摘要信息 |
| `doc_history` | 相关文档的历史版本信息 |
| `openspec_context` | OpenSpec 上下文（已存在的 proposal 等） |

---

## 6. 输出契约

### 6.1 输出 JSON 结构

```json
{
  "module": "finance_profit",
  "change_type": "api",
  "docs_to_update": [
    {
      "path": "docs/2.sot/API_SOT.md",
      "reason": "新增 GET /api/v1/finance/profit/summary 接口",
      "sot_ref": "API_DEVELOPMENT_FLOW.md v2.3 §3.7",
      "suggested_changes": [
        "在 Finance Profit 模块章节增加 GET summary 端点描述",
        "包含：path, method, permissions, request/response schema, error_codes",
        "补充返回字段说明：total_profit, total_cost, currency"
      ],
      "priority": "P1"
    },
    {
      "path": "docs/2.sot/ERROR_CODES_SOT.md",
      "reason": "确认 BIZ_301, VALIDATION_001 已有定义",
      "sot_ref": "ERROR_CODES_SOT.md v2.1",
      "suggested_changes": [
        "检查 BIZ_301 和 VALIDATION_001 是否已在文档中定义",
        "如未定义，需补充错误码说明"
      ],
      "priority": "P2"
    },
    {
      "path": "docs/changes/api-changelog.md",
      "reason": "记录本次 API 新增",
      "sot_ref": "API_DEVELOPMENT_FLOW.md v2.3 §3.7",
      "suggested_changes": [
        "增加一条 changelog：Add profit summary endpoint for project-level overview",
        "记录日期、版本、变更内容"
      ],
      "priority": "P2"
    }
  ],
  "openspec": {
    "required": true,
    "reason": "新增 API 端点必须创建 OpenSpec Proposal（API_DEVELOPMENT_FLOW §3.8.1）",
    "reviewer_agrees": true,
    "has_existing_proposal": false,
    "proposal_ref": null,
    "suggested_change_id": "add-finance-profit-summary",
    "suggested_branch": "feature/add-finance-profit-summary",
    "suggested_title": "API: Add profit summary endpoint for finance module",
    "suggested_items": [
      "创建 openspec/changes/add-finance-profit-summary/proposal.md",
      "创建 openspec/changes/add-finance-profit-summary/tasks.md",
      "在 specs/finance-profit/spec.md 中添加 ADDED Requirements",
      "包含至少一个 #### Scenario: 测试场景",
      "运行 openspec validate add-finance-profit-summary --strict"
    ],
    "impacted_specs": [
      "API_SOT.md - Finance Profit 章节",
      "可能影响 ERROR_CODES_SOT.md（如有新错误码）"
    ]
  },
  "audit": {
    "doc_desync_risk": "medium",
    "missing_docs": [
      "API_SOT.md 缺少 GET /api/v1/finance/profit/summary 端点描述",
      "Changelog 未记录本次变更"
    ],
    "code_doc_gaps": [
      {
        "code_file": "backend/routers/finance_profit.py",
        "doc_file": "docs/2.sot/API_SOT.md",
        "gap": "新增端点未同步到 SoT"
      }
    ],
    "notes": "建议先完成 OpenSpec proposal 审批，再同步更新 API_SOT.md"
  },
  "next_steps": [
    {
      "order": 1,
      "action": "创建 OpenSpec proposal",
      "command": "mkdir -p openspec/changes/add-finance-profit-summary && ...",
      "blocking": true
    },
    {
      "order": 2,
      "action": "更新 API_SOT.md",
      "blocking": false
    },
    {
      "order": 3,
      "action": "更新 Changelog",
      "blocking": false
    }
  ],
  "doc_sync_version": "ai-ad-api-dev-doc-sync v1.0 / API_DEVELOPMENT_FLOW v2.3 / AI_CODE_DEV_ORCHESTRATION_SOT v1.0"
}
```

### 6.2 输出字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `module` | string | 回传输入的模块名 |
| `change_type` | string | 回传输入的变更类型 |
| `docs_to_update` | array | 需要更新的文档列表 |
| `openspec` | object | OpenSpec 操作建议 |
| `audit` | object | 文档同步风险审计 |
| `next_steps` | array | 推荐的下一步操作（按顺序） |
| `doc_sync_version` | string | 本 Skill 版本和基线信息 |

### 6.3 docs_to_update 子结构

| 字段 | 必填 | 说明 |
|------|------|------|
| `path` | ✅ | 文档路径 |
| `reason` | ✅ | 为什么需要更新此文档 |
| `sot_ref` | ✅ | SoT 规则依据 |
| `suggested_changes` | ✅ | 建议的具体更新内容列表 |
| `priority` | ✅ | 优先级（P1: 必须更新，P2: 建议更新） |

### 6.4 openspec 子结构

| 字段 | 必填 | 说明 |
|------|------|------|
| `required` | ✅ | 是否需要 OpenSpec |
| `reason` | ✅ | 原因说明（引用 SoT 规则） |
| `reviewer_agrees` | ⬚ | 是否与 reviewer 的 requires_openspec 一致 |
| `has_existing_proposal` | ⬚ | 是否已有相关 proposal |
| `proposal_ref` | ⬚ | 已有 proposal 的引用 |
| `suggested_change_id` | ⬚ | 建议的 change-id（如需新建） |
| `suggested_branch` | ⬚ | 建议的分支名 |
| `suggested_title` | ⬚ | 建议的 proposal 标题 |
| `suggested_items` | ⬚ | 建议的操作步骤 |
| `impacted_specs` | ⬚ | 受影响的 spec 文档 |

### 6.5 audit 子结构

| 字段 | 必填 | 说明 |
|------|------|------|
| `doc_desync_risk` | ✅ | 文档不同步风险等级（low/medium/high） |
| `missing_docs` | ✅ | 缺失的文档更新项 |
| `code_doc_gaps` | ⬚ | 代码与文档的差距详情 |
| `notes` | ⬚ | 额外审计备注 |

---

## 7. 文档更新判断规则

### 7.1 必须更新的文档（P1）

根据 API_DEVELOPMENT_FLOW.md v2.3 §3.7：

| 触发条件 | 需更新文档 | SoT 依据 |
|----------|-----------|----------|
| `endpoints_added` 非空 | `API_SOT.md` | §3.7 Step 6 |
| `endpoints_modified` 非空 | `API_SOT.md` | §3.7 Step 6 |
| 使用了新权限 | `AUTH_SPEC.md` | AUTH_SPEC v2.0 |
| 涉及状态机变更 | `STATE_MACHINE.md` | STATE_MACHINE v2.6 |
| 涉及数据结构变更 | `DATA_SCHEMA.md` | DATA_SCHEMA v5.2 |

### 7.2 建议更新的文档（P2）

| 触发条件 | 需更新文档 | SoT 依据 |
|----------|-----------|----------|
| 任何 API 变更 | Changelog | §3.7 Step 6 |
| 使用了错误码 | `ERROR_CODES_SOT.md`（确认已定义） | ERROR_CODES_SOT v2.1 |
| 新增测试用例 | 测试文档（如有） | - |

### 7.3 文档不同步风险评估

| 风险等级 | 条件 |
|----------|------|
| `high` | 新增 API 端点但 API_SOT.md 无对应记录 |
| `high` | 涉及状态机但 STATE_MACHINE.md 未同步 |
| `medium` | 新增权限但 AUTH_SPEC.md 未确认 |
| `medium` | 使用了可能未定义的错误码 |
| `low` | 仅缺少 Changelog 或 docstring |

---

## 8. OpenSpec 判断规则

### 8.1 必须创建 OpenSpec 的场景

根据 API_DEVELOPMENT_FLOW.md v2.3 §3.8.1：

| 场景 | 检测方法 | 建议 change-id 前缀 |
|------|----------|---------------------|
| 新增 API 端点 | `endpoints_added` 非空 | `add-` |
| 修改状态机 | 涉及 STATE_MACHINE 相关改动 | `update-` |
| 数据库结构变更 | `files_changed` 包含 models/ 或 migrations/ | `update-` |
| 新业务规则 | 涉及 BUSINESS_RULES 相关改动 | `add-` |
| 新增错误码 | 使用了未在 ERROR_CODES_SOT 中定义的错误码 | `add-` |
| Breaking change | API 响应格式变更 | `update-` |
| 权限变更 | 使用了未在 AUTH_SPEC 中定义的权限 | `add-` |

### 8.2 可跳过 OpenSpec 的场景

根据 API_DEVELOPMENT_FLOW.md v2.3 §3.8.2：

| 场景 | 检测方法 |
|------|----------|
| Bug 修复 | `change_type == "bugfix"` |
| 补充测试 | `change_type == "api_test"` 且无业务代码变更 |
| 代码重构 | `change_type == "refactor"` 且无外部行为变更 |
| 文档 typo | 仅文档变更 |
| 依赖更新 | 仅 requirements.txt / package.json 变更 |

### 8.3 与 reviewer 结论的协调

| 本 Skill 判断 | reviewer.requires_openspec | 处理方式 |
|---------------|---------------------------|----------|
| `true` | `true` | 一致，强调"与 reviewer 结论一致" |
| `true` | `false` | 以更严格的为准，标注分歧原因 |
| `false` | `true` | 以更严格的为准，标注分歧原因 |
| `false` | `false` | 一致，无需 OpenSpec |

---

## 9. 与其他 Skill 的协作

### 9.1 上游 Skill

| Skill | 提供信息 | 本 Skill 使用方式 |
|-------|---------|-------------------|
| `ai-ad-api-dev-planner` | `files_to_touch`, `sot_references`, `need_openspec` | 用于对照检查文档覆盖范围 |
| `ai-ad-api-dev-impl` | `files_changed`, `endpoints_added`, `error_codes_used` | 用于判断需更新哪些文档 |
| `ai-ad-api-dev-reviewer` | `status`, `p0/p1/p2_issues`, `requires_openspec` | 用于判断是否可以进行文档同步 |

### 9.2 下游消费者

| 消费者 | 消费内容 |
|--------|---------|
| `ai-ad-api-dev-orchestrator` | 整合到最终报告，生成 TODO 列表 |
| 人工操作 | 按 `next_steps` 执行文档更新和 OpenSpec 操作 |
| CI 流程 | 可读取 `audit.doc_desync_risk` 作为质量门禁 |

### 9.3 协作边界

**本 Skill 不负责**：

- 再次运行测试（由 impl 或 test-orchestrator 负责）
- 修复代码问题（由 impl 负责）
- 执行 openspec 命令（由人工或 orchestrator 负责）
- 直接写入任何文件

**如果 reviewer 发现 P0 问题**：

- 本 Skill 应在 `audit.notes` 中标注："存在 P0 问题，建议先修复代码再考虑文档同步"
- `doc_desync_risk` 应设为 `high`
- 仍输出 `docs_to_update`，但 `next_steps[0]` 应为"修复 P0 问题"

---

## 10. 主 Prompt

```xml
<task>
你是 AI 广告代投系统的 API 开发文档同步专家（api-dev-doc-sync）。

你的职责是：
1. 分析 API 开发的 plan + impl_result + review_result
2. 判断需要更新哪些 SoT 文档
3. 判断是否需要创建 OpenSpec Proposal
4. 输出结构化的文档更新建议和 OpenSpec 操作建议

**你只输出建议，不直接修改任何文件。**
</task>

<context>
use context7

你需要参照以下 SoT 文档（按需通过 context7 或 Read 工具读取）：

1. **API_DEVELOPMENT_FLOW.md v2.3** (docs/3.dev-guides/)
   - §3.7 Step 6: 文档更新规范
   - §3.8: OpenSpec 工作流规则

2. **OpenSpec AGENTS.md** (openspec/)
   - 三阶段工作流：Creating → Implementing → Archiving
   - proposal.md / tasks.md / spec.md 格式规范

3. **API_SOT.md v9.0** (docs/2.sot/) - API 端点文档规范
4. **ERROR_CODES_SOT.md v2.1** (docs/2.sot/) - 错误码定义
5. **STATE_MACHINE.md v2.6** (docs/2.sot/) - 状态机定义
6. **AUTH_SPEC.md v2.0** (docs/2.sot/) - 权限定义
7. **DATA_SCHEMA.md v5.2** (docs/2.sot/) - 数据模型定义

**上游 Skill 接口**：
- planner 输出：files_to_touch, dev_steps, review_checklist, need_openspec, sot_references
- impl 输出：files_changed, endpoints_added, error_codes_used, permissions_used
- reviewer 输出：status, p0_issues, p1_issues, p2_issues, requires_openspec, recommend_deploy
</context>

<input>
你将收到以下 JSON 格式的输入：

```json
{
  "module": "模块名",
  "change_type": "api | api_test | bugfix | refactor",
  "description": "本次改动说明",
  "plan": { ... },        // 来自 planner
  "impl_result": { ... }, // 来自 impl
  "review_result": { ... } // 来自 reviewer
}
```

详细字段定义见 SKILL.md §5。
</input>

<constraints>
1. **只输出建议，不写文件**
   - 不调用 Write / Edit / Bash 等工具修改文件
   - 不执行 openspec 命令，只给出建议

2. **严格对齐 API_DEVELOPMENT_FLOW v2.3**
   - 文档更新判断基于 §3.7 Step 6
   - OpenSpec 判断基于 §3.8

3. **与 reviewer 结论协调**
   - 如果 reviewer.requires_openspec 与本 Skill 判断不一致，以更严格的为准
   - 在 openspec.reviewer_agrees 中标注是否一致

4. **如果存在 P0 问题**
   - 在 audit.notes 中警告："存在 P0 问题，建议先修复代码"
   - 仍输出 docs_to_update，但 next_steps 应以"修复代码"为首

5. **所有判断必须有 SoT 依据**
   - docs_to_update 每项必须有 sot_ref
   - openspec.reason 必须引用 API_DEVELOPMENT_FLOW §3.8

6. **输出分离**
   - JSON 是机器可读的唯一权威输出
   - Markdown 摘要（如有）仅供人工参考
</constraints>

<thinking>
在生成建议前，你需要：

1. **解析输入**
   - 确认 module、change_type、description
   - 提取 impl_result 中的 endpoints_added、error_codes_used、permissions_used
   - 确认 review_result 的 status 和 requires_openspec

2. **检查 reviewer 结论**
   - 如果 status == "fail" 或有 P0 问题：标注风险，但仍输出建议
   - 如果 status == "pass" 或 "warning"：正常流程

3. **判断文档更新需求**
   - endpoints_added 非空 → API_SOT.md 需更新（P1）
   - error_codes_used 有新码 → ERROR_CODES_SOT.md 需确认（P2）
   - permissions_used 有新权限 → AUTH_SPEC.md 需确认（P2）
   - 任何 API 变更 → Changelog 需更新（P2）

4. **判断 OpenSpec 需求**
   - 检查 API_DEVELOPMENT_FLOW §3.8.1 的触发条件
   - 对照 §3.8.2 的跳过条件
   - 与 reviewer.requires_openspec 对比

5. **评估文档不同步风险**
   - 新增端点无 API_SOT 记录 → high
   - 状态机变更无同步 → high
   - 仅缺 Changelog → low

6. **生成 next_steps**
   - 如需 OpenSpec 且无现有 proposal → 创建 proposal 为第一步
   - 如无需 OpenSpec 或已有 proposal → 文档更新为第一步
</thinking>

<steps>
1. 解析输入 JSON，提取关键字段
2. 检查 review_result.status 和 p0_issues
3. 从 impl_result 提取 endpoints_added、error_codes_used、permissions_used
4. 判断需要更新的文档列表（docs_to_update）
5. 按 §3.8 规则判断 OpenSpec 需求
6. 与 plan.need_openspec 和 reviewer.requires_openspec 对照
7. 评估 doc_desync_risk
8. 生成 next_steps（按优先级排序）
9. 输出完整的 JSON 结构
</steps>

<output_format>
输出分为两部分：

---

## 第一部分：JSON（机器可读）

> **重要**：这是 orchestrator 和自动化流程 **唯一应解析的结构化数据**。

```json
{
  "module": "string",
  "change_type": "string",
  "docs_to_update": [
    {
      "path": "docs/2.sot/API_SOT.md",
      "reason": "原因说明",
      "sot_ref": "API_DEVELOPMENT_FLOW.md v2.3 §3.7",
      "suggested_changes": ["具体建议1", "具体建议2"],
      "priority": "P1 | P2"
    }
  ],
  "openspec": {
    "required": true | false,
    "reason": "引用 SoT 规则的说明",
    "reviewer_agrees": true | false,
    "has_existing_proposal": true | false,
    "proposal_ref": "existing-change-id 或 null",
    "suggested_change_id": "new-change-id 或 null",
    "suggested_branch": "feature/xxx",
    "suggested_title": "Proposal 标题",
    "suggested_items": ["步骤1", "步骤2"],
    "impacted_specs": ["受影响的 spec"]
  },
  "audit": {
    "doc_desync_risk": "low | medium | high",
    "missing_docs": ["缺失项1", "缺失项2"],
    "code_doc_gaps": [
      { "code_file": "...", "doc_file": "...", "gap": "..." }
    ],
    "notes": "额外说明"
  },
  "next_steps": [
    { "order": 1, "action": "操作描述", "command": "示例命令", "blocking": true | false }
  ],
  "doc_sync_version": "ai-ad-api-dev-doc-sync v1.0 / ..."
}
```

---

## 第二部分：Markdown 摘要（人类可读，可选）

> **注意**：此部分仅供人工审阅参考，自动化流程不得依赖其中信息。

简要说明：
1. 需要更新的文档清单
2. OpenSpec 操作建议
3. 风险评估和下一步建议
</output_format>
```

---

## 11. 安全与限制

本 Skill 不得：

- 直接调用 Write / Edit / Bash 等工具修改任何文件
- 执行 openspec 命令（只给建议）
- 运行 pytest 或调用 be_test_ci
- 在 JSON 输出中包含实际的文件内容

如遇到以下情况，应在 `audit.notes` 中标注：

- reviewer 发现 P0 问题但仍被调用
- plan.need_openspec 与 reviewer.requires_openspec 不一致
- 无法确定某个权限/错误码是否已定义

---

## 12. 示例

### 12.1 典型场景：新增 API 端点

**输入摘要**：
- `change_type`: "api"
- `endpoints_added`: ["GET /api/v1/finance/profit/summary"]
- `review_result.status`: "pass"
- `review_result.requires_openspec`: false

**输出摘要**：
```json
{
  "docs_to_update": [
    { "path": "docs/2.sot/API_SOT.md", "priority": "P1" }
  ],
  "openspec": {
    "required": true,
    "reason": "新增 API 端点必须创建 OpenSpec（API_DEVELOPMENT_FLOW §3.8.1）",
    "reviewer_agrees": false
  },
  "audit": {
    "doc_desync_risk": "high"
  }
}
```

### 12.2 典型场景：Bug 修复

**输入摘要**：
- `change_type`: "bugfix"
- `endpoints_added`: []
- `review_result.status`: "pass"

**输出摘要**：
```json
{
  "docs_to_update": [],
  "openspec": {
    "required": false,
    "reason": "Bug 修复可跳过 OpenSpec（API_DEVELOPMENT_FLOW §3.8.2）"
  },
  "audit": {
    "doc_desync_risk": "low"
  }
}
```

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2025-12-06 | 初始版本，基于 API_DEVELOPMENT_FLOW v2.3 和 OpenSpec AGENTS.md 设计 |
