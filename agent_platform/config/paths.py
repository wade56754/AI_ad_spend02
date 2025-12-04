"""
agent_platform.config.paths - 项目路径常量

Phase 1 迁移：从 agents/agents_config.py 迁移路径常量。

路径推断优先级：
1. AGENT_PLATFORM_REPO_ROOT 环境变量（最高优先级）
2. 从文件位置推断：paths.py -> config/ -> agent_platform/ -> 项目根
3. 当前工作目录（fallback）

迁移文档：docs/dev/AGENT_PLATFORM_MIGRATION_PLAN_v1.2.md
"""

import os
import warnings
from pathlib import Path


def _validate_base_path(path: Path) -> bool:
    """
    验证路径是否为有效的项目根目录。

    检查 backend/ 和 docs/ 子目录是否存在。

    Args:
        path: 待验证的路径

    Returns:
        True: 是有效的项目根目录
        False: 不是有效的项目根目录
    """
    required_dirs = ["backend", "docs"]
    return all((path / d).is_dir() for d in required_dirs)


def _get_base_path() -> Path:
    """
    推断项目根路径（带 fallback 和验证）。

    优先级：
    1. AGENT_PLATFORM_REPO_ROOT 环境变量
    2. 从文件位置推断：config/ -> agent_platform/ -> 项目根
    3. 当前工作目录（fallback）

    验证：检查 backend/, docs/ 是否存在。

    Returns:
        项目根目录的 Path 对象
    """
    # 优先级 1: 环境变量
    env_root = os.environ.get("AGENT_PLATFORM_REPO_ROOT")
    if env_root:
        path = Path(env_root).resolve()
        if _validate_base_path(path):
            return path

    # 优先级 2: 从文件位置推断
    # paths.py -> config/ -> agent_platform/ -> 项目根
    inferred = Path(__file__).resolve().parent.parent.parent
    if _validate_base_path(inferred):
        return inferred

    # 优先级 3: 当前工作目录
    cwd = Path.cwd()
    if _validate_base_path(cwd):
        return cwd

    # 无法找到有效路径，使用推断值并警告
    warnings.warn(
        f"无法验证 BASE_PATH，使用推断值: {inferred}。"
        f"如有问题，请设置 AGENT_PLATFORM_REPO_ROOT 环境变量。",
        RuntimeWarning,
        stacklevel=2,
    )
    return inferred


# 项目根路径
BASE_PATH = _get_base_path()
PROJECT_ROOT = BASE_PATH  # 别名，兼容 agents/agents_config.py

# 子目录路径
BACKEND_DIR = BASE_PATH / "backend"
FRONTEND_DIR = BASE_PATH / "frontend"
DOCS_DIR = BASE_PATH / "docs"
TESTS_DIR = BASE_PATH / "tests"


def read_optional(path) -> str:
    """
    读取可选文件内容。

    如果文件不存在或读取失败，返回空字符串。

    Args:
        path: 文件路径（Path 对象或字符串）

    Returns:
        文件内容或空字符串
    """
    if path is None:
        return ""
    try:
        if isinstance(path, str):
            path = Path(path)
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""
    except Exception:
        return ""
