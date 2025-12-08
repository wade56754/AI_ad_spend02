"""
LLM Client Factory - LLM 客户端工厂

提供线程安全的 LLM 客户端获取和管理。
支持双后端策略：
1. Anthropic 官方 API（需要 ANTHROPIC_API_KEY）
2. Claude Code CLI 适配器（需要安装 Claude Code）
3. 回退到 DummyClient（开发/测试模式）

配置加载优先级 (Phase 3.0C):
1. 环境变量（最高优先级，不会被本地文件覆盖）
2. 仓库根目录 .env.local 文件
3. 仓库根目录 local_config/anthropic.json 文件

支持的配置项：
- ANTHROPIC_API_KEY: Anthropic API 密钥
- ANTHROPIC_BASE_URL: API 端点 URL（用于第三方代理，如 deeprouter.top）
"""

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, Optional, Tuple

from .base import LLMClient, LLMResponse, DummyLLMClient
from .anthropic_client import AnthropicLLMClient
from .deeprouter_client import DeepRouterLLMClient
from ..core.exceptions import LLMClientError, LLMNotConfiguredError

logger = logging.getLogger(__name__)

# 线程安全的客户端单例
_client: Optional[LLMClient] = None
_client_lock = threading.Lock()
_backend_type: Optional[str] = None  # "anthropic_api" | "claude_code" | "dummy"

# 仓库根目录（基于 factory.py 位置推导: llm/ -> agent_platform/ -> repo root）
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_anthropic_api_key() -> Tuple[Optional[str], Optional[str]]:
    """
    加载 Anthropic API Key（多来源优先级链）。

    加载优先级：
        1. 环境变量 ANTHROPIC_API_KEY
        2. 仓库根目录 .env.local 文件
        3. 仓库根目录 local_config/anthropic.json 文件

    Returns:
        Tuple[Optional[str], Optional[str]]:
            - api_key: API Key 值，如果未找到则为 None
            - source: 加载来源 ("env" | ".env.local" | "anthropic.json" | None)

    Note:
        日志中绝不记录 key 内容，仅记录来源。
    """
    # 策略 1: 环境变量（最高优先级）
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        logger.debug("Loaded ANTHROPIC_API_KEY from environment variable")
        return api_key, "env"

    # 策略 2: .env.local 文件
    env_local_path = _REPO_ROOT / ".env.local"
    if env_local_path.is_file():
        try:
            api_key = _parse_env_file(env_local_path, "ANTHROPIC_API_KEY")
            if api_key:
                logger.debug(f"Loaded ANTHROPIC_API_KEY from {env_local_path}")
                return api_key, ".env.local"
        except Exception as e:
            logger.warning(f"Failed to parse .env.local: {e}")

    # 策略 3: local_config/anthropic.json 文件
    json_path = _REPO_ROOT / "local_config" / "anthropic.json"
    if json_path.is_file():
        try:
            api_key = _parse_json_config(json_path, "ANTHROPIC_API_KEY")
            if api_key:
                logger.debug(f"Loaded ANTHROPIC_API_KEY from {json_path}")
                return api_key, "anthropic.json"
        except Exception as e:
            logger.warning(f"Failed to parse anthropic.json: {e}")

    # 策略 4: 自动转换 DEEPROUTER_CLAUDE_TOKEN（兼容性支持）
    # 如果找不到 ANTHROPIC_API_KEY，尝试从 DEEPROUTER_CLAUDE_TOKEN 读取
    deeprouter_token = os.environ.get("DEEPROUTER_CLAUDE_TOKEN")
    if not deeprouter_token:
        # 尝试从 .env.local 读取
        env_local_path = _REPO_ROOT / ".env.local"
        if env_local_path.is_file():
            try:
                deeprouter_token = _parse_env_file(env_local_path, "DEEPROUTER_CLAUDE_TOKEN")
            except Exception:
                pass
    
    if deeprouter_token:
        logger.info("Auto-converting DEEPROUTER_CLAUDE_TOKEN to ANTHROPIC_API_KEY for DeepRouter compatibility")
        return deeprouter_token, "deeprouter_token_auto_convert"

    # 未找到任何 key
    return None, None


