"""
工具模块：提供文件系统、Supabase、LLM 客户端等基础工具

Phase 2 Migration: LLM 客户端迁移到 agent_platform.llm
- get_llm_client: 现在从 agent_platform.llm 导入
- extract_response_text: 现在从 agent_platform.llm 导入
- reset_client: 现在从 agent_platform.llm 导入

旧的 llm_client.py 保留作为兼容层，但新代码应直接使用 agent_platform.llm
"""

from .fs_tool import read_files, write_files
from .supabase_tool import SupabaseTool
# Phase 2: LLM 客户端迁移到 agent_platform.llm
from agent_platform.llm import get_llm_client, extract_response_text, reset_client
from .types import AgentResponse, SkillResult, SotViolationDict, ReviewResult
from .validation import validate_task_and_files

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
]
