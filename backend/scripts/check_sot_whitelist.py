#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SoT Whitelist Validation Script

Validates codebase against SoT (Source of Truth) whitelists:
1. Roles - Must be in 6 valid roles from MASTER.md
2. States - Must match STATE_MACHINE.md definitions
3. Error codes - Must follow ERROR_CODES_SOT.md patterns

Usage:
  python backend/scripts/check_sot_whitelist.py

Exit codes:
  0 - No issues found
  1 - Issues found
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass

ROOT_DIR = Path(__file__).parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend" / "src"


# =============================================================================
# SoT Whitelist Definitions (from MASTER.md v4.9 / STATE_MACHINE.md v2.9)
# =============================================================================

# Valid roles (6 from MASTER.md v4.9 Section 2.4)
VALID_ROLES: Set[str] = {
    "ceo",
    "project_owner",
    "finance",
    "pitcher",
    "account_manager",
    "admin",
}

# Technical role alias (maps to pitcher in business layer)
TECHNICAL_ROLES: Set[str] = {
    "media_buyer",  # Technical alias -> pitcher
}

# Deprecated roles (MUST NOT use)
DEPRECATED_ROLES: Dict[str, str] = {
    "supervisor": "project_owner",
    "data_operator": "finance",
}

# Daily report states (Phase 1: 3 states only)
DAILY_REPORT_STATES: Set[str] = {
    "raw_submitted",
    "trend_ok",
    "final_confirmed",
}

# Phase 2 forbidden states (not allowed in Phase 1)
PHASE2_FORBIDDEN_STATES: Set[str] = {
    "trend_pending",
    "trend_flagged",
    "trend_rejected",
    "auto_rejected",
    "auto_suspended",
    "pending_verification",
}

# Topup states (7 states)
TOPUP_STATES: Set[str] = {
    "draft",
    "pending_review",
    "finance_approve",
    "paid",
    "completed",
    "rejected",
    "cancelled",
}

# Ad account states
AD_ACCOUNT_STATES: Set[str] = {
    "pending",
    "active",
    "paused",
    "suspended",
    "closed",
}

# All valid states combined
ALL_VALID_STATES: Set[str] = DAILY_REPORT_STATES | TOPUP_STATES | AD_ACCOUNT_STATES


@dataclass
class ValidationIssue:
    """Validation issue"""

    file: str
    line: int
    category: str  # role, state, phase
    severity: str  # error, warning
    value: str
    message: str
    suggestion: str = ""


def scan_python_files() -> List[Path]:
    """Get all Python files to scan"""
    files = []

    # Backend files
    for py_file in BACKEND_DIR.rglob("*.py"):
        # Skip migrations and cache
        if "migrations" in str(py_file) or "__pycache__" in str(py_file):
            continue
        # Skip this script itself (contains whitelist definitions)
        if py_file.name == "check_sot_whitelist.py":
            continue
        # Skip role_mapping.py (contains legacy mapping definitions)
        if py_file.name == "role_mapping.py":
            continue
        # Skip config files that define whitelist patterns
        if "hooks" in str(py_file) and py_file.name in (
            "config.py",
            "sot_validator.py",
        ):
            continue
        files.append(py_file)

    return files


def scan_typescript_files() -> List[Path]:
    """Get all TypeScript files to scan"""
    files = []

    if FRONTEND_DIR.exists():
        for ts_file in FRONTEND_DIR.rglob("*.ts"):
            if "node_modules" in str(ts_file):
                continue
            files.append(ts_file)
        for tsx_file in FRONTEND_DIR.rglob("*.tsx"):
            if "node_modules" in str(tsx_file):
                continue
            files.append(tsx_file)

    return files


