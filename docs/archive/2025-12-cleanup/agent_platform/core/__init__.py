"""
Agent Platform Core Module

提供核心抽象：
- AgentProtocol: Agent 标准协议
- AgentContext: 执行上下文
- AgentRegistry: 插件注册中心
- AgentRun/AgentRunStep: 执行记录
- OrchestratorBase: 编排器基类
"""

from .protocol import AgentProtocol, AgentContext
from .registry import (
    AgentRegistry,
    AgentMeta,
    get_registry,
    register_agent,
    create_agent,
    list_agents,
)
from .run import AgentRun, AgentRunStep, RunStatus
from .orchestrator import OrchestratorBase
from .exceptions import (
    AgentPlatformError,
    AgentNotFoundError,
    AgentRegistrationError,
    AgentExecutionError,
)
from .logging_utils import (
    ErrorKind,
    log_event,
    derive_error_kind,
    create_error_response,
)

__all__ = [
    # Protocol
    "AgentProtocol",
    "AgentContext",
    # Registry
    "AgentRegistry",
    "AgentMeta",
    "get_registry",
    "register_agent",
    "create_agent",
    "list_agents",
    # Run
    "AgentRun",
    "AgentRunStep",
    "RunStatus",
    # Orchestrator
    "OrchestratorBase",
    # Exceptions
    "AgentPlatformError",
    "AgentNotFoundError",
    "AgentRegistrationError",
    "AgentExecutionError",
    # Logging & Observability
    "ErrorKind",
    "log_event",
    "derive_error_kind",
    "create_error_response",
]
