#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SoT 验证器 - 轻量级核心模块

整合 code_factory 的独特价值能力:
1. SoT 动态加载和版本验证
2. 角色/状态白名单管理
3. Phase 1/2 边界控制
4. 高风险模块识别

借鉴:
- OpenHands: 事件驱动架构
- MetaGPT: SOP 配置化
- Cline: Plan Mode 用户确认

Version: 1.0.0
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .config import (
    SOT_VERSIONS,
    VALID_ROLES,
    DEPRECATED_ROLES,
    ROLE_MAPPING,
    DAILY_REPORT_STATES,
    TOPUP_STATES,
    PHASE2_FORBIDDEN_STATES,
    PHASE2_FORBIDDEN_KEYWORDS,
    get_high_risk_modules,
    get_current_phase,
    get_config_value,
    load_yaml_config,
    PROJECT_ROOT,
)


# =============================================================================
# 验证事件 (借鉴 OpenHands 事件驱动)
# =============================================================================


class ValidationEvent(str, Enum):
    """验证事件类型"""

    SOT_CHECK_STARTED = "sot_check_started"
    SOT_VERSION_VALIDATED = "sot_version_validated"
    ROLE_VALIDATED = "role_validated"
    ROLE_DEPRECATED = "role_deprecated"
    STATE_VALIDATED = "state_validated"
    STATE_FORBIDDEN = "state_forbidden"
    PHASE_BOUNDARY_CHECKED = "phase_boundary_checked"
    PHASE_VIOLATION = "phase_violation"
    HIGH_RISK_DETECTED = "high_risk_detected"
    VALIDATION_PASSED = "validation_passed"
    VALIDATION_FAILED = "validation_failed"


# =============================================================================
# 验证结果
# =============================================================================


@dataclass
class ValidationIssue:
    """验证问题"""

    level: str  # error, warning, info
    code: str  # 规则编号
    message: str
    file: str = ""
    line: int = 0
    suggestion: str = ""


@dataclass
class ValidationResult:
    """验证结果"""

    success: bool
    issues: List[ValidationIssue]
    events: List[str]  # 事件记录
    metadata: Dict[str, Any]

    def add_issue(
        self,
        level: str,
        code: str,
        message: str,
        file: str = "",
        line: int = 0,
        suggestion: str = "",
    ) -> None:
        """添加问题"""
        self.issues.append(
            ValidationIssue(
                level=level,
                code=code,
                message=message,
                file=file,
                line=line,
                suggestion=suggestion,
            )
        )
        if level == "error":
            self.success = False

    def add_event(self, event: ValidationEvent, details: str = "") -> None:
        """记录事件"""
        entry = f"{event.value}"
        if details:
            entry += f": {details}"
        self.events.append(entry)

    def has_errors(self) -> bool:
        """是否有错误"""
        return any(i.level == "error" for i in self.issues)

    def has_warnings(self) -> bool:
        """是否有警告"""
        return any(i.level == "warning" for i in self.issues)

    def format_report(self) -> str:
        """格式化报告"""
        if not self.issues:
            return "✅ SoT validation passed"

        lines = [f"SoT Validation: {len(self.issues)} issue(s) found"]
        lines.append("")

        for issue in self.issues:
            icon = (
                "🔴"
                if issue.level == "error"
                else "🟡"
                if issue.level == "warning"
                else "💡"
            )
            location = f"{issue.file}:{issue.line}" if issue.file else "global"
            lines.append(f"{icon} [{issue.code}] {location}")
            lines.append(f"   {issue.message}")
            if issue.suggestion:
                lines.append(f"   → {issue.suggestion}")
            lines.append("")

        return "\n".join(lines)


# =============================================================================
# SoT 验证器核心
# =============================================================================


