# wshobson/agents 整合文档

> **版本**: v1.0  
> **更新日期**: 2026-01-09  
> **基准**: wshobson/agents + AI 广告代投系统需求

## 概述

本文档说明如何将 wshobson/agents 开源项目的代理和技能整合到 AI 代码工厂。

## 整合架构

```
┌─────────────────────────────────────────────────────────────┐
│              AI 代码工厂 + wshobson/agents                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              插件市场 (.claude-plugin/)                │ │
│  │  - marketplace.json (统一插件定义)                      │ │
│  │  - 支持 wshobson/agents 和 custom 来源                  │ │
│  └───────────────────────────────────────────────────────┘ │
│                        │                                    │
│                        ▼                                    │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              插件加载器 (PluginLoader)                 │ │
│  │  - 自动发现和加载插件                                   │ │
│  │  - 支持多来源（wshobson/agents + custom）               │ │
│  └───────────────────────────────────────────────────────┘ │
│                        │                                    │
│        ┌───────────────┴───────────────┐                   │
│        ▼                               ▼                    │
│  ┌──────────────┐            ┌──────────────┐              │
│  │ 代理加载器    │            │ 技能加载器    │              │
│  │ (AgentLoader)│            │ (SkillLoader)│              │
│  └──────────────┘            └──────────────┘              │
│        │                               │                    │
│        ▼                               ▼                    │
│  ┌──────────────┐            ┌──────────────┐              │
│  │ 代理适配器    │            │ 技能适配器    │              │
│  │ (AgentAdapter)│           │ (SkillAdapter)│             │
│  └──────────────┘            └──────────────┘              │
│        │                               │                    │
│        └───────────────┬───────────────┘                   │
│                        ▼                                    │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              模型策略 (ModelStrategy)                   │ │
│  │  - Tier 1: Opus 4.5 (关键任务)                         │ │
│  │  - Tier 2: Sonnet 4.5 (其他任务)                       │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 两层模型策略

### Tier 1: Opus 4.5（关键任务）

使用 Opus 4.5 的任务类型：

- **系统架构** - 架构设计、系统规划
- **代码生成** - 核心业务代码生成
- **代码审查** - 代码质量审查、安全审计
- **Bug 修复** - 复杂 Bug 修复、调试
- **性能优化** - 性能分析、优化建议

### Tier 2: Sonnet 4.5（其他任务）

使用 Sonnet 4.5 的任务类型：

- 文档生成
- 测试生成
- 代码格式化
- 简单重构
- 工具类任务

## 整合步骤

### Step 1: 准备资源

1. **克隆 wshobson/agents 仓库**
   ```bash
   git submodule add https://github.com/wshobson/agents.git external/wshobson-agents
   ```

2. **分析可用资源**
   - 查看 `external/wshobson-agents/.claude-plugin/plugins/` 目录
   - 识别可直接使用的代理和技能
   - 识别需要适配的资源

3. **创建资源清单**
   - 参考 `docs/integration/wshobson_agents_inventory.md`

### Step 2: 配置映射

1. **代理映射**
   - 编辑 `agents/skills/skill_system/agent_mapping.yaml`
   - 定义代理 ID 映射、模型层级、类别

2. **技能映射**
   - 编辑 `agents/skills/skill_system/skill_mapping.yaml`
   - 定义技能 ID 映射、模型层级、适配需求

3. **插件市场**
   - 编辑 `.claude-plugin/marketplace.json`
   - 定义插件、代理、技能的关联关系

### Step 3: 使用整合资源

#### 加载代理

```python
from agents.skills.skill_system.wshobson_agent_loader import WshobsonAgentLoader
from agents.skills.skill_system.agent_adapter import AgentAdapter
from pathlib import Path

# 初始化加载器
loader = WshobsonAgentLoader()

# 加载代理
agent = loader.load_agent("backend-architect")

# 适配代理到项目
adapter = AgentAdapter(project_root=Path("."))
adapted_agent = adapter.adapt_agent(agent)

print(f"Agent: {adapted_agent.name}")
print(f"Model: {adapted_agent.model_tier}")
print(f"Skills: {adapted_agent.skills}")
```

#### 加载技能

```python
from agents.skills.skill_system.wshobson_skill_loader import WshobsonSkillLoader
from agents.skills.skill_system.skill_adapter import SkillAdapter
from pathlib import Path

# 初始化加载器
loader = WshobsonSkillLoader()

# 加载技能
skill = loader.load_skill("backend-development")

# 适配技能到项目
adapter = SkillAdapter(project_root=Path("."))
adapted_skill = adapter.adapt_skill(skill)

print(f"Skill: {adapted_skill.metadata.name}")
print(f"Instructions: {adapted_skill.instructions[:100]}...")
```

#### 使用插件

```python
from agents.skills.skill_system.plugin_loader import PluginLoader

# 初始化插件加载器
loader = PluginLoader()

# 加载插件
plugin = loader.load_plugin("backend-development")

print(f"Plugin: {plugin.name}")
print(f"Agents: {[a.id for a in plugin._loaded_agents]}")
print(f"Skills: {[s.metadata.id for s in plugin._loaded_skills]}")
```

#### 使用工作流

```python
from agents.skills.code_factory.workflow.presets import WorkflowPresets

