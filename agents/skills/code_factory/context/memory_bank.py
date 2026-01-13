"""
Memory Bank - 防止 AI 失忆

提供持久化的项目上下文，确保 AI 在每次对话中都能获取必要信息。

三层上下文:
1. Project Context (永久): .claude/rules.md, project-brief.md
2. Session Context (会话级): session/context.json
3. Task Context (任务级): progress.md, current-task.md

版本: v7.0
"""

import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class MemoryBank:
    """
    Memory Bank - 防止 AI 失忆
    
    管理项目级持久化上下文，确保 AI 了解:
    - 项目概况
    - 当前进度
    - 已做决策
    - 当前任务
    """
    
    DEFAULT_MEMORY_DIR = Path("memory-bank")
    
    # AI 每次对话必读的文件 (按重要性排序)
    REQUIRED_FILES = [
        "project-brief.md",   # 项目简介
        "progress.md",        # 当前进度
        "current-task.md",    # 当前任务
    ]
    
    # 可选的上下文文件
    OPTIONAL_FILES = [
        "architecture.md",    # 架构说明
        "decisions.md",       # 决策日志
    ]
    
    def __init__(self, memory_dir: Optional[Path] = None):
        """
        初始化 Memory Bank
        
        Args:
            memory_dir: 存储目录，默认为 memory-bank/
        """
        self.memory_dir = memory_dir or self.DEFAULT_MEMORY_DIR
        self._ensure_structure()
    
    def _ensure_structure(self) -> None:
        """确保目录结构存在"""
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        (self.memory_dir / "session").mkdir(exist_ok=True)
        
        # 创建必要文件的模板
        self._create_templates()
    
    def _create_templates(self) -> None:
        """创建文件模板"""
        templates = {
            "project-brief.md": self._project_brief_template(),
            "progress.md": self._progress_template(),
            "current-task.md": self._current_task_template(),
            "decisions.md": self._decisions_template(),
            "architecture.md": self._architecture_template(),
        }
        
        for filename, content in templates.items():
            filepath = self.memory_dir / filename
            if not filepath.exists():
                filepath.write_text(content, encoding="utf-8")
                logger.info(f"创建模板文件: {filepath}")
    
    def get_context_prompt(self) -> str:
        """
        生成上下文提示词
        
        返回 AI 每次对话必读的上下文内容
        """
        context_parts = []
        
        # 添加必读文件
        for filename in self.REQUIRED_FILES:
            filepath = self.memory_dir / filename
            if filepath.exists():
                content = filepath.read_text(encoding="utf-8")
                if content.strip():
                    context_parts.append(f"## {filename}\n\n{content}")
        
        if not context_parts:
            return "# 项目上下文\n\n暂无上下文信息。"
        
        return "# 项目上下文 (AI 必读)\n\n" + "\n\n---\n\n".join(context_parts)
    
    def update_progress(
        self,
        task_id: str,
        status: str,
        summary: str,
    ) -> None:
        """
        更新任务进度
        
        Args:
            task_id: 任务 ID
            status: 状态 (completed, in_progress, blocked)
            summary: 进度摘要
        """
        progress_file = self.memory_dir / "progress.md"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        entry = f"\n### [{timestamp}] {task_id}\n- **状态**: {status}\n- **摘要**: {summary}\n"
        
        with open(progress_file, "a", encoding="utf-8") as f:
            f.write(entry)
        
        logger.info(f"进度已更新: {task_id} -> {status}")
    
    def log_decision(
        self,
        decision: str,
        reason: str,
        alternatives: Optional[List[str]] = None,
    ) -> None:
        """
        记录决策
        
        Args:
            decision: 决策内容
            reason: 决策原因
            alternatives: 其他考虑过的方案
        """
        decisions_file = self.memory_dir / "decisions.md"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        entry = f"\n## [{timestamp}]\n\n"
        entry += f"**决策**: {decision}\n\n"
        entry += f"**原因**: {reason}\n"
        
        if alternatives:
            entry += "\n**其他方案**:\n"
            for alt in alternatives:
                entry += f"- {alt}\n"
        
        with open(decisions_file, "a", encoding="utf-8") as f:
            f.write(entry)
        
        logger.info(f"决策已记录: {decision}")
    
    def set_current_task(
        self,
        task_id: str,
        title: str,
        description: str,
        steps: Optional[List[str]] = None,
    ) -> None:
        """
        设置当前任务
        
        Args:
            task_id: 任务 ID
            title: 任务标题
            description: 任务描述
            steps: 实施步骤
        """
        current_task_file = self.memory_dir / "current-task.md"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        content = f"""# 当前任务

> 更新于 {timestamp}

## {task_id}: {title}

{description}
"""
        
        if steps:
            content += "\n## 实施步骤\n\n"
            for i, step in enumerate(steps, 1):
                content += f"{i}. [ ] {step}\n"
        
        current_task_file.write_text(content, encoding="utf-8")
        logger.info(f"当前任务已设置: {task_id}")
    
    def clear_current_task(self) -> None:
        """清除当前任务"""
        current_task_file = self.memory_dir / "current-task.md"
        current_task_file.write_text(self._current_task_template(), encoding="utf-8")
    
    def get_progress_summary(self) -> str:
        """获取进度摘要"""
        progress_file = self.memory_dir / "progress.md"
        if progress_file.exists():
            return progress_file.read_text(encoding="utf-8")
        return ""
    
    def get_decisions(self) -> str:
        """获取决策日志"""
        decisions_file = self.memory_dir / "decisions.md"
        if decisions_file.exists():
            return decisions_file.read_text(encoding="utf-8")
        return ""
    
    # =========================================================================
    # 模板
    # =========================================================================
    
    def _project_brief_template(self) -> str:
        return """# 项目简介

> AI 每次对话必读此文件

## 项目名称

AI 广告代投管理系统

## 技术栈

- 后端: FastAPI + SQLAlchemy 2.x + Pydantic v2
- 前端: Next.js 16 + TanStack Query v5 + shadcn/ui
- 数据库: PostgreSQL (Supabase)
- 认证: Supabase Auth

## 核心业务

- 广告账户管理 (AdAccount)
- 日报审核流程 (DailyReport) - 8 状态机
- 充值与对账 (Topup/Reconciliation)
- 财务账本 (Ledger)

## SoT 文档

- MASTER.md v4.8 - 架构宪法
- STATE_MACHINE.md v2.8 - 状态机定义
- DATA_SCHEMA.md v5.7 - 数据模型

## 关键约束

- 角色白名单: admin, finance, account_manager, media_buyer
- 日报状态: 8 状态机，禁止使用 draft/pending/approved
- 余额修改: 必须通过 ledger，禁止直接修改 balance
"""
    
    def _progress_template(self) -> str:
        return """# 任务进度

> 记录每个任务的完成情况

## 格式说明

每条记录包含:
- 时间戳
- 任务 ID
- 状态 (completed/in_progress/blocked)
- 摘要

---

"""
    
    def _current_task_template(self) -> str:
        return """# 当前任务

> 当前没有活动任务

使用 `memory_bank.set_current_task()` 设置当前任务。
"""
    
    def _decisions_template(self) -> str:
        return """# 决策日志

> 记录重要的技术和业务决策

## 格式说明

每条记录包含:
- 时间戳
- 决策内容
- 决策原因
- 其他考虑的方案 (可选)

---

"""
    
    def _architecture_template(self) -> str:
        return """# 系统架构

## 目录结构

```
AI_ad_spend02/
├── backend/
│   ├── routers/        # API 路由
│   ├── services/       # 业务逻辑
│   ├── models/         # SQLAlchemy 模型
│   └── schemas/        # Pydantic 模式
├── frontend/
│   └── src/
│       ├── app/        # Next.js App Router
│       ├── components/ # 通用组件
│       └── features/   # 业务模块
└── docs/
    └── sot/            # SoT 真相源文档
```

## 关键模块

- 日报审核: backend/services/daily_report_service.py
- 充值管理: backend/services/topup_service.py
- 财务账本: backend/services/ledger_service.py
- CEO 看板: backend/services/dashboard/
"""


# =============================================================================
# 单例访问
# =============================================================================

_memory_bank: Optional[MemoryBank] = None


def get_memory_bank() -> MemoryBank:
    """获取 Memory Bank 单例"""
    global _memory_bank
    if _memory_bank is None:
        _memory_bank = MemoryBank()
    return _memory_bank


__all__ = [
    "MemoryBank",
    "get_memory_bank",
]
