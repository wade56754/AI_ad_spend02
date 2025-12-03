"""
LLM Client Base Class - LLM 客户端抽象基类

定义 LLM 客户端的标准接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    """
    LLM 响应模型。

    统一不同 LLM 后端的响应格式。
    """

    text: str = ""
    model: str = ""
    usage: Dict[str, int] = Field(default_factory=dict)
    raw: Optional[Any] = None  # 原始响应（调试用）

    model_config = {"frozen": False}


class MessagesAPI:
    """
    兼容层：提供 messages.create() 接口以兼容旧代码。

    旧代码使用：client.messages.create(model=..., messages=[...])
    新代码使用：client.generate(system=..., user=..., model=...)

    此类将旧接口调用转换为新接口。

    ⚠️ Phase 2.1 限制：仅支持单轮对话模式
    - messages 列表中只能有 1 条 role="user" 的消息
    - 不支持 role="assistant" 消息（多轮对话）
    - 检测到多轮对话时抛出 NotImplementedError
    - 多轮对话支持计划在 Phase 3 实现
    """

    def __init__(self, client: "LLMClient"):
        self._client = client

    def create(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.0,
        system: str = "",
        **kwargs: Any,
    ) -> LLMResponse:
        """
        兼容 Anthropic API 的 messages.create() 接口。

        ⚠️ Phase 2.1 限制：仅支持单轮对话（1 条 user 消息）

        Args:
            model: 模型名称
            messages: 消息列表 [{"role": "user", "content": "..."}]
                     Phase 2.1 仅支持单条 user 消息
            max_tokens: 最大生成 token 数（可选，由下层决定默认值）
            temperature: 温度参数
            system: 系统提示词
            **kwargs: 其他参数

        Returns:
            LLMResponse 对象

        Raises:
            NotImplementedError: 检测到多轮对话（多条 user 或 assistant 消息）
            ValueError: messages 为空或格式错误
        """
        # Phase 2.1: 严格校验消息格式，避免静默丢失上下文
        if not messages:
            raise ValueError("messages cannot be empty")

        user_messages = [m for m in messages if m.get("role") == "user"]
        assistant_messages = [m for m in messages if m.get("role") == "assistant"]

        # 检测多轮对话并明确拒绝
        if len(user_messages) > 1:
            raise NotImplementedError(
                f"MessagesAPI.create() Phase 2.1 仅支持单轮对话，"
                f"但收到 {len(user_messages)} 条 user 消息。"
                f"多轮对话支持请等待 Phase 3 或直接使用 LLMClient.generate()。"
            )
        if assistant_messages:
            raise NotImplementedError(
                f"MessagesAPI.create() Phase 2.1 不支持多轮对话，"
                f"但收到 {len(assistant_messages)} 条 assistant 消息。"
                f"多轮对话支持请等待 Phase 3 或直接使用 LLMClient.generate()。"
            )

        if not user_messages:
            raise ValueError(
                "messages must contain at least one message with role='user'"
            )

        # 提取单条 user 消息内容
        user_msg = user_messages[0]
        content = user_msg.get("content", "")
        if isinstance(content, str):
            user_content = content
        elif isinstance(content, list):
            # 处理多模态消息（图片 + 文本）
            user_content = " ".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and part.get("type") == "text"
            )
        else:
            raise ValueError(
                f"Unsupported content type: {type(content)}. "
                f"Expected str or list of content blocks."
            )

        # 构建调用参数，max_tokens 为 None 时不传递，由下层决定
        generate_kwargs: Dict[str, Any] = {
            "system": system,
            "user": user_content,
            "model": model,
            "temperature": temperature,
            **kwargs,
        }
        if max_tokens is not None:
            generate_kwargs["max_tokens"] = max_tokens

        return self._client.generate(**generate_kwargs)


class LLMClient(ABC):
    """
    LLM 客户端抽象基类。

    所有 LLM 后端实现（Anthropic API、Claude Code CLI 等）必须继承此类。

    设计原则：
    - 简单接口：只提供 generate() 方法
    - 统一响应：返回 LLMResponse 模型
    - 可测试性：支持 Mock 实现
    - 兼容性：提供 messages.create() 兼容接口

    MCP 模式 (Phase 3.2):
    - 当 AGENT_PLATFORM_MODE=mcp 时，禁止创建 LLM 客户端实例
    - MCP 模式下 Claude 是唯一的 LLM，agent_platform 仅提供工具

    使用示例：
    ```python
    # 新接口（推荐）
    client = get_llm_client()
    resp = client.generate(system="...", user="...")
    text = resp.text

    # 旧接口（兼容）
    client = get_llm_client()
    resp = client.messages.create(
        model="claude-sonnet-4-20250514",
        messages=[{"role": "user", "content": "..."}],
    )
    text = extract_response_text(resp)
    ```
    """

    def __init__(self, *, _skip_mcp_check: bool = False):
        """
        初始化 LLM 客户端。

        Args:
            _skip_mcp_check: 内部参数，跳过 MCP 模式检查（仅用于 DummyLLMClient）

        Raises:
            LLMNotConfiguredError: 在 MCP 模式下尝试创建 LLM 客户端
        """
        # MCP 模式检查：禁止在 MCP 模式下创建 LLM 客户端
        if not _skip_mcp_check:
            self._check_mcp_mode()

        # 提供 messages.create() 兼容接口
        self._messages_api: Optional[MessagesAPI] = None

    def _check_mcp_mode(self) -> None:
        """
        检查 MCP 模式并在必要时抛出异常。

        MCP 模式下，agent_platform 作为纯工具箱运行，
        Claude 是唯一的 LLM，不允许创建其他 LLM 客户端。

        Phase 3.2 Fix P1-03: 使用 factory.is_mcp_mode() 统一检查逻辑
        """
        # 延迟导入避免循环依赖
        from .factory import is_mcp_mode
        if is_mcp_mode():
            from ..core.exceptions import LLMNotConfiguredError
            raise LLMNotConfiguredError(
                "MCP 工具模式下禁止创建 LLM 客户端。"
                "在此模式下，Claude 是唯一的 LLM，agent_platform 仅提供工具。"
                "如需使用 CLI 模式，请移除 AGENT_PLATFORM_MODE 环境变量或设置为 'cli'。"
            )

    @property
    def messages(self) -> MessagesAPI:
        """兼容层：提供 messages.create() 接口"""
        if self._messages_api is None:
            self._messages_api = MessagesAPI(self)
        return self._messages_api

    @abstractmethod
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
        """
        生成 LLM 响应。

        Args:
            system: 系统提示词
            user: 用户消息
            model: 模型名称（可选，使用默认模型）
            max_tokens: 最大生成 token 数
            temperature: 温度参数
            **kwargs: 其他模型特定参数

        Returns:
            LLMResponse 对象

        Raises:
            LLMClientError: LLM 调用失败
        """
        ...

    def generate_text(
        self,
        system: str,
        user: str,
        **kwargs: Any,
    ) -> str:
        """
        生成 LLM 响应（仅返回文本）。

        便捷方法，内部调用 generate() 并提取文本。

        Args:
            system: 系统提示词
            user: 用户消息
            **kwargs: 传递给 generate() 的参数

        Returns:
            生成的文本内容
        """
        response = self.generate(system, user, **kwargs)
        return response.text


class DummyLLMClient(LLMClient):
    """
    占位 LLM 客户端（用于测试或无 API Key 环境）。

    默认行为：调用 generate() 时抛出 RuntimeError，清晰提示配置方法。

    测试模式配置选项：
    - raise_on_call=False: 返回默认占位响应
    - mock_response: 自定义返回的 LLMResponse 或文本
    - mock_error: 自定义抛出的异常（模拟 RateLimitError 等）

    示例:
        # 生产环境默认行为（无 API Key 时的 fallback）
        client = DummyLLMClient()
        client.generate(...)  # 抛出 RuntimeError

        # 测试：返回默认 mock 响应
        client = DummyLLMClient(raise_on_call=False)
        resp = client.generate(...)  # 返回 "[DummyLLMClient Mock Response]..."

        # 测试：自定义 mock 响应
        client = DummyLLMClient(mock_response="Hello from mock!")
        resp = client.generate(...)  # resp.text == "Hello from mock!"

        # 测试：模拟 LLM 错误
        client = DummyLLMClient(mock_error=RateLimitError("Rate limited"))
        client.generate(...)  # 抛出 RateLimitError
    """

    # 清晰的错误提示信息
    NO_LLM_ERROR_MESSAGE = """
