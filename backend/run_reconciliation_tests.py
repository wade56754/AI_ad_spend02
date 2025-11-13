#!/usr/bin/env python
"""
对账管理模块测试运行脚本
Version: 1.0
Author: Claude协作开发
"""

import os
import sys
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_test_module(test_module: str, description: str):
    """运行单个测试模块"""
    print(f"\n{'='*60}")
    print(f"运行测试: {description}")
    print(f"模块: {test_module}")
    print(f"{'='*60}")

    try:
        # 运行测试
        result = subprocess.run(
            ["python", "-m", "pytest",
             f"tests/{test_module}",
             "-v",
             "--tb=short",
             "--disable-warnings"],
            capture_output=True,
            text=True,
            cwd=project_root
        )

        # 输出结果
        print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)

        # 返回结果码
        return result.returncode

    except Exception as e:
        print(f"运行测试时出错: {e}")
        return 1

def check_test_coverage():
    """检查测试覆盖率"""
    print(f"\n{'='*60}")
    print("检查测试覆盖率")
    print(f"{'='*60}")

    try:
        # 运行覆盖率测试
        result = subprocess.run(
            ["python", "-m", "pytest",
             "tests/test_reconciliation_*.py",
             "--cov=models.reconciliation",
             "--cov=services.reconciliation_service",
             "--cov=routers.reconciliation",
             "--cov=schemas.reconciliation",
             "--cov-report=term-missing",
             "--cov-report=html:htmlcov/reconciliation"],
            capture_output=True,
            text=True,
            cwd=project_root
        )

        print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)

        return result.returncode

    except Exception as e:
        print(f"检查覆盖率时出错: {e}")
        return 1

def main():
    """主函数"""
    print("AI广告代投系统 - 对账管理模块测试")
    print("="*60)

    # 测试模块列表
    test_modules = [
        ("test_reconciliation_api.py", "对账管理API测试"),
        ("test_reconciliation_permissions.py", "对账管理权限测试"),
        ("test_reconciliation_service.py", "对账管理服务层测试")
    ]

    # 运行所有测试
    total_failures = 0

    for module, description in test_modules:
        result = run_test_module(module, description)
        if result != 0:
            total_failures += 1
            print(f"❌ {description} 测试失败")
        else:
            print(f"✅ {description} 测试通过")

    # 检查覆盖率
    print(f"\n{'='*60}")
    if total_failures == 0:
        print("所有测试通过，检查覆盖率...")
        coverage_result = check_test_coverage()
        if coverage_result == 0:
            print("✅ 覆盖率报告已生成")
            print("📊 请查看 htmlcov/reconciliation/index.html")
    else:
        print(f"❌ 共 {total_failures} 个测试模块失败，跳过覆盖率检查")

    # 输出总结
    print(f"\n{'='*60}")
    print("测试总结")
    print(f"{'='*60}")

    if total_failures == 0:
        print("✅ 所有测试通过！")
        print("对账管理模块测试完成。")
    else:
        print(f"❌ {total_failures} 个测试模块失败")
        print("请修复失败的测试后重试。")

    # 返回退出码
    return 0 if total_failures == 0 else 1

if __name__ == "__main__":
    # 设置环境变量
    os.environ["PYTHONPATH"] = str(project_root)
    os.environ["TESTING"] = "true"

    # 运行测试
    exit_code = main()
    sys.exit(exit_code)