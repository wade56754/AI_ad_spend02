"""
仓库地图模块单元测试

基准文档: MASTER.md v4.6
版本: v4.2
"""

import pytest
from pathlib import Path

from agents.skills.code_factory.repo_map.map_generator import (
    RepoMapGenerator,
    RepoMap,
    FunctionSig,
    ClassDef,
)


class TestRepoMap:
    """仓库地图测试"""

    def test_create_empty_repo_map(self):
        """测试创建空地图"""
        repo_map = RepoMap()

        assert len(repo_map.functions) == 0
        assert len(repo_map.classes) == 0

    def test_add_function(self):
        """测试添加函数"""
        repo_map = RepoMap()
        func = FunctionSig(
            name="get_user",
            file="src/services/user.py",
            line=10,
            params=["user_id: str"],
            return_type="User",
        )
        repo_map.add_function(func)

        assert len(repo_map.functions) == 1
        assert "src/services/user.py:get_user" in repo_map.functions

    def test_add_class(self):
        """测试添加类"""
        repo_map = RepoMap()
        cls = ClassDef(
            name="UserService",
            file="src/services/user.py",
            line=20,
            methods=["get_user", "create_user"],
            bases=["BaseService"],
        )
        repo_map.add_class(cls)

        assert len(repo_map.classes) == 1
        assert "src/services/user.py:UserService" in repo_map.classes

    def test_get_files(self):
        """测试获取文件列表"""
        repo_map = RepoMap()
        repo_map.add_function(FunctionSig(
            name="func1",
            file="src/a.py",
            line=1,
        ))
        repo_map.add_class(ClassDef(
            name="Class1",
            file="src/b.py",
            line=1,
        ))

        files = repo_map.get_files()
        assert "src/a.py" in files
        assert "src/b.py" in files

    def test_to_prompt(self):
        """测试生成提示词格式"""
        repo_map = RepoMap()
        repo_map.add_function(FunctionSig(
            name="main",
            file="src/main.py",
            line=10,
            params=["args: list"],
            return_type="int",
        ))

        prompt = repo_map.to_prompt(max_tokens=2000)

        assert "src/main.py" in prompt
        assert "main" in prompt

    def test_to_prompt_with_limit(self):
        """测试带限制的提示词生成"""
        repo_map = RepoMap()

        # 添加多个函数
        for i in range(100):
            repo_map.add_function(FunctionSig(
                name=f"function_{i}",
                file=f"src/file_{i}.py",
                line=1,
            ))

        prompt = repo_map.to_prompt(max_tokens=500)

        # 应该被截断
        assert "truncated" in prompt

    def test_function_to_compact(self):
        """测试函数紧凑表示"""
        func = FunctionSig(
            name="get_user",
            file="test.py",
            line=1,
            params=["user_id: str"],
            return_type="User",
            is_async=True,
        )

        compact = func.to_compact()
        assert "async def get_user" in compact
        assert "-> User" in compact

    def test_class_to_compact(self):
        """测试类紧凑表示"""
        cls = ClassDef(
            name="UserService",
            file="test.py",
            line=1,
            methods=["get", "create", "update"],
            bases=["BaseService"],
        )

        compact = cls.to_compact()
        assert "class UserService(BaseService)" in compact


class TestRepoMapGenerator:
    """仓库地图生成器测试"""

    def test_generate_from_empty_dir(self, temp_dir):
        """测试从空目录生成"""
        generator = RepoMapGenerator(temp_dir)
        repo_map = generator.generate()

        assert len(repo_map.functions) == 0
        assert len(repo_map.classes) == 0

    def test_generate_finds_python_files(self, temp_dir):
        """测试发现 Python 文件"""
        # 创建测试文件
        src_dir = temp_dir / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("def main(): pass", encoding="utf-8")
        (src_dir / "utils.py").write_text("def helper(): pass", encoding="utf-8")

        generator = RepoMapGenerator(temp_dir)
        repo_map = generator.generate()

        assert len(repo_map.functions) == 2

    def test_generate_extracts_classes(self, temp_dir):
        """测试提取类"""
        src_dir = temp_dir / "src"
        src_dir.mkdir()

        code = '''
class UserService:
    """用户服务"""

    def get_user(self, user_id: str):
        pass

    def create_user(self, name: str):
        pass

def helper_function():
    pass
'''
        (src_dir / "service.py").write_text(code, encoding="utf-8")

        generator = RepoMapGenerator(temp_dir)
        repo_map = generator.generate()

        assert len(repo_map.classes) == 1
        cls_key = list(repo_map.classes.keys())[0]
        assert repo_map.classes[cls_key].name == "UserService"
        assert "get_user" in repo_map.classes[cls_key].methods

    def test_generate_with_include_dirs(self, temp_dir):
        """测试指定包含目录"""
        # 创建目录结构
        (temp_dir / "src").mkdir()
        (temp_dir / "tests").mkdir()
        (temp_dir / "src" / "main.py").write_text("def main(): pass", encoding="utf-8")
        (temp_dir / "tests" / "test_main.py").write_text("def test(): pass", encoding="utf-8")

        generator = RepoMapGenerator(temp_dir)
        repo_map = generator.generate(include_dirs=["src"])

        # 只应包含 src 目录
        files = repo_map.get_files()
        assert any("src" in f for f in files)
        assert not any("tests" in f for f in files)

    def test_generate_excludes_pycache(self, temp_dir):
        """测试排除 __pycache__"""
        src_dir = temp_dir / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("def main(): pass", encoding="utf-8")
        (src_dir / "__pycache__").mkdir()
        (src_dir / "__pycache__" / "main.cpython-39.pyc").write_bytes(b"")

        generator = RepoMapGenerator(temp_dir)
        repo_map = generator.generate()

        # 不应包含 __pycache__
        files = repo_map.get_files()
        assert not any("__pycache__" in f for f in files)

    def test_parse_invalid_syntax_gracefully(self, temp_dir):
        """测试优雅处理无效语法"""
        src_dir = temp_dir / "src"
        src_dir.mkdir()

        # 创建有语法错误的文件
        invalid_code = '''
def broken(
    pass
'''
        (src_dir / "broken.py").write_text(invalid_code, encoding="utf-8")

        generator = RepoMapGenerator(temp_dir)
        # 不应该抛出异常
        repo_map = generator.generate()

        # 语法错误的文件被跳过，不会添加函数
        assert len(repo_map.functions) == 0

    def test_search(self, temp_dir):
        """测试搜索功能"""
        src_dir = temp_dir / "src"
        src_dir.mkdir()
        (src_dir / "user_service.py").write_text("def get_user(): pass", encoding="utf-8")
        (src_dir / "order_service.py").write_text("def get_order(): pass", encoding="utf-8")

        generator = RepoMapGenerator(temp_dir)
        repo_map = generator.generate()

        # 搜索 user
        filtered = repo_map.search("user")
        assert len(filtered.functions) == 1
