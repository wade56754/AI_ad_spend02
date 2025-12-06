---
name: ai-ad-fe-dev-impl
version: v1.0.0
description: >
  前端实现工程师 Skill，在已明确 SoT 和开发计划的前提下，根据 planner 的 plan，
  生成/修改前端代码（Next.js 14 + TypeScript + Tailwind CSS）。
  本 Skill 只做两件事：生成/修改代码文件 + 提供测试建议。
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
  # === 现有前端代码结构（只读参考） ===
  - frontend/app/                             # Next.js App Router 路由入口
  - frontend/src/modules/                     # 业务模块（Shell + Components + Hooks + Types）
  - frontend/src/lib/                         # 核心工具库（api/apiFetch.ts, auth/, validation/）
  - frontend/src/modules/shared/              # 跨模块共享组件（PageShell, UI 组件）
---

# Frontend Dev Impl Skill

## 1. Skill 概要

本 Skill 的唯一职责：

> 根据 SoT（FRONTEND_STYLE_GUIDE_v2.0 + FRONTEND_DEVELOPMENT_FLOW v1.1.1）+ planner 的 plan，
> 生成/修改 TSX、hooks、module 等前端代码文件，
> 并在需要时提供测试命令建议。

**本 Skill 通常由 `ai-ad-fe-dev-orchestrator` 调用**，也可由用户直接调用。

---

## 2. 适用场景

当满足以下条件时使用本 Skill：

- 已有明确的前端开发需求（fe_page / fe_module / fe_refactor）
- 已确定目标模块（module）
- 已有来自 `ai-ad-fe-dev-planner` 的开发计划（plan）
- 需要实际生成或修改前端代码（TSX / hooks / types）

---

## 3. 禁用场景

出现以下情况时，不要使用本 Skill：

- 仅需要生成开发计划（应使用 `ai-ad-fe-dev-planner`）
- 仅需要 SoT 合规审查（应使用 `ai-ad-fe-dev-reviewer`）
- 仅需要运行测试（应使用测试工具或 CI/CD）
- 需求不明确，尚需探索和规划

---

## 4. SoT 文档依赖（只读，最高优先级）

| 文档 | 版本 | 用途 |
|------|------|------|
| `docs/3.dev-guides/FRONTEND_STYLE_GUIDE_v2.0.md` | v2.0 | UI Token、布局、组件规范（**最高优先级**） |
| `docs/3.dev-guides/FRONTEND_DEVELOPMENT_RULES.md` | v1.0 | 技术栈、组件架构参考 |
| `docs/3.dev-guides/FRONTEND_DEVELOPMENT_FLOW.md` | v1.1.1 | 前端开发 6 步流程 |
| `docs/2.sot/API_SOT.md` | v9.0 | API 契约（前端请求/响应格式必须对齐） |
| `docs/2.sot/ERROR_CODES_SOT.md` | v2.1 | 错误码定义（前端错误处理必须对齐） |
| `docs/2.sot/STATE_MACHINE.md` | v2.6 | 状态机定义（前端必须映射） |
| `docs/2.sot/DATA_SCHEMA.md` | v5.2 | 数据模型字段定义（前端类型定义必须对齐） |

**原则**：任何"规范是什么"的问题，以 SoT 文档为唯一真相来源。

---

## 5. 项目结构

本 Skill 主要操作以下目录：

```
frontend/
├── app/                          # Next.js App Router
│   ├── (dashboard)/              # 主业务路由组
│   │   └── {module}/
│   │       └── page.tsx           # 路由入口（仅负责路由与编排）
│   ├── layout.tsx                # 根布局
│   └── globals.css                # 全局样式（颜色 Token 定义）
└── src/
    ├── lib/                       # 核心工具库
    │   ├── api/                   # API 客户端（apiFetch.ts）
    │   ├── auth/                  # 认证工具
    │   └── validation/            # Zod schemas
    └── modules/                    # 业务模块（按领域划分）
        ├── shared/                 # 跨模块共享
        │   └── components/
        │       ├── ui/             # 基础 UI（shadcn 封装）
        │       ├── layout/         # 布局组件（PageShell）
        │       └── feedback/       # 反馈组件
        └── {module}/
            ├── {Module}PageShell.tsx  # Shell 组件（布局与数据组合）
            ├── components/            # 业务组件
            ├── hooks/                 # 数据 hooks
            ├── services/             # API 服务（可选）
            └── types/                # TypeScript 类型定义
```

