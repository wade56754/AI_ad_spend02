"""
会话管理器 - 支持多会话自主编码

借鉴 Anthropic autonomous-coding 的会话管理:
- 会话状态持久化
- 自动恢复中断
- 进度追踪

来源: Anthropic autonomous-coding/agent.py
"""

import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class SessionType(Enum):
    """会话类型"""
    INITIALIZER = "initializer"  # 初始化会话
    FACTORY = "factory"          # 工厂执行会话
    VERIFY = "verify"            # 验证会话


class SessionStatus(Enum):
    """会话状态"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SessionState:
    """会话状态"""
    session_id: str
    session_type: str
    status: str
    started_at: str
    updated_at: str
    completed_at: Optional[str] = None

    # 进度信息
    current_task_id: Optional[str] = None
    current_phase: Optional[str] = None
    tasks_completed: int = 0
    tasks_total: int = 0

    # 迭代信息
    iteration: int = 1
    max_iterations: Optional[int] = None

    # 错误信息
    last_error: Optional[str] = None
    retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionState":
        return cls(**data)


@dataclass
class ProgressNote:
    """进度笔记"""
    timestamp: str
    session_id: str
    message: str
    phase: Optional[str] = None
    task_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class SessionManager:
    """
    会话管理器

    核心功能:
    - 会话状态持久化
    - 断点续传
    - 进度追踪
    - 自动恢复
    """

    STATE_FILE = "factory-session.json"
    PROGRESS_FILE = "factory-progress.txt"
    AUTO_CONTINUE_DELAY = 3  # 秒

    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.state_file = self.project_dir / self.STATE_FILE
        self.progress_file = self.project_dir / self.PROGRESS_FILE
        self.state: Optional[SessionState] = None
        self._load_state()

    def _load_state(self) -> None:
        """加载会话状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.state = SessionState.from_dict(data)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Failed to load session state: {e}")
                self.state = None

    def _save_state(self) -> None:
        """保存会话状态"""
        if self.state:
            self.state.updated_at = datetime.now().isoformat()
            self.project_dir.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self.state.to_dict(), f, ensure_ascii=False, indent=2)

    def has_existing_session(self) -> bool:
        """检查是否有现有会话"""
        return self.state is not None and self.state.status != SessionStatus.COMPLETED.value

    def is_initializer_completed(self) -> bool:
        """检查初始化是否完成"""
        if not self.state:
            return False
        return (
            self.state.session_type == SessionType.INITIALIZER.value
            and self.state.status == SessionStatus.COMPLETED.value
        )

    def get_session_type(self) -> SessionType:
        """获取当前应该执行的会话类型"""
        if not self.has_existing_session():
            return SessionType.INITIALIZER
        if self.is_initializer_completed():
            return SessionType.FACTORY
        return SessionType(self.state.session_type)

    def start_session(self, session_type: SessionType, max_iterations: int = None) -> SessionState:
        """开始新会话"""
        session_id = f"{session_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.state = SessionState(
            session_id=session_id,
            session_type=session_type.value,
            status=SessionStatus.RUNNING.value,
            started_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            max_iterations=max_iterations,
        )

        self._save_state()
        self._log_progress(f"会话开始: {session_type.value.upper()}")

        return self.state

    def resume_session(self) -> Optional[SessionState]:
        """恢复会话"""
        if not self.has_existing_session():
            return None

        self.state.status = SessionStatus.RUNNING.value
        self.state.iteration += 1
        self._save_state()
        self._log_progress(f"会话恢复: 迭代 {self.state.iteration}")

        return self.state

    def pause_session(self) -> None:
        """暂停会话"""
        if self.state:
            self.state.status = SessionStatus.PAUSED.value
            self._save_state()
            self._log_progress("会话暂停 (Ctrl+C)")
            print(f"\n会话已暂停。要恢复，请运行相同的命令。")

    def complete_session(self) -> None:
        """完成会话"""
        if self.state:
            self.state.status = SessionStatus.COMPLETED.value
            self.state.completed_at = datetime.now().isoformat()
            self._save_state()
            self._log_progress("会话完成")

    def fail_session(self, error: str) -> None:
        """会话失败"""
        if self.state:
            self.state.status = SessionStatus.FAILED.value
            self.state.last_error = error
            self._save_state()
            self._log_progress(f"会话失败: {error}")

    def update_progress(
        self,
        task_id: str = None,
        phase: str = None,
        tasks_completed: int = None,
        tasks_total: int = None,
    ) -> None:
        """更新进度"""
        if self.state:
            if task_id:
                self.state.current_task_id = task_id
            if phase:
                self.state.current_phase = phase
            if tasks_completed is not None:
                self.state.tasks_completed = tasks_completed
            if tasks_total is not None:
                self.state.tasks_total = tasks_total
            self._save_state()

    def should_continue(self) -> bool:
        """检查是否应该继续"""
        if not self.state:
            return False

        # 检查迭代限制
        if self.state.max_iterations and self.state.iteration >= self.state.max_iterations:
            return False

        # 检查状态
        return self.state.status == SessionStatus.RUNNING.value

    def wait_for_continue(self) -> None:
        """等待自动继续"""
        print(f"\n等待 {self.AUTO_CONTINUE_DELAY} 秒后自动继续...")
        print("按 Ctrl+C 暂停\n")
        time.sleep(self.AUTO_CONTINUE_DELAY)

    def _log_progress(self, message: str) -> None:
        """记录进度到文件"""
        note = ProgressNote(
            timestamp=datetime.now().isoformat(),
            session_id=self.state.session_id if self.state else "unknown",
            message=message,
            phase=self.state.current_phase if self.state else None,
            task_id=self.state.current_task_id if self.state else None,
        )

        with open(self.progress_file, "a", encoding="utf-8") as f:
            f.write(f"[{note.timestamp}] [{note.session_id}] {note.message}\n")

    def get_progress_summary(self) -> str:
        """获取进度摘要"""
        if not self.state:
            return "无活动会话"

        progress = (
            f"{self.state.tasks_completed}/{self.state.tasks_total}"
            if self.state.tasks_total > 0
            else "0/0"
        )
        pct = (
            round(self.state.tasks_completed / self.state.tasks_total * 100, 1)
            if self.state.tasks_total > 0
            else 0
        )

        return (
            f"会话: {self.state.session_type} | "
            f"状态: {self.state.status} | "
            f"进度: {progress} ({pct}%) | "
            f"迭代: {self.state.iteration}"
        )

    def print_session_header(self) -> None:
        """打印会话头部"""
        session_type = self.state.session_type.upper() if self.state else "UNKNOWN"
        iteration = self.state.iteration if self.state else 1

        print("\n" + "=" * 60)
        print(f"  AI 代码工厂 v3.0 - {session_type} SESSION")
        print(f"  迭代: {iteration}")
        print("=" * 60 + "\n")


