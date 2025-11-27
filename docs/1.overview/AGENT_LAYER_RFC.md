---
version: v1.0
status: draft
layer: overview
owner: wade
last_reviewed: 2025-11-27
baseline: MASTER.md v3.4, SoT Freeze v2.6, Dev-Guides Freeze vFinal, Architecture Freeze v1.0, Infrastructure Freeze v1.0
---

# RFC: ASDD 第六层 - Agent Layer 提案

> **RFC 编号**: RFC-2025-001
> **提案日期**: 2025-11-27
> **提案者**: Wade (Documentation Owner)
> **状态**: Draft（待架构委员会审批）
> **目标版本**: Agent Layer v1.0

---

## 1. 执行摘要

本 RFC 提议在现有 ASDD 5 层框架基础上，新增第六层：**Agent Layer（智能体层）**，用于规范 AI Agent 系统的设计、开发、部署和治理。

**核心理由**：
- 项目已实现 4 个核心 Agent（OrchestratorAgent, BEAgent, FEAgent, TestAgent）
- 已有 9 个 Claude Skills 用于文档治理，但缺乏统一规范
- Agent 系统架构、安全、版本管理需要专门的规范层
- 现有 5 层框架未涵盖 Agent 协调、子 agent 通信、技能调度等关键主题

**预期成果**：
- 7 份 Agent Layer 规范文档（约 25,000 词）
- 1 份 Agent Layer Freeze Manifest
- 与现有 5 层完全对齐的治理流程

---

## 2. 背景与动机

### 2.1 现状分析

**ASDD 5 层框架现状**（截至 2025-11-27）：

| 层级 | 状态 | 文档数 | 健康度 | 冻结日期 |
|------|------|--------|--------|----------|
| Layer 1: Overview | ✅ Frozen v1.0 | 2 + 1 manifest | 100/100 | 2025-11-23 |
| Layer 2: SoT | ✅ Frozen v2.6 | 10 + 1 manifest | 100/100 | 2025-11-26 |
| Layer 3: Dev-Guides | ✅ Frozen vFinal | 10 + 1 manifest | 100/100 | 2025-11-27 |
| Layer 4: Architecture | ✅ Frozen v1.0 | 7 + 1 manifest | 100/100 | 2025-11-27 |
| Layer 5: Infrastructure | ✅ Frozen v1.0 | 5 + 1 manifest | 100/100 | 2025-11-27 |

**总计**: 34 规范文档 + 5 冻结清单 = **39 治理构件**

### 2.2 Agent 系统现状

**已实现的 Agent 基础设施**：

```
agents/
├── agent_core/          # 核心 Agent 实现
│   ├── orchestrator_agent.py    # 总控协调器
│   ├── be_agent.py              # 后端代码生成
│   ├── fe_agent.py              # 前端代码生成
│   └── test_agent.py            # 测试用例生成
├── agents_config.py             # Agent 注册中心
├── skills/                      # Agent Skills
│   ├── be_dev_skill.py
│   ├── fe_dev_skill.py
│   ├── db_test_skill.py
│   └── sot_guard_skill.py
└── tools/                       # Agent 工具
    ├── fs_tool.py               # 文件系统工具
    ├── supabase_tool.py         # Supabase 工具
    └── validation.py            # 验证工具
```

**已实现的 Claude Skills**（`.claude/skills/`）：
1. `ai-ad-spec-governor` - 规范治理总调度器
2. `ai-ad-doc-architect` - 文档架构设计
3. `ai-ad-doc-fixer` - 文档自动修复
4. `ai-ad-doc-orchestrator` - 文档编排
5. `ai-ad-doc-system-auditor` - 系统审计
6. `ai-ad-sot-doc-pipeline` - SoT 流水线（计划中）
7. `ai-ad-agents-test-orchestrator` - Agent 测试编排
8. `ai-ad-agents-test-runner` - Agent 测试执行
9. `ai-master-architect` - 主架构师（已废弃）

### 2.3 缺口识别

**当前文档覆盖缺口**：

