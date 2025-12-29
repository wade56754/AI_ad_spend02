#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PreToolUse Hook - 工具使用前的合规检查

从 stdin 读取 JSON 输入，调用 ComplianceChecker 检查内容，
输出 approve/reject 决策到 stdout。

输入格式 (stdin JSON):
{
    "tool_name": "Write",
    "tool_input": {
        "file_path": "/path/to/file.py",
        "content": "code content..."
    }
}

输出格式 (stdout JSON):
{
    "decision": "approve",  // approve | reject
    "reason": null          // 拒绝原因
}
"""
from __future__ import annotations

import io
import json
import logging
import os
import re
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
LOG_FILE = LOG_DIR / "pre_tool_use.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ]
)
logger = logging.getLogger(__name__)


# =============================================================================
# 导入合规检查器（带回退）
# =============================================================================

try:
    # 添加 lib 目录到路径
    sys.path.insert(0, str(Path(__file__).parent))
    from lib.compliance_checker import (
        ComplianceChecker,
        Severity,
        check_code,
        is_compliant,
    )
    CHECKER_AVAILABLE = True
    logger.info("ComplianceChecker loaded successfully")
except ImportError as e:
    CHECKER_AVAILABLE = False
    logger.warning(f"ComplianceChecker not available: {e}")

    # 回退到内置检查
    class Severity:
        CRITICAL = "critical"
        WARNING = "warning"


# =============================================================================
# 内置检查规则（ComplianceChecker 不可用时的回退）
# =============================================================================

# 业务层合法角色列表 (PRD v2.2)
VALID_BUSINESS_ROLES = {
    "ceo", "project_owner", "finance",
    "pitcher", "account_manager", "admin"
}

# 技术层合法角色列表 (MASTER.md v4.6 §INV-007)
VALID_TECHNICAL_ROLES = {
    "admin", "finance", "account_manager", "media_buyer"
}

# 废弃角色 (PRD v2.2 移除)
DEPRECATED_ROLES = {"supervisor", "data_operator"}

# Phase 2 forbidden keywords
PHASE2_PATTERNS = [
    (r"auto[_-]?reject", "Phase 1 violation: auto_reject forbidden"),
    (r"auto[_-]?suspend", "Phase 1 violation: auto_suspend forbidden"),
    (r"auto[_-]?block", "Phase 1 violation: auto_block forbidden"),
    (r"auto[_-]?freeze", "Phase 1 violation: auto_freeze forbidden"),
    (r"force[_-]?stop", "Phase 1 violation: force_stop forbidden"),
    (r"forced?[_-]?approval", "Phase 1 violation: forced_approval forbidden"),
]

# Forbidden patterns
FORBIDDEN_PATTERNS = [
    (r"\.(balance|current_balance)\s*[+\-*/]?=", "Direct balance modification forbidden"),
    (r"status\s*[=!]=\s*['\"]?(draft|submitted|approved|rejected)['\"]?", "Legacy status name detected"),
]

# Bash dangerous commands
BASH_DANGEROUS_PATTERNS = [
    (r"UPDATE\s+.*balance", "SQL direct balance update forbidden"),
    (r"rm\s+-rf?\s+.*docs/2\.sot", "SoT document deletion forbidden"),
    (r"DELETE\s+FROM\s+.*sot", "SoT data deletion forbidden"),
]


# =============================================================================
# 检查函数
# =============================================================================

def builtin_check_content(content: str, filepath: str) -> list[dict]:
    """内置检查（回退方案）"""
    violations = []
    lines = content.split("\n")

    # Phase 2 检查
    for pattern, message in PHASE2_PATTERNS:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            line_num = content[:match.start()].count("\n") + 1
            violations.append({
                "severity": Severity.CRITICAL,
                "message": message,
                "line": line_num,
                "snippet": lines[line_num - 1].strip() if line_num <= len(lines) else "",
            })

    # 禁止模式检查
    for pattern, message in FORBIDDEN_PATTERNS:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            line_num = content[:match.start()].count("\n") + 1
            violations.append({
                "severity": Severity.CRITICAL,
                "message": message,
                "line": line_num,
                "snippet": lines[line_num - 1].strip() if line_num <= len(lines) else "",
            })

    return violations


def check_write_tool(tool_input: dict) -> tuple[str, str | None]:
    """
    检查 Write 工具

    Returns:
        (decision, reason)
    """
    file_path = tool_input.get("file_path", "")
    content = tool_input.get("content", "")

    if not content:
        return "approve", None

    # 只检查代码文件
    if not any(file_path.endswith(ext) for ext in [".py", ".ts", ".tsx", ".js", ".jsx"]):
        return "approve", None

    # 使用 ComplianceChecker 或内置检查
    if CHECKER_AVAILABLE:
        checker = ComplianceChecker()
        result = checker.check_content(file_path, content)
        critical_violations = checker.get_critical_violations()

        if critical_violations:
            reasons = [f"{v.file}:{v.line} - {v.message}" for v in critical_violations[:3]]
            reason = f"Critical violations ({len(critical_violations)}): " + "; ".join(reasons)
            logger.warning(f"Write rejected: {file_path} - {len(critical_violations)} critical violations")
            return "reject", reason
    else:
        violations = builtin_check_content(content, file_path)
        critical = [v for v in violations if v["severity"] == Severity.CRITICAL]

        if critical:
            reasons = [f"Line {v['line']}: {v['message']}" for v in critical[:3]]
            reason = f"Critical violations ({len(critical)}): " + "; ".join(reasons)
            logger.warning(f"Write rejected: {file_path} - {len(critical)} critical violations")
            return "reject", reason

    logger.info(f"Write approved: {file_path}")
    return "approve", None


def check_edit_tool(tool_input: dict) -> tuple[str, str | None]:
    """
    检查 Edit 工具

    Returns:
        (decision, reason)
    """
    file_path = tool_input.get("file_path", "")
    new_string = tool_input.get("new_string", "")

    if not new_string:
        return "approve", None

    # 只检查代码文件
    if not any(file_path.endswith(ext) for ext in [".py", ".ts", ".tsx", ".js", ".jsx"]):
        return "approve", None

    # 使用 ComplianceChecker 或内置检查
    if CHECKER_AVAILABLE:
        checker = ComplianceChecker()
        result = checker.check_content(file_path, new_string)
        critical_violations = checker.get_critical_violations()

        if critical_violations:
            reasons = [f"{v.message}" for v in critical_violations[:3]]
            reason = f"Critical violations in edit: " + "; ".join(reasons)
            logger.warning(f"Edit rejected: {file_path} - {len(critical_violations)} critical violations")
            return "reject", reason
    else:
        violations = builtin_check_content(new_string, file_path)
        critical = [v for v in violations if v["severity"] == Severity.CRITICAL]

        if critical:
            reasons = [f"{v['message']}" for v in critical[:3]]
            reason = f"Critical violations in edit: " + "; ".join(reasons)
            logger.warning(f"Edit rejected: {file_path} - {len(critical)} critical violations")
            return "reject", reason

    logger.info(f"Edit approved: {file_path}")
    return "approve", None


def check_bash_tool(tool_input: dict) -> tuple[str, str | None]:
    """
    检查 Bash 工具

    Returns:
        (decision, reason)
    """
    command = tool_input.get("command", "")

    if not command:
        return "approve", None

    # 检查危险命令
    for pattern, message in BASH_DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            logger.warning(f"Bash rejected: {message} - {command[:100]}")
            return "reject", message

    logger.info(f"Bash approved: {command[:50]}...")
    return "approve", None


# =============================================================================
# 主函数
# =============================================================================

def output_decision(decision: str, reason: str | None = None) -> None:
    """输出决策到 stdout"""
    result = {
        "decision": decision,
        "reason": reason,
    }
    print(json.dumps(result, ensure_ascii=False))


def main() -> int:
    """主函数"""
    try:
        # 从 stdin 读取输入
        input_data = sys.stdin.read()

        if not input_data.strip():
            # 空输入，尝试从环境变量读取（兼容旧模式）
            tool_name = os.environ.get("TOOL_NAME", "")
            tool_params_json = os.environ.get("TOOL_PARAMETERS_JSON", "{}")

            if tool_name:
                try:
                    tool_input = json.loads(tool_params_json)
                except json.JSONDecodeError:
                    tool_input = {}
            else:
                output_decision("approve")
                return 0
        else:
            # 解析 stdin JSON
            try:
                data = json.loads(input_data)
                tool_name = data.get("tool_name", "")
                tool_input = data.get("tool_input", {})
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON input: {e}")
                output_decision("approve")
                return 0

        logger.info(f"Checking tool: {tool_name}")

        # 根据工具类型分发检查
        if tool_name in ["Write", "create_file"]:
            decision, reason = check_write_tool(tool_input)
        elif tool_name in ["Edit", "str_replace", "str_replace_editor"]:
            decision, reason = check_edit_tool(tool_input)
        elif tool_name in ["Bash", "bash_tool", "execute_command"]:
            decision, reason = check_bash_tool(tool_input)
        else:
            # 其他工具默认允许
            decision, reason = "approve", None

        output_decision(decision, reason)
        return 0 if decision == "approve" else 1

    except Exception as e:
        logger.error(f"Hook error: {e}", exc_info=True)
        # 出错时不阻止工具执行
        output_decision("approve")
        return 0


if __name__ == "__main__":
    sys.exit(main())
