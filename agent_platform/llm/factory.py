"""
LLM Client Factory - LLM 客户端工厂

提供线程安全的 LLM 客户端获取和管理。
支持双后端策略：
1. Anthropic 官方 API（需要 ANTHROPIC_API_KEY）
2. Claude Code CLI 适配器（需要安装 Claude Code）
3. 回退到 DummyClient（开发/测试模式）
"""

import logging
import os
import threading
from typing import Any, Optional

from .base import LLMClient, LLMResponse, DummyLLMClient
from ..core.exceptions import LLMClientError, LLMNotConfiguredError

logger = logging.getLogger(__name__)

# 线程安全的客户端单例
_client: Optional[LLMClient] = None
_client_lock = threading.Lock()
_backend_type: Optional[str] = None  # "anthropic_api" | "claude_code" | "dummy"


def get_llm_client(allow_dummy: bool = True) -> LLMClient:
    """
    获取 LLM 客户端实例（线程安全）。

    后端优先级：
        1. Anthropic 官方 API（如果 ANTHROPIC_API_KEY 存在）
        2. Claude Code CLI 适配器（如果 CLI 已安装）
        3. DummyLLMClient（如果 allow_dummy=True）

    Args:
        allow_dummy: 当前两种后端都不可用时，是否返回 DummyClient
            - True: 返回 DummyLLMClient（开发/测试用）
            - False: 抛出 LLMNotConfiguredError

    Returns:
        LLMClient 实例

    Raises:
        LLMNotConfiguredError: 所有后端都不可用且 allow_dummy=False
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
            try:
                _client = _create_anthropic_client(api_key)
                _backend_type = "anthropic_api"
                return _client
            except Exception as e:
                logger.warning(f"Failed to create Anthropic client: {e}")

        # 策略 2: 回退到 Claude Code CLI
        logger.info("ANTHROPIC_API_KEY not set, trying Claude Code CLI")
        try:
            _client = _create_claude_code_client()
            _backend_type = "claude_code"
            return _client
        except Exception as e:
            logger.warning(f"Claude Code CLI not available: {e}")

        # 策略 3: 回退到 DummyClient
        if allow_dummy:
            logger.warning(
                "No LLM backend available, using DummyLLMClient. "
                "Set ANTHROPIC_API_KEY or install Claude Code CLI for production use."
            )
            # raise_on_call=True: 调用时会抛出清晰的错误提示
            _client = DummyLLMClient(raise_on_call=True)
            _backend_type = "dummy"
            return _client

        raise LLMNotConfiguredError()


def _create_anthropic_client(api_key: str) -> LLMClient:
    """
    创建 Anthropic API 客户端包装器。

    Returns:
        AnthropicLLMClient 实例
    """
    base_url = os.environ.get("ANTHROPIC_BASE_URL")

    try:
        from anthropic import Anthropic
    except ImportError:
        raise LLMClientError(
            "anthropic package not installed. Run: pip install anthropic",
            provider="anthropic",
        )

    # 创建原生 Anthropic 客户端
    kwargs = {}
    if base_url:
        kwargs["base_url"] = base_url
        logger.info(f"Using Anthropic API with custom base URL: {base_url}")
    else:
        logger.info("Using Anthropic API (official endpoint)")

    native_client = Anthropic(api_key=api_key, **kwargs)

    # 返回包装器
    return AnthropicLLMClient(native_client)


def _create_claude_code_client() -> LLMClient:
    """
    创建 Claude Code CLI 适配器。

    Returns:
        ClaudeCodeLLMClient 实例
    """
    try:
        # 尝试从 agents.tools 导入现有的 ClaudeCodeClient
        from agents.tools.claude_code_adapter import (
            ClaudeCodeClient,
            check_claude_code_available,
        )

        cli_status = check_claude_code_available()
        if not cli_status["available"]:
            raise LLMClientError(
                f"Claude Code CLI not available: {cli_status.get('error', 'Unknown')}",
                provider="claude_code",
            )

        logger.info(
            f"Using Claude Code CLI (path: {cli_status.get('path')}, "
            f"version: {cli_status.get('version')})"
        )

        # 包装现有的 ClaudeCodeClient
        return ClaudeCodeLLMClient(ClaudeCodeClient())

    except ImportError:
        raise LLMClientError(
            "Claude Code adapter not available",
            provider="claude_code",
        )


class AnthropicLLMClient(LLMClient):
    """
    Anthropic API 客户端包装器。

    将 Anthropic 原生客户端包装为 LLMClient 接口。
    """

    DEFAULT_MODEL = "claude-sonnet-4-20250514"

    def __init__(self, native_client: Any):
        super().__init__()  # 初始化 messages 兼容层
        self._client = native_client

    def generate(
        self,
        system: str,
        user: str,
        *,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> LLMResponse:
        """调用 Anthropic API"""
        model = model or self.DEFAULT_MODEL

        try:
            response = self._client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=[{"role": "user", "content": user}],
                **kwargs,
            )

            # 提取文本
            text = ""
            for block in response.content:
                if getattr(block, "type", None) == "text":
                    text += block.text

            return LLMResponse(
                text=text,
                model=response.model,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
                raw=response,
            )

        except Exception as e:
            raise LLMClientError(f"Anthropic API call failed: {e}", provider="anthropic")


class ClaudeCodeLLMClient(LLMClient):
    """
    Claude Code CLI 客户端包装器。

    将 ClaudeCodeClient 包装为 LLMClient 接口。
    """

    def __init__(self, native_client: Any):
        super().__init__()  # 初始化 messages 兼容层
        self._client = native_client

    def generate(
        self,
        system: str,
        user: str,
        *,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> LLMResponse:
        """调用 Claude Code CLI"""
        try:
            # ClaudeCodeClient 使用 messages.create 接口
            response = self._client.messages.create(
                model=model or "claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )

            # 提取文本
            text = ""
            for block in response.content:
                if getattr(block, "type", None) == "text":
                    text += block.text

            return LLMResponse(
                text=text,
                model=getattr(response, "model", "claude-code"),
                usage={
                    "input_tokens": getattr(response.usage, "input_tokens", 0),
                    "output_tokens": getattr(response.usage, "output_tokens", 0),
                },
                raw=response,
            )

        except Exception as e:
            raise LLMClientError(f"Claude Code CLI call failed: {e}", provider="claude_code")


def get_backend_type() -> Optional[str]:
    """
    获取当前使用的 LLM 后端类型。

    Returns:
        "anthropic_api" - Anthropic 官方 API
        "claude_code" - Claude Code CLI
        "dummy" - 占位客户端
        None - 客户端尚未初始化
    """
    return _backend_type


def reset_client() -> None:
    """
    重置 LLM 客户端（用于测试或运行时切换）。

    调用后，下次 get_llm_client() 会重新创建客户端。
    """
    global _client, _backend_type
    with _client_lock:
        _client = None
        _backend_type = None
        logger.info("LLM client reset")


def extract_response_text(response: Any) -> str:
    """
    从 LLM 响应中提取文本内容（兼容多种响应格式）。

    优先级顺序（防御式逻辑）：
    1. 字符串: 直接返回（Fast path）
    2. 鸭子类型检查: 有 .text 属性且为 str 时返回
    3. LLMResponse 对象: 返回 response.text
    4. Anthropic API 原生响应: 提取 response.content[].text
    5. 无法识别的类型: 抛出 TypeError

    Args:
        response: LLM 响应对象

    Returns:
        提取的文本内容

    Raises:
        TypeError: 无法从响应中提取文本

    Example:
        client = get_llm_client()
        resp = client.generate(system="...", user="...")
        text = extract_response_text(resp)  # 或直接用 resp.text
    """
    # Case 1: 字符串（Fast path）
    if isinstance(response, str):
        return response

    # Case 2: 鸭子类型检查 - 有 .text 属性且为 str
    # 这处理 LLMResponse 和任何有 text 属性的对象
    if hasattr(response, "text"):
        text_attr = response.text
        if isinstance(text_attr, str):
            return text_attr
        # text 属性存在但不是 str（可能是 property 或方法），继续检查其他情况

    # Case 3: Anthropic API 原生响应（有 .content 列表）
    if hasattr(response, "content") and response.content is not None:
        content = response.content
        # 确保是可迭代的
        if hasattr(content, "__iter__"):
            text_parts = []
            for item in content:
                # 处理嵌套列表（某些 API 版本）
                if isinstance(item, list):
                    for block in item:
                        if getattr(block, "type", None) == "text":
                            block_text = getattr(block, "text", None)
                            if isinstance(block_text, str):
                                text_parts.append(block_text)
                # 处理单个块
                elif getattr(item, "type", None) == "text":
                    block_text = getattr(item, "text", None)
                    if isinstance(block_text, str):
                        text_parts.append(block_text)
            if text_parts:
                return "".join(text_parts)

    # Case 4: None 值
    if response is None:
        raise TypeError(
            "extract_response_text() received None. "
            "Check if the LLM call succeeded."
        )

    # Case 5: 无法识别的类型 - 抛出明确错误而非静默转换
    raise TypeError(
        f"extract_response_text() cannot extract text from type {type(response).__name__}. "
        f"Expected str, LLMResponse, or Anthropic API response object. "
        f"Response preview: {repr(response)[:100]}"
    )


__all__ = [
    "get_llm_client",
    "get_backend_type",
    "reset_client",
    "extract_response_text",
    "AnthropicLLMClient",
    "ClaudeCodeLLMClient",
]
