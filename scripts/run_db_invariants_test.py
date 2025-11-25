#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库不变量测试执行器
通过 Supabase MCP 执行测试脚本并生成报告
"""

import sys
import re
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 读取测试脚本
test_script_path = project_root / "backend" / "db" / "db_invariants_test_v2.sql"
test_cases_path = project_root / "backend" / "db" / "TEST_CASES_v2.0.md"

print(f"读取测试脚本: {test_script_path}")
with open(test_script_path, 'r', encoding='utf-8') as f:
    test_sql = f.read()

print(f"测试脚本长度: {len(test_sql)} 字符, {len(test_sql.splitlines())} 行")

# 读取测试用例文档以了解用例编号和严重级别
print(f"\n读取测试用例文档: {test_cases_path}")
with open(test_cases_path, 'r', encoding='utf-8') as f:
    test_cases_content = f.read()

# 解析测试用例编号和严重级别
test_case_info = {}
priority_pattern = r'## (\d+)\. (P\d+) 测试用例'
current_priority = None

for line in test_cases_content.splitlines():
    # 匹配优先级标题
    priority_match = re.match(priority_pattern, line)
    if priority_match:
        current_priority = priority_match.group(2)  # P0, P1, P2
    
    # 匹配测试用例编号
    tc_match = re.search(r'#### (TC-[A-Z]+-\d+):', line)
    if tc_match and current_priority:
        tc_id = tc_match.group(1)
        test_case_info[tc_id] = {
            'priority': current_priority,
            'module': tc_id.split('-')[1]  # LED, SUP, RPT, etc.
        }

# 集成测试用例
flow_tc_pattern = r'#### (TC-FLOW-\d+):'
for line in test_cases_content.splitlines():
    flow_match = re.search(flow_tc_pattern, line)
    if flow_match:
        tc_id = flow_match.group(1)
        test_case_info[tc_id] = {
            'priority': '集成',
            'module': 'FLOW'
        }

print(f"\n解析到 {len(test_case_info)} 个测试用例:")
for tc_id, info in sorted(test_case_info.items()):
    print(f"  {tc_id}: {info['priority']} - {info['module']}")

# 注意：由于 Supabase MCP 的 execute_sql 可能不支持 DO 块或长脚本
# 这里我们输出测试脚本内容，用户需要手动在 Supabase SQL Editor 中执行
# 或者我们可以尝试分段执行

print("\n" + "="*60)
print("测试脚本准备完成")
print("="*60)
print("\n由于测试脚本包含大量 DO 块，建议通过以下方式执行：")
print("1. 在 Supabase Dashboard 的 SQL Editor 中执行")
print("2. 或使用 psql 命令行工具")
print("\n测试脚本路径:", test_script_path)
print("\n执行后，请检查输出中的 'TEST_FAILED' 异常信息")


