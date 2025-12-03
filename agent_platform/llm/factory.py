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

        # 策略 1: 检查 Anthropic API Key（多来源优先级链）
        api_key, key_source = _load_anthropic_api_key()
        if api_key:
            try:
                # 将 key 注入环境变量，保持对下游 SDK 的兼容性
                if key_source != "env":
                    os.environ["ANTHROPIC_API_KEY"] = api_key
                    logger.info(f"Loaded ANTHROPIC_API_KEY from {key_source}")

                # 加载 base_url（支持第三方代理，如 deeprouter.top）
                base_url, url_source = _load_anthropic_base_url()
                
                # 检测不兼容的代理 API（仅对根路径进行跳过，/v1 路径可能可用）
                if base_url and "deeprouter.top" in base_url.lower():
                    # 如果只是根路径（没有 /v1），则跳过（不支持标准格式）
                    if base_url.rstrip('/').endswith('deeprouter.top'):
                        logger.warning(
                            f"Detected deeprouter.top root URL which does not support standard Anthropic API format. "
                            f"Skipping Anthropic API, will fallback to Claude Code CLI. "
                            f"Tip: Try using https://deeprouter.top/v1 instead."
                        )
                        # 跳过 Anthropic API，直接尝试 Claude Code CLI
                        raise Exception("Incompatible proxy API detected, skip to Claude Code CLI")
                    else:
                        # /v1 路径可能可用，允许尝试
                        logger.info(
                            f"Detected deeprouter.top with path: {base_url}. "
                            f"Attempting to use this proxy API."
                        )
                
                if base_url and url_source != "env":
                    # 注入环境变量，_create_anthropic_client 会从 os.environ 读取
                    os.environ["ANTHROPIC_BASE_URL"] = base_url
                    logger.info(f"Loaded ANTHROPIC_BASE_URL from {url_source}: {base_url}")

                _client = _create_anthropic_client(api_key)
                _backend_type = "anthropic_api"
                return _client
            except Exception as e:
                # 如果是已知的不兼容代理，不记录为错误，直接回退
                if "Incompatible proxy API" in str(e):
                    logger.info("Skipping Anthropic API due to incompatible proxy, trying Claude Code CLI")
                else:
                    logger.warning(f"Failed to create Anthropic client: {e}")

        # 策略 2: 回退到 Claude Code CLI
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
    支持代理 API 兼容性处理（如 deeprouter.top）。
    """

    DEFAULT_MODEL = "claude-sonnet-4-20250514"

    def __init__(self, native_client: Any):
        super().__init__()  # 初始化 messages 兼容层
        self._client = native_client
        # 检测是否使用代理 API（通过 base_url）
        self._is_proxy_api = self._detect_proxy_api()

    def _detect_proxy_api(self) -> bool:
        """
        检测是否使用代理 API。

        某些代理 API（如 deeprouter.top）需要特殊的参数格式。
        通过检查 base_url 来判断是否使用代理。

        Returns:
            True 如果使用代理 API，False 如果使用官方 API
        """
        base_url = getattr(self._client, "base_url", None)
        if not base_url:
            return False
        
        # 检查是否是已知的代理 API 域名
        proxy_domains = [
            "deeprouter.top",
            "deeprouter.com",
            "api.deeprouter",
            "claudelike.online",
            "claudelike.com",
        ]
        
        base_url_str = str(base_url).lower()
        return any(domain in base_url_str for domain in proxy_domains)

    def _normalize_system_param(self, system: str) -> Any:
        """
        规范化 system 参数格式。

        某些代理 API（如 deeprouter.top）期望 system 参数为数组格式：
        [{"type": "text", "text": "..."}]

        官方 API 接受字符串格式。

        Args:
            system: 系统提示词（字符串）

        Returns:
            规范化后的 system 参数（字符串或数组）
        """
        if self._is_proxy_api:
            # 代理 API：转换为数组格式
            # 注意：某些代理可能还需要其他格式调整
            return [{"type": "text", "text": system}]
        else:
            # 官方 API：保持字符串格式
            return system

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

        # 规范化 system 参数（代理 API 兼容性处理）
        normalized_system = self._normalize_system_param(system)

        try:
            response = self._client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=normalized_system,
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
            error_msg = str(e)
            
            # 检测代理 API 不支持的错误
            if self._is_proxy_api and ("不支持" in error_msg or "not supported" in error_msg.lower() or "claude code" in error_msg.lower()):
                base_url = getattr(self._client, "base_url", "unknown")
                logger.warning(
                    f"Proxy API ({base_url}) does not support standard Anthropic API format. "
                    f"Error: {error_msg[:200]}"
                )
                raise LLMClientError(
                    f"代理 API ({base_url}) 不支持标准 Anthropic API 格式。\n"
                    f"解决方案：\n"
                    f"  1. 移除 ANTHROPIC_BASE_URL 配置以使用官方 API\n"
                    f"  2. 或移除 ANTHROPIC_API_KEY 以自动使用 Claude Code CLI\n"
                    f"原始错误: {error_msg[:200]}",
                    provider="anthropic"
                )
            
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
