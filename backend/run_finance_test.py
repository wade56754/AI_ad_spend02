"""
运行财务服务测试并详细分析失败原因
"""
import subprocess
import sys
import re

def run_finance_tests():
    """运行财务服务测试"""
    print("=" * 80)
    print("运行财务服务测试")
    print("=" * 80)

    cmd = [
        sys.executable, "-m", "pytest",
        "tests/services/test_finance_service.py",
        "-v", "--tb=short",
        "-x"  # 遇到第一个失败就停止
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd="d:/git/1108/backend"
        )

        output = result.stdout + result.stderr
        print(output)

        # 提取失败信息
        if "FAILED" in output:
            print("\n" + "=" * 80)
            print("🔍 失败详情分析")
            print("=" * 80)

            # 提取失败的测试名
            failed_tests = re.findall(r'FAILED (.*?) -', output)
            for test in failed_tests:
                print(f"\n❌ 失败的测试: {test}")

            # 提取错误类型
            if "AttributeError" in output:
                print("\n📌 错误类型: AttributeError (属性不存在)")
                attr_errors = re.findall(r"AttributeError: (.*)", output)
                for error in attr_errors[:3]:
                    print(f"   - {error}")

            if "TypeError" in output:
                print("\n📌 错误类型: TypeError (类型错误)")
                type_errors = re.findall(r"TypeError: (.*)", output)
                for error in type_errors[:3]:
                    print(f"   - {error}")

            if "AssertionError" in output:
                print("\n📌 错误类型: AssertionError (断言失败)")
                # 提取断言详情
                assertion_lines = [line for line in output.split('\n') if 'assert' in line.lower()]
                for line in assertion_lines[:5]:
                    if line.strip():
                        print(f"   - {line.strip()}")

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("⏱️  测试超时")
        return False
    except Exception as e:
        print(f"❌ 执行错误: {e}")
        return False

if __name__ == "__main__":
    success = run_finance_tests()
    sys.exit(0 if success else 1)
