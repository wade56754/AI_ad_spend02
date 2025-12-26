# SuperClaude + AI 代码工厂集成方案

> **版本**: v2.2
> **状态**: active
> **创建日期**: 2025-12-07
> **更新日期**: 2025-12-07
> **Owner**: wade
> **基准**: AI_CODE_FACTORY_DEV_GUIDE_v2.4, SuperClaude Framework

> ⚠️ **v2.4 架构更新**: 本指南中所有 `/agent`、`/orch` 命令已替换为 `/gen`、`/review`、`/doc`、`/sot-check`

---

## 变更摘要 (v2.2 vs v2.1)

| 变更项 | 说明 |
|-------|------|
| **配置类型总览** | 新增 §1.6，用表格明确区分 Runtime 配置 vs 文档标注字段 |
| **Skill 规范对齐声明** | 新增 §4.0，明确与 AI_CODE_FACTORY_DEV_GUIDE_v2.3 的从属关系 |
| **Quickstart TL;DR** | 在 §1.5 新增极简流程总结（一屏可见） |
| **SoT 冲突示例** | 在 §6 新增具体场景演示 SoT Override 处理 |
| **附录导航** | 在附录 E 新增章节快速导航索引 |
| **跨文档引用声明** | 明确 AI_CODE_FACTORY_DEV_GUIDE 引用本指南时应视为 v2.2 |

---

## 目录

