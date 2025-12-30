"""
AST 代码分析器 - 用于 SoT 合规验证 v4.5

基准文档: MASTER.md v4.6
版本: v4.5

提供基于 AST 的代码分析，替代简单的正则匹配:
1. 角色值提取 (字符串常量、枚举成员)
2. 状态值提取 (字符串常量、枚举成员)
3. 错误码提取
4. API 端点提取

优势:
- 避免注释中的误匹配
- 精确识别代码结构
- 支持 Python 和 TypeScript
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class CodeLanguage(Enum):
    """代码语言"""
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    UNKNOWN = "unknown"


@dataclass
class ExtractedValue:
    """提取的值"""
    value: str
    line: int
    context: str  # 上下文 (如函数名、类名)
    value_type: str  # role, status, error_code, api_endpoint


@dataclass
class AstAnalysisResult:
    """AST 分析结果"""
    roles: List[ExtractedValue] = field(default_factory=list)
    statuses: List[ExtractedValue] = field(default_factory=list)
    error_codes: List[ExtractedValue] = field(default_factory=list)
    api_endpoints: List[ExtractedValue] = field(default_factory=list)
    enums: Dict[str, List[str]] = field(default_factory=dict)  # 枚举定义
    imports: List[str] = field(default_factory=list)


class PythonAstAnalyzer:
    """Python AST 分析器"""

    # 角色相关的标识符模式
    ROLE_IDENTIFIERS = {
        "role", "user_role", "current_role", "required_role",
        "UserRole", "RoleEnum", "Role"
    }

    # 状态相关的标识符模式
    STATUS_IDENTIFIERS = {
        "status", "state", "report_status", "topup_status",
        "DailyReportStatus", "TopupRequestStatus", "Status", "State"
    }

    # 错误码模式
    ERROR_CODE_PATTERN = re.compile(r'^[A-Z]{2,4}-\d{3}$')

    def __init__(self):
        self._current_context = []  # 当前上下文栈 (函数名、类名)

    def analyze(self, content: str, file_path: str = "") -> AstAnalysisResult:
        """分析 Python 代码

        Args:
            content: Python 源代码
            file_path: 文件路径 (用于错误报告)

        Returns:
            AstAnalysisResult
        """
        result = AstAnalysisResult()

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            # 语法错误，无法解析
            return result

        # 遍历 AST
        self._analyze_node(tree, result, content.split('\n'))

        return result

    def _analyze_node(self, node: ast.AST, result: AstAnalysisResult, lines: List[str]):
        """递归分析 AST 节点"""
        # 更新上下文
        context_pushed = False
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self._current_context.append(f"def {node.name}")
            context_pushed = True
        elif isinstance(node, ast.ClassDef):
            self._current_context.append(f"class {node.name}")
            context_pushed = True

            # 检查是否是枚举定义
            if self._is_enum_class(node):
                enum_values = self._extract_enum_values(node)
                if enum_values:
                    result.enums[node.name] = enum_values

        # 分析当前节点
        self._extract_from_node(node, result, lines)

        # 递归处理子节点
        for child in ast.iter_child_nodes(node):
            self._analyze_node(child, result, lines)

        # 恢复上下文
        if context_pushed:
            self._current_context.pop()

    def _is_enum_class(self, node: ast.ClassDef) -> bool:
        """检查是否是枚举类"""
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "Enum":
                return True
            if isinstance(base, ast.Attribute) and base.attr == "Enum":
                return True
            # str, Enum
            if isinstance(base, ast.Name) and base.id in ("str", "int"):
                continue
        return False

    def _extract_enum_values(self, node: ast.ClassDef) -> List[str]:
        """提取枚举值"""
        values = []
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        # 获取值
                        if isinstance(item.value, ast.Constant):
                            values.append(str(item.value.value))
                        elif isinstance(item.value, ast.Str):  # Python 3.7
                            values.append(item.value.s)
        return values

    def _extract_from_node(self, node: ast.AST, result: AstAnalysisResult, lines: List[str]):
        """从节点提取值"""
        context = " > ".join(self._current_context) if self._current_context else "module"

        # 1. 检查赋值语句
        if isinstance(node, ast.Assign):
            self._analyze_assignment(node, result, context)

        # 2. 检查比较表达式 (user.role == "admin")
        elif isinstance(node, ast.Compare):
            self._analyze_compare(node, result, context)

        # 3. 检查函数调用 (raise BusinessError(code="..."))
        elif isinstance(node, ast.Call):
            self._analyze_call(node, result, context)

        # 4. 检查装饰器 (@router.post("/api/v1/..."))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self._analyze_decorators(node, result, context)

        # 5. 检查导入
        elif isinstance(node, ast.Import):
            for alias in node.names:
                result.imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                result.imports.append(node.module)

    def _analyze_assignment(self, node: ast.Assign, result: AstAnalysisResult, context: str):
        """分析赋值语句"""
        for target in node.targets:
            target_name = self._get_name(target)
            if not target_name:
                continue

            # 检查角色赋值
            if any(ri in target_name.lower() for ri in ["role"]):
                value = self._get_string_value(node.value)
                if value:
                    result.roles.append(ExtractedValue(
                        value=value,
                        line=node.lineno,
                        context=context,
                        value_type="role"
                    ))

            # 检查状态赋值
            if any(si in target_name.lower() for si in ["status", "state"]):
                value = self._get_string_value(node.value)
                if value:
                    result.statuses.append(ExtractedValue(
                        value=value,
                        line=node.lineno,
                        context=context,
                        value_type="status"
                    ))

    def _analyze_compare(self, node: ast.Compare, result: AstAnalysisResult, context: str):
        """分析比较表达式"""
        # 获取左侧标识符名
        left_name = self._get_name(node.left)
        if not left_name:
            return

        # 检查是否是角色比较
        if "role" in left_name.lower():
            for comparator in node.comparators:
                value = self._get_string_value(comparator)
                if value:
                    result.roles.append(ExtractedValue(
                        value=value,
                        line=node.lineno,
                        context=context,
                        value_type="role"
                    ))

        # 检查是否是状态比较
        if any(s in left_name.lower() for s in ["status", "state"]):
            for comparator in node.comparators:
                value = self._get_string_value(comparator)
                if value:
                    result.statuses.append(ExtractedValue(
                        value=value,
                        line=node.lineno,
                        context=context,
                        value_type="status"
                    ))

    def _analyze_call(self, node: ast.Call, result: AstAnalysisResult, context: str):
        """分析函数调用"""
        func_name = self._get_name(node.func)

        # 检查 BusinessError, HTTPException 等
        if func_name and "error" in func_name.lower():
            for keyword in node.keywords:
                if keyword.arg == "code":
                    value = self._get_string_value(keyword.value)
                    if value and self.ERROR_CODE_PATTERN.match(value):
                        result.error_codes.append(ExtractedValue(
                            value=value,
                            line=node.lineno,
                            context=context,
                            value_type="error_code"
                        ))

    def _analyze_decorators(self, node: ast.FunctionDef, result: AstAnalysisResult, context: str):
        """分析装饰器 (提取 API 端点)"""
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                func_name = self._get_name(decorator.func)
                if func_name and any(m in func_name for m in ["get", "post", "put", "delete", "patch"]):
                    # 提取路径参数
                    if decorator.args:
                        path = self._get_string_value(decorator.args[0])
                        if path:
                            method = func_name.split(".")[-1].upper()
                            result.api_endpoints.append(ExtractedValue(
                                value=f"{method} {path}",
                                line=node.lineno,
                                context=context,
                                value_type="api_endpoint"
                            ))

    def _get_name(self, node: ast.AST) -> Optional[str]:
        """获取节点名称"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value_name = self._get_name(node.value)
            if value_name:
                return f"{value_name}.{node.attr}"
            return node.attr
        return None

    def _get_string_value(self, node: ast.AST) -> Optional[str]:
        """获取字符串值"""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        elif isinstance(node, ast.Str):  # Python 3.7
            return node.s
        elif isinstance(node, ast.Attribute):
            # 枚举成员 (如 UserRole.admin)
            return node.attr
        elif isinstance(node, ast.Name):
            # 变量引用
            return node.id
        return None


