"""
增强版代码验证器 - 主编排器

统一协调所有验证层，按优先级执行验证流程:
1. HallucinationDetector - 幻觉检测 (优先级 10)
2. ASTVerifier - 语法验证 (优先级 20)
3. SpecComplianceVerifier - SoT 合规 (优先级 30)
4. IntegrationVerifier - 集成验证 (优先级 40)
5. TestVerifier - 测试验证 (优先级 50)

支持功能:
- 自动修复 (auto_fix)
- 迭代验证 (max_iterations)
- 选择性跳过 (skip_verifiers)
- 详细报告生成
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type

from .base import (
    BaseVerifier,
    IssueCategory,
    IssueSeverity,
    VerifyContext,
    VerifyIssue,
    VerifyResult,
    VerifiedFile,
    VerifyStatus,
    merge_results,
)
from .hallucination_detector import HallucinationDetector
from .ast_verifier import ASTVerifier
from .spec_compliance_verifier import SpecComplianceVerifier
from .integration_verifier import IntegrationVerifier
from .test_verifier import TestVerifier


logger = logging.getLogger(__name__)


# ============================================================================
# 配置
# ============================================================================

@dataclass
class VerifierConfig:
    """验证器配置"""
    # 启用的验证器
    enable_hallucination: bool = True
    enable_ast: bool = True
    enable_spec: bool = True
    enable_integration: bool = True
    enable_test: bool = False  # 测试验证默认关闭

    # 自动修复设置
    auto_fix: bool = True
    max_fix_iterations: int = 3

    # 严格模式
    strict_mode: bool = False  # 严格模式下 WARNING 也算失败

    # 运行测试
    run_tests: bool = False

    # 跳过文件模式
    skip_patterns: List[str] = field(default_factory=lambda: [
        "**/test_*.py",
        "**/*_test.py",
        "**/migrations/**",
        "**/alembic/**",
        "**/__pycache__/**",
    ])


# ============================================================================
# 主验证器
# ============================================================================

class EnhancedCodeVerifier:
    """
    增强版代码验证器

    协调多个验证层，提供统一的验证接口

    使用示例:
    ```python
    # 创建上下文
    context = VerifyContext(
        project_root=Path("/path/to/project"),
        requirement="实现用户注册 API",
        valid_states={"pending", "active", "disabled"},
        valid_roles={"admin", "user"},
    )

    # 创建验证器
    verifier = EnhancedCodeVerifier(context)

    # 验证单个文件
    result = verifier.verify_file("path/to/file.py", file_content)

    # 验证多个文件
    results = verifier.verify_files([
        ("file1.py", content1),
        ("file2.py", content2),
    ])

    # 获取报告
    report = verifier.generate_report(results)
    ```
    """

    def __init__(
        self,
        context: Optional[VerifyContext] = None,
        config: Optional[VerifierConfig] = None,
    ):
        self.context = context
        self.config = config or VerifierConfig()
        self._verifiers: List[BaseVerifier] = []
        self._initialize_verifiers()

    def _initialize_verifiers(self):
        """初始化验证器列表"""
        self._verifiers = []

        if self.config.enable_hallucination:
            self._verifiers.append(HallucinationDetector(self.context))

        if self.config.enable_ast:
            self._verifiers.append(ASTVerifier(self.context))

        if self.config.enable_spec:
            self._verifiers.append(SpecComplianceVerifier(self.context))

        if self.config.enable_integration:
            self._verifiers.append(IntegrationVerifier(self.context))

        if self.config.enable_test:
            self._verifiers.append(TestVerifier(self.context))

        # 按优先级排序
        self._verifiers.sort(key=lambda v: v.priority)

        logger.info(f"已初始化 {len(self._verifiers)} 个验证器: "
                   f"{[v.name for v in self._verifiers]}")

    def verify_file(
        self,
        file_path: str,
        content: str,
        **kwargs
    ) -> VerifiedFile:
        """
        验证单个文件

        Args:
            file_path: 文件路径
            content: 文件内容
            **kwargs: 传递给验证器的额外参数

        Returns:
            VerifiedFile 对象
        """
        logger.info(f"开始验证文件: {file_path}")

        # 检查是否应跳过
        if self._should_skip(file_path):
            logger.info(f"跳过文件: {file_path}")
            return VerifiedFile(
                path=file_path,
                original_content=content,
                verified_content=content,
                status=VerifyStatus.SKIPPED,
            )

        all_issues: List[VerifyIssue] = []
        current_content = content
        total_fixes = 0
        iteration = 0

        # 迭代验证和修复
        while iteration < self.config.max_fix_iterations:
            iteration += 1
            logger.debug(f"验证迭代 {iteration}/{self.config.max_fix_iterations}")

            iteration_issues: List[VerifyIssue] = []
            fixes_this_iteration = 0

            # 运行所有验证器
            for verifier in self._verifiers:
                try:
                    result = verifier.verify(
                        file_path,
                        current_content,
                        run_tests=self.config.run_tests,
                        **kwargs
                    )

                    iteration_issues.extend(result.issues)

                    logger.debug(
                        f"[{verifier.name}] 通过={result.passed}, "
                        f"问题={len(result.issues)}"
                    )

                except Exception as e:
                    logger.error(f"验证器 {verifier.name} 执行失败: {e}")
                    iteration_issues.append(VerifyIssue(
                        file_path=file_path,
                        line=0,
                        column=0,
                        category=IssueCategory.INTEGRATION,
                        severity=IssueSeverity.ERROR,
                        code="VER-ERR",
                        message=f"验证器执行失败: {verifier.name}",
                        suggestion=str(e),
                    ))

            # 尝试自动修复
            if self.config.auto_fix:
                current_content, fixes = self._apply_fixes(
                    current_content, iteration_issues
                )
                fixes_this_iteration = fixes
                total_fixes += fixes

            # 收集未修复的问题
            unfixed_issues = [i for i in iteration_issues if not i.fix_applied]
            all_issues = unfixed_issues

            # 如果没有修复或没有可修复的问题，结束迭代
            if fixes_this_iteration == 0:
                break

            logger.info(f"迭代 {iteration}: 修复了 {fixes_this_iteration} 个问题")

        # 确定最终状态
        error_count = len([i for i in all_issues if i.severity == IssueSeverity.ERROR])
        warning_count = len([i for i in all_issues if i.severity == IssueSeverity.WARNING])

        if error_count > 0:
            status = VerifyStatus.FAILED
        elif self.config.strict_mode and warning_count > 0:
            status = VerifyStatus.FAILED
        elif total_fixes > 0:
            status = VerifyStatus.FIXED
        else:
            status = VerifyStatus.PASSED

        logger.info(
            f"验证完成: {file_path}, 状态={status.value}, "
            f"错误={error_count}, 警告={warning_count}, 修复={total_fixes}"
        )

        return VerifiedFile(
            path=file_path,
            original_content=content,
            verified_content=current_content,
            status=status,
            issues=all_issues,
            fixes_applied=total_fixes,
        )

    def verify_files(
        self,
        files: List[tuple[str, str]],
        **kwargs
    ) -> List[VerifiedFile]:
        """
        验证多个文件

        Args:
            files: [(file_path, content), ...] 列表
            **kwargs: 传递给验证器的额外参数

        Returns:
            VerifiedFile 列表
        """
        results = []

        for file_path, content in files:
            result = self.verify_file(file_path, content, **kwargs)
            results.append(result)

        return results

    def _should_skip(self, file_path: str) -> bool:
        """检查是否应跳过文件"""
        path = Path(file_path)

        for pattern in self.config.skip_patterns:
            if path.match(pattern):
                return True

        return False

    def _apply_fixes(
        self,
        content: str,
        issues: List[VerifyIssue]
    ) -> tuple[str, int]:
        """应用自动修复"""
        total_fixes = 0
        current_content = content

        # 按验证器分组
        issues_by_category: Dict[IssueCategory, List[VerifyIssue]] = {}
        for issue in issues:
            if issue.auto_fixable and not issue.fix_applied:
                if issue.category not in issues_by_category:
                    issues_by_category[issue.category] = []
                issues_by_category[issue.category].append(issue)

        # 使用对应验证器修复
        for verifier in self._verifiers:
            if verifier.category in issues_by_category:
                category_issues = issues_by_category[verifier.category]
                current_content, fixes = verifier.auto_fix(
                    current_content, category_issues
                )
                total_fixes += fixes

        return current_content, total_fixes

    def generate_report(
        self,
        results: List[VerifiedFile],
        format: str = "text"
    ) -> str:
        """
        生成验证报告

        Args:
            results: VerifiedFile 列表
            format: 报告格式 ("text", "json", "markdown")

        Returns:
            报告字符串
        """
        if format == "json":
            return self._generate_json_report(results)
        elif format == "markdown":
            return self._generate_markdown_report(results)
        else:
            return self._generate_text_report(results)

    def _generate_text_report(self, results: List[VerifiedFile]) -> str:
        """生成文本报告"""
        lines = [
            "=" * 60,
            "代码验证报告",
            f"生成时间: {datetime.now().isoformat()}",
            "=" * 60,
            "",
        ]

        # 汇总统计
        total_files = len(results)
        passed = len([r for r in results if r.status == VerifyStatus.PASSED])
        fixed = len([r for r in results if r.status == VerifyStatus.FIXED])
        failed = len([r for r in results if r.status == VerifyStatus.FAILED])
        skipped = len([r for r in results if r.status == VerifyStatus.SKIPPED])

        lines.extend([
            "【汇总】",
            f"  总文件数: {total_files}",
            f"  通过: {passed}",
            f"  已修复: {fixed}",
            f"  失败: {failed}",
            f"  跳过: {skipped}",
            "",
        ])

        # 详细问题
        all_issues = []
        for result in results:
            all_issues.extend(result.issues)

        if all_issues:
            errors = [i for i in all_issues if i.severity == IssueSeverity.ERROR]
            warnings = [i for i in all_issues if i.severity == IssueSeverity.WARNING]

            lines.extend([
                f"【问题统计】",
                f"  错误: {len(errors)}",
                f"  警告: {len(warnings)}",
                "",
            ])

            if errors:
                lines.append("【错误列表】")
                for issue in errors:
                    lines.append(
                        f"  [{issue.code}] {issue.file_path}:{issue.line} - {issue.message}"
                    )
                lines.append("")

            if warnings:
                lines.append("【警告列表】")
                for issue in warnings:
                    lines.append(
                        f"  [{issue.code}] {issue.file_path}:{issue.line} - {issue.message}"
                    )
                lines.append("")

        # 每个文件详情
        lines.append("【文件详情】")
        for result in results:
            status_emoji = {
                VerifyStatus.PASSED: "[PASS]",
                VerifyStatus.FIXED: "[FIX]",
                VerifyStatus.FAILED: "[FAIL]",
                VerifyStatus.SKIPPED: "[SKIP]",
            }
            lines.append(
                f"  {status_emoji[result.status]} {result.path} "
                f"(问题: {len(result.issues)}, 修复: {result.fixes_applied})"
            )

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    def _generate_json_report(self, results: List[VerifiedFile]) -> str:
        """生成 JSON 报告"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_files": len(results),
                "passed": len([r for r in results if r.status == VerifyStatus.PASSED]),
                "fixed": len([r for r in results if r.status == VerifyStatus.FIXED]),
                "failed": len([r for r in results if r.status == VerifyStatus.FAILED]),
                "skipped": len([r for r in results if r.status == VerifyStatus.SKIPPED]),
            },
            "files": [r.to_dict() for r in results],
            "all_issues": [],
        }

        for result in results:
            for issue in result.issues:
                report["all_issues"].append(issue.to_dict())

        return json.dumps(report, indent=2, ensure_ascii=False)

    def _generate_markdown_report(self, results: List[VerifiedFile]) -> str:
        """生成 Markdown 报告"""
        lines = [
            "# 代码验证报告",
            "",
            f"> 生成时间: {datetime.now().isoformat()}",
            "",
            "## 汇总",
            "",
            "| 指标 | 数量 |",
            "|------|------|",
            f"| 总文件数 | {len(results)} |",
            f"| 通过 | {len([r for r in results if r.status == VerifyStatus.PASSED])} |",
            f"| 已修复 | {len([r for r in results if r.status == VerifyStatus.FIXED])} |",
            f"| 失败 | {len([r for r in results if r.status == VerifyStatus.FAILED])} |",
            f"| 跳过 | {len([r for r in results if r.status == VerifyStatus.SKIPPED])} |",
            "",
        ]

        # 收集所有问题
        all_issues = []
        for result in results:
            all_issues.extend(result.issues)

        errors = [i for i in all_issues if i.severity == IssueSeverity.ERROR]
        warnings = [i for i in all_issues if i.severity == IssueSeverity.WARNING]

        if errors:
            lines.extend([
                "## 错误",
                "",
                "| 代码 | 文件:行 | 描述 |",
                "|------|---------|------|",
            ])
            for issue in errors:
                lines.append(
                    f"| `{issue.code}` | `{issue.file_path}:{issue.line}` | {issue.message} |"
                )
            lines.append("")

        if warnings:
            lines.extend([
                "## 警告",
                "",
                "| 代码 | 文件:行 | 描述 |",
                "|------|---------|------|",
            ])
            for issue in warnings:
                lines.append(
                    f"| `{issue.code}` | `{issue.file_path}:{issue.line}` | {issue.message} |"
                )
            lines.append("")

        # 文件详情
        lines.extend([
            "## 文件详情",
            "",
        ])

        for result in results:
            status_emoji = {
                VerifyStatus.PASSED: ":white_check_mark:",
                VerifyStatus.FIXED: ":wrench:",
                VerifyStatus.FAILED: ":x:",
                VerifyStatus.SKIPPED: ":fast_forward:",
            }
            lines.append(
                f"- {status_emoji[result.status]} `{result.path}` - "
                f"问题: {len(result.issues)}, 修复: {result.fixes_applied}"
            )

        return "\n".join(lines)