**目录结构规范**：必须遵守 `FRONTEND_STYLE_GUIDE_v2.0.md §4.1`。

---

## 6. 输入字段定义

```json
{
  "change_type": "fe_module",
  "module": "dashboard_overview",
  "route": "/dashboard",
  "description": "为 dashboard 模块新增概览页面，展示 KPI、趋势图表和风险预警",
  "plan": {
    "module": "dashboard_overview",
    "change_type": "fe_module",
    "files_to_touch": [
      "frontend/app/dashboard/page.tsx",
      "frontend/src/modules/dashboard/DashboardShell.tsx",
      "frontend/src/modules/dashboard/hooks/useDashboardData.ts",
      "frontend/src/modules/dashboard/types/index.ts"
    ],
    "dev_steps": [
      {
        "id": "FE-STEP-01",
        "phase": "sot_review",
        "description": "查阅相关 SoT 文档...",
        "sot_refs": ["FRONTEND_STYLE_GUIDE_v2.0.md §3.3"]
      },
      {
        "id": "FE-STEP-02",
        "phase": "route_design",
        "file": "frontend/app/dashboard/page.tsx",
        "description": "设计路由结构..."
      },
      {
        "id": "FE-STEP-03",
        "phase": "data_binding",
        "file": "frontend/src/modules/dashboard/hooks/useDashboardData.ts",
        "description": "实现数据层..."
      },
      {
        "id": "FE-STEP-04",
        "phase": "component_dev",
        "file": "frontend/src/modules/dashboard/DashboardShell.tsx",
        "description": "开发组件..."
      },
      {
        "id": "FE-STEP-05",
        "phase": "interaction",
        "description": "实现交互逻辑..."
      },
      {
        "id": "FE-STEP-06",
        "phase": "testing",
        "file": "frontend/src/modules/dashboard/__tests__/DashboardShell.test.tsx",
        "description": "编写测试..."
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
    ],
    "sot_references": [
      {
        "doc": "FRONTEND_STYLE_GUIDE.md",
        "version": "v2.0",
        "sections": ["§3.3 Dashboard 12 栅格布局"]
      }
    ]
  },
  "auto_write": true,
  "run_tests": true
}
```

**默认值**：
- `plan`: null（无计划时自行推导，但**强烈建议**提供 plan）
- `auto_write`: false（只给出建议 patch，不写文件）
- `run_tests`: true（生成测试命令建议，但不直接执行）

---

## 7. 硬性约束（Constraints）

### 7.1 SoT 对齐

- 前端代码必须符合 FRONTEND_STYLE_GUIDE_v2.0.md、FRONTEND_DEVELOPMENT_RULES.md v1.0、FRONTEND_DEVELOPMENT_FLOW.md v1.1.1
- 不得发明新的 UI Token、颜色值、间距值
- 不得违反 STYLE_GUIDE 的布局规范（如 12 栅格、PageShell 模式）
- 如确需新增，必须在输出中标记为"需要 SoT 更新"

### 7.2 UI Token 使用（FRONTEND_STYLE_GUIDE_v2.0.md §5）

所有颜色、间距、排版必须使用语义化 Token：

```tsx
// ✅ 正确：使用 UI Token
<div className="bg-card-bg text-text-strong p-4 gap-4">
  <h1 className="text-2xl font-semibold">标题</h1>
</div>

// ❌ 错误：硬编码颜色/间距
<div className="bg-white text-gray-900 p-16px gap-16px">
  <h1 className="text-24px font-semibold">标题</h1>
</div>
```

**禁止**：
- 硬编码颜色值（如 `bg-white`, `text-gray-900`）
- 硬编码间距值（如 `p-16px`, `gap-16px`）
- 使用不在 STYLE_GUIDE 中定义的 Token

### 7.3 组件命名与结构

**组件命名**（FRONTEND_DEVELOPMENT_RULES.md v1.0 §3.3）：
- 组件：PascalCase（如 `DashboardShell.tsx`）
- Hooks：camelCase with `use` prefix（如 `useDashboardData.ts`）
- Types：PascalCase（如 `DashboardData`, `DashboardProps`）

**目录结构**（FRONTEND_STYLE_GUIDE_v2.0.md §4.1）：
- `app/{route}/page.tsx`：路由入口（仅负责路由与编排）
- `src/modules/{module}/{Module}PageShell.tsx`：Shell 组件（布局与数据组合）
- `src/modules/{module}/components/`：业务组件
- `src/modules/{module}/hooks/`：数据 hooks
- `src/modules/{module}/types/`：TypeScript 类型定义

