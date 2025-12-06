---
name: ai-ad-fe-dev-planner
version: v1.0.1
description: >
  前端开发规划 Skill，负责将前端需求描述转换为结构化开发计划。
  只读 SoT 文档和代码结构，输出 files_to_touch、dev_steps、review_checklist 等字段，
  供 ai-ad-fe-dev-orchestrator 和 fe-dev-impl 使用。
  本 Skill 不直接生成或修改项目代码文件。
last_reviewed: 2025-12-06
baseline:
  # === SoT 层 (docs/2.sot/) ===
  - STATE_MACHINE.md v2.6                     # 状态机定义（前端必须映射）
  - DATA_SCHEMA.md v5.2                       # 数据模型（前端类型定义必须对齐）
  - BUSINESS_RULES.md v3.1                    # 业务规则（前端交互必须遵守）
  - API_SOT.md v9.0                           # API 契约（前端请求/响应格式必须对齐）
  - ERROR_CODES_SOT.md v2.1                   # 错误码（前端错误处理必须对齐）
  - AUTH_SPEC.md v2.0                         # 权限模型（前端路由/按钮权限必须对齐）
  # === Dev-Guides 层 (docs/3.dev-guides/) ===
  - FRONTEND_STYLE_GUIDE_v2.0.md              # UI Token、布局、组件规范（最高优先级）
  - FRONTEND_DEVELOPMENT_RULES.md v1.0         # 技术栈、组件架构参考
  - FRONTEND_DEVELOPMENT_FLOW.md v1.1.1        # 前端开发 6 步流程
  - API_DEVELOPMENT_FLOW.md v2.3              # 后端开发流程（前端需等待/对齐，仅流程结构参考）
  - AI_DEV_FACTORY_OVERVIEW.md v1.1.1         # AI 代码工厂总览（仅全局语义参考）
---

# Frontend Dev Planner Skill

## 1. Skill 概要

本 Skill 的唯一职责：

> 将前端开发需求转换成 **结构化开发计划**，包含：
> - 需要修改的文件列表 (`files_to_touch`)
> - 开发步骤 (`dev_steps`)，按 FRONTEND_DEVELOPMENT_FLOW v1.1.1 的 6 步流程组织
> - 审查检查项 (`review_checklist`)
> - 风险与待办事项 (`risks_and_todos`)
> - SoT 文档引用 (`sot_references`)

**本 Skill 严格只读，不写任何代码文件。**

---

## 2. 适用场景

当满足以下任一条件时，应优先考虑使用本 Skill：

- 用户需要为前端开发任务生成计划
- Orchestrator 需要在实现前获取任务蓝图
- 需要识别相关的 SoT 文档引用（FRONTEND_STYLE_GUIDE_v2.0.md 等）
- 需要判断任务是否需要等待后端 API 开发完成

---

## 3. 禁用场景

出现以下情况时，不要使用本 Skill：

- 用户只是想直接写代码，不需要规划
- 任务与前端开发无关（后端 API、纯文档、配置等）
- 用户已经有完整的开发计划，只需要执行

---

## 4. SoT 文档依赖

本 Skill 的所有决策必须遵守以下 SoT 文档（只读）：

| 文档 | 路径 | 版本 | 用途 |
|------|------|------|------|
| FRONTEND_STYLE_GUIDE | `docs/3.dev-guides/` | v2.0 | UI Token、布局、组件规范（最高优先级） |
| FRONTEND_DEVELOPMENT_RULES | `docs/3.dev-guides/` | v1.0 | 技术栈、组件架构参考 |
| FRONTEND_DEVELOPMENT_FLOW | `docs/3.dev-guides/` | v1.1.1 | 前端开发 6 步流程、不可变量检查 |
| API_DEVELOPMENT_FLOW | `docs/3.dev-guides/` | v2.3 | 后端开发流程（前端需等待/对齐，仅流程结构参考） |
| STATE_MACHINE | `docs/2.sot/` | v2.6 | 状态机定义（前端必须映射） |
| DATA_SCHEMA | `docs/2.sot/` | v5.2 | 数据模型字段定义（前端类型定义必须对齐） |
| API_SOT | `docs/2.sot/` | v9.0 | API 契约（前端请求/响应格式必须对齐） |
| ERROR_CODES_SOT | `docs/2.sot/` | v2.1 | 错误码定义（前端错误处理必须对齐） |
| AUTH_SPEC | `docs/2.sot/` | v2.0 | 权限模型（前端路由/按钮权限必须对齐） |

