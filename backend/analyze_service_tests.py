"""
服务层测试失败分析脚本
快速诊断哪些服务测试失败以及失败原因
"""
import subprocess
import json
import re

# 需要分析的测试文件
TEST_FILES = [
    "tests/services/test_finance_service.py",
    "tests/services/test_reports_service.py",
    "tests/services/test_ai_monitoring_service.py",
    "tests/services/test_ad_account_service.py",
    "tests/services/test_import_job_service.py",
]

def run_test_file(test_file):
    """运行单个测试文件并收集结果"""
    print(f"\n{'='*80}")
    print(f"分析: {test_file}")
    print('='*80)

    cmd = [
        "python", "-m", "pytest",
        test_file,
        "-v", "--tb=line",
        "--no-header",
        "-q"
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd="d:/git/1108/backend"
        )

        output = result.stdout + result.stderr

        # 统计测试结果
        passed = len(re.findall(r'PASSED', output))
        failed = len(re.findall(r'FAILED', output))
        errors = len(re.findall(r'ERROR', output))

        print(f"\n📊 统计:")
        print(f"  ✅ 通过: {passed}")
        print(f"  ❌ 失败: {failed}")
        print(f"  ⚠️  错误: {errors}")

        # 提取失败的测试名称
        if failed > 0 or errors > 0:
            print(f"\n❌ 失败/错误的测试:")
            for match in re.finditer(r'(FAILED|ERROR) (.*?) -', output):
                status, test_name = match.groups()
                print(f"  {status}: {test_name}")

        # 提取常见错误模式
        print(f"\n🔍 错误模式分析:")

        # ImportError
        if 'ImportError' in output or 'ModuleNotFoundError' in output:
            print("  - 发现导入错误")
            for match in re.finditer(r'(ImportError|ModuleNotFoundError): (.*)', output):
                print(f"    {match.group(0)}")

        # AttributeError (Mock问题)
        if 'AttributeError' in output:
            print("  - 发现属性错误（可能是Mock配置问题）")
            attr_errors = re.findall(r"AttributeError: (.*)", output)
            for error in set(attr_errors[:3]):  # 只显示前3个唯一错误
                print(f"    {error}")

        # AssertionError
        if 'AssertionError' in output:
            print("  - 发现断言错误（测试期望不匹配）")

        return {
            'file': test_file,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'total': passed + failed + errors
        }

    except subprocess.TimeoutExpired:
        print(f"  ⏱️  超时")
        return None
    except Exception as e:
        print(f"  ❌ 执行错误: {e}")
        return None

def main():
    print("🔬 服务层测试失败分析")
    print("="*80)

    results = []
    for test_file in TEST_FILES:
        result = run_test_file(test_file)
        if result:
            results.append(result)

    # 总结
    print(f"\n\n{'='*80}")
    print("📊 总体统计")
    print('='*80)

    total_passed = sum(r['passed'] for r in results)
    total_failed = sum(r['failed'] for r in results)
    total_errors = sum(r['errors'] for r in results)
    total_tests = sum(r['total'] for r in results)

    print(f"\n总测试数: {total_tests}")
    print(f"✅ 通过: {total_passed} ({total_passed/total_tests*100:.1f}%)")
    print(f"❌ 失败: {total_failed} ({total_failed/total_tests*100:.1f}%)")
    print(f"⚠️  错误: {total_errors} ({total_errors/total_tests*100:.1f}%)")

    print(f"\n\n📋 按文件统计:")
    for r in results:
        filename = r['file'].split('/')[-1]
        pass_rate = r['passed']/r['total']*100 if r['total'] > 0 else 0
        print(f"  {filename:40} {r['passed']:3}/{r['total']:3} ({pass_rate:5.1f}%)")

if __name__ == "__main__":
    main()
