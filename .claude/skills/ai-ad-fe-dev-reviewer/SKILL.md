---
name: ai-ad-fe-dev-reviewer
version: v1.0.3
description: >
  前端开发合规审查 Skill，负责在代码改动完成后执行 SoT 合规检查。
  基于 FRONTEND_STYLE_GUIDE_v2.0、FRONTEND_DEVELOPMENT_RULES v1.0 和 FRONTEND_DEVELOPMENT_FLOW v1.1.1 进行审查，
  输出 P0/P1/P2 级问题列表，判定是否建议上线。
last_reviewed: 2025-12-06
baseline:
  # === Dev-Guides 层 (docs/3.dev-guides/) ===
  - FRONTEND_STYLE_GUIDE_v2.0.md              # UI Token、布局、组件规范（最高优先级）
  - FRONTEND_DEVELOPMENT_RULES.md             # 技术栈、组件架构参考（版本见文档 frontmatter）
  - FRONTEND_DEVELOPMENT_FLOW_v1.0.md         # 前端开发 6 步流程（版本见文档 frontmatter）
  - AI_DEV_FACTORY_OVERVIEW_v1.0.md          # AI 代码工厂总览（全局语义参考，版本见文档 frontmatter）
  # === SoT 层 (docs/2.sot/) ===
  - STATE_MACHINE.md                          # 状态机定义（前端必须映射，版本见文档 frontmatter）
  - DATA_SCHEMA.md                            # 数据模型（前端类型定义必须对齐，版本见文档 frontmatter）
  - BUSINESS_RULES.md                         # 业务规则（前端交互行为必须遵守，版本见文档 frontmatter）
  - API_SOT.md                                # API 契约（前端请求/响应格式必须对齐，版本见文档 frontmatter）
  - ERROR_CODES_SOT.md                        # 错误码（前端错误处理必须对齐，版本见文档 frontmatter）
  - AUTH_SPEC.md                              # 权限模型（前端路由/按钮权限必须对齐，版本见文档 frontmatter）
  # 注意：版本号以各文档 frontmatter 中的 version 字段为准
---

# Frontend Dev Reviewer Skill

## 1. Skill 概要

本 Skill 的唯一职责：

> 在前端开发实现完成后，对代码改动进行 **SoT 合规审查**，
> 输出 P0/P1/P2 级问题列表，给出是否建议上线的结论。

**本 Skill 只做审查，不修改任何代码文件。**

---

## 2. 适用场景

当满足以下条件时，应调用本 Skill：

- `fe-dev-impl` 或手动实现完成后
- 用户要求对前端改动做合规检查
- CI 流水线中的 review 阶段
- PR 合并前的最终审查

---

## 3. 禁用场景

以下情况不应使用本 Skill：

- 代码尚未实现（应先调用 `fe-dev-impl`）
- 仅需运行测试（应使用测试工具或 CI/CD）
- 仅需生成文档（应使用 `ai-ad-doc-orchestrator`）
- 非前端改动（纯后端 API、配置文件、文档）

---

## 4. SoT 文档依赖

本 Skill 审查时必须参照以下 SoT 文档：

| 文档 | 版本 | 路径 | 审查用途 |
|------|------|------|----------|
| `FRONTEND_STYLE_GUIDE_v2.0.md` | v2.0 | `docs/3.dev-guides/` | UI Token、布局、组件规范（**最高优先级**） |
| `FRONTEND_DEVELOPMENT_RULES.md` | v1.0 | `docs/3.dev-guides/` | 技术栈、组件架构、目录结构 |
| `FRONTEND_DEVELOPMENT_FLOW_v1.0.md` | v1.1.1 | `docs/3.dev-guides/` | 6 步流程检查、不可变量定义 |
| `STATE_MACHINE.md` | v2.6 | `docs/2.sot/` | 状态机定义、UI 状态映射 |
| `DATA_SCHEMA.md` | v5.2 | `docs/2.sot/` | 数据模型字段定义（前端 TS 类型、表格列、表单字段必须对齐） |
| `BUSINESS_RULES.md` | v3.1 | `docs/2.sot/` | 业务规则（前端交互行为、状态可见性、按钮可点击性必须符合） |
| `API_SOT.md` | v9.0 | `docs/2.sot/` | API 契约、请求/响应格式 |
| `ERROR_CODES_SOT.md` | v2.1 | `docs/2.sot/` | 错误码定义、使用规范 |
| `AUTH_SPEC.md` | v2.0 | `docs/2.sot/` | 权限模型、路由/按钮权限 |

**版本号说明**：
- 以上依赖文档的实际版本号，以各文档 frontmatter 的 `version` 字段为准。
- `FRONTEND_DEVELOPMENT_FLOW_v1.0.md` 当前版本为 v1.1.1，文件名中的 `v1.0` 为历史命名，不影响版本引用。
- 其他文档的版本号同样以各自 frontmatter 为准。

**SoT 裁判链优先级**：
```
FRONTEND_STYLE_GUIDE_v2.0.md（最高优先级，前端开发必须遵守）
→ FRONTEND_DEVELOPMENT_RULES.md v1.0
→ FRONTEND_DEVELOPMENT_FLOW_v1.0.md v1.1.1
→ STATE_MACHINE.md v2.6 → DATA_SCHEMA.md v5.2 → BUSINESS_RULES.md v3.1
→ API_SOT.md v9.0 → ERROR_CODES_SOT.md v2.1 → AUTH_SPEC.md v2.0
```