> **注意**：`FRONTEND_STYLE_GUIDE` 位于 `docs/3.dev-guides/` 开发指南层，但作为前端开发的最高优先级 SoT。
> Planner 应优先读取 FRONTEND_STYLE_GUIDE_v2.0.md，其他 SoT 文档作为业务规则参考。

**SoT 裁判链优先级**：
```
FRONTEND_STYLE_GUIDE.md v2.0（最高优先级，前端开发必须遵守）
→ FRONTEND_DEVELOPMENT_RULES.md v1.0
→ FRONTEND_DEVELOPMENT_FLOW.md v1.1.1
→ STATE_MACHINE.md v2.6 → DATA_SCHEMA.md v5.2 → BUSINESS_RULES.md v3.1
→ API_SOT.md v9.0 → ERROR_CODES_SOT.md v2.1 → AUTH_SPEC.md v2.0
```

---

## 5. 输入契约

### 5.1 输入 JSON 结构

```json
{
  "change_type": "fe_module",
  "mode": "impl+test",
  "module": "dashboard_overview",
  "route": "/dashboard",
  "description": "为 dashboard 模块新增概览页面，展示 KPI、趋势图表和风险预警",
  "endpoint_bindings": [
    "GET /api/v1/dashboard/summary",
    "GET /api/v1/dashboard/trends"
  ],
  "constraints": {
    "requires_backend_api": true,
    "auth_required": true,
    "permission": "dashboard:read",
    "layout_type": "dashboard_12grid",
    "ui_style_constraints": ["必须使用 UI Token", "必须处理 Loading/Error/Empty 状态"]
  }
}
```

### 5.2 字段说明

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `change_type` | enum | ✅ | - | 变更类型（见 §5.3） |
| `mode` | enum | ❌ | `impl+test` | 执行模式（见 §5.4） |
| `module` | string | ✅ | - | 目标前端模块名（见 §5.5） |
| `route` | string | ❌ | - | 目标路由路径（如 `/dashboard`） |
| `description` | string | ✅ | - | 自然语言需求描述 |
| `endpoint_bindings` | array | ❌ | `[]` | 关联的后端 API 端点列表 |
| `constraints` | object | ❌ | `{}` | UI/性能/风格约束 |

### 5.3 change_type 枚举（变更类型）

> **权威定义**：以下枚举为 v1.0.0 唯一有效值，禁止使用未列出的值。

| change_type | 约束级别 | 说明 | 典型场景 |
|-------------|----------|------|---------|
| `fe_page` | ✅ 强制 | 新增/修改单个页面 | 新增 `/dashboard/finance` 页面 |
| `fe_module` | ✅ 强制 | 新增/修改完整前端模块（Page + Shell + Components + Hooks） | 新增 `finance_profit_panel` 模块 |
| `fe_refactor` | ✅ 强制 | 纯重构（不改业务行为） | 重构组件结构、优化性能 |

### 5.4 mode 枚举（执行模式）

> **重要说明**：`mode` 描述的是**整条前端开发流水线**的工作模式（plan / impl / impl+test / refactor），
> 本 Skill 只负责根据不同的 `mode` 生成不同颗粒度和范围的**开发计划**，
> 自身永远只输出"规划 JSON"，不执行代码实现、不执行测试、不产出任何代码文件或测试结果。
> 所有实际代码生成和测试执行由下游 Skill（fe-dev-impl）完成。

