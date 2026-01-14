"""
AI 代码工厂 v7.0 - 核心模块

包含:
- factory.py: 上下文增强引擎 (ContextEngine)
- config.py: 配置类
- feature_flags.py: 功能开关
- exceptions.py: 自定义异常
- constants.py: 常量定义
- logging.py: 统一日志 (v7.0 新增)

注意: ContextEngine 与外层 factory.py 中的 CodeFactory 是不同组件:
- CodeFactory (外层): 完整的 5 阶段流水线编排
- ContextEngine (本模块): 上下文构建、验证和确认
"""

from .config import FactoryConfig
from .feature_flags import FeatureFlags, get_flags
from .exceptions import (
    CodeFactoryError,
    SotVersionMismatchError,
    RiskBlockedError,
    TraceFailedError,
    EditRejectedError,
)
from .constants import VERSION, PHASE_NAMES

# v7.0: 统一日志
from .logging import (
    get_logger,
    set_context,
    get_context,
    log_context,
    log_phase,
    log_timing,
    PhaseLogger,
    LogContext,
)
from .factory import (
    ContextEngine,
    GenerationContext,
    VerifyResult,
    ConfirmResult,
    FactoryResult,
    run_context_engine,
    create_context_engine,
)

# 执行引擎（新）
from .agent_executor import AgentExecutor, ExecutionResult
from .task_queue import TaskQueue, ExecutionPattern
from .monitoring import PerformanceMonitor, PerformanceMetrics, get_monitor
from .orchestrator import CodeFactoryOrchestrator, OrchestrationContext

__all__ = [
    # 配置
    "FactoryConfig",
    "FeatureFlags",
    "get_flags",
    # 异常
    "CodeFactoryError",
    "SotVersionMismatchError",
    "RiskBlockedError",
    "TraceFailedError",
    "EditRejectedError",
    # 常量
    "VERSION",
    "PHASE_NAMES",
    # v7.0: 统一日志
    "get_logger",
    "set_context",
    "get_context",
    "log_context",
    "log_phase",
    "log_timing",
    "PhaseLogger",
    "LogContext",
    # 上下文引擎
    "ContextEngine",
    "GenerationContext",
    "VerifyResult",
    "ConfirmResult",
    "FactoryResult",
    "run_context_engine",
    "create_context_engine",
    # 执行引擎（新）
    "AgentExecutor",
    "ExecutionResult",
    "TaskQueue",
    "ExecutionPattern",
    "PerformanceMonitor",
    "PerformanceMetrics",
    "get_monitor",
    "CodeFactoryOrchestrator",
    "OrchestrationContext",
]
