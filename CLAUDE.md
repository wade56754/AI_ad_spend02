<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# AI 广告代投系统 - Claude Code 项目指令

> **文档版本**: v3.2 (基于 AI Code Factory v3.0 + SoT Freeze v2.6)
> **强制级别**: 🔴 自动加载，所有会话生效
> **架构模式**: 纯 SuperClaude Skill（已废弃 Python Agent）

## 🔒 强制规则 (Inviolable Rules)

### 1. 禁止修改 models/ 目录
- ❌ 除非明确允许，否则禁止直接修改 `backend/models/` 目录
- ✅ 任何改动必须：
  1. 先检查 `docs/2.sot/DATA_SCHEMA.md` v5.2
  2. 生成 Alembic 迁移脚本
  3. 经 DBA 审核

### 2. 遵循 SoT 裁判链
所有技术决策必须遵循以下优先级：
```
STATE_MACHINE.md v2.6 → DATA_SCHEMA.md v5.2 → BUSINESS_RULES.md v3.1
→ API_SOT.md v9.0 → ERROR_CODES_SOT.md v2.1 → AUTH_SPEC.md v2.0
→ LEDGER_SOT.md v1.1
```

### 3. 禁止重复定义状态枚举
- ❌ 错误: 在代码中定义 `DailyReportStatus = Enum("DRAFT", "PENDING", ...)`
- ✅ 正确: 使用 `STATE_MACHINE.md` v2.6 第8章的 **8 状态机**:
  ```
  raw_submitted → trend_pending → trend_ok/trend_flagged
  → trend_resolved → final_pending → final_confirmed → final_locked
  ```

### 4. 禁止自定义错误码
- ✅ 所有错误码必须来自 `ERROR_CODES_SOT.md` v2.1
- ✅ 使用格式: `{"code": "VAL-001", "message": "..."}`

### 5. 禁止绕过账本系统
- ❌ 禁止直接修改 `balance` 字段
- ✅ 必须通过 `ledger_entries` 表记录 (LEDGER_SOT.md v1.1)

## 📚 完整规则总纲

**详细规则**: 查阅 [.claude/PROJECT_RULES.md](.claude/PROJECT_RULES.md) v3.1
- SoT 裁判链完整版
- 8 状态机详细定义
- 反模式识别库
- Claude/SuperClaude 使用指南

## 🎯 每次开发前必做

1. 查询对应 SoT 文档（按裁判链优先级）
2. 找到相关业务规则编号 (如 BR-RPT-001)
3. 检查现有代码是否符合规则
4. 符合 → 继续开发 | 不符合 → 先修复或提 RFC

## ⚠️ 关键提醒

- **职责**: 执行裁判规则，而非创造规则
- **遇到未覆盖场景**: 提出 RFC，而非自行扩展
- **违规处理**: PR 自动拒绝 / 代码回滚

## 🏭 AI 代码工厂

本项目使用 **SuperClaude Skill** 进行代码生成，详见 [.claude/README.md](.claude/README.md)。

### 快速使用

**后端代码生成**:
```
使用 ai-ad-be-gen 实现充值审批 API
```

**前端代码生成**:
```
使用 ai-ad-fe-gen 实现充值列表页面
```

**SoT 合规检查**:
```
/sot-check backend/services/topup_service.py
```

### 核心 Skills

| Skill | 功能 |
|-------|------|
| `ai-ad-be-gen` | 后端代码生成 |
| `ai-ad-fe-gen` | 前端代码生成 |
| `ai-ad-test-gen` | 测试代码生成 |
| `ai-ad-doc-orchestrator` | 文档编排 |
| `ai-ad-spec-governor` | SoT 合规治理 |

> 完整指南: [.claude/SUPERCLAUDE_SETUP.md](.claude/SUPERCLAUDE_SETUP.md)

### 废弃组件

以下组件已废弃，不再使用：
- `agents/` 目录 (Python Agent)
- `agent_platform/` 目录
- `/agent` 和 `/orch` 命令

---

**生效日期**: 2025-12-07 | **基准**: AI Code Factory v3.0 + SoT Freeze v2.6