# AI 代码工厂 - 开发指南

> **版本**: v3.0 | **架构**: 纯 SuperClaude Skill | **更新**: 2025-12-07

## 🏭 概述

**AI 代码工厂**是本项目的自动化代码生成系统，基于 **SuperClaude Skill** 架构，通过对话式交互实现：

- 🔧 **后端代码生成** - FastAPI + SQLAlchemy + Pydantic
- 🎨 **前端代码生成** - Next.js + React + TypeScript
- 🧪 **测试代码生成** - pytest + vitest
- 📝 **文档自动审查** - SoT 一致性校验

---

## 📁 目录结构

```
.claude/
├── README.md              ← 你正在看的文档（主入口）
├── PROJECT_RULES.md       # 项目规则总纲
├── SUPERCLAUDE_SETUP.md   # Skill 使用详细指南
│
├── commands/              # Slash Commands（用户入口）
│   ├── doc-agent.md       # /doc-agent - 文档操作
│   ├── sot-check.md       # /sot-check - SoT 合规检查
│   └── openspec/          # OpenSpec 变更管理
│
├── skills/                # SuperClaude Skills（核心能力）
│   ├── README.md          # Skills 索引
│   ├── ai-ad-be-gen/      # 后端代码生成
│   ├── ai-ad-fe-gen/      # 前端代码生成
│   ├── ai-ad-test-gen/    # 测试代码生成
│   ├── ai-ad-doc-orchestrator/  # 文档编排
│   └── ...
│
└── agents/                # Claude Code Subagents
    ├── doc-architect.md
    ├── doc-fixer.md
    └── codex-loop.md
```

---

## 🚀 快速开始

### 1. 代码生成

**后端代码**（遵循 SoT 约束）：
```
使用 ai-ad-be-gen 实现充值审批 API，
目标文件: schemas/topup.py, services/topup_service.py, routers/topups.py
```

**前端代码**（遵循 UI 规范）：
```
使用 ai-ad-fe-gen 实现充值列表页面，
模块: topups
```

**测试代码**：
```
使用 ai-ad-test-gen 为 topup_service 生成单元测试
```

### 2. 文档审查

**SoT 合规检查**：
```
/sot-check backend/services/topup_service.py
```

**文档编排**：
```
使用 ai-ad-doc-orchestrator 生成 PROJECT.md 大纲
```

### 3. Slash Commands

| 命令 | 功能 |
|------|------|
| `/sot-check <file>` | 检查代码是否符合 SoT |
| `/doc-agent <action>` | 文档操作 |
| `/openspec:proposal` | 创建变更提案 |
| `/openspec:apply` | 应用已批准的变更 |

---

## 🎯 核心 Skills

| Skill | 功能 | 使用场景 |
|-------|------|----------|
| **ai-ad-be-gen** | 后端代码生成 | 实现 API、Service、Schema |
| **ai-ad-fe-gen** | 前端代码生成 | 实现页面、组件、hooks |
| **ai-ad-test-gen** | 测试代码生成 | 生成单元测试、集成测试 |
| **ai-ad-doc-orchestrator** | 文档编排 | 生成/审查项目文档 |
| **ai-ad-spec-governor** | SoT 治理 | 检查代码与 SoT 一致性 |

> 📚 完整 Skills 列表见 [skills/README.md](skills/README.md)

---

## 📋 SoT 真相源文档

所有代码生成必须遵循以下 SoT 文档（裁判链优先级从高到低）：

| 优先级 | 文档 | 职责 |
|--------|------|------|
| 1 | `STATE_MACHINE.md` v2.6 | 状态枚举定义 |
| 2 | `DATA_SCHEMA.md` v5.2 | 数据库字段定义 |
| 3 | `BUSINESS_RULES.md` v3.1 | 业务规则 (BR-*) |
| 4 | `API_SOT.md` v9.0 | API 契约 |
| 5 | `ERROR_CODES_SOT.md` v2.1 | 错误码 |
| 6 | `AUTH_SPEC.md` v2.0 | 认证授权 |
| 7 | `LEDGER_SOT.md` v1.1 | 账本规则 |

> 文档路径: `docs/2.sot/`

---

## ⚠️ 强制规则

### 代码生成边界

| 区域 | 后端 | 前端 |
|------|------|------|
| ✅ 可写 | `schemas/`, `services/`, `routers/` | `src/modules/`, `src/lib/api/` |
| ❌ 禁止 | `models/`, `migrations/` | `node_modules/`, `.next/` |

### 必须遵守

1. **状态枚举** - 必须使用 `STATE_MACHINE.md` 定义
2. **错误码** - 必须使用 `ERROR_CODES_SOT.md` 定义
3. **字段类型** - 必须与 `DATA_SCHEMA.md` 一致
4. **SoT 注释** - 生成的代码必须标注 SoT 引用

---

## 🔧 决策流程

```
收到需求
    │
    ▼
识别业务域 → 查询对应 SoT 文档
    │
    ▼
找到规则编号 (如 BR-RPT-001)
    │
    ▼
检查现有代码是否符合
    │
    ├── 符合 → 继续开发
    │
    └── 不符合 → 先修复或提 RFC
```

---

## 📚 相关文档

- **项目规则总纲**: [PROJECT_RULES.md](PROJECT_RULES.md)
- **Skill 使用指南**: [SUPERCLAUDE_SETUP.md](SUPERCLAUDE_SETUP.md)
- **Skills 索引**: [skills/README.md](skills/README.md)
- **项目指令**: [../CLAUDE.md](../CLAUDE.md)

---

## 🗑️ 废弃说明

以下组件已废弃，不再维护：

| 废弃组件 | 替代方案 |
|----------|----------|
| `agents/` (Python Agent) | SuperClaude Skills |
| `agent_platform/` | SuperClaude Skills |
| `/agent` 命令 | 直接使用 Skill |
| `/orch` 命令 | `ai-ad-doc-orchestrator` |

---

**基准**: SoT Freeze v2.6 + AI Code Factory v3.0