**前端最高裁判说明**：
- 样式与组件行为以 `FRONTEND_STYLE_GUIDE_v2.0.md` 为最高裁判。
- 如与其他文档冲突，以 `FRONTEND_STYLE_GUIDE_v2.0.md` 为准。

---

## 5. 输入结构

### 5.1 完整输入 JSON

```json
{
  "module": "dashboard_overview",
  "change_type": "fe_module",
  "description": "为 dashboard 模块新增概览页面，展示 KPI、趋势图表和风险预警",
  "plan": {
    "files_to_touch": [
      "frontend/app/dashboard/page.tsx",
      "frontend/src/modules/dashboard/DashboardShell.tsx",
      "frontend/src/modules/dashboard/hooks/useDashboardData.ts"
    ],
    "dev_steps": [
      {
        "id": "FE-STEP-01",
        "phase": "sot_review",
        "description": "查阅相关 SoT 文档",
        "sot_refs": ["FRONTEND_STYLE_GUIDE_v2.0.md §3.3"]
      }
    ],
    "review_checklist": [
      {
        "id": "C1",
        "category": "布局规范",
        "item": "符合 FRONTEND_STYLE_GUIDE_v2.0.md 布局规范",
        "severity": "P0",
        "sot_ref": "FRONTEND_STYLE_GUIDE_v2.0.md §3.3",
        "applicable": true
      }
    ]
  },
  "impl_result": {
    "files_changed": [
      {
        "path": "frontend/app/dashboard/page.tsx",
        "action": "created",
        "summary": "创建路由入口，使用 PageContainer 包装 DashboardShell"
      },
      {
        "path": "frontend/src/modules/dashboard/DashboardShell.tsx",
        "action": "created",
        "summary": "创建 Shell 组件，实现 12 栅格布局"
      }
    ],
    "patches": [
      {
        "file": "frontend/app/dashboard/page.tsx",
        "patch": "..."
      }
    ],
    "test_summary": {
      "executed": true,
      "lint_passed": true,
      "unit_passed": true,
      "unit_tests_count": 5,
      "unit_tests_passed": 5,
      "unit_tests_failed": 0
    },
    "style_guide_compliance": {
      "uses_ui_tokens": true,
      "follows_layout_rules": true,
      "handles_loading_state": true,
      "handles_error_state": true,
      "handles_empty_state": true
    },
    "warnings": []
  }
}
```

### 5.2 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `module` | ✅ | 目标模块名称 |
| `change_type` | ✅ | 改动类型（`fe_page`, `fe_module`, `fe_refactor`） |
| `description` | ✅ | 本次改动的目标描述 |
| `plan` | ⬚ | 来自 planner 的开发计划（可选，用于对照检查） |
| `impl_result` | ✅ | 来自 impl 的实现结果（包含 files_changed / patches / test_summary / style_guide_compliance） |

### 5.3 test_summary 与审查状态的强关联（MUST）

**规则 R-TEST-001**：`impl_result.test_summary` 直接影响审查结论。

| test_summary 状态 | 审查行为 | 说明 |
|------------------|----------|------|
| `executed=false` 或缺失 | **MUST** 产生至少 1 个 P1 问题 | 问题：`未执行自动化测试` |
| `lint_passed=false` | **MUST** 产生至少 1 个 P1 问题 | 问题：`Lint 检查未通过` |
| `unit_tests_failed > 0` | **MUST** 产生至少 1 个 P1 问题 | 问题：`单元测试失败` |
| `executed=true` 且 `lint_passed=true` 且 `unit_tests_failed=0` | 允许无测试相关问题 | 测试通过 |

**约束**：
- 若 `test_summary.executed == false`：`status` **MUST NOT** 为 `"pass"`
- 若 `test_summary.lint_passed == false` 或 `test_summary.unit_tests_failed > 0`：`recommend_deploy` **MUST** 为 `false`

### 5.4 change_type 驱动的检查重点

不同 `change_type` 有不同的审查严格程度：

| change_type | SoT 约束级别 | 审查重点 |
|-------------|--------------|----------|
| `fe_page` | ✅ **强制约束** | 必须检查路由、Shell 组件、数据层、UI 状态处理 |
| `fe_module` | ✅ **强制约束** | 必须检查完整模块结构（Page + Shell + Components + Hooks + Types） |
| `fe_refactor` | ⚠️ 实验性 | 重点检查行为等价性、结构优化合理性，其他项 best-effort |

**约束**：
- 对于 `fe_page` 和 `fe_module`，审查结论具有 SoT 违规判定效力
- 对于 `fe_refactor`，审查结论为建议性质，不构成 SoT 违规依据

### 5.5 change_type × 检查维度对照表

不同 `change_type` 对应的必检维度与可选维度：