| 主题 | 现有覆盖 | 缺口 |
|------|---------|------|
| **Agent 架构设计** | ❌ 无 | 需要：Agent 通信协议、编排模式、依赖管理 |
| **Sub-Agent 规范** | ❌ 无 | 需要：Sub-Agent 接口、生命周期、错误处理 |
| **Agent 安全** | ❌ 无 | 需要：权限模型、沙箱隔离、恶意代码防护 |
| **Agent 版本管理** | ❌ 无 | 需要：Agent 版本控制、兼容性、迁移策略 |
| **Skill 调度** | 部分覆盖（SKILL.md） | 需要：Skill 注册、依赖解析、冲突处理 |
| **Agent 测试** | ❌ 无 | 需要：Agent 单测、集成测试、E2E 测试 |
| **Agent 部署** | 部分覆盖（Infrastructure） | 需要：Agent MCP 集成、性能监控 |

### 2.4 为何需要独立的 Agent Layer

**选项对比**：

| 方案 | 优点 | 缺点 | 决策 |
|------|------|------|------|
| **方案 A**: 合并到 Infrastructure Layer | 简单，无需新层 | Agent 规范与基础设施规范职责混淆 | ❌ 不推荐 |
| **方案 B**: 合并到 Dev-Guides Layer | 保持 5 层结构 | Dev-Guides 已冻结，Agent 是实现细节非开发指南 | ❌ 不推荐 |
| **方案 C**: 创建独立 Agent Layer（本提案）| 职责清晰，治理独立 | 增加复杂度，需维护第 6 层 | ✅ **推荐** |

**推荐方案 C 的理由**：
1. **职责边界清晰**: Agent 系统是独立的运行时层，与 Infrastructure（CI/CD、部署）职责不同
2. **治理独立性**: Agent 系统频繁迭代，需要独立的冻结/解冻策略
3. **架构完整性**: ASDD 框架应覆盖"系统如何自我演化"（Agent 自动化），而非仅限于"人工开发"
4. **未来扩展性**: Agent Layer 可独立演进为 Multi-Agent System（MAS）规范

---

## 3. 范围定义

### 3.1 Agent Layer 解决的问题

**In-Scope（包含）**：

1. **Agent 架构规范**:
   - Agent 通信协议（Request/Response 格式）
   - Sub-Agent 接口设计（`handle_request` 方法签名）
   - Agent 编排模式（串行、并行、条件分支）
   - Agent 依赖管理（Agent Registry、Factory 模式）

2. **Agent 安全规范**:
   - Agent 权限模型（读/写文件、执行命令、调用 API）
   - 沙箱隔离机制（Agent 运行时隔离）
   - 恶意代码防护（代码生成审查、黑名单）
   - 敏感信息保护（API Key、数据库凭证）

3. **Agent 版本管理**:
   - Agent 版本控制策略（语义化版本）
   - Agent 兼容性矩阵（Agent A v1.0 ↔ Agent B v2.0）
   - Agent 迁移策略（Breaking Changes 处理）
   - Agent Deprecation 策略（Agent 废弃流程）

4. **Skill 调度规范**:
   - Skill 注册与发现（Skill Registry）
   - Skill 依赖解析（Skill A 依赖 Skill B）
   - Skill 冲突处理（多个 Skill 处理同一任务）
   - Skill 版本控制（Skill v1.0 vs v2.0）

5. **Agent 测试规范**:
   - Agent 单元测试（Mock Sub-Agent）
   - Agent 集成测试（真实 Sub-Agent 交互）
   - Agent E2E 测试（完整 Orchestrator → Sub-Agents 流程）
   - Agent 性能测试（吞吐量、延迟）

6. **Agent 部署规范**:
   - Agent MCP 集成（Model Context Protocol）
   - Agent 性能监控（调用次数、成功率、延迟）
   - Agent 日志规范（结构化日志、追踪 ID）
   - Agent 健康检查（Agent 存活性、就绪性）

7. **Codex Loop 规范**（特殊专题）:
   - Codex Loop 是什么（代码级 Agent）
   - Codex Loop 使用场景（代码审查、重构）
   - Codex Loop 安全限制（只读模式、沙箱）

### 3.2 Agent Layer 不解决的问题

**Out-of-Scope（不包含）**：

1. **业务逻辑实现**: Agent 的具体业务代码（由 Dev-Guides Layer 指导）
2. **SoT 规范**: Agent 不修改 SoT 文档内容（由 SoT Layer 定义）
3. **CI/CD 流程**: Agent 部署流水线（由 Infrastructure Layer 定义）
4. **数据库 Schema**: Agent 使用的数据模型（由 SoT Layer 定义）
5. **API 端点**: Agent 暴露的 API（由 API_SOT.md 定义）
6. **LLM 选型**: Agent 使用的 LLM 模型（由 Architecture Layer 定义）