def _load_anthropic_base_url() -> Tuple[Optional[str], Optional[str]]:
    """
    加载 Anthropic Base URL（多来源优先级链）。

    用于支持 Anthropic 兼容的第三方代理（如 deeprouter.top）。

    加载优先级：
        1. 环境变量 ANTHROPIC_BASE_URL（最高优先级，不会被覆盖）
        2. 仓库根目录 .env.local 文件
        3. 仓库根目录 local_config/anthropic.json 文件

    Returns:
        Tuple[Optional[str], Optional[str]]:
            - base_url: Base URL 值，如果未找到则为 None（使用官方端点）
            - source: 加载来源 ("env" | ".env.local" | "anthropic.json" | None)

    Note:
        如果返回 None，客户端将使用官方 https://api.anthropic.com 端点。
    """
    # 策略 1: 环境变量（最高优先级，不会被本地文件覆盖）
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    if base_url:
        logger.debug("Loaded ANTHROPIC_BASE_URL from environment variable")
        return base_url, "env"

    # 策略 2: .env.local 文件
    env_local_path = _REPO_ROOT / ".env.local"
    if env_local_path.is_file():
        try:
            base_url = _parse_env_file(env_local_path, "ANTHROPIC_BASE_URL")
            if base_url:
                logger.debug(f"Loaded ANTHROPIC_BASE_URL from {env_local_path}")
                return base_url, ".env.local"
        except Exception as e:
            logger.warning(f"Failed to parse .env.local for base_url: {e}")

    # 策略 3: local_config/anthropic.json 文件
    json_path = _REPO_ROOT / "local_config" / "anthropic.json"
    if json_path.is_file():
        try:
            base_url = _parse_json_config(json_path, "ANTHROPIC_BASE_URL")
            if base_url:
                logger.debug(f"Loaded ANTHROPIC_BASE_URL from {json_path}")
                return base_url, "anthropic.json"
        except Exception as e:
            logger.warning(f"Failed to parse anthropic.json for base_url: {e}")

    # 策略 4: 自动转换 DEEPROUTER_BASE_URL（兼容性支持）
    # 如果找不到 ANTHROPIC_BASE_URL，尝试从 DEEPROUTER_BASE_URL 读取
    deeprouter_base_url = os.environ.get("DEEPROUTER_BASE_URL")
    if not deeprouter_base_url:
        # 尝试从 .env.local 读取
        env_local_path = _REPO_ROOT / ".env.local"
        if env_local_path.is_file():
            try:
                deeprouter_base_url = _parse_env_file(env_local_path, "DEEPROUTER_BASE_URL")
            except Exception:
                pass
    
    if deeprouter_base_url:
        logger.info("Auto-converting DEEPROUTER_BASE_URL to ANTHROPIC_BASE_URL for DeepRouter compatibility")
        return deeprouter_base_url, "deeprouter_base_url_auto_convert"

    # 未找到 base_url（使用官方端点）
    return None, None


def _parse_env_file(file_path: Path, key_name: str) -> Optional[str]:
    """
    解析 .env 风格的配置文件。

    支持格式：
        - KEY=value
        - KEY="value"
        - KEY='value'
        - # 注释行
        - 空行

    Args:
        file_path: 配置文件路径
        key_name: 要查找的 key 名称

    Returns:
        key 对应的值，如果未找到则为 None
    """
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # 跳过空行和注释
            if not line or line.startswith("#"):
                continue

            # 解析 KEY=value 格式
            if "=" in line:
                parts = line.split("=", 1)
                if len(parts) == 2:
                    k = parts[0].strip()
                    v = parts[1].strip()

                    if k == key_name:
                        # 去除两边的引号（单引号或双引号）
                        if len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"):
                            v = v[1:-1]
                        return v if v else None

    return None


