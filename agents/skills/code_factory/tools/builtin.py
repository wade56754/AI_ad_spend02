"""
内置工具集 v5.0

提供常用的 Agent 工具:
- RunTestsTool: 运行测试
- LintCodeTool: 代码检查
- SearchDocsTool: 搜索文档
- GitCommitTool: Git 操作
- RunMigrationTool: 数据库迁移
- FileReadTool: 读取文件
- FileWriteTool: 写入文件

基准文档: MASTER.md v4.6
版本: v5.0
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess
import os

from .base import Tool, ToolResult, ToolStatus


class RunTestsTool(Tool):
    """
    运行测试工具
    
    支持:
    - pytest (Python)
    - jest/vitest (JavaScript/TypeScript)
    
    使用方式:
    ```python
    tool = RunTestsTool(project_dir=Path("./"))
    result = tool.run(
        path="tests/",
        pattern="test_*.py",
        verbose=True,
    )
    ```
    """
    
    name = "run_tests"
    description = "运行测试用例"
    timeout = 300  # 5 分钟
    
    def __init__(self, project_dir: Path = None, **config):
        super().__init__(**config)
        self.project_dir = project_dir or Path.cwd()
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "测试路径 (文件或目录)",
                    "default": "tests/",
                },
                "pattern": {
                    "type": "string",
                    "description": "测试文件模式",
                    "default": "test_*.py",
                },
                "verbose": {
                    "type": "boolean",
                    "description": "详细输出",
                    "default": False,
                },
                "framework": {
                    "type": "string",
                    "description": "测试框架",
                    "enum": ["pytest", "jest", "vitest", "auto"],
                    "default": "auto",
                },
            },
            "required": [],
        }
    
    def execute(
        self,
        path: str = "tests/",
        pattern: str = "test_*.py",
        verbose: bool = False,
        framework: str = "auto",
    ) -> ToolResult:
        """执行测试"""
        # 自动检测框架
        if framework == "auto":
            framework = self._detect_framework()
        
        # 构建命令
        if framework == "pytest":
            cmd = self._build_pytest_cmd(path, pattern, verbose)
        elif framework in ("jest", "vitest"):
            cmd = self._build_js_test_cmd(path, framework, verbose)
        else:
            return ToolResult.fail(f"不支持的测试框架: {framework}")
        
        # 执行命令
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            
            output = result.stdout + result.stderr
            
            if result.returncode == 0:
                return ToolResult.ok(
                    output=output,
                    passed=True,
                    command=" ".join(cmd),
                )
            else:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    output=output,
                    error=f"测试失败 (退出码: {result.returncode})",
                    metadata={
                        "passed": False,
                        "command": " ".join(cmd),
                        "returncode": result.returncode,
                    },
                )
        except subprocess.TimeoutExpired:
            return ToolResult(
                status=ToolStatus.TIMEOUT,
                error=f"测试超时 ({self.timeout}秒)",
            )
        except Exception as e:
            return ToolResult.fail(str(e))
    
    def _detect_framework(self) -> str:
        """检测测试框架"""
        # 检查 Python 项目
        if (self.project_dir / "pytest.ini").exists() or \
           (self.project_dir / "pyproject.toml").exists():
            return "pytest"
        
        # 检查 JS 项目
        pkg_json = self.project_dir / "package.json"
        if pkg_json.exists():
            import json
            with open(pkg_json) as f:
                pkg = json.load(f)
            
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "vitest" in deps:
                return "vitest"
            elif "jest" in deps:
                return "jest"
        
        return "pytest"  # 默认
    
    def _build_pytest_cmd(self, path: str, pattern: str, verbose: bool) -> List[str]:
        """构建 pytest 命令"""
        cmd = ["python", "-m", "pytest", path]
        if verbose:
            cmd.append("-v")
        return cmd
    
    def _build_js_test_cmd(self, path: str, framework: str, verbose: bool) -> List[str]:
        """构建 JS 测试命令"""
        if framework == "vitest":
            cmd = ["npx", "vitest", "run"]
        else:
            cmd = ["npx", "jest"]
        
        if path:
            cmd.append(path)
        if verbose:
            cmd.append("--verbose")
        
        return cmd


class LintCodeTool(Tool):
    """
    代码检查工具
    
    支持:
    - ruff (Python)
    - eslint (JavaScript/TypeScript)
    - mypy (Python 类型检查)
    """
    
    name = "lint_code"
    description = "检查代码质量"
    timeout = 120
    
    def __init__(self, project_dir: Path = None, **config):
        super().__init__(**config)
        self.project_dir = project_dir or Path.cwd()
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "检查路径",
                    "default": ".",
                },
                "linter": {
                    "type": "string",
                    "description": "检查工具",
                    "enum": ["ruff", "eslint", "mypy", "auto"],
                    "default": "auto",
                },
                "fix": {
                    "type": "boolean",
                    "description": "是否自动修复",
                    "default": False,
                },
            },
            "required": [],
        }
    
    def execute(
        self,
        path: str = ".",
        linter: str = "auto",
        fix: bool = False,
    ) -> ToolResult:
        """执行代码检查"""
        # 自动检测
        if linter == "auto":
            linter = self._detect_linter(path)
        
        # 构建命令
        if linter == "ruff":
            cmd = ["ruff", "check", path]
            if fix:
                cmd.append("--fix")
        elif linter == "eslint":
            cmd = ["npx", "eslint", path]
            if fix:
                cmd.append("--fix")
        elif linter == "mypy":
            cmd = ["mypy", path]
        else:
            return ToolResult.fail(f"不支持的检查工具: {linter}")
        
        # 执行
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            
            output = result.stdout + result.stderr
            
            return ToolResult.ok(
                output=output,
                passed=result.returncode == 0,
                command=" ".join(cmd),
                issues_found=result.returncode != 0,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(status=ToolStatus.TIMEOUT, error="检查超时")
        except Exception as e:
            return ToolResult.fail(str(e))
    
    def _detect_linter(self, path: str) -> str:
        """检测检查工具"""
        if path.endswith(".py") or (self.project_dir / "backend").exists():
            return "ruff"
        elif path.endswith((".ts", ".tsx", ".js", ".jsx")):
            return "eslint"
        return "ruff"


class SearchDocsTool(Tool):
    """
    搜索文档工具
    
    使用 RAG 知识库搜索相关文档
    """
    
    name = "search_docs"
    description = "搜索项目文档和代码"
    
    def __init__(self, knowledge_base=None, **config):
        super().__init__(**config)
        self.knowledge_base = knowledge_base
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询",
                },
                "top_k": {
                    "type": "integer",
                    "description": "返回结果数量",
                    "default": 5,
                },
                "source": {
                    "type": "string",
                    "description": "搜索范围",
                    "enum": ["all", "sot", "code"],
                    "default": "all",
                },
            },
            "required": ["query"],
        }
    
    def execute(
        self,
        query: str,
        top_k: int = 5,
        source: str = "all",
    ) -> ToolResult:
        """执行搜索"""
        if not self.knowledge_base:
            return ToolResult.fail("知识库未配置")
        
        try:
            if source == "sot":
                results = self.knowledge_base.search_sot(query, top_k)
            elif source == "code":
                results = self.knowledge_base.search_code(query, top_k)
            else:
                results = self.knowledge_base.search(query, top_k=top_k)
            
            # 格式化结果
            formatted = []
            for r in results:
                formatted.append({
                    "path": r.chunk.metadata.get("path", "unknown"),
                    "score": r.score,
                    "content": r.chunk.content[:200] + "...",
                })
            
            return ToolResult.ok(
                output=formatted,
                total_found=len(results),
            )
        except Exception as e:
            return ToolResult.fail(str(e))


class GitCommitTool(Tool):
    """
    Git 操作工具
    
    支持:
    - 查看状态
    - 添加文件
    - 提交更改
    """
    
    name = "git_commit"
    description = "Git 版本控制操作"
    requires_confirmation = True
    
    def __init__(self, project_dir: Path = None, **config):
        super().__init__(**config)
        self.project_dir = project_dir or Path.cwd()
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Git 操作",
                    "enum": ["status", "add", "commit", "diff"],
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "文件列表",
                    "default": ["."],
                },
                "message": {
                    "type": "string",
                    "description": "提交消息",
                },
            },
            "required": ["action"],
        }
    
    def execute(
        self,
        action: str,
        files: List[str] = None,
        message: str = None,
    ) -> ToolResult:
        """执行 Git 操作"""
        files = files or ["."]
        
        try:
            if action == "status":
                cmd = ["git", "status", "--porcelain"]
            elif action == "diff":
                cmd = ["git", "diff", "--stat"]
            elif action == "add":
                cmd = ["git", "add"] + files
            elif action == "commit":
                if not message:
                    return ToolResult.fail("提交需要消息")
                cmd = ["git", "commit", "-m", message]
            else:
                return ToolResult.fail(f"不支持的操作: {action}")
            
            result = subprocess.run(
                cmd,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
            )
            
            output = result.stdout + result.stderr
            
            return ToolResult.ok(
                output=output,
                command=" ".join(cmd),
                success=result.returncode == 0,
            )
        except Exception as e:
            return ToolResult.fail(str(e))


class RunMigrationTool(Tool):
    """
    数据库迁移工具
    
    支持 Alembic 迁移
    """
    
    name = "run_migration"
    description = "运行数据库迁移"
    requires_confirmation = True
    is_dangerous = True
    
    def __init__(self, project_dir: Path = None, **config):
        super().__init__(**config)
        self.project_dir = project_dir or Path.cwd()
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "迁移操作",
                    "enum": ["upgrade", "downgrade", "current", "history", "generate"],
                },
                "revision": {
                    "type": "string",
                    "description": "目标版本",
                    "default": "head",
                },
                "message": {
                    "type": "string",
                    "description": "迁移消息 (用于 generate)",
                },
            },
            "required": ["action"],
        }
    
    def execute(
        self,
        action: str,
        revision: str = "head",
        message: str = None,
    ) -> ToolResult:
        """执行迁移"""
        backend_dir = self.project_dir / "backend"
        
        try:
            if action == "upgrade":
                cmd = ["alembic", "upgrade", revision]
            elif action == "downgrade":
                cmd = ["alembic", "downgrade", revision]
            elif action == "current":
                cmd = ["alembic", "current"]
            elif action == "history":
                cmd = ["alembic", "history"]
            elif action == "generate":
                if not message:
                    return ToolResult.fail("生成迁移需要消息")
                cmd = ["alembic", "revision", "--autogenerate", "-m", message]
            else:
                return ToolResult.fail(f"不支持的操作: {action}")
            
            result = subprocess.run(
                cmd,
                cwd=backend_dir,
                capture_output=True,
                text=True,
            )
            
            output = result.stdout + result.stderr
            
            return ToolResult.ok(
                output=output,
                command=" ".join(cmd),
                success=result.returncode == 0,
            )
        except Exception as e:
            return ToolResult.fail(str(e))


class FileReadTool(Tool):
    """
    文件读取工具
    """
    
    name = "file_read"
    description = "读取文件内容"
    
    def __init__(self, project_dir: Path = None, **config):
        super().__init__(**config)
        self.project_dir = project_dir or Path.cwd()
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "文件路径",
                },
                "start_line": {
                    "type": "integer",
                    "description": "起始行",
                    "default": 1,
                },
                "end_line": {
                    "type": "integer",
                    "description": "结束行",
                },
            },
            "required": ["path"],
        }
    
    def execute(
        self,
        path: str,
        start_line: int = 1,
        end_line: int = None,
    ) -> ToolResult:
        """读取文件"""
        file_path = self.project_dir / path
        
        if not file_path.exists():
            return ToolResult.fail(f"文件不存在: {path}")
        
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")
            
            # 行号处理
            if end_line:
                lines = lines[start_line - 1:end_line]
            elif start_line > 1:
                lines = lines[start_line - 1:]
            
            return ToolResult.ok(
                output="\n".join(lines),
                total_lines=len(content.split("\n")),
                path=str(file_path),
            )
        except Exception as e:
            return ToolResult.fail(str(e))


class FileWriteTool(Tool):
    """
    文件写入工具
    """
    
    name = "file_write"
    description = "写入文件内容"
    requires_confirmation = True
    
    def __init__(self, project_dir: Path = None, **config):
        super().__init__(**config)
        self.project_dir = project_dir or Path.cwd()
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "文件路径",
                },
                "content": {
                    "type": "string",
                    "description": "文件内容",
                },
                "mode": {
                    "type": "string",
                    "description": "写入模式",
                    "enum": ["overwrite", "append"],
                    "default": "overwrite",
                },
            },
            "required": ["path", "content"],
        }
    
    def execute(
        self,
        path: str,
        content: str,
        mode: str = "overwrite",
    ) -> ToolResult:
        """写入文件"""
        file_path = self.project_dir / path
        
        try:
            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if mode == "append":
                with open(file_path, "a", encoding="utf-8") as f:
                    f.write(content)
            else:
                file_path.write_text(content, encoding="utf-8")
            
            return ToolResult.ok(
                output=f"已写入 {len(content)} 字符到 {path}",
                path=str(file_path),
                chars_written=len(content),
            )
        except Exception as e:
            return ToolResult.fail(str(e))


# ============================================================
# 注册内置工具
# ============================================================

def register_builtin_tools(registry, project_dir: Path = None):
    """注册所有内置工具
    
    Args:
        registry: ToolRegistry 实例
        project_dir: 项目目录
    """
    project_dir = project_dir or Path.cwd()
    
    registry.register(RunTestsTool(project_dir=project_dir))
    registry.register(LintCodeTool(project_dir=project_dir))
    registry.register(SearchDocsTool())
    registry.register(GitCommitTool(project_dir=project_dir))
    registry.register(RunMigrationTool(project_dir=project_dir))
    registry.register(FileReadTool(project_dir=project_dir))
    registry.register(FileWriteTool(project_dir=project_dir))