### 7.4 API 调用与 Envelope 解包

所有 API 调用必须使用 `apiFetch.ts`（FRONTEND_DEVELOPMENT_FLOW.md v1.1.1 §3.4）：

```tsx
// ✅ 正确：使用 apiFetch（自动处理 Envelope 解包）
import { apiFetch } from '@/lib/api/apiFetch';

const { data, error } = await apiFetch<DashboardSummary>('/api/v1/dashboard/summary');

// ❌ 错误：直接使用 fetch
const response = await fetch('/api/v1/dashboard/summary');
const json = await response.json();
```

**规则**：
- 必须使用 `apiFetch.ts` 进行所有 API 调用
- `apiFetch` 已自动处理 Envelope 解包（`success: true` → 返回 `data`，`success: false` → 抛出错误）
- 错误处理必须使用 ERROR_CODES_SOT.md v2.1 定义的错误码

### 7.5 状态处理（Loading/Error/Empty）

所有数据获取必须处理三种状态（FRONTEND_STYLE_GUIDE_v2.0.md §3.2）：

```tsx
// ✅ 正确：使用 DataStateManager 或 PageShell 统一封装
import { DataStateManager } from '@/modules/shared/components/ui/data-state/DataStateManager';

export function DashboardShell() {
  const { data, isLoading, error } = useDashboardData();
  
  return (
    <DataStateManager
      isLoading={isLoading}
      error={error}
      isEmpty={!data || data.length === 0}
      loadingComponent={<LoadingState />}
      errorComponent={<ErrorState error={error} />}
      emptyComponent={<EmptyState />}
    >
      {/* 实际内容 */}
    </DataStateManager>
  );
}

// ❌ 错误：未处理 Loading/Error/Empty 状态
export function DashboardShell() {
  const { data } = useDashboardData();
  return <div>{data.map(...)}</div>; // 缺少状态处理
}
```

### 7.6 错误处理与错误码

所有错误处理必须使用 ERROR_CODES_SOT.md v2.1 定义的错误码：

```tsx
// ✅ 正确：使用错误码
import { ApiError } from '@/lib/api/apiFetch';

try {
  await apiFetch('/api/v1/daily-reports/1/submit');
} catch (error) {
  if (error instanceof ApiError) {
    if (error.code === 'STATE_400') {
      toast.error('状态转换非法，请查看状态机规则');
    } else if (error.code === 'VALIDATION_001') {
      toast.error(error.message);
    }
  }
}

// ❌ 错误：使用字符串匹配或硬编码错误信息
catch (error) {
  if (error.message.includes('非法')) { // 禁止
    toast.error('操作失败');
  }
}
```

### 7.7 文件变更范围

- **优先**在 `plan.files_to_touch` 范围内修改
- **若需新增文件/模块**，必须说明理由并标注"超出原 plan"
- **不修改**与本次前端开发无关的模块
- **change_type=fe_refactor** 时，强调行为保持不变，只重构结构/命名

---

## 8. 执行流程

### Step 1: 解析输入

```typescript
// 解析输入 JSON，设置默认值
const change_type = input.get("change_type"); // "fe_page" | "fe_module" | "fe_refactor"
const module = input.get("module");
const description = input.get("description");
const plan = input.get("plan"); // 可能为 null
const auto_write = input.get("auto_write", false);
const run_tests = input.get("run_tests", true);
```

### Step 2: 对齐 SoT

使用 context7 或 MCP 工具读取：
1. `FRONTEND_STYLE_GUIDE_v2.0.md` - 定位对应布局/组件规范
2. `FRONTEND_DEVELOPMENT_RULES.md v1.0` - 确认技术栈/命名约定
3. `FRONTEND_DEVELOPMENT_FLOW.md v1.1.1` - 确认 6 步流程
4. `API_SOT.md v9.0` - 找到 module + endpoint 相关契约（如涉及 API 调用）

### Step 3: 推导/修正开发计划

**如果有 plan**：
- 检查与 SoT 是否冲突
- 必要时修正步骤顺序
- 确认 `files_to_touch` 符合目录结构规范

**如果无 plan**：
- 基于 SoT 推导最小必要 plan：
  1. 路由文件（`app/{route}/page.tsx`）
  2. Shell 组件（`src/modules/{module}/{Module}PageShell.tsx`）
  3. 数据 Hook（`src/modules/{module}/hooks/use{Module}Data.ts`）
  4. 类型定义（`src/modules/{module}/types/index.ts`）
  5. 业务组件（如需要）
  6. 测试文件（如需要）

