"""
llm_client.py - LLM 客户端统一管理（双后端策略）

提供线程安全的 LLM 客户端单例，支持以下后端优先级：
1. Anthropic 官方 API（需要 ANTHROPIC_API_KEY）
2. Claude Code CLI 适配器（ClaudeCodeClient，支持 Claude Max 订阅）

后端策略：
- 优先使用 Anthropic API（如果 ANTHROPIC_API_KEY 存在）
- 否则回退到 Claude Code CLI（如果已安装）
- 两者都不可用时抛出清晰的 RuntimeError

基准对齐：
- Agent Layer Freeze v1.0
- MASTER.md v3.5
"""

from typing import Any, List, Optional
import logging
import os
import threading

logger = logging.getLogger(__name__)

# 线程安全的客户端单例
_client: Optional[Any] = None
_client_lock = threading.Lock()
_backend_type: Optional[str] = None  # "anthropic_api" or "claude_code"


def get_llm_client() -> Any:
    """
    获取 LLM 客户端单例（线程安全，双后端策略）。

    后端优先级：
        1. Anthropic 官方 API（如果 ANTHROPIC_API_KEY 存在）
        2. Claude Code CLI 适配器（如果 CLI 已安装）

    环境变量：
        - ANTHROPIC_API_KEY (可选): Anthropic API密钥，存在时使用官方 API
        - ANTHROPIC_BASE_URL (可选): 自定义API基础URL（用于代理）

    Thread Safety:
        使用双重检查锁定模式，确保线程安全的单例初始化。

    Returns:
        Anthropic 客户端实例 或 ClaudeCodeClient 实例
        两者都实现 messages.create() 接口

    Raises:
        RuntimeError: 两种后端都不可用时
    """
    global _client, _backend_type

    # Fast path: 客户端已初始化
    if _client is not None:
        return _client

    with _client_lock:
        # 双重检查
        if _client is not None:
            return _client

        # 策略 1: 检查 Anthropic API Key
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            _client = _create_anthropic_client(api_key)
            _backend_type = "anthropic_api"
            return _client

        # 策略 2: 回退到 Claude Code CLI
        logger.info("ANTHROPIC_API_KEY not set, falling back to Claude Code CLI")
        _client = _create_claude_code_client()
        _backend_type = "claude_code"
        return _client


def _create_anthropic_client(api_key: str) -> Any:
    """
    创建 Anthropic 官方 API 客户端。

    Args:
        api_key: Anthropic API 密钥

    Returns:
        Anthropic 客户端实例

    Raises:
        RuntimeError: anthropic 包未安装或初始化失败
    """
    base_url = os.environ.get("ANTHROPIC_BASE_URL")

    try:
        from anthropic import Anthropic

        kwargs = {}
        if base_url:
            kwargs["base_url"] = base_url
            logger.info(f"Using Anthropic API with custom base URL: {base_url}")
        else:
            logger.info("Using Anthropic API (official endpoint)")

        client = Anthropic(api_key=api_key, **kwargs)
        logger.debug(f"Anthropic client initialized (key: {api_key[:10]}...)")
        return client

    except ImportError:
        raise RuntimeError(
            "anthropic 包未安装。请运行: pip install anthropic"
        )
    except Exception as e:
        raise RuntimeError(f"初始化 Anthropic 客户端失败: {e}")


def _create_claude_code_client() -> Any:
    """
    创建 Claude Code CLI 适配器客户端。

    Returns:
        ClaudeCodeClient 实例

    Raises:
        RuntimeError: Claude Code CLI 不可用
    """
    try:
        from .claude_code_adapter import ClaudeCodeClient, check_claude_code_available

        # 检查 CLI 是否可用
        cli_status = check_claude_code_available()
        if not cli_status["available"]:
            raise RuntimeError(
                "无法初始化 LLM 客户端。\n"
                "解决方案（任选其一）：\n"
                "  1. 设置环境变量 ANTHROPIC_API_KEY\n"
                "  2. 安装 Claude Code CLI: npm install -g @anthropic-ai/claude-code\n"
                f"错误详情: {cli_status.get('error', 'Unknown')}"
            )

        logger.info(
            f"Using Claude Code CLI (path: {cli_status.get('path')}, "
            f"version: {cli_status.get('version')})"
        )
        return ClaudeCodeClient()

    except ImportError as e:
        raise RuntimeError(
            f"无法导入 claude_code_adapter 模块: {e}"
        )


def get_backend_type() -> Optional[str]:
    """
    获取当前使用的 LLM 后端类型。

    Returns:
        "anthropic_api" - 使用 Anthropic 官方 API
        "claude_code" - 使用 Claude Code CLI 适配器
        None - 客户端尚未初始化
    """
    return _backend_type


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
    同时重置后端类型标记。
    """
    global _client, _backend_type
    with _client_lock:
        _client = None
        _backend_type = None
        logger.info("LLM client reset, will reinitialize on next call")


__all__ = [
    "get_llm_client",
    "get_backend_type",
    "extract_response_text",
    "reset_client",
]