# ============================================================================
# 便捷函数
# ============================================================================

def create_verifier_from_project(
    project_root: str,
    requirement: str = "",
    config: Optional[VerifierConfig] = None,
) -> EnhancedCodeVerifier:
    """
    从项目路径创建验证器

    自动加载项目的 SoT 定义
    """
    root = Path(project_root)

    # 尝试加载 SoT 定义
    valid_states = set()
    valid_roles = set()
    valid_error_codes = set()

    # 从 STATE_MACHINE.md 加载状态
    state_machine_file = root / "docs" / "2.sot" / "STATE_MACHINE.md"
    if state_machine_file.exists():
        # 简单解析，实际应该更复杂
        content = state_machine_file.read_text(encoding="utf-8")
        # 这里可以添加状态提取逻辑
        valid_states = {
            "raw_submitted", "trend_pending", "trend_ok", "trend_flagged",
            "trend_resolved", "final_pending", "final_confirmed", "final_locked",
            "pending", "approved", "rejected", "settled",
        }

    # 从 AUTH_SPEC.md 加载角色
    valid_roles = {"admin", "finance", "data_operator", "account_manager", "media_buyer"}

    # 从 ERROR_CODES_SOT.md 加载错误码
    valid_error_codes = {
        "VAL-001", "VAL-002", "AUTH-001", "AUTH-002",
        "BIZ-001", "BIZ-002", "SYS-001",
    }

    context = VerifyContext(
        project_root=root,
        requirement=requirement,
        valid_states=valid_states,
        valid_roles=valid_roles,
        valid_error_codes=valid_error_codes,
    )

    return EnhancedCodeVerifier(context, config)


def quick_verify(
    file_path: str,
    content: str,
    project_root: Optional[str] = None,
) -> Dict[str, Any]:
    """
    快速验证单个文件

    返回简化的结果字典
    """
    context = None
    if project_root:
        context = VerifyContext(
            project_root=Path(project_root),
            requirement="",
        )

    verifier = EnhancedCodeVerifier(context)
    result = verifier.verify_file(file_path, content)

    return {
        "passed": result.status in (VerifyStatus.PASSED, VerifyStatus.FIXED),
        "status": result.status.value,
        "issues_count": len(result.issues),
        "fixes_applied": result.fixes_applied,
        "errors": [
            {"code": i.code, "line": i.line, "message": i.message}
            for i in result.issues
            if i.severity == IssueSeverity.ERROR
        ],
        "warnings": [
            {"code": i.code, "line": i.line, "message": i.message}
            for i in result.issues
            if i.severity == IssueSeverity.WARNING
        ],
        "verified_content": result.verified_content,
    }
