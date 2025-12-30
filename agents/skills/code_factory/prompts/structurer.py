"""
提示词结构化器 v5.0

核心理念：约束优于指令 (Constraints Over Instructions)
将自然语言需求转换为 Claude 友好的结构化提示词。

v5.0 更新:
- 整合到 code_factory/prompts 模块
- 移除硬编码 SoT 版本，使用 PromptLoader 动态获取
- 保留 MCP 工具集成、行为模式、子代理定义

基准文档: MASTER.md v4.6
版本: v5.0
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .loader import PromptLoader


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
    DEEP_RESEARCH = "deep-research"
    ORCHESTRATION = "orchestration"
    TOKEN_EFFICIENCY = "token-efficiency"
    TASK_MANAGEMENT = "task-management"
    INTROSPECTION = "introspection"
    BRAINSTORMING = "brainstorming"
    IMPLEMENTATION = "implementation"


class SubAgentType(Enum):
    """子代理类型"""
    EXPLORE = "explore"
    PLAN = "plan"
    EXECUTE = "execute"
    VERIFY = "verify"
    RESEARCH = "research"


# ============================================================
# MCP 工具定义
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
    },
    "context7": {
        "description": "实时文档查询工具，获取最新库文档",
        "usage": "use mcp__context7__get-library-docs",
        "when_to_use": [
            "查询库/框架的最新文档",
            "获取 API 参考和代码示例",
            "验证实现是否符合最新规范",
        ],
    },
}


# ============================================================
# 任务类型关键词映射
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


@dataclass
class StructuredPrompt:
    """结构化提示词"""
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
# 核心类：提示词结构化器 v5.0
# ============================================================

class PromptStructurer:
    """
    提示词结构化器 v5.0
    
    核心理念：约束优于指令
    MCP 工具：sequential-thinking + context7
    
    v5.0 更新:
    - 使用 PromptLoader 动态加载约束模板
    - 移除硬编码 SoT 版本
    """
    
    VERSION = "5.0"
    
    def __init__(self, loader: Optional[PromptLoader] = None):
        """初始化
        
        Args:
            loader: 提示词模板加载器 (可选)
        """
        self.loader = loader
        self.default_paths = {
            "backend_dir": "backend/",
            "frontend_dir": "frontend/",
            "tests_dir": "backend/tests/",
            "docs_dir": "docs/sot/",
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
        constraints = []
        
        # Layer 1: 安全约束 (从模板加载或使用默认)
        security_content = ""
        if self.loader:
            security_content = self.loader.load("security")
        if not security_content:
            security_content = "## 安全约束\n- 禁止暴露密钥\n- 禁止编写恶意代码"
        constraints.append(Constraint(ConstraintLayer.SECURITY, security_content, 0))
        
        # Layer 2: 行为约束
        behavior_content = ""
        if self.loader:
            behavior_content = self.loader.load("behavior")
        if not behavior_content:
            behavior_content = "## 行为约束\n- 极简主义原则\n- 先读后改"
        constraints.append(Constraint(ConstraintLayer.BEHAVIOR, behavior_content, 1))
        
        # Layer 3: 任务约束
        task_content = ""
        if self.loader:
            task_content = self.loader.load(f"task/{task_type.value}")
        if not task_content:
            task_content = f"## 任务约束\n按照用户要求执行 {task_type.value} 任务"
        constraints.append(Constraint(ConstraintLayer.TASK, task_content, 2))
        
        return constraints
    
    def build_mcp_tools(self, task_type: TaskType) -> List[MCPToolUsage]:
        """构建 MCP 工具列表"""
        tools = []
        
        # sequential-thinking 用于复杂任务
        if task_type in [TaskType.REFACTOR, TaskType.FEATURE, TaskType.MIGRATION, TaskType.RESEARCH]:
            st = MCP_TOOLS["sequential-thinking"]
            tools.append(MCPToolUsage(
                tool_name="sequential-thinking",
                description=st["description"],
                usage=st["usage"]
            ))
        
        # context7 用于需要查文档的任务
        if task_type in [TaskType.RESEARCH, TaskType.FEATURE, TaskType.REFACTOR]:
            c7 = MCP_TOOLS["context7"]
            tools.append(MCPToolUsage(
                tool_name="context7",
                description=c7["description"],
                usage=c7["usage"]
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
        agent_sequence = [SubAgentType.EXPLORE, SubAgentType.PLAN, SubAgentType.EXECUTE, SubAgentType.VERIFY]
        
        for agent_type in agent_sequence:
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
    
    def structure(
        self, 
        user_request: str,
        project_paths: Optional[Dict[str, str]] = None
    ) -> StructuredPrompt:
        """将自然语言转换为结构化提示词"""
        
        task_type = self.analyze_intent(user_request)
        behavioral_mode = self.get_behavioral_mode(task_type)
        constraints = self.build_constraints(task_type)
        mcp_tools = self.build_mcp_tools(task_type)
        sub_agents = self.build_sub_agents(task_type)
        
        use_st = any(t.tool_name == "sequential-thinking" for t in mcp_tools)
        use_c7 = any(t.tool_name == "context7" for t in mcp_tools)
        
        workflow = self._build_workflow(use_st)
        
        # 加载系统约束获取 SoT 版本信息
        sot_docs = []
        if self.loader:
            system_content = self.loader.load("system")
            # 从内容中提取版本信息
            sot_docs = self._extract_sot_docs(system_content)
        
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
            sot_docs=sot_docs,
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
    
    def _build_workflow(self, use_sequential_thinking: bool) -> str:
        """构建工作流"""
        if use_sequential_thinking:
            return """## Sequential Thinking 工作流

