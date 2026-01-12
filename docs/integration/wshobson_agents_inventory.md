# wshobson/agents 资源清单

> **版本**: v1.0  
> **更新日期**: 2026-01-09  
> **来源**: [wshobson/agents](https://github.com/wshobson/agents)

## 概述

本文档列出从 wshobson/agents 项目中可整合的代理和技能资源。

## 代理资源（99个专业代理）

### 开发类代理（Development）

| 代理 ID | 名称 | 模型层级 | 状态 | 说明 |
|---------|------|---------|------|------|
| `backend-architect` | 后端架构师 | Tier 1 (Opus 4.5) | ✅ 已整合 | 后端代码生成、架构设计 |
| `frontend-developer` | 前端开发者 | Tier 2 (Sonnet 4.5) | ✅ 已整合 | 前端代码生成 |
| `full-stack-developer` | 全栈开发者 | Tier 1 (Opus 4.5) | ✅ 已整合 | 全栈代码生成 |
| `debugging-specialist` | 调试专家 | Tier 1 (Opus 4.5) | ✅ 已整合 | Bug 修复、调试 |

### 架构类代理（Architecture）

| 代理 ID | 名称 | 模型层级 | 状态 | 说明 |
|---------|------|---------|------|------|
| `system-architect` | 系统架构师 | Tier 1 (Opus 4.5) | ✅ 已整合 | 系统架构设计 |
| `database-architect` | 数据库架构师 | Tier 1 (Opus 4.5) | ✅ 已整合 | 数据库设计 |
| `api-architect` | API 架构师 | Tier 1 (Opus 4.5) | ✅ 已整合 | API 设计 |

### 质量类代理（Quality）

| 代理 ID | 名称 | 模型层级 | 状态 | 说明 |
|---------|------|---------|------|------|
| `code-reviewer` | 代码审查员 | Tier 1 (Opus 4.5) | ✅ 已整合 | 代码质量审查 |
| `test-automator` | 测试自动化专家 | Tier 2 (Sonnet 4.5) | ✅ 已整合 | 测试代码生成 |
| `performance-engineer` | 性能工程师 | Tier 1 (Opus 4.5) | ✅ 已整合 | 性能分析、优化 |

### 安全类代理（Security）

| 代理 ID | 名称 | 模型层级 | 状态 | 说明 |
|---------|------|---------|------|------|
| `security-auditor` | 安全审计员 | Tier 1 (Opus 4.5) | ✅ 已整合 | 安全审计 |
| `compliance-specialist` | 合规专家 | Tier 2 (Sonnet 4.5) | ✅ 已整合 | 合规检查 |

### 文档类代理（Documentation）

| 代理 ID | 名称 | 模型层级 | 状态 | 说明 |
|---------|------|---------|------|------|
| `documentation-engineer` | 文档工程师 | Tier 2 (Sonnet 4.5) | ✅ 已整合 | 文档生成 |
| `technical-writer` | 技术写作者 | Tier 2 (Sonnet 4.5) | ✅ 已整合 | 技术文档编写 |

## 技能资源（107个代理技能）

### 领域技能（Domain Skills）

| 技能 ID | 名称 | 模型层级 | 适配需求 | 状态 |
|---------|------|---------|---------|------|
| `backend-development` | 后端开发 | Tier 1 | ✅ 需要 | ✅ 已整合 |
| `frontend-development` | 前端开发 | Tier 2 | ✅ 需要 | ✅ 已整合 |
| `api-design` | API 设计 | Tier 1 | ✅ 需要 | ✅ 已整合 |
| `database-design` | 数据库设计 | Tier 1 | ✅ 需要 | ✅ 已整合 |
| `testing-patterns` | 测试模式 | Tier 2 | ❌ 不需要 | ✅ 已整合 |
| `security-patterns` | 安全模式 | Tier 1 | ✅ 需要 | ✅ 已整合 |
| `performance-optimization` | 性能优化 | Tier 1 | ✅ 需要 | ✅ 已整合 |

### 语言技能（Language Skills）

| 技能 ID | 名称 | 模型层级 | 适配需求 | 状态 |
|---------|------|---------|---------|------|
| `python` | Python | Tier 1 | ✅ 需要 | ✅ 已整合（增强） |
| `typescript` | TypeScript | Tier 2 | ✅ 需要 | ✅ 已整合（增强） |
| `javascript` | JavaScript | Tier 2 | ❌ 不需要 | ✅ 已整合 |
| `sql` | SQL | Tier 2 | ❌ 不需要 | ✅ 已整合 |

### 框架技能（Framework Skills）

| 技能 ID | 名称 | 模型层级 | 适配需求 | 状态 |
|---------|------|---------|---------|------|
| `fastapi` | FastAPI | Tier 1 | ✅ 需要 | ✅ 已整合 |
| `react` | React | Tier 2 | ✅ 需要 | ✅ 已整合 |
| `nextjs` | Next.js | Tier 2 | ✅ 需要 | ✅ 已整合 |
| `sqlalchemy` | SQLAlchemy | Tier 1 | ✅ 需要 | ✅ 已整合 |

## 整合状态

### 已整合资源

- **代理**: 14 个（优先整合的关键代理）
- **技能**: 15 个（核心开发技能）

### 待整合资源

- **代理**: 85 个（其他专业代理，按需整合）
- **技能**: 92 个（其他技能，按需整合）

## 使用说明

### 加载代理

```python
from agents.skills.skill_system.wshobson_agent_loader import WshobsonAgentLoader

loader = WshobsonAgentLoader()
agent = loader.load_agent("backend-architect")
print(f"Agent: {agent.name}, Model: {agent.model_tier}")
```

### 加载技能

```python
from agents.skills.skill_system.wshobson_skill_loader import WshobsonSkillLoader

loader = WshobsonSkillLoader()
skill = loader.load_skill("backend-development")
print(f"Skill: {skill.metadata.name}")
```

### 使用插件

```python
from agents.skills.skill_system.plugin_loader import PluginLoader

loader = PluginLoader()
plugin = loader.load_plugin("backend-development")
print(f"Plugin: {plugin.name}, Agents: {len(plugin.agents)}")
```

## 参考资源

- [wshobson/agents GitHub](https://github.com/wshobson/agents)
- [wshobson/agents 文档](https://github.com/wshobson/agents#readme)
- 整合文档: `docs/integration/WSHOBSON_AGENTS_INTEGRATION.md`

