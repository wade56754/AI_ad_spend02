"""
Claude Code Hooks Library

SoT 合规检查和进度跟踪支持库
"""
from .config import get_sot_versions, get_valid_roles, VALID_ROLES
from .compliance_checker import ComplianceChecker, Severity, check_code, is_compliant

__all__ = [
    "get_sot_versions",
    "get_valid_roles",
    "VALID_ROLES",
    "ComplianceChecker",
    "Severity",
    "check_code",
    "is_compliant",
]