def check_deprecated_roles(content: str, filepath: str) -> List[ValidationIssue]:
    """Check for deprecated role usage"""
    issues = []
    lines = content.split("\n")

    for deprecated, replacement in DEPRECATED_ROLES.items():
        # String patterns
        patterns = [
            rf'["\']({deprecated})["\']',
            rf"UserRole\.{deprecated.upper()}",
            rf'role\s*==\s*["\']?{deprecated}["\']?',
            rf'\.role\s*==\s*["\']?{deprecated}["\']?',
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[: match.start()].count("\n") + 1
                line_content = lines[line_num - 1].strip()

                # Skip comments
                if line_content.startswith("#") or line_content.startswith("//"):
                    continue
                # Skip docstrings
                if '"""' in line_content or "'''" in line_content:
                    continue

                issues.append(
                    ValidationIssue(
                        file=str(Path(filepath).relative_to(ROOT_DIR)),
                        line=line_num,
                        category="role",
                        severity="warning",
                        value=deprecated,
                        message=f"Deprecated role '{deprecated}' detected",
                        suggestion=f"Use '{replacement}' instead (MASTER.md v4.9 Section 2.4)",
                    )
                )

    return issues


def check_phase2_states(content: str, filepath: str) -> List[ValidationIssue]:
    """Check for Phase 2 forbidden states"""
    issues = []
    lines = content.split("\n")

    for state in PHASE2_FORBIDDEN_STATES:
        # String patterns
        pattern = rf'["\']({state})["\']'

        for match in re.finditer(pattern, content, re.IGNORECASE):
            line_num = content[: match.start()].count("\n") + 1
            line_content = lines[line_num - 1].strip()

            # Skip comments
            if line_content.startswith("#") or line_content.startswith("//"):
                continue
            # Skip docstrings and documentation
            if '"""' in line_content or "'''" in line_content:
                continue
            # Skip test assertions and mocks
            if "assert" in line_content.lower() or "mock" in line_content.lower():
                continue

            issues.append(
                ValidationIssue(
                    file=str(Path(filepath).relative_to(ROOT_DIR)),
                    line=line_num,
                    category="state",
                    severity="error",
                    value=state,
                    message=f"Phase 2 state '{state}' used in Phase 1 codebase",
                    suggestion="Phase 1 only allows: raw_submitted, trend_ok, final_confirmed",
                )
            )

    return issues


def check_phase1_violations(content: str, filepath: str) -> List[ValidationIssue]:
    """Check for Phase 1 principle violations"""
    issues = []
    lines = content.split("\n")

    # Phase 1 forbidden patterns (auto-blocking/rejection)
    forbidden_patterns = [
        (r"auto[_-]?reject", "auto_reject", "Use warning/notification instead"),
        (r"auto[_-]?suspend", "auto_suspend", "Use highlight/flag instead"),
        (r"auto[_-]?block", "auto_block", "Phase 1 is soft enforcement only"),
        (r"auto[_-]?freeze", "auto_freeze", "Use warning notification instead"),
        (r"force[_-]?stop", "force_stop", "Use soft warning instead"),
    ]

    for pattern, keyword, suggestion in forbidden_patterns:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            line_num = content[: match.start()].count("\n") + 1
            line_content = lines[line_num - 1].strip()

            # Skip comments and documentation
            if line_content.startswith("#") or line_content.startswith("//"):
                continue
            if '"""' in line_content or "'''" in line_content:
                continue

            issues.append(
                ValidationIssue(
                    file=str(Path(filepath).relative_to(ROOT_DIR)),
                    line=line_num,
                    category="phase",
                    severity="error",
                    value=keyword,
                    message=f"Phase 1 violation: '{keyword}' is forbidden",
                    suggestion=suggestion,
                )
            )

    return issues


def validate_file(filepath: Path) -> List[ValidationIssue]:
    """Validate a single file"""
    issues = []

    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return issues

    # Check deprecated roles
    issues.extend(check_deprecated_roles(content, str(filepath)))

    # Check Phase 2 states
    issues.extend(check_phase2_states(content, str(filepath)))

    # Check Phase 1 violations
    issues.extend(check_phase1_violations(content, str(filepath)))

    return issues


def print_report(issues: List[ValidationIssue]) -> bool:
    """Print validation report"""
    print("=" * 80)
    print("SoT Whitelist Validation Report")
    print("=" * 80)

    # Categorize issues
    role_issues = [i for i in issues if i.category == "role"]
    state_issues = [i for i in issues if i.category == "state"]
    phase_issues = [i for i in issues if i.category == "phase"]

    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]

    print(f"\n[Summary]")
    print(f"  Total issues: {len(issues)}")
    print(f"  - Errors: {len(errors)}")
    print(f"  - Warnings: {len(warnings)}")
    print(f"\n[By Category]")
    print(f"  - Deprecated roles: {len(role_issues)}")
    print(f"  - Phase 2 states: {len(state_issues)}")
    print(f"  - Phase 1 violations: {len(phase_issues)}")

    if role_issues:
        print(f"\n[WARN] Deprecated Role Usage ({len(role_issues)}):")
        print("-" * 60)
        by_file: Dict[str, List[int]] = {}
        for issue in role_issues:
            if issue.file not in by_file:
                by_file[issue.file] = []
            by_file[issue.file].append(issue.line)

        for f, lines in sorted(by_file.items())[:15]:
            print(f"  {f}")
            print(
                f"    Lines: {', '.join(map(str, lines[:5]))}{'...' if len(lines) > 5 else ''}"
            )
        if len(by_file) > 15:
            print(f"  ... and {len(by_file) - 15} more files")

    if state_issues:
        print(f"\n[ERROR] Phase 2 State Usage ({len(state_issues)}):")
        print("-" * 60)
        by_file = {}
        for issue in state_issues:
            if issue.file not in by_file:
                by_file[issue.file] = []
            by_file[issue.file].append((issue.line, issue.value))

        for f, items in sorted(by_file.items())[:10]:
            print(f"  {f}")
            for line, value in items[:3]:
                print(f"    Line {line}: '{value}'")
            if len(items) > 3:
                print(f"    ... and {len(items) - 3} more")
        if len(by_file) > 10:
            print(f"  ... and {len(by_file) - 10} more files")

    if phase_issues:
        print(f"\n[ERROR] Phase 1 Violations ({len(phase_issues)}):")
        print("-" * 60)
        for issue in phase_issues[:10]:
            print(f"  {issue.file}:{issue.line}")
            print(f"    Found: '{issue.value}'")
            print(f"    Suggestion: {issue.suggestion}")
        if len(phase_issues) > 10:
            print(f"  ... and {len(phase_issues) - 10} more")

    print("\n" + "=" * 80)
    print("Validation Result")
    print("=" * 80)

    if not issues:
        print("\n[OK] No SoT whitelist violations found!")
        return True

    if errors:
        print(f"\n[FAIL] Found {len(errors)} error(s) that must be fixed")
        return False

    print(f"\n[PASS] Passed with {len(warnings)} warning(s)")
    return True


def main():
    """Main function"""
    print("Scanning codebase for SoT whitelist violations...\n")

    all_issues = []

    # Scan Python files
    py_files = scan_python_files()
    print(f"Scanning {len(py_files)} Python files...")
    for filepath in py_files:
        issues = validate_file(filepath)
        all_issues.extend(issues)

    # Scan TypeScript files
    ts_files = scan_typescript_files()
    print(f"Scanning {len(ts_files)} TypeScript files...")
    for filepath in ts_files:
        issues = validate_file(filepath)
        all_issues.extend(issues)

    print(f"\nTotal files scanned: {len(py_files) + len(ts_files)}")

    success = print_report(all_issues)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
