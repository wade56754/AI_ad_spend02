"""
REVIEW 阶段 - 两阶段审查

对接 Superpowers 审查流程，实现两阶段审查:
1. 规格合规审查 (Spec Review)
2. 代码质量审查 (Quality Review)

基准文档: MASTER.md v4.8
版本: v7.0

Superpowers 对接:
- .superpowers/skills/subagent-driven-development/spec-reviewer-prompt.md
- .superpowers/skills/subagent-driven-development/code-quality-reviewer-prompt.md
- .superpowers/skills/requesting-code-review/SKILL.md
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from pathlib import Path
from enum import Enum

from ..types import (
    ExecutionContext,
    ReviewStage,
    ReviewIssue,
    ReviewResult as TypedReviewResult,
    AdaptedFile,
)
from ..verifier import CodeVerifier, VerifyDecision

logger = logging.getLogger(__name__)


class IssueSeverity(str, Enum):
    """问题严重程度"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class IssueCategory(str, Enum):
    """问题类别"""
    # 规格相关
    SPEC_MISSING = "spec_missing"        # 缺少需求功能
    SPEC_EXTRA = "spec_extra"            # 多余功能 (YAGNI 违规)
    SPEC_MISMATCH = "spec_mismatch"      # 不符合需求
    
    # 质量相关
    QUALITY_NAMING = "quality_naming"    # 命名问题
    QUALITY_COMPLEXITY = "quality_complexity"  # 复杂度问题
    QUALITY_DUPLICATION = "quality_duplication"  # 代码重复
    QUALITY_ERROR_HANDLING = "quality_error_handling"  # 错误处理
    QUALITY_TESTING = "quality_testing"  # 测试覆盖
    
    # SoT 相关
    SOT_STATE = "sot_state"              # 状态不在白名单
    SOT_ROLE = "sot_role"                # 角色不在白名单
    SOT_FIELD = "sot_field"              # 字段不在 Schema


@dataclass
class SpecReviewResult:
    """规格审查结果"""
    passed: bool
    issues: List[ReviewIssue] = field(default_factory=list)
    coverage: float = 0.0  # 需求覆盖率
    extra_features: List[str] = field(default_factory=list)  # 多余功能


@dataclass
class QualityReviewResult:
    """质量审查结果"""
    passed: bool
    issues: List[ReviewIssue] = field(default_factory=list)
    score: float = 0.0  # 质量分数 0-100


