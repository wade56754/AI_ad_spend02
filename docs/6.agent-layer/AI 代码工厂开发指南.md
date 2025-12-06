版本：v1.1
状态：Draft → 计划作为 Tier-3 平台规范文档

1. 文档定位

本指南约束和描述的是本项目的 AI 代码工厂体系，用于规范：

如何使用 Claude Code 对话 + Skill 来驱动代码生成 / refactor / 测试；

如何使用 agent_platform/ + CLI/MCP 在本地批量执行 Flow。

核心前提：

在实际日常开发中，Claude 本身就是 LLM 执行引擎；

我们的 “Skill” 的主要职责是：

加载正确的 SoT 文档和项目文件，作为 Claude 的上下文；

构造结构化的任务指令（统一的 XML Prompt 模板）；

在 Claude Code 对话框中执行，用户在侧边栏审查与应用 patch。

本指南覆盖：

agent_platform/ 核心框架层（CLI / MCP 批处理模式）

agents/ 下的 Agent / Skill / Flow 实现（逻辑分层与规范）

Claude Code / Claude Desktop 中的 “命令式用法”，例如：

/agent be gen_backend daily_reports

2. 体系与目录概览
2.1 代码目录结构
agent_platform/          # 核心框架层（通用，不写业务逻辑）
├── core/
│   ├── protocol.py      # AgentProtocol / AgentContext / AgentResult
│   ├── orchestrator.py  # OrchestratorBase 抽象基类（Flow 调度）
│   ├── registry.py      # Agent 注册表（按 name/role 取 Agent）
│   └── run.py           # AgentRun / Step 记录
├── llm/
│   ├── base.py          # LLMClient 抽象（CLI/服务模式用）
│   └── factory.py       # LLM 客户端工厂（anthropic_api / claude_code / dummy）
└── tools/               # 通用工具（fs 工具、校验、pytest runner 等）

agents/                  # 业务实现层（绑定本项目）
├── agent_core/
│   ├── orchestrator_agent.py  # Orchestrator 实现（聚合多个 Flow）
│   ├── be_agent.py            # 后端 Agent
│   ├── fe_agent.py            # 前端 Agent
│   ├── test_agent.py          # 测试 Agent
│   ├── doc_agent.py           # 文档 Agent
│   └── code_review_agent.py   # 代码审查 Agent
├── skills/                    # Skill 实现（Prompt 工厂 + 轻逻辑）
├── tools/                     # 项目级工具（如 sot-check、pytest wrapper）
└── agents_config.py           # Agent 注册与配置（逐步收敛为 registry 配置）

2.2 实际使用场景：Claude Code 对话框

日常开发时，主要使用场景是：

┌─────────────────────────────────────────────────────────┐
│                   Claude Code 对话框                     │
│  ┌─────────────────────────────────────────────────┐   │
│  │  用户: /agent be gen_backend daily_reports      │   │
│  │                                                 │   │
│  │  Claude: [读取 Skill] → [加载 SoT] → [执行任务] │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘


在这个场景下：

用户通过命令（如 /agent be ...）触发一个 Skill；

Skill 在 Claude 侧完成三件事：

读取 SoT 文档、代码文件（通过 File Tree / MCP）；

组装统一格式的 XML Prompt（<task> <context> <input> <constraints> <thinking> <steps> <output_format>）；

把这个 Prompt 交给 Claude，在当前对话内完成规划 / 生成 / patch 提案。

结论：
Claude 是执行引擎，Skill 是“Prompt 工厂 + SoT 装配器”。

3. 核心概念
3.1 Agent

概念层面：一个 有上下文 的执行单元，用于封装较复杂的开发流程。

代码层面：实现 AgentProtocol 的类（位于 agents/agent_core/）：

如 BEAgent / FEAgent / TestAgent / DocAgent / CodeReviewAgent。

在 CLI / MCP 模式下，由 agent_platform 调用 LLM API；

在 Claude Code 对话模式下，更多由 Claude 内置的 LLM 完成推理，Agent 概念更多体现在「命令入口 + Flow 选择」。

3.2 Skill

Skill 是 AI 工厂的核心颗粒度单位，在本项目里有两个角色：

在 Claude 对话模式：

Skill 是 Prompt 工厂：

负责读取 SoT / 代码片段；

负责构造统一结构的 XML Prompt；

