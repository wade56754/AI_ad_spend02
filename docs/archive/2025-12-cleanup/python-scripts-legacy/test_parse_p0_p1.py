#!/usr/bin/env python3
"""
测试 super_review_agent.py 中的 parse_p0_p1_count 函数
"""

import sys
from pathlib import Path

# 导入 super_review_agent 模块
sys.path.insert(0, str(Path(__file__).parent))
from super_review_agent import parse_p0_p1_count

def test_parse_p0_p1():
    """测试 parse_p0_p1_count 函数的 7 种解析方法"""

    # 读取模拟审查报告
    report_path = Path("test_super_review/mock_review_report.md")
    if not report_path.exists():
        print(f"❌ 测试文件不存在: {report_path}")
        return

    review_report = report_path.read_text(encoding='utf-8')

    print("=" * 70)
    print("[TEST] parse_p0_p1_count function")
    print("=" * 70)
    print(f"Test file: {report_path}")
    print(f"Report length: {len(review_report)} chars")
    print()

    # 执行解析
    p0_count, p1_count, is_parsed = parse_p0_p1_count(review_report)

    print("=" * 70)
    print("[RESULT] Parse result")
    print("=" * 70)
    print(f"[OK] P0 defects: {p0_count}")
    print(f"[OK] P1 defects: {p1_count}")
    print(f"[OK] Parse status: {'Success' if is_parsed else 'Failed'}")
    print()

    # 验证结果
    expected_p0 = 2
    expected_p1 = 3

    print("=" * 70)
    print("[VERIFY] Validation")
    print("=" * 70)

    if p0_count == expected_p0:
        print(f"[PASS] P0 count correct: {p0_count} == {expected_p0}")
    else:
        print(f"[FAIL] P0 count wrong: {p0_count} != {expected_p0}")

    if p1_count == expected_p1:
        print(f"[PASS] P1 count correct: {p1_count} == {expected_p1}")
    else:
        print(f"[FAIL] P1 count wrong: {p1_count} != {expected_p1}")

    if is_parsed:
        print(f"[PASS] Parse status correct: Success")
    else:
        print(f"[FAIL] Parse status wrong: Failed")

    print()

    # 总结
    if p0_count == expected_p0 and p1_count == expected_p1 and is_parsed:
        print("[SUMMARY] Test PASSED: parse_p0_p1_count works correctly!")
        return 0
    else:
        print("[SUMMARY] Test FAILED: parse_p0_p1_count has issues")
        return 1


def test_additional_formats():
    """测试额外的格式（方法 7: 正面检测）"""

    print()
    print("=" * 70)
    print("[TEST] Method 7: Positive detection (no defects)")
    print("=" * 70)

    test_cases = [
        ("wu P0 que xian, wu P1 que xian", 0, 0),
        ("P0 que xian: 0ge, P1 que xian: 0ge", 0, 0),
        ("P0: 0, P1: 0", 0, 0),
        ("No P0 defects, No P1 defects", 0, 0),
    ]

    for report, expected_p0, expected_p1 in test_cases:
        p0, p1, parsed = parse_p0_p1_count(report)
        status = "[PASS]" if (p0 == expected_p0 and p1 == expected_p1 and parsed) else "[FAIL]"
        print(f"{status} \"{report}\" => P0: {p0}, P1: {p1}, parsed: {parsed}")

    print()


if __name__ == "__main__":
    exit_code = test_parse_p0_p1()
    test_additional_formats()
    sys.exit(exit_code)