| change_type | 必检维度（MUST） | 可选维度（SHOULD/Best-effort） | 说明 |
|-------------|-----------------|-------------------------------|------|
| `fe_page` | §8.1 样式与组件<br>§8.2 结构与模块化<br>§8.3 Flow 对齐<br>§8.5 测试与稳定性 | §8.4 可用性与可维护性<br>§8.6 状态机映射（如涉及）<br>§8.7 计划一致性（如 plan 存在） | 新增页面必须符合完整规范 |
| `fe_module` | §8.1 样式与组件<br>§8.2 结构与模块化<br>§8.3 Flow 对齐<br>§8.5 测试与稳定性<br>§8.7 计划一致性（如 plan 存在） | §8.4 可用性与可维护性<br>§8.6 状态机映射（如涉及） | 新增模块必须检查完整结构 |
| `fe_refactor` | §8.3 Flow 对齐<br>§8.5 测试与稳定性 | §8.1 样式与组件<br>§8.2 结构与模块化<br>§8.4 可用性与可维护性<br>§8.6 状态机映射（如涉及）<br>§8.7 计划一致性（如 plan 存在） | 重构重点检查行为等价性和结构优化合理性 |

**审查流程要求**：
- Reviewer 需要先根据 `change_type` 决定本次审查的 MUST 维度，再在这些维度内给出 P0/P1/P2 结论。
- 必检维度内的违规必须判定为 P0 或 P1（根据 §7 问题分级定义）。
- 可选维度内的发现可判定为 P2 优化建议。

---

## 6. 输出结构

### 6.1 输出 JSON 格式

```json
{
  "module": "dashboard_overview",
  "change_type": "fe_module",
  "status": "pass",
  "p0_issues": [],
  "p1_issues": [
    {
      "id": "P1-FE-001",
      "category": "test_not_executed",
      "severity": "P1",
      "sot_ref": "FRONTEND_DEVELOPMENT_FLOW_v1.0.md v1.1.1 §3.7",
      "file": null,
      "line_hint": null,
      "message": "未执行自动化测试（lint/unit），违反 FRONTEND_DEVELOPMENT_FLOW v1.1.1 Step 6 要求",
      "fix_suggestion": "运行 `pnpm lint` 和 `pnpm test:unit` 确保代码质量"
    }
  ],
  "p2_issues": [
    {
      "id": "P2-FE-001",
      "category": "style_suggestion",
      "sot_ref": "FRONTEND_STYLE_GUIDE_v2.0.md §3.2",
      "file": "frontend/src/modules/dashboard/DashboardShell.tsx",
      "line_hint": "约第 45 行",
      "message": "建议使用 DataStateManager 统一处理 Loading/Error/Empty 状态",
      "fix_suggestion": "参考 FRONTEND_STYLE_GUIDE_v2.0.md §3.2，使用 DataStateManager 组件统一封装数据状态"
    }
  ],
  "review_summary": "发现 1 个 P1 问题（未执行测试），建议修复后再上线。代码实现符合 FRONTEND_STYLE_GUIDE_v2.0.md 规范。",
  "recommend_deploy": false,
  "requires_openspec": false,
  "next_actions": [
    "运行 `pnpm lint` 和 `pnpm test:unit` 确保代码质量",
    "考虑使用 DataStateManager 统一处理数据状态（P2 优化）"
  ],
  "reviewer_meta": {
    "skill_name": "ai-ad-fe-dev-reviewer",
    "skill_version": "v1.0.2",
    "reviewed_at": "2025-12-06T10:30:00Z"
  }
}
```

**输出字段说明**：

| 字段 | 必填 | 说明 |
|------|------|------|
| `module` | ✅ | 目标模块名称 |
| `change_type` | ✅ | 改动类型 |
| `status` | ✅ | 审查状态（`"pass"` \| `"warning"` \| `"fail"`） |
| `p0_issues` | ✅ | P0 级问题列表（数组） |
| `p1_issues` | ✅ | P1 级问题列表（数组） |
| `p2_issues` | ✅ | P2 级问题列表（数组） |
| `recommend_deploy` | ✅ | 是否建议上线（`true` / `false`） |
| `requires_openspec` | ✅ | 是否需要 OpenSpec proposal（`true` / `false`） |
| `review_summary` | ✅ | 审查总结（文本） |
| `next_actions` | ⬚ | 后续行动建议（字符串数组） |
| `reviewer_meta` | ⬚（推荐） | 审查元信息（包含 `skill_name`、`skill_version`、`reviewed_at`） |

### 6.2 status / recommend_deploy 与 P0/P1 的强绑定规则（MUST）

以下是 **硬性规则**，任何审查输出 **MUST** 遵守：

| 条件 | status | recommend_deploy |
|------|--------|------------------|
| `p0_issues` 非空 | **MUST** 为 `"fail"` | **MUST** 为 `false` |
| `p0_issues` 空 且 `p1_issues` 非空 | **MUST** 为 `"warning"` | **MUST** 为 `false`（默认） |
| `p0_issues` 空 且 `p1_issues` 空 | 可以为 `"pass"` | 可以为 `true` |

**决策逻辑伪代码**：

```python
def determine_status_and_deploy(p0_issues, p1_issues, test_summary):
    # 规则 1: P0 非空 → fail + 不可上线
    if len(p0_issues) > 0:
        return status="fail", recommend_deploy=False
    
    # 规则 2: P1 非空 → warning + 不可上线（默认）
    if len(p1_issues) > 0:
        return status="warning", recommend_deploy=False
    
    # 规则 3: 测试未执行或失败 → 不可 pass
    if not test_summary or not test_summary.executed:
        return status="warning", recommend_deploy=False
    if test_summary.lint_passed == False or test_summary.unit_tests_failed > 0:
        return status="warning", recommend_deploy=False
    
    # 规则 4: 全部通过
    return status="pass", recommend_deploy=True
```

### 6.3 requires_openspec 与其他字段的组合语义

