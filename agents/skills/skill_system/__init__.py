"""
技能系统 (Skill System)

基于 wshobson/agents 渐进式披露架构设计
版本: v1.0
"""

from .base import Skill, SkillMetadata, SkillRegistry
from .loader import SkillLoader
from .wshobson_agent_loader import WshobsonAgentLoader, Agent
from .wshobson_skill_loader import WshobsonSkillLoader
from .agent_adapter import AgentAdapter
from .skill_adapter import SkillAdapter, AdaptedSkill
from .plugin_loader import PluginLoader, Plugin
from .model_strategy import ModelStrategy, ModelTier
from .path_utils import get_project_root, get_wshobson_agents_path
from .cache import AgentCache, SkillCache, LRUCache
from .config import Config, get_config

__all__ = [
    "Skill",
    "SkillMetadata",
    "SkillRegistry",
    "SkillLoader",
    "WshobsonAgentLoader",
    "Agent",
    "WshobsonSkillLoader",
    "AgentAdapter",
    "SkillAdapter",
    "AdaptedSkill",
    "PluginLoader",
    "Plugin",
    "ModelStrategy",
    "ModelTier",
    "get_project_root",
    "get_wshobson_agents_path",
    "AgentCache",
    "SkillCache",
    "LRUCache",
    "Config",
    "get_config",
]
