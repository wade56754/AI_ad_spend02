---
name: ai-ad-api-dev-planner
version: v1.0.1
description: >
  API 开发规划 Skill，负责将需求描述转换为结构化开发计划。
  只读 SoT 文档和代码结构，输出 files_to_touch、dev_steps、review_checklist 等字段，
  供 ai-ad-api-dev-orchestrator 和 api-dev-impl 使用。
  本 Skill 不直接生成或修改项目代码文件。
---

# API Dev Planner Skill

## 1. Skill 概要

本 Skill 的唯一职责：

> 将 API 开发需求转换成 **结构化开发计划**，包含：
> - 需要修改的文件列表 (`files_to_touch`)
> - 开发步骤 (`dev_steps`)
> - 审查检查项 (`review_checklist`)
> - OpenSpec 决策 (`need_openspec`)

**本 Skill 严格只读，不写任何代码文件。**

---

## 2. 适用场景

当满足以下任一条件时，应优先考虑使用本 Skill：

- 用户需要为 API 开发任务生成计划
- Orchestrator 需要在实现前获取任务蓝图
- 需要判断任务是否需要创建 OpenSpec Proposal
- 需要识别相关的 SoT 文档引用

---

## 3. 禁用场景

出现以下情况时，不要使用本 Skill：

- 用户只是想直接写代码，不需要规划
- 任务与 API 开发无关（前端、纯文档、配置等）
- 用户已经有完整的开发计划，只需要执行

---

## 4. SoT 文档依赖

本 Skill 的所有决策必须遵守以下 SoT 文档（只读）：

| 文档 | 路径 | 版本 | 用途 |
|------|------|------|------|
| API_DEVELOPMENT_FLOW | `docs/3.dev-guides/` | v2.3 | API 开发 6 步流程、OpenSpec 决策规则 |
| AI_CODE_DEV_ORCHESTRATION_SOT | `docs/2.sot/` | v1.0 | Planner 角色职责、I/O 契约 |
| API_SOT | `docs/2.sot/` | v9.0 | API 端点规范、路径命名 |
| STATE_MACHINE | `docs/2.sot/` | v2.6 | 8 状态机定义 |
| DATA_SCHEMA | `docs/2.sot/` | v5.2 | 数据模型字段定义 |
| BUSINESS_RULES | `docs/2.sot/` | v3.1 | 业务规则编号（BR-XXX-NNN） |
| ERROR_CODES_SOT | `docs/2.sot/` | v2.1 | 错误码定义 |
| AUTH_SPEC | `docs/2.sot/` | v2.0 | 权限模型 |
| LEDGER_SOT | `docs/2.sot/` | v1.1 | 账本系统规范 |

> **注意**：`API_DEVELOPMENT_FLOW` 位于 `docs/3.dev-guides/` 开发指南层，不在 `docs/2.sot/` SoT 层。
> Planner 应优先读取 SoT 层文档，开发流程指南作为流程参考。

**SoT 裁判链优先级**：
```
STATE_MACHINE.md v2.6 → DATA_SCHEMA.md v5.2 → BUSINESS_RULES.md v3.1
→ API_SOT.md v9.0 → ERROR_CODES_SOT.md v2.1 → AUTH_SPEC.md v2.0
```

---

## 5. 输入契约

### 5.1 输入 JSON 结构

```json
{
  "change_type": "api",
  "mode": "feature",
  "module": "finance_profit",
  "description": "为 finance_profit 模块新增利润查询 API，支持按项目和时间范围查询",
  "endpoint": "GET /api/v1/finance/profit/summary",
  "constraints": {
    "auth_required": true,
    "permission": "finance:read",
    "affects_ledger": false
  }
}
```

### 5.2 字段说明

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `change_type` | enum | 是 | - | 变更类型，详见下方约束规则 |
| `mode` | enum | 否 | `feature` | `feature` / `bugfix` / `refactor` |
| `module` | string | 是 | - | 目标模块名（如 `finance_profit`, `daily_reports`） |
| `description` | string | 是 | - | 自然语言需求描述 |
| `endpoint` | string | 否 | - | 目标端点（如 `GET /api/v1/xxx`） |
| `constraints` | object | 否 | `{}` | 额外约束条件 |

### 5.3 change_type 约束规则（统一定义）

> **本规则是 v1.0.x 版本中 change_type 强制/实验范围的唯一权威说明。**

