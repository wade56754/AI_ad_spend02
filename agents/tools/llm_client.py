"""
llm_client.py - LLM 客户端统一管理（Anthropic API + Claude Code CLI 双后端）

提供线程安全的 LLM 客户端单例，按优先级选择后端：
1) 如果设置了 ANTHROPIC_API_KEY，则使用 Anthropic 官方 API
2) 否则回退到 Claude Code CLI（面向 Claude Max 订阅场景）

基准对齐：
- Agent Layer Freeze v1.0
- MASTER.md v3.5
"""

from typing import Any, List, Optional
import importlib.util
import logging
import os
import threading

logger = logging.getLogger(__name__)

# 线程安全的客户端单例
_client: Optional[Any] = None
_client_lock = threading.Lock()


def get_llm_client() -> Any:
    """
    获取 LLM 客户端单例（线程安全）。

    环境变量：
        - ANTHROPIC_API_KEY (必需): Anthropic API密钥
        - ANTHROPIC_BASE_URL (可选): 自定义API基础URL（用于代理）

    Thread Safety:
        使用双重检查锁定模式，确保线程安全的单例初始化。

    Backend Priority:
        1) Anthropic API（当 ANTHROPIC_API_KEY 存在）
        2) Claude Code CLI（当未设置 API Key 时自动回退）

    Returns:
        Anthropic 或 ClaudeCodeClient 客户端实例

    Raises:
        RuntimeError: 未找到可用的 LLM 后端
    """
    global _client

    # Fast path: 客户端已初始化
    if _client is not None:
        return _client

    with _client_lock:
        # 双重检查
        if _client is not None:
            return _client

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        base_url = os.environ.get("ANTHROPIC_BASE_URL")

        # 1) 优先使用 Anthropic API
        if api_key:
            _client = _init_anthropic_client(api_key=api_key, base_url=base_url)
            logger.info("LLM backend initialized: anthropic_api")
        else:
            # 2) 回退 Claude Code CLI
            _client = _init_claude_code_client()
            logger.info("LLM backend initialized: claude_code (fallback)")

    return _client


def _init_anthropic_client(api_key: str, base_url: Optional[str]) -> Any:
    """初始化 Anthropic 官方客户端。"""

    if importlib.util.find_spec("anthropic") is None:
        raise RuntimeError("anthropic 包未安装。请运行: pip install anthropic")

    from anthropic import Anthropic

    try:
        kwargs = {}
        if base_url:
            kwargs["base_url"] = base_url
            logger.info(f"Using Anthropic API with custom base URL: {base_url}")
        else:
            logger.info("Using Anthropic API (official endpoint)")

        client = Anthropic(api_key=api_key, **kwargs)
        logger.debug(f"Anthropic client initialized (key: {api_key[:10]}...)")
        return client
    except Exception as e:
        raise RuntimeError(f"初始化 Anthropic 客户端失败: {e}")


def _init_claude_code_client() -> Any:
    """初始化 Claude Code CLI 客户端。"""

    from .claude_code_adapter import (
        ClaudeCodeClient,
        check_claude_code_available,
    )

    status = check_claude_code_available()
    if not status.get("available"):
        raise RuntimeError(
            "Claude Code CLI 不可用："
            f"{status.get('error') or '未找到可执行文件'}"
        )

    logger.info("Using Claude Code CLI (fallback backend)")
    return ClaudeCodeClient()


def extract_response_text(resp: Any) -> str:
    """
    从 Anthropic API 响应中提取文本内容。

    处理响应格式：
    - resp.content: List[ContentBlock]
    - ContentBlock.type == "text"
    - ContentBlock.text: str

    Args:
        resp: Anthropic API 响应对象

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

    调用后，下次 get_llm_client() 会重新创建客户端。
    """
    global _client
    with _client_lock:
        _client = None
        logger.info("LLM client reset, will reinitialize on next call")


__all__ = [
    "get_llm_client",
    "extract_response_text",
    "reset_client",
]