#!/usr/bin/env python3
"""
接口开发辅助工具
提供常用的接口开发和检查功能
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional
import re

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class InterfaceDevHelper:
    """接口开发辅助工具"""

    def __init__(self):
        self.project_root = project_root
        self.backend_dir = project_root / "backend"

    def check_interface_compliance(self, module_name: str) -> Dict[str, bool]:
        """
        检查接口开发的合规性

        Args:
            module_name: 模块名称

        Returns:
            检查结果字典
        """
        results = {}

        # 检查文件是否存在
        results['route_file_exists'] = self._check_file_exists(f"routers/{module_name}.py")
        results['schema_file_exists'] = self._check_file_exists(f"schemas/{module_name}.py")
        results['service_file_exists'] = self._check_file_exists(f"services/{module_name}_service.py")
        results['test_file_exists'] = self._check_file_exists(f"tests/test_{module_name}.py")

        # 检查代码规范
        if results['route_file_exists']:
            results['route_compliance'] = self._check_route_compliance(module_name)

        if results['schema_file_exists']:
            results['schema_compliance'] = self._check_schema_compliance(module_name)

        # 检查测试覆盖率
        if results['test_file_exists']:
            results['test_coverage'] = self._check_test_coverage(module_name)

        return results

    def _check_file_exists(self, relative_path: str) -> bool:
        """检查文件是否存在"""
        file_path = self.backend_dir / relative_path
        return file_path.exists()

    def _check_route_compliance(self, module_name: str) -> bool:
        """检查路由文件合规性"""
        route_file = self.backend_dir / "routers" / f"{module_name}.py"

        try:
            with open(route_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查必要的导入
            required_imports = [
                'from fastapi import APIRouter',
                'from backend.core.response import',
                'from backend.core.security import',
            ]

            for import_stmt in required_imports:
                if import_stmt not in content:
                    print(f"❌ 缺少必要导入: {import_stmt}")
                    return False

            # 检查路由函数格式
            route_patterns = [
                r'@router\.get\(.*\)',
                r'@router\.post\(.*\)',
                r'@router\.put\(.*\)',
                r'@router\.delete\(.*\)',
                r'async def ',
                r'response_model=',
                r'current_user.*=.*Depends\(get_current_user\)',
            ]

            for pattern in route_patterns:
                if not re.search(pattern, content):
                    print(f"❌ 路由格式不符合规范: {pattern}")
                    return False

            # 检查错误处理
            if 'try:' not in content or 'except' not in content:
                print("❌ 缺少异常处理")
                return False

            return True

        except Exception as e:
            print(f"❌ 检查路由文件失败: {e}")
            return False

    def _check_schema_compliance(self, module_name: str) -> bool:
        """检查Schema文件合规性"""
        schema_file = self.backend_dir / "schemas" / f"{module_name}.py"

        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查必要的导入
            required_imports = [
                'from pydantic import BaseModel',
                'from typing import Optional',
            ]

            for import_stmt in required_imports:
                if import_stmt not in content:
                    print(f"❌ Schema缺少必要导入: {import_stmt}")
                    return False

            # 检查模型类
            if 'class' not in content or 'BaseModel' not in content:
                print("❌ 缺少Pydantic模型定义")
                return False

            # 检查字段验证
            if 'Field(' not in content:
                print("⚠️ 建议添加字段验证")

            return True

        except Exception as e:
            print(f"❌ 检查Schema文件失败: {e}")
            return False

    def _check_test_coverage(self, module_name: str) -> bool:
        """检查测试覆盖率"""
        test_file = self.project_root / "tests" / f"test_{module_name}.py"

        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查基本的测试结构
            required_patterns = [
                r'class Test',
                r'def test_',
                r'client\.',
                r'assert ',
            ]

            for pattern in required_patterns:
                if not re.search(pattern, content):
                    print(f"❌ 测试结构不完整: {pattern}")
                    return False

            return True

        except Exception as e:
            print(f"❌ 检查测试文件失败: {e}")
            return False

    def run_code_quality_checks(self, module_name: str) -> Dict[str, bool]:
        """运行代码质量检查"""
        results = {}

        # 运行black格式检查
        results['black_check'] = self._run_black_check(module_name)

        # 运行isort导入检查
        results['isort_check'] = self._run_isort_check(module_name)

        # 运行flake8代码检查
        results['flake8_check'] = self._run_flake8_check(module_name)

        # 运行mypy类型检查
        results['mypy_check'] = self._run_mypy_check(module_name)

        return results

    def _run_black_check(self, module_name: str) -> bool:
        """运行Black格式检查"""
        files = [
            f"backend/routers/{module_name}.py",
            f"backend/schemas/{module_name}.py",
            f"backend/services/{module_name}_service.py",
        ]

        existing_files = [f for f in files if (self.project_root / f).exists()]

        if not existing_files:
            return True

        try:
            cmd = ["black", "--check", "--diff"] + existing_files
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"❌ Black格式检查失败:")
                print(result.stdout)
                return False

            return True

        except Exception as e:
            print(f"❌ 运行Black检查失败: {e}")
            return False

    def _run_isort_check(self, module_name: str) -> bool:
        """运行isort导入检查"""
        files = [
            f"backend/routers/{module_name}.py",
            f"backend/schemas/{module_name}.py",
            f"backend/services/{module_name}_service.py",
        ]

        existing_files = [f for f in files if (self.project_root / f).exists()]

        if not existing_files:
            return True

        try:
            cmd = ["isort", "--check-only", "--diff"] + existing_files
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"❌ isort导入检查失败:")
                print(result.stdout)
                return False

            return True

        except Exception as e:
            print(f"❌ 运行isort检查失败: {e}")
            return False

    def _run_flake8_check(self, module_name: str) -> bool:
        """运行flake8代码检查"""
        files = [
            f"backend/routers/{module_name}.py",
            f"backend/schemas/{module_name}.py",
            f"backend/services/{module_name}_service.py",
        ]

        existing_files = [f for f in files if (self.project_root / f).exists()]

        if not existing_files:
            return True

        try:
            cmd = ["flake8"] + existing_files
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"❌ flake8代码检查失败:")
                print(result.stdout)
                return False

            return True

        except Exception as e:
            print(f"❌ 运行flake8检查失败: {e}")
            return False

    def _run_mypy_check(self, module_name: str) -> bool:
        """运行mypy类型检查"""
        files = [
            f"backend/routers/{module_name}.py",
            f"backend/schemas/{module_name}.py",
            f"backend/services/{module_name}_service.py",
        ]

        existing_files = [f for f in files if (self.project_root / f).exists()]

        if not existing_files:
            return True

        try:
            cmd = ["mypy", "--ignore-missing-imports"] + existing_files
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"❌ mypy类型检查失败:")
                print(result.stdout)
                return False

            return True

        except Exception as e:
            print(f"❌ 运行mypy检查失败: {e}")
            return False

    def format_code(self, module_name: str) -> bool:
        """自动格式化代码"""
        success = True

        # 运行black格式化
        files = [
            f"backend/routers/{module_name}.py",
            f"backend/schemas/{module_name}.py",
            f"backend/services/{module_name}_service.py",
        ]

        existing_files = [f for f in files if (self.project_root / f).exists()]

        if not existing_files:
            return True

        try:
            # Black格式化
            cmd = ["black"] + existing_files
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"❌ Black格式化失败:")
                print(result.stdout)
                success = False

            # isort导入排序
            cmd = ["isort"] + existing_files
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"❌ isort导入排序失败:")
                print(result.stdout)
                success = False

            return success

        except Exception as e:
            print(f"❌ 代码格式化失败: {e}")
            return False

    def run_tests(self, module_name: str, coverage: bool = True) -> bool:
        """运行测试"""
        try:
            cmd = ["python", "-m", "pytest", f"tests/test_{module_name}.py", "-v"]

            if coverage:
                cmd.extend(["--cov=backend", "--cov-report=term-missing"])

            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)

            print("🧪 测试输出:")
            print(result.stdout)

            if result.stderr:
                print("⚠️ 错误输出:")
                print(result.stderr)

            return result.returncode == 0

        except Exception as e:
            print(f"❌ 运行测试失败: {e}")
            return False

    def generate_api_documentation(self, module_name: str) -> bool:
        """生成API文档"""
        try:
            # 启动应用并获取OpenAPI文档
            cmd = [
                "python", "-c", f"""