| requires_openspec | status | recommend_deploy | 语义 |
|-------------------|--------|------------------|------|
| `false` | `pass` | `true` | ✅ 可直接上线 |
| `false` | `warning` | `false` | ⚠️ 有 P1 问题，修复后可上线 |
| `false` | `fail` | `false` | ❌ 有 P0 问题，必须修复 |
| `true` | `pass` | `false` | ⚠️ 代码无问题，但需先走 OpenSpec |
| `true` | `warning`/`fail` | `false` | ❌ 代码有问题 + 需走 OpenSpec |

**约束**：
- 若 `requires_openspec=true` 且未检测到 OpenSpec proposal，`recommend_deploy` **MUST** 为 `false`
- 即使代码本身无 P0/P1 问题，缺少 OpenSpec 也阻止上线

### 6.3.1 requires_openspec 在前端场景下的触发条件

**允许 `requires_openspec=true` 的典型前端场景**：

| 场景 | 说明 | 示例 |
|------|------|------|
| **导航信息架构变更** | 侧边栏结构、大菜单重构、路由层级变化 | 新增一级导航菜单、改变 Dashboard 布局结构 |
| **复杂业务流程 UI** | 新增多步表单、Wizard 型流程并改变业务路径 | 新增"充值申请"多步骤表单、新增"对账审批"流程 |
| **重大 UI/UX 变更** | 改变 Shell 模式、布局系统、颜色 Token 系统 | 从 12 栅格改为 16 栅格、修改全局颜色 Token 定义 |
| **需要更新产品需求文档** | 改动影响产品交互原型、用户流程 | 新增"风险控制"模块并改变用户操作路径 |

**明确禁止的场景**（应设置 `requires_openspec=false`）：

| 场景 | 说明 |
|------|------|
| **纯样式调整** | 颜色、间距、对齐、字体大小微调 |
| **小范围组件重构** | 组件内部结构优化，但行为不变、UI 不变 |
| **仅补充测试** | 为现有功能增加测试覆盖，无业务逻辑变更 |
| **修复前端 bug** | 恢复到既有 STYLE_GUIDE 定义的行为 |
| **组件内部优化** | 性能优化、代码清理，不影响外部接口和 UI |

### 6.4 issue 结构规范

每个 issue **SHOULD** 包含以下字段：

| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | ✅ | 问题编号（如 P0-FE-001, P1-FE-002） |
| `category` | ✅ | 问题分类（见 §7） |
| `severity` | ⬚（推荐） | 严重度（`"P0"` \| `"P1"` \| `"P2"`），如不提供，可由数组所属（p0_issues/p1_issues/p2_issues）推断 |
| `sot_ref` | ⬚ | SoT 文档引用（如 `FRONTEND_STYLE_GUIDE_v2.0.md §3.3`） |
| `file` | ⬚ | 问题所在文件路径（相对路径） |
| `line_hint` | ⬚ | 问题所在行号或行号范围（如 "约第 45 行"） |
| `message` | ✅ | 问题描述 |
| `fix_suggestion` | ✅ (P0/P1) | 修复建议（P0/P1 问题必须提供） |

**示例（带 severity 字段）**：

```json
{
  "id": "P1-FE-001",
  "category": "test_not_executed",
  "severity": "P1",
  "sot_ref": "FRONTEND_DEVELOPMENT_FLOW_v1.0.md v1.1.1 §3.7",
  "file": null,
  "line_hint": null,
  "message": "未执行自动化测试（lint/unit），违反 FRONTEND_DEVELOPMENT_FLOW v1.1.1 Step 6 要求",
  "fix_suggestion": "运行 `pnpm lint` 和 `pnpm test:unit` 确保代码质量"
}
```

---

## 7. 问题分级定义

**说明**：问题分级（P0/P1/P2）与输出 JSON 中的数组字段对应关系：
- **P0 问题** → 输出到 `p0_issues` 数组
- **P1 问题** → 输出到 `p1_issues` 数组
- **P2 问题** → 输出到 `p2_issues` 数组

每个问题对象的 `severity` 字段（可选）应与数组所属一致。

### 7.1 P0 阻塞问题（必须修复）

以下情况 **MUST** 判定为 P0：

| 类别 | 说明 | 示例 | 规则依据 |
|------|------|------|----------|
| `style_guide_violation` | 严重违反 FRONTEND_STYLE_GUIDE_v2.0 | 硬编码颜色值、未使用 UI Token、破坏 12 栅格布局 | FRONTEND_STYLE_GUIDE_v2.0 §3.3, §5.1 |
| `ui_token_missing` | 完全不使用 UI Token | 直接使用 `bg-white`、`text-gray-900` 等硬编码颜色 | FRONTEND_STYLE_GUIDE_v2.0 §5.1 |
| `layout_structure_violation` | 破坏布局结构 | 未使用 PageShell、破坏 App Shell 结构 | FRONTEND_STYLE_GUIDE_v2.0 §3.1, §3.2 |
| `state_handling_missing` | 未处理 Loading/Error/Empty 状态 | 数据获取后直接渲染，未处理加载/错误/空状态 | FRONTEND_STYLE_GUIDE_v2.0 §3.2 |
| `api_call_violation` | 未使用 apiFetch.ts | 直接使用 fetch，未处理 Envelope 解包 | FRONTEND_DEVELOPMENT_FLOW_v1.0.md v1.1.1 §3.4 |
| `error_code_mismatch` | 错误处理未使用 ERROR_CODES_SOT | 硬编码错误信息、未使用错误码 | ERROR_CODES_SOT.md v2.1 |
| `state_machine_violation` | 违反状态机映射 | UI 状态展示与 STATE_MACHINE.md 定义不一致 | STATE_MACHINE.md v2.6 |
| `security_breach` | 安全漏洞 | 未校验权限、暴露敏感信息 | AUTH_SPEC.md v2.0 |

