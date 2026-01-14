#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试断言质量检查脚本

检测问题:
1. 过于宽松的状态码断言 (包含 500)
2. 同时接受成功和失败状态码
3. 使用废弃角色的测试

使用方法:
  python backend/scripts/check_test_assertions.py

退出码:
  0 - 无问题
  1 - 发现问题
"""

import re
import sys
from pathlib import Path
from typing import List, Dict

ROOT_DIR = Path(__file__).parent.parent.parent
TESTS_DIR = ROOT_DIR / "backend" / "tests"


def find_loose_assertions() -> List[Dict]:
    """查找过于宽松的状态码断言"""
    issues = []

    # 匹配 status_code in [...] 模式
    pattern = re.compile(r'status_code\s+in\s+\[([^\]]+)\]')

    for py_file in TESTS_DIR.rglob("*.py"):
        try:
            content = py_file.read_text(encoding='utf-8')
        except Exception:
            continue

        for line_num, line in enumerate(content.split('\n'), 1):
            match = pattern.search(line)
            if match:
                codes_str = match.group(1)
                # 解析状态码列表
                codes = [c.strip() for c in codes_str.split(',')]
                code_values = []
                for code in codes:
                    # 处理 status.HTTP_xxx 和直接数字
                    if code.isdigit():
                        code_values.append(int(code))
                    elif 'HTTP_' in code:
                        # 提取数字部分
                        num_match = re.search(r'HTTP_(\d+)', code)
                        if num_match:
                            code_values.append(int(num_match.group(1)))

                # 检查问题
                has_500 = 500 in code_values
                has_success = any(200 <= c < 300 for c in code_values)
                has_error = any(c >= 400 for c in code_values)

                if has_500:
                    issues.append({
                        'file': str(py_file.relative_to(ROOT_DIR)),
                        'line': line_num,
                        'type': 'accepts_500',
                        'message': '500 should never be acceptable',
                        'codes': code_values
                    })
                elif has_success and has_error and len(code_values) > 2:
                    issues.append({
                        'file': str(py_file.relative_to(ROOT_DIR)),
                        'line': line_num,
                        'type': 'too_loose',
                        'message': 'Assertion accepts both success and error codes',
                        'codes': code_values
                    })

    return issues


def find_deprecated_roles() -> List[Dict]:
    """查找使用废弃角色的测试"""
    issues = []
    deprecated_roles = ['data_operator', 'supervisor']

    for py_file in TESTS_DIR.rglob("*.py"):
        try:
            content = py_file.read_text(encoding='utf-8')
        except Exception:
            continue

        for line_num, line in enumerate(content.split('\n'), 1):
            for role in deprecated_roles:
                if role in line.lower() and 'deprecated' not in line.lower():
                    # 排除注释和文档字符串
                    stripped = line.strip()
                    if not stripped.startswith('#') and not stripped.startswith('"""'):
                        issues.append({
                            'file': str(py_file.relative_to(ROOT_DIR)),
                            'line': line_num,
                            'type': 'deprecated_role',
                            'message': f'Uses deprecated role: {role}',
                            'role': role
                        })

    return issues


def print_report(assertion_issues: List[Dict], role_issues: List[Dict]) -> bool:
    """打印报告"""
    print("=" * 80)
    print("Test Quality Check Report")
    print("=" * 80)

    # 统计
    accepts_500 = [i for i in assertion_issues if i['type'] == 'accepts_500']
    too_loose = [i for i in assertion_issues if i['type'] == 'too_loose']

    print(f"\n[Assertion Issues]")
    print(f"  Accepts 500 as valid: {len(accepts_500)}")
    print(f"  Too loose (success+error): {len(too_loose)}")

    if accepts_500:
        print(f"\n[ERROR] Tests that accept 500 (must fix):")
        print("-" * 60)
        # 按文件分组
        by_file = {}
        for issue in accepts_500:
            f = issue['file']
            if f not in by_file:
                by_file[f] = []
            by_file[f].append(issue['line'])

        for f, lines in sorted(by_file.items()):
            print(f"  {f}")
            print(f"    Lines: {', '.join(map(str, lines[:5]))}{'...' if len(lines) > 5 else ''}")

    print(f"\n[Deprecated Role Usage]")
    print(f"  Uses deprecated roles: {len(role_issues)}")

    if role_issues:
        print(f"\n[WARN] Tests using deprecated roles:")
        print("-" * 60)
        by_file = {}
        for issue in role_issues:
            f = issue['file']
            if f not in by_file:
                by_file[f] = set()
            by_file[f].add(issue['role'])

        for f, roles in sorted(by_file.items())[:10]:
            print(f"  {f}: {', '.join(roles)}")
        if len(by_file) > 10:
            print(f"  ... and {len(by_file) - 10} more files")

    # 汇总
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)

    total_issues = len(accepts_500) + len(too_loose) + len(role_issues)
    if total_issues == 0:
        print("\n[OK] No issues found!")
        return True

    print(f"\n[WARN] Found {total_issues} issue(s)")
    print(f"  - {len(accepts_500)} assertions accept 500 (CRITICAL)")
    print(f"  - {len(too_loose)} assertions too loose")
    print(f"  - {len(role_issues)} uses of deprecated roles")

    return len(accepts_500) == 0  # Only fail on 500 acceptance


def main():
    print("Scanning test files...")

    assertion_issues = find_loose_assertions()
    role_issues = find_deprecated_roles()

    success = print_report(assertion_issues, role_issues)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
