"""
技能系统 (Skill System)

基于 wshobson/agents 渐进式披露架构设计
支持三层加载：元数据 → 指令 → 资源

版本: v1.0
基准: AI_CODING_BEST_PRACTICES.md BP-01
"""

from .base import Skill, SkillMetadata, SkillRegistry
from .loader import SkillLoader

__all__ = [
    "Skill",
    "SkillMetadata",
    "SkillRegistry",
    "SkillLoader",
]
