# SuperClaude Skill 使用指南

> **版本**: v3.0 | **更新**: 2025-12-07 | **架构**: 纯 Skill 模式

## 📋 概述

本项目使用 **SuperClaude Framework** 风格的 Skill 系统实现 AI 辅助开发。所有 Skill 位于 `.claude/skills/` 目录下，通过对话式调用。

> ⚠️ **重要**: 项目已迁移到纯 SuperClaude Skill 架构，废弃了 Python Agent 系统。

---

## 🎯 Skill 分类

### 代码生成 Skills

| Skill | 路径 | 功能 |
|-------|------|------|
| **ai-ad-be-gen** | `skills/ai-ad-be-gen/` | 后端代码生成（Schema/Service/Router） |
| **ai-ad-fe-gen** | `skills/ai-ad-fe-gen/` | 前端代码生成（Module/Hook/Component） |
| **ai-ad-test-gen** | `skills/ai-ad-test-gen/` | 测试代码生成（pytest/vitest） |

### 文档处理 Skills

| Skill | 路径 | 功能 |
|-------|------|------|
| **ai-ad-doc-orchestrator** | `skills/ai-ad-doc-orchestrator/` | 文档编排总控（大纲→正文→审查→冻结） |
| **ai-ad-doc-architect** | `skills/ai-ad-doc-architect/` | 文档架构设计 |
| **ai-ad-doc-fixer** | `skills/ai-ad-doc-fixer/` | 文档审查与修复 |
| **ai-project-doc-writer** | `skills/ai-project-doc-writer/` | 文档内容生成 |
| **ai-master-architect** | `skills/ai-master-architect/` | 宪法级一致性校验 |

### 治理 Skills

| Skill | 路径 | 功能 |
|-------|------|------|
| **ai-ad-spec-governor** | `skills/ai-ad-spec-governor/` | SoT 合规治理 |
| **ai-doc-system-auditor** | `skills/ai-doc-system-auditor/` | 文档系统审计 |

### 测试 Skills

| Skill | 路径 | 功能 |
|-------|------|------|
| **ai-ad-api-automation-test** | `skills/ai-ad-api-automation-test/` | API 自动化测试 |
| **ai-ad-agents-test-orchestrator** | `skills/ai-ad-agents-test-orchestrator/` | 测试编排 |
| **ai-ad-agents-test-runner** | `skills/ai-ad-agents-test-runner/` | 测试执行 |

### 工具 Skills

| Skill | 路径 | 功能 |
|-------|------|------|
| **prompt-engineer-skill** | `skills/prompt-engineer-skill/` | Prompt 工程辅助 |

---

## 🚀 使用方法

### 方法 1: 直接使用 Skill 名称（推荐）

在 Cursor/Claude Code 对话中：

```
使用 ai-ad-be-gen 实现充值审批 API，
目标文件: schemas/topup.py, services/topup_service.py, routers/topups.py
```

```
使用 ai-ad-fe-gen 实现充值列表页面，模块名: topups
```

```
使用 ai-ad-doc-orchestrator 生成 PROJECT.md，outline_exists = false
```

### 方法 2: 使用 Slash Commands

```
/sot-check backend/services/topup_service.py
```

```
/doc-agent 审查 docs/1.master/PROJECT.md
```

### 方法 3: 调用子 Skill 工作流

对于复杂任务，可以明确指定工作流：

```
请按以下步骤执行：
1. 使用 ai-project-doc-writer 生成 PROJECT.md 大纲
2. 使用 ai-ad-doc-fixer 审查大纲
3. 使用 ai-master-architect 进行宪法级校验
```

---

## 📝 核心 Skill 详解

### ai-ad-be-gen (后端代码生成)

**输入**:
```json
{
  "task": "实现充值审批 API",
  "target_files": ["schemas/topup.py", "services/topup_service.py", "routers/topups.py"]
}
```

**约束**:
- ✅ 可写: `backend/schemas/`, `backend/services/`, `backend/routers/`
- ❌ 禁止: `backend/models/`, `migrations/`
- 必须遵循 SoT: STATE_MACHINE, DATA_SCHEMA, API_SOT, ERROR_CODES

