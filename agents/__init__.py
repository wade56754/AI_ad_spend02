"""
agents - AI Agent 子系统

# Fix: P2-09 - 添加包级别 __init__.py

提供：
- Agent 创建和注册（agents_config）
- Agent 核心实现（agent_core）
- Skill 函数（skills）
- 工具函数（tools）
- CLI 入口（cli）
- HTTP Server（server）

基准对齐：
- Agent Layer Freeze v1.0
- MASTER.md v3.5

使用示例：
    from agents import create_agent, list_agents

    # 创建 Agent
    fe_agent = create_agent("fe")
    result = fe_agent.handle_request({"task": "...", "target_files": [...]})

    # 列出可用 Agent
    agents = list_agents()
"""

# Fix: P2-09 - 从 agents_config 导出核心 API
from .agents_config import (
    create_agent,
    list_agents,
    check_llm_available,
    AgentInfo,
)

# Fix: P2-09 - 从 agent_core 导出 Agent 类
from .agent_core import (
    FEAgent,
    BEAgent,
    TestAgent,
    DocAgent,
    CodeReviewAgent,
    OrchestratorAgent,
)

# Fix: P2-09 - 从 tools 导出常用类型
from .tools.types import (
    AgentResponse,
    SkillResult,
)

__version__ = "1.0.0"

__all__ = [
    # Factory functions
    "create_agent",
    "list_agents",
    "check_llm_available",
    "AgentInfo",
    # Agent classes
    "FEAgent",
    "BEAgent",
    "TestAgent",
    "DocAgent",
    "CodeReviewAgent",
    "OrchestratorAgent",
    # Types
    "AgentResponse",
    "SkillResult",
]