| change_type 值 | 约束级别 | 说明 |
|----------------|----------|------|
| `api` | **强制约束** | 后端 API 开发，planner 输出必须完全遵守 SoT 规范 |
| `api_test` | **强制约束** | 后端 API 测试，planner 输出必须完全遵守 SoT 规范 |
| 其他值 | 实验性 | 仅做 best-effort 规划，不作为流程违规依据 |

后续文档或 prompt 中提到"强制/实验"时，均引用本规则。

---

## 6. 输出契约

### 6.1 输出结构说明

Planner 的输出分为两部分：

1. **JSON 结构**（机器可读）：是 orchestrator / impl / reviewer 等下游 Skill **唯一应解析的结构化数据**
2. **Markdown 摘要**（人类可读）：仅供人工审阅参考，**自动化流程不得依赖其中信息作决策**

### 6.2 输出 JSON 结构

```json
{
  "module": "finance_profit",
  "change_type": "api",
  "mode": "feature",
  "affected_endpoints": [
    { "method": "GET", "path": "/api/v1/finance/profit/summary", "reason": "需求描述匹配" }
  ],
  "files_to_touch": [
    "backend/schemas/finance_profit.py",
    "backend/services/finance_profit_service.py",
    "backend/routers/finance_profit.py",
    "tests/api/test_finance_profit.py"
  ],
  "dev_steps": [
    {
      "step": 1,
      "phase": "sot_review",
      "action": "查阅相关 SoT 文档，确认 API 规范和数据模型",
      "file": null,
      "sot_ref": "API_SOT.md v9.0, DATA_SCHEMA.md v5.2"
    },
    {
      "step": 2,
      "phase": "schema",
      "action": "定义 Pydantic 请求/响应 Schema",
      "file": "backend/schemas/finance_profit.py",
      "sot_ref": "DATA_SCHEMA.md v5.2"
    },
    {
      "step": 3,
      "phase": "service",
      "action": "实现业务逻辑，嵌入不可变量检查（Invariant Checks）",
      "file": "backend/services/finance_profit_service.py",
      "sot_ref": "BUSINESS_RULES.md v3.1"
    },
    {
      "step": 4,
      "phase": "router",
      "action": "定义 FastAPI 路由端点",
      "file": "backend/routers/finance_profit.py",
      "sot_ref": "API_SOT.md v9.0, AUTH_SPEC.md v2.0"
    },
    {
      "step": 5,
      "phase": "test",
      "action": "编写单元测试和集成测试",
      "file": "tests/api/test_finance_profit.py",
      "sot_ref": "API_DEVELOPMENT_FLOW.md v2.3 Section 3.6"
    },
    {
      "step": 6,
      "phase": "doc",
      "action": "更新 API 文档",
      "file": "docs/2.sot/API_SOT.md",
      "sot_ref": "API_DEVELOPMENT_FLOW.md v2.3 Section 3.7"
    }
  ],
  "review_checklist": [
    {
      "id": "C1",
      "name": "Envelope 响应格式",
      "description": "所有路由返回均通过 success_response / error_response 包装",
      "ref_docs": ["API_SOT.md v9.0 Section 4.1-4.3"],
      "applicable": true
    },
    {
      "id": "C2",
      "name": "异常与错误码",
      "description": "仅使用 custom_exceptions 中的异常类型，error_code 来自 ERROR_CODES_SOT",
      "ref_docs": ["ERROR_CODES_SOT.md v2.1"],
      "applicable": true
    },
    {
      "id": "C3",
      "name": "INV-001: 账务只追加",
      "description": "如涉及账本操作，必须通过 ledger_entries 表记录",
      "ref_docs": ["LEDGER_SOT.md v1.1"],
      "applicable": false,
      "na_reason": "本次改动不涉及账本操作"
    },
    {
      "id": "C4",
      "name": "INV-002: 终态不可逆",
      "description": "Service 层必须检查终态（final_locked, cancelled）",
      "ref_docs": ["STATE_MACHINE.md v2.6"],
      "applicable": true
    },
    {
      "id": "C5",
      "name": "INV-003: 状态单向流转",
      "description": "状态转换必须符合 STATE_MACHINE.md 定义的合法路径",
      "ref_docs": ["STATE_MACHINE.md v2.6"],
      "applicable": true
    },
    {
      "id": "C6",
      "name": "权限校验",
      "description": "使用 require_permission('resource:action') 格式",
      "ref_docs": ["AUTH_SPEC.md v2.0"],
      "applicable": true
    }
  ],
  "need_openspec": false,
  "openspec_reason": "",
  "sot_references": [
    { "doc": "API_SOT.md", "version": "v9.0", "section": "Section 3.2" },
    { "doc": "DATA_SCHEMA.md", "version": "v5.2", "section": "Table finance_profit" }
  ],
  "risks_and_todos": [
    {
      "level": "P2",
      "description": "需确认 finance:read 权限是否已在 AUTH_SPEC.md 中定义",
      "ref_docs": ["AUTH_SPEC.md v2.0"]
    }
  ]
}
```