**输出**:
```json
{
  "changes": [{"file": "...", "content": "..."}],
  "notes": ["自检说明"],
  "sot_refs": ["STATE_MACHINE.md#topup", "BR-TP-001"]
}
```

### ai-ad-fe-gen (前端代码生成)

**输入**:
```json
{
  "task": "实现充值列表页面",
  "module": "topups",
  "target_files": ["src/modules/topups/TopupsPageShell.tsx"]
}
```

**约束**:
- ✅ 可写: `frontend/src/modules/`, `frontend/src/lib/api/`
- ❌ 禁止: `frontend/node_modules/`, `frontend/.next/`
- 技术栈: Next.js 14+, shadcn/ui, TanStack Query

**输出**: 同上

### ai-ad-doc-orchestrator (文档编排)

**工作流**:
```
CONTEXT_SCAN → OUTLINE_INIT → OUTLINE_GENERATE → OUTLINE_REVIEW
    → OUTLINE_PATCH → OUTLINE_FREEZE → INIT → DW-FILL
    → DOC-ANALYZE → DOC-PATCH → MASTER-CHECK → FREEZE
```

**输入**:
```json
{
  "doc_name": "PROJECT.md",
  "outline_exists": false,
  "start_chapter": 1,
  "end_chapter": 6
}
```

**子 Skill**:
- `ai-project-doc-writer` - 生成大纲和正文
- `ai-ad-doc-fixer` - 审查和修复
- `ai-master-architect` - 宪法级校验

---

## ⚙️ 配置说明

### Skill 自动加载

Cursor/Claude Code 会自动扫描 `.claude/skills/` 目录加载所有 Skill。

### 验证 Skill 加载

在对话中询问：
```
你现在可以使用哪些 Skill？请列出所有可用的 ai-ad-* Skill。
```

### Skill 文件结构

每个 Skill 包含：
```
skills/ai-ad-be-gen/
├── SKILL.md       # Skill 定义（必须）
└── README.md      # 使用说明（可选）
```

`SKILL.md` 必须包含 YAML frontmatter:
```yaml
---
name: ai-ad-be-gen
version: "2.0"
status: production
layer: Skill
sot_dependencies:
  required:
    - docs/2.sot/DATA_SCHEMA.md
    - docs/2.sot/STATE_MACHINE.md
output_boundaries:
  writable:
    - backend/schemas/**
  forbidden:
    - backend/models/**
---
```

---

## 🔧 故障排除

### Skill 未加载

1. 检查目录结构是否正确
2. 确认 `SKILL.md` 文件存在
3. 重启 Cursor/Claude Code

### Skill 执行失败

1. 检查输入参数是否完整
2. 确认目标文件在可写区域内
3. 验证 SoT 文档是否存在

### 输出不符合预期

1. 明确指定 target_files
2. 提供更详细的 task 描述
3. 检查是否需要先读取现有代码

---

## 🗑️ 废弃组件

以下组件已废弃，请勿使用：

| 废弃项 | 替代方案 |
|--------|----------|
| `/agent be <task>` | `使用 ai-ad-be-gen <task>` |
| `/agent fe <task>` | `使用 ai-ad-fe-gen <task>` |
| `/orch be_then_test` | 分步调用 be-gen + test-gen |
| `agents/` 目录 | `.claude/skills/` |
| `agent_platform/` 目录 | 废弃 |
| `ai-ad-sot-doc-pipeline` | `ai-ad-spec-governor` |
| `ai-ad-dev-doc-writer` | `ai-project-doc-writer` |

---

## 📚 相关文档

- **主入口**: [README.md](README.md)
- **项目规则**: [PROJECT_RULES.md](PROJECT_RULES.md)
- **Skills 索引**: [skills/README.md](skills/README.md)
- **Skill 优化报告**: [skills/SKILL_OPTIMIZATION_REPORT_v1.0.md](skills/SKILL_OPTIMIZATION_REPORT_v1.0.md)

---

**基准**: AI Code Factory v3.0 | SuperClaude Framework Style
