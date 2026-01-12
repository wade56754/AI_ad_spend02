"""
来源追溯验证器 (Source Tracing Verifier)

验证代码是否有正确的 SoT 来源标注

基准: AI_CODING_BEST_PRACTICES.md BP-05
版本: v1.0

来源标注格式:
    # SoT: {DOC}#{SECTION}

示例:
    # SoT: STATE_MACHINE.md#daily_report
    # SoT: DATA_SCHEMA.md#daily_reports.amount
    # SoT: API_SOT.md#POST /daily-reports
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import logging

from .base import (
    BaseVerifier,
    VerifyResult,
    VerifyIssue,
    VerifyContext,
    IssueCategory,
    IssueSeverity,
    create_issue,
)

logger = logging.getLogger(__name__)


# ============================================================================
# 配置常量
# ============================================================================

# 注释临近检测范围 (行数)
ANNOTATION_PROXIMITY_LINES = 5


# ============================================================================
# 来源追溯规则
# ============================================================================

# 必须标注来源的代码模式
SOURCE_REQUIRED_PATTERNS = {
    # 状态枚举定义
    "status_enum": {
        "pattern": r"class\s+\w*Status\w*\s*\([^)]*Enum[^)]*\):",
        "description": "状态枚举定义",
        "expected_sot": "STATE_MACHINE.md",
    },
    # 角色检查
    "role_check": {
        "pattern": r"require_role|check_role|has_role|allowed_roles",
        "description": "角色权限检查",
        "expected_sot": "AUTH_SPEC.md",
    },
    # 业务规则函数
    "business_rule": {
        "pattern": r"def\s+(validate_|check_|verify_|calculate_)",
        "description": "业务规则验证函数",
        "expected_sot": "BUSINESS_RULES.md",
    },
    # 错误码定义
    "error_code": {
        "pattern": r"class\s+\w*Error\w*Codes?\s*[:(]",
        "description": "错误码定义",
        "expected_sot": "ERROR_CODES_SOT.md",
    },
    # API 路由定义
    "api_route": {
        "pattern": r"@router\.(get|post|put|patch|delete)\s*\(",
        "description": "API 路由定义",
        "expected_sot": "API_SOT.md",
    },
    # 数据模型定义
    "data_model": {
        "pattern": r"class\s+\w+\s*\([^)]*(?:Base|BaseModel)[^)]*\):",
        "description": "数据模型定义",
        "expected_sot": "DATA_SCHEMA.md",
    },
}

# 有效的 SoT 文档列表
VALID_SOT_DOCS = {
    "MASTER.md",
    "STATE_MACHINE.md",
    "DATA_SCHEMA.md",
    "BUSINESS_RULES.md",
    "API_SOT.md",
    "ERROR_CODES_SOT.md",
    "AUTH_SPEC.md",
    "BR-RPT.md",
    "BR-FIN.md",
    "BR-ACCT.md",
    "BR-AUTH.md",
    "BR-DATA.md",
    "BR-PROJ.md",
    "BR-RECON.md",
    "BR-USER.md",
    "BR-PROFIT.md",
}


class SourceTracingVerifier(BaseVerifier):
    """
    来源追溯验证器

    检查代码是否有正确的 SoT 来源标注
    """

    @property
    def name(self) -> str:
        return "SourceTracingVerifier"

    @property
    def category(self) -> IssueCategory:
        return IssueCategory.SOT_COMPLIANCE

    @property
    def priority(self) -> int:
        return 35  # 在 SpecComplianceVerifier 之后

    def __init__(
        self,
        context: Optional[VerifyContext] = None,
        strict_mode: bool = False
    ):
        """
        初始化验证器

        Args:
            context: 验证上下文
            strict_mode: 严格模式，所有必须标注场景都报错
        """
        super().__init__(context)
        self.strict_mode = strict_mode

    def verify(
        self,
        file_path: str,
        content: str,
        **kwargs
    ) -> VerifyResult:
        """
        执行来源追溯验证

        检测:
        1. 必须标注场景是否有 SoT 注释
        2. SoT 注释格式是否正确
        3. SoT 引用的文档是否有效
        """
        issues: List[VerifyIssue] = []
        metrics: Dict[str, Any] = {
            "source_annotations_found": 0,
            "source_annotations_missing": 0,
            "invalid_annotations": 0,
            "patterns_checked": 0,
        }

        # 1. 提取所有 SoT 注释
        annotations = self._extract_sot_annotations(content)
        metrics["source_annotations_found"] = len(annotations)

        # 2. 验证注释格式
        for annotation, line, evidence in annotations:
            format_issues = self._validate_annotation_format(
                file_path, annotation, line, evidence
            )
            issues.extend(format_issues)
            if format_issues:
                metrics["invalid_annotations"] += 1

        # 3. 检查必须标注的场景
        for pattern_name, pattern_info in SOURCE_REQUIRED_PATTERNS.items():
            pattern = pattern_info["pattern"]
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            metrics["patterns_checked"] += len(matches)

            for match in matches:
                line = content[:match.start()].count('\n') + 1
                
                # 检查该位置是否有 SoT 注释
                if not self._has_nearby_annotation(content, match.start(), annotations):
                    severity = IssueSeverity.ERROR if self.strict_mode else IssueSeverity.WARNING
                    
                    issues.append(create_issue(
                        file_path=file_path,
                        line=line,
                        category=IssueCategory.SOT_COMPLIANCE,
                        code="SRC-001",
                        message=f"{pattern_info['description']}缺少来源标注",
                        suggestion=f"添加注释: # SoT: {pattern_info['expected_sot']}#<section>",
                        severity=severity,
                        evidence=match.group(0)[:50],
                        auto_fixable=False,
                    ))
                    metrics["source_annotations_missing"] += 1

        passed = not any(i.severity == IssueSeverity.ERROR for i in issues)

        return VerifyResult(
            passed=passed,
            category=self.category,
            issues=issues,
            metrics=metrics,
            details=[
                f"来源标注找到: {metrics['source_annotations_found']}",
                f"缺失标注: {metrics['source_annotations_missing']}",
                f"无效标注: {metrics['invalid_annotations']}",
            ],
        )

    def _extract_sot_annotations(
        self,
        content: str
    ) -> List[Tuple[str, int, str]]:
        """提取所有 SoT 注释"""
        annotations = []

        # 匹配 # SoT: DOC#SECTION 格式
        pattern = r'#\s*SoT:\s*([^\n]+)'
        for match in re.finditer(pattern, content):
            line = content[:match.start()].count('\n') + 1
            annotations.append((match.group(1).strip(), line, match.group(0)))

        return annotations

    def _validate_annotation_format(
        self,
        file_path: str,
        annotation: str,
        line: int,
        evidence: str
    ) -> List[VerifyIssue]:
        """验证注释格式"""
        issues = []

        # 格式应为: DOC#SECTION 或 DOC
        parts = annotation.split('#', 1)
        doc = parts[0].strip()

        # 验证文档名
        if not doc.endswith('.md'):
            # 可能省略了 .md
            doc_with_ext = doc + '.md'
            if doc_with_ext not in VALID_SOT_DOCS:
                issues.append(create_issue(
                    file_path=file_path,
                    line=line,
                    category=IssueCategory.SOT_COMPLIANCE,
                    code="SRC-002",
                    message=f"无效的 SoT 文档引用: '{doc}'",
                    suggestion=f"有效文档: {', '.join(sorted(VALID_SOT_DOCS)[:5])}...",
                    severity=IssueSeverity.WARNING,
                    evidence=evidence,
                ))
        elif doc not in VALID_SOT_DOCS:
            issues.append(create_issue(
                file_path=file_path,
                line=line,
                category=IssueCategory.SOT_COMPLIANCE,
                code="SRC-002",
                message=f"无效的 SoT 文档引用: '{doc}'",
                suggestion=f"有效文档: {', '.join(sorted(VALID_SOT_DOCS)[:5])}...",
                severity=IssueSeverity.WARNING,
                evidence=evidence,
            ))

        return issues

    def _has_nearby_annotation(
        self,
        content: str,
        position: int,
        annotations: List[Tuple[str, int, str]]
    ) -> bool:
        """检查指定位置附近是否有 SoT 注释"""
        # 计算位置对应的行号
        target_line = content[:position].count('\n') + 1

        # P1-4 fix: 同时检查前后各 ANNOTATION_PROXIMITY_LINES 行
        for _, line, _ in annotations:
            if target_line - ANNOTATION_PROXIMITY_LINES <= line <= target_line + ANNOTATION_PROXIMITY_LINES:
                return True

        return False


class HallucinationGuard:
    """
    防幻觉门禁

    集成 SpecComplianceVerifier 和 SourceTracingVerifier
    实现双重门禁验证

    基准: AI_CODING_BEST_PRACTICES.md BP-05
    """

    def __init__(
        self,
        context: Optional[VerifyContext] = None,
        strict_mode: bool = False
    ):
        """
        初始化门禁

        Args:
            context: 验证上下文
            strict_mode: 严格模式
        """
        self.context = context
        self.strict_mode = strict_mode

        # P0-3 fix: 延迟导入添加错误处理
        try:
            from .spec_compliance_verifier import SpecComplianceVerifier
            self.spec_verifier = SpecComplianceVerifier(context)
        except ImportError as e:
            logger.error(f"无法导入 SpecComplianceVerifier: {e}")
            self.spec_verifier = None
        
        self.source_verifier = SourceTracingVerifier(context, strict_mode)

    def verify(
        self,
        file_path: str,
        content: str,
        **kwargs
    ) -> VerifyResult:
        """
        执行双重门禁验证

        Gate 1: SoT 白名单验证 (SpecComplianceVerifier)
        Gate 2: 来源追溯检查 (SourceTracingVerifier)
        """
        all_issues: List[VerifyIssue] = []
        all_metrics: Dict[str, Any] = {}

        # P0-3 fix: 处理 spec_verifier 为 None 的情况
        spec_result = None
        if self.spec_verifier is not None:
            spec_result = self.spec_verifier.verify(file_path, content, **kwargs)
            all_issues.extend(spec_result.issues)
            all_metrics["gate1_spec_compliance"] = spec_result.metrics
        else:
            all_metrics["gate1_spec_compliance"] = {"skipped": True, "reason": "SpecComplianceVerifier 导入失败"}

        # Gate 2: 来源追溯检查
        source_result = self.source_verifier.verify(file_path, content, **kwargs)
        all_issues.extend(source_result.issues)
        all_metrics["gate2_source_tracing"] = source_result.metrics

        # 汇总结果
        blocking_issues = [i for i in all_issues if i.severity == IssueSeverity.ERROR]
        passed = len(blocking_issues) == 0

        # P0-3 fix: 处理 spec_verifier 为 None 的情况
        if spec_result is None:
            gate1_status = "SKIP"
        else:
            gate1_status = "PASS" if spec_result.passed else "FAIL"
        
        return VerifyResult(
            passed=passed,
            category=IssueCategory.HALLUCINATION,
            issues=all_issues,
            metrics=all_metrics,
            details=[
                f"Gate 1 (SoT 合规): {gate1_status}",
                f"Gate 2 (来源追溯): {'PASS' if source_result.passed else 'FAIL'}",
                f"阻塞问题: {len(blocking_issues)}",
                f"警告问题: {len(all_issues) - len(blocking_issues)}",
            ],
        )


# ============================================================================
# 便捷函数
# ============================================================================

def verify_source_tracing(
    file_path: str,
    content: str,
    strict_mode: bool = False,
    context: Optional[VerifyContext] = None
) -> VerifyResult:
    """
    来源追溯验证便捷函数

    Args:
        file_path: 文件路径
        content: 文件内容
        strict_mode: 严格模式
        context: 验证上下文

    Returns:
        验证结果
    """
    verifier = SourceTracingVerifier(context, strict_mode)
    return verifier.verify(file_path, content)


def verify_hallucination_guard(
    file_path: str,
    content: str,
    strict_mode: bool = False,
    context: Optional[VerifyContext] = None
) -> VerifyResult:
    """
    防幻觉门禁验证便捷函数

    Args:
        file_path: 文件路径
        content: 文件内容
        strict_mode: 严格模式
        context: 验证上下文

    Returns:
        验证结果
    """
    guard = HallucinationGuard(context, strict_mode)
    return guard.verify(file_path, content)
