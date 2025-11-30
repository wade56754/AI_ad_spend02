#!/usr/bin/env python
"""
Ledger Module Test Runner
=========================

专用于 ledger 模块的测试运行器脚本。
确保 SQLite 与 SQLAlchemy 2.x 兼容性。

用法：
    cd backend
    python tests/ledger/run_ledger_tests.py          # 运行所有 ledger 测试
    python tests/ledger/run_ledger_tests.py -v       # 详细输出
    python tests/ledger/run_ledger_tests.py --check  # 仅检查环境

对齐文档：
    - LEDGER_SOT.md v1.1
    - STATE_MACHINE.md v2.6
    - DATA_SCHEMA.md v5.2
"""

import os
import sys
from pathlib import Path


def get_backend_root() -> Path:
    """获取 backend 目录路径"""
    # tests/ledger/run_ledger_tests.py -> tests/ledger -> tests -> backend
    return Path(__file__).parent.parent.parent.absolute()


def setup_environment():
    """设置测试环境"""
    backend_root = get_backend_root()

    # 设置 PYTHONPATH
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    # 设置环境变量
    os.environ["TESTING"] = "true"
    os.environ["PYTHONPATH"] = str(backend_root)

    # 加载 .env.test
    env_test = backend_root / ".env.test"
    if env_test.exists():
        from dotenv import load_dotenv
        load_dotenv(str(env_test), override=True)
        print(f"[OK] Loaded .env.test from {env_test}")
    else:
        print(f"[WARN] .env.test not found at {env_test}")

    return backend_root


def check_dependencies():
    """检查依赖"""
    issues = []

    # Python 版本
    if sys.version_info < (3, 9):
        issues.append(f"Python 3.9+ required, got {sys.version_info.major}.{sys.version_info.minor}")
    else:
        print(f"[OK] Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    # SQLAlchemy
    try:
        import sqlalchemy
        print(f"[OK] SQLAlchemy {sqlalchemy.__version__}")
        if not sqlalchemy.__version__.startswith("2."):
            issues.append("SQLAlchemy 2.x required")
    except ImportError:
        issues.append("SQLAlchemy not installed")

    # pytest
    try:
        import pytest
        print(f"[OK] pytest {pytest.__version__}")
    except ImportError:
        issues.append("pytest not installed")

    # pytest-asyncio
    try:
        import pytest_asyncio
        print("[OK] pytest-asyncio installed")
    except ImportError:
        issues.append("pytest-asyncio not installed")

    return issues


def check_test_files(backend_root: Path):
    """检查测试文件"""
    issues = []

    # conftest.py
    conftest = backend_root / "tests" / "conftest.py"
    if conftest.exists():
        print(f"[OK] conftest.py found")

        # 检查 BigInteger 编译器
        content = conftest.read_text(encoding="utf-8")
        if "@compiles(BigInteger, 'sqlite')" in content:
            print("[OK] BigInteger SQLite compiler found")
        else:
            issues.append("BigInteger SQLite compiler missing in conftest.py")
    else:
        issues.append(f"conftest.py not found at {conftest}")

    # 测试文件
    ledger_tests = backend_root / "tests" / "ledger"
    if ledger_tests.exists():
        test_files = list(ledger_tests.glob("test_*.py"))
        print(f"[OK] Found {len(test_files)} test file(s) in tests/ledger/")
        for tf in test_files:
            print(f"     - {tf.name}")
    else:
        issues.append("tests/ledger/ directory not found")

    return issues


def run_tests(backend_root: Path, verbose: bool = False, extra_args: list = None):
    """运行测试"""
    import subprocess

    cmd = [
        sys.executable, "-m", "pytest",
        str(backend_root / "tests" / "ledger"),
        "-v" if verbose else "-q",
        "--tb=short",
        "--no-cov",
        "--disable-warnings",
    ]

    if extra_args:
        cmd.extend(extra_args)

    print("\n" + "=" * 60)
    print("Running Ledger Module Tests")
    print("=" * 60)
    print(f"Command: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd, cwd=str(backend_root))
    return result.returncode


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Ledger Module Test Runner")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--check", action="store_true", help="Only check environment")
    parser.add_argument("-k", type=str, help="Only run tests matching expression")
    parser.add_argument("-x", action="store_true", help="Stop on first failure")

    args, extra = parser.parse_known_args()

    print("=" * 60)
    print("Ledger Module Test Environment Setup")
    print("=" * 60)

    # 设置环境
    backend_root = setup_environment()
    os.chdir(backend_root)
    print(f"[OK] Working directory: {backend_root}")

    # 检查依赖
    print("\nDependency Check:")
    dep_issues = check_dependencies()

    # 检查测试文件
    print("\nTest Files Check:")
    file_issues = check_test_files(backend_root)

    all_issues = dep_issues + file_issues

    print("\n" + "-" * 60)
    if all_issues:
        print("Issues found:")
        for issue in all_issues:
            print(f"  [X] {issue}")
        if args.check:
            return 1
        print("\nProceeding with tests anyway...")
    else:
        print("All checks passed!")

    if args.check:
        return 0

    # 运行测试
    extra_args = []
    if args.k:
        extra_args.extend(["-k", args.k])
    if args.x:
        extra_args.append("-x")
    extra_args.extend(extra)

    return run_tests(backend_root, verbose=args.verbose, extra_args=extra_args)


if __name__ == "__main__":
    sys.exit(main())
