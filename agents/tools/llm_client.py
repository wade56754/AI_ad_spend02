"""
llm_client.py - LLM 客户端统一管理

# Fix: P1-03 - 从 fe_dev_skill/be_dev_skill 提取重复的 LLM 客户端逻辑
# Fix: NEW-02 - 修复 _use_claude_code 在模块加载时固定的问题

提供线程安全的 LLM 客户端单例，支持：
1. Anthropic API（需要 ANTHROPIC_API_KEY 环境变量）
2. Claude Code CLI（支持 Claude Max 订阅用户）

基准对齐：
- Agent Layer Freeze v1.0
- MASTER.md v3.5
"""

from typing import Any, List, Optional
import logging
import os
import threading

logger = logging.getLogger(__name__)

# Fix: P1-03 - 线程安全的客户端单例
_client: Optional[Any] = None
_client_lock = threading.Lock()
_current_backend: Optional[str] = None  # Fix: NEW-02 - 记录当前后端类型


def _should_use_claude_code() -> bool:
    """
    判断是否使用 Claude Code CLI。

    # Fix: NEW-02 - 每次调用时检查环境变量，而非模块加载时固定

    Returns:
        True: 使用 Claude Code CLI
        False: 使用 Anthropic API
    """
    return not bool(os.environ.get("ANTHROPIC_API_KEY"))


def get_llm_client() -> Any:
    """
    获取 LLM 客户端单例（线程安全）。

    # Fix: P1-03 - 统一的客户端获取函数
    # Fix: NEW-02 - 支持运行时切换后端（环境变量变化时重新创建客户端）

    优先级：
    1. 如果设置了 ANTHROPIC_API_KEY，使用 Anthropic API
    2. 否则使用 Claude Code CLI 适配器

    Thread Safety:
        使用双重检查锁定模式，确保线程安全的单例初始化。

    Returns:
        Anthropic 客户端或 ClaudeCodeClient 实例
    """
    global _client, _current_backend

    use_claude_code = _should_use_claude_code()
    expected_backend = "claude_code" if use_claude_code else "anthropic_api"

    # Fix: NEW-02 - 如果后端类型变化，重新创建客户端
    if _client is not None and _current_backend == expected_backend:
        return _client

    with _client_lock:
        # 双重检查
        if _client is not None and _current_backend == expected_backend:
            return _client

        # 后端变化或首次创建
        if _current_backend != expected_backend:
            if _current_backend is not None:
                logger.info(f"LLM backend changed: {_current_backend} -> {expected_backend}")
            _client = None

        if _client is None:
            if use_claude_code:
                from .claude_code_adapter import ClaudeCodeClient
                logger.info("Using Claude Code CLI adapter (no ANTHROPIC_API_KEY found)")
                _client = ClaudeCodeClient()
            else:
                from anthropic import Anthropic
                logger.info("Using Anthropic API")
                _client = Anthropic()
            _current_backend = expected_backend

    return _client


def extract_response_text(resp: Any) -> str:
    """
    从 LLM API 响应中提取文本内容。

    # Fix: P1-03 - 统一的响应文本提取函数

    处理以下响应格式：
    - Anthropic API 响应对象
    - ClaudeCodeClient mock 响应

    Args:
        resp: LLM API 响应对象

    Returns:
        提取的文本内容
    """
    if not hasattr(resp, "content"):
        return str(resp)

    text_parts: List[str] = []
    for item in resp.content:
        # 处理嵌套列表（某些 API 版本）
        if isinstance(item, list):
            for block in item:
                if getattr(block, "type", None) == "text":
                    text_parts.append(block.text)
        # 处理单个块
        elif getattr(item, "type", None) == "text":
            text_parts.append(item.text)

    return "".join(text_parts)


def reset_client() -> None:
    """
    重置 LLM 客户端（用于测试或运行时切换）。

    # Fix: NEW-02 - 提供手动重置入口

    调用后，下次 get_llm_client() 会重新创建客户端。
    """
    global _client, _current_backend
    with _client_lock:
        _client = None
        _current_backend = None
        logger.info("LLM client reset, will reinitialize on next call")


__all__ = [
    "get_llm_client",
    "extract_response_text",
    "reset_client",
]
