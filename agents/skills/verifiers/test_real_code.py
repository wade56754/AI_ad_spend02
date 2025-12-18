"""
使用真实后端代码测试验证器
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


def test_real_backend_files():
    """测试真实后端文件"""
    print()
    print("=" * 70)
    print(" 使用真实后端代码测试验证器 ".center(70, "="))
    print("=" * 70)
    print()

    # 要测试的文件
    test_files = [
        "backend/services/daily_report_service.py",
        "backend/services/topup_service.py",
        "backend/services/transfer_service.py",
        "backend/services/ledger_service.py",
        "backend/routers/daily_reports.py",
        "backend/routers/topup.py",
        "backend/routers/transfers.py",
    ]

    # 创建验证器
    context = VerifyContext(
        project_root=project_root,
        requirement="验证后端代码质量",
        valid_states={
            # 日报 8 状态
            "raw_submitted", "trend_pending", "trend_ok", "trend_flagged",
            "trend_resolved", "final_pending", "final_confirmed", "final_locked",
            # 充值状态
            "pending", "approved", "rejected", "settled",
            # 转账状态
            "completed", "failed", "cancelled",
        },
        valid_roles={"admin", "finance", "data_operator", "account_manager", "media_buyer"},
    )

    config = VerifierConfig(
        enable_hallucination=True,
        enable_ast=True,
        enable_spec=True,
        enable_integration=True,
        enable_test=False,
        auto_fix=False,
        strict_mode=False,
    )

    verifier = EnhancedCodeVerifier(context, config)

    # 收集所有文件内容
    files_to_verify = []
    for file_path in test_files:
        full_path = project_root / file_path
        if full_path.exists():
            content = full_path.read_text(encoding="utf-8")
            files_to_verify.append((file_path, content))
            print(f"[+] 加载: {file_path} ({len(content)} 字符)")
        else:
            print(f"[-] 跳过 (不存在): {file_path}")

    print()
    print("-" * 70)
    print(" 开始验证 ".center(70, "-"))
    print("-" * 70)
    print()

    # 批量验证
    results = verifier.verify_files(files_to_verify)

    # 显示每个文件的结果
    total_errors = 0
    total_warnings = 0

    for result in results:
        errors = [i for i in result.issues if i.severity == IssueSeverity.ERROR]
        warnings = [i for i in result.issues if i.severity == IssueSeverity.WARNING]
        total_errors += len(errors)
        total_warnings += len(warnings)

        status_icon = {
            "passed": "[PASS]",
            "fixed": "[FIX]",
            "failed": "[FAIL]",
            "skipped": "[SKIP]",
        }.get(result.status.value, "[???]")

        print(f"{status_icon} {result.path}")
        print(f"    错误: {len(errors)}, 警告: {len(warnings)}")

        # 显示前 5 个问题
        shown = 0
        for issue in result.issues:
            if shown >= 5:
                remaining = len(result.issues) - shown
                print(f"    ... 还有 {remaining} 个问题")
                break

            severity_icon = "X" if issue.severity == IssueSeverity.ERROR else "!"
            print(f"    [{severity_icon}] L{issue.line:3d} [{issue.code}] {issue.message[:60]}")
            shown += 1

        print()

    # 汇总
    print("=" * 70)
    print(" 验证汇总 ".center(70, "="))
    print("=" * 70)
    print()

    passed = len([r for r in results if r.status.value == "passed"])
    failed = len([r for r in results if r.status.value == "failed"])

    print(f"总文件数: {len(results)}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"总错误: {total_errors}")
    print(f"总警告: {total_warnings}")
    print()

    # 按类别统计问题
    print("-" * 70)
    print(" 问题分类统计 ".center(70, "-"))
    print("-" * 70)

    issues_by_code = {}
    for result in results:
        for issue in result.issues:
            code = issue.code
            if code not in issues_by_code:
                issues_by_code[code] = {"count": 0, "message": issue.message}
            issues_by_code[code]["count"] += 1

    # 按数量排序
    sorted_issues = sorted(issues_by_code.items(), key=lambda x: -x[1]["count"])

    for code, info in sorted_issues[:15]:
        print(f"  [{code}] x{info['count']:3d} - {info['message'][:50]}")

    if len(sorted_issues) > 15:
        print(f"  ... 还有 {len(sorted_issues) - 15} 种问题类型")

    print()

    # 生成详细报告
    print("-" * 70)
    print(" 生成 Markdown 报告 ".center(70, "-"))
    print("-" * 70)

    report = verifier.generate_report(results, format="markdown")

    # 保存报告
    report_path = project_root / "agents" / "skills" / "verifiers" / "VERIFICATION_REPORT.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"报告已保存到: {report_path}")
    print()

    return total_errors == 0


def test_specific_issues():
    """测试特定问题检测"""
    print()
    print("=" * 70)
    print(" 测试特定问题检测 ".center(70, "="))
    print("=" * 70)
    print()

    # 读取一个真实的 service 文件来检测特定问题
    topup_service_path = project_root / "backend" / "services" / "topup_service.py"

    if not topup_service_path.exists():
        print("topup_service.py 不存在，跳过")
        return True

    content = topup_service_path.read_text(encoding="utf-8")

    context = VerifyContext(
        project_root=project_root,
        requirement="检测充值服务问题",
        valid_states={"pending", "approved", "rejected", "settled"},
    )

    config = VerifierConfig(
        enable_hallucination=True,
        enable_ast=True,
        enable_spec=True,
        enable_integration=False,  # 跳过集成验证减少噪音
        enable_test=False,
        auto_fix=False,
    )

    verifier = EnhancedCodeVerifier(context, config)
    result = verifier.verify_file("backend/services/topup_service.py", content)

    print(f"文件: topup_service.py")
    print(f"状态: {result.status.value}")
    print(f"问题数: {len(result.issues)}")
    print()

    # 按严重程度分组
    errors = [i for i in result.issues if i.severity == IssueSeverity.ERROR]
    warnings = [i for i in result.issues if i.severity == IssueSeverity.WARNING]

    if errors:
        print("错误:")
        for issue in errors[:10]:
            print(f"  L{issue.line:3d} [{issue.code}] {issue.message}")
            if issue.suggestion:
                print(f"        建议: {issue.suggestion[:60]}")
        if len(errors) > 10:
            print(f"  ... 还有 {len(errors) - 10} 个错误")
        print()

    if warnings:
        print("警告:")
        for issue in warnings[:10]:
            print(f"  L{issue.line:3d} [{issue.code}] {issue.message}")
        if len(warnings) > 10:
            print(f"  ... 还有 {len(warnings) - 10} 个警告")
        print()

    return True


if __name__ == "__main__":
    test_real_backend_files()
    print()
    test_specific_issues()