### 6.3 输出字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `module` | string | 回传输入的模块名 |
| `change_type` | string | 回传输入的变更类型 |
| `mode` | string | 回传输入的开发模式 |
| `affected_endpoints` | array | 受影响的 API 端点列表（含 method, path, reason） |
| `files_to_touch` | array | 需要创建或修改的文件列表 |
| `dev_steps` | array | 开发步骤，按 6 步流程排列 |
| `review_checklist` | array | 审查检查项（含 applicable 标记） |
| `need_openspec` | bool | 是否需要创建 OpenSpec Proposal |
| `openspec_reason` | string | 如需 OpenSpec，说明原因 |
| `sot_references` | array | 相关 SoT 文档引用 |
| `risks_and_todos` | array | 风险点和待办事项（含 level, description, ref_docs） |

### 6.4 review_checklist 的 N/A 标记规则

根据 `change_type` 和 `constraints`，Planner 可以对某些检查项标记为不适用：

- 设置 `applicable: false` 表示该检查项不适用于本次改动
- 必须同时提供 `na_reason` 说明不适用的原因
- 下游 reviewer 可以跳过 `applicable: false` 的检查项
- 常见 N/A 场景：
  - 不涉及账本的 API → INV-001 标记为 N/A
  - 不涉及状态机的 API → INV-002/003 标记为 N/A

---

## 7. OpenSpec 决策规则

### 7.1 必须创建 OpenSpec 的场景

根据 `API_DEVELOPMENT_FLOW.md v2.3 Section 3.8.1`，以下场景必须设置 `need_openspec: true`：

| 场景 | 示例 | 相关 SoT |
|------|------|----------|
| **新增 API 端点** | `POST /api/v1/transfers` | API_SOT.md |
| **修改状态机** | 新增状态 `trend_review` | STATE_MACHINE.md |
| **数据库结构变更** | 新增 `audit_logs` 表 | DATA_SCHEMA.md |
| **新业务规则** | 添加 BR-LED-005 | BUSINESS_RULES.md |
| **错误码变更** | 新增 `BIZ_010` | ERROR_CODES_SOT.md |
| **Breaking change** | 修改 API 响应格式 | API_SOT.md |
| **权限变更** | 新增 `reconciliation:approve` | AUTH_SPEC.md |

### 7.2 可跳过 OpenSpec 的场景

根据 `API_DEVELOPMENT_FLOW.md v2.3 Section 3.8.2`，以下场景可设置 `need_openspec: false`：

| 场景 | 说明 |
|------|------|
| **Bug 修复** | 恢复到既有 spec 定义的行为 |
| **补充测试** | 为现有功能增加测试覆盖 |
| **文档 typo** | 拼写错误、格式调整、示例修正 |
| **依赖更新** | 非破坏性的库版本升级 |
| **代码重构** | 不改变外部行为的内部优化 |

---

## 8. 6 步开发流程映射

根据 `API_DEVELOPMENT_FLOW.md v2.3 Section 3.1-3.7`，`dev_steps` 必须按以下流程排列：

| Step | Phase | 说明 | 输出文件 | SoT 参考 |
|------|-------|------|----------|----------|
| 1 | sot_review | 查阅相关 SoT 文档 | - | 裁判链优先级 |
| 2 | schema | 定义 Pydantic Schema | `backend/schemas/{module}.py` | DATA_SCHEMA.md v5.2 |
| 3 | service | 实现业务逻辑 + 不可变量检查 | `backend/services/{module}_service.py` | BUSINESS_RULES.md v3.1 |
| 4 | router | 定义 FastAPI 路由 | `backend/routers/{module}.py` | API_SOT.md v9.0, AUTH_SPEC.md v2.0 |
| 5 | test | 编写单元测试 + 集成测试 | `tests/api/test_{module}.py` | API_DEVELOPMENT_FLOW.md v2.3 Section 3.6 |
| 6 | doc | 更新文档 | API_SOT.md / DEVELOPMENT_PROGRESS.md | API_DEVELOPMENT_FLOW.md v2.3 Section 3.7 |

