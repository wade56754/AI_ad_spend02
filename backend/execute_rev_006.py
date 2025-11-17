#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rev 006: 修复 reconciliation_adjustments 和 reconciliation_reports 用户FK (Integer -> UUID)
Strategy B: 置NULL + legacy备份
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

print('=== [DBA] Rev 006: 修复 reconciliation_adjustments/reports 用户FK ===')
print()

conn = psycopg2.connect(
    dbname=dbname,
    user=user,
    password=password,
    host=host,
    port=port
)
conn.autocommit = False
cursor = conn.cursor()

try:
    # ===== 表1: reconciliation_adjustments =====
    print('>>> 表1: reconciliation_adjustments')

    # Step 1: 添加备份列
    print('[1/6] 添加备份列 approved_by_legacy, finance_approved_by_legacy...')
    cursor.execute('''
        ALTER TABLE reconciliation_adjustments
        ADD COLUMN IF NOT EXISTS approved_by_legacy INTEGER
    ''')
    cursor.execute('''
        ALTER TABLE reconciliation_adjustments
        ADD COLUMN IF NOT EXISTS finance_approved_by_legacy INTEGER
    ''')
    print('  [OK] 备份列已添加')

    # Step 2: 复制当前值到 legacy 列
    print('[2/6] 复制当前值到 legacy 列...')
    cursor.execute('''
        UPDATE reconciliation_adjustments
        SET approved_by_legacy = approved_by,
            finance_approved_by_legacy = finance_approved_by
    ''')
    cursor.execute('SELECT COUNT(*) FROM reconciliation_adjustments WHERE approved_by IS NOT NULL OR finance_approved_by IS NOT NULL')
    backup_count = cursor.fetchone()[0]
    print(f'  [OK] 已备份 {backup_count} 条记录的用户FK')

    # Step 3: 删除外键约束（如果存在）
    print('[3/6] 检查并删除现有外键约束...')
    cursor.execute('''
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'reconciliation_adjustments'
        AND constraint_type = 'FOREIGN KEY'
        AND (constraint_name LIKE '%approved_by%' OR constraint_name LIKE '%finance%')
    ''')
    fk_constraints = cursor.fetchall()
    for (constraint_name,) in fk_constraints:
        cursor.execute(f'ALTER TABLE reconciliation_adjustments DROP CONSTRAINT IF EXISTS {constraint_name}')
        print(f'  [OK] 已删除约束: {constraint_name}')
    if not fk_constraints:
        print('  [OK] 未发现需要删除的外键约束')

    # Step 4: 修改列类型 INTEGER -> UUID (Strategy B: 置NULL)
    print('[4/6] 修改列类型 INTEGER -> UUID...')
    cursor.execute('ALTER TABLE reconciliation_adjustments ALTER COLUMN approved_by DROP NOT NULL')
    cursor.execute('ALTER TABLE reconciliation_adjustments ALTER COLUMN finance_approved_by DROP NOT NULL')
    cursor.execute('UPDATE reconciliation_adjustments SET approved_by = NULL, finance_approved_by = NULL')
    cursor.execute('ALTER TABLE reconciliation_adjustments ALTER COLUMN approved_by TYPE UUID USING NULL::UUID')
    cursor.execute('ALTER TABLE reconciliation_adjustments ALTER COLUMN finance_approved_by TYPE UUID USING NULL::UUID')
    print('  [OK] 列类型已修改为 UUID')

    # Step 5: 添加外键约束到 auth.users
    print('[5/6] 添加外键约束到 auth.users...')
    cursor.execute('''
        ALTER TABLE reconciliation_adjustments
        ADD CONSTRAINT fk_reconciliation_adjustments_approved_by
        FOREIGN KEY (approved_by) REFERENCES auth.users(id) ON DELETE SET NULL
    ''')
    cursor.execute('''
        ALTER TABLE reconciliation_adjustments
        ADD CONSTRAINT fk_reconciliation_adjustments_finance_approved_by
        FOREIGN KEY (finance_approved_by) REFERENCES auth.users(id) ON DELETE SET NULL
    ''')
    print('  [OK] 外键约束已添加')
    print()

    # ===== 表2: reconciliation_reports =====
    print('>>> 表2: reconciliation_reports')

    # Step 1: 添加备份列
    print('[1/6] 添加备份列 generated_by_legacy...')
    cursor.execute('''
        ALTER TABLE reconciliation_reports
        ADD COLUMN IF NOT EXISTS generated_by_legacy INTEGER
    ''')
    print('  [OK] 备份列已添加')

    # Step 2: 复制当前值到 legacy 列
    print('[2/6] 复制当前值到 legacy 列...')
    cursor.execute('''
        UPDATE reconciliation_reports
        SET generated_by_legacy = generated_by
    ''')
    cursor.execute('SELECT COUNT(*) FROM reconciliation_reports WHERE generated_by IS NOT NULL')
    backup_count2 = cursor.fetchone()[0]
    print(f'  [OK] 已备份 {backup_count2} 条记录的用户FK')

    # Step 3: 删除外键约束（如果存在）
    print('[3/6] 检查并删除现有外键约束...')
    cursor.execute('''
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'reconciliation_reports'
        AND constraint_type = 'FOREIGN KEY'
        AND constraint_name LIKE '%generated_by%'
    ''')
    fk_constraints2 = cursor.fetchall()
    for (constraint_name,) in fk_constraints2:
        cursor.execute(f'ALTER TABLE reconciliation_reports DROP CONSTRAINT IF EXISTS {constraint_name}')
        print(f'  [OK] 已删除约束: {constraint_name}')
    if not fk_constraints2:
        print('  [OK] 未发现需要删除的外键约束')

    # Step 4: 修改列类型 INTEGER -> UUID (Strategy B: 置NULL)
    print('[4/6] 修改列类型 INTEGER -> UUID...')
    cursor.execute('ALTER TABLE reconciliation_reports ALTER COLUMN generated_by DROP NOT NULL')
    cursor.execute('UPDATE reconciliation_reports SET generated_by = NULL')
    cursor.execute('ALTER TABLE reconciliation_reports ALTER COLUMN generated_by TYPE UUID USING NULL::UUID')
    print('  [OK] 列类型已修改为 UUID')

    # Step 5: 添加外键约束到 auth.users
    print('[5/6] 添加外键约束到 auth.users...')
    cursor.execute('''
        ALTER TABLE reconciliation_reports
        ADD CONSTRAINT fk_reconciliation_reports_generated_by
        FOREIGN KEY (generated_by) REFERENCES auth.users(id) ON DELETE SET NULL
    ''')
    print('  [OK] 外键约束已添加')

    # Gate #4 验证
    print()
    print('=== Gate #4: 验证 Rev 006 ===')

    # Check 1: reconciliation_adjustments 列类型验证
    cursor.execute('''
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'reconciliation_adjustments'
        AND column_name IN ('approved_by', 'finance_approved_by', 'approved_by_legacy', 'finance_approved_by_legacy')
        ORDER BY column_name
    ''')
    print('  reconciliation_adjustments 列类型:')
    for row in cursor.fetchall():
        col, dtype, nullable = row
        print(f'    {col}: {dtype} (nullable={nullable})')

    # Check 2: reconciliation_reports 列类型验证
    cursor.execute('''
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'reconciliation_reports'
        AND column_name IN ('generated_by', 'generated_by_legacy')
        ORDER BY column_name
    ''')
    print('  reconciliation_reports 列类型:')
    for row in cursor.fetchall():
        col, dtype, nullable = row
        print(f'    {col}: {dtype} (nullable={nullable})')

    # Check 3: legacy 列数据完整性
    cursor.execute('''
        SELECT COUNT(*) FROM reconciliation_adjustments
        WHERE approved_by_legacy IS NOT NULL OR finance_approved_by_legacy IS NOT NULL
    ''')
    legacy_count1 = cursor.fetchone()[0]
    cursor.execute('''
        SELECT COUNT(*) FROM reconciliation_reports
        WHERE generated_by_legacy IS NOT NULL
    ''')
    legacy_count2 = cursor.fetchone()[0]
    print(f'  [OK] reconciliation_adjustments legacy 列保留 {legacy_count1} 条历史记录')
    print(f'  [OK] reconciliation_reports legacy 列保留 {legacy_count2} 条历史记录')

    # Check 4: 外键约束验证
    cursor.execute('''
        SELECT constraint_name, column_name, table_name
        FROM information_schema.key_column_usage
        WHERE table_name IN ('reconciliation_adjustments', 'reconciliation_reports')
        AND constraint_name LIKE 'fk_%'
        AND column_name IN ('approved_by', 'finance_approved_by', 'generated_by')
        ORDER BY table_name, column_name
    ''')
    fk_list = cursor.fetchall()
    print(f'  [OK] 外键约束总数: {len(fk_list)}')
    for constraint, col, table in fk_list:
        print(f'    - {table}.{col} -> {constraint}')

    conn.commit()
    print()
    print('[SUCCESS] Rev 006 执行成功！')

except Exception as e:
    conn.rollback()
    print(f'[ERROR] 执行失败: {e}')
    import traceback
    traceback.print_exc()
finally:
    cursor.close()
    conn.close()
