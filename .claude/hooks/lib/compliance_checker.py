#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合规检查器 - SoT 合规性检查

检查代码是否符合 SoT 规范，包括：
- 角色白名单检查
- Phase 1 约束检查
- 禁止模式检查
- 状态机合规检查
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Set, Pattern

from .config import (
    VALID_ROLES,
    DEPRECATED_ROLES,
    ROLE_MAPPING,
    PHASE2_FORBIDDEN_KEYWORDS,
    PHASE2_FORBIDDEN_STATES,
    DAILY_REPORT_STATES,
    TOPUP_STATES,
)


# =============================================================================
# 严重级别
# =============================================================================


class Severity(str, Enum):
    """违规严重级别"""

    CRITICAL = "critical"  # 必须修复，阻止提交
    WARNING = "warning"  # 建议修复，不阻止
    INFO = "info"  # 提示信息


# =============================================================================
# 违规记录
# =============================================================================


@dataclass
class Violation:
    """单条违规记录"""

    severity: Severity
    message: str
    file: str
    line: int
    snippet: str = ""
    rule_id: str = ""
    suggestion: str = ""


# =============================================================================
# 检查规则
# =============================================================================


@dataclass
class Rule:
    """检查规则定义"""

    id: str
    pattern: str | Pattern
    message: str
    severity: Severity = Severity.CRITICAL
    suggestion: str = ""
    file_patterns: List[str] = field(default_factory=lambda: ["*.py", "*.ts", "*.tsx"])

    def __post_init__(self):
        if isinstance(self.pattern, str):
            self.compiled = re.compile(self.pattern, re.IGNORECASE)
        else:
            self.compiled = self.pattern


# =============================================================================
# 规则集
# =============================================================================

# Phase 2 禁止关键词规则
PHASE2_RULES = [
    Rule(
        id="P2-001",
        pattern=r"auto[_-]?reject",
        message="Phase 1 violation: auto_reject forbidden",
        suggestion="Remove auto_reject - Phase 1 only allows notifications, not automatic actions",
    ),
    Rule(
        id="P2-002",
        pattern=r"auto[_-]?suspend",
        message="Phase 1 violation: auto_suspend forbidden",
        suggestion="Remove auto_suspend - use warning/highlight instead",
    ),
    Rule(
        id="P2-003",
        pattern=r"auto[_-]?block",
        message="Phase 1 violation: auto_block forbidden",
        suggestion="Remove auto_block - Phase 1 is soft enforcement only",
    ),
    Rule(
        id="P2-004",
        pattern=r"auto[_-]?freeze",
        message="Phase 1 violation: auto_freeze forbidden",
        suggestion="Remove auto_freeze - accounts should not be frozen automatically",
    ),
    Rule(
        id="P2-005",
        pattern=r"force[_-]?stop",
        message="Phase 1 violation: force_stop forbidden",
        suggestion="Remove force_stop - use warnings instead",
    ),
    Rule(
        id="P2-006",
        pattern=r"forced?[_-]?approval",
        message="Phase 1 violation: forced_approval forbidden",
        suggestion="Remove forced_approval - approvals require human decision",
    ),
]

# 资金安全规则
FINANCE_RULES = [
    Rule(
        id="FIN-001",
        pattern=r"\.(balance|current_balance)\s*[+\-*/]?=",
        message="Direct balance modification forbidden",
        suggestion="Use ledger entries or fund_service for balance changes",
    ),
    Rule(
        id="FIN-002",
        pattern=r"UPDATE\s+.*balance",
        message="SQL direct balance update forbidden",
        suggestion="All balance changes must go through transaction log",
    ),
]

