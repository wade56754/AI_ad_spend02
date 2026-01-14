---
name: skills-index
version: "1.0"
status: active
layer: skill
owner: wade
last_reviewed: 2025-12-07
baseline: AI_CODE_FACTORY_DEV_GUIDE_v2.4, SoT Freeze v2.6
---

# AI 代码工厂 Skills 索引

> 纯 SuperClaude Skill 架构，无 Python 运行时依赖

## 架构概述

```
┌─────────────────────────────────────────────────────────┐
│                   Slash Commands                         │
│  /gen  /doc  /review  /sot-check  /dev-flow             │
└────────────────────────┬────────────────────────────────┘
                         │ 调用
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    Skills Layer                          │
│  ┌─────────┐ ┌───────────┐ ┌──────┐ ┌─────────┐        │
│  │  Core   │ │ Generators│ │ Docs │ │ Testing │        │
│  └─────────┘ └───────────┘ └──────┘ └─────────┘        │
└────────────────────────┬────────────────────────────────┘
                         │ 引用
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   SoT Documents                          │
│  STATE_MACHINE │ DATA_SCHEMA │ BUSINESS_RULES │ ...     │
└─────────────────────────────────────────────────────────┘
```

## Skills 分类

### Core (核心调度)

| Skill | 版本 | 状态 | 职责 |
|-------|------|------|------|
| [ai-ad-flow-orchestrator](./ai-ad-flow-orchestrator/) | 1.0 | active | **开发流程编排** |
| [ai-ad-doc-orchestrator](./ai-ad-doc-orchestrator/) | 1.4 | ready_for_production | 文档生产总调度 |
| [ai-master-architect](./ai-master-architect/) | 4.1 | ready_for_production | 架构审计裁决 |
| [ai-ad-spec-governor](./ai-ad-spec-governor/) | 1.5 | ready_for_production | 规范治理守护 |

### Generators (代码生成)

| Skill | 版本 | 状态 | 职责 |
|-------|------|------|------|
| [ai-ad-be-gen](./ai-ad-be-gen/) | 1.2 | ready_for_production | 后端代码生成 (FastAPI/SQLAlchemy) |
| [ai-ad-fe-gen](./ai-ad-fe-gen/) | 1.2 | ready_for_production | 前端代码生成 (React/TypeScript) |
| [ai-ad-test-gen](./ai-ad-test-gen/) | 1.2 | ready_for_production | 测试代码生成 (pytest) |

### Docs (文档工程)

| Skill | 版本 | 状态 | 职责 |
|-------|------|------|------|
| [ai-ad-doc-architect](./ai-ad-doc-architect/) | 2.0 | ready_for_production | 文档结构设计 |
| [ai-ad-doc-fixer](./ai-ad-doc-fixer/) | 2.0 | ready_for_production | 文档问题修复 |
| [ai-project-doc-writer](./ai-project-doc-writer/) | 3.1 | ready_for_production | ASDD 文档生产 |
| [ai-doc-system-auditor](./ai-doc-system-auditor/) | 2.0 | ready_for_production | 文档体系审计 |
| [ai-ad-sot-doc-pipeline](./ai-ad-sot-doc-pipeline/) | 1.2 | ready_for_production | SoT 文档流水线 |

### Testing (测试工具)

| Skill | 版本 | 状态 | 职责 |
|-------|------|------|------|
| [ai-ad-api-automation-test](./ai-ad-api-automation-test/) | 1.3 | ready_for_production | API 自动化测试 |

### Utils (工具类)

| Skill | 版本 | 状态 | 职责 |
|-------|------|------|------|
| [prompt-engineer-skill](./prompt-engineer-skill/) | 2.1 | ready_for_production | 提示词工程优化 |
| [superclaude-enhancer](./superclaude-enhancer/) | 1.0 | active | SuperClaude 增强器 |

### Bridge (整合桥接)

