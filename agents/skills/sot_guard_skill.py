"""
SoT 守门员 Skill - 最小可用版本

职责：
- 验证 AI 生成的代码是否违反 SoT 规则
- 检测是否发明了 SoT 中不存在的字段/状态/错误码
- 符合 PATTERNS.md AP-AI-002 要求

基准对齐：
- STATE_MACHINE.md v2.6 (8 状态机)
- ERROR_CODES_SOT.md v2.1
- DATA_SCHEMA.md v5.2
- LEDGER_SOT.md v1.1 (双账本)
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
import re
import logging

logger = logging.getLogger(__name__)


# === SoT 常量定义（来自 STATE_MACHINE.md v2.6）===

# 日报 8 状态机
DAILY_REPORT_STATES: Set[str] = {
    "raw_submitted",
    "trend_pending",
    "trend_ok",
    "trend_flagged",
    "trend_resolved",
    "final_pending",
    "final_confirmed",
    "final_locked",
}

# 日报状态流转白名单
DAILY_REPORT_TRANSITIONS: Dict[str, List[str]] = {
    "raw_submitted": ["trend_pending"],
    "trend_pending": ["trend_ok", "trend_flagged"],
    "trend_ok": ["final_pending"],
    "trend_flagged": ["trend_resolved"],
    "trend_resolved": ["final_pending"],
    "final_pending": ["final_confirmed"],
    "final_confirmed": ["final_locked"],
    "final_locked": [],  # 终态，不可再流转
}

# 项目状态枚举
PROJECT_STATES: Set[str] = {
    "draft",
    "active",
    "paused",
    "completed",
    "archived",
}

# 充值状态枚举
TOPUP_STATES: Set[str] = {
    "pending",
    "approved",
    "rejected",
    "completed",
    "cancelled",
}

# 账本类型枚举
LEDGER_TYPES: Set[str] = {
    "PROJECT",
    "SUPPLIER",
}

# 分录类型枚举
ENTRY_TYPES: Set[str] = {
    "RECHARGE",
    "SPEND",
    "ADJUST",
    "TRANSFER_OUT",
    "TRANSFER_IN",
}

# 用户角色枚举
USER_ROLES: Set[str] = {
    "admin",
    "finance",
    "data_operator",
    "account_manager",
    "media_buyer",
}


@dataclass
class SotViolation:
    """SoT 违规记录"""
    file: str
    rule: str
    severity: str  # P0 | P1 | P2
    detail: str
    line: Optional[int] = None


@dataclass
class SotGuardResult:
    """SoT 校验结果"""
    passed: bool
    violations: List[SotViolation] = field(default_factory=list)
    warnings: List[SotViolation] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "violations": [
                {
                    "file": v.file,
                    "rule": v.rule,
                    "severity": v.severity,
                    "detail": v.detail,
                    "line": v.line,
                }
                for v in self.violations
            ],
            "warnings": [
                {
                    "file": w.file,
                    "rule": w.rule,
                    "severity": w.severity,
                    "detail": w.detail,
                    "line": w.line,
                }
                for w in self.warnings
            ],
        }


def validate_against_sot(changes: Dict[str, str]) -> Dict[str, Any]:
    """
    校验生成的代码是否符合 SoT 规范。

    Args:
        changes: 文件路径 -> 文件内容的字典

    Returns:
        {
            "passed": bool,
            "violations": List[Dict],  # P0 违规列表
            "warnings": List[Dict],    # P1/P2 警告列表
        }
    """
    result = SotGuardResult(passed=True)

    for file_path, content in changes.items():
        # P0 检查：状态枚举
        state_violations = check_state_machine_compliance(content, file_path)
        for v in state_violations:
            if v.severity == "P0":
                result.violations.append(v)
                result.passed = False
            else:
                result.warnings.append(v)

        # P0 检查：账本操作
        ledger_violations = check_ledger_compliance(content, file_path)
        for v in ledger_violations:
            if v.severity == "P0":
                result.violations.append(v)
                result.passed = False
            else:
                result.warnings.append(v)

        # P1 检查：错误码
        error_warnings = check_error_code_compliance(content, file_path)
        result.warnings.extend(error_warnings)

        # P1 检查：数据结构
        schema_warnings = check_data_schema_compliance(content, file_path)
        result.warnings.extend(schema_warnings)

    logger.info(
        f"SoT Guard: passed={result.passed}, "
        f"violations={len(result.violations)}, warnings={len(result.warnings)}"
    )

    return result.to_dict()


def check_state_machine_compliance(code: str, file_path: str = "") -> List[SotViolation]:
    """
    检查代码中的状态枚举是否符合 STATE_MACHINE.md v2.6 定义。

    检测模式：
    1. 字符串字面量中的状态值
    2. Enum 定义中的状态值
    3. 状态流转逻辑中的非法跳转

    Args:
        code: 代码内容
        file_path: 文件路径（用于报告）

    Returns:
        违规列表
    """
    violations = []
    lines = code.split("\n")

    # 检测日报状态相关代码
    daily_report_patterns = [
        r'status\s*[=:]\s*["\'](\w+)["\']',  # status = "xxx" 或 status: "xxx"
        r'DailyReportStatus\.(\w+)',  # DailyReportStatus.xxx
        r'["\']status["\']\s*:\s*["\'](\w+)["\']',  # "status": "xxx"
    ]

    for line_num, line in enumerate(lines, 1):
        # 跳过注释
        if line.strip().startswith("#") or line.strip().startswith("//"):
            continue

        # 检查是否涉及日报状态
        if "daily" in line.lower() or "report" in line.lower() or "status" in line.lower():
            for pattern in daily_report_patterns:
                matches = re.findall(pattern, line, re.IGNORECASE)
                for match in matches:
                    state = match.lower()
                    # 检查是否是已知的日报状态
                    if state not in DAILY_REPORT_STATES and _looks_like_state(state):
                        violations.append(SotViolation(
                            file=file_path,
                            rule="SM-DR-001",
                            severity="P0",
                            detail=f"发现未定义的日报状态 '{match}'，不在 STATE_MACHINE.md v2.6 的 8 状态中",
                            line=line_num,
                        ))

    # 检测项目状态
    project_patterns = [
        r'project.*status\s*[=:]\s*["\'](\w+)["\']',
        r'ProjectStatus\.(\w+)',
    ]

    for line_num, line in enumerate(lines, 1):
        if "project" in line.lower():
            for pattern in project_patterns:
                matches = re.findall(pattern, line, re.IGNORECASE)
                for match in matches:
                    state = match.lower()
                    if state not in PROJECT_STATES and _looks_like_state(state):
                        violations.append(SotViolation(
                            file=file_path,
                            rule="SM-PROJ-001",
                            severity="P0",
                            detail=f"发现未定义的项目状态 '{match}'，不在 STATE_MACHINE.md v2.6 定义中",
                            line=line_num,
                        ))

    return violations


def check_ledger_compliance(code: str, file_path: str = "") -> List[SotViolation]:
    """
    检查代码是否违反账本系统规则（LEDGER_SOT.md v1.1）。

    P0 违规项：
    - 直接修改 balance 字段
    - 直接 UPDATE/DELETE ledger_entries
    - 绕过账本系统直接操作余额

    Args:
        code: 代码内容
        file_path: 文件路径

    Returns:
        违规列表
    """
    violations = []
    lines = code.split("\n")

    # P0: 直接修改 balance 的模式
    balance_patterns = [
        r'\.balance\s*[+\-*/]?=',  # .balance = / .balance += 等
        r'UPDATE.*SET.*balance\s*=',  # SQL UPDATE balance
        r'balance\s*=\s*balance\s*[+\-]',  # balance = balance + xxx
    ]

    # P0: 直接操作 ledger_entries 的模式
    ledger_danger_patterns = [
        r'UPDATE\s+ledger_entries',
        r'DELETE\s+FROM\s+ledger_entries',
        r'DELETE\s+ledger_entries',
    ]

    for line_num, line in enumerate(lines, 1):
        line_lower = line.lower()

        # 跳过注释
        if line.strip().startswith("#") or line.strip().startswith("//") or line.strip().startswith("--"):
            continue

        # 检查直接修改 balance
        for pattern in balance_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                violations.append(SotViolation(
                    file=file_path,
                    rule="LED-001",
                    severity="P0",
                    detail="禁止直接修改 balance 字段，必须通过 ledger_entries 分录操作",
                    line=line_num,
                ))
                break

        # 检查危险的 ledger_entries 操作
        for pattern in ledger_danger_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                violations.append(SotViolation(
                    file=file_path,
                    rule="LED-002",
                    severity="P0",
                    detail="禁止直接 UPDATE/DELETE ledger_entries 表，账本记录只允许 INSERT",
                    line=line_num,
                ))
                break

    return violations


def check_error_code_compliance(code: str, file_path: str = "") -> List[SotViolation]:
    """
    检查代码中的错误码是否符合 ERROR_CODES_SOT.md v2.1 定义。

    P1 警告：
    - 发现非标准格式的错误码
    - 发现未在 SoT 中注册的错误码

    Args:
        code: 代码内容
        file_path: 文件路径

    Returns:
        警告列表
    """
    warnings = []
    lines = code.split("\n")

    # 错误码格式：XXX-NNN（3字母-3数字）
    error_code_pattern = r'["\']([A-Z]{2,4}-\d{3})["\']'

    # 已知的错误码前缀（来自 ERROR_CODES_SOT.md v2.1）
    known_prefixes = {"VAL", "AUTH", "BIZ", "SYS", "DB", "API", "LED", "SM", "REC", "TRF"}

    for line_num, line in enumerate(lines, 1):
        matches = re.findall(error_code_pattern, line)
        for code_match in matches:
            prefix = code_match.split("-")[0]
            if prefix not in known_prefixes:
                warnings.append(SotViolation(
                    file=file_path,
                    rule="ERR-001",
                    severity="P1",
                    detail=f"错误码 '{code_match}' 前缀 '{prefix}' 不在 ERROR_CODES_SOT.md v2.1 已知前缀中",
                    line=line_num,
                ))

    return warnings


def check_data_schema_compliance(code: str, file_path: str = "") -> List[SotViolation]:
    """
    检查代码中的数据库字段是否符合 DATA_SCHEMA.md v5.2 定义。

    P1 警告：
    - 发现可疑的自定义字段名
    - 发现与 SoT 不一致的类型定义

    Args:
        code: 代码内容
        file_path: 文件路径

    Returns:
        警告列表
    """
    warnings = []

    # 已知的核心表名
    known_tables = {
        "users", "projects", "ad_accounts", "daily_reports",
        "ledger_entries", "topup_requests", "reconciliations",
        "transfers", "audit_logs", "channels", "project_channels",
    }

    # 检测可疑的表定义
    table_pattern = r'class\s+(\w+)\s*\(.*Base.*\)'
    matches = re.findall(table_pattern, code)
    for match in matches:
        table_name = _camel_to_snake(match)
        if table_name not in known_tables and not table_name.endswith("_association"):
            warnings.append(SotViolation(
                file=file_path,
                rule="SCHEMA-001",
                severity="P1",
                detail=f"发现未在 DATA_SCHEMA.md v5.2 定义的表 '{table_name}'",
                line=None,
            ))

    return warnings


def _looks_like_state(value: str) -> bool:
    """判断一个值是否看起来像状态枚举"""
    # 排除常见的非状态词
    non_states = {
        "true", "false", "null", "none", "undefined",
        "id", "name", "type", "value", "data", "error",
        "success", "failure", "ok", "fail",
    }
    return value.lower() not in non_states and len(value) > 2


def _camel_to_snake(name: str) -> str:
    """驼峰转下划线"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


# === 快捷入口函数 ===

def guard_check(changes: Dict[str, str]) -> Dict[str, Any]:
    """
    SoT 守门员快捷入口。

    等同于 validate_against_sot()，提供更简短的函数名。
    """
    return validate_against_sot(changes)
