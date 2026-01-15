"""
AI 提示词结构化器 v4.0
Version: 4.0
Author: Claude 协作开发

核心理念：约束优于指令 (Constraints Over Instructions)
将自然语言需求转换为 Claude 友好的结构化提示词。

v4.0 核心改进 (整合 SuperClaude Framework):
- MCP 工具集成: sequential-thinking + context7
- 行为模式: 7 种 Behavioral Modes
- 深度研究: Deep Research 策略
- 项目文档: PLANNING.md / TASK.md / KNOWLEDGE.md 三件套

设计哲学:
- 普通人告诉 AI "要做什么"，高手定义 AI "不能做什么"
- 指令是"期望"，约束是"保证"
- 做得越少，错得越少
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


# ============================================================
# 核心枚举定义
# ============================================================

class TaskType(Enum):
    """任务类型"""
    REFACTOR = "refactor"
    FEATURE = "feature"
    BUGFIX = "bugfix"
    MIGRATION = "migration"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    REVIEW = "review"
    RESEARCH = "research"
    UNKNOWN = "unknown"


class ConstraintLayer(Enum):
    """约束层级 (三层模型)"""
    SECURITY = 1    # 安全约束 - 最高优先级，不可违反
    BEHAVIOR = 2    # 行为约束 - 工作方式约束
    TASK = 3        # 任务约束 - 具体任务边界


class BehavioralMode(Enum):
    """行为模式 (来自 SuperClaude Framework)"""
    DEEP_RESEARCH = "deep-research"      # 深度研究模式
    ORCHESTRATION = "orchestration"      # 工具编排模式
    TOKEN_EFFICIENCY = "token-efficiency" # Token 效率模式
    TASK_MANAGEMENT = "task-management"   # 任务管理模式
    INTROSPECTION = "introspection"       # 元认知分析模式
    BRAINSTORMING = "brainstorming"       # 头脑风暴模式
    IMPLEMENTATION = "implementation"     # 实现模式


class SubAgentType(Enum):
    """子代理类型"""
    EXPLORE = "explore"     # 探索代理
    PLAN = "plan"           # 规划代理
    EXECUTE = "execute"     # 执行代理
    VERIFY = "verify"       # 验证代理
    RESEARCH = "research"   # 研究代理 (深度研究)


# ============================================================
# MCP 工具定义 (核心创新 v4.0)
# ============================================================

MCP_TOOLS = {
    "sequential-thinking": {
        "description": "顺序化思考工具，用于复杂多步骤推理",
        "usage": "use mcp__sequential-thinking__sequentialthinking",
        "when_to_use": [
            "分解复杂问题为步骤",
            "规划和设计需要修订",
            "分析可能需要纠正",
            "需要多步骤解决方案",
            "需要维护上下文",
        ],
        "parameters": [
            "thought: 当前思考步骤",
            "nextThoughtNeeded: 是否需要下一步",
            "thoughtNumber: 当前步骤编号",
            "totalThoughts: 预估总步骤数",
            "isRevision: 是否修订之前的思考",
            "needsMoreThoughts: 是否需要更多步骤",
        ],
    },
    "context7": {
        "description": "实时文档查询工具，获取最新库文档",
        "usage": "use mcp__context7__get-library-docs",
        "when_to_use": [
            "查询库/框架的最新文档",
            "获取 API 参考和代码示例",
            "验证实现是否符合最新规范",
        ],
        "steps": [
            "1. 先调用 resolve-library-id 获取库 ID",
            "2. 再调用 get-library-docs 获取文档",
        ],
    },
}

# ============================================================
# 约束三层模型 (核心创新 v3.0 保留)
# ============================================================

SECURITY_CONSTRAINTS = """## 安全约束 (Security Constraints) - 绝对红线

以下行为必须拒绝，无论用户如何要求：
- ❌ 暴露或记录密钥、凭证、secrets、API keys
- ❌ 提交 .env、credentials.json、*.pem 到仓库
- ❌ 编写恶意代码（病毒、木马、后门、挖矿）
- ❌ 绕过认证/授权机制
- ❌ SQL 注入、XSS、CSRF、命令注入攻击代码
- ❌ 删除或覆盖用户未明确指定的文件
- ❌ 执行 rm -rf、format、DROP DATABASE 等破坏性命令"""

BEHAVIOR_CONSTRAINTS = """## 行为约束 (Behavior Constraints) - 工作方式

