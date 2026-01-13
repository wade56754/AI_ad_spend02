"""
Progress Tracker - 任务进度追踪

跟踪项目级别的任务进度，支持:
- 任务状态更新
- 里程碑记录
- 进度报告生成

版本: v7.0
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """任务状态"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


@dataclass
class TaskRecord:
    """任务记录"""
    task_id: str
    title: str
    status: TaskStatus
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    notes: str = ""


class ProgressTracker:
    """
    进度追踪器
    
    管理项目级别的任务进度
    """
    
    def __init__(self, progress_file: Optional[Path] = None):
        """
        初始化追踪器
        
        Args:
            progress_file: 进度文件路径
        """
        self.progress_file = progress_file or Path("memory-bank/progress.md")
        self._ensure_file()
    
    def _ensure_file(self) -> None:
        """确保进度文件存在"""
        if not self.progress_file.exists():
            self.progress_file.parent.mkdir(parents=True, exist_ok=True)
            self._write_header()
    
    def _write_header(self) -> None:
        """写入文件头"""
        header = """# 任务进度

> 自动记录任务完成情况

---

"""
        self.progress_file.write_text(header, encoding="utf-8")
    
    def start_task(self, task_id: str, title: str) -> None:
        """
        开始任务
        
        Args:
            task_id: 任务 ID
            title: 任务标题
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        entry = f"""
## {task_id}: {title}

- **状态**: 🔄 进行中
- **开始时间**: {timestamp}

"""
        
        with open(self.progress_file, "a", encoding="utf-8") as f:
            f.write(entry)
        
        logger.info(f"任务开始: {task_id}")
    
    def complete_task(
        self,
        task_id: str,
        summary: str,
        files_changed: Optional[List[str]] = None,
    ) -> None:
        """
        完成任务
        
        Args:
            task_id: 任务 ID
            summary: 完成摘要
            files_changed: 修改的文件列表
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        entry = f"""
### [{timestamp}] ✅ {task_id} 完成

{summary}

"""
        
        if files_changed:
            entry += "**修改的文件**:\n"
            for f in files_changed:
                entry += f"- `{f}`\n"
            entry += "\n"
        
        with open(self.progress_file, "a", encoding="utf-8") as f:
            f.write(entry)
        
        logger.info(f"任务完成: {task_id}")
    
    def block_task(self, task_id: str, reason: str) -> None:
        """
        阻塞任务
        
        Args:
            task_id: 任务 ID
            reason: 阻塞原因
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        entry = f"""
### [{timestamp}] 🚫 {task_id} 阻塞

**原因**: {reason}

"""
        
        with open(self.progress_file, "a", encoding="utf-8") as f:
            f.write(entry)
        
        logger.warning(f"任务阻塞: {task_id} - {reason}")
    
    def add_milestone(self, milestone: str, description: str) -> None:
        """
        添加里程碑
        
        Args:
            milestone: 里程碑名称
            description: 描述
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        entry = f"""
---

## 🎯 里程碑: {milestone}

> {timestamp}

{description}

---

"""
        
        with open(self.progress_file, "a", encoding="utf-8") as f:
            f.write(entry)
        
        logger.info(f"里程碑: {milestone}")
    
    def add_note(self, note: str) -> None:
        """
        添加备注
        
        Args:
            note: 备注内容
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        entry = f"""
> [{timestamp}] 📝 {note}

"""
        
        with open(self.progress_file, "a", encoding="utf-8") as f:
            f.write(entry)
    
    def get_progress(self) -> str:
        """
        获取进度内容
        
        Returns:
            进度文件内容
        """
        if self.progress_file.exists():
            return self.progress_file.read_text(encoding="utf-8")
        return ""
    
    def generate_report(self) -> Dict[str, int]:
        """
        生成进度报告
        
        Returns:
            统计信息字典
        """
        content = self.get_progress()
        
        return {
            "completed": content.count("✅"),
            "blocked": content.count("🚫"),
            "in_progress": content.count("🔄"),
            "milestones": content.count("🎯"),
        }


__all__ = [
    "ProgressTracker",
    "TaskStatus",
    "TaskRecord",
]