class SoTValidator:
    """
    SoT 验证器 - 轻量级核心

    整合 code_factory 的独特价值:
    - SoT 版本验证
    - 角色白名单验证
    - 状态机验证
    - Phase 边界控制
    - 高风险模块检测
    """

    def __init__(self):
        self.config = load_yaml_config()
        self.current_phase = get_current_phase()

    # ========== 角色验证 ==========

    def validate_roles(self, content: str, filepath: str = "") -> List[ValidationIssue]:
        """
        验证代码中的角色使用

        Args:
            content: 代码内容
            filepath: 文件路径

        Returns:
            问题列表
        """
        issues = []
        lines = content.split("\n")

        # 检测废弃角色
        for deprecated, replacement in ROLE_MAPPING.items():
            # 字符串形式
            pattern = rf'["\']({deprecated})["\']'
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[: match.start()].count("\n") + 1
                issues.append(
                    ValidationIssue(
                        level="warning",
                        code=f"ROLE-DEP-{deprecated.upper()}",
                        message=f"Deprecated role '{deprecated}' detected",
                        file=filepath,
                        line=line_num,
                        suggestion=f"Use '{replacement}' instead"
                        if replacement
                        else "Remove this role",
                    )
                )

            # 枚举形式
            enum_patterns = [
                rf"UserRole\.{deprecated.upper()}",
                rf"role\s*==\s*['\"]?{deprecated}['\"]?",
            ]
            for enum_pattern in enum_patterns:
                for match in re.finditer(enum_pattern, content, re.IGNORECASE):
                    line_num = content[: match.start()].count("\n") + 1
                    issues.append(
                        ValidationIssue(
                            level="warning",
                            code=f"ROLE-ENUM-{deprecated.upper()}",
                            message=f"Deprecated role enum '{match.group()}' detected",
                            file=filepath,
                            line=line_num,
                            suggestion=f"Use '{replacement}' instead"
                            if replacement
                            else "Remove this check",
                        )
                    )

        return issues

    # ========== 状态机验证 ==========

    def validate_states(
        self, content: str, filepath: str = ""
    ) -> List[ValidationIssue]:
        """
        验证状态机使用

        Args:
            content: 代码内容
            filepath: 文件路径

        Returns:
            问题列表
        """
        issues = []

        # Phase 1 禁用状态检测
        if self.current_phase == 1:
            for state in PHASE2_FORBIDDEN_STATES:
                pattern = rf'["\']({state})["\']'
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    line_num = content[: match.start()].count("\n") + 1
                    issues.append(
                        ValidationIssue(
                            level="error",
                            code=f"STATE-P2-{state.upper()}",
                            message=f"Phase 2 state '{state}' used in Phase 1",
                            file=filepath,
                            line=line_num,
                            suggestion="Phase 1 only allows: raw_submitted, trend_ok, final_confirmed",
                        )
                    )

        return issues

    # ========== Phase 边界控制 ==========

    def validate_phase_boundary(
        self, content: str, filepath: str = ""
    ) -> List[ValidationIssue]:
        """
        验证 Phase 1/2 边界

        Phase 1 禁止:
        - 自动拒绝/暂停/冻结
        - 强制审批
        - 惩罚机制

        Args:
            content: 代码内容
            filepath: 文件路径

        Returns:
            问题列表
        """
        issues = []

        if self.current_phase != 1:
            return issues

        # Phase 2 禁止关键词
        forbidden_patterns = [
            (r"auto[_-]?reject", "auto_reject", "Use warning/notification instead"),
            (r"auto[_-]?suspend", "auto_suspend", "Use highlight/flag instead"),
            (r"auto[_-]?block", "auto_block", "Phase 1 is soft enforcement only"),
            (r"auto[_-]?freeze", "auto_freeze", "Use warning notification instead"),
            (r"force[_-]?stop", "force_stop", "Use soft warning instead"),
            (
                r"forced?[_-]?approval",
                "forced_approval",
                "Approvals require human decision",
            ),
            (
                r"raise\s+HTTPException.*403.*Forbidden",
                "HTTP_403",
                "Phase 1 should not block access",
            ),
            (
                r"is_blocked\s*=\s*True",
                "is_blocked",
                "Phase 1 should not block entities",
            ),
        ]

        for pattern, keyword, suggestion in forbidden_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[: match.start()].count("\n") + 1
                issues.append(
                    ValidationIssue(
                        level="error",
                        code=f"PHASE1-{keyword.upper().replace('-', '_')}",
                        message=f"Phase 1 violation: '{keyword}' is forbidden",
                        file=filepath,
                        line=line_num,
                        suggestion=suggestion,
                    )
                )

        return issues

    # ========== 高风险模块检测 ==========

    def detect_high_risk(
        self, content: str, filepath: str = ""
    ) -> List[ValidationIssue]:
        """
        检测高风险模块

        Args:
            content: 代码内容
            filepath: 文件路径

        Returns:
            问题列表
        """
        issues = []

        for module in get_high_risk_modules():
            pattern = module.get("pattern", "")
            if not pattern:
                continue

            # 检查文件路径
            if re.search(pattern, filepath, re.IGNORECASE):
                issues.append(
                    ValidationIssue(
                        level="warning",
                        code=module.get("id", "RISK-UNKNOWN"),
                        message=f"High-risk module detected: {module.get('id')}",
                        file=filepath,
                        suggestion=module.get("reason", "Proceed with caution"),
                    )
                )

            # 检查内容中的关键模式
            if re.search(pattern, content, re.IGNORECASE):
                matches = list(re.finditer(pattern, content, re.IGNORECASE))
                if matches:
                    line_num = content[: matches[0].start()].count("\n") + 1
                    issues.append(
                        ValidationIssue(
                            level="warning",
                            code=module.get("id", "RISK-UNKNOWN"),
                            message=f"High-risk code pattern: {module.get('id')}",
                            file=filepath,
                            line=line_num,
                            suggestion=module.get("reason", "Proceed with caution"),
                        )
                    )

        return issues

    # ========== SoT 版本验证 ==========

    def validate_sot_versions(self) -> List[ValidationIssue]:
        """
        验证 SoT 文档版本

        Returns:
            问题列表
        """
        issues = []

        for doc_name, expected_version in SOT_VERSIONS.items():
            doc_path = PROJECT_ROOT / "docs" / "sot" / doc_name

            if not doc_path.exists():
                issues.append(
                    ValidationIssue(
                        level="warning",
                        code=f"SOT-MISSING-{doc_name.replace('.', '_').upper()}",
                        message=f"SoT document not found: {doc_name}",
                        file=str(doc_path),
                        suggestion="Ensure SoT documents are in place",
                    )
                )
                continue

            # 读取文档检查版本
            try:
                content = doc_path.read_text(encoding="utf-8")[:2000]  # 只读取开头
                # 查找版本号模式
                version_match = re.search(
                    r"[Vv]ersion[:\s]*(\d+\.\d+|\w+\.\d+)", content
                )
                if version_match:
                    actual_version = version_match.group(1)
                    if not actual_version.startswith("v"):
                        actual_version = f"v{actual_version}"

                    # 简单版本比较 (可以更复杂)
                    if actual_version != expected_version:
                        issues.append(
                            ValidationIssue(
                                level="info",
                                code=f"SOT-VERSION-{doc_name.replace('.', '_').upper()}",
                                message=f"SoT version mismatch: {doc_name} (expected {expected_version}, found {actual_version})",
                                file=str(doc_path),
                                suggestion="Update config to match actual SoT version",
                            )
                        )
            except Exception:
                pass

        return issues

    # ========== 综合验证 ==========

    def validate(
        self, content: str, filepath: str = "", check_sot_versions: bool = False
    ) -> ValidationResult:
        """
        综合验证

        Args:
            content: 代码内容
            filepath: 文件路径
            check_sot_versions: 是否检查 SoT 版本

        Returns:
            验证结果
        """
        result = ValidationResult(
            success=True,
            issues=[],
            events=[],
            metadata={"filepath": filepath, "phase": self.current_phase},
        )

        result.add_event(ValidationEvent.SOT_CHECK_STARTED, filepath)

        # 1. 角色验证
        role_issues = self.validate_roles(content, filepath)
        for issue in role_issues:
            result.issues.append(issue)
            if issue.level == "error":
                result.success = False
            result.add_event(
                ValidationEvent.ROLE_DEPRECATED
                if "deprecated" in issue.message.lower()
                else ValidationEvent.ROLE_VALIDATED,
                issue.message,
            )

        # 2. 状态机验证
        state_issues = self.validate_states(content, filepath)
        for issue in state_issues:
            result.issues.append(issue)
            if issue.level == "error":
                result.success = False
            result.add_event(ValidationEvent.STATE_FORBIDDEN, issue.message)

        # 3. Phase 边界验证
        phase_issues = self.validate_phase_boundary(content, filepath)
        for issue in phase_issues:
            result.issues.append(issue)
            if issue.level == "error":
                result.success = False
            result.add_event(ValidationEvent.PHASE_VIOLATION, issue.message)

        # 4. 高风险模块检测
        risk_issues = self.detect_high_risk(content, filepath)
        for issue in risk_issues:
            result.issues.append(issue)
            result.add_event(ValidationEvent.HIGH_RISK_DETECTED, issue.message)

        # 5. SoT 版本验证 (可选)
        if check_sot_versions:
            version_issues = self.validate_sot_versions()
            for issue in version_issues:
                result.issues.append(issue)
            result.add_event(ValidationEvent.SOT_VERSION_VALIDATED)

        # 最终事件
        if result.success:
            result.add_event(ValidationEvent.VALIDATION_PASSED)
        else:
            result.add_event(ValidationEvent.VALIDATION_FAILED)

        return result


# =============================================================================
# 便捷函数
# =============================================================================


def validate_code(content: str, filepath: str = "") -> ValidationResult:
    """
    验证代码合规性

    Args:
        content: 代码内容
        filepath: 文件路径

    Returns:
        验证结果
    """
    validator = SoTValidator()
    return validator.validate(content, filepath)


def is_sot_compliant(content: str, filepath: str = "") -> bool:
    """
    检查代码是否 SoT 合规

    Args:
        content: 代码内容
        filepath: 文件路径

    Returns:
        True if compliant (no errors)
    """
    result = validate_code(content, filepath)
    return result.success


def get_validation_report(content: str, filepath: str = "") -> str:
    """
    获取验证报告

    Args:
        content: 代码内容
        filepath: 文件路径

    Returns:
        格式化的报告字符串
    """
    result = validate_code(content, filepath)
    return result.format_report()
