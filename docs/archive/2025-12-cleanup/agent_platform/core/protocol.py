"""
Agent Protocol - Agent 标准协议定义

所有 Agent 必须实现 AgentProtocol 抽象基类。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class AgentContext(BaseModel):
    """
    Agent 执行上下文。

    用于在 Agent 调用链中传递追溯信息。
    """

    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_run_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"frozen": False}


class AgentProtocol(ABC):
    """
    所有 Agent 必须实现的协议。

    设计原则：
    - 无状态：每次调用独立，不依赖实例变量存储状态
    - 可追溯：通过 AgentContext 传递 run_id 用于日志关联
    - 可插拔：通过 registry 动态注册/发现

    实现示例：
    ```python
    class MyAgent(AgentProtocol):
        @property
        def name(self) -> str:
            return "my_agent"

        def handle_request(
            self,
            request: Dict[str, Any],
            context: Optional[AgentContext] = None,
        ) -> Dict[str, Any]:
            # 处理逻辑
            return {"success": True, "data": {"result": "..."}}
    ```
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent 唯一标识符（用于注册）"""
        ...

    @property
    def description(self) -> str:
        """Agent 描述（用于文档/发现）"""
        return ""

    @property
    def version(self) -> str:
        """Agent 版本号"""
        return "1.0.0"

    @abstractmethod
    def handle_request(
        self,
        request: Dict[str, Any],
        context: Optional[AgentContext] = None,
    ) -> Dict[str, Any]:
        """
        处理请求的主入口。

        Args:
            request: 请求参数，结构由具体 Agent 定义
            context: 执行上下文（可选，用于追溯）

        Returns:
            标准响应：{"success": bool, "data": Any, "error": Optional[str]}
        """
        ...

    def validate_request(self, request: Dict[str, Any]) -> Optional[str]:
        """
        请求校验（可选重写）。

        Returns:
            None 表示校验通过，否则返回错误信息
        """
        return None

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r} version={self.version!r}>"
