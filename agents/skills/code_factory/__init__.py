"""
AI 代码工厂 v3.0 - 自主编码集成版

借鉴 Anthropic autonomous-coding 项目的核心设计:
- 双 Agent 模式 (Initializer + Factory)
- task_list.json 持久化
- 会话管理与恢复
- Defense-in-Depth 安全模型

结合我们的 5 阶段流水线:
SEARCH → SELECT → ADAPT → ASSEMBLE → VERIFY
"""

# 核心组件
from .task_list import TaskList, Task, TaskStatus
from .security import SecurityValidator, SoTComplianceChecker, ALLOWED_COMMANDS
from .session import SessionManager, SessionType, ProgressTracker
from .factory import CodeFactory, FactoryConfig, run_factory, create_factory

# 子 Skill 组件
from .searcher import CodeSearcher, SearchCandidate, SearchResult
from .selector import CodeSelector, SelectionResult, AdaptationPlan
from .adapter import CodeAdapter, AdaptResult, AdaptedFile
from .assembler import CodeAssembler, AssembleResult
from .verifier import CodeVerifier, VerifyResult, VerifyDecision

__version__ = "3.0"
__all__ = [
    # 核心
    "TaskList",
    "Task",
    "TaskStatus",
    "SecurityValidator",
    "SoTComplianceChecker",
    "ALLOWED_COMMANDS",
    "SessionManager",
    "SessionType",
    "ProgressTracker",
    "CodeFactory",
    "FactoryConfig",
    "run_factory",
    "create_factory",
    # 子 Skill
    "CodeSearcher",
    "SearchCandidate",
    "SearchResult",
    "CodeSelector",
    "SelectionResult",
    "AdaptationPlan",
    "CodeAdapter",
    "AdaptResult",
    "AdaptedFile",
    "CodeAssembler",
    "AssembleResult",
    "CodeVerifier",
    "VerifyResult",
    "VerifyDecision",
]