Step 1: 理解任务 - 分析需求，识别约束
Step 2: 探索上下文 - 读取文件，推断风格
Step 3: 制定计划 - 分解任务，定义验收标准
Step 4: 执行变更 - 按计划执行，输出 diff
Step 5: 验证结果 - 运行测试，检查标准
Step 6: 总结输出 - 变更清单，回滚方案"""
        return "按步骤执行任务"
    
    def _extract_sot_docs(self, content: str) -> List[str]:
        """从系统约束内容中提取 SoT 文档列表"""
        import re
        docs = []
        # 匹配 "MASTER.md v4.6" 格式
        pattern = r'(\w+\.md)\s+(v[\d.]+)'
        matches = re.findall(pattern, content)
        for doc, version in matches:
            docs.append(f"{doc} {version}")
        return docs
    
    def render(self, prompt: StructuredPrompt) -> str:
        """渲染结构化提示词为文本"""
        lines = []
        
        # 任务
        lines.append("<task>")
        lines.append(prompt.task)
        lines.append(f"原始需求：{prompt.original_request}")
        lines.append(f"行为模式：{prompt.behavioral_mode.value}")
        lines.append("</task>")
        lines.append("")
        
        # MCP 工具
        if prompt.mcp_tools:
            lines.append("<mcp_tools>")
            for tool in prompt.mcp_tools:
                lines.append(f"## {tool.tool_name}")
                lines.append(f"用途: {tool.description}")
                lines.append(f"使用: {tool.usage}")
                lines.append("")
            lines.append("</mcp_tools>")
            lines.append("")
        
        # 约束
        lines.append("<constraints>")
        for constraint in sorted(prompt.constraints, key=lambda c: c.priority):
            lines.append(constraint.content)
            lines.append("")
        lines.append("</constraints>")
        lines.append("")
        
        # 工作流
        lines.append("<workflow>")
        lines.append(prompt.workflow)
        lines.append("</workflow>")
        lines.append("")
        
        # 子代理
        if prompt.sub_agents:
            lines.append("<delegation>")
            agent_chain = " → ".join([a.agent_type.value.title() for a in prompt.sub_agents])
            lines.append(f"执行链：{agent_chain}")
            lines.append("")
            for agent in prompt.sub_agents:
                lines.append(f"### {agent.agent_type.value.title()} Agent")
                lines.append(f"- 使命: {agent.mission}")
                lines.append(f"- 约束: {', '.join(agent.constraints)}")
                lines.append("")
            lines.append("</delegation>")
        
        return "\n".join(lines)


# ============================================================
# 便捷函数
# ============================================================

def structure_prompt(
    user_request: str,
    project_dir: Optional[Path] = None,
    render: bool = True
) -> Dict[str, Any]:
    """
    便捷函数：将自然语言转换为结构化提示词
    
    Args:
        user_request: 用户的自然语言需求
        project_dir: 项目目录 (用于加载自定义模板)
        render: 是否渲染为文本格式
        
    Returns:
        包含结构化提示词的字典
    """
    loader = None
    if project_dir:
        loader = PromptLoader(project_dir)
    
    structurer = PromptStructurer(loader)
    prompt = structurer.structure(user_request)
    
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

