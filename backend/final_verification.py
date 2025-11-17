#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1 迁移最终验证
验证 Rev 001, 002, 005, 006 执行结果
"""

import os
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse

# 加载环境变量
load_dotenv('C:/Users/Administrator/.env')
db_url = os.getenv('DATABASE_URL')

# 解析连接字符串
parsed = urlparse(db_url)
dbname = parsed.path[1:]
user = parsed.username
password = parsed.password
host = parsed.hostname
port = parsed.port

print('=== Phase 1 迁移最终验证 ===')
print()

conn = psycopg2.connect(
    dbname=dbname,
    user=user,
    password=password,
    host=host,
    port=port
)
cursor = conn.cursor()

try:
    # ===== 验证 Rev 001: 主键类型 =====
    print('[Rev 001] 验证主键类型 (Integer -> BIGINT)')
    cursor.execute('''
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_name IN (
            'reconciliation_batches',
            'reconciliation_details',
            'reconciliation_adjustments',
            'reconciliation_reports'
        )
        AND column_name = 'id'
        ORDER BY table_name
    ''')
    all_bigint = True
    for table, col, dtype in cursor.fetchall():
        status = '[OK]' if dtype == 'bigint' else '[FAIL]'
        print(f'  {status} {table}.{col}: {dtype}')
        if dtype != 'bigint':
            all_bigint = False
    if all_bigint:
        print('  [PASS] 所有主键已升级为 BIGINT')
    else:
        print('  [FAIL] 部分主键类型不正确')
    print()

    # ===== 验证 Rev 002: status 枚举对齐 =====
    print('[Rev 002] 验证 status 枚举值')
    cursor.execute('''
        SELECT DISTINCT status FROM reconciliation_batches ORDER BY status
    ''')
    status_values = [row[0] for row in cursor.fetchall()]
    expected_statuses = ['closed', 'draft', 'pending', 'reviewing']

    if not status_values:
        print('  [OK] 表为空，无数据验证')
    else:
        invalid_statuses = [s for s in status_values if s not in expected_statuses]
        if invalid_statuses:
            print(f'  [FAIL] 发现非法 status 值: {invalid_statuses}')
        else:
            print(f'  [PASS] 所有 status 值符合 SoT 规范: {status_values}')

    # 检查 status_legacy 列是否存在
    cursor.execute('''
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'reconciliation_batches'
        AND column_name = 'status_legacy'
    ''')
    if cursor.fetchone():
        print('  [OK] status_legacy 备份列已创建')
    else:
        print('  [FAIL] status_legacy 备份列不存在')
    print()

    # ===== 验证 Rev 005: reconciliation_details 用户FK =====
    print('[Rev 005] 验证 reconciliation_details 用户FK类型')
    cursor.execute('''
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'reconciliation_details'
        AND column_name IN ('reviewed_by', 'resolved_by', 'reviewed_by_legacy', 'resolved_by_legacy')
        ORDER BY column_name
    ''')
    rev005_pass = True
    for col, dtype, nullable in cursor.fetchall():
        if '_legacy' in col:
            expected = 'integer'
        else:
            expected = 'uuid'
        status = '[OK]' if dtype == expected else '[FAIL]'
        print(f'  {status} {col}: {dtype} (nullable={nullable})')
        if dtype != expected:
            rev005_pass = False

    # 检查外键约束
    cursor.execute('''
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'reconciliation_details'
        AND constraint_type = 'FOREIGN KEY'
        AND constraint_name LIKE 'fk_%reviewed_by%' OR constraint_name LIKE 'fk_%resolved_by%'
    ''')
    fk_count = len(cursor.fetchall())
    print(f'  [OK] 外键约束数量: {fk_count}/2')
    if rev005_pass and fk_count == 2:
        print('  [PASS] Rev 005 验证通过')
    else:
        print('  [FAIL] Rev 005 验证失败')
    print()

    # ===== 验证 Rev 006: reconciliation_adjustments/reports 用户FK =====
    print('[Rev 006] 验证 reconciliation_adjustments/reports 用户FK类型')

    # reconciliation_adjustments
    cursor.execute('''
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'reconciliation_adjustments'
        AND column_name IN ('approved_by', 'finance_approved_by', 'approved_by_legacy', 'finance_approved_by_legacy')
        ORDER BY column_name
    ''')
    print('  reconciliation_adjustments:')
    rev006_adj_pass = True
    for col, dtype, nullable in cursor.fetchall():
        if '_legacy' in col:
            expected = 'integer'
        else:
            expected = 'uuid'
        status = '[OK]' if dtype == expected else '[FAIL]'
        print(f'    {status} {col}: {dtype}')
        if dtype != expected:
            rev006_adj_pass = False

    # reconciliation_reports
    cursor.execute('''
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'reconciliation_reports'
        AND column_name IN ('generated_by', 'generated_by_legacy')
        ORDER BY column_name
    ''')
    print('  reconciliation_reports:')
    rev006_rep_pass = True
    for col, dtype, nullable in cursor.fetchall():
        if '_legacy' in col:
            expected = 'integer'
        else:
            expected = 'uuid'
        status = '[OK]' if dtype == expected else '[FAIL]'
        print(f'    {status} {col}: {dtype}')
        if dtype != expected:
            rev006_rep_pass = False

    # 检查外键约束
    cursor.execute('''
        SELECT table_name, constraint_name
        FROM information_schema.table_constraints
        WHERE table_name IN ('reconciliation_adjustments', 'reconciliation_reports')
        AND constraint_type = 'FOREIGN KEY'
        AND (
            constraint_name LIKE 'fk_%approved_by%'
            OR constraint_name LIKE 'fk_%finance%'
            OR constraint_name LIKE 'fk_%generated_by%'
        )
        ORDER BY table_name
    ''')
    fk_list = cursor.fetchall()
    print(f'  [OK] 外键约束数量: {len(fk_list)}/3')
    for table, fk_name in fk_list:
        print(f'    - {table}: {fk_name}')

    if rev006_adj_pass and rev006_rep_pass and len(fk_list) == 3:
        print('  [PASS] Rev 006 验证通过')
    else:
        print('  [FAIL] Rev 006 验证失败')
    print()

    # ===== 数据完整性汇总 =====
    print('[数据完整性] 汇总统计')
    tables = [
        'reconciliation_batches',
        'reconciliation_details',
        'reconciliation_adjustments',
        'reconciliation_reports'
    ]
    for table in tables:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f'  {table}: {count} 条记录')
    print()

    # ===== 最终结论 =====
    print('=== 最终验证结果 ===')
    if all_bigint and rev005_pass and rev006_adj_pass and rev006_rep_pass:
        print('[SUCCESS] Phase 1 迁移验证通过！')
        print()
        print('下一步建议:')
        print('1. 观察期 7 天（保留 *_legacy 列）')
        print('2. 监控应用程序日志，确保无业务异常')
        print('3. 7 天后可考虑删除 *_legacy 列（需评估）')
        print('4. 更新相关业务代码以适配新的 UUID 类型')
    else:
        print('[WARNING] 部分验证未通过，请检查上述详细日志')

except Exception as e:
    print(f'[ERROR] 验证失败: {e}')
    import traceback
    traceback.print_exc()
finally:
    cursor.close()
    conn.close()