# 获取全栈开发工作流
workflow = WorkflowPresets.full_stack_development()

print(f"Workflow: {workflow['name']}")
print(f"Agents: {[a['id'] for a in workflow['agents']]}")
print(f"Pattern: {workflow['pattern']}")
```

#### 模型选择

```python
from agents.skills.skill_system.model_strategy import ModelStrategy

# 初始化模型策略
strategy = ModelStrategy()

# 根据任务类型选择模型
model = strategy.get_model_for_task("code-generation")
print(f"Model for code-generation: {model}")  # opus-4.5

# 根据代理 ID 选择模型
model = strategy.get_model_for_agent("backend-architect")
print(f"Model for backend-architect: {model}")  # opus-4.5
```

## 标准工作流

### 全栈功能开发

```python
workflow = WorkflowPresets.full_stack_development()
# 顺序执行：
# 1. system-architect (Opus 4.5) - 系统架构
# 2. backend-architect (Opus 4.5) - 后端开发
# 3. frontend-developer (Sonnet 4.5) - 前端开发
# 4. code-reviewer (Opus 4.5) - 代码审查
# 5. test-automator (Sonnet 4.5) - 测试生成
```

### 代码审查

```python
workflow = WorkflowPresets.code_review_workflow()
# 并行执行：
# 1. code-reviewer (Opus 4.5) - 代码质量审查
# 2. security-auditor (Opus 4.5) - 安全审计
# 3. performance-engineer (Opus 4.5) - 性能分析
```

### Bug 修复

```python
workflow = WorkflowPresets.bug_fixing_workflow()
# 顺序执行：
# 1. debugging-specialist (Opus 4.5) - 调试
# 2. code-reviewer (Opus 4.5) - 审查
# 3. test-automator (Sonnet 4.5) - 测试
```

## 适配说明

### 代理适配

代理适配器会：

1. **保留核心能力** - 保留 wshobson/agents 代理的核心功能
2. **注入 SoT 规范约束** - 添加项目 SoT 规范约束
3. **适配技术栈** - 适配到 FastAPI, SQLAlchemy 2.x, Next.js 16
4. **设置模型层级** - 根据任务类型设置模型层级

### 技能适配

技能适配器会：

1. **保留核心指令** - 保留 wshobson/agents 技能的核心指令
2. **注入 SoT 约束** - 添加 SoT 规范约束说明
3. **适配技术栈示例** - 将通用示例替换为项目特定示例
4. **添加项目特定规则** - 添加项目代码风格和规范

## 文件结构

```
agents/skills/skill_system/
├── wshobson_agent_loader.py    # wshobson/agents 代理加载器
├── wshobson_skill_loader.py    # wshobson/agents 技能加载器
├── agent_adapter.py             # 代理适配器
├── skill_adapter.py             # 技能适配器
├── plugin_loader.py             # 插件加载器（新增）
├── model_strategy.py            # 模型策略（新增）
├── agent_mapping.yaml           # 代理映射表（新增）
└── skill_mapping.yaml           # 技能映射表（新增）

.claude-plugin/
└── marketplace.json             # 插件市场（新增）

agents/skills/code_factory/workflow/
└── presets.py                   # 工作流预设（新增）

docs/integration/
├── wshobson_agents_inventory.md # 资源清单（新增）
└── WSHOBSON_AGENTS_INTEGRATION.md # 整合文档（本文件）

external/
└── wshobson-agents/             # wshobson/agents 仓库（submodule）
```

## 最佳实践

### 1. 优先使用已整合资源

优先使用已在 `agent_mapping.yaml` 和 `skill_mapping.yaml` 中定义的资源，避免重复配置。

### 2. 按需适配

不是所有资源都需要适配。优先整合可直接使用的资源，复杂适配分阶段进行。

### 3. 模型选择

- 关键任务（架构、代码生成、审查、Bug 修复、性能优化）使用 Opus 4.5
- 其他任务使用 Sonnet 4.5

### 4. 工作流设计

- 使用标准工作流预设（`WorkflowPresets`）
- 根据任务复杂度选择顺序或并行执行

## 故障排查

### 问题 1: 代理加载失败

**原因**: wshobson/agents 仓库路径不正确

**解决**: 检查 `external/wshobson-agents/` 目录是否存在，或指定正确的路径

```python
loader = WshobsonAgentLoader(wshobson_repo_path=Path("/path/to/wshobson-agents"))
```

### 问题 2: 技能找不到

**原因**: 技能路径不匹配

**解决**: 检查 `skill_mapping.yaml` 中的映射配置，或手动指定技能路径

### 问题 3: 模型选择错误

**原因**: 代理配置中缺少 `model_tier` 字段

**解决**: 在 `agent_mapping.yaml` 中为代理添加 `model_tier` 配置

## 参考资源

- [wshobson/agents GitHub](https://github.com/wshobson/agents)
- [资源清单](./wshobson_agents_inventory.md)
- [模型策略](../agents/skills/skill_system/model_strategy.py)
- [工作流预设](../agents/skills/code_factory/workflow/presets.py)