import sys
sys.path.append('{self.project_root}')

from backend.main import app
import json

openapi_spec = app.openapi()
with open('{self.project_root}/docs/api_{module_name}.json', 'w', encoding='utf-8') as f:
    json.dump(openapi_spec, f, indent=2, ensure_ascii=False)

print("✅ API文档生成完成")
"""
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"❌ 生成API文档失败:")
                print(result.stdout)
                return False

            print("📖 API文档生成完成")
            return True

        except Exception as e:
            print(f"❌ 生成API文档失败: {e}")
            return False


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="接口开发辅助工具")
    parser.add_argument("module", help="模块名称")
    parser.add_argument("--check", action="store_true", help="检查合规性")
    parser.add_argument("--quality", action="store_true", help="运行代码质量检查")
    parser.add_argument("--format", action="store_true", help="格式化代码")
    parser.add_argument("--test", action="store_true", help="运行测试")
    parser.add_argument("--coverage", action="store_true", help="生成测试覆盖率报告")
    parser.add_argument("--docs", action="store_true", help="生成API文档")
    parser.add_argument("--all", action="store_true", help="执行所有检查")

    args = parser.parse_args()
    helper = InterfaceDevHelper()

    if args.all:
        args.check = True
        args.quality = True
        args.format = True
        args.test = True
        args.coverage = True
        args.docs = True

    module_name = args.module
    print(f"🔧 处理模块: {module_name}")

    # 执行检查
    if args.check:
        print("\n📋 检查接口合规性...")
        results = helper.check_interface_compliance(module_name)
        for check, passed in results.items():
            status = "✅" if passed else "❌"
            print(f"{status} {check}")

    # 代码质量检查
    if args.quality:
        print("\n🔍 运行代码质量检查...")
        results = helper.run_code_quality_checks(module_name)
        for check, passed in results.items():
            status = "✅" if passed else "❌"
            print(f"{status} {check}")

    # 格式化代码
    if args.format:
        print("\n🎨 格式化代码...")
        if helper.format_code(module_name):
            print("✅ 代码格式化完成")
        else:
            print("❌ 代码格式化失败")

    # 运行测试
    if args.test:
        print("\n🧪 运行测试...")
        if helper.run_tests(module_name, args.coverage):
            print("✅ 测试通过")
        else:
            print("❌ 测试失败")

    # 生成文档
    if args.docs:
        print("\n📖 生成API文档...")
        if helper.generate_api_documentation(module_name):
            print("✅ API文档生成完成")
        else:
            print("❌ API文档生成失败")


if __name__ == "__main__":
    main()