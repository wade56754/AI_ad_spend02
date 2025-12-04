"""
SoT 守门员 Skill - P2 增强版

Phase 3: 从 agents/skills/sot_guard_skill.py 迁移

职责：
- 验证 AI 生成的代码是否违反 SoT 规则
- 检测是否发明了 SoT 中不存在的字段/状态/错误码
- 符合 PATTERNS.md AP-AI-002 要求

基准对齐：
- STATE_MACHINE.md v2.6 (8 状态机)
- ERROR_CODES_SOT.md v2.1
- DATA_SCHEMA.md v5.2
- LEDGER_SOT.md v1.1 (双账本)
- AGENT_PLATFORM_MIGRATION_PLAN_v1.2.md Phase 3

P2 增强：
- 支持动态解析 SoT 文档获取枚举值
- 解析失败时回退到硬编码默认值
- 增加 SoT 文件缺失警告
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path
import re
import logging

logger = logging.getLogger(__name__)


# === SoT 文档路径配置 ===
# 使用新的 agent_platform.config 模块
try:
    from agent_platform.config.sot_files import SOT_FILES
    from agent_platform.config.paths import read_optional, PROJECT_ROOT
except ImportError:
    # Fallback for standalone usage
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
    SOT_FILES = {
        "STATE_MACHINE": PROJECT_ROOT / "docs" / "2.sot" / "STATE_MACHINE.md",
        "ERROR_CODES": PROJECT_ROOT / "docs" / "2.sot" / "ERROR_CODES_SOT.md",
        "DATA_SCHEMA": PROJECT_ROOT / "docs" / "2.sot" / "DATA_SCHEMA.md",
        "LEDGER_SOT": PROJECT_ROOT / "docs" / "2.sot" / "LEDGER_SOT.md",
    }

    def read_optional(path: Path) -> str:
        """Fallback read_optional implementation."""
        try:
            return path.read_text(encoding="utf-8") if path and path.exists() else ""
        except Exception:
            return ""


# === 硬编码默认值（来自 STATE_MACHINE.md v2.6）===
# 这些值作为 SoT 解析失败时的回退

DEFAULT_DAILY_REPORT_STATES: Set[str] = {
    "raw_submitted",
    "trend_pending",
    "trend_ok",
    "trend_flagged",
    "trend_resolved",
    "final_pending",
    "final_confirmed",
    "final_locked",
}

DEFAULT_DAILY_REPORT_TRANSITIONS: Dict[str, List[str]] = {
    "raw_submitted": ["trend_pending"],
    "trend_pending": ["trend_ok", "trend_flagged"],
    "trend_ok": ["final_pending"],
    "trend_flagged": ["trend_resolved"],
    "trend_resolved": ["final_pending"],
    "final_pending": ["final_confirmed"],
    "final_confirmed": ["final_locked"],
    "final_locked": [],  # 终态，不可再流转
}

DEFAULT_PROJECT_STATES: Set[str] = {
    "draft",
    "active",
    "paused",
    "completed",
    "archived",
}

DEFAULT_TOPUP_STATES: Set[str] = {
    "pending",
    "approved",
    "rejected",
    "completed",
    "cancelled",
}

DEFAULT_LEDGER_TYPES: Set[str] = {
    "PROJECT",
    "SUPPLIER",
}

DEFAULT_ENTRY_TYPES: Set[str] = {
    "RECHARGE",
    "SPEND",
    "ADJUST",
    "TRANSFER_OUT",
    "TRANSFER_IN",
}

DEFAULT_USER_ROLES: Set[str] = {
    "admin",
    "finance",
    "data_operator",
    "account_manager",
    "media_buyer",
}

DEFAULT_ERROR_CODE_PREFIXES: Set[str] = {
    "VAL", "AUTH", "BIZ", "SYS", "DB", "API", "LED", "SM", "REC", "TRF"
}

DEFAULT_KNOWN_TABLES: Set[str] = {
    "users", "projects", "ad_accounts", "daily_reports",
    "ledger_entries", "topup_requests", "reconciliations",
    "transfers", "audit_logs", "channels", "project_channels",
}


# === 动态 SoT 解析器 ===

class SotParser:
    """
    从 SoT 文档中动态解析枚举值。

    P2 增强：优先从 SoT 文档解析，解析失败时退回硬编码默认值。
    """

    _instance: Optional["SotParser"] = None
    _cached: bool = False

    # 解析后的值
    daily_report_states: Set[str] = set()
    project_states: Set[str] = set()
    topup_states: Set[str] = set()
    ledger_types: Set[str] = set()
    entry_types: Set[str] = set()
    user_roles: Set[str] = set()
    error_code_prefixes: Set[str] = set()
    known_tables: Set[str] = set()

    # 解析状态
    parse_warnings: List[str] = []

    @classmethod
    def get_instance(cls) -> "SotParser":
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = SotParser()
            cls._instance._parse_all()
        return cls._instance

    @classmethod
    def reload(cls) -> "SotParser":
        """
        重新加载 SoT 文档。

        当 SoT 文档更新后，调用此方法使解析器重新读取最新内容。
        无需重启进程即可获取最新的状态枚举、错误码等定义。
        """
        cls.invalidate_cache()
        return cls.get_instance()

    @classmethod
    def invalidate_cache(cls) -> None:
        """使当前缓存失效。"""
        if cls._instance is not None:
            cls._instance._cached = False
            cls._instance = None
            logger.info("SotParser cache invalidated, will reload on next access")

    def _parse_all(self) -> None:
        """解析所有 SoT 文档"""
        if self._cached:
            return

        self.parse_warnings = []

        # 解析 STATE_MACHINE.md
        self._parse_state_machine()

        # 解析 DATA_SCHEMA.md
        self._parse_data_schema()

        # 解析 ERROR_CODES_SOT.md
        self._parse_error_codes()

        self._cached = True

        if self.parse_warnings:
            logger.warning(
                f"SoT Parser: {len(self.parse_warnings)} warnings during parsing. "
                "Using default values for missing items."
            )
            for w in self.parse_warnings[:5]:
                logger.warning(f"  - {w}")

    def _parse_state_machine(self) -> None:
        """从 STATE_MACHINE.md 解析状态枚举"""
        content = ""
        if "STATE_MACHINE" in SOT_FILES:
            content = read_optional(SOT_FILES["STATE_MACHINE"])

        if not content:
            self.parse_warnings.append("STATE_MACHINE.md not found or empty, using defaults")
            self.daily_report_states = DEFAULT_DAILY_REPORT_STATES.copy()
            self.project_states = DEFAULT_PROJECT_STATES.copy()
            self.topup_states = DEFAULT_TOPUP_STATES.copy()
            return

        # 尝试解析日报状态
        dr_states = self._extract_enum_from_markdown(
            content,
            patterns=[
                r"日报.*状态.*:\s*([a-z_]+(?:\s*[,→|]\s*[a-z_]+)*)",
                r"DailyReportStatus.*:\s*`?([a-z_]+(?:\s*[,|]\s*[a-z_]+)*)`?",
                r"raw_submitted\s*→\s*([a-z_]+(?:\s*→\s*[a-z_]+)*)",
            ],
            default=DEFAULT_DAILY_REPORT_STATES
        )
        self.daily_report_states = dr_states

        # 尝试解析项目状态
        proj_states = self._extract_enum_from_markdown(
            content,
            patterns=[
                r"项目状态.*:\s*([a-z_]+(?:\s*[,|]\s*[a-z_]+)*)",
                r"ProjectStatus.*:\s*([a-z_]+(?:\s*[,|]\s*[a-z_]+)*)",
            ],
            default=DEFAULT_PROJECT_STATES
        )
        self.project_states = proj_states

        # 尝试解析充值状态
        topup_states = self._extract_enum_from_markdown(
            content,
            patterns=[
                r"充值.*状态.*:\s*([a-z_]+(?:\s*[,|]\s*[a-z_]+)*)",
                r"TopupStatus.*:\s*([a-z_]+(?:\s*[,|]\s*[a-z_]+)*)",
            ],
            default=DEFAULT_TOPUP_STATES
        )
        self.topup_states = topup_states

        # 账本类型和分录类型
        self.ledger_types = DEFAULT_LEDGER_TYPES.copy()
        self.entry_types = DEFAULT_ENTRY_TYPES.copy()
        self.user_roles = DEFAULT_USER_ROLES.copy()

    def _parse_data_schema(self) -> None:
        """从 DATA_SCHEMA.md 解析表名"""
        content = ""
        if "DATA_SCHEMA" in SOT_FILES:
            content = read_optional(SOT_FILES["DATA_SCHEMA"])

        if not content:
            self.parse_warnings.append("DATA_SCHEMA.md not found or empty, using default table list")
            self.known_tables = DEFAULT_KNOWN_TABLES.copy()
            return

        # 尝试提取表名
        tables = set()
        table_patterns = [
            r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)",
            r"表名[：:]\s*`?(\w+)`?",
            r"###?\s+(\w+)\s*表",
        ]

        for pattern in table_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            tables.update(m.lower() for m in matches)

        if tables:
            self.known_tables = tables
        else:
            self.parse_warnings.append("Could not parse table names from DATA_SCHEMA.md")
            self.known_tables = DEFAULT_KNOWN_TABLES.copy()

    def _parse_error_codes(self) -> None:
        """从 ERROR_CODES_SOT.md 解析错误码前缀"""
        content = ""
        if "ERROR_CODES" in SOT_FILES:
            content = read_optional(SOT_FILES["ERROR_CODES"])

        if not content:
            self.parse_warnings.append("ERROR_CODES_SOT.md not found or empty, using default prefixes")
            self.error_code_prefixes = DEFAULT_ERROR_CODE_PREFIXES.copy()
            return

        # 提取错误码前缀
        prefixes = set()
        error_pattern = r'"([A-Z]{2,4})-\d{3}"'
        matches = re.findall(error_pattern, content)
        prefixes.update(matches)

        if prefixes:
            self.error_code_prefixes = prefixes
        else:
            self.parse_warnings.append("Could not parse error code prefixes from ERROR_CODES_SOT.md")
            self.error_code_prefixes = DEFAULT_ERROR_CODE_PREFIXES.copy()

    def _extract_enum_from_markdown(
        self,
        content: str,
        patterns: List[str],
        default: Set[str]
    ) -> Set[str]:
        """尝试从 Markdown 内容中提取枚举值。"""
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                values = set()
                for match in matches:
                    parts = re.split(r'\s*[,→|]\s*', match)
                    values.update(p.strip().lower() for p in parts if p.strip())
                if values:
                    return values
        return default.copy()


# === 运行时获取 SoT 值的便捷函数 ===

def get_daily_report_states() -> Set[str]:
    """获取日报状态枚举"""
    return SotParser.get_instance().daily_report_states


def get_project_states() -> Set[str]:
    """获取项目状态枚举"""
    return SotParser.get_instance().project_states


def get_topup_states() -> Set[str]:
    """获取充值状态枚举"""
    return SotParser.get_instance().topup_states


def get_known_tables() -> Set[str]:
    """获取已知表名集合"""
    return SotParser.get_instance().known_tables


def get_error_code_prefixes() -> Set[str]:
    """获取已知错误码前缀"""
    return SotParser.get_instance().error_code_prefixes


# === 兼容旧 API：模块级变量 ===
DAILY_REPORT_STATES = DEFAULT_DAILY_REPORT_STATES
DAILY_REPORT_TRANSITIONS = DEFAULT_DAILY_REPORT_TRANSITIONS
PROJECT_STATES = DEFAULT_PROJECT_STATES
TOPUP_STATES = DEFAULT_TOPUP_STATES
LEDGER_TYPES = DEFAULT_LEDGER_TYPES
ENTRY_TYPES = DEFAULT_ENTRY_TYPES
USER_ROLES = DEFAULT_USER_ROLES


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

    # 触发 SoT 解析
    parser = SotParser.get_instance()

    # 如果解析时有警告，添加到结果中
    for warn_msg in parser.parse_warnings:
        result.warnings.append(SotViolation(
            file="<sot_parser>",
            rule="SOT-PARSE-001",
            severity="P2",
            detail=warn_msg,
        ))

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
    """
    violations = []
    lines = code.split("\n")

    daily_report_states = get_daily_report_states()
    project_states = get_project_states()

    # 日报相关上下文关键词
    daily_report_context_keywords = {
        "daily_report", "dailyreport", "daily_reports", "dailyreports",
        "dailyreportstatus", "daily_report_status",
        "ad_spend_daily", "report_status", "日报",
    }

    # 日报状态模式
    daily_report_patterns = [
        r'DailyReportStatus\.(\w+)',
        r'daily_report.*status\s*[=:]\s*["\'](\w+)["\']',
        r'report_status\s*[=:]\s*["\'](\w+)["\']',
    ]

    generic_status_pattern = r'status\s*[=:]\s*["\'](\w+)["\']'

    for line_num, line in enumerate(lines, 1):
        if line.strip().startswith("#") or line.strip().startswith("//"):
            continue

        line_lower = line.lower()
        has_daily_report_context = any(
            kw in line_lower for kw in daily_report_context_keywords
        )

        # 检查明确的日报状态模式
        for pattern in daily_report_patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            for match in matches:
                state = match.lower()
                if state not in daily_report_states and _looks_like_state(state):
                    violations.append(SotViolation(
                        file=file_path,
                        rule="SM-DR-001",
                        severity="P0",
                        detail=f"发现未定义的日报状态 '{match}'，不在 STATE_MACHINE.md v2.6 的 8 状态中",
                        line=line_num,
                    ))

        # 通用 status 模式仅在有明确日报上下文时检测
        if has_daily_report_context:
            matches = re.findall(generic_status_pattern, line, re.IGNORECASE)
            for match in matches:
                state = match.lower()
                if (state not in daily_report_states
                    and _looks_like_state(state)
                    and not _is_generic_status_value(state)):
                    violations.append(SotViolation(
                        file=file_path,
                        rule="SM-DR-001",
                        severity="P0",
                        detail=f"发现未定义的日报状态 '{match}'，不在 STATE_MACHINE.md v2.6 的 8 状态中",
                        line=line_num,
                    ))

    # 检测项目状态
    project_patterns = [
        r'ProjectStatus\.(\w+)',
        r'project.*status\s*[=:]\s*["\'](\w+)["\']',
    ]

    for line_num, line in enumerate(lines, 1):
        if "project" in line.lower():
            for pattern in project_patterns:
                matches = re.findall(pattern, line, re.IGNORECASE)
                for match in matches:
                    state = match.lower()
                    if state not in project_states and _looks_like_state(state):
                        violations.append(SotViolation(
                            file=file_path,
                            rule="SM-PROJ-001",
                            severity="P0",
                            detail=f"发现未定义的项目状态 '{match}'，不在 STATE_MACHINE.md v2.6 定义中",
                            line=line_num,
                        ))

    return violations


