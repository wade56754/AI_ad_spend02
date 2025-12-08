# 统一工作流模板配置

> **SoT 基准**: DEV_FLOW_SOT_v1.1 (docs/2.sot/DEV_FLOW_SOT_v1.0.md)
> **版本**: v1.2 (7 Flow 架构)

## 概述

本文件定义 SuperClaude + AI 代码工厂的标准工作流模板，供 `/dev-flow` 命令和其他自动化工具使用。

## SuperClaude 增强层

所有 Skills 现已集成 SuperClaude 增强能力，通过 `superclaude-enhancer` Skill 提供：

### 增强模式

| 模式 | 说明 | 触发时机 | SuperClaude 命令 |
|------|------|---------|-----------------|
| `pre_analysis` | 前置分析 | 代码生成前 | /sc:analyze, /sc:research |
| `post_review` | 后置审查 | 代码生成后 | /sc:analyze, /sot-check |
| `smart_suggest` | 智能建议 | 按需调用 | /sc:improve, /sc:design |
| `troubleshoot` | 问题诊断 | Bug 修复时 | /sc:troubleshoot |

### 已增强的 Skills

| Skill | 版本 | 增强模式 |
|-------|------|---------|
| ai-ad-be-gen | v2.1 | pre_analysis, post_review |
| ai-ad-test-gen | v2.1 | pre_analysis, post_review |
| ai-ad-fe-gen | v2.1 | pre_analysis, post_review |
| ai-doc-system-auditor | v2.0 | post_review, smart_suggest |

## 工作流模板定义 (7 Flow)

### 1. BE 工作流 (BE_DEV_FLOW - 后端功能开发)

```yaml
name: be
flow_id: BE_DEV_FLOW
description: "后端功能开发流程"
phases:
  - id: analyze
    tool: "/sc:pm"
    type: superclaude
    description: "需求分析与任务分解"
    required: true

  - id: sot_check
    tool: "/sot-check docs/2.sot/"
    type: ai_code_factory
    description: "SoT 合规性检查"
    required: true
    blocking_on_fail: true

  - id: generate_schema
    tool: "/gen be"
    type: ai_code_factory
    description: "Schema 层生成"
    required: true

  - id: generate_service
    tool: "/gen be"
    type: ai_code_factory
    description: "Service 层生成"
    required: true

  - id: generate_router
    tool: "/gen be"
    type: ai_code_factory
    description: "Router 层生成"
    required: true

  - id: generate_test
    tool: "/gen test"
    type: ai_code_factory
    description: "测试生成"
    required: true

  - id: review
    tools:
      - "/sc:analyze"
      - "/sot-check"
    type: hybrid
    description: "代码审查"
    required: true

  - id: commit
    tool: "/sc:git commit"
    type: superclaude
    description: "提交代码"
    required: false
```

### 2. FE 工作流 (FE_DEV_FLOW - 前端功能开发)

```yaml
name: fe
flow_id: FE_DEV_FLOW
description: "前端功能开发流程"
phases:
  - id: sot_check
    tool: "/sot-check docs/2.sot/API_SOT.md"
    type: ai_code_factory
    description: "API 契约检查"
    required: true

  - id: generate_api_client
    tool: "/gen fe"
    type: ai_code_factory
    description: "API Client 生成"
    required: true

  - id: generate_component
    tool: "/gen fe"
    type: ai_code_factory
    description: "组件/页面生成"
    required: true

  - id: generate_test
    tool: "/gen test"
    type: ai_code_factory
    description: "前端测试生成"
    required: true

  - id: review
    tool: "/review"
    type: ai_code_factory
    description: "代码审查"
    required: true
```

### 3. FIX 工作流 (API_FIX_FLOW - 接口 Bug 修复)

```yaml
name: fix
flow_id: API_FIX_FLOW
description: "接口 Bug 修复流程"
phases:
  - id: diagnose
    tool: "/sc:troubleshoot"
    type: superclaude
    description: "问题诊断"
    required: true

  - id: sot_check
    tool: "/sot-check"
    type: ai_code_factory
    description: "SoT 对比"
    required: true

  - id: fix
    tool: "/gen be"
    type: ai_code_factory
    description: "代码修复"
    required: true

  - id: test
    tools:
      - "/gen test"
      - "/review"
    type: hybrid
    description: "测试验证"
    required: true
```

### 4. TEST 工作流 (TEST_HARDEN_FLOW - 测试加固)

```yaml
name: test
flow_id: TEST_HARDEN_FLOW
description: "测试加固流程"
phases:
  - id: coverage_analysis
    tool: "/sot-check backend/tests/"
    type: ai_code_factory
    description: "覆盖分析"
    required: true

  - id: state_machine_test
    tool: "/gen test"
    type: ai_code_factory
    description: "状态机测试补齐"
    required: true

  - id: boundary_test
    tool: "/gen test"
    type: ai_code_factory
    description: "边界条件测试补齐"
    required: true

  - id: review
    tool: "/review backend/tests/"
    type: ai_code_factory
    description: "测试审查"
    required: true
```

### 5. DOC 工作流 (DOC_FREEZE_FLOW - 文档审计/冻结)

```yaml
name: doc
flow_id: DOC_FREEZE_FLOW
description: "文档审计/冻结流程"
phases:
  - id: audit
    tool: "/doc"
    type: ai_code_factory
    description: "文档审计"
    required: true

  - id: verify
    tool: "/sot-check docs/2.sot/"
    type: ai_code_factory
    description: "SoT 一致性验证"
    required: true

  - id: freeze
    tool: "/doc --freeze"
    type: ai_code_factory
    description: "Freeze 报告生成"
    required: false

  - id: generate
    tool: "/sc:document"
    type: superclaude
    description: "补充文档生成"
    required: false
```

