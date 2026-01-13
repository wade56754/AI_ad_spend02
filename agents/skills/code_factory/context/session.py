"""
Session Context - 会话级上下文管理

跟踪单次开发会话的状态，包括:
- 会话 ID
- 当前任务
- 已完成步骤
- 待处理步骤
- 关键决策
- 修改的文件

版本: v7.0
"""

import json
import uuid
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SessionContext:
    """
    会话上下文 - 跨消息记忆
    
    在单次开发会话中保持状态，即使对话中断也能恢复。
    """
    
    session_id: str
    started_at: str
    current_task: Optional[str] = None
    current_task_title: Optional[str] = None
    completed_steps: List[str] = field(default_factory=list)
    pending_steps: List[str] = field(default_factory=list)
    key_decisions: List[Dict[str, str]] = field(default_factory=list)
    modified_files: List[str] = field(default_factory=list)
    errors_encountered: List[Dict[str, str]] = field(default_factory=list)
    last_updated: Optional[str] = None
    
    # 默认存储路径
    DEFAULT_SESSION_PATH = Path("memory-bank/session/context.json")
    
    def save(self, path: Optional[Path] = None) -> None:
        """
        保存会话状态
        
        Args:
            path: 保存路径，默认为 memory-bank/session/context.json
        """
        save_path = path or self.DEFAULT_SESSION_PATH
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.last_updated = datetime.now().isoformat()
        
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)
        
        logger.debug(f"会话已保存: {self.session_id}")
    
    @classmethod
    def load(cls, path: Optional[Path] = None) -> Optional["SessionContext"]:
        """
        加载会话状态
        
        Args:
            path: 加载路径
            
        Returns:
            SessionContext 或 None
        """
        load_path = path or cls.DEFAULT_SESSION_PATH
        
        if not load_path.exists():
            return None
        
        try:
            with open(load_path, encoding="utf-8") as f:
                data = json.load(f)
            
            # 移除不在 dataclass 中的字段
            valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
            filtered_data = {k: v for k, v in data.items() if k in valid_fields}
            
            return cls(**filtered_data)
        except Exception as e:
            logger.error(f"加载会话失败: {e}")
            return None
    
    @classmethod
    def load_or_create(cls, path: Optional[Path] = None) -> "SessionContext":
        """
        加载或创建会话
        
        Args:
            path: 存储路径
            
        Returns:
            SessionContext 实例
        """
        session = cls.load(path)
        
        if session is not None:
            logger.info(f"恢复会话: {session.session_id}")
            return session
        
        # 创建新会话
        new_session = cls(
            session_id=str(uuid.uuid4())[:8],
            started_at=datetime.now().isoformat(),
        )
        new_session.save(path)
        logger.info(f"创建新会话: {new_session.session_id}")
        
        return new_session
    
    def start_task(self, task_id: str, title: str, steps: List[str]) -> None:
        """
        开始新任务
        
        Args:
            task_id: 任务 ID
            title: 任务标题
            steps: 实施步骤
        """
        self.current_task = task_id
        self.current_task_title = title
        self.pending_steps = steps.copy()
        self.completed_steps = []
        self.save()
        
        logger.info(f"开始任务: {task_id} - {title}")
    
    def complete_step(self, step: str, summary: Optional[str] = None) -> None:
        """
        完成一个步骤
        
        Args:
            step: 步骤描述
            summary: 完成摘要
        """
        if step in self.pending_steps:
            self.pending_steps.remove(step)
        
        completed = step
        if summary:
            completed = f"{step} - {summary}"
        
        self.completed_steps.append(completed)
        self.save()
        
        logger.info(f"步骤完成: {step}")
    
    def add_decision(self, decision: str, reason: str) -> None:
        """
        添加决策记录
        
        Args:
            decision: 决策内容
            reason: 决策原因
        """
        self.key_decisions.append({
            "decision": decision,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
        })
        self.save()
    
    def add_modified_file(self, filepath: str) -> None:
        """
        记录修改的文件
        
        Args:
            filepath: 文件路径
        """
        if filepath not in self.modified_files:
            self.modified_files.append(filepath)
            self.save()
    
    def add_error(self, error: str, context: str) -> None:
        """
        记录遇到的错误
        
        Args:
            error: 错误信息
            context: 错误上下文
        """
        self.errors_encountered.append({
            "error": error,
            "context": context,
            "timestamp": datetime.now().isoformat(),
        })
        self.save()
    
    def finish_task(self) -> None:
        """完成当前任务"""
        self.current_task = None
        self.current_task_title = None
        self.pending_steps = []
        self.save()
    
    def get_status_summary(self) -> str:
        """
        获取状态摘要
        
        Returns:
            状态摘要文本
        """
        lines = [
            f"## 会话状态",
            f"",
            f"- **会话 ID**: {self.session_id}",
            f"- **开始时间**: {self.started_at}",
            f"- **最后更新**: {self.last_updated or '未知'}",
        ]
        
        if self.current_task:
            lines.extend([
                f"",
                f"### 当前任务",
                f"- **ID**: {self.current_task}",
                f"- **标题**: {self.current_task_title or '未知'}",
            ])
            
            if self.completed_steps:
                lines.append(f"")
                lines.append(f"**已完成步骤**:")
                for step in self.completed_steps:
                    lines.append(f"- [x] {step}")
            
            if self.pending_steps:
                lines.append(f"")
                lines.append(f"**待处理步骤**:")
                for step in self.pending_steps:
                    lines.append(f"- [ ] {step}")
        
        if self.modified_files:
            lines.extend([
                f"",
                f"### 修改的文件",
            ])
            for f in self.modified_files[-10:]:  # 只显示最近 10 个
                lines.append(f"- {f}")
        
        return "\n".join(lines)
    
    def reset(self) -> None:
        """重置会话"""
        self.current_task = None
        self.current_task_title = None
        self.completed_steps = []
        self.pending_steps = []
        self.key_decisions = []
        self.modified_files = []
        self.errors_encountered = []
        self.save()


__all__ = [
    "SessionContext",
]
