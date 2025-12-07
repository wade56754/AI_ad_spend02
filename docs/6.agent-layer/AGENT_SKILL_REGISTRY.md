---
version: v2.0
status: production
layer: agent-layer
owner: wade
last_reviewed: 2025-12-07
baseline: MASTER.md v3.4, SoT Freeze v2.6, AI Code Factory v3.0
---

# SuperClaude Skill 注册表

> **文档版本**: v2.0
> **状态**: Production
> **最后审查**: 2025-12-07
> **基准**: MASTER.md v3.4, SoT Freeze v2.6, AI Code Factory v3.0

---

## 1. Skills 总览

### 1.1 架构说明

本项目采用 **纯 SuperClaude Skill 架构**，所有 AI 辅助开发能力通过 `.claude/skills/` 目录下的 Markdown 定义实现。

> ⚠️ **架构变更 (v2.0)**: Python Agent/Skill 系统已废弃，统一使用 SuperClaude Skills。

### 1.2 Skill 定义

**SuperClaude Skill** 是一个 Markdown 定义的 AI 能力单元，包含：

| 组成部分 | 说明 |
|---------|------|
| **YAML Frontmatter** | 元数据（名称、版本、SoT 依赖、输出边界） |
| **Purpose** | Skill 用途说明 |
| **Input Contract** | 输入参数定义 |
| **Output Contract** | 输出格式定义 |
| **Constraints** | 必须遵守的边界约束 |
| **Prompt Template** | 执行指令模板 |

### 1.3 调用方式

**对话式调用**:
```
使用 ai-ad-be-gen 实现充值审批 API，
目标文件: schemas/topup.py, services/topup_service.py, routers/topups.py
```

**Slash Command 调用**:
```
/sot-check backend/services/topup_service.py
```

---

## 2. Skills 分类

### 2.1 代码生成 Skills

| Skill | 版本 | 功能 | 输出 |
|-------|------|------|------|
| **ai-ad-be-gen** | v2.0 | 后端代码生成 | Schema、Service、Router |
| **ai-ad-fe-gen** | v2.0 | 前端代码生成 | PageShell、hooks、components |
| **ai-ad-test-gen** | v1.0 | 测试代码生成 | pytest、vitest 测试用例 |

### 2.2 文档处理 Skills

| Skill | 版本 | 功能 | 工作流 |
|-------|------|------|--------|
| **ai-ad-doc-orchestrator** | v5.3 | 文档编排总控 | 大纲→审查→正文→冻结 |
| **ai-project-doc-writer** | v2.0 | 文档内容生成 | OUTLINE / DW-FILL 模式 |
| **ai-ad-doc-fixer** | v2.0 | 文档审查修复 | DOC-ANALYZE / DOC-PATCH 模式 |
| **ai-master-architect** | v1.0 | 宪法级校验 | MASTER/SoT 对齐检查 |
| **ai-ad-doc-architect** | v2.0 | 文档架构设计 | 结构一致性审查 |

### 2.3 治理 Skills

| Skill | 版本 | 功能 | 检查项 |
|-------|------|------|--------|
| **ai-ad-spec-governor** | v2.0 | SoT 合规治理 | 状态枚举、错误码、字段类型 |
| **ai-doc-system-auditor** | v1.0 | 文档系统审计 | 文档健康度评估 |

### 2.4 测试 Skills

| Skill | 版本 | 功能 |
|-------|------|------|
| **ai-ad-api-automation-test** | v1.0 | API 自动化测试设计 |
| **ai-ad-agents-test-orchestrator** | v1.0 | 测试编排 |
| **ai-ad-agents-test-runner** | v1.0 | 测试执行 |

### 2.5 工具 Skills

| Skill | 版本 | 功能 |
|-------|------|------|
| **prompt-engineer-skill** | v1.0 | Prompt 工程辅助 |

---

## 3. Skill 定义规范

### 3.1 SKILL.md 格式

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
    - docs/2.sot/API_SOT.md
  optional:
    - docs/2.sot/LEDGER_SOT.md
    - docs/2.sot/ERROR_CODES_SOT.md

