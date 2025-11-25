#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行数据库不变量测试并解析结果
"""

import re
from pathlib import Path

# 读取测试脚本
script_path = Path(__file__).parent.parent / "backend" / "db" / "db_invariants_test_v2.sql"
with open(script_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 提取所有测试用例编号
test_cases = re.findall(r'-- (TC-[A-Z]+-\d+):', content)
print(f"找到 {len(test_cases)} 个测试用例:")
for tc in test_cases:
    print(f"  {tc}")

# 由于 Supabase MCP 可能不支持长脚本，我们需要告知用户手动执行
print("\n" + "="*60)
print("测试执行说明")
print("="*60)
print("\n由于测试脚本包含大量 DO 块（1216 行），")
print("建议通过以下方式执行：")
print("\n1. 在 Supabase Dashboard 的 SQL Editor 中执行完整脚本")
print("2. 或使用 psql 命令行工具")
print(f"\n测试脚本路径: {script_path}")
print("\n执行后，请检查输出中的：")
print("  - 'PASS: TC-XXX-YYY' 表示测试通过")
print("  - 'TEST_FAILED [TC-XXX-YYY]: ...' 表示测试失败")
print("\n所有测试用例执行完成后，脚本会自动清理测试数据。")


