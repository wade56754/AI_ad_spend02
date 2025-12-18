"""
AST 验证器 (AST Verifier)

验证代码的语法正确性和结构完整性：
- Python: 使用 ast 模块解析
- TypeScript: 使用 esprima/tree-sitter 概念

借鉴项目:
- tree-sitter: 多语言 AST 解析
- mypy: Python AST 分析

Code Sources:
- tree-sitter: https://github.com/tree-sitter/tree-sitter
- mypy: https://github.com/python/mypy
"""

import ast
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
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


class ASTVerifier(BaseVerifier):
    """
    AST 验证器

    验证代码的语法正确性和结构完整性
    """

    @property
    def name(self) -> str:
        return "ASTVerifier"

    @property
    def category(self) -> IssueCategory:
        return IssueCategory.SYNTAX

    @property
    def priority(self) -> int:
        return 5  # 最高优先级，语法错误必须首先检查

    def verify(
        self,
        file_path: str,
        content: str,
        **kwargs
    ) -> VerifyResult:
        """
        执行 AST 验证

        检测:
        1. 语法错误
        2. 缩进错误
        3. 括号匹配
        4. 字符串引号匹配
        5. 结构完整性
        """
        issues: List[VerifyIssue] = []
        metrics: Dict[str, Any] = {
            "lines": content.count('\n') + 1,
            "syntax_valid": False,
            "structure_valid": False,
        }

        # 根据文件类型选择验证方法
        if file_path.endswith(".py"):
            issues = self._verify_python(file_path, content)
            metrics["language"] = "python"
        elif file_path.endswith((".ts", ".tsx", ".js", ".jsx")):
            issues = self._verify_typescript(file_path, content)
            metrics["language"] = "typescript"
        else:
            # 不支持的文件类型，跳过
            return VerifyResult(
                passed=True,
                category=self.category,
                issues=[],
                metrics={"skipped": True, "reason": "Unsupported file type"},
                details=["Skipped: unsupported file type"],
            )

        # 更新 metrics
        metrics["syntax_valid"] = not any(
            i.code.startswith("SYN") for i in issues
        )
        metrics["structure_valid"] = not any(
            i.code.startswith("STR") for i in issues
        )

        passed = not any(i.severity == IssueSeverity.ERROR for i in issues)

        return VerifyResult(
            passed=passed,
            category=self.category,
            issues=issues,
            metrics=metrics,
            details=[
                f"Language: {metrics.get('language', 'unknown')}",
                f"Lines: {metrics['lines']}",
                f"Syntax valid: {metrics['syntax_valid']}",
            ],
        )

    # ========================================================================
    # Python AST 验证
    # ========================================================================

    def _verify_python(
        self,
        file_path: str,
        content: str
    ) -> List[VerifyIssue]:
        """验证 Python 代码"""
        issues = []

        # 1. 基础语法检查
        try:
            tree = ast.parse(content, filename=file_path)
        except SyntaxError as e:
            issues.append(create_issue(
                file_path=file_path,
                line=e.lineno or 1,
                column=e.offset or 0,
                category=IssueCategory.SYNTAX,
                code="SYN-001",
                message=f"Python 语法错误: {e.msg}",
                suggestion=self._get_syntax_fix_suggestion(e),
                severity=IssueSeverity.ERROR,
                evidence=e.text.strip() if e.text else None,
                auto_fixable=self._is_syntax_auto_fixable(e),
            ))
            return issues

        # 2. 结构完整性检查
        structure_issues = self._check_python_structure(file_path, content, tree)
        issues.extend(structure_issues)

        # 3. 常见问题检查
        common_issues = self._check_python_common_issues(file_path, content, tree)
        issues.extend(common_issues)

        return issues

    def _check_python_structure(
        self,
        file_path: str,
        content: str,
        tree: ast.AST
    ) -> List[VerifyIssue]:
        """检查 Python 代码结构"""
        issues = []

        # 检查是否有孤立的代码块
        for node in ast.walk(tree):
            # 检查空的 try 块
            if isinstance(node, ast.Try):
                if not node.body:
                    issues.append(create_issue(
                        file_path=file_path,
                        line=node.lineno,
                        category=IssueCategory.SYNTAX,
                        code="STR-001",
                        message="空的 try 块",
                        suggestion="添加 try 块内容或使用 pass",
                        severity=IssueSeverity.ERROR,
                    ))

                # 检查空的 except 块
                for handler in node.handlers:
                    if not handler.body:
                        issues.append(create_issue(
                            file_path=file_path,
                            line=handler.lineno,
                            category=IssueCategory.SYNTAX,
                            code="STR-002",
                            message="空的 except 块",
                            suggestion="添加异常处理逻辑或使用 pass",
                            severity=IssueSeverity.WARNING,
                        ))

            # 检查空的类定义
            if isinstance(node, ast.ClassDef):
                if not node.body or (len(node.body) == 1 and isinstance(node.body[0], ast.Pass)):
                    issues.append(create_issue(
                        file_path=file_path,
                        line=node.lineno,
                        category=IssueCategory.SYNTAX,
                        code="STR-003",
                        message=f"空的类定义: {node.name}",
                        suggestion="添加类属性或方法",
                        severity=IssueSeverity.WARNING,
                    ))

            # 检查空的函数定义
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                body_without_docstring = [
                    n for n in node.body
                    if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))
                ]
                if not body_without_docstring or (
                    len(body_without_docstring) == 1 and
                    isinstance(body_without_docstring[0], ast.Pass)
                ):
                    # 允许抽象方法为空
                    is_abstract = any(
                        isinstance(d, ast.Name) and d.id == "abstractmethod"
                        for d in node.decorator_list
                    ) if hasattr(node, 'decorator_list') else False

                    if not is_abstract:
                        issues.append(create_issue(
                            file_path=file_path,
                            line=node.lineno,
                            category=IssueCategory.SYNTAX,
                            code="STR-004",
                            message=f"空的函数定义: {node.name}",
                            suggestion="添加函数实现或使用 @abstractmethod",
                            severity=IssueSeverity.WARNING,
                        ))

        return issues

    def _check_python_common_issues(
        self,
        file_path: str,
        content: str,
        tree: ast.AST
    ) -> List[VerifyIssue]:
        """检查 Python 常见问题"""
        issues = []

        # 1. 检查未闭合的字符串
        string_issues = self._check_unclosed_strings(file_path, content)
        issues.extend(string_issues)

        # 2. 检查混合缩进
        indent_issues = self._check_mixed_indentation(file_path, content)
        issues.extend(indent_issues)

        # 3. 检查重复定义
        duplicate_issues = self._check_duplicate_definitions(file_path, tree)
        issues.extend(duplicate_issues)

        return issues

    def _check_unclosed_strings(
        self,
        file_path: str,
        content: str
    ) -> List[VerifyIssue]:
        """检查未闭合的字符串"""
        issues = []

        # 简化检查: 计算引号数量
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            # 跳过注释
            if line.strip().startswith('#'):
                continue

            # 检查三引号字符串
            if '"""' in line or "'''" in line:
                continue  # 三引号字符串复杂，跳过简单检查

            # 计算单引号和双引号
            single_count = line.count("'") - line.count("\\'")
            double_count = line.count('"') - line.count('\\"')

            if single_count % 2 != 0:
                issues.append(create_issue(
                    file_path=file_path,
                    line=i,
                    category=IssueCategory.SYNTAX,
                    code="SYN-002",
                    message="可能存在未闭合的单引号字符串",
                    suggestion="检查单引号是否匹配",
                    severity=IssueSeverity.WARNING,
                    evidence=line.strip()[:50],
                ))

            if double_count % 2 != 0:
                issues.append(create_issue(
                    file_path=file_path,
                    line=i,
                    category=IssueCategory.SYNTAX,
                    code="SYN-003",
                    message="可能存在未闭合的双引号字符串",
                    suggestion="检查双引号是否匹配",
                    severity=IssueSeverity.WARNING,
                    evidence=line.strip()[:50],
                ))

        return issues

    def _check_mixed_indentation(
        self,
        file_path: str,
        content: str
    ) -> List[VerifyIssue]:
        """检查混合缩进"""
        issues = []
        has_tabs = False
        has_spaces = False

        for i, line in enumerate(content.split('\n'), 1):
            if line.startswith('\t'):
                has_tabs = True
            elif line.startswith('    '):
                has_spaces = True

            # 检查同一行混合
            leading = len(line) - len(line.lstrip())
            if leading > 0:
                leading_chars = line[:leading]
                if '\t' in leading_chars and ' ' in leading_chars:
                    issues.append(create_issue(
                        file_path=file_path,
                        line=i,
                        category=IssueCategory.SYNTAX,
                        code="SYN-004",
                        message="混合使用 Tab 和空格缩进",
                        suggestion="统一使用 4 个空格缩进",
                        severity=IssueSeverity.ERROR,
                        auto_fixable=True,
                    ))

        # 检查文件级别混合
        if has_tabs and has_spaces:
            issues.append(create_issue(
                file_path=file_path,
                line=1,
                category=IssueCategory.SYNTAX,
                code="SYN-005",
                message="文件中混合使用 Tab 和空格缩进",
                suggestion="统一使用 4 个空格缩进",
                severity=IssueSeverity.WARNING,
                auto_fixable=True,
            ))

        return issues

    def _check_duplicate_definitions(
        self,
        file_path: str,
        tree: ast.AST
    ) -> List[VerifyIssue]:
        """检查重复定义"""
        issues = []
        definitions: Dict[str, List[int]] = {}

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = node.name
                if name in definitions:
                    definitions[name].append(node.lineno)
                else:
                    definitions[name] = [node.lineno]

            elif isinstance(node, ast.ClassDef):
                name = node.name
                if name in definitions:
                    definitions[name].append(node.lineno)
                else:
                    definitions[name] = [node.lineno]

        for name, lines in definitions.items():
            if len(lines) > 1:
                issues.append(create_issue(
                    file_path=file_path,
                    line=lines[-1],  # 报告最后一个定义
                    category=IssueCategory.SYNTAX,
                    code="STR-005",
                    message=f"重复定义: {name} (行 {', '.join(map(str, lines))})",
                    suggestion=f"移除或重命名重复的 {name} 定义",
                    severity=IssueSeverity.WARNING,
                ))

        return issues

    def _get_syntax_fix_suggestion(self, error: SyntaxError) -> str:
        """获取语法错误修复建议"""
        msg = str(error.msg).lower() if error.msg else ""

        if "expected ':'" in msg:
            return "在函数定义、类定义、if/for/while 语句后添加冒号 ':'"
        if "unexpected indent" in msg:
            return "检查缩进是否正确，确保使用一致的缩进 (4 个空格)"
        if "expected 'EOF'" in msg or "unexpected EOF" in msg:
            return "检查括号、引号是否闭合"
        if "invalid syntax" in msg:
            return "检查语法是否正确，可能存在拼写错误或遗漏的符号"
        if "expected an indented block" in msg:
            return "在 if/for/while/def/class 语句后添加缩进的代码块"

        return "检查语法错误位置附近的代码"

    def _is_syntax_auto_fixable(self, error: SyntaxError) -> bool:
        """判断语法错误是否可自动修复"""
        msg = str(error.msg).lower() if error.msg else ""

        # 这些错误通常可以自动修复
        auto_fixable_patterns = [
            "expected ':'",
            "trailing comma",
        ]

        return any(pattern in msg for pattern in auto_fixable_patterns)

    # ========================================================================
    # TypeScript AST 验证
    # ========================================================================

    def _verify_typescript(
        self,
        file_path: str,
        content: str
    ) -> List[VerifyIssue]:
        """验证 TypeScript 代码"""
        issues = []

        # 简化实现: 使用正则检查常见问题
        # 完整实现应使用 tree-sitter 或 esprima

        # 1. 检查括号匹配
        bracket_issues = self._check_bracket_matching(file_path, content)
        issues.extend(bracket_issues)

        # 2. 检查分号 (可选，取决于项目风格)
        # 跳过分号检查，因为可能使用无分号风格

        # 3. 检查基础语法模式
        pattern_issues = self._check_ts_patterns(file_path, content)
        issues.extend(pattern_issues)

        return issues

    def _check_bracket_matching(
        self,
        file_path: str,
        content: str
    ) -> List[VerifyIssue]:
        """检查括号匹配"""
        issues = []
        brackets = {'(': ')', '[': ']', '{': '}'}
        stack = []

        # 简化: 不处理字符串和注释内的括号
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for col, char in enumerate(line):
                if char in brackets:
                    stack.append((char, line_num, col))
                elif char in brackets.values():
                    if not stack:
                        issues.append(create_issue(
                            file_path=file_path,
                            line=line_num,
                            column=col,
                            category=IssueCategory.SYNTAX,
                            code="SYN-006",
                            message=f"多余的闭合括号: {char}",
                            suggestion="检查括号匹配",
                            severity=IssueSeverity.ERROR,
                        ))
                    else:
                        open_bracket, _, _ = stack[-1]
                        if brackets[open_bracket] != char:
                            issues.append(create_issue(
                                file_path=file_path,
                                line=line_num,
                                column=col,
                                category=IssueCategory.SYNTAX,
                                code="SYN-007",
                                message=f"括号不匹配: 期望 {brackets[open_bracket]}，实际 {char}",
                                suggestion="检查括号匹配",
                                severity=IssueSeverity.ERROR,
                            ))
                        stack.pop()

        # 检查未闭合的括号
        for open_bracket, line_num, col in stack:
            issues.append(create_issue(
                file_path=file_path,
                line=line_num,
                column=col,
                category=IssueCategory.SYNTAX,
                code="SYN-008",
                message=f"未闭合的括号: {open_bracket}",
                suggestion=f"添加闭合括号: {brackets[open_bracket]}",
                severity=IssueSeverity.ERROR,
            ))

        return issues

    def _check_ts_patterns(
        self,
        file_path: str,
        content: str
    ) -> List[VerifyIssue]:
        """检查 TypeScript 常见问题模式"""
        issues = []

        # 1. 检查空的函数体
        empty_func_pattern = r'(function\s+\w+\s*\([^)]*\)\s*\{)\s*\}'
        for match in re.finditer(empty_func_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            issues.append(create_issue(
                file_path=file_path,
                line=line_num,
                category=IssueCategory.SYNTAX,
                code="STR-006",
                message="空的函数体",
                suggestion="添加函数实现",
                severity=IssueSeverity.WARNING,
            ))

        # 2. 检查 console.log 残留 (可能是调试代码)
        console_pattern = r'\bconsole\.(log|warn|error)\s*\('
        for match in re.finditer(console_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            issues.append(create_issue(
                file_path=file_path,
                line=line_num,
                category=IssueCategory.SYNTAX,
                code="STR-007",
                message="发现 console 调用",
                suggestion="考虑移除调试代码或使用 logger",
                severity=IssueSeverity.WARNING,
            ))

        return issues

    # ========================================================================
    # 自动修复
    # ========================================================================

    def auto_fix(
        self,
        content: str,
        issues: List[VerifyIssue]
    ) -> tuple[str, int]:
        """自动修复语法问题"""
        fixed_count = 0

        for issue in issues:
            if not issue.auto_fixable:
                continue

            # 修复混合缩进
            if issue.code in ("SYN-004", "SYN-005"):
                content = content.replace('\t', '    ')
                fixed_count += 1
                issue.fix_applied = True

        return content, fixed_count


# ============================================================================
# 便捷函数
# ============================================================================

def verify_ast(
    file_path: str,
    content: str,
    context: Optional[VerifyContext] = None
) -> VerifyResult:
    """
    AST 验证便捷函数

    Args:
        file_path: 文件路径
        content: 文件内容
        context: 验证上下文

    Returns:
        验证结果
    """
    verifier = ASTVerifier(context)
    return verifier.verify(file_path, content)
