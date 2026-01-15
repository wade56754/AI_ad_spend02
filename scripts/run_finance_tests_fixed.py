#!/usr/bin/env python3
"""
财务模块全量测试脚本（修复版）
修复了环境配置问题
"""

import sys
import os
import subprocess
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
backend_dir = project_root / "backend"

# 财务模块测试文件列表
FINANCE_TEST_FILES = [
    "tests/test_finance_profit_api.py",
    "tests/services/test_finance_service.py",
    "tests/services/test_finance_v2_service.py",
    # "tests/services/test_finance_dashboard_service.py",  # 跳过：服务不存在
    "tests/services/test_profit_service_v2.py",
    "tests/services/test_ledger_service.py",
    "tests/test_topup_service.py",
    "tests/test_topup_api.py",
    "tests/test_topup_permissions.py",
    "tests/test_reconciliation_api.py",
    "tests/test_reconciliation_service.py",
    "tests/test_reconciliation_permissions.py",
]


def setup_test_environment():
    """设置测试环境"""
    # 创建必要的目录
    (backend_dir / "logs").mkdir(parents=True, exist_ok=True)
    (project_root / "test-results").mkdir(parents=True, exist_ok=True)
    
    # 设置环境变量
    env = os.environ.copy()
    
    # PYTHONPATH: 确保可以导入 backend 模块
    pythonpath_parts = [
        str(backend_dir),
        str(project_root),
    ]
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = os.pathsep.join(pythonpath_parts) + os.pathsep + env['PYTHONPATH']
    else:
        env['PYTHONPATH'] = os.pathsep.join(pythonpath_parts)
    
    # 环境名称：使用 development（因为 config.py 只允许 development/staging/production）
    env['ENV_NAME'] = 'development'
    
    # 数据库配置（测试环境使用 SQLite 内存数据库）
    env.setdefault('DATABASE_URL', 'sqlite:///:memory:')
    
    # 其他必要的环境变量
    env.setdefault('DEBUG', 'true')
    env.setdefault('LOG_LEVEL', 'DEBUG')
    
    return env


def run_tests():
    """运行财务模块测试"""
    print("=" * 80)
    print("🎯 财务模块全量测试（修复版）")
    print("=" * 80)
    print(f"\n⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 设置测试环境
    env = setup_test_environment()
    
    print("📋 测试文件清单:")
    for i, test_file in enumerate(FINANCE_TEST_FILES, 1):
        file_path = backend_dir / test_file
        exists = "✅" if file_path.exists() else "❌"
        print(f"   {i:2d}. {exists} {test_file}")
    
    print(f"\n📁 工作目录: {backend_dir}")
    print(f"🔧 PYTHONPATH: {env.get('PYTHONPATH', '未设置')[:100]}...")
    print(f"🔧 ENV_NAME: {env.get('ENV_NAME', '未设置')}")
    print(f"🔧 DATABASE_URL: {env.get('DATABASE_URL', '未设置')}")
    
    # 构建 pytest 命令
    cmd = [
        sys.executable, "-m", "pytest",
        *FINANCE_TEST_FILES,
        "-v",
        "--tb=short",
        "--cov=backend/services",
        "--cov=backend/routers",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov/finance",
        "--junitxml=test-results/finance_tests_junit.xml",
        "-o", "junit_family=xunit2",
    ]
    
    print(f"\n🚀 执行命令:")
    print(f"   {' '.join(cmd[:5])} ... ({len(cmd)} 个参数)")
    print()
    
    try:
        # 执行测试
        result = subprocess.run(
            cmd,
            cwd=str(backend_dir),
            env=env,
            capture_output=True,
            text=True,
            timeout=600  # 10 分钟超时
        )
        
        # 输出结果
        print("=" * 80)
        print("📊 测试执行结果")
        print("=" * 80)
        
        # 显示标准输出
        if result.stdout:
            print("\n📝 标准输出:")
            # 提取关键信息
            lines = result.stdout.split('\n')
            summary_start = False
            for line in lines:
                if 'passed' in line.lower() or 'failed' in line.lower() or 'error' in line.lower():
                    summary_start = True
                if summary_start or 'test_' in line.lower() or 'FAILED' in line or 'PASSED' in line:
                    print(f"   {line}")
            
            # 如果输出太长，只显示最后部分
            if len(lines) > 100:
                print(f"\n   ... (省略中间部分，共 {len(lines)} 行)")
                print("\n   最后部分:")
                for line in lines[-20:]:
                    print(f"   {line}")
        
        # 显示错误输出
        if result.stderr:
            print("\n⚠️  错误/警告输出:")
            stderr_lines = result.stderr.split('\n')
            for line in stderr_lines[-30:]:  # 只显示最后30行
                if line.strip():
                    print(f"   {line}")
        
        print(f"\n✅ 退出码: {result.returncode}")
        
        # 解析测试结果
        if result.stdout:
            lines = result.stdout.split('\n')
            for line in lines:
                if 'passed' in line.lower() and ('failed' in line.lower() or 'error' in line.lower()):
                    print("\n" + "-" * 80)
                    print("📈 测试统计")
                    print("-" * 80)
                    print(f"   {line.strip()}")
                    break
        
        # 检查 JUnit XML 报告
        junit_file = backend_dir / "test-results" / "finance_tests_junit.xml"
        if junit_file.exists():
            print(f"\n💾 JUnit XML 报告已生成: {junit_file}")
        
        # 检查 HTML 覆盖率报告
        htmlcov_dir = backend_dir / "htmlcov" / "finance"
        if htmlcov_dir.exists():
            index_file = htmlcov_dir / "index.html"
            if index_file.exists():
                print(f"📊 HTML 覆盖率报告: {htmlcov_dir / 'index.html'}")
        
        print("\n" + "=" * 80)
        print(f"⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        return result.returncode
        
    except subprocess.TimeoutExpired:
        print("\n❌ 测试执行超时（超过 10 分钟）")
        return 1
    except Exception as e:
        print(f"\n❌ 执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """主函数"""
    return run_tests()


if __name__ == "__main__":
    sys.exit(main())
