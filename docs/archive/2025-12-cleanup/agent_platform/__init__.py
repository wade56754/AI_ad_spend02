"""
Agent Platform - 可独立拆分的通用 Agent 基础设施

提供：
- AgentProtocol: Agent 标准协议
- AgentRegistry: 插件注册中心
- AgentRun/AgentRunStep: 执行记录模型
- OrchestratorBase: 编排器抽象基类
- LLM 客户端抽象和工厂
- 通用工具（fs_tool, validation, types）

使用方式：
```python
from agent_platform.core import AgentProtocol, register_agent, create_agent
from agent_platform.llm import get_llm_client
from agent_platform.tools import read_files, write_files
```
"""

__version__ = "0.1.0"
__author__ = "AI_ad_spend02 Team"

# 公开 API（延迟导入以避免循环依赖）
def __getattr__(name: str):
    # Core
    if name == "AgentProtocol":
        from .core.protocol import AgentProtocol
        return AgentProtocol
    if name == "AgentContext":
        from .core.protocol import AgentContext
        return AgentContext
    if name == "AgentRegistry":
        from .core.registry import AgentRegistry
        return AgentRegistry
    if name == "register_agent":
        from .core.registry import register_agent
        return register_agent
    if name == "create_agent":
        from .core.registry import create_agent
        return create_agent
    if name == "AgentRun":
        from .core.run import AgentRun
        return AgentRun
    if name == "AgentRunStep":
        from .core.run import AgentRunStep
        return AgentRunStep
    if name == "OrchestratorBase":
        from .core.orchestrator import OrchestratorBase
        return OrchestratorBase
    # LLM
    if name == "get_llm_client":
        from .llm.factory import get_llm_client
        return get_llm_client
    if name == "LLMClient":
        from .llm.base import LLMClient
        return LLMClient
    if name == "LLMResponse":
        from .llm.base import LLMResponse
        return LLMResponse
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "__version__",
    # Core
    "AgentProtocol",
    "AgentContext",
    "AgentRegistry",
    "register_agent",
    "create_agent",
    "AgentRun",
    "AgentRunStep",
    "OrchestratorBase",
    # LLM
    "get_llm_client",
    "LLMClient",
    "LLMResponse",
]
