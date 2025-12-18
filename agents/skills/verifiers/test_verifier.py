"""
测试验证器

验证代码的测试覆盖:
1. 检查测试文件是否存在
2. 运行现有测试
3. 生成测试建议
4. 验证测试质量

借鉴 Qodo Cover 的理念
"""

import ast
import os
import re
import subprocess
import tempfile
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

# 测试文件命名模式
TEST_FILE_PATTERNS = [
    "test_{name}.py",
    "{name}_test.py",
    "tests/test_{name}.py",
    "tests/{name}_test.py",
]

# 需要测试的函数特征
TESTABLE_FUNCTION_PATTERNS = [
    r"^(create|update|delete|get|list|process|validate|calculate|convert|parse)",
    r"^(handle|check|verify|ensure|generate|build|transform)",
    r"_handler$",
    r"_service$",
]

# 不需要测试的函数
SKIP_TEST_PATTERNS = [
    r"^_",           # 私有函数
    r"^__",          # 魔术方法
    r"^main$",       # 入口函数
    r"^setup$",      # 设置函数
    r"^teardown$",   # 清理函数
]

# 测试质量指标阈值
MIN_COVERAGE_THRESHOLD = 70  # 最低覆盖率
MIN_ASSERTIONS_PER_TEST = 1  # 每个测试最少断言数


