# Claude Code 项目配置说明

## 📚 项目规则文档

本项目的所有开发规范已整理在以下文档中：

### 核心规则文档（必读）
- **[PROJECT_RULES.md](.claude/PROJECT_RULES.md)** - 项目规则总纲（本文档）
  - 包含所有强制执行的开发规范
  - AI自检清单
  - 快速参考指南

### SoT 真相源文档（开发时必须参考）
1. **[DATA_SCHEMA.md](../docs/core/DATA_SCHEMA.md)** - 数据库结构唯一真相
2. **[STATE_MACHINE.md](../docs/core/STATE_MACHINE.md)** - 状态机定义唯一真相
3. **[API_DEVELOPMENT_FLOW.md](../docs/core/API_DEVELOPMENT_FLOW.md)** - API开发流程唯一真相
4. **[AI_AD_SYSTEM_MAIN_DOCUMENT.md](../docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md)** - 系统实现规范唯一真相

## 🤖 如何让 Claude 使用这些规则

### 方法1：在对话开始时引用（推荐）
```
请严格遵循 .claude/PROJECT_RULES.md 中定义的所有规则进行开发。
```

### 方法2：在每次任务中明确引用
```
基于以下规范实现 XXX 功能：
1. 数据结构：参考 docs/core/DATA_SCHEMA.md
2. 状态流转：参考 docs/core/STATE_MACHINE.md
3. API规范：参考 docs/core/API_DEVELOPMENT_FLOW.md
```

### 方法3：使用项目记忆功能
在 Claude 对话中使用 `/project` 命令，将 PROJECT_RULES.md 的内容添加到项目记忆中。

## ⚠️ 重要提醒

所有代码生成和修改都必须：
1. ✅ 符合 PROJECT_RULES.md 中的五大不可违背规则
2. ✅ 通过 AI 自检清单的所有检查项
3. ✅ 以 docs/core 下的 SoT 文档为唯一依据

如果发现任何代码与规则冲突，**必须以规则为准进行修正**。

---

**最后更新**: 2024-11-18
