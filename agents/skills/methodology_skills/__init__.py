"""
方法论技能模块

这些技能封装了软件开发最佳实践的方法论，
与 Superpowers 技能系统保持兼容。

可用技能:
- tdd: 测试驱动开发
- debugging: 系统化调试
- planning: 计划编写

版本: v7.0
"""

from pathlib import Path

METHODOLOGY_SKILLS_DIR = Path(__file__).parent

__all__ = ["METHODOLOGY_SKILLS_DIR"]
