#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stop Hook - 会话结束时的处理

统计会话修改、生成摘要、触发日报生成。

输入格式 (stdin JSON):
{
    "session_id": "xxx",
    "start_time": "2025-01-01T10:00:00"
}

输出: 会话摘要（stdout）
"""

import io
import json
import logging
import os
import platform
import subprocess
import sys
from datetime import datetime, date
from pathlib import Path
from typing import Any

# Windows UTF-8 编码设置
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 设置日志
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "stop.log"

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
        get_tracker,
        generate_progress_report,
    )
    from lib.risk_detector import (
        RiskDetector,
        get_detector,
        generate_risk_report,
    )
    MODULES_AVAILABLE = True
    logger.info("Modules loaded successfully")
except ImportError as e:
    MODULES_AVAILABLE = False
    logger.warning(f"Modules not available: {e}")


# =============================================================================
# 数据文件路径
# =============================================================================

DATA_DIR = Path(__file__).parent.parent / "data"
SESSION_DATA_FILE = DATA_DIR / "session_data.json"
DAILY_REPORT_FILE = DATA_DIR / "daily_reports.json"
SESSION_HISTORY_FILE = DATA_DIR / "session_history.json"


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
        "modules_touched": [],
    }


def save_session_history(session_summary: dict) -> None:
    """保存会话历史"""
    history = []
    if SESSION_HISTORY_FILE.exists():
        try:
            with open(SESSION_HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            pass

    history.append(session_summary)

    # 只保留最近 100 条
    history = history[-100:]

    try:
        with open(SESSION_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to save session history: {e}")


def load_daily_reports() -> dict:
    """加载日报数据"""
    if DAILY_REPORT_FILE.exists():
        try:
            with open(DAILY_REPORT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"reports": {}}


def save_daily_report(report: dict) -> None:
    """保存日报"""
    reports = load_daily_reports()
    today = date.today().isoformat()
    reports["reports"][today] = report
    reports["last_updated"] = datetime.now().isoformat()

    try:
        with open(DAILY_REPORT_FILE, "w", encoding="utf-8") as f:
            json.dump(reports, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to save daily report: {e}")


def is_first_session_today() -> bool:
    """检查是否是今天的第一次会话"""
    reports = load_daily_reports()
    today = date.today().isoformat()
    return today not in reports.get("reports", {})


def calculate_session_duration(start_time: str) -> str:
    """计算会话持续时间"""
    try:
        start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        now = datetime.now()
        if start.tzinfo:
            now = now.astimezone()
        duration = now - start.replace(tzinfo=None)
        minutes = int(duration.total_seconds() / 60)
        if minutes < 60:
            return f"{minutes}m"
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}h {mins}m"
    except Exception:
        return "unknown"


def generate_session_summary(session_data: dict, input_data: dict) -> dict:
    """生成会话摘要"""
    start_time = input_data.get("start_time") or session_data.get("session_start", "")
    session_id = input_data.get("session_id", "unknown")

    files_modified = session_data.get("files_modified", [])
    tools_used = session_data.get("tools_used", {})
    modules_touched = session_data.get("modules_touched", [])

    # 按文件类型统计
    file_types: dict[str, int] = {}
    for f in files_modified:
        ext = Path(f).suffix or "other"
        file_types[ext] = file_types.get(ext, 0) + 1

    summary = {
        "session_id": session_id,
        "start_time": start_time,
        "end_time": datetime.now().isoformat(),
        "duration": calculate_session_duration(start_time),
        "files_modified_count": len(files_modified),
        "files_modified": files_modified[:20],  # 限制数量
        "file_types": file_types,
        "tools_used": tools_used,
        "total_tool_calls": sum(tools_used.values()),
        "modules_touched": list(modules_touched) if isinstance(modules_touched, (list, set)) else [],
    }

    # 添加进度信息
    if MODULES_AVAILABLE:
        try:
            tracker = get_tracker()
            summary["overall_progress"] = tracker.get_overall_progress()
            summary["completed_tasks"] = len(tracker.get_tasks_by_status("completed"))
            summary["in_progress_tasks"] = len(tracker.get_tasks_by_status("in_progress"))
        except Exception as e:
            logger.warning(f"Failed to get progress info: {e}")

    return summary


def generate_daily_report(session_summary: dict) -> dict:
    """生成日报"""
    today = date.today().isoformat()

    report = {
        "date": today,
        "generated_at": datetime.now().isoformat(),
        "sessions": [session_summary],
        "total_files_modified": session_summary.get("files_modified_count", 0),
        "total_tool_calls": session_summary.get("total_tool_calls", 0),
        "modules_touched": session_summary.get("modules_touched", []),
    }

    # 合并已有的日报数据
    existing_reports = load_daily_reports()
    if today in existing_reports.get("reports", {}):
        existing = existing_reports["reports"][today]
        report["sessions"] = existing.get("sessions", []) + [session_summary]
        report["total_files_modified"] = (
            existing.get("total_files_modified", 0) +
            session_summary.get("files_modified_count", 0)
        )
        report["total_tool_calls"] = (
            existing.get("total_tool_calls", 0) +
            session_summary.get("total_tool_calls", 0)
        )

        # 合并模块
        existing_modules = set(existing.get("modules_touched", []))
        new_modules = set(session_summary.get("modules_touched", []))
        report["modules_touched"] = list(existing_modules | new_modules)

    # 添加进度快照
    if MODULES_AVAILABLE:
        try:
            tracker = get_tracker()
            report["progress_snapshot"] = {
                "overall": tracker.get_overall_progress(),
                "modules": {
                    mid: m.progress
                    for mid, m in tracker.modules.items()
                }
            }
        except Exception:
            pass

    return report


def print_session_summary(summary: dict) -> None:
    """打印会话摘要"""
    print("=" * 60)
    print("  Session Summary")
    print("=" * 60)
    print()
    print(f"  Session ID: {summary.get('session_id', 'unknown')}")
    print(f"  Duration: {summary.get('duration', 'unknown')}")
    print(f"  Files Modified: {summary.get('files_modified_count', 0)}")
    print(f"  Tool Calls: {summary.get('total_tool_calls', 0)}")

    if summary.get("modules_touched"):
        print(f"  Modules Touched: {', '.join(summary['modules_touched'])}")

    if summary.get("overall_progress") is not None:
        print(f"  Overall Progress: {summary['overall_progress']}%")

    # 文件类型统计
    if summary.get("file_types"):
        print("\n  Files by Type:")
        for ext, count in sorted(summary["file_types"].items()):
            print(f"    {ext}: {count}")

    # 工具使用统计
    if summary.get("tools_used"):
        print("\n  Tools Used:")
        for tool, count in sorted(summary["tools_used"].items(), key=lambda x: -x[1]):
            print(f"    {tool}: {count}")

    print()
    print("=" * 60)


def send_notification(title: str, message: str) -> bool:
    """发送桌面通知"""
    system = platform.system()

    try:
        if system == "Windows":
            ps_script = f"""
