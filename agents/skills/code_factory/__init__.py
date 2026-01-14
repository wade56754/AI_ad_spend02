"""
AI 代码工厂 v7.0 - Superpowers 集成版

基准文档: MASTER.md v4.8, STATE_MACHINE.md v2.8, DATA_SCHEMA.md v5.7

v7.0 变更:
- 删除 stubs.py 废弃占位代码
- 新增 LightweightOrchestrator 轻量编排器
- 新增 5 阶段流水线 (CLARIFY → PLAN → IMPLEMENT → REVIEW → CONFIRM)
- 集成 Superpowers 方法论技能 (TDD, 两阶段审查)
- 新增 types.py 核心数据类型

核心能力:
- TDD 强制: 先写测试再写实现
- 两阶段审查: 规格合规 → 代码质量
- 幻觉抑制: 状态/角色/字段追溯验证
- SoT 验证: 角色白名单、状态机、Phase 边界

架构说明:
- LightweightOrchestrator (orchestrator.py): 新轻量编排器
- CodeFactory (factory.py): 旧编排器 (向后兼容)
- SecurityValidator (security.py): 安全验证
"""

# 核心组件
from .task_list import TaskList, Task, TaskStatus
from .security import SecurityValidator, SoTComplianceChecker, ALLOWED_COMMANDS
from .session import SessionManager, SessionType, ProgressTracker
from .factory import CodeFactory, FactoryConfig, run_factory, create_factory

# v7.0: 新轻量编排器
from .orchestrator import LightweightOrchestrator, create_orchestrator, run_pipeline

# v7.0: 核心数据类型
from .types import (
    PhaseType,
    ReviewStage,
    AdaptedFile,
    GeneratedFile,
    TaskSpec,
    ImplementationPlan,
    ReviewIssue,
    ExecutionContext,
)

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

__version__ = "7.0.0"
__all__ = [
    # v7.0 轻量编排器
    "LightweightOrchestrator",
    "create_orchestrator",
    "run_pipeline",
    # v7.0 核心数据类型
    "PhaseType",
    "ReviewStage",
    "AdaptedFile",
    "GeneratedFile",
    "TaskSpec",
    "ImplementationPlan",
    "ReviewIssue",
    "ExecutionContext",
    # 旧编排器 (向后兼容)
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
