#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SoT 验证器测试

测试 Hook 集成的验证能力:
1. 角色验证
2. 状态机验证
3. Phase 边界控制
4. 高风险模块检测
"""
import sys
from pathlib import Path

# 添加 lib 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.sot_validator import SoTValidator, validate_code, is_sot_compliant
from lib.config import VALID_ROLES, DEPRECATED_ROLES, SOT_VERSIONS


def test_role_validation():
    """测试角色验证"""
    print("\n=== 测试角色验证 ===")

    validator = SoTValidator()

    # 测试 1: 检测 supervisor
    code_with_supervisor = """
    if user.role == "supervisor":
        return True
    """
    issues = validator.validate_roles(code_with_supervisor, "test.py")
    assert len(issues) > 0, "应该检测到 supervisor"
    print(f"✅ 检测到废弃角色 supervisor: {issues[0].message}")

    # 测试 2: 检测 media_buyer
    code_with_media_buyer = """
    role = "media_buyer"
    """
    issues = validator.validate_roles(code_with_media_buyer, "test.py")
    assert len(issues) > 0, "应该检测到 media_buyer"
    print(f"✅ 检测到废弃角色 media_buyer: {issues[0].message}")

    # 测试 3: 合法角色不应报错
    code_with_valid_role = """
    role = "pitcher"
    """
    issues = validator.validate_roles(code_with_valid_role, "test.py")
    assert len(issues) == 0, "pitcher 是合法角色"
    print("✅ 合法角色 pitcher 通过验证")


def test_phase_boundary():
    """测试 Phase 边界控制"""
    print("\n=== 测试 Phase 边界控制 ===")

    validator = SoTValidator()

    # 测试 1: 检测 auto_reject
    code_with_auto_reject = """
    def process():
        if condition:
            auto_reject(user)
    """
    issues = validator.validate_phase_boundary(code_with_auto_reject, "test.py")
    assert len(issues) > 0, "应该检测到 auto_reject"
    print(f"✅ 检测到 Phase 1 违规 auto_reject: {issues[0].message}")

    # 测试 2: 检测 auto_suspend
    code_with_auto_suspend = """
    user.auto_suspend = True
    """
    issues = validator.validate_phase_boundary(code_with_auto_suspend, "test.py")
    assert len(issues) > 0, "应该检测到 auto_suspend"
    print(f"✅ 检测到 Phase 1 违规 auto_suspend: {issues[0].message}")

    # 测试 3: 合法操作应通过
    code_with_warning = """
    logger.warning("异常检测")
    send_notification(user)
    """
    issues = validator.validate_phase_boundary(code_with_warning, "test.py")
    assert len(issues) == 0, "warning/notification 是允许的"
    print("✅ 合法操作 (warning/notification) 通过验证")


def test_high_risk_detection():
    """测试高风险模块检测"""
    print("\n=== 测试高风险模块检测 ===")

    validator = SoTValidator()

    # 测试 1: 检测 ledger
    code_with_ledger = """
    class LedgerEntry:
        pass
    """
    issues = validator.detect_high_risk(code_with_ledger, "ledger_service.py")
    assert len(issues) > 0, "应该检测到 ledger 高风险模块"
    print(f"✅ 检测到高风险模块: {issues[0].message}")

    # 测试 2: 检测 profit
    code_with_profit = """
    def calculate_profit():
        gross_profit = revenue - cost
    """
    issues = validator.detect_high_risk(code_with_profit, "profit_calc.py")
    assert len(issues) > 0, "应该检测到 profit 高风险模块"
    print(f"✅ 检测到高风险模块: {issues[0].message}")


def test_comprehensive_validation():
    """测试综合验证"""
    print("\n=== 测试综合验证 ===")

    # 包含多种问题的代码
    bad_code = """
    if user.role == "supervisor":
        auto_reject(user)
        ledger_entries.append(entry)
    """

    result = validate_code(bad_code, "bad_code.py")

    print(f"验证结果: {'失败' if not result.success else '通过'}")
    print(f"问题数量: {len(result.issues)}")

    for issue in result.issues:
        icon = "🔴" if issue.level == "error" else "🟡"
        print(f"  {icon} [{issue.code}] {issue.message}")

    print(f"\n事件记录: {len(result.events)} 条")
    for event in result.events[:5]:
        print(f"  - {event}")


def test_config_loading():
    """测试配置加载"""
    print("\n=== 测试配置加载 ===")

    print(f"合法角色: {VALID_ROLES}")
    print(f"废弃角色: {DEPRECATED_ROLES}")
    print(f"SoT 版本: {SOT_VERSIONS}")

    assert "pitcher" in VALID_ROLES, "pitcher 应该在合法角色中"
    assert "supervisor" in DEPRECATED_ROLES, "supervisor 应该在废弃角色中"
    assert SOT_VERSIONS.get("MASTER.md") == "v4.8", "MASTER.md 版本应为 v4.8"

    print("✅ 配置加载正确")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("SoT 验证器测试 - 方案 C Hook 集成")
    print("=" * 60)

    try:
        test_config_loading()
        test_role_validation()
        test_phase_boundary()
        test_high_risk_detection()
        test_comprehensive_validation()

        print("\n" + "=" * 60)
        print("✅ 所有测试通过!")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 测试错误: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