╔══════════════════════════════════════════════════════════════════╗
║  DummyLLMClient: No LLM backend configured                       ║
╠══════════════════════════════════════════════════════════════════╣
║  To use LLM features, configure one of the following:            ║
║                                                                  ║
║  Option 1: Set ANTHROPIC_API_KEY environment variable            ║
║    export ANTHROPIC_API_KEY="sk-ant-..."                         ║
║                                                                  ║
║  Option 2: Install Claude Code CLI                               ║
║    npm install -g @anthropic-ai/claude-code                      ║
║                                                                  ║
║  For development/testing without LLM:                            ║
║    Use DummyLLMClient(raise_on_call=False) to get mock responses ║
╚══════════════════════════════════════════════════════════════════╝
""".strip()

    def __init__(
        self,
        raise_on_call: bool = True,
        mock_response: Optional[Any] = None,
        mock_error: Optional[Exception] = None,
    ):
        """
        Args:
            raise_on_call: 调用时是否抛出异常（默认 True）
                - True: 抛出 RuntimeError，清晰提示配置方法
                - False: 返回占位响应（仅用于测试）
            mock_response: 自定义 mock 响应（可选）
                - str: 将被包装为 LLMResponse(text=...)
                - LLMResponse: 直接返回
                - 设置后自动禁用 raise_on_call
            mock_error: 自定义 mock 异常（可选）
                - 设置后 generate() 将抛出此异常
                - 优先级高于 mock_response
        """
        # DummyLLMClient 跳过 MCP 模式检查，允许在测试中使用
        super().__init__(_skip_mcp_check=True)
        self._raise_on_call = raise_on_call
        self._mock_response = mock_response
        self._mock_error = mock_error

        # 如果设置了 mock_response 或 mock_error，自动禁用默认的 raise_on_call
        if mock_response is not None or mock_error is not None:
            self._raise_on_call = False

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
        """返回占位响应、自定义 mock 响应，或抛出异常"""
        # 优先级 1: 抛出自定义错误（模拟 LLM 错误场景）
        if self._mock_error is not None:
            raise self._mock_error

        # 优先级 2: 默认的"未配置 LLM"错误
        if self._raise_on_call:
            raise RuntimeError(self.NO_LLM_ERROR_MESSAGE)

        # 优先级 3: 返回自定义 mock 响应
        if self._mock_response is not None:
            if isinstance(self._mock_response, LLMResponse):
                return self._mock_response
            elif isinstance(self._mock_response, str):
                return LLMResponse(
                    text=self._mock_response,
                    model="dummy-mock",
                    usage={"input_tokens": 0, "output_tokens": 0},
                )
            else:
                # 尝试转为字符串
                return LLMResponse(
                    text=str(self._mock_response),
                    model="dummy-mock",
                    usage={"input_tokens": 0, "output_tokens": 0},
                )

        # 优先级 4: 默认 mock 响应（raise_on_call=False 且无 mock_response）
        system_preview = system[:50] + "..." if len(system) > 50 else system
        user_preview = user[:50] + "..." if len(user) > 50 else user
        return LLMResponse(
            text=f"[DummyLLMClient Mock Response]\nSystem: {system_preview}\nUser: {user_preview}",
            model="dummy-mock",
            usage={"input_tokens": 0, "output_tokens": 0},
        )


__all__ = [
    "LLMClient",
    "LLMResponse",
    "DummyLLMClient",
]