### 7.2 P1 高危问题（强烈建议修复）

以下情况 **SHOULD** 判定为 P1：

| 类别 | 说明 | 示例 | 规则依据 |
|------|------|------|----------|
| `test_not_executed` | 未执行自动化测试 | `test_summary.executed=false` | FRONTEND_DEVELOPMENT_FLOW_v1.0.md v1.1.1 §3.7 |
| `test_failure` | 测试失败 | `lint_passed=false` 或 `unit_tests_failed > 0` | FRONTEND_DEVELOPMENT_FLOW_v1.0.md v1.1.1 §3.7 |
| `directory_structure_violation` | 目录结构不符合规范 | 文件位置不符合 FRONTEND_STYLE_GUIDE_v2.0 §4.1 | FRONTEND_STYLE_GUIDE_v2.0.md §4.1 |
| `component_naming_violation` | 组件命名不符合规范 | 未使用 PascalCase、hooks 未使用 `use` 前缀 | FRONTEND_DEVELOPMENT_RULES.md v1.0 §3.3 |
| `import_path_violation` | 未使用路径别名 | 使用相对路径 `../` 而非 `@/` 别名 | FRONTEND_STYLE_GUIDE_v2.0.md §4.1 |
| `client_boundary_violation` | Client 边界使用不当 | 在 `page.tsx` 顶层添加 `'use client'` | FRONTEND_STYLE_GUIDE_v2.0.md §2.2 |
| `sot_drift` | 与 SoT 定义不一致 | 类型定义与 DATA_SCHEMA.md 不一致、API 调用与 API_SOT.md 不一致 | DATA_SCHEMA.md v5.2, API_SOT.md v9.0 |
| `permission_bypass` | 权限检查不完整 | 前端路由/按钮未校验权限 | AUTH_SPEC.md v2.0 |
| `plan_file_mismatch` | 计划与实际改动不一致 | 见 §8.7 | FRONTEND_DEVELOPMENT_FLOW_v1.0.md v1.1.1 |

### 7.3 P2 优化建议（可选修复）

| 类别 | 说明 | 示例 |
|------|------|------|
| `style_suggestion` | 代码风格建议 | 建议使用 DataStateManager 统一处理状态、建议拆分大组件 |
| `doc_missing` | 文档缺失 | TypeScript 类型缺少注释、组件缺少 JSDoc |
| `test_coverage` | 测试覆盖建议 | 边界用例未覆盖、集成测试缺失 |
| `performance_hint` | 性能优化提示 | 大列表未使用虚拟滚动、重复渲染未优化 |
| `accessibility_hint` | 可访问性提示 | 缺少 aria-label、键盘导航支持不完整 |

---

## 8. 审查维度与检查项

### 8.1 样式与组件（FRONTEND_STYLE_GUIDE_v2.0）

**检查项**：

1. **UI Token 使用**（P0）：
   - 所有颜色必须使用语义化 Token（如 `bg-card-bg`, `text-text-strong`）
   - 禁止硬编码颜色值（如 `bg-white`, `text-gray-900`）
   - 参考：FRONTEND_STYLE_GUIDE_v2.0.md §5.1

2. **布局规范**（P0）：
   - Dashboard 页面必须使用 12 栅格布局
   - 必须使用 PageShell 组件作为页面容器
   - 参考：FRONTEND_STYLE_GUIDE_v2.0.md §3.3

3. **状态处理**（P0）：
   - 必须处理 Loading/Error/Empty 三种状态
   - 推荐使用 DataStateManager 统一封装
   - 参考：FRONTEND_STYLE_GUIDE_v2.0.md §3.2

4. **组件命名**（P1）：
   - 组件使用 PascalCase（如 `DashboardShell.tsx`）
   - Hooks 使用 camelCase with `use` prefix（如 `useDashboardData.ts`）
   - 参考：FRONTEND_DEVELOPMENT_RULES.md v1.0 §3.3

### 8.2 结构与模块化（FRONTEND_DEVELOPMENT_RULES v1.0）

**检查项**：

1. **目录结构**（P1）：
   - 路由文件：`app/{route}/page.tsx`
   - Shell 组件：`src/modules/{module}/{Module}PageShell.tsx`
   - 业务组件：`src/modules/{module}/components/`
   - 数据 Hooks：`src/modules/{module}/hooks/`
   - 类型定义：`src/modules/{module}/types/`
   - 参考：FRONTEND_STYLE_GUIDE_v2.0.md §4.1

2. **路径别名**（P1）：
   - 必须使用 `@/` 别名，禁止使用相对路径 `../`
   - 参考：FRONTEND_STYLE_GUIDE_v2.0.md §4.1

3. **Client 边界**（P1）：
   - `'use client'` 只在需要交互的最小组件范围使用
   - 禁止在 `layout.tsx` 或 `page.tsx` 顶层添加 `'use client'`
   - 参考：FRONTEND_STYLE_GUIDE_v2.0.md §2.2

