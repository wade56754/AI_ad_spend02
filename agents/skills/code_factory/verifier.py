"""
代码验证器 - VERIFY 阶段实现

职责: 验证生成/适配的代码符合项目标准

验证层次 (借助 agents/skills/verifiers):
1. 幻觉检测 (HallucinationDetector)
2. AST 语法验证 (ASTVerifier)
3. SoT 合规验证 (SpecComplianceVerifier)
4. 集成验证 (IntegrationVerifier)
5. 测试验证 (TestVerifier)

来源:
- agents/skills/verifiers: 已实现的 5 层验证器
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

# 导入现有验证器
from agents.skills.verifiers import (
    EnhancedCodeVerifier,
    VerifierConfig,
    VerifyContext,
    VerifyStatus,
    VerifiedFile,
    IssueSeverity,
    create_verifier_from_project,
    quick_verify,
)

# v6.0: 使用 stub 实现
from .stubs import AdaptedFile


class VerifyDecision(Enum):
    """验证决策"""

    APPROVED = "approved"  # 通过
    FIX_APPLIED = "fix_applied"  # 已自动修复
    REJECTED = "rejected"  # 拒绝
    MANUAL_REVIEW = "manual_review"  # 需人工审查


@dataclass
class VerifyIssue:
    """验证问题 (简化版)"""

    code: str
    line: int
    message: str
    severity: str  # error, warning
    auto_fixable: bool = False
    fixed: bool = False


@dataclass
class FileVerifyResult:
    """单文件验证结果"""

    file_path: str
    decision: VerifyDecision
    issues: List[VerifyIssue] = field(default_factory=list)
    fixed_content: str = None
    original_content: str = None


@dataclass
class VerifyResult:
    """整体验证结果"""

    success: bool
    decision: VerifyDecision
    file_results: List[FileVerifyResult] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    report: str = ""
    error: str = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "decision": self.decision.value,
            "file_results": [
                {
                    "file_path": fr.file_path,
                    "decision": fr.decision.value,
                    "issues_count": len(fr.issues),
                    "issues": [
                        {
                            "code": i.code,
                            "line": i.line,
                            "message": i.message,
                            "severity": i.severity,
                            "fixed": i.fixed,
                        }
                        for i in fr.issues
                    ],
                }
                for fr in self.file_results
            ],
            "summary": self.summary,
            "error": self.error,
        }


class CodeVerifier:
    """
    代码验证器

    集成 agents/skills/verifiers 的验证能力，
    为代码工厂提供 VERIFY 阶段验证。

    验证流程:
    1. 创建验证上下文 (加载 SoT 定义)
    2. 对每个文件执行验证
    3. 尝试自动修复
    4. 生成验证报告
    5. 做出验证决策
    """

    def __init__(
        self,
        project_root: Path,
        requirement: str = "",
        auto_fix: bool = True,
        strict_mode: bool = False,
    ):
        self.project_root = Path(project_root)
        self.requirement = requirement
        self.auto_fix = auto_fix
        self.strict_mode = strict_mode

        # 配置
        self.config = VerifierConfig(
            enable_hallucination=True,
            enable_ast=True,
            enable_spec=True,
            enable_integration=True,
            enable_test=False,  # 测试验证默认关闭
            auto_fix=auto_fix,
            max_fix_iterations=3,
            strict_mode=strict_mode,
        )

        # 创建验证器
        self._verifier = create_verifier_from_project(
            str(self.project_root),
            requirement,
            self.config,
        )

    def verify(
        self,
        adapted_files: List[AdaptedFile],
        requirement: str = None,
    ) -> VerifyResult:
        """
        验证适配后的代码

        Args:
            adapted_files: 适配后的文件列表
            requirement: 原始需求 (可选，覆盖构造函数中的)

        Returns:
            VerifyResult
        """
        if not adapted_files:
            return VerifyResult(
                success=False,
                decision=VerifyDecision.REJECTED,
                error="没有需要验证的文件",
            )

        # 准备文件列表
        files_to_verify = [(af.file_path, af.content) for af in adapted_files]

        # 执行验证
        verified_files = self._verifier.verify_files(files_to_verify)

        # 转换结果
        file_results = []
        total_errors = 0
        total_warnings = 0
        total_fixes = 0

        for vf in verified_files:
            # 转换问题
            issues = [
                VerifyIssue(
                    code=vi.code,
                    line=vi.line,
                    message=vi.message,
                    severity="error"
                    if vi.severity == IssueSeverity.ERROR
                    else "warning",
                    auto_fixable=vi.auto_fixable,
                    fixed=vi.fix_applied,
                )
                for vi in vf.issues
            ]

            # 统计
            errors = len([i for i in issues if i.severity == "error"])
            warnings = len([i for i in issues if i.severity == "warning"])
            total_errors += errors
            total_warnings += warnings
            total_fixes += vf.fixes_applied

            # 确定单文件决策
            if vf.status == VerifyStatus.PASSED:
                decision = VerifyDecision.APPROVED
            elif vf.status == VerifyStatus.FIXED:
                decision = VerifyDecision.FIX_APPLIED
            elif vf.status == VerifyStatus.FAILED:
                if errors > 0:
                    decision = VerifyDecision.REJECTED
                else:
                    decision = VerifyDecision.MANUAL_REVIEW
            else:  # SKIPPED
                decision = VerifyDecision.APPROVED

            file_results.append(
                FileVerifyResult(
                    file_path=vf.path,
                    decision=decision,
                    issues=issues,
                    fixed_content=vf.verified_content
                    if vf.status == VerifyStatus.FIXED
                    else None,
                    original_content=vf.original_content,
                )
            )

        # 生成报告
        report = self._verifier.generate_report(verified_files, format="text")

        # 确定整体决策
        rejected_count = len(
            [fr for fr in file_results if fr.decision == VerifyDecision.REJECTED]
        )
        fixed_count = len(
            [fr for fr in file_results if fr.decision == VerifyDecision.FIX_APPLIED]
        )
        review_count = len(
            [fr for fr in file_results if fr.decision == VerifyDecision.MANUAL_REVIEW]
        )

        if rejected_count > 0:
            overall_decision = VerifyDecision.REJECTED
            success = False
        elif review_count > 0:
            overall_decision = VerifyDecision.MANUAL_REVIEW
            success = True  # 可以继续，但需要人工确认
        elif fixed_count > 0:
            overall_decision = VerifyDecision.FIX_APPLIED
            success = True
        else:
            overall_decision = VerifyDecision.APPROVED
            success = True

        # 汇总
        summary = {
            "total_files": len(file_results),
            "approved": len(
                [fr for fr in file_results if fr.decision == VerifyDecision.APPROVED]
            ),
            "fixed": fixed_count,
            "rejected": rejected_count,
            "manual_review": review_count,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "total_fixes": total_fixes,
        }

        return VerifyResult(
            success=success,
            decision=overall_decision,
            file_results=file_results,
            summary=summary,
            report=report,
        )

    def verify_single(
        self,
        file_path: str,
        content: str,
    ) -> FileVerifyResult:
        """
        验证单个文件 (快速方法)

        Args:
            file_path: 文件路径
            content: 文件内容

        Returns:
            FileVerifyResult
        """
        result = quick_verify(file_path, content, str(self.project_root))

        issues = [
            VerifyIssue(
                code=e["code"],
                line=e["line"],
                message=e["message"],
                severity="error",
            )
            for e in result["errors"]
        ] + [
            VerifyIssue(
                code=w["code"],
                line=w["line"],
                message=w["message"],
                severity="warning",
            )
            for w in result["warnings"]
        ]

        if result["passed"]:
            if result["fixes_applied"] > 0:
                decision = VerifyDecision.FIX_APPLIED
            else:
                decision = VerifyDecision.APPROVED
        else:
            if len(result["errors"]) > 0:
                decision = VerifyDecision.REJECTED
            else:
                decision = VerifyDecision.MANUAL_REVIEW

        return FileVerifyResult(
            file_path=file_path,
            decision=decision,
            issues=issues,
            fixed_content=result["verified_content"]
            if result["fixes_applied"] > 0
            else None,
            original_content=content,
        )

    def get_fixed_files(self, verify_result: VerifyResult) -> List[AdaptedFile]:
        """
        从验证结果中提取已修复的文件

        Args:
            verify_result: 验证结果

        Returns:
            修复后的 AdaptedFile 列表
        """
        fixed_files = []

        for fr in verify_result.file_results:
            if fr.decision == VerifyDecision.FIX_APPLIED and fr.fixed_content:
                fixed_files.append(
                    AdaptedFile(
                        file_path=fr.file_path,
                        content=fr.fixed_content,
                        adaptations=[],  # 验证修复不记录适配历史
                        source_attribution=None,
                    )
                )
            elif fr.decision == VerifyDecision.APPROVED:
                # 原样保留
                fixed_files.append(
                    AdaptedFile(
                        file_path=fr.file_path,
                        content=fr.original_content or "",
                        adaptations=[],
                        source_attribution=None,
                    )
                )

        return fixed_files
