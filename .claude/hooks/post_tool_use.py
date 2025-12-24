#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostToolUse Hook - 工具使用后的处理

记录工具使用、关联模块、更新任务进度。

输入格式 (stdin JSON):
{
    "tool_name": "Write",
    "tool_input": {
        "file_path": "/path/to/file.py",
        "content": "..."
    },
    "success": true
}

输出: 无（仅记录日志和更新进度）
"""

import io
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Windows UTF-8 编码设置
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 设置日志
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "post_tool_use.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ]
)
logger = logging.getLogger(__name__)


# =============================================================================
# 导入进度追踪器（带回退）
# =============================================================================

try:
    sys.path.insert(0, str(Path(__file__).parent))
    from lib.progress_tracker import (
        ProgressTracker,
        TaskStatus,
        get_tracker,
    )
    TRACKER_AVAILABLE = True
    logger.info("ProgressTracker loaded successfully")
except ImportError as e:
    TRACKER_AVAILABLE = False
    logger.warning(f"ProgressTracker not available: {e}")


# =============================================================================
# 模块-路径关键词映射
# =============================================================================

MODULE_PATH_PATTERNS: dict[str, list[str]] = {
    # A 组: 数据看板
    "A1": ["dashboard", "驾驶舱", "kpi", "stat_card"],
    "A2": ["fund", "资金", "balance", "ledger"],
    "A3": ["pnl", "盈亏", "profit", "loss"],

    # B 组: 日常操作
    "B1": ["daily_report", "日报", "report_submit", "daily-report"],
    "B2": ["review", "审核", "trend_", "approval"],
    "B3": ["weekly", "周报", "brief"],

    # C 组: 管理功能
    "C1": ["topup", "充值", "recharge"],
    "C2": ["pitcher", "投手", "pitcher_mgmt"],
    "C3": ["spend", "消耗", "spend_detail"],

    # D 组: 项目管理
    "D1": ["project", "项目", "project_mgmt"],

    # E 组: 结算
    "E1": ["settlement", "结算", "monthly"],
}

# 文件操作记录（会话内）
SESSION_DATA_FILE = Path(__file__).parent.parent / "data" / "session_data.json"


# =============================================================================
# 辅助函数
# =============================================================================

def load_session_data() -> dict:
    """加载会话数据"""
    if SESSION_DATA_FILE.exists():
        try:
            with open(SESSION_DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "session_start": datetime.now().isoformat(),
        "files_modified": [],
        "tools_used": {},
        "modules_touched": set(),
    }


def save_session_data(data: dict) -> None:
    """保存会话数据"""
    SESSION_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    # 转换 set 为 list 以便 JSON 序列化
    save_data = data.copy()
    if isinstance(save_data.get("modules_touched"), set):
        save_data["modules_touched"] = list(save_data["modules_touched"])

    try:
        with open(SESSION_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to save session data: {e}")


def detect_module(file_path: str) -> str | None:
    """根据文件路径检测关联模块"""
    path_lower = file_path.lower()

    for module_id, patterns in MODULE_PATH_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in path_lower:
                return module_id

    return None


def get_related_tasks(module_id: str) -> list[str]:
    """获取模块下进行中的任务"""
    if not TRACKER_AVAILABLE:
        return []

    tracker = get_tracker()
    tasks = tracker.get_module_tasks(module_id)

    # 返回进行中的任务
    return [t.id for t in tasks if t.status == TaskStatus.IN_PROGRESS]


def update_task_progress(task_id: str, increment: int = 10) -> bool:
    """更新任务进度"""
    if not TRACKER_AVAILABLE:
        return False

    tracker = get_tracker()
    task = tracker.get_task(task_id)

    if not task:
        return False

    new_progress = min(100, task.progress + increment)
    tracker.update_task(task_id, progress=new_progress)
    tracker.save()

    logger.info(f"Updated task {task_id}: {task.progress}% -> {new_progress}%")
    return True


# =============================================================================
# 格式化函数（保留原有功能）
# =============================================================================

def format_python_file(file_path: str) -> bool:
    """使用 black 格式化 Python 文件"""
    if not shutil.which("black"):
        return False

    try:
        result = subprocess.run(
            ["black", "--quiet", file_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            logger.info(f"Formatted with black: {file_path}")
            return True
    except Exception as e:
        logger.warning(f"Black format failed: {e}")

    return False


def format_typescript_file(file_path: str) -> bool:
    """使用 prettier 格式化 TypeScript 文件"""
    has_prettier = shutil.which("prettier") or shutil.which("npx")
    if not has_prettier:
        return False

    try:
        cmd = ["prettier", "--write", file_path]
        if not shutil.which("prettier"):
            cmd = ["npx", "prettier", "--write", file_path]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.path.dirname(os.path.abspath(file_path)) or ".",
        )
        if result.returncode == 0:
            logger.info(f"Formatted with prettier: {file_path}")
            return True
    except Exception as e:
        logger.warning(f"Prettier format failed: {e}")

    return False


# =============================================================================
# 工具处理函数
# =============================================================================

def handle_write_tool(tool_input: dict, success: bool) -> None:
    """处理 Write 工具"""
    file_path = tool_input.get("file_path", "")

    if not success or not file_path:
        return

    logger.info(f"File created: {file_path}")

    # 记录到会话数据
    session_data = load_session_data()
    if file_path not in session_data["files_modified"]:
        session_data["files_modified"].append(file_path)

    # 检测关联模块
    module_id = detect_module(file_path)
    if module_id:
        logger.info(f"Detected module: {module_id}")

        # 记录模块
        modules = set(session_data.get("modules_touched", []))
        modules.add(module_id)
        session_data["modules_touched"] = modules

        # 更新进行中的任务进度
        related_tasks = get_related_tasks(module_id)
        for task_id in related_tasks[:1]:  # 只更新第一个进行中的任务
            update_task_progress(task_id, increment=10)

    save_session_data(session_data)

    # 格式化代码
    if os.path.exists(file_path):
        if file_path.endswith(".py"):
            format_python_file(file_path)
        elif file_path.endswith((".ts", ".tsx", ".js", ".jsx")):
            format_typescript_file(file_path)


def handle_edit_tool(tool_input: dict, success: bool) -> None:
    """处理 Edit 工具"""
    file_path = tool_input.get("file_path", "")

    if not success or not file_path:
        return

    logger.info(f"File edited: {file_path}")

    # 记录到会话数据
    session_data = load_session_data()
    if file_path not in session_data["files_modified"]:
        session_data["files_modified"].append(file_path)

    # 检测关联模块
    module_id = detect_module(file_path)
    if module_id:
        logger.info(f"Detected module: {module_id}")

        modules = set(session_data.get("modules_touched", []))
        modules.add(module_id)
        session_data["modules_touched"] = modules

        # 编辑操作增加较少进度
        related_tasks = get_related_tasks(module_id)
        for task_id in related_tasks[:1]:
            update_task_progress(task_id, increment=5)

    save_session_data(session_data)

    # 格式化代码
    if os.path.exists(file_path):
        if file_path.endswith(".py"):
            format_python_file(file_path)
        elif file_path.endswith((".ts", ".tsx", ".js", ".jsx")):
            format_typescript_file(file_path)


def handle_bash_tool(tool_input: dict, success: bool) -> None:
    """处理 Bash 工具"""
    command = tool_input.get("command", "")

    if success:
        logger.info(f"Bash executed: {command[:100]}...")

        # 更新工具使用统计
        session_data = load_session_data()
        tools_used = session_data.get("tools_used", {})
        tools_used["Bash"] = tools_used.get("Bash", 0) + 1
        session_data["tools_used"] = tools_used
        save_session_data(session_data)


# =============================================================================
# 主函数
# =============================================================================

def main() -> int:
    """主函数"""
    try:
        # 从 stdin 读取输入
        input_data = sys.stdin.read()

        if not input_data.strip():
            # 尝试从环境变量读取（兼容旧模式）
            tool_name = os.environ.get("TOOL_NAME", "")
            tool_params_json = os.environ.get("TOOL_PARAMETERS_JSON", "{}")

            if tool_name:
                try:
                    tool_input = json.loads(tool_params_json)
                except json.JSONDecodeError:
                    tool_input = {}
                success = True  # 旧模式假设成功
            else:
                return 0
        else:
            # 解析 stdin JSON
            try:
                data = json.loads(input_data)
                tool_name = data.get("tool_name", "")
                tool_input = data.get("tool_input", {})
                success = data.get("success", True)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON input: {e}")
                return 0

        logger.info(f"PostToolUse: {tool_name} (success={success})")

        # 更新工具使用统计
        session_data = load_session_data()
        tools_used = session_data.get("tools_used", {})
        tools_used[tool_name] = tools_used.get(tool_name, 0) + 1
        session_data["tools_used"] = tools_used
        save_session_data(session_data)

        # 根据工具类型分发处理
        if tool_name in ["Write", "create_file"]:
            handle_write_tool(tool_input, success)
        elif tool_name in ["Edit", "str_replace", "str_replace_editor"]:
            handle_edit_tool(tool_input, success)
        elif tool_name in ["Bash", "bash_tool", "execute_command"]:
            handle_bash_tool(tool_input, success)

        return 0

    except Exception as e:
        logger.error(f"Hook error: {e}", exc_info=True)
        return 0


if __name__ == "__main__":
    sys.exit(main())