| mode | 说明 | 对 planner 的规划影响 | 推荐场景 |
|------|------|---------------------|---------|
| `plan` | 只生成计划（不动代码） | 规划重点：只生成规划，不考虑具体实现和测试细节<br>- `dev_steps` 可只覆盖到 FE-STEP-04（组件设计）之前<br>- `review_checklist` 以"确保 SoT 对齐/信息完整"为主<br>- `files_to_touch` 列出预期文件，但不涉及实现细节 | 方案确认 |
| `impl` | 代码实现（可选 auto_write） | 规划重点：需要规划完整的实现路径（FE-STEP-01~05）<br>- `dev_steps` 必须包含 FE-STEP-01~05，明确每个步骤需要做什么<br>- 测试步骤（FE-STEP-06）可标为"建议/可选"，实际执行由下游 impl Skill 决定<br>- `files_to_touch` 列出所有需要创建/修改的文件 | 快速实现 |
| `impl+test` | 代码 + 测试（**推荐默认**） | 规划重点：必须包含完整的 6 步流程，包括测试<br>- `dev_steps` 必须包含 FE-STEP-01~06，明确需要新增哪些前端测试文件/用例<br>- planner 只列出"该做什么"（如"编写 DashboardShell.test.tsx"），不直接生成测试代码<br>- `files_to_touch` 包含测试文件路径 | 标准开发流程 |
| `refactor` | 纯重构（不改业务行为） | 规划重点：行为不变 + 回归测试<br>- `dev_steps` 强调"行为不变 / 结构优化"的检查项<br>- 在 `risks_and_todos` 中强调回归验证和对视觉/交互不变性的说明<br>- `files_to_touch` 仅列出需要重构的文件（不新增文件） | 代码优化 |

**注意**：本 Skill 永远只输出规划 JSON，任何代码实现/测试执行都由其它 Skill（fe-dev-impl）或人工完成。

### 5.5 module 枚举（目标前端模块）

> **来源**：FRONTEND_DEVELOPMENT_FLOW v1.1.1 §6.1 + 现有前端模块结构

| module | 路由路径 | Shell 组件 | 说明 |
|--------|---------|-----------|------|
| `dashboard` | `/dashboard` | `DashboardShell.tsx` | 仪表盘模块（金样本） |
| `dashboard_overview` | `/dashboard` | `DashboardShell.tsx` | 仪表盘概览（dashboard 子模块） |
| `daily_reports` | `/dashboard/daily-reports` | `DailyReportsPageShell.tsx` | 日报管理 |
| `topup_requests` | `/dashboard/topup` | `TopupPageShell.tsx` | 充值申请 |
| `reconciliation` | `/dashboard/reconciliation` | `ReconciliationPageShell.tsx` | 对账管理 |
| `finance_profit_panel` | `/dashboard/finance/profit` | `FinanceProfitPanelShell.tsx` | 利润分析面板 |
| `ad_accounts` | `/dashboard/ad-accounts` | `AdAccountsPageShell.tsx` | 广告账户 |
| `projects` | `/dashboard/projects` | `ProjectsPageShell.tsx` | 项目管理 |
| `transfers` | `/dashboard/transfer` | `TransfersPageShell.tsx` | 余额迁移 |

**约束**：module 可以是上表中的值，也可以是符合命名规范的新模块名（kebab-case，如 `finance_profit_panel`）。

---

## 6. 输出契约

### 6.1 输出结构说明

Planner 的输出分为两部分：

1. **JSON 结构**（机器可读）：是 orchestrator / impl / reviewer 等下游 Skill **唯一应解析的结构化数据**
2. **Markdown 摘要**（人类可读）：仅供人工审阅参考，**自动化流程不得依赖其中信息作决策**

### 6.2 输出 JSON 结构

