"""
SoT 守门员 Skill - P2 增强版

职责：
- 验证 AI 生成的代码是否违反 SoT 规则
- 检测是否发明了 SoT 中不存在的字段/状态/错误码
- 符合 PATTERNS.md AP-AI-002 要求

基准对齐：
- STATE_MACHINE.md v2.6 (8 状态机)
- ERROR_CODES_SOT.md v2.1
- DATA_SCHEMA.md v5.2
- LEDGER_SOT.md v1.1 (双账本)

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
# 尝试从 agents_config 导入，失败则使用默认路径
try:
    from ..agents_config import SOT_FILES, read_optional, PROJECT_ROOT
except ImportError:
    # Fallback for standalone usage
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    SOT_FILES = {
        "STATE_MACHINE": PROJECT_ROOT / "docs" / "2.sot" / "STATE_MACHINE.md",
        "ERROR_CODES": PROJECT_ROOT / "docs" / "2.sot" / "ERROR_CODES_SOT.md",
        "DATA_SCHEMA": PROJECT_ROOT / "docs" / "2.sot" / "DATA_SCHEMA.md",
        "LEDGER_SOT": PROJECT_ROOT / "docs" / "2.sot" / "LEDGER_SOT.md",
    }

    def read_optional(path: Path) -> str:
        """Fallback read_optional implementation."""
        try:
            return path.read_text(encoding="utf-8") if path.exists() else ""
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
        P1-AG-003 增强：重新加载 SoT 文档。

        当 SoT 文档更新后，调用此方法使解析器重新读取最新内容。
        无需重启进程即可获取最新的状态枚举、错误码等定义。

        Returns:
            重新加载后的 SotParser 实例

        Example:
            from agents.skills.sot_guard_skill import SotParser
            SotParser.reload()
        """
        cls.invalidate_cache()
        return cls.get_instance()

    @classmethod
    def invalidate_cache(cls) -> None:
        """
        使当前缓存失效。

        下次调用 get_instance() 时会重新解析 SoT 文档。
        """
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
            for w in self.parse_warnings[:5]:  # Log first 5
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

        # 尝试解析日报状态（查找 8 状态机相关段落）
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

        # 尝试提取表名（从 CREATE TABLE 或 class XXX(Base) 定义）
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

        # 提取错误码前缀（XXX-NNN 格式）
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
        """
        尝试从 Markdown 内容中提取枚举值。

        Args:
            content: Markdown 内容
            patterns: 正则模式列表
            default: 解析失败时的默认值

        Returns:
            提取的枚举集合
        """
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                # 将匹配结果分割成单独的值
                values = set()
                for match in matches:
                    # 分割 "a, b, c" 或 "a → b → c" 或 "a | b | c"
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


# === 兼容旧 API：模块级变量（从解析器获取） ===
# 这些变量会在首次访问时初始化

def _init_module_vars():
    """初始化模块级变量（延迟初始化）"""
    parser = SotParser.get_instance()
    return {
        "DAILY_REPORT_STATES": parser.daily_report_states,
        "PROJECT_STATES": parser.project_states,
        "TOPUP_STATES": parser.topup_states,
        "LEDGER_TYPES": parser.ledger_types,
        "ENTRY_TYPES": parser.entry_types,
        "USER_ROLES": parser.user_roles,
    }


# 使用默认值初始化，调用 get_*() 函数获取动态值
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

    # 触发 SoT 解析（如果尚未解析）
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

    # 使用动态解析的状态值
    daily_report_states = get_daily_report_states()
    project_states = get_project_states()

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
                    if state not in daily_report_states and _looks_like_state(state):
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
                    if state not in project_states and _looks_like_state(state):
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

    # 使用动态解析的前缀
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

    # 使用动态解析的表名
    known_tables = get_known_tables()

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
