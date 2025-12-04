"""
Agent Registry - 插件注册中心

提供 Agent 的注册、发现和实例化功能。
"""

from typing import Any, Callable, Dict, List, Optional, Type, Union
from dataclasses import dataclass, field
import logging
import threading

from .protocol import AgentProtocol
from .exceptions import AgentNotFoundError, AgentRegistrationError

logger = logging.getLogger(__name__)


@dataclass
class AgentMeta:
    """
    Agent 元信息

    Phase 2: 新增 mcp_safe 字段
    - mcp_safe=True: Agent 不调用 LLM，可在 MCP 模式下安全运行
    - mcp_safe=False: Agent 可能调用 LLM，MCP 模式下禁用
    """

    name: str
    factory: Callable[..., AgentProtocol]
    description: str = ""
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    mcp_safe: bool = False  # Phase 2: 默认不安全，需显式声明

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "tags": self.tags,
            "mcp_safe": self.mcp_safe,
        }


class AgentRegistry:
    """
    Agent 插件注册中心（线程安全单例）。

    使用方式：
    ```python
    # 获取注册表
    registry = AgentRegistry.instance()

    # 注册 Agent
    registry.register("fe", FEAgent, description="Frontend Agent")

    # 发现 Agent
    agent = registry.create("fe", config={"model": "claude-3"})

    # 列出所有 Agent
    for meta in registry.list_agents():
        print(f"{meta.name}: {meta.description}")
    ```
    """

    _instance: Optional["AgentRegistry"] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self):
        self._agents: Dict[str, AgentMeta] = {}
        self._agents_lock = threading.Lock()

    @classmethod
    def instance(cls) -> "AgentRegistry":
        """获取单例实例（线程安全）"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """重置注册表（用于测试）"""
        with cls._lock:
            cls._instance = None

    def register(
        self,
        name: str,
        factory: Union[Callable[..., AgentProtocol], Type[AgentProtocol]],
        *,
        description: str = "",
        version: str = "1.0.0",
        tags: Optional[List[str]] = None,
        mcp_safe: bool = False,
        override: bool = False,
    ) -> None:
        """
        注册 Agent。

        Args:
            name: 唯一标识符
            factory: Agent 工厂函数或类
            description: 描述
            version: 版本号
            tags: 标签（用于分类筛选）
            mcp_safe: (Phase 2) 是否 MCP 安全（不调用 LLM）
            override: 是否允许覆盖已注册的同名 Agent

        Raises:
            AgentRegistrationError: 注册失败
        """
        with self._agents_lock:
            if name in self._agents and not override:
                raise AgentRegistrationError(
                    name,
                    f"Already registered. Use override=True to replace.",
                )

            self._agents[name] = AgentMeta(
                name=name,
                factory=factory,
                description=description,
                version=version,
                tags=tags or [],
                mcp_safe=mcp_safe,
            )
            logger.info(f"Registered agent: {name} (v{version}, mcp_safe={mcp_safe})")

    def unregister(self, name: str) -> bool:
        """
        注销 Agent。

        Returns:
            True 如果成功注销，False 如果 Agent 不存在
        """
        with self._agents_lock:
            if name in self._agents:
                del self._agents[name]
                logger.info(f"Unregistered agent: {name}")
                return True
            return False

    def get(self, name: str) -> Optional[AgentMeta]:
        """获取 Agent 元信息"""
        return self._agents.get(name)

    def create(self, name: str, **kwargs: Any) -> AgentProtocol:
        """
        创建 Agent 实例。

        Args:
            name: Agent 名称
            **kwargs: 传递给工厂函数的参数

        Returns:
            Agent 实例

        Raises:
            AgentNotFoundError: Agent 未注册
            AgentRegistrationError: 工厂函数调用失败（参数不匹配等）
        """
        meta = self._agents.get(name)
        if meta is None:
            available = list(self._agents.keys())
            raise AgentNotFoundError(name, available)

        # Phase 2.1: 增强错误处理，捕获工厂函数调用失败
        try:
            return meta.factory(**kwargs)
        except TypeError as e:
            # 工厂函数参数不匹配
            raise AgentRegistrationError(
                name,
                f"Factory instantiation failed: {e}. "
                f"Check if the provided kwargs match the Agent's __init__ signature.",
            ) from e
        except Exception as e:
            # 其他初始化错误
            raise AgentRegistrationError(
                name,
                f"Agent creation failed: {type(e).__name__}: {e}",
            ) from e

    def list_agents(
        self, tag: Optional[str] = None, mcp_safe_only: bool = False
    ) -> List[AgentMeta]:
        """
        列出已注册的 Agent。

        Args:
            tag: 按标签筛选（可选）
            mcp_safe_only: (Phase 2) 仅返回 mcp_safe=True 的 Agent
        """
        agents = list(self._agents.values())
        if tag:
            agents = [a for a in agents if tag in a.tags]
        if mcp_safe_only:
            agents = [a for a in agents if a.mcp_safe]
        return agents

    def list_mcp_safe_agents(self) -> List[AgentMeta]:
        """
        (Phase 2) 列出所有 MCP 安全的 Agent。

        MCP 模式下，只有 mcp_safe=True 的 Agent 可被调用。
        """
        return self.list_agents(mcp_safe_only=True)

    def is_mcp_safe(self, name: str) -> bool:
        """
        (Phase 2) 检查 Agent 是否 MCP 安全。

        Args:
            name: Agent 名称

        Returns:
            True 如果 mcp_safe=True，否则 False
            Agent 不存在时也返回 False
        """
        meta = self._agents.get(name)
        return meta.mcp_safe if meta else False

    def has(self, name: str) -> bool:
        """检查 Agent 是否已注册"""
        return name in self._agents

    @property
    def count(self) -> int:
        """已注册的 Agent 数量"""
        return len(self._agents)

    def __repr__(self) -> str:
        return f"<AgentRegistry agents={list(self._agents.keys())}>"


# ============================================================
# 便捷函数（模块级 API）
# ============================================================


def get_registry() -> AgentRegistry:
    """获取全局注册表实例"""
    return AgentRegistry.instance()


def register_agent(
    name: str,
    factory: Union[Callable[..., AgentProtocol], Type[AgentProtocol]],
    *,
    description: str = "",
    version: str = "1.0.0",
    tags: Optional[List[str]] = None,
    mcp_safe: bool = False,
    override: bool = False,
) -> None:
    """
    注册 Agent（便捷函数）。

    等价于 `get_registry().register(...)`

    Args:
        mcp_safe: (Phase 2) 是否 MCP 安全，默认 False
    """
    get_registry().register(
        name,
        factory,
        description=description,
        version=version,
        tags=tags,
        mcp_safe=mcp_safe,
        override=override,
    )


def create_agent(name: str, **kwargs: Any) -> AgentProtocol:
    """
    创建 Agent 实例（便捷函数）。

    等价于 `get_registry().create(...)`
    """
    return get_registry().create(name, **kwargs)


def list_agents(
    tag: Optional[str] = None, mcp_safe_only: bool = False
) -> List[AgentMeta]:
    """
    列出已注册的 Agent（便捷函数）。

    等价于 `get_registry().list_agents(...)`

    Args:
        mcp_safe_only: (Phase 2) 仅返回 mcp_safe=True 的 Agent
    """
    return get_registry().list_agents(tag=tag, mcp_safe_only=mcp_safe_only)


def list_mcp_safe_agents() -> List[AgentMeta]:
    """
    (Phase 2) 列出所有 MCP 安全的 Agent（便捷函数）。
    """
    return get_registry().list_mcp_safe_agents()


def is_agent_mcp_safe(name: str) -> bool:
    """
    (Phase 2) 检查 Agent 是否 MCP 安全（便捷函数）。
    """
    return get_registry().is_mcp_safe(name)