```json
{
  "module": "dashboard_overview",
  "change_type": "fe_module",
  "mode": "impl+test",
  "route": "/dashboard",
  "files_to_touch": [
    "frontend/app/dashboard/page.tsx",
    "frontend/src/modules/dashboard/DashboardShell.tsx",
    "frontend/src/modules/dashboard/components/DashboardKpiRow.tsx",
    "frontend/src/modules/dashboard/hooks/useDashboardData.ts",
    "frontend/src/modules/dashboard/types/index.ts",
    "frontend/src/modules/dashboard/__tests__/DashboardShell.test.tsx"
  ],
  "dev_steps": [
    {
      "id": "FE-STEP-01",
      "phase": "sot_review",
      "description": "查阅相关 SoT 文档，理解业务规则、状态机、API 契约",
      "file": null,
      "sot_refs": [
        "FRONTEND_STYLE_GUIDE_v2.0.md §3.3 Dashboard 12 栅格布局",
        "API_SOT.md v9.0 §9 Daily Reports API",
        "STATE_MACHINE.md v2.6 §8.2 Daily Report 状态机"
      ],
      "outputs": ["SoT 对齐清单", "状态机映射表", "API 端点定义"]
    },
    {
      "id": "FE-STEP-02",
      "phase": "route_design",
      "description": "设计路由结构（App Router）和页面布局（Shell 模式）",
      "file": "frontend/app/dashboard/page.tsx",
      "sot_refs": [
        "FRONTEND_DEVELOPMENT_FLOW.md v1.1.1 §3.3 Step 2: 路由与布局设计",
        "FRONTEND_STYLE_GUIDE_v2.0.md §4.1 目录结构规范"
      ],
      "outputs": ["路由文件", "Shell 组件框架"]
    },
    {
      "id": "FE-STEP-03",
      "phase": "data_binding",
      "description": "实现数据层（API 调用、Envelope 解包），等待/对齐后端 API",
      "file": "frontend/src/modules/dashboard/hooks/useDashboardData.ts",
      "sot_refs": [
        "FRONTEND_DEVELOPMENT_FLOW.md v1.1.1 §3.4 Step 3: 数据层与 API 适配",
        "API_SOT.md v9.0 §4 Envelope 响应格式",
        "ERROR_CODES_SOT.md v2.1 错误码定义"
      ],
      "outputs": ["数据 Hook", "API 服务封装"],
      "blocking_dependency": "需要等待后端 API 开发完成（参考 API_DEVELOPMENT_FLOW.md v2.3 Step 4）"
    },
    {
      "id": "FE-STEP-04",
      "phase": "component_dev",
      "description": "开发组件（Page Shell、业务组件），管理 UI 状态（React Hooks）",
      "file": "frontend/src/modules/dashboard/DashboardShell.tsx",
      "sot_refs": [
        "FRONTEND_DEVELOPMENT_FLOW.md v1.1.1 §3.5 Step 4: 组件开发与 UI 状态管理",
        "FRONTEND_STYLE_GUIDE_v2.0.md §3.2 PageShell 组件规范",
        "FRONTEND_STYLE_GUIDE_v2.0.md §5 UI Token（颜色、间距、排版）"
      ],
      "outputs": ["Page Shell 组件", "业务组件", "UI 状态管理"]
    },
    {
      "id": "FE-STEP-05",
      "phase": "interaction",
      "description": "实现交互逻辑（表单提交、状态转换触发），处理错误（Envelope 错误响应）",
      "file": null,
      "sot_refs": [
        "FRONTEND_DEVELOPMENT_FLOW.md v1.1.1 §3.6 Step 5: 交互与错误处理",
        "ERROR_CODES_SOT.md v2.1 错误码定义",
        "STATE_MACHINE.md v2.6 状态转换规则"
      ],
      "outputs": ["交互逻辑", "错误处理", "状态转换触发"]
    },
    {
      "id": "FE-STEP-06",
      "phase": "testing",
      "description": "编写测试（单测、集成测），更新文档，纳入回归基线",
      "file": "frontend/src/modules/dashboard/__tests__/DashboardShell.test.tsx",
      "sot_refs": [
        "FRONTEND_DEVELOPMENT_FLOW.md v1.1.1 §3.7 Step 6: 测试与回归",
        "FRONTEND_DEVELOPMENT_RULES.md v1.0 §8 测试要求"
      ],
      "outputs": ["单元测试", "集成测试", "回归测试记录"]
    }
  ],
  "review_checklist": [
    {
      "id": "C1",
      "category": "布局规范",
      "item": "符合 FRONTEND_STYLE_GUIDE_v2.0.md 布局规范",
      "description": "Dashboard 页面必须使用 12 栅格布局（STYLE_GUIDE §3.3）",
      "severity": "P0",
      "sot_ref": "FRONTEND_STYLE_GUIDE_v2.0.md §3.3",
      "applicable": true
    },
    {
      "id": "C2",
      "category": "UI Token",
      "item": "使用 UI Token（颜色、间距、排版）",
      "description": "所有颜色必须使用语义化 Token，禁止硬编码（STYLE_GUIDE §5.1）",
      "severity": "P0",
      "sot_ref": "FRONTEND_STYLE_GUIDE_v2.0.md §5.1",
      "applicable": true
    },
    {
      "id": "C3",
      "category": "状态处理",
      "item": "处理 Loading/Error/Empty 三种状态",
      "description": "推荐使用统一的数据状态管理组件（如 DataStateManager），或在 PageShell 中统一封装（STYLE_GUIDE §3.2）",
      "severity": "P1",
      "sot_ref": "FRONTEND_STYLE_GUIDE_v2.0.md §3.2",
      "applicable": true
    },
    {
      "id": "C4",
      "category": "API 调用",
      "item": "API 调用使用 apiFetch.ts（Envelope 解包）",
      "description": "必须使用 apiFetch.ts 进行所有 API 调用（自动处理 Envelope 解包）",
      "severity": "P0",
      "sot_ref": "FRONTEND_DEVELOPMENT_FLOW.md v1.1.1 §3.4",
      "applicable": true
    },
    {
      "id": "C5",
      "category": "错误处理",
      "item": "错误处理使用 ERROR_CODES_SOT.md v2.1 错误码",
      "description": "所有错误处理必须使用 ERROR_CODES_SOT.md v2.1 定义的错误码",
      "severity": "P0",
      "sot_ref": "ERROR_CODES_SOT.md v2.1",
      "applicable": true
    },
    {
      "id": "C6",
      "category": "状态机映射",
      "item": "状态机映射对齐 STATE_MACHINE.md v2.6",
      "description": "UI 状态展示必须映射到 STATE_MACHINE.md v2.6 定义的状态",
      "severity": "P1",
      "sot_ref": "STATE_MACHINE.md v2.6",
      "applicable": false,
      "na_reason": "dashboard 模块不涉及状态机"
    },
    {
      "id": "C7",
      "category": "权限控制",
      "item": "权限控制对齐 AUTH_SPEC.md v2.0",
      "description": "前端路由/按钮权限必须对齐 AUTH_SPEC.md v2.0 定义的权限字符串",
      "severity": "P1",
      "sot_ref": "AUTH_SPEC.md v2.0",
      "applicable": true
    },
    {
      "id": "C8",
      "category": "目录结构",
      "item": "目录结构符合 FRONTEND_STYLE_GUIDE_v2.0.md §4.1",
      "description": "模块目录结构必须符合 STYLE_GUIDE 定义的规范",
      "severity": "P1",
      "sot_ref": "FRONTEND_STYLE_GUIDE_v2.0.md §4.1",
      "applicable": true
    }
  ],
  "risks_and_todos": [
    {
      "level": "P1",
      "type": "blocking",
      "description": "需要等待后端 API 完成",
      "details": "GET /api/v1/dashboard/summary 和 GET /api/v1/dashboard/trends 端点需要先由后端 API 开发流水线完成（参考 API_DEVELOPMENT_FLOW.md v2.3）",
      "ref_docs": ["API_DEVELOPMENT_FLOW.md v2.3 §4 与 API 开发 Flow 的协同"],
      "suggested_action": "确认后端 API 端点已实现，或使用 Mock 数据临时开发"
    },
    {
      "level": "P2",
      "type": "warning",
      "description": "需确认 dashboard:read 权限是否已在 AUTH_SPEC.md 中定义",
      "details": "如果权限未定义，需要先更新 AUTH_SPEC.md（需 OpenSpec Proposal）",
      "ref_docs": ["AUTH_SPEC.md v2.0"],
      "suggested_action": "检查 AUTH_SPEC.md 中是否存在 dashboard:read 权限定义"
    }
  ],
  "sot_references": [
    {
      "doc": "FRONTEND_STYLE_GUIDE.md",
      "version": "v2.0",
      "sections": [
        "§3.3 Dashboard 12 栅格布局",
        "§4.1 目录结构规范",
        "§5.1 UI Token（颜色、间距、排版）"
      ],
      "relevance": "必须遵守"
    },
    {
      "doc": "FRONTEND_DEVELOPMENT_FLOW.md",
      "version": "v1.1.1",
      "sections": [
        "§3 前端开发 6 步流程",
        "§3.4 Step 3: 数据层与 API 适配",
        "§4 与 API 开发 Flow 的协同"
      ],
      "relevance": "流程规范"
    },
    {
      "doc": "API_SOT.md",
      "version": "v9.0",
      "sections": [
        "§4 Envelope 响应格式",
        "§9 Daily Reports API（如涉及）"
      ],
      "relevance": "API 契约对齐"
    },
    {
      "doc": "ERROR_CODES_SOT.md",
      "version": "v2.1",
      "sections": ["错误码定义"],
      "relevance": "错误处理对齐"
    }
  ],
  "need_openspec": false,
  "openspec_reason": ""
}
```

