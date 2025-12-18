"""
自动修复测试脚本

测试验证器的自动修复功能
"""

import sys
import io
from pathlib import Path

# 设置 stdout 编码为 utf-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.skills.verifiers import (
    EnhancedCodeVerifier,
    VerifyContext,
    VerifierConfig,
    IssueSeverity,
)


def test_auto_fix_error_codes():
    """测试错误码格式自动修复"""
    print()
    print("=" * 70)
    print(" 测试错误码格式自动修复 (SOT-004) ".center(70, "="))
    print("=" * 70)
    print()

    # 包含下划线格式错误码的测试代码
    test_code = '''
"""测试服务"""

from backend.exceptions import BusinessLogicError


def create_user(name: str):
    """创建用户"""
    if not name:
        raise BusinessLogicError(
            message="名称不能为空",
            error_code="VAL_001"  # 应该是 VAL-001
        )

    if len(name) > 100:
        raise BusinessLogicError(
            message="名称过长",
            error_code="VAL_002"  # 应该是 VAL-002
        )

    return {"id": 1, "name": name}


def process_payment(amount: float):
    """处理支付"""
    if amount <= 0:
        raise BusinessLogicError(
            message="金额必须大于0",
            error_code="BIZ_101"  # 应该是 BIZ-101
        )

    if amount > 1000000:
        raise BusinessLogicError(
            message="金额超限",
            error_code="BIZ_102"  # 应该是 BIZ-102
        )

    return {"success": True, "amount": amount}


def handle_error(error_type: str):
    """处理错误"""
    error_codes = {
        "validation": "VAL_001",
        "business": "BIZ_001",
        "system": "SYS_001",
        "auth": "AUTH_001",
        "database": "DB_001",
    }
    return error_codes.get(error_type, "SYS_500")
'''

    print("原始代码中的错误码格式:")
    print("-" * 40)
    for line_no, line in enumerate(test_code.split('\n'), 1):
        if '_0' in line and ('VAL' in line or 'BIZ' in line or 'SYS' in line or 'AUTH' in line or 'DB' in line):
            print(f"  L{line_no:3d}: {line.strip()}")
    print()

    # 创建验证器 (启用自动修复)
    context = VerifyContext(
        project_root=project_root,
        requirement="测试自动修复",
    )

    config = VerifierConfig(
        enable_hallucination=False,  # 跳过幻觉检测
        enable_ast=True,
        enable_spec=True,
        enable_integration=False,
        enable_test=False,
        auto_fix=True,  # 启用自动修复
        max_fix_iterations=3,
    )

    verifier = EnhancedCodeVerifier(context, config)
    result = verifier.verify_file("test_service.py", test_code)

    print(f"验证状态: {result.status.value}")
    print(f"修复数量: {result.fixes_applied}")
    print()

    if result.fixes_applied > 0:
        print("修复后的代码中的错误码格式:")
        print("-" * 40)
        for line_no, line in enumerate(result.verified_content.split('\n'), 1):
            if '-0' in line and ('VAL' in line or 'BIZ' in line or 'SYS' in line or 'AUTH' in line or 'DB' in line):
                print(f"  L{line_no:3d}: {line.strip()}")
        print()

        # 显示修复前后对比
        print("修复对比:")
        print("-" * 40)
        original_lines = test_code.split('\n')
        fixed_lines = result.verified_content.split('\n')
        for i, (orig, fixed) in enumerate(zip(original_lines, fixed_lines), 1):
            if orig != fixed:
                print(f"  L{i}: {orig.strip()}")
                print(f"    → {fixed.strip()}")
        print()

    return result.fixes_applied > 0