把任务交给 Claude 在对话中执行。

Skill 本身一般不直接调用 LLM API（Claude 已经是 LLM）。

在 CLI / MCP 模式：

Skill 也可以通过 agent_platform.llm 调用 LLM；

但建议保持“逻辑尽量无副作用”，IO 交给工具层。

统一约束：

Skill 尽量接近纯函数：

输入：上下文 + SoT 内容 + 任务参数；

输出：Prompt、Patch 文本、报告文本等；

文件写入 / pytest 执行 / git 操作等副作用由 Agent 或 tools 层负责。

3.3 Flow

Flow = 一条 完整的开发流水线 定义：
例如：

be_then_test：后端代码修改 → 生成测试提示 → 人工执行 pytest；

gen_backend：根据模块清单批量生成后端模块骨架；

规划中的 module_full_cycle：PLAN → IMPL → TEST → REPORT。

在 Claude 对话模式中：

Flow 主要体现为 Prompt 内部的 <steps> + 总体 task 结构；

复杂 Flow 可由 Skill 在一次 Prompt 中指导 Claude 分步执行。

在 CLI / MCP 模式中：

Flow 由 OrchestratorBase / orchestrator_agent.py 实际调度多个 Agent + Skill + 工具。

3.4 模块（Module）与模块类型（Module Type）

模块 = 项目中的一个业务功能域：

例：topup、daily_reports、reports、import_jobs。

每个模块必须声明其 module_type，以便 AI 工厂选用正确的模具。

当前支持的 module_type：

api_crud

stateful_workflow

report_module

import_module

模块类型详见后文第 4 章。

