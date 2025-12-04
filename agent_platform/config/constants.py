"""
agent_platform.config.constants - 运行模式常量

Phase 0 迁移：引入 AGENT_PLATFORM_LEGACY 回退机制。

注意：此文件不应被 agents/__init__.py 直接导入。
影子模式使用纯 os.environ 检查，避免循环依赖。

环境变量：
- AGENT_PLATFORM_LEGACY: 设为 "1" 启用 Legacy 模式（使用旧 agents/ 逻辑）
- AGENT_PLATFORM_MODE: 设为 "mcp" 启用 MCP 工具模式

迁移文档：docs/dev/AGENT_PLATFORM_MIGRATION_PLAN_v1.2.md
"""

import os


def is_legacy_mode() -> bool:
    """
    检查是否启用 Legacy 模式（用于 agent_platform 内部）。

    设置 AGENT_PLATFORM_LEGACY=1 可临时回退到旧 agents/ 模块逻辑。
    用于迁移期间的紧急回退。

    Returns:
        True: 使用旧 agents/ 模块
        False: 使用新 agent_platform 模块（默认）
    """
    return os.environ.get("AGENT_PLATFORM_LEGACY", "0") == "1"


def is_mcp_mode() -> bool:
    """
    检查是否运行在 MCP 工具模式。

    MCP 模式下：
    - agent_platform 作为纯工具箱运行
    - Claude 是唯一的 LLM，直接使用工具
    - 禁止任何内部 LLM 调用

    Returns:
        True: MCP 工具模式（AGENT_PLATFORM_MODE=mcp）
        False: CLI 模式（默认）
    """
    return os.environ.get("AGENT_PLATFORM_MODE", "cli").strip().lower() == "mcp"


def get_platform_mode() -> str:
    """
    获取当前平台运行模式。

    Returns:
        "mcp": MCP 工具模式
        "cli": CLI 命令行模式（默认）
    """
    return os.environ.get("AGENT_PLATFORM_MODE", "cli").strip().lower()