### 6.3 输出字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `module` | string | 回传输入的模块名 |
| `change_type` | string | 回传输入的变更类型 |
| `mode` | string | 回传输入的开发模式 |
| `route` | string | 回传输入的路由路径 |
| `files_to_touch` | array | 需要创建或修改的文件列表（相对路径，从项目根目录） |
| `dev_steps` | array | 开发步骤，按 FRONTEND_DEVELOPMENT_FLOW v1.1.1 的 6 步流程排列（FE-STEP-01 ~ FE-STEP-06） |
| `review_checklist` | array | 审查检查项（含 applicable 标记、severity、sot_ref） |
| `risks_and_todos` | array | 风险点和待办事项（含 level, type, description, ref_docs, suggested_action） |
| `sot_references` | array | 相关 SoT 文档引用（含 doc, version, sections, relevance） |
| `need_openspec` | bool | 是否需要创建 OpenSpec Proposal（前端 UI/UX 大变动） |
| `openspec_reason` | string | 如需 OpenSpec，说明原因 |

### 6.4 dev_steps 结构说明

每个 `dev_steps` 项包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 步骤 ID，格式：`FE-STEP-01` ~ `FE-STEP-06` |
| `phase` | enum | 阶段标识：`sot_review` \| `route_design` \| `data_binding` \| `component_dev` \| `interaction` \| `testing` |
| `description` | string | 步骤说明（来自 FRONTEND_DEVELOPMENT_FLOW v1.1.1） |
| `file` | string \| null | 主要涉及的文件路径（如适用） |
| `sot_refs` | array | 相关 SoT 文档引用列表（格式：`文档名 版本 章节`） |
| `outputs` | array | 本步骤的预期输出 |
| `blocking_dependency` | string \| null | 阻塞依赖（如"需要等待后端 API 开发完成"） |