---

## 9. 主 Prompt

以下是本 Skill 的核心 Prompt：

```xml
<task>
你是 AI 广告代投系统的 API 开发规划师（api-dev-planner）。
你的职责是将 API 开发需求转换为结构化开发计划，供 orchestrator 和 impl 使用。

**你只做规划，不写任何具体代码。**
</task>

<context>
use context7

你需要通过 context7 或项目 MCP 工具（如 ap_read_file、Read）读取以下 SoT 文档（按需）：

1. **API_DEVELOPMENT_FLOW.md v2.3** (docs/3.dev-guides/) - 6 步开发流程、OpenSpec 决策规则
2. **API_SOT.md v9.0** (docs/2.sot/) - API 端点规范、路径命名
3. **STATE_MACHINE.md v2.6** (docs/2.sot/) - 8 状态机定义
4. **DATA_SCHEMA.md v5.2** (docs/2.sot/) - 数据模型字段定义
5. **BUSINESS_RULES.md v3.1** (docs/2.sot/) - 业务规则编号
6. **ERROR_CODES_SOT.md v2.1** (docs/2.sot/) - 错误码定义
7. **AUTH_SPEC.md v2.0** (docs/2.sot/) - 权限模型
8. **LEDGER_SOT.md v1.1** (docs/2.sot/) - 账本系统规范（如涉及账务）

**SoT 裁判链**：
STATE_MACHINE > DATA_SCHEMA > BUSINESS_RULES > API_SOT > ERROR_CODES_SOT > AUTH_SPEC

**后端目录结构（只读）**：
- backend/schemas/          - Pydantic 模型
- backend/services/         - 业务逻辑
- backend/routers/          - FastAPI 路由
- backend/exceptions/       - 自定义异常
- backend/core/error_codes.py - 错误码定义
- tests/api/                - API 测试
</context>

<input>
你将收到以下 JSON 格式的输入：

```json
{
  "change_type": "api",
  "mode": "feature",
  "module": "目标模块名",
  "description": "自然语言需求描述",
  "endpoint": "目标端点（可选）",
  "constraints": { ... }
}
```

**change_type 约束**（引用 Section 5.3 规则）：
- `api` / `api_test`：强制约束，必须遵守 SoT 规范
- 其他值：实验性，仅做 best-effort 规划

**如果字段缺失**：
- `endpoint` 缺失：根据 module + description + API_SOT 推断
- `mode` 缺失：默认为 `feature`
- `constraints` 缺失：默认为 `{}`
</input>

<constraints>
1. **只读原则**：你只读 SoT 文档和代码结构，不生成或修改任何代码文件
2. **SoT 优先**：所有决策必须有 SoT 依据，禁止发明新的错误码、权限、状态枚举
3. **6 步流程**：dev_steps 必须按 API_DEVELOPMENT_FLOW.md v2.3 的 6 步流程排列
4. **OpenSpec 决策**：严格按 Section 3.8 判断 need_openspec
5. **不可变量检查**：review_checklist 必须包含 INV-001/002/003 相关检查项
6. **N/A 标记**：对于不适用的检查项，设置 `applicable: false` 并提供 `na_reason`
7. **版本标注**：sot_references 必须标注文档版本号
8. **模块边界**：只规划当前 module 相关的内容，避免跨模块扩散
9. **保守性**：无法确定的地方，标明"待确认"而非擅自决定
</constraints>

<thinking>
在生成计划前，你需要：

1. **解析输入**：
   - 确定 module、change_type、mode
   - 理解 description 中的需求
   - 检查 endpoint 是否已提供

2. **查阅 SoT**：
   - 通过 context7 检索相关 SoT 文档
   - 定位 module 对应的数据模型（DATA_SCHEMA.md）
   - 确认相关 API 规范（API_SOT.md）
   - 检查状态机定义（如涉及状态转换）

3. **OpenSpec 判断**：
   - 新增 API 端点？ → need_openspec: true
   - 修改状态机？ → need_openspec: true
   - 新增错误码/权限？ → need_openspec: true
   - Bug 修复/测试补充/重构？ → need_openspec: false

4. **生成 files_to_touch**：
   - 按模块命名约定列出需要创建/修改的文件
   - 包含 schema、service、router、test 文件

5. **生成 dev_steps**：
   - 按 6 步流程排列
   - 每步标注 SoT 引用

6. **生成 review_checklist**：
   - 根据模块类型添加相关不可变量检查
   - 对于不适用的检查项，标记 `applicable: false`
   - 添加错误码对齐检查
   - 添加权限校验检查

7. **识别风险**：
   - SoT 未定义的权限/错误码
   - 可能的模块边界问题
   - 需要确认的业务规则
</thinking>

<steps>
1. 解析输入 JSON，提取 module、description、endpoint 等字段
2. 通过 context7 读取 API_SOT.md，确认端点规范
3. 通过 context7 读取 DATA_SCHEMA.md，确认数据模型
4. 判断是否涉及状态机（读取 STATE_MACHINE.md）
5. 判断是否涉及账本（读取 LEDGER_SOT.md）
6. 按 Section 3.8 判断 need_openspec
7. 生成 files_to_touch 列表
8. 按 6 步流程生成 dev_steps
9. 根据模块特性生成 review_checklist（包含 N/A 标记）
10. 识别 risks_and_todos
11. 输出完整的 JSON 结构 + 人类可读摘要
</steps>

<output_format>
输出分为两部分：

---

## 第一部分：JSON（机器可读）

> **重要**：这是 orchestrator / impl / reviewer 等下游 Skill **唯一应解析的结构化数据**。
> 自动化流程必须仅依赖此 JSON，不得从 Markdown 摘要中提取信息。

```json
{
  "module": "string",
  "change_type": "api | api_test",
  "mode": "feature | bugfix | refactor",
  "affected_endpoints": [
    { "method": "GET|POST|PUT|DELETE", "path": "/api/v1/...", "reason": "..." }
  ],
  "files_to_touch": ["array of file paths"],
  "dev_steps": [
    {
      "step": 1,
      "phase": "sot_review | schema | service | router | test | doc",
      "action": "描述操作（中文）",
      "file": "目标文件路径或 null",
      "sot_ref": "SoT 文档引用"
    }
  ],
  "review_checklist": [
    {
      "id": "C1",
      "name": "检查项名称",
      "description": "检查项说明",
      "ref_docs": ["SoT 文档引用"],
      "applicable": true | false,
      "na_reason": "如 applicable=false，说明不适用原因"
    }
  ],
  "need_openspec": true | false,
  "openspec_reason": "如需 OpenSpec，说明原因",
  "sot_references": [
    { "doc": "SoT 文档名", "version": "版本号", "section": "章节" }
  ],
  "risks_and_todos": [
    {
      "level": "P0 | P1 | P2",
      "description": "风险或待办说明",
      "ref_docs": ["相关文档"]
    }
  ]
}
```

---

## 第二部分：Markdown 摘要（人类可读）

> **注意**：此部分仅供人工审阅参考，自动化流程不得依赖其中信息。

简要说明：
1. 本次改动影响的端点
2. 推荐的开发步骤概览
3. 审查 checklist 的关键项
4. 风险与待确认项

**重要**：不要在输出中包含任何代码实现，只输出计划结构。
</output_format>
```