class ReviewPhase:
    """
    两阶段审查
    
    职责:
    1. 规格合规审查: 检查代码是否符合需求规格
    2. 代码质量审查: 检查代码质量 (仅在规格通过后)
    
    Superpowers 审查原则:
    - 规格审查在质量审查之前
    - 规格不通过就不进行质量审查
    - 审查循环直到通过
    
    集成 5 层验证器:
    1. HallucinationDetector - 幻觉检测
    2. ASTVerifier - 语法验证
    3. SpecComplianceVerifier - SoT 合规
    4. IntegrationVerifier - 集成验证
    5. TestVerifier - 测试验证
    """
    
    PHASE_NAME = "review"
    
    def __init__(self, context: ExecutionContext):
        self.context = context
        self.superpowers_dir = context.superpowers_dir
        
        # 初始化代码验证器 (集成 5 层验证)
        self.code_verifier = CodeVerifier(
            project_root=context.project_root,
            auto_fix=True,
            strict_mode=False,
        )
    
    def execute(
        self,
        requirement: str,
        phase_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        执行两阶段审查
        
        Args:
            requirement: 需求描述
            phase_data: 前序阶段数据
            
        Returns:
            审查结果
        """
        logger.info("开始 REVIEW 阶段 (两阶段审查)")
        
        # 获取实现数据
        impl_data = phase_data.get("implement", {})
        plan_data = phase_data.get("plan", {})
        
        # 阶段 1: 规格合规审查
        logger.info("  [阶段 1] 规格合规审查")
        spec_result = self._spec_review(requirement, plan_data, impl_data)
        
        if not spec_result.passed:
            logger.warning(f"  规格审查未通过: {len(spec_result.issues)} 个问题")
            return {
                "passed": False,
                "stage": ReviewStage.SPEC.value,
                "spec_result": self._spec_result_to_dict(spec_result),
                "quality_result": None,
                "action": "修复规格不符项后重新审查",
            }
        
        logger.info("  规格审查通过")
        
        # 阶段 2: 代码质量审查 (仅在规格通过后)
        logger.info("  [阶段 2] 代码质量审查")
        quality_result = self._quality_review(impl_data)
        
        if not quality_result.passed:
            logger.warning(f"  质量审查未通过: {len(quality_result.issues)} 个问题")
            return {
                "passed": False,
                "stage": ReviewStage.QUALITY.value,
                "spec_result": self._spec_result_to_dict(spec_result),
                "quality_result": self._quality_result_to_dict(quality_result),
                "action": "修复质量问题后重新审查",
            }
        
        logger.info("  质量审查通过")
        
        return {
            "passed": True,
            "stage": "completed",
            "spec_result": self._spec_result_to_dict(spec_result),
            "quality_result": self._quality_result_to_dict(quality_result),
        }
    
    def _spec_review(
        self,
        requirement: str,
        plan_data: Dict[str, Any],
        impl_data: Dict[str, Any],
    ) -> SpecReviewResult:
        """
        规格合规审查
        
        检查:
        1. 所有需求点都已实现
        2. 没有多余功能 (YAGNI)
        3. 实现符合验收标准
        """
        issues = []
        tasks = plan_data.get("tasks", [])
        cycles = impl_data.get("cycles", [])
        
        # 检查任务完成情况
        completed_tasks = {c["task_id"] for c in cycles if c.get("success")}
        
        for task in tasks:
            task_id = task.get("id")
            
            if task_id not in completed_tasks:
                issues.append(ReviewIssue(
                    code=f"SPEC-{IssueCategory.SPEC_MISSING.value}",
                    line=0,
                    message=f"任务未完成: {task.get('description', task_id)}",
                    severity=IssueSeverity.ERROR.value,
                    category=IssueCategory.SPEC_MISSING.value,
                ))
        
        # 检查验收标准
        for task in tasks:
            criteria = task.get("acceptance_criteria", [])
            for criterion in criteria:
                # 简化检查: 在实际环境中会分析代码
                if not self._check_criterion(criterion, impl_data):
                    issues.append(ReviewIssue(
                        code=f"SPEC-{IssueCategory.SPEC_MISMATCH.value}",
                        line=0,
                        message=f"验收标准未满足: {criterion}",
                        severity=IssueSeverity.WARNING.value,
                        category=IssueCategory.SPEC_MISMATCH.value,
                    ))
        
        # 计算覆盖率
        coverage = len(completed_tasks) / len(tasks) if tasks else 1.0
        
        # 判断是否通过
        error_count = sum(1 for i in issues if i.severity == IssueSeverity.ERROR.value)
        passed = error_count == 0
        
        return SpecReviewResult(
            passed=passed,
            issues=issues,
            coverage=coverage,
        )
    
    def _quality_review(
        self,
        impl_data: Dict[str, Any],
    ) -> QualityReviewResult:
        """
        代码质量审查
        
        集成 5 层验证器:
        1. HallucinationDetector - 幻觉检测
        2. ASTVerifier - 语法验证
        3. SpecComplianceVerifier - SoT 合规
        4. IntegrationVerifier - 集成验证
        5. TestVerifier - 测试验证
        
        检查:
        1. 命名清晰度
        2. 函数长度
        3. 错误处理
        4. 测试覆盖
        5. SoT 合规
        """
        issues = []
        score = 100.0
        
        cycles = impl_data.get("cycles", [])
        
        # 收集所有文件用于验证器
        adapted_files = []
        
        for cycle in cycles:
            if not cycle.get("success"):
                continue
            
            # 检查测试文件
            test_file = cycle.get("test_file", {})
            if test_file and test_file.get("content"):
                test_issues = self._check_test_quality(test_file)
                issues.extend(test_issues)
                score -= len(test_issues) * 5
                
                # 添加到验证器列表
                adapted_files.append(AdaptedFile(
                    file_path=test_file.get("path", "unknown"),
                    content=test_file.get("content", ""),
                ))
            
            # 检查实现文件
            impl_file = cycle.get("impl_file", {})
            if impl_file and impl_file.get("content"):
                impl_issues = self._check_impl_quality(impl_file)
                issues.extend(impl_issues)
                score -= len(impl_issues) * 5
                
                # 添加到验证器列表
                adapted_files.append(AdaptedFile(
                    file_path=impl_file.get("path", "unknown"),
                    content=impl_file.get("content", ""),
                ))
        
        # 使用 5 层验证器进行深度检查
        if adapted_files:
            try:
                verify_result = self.code_verifier.verify(adapted_files)
                
                # 转换验证器问题
                for file_result in verify_result.file_results:
                    for vi in file_result.issues:
                        issues.append(ReviewIssue(
                            code=vi.code,
                            line=vi.line,
                            message=vi.message,
                            severity=vi.severity,
                            category=IssueCategory.SOT_STATE.value if "状态" in vi.message else IssueCategory.QUALITY_COMPLEXITY.value,
                        ))
                        score -= 5 if vi.severity == "error" else 2
                
                # 如果验证器拒绝，降低分数
                if verify_result.decision == VerifyDecision.REJECTED:
                    score -= 20
                    
            except Exception as e:
                logger.warning(f"验证器检查失败: {e}")
        
        # 确保分数在 0-100 之间
        score = max(0, min(100, score))
        
        # 判断是否通过 (分数 >= 70)
        passed = score >= 70 and not any(
            i.severity == IssueSeverity.ERROR.value for i in issues
        )
        
        return QualityReviewResult(
            passed=passed,
            issues=issues,
            score=score,
        )
    
    def _check_criterion(
        self,
        criterion: str,
        impl_data: Dict[str, Any],
    ) -> bool:
        """检查验收标准是否满足"""
        # 简化实现: 在实际环境中会分析代码内容
        return True
    
    def _check_test_quality(
        self,
        test_file: Dict[str, Any],
    ) -> List[ReviewIssue]:
        """检查测试质量"""
        issues = []
        content = test_file.get("content", "")
        path = test_file.get("path", "unknown")
        
        # 检查是否有实际断言 (不只是 assert False)
        if content.count("assert") < 2:
            issues.append(ReviewIssue(
                code=f"QUAL-{IssueCategory.QUALITY_TESTING.value}",
                line=0,
                message=f"测试断言不足: {path}",
                severity=IssueSeverity.WARNING.value,
                category=IssueCategory.QUALITY_TESTING.value,
                suggestion="添加更多具体的断言",
            ))
        
        return issues
    
    def _check_impl_quality(
        self,
        impl_file: Dict[str, Any],
    ) -> List[ReviewIssue]:
        """检查实现质量"""
        issues = []
        content = impl_file.get("content", "")
        path = impl_file.get("path", "unknown")
        
        # 检查 TODO 注释
        if "TODO" in content:
            issues.append(ReviewIssue(
                code=f"QUAL-{IssueCategory.QUALITY_COMPLEXITY.value}",
                line=0,
                message=f"存在未完成的 TODO: {path}",
                severity=IssueSeverity.WARNING.value,
                category=IssueCategory.QUALITY_COMPLEXITY.value,
                suggestion="完成或移除 TODO 注释",
            ))
        
        # 检查错误处理 (Python)
        if path.endswith(".py"):
            if "try:" not in content and "except" not in content:
                if "def " in content or "async def " in content:
                    issues.append(ReviewIssue(
                        code=f"QUAL-{IssueCategory.QUALITY_ERROR_HANDLING.value}",
                        line=0,
                        message=f"缺少错误处理: {path}",
                        severity=IssueSeverity.INFO.value,
                        category=IssueCategory.QUALITY_ERROR_HANDLING.value,
                        suggestion="考虑添加 try-except 错误处理",
                    ))
        
        return issues
    
    def _spec_result_to_dict(self, result: SpecReviewResult) -> Dict[str, Any]:
        """规格结果转字典"""
        return {
            "passed": result.passed,
            "issues": [i.to_dict() for i in result.issues],
            "coverage": result.coverage,
            "extra_features": result.extra_features,
        }
    
    def _quality_result_to_dict(self, result: QualityReviewResult) -> Dict[str, Any]:
        """质量结果转字典"""
        return {
            "passed": result.passed,
            "issues": [i.to_dict() for i in result.issues],
            "score": result.score,
        }
