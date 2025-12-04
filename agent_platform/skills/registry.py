"""
agent_platform.skills.registry - Skill 注册与发现

Phase 3: 技能层迁移
- 提供 Skill 注册、发现、调用机制
- mcp_safe=True 的 Skill 可在 MCP 模式下安全运行
- 与 Agent Registry 设计对齐

设计原则:
- mcp_safe 是注册时的"唯一真相"
- 所有 Skill 通过 registry 注册
- MCP 模式下只暴露 mcp_safe=True 的 Skill

基准对齐:
- AGENT_PLATFORM_MIGRATION_PLAN_v1.2.md Phase 3
- Agent Layer Freeze v1.0
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class SkillMeta:
    """Skill 元数据."""

    name: str
    func: Callable[..., Dict[str, Any]]
    description: str = ""
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    mcp_safe: bool = False  # 默认不安全，需显式声明

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于 MCP 响应）."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "tags": self.tags,
            "mcp_safe": self.mcp_safe,
        }


class SkillRegistry:
    """Skill 注册表 (Singleton)."""

    _instance: Optional["SkillRegistry"] = None

    def __new__(cls) -> "SkillRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._skills: Dict[str, SkillMeta] = {}
        return cls._instance

    def register(
        self,
        name: str,
        func: Callable[..., Dict[str, Any]],
        description: str = "",
        version: str = "1.0.0",
        tags: Optional[List[str]] = None,
        mcp_safe: bool = False,
        override: bool = False,
    ) -> SkillMeta:
        """
        注册 Skill.

        Args:
            name: Skill 名称（唯一标识）
            func: Skill 函数
            description: 描述
            version: 版本号
            tags: 标签列表
            mcp_safe: 是否 MCP 安全
            override: 是否允许覆盖已注册的 Skill

        Returns:
            SkillMeta: 注册的元数据

        Raises:
            ValueError: Skill 已存在且 override=False
        """
        if name in self._skills and not override:
            raise ValueError(f"Skill '{name}' already registered. Use override=True to replace.")

        meta = SkillMeta(
            name=name,
            func=func,
            description=description,
            version=version,
            tags=tags or [],
            mcp_safe=mcp_safe,
        )
        self._skills[name] = meta
        logger.debug(f"Skill registered: {name} (mcp_safe={mcp_safe})")
        return meta

    def get(self, name: str) -> Optional[SkillMeta]:
        """获取 Skill 元数据."""
        return self._skills.get(name)

    def list_skills(self, mcp_safe_only: bool = False) -> List[SkillMeta]:
        """
        列出所有 Skill.

        Args:
            mcp_safe_only: 只返回 mcp_safe=True 的 Skill

        Returns:
            List[SkillMeta]: Skill 元数据列表
        """
        if mcp_safe_only:
            return [m for m in self._skills.values() if m.mcp_safe]
        return list(self._skills.values())

    def invoke(self, name: str, **kwargs: Any) -> Dict[str, Any]:
        """
        调用 Skill.

        Args:
            name: Skill 名称
            **kwargs: Skill 参数

        Returns:
            Dict[str, Any]: Skill 执行结果

        Raises:
            SkillNotFoundError: Skill 不存在
        """
        meta = self.get(name)
        if meta is None:
            from agent_platform.core.exceptions import SkillNotFoundError
            raise SkillNotFoundError(f"Skill '{name}' not found")
        return meta.func(**kwargs)

    def is_mcp_safe(self, name: str) -> bool:
        """检查 Skill 是否 MCP 安全."""
        meta = self.get(name)
        return meta.mcp_safe if meta else False

    def clear(self) -> None:
        """清空注册表（仅用于测试）."""
        self._skills.clear()


# Singleton instance
_registry = SkillRegistry()


def get_registry() -> SkillRegistry:
    """获取 Skill 注册表实例."""
    return _registry


def register_skill(
    name: str,
    func: Callable[..., Dict[str, Any]],
    description: str = "",
    version: str = "1.0.0",
    tags: Optional[List[str]] = None,
    mcp_safe: bool = False,
    override: bool = False,
) -> SkillMeta:
    """注册 Skill 到全局注册表."""
    return _registry.register(
        name=name,
        func=func,
        description=description,
        version=version,
        tags=tags,
        mcp_safe=mcp_safe,
        override=override,
    )


def list_skills(mcp_safe_only: bool = False) -> List[SkillMeta]:
    """列出所有 Skill."""
    return _registry.list_skills(mcp_safe_only=mcp_safe_only)


def list_mcp_safe_skills() -> List[SkillMeta]:
    """列出 MCP 安全的 Skill."""
    return _registry.list_skills(mcp_safe_only=True)


def invoke_skill(name: str, **kwargs: Any) -> Dict[str, Any]:
    """调用 Skill."""
    return _registry.invoke(name, **kwargs)


def is_skill_mcp_safe(name: str) -> bool:
    """检查 Skill 是否 MCP 安全."""
    return _registry.is_mcp_safe(name)