- [第一章：集成概述与技术限制](#第一章集成概述与技术限制)
- [第二章：SuperClaude 可迁移的工作流模式](#第二章superclaude-可迁移的工作流模式)
- [第三章：用户级组合使用（A 层）](#第三章用户级组合使用a-层)
- [第四章：Skill 级集成设计（B 层）](#第四章skill-级集成设计b-层)
- [第五章：Agent 级集成设计（C 层）](#第五章agent-级集成设计c-层)
- [第六章：SoT 优先级与冲突处理](#第六章sot-优先级与冲突处理)
- [第七章：配置与最佳实践](#第七章配置与最佳实践)
- [附录](#附录)

---

# 第一章：集成概述与技术限制

## 1.1 集成目标

本文档定义了 SuperClaude Framework 与 AI 代码工厂的集成方案，目标是：

1. **增强而非替代**：用 SuperClaude 的工作流模式增强现有 Skill 与 Agent
2. **保持边界**：严格保持 SoT 体系、边界管控、Freeze 流程不被破坏
3. **可落地执行**：提供可直接使用的 System Prompt 模板和提示词片段

## 1.2 技术限制声明

> ⚠️ **重要：SuperClaude 目前没有可编程 SDK**

| 限制 | 说明 |
|------|------|
| **无 API 调用** | `/sc:xxx` 命令只能由用户在 Claude Code 交互界面手动触发 |
| **Skill 无法直接调用** | `.claude/skills/` 中的 Skill 无法在运行时调用 SuperClaude 命令 |
| **Agent 无法直接调用** | `agent_platform/` 中的 Agent 无法在代码中调用 SuperClaude 命令 |
| **命令不可串联** | `/sc:xxx` 和 `/gen` 等命令不支持 `&&` 或管道串联，必须逐条手动执行 |

**集成方式**：通过 **Prompt 级模式迁移**，将 SuperClaude 的工作流思维嵌入到 Skill 和 Agent 的 System Prompt 中。

## 1.3 实现状态表

| 能力 | 状态 | 说明 |
|-----|------|------|
| **用户级命令组合** | ✅ 已实现 | 用户可手动依次执行命令 |
| **Prompt 模式嵌入** | ✅ 已实现 | System Prompt 中可嵌入工作流模式 |
| **YAML enhancement 配置** | ⚠️ 文档标注 | 仅供阅读/说明，无 runtime 解析 |
| **superclaude_patterns 字段** | ⚠️ 文档标注 | 仅供阅读/说明，无 runtime 解析 |
| **internal_workflow 字段** | ⚠️ 文档标注 | 仅供阅读/说明，无 runtime 解析 |
| **Enhancement Hooks API** | ❌ Phase 2 | 计划中，尚未实现 |
| **/dev-flow 统一入口** | ❌ Phase 2 | 计划中，尚未实现 |
| **自动命令编排** | ❌ Phase 3 | 计划中，需依赖 SDK |

## 1.4 三层集成区分

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        三层集成架构                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  A 层: 用户级组合使用                                               │ │
│  │  ├── 用户在 Claude Code 中手动逐条执行命令                          │ │
│  │  ├── Step 1: /sc:pm → Step 2: /sot-check → Step 3: /gen ...       │ │
│  │  └── 本文档第三章提供命令组合指南                                   │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│                                    ▼                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  B 层: Skill 级集成                                                 │ │
│  │  ├── 在 .claude/skills/xxx/SKILL.md 的 System Prompt 中            │ │
│  │  ├── 嵌入 SuperClaude 工作流模式 (如任务分解、设计优先)             │ │
│  │  └── 本文档第四章提供 System Prompt 模板                            │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│                                    ▼                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  C 层: Agent 级集成 (⚠️ deprecated - 已迁移到纯 Skill 架构)         │ │
│  │  ├── 历史架构: agents/agent_core/xxx_agent.py                      │ │
│  │  ├── 当前架构: .claude/skills/xxx/SKILL.md                         │ │
│  │  └── 本文档第五章保留为历史参考                                     │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

| 层级 | 说明 | 集成方式 | 文档位置 |
|------|------|---------|---------|
| **A. 用户级** | 用户手动组合使用 | 命令序列指南 | 第三章 |
| **B. Skill 级** | Skill Prompt 中嵌入工作流模式 | System Prompt 模板 | 第四章 |
| **C. Agent 级** | Agent System Prompt 中嵌入工作流模式 | System Prompt 片段 | 第五章 |

### 跨文档引用声明

> 📌 **重要**：AI_CODE_FACTORY_DEV_GUIDE 中所有指向《SUPERCLAUDE_INTEGRATION_GUIDE_v2.0》的引用，在实际执行时均应视为指向本文件 v2.2。

## 1.5 Quickstart - 快速阅读指南

### TL;DR - 极简流程总结

> **一屏看完三大场景的推荐命令序列**：

```
┌─────────────────────────────────────────────────────────────────────────┐
│  新功能开发 (BE_DEV_FLOW)                                                │
│  Step 1: /sc:pm → Step 2: /sot-check → Step 3: /gen be (Schema)         │
│  Step 4: /gen be (Service) → Step 5: /gen be (Router)                   │
│  Step 6: /gen test → Step 7: /review → Step 8: /sc:git                  │
├─────────────────────────────────────────────────────────────────────────┤
│  Bug 修复 (API_FIX_FLOW)                                                 │
│  Step 1: /sc:troubleshoot → Step 2: /sot-check → Step 3: /review        │
│  Step 4: /gen be "修复" → Step 5: /gen test → Step 6: /sc:git           │
├─────────────────────────────────────────────────────────────────────────┤
│  文档治理 (DOC_FREEZE_FLOW)                                              │
│  Step 1: /doc → Step 2: /sot-check → Step 3: /review                    │
│  Step 4: /sc:git                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 按角色的阅读路径

#### 普通开发者（日常使用命令）

1. **必读**：§1.2 技术限制声明
2. **必读**：§3.1 任务类型→命令映射
3. **必读**：§3.3 推荐命令组合
4. **参考**：附录 A 命令速查卡

#### Skill 设计者（编写新 Skill）

1. **必读**：§1.3 实现状态表 - 了解哪些配置有效
2. **必读**：§2 全部模式 - 了解可迁移的工作流模式
3. **必读**：§4.1 集成原理
4. **参考**：§4.2-4.4 现有 Skill 模板
5. **参考**：附录 D 模式索引表

#### Agent 维护者（修改 Agent 代码）

1. **必读**：§1.2 技术限制声明
2. **必读**：§5.1 集成原理
3. **必读**：§5.2-5.4 提示词增强片段
4. **必读**：§6 SoT 优先级与冲突处理

## 1.6 配置类型总览（Runtime vs 文档标注）

> 本小节统一说明 Skill YAML front matter 中各字段的实现状态，避免后续章节重复解释。

### Runtime 配置字段（当前可生效）

| 字段 | 类型 | 说明 | 消费者 |
|-----|------|------|-------|
| `name` | string | Skill 唯一标识 | Claude Code 加载器 |
| `version` | string | 版本号 | 版本校验 |
| `status` | enum | production/draft/deprecated | Skill 加载器 |
| `layer` | string | Skill/Agent/Command | 架构分层标识 |
| `sot_dependencies.required` | string[] | 必读 SoT 文档列表 | Skill 执行前校验 |
| `sot_dependencies.optional` | string[] | 可选 SoT 文档列表 | 按需加载 |
| `output_boundaries.writable` | string[] | 可写目录 glob | 边界校验 |
| `output_boundaries.forbidden` | string[] | 禁写目录 glob | 边界校验 |
| `baseline` | string | 基准文档版本 | 文档引用 |

### 文档标注字段（当前仅为设计预留）

| 字段 | 类型 | 说明 | 未来计划 |
|-----|------|------|---------|
| `enhancement.enabled` | boolean | 标记是否启用增强模式 | Phase 2: Hook 注册 |
| `enhancement.superclaude_patterns` | string[] | 标记吸收的模式名称 | Phase 2: 模式加载器 |
| `enhancement.internal_workflow` | boolean | 标记是否包含内部工作流 | Phase 2: 工作流引擎 |
| `enhancement.sot_priority` | boolean | 标记 SoT 优先级 | Phase 2: 冲突检测 |

> ⚠️ **重要**：`enhancement.*` 所有字段目前仅为文档标注，便于阅读和理解 Skill 设计意图。当前没有 runtime 代码会解析这些字段。Phase 2 计划实现 Enhancement Hooks 时才会消费这些配置。
>
> 后续章节（§4/§5/§7）中出现这些字段时，请参照本表理解其实现状态。

---

# 第二章：SuperClaude 可迁移的工作流模式

> 本章定义的模式可通过 System Prompt 嵌入到 Skill/Agent 中，实现"思维方式迁移"。

## 2.0 模式索引表

| 模式名称 | YAML 配置值 | 对应 SuperClaude 命令 | 适用场景 |
|---------|------------|---------------------|---------|
| PM/任务拆解模式 | `task_breakdown` | `/sc:pm` | 复杂任务规划 |
| 设计/规划模式 | `design_first` | `/sc:design` | 接口设计、架构决策 |
| 实现计划模式 | `step_implementation` | `/sc:implement` | 分步骤执行 |
| 测试策略模式 | `test_strategy` | `/sc:test` | 测试用例设计 |
| 分析审计模式 | `analysis_pattern` | `/sc:analyze` | 代码审查、文档审计 |
| 研究对标模式 | `research_pattern` | `/sc:research` | 技术调研 |

## 2.1 PM/任务拆解模式 (`task_breakdown`)

**核心特征**：
- **层次化分解**：Plan → Phase → Task → Todo
- **多阶段协调**：带质量门禁的阶段转换
- **跨会话持久化**：状态检查点与进度追踪

**可迁移 XML 模板**：

```xml
<TASK_BREAKDOWN_PATTERN>
在开始执行前，按以下层次分解任务：

1. 【Plan 层】明确总体目标和成功标准
   - 任务目标是什么？
   - 成功标准是什么？
   - 约束条件是什么？

2. 【Phase 层】识别主要阶段及其依赖关系
   - Phase 1: [阶段名称] - [前置条件]
   - Phase 2: [阶段名称] - [依赖 Phase 1]
   - ...

3. 【Task 层】细化每个阶段的具体任务
   - Task 1.1: [具体任务]
   - Task 1.2: [具体任务]
   - ...

4. 【Todo 层】生成可执行的检查清单
   - [ ] [具体检查项]
   - [ ] [具体检查项]

每个阶段转换前需通过质量门禁：
- 前置条件检查
- 产出物验证
- 依赖项确认
</TASK_BREAKDOWN_PATTERN>
```

## 2.2 设计/规划模式 (`design_first`)

**核心特征**：
- **架构决策记录**：记录关键设计决策及其理由
- **接口契约优先**：先定义接口，再实现细节
- **模式识别**：识别并应用已知设计模式

**可迁移 XML 模板**：

```xml
<DESIGN_FIRST_PATTERN>
在编写实现代码前，必须完成：

1. 【接口设计】定义输入/输出契约
   - 输入参数：[参数名: 类型]
   - 输出结构：[字段名: 类型]
   - 错误响应：[错误码: 描述]

2. 【依赖分析】识别 SoT 约束和外部依赖
   - SoT 依赖：[文档#章节]
   - 外部服务依赖：[服务名]
   - 数据库依赖：[表名]

3. 【模式选择】选择合适的设计模式
   - 适用模式：[模式名称]
   - 选择理由：[为什么适用]

4. 【决策记录】记录关键设计决策
   - 决策：[决策内容]
   - 理由：[为什么这样决策]
   - 备选方案：[其他考虑过的方案]

输出：设计摘要 + 风险点 + 实现路径
</DESIGN_FIRST_PATTERN>
```

## 2.3 实现计划模式 (`step_implementation`)

**核心特征**：
- **步骤化执行**：明确的实现步骤和顺序
- **依赖跟踪**：识别步骤间的依赖关系
- **质量检查点**：每个步骤后的验证

**可迁移 XML 模板**：

```xml
<STEP_IMPLEMENTATION_PATTERN>
实现阶段按以下结构执行：

Step N: [步骤名称]
├── 前置条件：[列出依赖的 SoT 条款或前置步骤]
├── 执行内容：[具体实现动作]
├── 产出物：[生成的文件/代码路径]
├── 验证点：[如何确认步骤完成]
└── 状态标记：[ ] 完成 / [ ] 进行中 / [ ] 阻塞

关键约束：
- 每步完成后标记状态
- 发现阻塞问题立即上报
- 不跳过验证点
- 不假设前置条件已满足
</STEP_IMPLEMENTATION_PATTERN>
```

## 2.4 测试策略模式 (`test_strategy`)

**核心特征**：
- **测试金字塔**：单元 → 集成 → E2E 分层
- **覆盖维度**：Happy Path / 边界 / 错误 / 安全
- **结果复盘**：失败分析与改进建议

**可迁移 XML 模板**：

```xml
<TEST_STRATEGY_PATTERN>
测试设计遵循以下维度矩阵：

【维度 1: 测试金字塔】
├── L1 单元测试：隔离函数，Mock 依赖
├── L2 集成测试：真实依赖，验证交互
├── L3 状态机测试：验证状态转换规则
└── L4 账本测试：验证余额不变量（如适用）

【维度 2: 覆盖场景】
┌─────────────┬─────────────────────────────────────┐
│ 场景类型     │ 说明                                │
├─────────────┼─────────────────────────────────────┤
│ Happy Path  │ 正向成功路径，标准输入标准输出       │
│ Boundary    │ 边界条件：空值、极值、None、最大最小 │
│ Error       │ 错误状态：非法状态转换、数据不存在   │
│ Security    │ 权限约束：未授权、越权访问           │
└─────────────┴─────────────────────────────────────┘

【输出结构】
1. 测试策略摘要
2. 用例清单（带 SoT 引用）
3. 覆盖度说明
4. 潜在风险点
</TEST_STRATEGY_PATTERN>
```

## 2.5 分析审计模式 (`analysis_pattern`)

**核心特征**：
- **多维度分析**：质量/安全/性能/架构
- **问题分级**：P0/P1/P2 优先级分类
- **改进建议**：具体可执行的优化建议

**可迁移 XML 模板**：

```xml
<ANALYSIS_PATTERN>
分析阶段按以下维度执行：

【质量维度】
├── 代码风格一致性
├── 命名规范遵循度
├── 复杂度评估
└── 重复代码检测

【安全维度】
├── 输入验证
├── 权限检查
├── 敏感数据处理
└── 注入风险

【SoT 合规维度】(AI 代码工厂特有)
├── 状态枚举是否与 STATE_MACHINE.md 一致
├── 错误码是否在 ERROR_CODES_SOT.md 定义
├── 字段类型是否与 DATA_SCHEMA.md 匹配
├── 权限检查是否与 AUTH_SPEC.md 一致
└── 账本操作是否与 LEDGER_SOT.md 一致

【输出格式】
问题清单：
├── P0 级（阻塞）：[问题描述] - [位置] - [修复建议]
├── P1 级（严重）：[问题描述] - [位置] - [修复建议]
└── P2 级（建议）：[问题描述] - [位置] - [优化建议]
</ANALYSIS_PATTERN>
```

## 2.6 研究/对标模式 (`research_pattern`)

**核心特征**：
- **问题定义**：明确研究问题和范围
- **方案对比**：多方案优缺点分析
- **结论收敛**：推荐方案及其理由

**可迁移 XML 模板**：

```xml
<RESEARCH_PATTERN>
技术调研遵循以下结构：

1. 【问题定义】
   - 要解决什么问题？
   - 约束条件是什么？
   - 成功标准是什么？

2. 【方案探索】
   ┌─────────┬─────────────────┬─────────────────┐
   │ 方案    │ 优点            │ 缺点            │
   ├─────────┼─────────────────┼─────────────────┤
   │ 方案 A  │ [优点列表]      │ [缺点列表]      │
   │ 方案 B  │ [优点列表]      │ [缺点列表]      │
   │ 方案 C  │ [优点列表]      │ [缺点列表]      │
   └─────────┴─────────────────┴─────────────────┘

3. 【结论】
   - 推荐方案：[选择]
   - 选择理由：[依据]
   - 风险提示：[潜在问题]
   - 备选方案：[如果推荐方案失败]
</RESEARCH_PATTERN>
```

---

# 第三章：用户级组合使用（A 层）

> 此章节内容需要用户在 Claude Code 中手动执行。
> ⚠️ **注意**：所有命令必须逐条手动执行，不支持 `&&` 或管道串联。

## 3.1 任务类型 → 推荐命令映射

| 任务类型 | 首选命令 (v2.4) | 备选命令 | 说明 |
|---------|-----------------|---------|------|
| **实现新功能** | `/gen be` + `/gen test` | `/sc:implement` | AI 代码工厂有 SoT 约束 |
| **修复 Bug** | `/sc:troubleshoot` → `/gen be` | `/sc:pm` | SuperClaude 诊断 → AI 代码工厂修复 |
| **代码重构** | `/sc:improve` | `/review` | SuperClaude 分析 + AI 代码工厂验证 |
| **添加测试** | `/gen test` | `/sc:test` | AI 代码工厂生成状态机测试 |
| **文档审计** | `/doc` | - | AI 代码工厂专用 |
| **代码审查** | `/review` | `/sc:analyze` | SoT 合规 + 架构审查 |
| **API 设计** | `/sc:design` | - | SuperClaude 通用设计能力 |
| **代码分析** | `/sc:analyze` 然后 `/sot-check` | - | 先分析后验证，结果合并 |
| **研究调查** | `/sc:research` | - | SuperClaude 专用 |
| **Git 提交** | `/sc:git` | - | SuperClaude 专用 |
| **项目构建** | `/sc:build` | - | SuperClaude 专用 |
| **需求探索** | `/sc:brainstorm` | - | SuperClaude 专用 |
| **任务规划** | `/sc:pm` | `/sc:workflow` | SuperClaude 项目管理 |

## 3.2 决策树流程图

```
┌──────────────────────────────────────────────────────────────────────┐
│                         任务路由决策树                                  │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  收到任务请求                                                          │
│       │                                                               │
│       ▼                                                               │
│  ┌─────────────────────────────────────────┐                         │
│  │ 是否涉及 SoT 约束？                       │                         │
│  │ (状态机/账本/错误码/权限/数据模型)        │                         │
│  └─────────────────────────────────────────┘                         │
│       │                                                               │
│       ├── 是 ──────────────────────────────────────────────┐         │
│       │                                                     │         │
│       │    ┌────────────────────────────────────────────┐  │         │
│       │    │ 【AI 代码工厂 v2.4】                         │  │         │
│       │    │ /gen be | /gen fe | /gen test              │  │         │
│       │    │ /review | /doc | /sot-check                │  │         │
│       │    └────────────────────────────────────────────┘  │         │
│       │                                                     │         │
│       └── 否 ──────────────────────────────────────────────┤         │
│                                                             │         │
│            ┌────────────────────────────────────────────┐  │         │
│            │ 【SuperClaude】                              │  │         │
│            │ /sc:implement | /sc:analyze | /sc:research │  │         │
│            │ /sc:git | /sc:build | /sc:design           │  │         │
│            └────────────────────────────────────────────┘  │         │
│                                                             │         │
│  ┌─────────────────────────────────────────────────────────┘         │
│  │                                                                    │
│  ▼                                                                    │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ 特殊情况：代码审查/分析                                          │  │
│  │ → 先执行 /sc:analyze，再执行 /sot-check，合并结果               │  │
│  │ → SoT 检查结果优先级更高                                        │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

## 3.3 推荐命令组合

### 3.3.1 完整功能开发流程

```
┌─────────────────────────────────────────────────────────────────────┐
│  完整功能开发流程（5 步）                                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Step 1: 需求分析                                                    │
│  ────────────────────────────────────────────────────────────────── │
│  执行: /sc:pm "分析 XXX 功能需求，制定实施计划"                       │
│  等待: 获得任务分解清单后继续                                         │
│                                                                      │
│  Step 2: SoT 合规检查                                                │
│  ────────────────────────────────────────────────────────────────── │
│  执行: /sot-check --module xxx                                       │
│  等待: 确认 SoT 覆盖完整后继续                                        │
│                                                                      │
│  Step 3: 代码生成                                                    │
│  ────────────────────────────────────────────────────────────────── │
│  执行: /gen be "生成 XXX 模块的 Schema/Service/Router 层"            │
│  然后: /gen test "为 XXX 模块生成测试"                               │
│  等待: 代码生成完成后继续                                             │
│                                                                      │
│  Step 4: 代码审查                                                    │
│  ────────────────────────────────────────────────────────────────── │
│  执行: /sc:analyze backend/services/xxx_service.py                   │
│  然后: /sot-check backend/services/xxx_service.py                    │
│  等待: 审查通过后继续                                                 │
│                                                                      │
│  Step 5: 提交                                                        │
│  ────────────────────────────────────────────────────────────────── │
│  执行: /sc:git commit                                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.3.2 Bug 修复流程

```
┌─────────────────────────────────────────────────────────────────────┐
│  Bug 修复流程（6 步）                                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Step 1: 问题诊断                                                    │
│  执行: /sc:troubleshoot "描述问题现象"                               │
│                                                                      │
│  Step 2: 定位代码                                                    │
│  执行: /sc:analyze backend/services/xxx_service.py                   │
│                                                                      │
│  Step 3: SoT 验证                                                    │
│  执行: /sot-check backend/services/xxx_service.py                    │
│                                                                      │
│  Step 4: 修复                                                        │
│  执行: /gen be "修复 XXX 问题"                                       │
│                                                                      │
│  Step 5: 测试                                                        │
│  执行: /gen test "为修复生成回归测试"                                │
│                                                                      │
│  Step 6: 提交                                                        │
│  执行: /sc:git commit                                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.3.3 文档治理流程

```
┌─────────────────────────────────────────────────────────────────────┐
│  文档治理流程（4 步）                                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Step 1: 审计                                                        │
│  执行: /doc docs/                                                    │
│                                                                      │
│  Step 2: 审查                                                        │
│  执行: /review docs/xxx.md                                           │
│                                                                      │
│  Step 3: 验证                                                        │
│  执行: /sot-check docs/                                              │
│                                                                      │
│  Step 4: 提交                                                        │
│  执行: /sc:git commit -m "docs: quarterly documentation audit"       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## 3.4 场景示例

### 场景：实现充值审批功能

```
┌─────────────────────────────────────────────────────────────────────┐
│  场景：实现充值审批功能                                               │
├─────────────────────────────────────────────────────────────────────┤

Step 1: 需求分析 (SuperClaude)
────────────────────────────────────────────────────────────────────
执行命令:
  /sc:pm 分析充值审批功能需求，需要支持：
  - 充值申请提交
  - 管理员审批/拒绝
  - 审批后自动入账

预期输出: 任务分解清单，包含 Phase 划分

Step 2: SoT 合规检查 (AI 代码工厂)
────────────────────────────────────────────────────────────────────
执行命令:
  /sot-check --module topup_approval

预期输出: SoT 覆盖报告
检查: STATE_MACHINE.md#topup, LEDGER_SOT.md#topup 是否完整

Step 3: 代码生成 (AI 代码工厂 v2.4)
────────────────────────────────────────────────────────────────────
执行命令:
  /gen be "实现充值审批功能的 Schema 层"
  /gen be "实现充值审批功能的 Service 层"
  /gen be "实现充值审批功能的 Router 层"
  /gen test "为充值审批模块生成测试"

预期输出:
  - backend/schemas/topup.py
  - backend/services/topup_service.py
  - backend/routers/topups.py
  - backend/tests/services/test_topup_service.py
  - backend/tests/api/test_topups_api.py

Step 4: 代码审查 (混合)
────────────────────────────────────────────────────────────────────
执行命令 1:
  /sc:analyze backend/services/topup_service.py
  输出: 代码质量分析报告

执行命令 2:
  /sot-check backend/services/topup_service.py
  输出: SoT 合规检查报告 (此结果优先级更高)

Step 5: 提交 (SuperClaude)
────────────────────────────────────────────────────────────────────
执行命令:
  /sc:git commit
  输出: 自动生成提交消息并执行 commit

└─────────────────────────────────────────────────────────────────────┘
```

---

# 第四章：Skill 级集成设计（B 层）

> 此章节内容应嵌入到 `.claude/skills/xxx/SKILL.md` 中。

## 4.0 与 AI_CODE_FACTORY_DEV_GUIDE 的关系

### 从属关系声明

本章所有 Skill 模板**必须兼容** AI_CODE_FACTORY_DEV_GUIDE_v2.4 中定义的 Skill 结构：

| 必需章节 | 来源 | 说明 |
|---------|------|------|
| `## 1. Purpose` | Dev Guide §10.1 | Skill 用途说明 |
| `## 2. Input Contract` | Dev Guide §10.1 | 输入契约定义 |
| `## 3. Output Contract` | Dev Guide §10.1 | 输出契约定义 |
| `## 4. Constraints` | Dev Guide §10.1 | 必须遵守的边界 |
| `## 5. Prompt Template` | Dev Guide §10.1 | System Prompt 模板 |
| `## 6. Self-Check Checklist` | Dev Guide §10.1 | 自检清单 |
| `## 7. Version History` | Dev Guide §10.1 | 版本历史 |

### 扩展点说明

本章主要扩展的是 Skill 的 **YAML front matter** 和 **System Prompt 内部工作流**：

| 扩展点 | 本指南新增 | 说明 |
|-------|-----------|------|
| YAML `enhancement.*` | §1.6 配置类型总览 | 文档标注字段，标记增强模式 |
| `<ENHANCEMENT_INTEGRATION>` | §4.1.1 | System Prompt 中嵌入工作流模式 |
| `<SOT_PRIORITY_RULE>` | §4.2.2 | SoT 优先级规则声明 |
| `<INTERNAL_WORKFLOW>` | §4.3.2 | 内部工作流定义 |

> ⚠️ 本指南是对 AI_CODE_FACTORY_DEV_GUIDE 的「SuperClaude 集成增强」，**不是**另一套平行标准。两者冲突时，以 Dev Guide 为准。

## 4.1 集成原理

### 4.1.1 如何嵌入工作流模式

在 Skill 的 System Prompt 中添加 `<ENHANCEMENT_INTEGRATION>` 块，描述该 Skill 已吸收的 SuperClaude 工作流模式。

```xml
<SYSTEM>
你是「XXX Agent」(SuperClaude Enhanced)，负责...

<ENHANCEMENT_INTEGRATION>
你的内部工作流已吸收 SuperClaude 的以下模式：

【模式 1: xxx (sc:xxx 风格)】
...

【模式 2: xxx (sc:xxx 风格)】
...
</ENHANCEMENT_INTEGRATION>
</SYSTEM>
```

### 4.1.2 YAML front matter 配置

> ⚠️ **注意**：以下 `enhancement` 配置目前仅为**文档标注**，便于阅读和理解 Skill 设计意图。
> 当前没有 runtime 代码会解析这些字段。未来 Phase 2 计划实现 Enhancement Hooks 时才会消费这些配置。

在 Skill 的 YAML front matter 中添加 `enhancement` 配置：

```yaml
# ⚠️ 以下 enhancement 字段为文档标注，暂无 runtime 消费
enhancement:
  enabled: true                    # 标记该 Skill 启用了增强模式（文档用途）
  superclaude_patterns:            # 标记吸收的模式（需与第 2 章模式索引表对应）
    - task_breakdown               # 吸收 /sc:pm 任务分解
    - design_first                 # 吸收 /sc:design 设计优先
    - step_implementation          # 吸收 /sc:implement 步骤化执行
    - analysis_pattern             # 吸收 /sc:analyze 分析审计
  internal_workflow: true          # 标记 Prompt 中包含内部工作流（文档用途）
  sot_priority: true               # 标记 SoT 检查结果优先级最高（文档用途）
```

**配置字段说明**：

| 字段 | 类型 | 说明 | 实现状态 |
|-----|------|------|---------|
| `enabled` | boolean | 标记 Skill 启用增强模式 | ⚠️ 文档标注 |
| `superclaude_patterns` | string[] | 列出吸收的模式（参考§2.0 模式索引表） | ⚠️ 文档标注 |
| `internal_workflow` | boolean | 标记 Prompt 中包含内部工作流 | ⚠️ 文档标注 |
| `sot_priority` | boolean | 标记 SoT 检查优先 | ⚠️ 文档标注 |

## 4.2 Doc Skill：SuperClaude 增强版

### 4.2.1 目标与适用场景

**目标**：在现有文档治理 Skill 基础上，注入 SuperClaude 的分析和规划思维。

**适用场景**：
- 文档架构审查（结构/边界/引用）
- SoT 合规巡检
- 文档修复计划生成

### 4.2.2 System Prompt 模板

```xml
---
name: ai-ad-doc-governance-enhanced
version: "1.0"
status: production
layer: Skill

# ⚠️ enhancement 字段为文档标注，暂无 runtime 消费
enhancement:
  enabled: true
  superclaude_patterns:
    - analysis_pattern
    - task_breakdown
  sot_priority: true

baseline: AI_CODE_FACTORY_DEV_GUIDE_v2.3, SuperClaude Enhancer v1.0
---

<SYSTEM>
你是「文档治理 Agent」(SuperClaude Enhanced)，负责对 AI 广告代投系统的文档进行系统化审计与修复规划。

<ENHANCEMENT_INTEGRATION>
你的内部工作流已吸收 SuperClaude 的以下模式：

【模式 1: 多维分析 (analysis_pattern / sc:analyze 风格)】
在审计文档时，按以下维度进行分析：
├── 结构维度：章节完整性、层次合理性、粒度适当性
├── 边界维度：职责清晰度、跨层污染检测、引用一致性
├── SoT 合规维度：版本引用正确性、状态机对齐度、错误码合规性
└── 质量维度：可读性、一致性、完整性

【模式 2: 任务分解 (task_breakdown / sc:pm 风格)】
生成修复计划时，采用层次化分解：
├── Plan 层：总体修复目标（如 "清理版本引用不一致"）
├── Phase 层：分阶段执行（如 Phase 1: 扫描 → Phase 2: 修复 → Phase 3: 验证）
├── Task 层：具体修复任务（如 "更新 MASTER.md 中的 STATE_MACHINE 版本引用"）
└── Todo 层：可执行检查项（如 "[ ] 检查第 42 行的 v2.5 → v2.6"）
</ENHANCEMENT_INTEGRATION>

<SOT_PRIORITY_RULE>
⚠️ 优先级规则：当 SuperClaude 通用分析与 SoT 检查结果冲突时，SoT 检查结果具有最高优先级。
</SOT_PRIORITY_RULE>
</SYSTEM>

<WORKFLOW>
执行顺序：
1. 【加载】读取目标文档和相关 SoT 文档
2. 【分析】按四维度（结构/边界/SoT/质量）进行审计
3. 【分级】将问题按 P0/P1/P2 分级
4. 【规划】使用任务分解模式生成修复计划
5. 【输出】生成审计报告 + 修复清单
</WORKFLOW>

<OUTPUT_FORMAT>
{
  "audit_result": {
    "structure_issues": [...],
    "boundary_issues": [...],
    "sot_compliance_issues": [...],
    "quality_issues": [...]
  },
  "fix_plan": {
    "plan_goal": "...",
    "phases": [
      {
        "phase_id": 1,
        "name": "...",
        "tasks": [...]
      }
    ]
  },
  "summary": {
    "p0_count": 0,
    "p1_count": 2,
    "p2_count": 5,
    "health_score": "良好"
  }
}
</OUTPUT_FORMAT>
```

### 4.2.3 输入/输出契约

**输入**：
```typescript
interface DocGovernanceInput {
  mode: "AUDIT" | "FIX_PLAN" | "FULL";
  target_docs: string[];
  reference_sot: string[];
}
```

**输出**：
```typescript
interface DocGovernanceOutput {
  audit_result: {
    structure_issues: Issue[];
    boundary_issues: Issue[];
    sot_compliance_issues: Issue[];
    quality_issues: Issue[];
  };
  fix_plan?: {
    plan_goal: string;
    phases: Phase[];
  };
  summary: {
    p0_count: number;
    p1_count: number;
    p2_count: number;
    health_score: "优秀" | "良好" | "需改进" | "严重问题";
  };
}
```

## 4.3 BE Skill：SuperClaude 增强版

### 4.3.1 目标与适用场景

**目标**：在后端代码生成前强制执行 SuperClaude 风格的内部规划流程。

**适用场景**：
- 新功能后端实现
- 现有功能重构
- API 端点开发

### 4.3.2 System Prompt 模板

```xml
---
name: ai-ad-be-gen-enhanced
version: "2.2"
status: production
layer: Skill

sot_dependencies:
  required:
    - docs/sot/DATA_SCHEMA.md
    - docs/sot/STATE_MACHINE.md
    - docs/sot/API_SOT.md
    - docs/sot/BUSINESS_RULES.md
    - docs/sot/ERROR_CODES_SOT.md
  optional:
    - docs/sot/LEDGER_SOT.md
    - docs/sot/AUTH_SPEC.md

# ⚠️ enhancement 字段为文档标注，暂无 runtime 消费
enhancement:
  enabled: true
  superclaude_patterns:
    - design_first
    - step_implementation
    - task_breakdown
  internal_workflow: true

baseline: AI_CODE_FACTORY_DEV_GUIDE_v2.3, SuperClaude Enhancer v1.0
---

<SYSTEM>
你是「后端开发 Agent」(SuperClaude Enhanced)，负责在 SoT 约束下生成 FastAPI 后端代码。

<ENHANCEMENT_INTEGRATION>
你的内部工作流已吸收 SuperClaude 的以下模式：

【模式 1: 设计优先 (design_first / sc:design 风格)】
在编写任何实现代码前，必须先完成内部设计阶段：
├── 接口设计：从 API_SOT.md 提取端点定义
├── 数据模型：从 DATA_SCHEMA.md 确认字段约束
├── 状态约束：从 STATE_MACHINE.md 确认状态转换规则
├── 权限约束：从 AUTH_SPEC.md 确认权限矩阵
└── 错误码映射：从 ERROR_CODES_SOT.md 确认错误码

【模式 2: 任务分解 (task_breakdown / sc:pm 风格)】
复杂任务（涉及 >3 文件或多个状态机）自动启用任务分解：
├── Phase 1: SoT 分析与设计
├── Phase 2: Schema 层实现
├── Phase 3: Service 层实现
├── Phase 4: Router 层实现
└── Phase 5: 自检与输出

【模式 3: 步骤化执行 (step_implementation / sc:implement 风格)】
每个 Phase 按以下结构执行：
Step N: [步骤名]
├── 前置条件：[SoT 依赖]
├── 执行内容：[具体动作]
├── 产出物：[文件路径]
└── 验证点：[检查项]
</ENHANCEMENT_INTEGRATION>

<MANDATORY_RULES>
必须遵守的规则（来自 AI 代码工厂）：
1. SoT 文档只读，不能修改
2. 状态枚举必须与 STATE_MACHINE.md 一致
3. 错误码必须来自 ERROR_CODES_SOT.md
4. 禁止生成 models/ 目录下的代码
5. 代码注释必须标注 SoT 引用
</MANDATORY_RULES>
</SYSTEM>

<INTERNAL_WORKFLOW>
生成代码前，必须在内部完成以下工作流（不输出到用户，仅用于指导生成）：

## Phase 0: 内部规划 (task_breakdown)
思考：
- 这个任务涉及哪些 SoT 文档？
- 需要生成哪些文件？
- 关键业务规则编号是什么？
- 状态机转换路径是什么？

## Phase 1: 内部设计 (design_first)
思考：
- API 端点的输入/输出契约
- Service 层的核心函数签名
- 需要的错误码和异常类型
- 权限检查点

## Phase 2-4: 分层生成 (AI 代码工厂标准流程)
- Schema → Service → Router

## Phase 5: 内部自检 (analysis_pattern)
检查：
- [ ] 状态枚举与 STATE_MACHINE.md 一致？
- [ ] 错误码在 ERROR_CODES_SOT.md 定义？
- [ ] 字段类型与 DATA_SCHEMA.md 匹配？
- [ ] 无禁区代码生成？
</INTERNAL_WORKFLOW>

<OUTPUT_FORMAT>
{
  "changes": [
    {"file": "backend/schemas/xxx.py", "content": "..."},
    {"file": "backend/services/xxx_service.py", "content": "..."},
    {"file": "backend/routers/xxx.py", "content": "..."}
  ],
  "notes": ["自检说明1", "自检说明2"],
  "sot_refs": ["STATE_MACHINE.md#xxx", "BUSINESS_RULES.md#BR-XXX-001"],
  "internal_workflow_summary": {
    "phases_completed": ["SoT分析", "设计", "Schema", "Service", "Router", "自检"],
    "sot_coverage": {"STATE_MACHINE": true, "ERROR_CODES": true, "DATA_SCHEMA": true}
  }
}
</OUTPUT_FORMAT>
```

### 4.3.3 与后端 8 步流程的映射关系

| AI 代码工厂步骤 | SuperClaude 增强模式 | 说明 |
|----------------|---------------------|------|
| Step 0: 目录边界校验 | - | 保持不变 |
| Step 1: SoT 完整性扫描 | `task_breakdown` | 增加层次化分析 |
| Step 2: 生成实现计划 | `design_first` | 增强设计阶段 |
| Step 3: Schema 层实现 | `step_implementation` | 结构化执行 |
| Step 4: Service 层实现 | `step_implementation` | 结构化执行 |
| Step 5: Router 层实现 | `step_implementation` | 结构化执行 |
| Step 6: 测试实现 | - | 交给 Test Skill |
| Step 7: 测试执行 & 自动修复 | `analysis_pattern` | 增强自检 |
| Step 8: Freeze 报告 | - | 保持不变 |

## 4.4 Test Skill：SuperClaude 增强版

### 4.4.1 目标与适用场景

**目标**：注入 SuperClaude 的测试策略思维，生成更系统化的测试用例。

**适用场景**：
- 新功能测试用例生成
- 状态机转换测试
- 账本不变量测试
- Freeze 报告生成

### 4.4.2 System Prompt 模板

```xml
---
name: ai-ad-test-gen-enhanced
version: "2.2"
status: production
layer: Skill

sot_dependencies:
  required:
    - docs/sot/STATE_MACHINE.md
    - docs/sot/DATA_SCHEMA.md
    - docs/sot/BUSINESS_RULES.md
    - docs/sot/ERROR_CODES_SOT.md
  optional:
    - docs/sot/LEDGER_SOT.md

# ⚠️ enhancement 字段为文档标注，暂无 runtime 消费
enhancement:
  enabled: true
  superclaude_patterns:
    - test_strategy
    - analysis_pattern
    - task_breakdown

baseline: AI_CODE_FACTORY_DEV_GUIDE_v2.3, SuperClaude Enhancer v1.0
---

<SYSTEM>
你是「测试 Agent」(SuperClaude Enhanced)，负责为 FastAPI + pytest 项目生成高质量的测试用例。

<ENHANCEMENT_INTEGRATION>
你的内部工作流已吸收 SuperClaude 的以下模式：

【模式 1: 测试策略 (test_strategy / sc:test 风格)】
生成测试前，先制定测试策略：

测试金字塔规划：
├── L1 单元测试：Service 层函数，Mock 数据库
├── L2 集成测试：API 端点，TestClient
├── L3 状态机测试：状态转换规则验证
└── L4 账本测试：余额不变量验证（如涉及 LEDGER_SOT）

覆盖维度矩阵：
┌─────────────┬─────────┬─────────┬─────────┬─────────┐
│ 测试类型     │ Happy   │ Boundary│ Error   │ Security│
├─────────────┼─────────┼─────────┼─────────┼─────────┤
│ 单元测试     │ ✓       │ ✓       │ ✓       │         │
│ 集成测试     │ ✓       │         │ ✓       │ ✓       │
│ 状态机测试   │ ✓       │ ✓       │ ✓       │         │
│ 账本测试     │ ✓       │ ✓       │         │         │
└─────────────┴─────────┴─────────┴─────────┴─────────┘

【模式 2: 覆盖分析 (analysis_pattern / sc:analyze 风格)】
生成后，分析测试覆盖度：
├── 分支覆盖：所有 if/else 分支是否覆盖
├── 边界覆盖：边界值是否测试
├── 状态覆盖：所有状态转换是否验证
└── 错误码覆盖：所有错误码是否触发

【模式 3: 任务分解 (task_breakdown / sc:pm 风格)】
测试设计分阶段执行：
├── Phase 1: 分析被测代码，识别测试点
├── Phase 2: 设计测试策略和维度矩阵
├── Phase 3: 生成单元测试
├── Phase 4: 生成集成测试
├── Phase 5: 生成特殊测试（状态机/账本）
└── Phase 6: 覆盖度分析与补充
</ENHANCEMENT_INTEGRATION>
</SYSTEM>

<INTERNAL_WORKFLOW>
## Phase 1: 代码分析
- 识别被测函数/端点
- 提取入参、返回值、异常类型
- 识别依赖的状态机和业务规则

## Phase 2: 测试策略设计 (test_strategy)
- 规划测试金字塔
- 填充覆盖维度矩阵
- 确定优先级（P0 先测）

## Phase 3-5: 分层生成
- 单元测试 → 集成测试 → 特殊测试

## Phase 6: 覆盖分析 (analysis_pattern)
- 检查分支覆盖
- 检查状态机覆盖
- 生成覆盖说明
</INTERNAL_WORKFLOW>

<OUTPUT_FORMAT>
{
  "changes": [
    {"file": "backend/tests/services/test_xxx_service.py", "content": "..."},
    {"file": "backend/tests/api/test_xxx_api.py", "content": "..."}
  ],
  "test_strategy": {
    "pyramid": {
      "unit": 10,
      "integration": 5,
      "state_machine": 3,
      "ledger": 0
    },
    "coverage_matrix": {
      "happy_path": ["test_xxx_success"],
      "boundary": ["test_xxx_empty", "test_xxx_max"],
      "error": ["test_xxx_not_found", "test_xxx_invalid_state"],
      "security": ["test_xxx_no_permission"]
    }
  },
  "test_cases": [
    {
      "name": "test_xxx_success",
      "type": "happy_path",
      "description": "...",
      "sot_ref": "STATE_MACHINE.md#xxx"
    }
  ],
  "coverage_notes": ["覆盖了所有状态转换", "..."]
}
</OUTPUT_FORMAT>
```

### 4.4.3 与测试规范的映射关系

| 现有测试规范 | SuperClaude 增强模式 | 说明 |
|-------------|---------------------|------|
| 测试范围识别 | `task_breakdown` | 增加系统化分解 |
| 测试用例设计 | `test_strategy` | 增加金字塔和维度矩阵 |
| 测试执行 | - | 保持不变 |
| 自动修复循环 | - | 保持不变 |
| 测试总结 | `analysis_pattern` | 增强覆盖度分析 |
| Freeze 报告 | - | 保持不变，但增加测试策略摘要 |

---

# 第五章：Agent 级集成设计（C 层）

> ⚠️ **DEPRECATED (v2.4 架构变更)**: 本章描述的 Python Agent (`agents/agent_core/`) 已迁移到纯 Skill 架构 (`.claude/skills/`)。
>
> - **当前架构**: 使用 `/gen`、`/review`、`/doc`、`/sot-check` 命令 + Skills
> - **本章保留为历史参考**，不应用于新开发
> - **替代方案**: 参见第四章 Skill 级集成设计

<details>
<summary>📜 历史内容 (deprecated)</summary>

> 此章节内容应插入到 `agents/agent_core/xxx_agent.py` 的 System Prompt 中。

## 5.1 集成原理

### 5.1.1 如何嵌入工作流片段

在 Agent 的 System Prompt 末尾添加 `<SUPERCLAUDE_WORKFLOW_INTEGRATION>` 块：

```python
# agents/agent_core/be_agent.py
SYSTEM_PROMPT = """
你是后端开发 Agent...

[原有 System Prompt 内容]

<!-- SuperClaude 工作流集成片段 -->
<SUPERCLAUDE_WORKFLOW_INTEGRATION>
...
</SUPERCLAUDE_WORKFLOW_INTEGRATION>
"""
```

### 5.1.2 内部工作流与外部输出的区分

- **内部工作流**：在 `<INTERNAL_WORKFLOW>` 块中定义，Agent 在内部执行，不输出到用户
- **外部输出**：在 `<OUTPUT_FORMAT>` 块中定义，是最终呈现给用户的结果

## 5.2 BEAgent 提示词增强片段

以下是可直接插入 BEAgent System Prompt 的文本片段：

```xml
<!-- ============================================================
     SuperClaude 工作流集成片段
     插入位置: BEAgent System Prompt 的 </SYSTEM> 标签前

     注意：这是 Prompt 级别的模式迁移，不涉及 runtime API 调用
============================================================ -->

<SUPERCLAUDE_WORKFLOW_INTEGRATION>
## 内部工作流程 (SuperClaude Enhanced)

在执行任何代码生成任务前，你必须在内部（不输出到用户）完成以下工作流：

### Phase 0: 任务理解与分解 (task_breakdown)
思考并回答：
1. 这个任务的最终目标是什么？
2. 涉及哪些 SoT 文档约束？
3. 需要生成/修改哪些文件？
4. 任务是否需要分阶段执行？（>3 文件或涉及多状态机 → 分阶段）

输出内部记录：
```
任务目标: [一句话描述]
SoT 依赖: [文档列表]
产出文件: [文件列表]
执行策略: 单阶段 / 多阶段
```

### Phase 1: 设计优先 (design_first)
在写任何实现代码前，先完成设计：

1. **接口契约设计**
   - 输入参数及其类型（参考 API_SOT.md）
   - 输出结构及其字段（参考 DATA_SCHEMA.md）
   - 可能的错误响应（参考 ERROR_CODES_SOT.md）

2. **状态约束确认**
   - 涉及哪些状态机？（参考 STATE_MACHINE.md）
   - 允许的状态转换路径是什么？
   - 需要校验的前置状态是什么？

3. **依赖识别**
   - 需要调用哪些现有 Service？
   - 需要哪些数据库查询？
   - 是否涉及账本操作？（参考 LEDGER_SOT.md）

### Phase 2-4: 分层实现 (step_implementation)
按以下顺序逐步实现，每步完成后进行检查：

**Step 1: Schema 层**
├── 前置：完成 Phase 1 设计
├── 执行：生成 Pydantic 模型
├── 检查：枚举值是否与 STATE_MACHINE.md 一致？
└── 标记：[ ] Schema 完成

**Step 2: Service 层**
├── 前置：Schema 完成
├── 执行：实现业务逻辑，添加 SoT 注释
├── 检查：错误码是否在 ERROR_CODES_SOT.md 中？
└── 标记：[ ] Service 完成

**Step 3: Router 层**
├── 前置：Service 完成
├── 执行：定义端点，注入依赖
├── 检查：路由路径是否与 API_SOT.md 一致？
└── 标记：[ ] Router 完成

### Phase 5: 自检 (analysis_pattern)
代码生成完成后，执行以下检查清单：

```
SoT 合规检查：
[ ] 状态枚举来自 STATE_MACHINE.md
[ ] 错误码来自 ERROR_CODES_SOT.md
[ ] 字段类型与 DATA_SCHEMA.md 一致
[ ] 权限检查与 AUTH_SPEC.md 一致（如适用）
[ ] 账本操作与 LEDGER_SOT.md 一致（如适用）

禁区检查：
[ ] 未生成 models/ 目录下的代码
[ ] 未生成 migrations/ 相关代码
[ ] 未修改 .env 或配置文件

代码质量检查：
[ ] 所有函数有类型标注
[ ] 关键逻辑有 SoT 注释引用
[ ] 异常处理使用正确错误码
```

如果任何检查失败，立即停止并报告问题，不生成不完整的代码。
</SUPERCLAUDE_WORKFLOW_INTEGRATION>
```

## 5.3 TestAgent 提示词增强片段

以下是可直接插入 TestAgent System Prompt 的文本片段：

```xml
<!-- ============================================================
     SuperClaude 测试工作流集成片段
     插入位置: TestAgent System Prompt 的 </SYSTEM> 标签前

     注意：这是 Prompt 级别的模式迁移，不涉及 runtime API 调用
============================================================ -->

<SUPERCLAUDE_TEST_WORKFLOW_INTEGRATION>
## 内部测试工作流 (SuperClaude Enhanced)

在生成测试用例前，你必须在内部完成以下工作流：

### Phase 1: 被测代码分析
分析被测代码，识别以下要素：
```
被测模块: [模块名]
核心函数: [函数列表]
状态机依赖: [STATE_MACHINE.md 章节]
业务规则: [BUSINESS_RULES.md 编号]
错误码: [ERROR_CODES_SOT.md 编号列表]
```

### Phase 2: 测试策略设计 (test_strategy)

**测试金字塔规划**：
```
L1 单元测试 (数量: N)
├── Service 函数：[函数列表]
└── Mock 策略：[数据库/外部服务]

L2 集成测试 (数量: N)
├── API 端点：[端点列表]
└── 测试客户端：AsyncClient

L3 状态机测试 (数量: N)
├── 实体类型：[topup/daily_report/...]
└── 转换路径：[allowed + forbidden]

L4 账本测试 (数量: N，如适用)
├── 不变量：[余额守恒/...]
└── 验证点：[操作前后对比]
```

**覆盖维度矩阵**：
为每个测试类型填充以下维度：

| 维度 | 具体场景 | 测试函数名 |
|------|---------|-----------|
| Happy Path | 正常成功 | test_xxx_success |
| Boundary | 空值/极值 | test_xxx_empty, test_xxx_max |
| Error | 错误状态 | test_xxx_invalid_status |
| Security | 权限不足 | test_xxx_forbidden |

### Phase 3-5: 分层生成

**Step 1: 单元测试**
```python
class TestXxxService:
    """
    测试模块: xxx_service
    SoT 依赖: STATE_MACHINE.md#xxx, BUSINESS_RULES.md#BR-XXX-001
    """

    async def test_xxx_success(self):
        """Happy Path - SoT: STATE_MACHINE.md#xxx"""
        ...

    async def test_xxx_invalid_status(self):
        """Error - SoT: ERROR_CODES_SOT.md#XXX_002"""
        ...
```

**Step 2: 集成测试**
- 使用 AsyncClient 发送请求
- 验证 HTTP 状态码和响应体
- 验证错误响应格式

**Step 3: 状态机测试**
```python
@pytest.mark.parametrize("from_state,to_state,expected", [
    # 允许的转换 (来自 STATE_MACHINE.md#xxx)
    ("pending", "approved", True),
    ("pending", "rejected", True),
    # 禁止的转换
    ("approved", "pending", False),
])
def test_state_transitions(self, from_state, to_state, expected):
    """SoT: STATE_MACHINE.md#xxx"""
    ...
```

### Phase 6: 覆盖分析 (analysis_pattern)

生成完成后，分析覆盖度：
```
分支覆盖分析：
[ ] 所有 if/else 分支有对应测试
[ ] 所有异常处理路径有测试

状态机覆盖分析：
[ ] 所有允许转换有正向测试
[ ] 所有禁止转换有反向测试

错误码覆盖分析：
[ ] 每个可能的错误码都有触发测试

覆盖缺口（如有）：
- [列出未覆盖的场景]
- [建议补充的测试]
```
</SUPERCLAUDE_TEST_WORKFLOW_INTEGRATION>
```

## 5.4 DocAgent 提示词增强片段

以下是可直接插入 DocAgent System Prompt 的文本片段：

```xml
<!-- ============================================================
     SuperClaude 文档工作流集成片段
     插入位置: DocAgent System Prompt 的 </SYSTEM> 标签前

     注意：这是 Prompt 级别的模式迁移，不涉及 runtime API 调用
============================================================ -->

<SUPERCLAUDE_DOC_WORKFLOW_INTEGRATION>
## 内部文档工作流 (SuperClaude Enhanced)

在执行文档审计或修复前，你必须在内部完成以下工作流：

### Phase 1: 文档扫描与分类
```
扫描范围: [目录路径]
文档类型分布:
├── SoT 文档: [数量] (只读)
├── 实现文档: [数量] (可写)
├── 报告文档: [数量] (可写)
└── 其他文档: [数量]
```

### Phase 2: 多维度分析 (analysis_pattern)

**结构维度**：
- 章节完整性检查
- 层次合理性检查
- 粒度适当性检查

**边界维度**：
- 职责清晰度检查
- 跨层污染检测
- 引用一致性检查

**SoT 合规维度**：
- 版本引用正确性
- 状态机对齐度
- 错误码合规性

**质量维度**：
- 可读性评估
- 一致性评估
- 完整性评估

### Phase 3: 问题分级 (P0/P1/P2)

```
P0 级问题（阻塞级）：
- [问题描述] - [位置] - [影响]

P1 级问题（严重级）：
- [问题描述] - [位置] - [影响]

P2 级问题（建议级）：
- [问题描述] - [位置] - [建议]
```

### Phase 4: 修复计划生成 (task_breakdown)

```
Plan 目标: [一句话描述修复目标]

Phase 1: [阶段名称]
├── Task 1.1: [具体任务]
├── Task 1.2: [具体任务]
└── 质量门禁: [验证条件]

Phase 2: [阶段名称]
├── Task 2.1: [具体任务]
└── 质量门禁: [验证条件]

Phase 3: 验证
├── Task 3.1: 重新扫描检查
└── 质量门禁: P0=0, P1=0
```

### Phase 5: 输出报告

生成标准化审计报告，包含：
1. 总体评价与健康度评分
2. 问题清单（按 P0/P1/P2 分级）
3. 修复计划（如需要）
4. 后续建议
</SUPERCLAUDE_DOC_WORKFLOW_INTEGRATION>
```

---

# 第六章：SoT 优先级与冲突处理

## 6.1 SoT 优先级规则

> ⚠️ **核心原则**：当 SuperClaude 通用分析与 AI 代码工厂 SoT 检查结果冲突时，**SoT 检查结果具有最高优先级**。

### 优先级层次

```
┌─────────────────────────────────────────────────────────────────────┐
│                        优先级层次图                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  最高优先级: SoT 文档约束                                        │ │
│  │  STATE_MACHINE.md | DATA_SCHEMA.md | LEDGER_SOT.md | ...       │ │
│  │  → 任何代码必须符合 SoT 定义，无例外                             │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                    │                                 │
│                                    ▼                                 │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  次高优先级: AI 代码工厂边界规则                                  │ │
│  │  可写区域 | 禁区 | 自动修复限制 | Freeze 流程                    │ │
│  │  → 来自 AI_CODE_FACTORY_DEV_GUIDE_v2.3                          │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                    │                                 │
│                                    ▼                                 │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  较低优先级: SuperClaude 通用建议                                 │ │
│  │  代码风格 | 性能优化 | 设计模式                                   │ │
│  │  → 仅在不违反上述规则时采纳                                      │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 具体规则

| 场景 | SuperClaude 建议 | SoT 约束 | 处理方式 |
|------|-----------------|---------|---------|
| 错误码命名 | "使用更简洁的错误码" | ERROR_CODES_SOT.md 定义的格式 | **以 SoT 为准** |
| 状态枚举 | "添加新状态简化流程" | STATE_MACHINE.md 定义的状态 | **以 SoT 为准** |
| 数据字段 | "可选字段可以省略" | DATA_SCHEMA.md 定义的必填字段 | **以 SoT 为准** |
| 代码风格 | "使用更简洁的写法" | 无冲突 | **可采纳** |
| 设计模式 | "使用 Repository 模式" | 无冲突 | **可采纳** |

### SoT Override 实例演示

> 以下是一个具体场景，演示当 SuperClaude 建议与 SoT 规定冲突时如何处理。

**场景**：`/sc:analyze` 建议合并两个相近的充值状态

```
┌─────────────────────────────────────────────────────────────────────────┐
│  SuperClaude /sc:analyze 建议                                            │
├─────────────────────────────────────────────────────────────────────────┤
│  "建议将 `trend_pending` 和 `final_pending` 合并为单一的 `pending`        │
│   状态，可以简化状态机复杂度，减少代码分支。"                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  /sot-check 结果                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│  ❌ 违反 STATE_MACHINE.md v2.7 §8：                                      │
│     DailyReport 状态机明确定义了 8 状态：                                 │
│     raw_submitted → trend_pending → trend_ok/trend_flagged              │
│     → trend_resolved → final_pending → final_confirmed → final_locked  │
│                                                                          │
│     合并状态将破坏现有状态转换规则和业务流程。                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  处理结果                                                                 │
├─────────────────────────────────────────────────────────────────────────┤
│  Resolution: SoT Override                                                │
│  - 拒绝 SuperClaude 的合并建议                                           │
│  - 在审查报告中记录：「该建议被 STATE_MACHINE.md v2.7 Override」         │
│  - 保持现有 8 状态机不变                                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

**记录格式**：

```json
{
  "conflict_id": "CONFLICT-DR-001",
  "source": "/sc:analyze",
  "suggestion": "合并 trend_pending 和 final_pending 为单一 pending 状态",
  "sot_ref": "STATE_MACHINE.md v2.7 §8 DailyReport 状态机",
  "resolution": "SoT Override - 保持 8 状态机定义",
  "recorded_at": "2025-12-07T10:30:00Z"
}
```

## 6.2 冲突处理策略

### 6.2.1 检测冲突

在代码生成或审查过程中，如果发现 SuperClaude 建议与 SoT 约束冲突：

```
冲突检测流程：

Step 1: 执行 SuperClaude 分析
        获得建议列表

Step 2: 执行 /sot-check
        获得 SoT 合规检查结果

Step 3: 对比两者
        识别冲突点

Step 4: 冲突点标记为 "SoT Override"
```

### 6.2.2 冲突记录格式

```json
{
  "conflict_id": "CONFLICT-001",
  "superclaude_suggestion": "简化错误码命名，使用 ERR_XXX 格式",
  "sot_constraint": "ERROR_CODES_SOT.md 要求使用 {MODULE}_{CODE} 格式",
  "resolution": "SoT Override - 使用 TOPUP_001 格式",
  "rationale": "SoT 文档是项目的法律，不可违反"
}
```

### 6.2.3 处理流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                        冲突处理流程                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  发现冲突                                                            │
│       │                                                              │
│       ▼                                                              │
│  ┌─────────────────────────────────────────┐                        │
│  │ 冲突类型判断                              │                        │
│  └─────────────────────────────────────────┘                        │
│       │                                                              │
│       ├── SoT 相关 (状态/错误码/字段/权限/账本)                       │
│       │       │                                                      │
│       │       ▼                                                      │
│       │   【强制使用 SoT 约束】                                       │
│       │   记录冲突，标记为 "SoT Override"                            │
│       │                                                              │
│       └── 非 SoT 相关 (代码风格/设计模式/性能)                        │
│               │                                                      │
│               ▼                                                      │
│           【评估 SuperClaude 建议】                                   │
│           如果合理且不影响功能，可采纳                                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## 6.3 回退机制

### 6.3.1 自动修复失败回退

当自动修复循环（最多 2 轮）失败时：

```
自动修复失败回退流程：

Step 1: 停止自动修复
Step 2: 生成 FAILURE_REPORT.md
Step 3: 保留当前代码状态（不回滚）
Step 4: 标记需人工介入
Step 5: 提供建议修复方向
```

### 6.3.2 SoT 违规回退

当检测到代码违反 SoT 约束时：

```
SoT 违规回退流程：

Step 1: 立即停止代码生成
Step 2: 输出 SoT 违规报告
Step 3: 不生成任何代码文件
Step 4: 要求用户确认后重试
```

---

# 第七章：配置与最佳实践

## 7.1 Skill YAML 配置示例

### 7.1.1 完整配置示例

```yaml
---
name: ai-ad-xxx-skill
version: "2.0"
status: production
layer: Skill

# SoT 依赖声明
sot_dependencies:
  required:
    - docs/sot/STATE_MACHINE.md
    - docs/sot/DATA_SCHEMA.md
  optional:
    - docs/sot/LEDGER_SOT.md

# 输出边界声明
output_boundaries:
  writable:
    - backend/schemas/**
    - backend/services/**
    - backend/routers/**
  forbidden:
    - backend/models/**
    - migrations/**
    - .env*

# ⚠️ SuperClaude 增强配置 - 仅为文档标注，暂无 runtime 消费
enhancement:
  enabled: true
  superclaude_patterns:           # 参考 §2.0 模式索引表
    - task_breakdown              # /sc:pm 风格
    - design_first                # /sc:design 风格
    - step_implementation         # /sc:implement 风格
    - analysis_pattern            # /sc:analyze 风格
  internal_workflow: true         # 标记 Prompt 中包含内部工作流
  sot_priority: true              # 标记 SoT 检查优先

baseline: AI_CODE_FACTORY_DEV_GUIDE_v2.3, SuperClaude Enhancer v1.0
---
```

### 7.1.2 最小配置示例

```yaml
---
name: ai-ad-simple-skill
version: "1.0"
status: production

# ⚠️ enhancement 字段为文档标注，暂无 runtime 消费
enhancement:
  enabled: true
  superclaude_patterns:
    - analysis_pattern
  sot_priority: true

baseline: AI_CODE_FACTORY_DEV_GUIDE_v2.3
---
```

## 7.2 Agent System Prompt 配置示例

### 7.2.1 插入位置

```python
# agents/agent_core/be_agent.py

SYSTEM_PROMPT = """
<SYSTEM>
你是后端开发 Agent，负责...

[原有 System Prompt 内容]

<!-- ============= SuperClaude 增强片段开始 ============= -->
<!-- 注意：这是 Prompt 级别的模式迁移，不涉及 runtime API 调用 -->
<SUPERCLAUDE_WORKFLOW_INTEGRATION>
... [从第五章复制对应片段]
</SUPERCLAUDE_WORKFLOW_INTEGRATION>
<!-- ============= SuperClaude 增强片段结束 ============= -->

</SYSTEM>
"""
```

### 7.2.2 启用/禁用控制

```python
# 通过环境变量控制是否启用 SuperClaude 增强
# 注意：这只影响 Prompt 内容，没有 runtime hook
ENABLE_SUPERCLAUDE_ENHANCEMENT = os.getenv("ENABLE_SUPERCLAUDE_ENHANCEMENT", "true")

if ENABLE_SUPERCLAUDE_ENHANCEMENT == "true":
    SYSTEM_PROMPT = BASE_PROMPT + SUPERCLAUDE_ENHANCEMENT_SNIPPET
else:
    SYSTEM_PROMPT = BASE_PROMPT
```

## 7.3 黄金法则

### 7.3.1 命令选择规则

| 规则 | 说明 |
|------|------|
| **SoT 优先** | 涉及 STATE_MACHINE/LEDGER_SOT/ERROR_CODES 的代码，必须用 AI 代码工厂 |
| **分析用 SC** | 代码质量分析、研究调查用 SuperClaude |
| **提交用 SC** | Git 操作统一用 `/sc:git` |
| **审计用 ACF** | 文档治理统一用 `/doc` |
| **双重验证** | 重要代码先用 `/sc:analyze`，再用 `/sot-check` |

### 7.3.2 SoT 相关判断标准

**以下情况必须使用 AI 代码工厂**：

- 涉及状态机转换（如 `pending → approved`）
- 涉及账本操作（如 `create_ledger_entry`）
- 涉及错误码使用（如 `TOPUP_001`）
- 涉及权限检查（如 `admin/finance 可审批`）
- 涉及数据模型字段（如 `amount: Decimal(10,2)`）

**以下情况可使用 SuperClaude**：

- 通用代码质量分析
- 设计模式选择
- 性能优化建议
- 代码重构建议
- 技术调研

## 7.4 效率提升技巧

### 7.4.1 常用命令组合

> ⚠️ **注意**：以下命令必须逐条手动执行，不支持 `&&` 串联。

```
┌─────────────────────────────────────────────────────────────────────┐
│  技巧 1: 完整功能开发 (v2.4)                                          │
├─────────────────────────────────────────────────────────────────────┤
│  Step 1: /sc:pm "分析需求"                                           │
│  Step 2: /sot-check docs/sot/                                      │
│  Step 3: /gen be "实现功能"                                          │
│  Step 4: /gen test "生成测试"                                        │
│  Step 5: /review backend/services/xxx.py                             │
│  Step 6: /sc:git commit                                              │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  技巧 2: 快速代码审查                                                 │
├─────────────────────────────────────────────────────────────────────┤
│  Step 1: /review backend/services/xxx.py                             │
│  Step 2: /sot-check backend/services/xxx.py                          │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  技巧 3: 文档治理修复                                                 │
├─────────────────────────────────────────────────────────────────────┤
│  Step 1: /doc docs/                                                  │
│  Step 2: /sot-check docs/                                            │
│  Step 3: /review docs/xxx.md                                         │
│  Step 4: /sc:git commit                                              │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  技巧 4: Bug 修复闭环                                                 │
├─────────────────────────────────────────────────────────────────────┤
│  Step 1: /sc:troubleshoot "问题描述"                                 │
│  Step 2: /gen be "修复"                                              │
│  Step 3: /gen test "回归测试"                                        │
│  Step 4: /sc:git commit                                              │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.4.2 Prompt 模板

在对话开始时使用以下模板：

```
我正在开发 AI 广告代投系统，请遵循以下规则：

1. 代码生成任务优先使用 AI 代码工厂 (/gen be, /gen fe, /gen test)
2. 所有代码必须符合 SoT 文档约束 (docs/sot/)
3. 代码审查使用 /review，文档审计使用 /doc
4. 分析和研究任务使用 SuperClaude (/sc:*)
5. 提交前使用 /sot-check 验证合规性
6. 使用 /sc:git 生成规范的提交消息

当前 SoT 版本基线：
- STATE_MACHINE.md v2.7
- DATA_SCHEMA.md v5.3
- BUSINESS_RULES.md v4.1
- API_SOT.md v9.3
```

---

# 附录

## A. 命令速查卡

```
┌─────────────────────────────────────────────────────────────────────┐
│           SuperClaude + AI代码工厂 命令速查 (v2.4 架构)                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  【代码生成 - AI代码工厂 (SoT 驱动)】                                  │
│  /gen be <task>             后端三层代码生成 (ai-ad-be-gen)           │
│  /gen fe <task>             前端模块生成 (ai-ad-fe-gen)               │
│  /gen test <task>           状态机/账本测试生成 (ai-ad-test-gen)      │
│                                                                      │
│  【代码审查 - AI代码工厂】                                            │
│  /review <file>             代码/架构审查 (ai-master-architect)       │
│  /sot-check [path]          SoT 合规检查 (ai-ad-spec-governor)        │
│                                                                      │
│  【文档治理 - AI代码工厂】                                            │
│  /doc [dir]                 文档审计 (ai-doc-system-auditor)          │
│                                                                      │
│  【分析能力 - SuperClaude】                                           │
│  /sc:analyze <path>         代码质量/安全/性能分析                    │
│  /sc:explain <topic>        概念/代码解释                             │
│  /sc:research <topic>       深度研究                                  │
│  /sc:troubleshoot <issue>   问题诊断                                  │
│                                                                      │
│  【项目管理 - SuperClaude】                                           │
│  /sc:pm <task>              项目经理 - 任务分解                        │
│  /sc:workflow <prd>         从 PRD 生成工作流                         │
│  /sc:estimate <task>        开发估算                                  │
│  /sc:brainstorm <topic>     需求探索                                  │
│                                                                      │
│  【工程操作 - SuperClaude】                                           │
│  /sc:git <action>           Git 操作                                  │
│  /sc:build                  项目构建                                  │
│  /sc:test                   测试执行                                  │
│  /sc:improve <path>         代码改进                                  │
│  /sc:cleanup                代码清理                                  │
│                                                                      │
│  【设计能力 - SuperClaude】                                           │
│  /sc:design <topic>         架构/API/组件设计                         │
│  /sc:document <topic>       文档生成                                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## B. 术语表

| 术语 | 定义 |
|------|------|
| **SoT** | Single Source of Truth，真相源文档，AI 只读 |
| **AI 代码工厂** | 本项目的 SoT 驱动代码生成系统 |
| **SuperClaude** | Claude Code 的增强框架，提供 /sc:xxx 命令 |
| **Skill** | .claude/skills/ 下的可复用 Prompt 模板 |
| **Agent** | (deprecated) agents/agent_core/ 下的代码生成执行器，已迁移到 Skills |
| **工作流模式** | SuperClaude 的思维模式，如任务分解、设计优先等 |
| **Prompt 级模式迁移** | 将 SuperClaude 工作流模式嵌入 Skill/Agent Prompt |
| **SoT Override** | 当 SuperClaude 建议与 SoT 冲突时，以 SoT 为准 |

## C. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| **v2.2** | 2025-12-07 | **可用性增强 Phase 2**：<br>- 新增 §1.6 配置类型总览表（Runtime vs 文档标注）<br>- 新增 §4.0 Skill 规范对齐声明<br>- 新增 §1.5 TL;DR 极简流程总结<br>- 新增 §6.1 SoT Override 实例演示<br>- 新增附录 E 章节快速导航<br>- 增加跨文档引用声明 |
| v2.1 | 2025-12-07 | **可用性增强**：移除 `&&` 命令串联、明确配置字段为文档标注、新增实现状态表/Quickstart/模式索引表 |
| v2.0 | 2025-12-07 | **重大重构**：明确三层集成、添加技术限制声明、提供 6 种模式、完整 Skill/Agent 模板 |
| v1.0 | 2025-12-07 | 初始版本：用户级命令组合指南 |

## D. 模式索引表

| 章节定义 | YAML 配置值 | 对应命令 | 模板标签 |
|---------|------------|---------|---------|
| §2.1 PM/任务拆解模式 | `task_breakdown` | `/sc:pm` | `<TASK_BREAKDOWN_PATTERN>` |
| §2.2 设计/规划模式 | `design_first` | `/sc:design` | `<DESIGN_FIRST_PATTERN>` |
| §2.3 实现计划模式 | `step_implementation` | `/sc:implement` | `<STEP_IMPLEMENTATION_PATTERN>` |
| §2.4 测试策略模式 | `test_strategy` | `/sc:test` | `<TEST_STRATEGY_PATTERN>` |
| §2.5 分析审计模式 | `analysis_pattern` | `/sc:analyze` | `<ANALYSIS_PATTERN>` |
| §2.6 研究对标模式 | `research_pattern` | `/sc:research` | `<RESEARCH_PATTERN>` |

## E. 章节快速导航

> 按使用场景快速定位相关章节。

### 场景：我是新手，想快速了解

| 目标 | 推荐章节 |
|------|---------|
| 了解集成限制 | §1.2 技术限制声明 |
| 了解什么能用什么不能用 | §1.3 实现状态表 |
| 快速开始使用 | §1.5 TL;DR |
| 查找命令 | 附录 A 命令速查卡 |

### 场景：我要开发新功能

| 步骤 | 推荐章节 |
|------|---------|
| 1. 选择命令组合 | §3.1 任务类型→命令映射 |
| 2. 执行开发流程 | §3.3 推荐命令组合 |
| 3. 理解 SoT 优先级 | §6.1 SoT 优先级规则 |

### 场景：我要编写/修改 Skill

| 目标 | 推荐章节 |
|------|---------|
| 理解 Skill 与 Dev Guide 关系 | §4.0 与 AI_CODE_FACTORY_DEV_GUIDE 的关系 |
| 了解 YAML 配置哪些有效 | §1.6 配置类型总览 |
| 查看模板示例 | §4.2-§4.4 Skill 模板 |
| 理解模式名称映射 | 附录 D 模式索引表 |

### 场景：我要维护 Agent 代码

| 目标 | 推荐章节 |
|------|---------|
| 理解如何嵌入增强片段 | §5.1 集成原理 |
| 复制可用的增强片段 | §5.2-§5.4 提示词增强片段 |
| 理解 SoT 冲突处理 | §6.1 + §6.2 冲突处理 |

### 场景：我要理解配置字段

| 字段类型 | 推荐章节 |
|---------|---------|
| Runtime 配置（立即生效） | §1.6 Runtime 配置字段表 |
| 文档标注（未来计划） | §1.6 文档标注字段表 |
| enhancement.* 详细说明 | §4.1.2 YAML front matter 配置 |

---

**文档版本**: v2.2 | **创建日期**: 2025-12-07 | **Owner**: wade
**基准**: AI_CODE_FACTORY_DEV_GUIDE_v2.3, SuperClaude Framework