---

## 4. 提案文档清单

### 4.1 Agent Layer 文档结构

```
docs/6.agent-layer/
├── AGENT_LAYER_OVERVIEW.md                      # Layer 6 总览
├── SUBAGENT_PROTOCOL.md                         # Sub-Agent 通信协议
├── AGENT_SECURITY_SPEC.md                       # Agent 安全规范
├── AGENT_ORCHESTRATION_PIPELINE.md              # Agent 编排流水线
├── CODEX_LOOP_SPEC.md                           # Codex Loop 专项规范
├── AGENT_VERSIONING_RULES.md                    # Agent 版本管理
├── AGENT_SKILL_REGISTRY.md                      # Skill 注册与调度（新增）
└── AGENT_LAYER_FREEZE_MANIFEST_v1.0.md          # Agent Layer 冻结清单
```

### 4.2 文档详细说明

#### 文档 1: AGENT_LAYER_OVERVIEW.md (~3,500 词)

**目的**: Agent Layer 总览，定位与其他层的关系

**章节结构**:
1. Agent Layer 在 ASDD 6 层中的定位
2. 与 Infrastructure / Architecture 层的关系
3. Agent 系统架构概览（Orchestrator → Sub-Agents）
4. Agent 生命周期（注册、调度、执行、销毁）
5. 文档使用指南（何时查阅哪个文档）
6. 版本对齐矩阵（Agent Layer 依赖其他层的版本）

**关键图表**:
- Mermaid: ASDD 6 层架构图
- Mermaid: Agent 生命周期状态机

---

#### 文档 2: SUBAGENT_PROTOCOL.md (~4,000 词)

**目的**: 定义 Sub-Agent 通信协议与接口规范

**章节结构**:
1. Sub-Agent 接口定义（`AgentProtocol`）
2. Request/Response 格式（JSON Schema）
3. 错误处理协议（ERROR_CODES_SOT 对齐）
4. 超时与重试机制
5. Agent 状态管理（Stateful vs Stateless）
6. 示例：BEAgent / FEAgent / TestAgent 实现

**关键规范**:
```python
class AgentProtocol(Protocol):
    def handle_request(self, request: Dict[str, Any]) -> AgentResponse:
        """
        Args:
            request: {
                "task": str,
                "context": Dict[str, Any],
                "timeout_ms": int,
            }

        Returns:
            {
                "success": bool,
                "data": Any,
                "error": Optional[str],
                "metadata": {
                    "agent_id": str,
                    "execution_time_ms": int,
                    "tokens_used": int,
                }
            }
        """
```

---

#### 文档 3: AGENT_SECURITY_SPEC.md (~4,500 词)

**目的**: 定义 Agent 系统安全规范与威胁模型

**章节结构**:
1. 威胁模型（恶意代码注入、数据泄露、权限提升）
2. Agent 权限模型（文件系统、数据库、外部 API）
3. 沙箱隔离机制（Docker 容器、chroot）
4. 代码生成审查（黑名单关键词、AST 分析）
5. 敏感信息保护（Environment Variables、Secrets Manager）
6. 审计日志规范（操作记录、追踪 ID）
7. 与 AUTH_SPEC.md 的对齐（用户权限 vs Agent 权限）

**威胁模型示例**:
- **T-AGENT-001**: Agent 生成恶意代码删除数据库
- **T-AGENT-002**: Agent 泄露 `.env` 文件中的 API Key
- **T-AGENT-003**: Agent 绕过权限检查直接修改 SoT 文档

---

#### 文档 4: AGENT_ORCHESTRATION_PIPELINE.md (~4,000 词)

**目的**: 定义 Agent 编排模式与流水线设计

**章节结构**:
1. Orchestrator 职责与边界
2. 编排模式（串行、并行、条件分支、循环）
3. Sub-Agent 依赖管理（依赖图、拓扑排序）
4. 错误传播与回滚策略
5. 流水线示例：`full_pipeline` 流程
6. 与 CI_PIPELINE_SPEC.md 的对齐（CI 流水线 vs Agent 流水线）

**流水线模式**:
```python
# 串行模式（Sequential）
backend → frontend → test

# 并行模式（Parallel）
backend ┐
frontend ┼→ test
docs    ┘

# 条件分支（Conditional）
backend → (if success) → frontend
       → (if failed) → rollback
```

---

