"""
agent_platform.agents - Agent 子系统

Phase 2: Agent 层迁移
- 提供 MCP 安全的 Agent 实现
- 统一 Agent 注册与发现机制
- mcp_safe=True 的 Agent 可在 MCP 模式下安全运行

设计原则:
- mcp_safe 是注册时的"唯一真相"，禁止在多处重复维护
- 所有 Agent 通过 registry 注册，不直接导出类（除非需要继承）
- MCP 模式下只暴露 mcp_safe=True 的 Agent

使用示例:
```python
from agent_platform.agents import (
    list_agents,
    list_mcp_safe_agents,
    create_agent,
    is_agent_mcp_safe,
)

# 列出所有 Agent
for meta in list_agents():
    print(f"{meta.name}: mcp_safe={meta.mcp_safe}")

# 列出 MCP 安全的 Agent
safe_agents = list_mcp_safe_agents()

# 创建 Agent 实例
agent = create_agent("test")
result = agent.handle_request({"mode": "db"})
```

基准对齐:
- AGENT_PLATFORM_MIGRATION_PLAN_v1.2.md Phase 2
- MASTER.md v3.5
- Agent Layer Freeze v1.0
"""

# Re-export from core registry
from agent_platform.core.registry import (
    AgentMeta,
    AgentRegistry,
    get_registry,
    register_agent,
    create_agent,
    list_agents,
    list_mcp_safe_agents,
    is_agent_mcp_safe,
)

# Re-export protocol
from agent_platform.core.protocol import AgentProtocol, AgentContext

# Import agent modules to trigger registration
# Order matters: pure_logic first, then llm_dependent (to override with mcp_safe info)
from . import pure_logic  # MCP safe agents (test, review, doc)
from . import llm_dependent  # LLM-dependent agents (fe, be, orch)

__all__ = [
    # Registry
    "AgentMeta",
    "AgentRegistry",
    "get_registry",
    "register_agent",
    "create_agent",
    "list_agents",
    "list_mcp_safe_agents",
    "is_agent_mcp_safe",
    # Protocol
    "AgentProtocol",
    "AgentContext",
]
