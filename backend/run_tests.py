#!/usr/bin/env python3
"""
AI广告代投系统测试执行脚本
自动化执行所有测试并生成报告
Version: 1.0
Author: Claude协作开发
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path


def run_command(command, description):
    """执行命令并处理结果"""
    print(f"\n🔄 {description}...")
    print(f"执行命令: {command}")

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=600  # 10分钟超时
        )

        if result.returncode == 0:
            print(f"✅ {description} - 成功")
            if result.stdout:
                print("输出:", result.stdout[-500:])  # 显示最后500个字符
        else:
            print(f"❌ {description} - 失败")
            print("错误:", result.stderr[-500:])  # 显示最后500个字符

        return result.returncode == 0, result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - 超时")
        return False, "", "Command timeout"
    except Exception as e:
        print(f"💥 {description} - 异常: {str(e)}")
        return False, "", str(e)


def check_environment():
    """检查测试环境"""
    print("🔍 检查测试环境...")

    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ Python版本过低，需要Python 3.8+")
        return False

    print(f"✅ Python版本: {sys.version}")

    # 检查必要文件
    required_files = [
        "requirements.txt",
        "main.py",
        "core/db.py",
        "tests/conftest.py"
    ]

    for file in required_files:
        if not Path(file).exists():
            print(f"❌ 缺少必要文件: {file}")
            return False

    print("✅ 必要文件检查通过")

    return True


def install_dependencies():
    """安装测试依赖"""
    commands = [
        ("pip install -r requirements.txt", "安装项目依赖"),
        ("pip install pytest pytest-cov pytest-asyncio pytest-mock", "安装测试框架"),
        ("pip install bandit safety", "安装安全检查工具"),
        ("pip install flake8 black isort", "安装代码质量工具")
    ]

    success_count = 0
    for command, description in commands:
        success, _, _ = run_command(command, description)
        if success:
            success_count += 1

    return success_count == len(commands)


def run_unit_tests():
    """运行单元测试"""
    print("\n🧪 运行单元测试...")

    test_commands = [
        ("pytest tests/test_auth_service.py -v --cov=core.auth --cov-report=term-missing", "认证服务测试"),
        ("pytest tests/test_project_service.py -v --cov=services.project_service --cov-report=term-missing", "项目服务测试"),
        ("pytest tests/test_daily_report_service.py -v --cov=services.daily_report_service --cov-report=term-missing", "日报服务测试"),
        ("pytest tests/test_topup_service.py -v --cov=services.topup_service --cov-report=term-missing", "充值服务测试"),
        ("pytest tests/test_reconciliation_service.py -v --cov=services.reconciliation_service --cov-report=term-missing", "对账服务测试"),
        ("pytest tests/test_ai_analytics_service.py -v --cov=services.ai_anomaly_detection_service --cov-report=term-missing", "AI分析服务测试")
    ]

    results = {}
    for command, description in test_commands:
        success, stdout, stderr = run_command(command, description)
        results[description] = {
            "success": success,
            "output": stdout,
            "error": stderr
        }

    return results


def run_integration_tests():
    """运行集成测试"""
    print("\n🔗 运行集成测试...")

    test_commands = [
        ("pytest tests/test_authentication_api.py -v", "认证API测试"),
        ("pytest tests/test_project_api.py -v", "项目API测试"),
        ("pytest tests/test_daily_report_api.py -v", "日报API测试"),
        ("pytest tests/test_topup_api.py -v", "充值API测试"),
        ("pytest tests/test_reconciliation_api.py -v", "对账API测试"),
        ("pytest tests/test_ai_analytics_api.py -v", "AI分析API测试")
    ]

    results = {}
    for command, description in test_commands:
        success, stdout, stderr = run_command(command, description)
        results[description] = {
            "success": success,
            "output": stdout,
            "error": stderr
        }

    return results


def generate_test_report(results, output_file="test_report.json"):
    """生成测试报告"""
    print(f"\n📋 生成测试报告: {output_file}")

    # 统计结果
    total_tests = 0
    passed_tests = 0
    failed_tests = 0

    for category, tests in results.items():
        for test_name, test_result in tests.items():
            total_tests += 1
            if test_result["success"]:
                passed_tests += 1
            else:
                failed_tests += 1

    report = {
        "test_run_time": datetime.now().isoformat(),
        "summary": {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": f"{(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%"
        },
        "categories": results,
        "environment": {
            "python_version": sys.version,
            "platform": sys.platform
        }
    }

    # 保存JSON报告
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 生成可读报告
    txt_file = output_file.replace('.json', '.txt')
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("AI广告代投系统测试报告\n")
        f.write("=" * 80 + "\n")
        f.write(f"测试时间: {report['test_run_time']}\n")
        f.write(f"总测试数: {report['summary']['total_tests']}\n")
        f.write(f"通过测试: {report['summary']['passed_tests']}\n")
        f.write(f"失败测试: {report['summary']['failed_tests']}\n")
        f.write(f"成功率: {report['summary']['success_rate']}\n")
        f.write("\n")

        for category, tests in results.items():
            f.write(f"\n{category}:\n")
            f.write("-" * 40 + "\n")
            for test_name, test_result in tests.items():
                status = "✅ PASS" if test_result["success"] else "❌ FAIL"
                f.write(f"{status} {test_name}\n")
                if not test_result["success"] and test_result["error"]:
                    f.write(f"错误: {test_result['error'][:200]}\n")

    print(f"✅ 测试报告已生成: {output_file} 和 {txt_file}")
    return report


def main():
    """主函数"""
    print("=" * 80)
    print("🚀 AI广告代投系统自动化测试")
    print("=" * 80)

    # 切换到backend目录
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)

    # 设置Python路径
    sys.path.insert(0, str(backend_dir))
    os.environ["PYTHONPATH"] = str(backend_dir)
    os.environ["ENVIRONMENT"] = "test"

    all_results = {}

    try:
        # 1. 环境检查
        if not check_environment():
            print("❌ 环境检查失败，退出测试")
            return 1

        # 2. 安装依赖
        print("\n📦 安装测试依赖...")
        if not install_dependencies():
            print("❌ 依赖安装失败，退出测试")
            return 1

        # 3. 单元测试
        all_results["单元测试"] = run_unit_tests()

        # 4. 集成测试
        all_results["集成测试"] = run_integration_tests()

        # 5. 生成报告
        report = generate_test_report(all_results)

        # 6. 输出摘要
        print("\n" + "=" * 80)
        print("📊 测试结果摘要")
        print("=" * 80)
        print(f"总测试数: {report['summary']['total_tests']}")
        print(f"通过测试: {report['summary']['passed_tests']}")
        print(f"失败测试: {report['summary']['failed_tests']}")
        print(f"成功率: {report['summary']['success_rate']}")

        if report['summary']['failed_tests'] == 0:
            print("\n🎉 所有测试通过！")
            return 0
        else:
            print(f"\n⚠️  有 {report['summary']['failed_tests']} 个测试失败")
            return 1

    except KeyboardInterrupt:
        print("\n⏰ 测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n💥 测试执行异常: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)