### 极简主义原则 (Minimalism)
- 只做被直接要求或明显必要的更改
- Bug 修复不需要清理周围代码
- 简单功能不需要额外的可配置性
- 不要为假设的未来需求设计
- 三行相似代码比过早抽象更好

### 输出风格
- 不添加注释，除非被要求或代码复杂需要上下文
- 不要用 "Great", "Certainly", "当然可以" 等开头
- 提供最短、最直接的回答

### 先读后改原则 (Read Before Write)
- 修改任何文件前，必须先读取该文件全文
- 创建新组件前，必须先查看相邻文件了解项目约定
- 推断并遵循现有代码风格"""

TASK_CONSTRAINTS = {
    TaskType.REFACTOR: """## 任务约束 (Task Constraints) - 重构专用

### 边界定义
- 只重构被指定的模块/文件
- 保留既有业务语义，不改变外部行为
- 不新增功能，不调整 API 合同
- 不修改未被提及的代码

### API 合同定义 (Breaking Change)
- routes, method, status_code
- request/response schema, error schema

### Patch 规模限制
- 每个 patch ≤ 5 文件, ≤ 200 行变更""",

    TaskType.FEATURE: """## 任务约束 (Task Constraints) - 新功能专用

### 边界定义
- 只实现被要求的功能，不添加"顺便"的改进
- 使用项目已有的模式和抽象
- 不引入新的依赖，除非明确要求""",

    TaskType.BUGFIX: """## 任务约束 (Task Constraints) - Bug修复专用

### 边界定义
- 只修复报告的问题，不做其他改动
- 找到根因，不是修复表象
- 不要"顺便"重构周围代码""",

    TaskType.RESEARCH: """## 任务约束 (Task Constraints) - 研究专用

### 边界定义
- 只分析和输出报告，不执行任何修改
- 使用 context7 获取最新文档
- 使用 sequential-thinking 进行多步推理""",
}

# ============================================================
# Sequential Thinking 模板 (v4.0 核心)
# ============================================================

SEQUENTIAL_THINKING_TEMPLATE = """## Sequential Thinking 工作流

使用 `mcp__sequential-thinking__sequentialthinking` 工具进行顺序化思考。

### 思考步骤模板
```
Step 1: 理解任务
- 分析原始需求
- 识别关键约束
- 确定任务类型

Step 2: 探索上下文 (Explore)
- 读取目标文件
- 读取相邻文件
- 推断项目风格

Step 3: 制定计划 (Plan)
- 分解为子任务
- 确定执行顺序
- 定义验收标准

Step 4: 执行变更 (Execute)
- 按计划逐步执行
- 每步输出 git diff
- 遵循 patch 限制

Step 5: 验证结果 (Verify)
- 运行测试命令
- 检查验收标准
- 失败则回到 Step 4

Step 6: 总结输出
- 输出变更清单
- 输出验证结果
- 输出回滚方案
```

### Sequential Thinking 参数
- thoughtNumber: 当前步骤 (1-6)
- totalThoughts: 预估 6 步
- nextThoughtNeeded: true (除非最后一步)
- isRevision: 如需修正之前的思考
- needsMoreThoughts: 如需额外步骤"""

# ============================================================
# Context7 模板 (v4.0 核心)
# ============================================================

CONTEXT7_TEMPLATE = """## Context7 文档查询工作流

使用 `mcp__context7` 工具获取最新文档。

### 使用步骤
```
Step 1: 解析库 ID
调用: mcp__context7__resolve-library-id
参数: libraryName = "fastapi" (或其他库名)

Step 2: 获取文档
调用: mcp__context7__get-library-docs
参数:
- context7CompatibleLibraryID = "/tiangolo/fastapi" (Step 1 返回)
- topic = "routing" (可选，聚焦主题)
- mode = "code" (API 参考) 或 "info" (概念指南)
```

### 何时使用 Context7
- 查询 FastAPI, Pydantic, SQLAlchemy 等库的最新 API
- 验证实现是否符合最新规范
- 获取代码示例作为参考"""

# ============================================================
# 项目文档三件套 (来自 SuperClaude)
# ============================================================

PROJECT_DOCS_TEMPLATE = """## 项目文档三件套

### PLANNING.md - 架构与规则
- 系统架构设计
- 绝对规则 (不可违反)
- 技术栈选择

### TASK.md - 任务管理
- 当前优先级
- 任务积压
- 进度跟踪