### 6.5 review_checklist 的 N/A 标记规则

根据 `change_type` 和 `constraints`，Planner 可以对某些检查项标记为不适用：

- 设置 `applicable: false` 表示该检查项不适用于本次改动
- 必须同时提供 `na_reason` 说明不适用的原因
- 下游 reviewer 可以跳过 `applicable: false` 的检查项
- 常见 N/A 场景：
  - 不涉及状态机的页面 → C6（状态机映射）标记为 N/A
  - 不涉及权限的页面 → C7（权限控制）标记为 N/A
  - `change_type=fe_refactor` → 强调"行为不变"的检查项

### 6.6 change_type=fe_refactor 的特殊处理

当 `change_type=fe_refactor` 时，Planner 需要：

- 在 `dev_steps` 中强调"行为不变 / 结构优化"的检查项
- 在 `review_checklist` 中增加"重构合规性"检查：
  - 是否保持原有业务行为
  - 是否保持原有 API 调用接口
  - 是否保持原有 UI 交互逻辑
- 在 `risks_and_todos` 中标注"需要回归测试验证行为不变"

---

## 7. 流程逻辑

### 7.1 严格按照 FRONTEND_DEVELOPMENT_FLOW 的 6 步组织 dev_steps

Planner 必须按照 FRONTEND_DEVELOPMENT_FLOW v1.1.1 §3 的 6 步流程组织 `dev_steps`：

