"""
Agent Platform LLM Module

提供 LLM 客户端抽象和工厂函数。

公开 API:
- LLMClient: LLM 客户端抽象基类
- LLMResponse: LLM 响应模型
- DummyLLMClient: 占位客户端（测试/无 Key 环境）
- get_llm_client: 获取 LLM 客户端实例
- extract_response_text: 从响应中提取文本
- reset_client: 重置客户端单例
- get_backend_type: 获取当前后端类型
- is_mcp_mode: 检查是否在 MCP 工具模式
- get_platform_mode: 获取当前平台模式
"""

from .base import LLMClient, LLMResponse, DummyLLMClient
from .factory import (
    get_llm_client,
    reset_client,
    get_backend_type,
    extract_response_text,
    is_mcp_mode,
    get_platform_mode,
)

__all__ = [
    "LLMClient",
    "LLMResponse",
    "DummyLLMClient",
    "get_llm_client",
    "extract_response_text",
    "reset_client",
    "get_backend_type",
    "is_mcp_mode",
    "get_platform_mode",
]