class TestVerifier(BaseVerifier):
    """
    测试验证器

    检测:
    1. 测试文件是否存在
    2. 测试是否通过
    3. 测试覆盖率
    4. 测试质量 (断言数量、边界情况)
    """

    @property
    def name(self) -> str:
        return "TestVerifier"

    @property
    def category(self) -> IssueCategory:
        return IssueCategory.TEST

    @property
    def priority(self) -> int:
        return 50  # 最后运行

    def __init__(self, context: Optional[VerifyContext] = None):
        super().__init__(context)
        self._test_results_cache: Dict[str, bool] = {}

    def verify(
        self,
        file_path: str,
        content: str,
        run_tests: bool = False,
        **kwargs
    ) -> VerifyResult:
        """执行测试验证"""
        issues: List[VerifyIssue] = []
        details: List[str] = []
        metrics: Dict[str, Any] = {
            "testable_functions": 0,
            "covered_functions": 0,
            "test_file_exists": False,
            "tests_passed": None,
            "test_count": 0,
            "assertion_count": 0,
            "coverage_estimate": 0.0,
        }

        # 只验证 Python 文件
        if not file_path.endswith(".py"):
            return VerifyResult(
                passed=True,
                category=self.category,
                issues=[],
                metrics=metrics,
                details=["跳过: 非 Python 文件"],
            )

        # 跳过测试文件自身
        if self._is_test_file(file_path):
            test_issues = self._verify_test_quality(file_path, content)
            issues.extend(test_issues)
            metrics["test_count"] = self._count_tests(content)
            metrics["assertion_count"] = self._count_assertions(content)

            return VerifyResult(
                passed=len([i for i in issues if i.severity == IssueSeverity.ERROR]) == 0,
                category=self.category,
                issues=issues,
                metrics=metrics,
                details=["测试文件质量检查完成"],
            )

        # 解析源文件
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return VerifyResult(
                passed=True,
                category=self.category,
                issues=[],
                metrics=metrics,
                details=["跳过: 语法错误由 AST 验证器处理"],
            )

        # 提取可测试的函数/类
        testable_items = self._extract_testable_items(tree)
        metrics["testable_functions"] = len(testable_items)

        if not testable_items:
            return VerifyResult(
                passed=True,
                category=self.category,
                issues=[],
                metrics=metrics,
                details=["无需测试: 没有可测试的函数"],
            )

        # 查找对应的测试文件
        test_file = self._find_test_file(file_path)
        metrics["test_file_exists"] = test_file is not None

        if not test_file:
            issues.append(create_issue(
                file_path=file_path,
                line=1,
                category=IssueCategory.TEST,
                code="TST-001",
                message="缺少测试文件",
                suggestion=self._suggest_test_file_path(file_path),
                severity=IssueSeverity.WARNING,
            ))
        else:
            # 检查测试覆盖
            coverage_issues = self._check_test_coverage(
                file_path, testable_items, test_file
            )
            issues.extend(coverage_issues)
            metrics["covered_functions"] = len(testable_items) - len([
                i for i in coverage_issues if i.code == "TST-002"
            ])

        # 运行测试 (可选)
        if run_tests and test_file:
            test_result = self._run_tests(test_file)
            metrics["tests_passed"] = test_result["passed"]
            metrics["test_count"] = test_result["count"]

            if not test_result["passed"]:
                issues.append(create_issue(
                    file_path=file_path,
                    line=1,
                    category=IssueCategory.TEST,
                    code="TST-003",
                    message=f"测试失败: {test_result['failures']} 个失败",
                    suggestion="修复失败的测试用例",
                    severity=IssueSeverity.ERROR,
                    evidence=test_result.get("output", ""),
                ))

        # 计算覆盖率估算
        if metrics["testable_functions"] > 0:
            metrics["coverage_estimate"] = (
                metrics["covered_functions"] / metrics["testable_functions"] * 100
            )

        # 汇总
        error_count = len([i for i in issues if i.severity == IssueSeverity.ERROR])
        passed = error_count == 0

        if passed:
            details.append(f"测试验证通过: {metrics['covered_functions']}/{metrics['testable_functions']} 函数已覆盖")
        else:
            details.append(f"发现 {error_count} 个测试问题")

        return VerifyResult(
            passed=passed,
            category=self.category,
            issues=issues,
            metrics=metrics,
            details=details,
        )

    def _is_test_file(self, file_path: str) -> bool:
        """判断是否是测试文件"""
        name = Path(file_path).name
        return name.startswith("test_") or name.endswith("_test.py")

    def _extract_testable_items(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """提取可测试的函数和类"""
        items = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if self._should_test_function(node.name):
                    items.append({
                        "type": "function",
                        "name": node.name,
                        "line": node.lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "is_async": False,
                    })

            elif isinstance(node, ast.AsyncFunctionDef):
                if self._should_test_function(node.name):
                    items.append({
                        "type": "function",
                        "name": node.name,
                        "line": node.lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "is_async": True,
                    })

            elif isinstance(node, ast.ClassDef):
                # 提取类的公共方法
                methods = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if self._should_test_function(item.name):
                            methods.append(item.name)

                if methods:
                    items.append({
                        "type": "class",
                        "name": node.name,
                        "line": node.lineno,
                        "methods": methods,
                    })

        return items

    def _should_test_function(self, name: str) -> bool:
        """判断函数是否需要测试"""
        # 跳过不需要测试的
        for pattern in SKIP_TEST_PATTERNS:
            if re.match(pattern, name):
                return False

        # 检查是否匹配需要测试的模式
        for pattern in TESTABLE_FUNCTION_PATTERNS:
            if re.search(pattern, name, re.IGNORECASE):
                return True

        # 默认公共函数需要测试
        return not name.startswith("_")

    def _find_test_file(self, source_file: str) -> Optional[str]:
        """查找对应的测试文件"""
        path = Path(source_file)
        name = path.stem  # 不含扩展名的文件名
        parent = path.parent

        # 尝试各种测试文件位置
        possible_locations = [
            parent / f"test_{name}.py",
            parent / f"{name}_test.py",
            parent / "tests" / f"test_{name}.py",
            parent / "tests" / f"{name}_test.py",
            parent.parent / "tests" / f"test_{name}.py",
            parent.parent / "tests" / path.parent.name / f"test_{name}.py",
        ]

        # 如果有 context，使用项目根目录
        if self.context:
            root = self.context.project_root
            rel_path = path.relative_to(root) if path.is_relative_to(root) else path

            # 常见的测试目录结构
            possible_locations.extend([
                root / "tests" / f"test_{name}.py",
                root / "tests" / rel_path.parent / f"test_{name}.py",
                root / "backend" / "tests" / f"test_{name}.py",
            ])

        for loc in possible_locations:
            if loc.exists():
                return str(loc)

        return None

    def _suggest_test_file_path(self, source_file: str) -> str:
        """建议测试文件路径"""
        path = Path(source_file)
        name = path.stem

        if "backend" in path.parts:
            # 后端测试放在 backend/tests/
            idx = path.parts.index("backend")
            rel_parts = path.parts[idx + 1:-1]  # 去掉 backend 和文件名
            test_path = Path("backend/tests") / "/".join(rel_parts) / f"test_{name}.py"
        else:
            test_path = path.parent / "tests" / f"test_{name}.py"

        return f"创建测试文件: {test_path}"

    def _check_test_coverage(
        self,
        source_file: str,
        testable_items: List[Dict[str, Any]],
        test_file: str
    ) -> List[VerifyIssue]:
        """检查测试覆盖情况"""
        issues = []

        try:
            with open(test_file, "r", encoding="utf-8") as f:
                test_content = f.read()
        except Exception:
            return issues

        # 检查每个可测试项是否有对应测试
        for item in testable_items:
            name = item["name"]

            # 查找测试函数/方法
            test_patterns = [
                f"def test_{name}",
                f"def test_{name.lower()}",
                f"async def test_{name}",
                f"def test.*{name}",  # 模糊匹配
            ]

            found = any(
                re.search(pattern, test_content, re.IGNORECASE)
                for pattern in test_patterns
            )

            if not found:
                issues.append(create_issue(
                    file_path=source_file,
                    line=item["line"],
                    category=IssueCategory.TEST,
                    code="TST-002",
                    message=f"缺少测试: {item['type']} '{name}'",
                    suggestion=self._generate_test_suggestion(item),
                    severity=IssueSeverity.WARNING,
                ))

        return issues

    def _generate_test_suggestion(self, item: Dict[str, Any]) -> str:
        """生成测试建议"""
        name = item["name"]
        item_type = item["type"]

        if item_type == "function":
            args = item.get("args", [])
            is_async = item.get("is_async", False)

            if is_async:
                template = f"""
@pytest.mark.asyncio
async def test_{name}():
    # Arrange
    # TODO: 设置测试数据

    # Act
    result = await {name}({', '.join(['...' for _ in args])})

    # Assert
    assert result is not None
"""
            else:
                template = f"""
def test_{name}():
    # Arrange
    # TODO: 设置测试数据

    # Act
    result = {name}({', '.join(['...' for _ in args])})

    # Assert
    assert result is not None
"""
        else:  # class
            methods = item.get("methods", [])
            template = f"""
class Test{name}:
    def test_init(self):
        instance = {name}()
        assert instance is not None

    # TODO: 为以下方法添加测试
    # {', '.join(methods)}
"""

        return f"建议添加测试:\n```python{template}```"

    def _verify_test_quality(
        self,
        test_file: str,
        content: str
    ) -> List[VerifyIssue]:
        """验证测试文件质量"""
        issues = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        # 检查每个测试函数
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("test_"):
                    test_issues = self._check_single_test(test_file, node, content)
                    issues.extend(test_issues)

        return issues

    def _check_single_test(
        self,
        test_file: str,
        node: ast.FunctionDef,
        content: str
    ) -> List[VerifyIssue]:
        """检查单个测试函数质量"""
        issues = []

        # 计算断言数量
        assertion_count = 0
        for child in ast.walk(node):
            if isinstance(child, ast.Assert):
                assertion_count += 1
            elif isinstance(child, ast.Call):
                # 检查 pytest 断言
                if isinstance(child.func, ast.Attribute):
                    if child.func.attr in ("assert_called", "assert_called_once",
                                           "assert_called_with", "assert_not_called"):
                        assertion_count += 1
                elif isinstance(child.func, ast.Name):
                    if child.func.id in ("assertEqual", "assertTrue", "assertFalse",
                                        "assertRaises", "assertIn"):
                        assertion_count += 1

        if assertion_count < MIN_ASSERTIONS_PER_TEST:
            issues.append(create_issue(
                file_path=test_file,
                line=node.lineno,
                category=IssueCategory.TEST,
                code="TST-004",
                message=f"测试 '{node.name}' 缺少断言",
                suggestion="每个测试至少应该有一个 assert 语句",
                severity=IssueSeverity.WARNING,
            ))

        # 检查测试是否只是 pass
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            issues.append(create_issue(
                file_path=test_file,
                line=node.lineno,
                category=IssueCategory.TEST,
                code="TST-005",
                message=f"测试 '{node.name}' 是空的 (只有 pass)",
                suggestion="实现测试逻辑或删除该测试",
                severity=IssueSeverity.WARNING,
            ))

        # 检查测试名称是否描述性
        if node.name == "test_" or len(node.name) < 8:
            issues.append(create_issue(
                file_path=test_file,
                line=node.lineno,
                category=IssueCategory.TEST,
                code="TST-006",
                message=f"测试名称 '{node.name}' 不够描述性",
                suggestion="使用描述性名称，如 test_function_should_return_x_when_y",
                severity=IssueSeverity.INFO,
            ))

        return issues

    def _count_tests(self, content: str) -> int:
        """统计测试数量"""
        try:
            tree = ast.parse(content)
            count = 0
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name.startswith("test_"):
                        count += 1
            return count
        except SyntaxError:
            return 0

    def _count_assertions(self, content: str) -> int:
        """统计断言数量"""
        try:
            tree = ast.parse(content)
            count = 0
            for node in ast.walk(tree):
                if isinstance(node, ast.Assert):
                    count += 1
            return count
        except SyntaxError:
            return 0

    def _run_tests(self, test_file: str) -> Dict[str, Any]:
        """运行测试文件"""
        result = {
            "passed": False,
            "count": 0,
            "failures": 0,
            "output": "",
        }

        try:
            # 使用 pytest 运行
            proc = subprocess.run(
                ["python", "-m", "pytest", test_file, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.context.project_root) if self.context else None,
            )

            result["output"] = proc.stdout + proc.stderr
            result["passed"] = proc.returncode == 0

            # 解析测试数量
            match = re.search(r"(\d+) passed", result["output"])
            if match:
                result["count"] = int(match.group(1))

            match = re.search(r"(\d+) failed", result["output"])
            if match:
                result["failures"] = int(match.group(1))

        except subprocess.TimeoutExpired:
            result["output"] = "测试超时"
        except FileNotFoundError:
            result["output"] = "pytest 未安装"
        except Exception as e:
            result["output"] = f"运行测试时出错: {str(e)}"

        return result

    def generate_test_template(
        self,
        source_file: str,
        content: str
    ) -> str:
        """生成完整的测试文件模板"""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return "# 无法解析源文件"

        testable_items = self._extract_testable_items(tree)
        module_name = Path(source_file).stem

        lines = [
            '"""',
            f"Tests for {module_name}",
            '"""',
            "",
            "import pytest",
            f"from {self._get_import_path(source_file)} import (",
        ]

        # 添加导入
        for item in testable_items:
            lines.append(f"    {item['name']},")
        lines.append(")")
        lines.append("")
        lines.append("")

        # 生成测试
        for item in testable_items:
            if item["type"] == "function":
                is_async = item.get("is_async", False)
                if is_async:
                    lines.extend([
                        "@pytest.mark.asyncio",
                        f"async def test_{item['name']}():",
                        '    """Test {item["name"]}"""',
                        "    # Arrange",
                        "    # TODO: Setup test data",
                        "",
                        "    # Act",
                        f"    result = await {item['name']}()",
                        "",
                        "    # Assert",
                        "    assert result is not None",
                        "",
                        "",
                    ])
                else:
                    lines.extend([
                        f"def test_{item['name']}():",
                        f'    """Test {item["name"]}"""',
                        "    # Arrange",
                        "    # TODO: Setup test data",
                        "",
                        "    # Act",
                        f"    result = {item['name']}()",
                        "",
                        "    # Assert",
                        "    assert result is not None",
                        "",
                        "",
                    ])
            else:  # class
                lines.extend([
                    f"class Test{item['name']}:",
                    f'    """Tests for {item["name"]} class"""',
                    "",
                    "    def test_init(self):",
                    f"        instance = {item['name']}()",
                    "        assert instance is not None",
                    "",
                ])
                for method in item.get("methods", []):
                    lines.extend([
                        f"    def test_{method}(self):",
                        f'        """Test {method}"""',
                        "        # TODO: Implement",
                        "        pass",
                        "",
                    ])
                lines.append("")

        return "\n".join(lines)

    def _get_import_path(self, source_file: str) -> str:
        """获取导入路径"""
        path = Path(source_file)

        if self.context:
            try:
                rel_path = path.relative_to(self.context.project_root)
                return str(rel_path.with_suffix("")).replace(os.sep, ".")
            except ValueError:
                pass

        return path.stem
