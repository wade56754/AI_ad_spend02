#!/usr/bin/env python3
"""
使用 AI 代码工厂执行财务模块全量测试
"""

import sys
import os
import subprocess
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

# 财务模块测试文件列表
FINANCE_TEST_FILES = [
    "tests/test_finance_profit_api.py",
    "tests/services/test_finance_service.py",
    "tests/services/test_finance_v2_service.py",
    "tests/services/test_finance_dashboard_service.py",
    "tests/services/test_profit_service_v2.py",
    "tests/services/test_ledger_service.py",
    "tests/test_topup_service.py",
    "tests/test_topup_api.py",
    "tests/test_topup_permissions.py",
    "tests/test_reconciliation_api.py",
    "tests/test_reconciliation_service.py",
    "tests/test_reconciliation_permissions.py",
]


def run_tests():
    """运行财务模块测试"""
    print("=" * 80)
    print("🎯 财务模块全量测试")
    print("=" * 80)
    print(f"\n⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    backend_dir = project_root / "backend"
    test_files = [f for f in FINANCE_TEST_FILES]  # 使用相对路径，pytest 会在 backend 目录下运行
    
    # 设置环境变量
    env = os.environ.copy()
    # pytest.ini 中设置了 pythonpath = .，所以只需要设置 backend 目录
    env['PYTHONPATH'] = str(backend_dir) + os.pathsep + str(project_root)
    # 设置测试环境
    env['ENV_NAME'] = 'development'  # 使用 development 而不是 testing
    
    # 构建 pytest 命令（简化版本，不使用 json-report）
    cmd = [
        "python3", "-m", "pytest",
        *test_files,
        "-v",
        "--tb=short",
        "--cov=backend/services",
        "--cov=backend/routers",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov/finance",
    ]
    
    print(f"📋 测试文件 ({len(test_files)} 个):")
    for f in FINANCE_TEST_FILES:
        print(f"   - {f}")
    
    print(f"\n📁 工作目录: {backend_dir}")
    print(f"🔧 PYTHONPATH: {env.get('PYTHONPATH', '未设置')}")
    
    print(f"\n🚀 执行命令: {' '.join(cmd[:5])} ... ({len(cmd)} 个参数)\n")
    
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
        
        if result.stdout:
            print("\n📝 标准输出:")
            print(result.stdout[-2000:])  # 只显示最后 2000 字符
        
        if result.stderr:
            print("\n⚠️  错误输出:")
            print(result.stderr[-1000:])  # 只显示最后 1000 字符
        
        print(f"\n✅ 退出码: {result.returncode}")
        
        # 从输出中提取测试统计（简化版本）
        if result.stdout:
            # 尝试从输出中提取测试统计信息
            lines = result.stdout.split('\n')
            summary_line = None
            for line in lines:
                if 'passed' in line.lower() or 'failed' in line.lower():
                    summary_line = line
                    break
            
            if summary_line:
                print("\n" + "-" * 80)
                print("📈 测试统计")
                print("-" * 80)
                print(f"   {summary_line}")
        
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


def analyze_with_factory():
    """使用代码工厂分析测试结果"""
    print("\n" + "=" * 80)
    print("🤖 AI 代码工厂 - 测试结果分析")
    print("=" * 80)
    
    try:
        from agents.skills.code_factory.core.orchestrator import CodeFactoryOrchestrator
        
        orchestrator = CodeFactoryOrchestrator(project_root=project_root)
        
        requirement = """
        分析财务模块测试结果，提供：
        1. 测试覆盖率分析
        2. 失败测试用例分析
        3. 测试质量评估
        4. 改进建议
        """
        
        result = orchestrator.execute(
            requirement=requirement,
            workflow_type="code_review"
        )
        
        print(f"\n✅ 分析状态: {result.get('status', 'unknown')}")
        
        execution_results = result.get('execution_results', [])
        for exec_result in execution_results:
            agent_id = exec_result.get('agent_id', 'unknown')
            success = exec_result.get('success', False)
            status_icon = "✅" if success else "❌"
            
            print(f"\n{status_icon} {agent_id}")
            if exec_result.get('output'):
                output = exec_result.get('output', '')
                if len(output) > 500:
                    output = output[:500] + "..."
                print(f"   输出: {output}")
        
    except Exception as e:
        print(f"\n⚠️  代码工厂分析失败: {str(e)}")
        print("   继续使用标准测试报告...")


def main():
    """主函数"""
    # 运行测试
    exit_code = run_tests()
    
    # 使用代码工厂分析（可选）
    # analyze_with_factory()
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
