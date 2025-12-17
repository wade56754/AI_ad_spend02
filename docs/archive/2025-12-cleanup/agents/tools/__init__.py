"""
工具模块：提供文件系统、Supabase、LLM 客户端等基础工具

Phase 2 Migration: LLM 客户端迁移到 agent_platform.llm
- get_llm_client: 现在从 agent_platform.llm 导入
- extract_response_text: 现在从 agent_platform.llm 导入
- reset_client: 现在从 agent_platform.llm 导入

Phase 3 新增:
- sot_loader: 统一 SoT 文档加载器
- auto_fix_loop: 自动修复循环机制

旧的 llm_client.py 保留作为兼容层，但新代码应直接使用 agent_platform.llm
"""

from .fs_tool import read_files, write_files
from .supabase_tool import SupabaseTool
# Phase 2: LLM 客户端迁移到 agent_platform.llm
from agent_platform.llm import get_llm_client, extract_response_text, reset_client
from .types import AgentResponse, SkillResult, SotViolationDict, ReviewResult
from .validation import validate_task_and_files
# Phase 3: SoT Loader 和 Auto-Fix Loop
from .sot_loader import (
    SoTLoader,
    SoTSnapshot,
    SoTDependency,
    get_sot_loader,
    load_sot_for_skill,
    load_sot,
)
from .auto_fix_loop import (
    AutoFixLoop,
    AutoFixResult,
    FixRound,
    TestResult,
    run_auto_fix,
)

__all__ = [
    # 文件工具
    "read_files",
    "write_files",
    # Supabase 工具
    "SupabaseTool",
    # LLM 客户端 (from agent_platform.llm)
    "get_llm_client",
    "extract_response_text",
    "reset_client",
    # 类型定义
    "AgentResponse",
    "SkillResult",
    "SotViolationDict",
    "ReviewResult",
    # 校验工具
    "validate_task_and_files",
    # SoT Loader (Phase 3)
    "SoTLoader",
    "SoTSnapshot",
    "SoTDependency",
    "get_sot_loader",
    "load_sot_for_skill",
    "load_sot",
    # Auto-Fix Loop (Phase 3)
    "AutoFixLoop",
    "AutoFixResult",
    "FixRound",
    "TestResult",
    "run_auto_fix",
]