### 8.3 Flow 对齐（FRONTEND_DEVELOPMENT_FLOW v1.1.1）

**检查项**：

1. **6 步流程完整性**（P1）：
   - Step 1: 对齐 SoT 与产品需求
   - Step 2: 路由与布局设计
   - Step 3: 数据层与 API 适配
   - Step 4: 组件开发与 UI 状态管理
   - Step 5: 交互与错误处理
   - Step 6: 测试与回归
   - 参考：FRONTEND_DEVELOPMENT_FLOW_v1.0.md v1.1.1 §3

2. **API 调用规范**（P0）：
   - 必须使用 `apiFetch.ts` 进行所有 API 调用
   - 必须处理 Envelope 解包和错误响应
   - 参考：FRONTEND_DEVELOPMENT_FLOW_v1.0.md v1.1.1 §3.4

3. **错误处理规范**（P0）：
   - 所有错误处理必须使用 ERROR_CODES_SOT.md v2.1 定义的错误码
   - 参考：FRONTEND_DEVELOPMENT_FLOW_v1.0.md v1.1.1 §3.6

### 8.4 可用性与可维护性

**检查项**：

1. **复杂度**（P2）：
   - 组件行数过多（建议 < 300 行）
   - 嵌套层级过深（建议 < 5 层）

2. **可读性**（P2）：
   - 变量命名不清晰
   - 缺少必要的注释

3. **重复代码**（P2）：
   - 发现重复的组件逻辑
   - 建议提取为共享组件或 Hook

### 8.5 测试与稳定性

**检查项**：

1. **测试执行**（P1）：
   - 具体测试判定规则见 §5.3（R-TEST 系列规则）
   - 参考：FRONTEND_DEVELOPMENT_FLOW_v1.0.md v1.1.1 §3.7

2. **测试覆盖**（P2）：
   - 建议覆盖主要业务逻辑
   - 建议覆盖边界用例

### 8.6 状态机映射（STATE_MACHINE.md v2.6）

**检查项**（如涉及状态机）：

1. **状态映射一致性**（P0）：
   - UI 状态展示必须映射到 STATE_MACHINE.md v2.6 定义的状态
   - 状态转换必须通过后端 API 触发
   - 参考：FRONTEND_DEVELOPMENT_FLOW_v1.0.md v1.1.1 §3.6

### 8.7 计划与实际改动一致性

**检查项**：

1. **文件一致性**（P1）：
   - `plan.files_to_touch` 与实际 `impl_result.files_changed` 是否一致
   - 如有新增文件，是否在 `impl_result.warnings` 中说明原因

2. **步骤完整性**（P1）：
   - `plan.dev_steps` 中的步骤是否都已执行
   - 是否有跳过的步骤（如测试、文档）

---

## 9. 审查流程

### Step 1: 解析输入

```python
module = input.get("module")
change_type = input.get("change_type")
description = input.get("description")
plan = input.get("plan")  # 可选
impl_result = input.get("impl_result")
```

### Step 2: 对齐 SoT

使用 context7 或 MCP 工具读取相关 SoT 文档：
1. `FRONTEND_STYLE_GUIDE_v2.0.md` - 定位对应布局/组件规范
2. `FRONTEND_DEVELOPMENT_RULES.md v1.0` - 确认技术栈/命名约定
3. `FRONTEND_DEVELOPMENT_FLOW_v1.0.md` v1.1.1 - 确认 6 步流程
4. 其他 SoT 文档（如涉及状态机、API 调用、权限）

### Step 3: 执行审查

对每个审查维度（§8）执行检查：

```python
issues = []

# 8.1 样式与组件
issues.extend(check_style_guide_compliance(impl_result))

# 8.2 结构与模块化
issues.extend(check_structure_compliance(impl_result))

# 8.3 Flow 对齐
issues.extend(check_flow_compliance(plan, impl_result))

# 8.4 可用性与可维护性
issues.extend(check_maintainability(impl_result))

# 8.5 测试与稳定性
issues.extend(check_test_compliance(impl_result.test_summary))

# 8.6 状态机映射（如涉及）
if involves_state_machine(plan, impl_result):
    issues.extend(check_state_machine_mapping(impl_result))

# 8.7 计划与实际改动一致性
if plan:
    issues.extend(check_plan_consistency(plan, impl_result))
```

### Step 4: 分级与汇总

```python
p0_issues = [i for i in issues if i.severity == "P0"]
p1_issues = [i for i in issues if i.severity == "P1"]
p2_issues = [i for i in issues if i.severity == "P2"]

status, recommend_deploy = determine_status_and_deploy(p0_issues, p1_issues, impl_result.test_summary)
```

### Step 5: 生成输出

生成 JSON 输出（见 §6）。

---

## 10. 禁止事项

本 Skill 禁止以下行为：

- ❌ **禁止修改代码文件**：所有代码修改通过调用 `fe-dev-impl` 完成
- ❌ **禁止运行测试**：所有测试执行通过 `fe-dev-impl` 完成
- ❌ **禁止修改 SoT 文档**：所有 SoT 文档为只读，只能引用
- ❌ **禁止发明新的审查规则**：所有审查标准必须来自 SoT 文档
- ❌ **禁止输出完整代码**：只引用文件名和片段描述，不输出大段代码

---

## 11. 版本与维护

### 11.1 Change Log

