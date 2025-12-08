"""
Anthropic LLM Client - Anthropic API 客户端包装器

通过 Anthropic 官方 SDK 调用 Claude 模型，支持官方 API 和第三方代理（如 DeepRouter）。

配置要求：
- ANTHROPIC_API_KEY: Anthropic API 密钥（DeepRouter token 或官方 API key）
- ANTHROPIC_BASE_URL: API 端点 URL（可选，用于第三方代理，如 https://deeprouter.top）
- DEEPROUTER_MODEL: 模型名称（可选，默认 claude-sonnet-4-20250514）

模型设置方式：
1. 环境变量（全局默认）：
   在 .env.local 中设置: DEEPROUTER_MODEL=claude-opus-4-20250514

2. 代码中临时指定（单次调用）：
   client.generate(..., model='claude-opus-4-20250514')

注意：模型名称完全由环境变量和调用参数控制，代码不做任何限制。
"""

import logging
import os
from typing import Any, Optional

from .base import LLMClient, LLMResponse
from ..core.exceptions import LLMClientError

logger = logging.getLogger(__name__)


class AnthropicLLMClient(LLMClient):
    """
    Anthropic API 客户端包装器。

    将 Anthropic 原生客户端包装为 LLMClient 接口。
    支持代理 API 兼容性处理（如 deeprouter.top）。

    模型选择：
    - 优先使用 generate() 调用时传入的 model 参数
    - 其次使用环境变量 DEEPROUTER_MODEL
    - 最后使用默认值 "claude-sonnet-4-20250514"（仅作为占位值，不限制其他模型）
    """

    # 默认模型（仅作为占位值，实际模型由环境变量或调用参数决定）
    DEFAULT_MODEL = "claude-sonnet-4-20250514"

    def __init__(self, native_client: Any):
        """
        初始化 Anthropic LLM 客户端。

        Args:
            native_client: anthropic.Anthropic 客户端实例
        """
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

    def _get_model(self, model: Optional[str] = None) -> str:
        """
        获取模型名称（优先级：参数 > 环境变量 > 默认值）。

        Args:
            model: 调用时指定的模型名称（可选）

        Returns:
            模型名称字符串
        """
        # 优先级 1: 调用时指定的模型
        if model:
            return model

        # 优先级 2: 环境变量 DEEPROUTER_MODEL
        env_model = os.environ.get("DEEPROUTER_MODEL")
        if env_model:
            return env_model

        # 优先级 3: 默认值（仅作为占位值）
        return self.DEFAULT_MODEL

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
        thinking: bool = False,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        调用 Anthropic API 生成响应。

        Args:
            system: 系统提示词
            user: 用户消息
            model: 模型名称（可选，优先使用此参数，其次使用环境变量 DEEPROUTER_MODEL）
            max_tokens: 最大生成 token 数
            temperature: 温度参数
            thinking: 是否启用思考模式（可选）
            **kwargs: 其他模型特定参数

        Returns:
            LLMResponse 对象

        Raises:
            LLMClientError: LLM 调用失败
        """
        # 获取模型名称（优先级：参数 > 环境变量 > 默认值）
        model_name = self._get_model(model)

        # 规范化 system 参数（代理 API 兼容性处理）
        normalized_system = self._normalize_system_param(system)

        # 构建请求参数
        request_kwargs: dict[str, Any] = {
            "model": model_name,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": normalized_system,
            "messages": [{"role": "user", "content": user}],
        }

        # 如果启用思考模式，添加 thinking 参数
        if thinking:
            request_kwargs["thinking"] = {}

        # 合并其他参数
        request_kwargs.update(kwargs)

        try:
            response = self._client.messages.create(**request_kwargs)

            # 提取文本
            text = ""
            for block in response.content:
                if getattr(block, "type", None) == "text":
                    text += block.text

            # 提取 usage 信息
            usage = {}
            if hasattr(response, "usage") and response.usage:
                usage = {
                    "input_tokens": getattr(response.usage, "input_tokens", 0),
                    "output_tokens": getattr(response.usage, "output_tokens", 0),
                }

            return LLMResponse(
                text=text,
                model=response.model,
                usage=usage,
                raw=response,
            )

        except Exception as e:
            error_msg = str(e)

            # 检测代理 API 不支持的错误
            if self._is_proxy_api and (
                "不支持" in error_msg
                or "not supported" in error_msg.lower()
                or "claude code" in error_msg.lower()
            ):
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
                    provider="anthropic",
                )

            raise LLMClientError(
                f"Anthropic API call failed: {e}", provider="anthropic"
            )


__all__ = ["AnthropicLLMClient"]

