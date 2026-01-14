"""
适配器模块

提供与外部技能系统的集成:
- Superpowers: TDD, 调试, 计划编写
"""

from .superpowers import SuperpowersAdapter, load_superpowers_skill

__all__ = [
    "SuperpowersAdapter",
    "load_superpowers_skill",
]