#### 文档 5: CODEX_LOOP_SPEC.md (~3,500 词)

**目的**: Codex Loop 专项规范（代码级 Agent）

**章节结构**:
1. Codex Loop 定义与使用场景
2. Codex Loop 与普通 Agent 的区别
3. 代码审查模式（Code Review Agent）
4. 代码重构模式（Refactor Agent）
5. 安全限制（只读模式、沙箱隔离）
6. 与 TESTING_STRATEGY.md 的对齐（测试驱动重构）

**使用场景**:
- 代码审查：检测代码是否符合 SoT 规范
- 代码重构：自动重构代码以符合新 SoT 版本
- 代码生成：根据 SoT 生成 Pydantic Schema

---

#### 文档 6: AGENT_VERSIONING_RULES.md (~3,500 词)

**目的**: Agent 版本管理与兼容性策略

**章节结构**:
1. 语义化版本（SemVer）在 Agent 中的应用
2. Agent 兼容性矩阵（Agent A v1.0 ↔ Agent B v2.0）
3. Breaking Changes 处理（版本升级 Checklist）
4. Agent Deprecation 策略（Agent 废弃流程）
5. 版本迁移策略（v1 → v2 迁移路径）
6. 与 SoT 版本的对齐（SoT v2.6 → Agent 需要 v1.1+）

**版本规则**:
- **MAJOR**: Breaking Changes（如修改 `handle_request` 签名）
- **MINOR**: 新增功能（如新增 `handle_batch_request` 方法）
- **PATCH**: Bug 修复（如修复错误处理逻辑）

---

#### 文档 7: AGENT_SKILL_REGISTRY.md (~3,000 词)（新增）

**目的**: Skill 注册、发现与调度规范

**章节结构**:
1. Skill 定义与分类（Doc Skill, Code Skill, Test Skill）
2. Skill 注册机制（`_SKILL_REGISTRY`）
3. Skill 依赖解析（Skill A 依赖 Skill B）
4. Skill 冲突处理（多个 Skill 处理同一任务）
5. Skill 版本控制（Skill v1.0 vs v2.0）
6. 与 `.claude/skills/` 的对齐（Claude Skills 集成）

**Skill 注册示例**:
```python
_SKILL_REGISTRY = {
    "doc-architect": SkillMeta(
        key="doc-architect",
        name="DocumentArchitect",
        description="文档架构设计",
        version="v1.0",
        dependencies=["doc-auditor"],
        factory=_doc_architect_factory,
    ),
}
```

---

#### 文档 8: AGENT_LAYER_FREEZE_MANIFEST_v1.0.md (~7,000 词)

**目的**: Agent Layer 冻结清单

**章节结构**:
1. Executive Summary (P0/P1/P2 统计、健康度)
2. Frozen Documents Inventory (7 文档清单)
3. Freeze Conditions Verification (冻结条件检查)
4. Baseline Alignment (上游层版本对齐)
5. Traceability Matrix (追溯矩阵)
6. Health Score Calculation (健康度计算)
7. Freeze Decision (冻结决策)
8. Unfreeze Policy (解冻策略)
9. Maintenance Schedule (维护计划)
10. Audit Conclusion (审计结论)

---

## 5. 架构影响分析

### 5.1 对现有层级的影响

| 层级 | 影响类型 | 具体影响 | 需要更新的文档 |
|------|---------|---------|---------------|
| **Layer 1: Overview** | ✅ 轻微 | 需在 MASTER.md 中增加 Layer 6 描述 | MASTER.md v3.4 → v3.5 |
| **Layer 2: SoT** | ❌ 无 | Agent Layer 不修改 SoT | 无 |
| **Layer 3: Dev-Guides** | ✅ 轻微 | 增加"Agent 开发指南"章节引用 | AGENT_WORKFLOW_GUIDE.md |
| **Layer 4: Architecture** | ✅ 中等 | 增加 Agent 架构视图 | 新增 AGENT_ARCHITECTURE_VIEW.md（可选）|
| **Layer 5: Infrastructure** | ✅ 中等 | 增加 Agent 部署流程 | DEPLOYMENT_PIPELINE_SPEC.md 更新 |