class TypeScriptAnalyzer:
    """TypeScript 简易分析器 (基于正则)

    由于 Python 无法直接解析 TypeScript AST，
    使用正则表达式进行分析。
    """

    # 角色模式
    ROLE_PATTERNS = [
        re.compile(r'role\s*[=:]\s*["\'](\w+)["\']', re.IGNORECASE),
        re.compile(r'\.role\s*===?\s*["\'](\w+)["\']', re.IGNORECASE),
        re.compile(r'UserRole\.(\w+)', re.IGNORECASE),
    ]

    # 状态模式
    STATUS_PATTERNS = [
        re.compile(r'status\s*[=:]\s*["\'](\w+)["\']', re.IGNORECASE),
        re.compile(r'\.status\s*===?\s*["\'](\w+)["\']', re.IGNORECASE),
        re.compile(r'ReportStatus\.(\w+)', re.IGNORECASE),
    ]

    # 错误码模式
    ERROR_CODE_PATTERN = re.compile(r'["\']([A-Z]{2,4}-\d{3})["\']')

    def analyze(self, content: str, file_path: str = "") -> AstAnalysisResult:
        """分析 TypeScript 代码"""
        result = AstAnalysisResult()
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # 跳过注释
            stripped = line.strip()
            if stripped.startswith('//') or stripped.startswith('/*'):
                continue

            # 提取角色
            for pattern in self.ROLE_PATTERNS:
                for match in pattern.finditer(line):
                    result.roles.append(ExtractedValue(
                        value=match.group(1),
                        line=i,
                        context="",
                        value_type="role"
                    ))

            # 提取状态
            for pattern in self.STATUS_PATTERNS:
                for match in pattern.finditer(line):
                    result.statuses.append(ExtractedValue(
                        value=match.group(1),
                        line=i,
                        context="",
                        value_type="status"
                    ))

            # 提取错误码
            for match in self.ERROR_CODE_PATTERN.finditer(line):
                result.error_codes.append(ExtractedValue(
                    value=match.group(1),
                    line=i,
                    context="",
                    value_type="error_code"
                ))

        return result