class ProgressTracker:
    """
    进度追踪器

    用于在会话中追踪和显示进度
    """

    def __init__(self, session_manager: SessionManager):
        self.session = session_manager

    def start_task(self, task_id: str, description: str) -> None:
        """开始任务"""
        self.session.update_progress(task_id=task_id)
        print(f"\n>>> 任务: {task_id}")
        print(f"    描述: {description}")

    def start_phase(self, phase: str) -> None:
        """开始阶段"""
        self.session.update_progress(phase=phase)
        phase_emoji = {
            "search": "🔍",
            "select": "🎯",
            "adapt": "🔧",
            "assemble": "🧩",
            "verify": "✅",
        }.get(phase, "📝")
        print(f"    {phase_emoji} Phase: {phase.upper()}")

    def complete_phase(self, phase: str, result: str = "ok") -> None:
        """完成阶段"""
        status = "✓" if result == "ok" else "✗"
        print(f"       {status} {phase} 完成")

    def complete_task(self, task_id: str, output_files: List[str] = None) -> None:
        """完成任务"""
        completed = self.session.state.tasks_completed + 1 if self.session.state else 1
        self.session.update_progress(tasks_completed=completed)
        print(f"    ✅ 任务完成: {task_id}")
        if output_files:
            for f in output_files[:3]:  # 最多显示 3 个
                print(f"       - {f}")

    def show_summary(self) -> None:
        """显示摘要"""
        print(f"\n{self.session.get_progress_summary()}")
