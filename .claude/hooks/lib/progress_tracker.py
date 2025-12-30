#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Progress Tracker - 进度追踪器存根模块

提供基本的进度追踪功能。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path
import json


@dataclass
class Module:
    """模块信息"""
    id: str
    name: str
    progress: int = 0
    status: str = "pending"


@dataclass
class Task:
    """任务信息"""
    id: str
    title: str
    status: str = "pending"  # pending, in_progress, completed


class ProgressTracker:
    """进度追踪器"""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path(__file__).parent.parent.parent / "data"
        self.modules: Dict[str, Module] = {}
        self.tasks: List[Task] = []

    def get_overall_progress(self) -> int:
        """获取整体进度百分比"""
        if not self.modules:
            return 0
        total = sum(m.progress for m in self.modules.values())
        return int(total / len(self.modules))

    def get_tasks_by_status(self, status: str) -> List[Task]:
        """按状态获取任务"""
        return [t for t in self.tasks if t.status == status]

    def load(self) -> None:
        """加载进度数据"""
        progress_file = self.data_dir / "progress.json"
        if progress_file.exists():
            try:
                with open(progress_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for mid, mdata in data.get("modules", {}).items():
                        self.modules[mid] = Module(
                            id=mid,
                            name=mdata.get("name", mid),
                            progress=mdata.get("progress", 0),
                            status=mdata.get("status", "pending"),
                        )
                    for tdata in data.get("tasks", []):
                        self.tasks.append(Task(
                            id=tdata.get("id", ""),
                            title=tdata.get("title", ""),
                            status=tdata.get("status", "pending"),
                        ))
            except Exception:
                pass


# 单例实例
_tracker: Optional[ProgressTracker] = None


def get_tracker() -> ProgressTracker:
    """获取全局追踪器实例"""
    global _tracker
    if _tracker is None:
        _tracker = ProgressTracker()
        _tracker.load()
    return _tracker


def generate_progress_report() -> str:
    """生成进度报告"""
    tracker = get_tracker()
    progress = tracker.get_overall_progress()
    completed = len(tracker.get_tasks_by_status("completed"))
    in_progress = len(tracker.get_tasks_by_status("in_progress"))

    return f"Progress: {progress}% | Completed: {completed} | In Progress: {in_progress}"