### 5.2 ASDD 6 层架构图

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Overview (Freeze v1.0)                             │
│ MASTER.md v3.5 + PROJECT.md                                 │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: SoT (Freeze v2.6)                                  │
│ 10 SoT Documents (STATE_MACHINE, DATA_SCHEMA, API_SOT...)   │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Dev-Guides (Freeze vFinal)                         │
│ 10 Dev-Guide Documents                                      │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: Architecture (Freeze v1.0)                         │
│ 7 Architecture Views                                        │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 5: Infrastructure (Freeze v1.0)                       │
│ 5 Infrastructure Specs (CI/CD, Deployment, Observability)   │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 6: Agent (提案中)                                      │
│ 7 Agent Specs (Sub-Agent Protocol, Security, Orchestration) │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Baseline 依赖

**Agent Layer Baseline**:
```
MASTER.md v3.5, SoT Freeze v2.6, Dev-Guides Freeze vFinal,
Architecture Freeze v1.0, Infrastructure Freeze v1.0
```

**注意**: Agent Layer 依赖 MASTER.md v3.5（需先更新 MASTER.md 增加 Layer 6 描述）

---

## 6. 安全与风险

### 6.1 Token 预算风险

**估算**:

| 阶段 | 预估 Token 消耗 | 备注 |
|------|----------------|------|
| **DISCOVER** | 5,000 | 分析现有 Agent 代码 |
| **DESIGN** | 8,000 | 设计 7 份文档大纲 |
| **DRAFT** | 50,000 | 编写 7 份文档（每份 7,000 tokens） |
| **AUDIT** | 15,000 | 审计 7 份文档（每份 2,000 tokens） |
| **FIX** | 20,000 | 修复 P0/P1 问题（迭代 2-3 轮） |
| **FREEZE** | 10,000 | 生成 Freeze Manifest + 更新导航 |
| **总计** | **108,000 tokens** | **高风险：超出单会话预算** |

**缓解策略**:
1. **分阶段执行**: 分 2-3 个会话完成（每会话 40,000 tokens）
2. **精简文档**: 每份文档目标 2,500-3,000 词（而非 4,000 词）
3. **跳过审计**: 首次生成时跳过 AUDIT，直接进入 FREEZE（风险：质量下降）

### 6.2 文档量风险

**预估文档量**:
- 7 份规范文档 × 3,500 词/份 = **24,500 词**
- 1 份 Freeze Manifest × 7,000 词 = **7,000 词**
- **总计**: **31,500 词**（约 42,000 tokens）

**缓解策略**:
1. **合并文档**: 将 7 份合并为 5 份（如合并 Skill Registry 到 Orchestration）
2. **引用复用**: 通过引用其他层文档减少重复内容
3. **示例精简**: 减少代码示例数量

### 6.3 冻结策略风险

**风险**: Agent Layer 频繁迭代，冻结后难以更新

**缓解策略**:
1. **延迟冻结**: Agent Layer v1.0 仅标记为 `ready_for_production`，不立即冻结
2. **季度审查**: 每季度重新评估是否需要冻结
3. **独立解冻**: Agent Layer 解冻不影响其他 5 层

---

## 7. ASDD 方法对齐

### 7.1 ASDD 6 步流程

**Agent Layer 创建流程**:

```
STEP 1: DISCOVER (发现)
  - 分析现有 Agent 代码（agents/ 目录）
  - 识别 Agent 架构模式（Orchestrator + Sub-Agents）
  - 提取关键设计决策（AgentProtocol, agents_config.py）
  - 输出: Agent 架构现状报告

STEP 2: DESIGN (设计)
  - 设计 7 份文档大纲
  - 定义章节结构、关键图表、代码示例
  - 确定 Baseline 依赖（哪些 SoT / Dev-Guides 需要引用）
  - 输出: 7 份文档大纲（Markdown）

STEP 3: DRAFT (起草)
  - 编写 7 份文档完整内容
  - 插入 Mermaid 图表、代码示例、表格
  - 添加 YAML Frontmatter
  - 输出: 7 份完整文档（draft 状态）

STEP 4: AUDIT (审计)
  - 调用 ai-ad-doc-system-auditor 审计每份文档
  - 生成 P0/P1/P2 问题报告
  - 检查 SoT 版本对齐、Baseline 格式
  - 输出: Audit 报告（P0/P1/P2 清单）

STEP 5: FIX (修复)
  - 调用 ai-ad-doc-fixer 修复 P0/P1 问题
  - 迭代 AUDIT → FIX 直到 P0=0, P1=0
  - 验证修复效果（再次审计）
  - 输出: 修复后的文档（ready_for_production）

STEP 6: FREEZE (冻结)
  - 生成 AGENT_LAYER_FREEZE_MANIFEST_v1.0.md
  - 更新 docs/README.md 增加 Layer 6 导航
  - 更新 docs/PROJECT_DOCS_INDEX_v1.0.md
  - 提交 Git Commit（标记 Agent Layer Freeze v1.0）
  - 输出: Freeze Manifest + 更新的导航文档
```