def _is_generic_status_value(value: str) -> bool:
    """判断是否是通用的状态值（不属于业务状态机）。"""
    generic_statuses = {
        "ok", "error", "success", "failed", "failure",
        "pending", "processing", "completed", "cancelled", "canceled",
        "active", "inactive", "enabled", "disabled",
        "valid", "invalid", "verified", "unverified",
        "loading", "loaded", "idle",
    }
    return value.lower() in generic_statuses


def check_ledger_compliance(code: str, file_path: str = "") -> List[SotViolation]:
    """
    检查代码是否违反账本系统规则（LEDGER_SOT.md v1.1）。
    """
    violations = []
    lines = code.split("\n")

    # P0: 直接修改 balance 的模式
    balance_patterns = [
        r'\.balance\s*[+\-*/]?=',
        r'UPDATE.*SET.*balance\s*=',
        r'balance\s*=\s*balance\s*[+\-]',
    ]

    # P0: 直接操作 ledger_entries 的模式
    ledger_danger_patterns = [
        r'UPDATE\s+ledger_entries',
        r'DELETE\s+FROM\s+ledger_entries',
        r'DELETE\s+ledger_entries',
    ]

    for line_num, line in enumerate(lines, 1):
        if line.strip().startswith("#") or line.strip().startswith("//") or line.strip().startswith("--"):
            continue

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
    """
    warnings = []
    lines = code.split("\n")

    error_code_pattern = r'["\']([A-Z]{2,4}-\d{3})["\']'
    known_prefixes = get_error_code_prefixes()

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
    """
    warnings = []

    known_tables = get_known_tables()

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
    """判断一个值是否看起来像状态枚举。"""
    value_lower = value.lower()

    non_states = {
        "true", "false", "null", "none", "undefined", "nil",
        "id", "name", "type", "value", "data", "error", "message",
        "result", "response", "request", "content", "body",
        "success", "failure", "ok", "fail", "failed", "passed",
        "enabled", "disabled", "valid", "invalid",
        "created", "updated", "deleted", "new", "old",
        "insert", "update", "delete", "select", "query",
        "get", "post", "put", "patch", "head", "options",
    }

    if len(value) <= 2:
        return False
    if value_lower in non_states:
        return False
    if value.isdigit() or (value and value[0].isdigit()):
        return False
    if not value.replace("_", "").isalnum():
        return False

    return True


def _camel_to_snake(name: str) -> str:
    """驼峰转下划线"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


# === 快捷入口函数 ===

def guard_check(changes: Dict[str, str]) -> Dict[str, Any]:
    """SoT 守门员快捷入口。"""
    return validate_against_sot(changes)


# Export all public functions and classes
__all__ = [
    "validate_against_sot",
    "guard_check",
    "check_state_machine_compliance",
    "check_ledger_compliance",
    "check_error_code_compliance",
    "check_data_schema_compliance",
    "SotViolation",
    "SotGuardResult",
    "SotParser",
    "get_daily_report_states",
    "get_project_states",
    "get_topup_states",
    "get_known_tables",
    "get_error_code_prefixes",
]
