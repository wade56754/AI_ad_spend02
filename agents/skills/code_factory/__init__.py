"""
AI 代码工厂 v6.0 - 轻量化 Hook 集成版

基准文档: MASTER.md v4.8, STATE_MACHINE.md v2.8, DATA_SCHEMA.md v5.7

v6.0 变更 (方案 C 实施):
- 移除与 Claude Code 重叠的功能 (CLI, RAG, Searcher 等)
- 核心验证能力迁移到 .claude/hooks/lib/
- 保留核心编排和安全验证模块

核心能力:
- SoT 验证: 角色白名单、状态机、Phase 边界
- 安全检查: 高风险模块检测、合规验证
- 任务管理: 任务列表、会话管理

架构说明:
- CodeFactory (factory.py): 主编排器
- SecurityValidator (security.py): 安全验证
- SoT 验证: 已迁移到 .claude/hooks/lib/sot_validator.py
"""

# 核心组件
from .task_list import TaskList, Task, TaskStatus
from .security import SecurityValidator, SoTComplianceChecker, ALLOWED_COMMANDS
from .session import SessionManager, SessionType, ProgressTracker
from .factory import CodeFactory, FactoryConfig, run_factory, create_factory

# 上下文引擎 (core 模块)
from .core import (
    ContextEngine,
    GenerationContext,
    run_context_engine,
    create_context_engine,
)

# 验证器
from .verifier import CodeVerifier, VerifyResult, VerifyDecision

# v5.0 - CLARIFY 阶段 (保留)
from .phases import (
    ClarifyPhase,
    ClarifyResult,
    ClarifiedRequirement,
    clarify_requirement,
    auto_clarify,
)

# v5.0 - 项目配置 (保留)
from .config import (
    ProjectConfig,
    ProjectConfigLoader,
    load_project_config,
)

# v5.0 - Agent 工具 (保留)
from .tools import (
    Tool,
    ToolResult,
    ToolRegistry,
)

__version__ = "6.0.0"
__all__ = [
    # 核心编排器
    "CodeFactory",
    "FactoryConfig",
    "run_factory",
    "create_factory",
    # 上下文引擎
    "ContextEngine",
    "GenerationContext",
    "run_context_engine",
    "create_context_engine",
    # 任务管理
    "TaskList",
    "Task",
    "TaskStatus",
    # 安全
    "SecurityValidator",
    "SoTComplianceChecker",
    "ALLOWED_COMMANDS",
    # 会话
    "SessionManager",
    "SessionType",
    "ProgressTracker",
    # 验证
    "CodeVerifier",
    "VerifyResult",
    "VerifyDecision",
    # v5.0 - CLARIFY
    "ClarifyPhase",
    "ClarifyResult",
    "ClarifiedRequirement",
    "clarify_requirement",
    "auto_clarify",
    # v5.0 - 配置
    "ProjectConfig",
    "ProjectConfigLoader",
    "load_project_config",
    # v5.0 - 工具
    "Tool",
    "ToolResult",
    "ToolRegistry",
]