### Step 4: 代码生成/修改

对每个 `files_to_touch`（或推导出的文件列表）：

```typescript
// 1. 读取现有实现（如存在）
const current_content = read_file(file_path);

// 2. 分析应如何变化（对照 SoT + plan）
// - 如果是新文件：生成完整代码
// - 如果是修改：生成最小差异 patch

// 3. 生成代码片段（不直接写入，除非 auto_write=true）
const patch = generate_patch(current_content, target_content);

// 4. 验证是否符合 SoT
validate_against_sot(patch, FRONTEND_STYLE_GUIDE_v2.0);
```

**代码生成规则**：
- 必须遵守 FRONTEND_STYLE_GUIDE_v2.0.md 的所有规则
- 必须使用 UI Token（颜色、间距、排版）
- 必须处理 Loading/Error/Empty 三种状态
- 必须使用 `apiFetch.ts` 进行 API 调用
- 必须使用 ERROR_CODES_SOT.md v2.1 错误码

### Step 5: 生成测试建议（如 run_tests=true）

```json
{
  "test_summary": {
    "executed": false,
    "suggested_commands": [
      "pnpm lint",
      "pnpm test:unit frontend/src/modules/dashboard",
      "pnpm test:e2e frontend/app/dashboard"
    ]
  }
}
```

**注意**：本 Skill **不直接执行测试**，只提供建议命令。

### Step 6: 输出结果

生成 JSON 输出（见 §9）。

---

## 9. 输出字段定义

```json
{
  "module": "dashboard_overview",
  "change_type": "fe_module",
  "files_changed": [
    "frontend/app/dashboard/page.tsx",
    "frontend/src/modules/dashboard/DashboardShell.tsx",
    "frontend/src/modules/dashboard/hooks/useDashboardData.ts",
    "frontend/src/modules/dashboard/types/index.ts"
  ],
  "code_summaries": [
    {
      "file": "frontend/app/dashboard/page.tsx",
      "action": "created",
      "summary": "创建路由入口，使用 PageContainer 包装 DashboardShell",
      "lines_added": 15,
      "lines_removed": 0
    },
    {
      "file": "frontend/src/modules/dashboard/DashboardShell.tsx",
      "action": "created",
      "summary": "创建 Shell 组件，实现 12 栅格布局，使用 UI Token",
      "lines_added": 120,
      "lines_removed": 0
    },
    {
      "file": "frontend/src/modules/dashboard/hooks/useDashboardData.ts",
      "action": "created",
      "summary": "创建数据 Hook，使用 React Query 和 apiFetch",
      "lines_added": 45,
      "lines_removed": 0
    }
  ],
  "patches": [
    {
      "file": "frontend/app/dashboard/page.tsx",
      "patch": "--- a/frontend/app/dashboard/page.tsx\n+++ b/frontend/app/dashboard/page.tsx\n@@ -0,0 +1,15 @@\n+'use client';\n+import PageContainer from '@/components/layout/page-container';\n+import { DashboardShell } from '@/modules/dashboard/DashboardShell';\n+\n+export default function DashboardPage() {\n+  return (\n+    <PageContainer>\n+      <DashboardShell />\n+    </PageContainer>\n+  );\n+}\n",
      "format": "unified_diff"
    }
  ],
  "test_summary": {
    "executed": false,
    "suggested_commands": [
      "pnpm lint",
      "pnpm test:unit frontend/src/modules/dashboard",
      "pnpm test:e2e frontend/app/dashboard"
    ],
    "coverage_target": "80%"
  },
  "warnings": [
    {
      "level": "P1",
      "type": "sot_violation",
      "message": "建议人工审查：颜色 Token 使用是否符合 STYLE_GUIDE §5.1",
      "file": "frontend/src/modules/dashboard/DashboardShell.tsx",
      "sot_ref": "FRONTEND_STYLE_GUIDE_v2.0.md §5.1"
    },
    {
      "level": "P2",
      "type": "scope_expansion",
      "message": "超出原 plan：新增了 frontend/src/modules/dashboard/components/DashboardKpiRow.tsx（原因：Shell 组件需要拆分子组件）",
      "file": "frontend/src/modules/dashboard/components/DashboardKpiRow.tsx"
    }
  ],
  "sot_compliance": {
    "status": "pass",
    "violations": [],
    "warnings": [
      {
        "rule": "UI Token 使用",
        "severity": "P1",
        "description": "建议人工审查颜色 Token 使用"
      }
    ]
  }
}
```

