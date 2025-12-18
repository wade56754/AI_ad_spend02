"""
集成验证器

验证代码的集成问题:
1. 导入路径有效性
2. 依赖可用性
3. 循环导入检测
4. 模块结构验证
"""

import ast
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .base import (
    BaseVerifier,
    IssueCategory,
    IssueSeverity,
    VerifyContext,
    VerifyIssue,
    VerifyResult,
    create_issue,
)


# ============================================================================
# 常量定义
# ============================================================================

# Python 标准库模块 (常用)
STDLIB_MODULES = {
    "abc", "argparse", "ast", "asyncio", "base64", "collections",
    "contextlib", "copy", "csv", "dataclasses", "datetime", "decimal",
    "enum", "functools", "glob", "gzip", "hashlib", "heapq", "hmac",
    "http", "importlib", "inspect", "io", "itertools", "json", "logging",
    "math", "multiprocessing", "os", "pathlib", "pickle", "pprint",
    "queue", "random", "re", "secrets", "shutil", "signal", "socket",
    "sqlite3", "ssl", "statistics", "string", "subprocess", "sys",
    "tempfile", "threading", "time", "traceback", "types", "typing",
    "unittest", "urllib", "uuid", "warnings", "weakref", "xml", "zipfile",
}

# 项目内部模块前缀
PROJECT_MODULE_PREFIXES = {
    "backend.",
    "agents.",
    "frontend.",
}

# 常见第三方包
COMMON_THIRD_PARTY = {
    # Web 框架
    "fastapi", "flask", "django", "starlette", "uvicorn", "gunicorn",
    # ORM
    "sqlalchemy", "alembic", "peewee", "tortoise",
    # 数据验证
    "pydantic", "marshmallow", "cerberus",
    # HTTP 客户端
    "requests", "httpx", "aiohttp", "urllib3",
    # 数据处理
    "pandas", "numpy", "scipy", "polars",
    # 测试
    "pytest", "unittest", "mock", "faker", "hypothesis",
    # 异步
    "anyio", "trio", "curio",
    # 数据库
    "psycopg2", "asyncpg", "pymysql", "redis", "motor",
    # 认证
    "passlib", "python_jose", "jose", "jwt", "authlib",
    # 工具
    "click", "rich", "typer", "loguru", "structlog",
    # Supabase
    "supabase", "gotrue", "postgrest", "storage3",
}

# 项目期望的目录结构
EXPECTED_BACKEND_STRUCTURE = {
    "routers": "API 路由层",
    "services": "业务逻辑层",
    "models": "数据模型层",
    "schemas": "数据验证层",
    "core": "核心工具层",
}


