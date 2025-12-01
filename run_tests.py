#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试运行脚本
提供便捷的测试执行命令和配置
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# 设置项目根目录
ROOT_DIR = Path(__file__).parent
os.chdir(ROOT_DIR)
sys.path.insert(0, str(ROOT_DIR))


def run_command(cmd, description):
    """运行命令并处理结果"""
    print(f"\n{'='*60}")
    print(f"执行: {description}")
    print(f"命令: {' '.join(cmd)}")
    print(f"{'='*60}")

    result = subprocess.run(cmd, capture_output=False, text=True)

    if result.returncode == 0:
        print(f"\n[PASS] {description} - 成功")
    else:
        print(f"\n[FAIL] {description} - 失败 (退出码: {result.returncode})")

    return result.returncode == 0


def run_unit_tests(verbose=False, coverage=False):
    """运行单元测试"""
    cmd = ["python", "-m", "pytest", "-m", "unit"]

    if verbose:
        cmd.append("-v")

    if coverage:
        cmd.extend([
            "--cov=backend",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=70"
        ])

    cmd.extend([
        "tests/test_models.py",
        "tests/test_business_logic.py"
    ])

    return run_command(cmd, "单元测试")


def run_integration_tests(verbose=False):
    """运行集成测试"""
    cmd = ["python", "-m", "pytest", "-m", "integration"]

    if verbose:
        cmd.append("-v")

    return run_command(cmd, "集成测试")


def run_functional_tests(verbose=False):
    """运行功能测试"""
    cmd = ["python", "-m", "pytest", "-m", "functional"]

    if verbose:
        cmd.append("-v")

    return run_command(cmd, "功能测试")


def run_security_tests(verbose=False):
    """运行安全测试"""
    cmd = ["python", "-m", "pytest", "-m", "security"]

    if verbose:
        cmd.append("-v")

    return run_command(cmd, "安全测试")


def run_performance_tests(verbose=False):
    """运行性能测试"""
    cmd = ["python", "-m", "pytest", "-m", "performance", "--tb=short"]

    if verbose:
        cmd.append("-v")

    return run_command(cmd, "性能测试")


def run_smoke_tests(verbose=False):
    """运行冒烟测试"""
    cmd = ["python", "-m", "pytest", "-m", "smoke"]

    if verbose:
        cmd.append("-v")

    return run_command(cmd, "冒烟测试")


def run_regression_tests(verbose=False):
    """运行回归测试套件（五连拍）"""
    test_suites = [
        ("backend/tests/api/test_daily_report_flow_generated.py", "Daily Reports API"),
        ("backend/tests/api/test_trend_risk_flow_generated.py", "Trend Risk API"),
        ("backend/tests/ledger", "Ledger"),
        ("backend/tests/ad_accounts", "Ad Accounts"),
        ("backend/tests/test_topup_api.py", "Topup API"),
    ]

    all_success = True

    for test_path, description in test_suites:
        cmd = ["python", "-m", "pytest", "-q", "-p", "no:pytest_postgresql"]

        if verbose:
            cmd = ["python", "-m", "pytest", "-v", "--tb=short", "-p", "no:pytest_postgresql"]

        # Topup 测试需要排除 skip 标记
        if "topup" in test_path.lower():
            cmd.extend(["-k", "not skip"])

        cmd.append(test_path)

        success = run_command(cmd, description)
        if not success:
            all_success = False

    return all_success


def run_all_tests(verbose=False, coverage=False, html_report=False):
    """运行所有测试"""
    cmd = ["python", "-m", "pytest"]

    if verbose:
        cmd.append("-v")

    if coverage:
        cmd.extend([
            "--cov=backend",
            "--cov-report=html",
            "--cov-report=term-missing"
        ])

    if html_report:
        cmd.extend([
            "--html=test_reports.html",
            "--self-contained-html"
        ])

    # 创建测试报告目录
    Path("test_reports").mkdir(exist_ok=True)

    return run_command(cmd, "所有测试")


def run_specific_test(test_path, verbose=False):
    """运行特定测试"""
    cmd = ["python", "-m", "pytest"]

    if verbose:
        cmd.append("-v")

    cmd.append(test_path)

    return run_command(cmd, f"特定测试: {test_path}")


def run_database_tests(verbose=False):
    """运行数据库相关测试"""
    test_files = [
        "tests/test_models.py",
        "tests/test_business_logic.py",
        "tests/test_reconciliation_auto.py"
    ]

    cmd = ["python", "-m", "pytest"]

    if verbose:
        cmd.append("-v")

    cmd.extend(test_files)

    return run_command(cmd, "数据库测试")


def check_test_dependencies():
    """检查测试依赖"""
    print("\n检查测试依赖...")

    required_packages = [
        "pytest",
        "pytest-cov",
        "pytest-html",
        "pytest-mock",
        "factory-boy",
        "faker"
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"[OK] {package}")
        except ImportError:
            print(f"[MISSING] {package} - 未安装")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n请安装缺失的依赖:")
        print(f"pip install {' '.join(missing_packages)}")
        return False

    print("\n所有依赖已满足 ✓")
    return True


def main():
    parser = argparse.ArgumentParser(description="测试运行脚本")

    parser.add_argument(
        "--type", "-t",
        choices=["unit", "integration", "functional", "security",
                "performance", "smoke", "database", "regression", "all"],
        default="all",
        help="要运行的测试类型"
    )

    parser.add_argument(
        "--file", "-f",
        help="运行特定的测试文件"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )

    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="生成覆盖率报告"
    )

    parser.add_argument(
        "--html-report",
        action="store_true",
        help="生成HTML测试报告"
    )

    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="检查测试依赖"
    )

    parser.add_argument(
        "--parallel", "-p",
        type=int,
        help="并行运行的进程数"
    )

    args = parser.parse_args()

    # 检查依赖
    if args.check_deps:
        check_test_dependencies()
        return

    # 设置并行测试
    if args.parallel:
        os.environ["PYTEST_XDIST_AUTO_NUM_WORKERS"] = str(args.parallel)

    # 运行测试
    success = True

    if args.file:
        success = run_specific_test(args.file, args.verbose)
    elif args.type == "unit":
        success = run_unit_tests(args.verbose, args.coverage)
    elif args.type == "integration":
        success = run_integration_tests(args.verbose)
    elif args.type == "functional":
        success = run_functional_tests(args.verbose)
    elif args.type == "security":
        success = run_security_tests(args.verbose)
    elif args.type == "performance":
        success = run_performance_tests(args.verbose)
    elif args.type == "smoke":
        success = run_smoke_tests(args.verbose)
    elif args.type == "regression":
        success = run_regression_tests(args.verbose)
    elif args.type == "database":
        success = run_database_tests(args.verbose)
    elif args.type == "all":
        success = run_all_tests(args.verbose, args.coverage, args.html_report)

    # 输出总结
    print(f"\n{'='*60}")
    if success:
        print("[PASS] 所有测试通过")
        exit_code = 0
    else:
        print("[FAIL] 部分测试失败")
        exit_code = 1
    print(f"{'='*60}")

    # 查看报告
    if args.coverage and Path("htmlcov").exists():
        print("\n📊 覆盖率报告已生成: htmlcov/index.html")

    if args.html_report and Path("test_reports.html").exists():
        print("\n📄 HTML测试报告已生成: test_reports.html")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()