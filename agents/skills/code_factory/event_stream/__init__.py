"""
事件流模块 (OpenHands 风格)

功能:
- Action-Observation 事件记录
- 完整审计追踪
- 事件流分析
"""

from .events import Event, EventType
from .stream import EventStream

__all__ = [
    "Event",
    "EventType",
    "EventStream",
]
