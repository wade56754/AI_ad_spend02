"""
批量应用自动修复到所有服务文件
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
)


def apply_fixes_to_all_services():
    """批量修复所有服务文件"""
    print()
    print("=" * 70)
    print(" 批量修复服务文件 ".center(70, "="))
    print("=" * 70)
    print()

    services_dir = project_root / "backend" / "services"
    service_files = list(services_dir.glob("*.py"))

    print(f"找到 {len(service_files)} 个服务文件")
    print()

    context = VerifyContext(
        project_root=project_root,
        requirement="批量自动修复错误码格式",
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
    fixed_files = []

    for service_file in sorted(service_files):
        if service_file.name.startswith("__"):
            continue

        original_content = service_file.read_text(encoding="utf-8")
        result = verifier.verify_file(str(service_file), original_content)

        if result.fixes_applied > 0:
            # 写回修复后的内容
            service_file.write_text(result.verified_content, encoding="utf-8")
            fixed_files.append((service_file.name, result.fixes_applied))
            total_fixes += result.fixes_applied
            print(f"  [FIXED] {service_file.name}: {result.fixes_applied} 处修复")
        else:
            print(f"  [OK]    {service_file.name}: 无需修复")

    print()
    print("-" * 70)
    print(f"修复完成: {len(fixed_files)} 个文件, 共 {total_fixes} 处修复")
    print("-" * 70)

    return total_fixes, fixed_files


def apply_fixes_to_routers():
    """批量修复所有路由文件"""
    print()
    print("=" * 70)
    print(" 批量修复路由文件 ".center(70, "="))
    print("=" * 70)
    print()

    routers_dir = project_root / "backend" / "routers"
    router_files = list(routers_dir.glob("*.py"))

    print(f"找到 {len(router_files)} 个路由文件")
    print()

    context = VerifyContext(
        project_root=project_root,
        requirement="批量自动修复错误码格式",
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
    fixed_files = []

    for router_file in sorted(router_files):
        if router_file.name.startswith("__"):
            continue

        original_content = router_file.read_text(encoding="utf-8")
        result = verifier.verify_file(str(router_file), original_content)

        if result.fixes_applied > 0:
            # 写回修复后的内容
            router_file.write_text(result.verified_content, encoding="utf-8")
            fixed_files.append((router_file.name, result.fixes_applied))
            total_fixes += result.fixes_applied
            print(f"  [FIXED] {router_file.name}: {result.fixes_applied} 处修复")
        else:
            print(f"  [OK]    {router_file.name}: 无需修复")

    print()
    print("-" * 70)
    print(f"修复完成: {len(fixed_files)} 个文件, 共 {total_fixes} 处修复")
    print("-" * 70)

    return total_fixes, fixed_files


if __name__ == "__main__":
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " 批量自动修复 - 错误码格式 (下划线 → 连字符) ".center(60) + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    # 修复服务文件
    service_fixes, service_files = apply_fixes_to_all_services()

    # 修复路由文件
    router_fixes, router_files = apply_fixes_to_routers()

    # 汇总
    print()
    print("=" * 70)
    print(" 修复汇总 ".center(70, "="))
    print("=" * 70)
    print()
    print(f"服务文件: {len(service_files)} 个文件, {service_fixes} 处修复")
    print(f"路由文件: {len(router_files)} 个文件, {router_fixes} 处修复")
    print(f"总计: {len(service_files) + len(router_files)} 个文件, {service_fixes + router_fixes} 处修复")
    print()

    # 删除之前生成的预览文件
    preview_file = project_root / "backend" / "services" / "daily_report_service_FIXED.py"
    if preview_file.exists():
        preview_file.unlink()
        print("已删除预览文件: daily_report_service_FIXED.py")