class IntegrationVerifier(BaseVerifier):
    """
    集成验证器

    检测:
    1. 导入路径是否存在
    2. 依赖是否已安装
    3. 循环导入风险
    4. 相对/绝对导入规范
    """

    @property
    def name(self) -> str:
        return "IntegrationVerifier"

    @property
    def category(self) -> IssueCategory:
        return IssueCategory.INTEGRATION

    @property
    def priority(self) -> int:
        return 40  # 在幻觉检测和 AST 之后

    def __init__(self, context: Optional[VerifyContext] = None):
        super().__init__(context)
        self._import_cache: Dict[str, bool] = {}
        self._module_cache: Dict[str, Path] = {}

    def verify(
        self,
        file_path: str,
        content: str,
        **kwargs
    ) -> VerifyResult:
        """执行集成验证"""
        issues: List[VerifyIssue] = []
        details: List[str] = []
        metrics: Dict[str, Any] = {
            "total_imports": 0,
            "stdlib_imports": 0,
            "third_party_imports": 0,
            "local_imports": 0,
            "missing_imports": 0,
            "circular_risks": 0,
        }

        # 解析 AST
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            # 语法错误交给 AST 验证器处理
            return VerifyResult(
                passed=True,
                category=self.category,
                issues=[],
                metrics=metrics,
                details=["跳过: 语法错误由 AST 验证器处理"],
            )

        # 提取所有导入
        imports = self._extract_imports(tree)
        metrics["total_imports"] = len(imports)

        # 验证每个导入
        for imp in imports:
            result = self._verify_import(file_path, imp, content)
            if result:
                issues.append(result)

            # 分类统计
            module_name = imp["module"].split(".")[0]
            if module_name in STDLIB_MODULES:
                metrics["stdlib_imports"] += 1
            elif any(imp["module"].startswith(p) for p in PROJECT_MODULE_PREFIXES):
                metrics["local_imports"] += 1
            else:
                metrics["third_party_imports"] += 1

        metrics["missing_imports"] = len([i for i in issues if i.code.startswith("INT-001")])

        # 检测循环导入风险
        circular_issues = self._check_circular_import_risk(file_path, imports)
        issues.extend(circular_issues)
        metrics["circular_risks"] = len(circular_issues)

        # 检查导入规范
        style_issues = self._check_import_style(file_path, tree, content)
        issues.extend(style_issues)

        # 检查项目结构合规性
        structure_issues = self._check_project_structure(file_path, content)
        issues.extend(structure_issues)

        # 汇总
        error_count = len([i for i in issues if i.severity == IssueSeverity.ERROR])
        passed = error_count == 0

        if passed:
            details.append(f"集成验证通过: {len(imports)} 个导入")
        else:
            details.append(f"发现 {error_count} 个集成问题")

        return VerifyResult(
            passed=passed,
            category=self.category,
            issues=issues,
            metrics=metrics,
            details=details,
        )

    def _extract_imports(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """提取所有导入语句"""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        "type": "import",
                        "module": alias.name,
                        "name": alias.asname or alias.name,
                        "line": node.lineno,
                        "is_relative": False,
                    })

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                level = node.level  # 相对导入层级

                for alias in node.names:
                    imports.append({
                        "type": "from",
                        "module": module,
                        "name": alias.name,
                        "alias": alias.asname,
                        "line": node.lineno,
                        "level": level,
                        "is_relative": level > 0,
                    })

        return imports

    def _verify_import(
        self,
        file_path: str,
        imp: Dict[str, Any],
        content: str
    ) -> Optional[VerifyIssue]:
        """验证单个导入"""
        module_name = imp["module"]
        root_module = module_name.split(".")[0] if module_name else ""

        # 相对导入
        if imp.get("is_relative"):
            return self._verify_relative_import(file_path, imp)

        # 标准库
        if root_module in STDLIB_MODULES:
            return None

        # 第三方库
        if root_module in COMMON_THIRD_PARTY:
            return self._verify_third_party(file_path, imp)

        # 项目内部模块
        if any(module_name.startswith(p) for p in PROJECT_MODULE_PREFIXES):
            return self._verify_project_import(file_path, imp)

        # 未知模块 - 可能是幻觉
        if self.context and root_module not in self.context.installed_packages:
            return create_issue(
                file_path=file_path,
                line=imp["line"],
                category=IssueCategory.INTEGRATION,
                code="INT-001",
                message=f"未识别的模块: {module_name}",
                suggestion=f"确认 '{root_module}' 是否已安装或是否为正确的模块名",
                severity=IssueSeverity.WARNING,
            )

        return None

    def _verify_relative_import(
        self,
        file_path: str,
        imp: Dict[str, Any]
    ) -> Optional[VerifyIssue]:
        """验证相对导入"""
        if not self.context:
            return None

        level = imp.get("level", 1)
        module = imp.get("module", "")

        # 计算目标路径
        current_dir = Path(file_path).parent
        for _ in range(level - 1):
            current_dir = current_dir.parent

        if module:
            target_path = current_dir / module.replace(".", os.sep)
        else:
            target_path = current_dir

        # 检查目标是否存在
        target_file = target_path.with_suffix(".py")
        target_init = target_path / "__init__.py"

        if not target_file.exists() and not target_init.exists() and not target_path.is_dir():
            return create_issue(
                file_path=file_path,
                line=imp["line"],
                category=IssueCategory.INTEGRATION,
                code="INT-002",
                message=f"相对导入路径不存在: {'.' * level}{module}",
                suggestion=f"检查目录结构，确保 {target_path} 存在",
                severity=IssueSeverity.ERROR,
            )

        return None

    def _verify_third_party(
        self,
        file_path: str,
        imp: Dict[str, Any]
    ) -> Optional[VerifyIssue]:
        """验证第三方库"""
        module_name = imp["module"]
        root_module = module_name.split(".")[0]

        # 检查是否已安装
        try:
            __import__(root_module)
            return None
        except ImportError:
            return create_issue(
                file_path=file_path,
                line=imp["line"],
                category=IssueCategory.INTEGRATION,
                code="INT-003",
                message=f"第三方库未安装: {root_module}",
                suggestion=f"运行 'pip install {root_module}' 安装依赖",
                severity=IssueSeverity.WARNING,
                auto_fixable=True,
            )

    def _verify_project_import(
        self,
        file_path: str,
        imp: Dict[str, Any]
    ) -> Optional[VerifyIssue]:
        """验证项目内部导入"""
        if not self.context:
            return None

        module_name = imp["module"]
        import_name = imp["name"]

        # 转换为文件路径
        module_path = module_name.replace(".", os.sep)
        project_root = self.context.project_root

        # 可能的路径
        possible_paths = [
            project_root / f"{module_path}.py",
            project_root / module_path / "__init__.py",
            project_root / module_path,
        ]

        exists = any(p.exists() for p in possible_paths)

        if not exists:
            return create_issue(
                file_path=file_path,
                line=imp["line"],
                category=IssueCategory.INTEGRATION,
                code="INT-004",
                message=f"项目模块不存在: {module_name}",
                suggestion=f"确认模块路径是否正确，或创建缺失的模块",
                severity=IssueSeverity.ERROR,
            )

        # 检查导入的具体名称是否存在
        if import_name != "*":
            # 这需要更复杂的静态分析，暂时跳过
            pass

        return None

    def _check_circular_import_risk(
        self,
        file_path: str,
        imports: List[Dict[str, Any]]
    ) -> List[VerifyIssue]:
        """检测循环导入风险"""
        issues = []

        if not self.context:
            return issues

        current_module = self._path_to_module(file_path)
        if not current_module:
            return issues

        for imp in imports:
            module_name = imp["module"]

            # 只检查项目内部导入
            if not any(module_name.startswith(p) for p in PROJECT_MODULE_PREFIXES):
                continue

            # 检查是否在模块顶层导入
            # 循环导入通常发生在顶层相互导入的情况
            # 这里简化处理：检测同一包内的相互引用
            if self._is_same_package(current_module, module_name):
                # 同包内导入，检查是否可能形成循环
                if self._could_cause_circular(current_module, module_name):
                    issues.append(create_issue(
                        file_path=file_path,
                        line=imp["line"],
                        category=IssueCategory.INTEGRATION,
                        code="INT-005",
                        message=f"潜在循环导入风险: {module_name}",
                        suggestion="考虑使用延迟导入 (在函数内导入) 或重构模块结构",
                        severity=IssueSeverity.WARNING,
                    ))

        return issues

    def _check_import_style(
        self,
        file_path: str,
        tree: ast.AST,
        content: str
    ) -> List[VerifyIssue]:
        """检查导入风格"""
        issues = []
        lines = content.split("\n")

        # 检查导入顺序 (PEP 8: stdlib, third-party, local)
        import_groups: List[Tuple[int, str, str]] = []  # (line, type, module)

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        import_groups.append((
                            node.lineno,
                            self._classify_import(alias.name),
                            alias.name
                        ))
                else:
                    module = node.module or ""
                    import_groups.append((
                        node.lineno,
                        self._classify_import(module, node.level > 0),
                        module
                    ))

        # 检查分组是否正确
        prev_type = None
        prev_line = 0
        for line, imp_type, module in sorted(import_groups, key=lambda x: x[0]):
            if prev_type and imp_type != prev_type:
                # 类型变化时应该有空行分隔
                if line - prev_line == 1:
                    issues.append(create_issue(
                        file_path=file_path,
                        line=line,
                        category=IssueCategory.INTEGRATION,
                        code="INT-006",
                        message="导入分组之间缺少空行",
                        suggestion="在标准库、第三方库、本地导入之间添加空行",
                        severity=IssueSeverity.INFO,
                        auto_fixable=True,
                    ))
            prev_type = imp_type
            prev_line = line

        # 检查 star imports
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == "*":
                        issues.append(create_issue(
                            file_path=file_path,
                            line=node.lineno,
                            category=IssueCategory.INTEGRATION,
                            code="INT-007",
                            message=f"避免使用 star import: from {node.module} import *",
                            suggestion="明确列出需要导入的名称",
                            severity=IssueSeverity.WARNING,
                        ))

        return issues

    def _check_project_structure(
        self,
        file_path: str,
        content: str
    ) -> List[VerifyIssue]:
        """检查项目结构合规性"""
        issues = []
        path = Path(file_path)

        # 只检查后端代码
        if "backend" not in path.parts:
            return issues

        # 检查是否在正确的层级
        for parent in path.parents:
            if parent.name in EXPECTED_BACKEND_STRUCTURE:
                break
        else:
            # 不在标准目录中，可能需要检查
            if path.suffix == ".py" and path.name != "__init__.py":
                # 检查是否有业务逻辑放在错误的位置
                if "router" in content.lower() and "routers" not in path.parts:
                    issues.append(create_issue(
                        file_path=file_path,
                        line=1,
                        category=IssueCategory.INTEGRATION,
                        code="INT-008",
                        message="路由代码可能放在了错误的位置",
                        suggestion="路由代码应该放在 backend/routers/ 目录下",
                        severity=IssueSeverity.WARNING,
                    ))

        return issues

    def _path_to_module(self, file_path: str) -> Optional[str]:
        """将文件路径转换为模块名"""
        if not self.context:
            return None

        path = Path(file_path)
        try:
            rel_path = path.relative_to(self.context.project_root)
            module = str(rel_path.with_suffix("")).replace(os.sep, ".")
            return module
        except ValueError:
            return None

    def _is_same_package(self, module1: str, module2: str) -> bool:
        """检查两个模块是否在同一包中"""
        parts1 = module1.split(".")
        parts2 = module2.split(".")

        if len(parts1) < 2 or len(parts2) < 2:
            return False

        return parts1[:-1] == parts2[:-1]

    def _could_cause_circular(self, current: str, imported: str) -> bool:
        """检查是否可能导致循环导入"""
        # 简化实现：检查是否是同级模块的相互引用
        # 更完整的实现需要构建完整的依赖图
        return self._is_same_package(current, imported)

    def _classify_import(self, module: str, is_relative: bool = False) -> str:
        """分类导入类型"""
        if is_relative:
            return "local"

        root = module.split(".")[0]

        if root in STDLIB_MODULES:
            return "stdlib"
        elif any(module.startswith(p) for p in PROJECT_MODULE_PREFIXES):
            return "local"
        else:
            return "third_party"

    def auto_fix(
        self,
        content: str,
        issues: List[VerifyIssue]
    ) -> Tuple[str, int]:
        """自动修复导入问题"""
        fixed_count = 0
        lines = content.split("\n")

        # 目前只支持添加导入分组空行
        for issue in issues:
            if issue.code == "INT-006" and issue.auto_fixable:
                # 在导入分组之间添加空行
                line_idx = issue.line - 1
                if 0 <= line_idx < len(lines):
                    lines.insert(line_idx, "")
                    fixed_count += 1
                    issue.fix_applied = True

        return "\n".join(lines), fixed_count
