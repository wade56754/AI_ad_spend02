# Agent Layer 文档索引

> **版本**: v2.0
> **状态**: active
> **更新日期**: 2025-12-07
> **Owner**: wade

---

## SoT 链声明

本目录（`docs/6.agent-layer/`）是 ASDD 六层架构的 **Layer 6: Agent Layer**。

### 上游规范（Tier-3，本目录内但具有上游权威性）

> ⚠️ **重要**：以下两份文档虽然存放在本目录，但它们是 **Tier-3 平台规范**，对本层所有文档具有约束力。

| 文档 | 版本 | 角色 | 说明 |
|------|------|------|------|
| [**AI_CODE_FACTORY_DEV_GUIDE_v2.4.md**](./AI_CODE_FACTORY_DEV_GUIDE_v2.4.md) | v2.4 | **上游 SoT** | AI 代码工厂开发指南（六层架构、开发流程、Skill 规范） |
| [**SUPERCLAUDE_INTEGRATION_GUIDE_v2.2.md**](./SUPERCLAUDE_INTEGRATION_GUIDE_v2.2.md) | v2.2 | **上游 SoT** | SuperClaude 集成方案（模式定义、Skill/Agent 模板） |

### 业务 SoT（Tier-1，只读引用）

| 层级 | 文档 | 位置 | 说明 |
|------|------|------|------|
| **Tier-1** | docs/2.sot/*.md | `docs/2.sot/` | 业务 SoT（STATE_MACHINE, DATA_SCHEMA 等） |

### 本层文档定位

本层文档**只能在上游规范约束下**补充：
- Agent 角色与职责的详细定义
- Agent 通信协议与安全规范
- 工作流模板与使用指南
- 不能推翻或修改上游 SoT

---

## 文档分类与导航

### 规范文档（Specs）

| 文档 | 版本 | 用途 | 对应上游章节 |
|------|------|------|-------------|
| [SUBAGENT_PROTOCOL.md](./SUBAGENT_PROTOCOL.md) | v1.0 | Sub-Agent 通信协议（Request/Response 格式） | Dev Guide §9.3 |
| [AGENT_SECURITY_SPEC.md](./AGENT_SECURITY_SPEC.md) | v1.0 | Agent 安全规范（威胁模型、权限约束） | Dev Guide §2.3 |
| [AGENT_VERSIONING_RULES.md](./AGENT_VERSIONING_RULES.md) | v1.0 | Agent 版本管理（SemVer、兼容性矩阵） | - |
| [AGENT_ORCHESTRATION_PIPELINE.md](./AGENT_ORCHESTRATION_PIPELINE.md) | v1.0 | 编排流水线（Orchestrator 职责） | Dev Guide §9.6 |

### 流程指南（Guides）

| 文档 | 版本 | 用途 | 适用场景 |
|------|------|------|---------|
| [CLAUDE_CODE_AGENT_GUIDE.md](./CLAUDE_CODE_AGENT_GUIDE.md) | v1.0 | Claude Code Agent 快速参考 | 日常使用命令 |
| [AI_AD_CODE_FIXER_FLOW.md](./AI_AD_CODE_FIXER_FLOW.md) | v1.2.0 | 代码修复流程规范 | Backend 代码治理 |
| [CODEX_LOOP_SPEC.md](./CODEX_LOOP_SPEC.md) | v1.0 | Codex Loop 使用指南 | 代码审查/重构 |

### 冻结与审计

| 文档 | 版本 | 用途 |
|------|------|------|
| [AGENT_LAYER_FREEZE_MANIFEST_v1.0.md](./AGENT_LAYER_FREEZE_MANIFEST_v1.0.md) | v1.0 | 冻结清单与审计历史 |

### 归档文档（Archive）

> 以下文档内容已合并到上游规范，保留仅供历史参考。

| 文档 | 归档原因 |
|------|---------|
| [archive/AGENT_LAYER_OVERVIEW_v1.0.md](./archive/AGENT_LAYER_OVERVIEW_v1.0.md) | 与 Dev Guide §9.1-9.5 重复 |
| [archive/AGENT_SKILL_REGISTRY_v1.0.md](./archive/AGENT_SKILL_REGISTRY_v1.0.md) | 与 Dev Guide §10 重复 |
| [archive/AI_CODE_DEV_ORCHESTRATION_SOT_v1.0.md](./archive/AI_CODE_DEV_ORCHESTRATION_SOT_v1.0.md) | 与 Dev Guide §4-7, §11 重复 |

---

## 阅读路径推荐

### 普通开发者（日常使用 Agent 命令）

1. **快速开始**：[CLAUDE_CODE_AGENT_GUIDE.md](./CLAUDE_CODE_AGENT_GUIDE.md)
2. **详细流程**：上游 [AI_CODE_FACTORY_DEV_GUIDE_v2.4.md](./AI_CODE_FACTORY_DEV_GUIDE_v2.4.md) §10-11
3. **命令组合**：上游 [SUPERCLAUDE_INTEGRATION_GUIDE_v2.2.md](../3.dev-guides/SUPERCLAUDE_INTEGRATION_GUIDE_v2.2.md) §3

### Agent/Skill 开发者

1. **架构总览**：上游 Dev Guide §9（六层架构）
2. **通信协议**：[SUBAGENT_PROTOCOL.md](./SUBAGENT_PROTOCOL.md)
3. **安全规范**：[AGENT_SECURITY_SPEC.md](./AGENT_SECURITY_SPEC.md)
4. **Skill 模板**：上游 Integration Guide §4

### 维护者

1. **版本管理**：[AGENT_VERSIONING_RULES.md](./AGENT_VERSIONING_RULES.md)
2. **冻结清单**：[AGENT_LAYER_FREEZE_MANIFEST_v1.0.md](./AGENT_LAYER_FREEZE_MANIFEST_v1.0.md)

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| **v2.0** | 2025-12-07 | 重构：移出上游规范、新增 SoT 链声明、添加导航索引 |
| v1.0 | 2025-11-27 | 初始版本（无索引文件） |

---

**基准**: AI_CODE_FACTORY_DEV_GUIDE_v2.4, SUPERCLAUDE_INTEGRATION_GUIDE_v2.2, SoT Freeze v2.6