output_boundaries:
  writable:
    - backend/schemas/**
    - backend/services/**
    - backend/routers/**
  forbidden:
    - backend/models/**
    - migrations/**
---

# ai-ad-be-gen

## 1. Purpose
后端代码生成 Skill，生成 FastAPI + SQLAlchemy + Pydantic 代码。

## 2. Input Contract
- task: 任务描述
- target_files: 目标文件列表

## 3. Output Contract
- changes: Dict[file_path, content]
- notes: List[str] - 自审笔记
- sot_refs: List[str] - SoT 引用

## 4. Constraints
- 必须遵循 SoT 裁判链
- 只能写入 writable 目录
- 禁止触碰 forbidden 目录

## 5. Prompt Template
...
```

### 3.2 命名约定

**规则**: `ai-ad-{domain}-{action}`

| 示例 | 域 | 动作 |
|------|---|------|
| `ai-ad-be-gen` | be (Backend) | gen (Generate) |
| `ai-ad-fe-gen` | fe (Frontend) | gen (Generate) |
| `ai-ad-test-gen` | test | gen (Generate) |
| `ai-ad-doc-fixer` | doc | fixer (Fix) |
| `ai-ad-spec-governor` | spec | governor (Govern) |

### 3.3 目录结构

```
.claude/skills/{skill-name}/
├── SKILL.md       # Skill 定义（必须）
└── README.md      # 使用说明（可选）
```

---

## 4. SoT 依赖矩阵

### 4.1 代码生成 Skills 依赖

| Skill | DATA_SCHEMA | STATE_MACHINE | API_SOT | ERROR_CODES | LEDGER_SOT | AUTH_SPEC |
|-------|------------|--------------|---------|-------------|------------|-----------|
| ai-ad-be-gen | ✅ 必须 | ✅ 必须 | ✅ 必须 | ⚪ 可选 | ⚪ 可选 | ⚪ 可选 |
| ai-ad-fe-gen | ❌ | ⚪ 可选 | ✅ 必须 | ❌ | ❌ | ⚪ 可选 |
| ai-ad-test-gen | ✅ 必须 | ✅ 必须 | ⚪ 可选 | ❌ | ⚪ 可选 | ❌ |

### 4.2 治理 Skills 依赖

| Skill | 依赖全部 SoT |
|-------|-------------|
| ai-ad-spec-governor | ✅ |
| ai-doc-system-auditor | ✅ |
| ai-master-architect | ✅ |

---

## 5. 输出边界定义

### 5.1 后端 Skills 边界

| Skill | 可写 | 禁止 |
|-------|------|------|
| **ai-ad-be-gen** | `backend/schemas/**`<br>`backend/services/**`<br>`backend/routers/**` | `backend/models/**`<br>`migrations/**` |
| **ai-ad-test-gen** | `backend/tests/**` | `backend/models/**` |

### 5.2 前端 Skills 边界

| Skill | 可写 | 禁止 |
|-------|------|------|
| **ai-ad-fe-gen** | `frontend/src/modules/**`<br>`frontend/src/lib/api/**` | `frontend/node_modules/**`<br>`frontend/.next/**` |

### 5.3 文档 Skills 边界

| Skill | 可写 | 禁止 |
|-------|------|------|
| **ai-ad-doc-orchestrator** | `docs/**` (非 SoT) | `docs/2.sot/**` |
| **ai-project-doc-writer** | `docs/**` (非 SoT) | `docs/2.sot/**` |

---

## 6. Skill 调用链

### 6.1 文档编排调用链

```
                    ┌─────────────────────────────────┐
                    │   ai-ad-doc-orchestrator        │
                    │   (文档编排总控)                 │
                    └─────────────┬───────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ ai-project-     │    │ ai-ad-doc-      │    │ ai-master-      │
│ doc-writer      │    │ fixer           │    │ architect       │
│ (内容生成)       │    │ (审查修复)       │    │ (宪法校验)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 6.2 代码生成调用链

```
┌─────────────────────────────────────────────────────────┐
│                  代码生成工作流                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  需求 ──▶ ai-ad-be-gen ──▶ ai-ad-test-gen              │
│              │                    │                     │
│              ▼                    ▼                     │
│         后端代码              单元测试                   │
│                                                         │
│  需求 ──▶ ai-ad-fe-gen ──▶ ai-ad-test-gen              │
│              │                    │                     │
│              ▼                    ▼                     │
│         前端代码              前端测试                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 7. 版本管理

### 7.1 版本号格式

**格式**: `v{MAJOR}.{MINOR}`

| 变更类型 | 版本策略 |
|---------|---------|
| 新增功能（向后兼容） | MINOR +1 |
| Breaking Changes | MAJOR +1 |

### 7.2 当前版本清单

| Skill | 版本 | 状态 | 最后更新 |
|-------|------|------|----------|
| ai-ad-be-gen | v2.0 | ✅ Production | 2025-12-06 |
| ai-ad-fe-gen | v2.0 | ✅ Production | 2025-12-06 |
| ai-ad-test-gen | v1.0 | ✅ Production | 2025-12-06 |
| ai-ad-doc-orchestrator | v5.3 | ✅ Production | 2025-11-28 |
| ai-ad-doc-architect | v2.0 | ✅ Production | 2025-11-27 |
| ai-ad-doc-fixer | v2.0 | ✅ Production | 2025-11-27 |
| ai-project-doc-writer | v2.0 | ✅ Production | 2025-11-27 |
| ai-master-architect | v1.0 | ✅ Production | 2025-11-27 |
| ai-ad-spec-governor | v2.0 | ✅ Production | 2025-11-27 |
| ai-doc-system-auditor | v1.0 | ✅ Production | 2025-11-27 |
| ai-ad-api-automation-test | v1.0 | ✅ Production | 2025-12-06 |
| prompt-engineer-skill | v1.0 | ✅ Production | 2025-11-25 |

---

## 8. 使用示例

### 8.1 后端代码生成

```
使用 ai-ad-be-gen 实现充值审批 API，
目标文件: schemas/topup.py, services/topup_service.py, routers/topups.py

要求:
1. 遵循 STATE_MACHINE.md#topup 状态转换
2. 遵循 LEDGER_SOT.md#topup 账本分录规则
3. 遵循 AUTH_SPEC.md 权限矩阵
4. 使用 ERROR_CODES_SOT.md 定义的错误码
```

### 8.2 前端代码生成

```
使用 ai-ad-fe-gen 实现充值列表页面，模块名: topups

要求:
1. 使用 shadcn/ui 组件库
2. 使用 TanStack Query 数据获取
3. 遵循 FRONTEND_RULES 规范
```

### 8.3 测试代码生成

```
使用 ai-ad-test-gen 为 topup_service 生成单元测试，覆盖:
1. test_approve_success - 成功审批
2. test_approve_wrong_status - 状态不允许审批
3. test_approve_no_permission - 权限不足
```

### 8.4 SoT 合规检查

```
/sot-check backend/services/topup_service.py
```

或:

```
使用 ai-ad-spec-governor 检查 backend/services/topup_service.py 的 SoT 合规性
```

### 8.5 文档编排

```
使用 ai-ad-doc-orchestrator 生成 PROJECT.md，outline_exists = false
```

---

## 9. 废弃说明

> ⚠️ **重要**: 以下 Python Skill 系统组件已废弃。

| 废弃组件 | 原位置 | 替代方案 |
|----------|--------|----------|
| **be_dev_skill** | `agents/skills/` | ai-ad-be-gen |
| **fe_dev_skill** | `agents/skills/` | ai-ad-fe-gen |
| **db_test_skill** | `agents/skills/` | ai-ad-test-gen |
| **sot_guard_skill** | `agents/skills/` | ai-ad-spec-governor |
| **_SKILL_REGISTRY** | `agents/skills_config.py` | `.claude/skills/README.md` |

---

## 10. 引用文献

**本文档引用的规范**:
- MASTER.md v3.4 - 系统宪法
- .claude/README.md - AI 代码工厂主入口
- .claude/skills/README.md - Skills 索引
- .claude/SUPERCLAUDE_SETUP.md - Skill 使用指南

**相关文档**:
- [AGENT_LAYER_OVERVIEW.md](./AGENT_LAYER_OVERVIEW.md) - Agent Layer 总览
- [AI_CODE_FACTORY_DEV_GUIDE_v2.0.md](./AI_CODE_FACTORY_DEV_GUIDE_v2.0.md) - 开发指南

---

**文档状态**: ✅ Production
**健康度**: P0 - 核心文档
**基准**: AI Code Factory v3.0 + SoT Freeze v2.6
