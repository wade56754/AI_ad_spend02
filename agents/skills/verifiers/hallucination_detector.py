"""
幻觉检测器 (Hallucination Detector)

检测 AI 生成代码中的"幻觉"问题：
- 调用不存在的函数/方法
- 导入不存在的模块
- 使用不存在的类
- 引用不存在的 API 端点
- 虚构的配置/常量

借鉴项目:
- HallOumi: 逐句分析验证理念
- FacTool: 代码生成幻觉检测
- IRIS: LLM + 静态分析结合

Code Sources:
- HallOumi (Oumi): https://github.com/oumi-ai/oumi
- FacTool: https://github.com/GAIR-NLP/factool
"""

import ast
import re
import importlib.util
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
# 常量定义
# ============================================================================

# Python 标准库模块 (部分常用)
STDLIB_MODULES = {
    # 内置
    "builtins", "sys", "os", "io", "re", "json", "datetime", "time",
    "pathlib", "typing", "collections", "itertools", "functools",
    "dataclasses", "enum", "abc", "copy", "uuid", "hashlib", "base64",
    "logging", "warnings", "traceback", "contextlib", "asyncio",
    # 文件/网络
    "urllib", "http", "socket", "ssl", "email", "mimetypes",
    # 数据
    "csv", "xml", "html", "sqlite3", "pickle", "struct",
    # 并发
    "threading", "multiprocessing", "concurrent", "queue",
    # 测试
    "unittest", "doctest",
    # 其他
    "math", "random", "decimal", "fractions", "statistics",
    "tempfile", "shutil", "glob", "fnmatch", "configparser",
    "argparse", "getopt", "textwrap", "string", "difflib",
}

# 常用第三方库
COMMON_THIRD_PARTY = {
    # Web
    "fastapi", "starlette", "uvicorn", "flask", "django", "httpx", "requests",
    # 数据库
    "sqlalchemy", "alembic", "databases", "asyncpg", "psycopg2",
    # 数据验证
    "pydantic", "marshmallow", "cerberus",
    # 工具
    "structlog", "loguru", "click", "typer", "rich",
    # 异步
    "aiohttp", "anyio", "trio",
    # 测试
    "pytest", "mock", "faker", "factory_boy", "hypothesis",
    # 数据处理
    "pandas", "numpy", "openpyxl", "xlrd", "xlwt",
    # 其他
    "dotenv", "python-dotenv", "celery", "redis", "boto3",
}

# 本项目模块前缀
PROJECT_MODULE_PREFIXES = {"backend", "frontend", "agents"}


