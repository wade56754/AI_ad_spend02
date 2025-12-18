"""
验证器基础类型定义

提供所有验证器共用的数据结构和接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# 枚举类型
# ============================================================================

class IssueSeverity(str, Enum):
    """问题严重程度"""
    ERROR = "error"        # 必须修复，阻止通过
    WARNING = "warning"    # 建议修复，不阻止通过
    INFO = "info"          # 提示信息


class IssueCategory(str, Enum):
    """问题分类"""
    HALLUCINATION = "hallucination"     # AI 幻觉
    SYNTAX = "syntax"                   # 语法错误
    TYPE = "type"                       # 类型错误
    LINT = "lint"                       # 代码风格
    SOT_COMPLIANCE = "sot_compliance"   # SoT 合规
    INTEGRATION = "integration"         # 集成问题
    TEST = "test"                       # 测试失败
    SECURITY = "security"               # 安全问题


class VerifyStatus(str, Enum):
    """验证状态"""
    PASSED = "passed"      # 通过
    FIXED = "fixed"        # 已自动修复
    FAILED = "failed"      # 失败
    SKIPPED = "skipped"    # 跳过


# ============================================================================
# 数据类
# ============================================================================

@dataclass
class VerifyIssue:
    """
    验证问题

    记录验证过程中发现的问题
    """
    file_path: str
    line: int
    column: int
    category: IssueCategory
    severity: IssueSeverity
    code: str                    # 问题编码，如 "HALL-001"
    message: str                 # 问题描述
    suggestion: str              # 修复建议
    evidence: Optional[str] = None  # 证据/上下文
    auto_fixable: bool = False   # 是否可自动修复
    fix_applied: bool = False    # 是否已修复

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line": self.line,
            "column": self.column,
            "category": self.category.value,
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
            "suggestion": self.suggestion,
            "evidence": self.evidence,
            "auto_fixable": self.auto_fixable,
            "fix_applied": self.fix_applied,
        }


@dataclass
class VerifiedFile:
    """验证后的文件"""
    path: str
    original_content: str
    verified_content: str
    status: VerifyStatus
    issues: List[VerifyIssue] = field(default_factory=list)
    fixes_applied: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "status": self.status.value,
            "issues_count": len(self.issues),
            "fixes_applied": self.fixes_applied,
            "content": self.verified_content,
        }


@dataclass
class VerifyResult:
    """
    验证结果

    单个验证器的结果
    """
    passed: bool
    category: IssueCategory
    issues: List[VerifyIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    details: List[str] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return len([i for i in self.issues if i.severity == IssueSeverity.ERROR])

    @property
    def warning_count(self) -> int:
        return len([i for i in self.issues if i.severity == IssueSeverity.WARNING])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "category": self.category.value,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "issues": [i.to_dict() for i in self.issues],
            "metrics": self.metrics,
            "details": self.details,
        }


@dataclass
class VerifyContext:
    """
    验证上下文

    提供验证所需的上下文信息
    """
    # 项目信息
    project_root: Path
    requirement: str

    # SoT 定义
    valid_states: Set[str] = field(default_factory=set)
    valid_fields: Set[str] = field(default_factory=set)
    valid_error_codes: Set[str] = field(default_factory=set)
    valid_roles: Set[str] = field(default_factory=set)

    # 项目代码信息 (用于幻觉检测)
    existing_modules: Set[str] = field(default_factory=set)
    existing_functions: Set[str] = field(default_factory=set)
    existing_classes: Set[str] = field(default_factory=set)
    existing_endpoints: Set[str] = field(default_factory=set)

    # 外部依赖信息
    installed_packages: Set[str] = field(default_factory=set)

    # 配置
    strict_mode: bool = False
    auto_fix: bool = True
    max_fix_iterations: int = 3


# ============================================================================
# 基类
# ============================================================================

class BaseVerifier(ABC):
    """
    验证器基类

    所有验证器必须继承此类
    """

    def __init__(self, context: Optional[VerifyContext] = None):
        self.context = context
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    @abstractmethod
    def name(self) -> str:
        """验证器名称"""
        pass

    @property
    @abstractmethod
    def category(self) -> IssueCategory:
        """验证器分类"""
        pass

    @property
    def priority(self) -> int:
        """验证器优先级 (越小越优先)"""
        return 50

    @abstractmethod
    def verify(
        self,
        file_path: str,
        content: str,
        **kwargs
    ) -> VerifyResult:
        """
        执行验证

        Args:
            file_path: 文件路径
            content: 文件内容
            **kwargs: 额外参数

        Returns:
            验证结果
        """
        pass

    def can_auto_fix(self, issue: VerifyIssue) -> bool:
        """判断问题是否可自动修复"""
        return issue.auto_fixable

    def auto_fix(
        self,
        content: str,
        issues: List[VerifyIssue]
    ) -> tuple[str, int]:
        """
        自动修复问题

        Args:
            content: 原始内容
            issues: 问题列表

        Returns:
            (修复后内容, 修复数量)
        """
        # 默认不实现自动修复
        return content, 0


# ============================================================================
# 工具函数
# ============================================================================

def create_issue(
    file_path: str,
    line: int,
    category: IssueCategory,
    code: str,
    message: str,
    suggestion: str = "",
    severity: IssueSeverity = IssueSeverity.ERROR,
    column: int = 0,
    evidence: Optional[str] = None,
    auto_fixable: bool = False,
) -> VerifyIssue:
    """快速创建 VerifyIssue"""
    return VerifyIssue(
        file_path=file_path,
        line=line,
        column=column,
        category=category,
        severity=severity,
        code=code,
        message=message,
        suggestion=suggestion,
        evidence=evidence,
        auto_fixable=auto_fixable,
    )


def merge_results(results: List[VerifyResult]) -> Dict[str, Any]:
    """合并多个验证结果"""
    all_issues = []
    all_passed = True
    metrics = {}

    for result in results:
        all_issues.extend(result.issues)
        if not result.passed:
            all_passed = False
        metrics[result.category.value] = result.metrics

    return {
        "passed": all_passed,
        "total_issues": len(all_issues),
        "error_count": len([i for i in all_issues if i.severity == IssueSeverity.ERROR]),
        "warning_count": len([i for i in all_issues if i.severity == IssueSeverity.WARNING]),
        "issues": [i.to_dict() for i in all_issues],
        "metrics_by_category": metrics,
    }