# 废弃角色规则
ROLE_RULES = [
    Rule(
        id="ROLE-001",
        pattern=r"['\"]supervisor['\"]",
        message="Deprecated role 'supervisor' detected",
        severity=Severity.WARNING,
        suggestion="Use 'project_owner' instead (PRD v2.2)",
    ),
    Rule(
        id="ROLE-002",
        pattern=r"['\"]data_operator['\"]",
        message="Deprecated role 'data_operator' detected",
        severity=Severity.WARNING,
        suggestion="Use 'finance' instead (PRD v2.2)",
    ),
    Rule(
        id="ROLE-003",
        pattern=r"role\s*===?\s*['\"]supervisor['\"]",
        message="Role check for deprecated 'supervisor'",
        suggestion="Change to project_owner check",
    ),
]

# SoT 文档保护规则
SOT_RULES = [
    Rule(
        id="SOT-001",
        pattern=r"rm\s+-rf?\s+.*docs/2\.sot",
        message="SoT document deletion forbidden",
        suggestion="SoT documents are read-only source of truth",
    ),
    Rule(
        id="SOT-002",
        pattern=r"DELETE\s+FROM\s+.*sot",
        message="SoT data deletion forbidden",
        suggestion="SoT data cannot be deleted",
    ),
]

# 废弃角色检测规则 (补充)
DEPRECATED_ROLE_RULES = [
    Rule(
        id="ROLE-004",
        pattern=r"['\"]media_buyer['\"]",
        message="Non-standard role 'media_buyer' detected",
        severity=Severity.WARNING,
        suggestion="Use 'pitcher' instead (MASTER.md v4.8 §2.4)",
    ),
    Rule(
        id="ROLE-005",
        pattern=r"UserRole\.MEDIA_BUYER",
        message="Deprecated enum 'UserRole.MEDIA_BUYER' detected",
        severity=Severity.WARNING,
        suggestion="Use 'UserRole.PITCHER' instead (requires DB migration)",
    ),
    Rule(
        id="ROLE-006",
        pattern=r"UserRole\.DATA_OPERATOR",
        message="Deprecated enum 'UserRole.DATA_OPERATOR' detected",
        severity=Severity.WARNING,
        suggestion="This role should be removed (requires DB migration)",
    ),
]

# 高风险模块检测规则
HIGH_RISK_RULES = [
    Rule(
        id="RISK-001",
        pattern=r"class\s+\w*[Ll]edger|ledger_entries|LedgerEntry",
        message="High-risk module: Ledger (M8-LEDGER)",
        severity=Severity.WARNING,
        suggestion="Ledger modifications require OpenSpec proposal",
    ),
    Rule(
        id="RISK-002",
        pattern=r"class\s+\w*[Rr]econciliation|recon_|_recon",
        message="High-risk module: Reconciliation (M9-RECON)",
        severity=Severity.WARNING,
        suggestion="Reconciliation modifications require OpenSpec proposal",
    ),
    Rule(
        id="RISK-003",
        pattern=r"gross_profit|net_profit|calculate_profit",
        message="High-risk module: Profit calculation (M10-PROFIT)",
        severity=Severity.WARNING,
        suggestion="Profit calculation modifications require OpenSpec proposal",
    ),
]

# 所有规则
ALL_RULES = (
    PHASE2_RULES
    + FINANCE_RULES
    + ROLE_RULES
    + DEPRECATED_ROLE_RULES
    + SOT_RULES
    + HIGH_RISK_RULES
)


# =============================================================================
# 合规检查器
# =============================================================================


