"""
Agent 工具框架 v5.0

提供 AI Agent 可调用的工具集:
- run_tests: 运行测试
- lint_code: 代码检查
- search_docs: 搜索文档
- git_commit: Git 操作
- run_migration: 数据库迁移

基准文档: MASTER.md v4.6
版本: v5.0
"""

from .base import (
    Tool,
    ToolResult,
    ToolRegistry,
    tool,
)
from .builtin import (
    RunTestsTool,
    LintCodeTool,
    SearchDocsTool,
    GitCommitTool,
    RunMigrationTool,
    FileReadTool,
    FileWriteTool,
)

__all__ = [
    # 基类
    "Tool",
    "ToolResult",
    "ToolRegistry",
    "tool",
    
    # 内置工具
    "RunTestsTool",
    "LintCodeTool",
    "SearchDocsTool",
    "GitCommitTool",
    "RunMigrationTool",
    "FileReadTool",
    "FileWriteTool",
]






