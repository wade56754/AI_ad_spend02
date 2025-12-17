# Claude Agents 索引

> **版本**: v1.0
> **更新日期**: 2025-12-17
> **代理总数**: 3

---

## 代理清单

| 代理 | 用途 | 触发条件 |
|------|------|---------|
| [codex-loop](./codex-loop.md) | Codex 循环代理 | 代码审查/重构/生成的迭代优化 |
| [doc-architect](./doc-architect.md) | 文档架构代理 | 文档规划、结构设计 |
| [doc-fixer](./doc-fixer.md) | 文档修复代理 | 文档问题修正、一致性检查 |

---

## 代理详情

### 1. codex-loop (Codex 循环代理)

**文件**: `codex-loop.md` (8.3 KB)

**功能**:
- 代码审查 (Code Review)
- 代码重构 (Code Refactor)
- 代码生成 (Code Generation)
- 反复迭代优化

**使用场景**:
- 需要多轮优化的代码任务
- 复杂的重构工作
- 自动化代码质量提升

### 2. doc-architect (文档架构代理)

**文件**: `doc-architect.md` (7.5 KB)

**功能**:
- 文档架构规划
- 大纲设计与审查
- 文档结构优化

**使用场景**:
- 创建新的架构文档
- 重构现有文档结构
- 规划文档体系

### 3. doc-fixer (文档修复代理)

**文件**: `doc-fixer.md` (6.5 KB)

**功能**:
- 文档一致性检查
- 错误修正
- 格式规范化

**使用场景**:
- 文档质量审计
- 批量修复文档问题
- SoT 对齐检查

---

## 代理结构规范

每个代理文件应遵循以下结构：

```yaml
---
name: agent-name
type: agent
version: "1.0"
description: |
  代理描述和触发条件
capabilities:
  - capability_1
  - capability_2
---

# Agent Name

## 功能
...

## 工作流程
...

## 输入/输出
...
```

---

## 与 Skills 的关系

代理 (Agents) 和技能 (Skills) 的区别：

| 特性 | Agents | Skills |
|------|--------|--------|
| 定位 | 任务执行者 | 能力提供者 |
| 交互 | 对话式 | 调用式 |
| 状态 | 有状态 | 无状态 |
| 触发 | 自然语言匹配 | 显式调用 |

**协作模式**:
- Agent 调用 Skill 完成具体任务
- Skill 提供标准化的能力接口
- Agent 负责任务编排和状态管理

---

## 相关文件

- 技能索引: `../skills/INDEX.md`
- 命令索引: `../commands/README.md`
- 项目规则: `../PROJECT_RULES.md`