class ComplianceChecker:
    """SoT 合规检查器"""

    def __init__(self, rules: List[Rule] | None = None):
        """
        初始化检查器

        Args:
            rules: 自定义规则列表，默认使用 ALL_RULES
        """
        self.rules = rules or ALL_RULES
        self.violations: List[Violation] = []
        self._checked_files: Set[str] = set()

    def check_content(self, filepath: str, content: str) -> bool:
        """
        检查内容合规性

        Args:
            filepath: 文件路径
            content: 文件内容

        Returns:
            True if compliant, False if violations found
        """
        self._checked_files.add(filepath)
        lines = content.split("\n")
        found_violations = False

        for rule in self.rules:
            # 检查文件扩展名是否匹配
            if not self._matches_file_pattern(filepath, rule.file_patterns):
                continue

            # 查找所有匹配
            for match in rule.compiled.finditer(content):
                found_violations = True
                line_num = content[: match.start()].count("\n") + 1
                snippet = lines[line_num - 1].strip() if line_num <= len(lines) else ""

                violation = Violation(
                    severity=rule.severity,
                    message=rule.message,
                    file=filepath,
                    line=line_num,
                    snippet=snippet,
                    rule_id=rule.id,
                    suggestion=rule.suggestion,
                )
                self.violations.append(violation)

        return not found_violations

    def check_file(self, filepath: str | Path) -> bool:
        """
        检查文件合规性

        Args:
            filepath: 文件路径

        Returns:
            True if compliant, False if violations found
        """
        path = Path(filepath)
        if not path.exists():
            return True

        content = path.read_text(encoding="utf-8")
        return self.check_content(str(filepath), content)

    def get_violations(self) -> List[Violation]:
        """获取所有违规"""
        return self.violations

    def get_critical_violations(self) -> List[Violation]:
        """获取严重违规"""
        return [v for v in self.violations if v.severity == Severity.CRITICAL]

    def get_warnings(self) -> List[Violation]:
        """获取警告"""
        return [v for v in self.violations if v.severity == Severity.WARNING]

    def is_compliant(self) -> bool:
        """检查是否合规（无严重违规）"""
        return len(self.get_critical_violations()) == 0

    def clear(self) -> None:
        """清空违规记录"""
        self.violations = []
        self._checked_files = set()

    def _matches_file_pattern(self, filepath: str, patterns: List[str]) -> bool:
        """检查文件是否匹配模式"""
        path = Path(filepath)
        for pattern in patterns:
            if pattern.startswith("*"):
                if path.suffix == pattern[1:]:
                    return True
            elif path.match(pattern):
                return True
        return False

    def format_report(self) -> str:
        """格式化违规报告"""
        if not self.violations:
            return "✅ No violations found"

        lines = [f"Found {len(self.violations)} violation(s):"]
        lines.append("")

        for v in self.violations:
            severity_icon = "🔴" if v.severity == Severity.CRITICAL else "🟡"
            lines.append(f"{severity_icon} [{v.rule_id}] {v.file}:{v.line}")
            lines.append(f"   {v.message}")
            if v.snippet:
                lines.append(f"   > {v.snippet}")
            if v.suggestion:
                lines.append(f"   💡 {v.suggestion}")
            lines.append("")

        return "\n".join(lines)


# =============================================================================
# 便捷函数
# =============================================================================


def check_code(filepath: str, content: str) -> List[Violation]:
    """
    检查代码合规性

    Args:
        filepath: 文件路径
        content: 文件内容

    Returns:
        违规列表
    """
    checker = ComplianceChecker()
    checker.check_content(filepath, content)
    return checker.get_violations()


def is_compliant(filepath: str, content: str) -> bool:
    """
    检查代码是否合规

    Args:
        filepath: 文件路径
        content: 文件内容

    Returns:
        True if compliant (no critical violations)
    """
    checker = ComplianceChecker()
    checker.check_content(filepath, content)
    return checker.is_compliant()


def check_role(role: str) -> Optional[str]:
    """
    检查角色是否合法

    Args:
        role: 角色名称

    Returns:
        None if valid, error message if invalid
    """
    role_lower = role.lower()

    if role_lower in VALID_ROLES:
        return None

    if role_lower in DEPRECATED_ROLES:
        correct_role = ROLE_MAPPING.get(role_lower)
        return f"Role '{role}' is deprecated. Use '{correct_role}' instead."

    return f"Unknown role '{role}'. Valid roles: {', '.join(sorted(VALID_ROLES))}"