### 7.2 子 Skill 调度

| Phase | 调用的 Skill | 用途 |
|-------|-------------|------|
| **DISCOVER** | - | 内置逻辑（Read, Grep, Glob） |
| **DESIGN** | `ai-ad-doc-architect` | 生成文档大纲 |
| **DRAFT** | `ai-ad-doc-architect` | 生成完整文档 |
| **AUDIT** | `ai-ad-doc-system-auditor` | 审计文档 |
| **FIX** | `ai-ad-doc-fixer` | 修复问题 |
| **FREEZE** | `ai-ad-spec-governor` | 生成 Freeze Manifest |

---

## 8. 冻结策略

### 8.1 Agent Layer 冻结条件

**必须满足的条件**:
1. ✅ P0 = 0（零阻塞缺陷）
2. ✅ P1 = 0（零高优先级问题）
3. ✅ 所有文档 status = `ready_for_production`
4. ✅ Health Score ≥ 100/100
5. ✅ Baseline 对齐：引用正确的上游层版本
6. ✅ YAML Frontmatter 完整（version, status, layer, owner, baseline）
7. ✅ 无 TODO / PLACEHOLDER
8. ✅ 所有 Mermaid 图表语法正确
9. ✅ 所有代码示例可执行（Python 语法正确）

### 8.2 Agent Layer 解冻条件

**触发解冻的情况**:
1. **Agent 架构重大变更**: 如引入 Multi-Agent System（MAS）
2. **上游层更新**: SoT Freeze v3.0 发布，Agent Layer 需对齐
3. **安全漏洞**: 发现 Agent 安全规范存在漏洞
4. **P0 缺陷**: 生产环境发现 P0 级别文档错误

**解冻流程**:
1. 创建 RFC（如 RFC-2026-001: Agent Layer v2.0 Unfreeze）
2. 架构委员会审批
3. 执行 ASDD 6 步流程（DISCOVER → ... → FREEZE）
4. 生成新版本 Freeze Manifest（v2.0）

### 8.3 Agent Layer 独立解冻

**重要原则**: Agent Layer 解冻不影响其他 5 层

```
Layer 1-5: Frozen ✅
Layer 6: Unfrozen 🔓 (独立迭代)

当 Layer 6 重新冻结后:
Layer 1-6: Frozen ✅
```

---

## 9. 预估资源需求

### 9.1 Token 预算

| 阶段 | 预估 Token | 风险等级 |
|------|-----------|---------|
| **DISCOVER** | 5,000 | 🟢 低 |
| **DESIGN** | 8,000 | 🟢 低 |
| **DRAFT** | 50,000 | 🔴 高（超出单会话） |
| **AUDIT** | 15,000 | 🟡 中 |
| **FIX** | 20,000 | 🟡 中 |
| **FREEZE** | 10,000 | 🟢 低 |
| **总计** | **108,000 tokens** | 🔴 **高风险** |

**建议**: 分 3 个会话执行
- 会话 1: DISCOVER + DESIGN + DRAFT（前 4 份文档）
- 会话 2: DRAFT（后 3 份文档）+ AUDIT
- 会话 3: FIX + FREEZE + 导航更新

### 9.2 时间预算

| 阶段 | 预估时间 |
|------|---------|
| **DISCOVER** | 30 分钟 |
| **DESIGN** | 1 小时 |
| **DRAFT** | 3 小时 |
| **AUDIT** | 1 小时 |
| **FIX** | 2 小时 |
| **FREEZE** | 30 分钟 |
| **总计** | **8 小时** |

### 9.3 Skill 调用预算

| Skill | 调用次数 | 用途 |
|-------|---------|------|
| `ai-ad-doc-architect` | 7 次 | 生成 7 份文档 |
| `ai-ad-doc-system-auditor` | 7 次 | 审计 7 份文档 |
| `ai-ad-doc-fixer` | 14 次 | 修复问题（迭代 2 轮） |
| `ai-ad-spec-governor` | 1 次 | 生成 Freeze Manifest |
| **总计** | **29 次** | |

---