---

## 10. 安全与限制

本 Skill 不得：

- 生成或修改任何代码文件
- 绕过 SoT 裁判链发明新规则
- 在 dev_steps 中包含具体代码实现
- 遗漏不可变量检查项（INV-001/002/003）

如遇到以下情况，应在 `risks_and_todos` 中标注：

- SoT 文档版本不一致
- 需求涉及未定义的权限
- 需求涉及未定义的错误码
- 需求涉及未定义的状态转换

---

## 11. 与其他 Skill 的关系

| Skill | 关系 |
|-------|------|
| `ai-ad-api-dev-orchestrator` | 调用本 Skill 获取开发计划 |
| `api-dev-impl` | 消费本 Skill 的 files_to_touch 和 dev_steps |
| `api-dev-reviewer` | 消费本 Skill 的 review_checklist |

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| v1.0.1 | 2025-12-06 | 补丁级优化：(1) SoT 依赖表补充 BUSINESS_RULES.md 并标注路径；(2) change_type 强制/实验规则集中到 Section 5.3；(3) MCP 工具描述抽象化；(4) 输出格式明确 JSON 给机器、Markdown 给人；(5) review_checklist 支持 N/A 标记；(6) dev_steps action 统一为中文表述 |
| v1.0 | 2025-12-06 | 初始版本，基于 API_DEVELOPMENT_FLOW v2.3 和 AI_CODE_DEV_ORCHESTRATION_SOT v1.0 设计 |
