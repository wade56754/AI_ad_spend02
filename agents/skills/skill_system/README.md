# 技能系统 (Skill System)

> **版本**: v1.0
> **基准**: AI_CODING_BEST_PRACTICES.md BP-01

## 概述

技能系统基于 [wshobson/agents](https://github.com/wshobson/agents) 的渐进式披露架构设计，支持三层加载策略以优化 Token 消耗。

## 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      渐进式披露架构                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Layer 1: 元数据 (~50 tokens)                                    │
│  ├── 名称 (name)                                                 │
│  ├── 触发词 (triggers)                                           │
│  ├── 关键词 (keywords)                                           │
│  └── SoT 引用 (sot_references)                                   │
│                                                                 │
│  Layer 2: 核心指令 (~200 tokens)                                  │
│  ├── 代码模板                                                    │
│  ├── 约束规则                                                    │
│  └── 示例片段                                                    │
│                                                                 │
│  Layer 3: 完整资源 (~500+ tokens)                                 │
│  ├── 详细文档                                                    │
│  ├── 边缘案例                                                    │
│  └── 完整示例                                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 目录结构

```
agents/skills/
├── skill_system/           # 技能系统核心
│   ├── __init__.py
│   ├── base.py             # Skill, SkillMetadata, SkillRegistry
│   ├── loader.py           # SkillLoader
│   └── README.md
│
├── domain_skills/          # 领域技能
│   ├── daily_report/
│   │   ├── skill.yaml      # Layer 1: 元数据
│   │   ├── instructions.md # Layer 2: 核心指令
│   │   └── resources/      # Layer 3: 完整资源
│   ├── topup/
│   └── ledger/
│
└── language_skills/        # 语言技能
    ├── python/
    └── typescript/
```

## 使用方法

### 加载所有技能

```python
from agents.skills.skill_system import SkillLoader

loader = SkillLoader()
registry = loader.load_all()

print(f"已加载 {len(registry)} 个技能")
```

### 根据查询查找技能

```python
# 查找日报相关技能
skills = loader.find_skill("日报状态")
for skill in skills:
    print(f"匹配技能: {skill.metadata.name}")
    print(f"  指令: {skill.instructions[:100]}...")
```

### 按需加载资源

```python
skill = loader.get_skill("daily-report")

# Layer 1: 元数据 (已加载)
print(skill.metadata.triggers)

# Layer 2: 核心指令 (激活时加载)
print(skill.instructions)

# Layer 3: 完整资源 (按需加载)
state_machine = skill.get_resource("state_machine")
```

### Token 估算

```python
skill = loader.get_skill("daily-report")
estimates = skill.get_token_estimate()

print(f"Layer 1: {estimates['layer1_metadata']} tokens")
print(f"Layer 2: {estimates['layer2_instructions']} tokens")
print(f"Layer 3: {estimates['layer3_resources']} tokens")
```

## 创建新技能

### 1. 创建目录结构

```bash
mkdir -p agents/skills/domain_skills/my_skill/resources
```

### 2. 创建 skill.yaml (Layer 1)

```yaml
id: my-skill
name: 我的技能
version: "1.0"
category: domain

triggers:
  - "触发词1"
  - "触发词2"

keywords:
  - "关键词1"
  - "关键词2"

sot_references:
  - "STATE_MACHINE.md#xxx"
  - "DATA_SCHEMA.md#xxx"

instructions: "./instructions.md"
resources:
  - "./resources/example.md"
```

### 3. 创建 instructions.md (Layer 2)

核心使用指南，包含代码模板和关键约束。

### 4. 创建 resources/ (Layer 3)

详细文档和边缘案例。

## 与代码工厂集成

技能系统可与六阶段流水线集成：

```
SEARCH 阶段 → 查询技能注册表
SELECT 阶段 → 加载匹配技能的 Layer 2
ADAPT 阶段  → 按需加载 Layer 3 资源
```

## 相关文档

- [AI_CODING_BEST_PRACTICES.md](../../../docs/guides/AI_CODING_BEST_PRACTICES.md)
- [代码工厂 README](../code_factory/README.md)