## 10. 提案决策

### 10.1 提案状态

**当前状态**: ✅ **Draft**（待架构委员会审批）

**下一步行动**:
1. **架构委员会审批**: 提交给 Wade + 架构团队审核
2. **MASTER.md 更新**: 在 MASTER.md v3.4 基础上增加 Layer 6 描述 → v3.5
3. **执行创建**: 批准后，分 3 个会话执行 ASDD 6 步流程
4. **冻结决策**: Agent Layer v1.0 完成后，决定是否立即冻结或标记为 `active`

### 10.2 批准标准

**必须获得以下批准**:
- ✅ Wade (Documentation Owner)
- ✅ 架构团队（至少 1 名架构师）
- ✅ DevOps 团队（Agent 部署相关）

**批准后**:
- 更新 MASTER.md v3.4 → v3.5（增加 Layer 6 描述）
- 创建 `docs/6.agent-layer/` 目录
- 开始执行 ASDD 6 步流程

### 10.3 拒绝场景

**如果提案被拒绝**:
- 将 Agent 规范合并到 Infrastructure Layer（方案 A）
- 或将 Agent 规范合并到 Dev-Guides Layer（方案 B）
- 或推迟到 ASDD 框架 v2.0 再考虑（方案 D）

---

## 11. 参考文献

**引用文档**:
- MASTER.md v3.4 - ASDD 框架定义
- ARCHITECTURE_FREEZE_MANIFEST_v1.0.md - Freeze 流程参考
- INFRASTRUCTURE_FREEZE_MANIFEST_v1.0.md - Freeze Manifest 模板
- agents/agents_config.py - Agent 注册中心实现
- agents/agent_core/orchestrator_agent.py - Orchestrator 实现
- .claude/skills/ai-ad-spec-governor/SKILL.md - Spec Governor 定义

**外部参考**:
- [Anthropic MCP](https://modelcontextprotocol.io/) - Model Context Protocol
- [LangChain Agents](https://python.langchain.com/docs/modules/agents/) - Agent 架构参考
- [AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) - Multi-Agent System 参考

---

## 12. 附录

### 附录 A: Agent Layer 与其他层的对比

| 维度 | Infrastructure Layer | Agent Layer |
|------|---------------------|-------------|
| **职责** | CI/CD、部署、监控 | Agent 架构、安全、版本管理 |
| **关注点** | 基础设施即代码（IaC） | Agent 系统即代码（AgaC） |
| **冻结频率** | 低（每 6 个月） | 中（每 3 个月） |
| **解冻风险** | 低 | 中（Agent 快速迭代） |
| **依赖关系** | 被 Agent Layer 依赖 | 依赖 Infrastructure Layer |

### 附录 B: Agent Layer 创建检查清单

**会话 1: DISCOVER + DESIGN + DRAFT（前 4 份文档）**:
- [ ] 分析 `agents/` 目录代码
- [ ] 分析 `.claude/skills/` 目录 Skills
- [ ] 设计 7 份文档大纲
- [ ] 编写 AGENT_LAYER_OVERVIEW.md
- [ ] 编写 SUBAGENT_PROTOCOL.md
- [ ] 编写 AGENT_SECURITY_SPEC.md
- [ ] 编写 AGENT_ORCHESTRATION_PIPELINE.md

**会话 2: DRAFT（后 3 份文档）+ AUDIT**:
- [ ] 编写 CODEX_LOOP_SPEC.md
- [ ] 编写 AGENT_VERSIONING_RULES.md
- [ ] 编写 AGENT_SKILL_REGISTRY.md
- [ ] 审计全部 7 份文档

**会话 3: FIX + FREEZE + 导航更新**:
- [ ] 修复全部 P0/P1 问题
- [ ] 再次审计（验证修复效果）
- [ ] 生成 AGENT_LAYER_FREEZE_MANIFEST_v1.0.md
- [ ] 更新 docs/README.md
- [ ] 更新 docs/PROJECT_DOCS_INDEX_v1.0.md
- [ ] 更新 README.md
- [ ] Git Commit + Push

---

## 13. 提案批准

**提案者签名**:
Wade (Documentation Owner)
日期: 2025-11-27

**批准者签名**:
_待填写_

**批准日期**:
_待填写_

---

**RFC 状态**: ✅ Draft（待审批）
**下一步**: 提交架构委员会审核
**预计批准日期**: 2025-11-28

---

**End of RFC**