def detect_language(file_path: str) -> CodeLanguage:
    """检测文件语言"""
    path = Path(file_path)
    if path.suffix == ".py":
        return CodeLanguage.PYTHON
    elif path.suffix in [".ts", ".tsx", ".js", ".jsx"]:
        return CodeLanguage.TYPESCRIPT
    return CodeLanguage.UNKNOWN


def analyze_code(content: str, file_path: str = "") -> AstAnalysisResult:
    """分析代码 (自动检测语言)

    Args:
        content: 代码内容
        file_path: 文件路径

    Returns:
        AstAnalysisResult
    """
    language = detect_language(file_path)

    if language == CodeLanguage.PYTHON:
        analyzer = PythonAstAnalyzer()
    elif language == CodeLanguage.TYPESCRIPT:
        analyzer = TypeScriptAnalyzer()
    else:
        # 默认使用 TypeScript 分析器 (基于正则)
        analyzer = TypeScriptAnalyzer()

    return analyzer.analyze(content, file_path)


def validate_against_whitelist(
    analysis: AstAnalysisResult,
    valid_roles: Set[str],
    valid_statuses: Set[str],
    valid_error_prefixes: Set[str],
) -> Tuple[List[str], List[str]]:
    """验证分析结果是否符合白名单

    Args:
        analysis: AST 分析结果
        valid_roles: 有效角色集合
        valid_statuses: 有效状态集合
        valid_error_prefixes: 有效错误码前缀集合

    Returns:
        Tuple[List[str], List[str]]: (错误列表, 警告列表)
    """
    errors = []
    warnings = []

    # 验证角色
    for role in analysis.roles:
        role_value = role.value.lower()
        if role_value not in {r.lower() for r in valid_roles}:
            errors.append(
                f"Line {role.line}: 无效角色 '{role.value}' "
                f"(有效角色: {', '.join(sorted(valid_roles))})"
            )

    # 验证状态
    for status in analysis.statuses:
        status_value = status.value.lower()
        if status_value not in {s.lower() for s in valid_statuses}:
            # 某些通用状态词不算错误
            if status_value not in {"pending", "completed", "active", "inactive", "success", "error"}:
                warnings.append(
                    f"Line {status.line}: 未识别状态 '{status.value}'"
                )

    # 验证错误码
    for error_code in analysis.error_codes:
        prefix = error_code.value.split("-")[0]
        if prefix not in valid_error_prefixes:
            errors.append(
                f"Line {error_code.line}: 无效错误码前缀 '{prefix}' "
                f"(有效前缀: {', '.join(sorted(valid_error_prefixes))})"
            )

    return errors, warnings

