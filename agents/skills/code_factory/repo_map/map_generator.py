"""
代码地图生成器 (Aider 风格)

基准文档: MASTER.md v4.6
版本: v4.2

功能:
- AST 解析提取函数/类签名
- 生成紧凑代码地图用于 LLM 上下文
- 支持多种输出格式
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set
import ast


@dataclass
class FunctionSig:
    """函数签名"""

    name: str
    file: str
    line: int
    params: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False
    docstring: Optional[str] = None

    def to_compact(self) -> str:
        """生成紧凑表示"""
        async_prefix = "async " if self.is_async else ""
        params_str = ", ".join(self.params)
        ret = f" -> {self.return_type}" if self.return_type else ""
        return f"{async_prefix}def {self.name}({params_str}){ret}"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "file": self.file,
            "line": self.line,
            "params": self.params,
            "return_type": self.return_type,
            "is_async": self.is_async,
        }


@dataclass
class ClassDef:
    """类定义"""

    name: str
    file: str
    line: int
    methods: List[str] = field(default_factory=list)
    bases: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    docstring: Optional[str] = None

    def to_compact(self) -> str:
        """生成紧凑表示"""
        bases_str = f"({', '.join(self.bases)})" if self.bases else ""
        methods_str = ", ".join(self.methods[:5])
        if len(self.methods) > 5:
            methods_str += f", ... +{len(self.methods) - 5}"
        return f"class {self.name}{bases_str}: [{methods_str}]"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "file": self.file,
            "line": self.line,
            "methods": self.methods,
            "bases": self.bases,
        }


@dataclass
class RepoMap:
    """代码地图"""

    functions: Dict[str, FunctionSig] = field(default_factory=dict)
    classes: Dict[str, ClassDef] = field(default_factory=dict)
    imports: Dict[str, List[str]] = field(default_factory=dict)  # file -> imports

    def add_function(self, func: FunctionSig):
        """添加函数"""
        key = f"{func.file}:{func.name}"
        self.functions[key] = func

    def add_class(self, cls: ClassDef):
        """添加类"""
        key = f"{cls.file}:{cls.name}"
        self.classes[key] = cls

    def get_files(self) -> Set[str]:
        """获取所有文件"""
        files = set()
        for func in self.functions.values():
            files.add(func.file)
        for cls in self.classes.values():
            files.add(cls.file)
        return files

    def to_prompt(self, max_tokens: int = 2000) -> str:
        """生成 LLM 提示词格式

        Args:
            max_tokens: 最大 token 数 (估算)

        Returns:
            格式化的代码地图
        """
        lines = ["# 代码地图", ""]

        # 按文件分组
        files = sorted(self.get_files())

        for file in files:
            lines.append(f"## {file}")

            # 类
            for key, cls in sorted(self.classes.items()):
                if cls.file == file:
                    lines.append(f"- {cls.to_compact()}")

            # 独立函数 (不在类中)
            for key, func in sorted(self.functions.items()):
                if func.file == file:
                    lines.append(f"- {func.to_compact()}")

            lines.append("")

        result = "\n".join(lines)

        # 截断
        max_chars = max_tokens * 4  # 估算每个 token 4 个字符
        if len(result) > max_chars:
            result = result[:max_chars] + "\n... (truncated)"

        return result

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "functions": {k: v.to_dict() for k, v in self.functions.items()},
            "classes": {k: v.to_dict() for k, v in self.classes.items()},
        }

    def filter_by_files(self, files: List[str]) -> "RepoMap":
        """按文件过滤"""
        filtered = RepoMap()
        for key, func in self.functions.items():
            if func.file in files:
                filtered.functions[key] = func
        for key, cls in self.classes.items():
            if cls.file in files:
                filtered.classes[key] = cls
        return filtered

    def search(self, query: str) -> "RepoMap":
        """搜索代码地图"""
        query_lower = query.lower()
        filtered = RepoMap()

        for key, func in self.functions.items():
            if query_lower in func.name.lower() or query_lower in func.file.lower():
                filtered.functions[key] = func

        for key, cls in self.classes.items():
            if query_lower in cls.name.lower() or query_lower in cls.file.lower():
                filtered.classes[key] = cls

        return filtered


class RepoMapGenerator:
    """代码地图生成器"""

    # 默认排除目录
    EXCLUDE_DIRS: Set[str] = {
        "__pycache__",
        ".git",
        "node_modules",
        "venv",
        ".venv",
        ".pytest_cache",
        ".mypy_cache",
        "dist",
        "build",
        ".next",
    }

    def __init__(self, project_dir: Path):
        """初始化

        Args:
            project_dir: 项目根目录
        """
        self.project_dir = Path(project_dir)

    def generate(
        self,
        include_dirs: Optional[List[str]] = None,
        exclude_dirs: Optional[Set[str]] = None,
        max_files: int = 100,
    ) -> RepoMap:
        """生成代码地图

        Args:
            include_dirs: 包含的目录 (相对路径)
            exclude_dirs: 排除的目录
            max_files: 最大文件数

        Returns:
            RepoMap
        """
        repo_map = RepoMap()
        exclude = exclude_dirs or self.EXCLUDE_DIRS

        file_count = 0

        for py_file in self.project_dir.rglob("*.py"):
            # 检查排除
            if any(ex in py_file.parts for ex in exclude):
                continue

            # 检查包含
            if include_dirs:
                rel_path = str(py_file.relative_to(self.project_dir))
                if not any(rel_path.startswith(d) for d in include_dirs):
                    continue

            # 解析文件
            self._parse_file(py_file, repo_map)

            file_count += 1
            if file_count >= max_files:
                break

        return repo_map

    def _parse_file(self, path: Path, repo_map: RepoMap):
        """解析单个文件"""
        try:
            content = path.read_text(encoding="utf-8")
            tree = ast.parse(content)
            rel_path = str(path.relative_to(self.project_dir))

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # 跳过类方法 (在 ClassDef 中处理)
                    if self._is_method(node, tree):
                        continue

                    func = self._parse_function(node, rel_path)
                    repo_map.add_function(func)

                elif isinstance(node, ast.ClassDef):
                    cls = self._parse_class(node, rel_path)
                    repo_map.add_class(cls)

        except Exception:
            pass  # 忽略解析错误

    def _is_method(self, node: ast.AST, tree: ast.Module) -> bool:
        """检查是否是类方法"""
        for parent in ast.walk(tree):
            if isinstance(parent, ast.ClassDef):
                for child in parent.body:
                    if child is node:
                        return True
        return False

    def _parse_function(self, node, rel_path: str) -> FunctionSig:
        """解析函数"""
        # 参数
        params = []
        for arg in node.args.args:
            param = arg.arg
            if arg.annotation:
                try:
                    param += f": {ast.unparse(arg.annotation)}"
                except Exception:
                    pass
            params.append(param)

        # 返回类型
        return_type = None
        if node.returns:
            try:
                return_type = ast.unparse(node.returns)
            except Exception:
                pass

        # 装饰器
        decorators = []
        for dec in node.decorator_list:
            try:
                decorators.append(ast.unparse(dec))
            except Exception:
                pass

        # 文档字符串
        docstring = ast.get_docstring(node)

        return FunctionSig(
            name=node.name,
            file=rel_path,
            line=node.lineno,
            params=params,
            return_type=return_type,
            decorators=decorators,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            docstring=docstring[:100] if docstring else None,
        )

    def _parse_class(self, node: ast.ClassDef, rel_path: str) -> ClassDef:
        """解析类"""
        # 方法
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(item.name)

        # 基类
        bases = []
        for base in node.bases:
            try:
                bases.append(ast.unparse(base))
            except Exception:
                pass

        # 装饰器
        decorators = []
        for dec in node.decorator_list:
            try:
                decorators.append(ast.unparse(dec))
            except Exception:
                pass

        # 文档字符串
        docstring = ast.get_docstring(node)

        return ClassDef(
            name=node.name,
            file=rel_path,
            line=node.lineno,
            methods=methods,
            bases=bases,
            decorators=decorators,
            docstring=docstring[:100] if docstring else None,
        )

    def generate_for_module(self, module_path: str) -> RepoMap:
        """为指定模块生成代码地图

        Args:
            module_path: 模块路径 (如 "backend/services")

        Returns:
            RepoMap
        """
        return self.generate(include_dirs=[module_path])