def _parse_json_config(file_path: Path, key_name: str) -> Optional[str]:
    """
    解析 JSON 格式的配置文件。

    支持大写和小写版本的 key 名称：
        - 例如: ANTHROPIC_API_KEY / anthropic_api_key
        - 例如: ANTHROPIC_BASE_URL / anthropic_base_url

    Args:
        file_path: JSON 配置文件路径
        key_name: 要查找的 key 名称（大写形式）

    Returns:
        key 对应的值，如果未找到则为 None
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        return None

    # 优先查找大写版本
    value = data.get(key_name)
    if value and isinstance(value, str):
        return value

    # 回退到小写版本
    value = data.get(key_name.lower())
    if value and isinstance(value, str):
        return value

    return None


def get_llm_client(allow_dummy: bool = True) -> LLMClient:
    """
    获取 LLM 客户端实例（线程安全）。

    后端选择：
        - 如果 LLM_BACKEND="deeprouter"，使用 DeepRouter LLM Client
        - 否则按优先级选择：
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

        # 检查显式指定的后端类型
        backend_type = os.environ.get("LLM_BACKEND", "anthropic_api").strip().lower()

        # 策略 0: DeepRouter 后端（显式指定 LLM_BACKEND=deeprouter）
        # 注意：如果同时有 ANTHROPIC_API_KEY + ANTHROPIC_BASE_URL（指向 DeepRouter），
        # 应该优先使用 Anthropic API 风格（策略 1），而不是直接使用 DeepRouterLLMClient
        if backend_type == "deeprouter":
            # 检查是否同时配置了 ANTHROPIC_API_KEY（可能指向 DeepRouter）
            api_key, _ = _load_anthropic_api_key()
            base_url, _ = _load_anthropic_base_url()
            
            if api_key and base_url and "deeprouter" in base_url.lower():
                # 有 API key 和 DeepRouter base_url，优先使用 Anthropic API 风格
                logger.info(
                    "LLM_BACKEND=deeprouter but ANTHROPIC_API_KEY+ANTHROPIC_BASE_URL found. "
                    "Using Anthropic API format via DeepRouter proxy (recommended)."
                )
                # 继续到策略 1，使用 Anthropic API 风格
            else:
                # 没有 API key，尝试直接使用 DeepRouterLLMClient
                # 但注意：DeepRouter 可能要求使用 ANTHROPIC_API_KEY 方式
                try:
                    _client = _create_deeprouter_client()
                    _backend_type = "deeprouter"
                    logger.warning(
                        "Using DeepRouterLLMClient (direct). "
                        "Note: DeepRouter may require ANTHROPIC_API_KEY format. "
                        "Consider setting ANTHROPIC_API_KEY=<deeprouter_token> and ANTHROPIC_BASE_URL=https://deeprouter.top"
                    )
                    return _client
                except Exception as e:
                    logger.warning(f"Failed to create DeepRouter client: {e}")
                    if not allow_dummy:
                        raise LLMNotConfiguredError() from e
                    # 继续尝试其他后端

        # 策略 1: 检查 Anthropic API Key（多来源优先级链）
        # 优先使用 Anthropic API 风格（支持 DeepRouter 代理），而不是回退到 Claude Code CLI
        api_key, key_source = _load_anthropic_api_key()
        if api_key:
            try:
                # 将 key 注入环境变量，保持对下游 SDK 的兼容性
                if key_source != "env":
                    os.environ["ANTHROPIC_API_KEY"] = api_key
                    logger.info(f"Loaded ANTHROPIC_API_KEY from {key_source}")

                # 加载 base_url（支持第三方代理，如 deeprouter.top）
                base_url, url_source = _load_anthropic_base_url()
                
                # 检测 DeepRouter 代理
                is_deeprouter = base_url and "deeprouter.top" in base_url.lower()
                
                if is_deeprouter:
                    # DeepRouter 代理：规范化 base_url
                    if base_url.rstrip('/').endswith('deeprouter.top'):
                        # 根路径，需要添加 /v1（Anthropic SDK 会自动添加 /messages）
                        normalized_base_url = base_url.rstrip('/')
                        logger.info(
                            f"Detected DeepRouter proxy: {normalized_base_url}. "
                            f"Using Anthropic API format via DeepRouter."
                        )
                    else:
                        # 已包含路径，规范化处理
                        normalized_base_url = base_url.rstrip('/')
                        if normalized_base_url.endswith('/v1'):
                            normalized_base_url = normalized_base_url[:-3].rstrip('/')
                        logger.info(
                            f"Detected DeepRouter proxy with path: {base_url}. "
                            f"Normalized to: {normalized_base_url}. "
                            f"Using Anthropic API format via DeepRouter."
                        )
                    
                    if url_source != "env":
                        os.environ["ANTHROPIC_BASE_URL"] = normalized_base_url
                        logger.info(f"Set ANTHROPIC_BASE_URL from {url_source}: {normalized_base_url}")
                    else:
                        # 环境变量已设置，但需要规范化
                        os.environ["ANTHROPIC_BASE_URL"] = normalized_base_url
                elif base_url:
                    # 其他代理或官方 API
                    if url_source != "env":
                        os.environ["ANTHROPIC_BASE_URL"] = base_url
                        logger.info(f"Loaded ANTHROPIC_BASE_URL from {url_source}: {base_url}")
                    logger.info(f"Using Anthropic API with base URL: {base_url}")
                else:
                    # 官方 API（无 base_url）
                    logger.info("Using Anthropic API (official endpoint: https://api.anthropic.com)")

                _client = _create_anthropic_client(api_key)
                _backend_type = "anthropic_api"
                
                # 记录后端类型信息（不打印 key）
                backend_info = "DeepRouter proxy" if is_deeprouter else "Anthropic official API"
                logger.info(f"LLM backend initialized: {backend_info} (backend_type={_backend_type})")
                
                return _client
            except Exception as e:
                logger.warning(f"Failed to create Anthropic API client: {e}")
                # 继续尝试其他后端，不立即回退

        # 策略 2: 回退到 Claude Code CLI（仅在无 API key 时）
        if not api_key:
            logger.info("ANTHROPIC_API_KEY not found in env/.env.local/anthropic.json, trying Claude Code CLI")
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
        # Anthropic SDK 会自动添加 /v1/messages 路径
        # 如果 base_url 已经包含 /v1，需要移除以避免路径重复
        normalized_base_url = base_url.rstrip('/')
        if normalized_base_url.endswith('/v1'):
            # 移除尾部的 /v1，让 SDK 自动添加
            normalized_base_url = normalized_base_url[:-3].rstrip('/')
            logger.info(
                f"Normalized base_url: {base_url} -> {normalized_base_url} "
                f"(SDK will auto-add /v1/messages)"
            )
        kwargs["base_url"] = normalized_base_url
        logger.info(f"Using Anthropic API with custom base URL: {normalized_base_url}")
    else:
        logger.info("Using Anthropic API (official endpoint)")

    native_client = Anthropic(api_key=api_key, **kwargs)

    # 返回包装器
    return AnthropicLLMClient(native_client)


def _create_deeprouter_client() -> LLMClient:
    """
    创建 DeepRouter LLM 客户端。

    Returns:
        DeepRouterLLMClient 实例

    Raises:
        LLMClientError: 如果配置缺失或创建失败
    """
    try:
        return DeepRouterLLMClient()
    except LLMClientError:
        raise
    except Exception as e:
        raise LLMClientError(
            f"Failed to create DeepRouter client: {e}",
            provider="deeprouter",
        ) from e


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
        "deeprouter" - DeepRouter 代理 API
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
    "DeepRouterLLMClient",
]