1. **FE-STEP-01 (sot_review)**: 对齐 SoT 与产品需求
   - 查阅相关 SoT 文档
   - 提取关键信息（状态机、数据模型、API 契约、权限、错误码）
   - 检查是否存在冲突

2. **FE-STEP-02 (route_design)**: 路由与布局设计
   - 设计路由结构（App Router）
   - 设计 Shell 组件结构
   - 确认目录结构符合 STYLE_GUIDE §4.1

3. **FE-STEP-03 (data_binding)**: 数据层与 API 适配
   - 实现 API 调用层（使用 `apiFetch.ts`）
   - 实现模块级 API 服务（可选）
   - 实现数据 Hooks（React Query / SWR 模式）
   - **关键**：如果绑定了 `endpoint_bindings`，必须标注"需要等待后端 API 开发完成"

4. **FE-STEP-04 (component_dev)**: 组件开发与 UI 状态管理
   - 开发 Page Shell 组件
   - 开发业务组件
   - 管理 UI 状态（React Hooks）
   - **关键**：必须遵守 FRONTEND_STYLE_GUIDE_v2.0.md 的所有规则

5. **FE-STEP-05 (interaction)**: 交互与错误处理
   - 实现表单提交逻辑
   - 实现状态转换触发
   - 处理错误（Envelope 错误响应）
   - **关键**：所有错误处理必须使用 ERROR_CODES_SOT.md v2.1 定义的错误码

6. **FE-STEP-06 (testing)**: 测试与回归
   - 编写单元测试
   - 编写集成测试
   - 更新文档
   - 纳入回归基线

### 7.2 endpoint_bindings 的处理

如果输入中包含 `endpoint_bindings`，Planner 需要：

- 在 `dev_steps[FE-STEP-03]` 中标注 `blocking_dependency: "需要等待后端 API 开发完成（参考 API_DEVELOPMENT_FLOW.md v2.3 Step 4）"`
- 在 `risks_and_todos` 中添加 P1 级风险："需要等待后端 API 完成"
- 在 `sot_references` 中引用 `API_SOT.md v9.0` 相关章节
- 在 `review_checklist` 中增加"API 契约对齐"检查项

### 7.3 files_to_touch 的生成规则

根据 `change_type` 和 `module`，Planner 应生成以下文件列表：

**change_type=fe_page**：
- `frontend/app/{route}/page.tsx`（路由入口）
- `frontend/src/modules/{module}/{Module}PageShell.tsx`（Shell 组件，如需要）
- `frontend/src/modules/{module}/components/{Component}.tsx`（业务组件，如需要）
- `frontend/src/modules/{module}/hooks/use{Module}Data.ts`（数据 Hook，如需要）
- `frontend/src/modules/{module}/types/index.ts`（类型定义，如需要）

