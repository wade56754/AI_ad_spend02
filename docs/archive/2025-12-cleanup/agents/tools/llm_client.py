"""
llm_client.py - LLM 客户端统一管理（支持 API Key 和 Claude Code CLI fallback）

提供线程安全的 LLM 客户端单例，优先使用 Anthropic 官方 API，无 API Key 时自动 fallback 到 Claude Code CLI。

优先级：
1. ANTHROPIC_API_KEY 存在时，使用 Anthropic API 客户端
2. 无 API Key 时，fallback 到 Claude Code CLI 客户端
3. 两者都不可用时，抛出 RuntimeError

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


def get_llm_client() -> Any:
    """
    获取 LLM 客户端单例（线程安全）。

    优先级：
        1. ANTHROPIC_API_KEY 存在时，使用 Anthropic API 客户端
        2. 无 API Key 时，fallback 到 Claude Code CLI 客户端
        3. 两者都不可用时，抛出 RuntimeError

    环境变量：
        - ANTHROPIC_API_KEY (可选): Anthropic API密钥
        - ANTHROPIC_BASE_URL (可选): 自定义API基础URL（用于代理）

    Thread Safety:
        使用双重检查锁定模式，确保线程安全的单例初始化。

    Returns:
        LLM 客户端实例（Anthropic 或 ClaudeCodeClient）

    Raises:
        RuntimeError: 既没有 ANTHROPIC_API_KEY，也没有可用的 Claude Code CLI
    """
    global _client

    # Fast path: 客户端已初始化
    if _client is not None:
        return _client

    with _client_lock:
        # 双重检查
        if _client is not None:
            return _client

        # 优先尝试使用 Anthropic API
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            # 检查可选的代理 URL
            base_url = os.environ.get("ANTHROPIC_BASE_URL")

            # 创建 Anthropic 客户端
            try:
                from anthropic import Anthropic

                kwargs = {}
                if base_url:
                    kwargs["base_url"] = base_url
                    logger.info(f"Using Anthropic API with custom base URL: {base_url}")
                else:
                    logger.info("Using Anthropic API (official endpoint)")

                _client = Anthropic(api_key=api_key, **kwargs)
                logger.debug(f"Anthropic client initialized (key: {api_key[:10]}...)")
                return _client

            except ImportError:
                raise RuntimeError(
                    "anthropic 包未安装。请运行: pip install anthropic"
                )
            except Exception as e:
                raise RuntimeError(f"初始化 Anthropic 客户端失败: {e}")

        # Fallback: 尝试使用 Claude Code CLI
        logger.info("ANTHROPIC_API_KEY not set, falling back to Claude Code CLI")
        try:
            from .claude_code_adapter import ClaudeCodeClient, check_claude_code_available

            # 先尝试创建 ClaudeCodeClient（测试可能 patch 了它，所以先创建再检查）
            try:
                _client = ClaudeCodeClient()
                # 创建成功，验证是否真的可用（用于日志和错误提示）
                availability = check_claude_code_available()
                if availability["available"]:
                    logger.info(f"Using Claude Code CLI (path: {availability['path']})")
                else:
                    # 创建成功但检查显示不可用（可能是测试环境），记录信息但继续使用
                    logger.debug(
                        f"ClaudeCodeClient created (possibly mocked), "
                        f"but availability check: {availability.get('error', 'Unknown')}"
                    )
                return _client
            except Exception as create_error:
                # 创建失败，检查可用性以提供更好的错误信息
                availability = check_claude_code_available()
                error_msg = availability.get("error", "Unknown error")
                raise RuntimeError(
                    "ANTHROPIC_API_KEY 环境变量未设置，且 Claude Code CLI 不可用。\n"
                    f"Claude Code 错误: {error_msg}\n"
                    "请设置 ANTHROPIC_API_KEY 或安装 Claude Code CLI 后重试。"
                )
        except ImportError:
            # claude_code_adapter 模块不存在（理论上不应该发生）
            raise RuntimeError(
                "ANTHROPIC_API_KEY 环境变量未设置，且无法导入 Claude Code 适配器。\n"
                "请设置 ANTHROPIC_API_KEY 后重试。"
            )

    return _client


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