"""
Agent Platform Tools Module

提供通用工具函数和类型定义。

公开 API:
- AgentResponse: Agent 响应类型
- SkillResult: Skill 响应类型
- read_files: 批量读取文件
- write_files: 批量写入文件
- validate_task_and_files: 参数校验
"""

from .types import (
    AgentResponse,
    AgentResponseData,
    SkillResult,
    SotViolationDict,
    ReviewResult,
    ChangesDict,
    NotesType,
    MetaType,
)
from .fs_tool import read_files, write_files, WritePreview
from .validation import validate_task_and_files

__all__ = [
    # Types
    "AgentResponse",
    "AgentResponseData",
    "SkillResult",
    "SotViolationDict",
    "ReviewResult",
    "ChangesDict",
    "NotesType",
    "MetaType",
    # FS Tools
    "read_files",
    "write_files",
    "WritePreview",
    # Validation
    "validate_task_and_files",
]