### 9.1 输出字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `module` | string | 回传输入的模块名 |
| `change_type` | string | 回传输入的变更类型 |
| `files_changed` | array | 实际修改的文件列表（相对路径，从项目根目录） |
| `code_summaries` | array | 每个文件的变更摘要（action, summary, lines_added, lines_removed） |
| `patches` | array | 每个文件的建议 patch（unified_diff 格式） |
| `test_summary` | object | 测试建议（executed=false, suggested_commands, coverage_target） |
| `warnings` | array | 警告信息（level, type, message, file, sot_ref） |
| `sot_compliance` | object | SoT 合规性检查结果（status, violations, warnings） |

### 9.2 patches 格式说明

每个 `patches` 项包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| `file` | string | 文件路径（相对路径） |
| `patch` | string | unified_diff 格式的 patch 文本 |
| `format` | enum | `unified_diff`（唯一支持格式） |

**unified_diff 格式示例**：
```
--- a/frontend/app/dashboard/page.tsx
+++ b/frontend/app/dashboard/page.tsx
@@ -0,0 +1,15 @@
+'use client';
+import PageContainer from '@/components/layout/page-container';
+import { DashboardShell } from '@/modules/dashboard/DashboardShell';
+
+export default function DashboardPage() {
+  return (
+    <PageContainer>
+      <DashboardShell />
+    </PageContainer>
+  );
+}
```

### 9.3 warnings 类型说明

| type | 说明 | 示例 |
|------|------|------|
| `sot_violation` | 可能违反 SoT 规范 | "建议人工审查：颜色 Token 使用是否符合 STYLE_GUIDE §5.1" |
| `scope_expansion` | 超出原 plan 范围 | "超出原 plan：新增了 DashboardKpiRow.tsx" |
| `risk_high` | 高风险改动 | "改动过大，建议分阶段提交" |
| `manual_review_required` | 需要人工审查 | "建议人工审查：复杂状态管理逻辑" |

---

## 10. change_type=fe_refactor 的特殊处理

当 `change_type=fe_refactor` 时，本 Skill 需要：

1. **强调行为保持不变**：
   - 在 `code_summaries` 中标注"重构：行为不变，仅优化结构/命名"
   - 在 `warnings` 中添加"需要回归测试验证行为不变"

2. **只重构结构/命名**：
   - 不改变组件 props 接口
   - 不改变 API 调用接口
   - 不改变 UI 交互逻辑
   - 不改变状态管理逻辑

3. **回归测试建议**：
   - 在 `test_summary.suggested_commands` 中强调回归测试
   - 建议运行 E2E 测试验证行为不变

---

## 11. 禁止事项

本 Skill 禁止以下行为：

- ❌ **禁止直接覆盖整个文件**：必须使用 patch 格式，只修改必要的部分
- ❌ **禁止违反 STYLE_GUIDE**：所有样式必须使用 UI Token，禁止硬编码
- ❌ **禁止绕过 FRONTEND_DEVELOPMENT_FLOW 流程**：必须遵循 6 步标准流程
- ❌ **禁止直接执行测试**：只提供测试命令建议，不直接运行
- ❌ **禁止修改 SoT 文档**：所有 SoT 文档为只读，只能引用
- ❌ **禁止发明新的样式规则**：所有样式规则必须来自 FRONTEND_STYLE_GUIDE_v2.0.md
- ❌ **禁止硬编码文件路径**：文件路径必须符合 FRONTEND_STYLE_GUIDE_v2.0.md §4.1 目录结构规范

---

## 12. 版本与维护

### 12.1 Change Log

| Version | Date | Changes |
|---------|------|---------|
| v1.0.0 | 2025-12-06 | 初版：基于 FRONTEND_DEVELOPMENT_FLOW v1.1.1，定义前端实现 Skill，对标 ai-ad-api-dev-impl v1.0.0 |

### 12.2 相关 Skill

| Skill | 版本 | 关系 |
|-------|------|------|
| `ai-ad-fe-dev-orchestrator` | v1.0.0 | 调用本 Skill 进行实现阶段 |
| `ai-ad-fe-dev-planner` | v1.0.0 | 提供 plan 输入 |
| `ai-ad-fe-dev-reviewer` | v1.0.0（规划中） | 使用本 Skill 输出的代码进行审查 |

---

**文档状态**：Ready（Skill 定义完成）