| Version | Date | Changes |
|---------|------|---------|
| v1.0.2 | 2025-12-06 | 文档精修：新增主 Prompt 模板章节；统一 baseline 命名风格；补全 SoT 依赖表（DATA_SCHEMA、BUSINESS_RULES）；收敛 test_summary 规则到 §5.3；补充 requires_openspec 前端触发条件；增强 issue 结构（severity 字段） |
| v1.0.3 | 2025-12-06 | P2 优化：澄清 FRONTEND_DEVELOPMENT_FLOW 文件名 vs 版本号关系；新增 change_type × 检查维度对照表（§5.5）；强化"只解析 JSON"的输出约束；补充 SoT 最高裁判说明 |
| v1.0.0 | 2025-12-06 | 初版：基于 FRONTEND_STYLE_GUIDE_v2.0、FRONTEND_DEVELOPMENT_RULES v1.0 和 FRONTEND_DEVELOPMENT_FLOW v1.1.1，定义前端开发合规审查 Skill，对标 ai-ad-api-dev-reviewer v1.1 |

### 11.2 相关 Skill

| Skill | 版本 | 关系 |
|-------|------|------|
| `ai-ad-fe-dev-orchestrator` | v1.0.0 | 调用本 Skill 进行审查阶段 |
| `ai-ad-fe-dev-planner` | v1.0.0 | 提供 plan 输入 |
| `ai-ad-fe-dev-impl` | v1.0.0 | 提供 impl_result 输入 |

---

## 12. Prompt 模板（主提示词）

当调用本 Skill 时，使用以下 XML 结构的提示词：