4. 模块类型规范（Module Types）
4.1 类型总览表
module_type	适用模块示例	绑定 SoT 文档	标准产物（至少包括）
api_crud	projects, channels, suppliers…	DATA_SCHEMA, API_SOT, AUTH_SPEC	schemas/{name}.py, services/{name}_service.py, routers/{name}.py, tests/api/*
stateful_workflow	daily_reports, topup, reconciliation	STATE_MACHINE, BUSINESS_RULES, AUTH_SPEC, ERROR_CODES_SOT	schemas/{name}.py, services/{name}_service.py, routers/{name}.py, state_machine tests
report_module	reports, finance_profit, ai_monitoring	LEDGER_SOT, STATE_MACHINE, BUSINESS_RULES, AUTH_SPEC	schemas/reports.py, services/report_service.py, routers/reports.py, report tests
import_module	import_jobs（CSV/Excel 导入）	DATA_SCHEMA, BUSINESS_RULES, DAILY_REPORT_SOT	models/workflow/import_job.py, schemas/import_jobs.py, services/import_job_service.py, routers/import_jobs.py, tests/api/*

规则：

新模块必须选择其中一种类型；

无法归类时，禁止随意发明“第 5 类”，必须先在本指南中新增 module_type 定义。

4.2 各类型简要规范（略写，只给关键点）
4.2.1 api_crud

场景：简单 CRUD + 过滤；

工厂职责：

生成标准 CRUD 端点；

对齐 DATA_SCHEMA / API_SOT；

挂上基本权限（AUTH_SPEC）。

4.2.2 stateful_workflow

场景：带审批/多状态，如 topup/daily_reports。

工厂职责：

所有状态流转必须来自 STATE_MACHINE 白名单；

自动生成：

合法流转测试；

非法流转拒绝测试；

终态不可变测试；

角色边界测试。

4.2.3 report_module

场景：只读统计，如 reports。

工厂职责：

执行“数据源分离”：

粉数 → daily_reports；

收入/成本 → ledger_entries（PROJECT/SUPPLIER ledger）。

加上日报状态过滤、权限过滤；

生成 Service + Router + 报表测试。

4.2.4 import_module

场景：数据导入任务，如 import_jobs。

工厂职责：

生成 ImportJob 模型 + 状态机；

只产生中间数据/草稿，不直接写账本；

生成导入 API + 基本幂等逻辑测试。

5. 模块规范文件（Module Spec / Manifest）

所有使用 AI 工厂开发/重构的模块，都应有一个模块规范文件，建议路径：

openspec/changes/{module}.module.yml


示例：reports.module.yml：

module: reports
module_type: report_module

sot_refs:
  - docs/2.sot/LEDGER_SOT.md#project-ledger
  - docs/2.sot/LEDGER_SOT.md#supplier-ledger
  - docs/2.sot/STATE_MACHINE.md#daily-report
  - docs/2.sot/AUTH_SPEC.md#roles

data_sources:
  metrics:
    exposure: daily_reports
    clicks: daily_reports
    leads: daily_reports
    revenue: ledger_entries.PROJECT.REVENUE
    cost: ledger_entries.SUPPLIER.COST
    profit: revenue - cost

permissions:
  admin: all
  finance: all
  data_operator: all
  account_manager: own_projects
  media_buyer: own_accounts

artifacts:
  - backend/schemas/reports.py
  - backend/services/report_service.py
  - backend/routers/reports.py
  - backend/tests/services/test_report_service.py
  - backend/tests/api/test_reports_api.py


Skill/Flow 在运行时：

读取 module + module_type；

加载MODULE_TYPE_*规范 + 上述 sot_refs 文档；

将 data_sources / permissions 转成 Prompt 中的 <context> 与 <constraints>。

6. 协议与架构约束
6.1 AgentProtocol 统一

统一规范在：agent_platform/core/protocol.py。

所有 Agent 必须使用这份定义，不允许在 agents_config.py 等处重复定义协议结构。

协议变更流程：

修改 agent_platform/core/protocol.py；

同步更新：

agent_platform/core/orchestrator.py

agents/agent_core/*.py

相关测试。

6.2 OrchestratorBase vs OrchestratorAgent

OrchestratorBase（core 层）：

提供 Flow 注册与执行的抽象；

管理 AgentRun / Step 记录。

OrchestratorAgent（agents 层）：

实现本项目具体 Flow（如 be_then_test、gen_backend 等）；

中长期目标：将每个 Flow 拆到独立 Handler 类（避免 1500+ 行巨石）。

在 Claude 对话模式中：

这些 Flow 的实现在概念上仍然存在；

Skill 会根据用户输入（如 /agent be gen_backend daily_reports）选择正确 Flow，并生成对应 XML Prompt，让 Claude 在对话中执行。

6.3 错误处理

业务 API 层：使用 ERROR_CODES_SOT 中定义的业务错误码（BIZ_/STATE_/AUTH_/VALIDATION_）。

AI 工厂层（agent_platform / skills）：

使用内部枚举（示例）：

class AgentErrorKind(str, Enum):
    LLM_ERROR = "LLM_ERROR"
    TOOL_ERROR = "TOOL_ERROR"
    SPEC_VIOLATION = "SPEC_VIOLATION"
    TEST_FAILED = "TEST_FAILED"


仅在对外提供 HTTP 服务时才映射为 HTTP 状态码；

不在 AI 工厂内部混用业务错误码段。

7. 运行模式：Claude 对话 vs CLI / MCP
7.1 Claude Code 对话模式（主模式）

使用方式：在 Claude Code / Claude Desktop 中输入命令，比如：

/agent be gen_backend daily_reports


执行流程：

命令被解析为：调用某个 Skill（如 be_gen_backend_skill）；

Skill：

读取 module manifest（如 daily_reports.module.yml）；

加载 SoT 文档（STATE_MACHINE / LEDGER_SOT / API_SOT 等）；

读取相关代码文件（通过项目文件树/MCP）；

生成一份结构化 XML Prompt；

Claude 使用该 Prompt：

先给出实现计划；

再生成 patch / 新文件内容；

用户在侧边栏审查并应用。

特点：

所有推理/生成直接用 Claude 自身；

安全：没有自动写磁盘，用户最后拍板；

适合日常开发、迭代型任务（增量修改、单模块完善）。

7.2 CLI / MCP 批处理模式（辅助模式）

使用方式：

python -m agent_platform.cli orch \
  --flow be_then_test \
  --task "修复 ledger 模块中与对账批次状态机相关的测试失败问题..."


执行流程：

使用 agent_platform.llm 调用 LLM；

通过 Orchestrator + Agent + Skill 自动生成 patch、写文件、执行 pytest；

流程和 Claude 对话模式概念一致，但执行在本地或服务端。

特点：

适合长任务 / 多模块批处理；

可用于 CI / Nightly 修复类 Flow；

风险略高（自动写文件），必须有测试和审查流程兜底。

8. Claude Skill 提示词结构规范（XML Prompt 模板）

为保证 Claude 在对话模式中的行为稳定、可复用，所有面向 Claude 的 Skill Prompt 必须遵守统一 XML 结构：

<task>        # 任务目标（一句话 + 必要细化）
</task>

<context>
  use context7
  <!-- 必要项目背景、模块说明、SoT 简述 -->
</context>

<input>
  <!-- 本次任务的输入：如 module_spec 内容、相关代码片段、变更请求描述等 -->
</input>

<constraints>
  <!-- 硬约束：SoT 不可改动、不能新增错误码、必须对齐 STATE_MACHINE/LEDGER_SOT 等 -->
</constraints>

<thinking>
  <!-- 要求 Claude 内部思考的步骤说明（不会直接暴露给用户），用于规范推理顺序 -->
</thinking>

<steps>
  <!-- 对 Claude 的执行步骤指导，偏“流程图”视角（先做 PLAN 再做 IMPL 再做 TEST） -->
</steps>

<output_format>
  <!-- 期望输出结构：例如“先给变更概要，再给分文件代码块，最后给 pytest 命令和 TODO” -->
</output_format>


Skill 实现要求：

对于每个模块类型（api_crud / stateful_workflow / report_module / import_module），可在 <constraints> 与 <steps> 中注入类型特定规则；

<context> 中必须包含：

本模块的 module_type；

关键 SoT 引用（来自 module_spec.sot_refs）；

相关文件路径（schemas/services/routers/tests）。

对于“只做规划不写代码”的 Skill（如 PLAN 阶段），<output_format> 必须要求生成 IMPLEMENTATION.md 结构化内容；

Skill 不直接写文件，只返回文本由用户应用（对话模式）或交给 CLI/工具层处理（批处理模式）。

9. 使用 AI 工厂开发/改造一个模块的标准流程

以强化 reports 模块为例：

模块归类

在 MODULE_INDEX.md 登记：reports → report_module。

创建/更新 module_spec

编辑 openspec/changes/reports.module.yml：

module_type

sot_refs

data_sources

permissions

artifacts

Claude 对话模式：执行 PLAN + IMPL

在 Claude Code 中：

/agent be reports_plan


Skill 行为：

读取 reports.module.yml；

加载 LEDGER_SOT / STATE_MACHINE / AUTH_SPEC；

生成 <task>/<context>/... 完整 XML Prompt；

Claude 输出 REPORTS_MODULE_IMPLEMENTATION.md。

审核无误后，再调用：

/agent be reports_impl


Skill 生成实现代码（Service / Router / Tests），由 Claude 提案 patch，用户手动应用。

执行测试

手动或在 TestAgent 帮助下执行：

pytest backend/tests/test_reports*.py -v


（可选）生成 Freeze 报告

Claude 中调用：

/agent test reports_freeze


生成 REPORTS_MODULE_FREEZE_REPORT_vX.Y.md，记录变更与测试结果。

CLI 批处理（仅在需要时）

若需要自动跑大范围修复，可使用 agent_platform.cli 调 module_full_cycle 之类的 Flow，前提是 Skill/Flow 已对齐本指南要求。

10. 质量分级与 Roadmap
10.1 问题分级（针对 AI 工厂自身）

P0：必须立即修复

协议重复定义/不一致（如 AgentProtocol 多份定义）；

Flow 逻辑会破坏 SoT（绕过状态机、直接写 LedgerEntry 等）；

生成 Patch 有明显数据损坏风险。

P1：建议尽快修复

巨石文件（如 1500+ 行的 OrchestratorAgent）导致难以维护；

Skill 与 Agent 边界混乱，副作用四散；

缺少重试 / 基础健壮性。

P2：优化级

async / streaming；

structlog / metrics / pydantic-settings 等基础设施优化。

10.2 Roadmap（简要）

Flow 抽象强化

将 OrchestratorAgent 按 Flow 拆分；

明确每个 Flow 支持哪些 module_type。

模块模板固化

为 api_crud / stateful_workflow / report_module / import_module 提供标准 Skill 模板；

module_spec → Skill Prompt 全自动拼装。

SoT 质检集成

在 TEST 阶段集成：

账本不变量测试；

状态机不变量测试；

Fail 时阻止自动 patch merge。

服务化（可选）

当需要将 AI 工厂长期以服务形式运行时：

增加 /health；

暴露 Prometheus metrics；

统一日志格式。