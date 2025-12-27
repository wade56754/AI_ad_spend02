"""
事件定义

版本: v4.2
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class EventType(Enum):
    """事件类型"""

    # 阶段事件
    PHASE_START = "phase_start"
    PHASE_END = "phase_end"

    # 操作事件
    FILE_READ = "file_read"
    FILE_EDIT = "file_edit"
    FILE_CREATE = "file_create"

    # 搜索事件
    SEARCH_START = "search_start"
    SEARCH_RESULT = "search_result"

    # 验证事件
    VALIDATE_START = "validate_start"
    VALIDATE_RESULT = "validate_result"

    # 错误事件
    ERROR = "error"
    WARNING = "warning"

    # 用户交互
    USER_INPUT = "user_input"
    USER_CONFIRM = "user_confirm"

    # 系统事件
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    CHECKPOINT = "checkpoint"


@dataclass
class Event:
    """事件记录"""

    type: EventType
    phase_id: Optional[int] = None
    phase_name: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    duration_ms: Optional[int] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "type": self.type.value,
            "phase_id": self.phase_id,
            "phase_name": self.phase_name,
            "data": self.data,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """从字典创建"""
        return cls(
            type=EventType(data["type"]),
            phase_id=data.get("phase_id"),
            phase_name=data.get("phase_name"),
            data=data.get("data", {}),
            timestamp=data.get("timestamp", ""),
            duration_ms=data.get("duration_ms"),
        )

    def is_error(self) -> bool:
        """是否是错误事件"""
        return self.type in (EventType.ERROR, EventType.WARNING)

    def is_phase_event(self) -> bool:
        """是否是阶段事件"""
        return self.type in (EventType.PHASE_START, EventType.PHASE_END)
