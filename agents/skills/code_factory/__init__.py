"""
AI 代码工厂 v5.0 - AI 编程助手升级版

基准文档: MASTER.md v4.6, STATE_MACHINE.md v2.8, DATA_SCHEMA.md v5.6

借鉴开源项目最佳实践:
- gpt-engineer: Preprompts 系统、增量改进模式
- Dify: RAG 知识库、工作流编排
- awesome-cursorrules: 规则配置化、多项目模板

v5.0 新增能力:
- Preprompts 系统: 可配置的提示词模板
- CLARIFY 阶段: 需求澄清
- RAG 知识库: 文档索引与语义检索
- 项目配置: .codefactory.yaml
- Agent 工具: 可扩展的工具框架
- CLI 命令行: 交互模式与一次性生成

架构说明:
- CodeFactory (factory.py): 主编排器，管理完整的 7 阶段流水线
  CLARIFY → SEARCH → SELECT → ADAPT → ASSEMBLE → VERIFY → CONFIRM
- ContextEngine (core/factory.py): 上下文构建器，专注于 SoT 加载、验证
"""

# 核心组件
from .task_list import TaskList, Task, TaskStatus
from .security import SecurityValidator, SoTComplianceChecker, ALLOWED_COMMANDS
from .session import SessionManager, SessionType, ProgressTracker
from .factory import CodeFactory, FactoryConfig, run_factory, create_factory

# 上下文引擎 (core 模块)
from .core import ContextEngine, GenerationContext, run_context_engine, create_context_engine

# 子 Skill 组件
from .searcher import CodeSearcher, SearchCandidate, SearchResult
from .selector import CodeSelector, SelectionResult, AdaptationPlan
from .adapter import CodeAdapter, AdaptResult, AdaptedFile
from .assembler import CodeAssembler, AssembleResult
from .verifier import CodeVerifier, VerifyResult, VerifyDecision

# v5.0 新增 - Preprompts 系统
from .prompts import (
    Preprompts, 
    PrepromptType, 
    PrepromptSet, 
    ProjectTemplate,
    create_preprompts,
)

# v5.0 新增 - CLARIFY 阶段
from .phases import (
    ClarifyPhase,
    ClarifyResult,
    ClarifiedRequirement,
    clarify_requirement,
    auto_clarify,
)

# v5.0 新增 - 项目配置
from .config import (
    ProjectConfig,
    ProjectConfigLoader,
    load_project_config,
)

# v5.0 新增 - RAG 知识库
from .rag import (
    KnowledgeBase,
    KnowledgeBaseConfig,
    DocumentIndexer,
    DocumentRetriever,
    create_knowledge_base,
)

# v5.0 新增 - Agent 工具
from .tools import (
    Tool,
    ToolResult,
    ToolRegistry,
)

# v5.0 新增 - CLI
from .cli import CodeFactoryCLI, main as cli_main

__version__ = "5.0.0"
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
    # v5.0 - Preprompts
    "Preprompts",
    "PrepromptType",
    "PrepromptSet",
    "ProjectTemplate",
    "create_preprompts",
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
    # v5.0 - RAG
    "KnowledgeBase",
    "KnowledgeBaseConfig",
    "DocumentIndexer",
    "DocumentRetriever",
    "create_knowledge_base",
    # v5.0 - 工具
    "Tool",
    "ToolResult",
    "ToolRegistry",
    # v5.0 - CLI
    "CodeFactoryCLI",
    "cli_main",
]