$null = [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]
$null = [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime]
$APP_ID = '{{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}}\\WindowsPowerShell\\v1.0\\powershell.exe'
$template = @"
<toast><visual><binding template="ToastText02">
<text id="1">{title}</text><text id="2">{message}</text>
</binding></visual></toast>
"@
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)
$toast = New-Object Windows.UI.Notifications.ToastNotification $xml
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($APP_ID).Show($toast)
"""
            subprocess.run(["powershell", "-Command", ps_script], capture_output=True, timeout=5)
            return True

        elif system == "Darwin":
            subprocess.run(
                ["osascript", "-e", f'display notification "{message}" with title "{title}"'],
                capture_output=True, timeout=5
            )
            return True

        elif system == "Linux":
            subprocess.run(["notify-send", title, message], capture_output=True, timeout=5)
            return True

    except Exception as e:
        logger.warning(f"Notification failed: {e}")

    return False


def clear_session_data() -> None:
    """清除会话数据"""
    if SESSION_DATA_FILE.exists():
        try:
            SESSION_DATA_FILE.unlink()
        except Exception as e:
            logger.warning(f"Failed to clear session data: {e}")


# =============================================================================
# 主函数
# =============================================================================

def main() -> int:
    """主函数"""
    try:
        # 从 stdin 读取输入
        input_data = {}
        stdin_content = sys.stdin.read()

        if stdin_content.strip():
            try:
                input_data = json.loads(stdin_content)
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON input: {e}")

        logger.info("Stop hook triggered")

        # 加载会话数据
        session_data = load_session_data()

        # 生成会话摘要
        summary = generate_session_summary(session_data, input_data)

        # 保存会话历史
        save_session_history(summary)
        logger.info(f"Session summary saved: {summary.get('files_modified_count', 0)} files, {summary.get('total_tool_calls', 0)} tool calls")

        # 生成日报（如果是今天首次或有新内容）
        if summary.get("files_modified_count", 0) > 0 or summary.get("total_tool_calls", 0) > 0:
            daily_report = generate_daily_report(summary)
            save_daily_report(daily_report)
            logger.info(f"Daily report updated: {daily_report.get('date')}")

        # 打印摘要
        print_session_summary(summary)

        # 发送通知
        notification_msg = f"Modified {summary.get('files_modified_count', 0)} files, {summary.get('total_tool_calls', 0)} tool calls"
        send_notification("Claude Code Session Ended", notification_msg)

        # 清除临时会话数据
        clear_session_data()

        print("Session data saved. Goodbye!")
        print()

        return 0

    except Exception as e:
        logger.error(f"Stop hook error: {e}", exc_info=True)
        print(f"Stop hook error: {e}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
