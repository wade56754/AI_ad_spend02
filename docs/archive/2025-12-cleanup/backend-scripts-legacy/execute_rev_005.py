#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rev 005: 修复 reconciliation_details 用户FK (Integer -> UUID)
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

print('=== [DBA] Rev 005: 修复 reconciliation_details 用户FK ===')
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
    # Step 1: 添加备份列
    print('[1/6] 添加备份列 reviewed_by_legacy, resolved_by_legacy...')
    cursor.execute('''
        ALTER TABLE reconciliation_details
        ADD COLUMN IF NOT EXISTS reviewed_by_legacy INTEGER
    ''')
    cursor.execute('''
        ALTER TABLE reconciliation_details
        ADD COLUMN IF NOT EXISTS resolved_by_legacy INTEGER
    ''')
    print('  [OK] 备份列已添加')

    # Step 2: 复制当前值到 legacy 列
    print('[2/6] 复制当前值到 legacy 列...')
    cursor.execute('''
        UPDATE reconciliation_details
        SET reviewed_by_legacy = reviewed_by,
            resolved_by_legacy = resolved_by
    ''')
    cursor.execute('SELECT COUNT(*) FROM reconciliation_details WHERE reviewed_by IS NOT NULL OR resolved_by IS NOT NULL')
    backup_count = cursor.fetchone()[0]
    print(f'  [OK] 已备份 {backup_count} 条记录的用户FK')

    # Step 3: 删除外键约束（如果存在）
    print('[3/6] 检查并删除现有外键约束...')
    cursor.execute('''
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'reconciliation_details'
        AND constraint_type = 'FOREIGN KEY'
        AND (constraint_name LIKE '%reviewed_by%' OR constraint_name LIKE '%resolved_by%')
    ''')
    fk_constraints = cursor.fetchall()
    for (constraint_name,) in fk_constraints:
        cursor.execute(f'ALTER TABLE reconciliation_details DROP CONSTRAINT IF EXISTS {constraint_name}')
        print(f'  [OK] 已删除约束: {constraint_name}')
    if not fk_constraints:
        print('  [OK] 未发现需要删除的外键约束')

    # Step 4: 修改列类型 INTEGER -> UUID (Strategy B: 置NULL)
    print('[4/6] 修改列类型 INTEGER -> UUID...')
    cursor.execute('ALTER TABLE reconciliation_details ALTER COLUMN reviewed_by DROP NOT NULL')
    cursor.execute('ALTER TABLE reconciliation_details ALTER COLUMN resolved_by DROP NOT NULL')
    cursor.execute('UPDATE reconciliation_details SET reviewed_by = NULL, resolved_by = NULL')
    cursor.execute('ALTER TABLE reconciliation_details ALTER COLUMN reviewed_by TYPE UUID USING NULL::UUID')
    cursor.execute('ALTER TABLE reconciliation_details ALTER COLUMN resolved_by TYPE UUID USING NULL::UUID')
    print('  [OK] 列类型已修改为 UUID')

    # Step 5: 添加外键约束到 auth.users
    print('[5/6] 添加外键约束到 auth.users...')
    cursor.execute('''
        ALTER TABLE reconciliation_details
        ADD CONSTRAINT fk_reconciliation_details_reviewed_by
        FOREIGN KEY (reviewed_by) REFERENCES auth.users(id) ON DELETE SET NULL
    ''')
    cursor.execute('''
        ALTER TABLE reconciliation_details
        ADD CONSTRAINT fk_reconciliation_details_resolved_by
        FOREIGN KEY (resolved_by) REFERENCES auth.users(id) ON DELETE SET NULL
    ''')
    print('  [OK] 外键约束已添加')

    # Gate #4 验证
    print()
    print('=== Gate #4: 验证 Rev 005 ===')

    # Check 1: 列类型验证
    cursor.execute('''
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'reconciliation_details'
        AND column_name IN ('reviewed_by', 'resolved_by', 'reviewed_by_legacy', 'resolved_by_legacy')
        ORDER BY column_name
    ''')
    print('  列类型验证:')
    for row in cursor.fetchall():
        col, dtype, nullable = row
        print(f'    {col}: {dtype} (nullable={nullable})')

    # Check 2: legacy 列数据完整性
    cursor.execute('''
        SELECT COUNT(*) FROM reconciliation_details
        WHERE reviewed_by_legacy IS NOT NULL OR resolved_by_legacy IS NOT NULL
    ''')
    legacy_count = cursor.fetchone()[0]
    print(f'  [OK] legacy 列保留 {legacy_count} 条历史记录')

    # Check 3: 外键约束验证
    cursor.execute('''
        SELECT constraint_name, column_name
        FROM information_schema.key_column_usage
        WHERE table_name = 'reconciliation_details'
        AND constraint_name LIKE 'fk_%'
        AND column_name IN ('reviewed_by', 'resolved_by')
    ''')
    fk_list = cursor.fetchall()
    print(f'  [OK] 外键约束数量: {len(fk_list)}')
    for constraint, col in fk_list:
        print(f'    - {constraint} ({col})')

    conn.commit()
    print()
    print('[SUCCESS] Rev 005 执行成功！')

except Exception as e:
    conn.rollback()
    print(f'[ERROR] 执行失败: {e}')
    import traceback
    traceback.print_exc()
finally:
    cursor.close()
    conn.close()
