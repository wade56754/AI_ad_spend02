"""
事件流管理器 (OpenHands 风格)

基准文档: MASTER.md v4.6
版本: v4.2

功能:
- 记录所有事件
- 持久化到文件
- 支持事件查询和分析
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import json
import time

from .events import Event, EventType


@dataclass
class EventStreamStats:
    """事件流统计"""
    total_events: int = 0
    phases_completed: int = 0
    errors: int = 0
    warnings: int = 0
    file_operations: int = 0
    duration_ms: int = 0


class EventStream:
    """事件流管理器"""

    def __init__(
        self,
        event_file: Optional[Path] = None,
        auto_save: bool = True,
    ):
        """初始化

        Args:
            event_file: 事件文件路径 (None 表示不持久化)
            auto_save: 是否自动保存
        """
        self.event_file = Path(event_file) if event_file else None
        self.auto_save = auto_save
        self.events: List[Event] = []
        self._start_time: Optional[float] = None
        self._listeners: List[Callable[[Event], None]] = []

    def record(self, event: Event):
        """记录事件

        Args:
            event: 事件
        """
        self.events.append(event)

        # 通知监听器
        for listener in self._listeners:
            try:
                listener(event)
            except Exception:
                pass

        # 自动保存
        if self.auto_save and self.event_file:
            self._save()

    def _save(self):
        """保存到文件"""
        if not self.event_file:
            return

        self.event_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "created_at": datetime.now().isoformat(),
            "total_events": len(self.events),
            "events": [e.to_dict() for e in self.events],
        }

        self.event_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def load(self):
        """从文件加载"""
        if not self.event_file or not self.event_file.exists():
            return

        try:
            data = json.loads(self.event_file.read_text(encoding="utf-8"))
            self.events = [Event.from_dict(e) for e in data.get("events", [])]
        except Exception:
            pass

    # === 便捷方法 ===

    def session_start(self, session_id: str, requirement: str):
        """记录会话开始"""
        self._start_time = time.time()
        self.record(Event(
            type=EventType.SESSION_START,
            data={"session_id": session_id, "requirement": requirement},
        ))

    def session_end(self, success: bool):
        """记录会话结束"""
        duration_ms = int((time.time() - self._start_time) * 1000) if self._start_time else 0
        self.record(Event(
            type=EventType.SESSION_END,
            data={"success": success},
            duration_ms=duration_ms,
        ))

    def phase_start(self, phase_id: int, phase_name: str):
        """记录阶段开始"""
        self.record(Event(
            type=EventType.PHASE_START,
            phase_id=phase_id,
            phase_name=phase_name,
        ))

    def phase_end(self, phase_id: int, phase_name: str, success: bool, duration_ms: int = 0):
        """记录阶段结束"""
        self.record(Event(
            type=EventType.PHASE_END,
            phase_id=phase_id,
            phase_name=phase_name,
            data={"success": success},
            duration_ms=duration_ms,
        ))

    def file_edit(self, file_path: str, action: str, success: bool):
        """记录文件编辑"""
        self.record(Event(
            type=EventType.FILE_EDIT,
            data={"file": file_path, "action": action, "success": success},
        ))

    def error(self, message: str, phase_id: Optional[int] = None, phase_name: Optional[str] = None):
        """记录错误"""
        self.record(Event(
            type=EventType.ERROR,
            phase_id=phase_id,
            phase_name=phase_name,
            data={"message": message},
        ))

    def warning(self, message: str, phase_id: Optional[int] = None):
        """记录警告"""
        self.record(Event(
            type=EventType.WARNING,
            phase_id=phase_id,
            data={"message": message},
        ))

    def checkpoint(self, name: str, data: Optional[Dict[str, Any]] = None):
        """记录检查点"""
        self.record(Event(
            type=EventType.CHECKPOINT,
            data={"name": name, **(data or {})},
        ))

    # === 查询方法 ===

    def get_errors(self) -> List[Event]:
        """获取所有错误事件"""
        return [e for e in self.events if e.type == EventType.ERROR]

    def get_warnings(self) -> List[Event]:
        """获取所有警告事件"""
        return [e for e in self.events if e.type == EventType.WARNING]

    def get_phase_events(self) -> List[Event]:
        """获取所有阶段事件"""
        return [e for e in self.events if e.is_phase_event()]

    def get_by_phase(self, phase_id: int) -> List[Event]:
        """获取指定阶段的事件"""
        return [e for e in self.events if e.phase_id == phase_id]

    # === 统计方法 ===

    def get_stats(self) -> EventStreamStats:
        """获取统计"""
        phases_completed = len([
            e for e in self.events
            if e.type == EventType.PHASE_END and e.data.get("success")
        ])

        return EventStreamStats(
            total_events=len(self.events),
            phases_completed=phases_completed,
            errors=len(self.get_errors()),
            warnings=len(self.get_warnings()),
            file_operations=len([e for e in self.events if e.type in (EventType.FILE_EDIT, EventType.FILE_CREATE)]),
            duration_ms=sum(e.duration_ms or 0 for e in self.events),
        )

    def get_summary(self) -> Dict[str, Any]:
        """获取摘要"""
        stats = self.get_stats()
        return {
            "total_events": stats.total_events,
            "phases_completed": stats.phases_completed,
            "errors": stats.errors,
            "warnings": stats.warnings,
            "duration_ms": stats.duration_ms,
        }

    # === 监听器 ===

    def add_listener(self, listener: Callable[[Event], None]):
        """添加事件监听器"""
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[Event], None]):
        """移除事件监听器"""
        if listener in self._listeners:
            self._listeners.remove(listener)

    # === 其他 ===

    def clear(self):
        """清空事件"""
        self.events = []
        self._start_time = None