### 6. FULL 工作流 (FULL_FLOW - 完整功能开发)

```yaml
name: full
flow_id: FULL_FLOW
description: "完整功能开发流程 (BE + FE + TEST + DOC)"
phases:
  - id: backend
    workflow: "be"
    description: "执行 BE_DEV_FLOW"
    required: true

  - id: frontend
    workflow: "fe"
    description: "执行 FE_DEV_FLOW"
    required: true

  - id: test_harden
    workflow: "test"
    description: "执行 TEST_HARDEN_FLOW"
    required: true

  - id: doc_freeze
    workflow: "doc"
    description: "执行 DOC_FREEZE_FLOW"
    required: true
```

### 7. REFACTOR 工作流 (REFACTOR_FLOW - 代码重构)

```yaml
name: refactor
flow_id: REFACTOR_FLOW
description: "代码重构流程 (不改变业务行为)"
constraints:
  - "不得改变业务行为"
  - "不得修改 SoT 定义"
  - "输入/输出契约保持不变"
entry_conditions:
  - "测试覆盖率 >= 80%"
  - "CI 绿色"
  - "SoT 文档 frozen"
exit_conditions:
  - "所有现有测试通过"
  - "行为等价验证通过"
phases:
  - id: baseline
    tool: "pytest backend/tests/"
    type: manual
    description: "建立测试基线"
    required: true

  - id: analyze
    tool: "/sc:analyze"
    type: superclaude
    description: "代码分析"
    required: true

  - id: sot_verify
    tool: "/sot-check"
    type: ai_code_factory
    description: "SoT 验证"
    required: true

  - id: improve
    tools:
      - "/sc:improve"
      - "/gen be"
    type: hybrid
    description: "重构实施"
    required: true

  - id: regression
    tools:
      - "/sot-check"
      - "pytest"
    type: hybrid
    description: "等价验证"
    required: true
```

## 工具分类

### SuperClaude 专属工具

| 工具 | 用途 | 场景 |
|------|------|------|
| `/sc:pm` | 项目管理/任务分解 | 需求分析、规划 |
| `/sc:analyze` | 代码分析 | 质量、安全、性能 |
| `/sc:troubleshoot` | 问题诊断 | Bug 定位 |
| `/sc:improve` | 代码改进 | 重构、优化 |
| `/sc:research` | 深度研究 | 技术调研 |
| `/sc:explain` | 概念解释 | 文档、教学 |
| `/sc:design` | 架构设计 | API、组件设计 |
| `/sc:document` | 文档生成 | 文档编写 |
| `/sc:git` | Git 操作 | 提交、分支 |
| `/sc:build` | 构建部署 | 编译、打包 |
| `/sc:test` | 测试执行 | 运行测试 |

### AI 代码工厂专属工具 (v2.4)

| 工具 | 用途 | 场景 |
|------|------|------|
| `/gen be` | 后端代码生成 | Router/Service/Schema |
| `/gen fe` | 前端代码生成 | 组件/页面 |
| `/gen test` | 测试代码生成 | 状态机/账本测试 |
| `/review` | 代码/架构审查 | 质量/安全/SoT 检查 |
| `/doc` | 文档审计 | P0/P1/P2 检查 |
| `/sot-check` | SoT 合规检查 | 版本/引用验证 |

## SoT 裁判链

所有工作流必须遵循以下 SoT 优先级：

```
1. STATE_MACHINE.md v2.6    (状态机定义)
2. DATA_SCHEMA.md v5.2      (数据结构)
3. BUSINESS_RULES.md v3.2   (业务规则)
4. API_SOT.md v9.0          (API 规范)
5. ERROR_CODES_SOT.md v2.1  (错误码)
6. AUTH_SPEC.md v2.0        (权限)
7. LEDGER_SOT.md v1.1       (账本)
```

## 快速命令组合

```bash
# 后端功能开发
/dev-flow be <任务描述>

# 前端功能开发
/dev-flow fe <任务描述>

# 接口 Bug 修复
/dev-flow fix <问题描述>

# 测试加固
/dev-flow test <测试目标>

# 文档审计/冻结
/dev-flow doc [目标目录]

# 完整功能开发 (前后端 + 测试 + 文档)
/dev-flow full <任务描述>

# 代码重构 (不改业务)
/dev-flow refactor <重构目标>
```

## 历史命名对照 (已废弃)

| 旧命名 | 新命名 | 说明 |
|--------|--------|------|
| `feature` | `be` 或 `full` | 按范围选择 |
| `bugfix` | `fix` | 统一简写 |
| `docs` | `doc` | 统一简写 |

## 决策矩阵

| 任务类型 | 涉及 SoT | 推荐工作流 | Flow ID |
|---------|---------|-----------|---------|
| 后端新功能 | 是 | `/dev-flow be` | BE_DEV_FLOW |
| 前端新功能 | 是 | `/dev-flow fe` | FE_DEV_FLOW |
| Bug 修复 | 可能 | `/dev-flow fix` | API_FIX_FLOW |
| 测试补齐 | 是 | `/dev-flow test` | TEST_HARDEN_FLOW |
| 文档治理 | 是 | `/dev-flow doc` | DOC_FREEZE_FLOW |
| 端到端功能 | 是 | `/dev-flow full` | FULL_FLOW |
| 代码重构 | 是 | `/dev-flow refactor` | REFACTOR_FLOW |
| 简单修改 | 否 | `/sc:implement` | - |
| 研究调查 | 否 | `/sc:research` | - |
| Git 操作 | 否 | `/sc:git` | - |

---

**版本**: v1.2 (7 Flow 架构)
**SoT 基准**: DEV_FLOW_SOT_v1.1
**创建日期**: 2025-12-07
**更新日期**: 2025-12-07
**维护者**: AI Code Factory Team