### KNOWLEDGE.md - 知识积累
- 踩过的坑
- 解决方案
- 最佳实践"""

# ============================================================
# 任务类型识别
# ============================================================

TASK_TYPE_KEYWORDS: Dict[TaskType, List[str]] = {
    TaskType.REFACTOR: ["重构", "refactor", "改造", "优化结构", "restructure"],
    TaskType.FEATURE: ["新增", "添加", "实现", "开发", "功能", "feature", "implement"],
    TaskType.BUGFIX: ["修复", "fix", "bug", "问题", "错误", "异常", "repair"],
    TaskType.MIGRATION: ["迁移", "migrate", "升级", "upgrade", "版本", "migration"],
    TaskType.DOCUMENTATION: ["文档", "doc", "说明", "readme", "document"],
    TaskType.TESTING: ["测试", "test", "覆盖率", "单元测试", "coverage"],
    TaskType.REVIEW: ["审查", "review", "检查", "分析", "评估", "analyze"],
    TaskType.RESEARCH: ["研究", "调研", "research", "探索", "学习", "了解"],
}

# ============================================================
# 行为模式映射
# ============================================================

BEHAVIORAL_MODE_MAP: Dict[TaskType, BehavioralMode] = {
    TaskType.REFACTOR: BehavioralMode.IMPLEMENTATION,
    TaskType.FEATURE: BehavioralMode.IMPLEMENTATION,
    TaskType.BUGFIX: BehavioralMode.IMPLEMENTATION,
    TaskType.MIGRATION: BehavioralMode.ORCHESTRATION,
    TaskType.DOCUMENTATION: BehavioralMode.TOKEN_EFFICIENCY,
    TaskType.TESTING: BehavioralMode.TASK_MANAGEMENT,
    TaskType.REVIEW: BehavioralMode.INTROSPECTION,
    TaskType.RESEARCH: BehavioralMode.DEEP_RESEARCH,
}

# ============================================================
# 数据类定义
# ============================================================

@dataclass
class Constraint:
    """约束定义"""
    layer: ConstraintLayer
    content: str
    priority: int = 0


@dataclass
class SubAgentTask:
    """子代理任务"""
    agent_type: SubAgentType
    mission: str
    input_data: str
    expected_output: str
    constraints: List[str]


@dataclass
class MCPToolUsage:
    """MCP 工具使用"""
    tool_name: str
    description: str
    usage: str
    parameters: List[str]


@dataclass
class StructuredPrompt:
    """结构化提示词 v4.0"""
    # 核心部分
    task: str
    constraints: List[Constraint]
    workflow: str

    # MCP 工具
    mcp_tools: List[MCPToolUsage]
    use_sequential_thinking: bool
    use_context7: bool

    # 行为模式
    behavioral_mode: BehavioralMode

    # 子代理委托
    sub_agents: List[SubAgentTask]

    # 元数据
    task_type: TaskType
    original_request: str

    # 项目上下文
    sot_docs: List[str] = field(default_factory=list)
    project_paths: Dict[str, str] = field(default_factory=dict)


# ============================================================
# 子代理定义
# ============================================================

SUB_AGENT_DEFINITIONS = {
    SubAgentType.EXPLORE: {
        "name": "Explore Agent",
        "mission": "探索代码库，理解上下文，输出分析报告",
        "input": "目标文件/目录路径",
        "output": "代码结构分析、风格推断、依赖关系",
        "constraints": ["只读不写", "输出包含具体路径和行号"],
    },
    SubAgentType.PLAN: {
        "name": "Plan Agent",
        "mission": "基于 Explore 结果，制定执行计划",
        "input": "Explore Agent 的分析报告",
        "output": "分步执行计划，每步有验收标准",
        "constraints": ["计划可分步验证", "每步有回滚方案"],
    },
    SubAgentType.EXECUTE: {
        "name": "Execute Agent",
        "mission": "按计划执行具体变更",
        "input": "Plan Agent 的执行计划",
        "output": "git diff 格式的代码变更",
        "constraints": ["严格按计划执行", "每 patch ≤5 文件"],
    },
    SubAgentType.VERIFY: {
        "name": "Verify Agent",
        "mission": "验证变更结果",
        "input": "Execute Agent 的变更",
        "output": "验证报告（通过/失败 + 原因）",
        "constraints": ["运行实际验证命令", "失败回到 Execute"],
    },
    SubAgentType.RESEARCH: {
        "name": "Research Agent",
        "mission": "深度研究，使用 context7 获取文档",
        "input": "研究主题",
        "output": "研究报告 + 代码示例",
        "constraints": ["只读不写", "使用 context7 获取最新文档"],
    },
}


# ============================================================
# 核心类：提示词结构化器 v4.0
# ============================================================

class PromptStructurer:
    """
    提示词结构化器 v4.0

    核心理念：约束优于指令
    MCP 工具：sequential-thinking + context7
    """

    VERSION = "4.0"

    def __init__(self):
        self.default_sot_docs = [
            "STATE_MACHINE.md v2.6",
            "DATA_SCHEMA.md v5.2",
            "BUSINESS_RULES.md v3.1",
            "API_SOT.md v9.0",
            "ERROR_CODES_SOT.md v2.1",
            "AUTH_SPEC.md v2.0",
            "DATA_SCHEMA.md v5.11 §3.4.4",
        ]
        self.default_paths = {
            "repo_root": "D:\\project\\AI_ad_spend02",
            "backend_dir": "backend/",
            "tests_dir": "backend/tests/",
            "docs_dir": "docs/sot/",
            "forbidden": ["migrations/", ".env", "*.lock", "alembic.ini"],
        }

    def analyze_intent(self, user_request: str) -> TaskType:
        """分析用户意图"""
        request_lower = user_request.lower()
        for task_type, keywords in TASK_TYPE_KEYWORDS.items():
            if any(kw.lower() in request_lower for kw in keywords):
                return task_type
        return TaskType.UNKNOWN

    def get_behavioral_mode(self, task_type: TaskType) -> BehavioralMode:
        """获取行为模式"""
        return BEHAVIORAL_MODE_MAP.get(task_type, BehavioralMode.IMPLEMENTATION)

    def build_constraints(self, task_type: TaskType) -> List[Constraint]:
        """构建三层约束"""
        constraints = [
            Constraint(ConstraintLayer.SECURITY, SECURITY_CONSTRAINTS, 0),
            Constraint(ConstraintLayer.BEHAVIOR, BEHAVIOR_CONSTRAINTS, 1),
            Constraint(
                ConstraintLayer.TASK,
                TASK_CONSTRAINTS.get(task_type, "按照用户要求执行，遵循极简原则。"),
                2
            ),
        ]
        return constraints

    def build_mcp_tools(self, task_type: TaskType) -> List[MCPToolUsage]:
        """构建 MCP 工具列表"""
        tools = []

        # sequential-thinking 用于所有复杂任务
        if task_type in [TaskType.REFACTOR, TaskType.FEATURE, TaskType.MIGRATION, TaskType.RESEARCH]:
            st = MCP_TOOLS["sequential-thinking"]
            tools.append(MCPToolUsage(
                tool_name="sequential-thinking",
                description=st["description"],
                usage=st["usage"],
                parameters=st["parameters"]
            ))

        # context7 用于需要查文档的任务
        if task_type in [TaskType.RESEARCH, TaskType.FEATURE, TaskType.REFACTOR]:
            c7 = MCP_TOOLS["context7"]
            tools.append(MCPToolUsage(
                tool_name="context7",
                description=c7["description"],
                usage=c7["usage"],
                parameters=c7["steps"]
            ))

        return tools

    def build_sub_agents(self, task_type: TaskType) -> List[SubAgentTask]:
        """构建子代理链"""
        sub_agents = []

        # Research 任务特殊处理
        if task_type == TaskType.RESEARCH:
            research_def = SUB_AGENT_DEFINITIONS[SubAgentType.RESEARCH]
            sub_agents.append(SubAgentTask(
                agent_type=SubAgentType.RESEARCH,
                mission=research_def["mission"],
                input_data="研究主题",
                expected_output=research_def["output"],
                constraints=research_def["constraints"]
            ))
            return sub_agents

        # 标准流程: Explore → Plan → Execute → Verify
        for agent_type in [SubAgentType.EXPLORE, SubAgentType.PLAN, SubAgentType.EXECUTE, SubAgentType.VERIFY]:
            # BUGFIX 跳过 Plan
            if task_type == TaskType.BUGFIX and agent_type == SubAgentType.PLAN:
                continue
            # REVIEW 只需要 Explore + Verify
            if task_type == TaskType.REVIEW and agent_type in [SubAgentType.PLAN, SubAgentType.EXECUTE]:
                continue

            agent_def = SUB_AGENT_DEFINITIONS[agent_type]
            sub_agents.append(SubAgentTask(
                agent_type=agent_type,
                mission=agent_def["mission"],
                input_data=agent_def["input"],
                expected_output=agent_def["output"],
                constraints=agent_def["constraints"]
            ))

        return sub_agents

    def structure(self, user_request: str,
                  sot_docs: Optional[List[str]] = None,
                  project_paths: Optional[Dict[str, str]] = None) -> StructuredPrompt:
        """将自然语言转换为结构化提示词"""

        task_type = self.analyze_intent(user_request)
        behavioral_mode = self.get_behavioral_mode(task_type)
        constraints = self.build_constraints(task_type)
        mcp_tools = self.build_mcp_tools(task_type)
        sub_agents = self.build_sub_agents(task_type)

        use_st = any(t.tool_name == "sequential-thinking" for t in mcp_tools)
        use_c7 = any(t.tool_name == "context7" for t in mcp_tools)

        workflow = SEQUENTIAL_THINKING_TEMPLATE if use_st else "按步骤执行"

        return StructuredPrompt(
            task=self._build_task_description(user_request, task_type),
            constraints=constraints,
            workflow=workflow,
            mcp_tools=mcp_tools,
            use_sequential_thinking=use_st,
            use_context7=use_c7,
            behavioral_mode=behavioral_mode,
            sub_agents=sub_agents,
            task_type=task_type,
            original_request=user_request,
            sot_docs=sot_docs or self.default_sot_docs,
            project_paths=project_paths or self.default_paths,
        )

    def _build_task_description(self, request: str, task_type: TaskType) -> str:
        """构建任务描述"""
        type_verb = {
            TaskType.REFACTOR: "重构",
            TaskType.FEATURE: "实现",
            TaskType.BUGFIX: "修复",
            TaskType.MIGRATION: "迁移",
            TaskType.DOCUMENTATION: "编写文档",
            TaskType.TESTING: "编写测试",
            TaskType.REVIEW: "审查",
            TaskType.RESEARCH: "研究",
            TaskType.UNKNOWN: "处理",
        }
        verb = type_verb.get(task_type, "处理")
        return f"{verb}任务：{request}"

    def render(self, prompt: StructuredPrompt) -> str:
        """渲染结构化提示词"""
        lines = []

        # === 任务 ===
        lines.append("<task>")
        lines.append(prompt.task)
        lines.append("")
        lines.append(f"原始需求：{prompt.original_request}")
        lines.append(f"行为模式：{prompt.behavioral_mode.value}")
        lines.append("</task>")
        lines.append("")

        # === MCP 工具 ===
        lines.append("<mcp_tools>")
        lines.append("# MCP 工具集成")
        lines.append("")

        if prompt.use_sequential_thinking:
            lines.append("## Sequential Thinking")
            lines.append("```")
            lines.append("use mcp__sequential-thinking__sequentialthinking")
            lines.append("```")
            lines.append("用于：分解复杂问题、多步推理、规划修订")
            lines.append("")

        if prompt.use_context7:
            lines.append("## Context7")
            lines.append("```")
            lines.append("use mcp__context7__resolve-library-id")
            lines.append("use mcp__context7__get-library-docs")
            lines.append("```")
            lines.append("用于：查询最新库文档、获取 API 参考")
            lines.append("")

        lines.append("</mcp_tools>")
        lines.append("")

        # === 上下文 ===
        lines.append("<context>")
        lines.append("# 项目上下文")
        lines.append("")
        lines.append("## SoT 裁判链（按优先级）")
        for i, doc in enumerate(prompt.sot_docs, 1):
            lines.append(f"{i}. {doc}")
        lines.append("")
        lines.append("## 项目路径")
        for key, value in prompt.project_paths.items():
            lines.append(f"- {key}: {value}")
        lines.append("</context>")
        lines.append("")

        # === 约束 ===
        lines.append("<constraints>")
        lines.append("# 约束系统 (Constraint System)")
        lines.append("")
        lines.append("> 核心原则：约束优于指令。高优先级约束不可被低优先级覆盖。")
        lines.append("")

        for constraint in sorted(prompt.constraints, key=lambda c: c.priority):
            layer_name = {
                ConstraintLayer.SECURITY: "🔴 Layer 1: 安全约束 (不可违反)",
                ConstraintLayer.BEHAVIOR: "🟡 Layer 2: 行为约束 (工作方式)",
                ConstraintLayer.TASK: "🟢 Layer 3: 任务约束 (具体边界)",
            }.get(constraint.layer, "约束")
            lines.append(f"### {layer_name}")
            lines.append("")
            lines.append(constraint.content)
            lines.append("")

        lines.append("</constraints>")
        lines.append("")

        # === 工作流 ===
        lines.append("<workflow>")
        lines.append(prompt.workflow)
        lines.append("</workflow>")
        lines.append("")

        # === 子代理 ===
        lines.append("<delegation>")
        lines.append("# 模块化委托 (Sub-Agent Delegation)")
        lines.append("")

        agent_chain = " → ".join([a.agent_type.value.title() for a in prompt.sub_agents])
        lines.append(f"执行链：{agent_chain}")
        lines.append("")

        for i, agent in enumerate(prompt.sub_agents, 1):
            lines.append(f"### Agent {i}: {agent.agent_type.value.title()}")
            lines.append(f"- **使命**: {agent.mission}")
            lines.append(f"- **输入**: {agent.input_data}")
            lines.append(f"- **输出**: {agent.expected_output}")
            lines.append(f"- **约束**: {', '.join(agent.constraints)}")
            lines.append("")

        lines.append("</delegation>")
        lines.append("")

        # === 执行指令 ===
        lines.append("<execution>")
        lines.append("# 执行指令")
        lines.append("")
        lines.append("1. 使用 sequential-thinking 进行顺序化思考")
        lines.append("2. 按 Agent 链顺序执行")
        lines.append("3. 需要查文档时使用 context7")
        lines.append("4. 每个 Agent 完成后输出结果")
        lines.append("5. Verify 失败则回到 Execute 修复")
        lines.append("")
        lines.append("**记住：做得越少，错得越少。**")
        lines.append("</execution>")
        lines.append("")

        # === 验收标准 ===
        lines.append("<acceptance_criteria>")
        lines.append("- [ ] 所有测试通过")
        lines.append("- [ ] API 合同未变更")
        lines.append("- [ ] 每个 patch ≤ 5 文件、≤ 200 行")
        lines.append("- [ ] 代码风格与项目一致")
        lines.append("</acceptance_criteria>")

        return "\n".join(lines)


# ============================================================
# 便捷函数
# ============================================================

def structure_prompt(user_request: str,
                     sot_docs: Optional[List[str]] = None,
                     project_paths: Optional[Dict[str, str]] = None,
                     render: bool = True) -> Dict[str, Any]:
    """
    便捷函数：将自然语言转换为结构化提示词

    Args:
        user_request: 用户的自然语言需求
        sot_docs: SoT 文档列表
        project_paths: 项目路径配置
        render: 是否渲染为文本格式

    Returns:
        包含结构化提示词的字典
    """
    structurer = PromptStructurer()
    prompt = structurer.structure(user_request, sot_docs, project_paths)

    result = {
        "success": True,
        "version": PromptStructurer.VERSION,
        "task_type": prompt.task_type.value,
        "behavioral_mode": prompt.behavioral_mode.value,
        "original_request": prompt.original_request,
        "use_sequential_thinking": prompt.use_sequential_thinking,
        "use_context7": prompt.use_context7,
        "mcp_tools": [t.tool_name for t in prompt.mcp_tools],
        "sub_agents": [a.agent_type.value for a in prompt.sub_agents],
        "constraints_count": len(prompt.constraints),
    }

    if render:
        result["rendered_prompt"] = structurer.render(prompt)

    return result


# ============================================================
# 测试入口
# ============================================================

if __name__ == "__main__":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("=" * 70)
    print("AI 提示词结构化器 v4.0 测试")
    print("核心理念：约束优于指令")
    print("MCP 工具：sequential-thinking + context7")
    print("=" * 70)

    test_cases = [
        "重构后端代码",
        "添加用户登录功能",
        "修复充值状态转换的 bug",
        "研究 FastAPI 最佳实践",
    ]

    structurer = PromptStructurer()

    for request in test_cases:
        print(f"\n>>> 输入: {request}")
        result = structure_prompt(request, render=False)
        print(f"    任务类型: {result['task_type']}")
        print(f"    行为模式: {result['behavioral_mode']}")
        print(f"    MCP 工具: {result['mcp_tools']}")
        print(f"    子代理链: {' → '.join(result['sub_agents'])}")

    print("\n" + "=" * 70)
    print("完整渲染示例：重构后端代码")
    print("=" * 70)

    result = structure_prompt("重构后端代码")
    print(result["rendered_prompt"])