| Skill | 版本 | 状态 | 职责 |
|-------|------|------|------|
| [superpowers-factory-bridge](./superpowers-factory-bridge/) | 1.0 | active | **Superpowers + AI Factory 统一编排器** |

> 整合 Superpowers 方法论 + AI Code Factory 代码生成 + SuperClaude 质量增强
>
> 子代理提示词:
> - `prompts/implementer-with-factory.md` - TDD 实现者
> - `prompts/sot-spec-reviewer.md` - SoT 规格审查
> - `prompts/quality-reviewer-enhanced.md` - 质量审查增强

### Deprecated (已弃用)

| Skill | 原职责 | 弃用原因 |
|-------|--------|----------|
| ai-ad-agents-test-orchestrator | Agent 测试编排 | 迁移到纯 Skill 架构 |
| ai-ad-agents-test-runner | Agent 测试运行 | 迁移到纯 Skill 架构 |

## 命令映射

| 命令 | 触发的 Skills | 说明 |
|------|---------------|------|
| `/gen be <task>` | ai-ad-be-gen | 生成后端代码 |
| `/gen fe <task>` | ai-ad-fe-gen | 生成前端代码 |
| `/gen test <task>` | ai-ad-test-gen | 生成测试代码 |
| `/doc [dir]` | ai-doc-system-auditor | 文档审计 |
| `/review <file>` | ai-master-architect + ai-ad-spec-governor | 代码审查 |
| `/sot-check <file>` | ai-ad-spec-governor | SoT 合规检查 |
| `/dev-flow <type> <task>` | ai-ad-flow-orchestrator | 开发流程编排 (5 大 Flow) |
| `/udev <subcommand> <task>` | superpowers-factory-bridge | **统一开发编排** (Superpowers + Factory) |

### /udev 子命令详情

| 子命令 | 描述 | 触发的工作流 |
|--------|------|-------------|
| `/udev full <task>` | 完整开发周期 | BRAINSTORM → PLAN → EXECUTE → FINISH |
| `/udev brainstorm <topic>` | 设计+SoT上下文 | superpowers:brainstorming + /sot-context |
| `/udev plan <task>` | SoT感知计划 | superpowers:writing-plans + sot-aware-planning |
| `/udev tdd <feature>` | TDD+工厂测试 | RED → GREEN → REFACTOR + /gen test |
| `/udev impl <task>` | 子代理实现 | subagent-driven-dev + /gen be/fe |
| `/udev debug <issue>` | 系统化调试 | systematic-debugging + /sc:troubleshoot |
| `/udev finish` | 完成分支 | finishing-branch + /sot-check |

## Skill 元数据标准

所有 Skill 必须包含 YAML frontmatter:

```yaml
---
name: skill-name
version: "X.Y"
status: draft | active | ready_for_production | frozen | deprecated
layer: skill
owner: owner-name
last_reviewed: YYYY-MM-DD
baseline: AI_CODE_FACTORY_DEV_GUIDE_v2.4, SoT Freeze v2.6
---
```

## 开发规范

### 创建新 Skill

1. 在 `.claude/skills/` 下创建目录
2. 创建 `SKILL.md` 文件 (大写)
3. 添加完整的 YAML frontmatter
4. 定义 XML 结构化的 Skill 内容
5. 更新本索引文件

### Skill 文件命名

- 目录名: `ai-ad-{domain}-{function}`
- 文件名: `SKILL.md` (大写) 或 `skill.md` (小写)

### 版本管理

- 遵循 SemVer: MAJOR.MINOR
- MAJOR: 不兼容的接口变更
- MINOR: 向后兼容的功能增加

## 变更记录

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2026-01-13 | 1.2 | 新增 superpowers-factory-bridge，统一开发编排器整合 Superpowers + AI Factory |
| 2025-12-07 | 1.1 | 新增 ai-ad-flow-orchestrator，完善 /dev-flow 命令映射 |
| 2025-12-07 | 1.0 | 初始版本，完成从 Python Agent 到纯 Skill 架构迁移 |
