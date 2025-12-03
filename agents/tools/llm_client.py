"""
llm_client.py - LLM 客户端统一管理（重导出层）

此文件已迁移为重导出层，所有实现已移至 agent_platform.llm。
保留此文件是为了向后兼容旧的导入路径。

⚠️ 重要: 新代码应直接使用 agent_platform.llm 模块
  from agent_platform.llm import get_llm_client, extract_response_text, reset_client

Phase 3.2: 修复 P0-01 - 消除 MCP 模式绕过风险
- 旧版本包含独立的 get_llm_client() 实现，没有 MCP 模式检查
- 现在改为从 agent_platform.llm 重导出，确保 MCP 模式检查生效

基准对齐：
- Agent Layer Freeze v1.0
- MASTER.md v3.5
- MCP Mode Phase 3.2
"""

# Re-export from canonical source (agent_platform.llm)
# This ensures MCP mode checks are enforced regardless of import path
from agent_platform.llm import (
    get_llm_client,
    extract_response_text,
    reset_client,
)

__all__ = [
    "get_llm_client",
    "extract_response_text",
    "reset_client",
]