"""
DeepRouter LLM Client - DeepRouter Claude 代理 API 客户端

支持通过 DeepRouter 代理 API 调用 Claude 模型，用于替代官方 Anthropic API 以降低成本。

配置要求：
- DEEPROUTER_CLAUDE_TOKEN: DeepRouter API Token（必填）
- DEEPROUTER_BASE_URL: API 端点 URL（可选，默认 https://deeprouter.top）
- DEEPROUTER_MODEL: 模型名称（可选，默认 claude-sonnet-4-20250514）
"""

import logging
import os
from typing import Any, Dict, Optional

import httpx

from .base import LLMClient, LLMResponse
from ..core.exceptions import LLMClientError

logger = logging.getLogger(__name__)


class DeepRouterLLMClient(LLMClient):
    """
    DeepRouter Claude 代理 API 客户端。

    使用 DeepRouter 代理 API 调用 Claude 模型，支持与官方 Anthropic API 兼容的接口。
    """

    DEFAULT_MODEL = "claude-sonnet-4-20250514"
    DEFAULT_BASE_URL = "https://deeprouter.top"

    def __init__(
        self,
        token: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        初始化 DeepRouter LLM 客户端。

        Args:
            token: DeepRouter API Token（必填）
                如果未提供，将从环境变量 DEEPROUTER_CLAUDE_TOKEN 读取
            base_url: API 端点 URL（可选）
                如果未提供，将从环境变量 DEEPROUTER_BASE_URL 读取，缺省值为 https://deeprouter.top
            model: 模型名称（可选）
                如果未提供，将从环境变量 DEEPROUTER_MODEL 读取，缺省值为 claude-sonnet-4-20250514

        Raises:
            LLMClientError: 如果 token 未配置
        """
        super().__init__()  # 初始化 messages 兼容层

        # 加载配置（优先级：参数 > 环境变量 > 默认值）
        self._token = token or os.environ.get("DEEPROUTER_CLAUDE_TOKEN")
        if not self._token:
            raise LLMClientError(
                "DEEPROUTER_CLAUDE_TOKEN is required. "
                "Set it as environment variable or pass as parameter.",
                provider="deeprouter",
            )

        self._base_url = (base_url or os.environ.get("DEEPROUTER_BASE_URL") or self.DEFAULT_BASE_URL).rstrip("/")
        self._model = model or os.environ.get("DEEPROUTER_MODEL") or self.DEFAULT_MODEL

        # 构建完整的 API 端点 URL
        self._api_url = f"{self._base_url}/v1/messages"

        logger.info(
            f"Initialized DeepRouter LLM Client: "
            f"base_url={self._base_url}, model={self._model}"
        )

    def generate(
        self,
        system: str,
        user: str,
        *,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        stream: bool = False,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        生成 LLM 响应。

        Args:
            system: 系统提示词
            user: 用户消息
            model: 模型名称（可选，使用默认模型）
            max_tokens: 最大生成 token 数
            temperature: 温度参数
            stream: 是否流式返回（当前仅支持 False）
            **kwargs: 其他参数（将被忽略）

        Returns:
            LLMResponse 对象

        Raises:
            LLMClientError: API 调用失败
        """
        if stream:
            logger.warning("DeepRouter client does not support streaming yet, using non-streaming mode")

        model = model or self._model

        # 构建请求体（Claude Messages 风格）
        request_body: Dict[str, Any] = {
            "model": model,
            "system": system,
            "messages": [{"role": "user", "content": user}],
            "max_tokens": max_tokens,
            "stream": False,  # 当前仅支持非流式
        }

        # 添加 temperature（如果非默认值）
        if temperature != 0.0:
            request_body["temperature"] = temperature

        # 构建请求头
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._token}",
            "x-api-key": self._token,  # 增加兼容性
        }

        try:
            # 发送 HTTP 请求
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    self._api_url,
                    json=request_body,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

            # 解析响应（兼容多种格式）
            text = self._extract_text_from_response(data)
            usage = data.get("usage", {})

            return LLMResponse(
                text=text,
                model=data.get("model", model),
                usage={
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                },
                raw=data,
            )

        except httpx.HTTPStatusError as e:
            error_msg = f"DeepRouter API returned {e.response.status_code}: {e.response.text[:200]}"
            logger.error(error_msg)
            raise LLMClientError(
                f"DeepRouter API call failed: {error_msg}",
                provider="deeprouter",
            ) from e
        except httpx.RequestError as e:
            error_msg = f"DeepRouter API request failed: {str(e)}"
            logger.error(error_msg)
            raise LLMClientError(
                error_msg,
                provider="deeprouter",
            ) from e
        except Exception as e:
            error_msg = f"Unexpected error in DeepRouter API call: {str(e)}"
            logger.error(error_msg)
            raise LLMClientError(
                error_msg,
                provider="deeprouter",
            ) from e

    def _extract_text_from_response(self, data: Dict[str, Any]) -> str:
        """
        从响应中提取文本内容（兼容多种响应格式）。

        优先级：
        1. OpenAI 风格：choices[0].message.content
        2. Anthropic 风格：content[{"type": "text", "text": "..."}]
        3. 直接 content 字段（字符串）

        Args:
            data: API 响应数据（字典）

        Returns:
            提取的文本内容

        Raises:
            LLMClientError: 无法从响应中提取文本
        """
        # 策略 1: OpenAI 风格 - choices[0].message.content
        if "choices" in data and isinstance(data["choices"], list) and len(data["choices"]) > 0:
            choice = data["choices"][0]
            if isinstance(choice, dict) and "message" in choice:
                message = choice["message"]
                if isinstance(message, dict) and "content" in message:
                    content = message["content"]
                    if isinstance(content, str):
                        return content
                    # content 可能是列表（多模态）
                    if isinstance(content, list):
                        text_parts = []
                        for part in content:
                            if isinstance(part, dict):
                                if part.get("type") == "text" and "text" in part:
                                    text_parts.append(str(part["text"]))
                        if text_parts:
                            return "".join(text_parts)

        # 策略 2: Anthropic 风格 - content[{"type": "text", "text": "..."}]
        if "content" in data:
            content = data["content"]
            if isinstance(content, list):
                text_parts = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text" and "text" in block:
                            text_parts.append(str(block["text"]))
                if text_parts:
                    return "".join(text_parts)
            elif isinstance(content, str):
                # 直接字符串格式
                return content

        # 策略 3: 尝试直接查找 text 字段
        if "text" in data and isinstance(data["text"], str):
            return data["text"]

        # 无法提取文本
        raise LLMClientError(
            f"Cannot extract text from DeepRouter API response. "
            f"Response structure: {list(data.keys())}",
            provider="deeprouter",
        )


__all__ = ["DeepRouterLLMClient"]