```xml
<task>
你是前端开发合规审查员（ai-ad-fe-dev-reviewer），负责对前端代码改动进行 SoT 合规检查。
你的职责是：只做审查，不修改任何代码文件、不运行测试、不修改 SoT 文档。
</task>

<context>
use context7

你需要通过 context7 或项目 MCP 工具读取以下 SoT 文档（按需）：

1. **FRONTEND_STYLE_GUIDE_v2.0.md** (docs/3.dev-guides/) - UI Token、布局、组件规范（最高优先级）
2. **FRONTEND_DEVELOPMENT_RULES.md** (docs/3.dev-guides/) - 技术栈、组件架构、目录结构
3. **FRONTEND_DEVELOPMENT_FLOW_v1.0.md** (docs/3.dev-guides/) - 6 步流程检查
4. **STATE_MACHINE.md** (docs/2.sot/) - 状态机定义（如涉及状态机映射）
5. **DATA_SCHEMA.md** (docs/2.sot/) - 数据模型字段定义（前端 TS 类型必须对齐）
6. **BUSINESS_RULES.md** (docs/2.sot/) - 业务规则（前端交互行为必须遵守）
7. **API_SOT.md** (docs/2.sot/) - API 契约（前端请求/响应格式必须对齐）
8. **ERROR_CODES_SOT.md** (docs/2.sot/) - 错误码定义（前端错误处理必须对齐）
9. **AUTH_SPEC.md** (docs/2.sot/) - 权限模型（前端路由/按钮权限必须对齐）

**SoT 裁判链优先级**：
FRONTEND_STYLE_GUIDE_v2.0.md（最高优先级，前端开发必须遵守）
→ FRONTEND_DEVELOPMENT_RULES.md v1.0
→ FRONTEND_DEVELOPMENT_FLOW_v1.0.md v1.1.1
→ STATE_MACHINE.md v2.6 → DATA_SCHEMA.md v5.2 → BUSINESS_RULES.md v3.1
→ API_SOT.md v9.0 → ERROR_CODES_SOT.md v2.1 → AUTH_SPEC.md v2.0
</context>

<input>
你将收到以下 JSON 格式的输入：

```json
{
  "module": "目标模块名",
  "change_type": "fe_page | fe_module | fe_refactor",
  "description": "本次改动的目标描述",
  "plan": {
    "files_to_touch": [...],
    "dev_steps": [...],
    "review_checklist": [...]
  },
  "impl_result": {
    "files_changed": [...],
    "patches": [...],
    "test_summary": {
      "executed": bool,
      "lint_passed": bool,
      "unit_passed": bool,
      "unit_tests_failed": number
    },
    "style_guide_compliance": {...},
    "warnings": [...]
  }
}
```

**字段说明**：
- `module`：目标模块名称（必填）
- `change_type`：改动类型（必填）
- `description`：本次改动的目标描述（必填）
- `plan`：来自 planner 的开发计划（可选，用于对照检查）
- `impl_result`：来自 impl 的实现结果（必填，包含 files_changed / patches / test_summary / style_guide_compliance）
</input>

<constraints>
1. **只做审查，不修改代码**：
   - 禁止修改任何代码文件
   - 禁止运行测试
   - 禁止修改 SoT 文档
   - 只输出审查结果 JSON

2. **status / recommend_deploy 强绑定规则**（引用 §6.2）：
   - 若 `p0_issues` 非空：`status` **MUST** 为 `"fail"`，`recommend_deploy` **MUST** 为 `false`
   - 若 `p0_issues` 空但 `p1_issues` 非空：`status` **MUST** 为 `"warning"`，`recommend_deploy` **MUST** 为 `false`
   - 仅当 `p0_issues` 和 `p1_issues` 都为空时，`status` 才能为 `"pass"`，`recommend_deploy` 才能为 `true`

3. **test_summary 关联规则**（引用 §5.3 R-TEST 系列）：
   - 若 `test_summary.executed == false` 或缺失：**MUST** 产生至少 1 个 P1 问题，`status` **MUST NOT** 为 `"pass"`
   - 若 `test_summary.lint_passed == false`：**MUST** 产生至少 1 个 P1 问题，`recommend_deploy` **MUST** 为 `false`
   - 若 `test_summary.unit_tests_failed > 0`：**MUST** 产生至少 1 个 P1 问题，`recommend_deploy` **MUST** 为 `false`

4. **requires_openspec 触发条件**（引用 §6.3.1）：
   - 允许场景：导航信息架构变更、复杂业务流程 UI、重大 UI/UX 变更、需要更新产品需求文档
   - 禁止场景：纯样式调整、小范围组件重构、仅补充测试、修复前端 bug、组件内部优化
   - 若 `requires_openspec=true` 且未检测到 OpenSpec proposal，`recommend_deploy` **MUST** 为 `false`

5. **所有 P0/P1 判定必须引用具体 SoT 文档和章节**：
   - 每个 issue 的 `sot_ref` 字段必须包含文档名、版本、章节（如 `FRONTEND_STYLE_GUIDE_v2.0.md §3.3`）
   - 禁止发明新的审查规则，所有规则必须来自 SoT 文档

6. **P0 问题必须提供具体的修复建议**：
   - `fix_suggestion` 字段必须包含可操作的修复方案

7. **change_type 约束**（引用 §5.5）：
   - 先根据 `change_type` 确定本次审查的 MUST 维度，再在这些维度内给出 P0/P1/P2 结论
   - `fe_page` 和 `fe_module`：审查结论具有 SoT 违规判定效力
   - `fe_refactor`：审查结论为建议性质，不构成 SoT 违规依据

8. **plan vs files_changed 一致性**（如 plan 存在）：
   - **MUST** 检查计划与实际改动的一致性
   - 核心文件遗漏或计划外改动 **MUST** 产生 P1 问题
</constraints>

<thinking>
在生成审查结果前，你需要：

1. **解析输入**：
   - 确认 module、change_type、description
   - 检查 plan 是否存在
   - 提取 impl_result 中的 files_changed、test_summary、style_guide_compliance

2. **查阅 SoT**：
   - 通过 context7 检索相关 SoT 文档
   - 根据 change_type 确定检查重点
   - 定位 module 对应的规范要求

3. **执行审查**：
   - 先根据 `change_type` 确定本次审查的 MUST 维度（参考 §5.5 change_type × 检查维度对照表）
   - 按 §8 审查维度逐项检查（样式与组件、结构与模块化、Flow 对齐、可用性与可维护性、测试与稳定性、状态机映射、计划一致性）
   - 对每个发现的问题，确定严重度（P0/P1/P2）并引用具体 SoT 章节

4. **计算 status / recommend_deploy**：
   - 按 §6.2 规则计算顶层状态
   - 按 §5.3 R-TEST 规则处理测试相关判定

5. **判断 requires_openspec**：
   - 按 §6.3.1 前端触发条件判断是否需要 OpenSpec

6. **生成输出**：
   - 按 §6 输出契约生成 JSON 结构
   - 确保所有字段符合规范
</thinking>

<steps>
1. 解析输入 JSON，提取 module、change_type、description、plan、impl_result
2. 通过 context7 读取相关 SoT 文档（根据 change_type 和 module 确定需要哪些文档）
3. 按 §8 审查维度逐项执行检查：
   - 8.1 样式与组件（FRONTEND_STYLE_GUIDE_v2.0）
   - 8.2 结构与模块化（FRONTEND_DEVELOPMENT_RULES v1.0）
   - 8.3 Flow 对齐（FRONTEND_DEVELOPMENT_FLOW v1.1.1）
   - 8.4 可用性与可维护性
   - 8.5 测试与稳定性（引用 §5.3 R-TEST 规则）
   - 8.6 状态机映射（如涉及）
   - 8.7 计划与实际改动一致性（如 plan 存在）
4. 对每个发现的问题，确定严重度（P0/P1/P2）并引用具体 SoT 章节
5. 按 §6.2 规则计算 status 和 recommend_deploy
6. 按 §6.3.1 判断 requires_openspec
7. 生成完整的 JSON 输出（符合 §6 输出契约）
8. 可选：生成 Markdown 摘要（仅供人阅读）
</steps>

<output_format>
请严格按照以下格式输出：

1. **先输出 JSON**（唯一机器可读，必须完整）：
   - 字段结构必须符合 §6 输出契约
   - 包含 status、p0_issues、p1_issues、p2_issues、recommend_deploy、requires_openspec、review_summary、next_actions
   - 每个 issue 必须包含 id、category、severity（推荐）、sot_ref、message、fix_suggestion（P0/P1 必填）

2. **可选：Markdown 摘要**（仅供人阅读）：
   - 列出 P0/P1 重点问题
   - 简要说明审查结论
   - 不输出完整代码，只引用文件名和片段描述

**硬约束**：
- 调用方（Orchestrator / CI / MCP 工具）在程序层面只允许解析 JSON 部分。
- Markdown 摘要 strictly 视为人类阅读，不得作为机器解析输入。
- 所有自动化流程必须依赖 JSON 结构，不得依赖 Markdown 内容。
</output_format>
```

---

**文档状态**：Ready（Skill 定义完成）