class HallucinationDetector(BaseVerifier):
    """
    幻觉检测器

    检测 AI 生成代码中的幻觉问题，包括：
    1. 不存在的导入
    2. 不存在的函数/方法调用
    3. 不存在的类
    4. 虚构的 API 端点
    5. 不存在的配置常量
    """

    @property
    def name(self) -> str:
        return "HallucinationDetector"

    @property
    def category(self) -> IssueCategory:
        return IssueCategory.HALLUCINATION

    @property
    def priority(self) -> int:
        return 10  # 最高优先级

    def __init__(self, context: Optional[VerifyContext] = None):
        super().__init__(context)
        self._project_index: Optional[Dict[str, Any]] = None

    def verify(
        self,
        file_path: str,
        content: str,
        **kwargs
    ) -> VerifyResult:
        """
        执行幻觉检测

        检测流程:
        1. 解析 AST
        2. 提取所有导入
        3. 验证导入是否存在
        4. 提取所有函数/方法调用
        5. 验证调用是否存在
        6. 检查 API 端点引用
        """
        issues: List[VerifyIssue] = []
        metrics: Dict[str, Any] = {
            "imports_checked": 0,
            "calls_checked": 0,
            "hallucinations_found": 0,
        }

        try:
            # 解析 AST
            tree = ast.parse(content)

            # 1. 检测导入幻觉
            import_issues = self._check_imports(file_path, content, tree)
            issues.extend(import_issues)
            metrics["imports_checked"] = len(self._extract_imports(tree))

            # 2. 检测函数/方法调用幻觉
            call_issues = self._check_function_calls(file_path, content, tree)
            issues.extend(call_issues)
            metrics["calls_checked"] = len(list(ast.walk(tree)))

            # 3. 检测 API 端点幻觉 (仅限前端代码)
            if "frontend" in file_path or file_path.endswith((".ts", ".tsx", ".js")):
                api_issues = self._check_api_endpoints(file_path, content)
                issues.extend(api_issues)

            # 4. 检测项目内模块引用幻觉
            if self.context and self.context.existing_modules:
                module_issues = self._check_project_modules(file_path, content, tree)
                issues.extend(module_issues)

            metrics["hallucinations_found"] = len(issues)

        except SyntaxError as e:
            # 语法错误不是幻觉问题，返回空结果让 AST 验证器处理
            logger.warning(f"Syntax error in {file_path}: {e}")
            return VerifyResult(
                passed=True,
                category=self.category,
                issues=[],
                metrics=metrics,
                details=["Skipped due to syntax error"],
            )

        # 只有 ERROR 级别的问题才算失败
        passed = not any(i.severity == IssueSeverity.ERROR for i in issues)

        return VerifyResult(
            passed=passed,
            category=self.category,
            issues=issues,
            metrics=metrics,
            details=[
                f"Checked {metrics['imports_checked']} imports",
                f"Found {metrics['hallucinations_found']} hallucinations",
            ],
        )

    # ========================================================================
    # 导入检测
    # ========================================================================

    def _check_imports(
        self,
        file_path: str,
        content: str,
        tree: ast.AST
    ) -> List[VerifyIssue]:
        """检测导入幻觉"""
        issues = []
        imports = self._extract_imports(tree)

        for imp in imports:
            module_name = imp["module"]
            names = imp["names"]
            line = imp["line"]

            # 跳过标准库
            root_module = module_name.split(".")[0]
            if root_module in STDLIB_MODULES:
                continue

            # 跳过已知第三方库
            if root_module in COMMON_THIRD_PARTY:
                # 但仍需检查具体导入项
                if names:
                    suspicious = self._check_suspicious_imports(module_name, names)
                    for name, reason in suspicious:
                        issues.append(create_issue(
                            file_path=file_path,
                            line=line,
                            category=IssueCategory.HALLUCINATION,
                            code="HALL-001",
                            message=f"疑似幻觉导入: {name} from {module_name}",
                            suggestion=f"验证 {module_name} 是否真的提供 {name}. {reason}",
                            severity=IssueSeverity.WARNING,
                        ))
                continue

            # 检查项目内模块
            if any(module_name.startswith(prefix) for prefix in PROJECT_MODULE_PREFIXES):
                exists, reason = self._check_project_module_exists(module_name)
                if not exists:
                    issues.append(create_issue(
                        file_path=file_path,
                        line=line,
                        category=IssueCategory.HALLUCINATION,
                        code="HALL-002",
                        message=f"导入不存在的项目模块: {module_name}",
                        suggestion=f"检查模块路径是否正确. {reason}",
                        severity=IssueSeverity.ERROR,
                        evidence=f"import {module_name}",
                    ))
                else:
                    # 检查具体导入项
                    for name in names:
                        if not self._check_name_in_module(module_name, name):
                            issues.append(create_issue(
                                file_path=file_path,
                                line=line,
                                category=IssueCategory.HALLUCINATION,
                                code="HALL-003",
                                message=f"从 {module_name} 导入不存在的 {name}",
                                suggestion=f"检查 {name} 是否在 {module_name} 中定义",
                                severity=IssueSeverity.ERROR,
                                evidence=f"from {module_name} import {name}",
                            ))
                continue

            # 未知模块 - 可能是幻觉
            issues.append(create_issue(
                file_path=file_path,
                line=line,
                category=IssueCategory.HALLUCINATION,
                code="HALL-004",
                message=f"未知模块导入: {module_name}",
                suggestion="确认此模块是否存在于项目依赖中",
                severity=IssueSeverity.WARNING,
                evidence=f"import {module_name}",
            ))

        return issues

    def _extract_imports(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """提取所有导入语句"""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        "module": alias.name,
                        "names": [],
                        "line": node.lineno,
                    })
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append({
                        "module": node.module,
                        "names": [alias.name for alias in node.names],
                        "line": node.lineno,
                    })

        return imports

    def _check_suspicious_imports(
        self,
        module: str,
        names: List[str]
    ) -> List[Tuple[str, str]]:
        """检查可疑的导入项"""
        suspicious = []

        # FastAPI 常见错误
        if module == "fastapi":
            fake_fastapi = {"JsonResponse", "HTTPError", "RequestBody"}
            for name in names:
                if name in fake_fastapi:
                    suspicious.append((
                        name,
                        f"FastAPI 没有 {name}，正确的可能是: "
                        "JSONResponse (from starlette.responses), "
                        "HTTPException, Body"
                    ))

        # Pydantic v2 常见错误
        if module == "pydantic":
            fake_pydantic = {"validator", "root_validator", "Field.default"}
            for name in names:
                if name in fake_pydantic:
                    suspicious.append((
                        name,
                        f"Pydantic v2 已废弃 {name}，使用 "
                        "field_validator, model_validator 替代"
                    ))

        # SQLAlchemy 2.x 常见错误
        if "sqlalchemy" in module:
            fake_sa = {"declarative_base", "relationship.lazy"}
            for name in names:
                if name in fake_sa:
                    suspicious.append((
                        name,
                        f"SQLAlchemy 2.x 推荐使用 DeclarativeBase 类"
                    ))

        return suspicious

    def _check_project_module_exists(self, module_path: str) -> Tuple[bool, str]:
        """检查项目模块是否存在"""
        if not self.context:
            return True, ""  # 无上下文时跳过检查

        # 转换模块路径为文件路径
        parts = module_path.split(".")
        possible_paths = [
            self.context.project_root / "/".join(parts) / "__init__.py",
            self.context.project_root / f"{'/'.join(parts)}.py",
        ]

        for path in possible_paths:
            if path.exists():
                return True, ""

        # 检查是否在已知模块列表中
        if module_path in self.context.existing_modules:
            return True, ""

        return False, f"找不到模块文件: {possible_paths[1]}"

    def _check_name_in_module(self, module_path: str, name: str) -> bool:
        """检查名称是否在模块中定义"""
        if not self.context:
            return True  # 无上下文时跳过检查

        # 检查已知函数/类
        full_name = f"{module_path}.{name}"
        if full_name in self.context.existing_functions:
            return True
        if full_name in self.context.existing_classes:
            return True

        # 尝试动态检查 (仅对已安装模块)
        try:
            spec = importlib.util.find_spec(module_path)
            if spec and spec.loader:
                # 这里可以进一步加载模块检查，但为了安全暂不实现
                return True
        except (ImportError, ModuleNotFoundError):
            pass

        # 通过文件解析检查 (针对项目内部模块)
        if any(module_path.startswith(prefix) for prefix in PROJECT_MODULE_PREFIXES):
            return self._check_name_in_file(module_path, name)

        return False

    def _check_name_in_file(self, module_path: str, name: str) -> bool:
        """通过解析文件检查名称是否存在"""
        if not self.context:
            return True

        # 转换模块路径为文件路径
        parts = module_path.split(".")
        possible_paths = [
            self.context.project_root / f"{'/'.join(parts)}.py",
            self.context.project_root / "/".join(parts) / "__init__.py",
        ]

        for file_path in possible_paths:
            if not file_path.exists():
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                tree = ast.parse(content)

                # 查找定义的名称
                for node in ast.walk(tree):
                    # 类定义
                    if isinstance(node, ast.ClassDef) and node.name == name:
                        return True
                    # 函数定义
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
                        return True
                    # 赋值语句 (变量/常量)
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and target.id == name:
                                return True
                    # 导入重导出 (from x import y as name)
                    if isinstance(node, ast.ImportFrom):
                        for alias in node.names:
                            actual_name = alias.asname or alias.name
                            if actual_name == name:
                                return True
                    # 直接导入
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            actual_name = alias.asname or alias.name.split(".")[-1]
                            if actual_name == name:
                                return True

                # 检查 __all__ 导出
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and target.id == "__all__":
                                if isinstance(node.value, (ast.List, ast.Tuple)):
                                    for elt in node.value.elts:
                                        if isinstance(elt, ast.Constant) and elt.value == name:
                                            return True

            except (SyntaxError, UnicodeDecodeError):
                # 文件解析失败，保守起见认为存在
                return True

        return False

    # ========================================================================
    # 函数调用检测
    # ========================================================================

    def _check_function_calls(
        self,
        file_path: str,
        content: str,
        tree: ast.AST
    ) -> List[VerifyIssue]:
        """检测函数调用幻觉"""
        issues = []

        # 提取所有导入的名称
        imported_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name.split(".")[0])

        # 检查函数调用
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_name = self._get_call_name(node)
                if not call_name:
                    continue

                # 检查常见幻觉模式
                hallucination = self._detect_call_hallucination(call_name, node)
                if hallucination:
                    issues.append(create_issue(
                        file_path=file_path,
                        line=node.lineno,
                        column=node.col_offset,
                        category=IssueCategory.HALLUCINATION,
                        code="HALL-005",
                        message=hallucination["message"],
                        suggestion=hallucination["suggestion"],
                        severity=IssueSeverity.ERROR,
                        evidence=call_name,
                    ))

        return issues

    def _get_call_name(self, node: ast.Call) -> Optional[str]:
        """获取函数调用名称"""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            parts = []
            current = node.func
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return ".".join(reversed(parts))
        return None

    def _detect_call_hallucination(
        self,
        call_name: str,
        node: ast.Call
    ) -> Optional[Dict[str, str]]:
        """检测函数调用幻觉"""

        # 常见幻觉模式
        hallucinations = {
            # FastAPI
            "app.get_router": {
                "message": "FastAPI 没有 get_router 方法",
                "suggestion": "使用 APIRouter() 创建路由器，然后 app.include_router()",
            },
            "Response.json": {
                "message": "Response 没有 json 方法",
                "suggestion": "使用 JSONResponse 或 return dict (FastAPI 自动转换)",
            },
            # Pydantic
            "BaseModel.dict": {
                "message": "Pydantic v2 已废弃 .dict()",
                "suggestion": "使用 .model_dump() 替代",
            },
            "BaseModel.json": {
                "message": "Pydantic v2 已废弃 .json()",
                "suggestion": "使用 .model_dump_json() 替代",
            },
            "BaseModel.parse_obj": {
                "message": "Pydantic v2 已废弃 parse_obj()",
                "suggestion": "使用 Model.model_validate(obj) 替代",
            },
            # SQLAlchemy
            "session.query": {
                "message": "SQLAlchemy 2.x 推荐使用 select() 语法",
                "suggestion": "使用 session.execute(select(Model)) 替代",
            },
            # 常见错误
            "json.loads.decode": {
                "message": "json.loads 返回 dict，没有 decode 方法",
                "suggestion": "json.loads() 已经返回 Python 对象",
            },
        }

        # 模糊匹配
        for pattern, info in hallucinations.items():
            if pattern in call_name or call_name.endswith(pattern.split(".")[-1]):
                # 进一步验证
                if pattern == "BaseModel.dict" and ".dict(" in call_name:
                    return info
                if pattern == "session.query" and "query(" in call_name:
                    return info

        return None

    # ========================================================================
    # API 端点检测
    # ========================================================================

    def _check_api_endpoints(
        self,
        file_path: str,
        content: str
    ) -> List[VerifyIssue]:
        """检测 API 端点幻觉 (前端代码)"""
        issues = []

        if not self.context or not self.context.existing_endpoints:
            return issues

        # 提取 API 调用
        api_patterns = [
            r'fetch\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
            r'axios\.\w+\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
            r'apiFetch\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
            r'api\.\w+\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
        ]

        for pattern in api_patterns:
            for match in re.finditer(pattern, content):
                endpoint = match.group(1)
                line_num = content[:match.start()].count('\n') + 1

                # 标准化端点 (移除变量插值)
                endpoint_normalized = re.sub(r'\$\{[^}]+\}', '{id}', endpoint)
                endpoint_normalized = re.sub(r'/\d+/', '/{id}/', endpoint_normalized)

                # 检查端点是否存在
                if not self._endpoint_exists(endpoint_normalized):
                    issues.append(create_issue(
                        file_path=file_path,
                        line=line_num,
                        category=IssueCategory.HALLUCINATION,
                        code="HALL-006",
                        message=f"API 端点可能不存在: {endpoint}",
                        suggestion="检查后端是否提供此 API 端点",
                        severity=IssueSeverity.WARNING,
                        evidence=endpoint,
                    ))

        return issues

    def _endpoint_exists(self, endpoint: str) -> bool:
        """检查端点是否存在"""
        if not self.context:
            return True

        # 移除 API 前缀
        endpoint = endpoint.replace("/api/v1", "").replace("/api", "")

        # 模糊匹配
        for known in self.context.existing_endpoints:
            # 标准化比较
            known_normalized = known.replace("{", "").replace("}", "")
            endpoint_normalized = endpoint.replace("{", "").replace("}", "")

            if known_normalized.rstrip("/") == endpoint_normalized.rstrip("/"):
                return True

            # 前缀匹配
            if endpoint_normalized.startswith(known_normalized.split("{")[0]):
                return True

        return False

    # ========================================================================
    # 项目模块检测
    # ========================================================================

    def _check_project_modules(
        self,
        file_path: str,
        content: str,
        tree: ast.AST
    ) -> List[VerifyIssue]:
        """检测项目内模块引用幻觉"""
        issues = []

        # 提取字符串中的模块引用
        string_refs = re.findall(r'[\'"]backend\.\w+(?:\.\w+)*[\'"]', content)

        for ref in string_refs:
            module_path = ref.strip("'\"")
            if self.context and module_path not in self.context.existing_modules:
                line_num = content.find(ref)
                line_num = content[:line_num].count('\n') + 1 if line_num >= 0 else 1

                issues.append(create_issue(
                    file_path=file_path,
                    line=line_num,
                    category=IssueCategory.HALLUCINATION,
                    code="HALL-007",
                    message=f"字符串引用不存在的模块: {module_path}",
                    suggestion="检查模块路径是否正确",
                    severity=IssueSeverity.WARNING,
                    evidence=ref,
                ))

        return issues


# ============================================================================
# 便捷函数
# ============================================================================

def detect_hallucinations(
    file_path: str,
    content: str,
    context: Optional[VerifyContext] = None
) -> VerifyResult:
    """
    幻觉检测便捷函数

    Args:
        file_path: 文件路径
        content: 文件内容
        context: 验证上下文

    Returns:
        验证结果
    """
    detector = HallucinationDetector(context)
    return detector.verify(file_path, content)