def test_auto_fix_real_file():
    """测试真实文件的自动修复"""
    print()
    print("=" * 70)
    print(" 测试真实后端文件自动修复 ".center(70, "="))
    print("=" * 70)
    print()

    # 读取一个真实的服务文件
    test_file = project_root / "backend" / "services" / "daily_report_service.py"

    if not test_file.exists():
        print(f"文件不存在: {test_file}")
        return False

    original_content = test_file.read_text(encoding="utf-8")
    print(f"文件: {test_file.name}")
    print(f"大小: {len(original_content)} 字符")
    print()

    # 统计原始错误码
    import re
    underscore_codes = re.findall(r'["\']([A-Z]+_\d+)["\']', original_content)
    print(f"发现下划线格式错误码: {len(underscore_codes)} 个")
    if underscore_codes[:10]:
        print(f"  示例: {', '.join(underscore_codes[:10])}")
    print()

    # 创建验证器
    context = VerifyContext(
        project_root=project_root,
        requirement="自动修复错误码格式",
    )

    config = VerifierConfig(
        enable_hallucination=False,
        enable_ast=True,
        enable_spec=True,
        enable_integration=False,
        enable_test=False,
        auto_fix=True,
        max_fix_iterations=3,
    )

    verifier = EnhancedCodeVerifier(context, config)
    result = verifier.verify_file(str(test_file), original_content)

    print(f"验证状态: {result.status.value}")
    print(f"修复数量: {result.fixes_applied}")
    print()

    # 统计修复后的错误码
    if result.fixes_applied > 0:
        fixed_underscore_codes = re.findall(r'["\']([A-Z]+_\d+)["\']', result.verified_content)
        fixed_dash_codes = re.findall(r'["\']([A-Z]+-\d+)["\']', result.verified_content)

        print(f"修复后:")
        print(f"  下划线格式: {len(fixed_underscore_codes)} 个")
        print(f"  连字符格式: {len(fixed_dash_codes)} 个")
        print()

        # 保存修复后的内容到临时文件
        fixed_file = project_root / "backend" / "services" / "daily_report_service_FIXED.py"
        fixed_file.write_text(result.verified_content, encoding="utf-8")
        print(f"修复后的代码已保存到: {fixed_file}")
        print("(这是临时文件，用于预览修复结果)")
        print()

    return result.fixes_applied > 0


def test_dry_run_all_services():
    """预演修复所有服务文件"""
    print()
    print("=" * 70)
    print(" 预演修复所有服务文件 (不实际修改) ".center(70, "="))
    print("=" * 70)
    print()

    services_dir = project_root / "backend" / "services"
    service_files = list(services_dir.glob("*.py"))

    print(f"找到 {len(service_files)} 个服务文件")
    print()

    context = VerifyContext(
        project_root=project_root,
        requirement="批量自动修复",
    )

    config = VerifierConfig(
        enable_hallucination=False,
        enable_ast=True,
        enable_spec=True,
        enable_integration=False,
        enable_test=False,
        auto_fix=True,
    )

    verifier = EnhancedCodeVerifier(context, config)

    total_fixes = 0
    results_summary = []

    for service_file in service_files:
        if service_file.name.startswith("__"):
            continue

        content = service_file.read_text(encoding="utf-8")
        result = verifier.verify_file(str(service_file), content)

        if result.fixes_applied > 0:
            results_summary.append((service_file.name, result.fixes_applied))
            total_fixes += result.fixes_applied

    print("文件修复统计:")
    print("-" * 40)
    for filename, fixes in sorted(results_summary, key=lambda x: -x[1]):
        print(f"  {filename}: {fixes} 处修复")

    print()
    print(f"总计可修复: {total_fixes} 处")
    print()

    return total_fixes


if __name__ == "__main__":
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " 自动修复功能测试 ".center(68) + "║")
    print("╚" + "═" * 68 + "╝")

    # 测试 1: 测试代码自动修复
    test1_passed = test_auto_fix_error_codes()
    print("✅ 测试代码修复成功" if test1_passed else "❌ 测试代码修复失败")

    # 测试 2: 真实文件修复预览
    test2_passed = test_auto_fix_real_file()
    print("✅ 真实文件修复成功" if test2_passed else "❌ 真实文件无需修复")

    # 测试 3: 批量预演
    total = test_dry_run_all_services()
    print(f"✅ 批量预演完成，共 {total} 处可修复")

    print()
    print("=" * 70)
    print(" 测试完成 ".center(70, "="))
    print("=" * 70)
