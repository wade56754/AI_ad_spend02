"""
任务列表持久化 (Anthropic 风格)

基准文档: MASTER.md v4.6
版本: v4.2

设计原则:
- 任务只能 pending → in_progress → completed/failed
- 禁止删除或回滚任务状态
- 支持 Session 恢复
"""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
import json
import uuid

# 任务状态类型
TaskStatus = Literal["pending", "in_progress", "completed", "failed", "blocked"]


@dataclass
class TaskItem:
    """任务项"""

    id: str
    content: str
    status: TaskStatus = "pending"
    priority: int = 5  # 1-10, 10 最高

    # 阶段信息
    phase_id: Optional[int] = None
    phase_name: Optional[str] = None

    # 输出文件
    output_files: List[str] = field(default_factory=list)

    # 元数据
    created_at: str = ""
    updated_at: str = ""
    completed_at: Optional[str] = None

    # 错误信息
    error_message: Optional[str] = None
    retry_count: int = 0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskItem":
        """从字典创建"""
        return cls(**data)

    def is_pending(self) -> bool:
        return self.status == "pending"

    def is_completed(self) -> bool:
        return self.status == "completed"

    def is_failed(self) -> bool:
        return self.status == "failed"


class TaskListManager:
    """任务列表管理器 - 支持持久化和 Session 恢复"""

    def __init__(self, task_file: Path):
        """初始化

        Args:
            task_file: 任务文件路径
        """
        self.task_file = Path(task_file)
        self.tasks: List[TaskItem] = []
        self.session_id: str = ""
        self.requirement: str = ""
        self.created_at: str = ""

        self._load()

    def _load(self):
        """从文件加载"""
        if not self.task_file.exists():
            return

        try:
            data = json.loads(self.task_file.read_text(encoding="utf-8"))
            self.tasks = [TaskItem.from_dict(t) for t in data.get("tasks", [])]
            self.session_id = data.get("session_id", "")
            self.requirement = data.get("requirement", "")
            self.created_at = data.get("created_at", "")
        except Exception:
            pass

    def _save(self):
        """保存到文件"""
        self.task_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "session_id": self.session_id,
            "requirement": self.requirement,
            "created_at": self.created_at,
            "updated_at": datetime.now().isoformat(),
            "tasks": [t.to_dict() for t in self.tasks],
        }

        self.task_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def init_session(self, requirement: str) -> str:
        """初始化新会话

        Args:
            requirement: 需求描述

        Returns:
            session_id
        """
        self.session_id = str(uuid.uuid4())[:8]
        self.requirement = requirement
        self.created_at = datetime.now().isoformat()
        self.tasks = []
        self._save()
        return self.session_id

    def add(
        self,
        content: str,
        priority: int = 5,
        phase_id: Optional[int] = None,
        phase_name: Optional[str] = None,
    ) -> TaskItem:
        """添加任务

        Args:
            content: 任务内容
            priority: 优先级 (1-10)
            phase_id: 阶段 ID
            phase_name: 阶段名称

        Returns:
            TaskItem
        """
        task = TaskItem(
            id=f"task_{len(self.tasks):03d}",
            content=content,
            priority=priority,
            phase_id=phase_id,
            phase_name=phase_name,
        )
        self.tasks.append(task)
        self._save()
        return task

    def update_status(self, task_id: str, status: TaskStatus, error: Optional[str] = None):
        """更新任务状态

        Args:
            task_id: 任务 ID
            status: 新状态
            error: 错误信息 (如果失败)
        """
        for task in self.tasks:
            if task.id == task_id:
                task.status = status
                task.updated_at = datetime.now().isoformat()

                if status == "completed":
                    task.completed_at = task.updated_at
                elif status == "failed":
                    task.error_message = error

                self._save()
                return

    def complete_task(self, task_id: str, output_files: Optional[List[str]] = None):
        """完成任务

        Args:
            task_id: 任务 ID
            output_files: 输出文件列表
        """
        for task in self.tasks:
            if task.id == task_id:
                task.status = "completed"
                task.updated_at = datetime.now().isoformat()
                task.completed_at = task.updated_at
                if output_files:
                    task.output_files = output_files
                self._save()
                return

    def fail_task(self, task_id: str, error: str):
        """标记任务失败

        Args:
            task_id: 任务 ID
            error: 错误信息
        """
        for task in self.tasks:
            if task.id == task_id:
                task.status = "failed"
                task.error_message = error
                task.retry_count += 1
                task.updated_at = datetime.now().isoformat()
                self._save()
                return

    def get_pending(self) -> List[TaskItem]:
        """获取待处理任务 (按优先级排序)"""
        pending = [t for t in self.tasks if t.status == "pending"]
        return sorted(pending, key=lambda x: -x.priority)

    def get_next(self) -> Optional[TaskItem]:
        """获取下一个待处理任务"""
        pending = self.get_pending()
        return pending[0] if pending else None

    def get_in_progress(self) -> List[TaskItem]:
        """获取进行中的任务"""
        return [t for t in self.tasks if t.status == "in_progress"]

    def get_completed(self) -> List[TaskItem]:
        """获取已完成任务"""
        return [t for t in self.tasks if t.status == "completed"]

    def get_failed(self) -> List[TaskItem]:
        """获取失败任务"""
        return [t for t in self.tasks if t.status == "failed"]

    def can_resume(self) -> bool:
        """检查是否可以恢复"""
        return len(self.tasks) > 0 and any(
            t.status in ("pending", "in_progress")
            for t in self.tasks
        )

    def get_progress(self) -> Dict[str, int]:
        """获取进度统计"""
        return {
            "total": len(self.tasks),
            "pending": len(self.get_pending()),
            "in_progress": len(self.get_in_progress()),
            "completed": len(self.get_completed()),
            "failed": len(self.get_failed()),
        }

    def generate_reminder(self) -> str:
        """生成任务提醒"""
        progress = self.get_progress()
        pending = self.get_pending()

        lines = [
            "=" * 40,
            "📋 任务状态",
            "=" * 40,
            f"需求: {self.requirement}",
            f"会话: {self.session_id}",
            f"进度: {progress['completed']}/{progress['total']}",
            "",
        ]

        if pending:
            lines.append("待处理任务:")
            for task in pending[:5]:  # 只显示前 5 个
                phase_info = f"[P{task.phase_id}]" if task.phase_id is not None else ""
                lines.append(f"  - [{task.id}] {phase_info} {task.content}")
        else:
            lines.append("✅ 所有任务已完成!")

        if progress['failed'] > 0:
            lines.extend([
                "",
                f"⚠️ 失败任务: {progress['failed']}",
            ])
            for task in self.get_failed()[:3]:
                lines.append(f"  - {task.id}: {task.error_message}")

        return "\n".join(lines)

    def clear(self):
        """清空任务列表"""
        self.tasks = []
        self.session_id = ""
        self.requirement = ""
        if self.task_file.exists():
            self.task_file.unlink()