**change_type=fe_module**：
- 上述所有文件 + 模块级共享组件/服务

**change_type=fe_refactor**：
- 仅列出需要重构的文件（不新增文件）

**目录结构规范**（必须遵守 FRONTEND_STYLE_GUIDE_v2.0.md §4.1）：
- `app/` 目录：Next.js App Router 路由入口
- `src/modules/{module}/` 目录：业务模块（Shell + Components + Hooks + Types）

---

## 8. OpenSpec 决策规则

### 8.1 必须创建 OpenSpec 的场景

根据 `FRONTEND_DEVELOPMENT_FLOW.md v1.1.1 §9.1`，以下场景必须设置 `need_openspec: true`：

| 场景 | 示例 | 相关 SoT |
|------|------|----------|
| **新增前端模块** | 新增"财务分析"模块 | FRONTEND_STYLE_GUIDE_v2.0.md |
| **重大 UI/UX 变更** | 改变 Shell 模式、布局结构 | FRONTEND_STYLE_GUIDE_v2.0.md |
| **新增前端路由** | 新增 `/dashboard/finance` | FRONTEND_DEVELOPMENT_FLOW.md v1.1.1 |
| **修改 STYLE_GUIDE 规则** | 改变 12 栅格布局、修改颜色 Token 系统 | FRONTEND_STYLE_GUIDE_v2.0.md |

### 8.2 可跳过 OpenSpec 的场景

根据 `FRONTEND_DEVELOPMENT_FLOW.md v1.1.1 §9.1`，以下场景可设置 `need_openspec: false`：

| 场景 | 说明 |
|------|------|
| **不影响 SoT 的小改动** | 样式微调、组件内部优化 |
| **Bug 修复** | 恢复到既有 STYLE_GUIDE 定义的行为 |
| **纯重构** | 不改业务行为、不改 UI/UX 的结构优化 |

---

## 9. 禁止事项

本 Skill 禁止以下行为：

- ❌ **禁止直接生成代码文件**：所有代码生成通过调用 `fe-dev-impl` 完成
- ❌ **禁止修改 SoT 文档**：所有 SoT 文档为只读，只能引用
- ❌ **禁止发明新的样式规则**：所有样式规则必须来自 FRONTEND_STYLE_GUIDE_v2.0.md
- ❌ **禁止绕过 FRONTEND_DEVELOPMENT_FLOW 流程**：必须遵循 6 步标准流程
- ❌ **禁止硬编码文件路径**：文件路径必须符合 FRONTEND_STYLE_GUIDE_v2.0.md §4.1 目录结构规范

---

## 10. 版本与维护

### 10.1 Change Log

| Version | Date | Changes |
|---------|------|---------|
| v1.0.1 | 2025-12-06 | 文档语义澄清：修正 mode 描述，明确 mode 是"整条流水线的模式"，planner 只根据 mode 调整规划内容，不产出代码/测试结果；强调本 Skill 仅输出规划，避免与职责边界冲突 |
| v1.0.0 | 2025-12-06 | 初版：基于 FRONTEND_DEVELOPMENT_FLOW v1.1.1，定义前端开发规划 Skill，对标 ai-ad-api-dev-planner v1.0.1 |

### 10.2 相关 Skill

| Skill | 版本 | 关系 |
|-------|------|------|
| `ai-ad-fe-dev-orchestrator` | v1.0.0 | 调用本 Skill 进行规划阶段 |
| `ai-ad-fe-dev-impl` | v1.0.0（规划中） | 使用本 Skill 输出的 plan 进行实现 |
| `ai-ad-fe-dev-reviewer` | v1.0.0（规划中） | 使用本 Skill 输出的 review_checklist 进行审查 |

---

**文档状态**：Ready（Skill 定义完成）

