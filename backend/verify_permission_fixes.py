"""
验证权限测试修复脚本
快速验证 AuthenticatedUser 参数修复是否成功
"""
import subprocess
import sys

def run_permission_tests():
    """运行权限测试"""
    print("=" * 80)
    print("运行权限测试验证")
    print("=" * 80)

    cmd = [
        sys.executable, "-m", "pytest",
        "tests/core/test_permissions.py",
        "-v", "--tb=short",
        "-q"
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

        # 统计结果
        import re
        passed = len(re.findall(r'PASSED', output))
        failed = len(re.findall(r'FAILED', output))
        errors = len(re.findall(r'ERROR', output))

        print("\n" + "=" * 80)
        print("📊 测试结果统计")
        print("=" * 80)
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"⚠️  错误: {errors}")
        print(f"总计: {passed + failed + errors}")

        if errors == 0:
            print("\n🎉 所有 AuthenticatedUser 参数错误已修复！")
        else:
            print(f"\n⚠️  仍有 {errors} 个错误需要修复")

        # 检查特定错误
        if "user_id" in output:
            print("\n❌ 仍然存在 'user_id' 参数错误")
        else:
            print("\n✅ 'user_id' 参数错误已全部修复")

        if "ADVERTISER" in output and "AttributeError" in output:
            print("❌ 仍然存在 UserRole.ADVERTISER 错误")
        else:
            print("✅ UserRole.ADVERTISER 错误已全部修复")

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("⏱️  测试超时")
        return False
    except Exception as e:
        print(f"❌ 执行错误: {e}")
        return False

if __name__ == "__main__":
    success = run_permission_tests()
    sys.exit(0 if success else 1)
