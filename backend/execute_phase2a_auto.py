#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2A 自动执行脚本（无需确认）
基于 execute_phase2a.py，移除交互式确认
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse

# 加载环境变量
env_path = 'D:/git/1108/AI_ad_spend02/.env'
load_dotenv(env_path)
db_url = os.getenv('DATABASE_URL')

if not db_url:
    print(f"[ERROR] DATABASE_URL 未设置！检查 .env 文件: {env_path}")
    sys.exit(1)

# 解析连接字符串
parsed = urlparse(db_url)
dbname = parsed.path[1:]
user = parsed.username
password = parsed.password
host = parsed.hostname
port = parsed.port

print('=' * 60)
print('Phase 2A: 时间字段 timezone 修复（自动执行模式）')
print('=' * 60)
print(f'数据库: {dbname}')
print(f'主机: {host}')
print(f'端口: {port}')
print()
print('[AUTO] 自动执行模式，跳过确认步骤')
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
    # ========== Rev 2A-001: projects 模块 ==========
    print('[Rev 2A-001] 修复 projects 模块时间字段...')

    # projects 表
    print('  [1/7] projects 表...')
    cursor.execute("""
        ALTER TABLE projects
        ALTER COLUMN created_at TYPE TIMESTAMPTZ
        USING created_at AT TIME ZONE 'UTC'
    """)
    cursor.execute("""
        ALTER TABLE projects
        ALTER COLUMN updated_at TYPE TIMESTAMPTZ
        USING updated_at AT TIME ZONE 'UTC'
    """)
    print('    [OK] 2 个字段完成')

    # project_members 表
    print('  [2/7] project_members 表...')
    cursor.execute("""
        ALTER TABLE project_members
        ALTER COLUMN joined_at TYPE TIMESTAMPTZ
        USING joined_at AT TIME ZONE 'UTC'
    """)
    print('    [OK] 1 个字段完成')

    # project_expenses 表
    print('  [3/7] project_expenses 表...')
    cursor.execute("""
        ALTER TABLE project_expenses
        ALTER COLUMN occurred_at TYPE TIMESTAMPTZ
        USING occurred_at AT TIME ZONE 'UTC'
    """)
    cursor.execute("""
        ALTER TABLE project_expenses
        ALTER COLUMN created_at TYPE TIMESTAMPTZ
        USING created_at AT TIME ZONE 'UTC'
    """)
    print('    [OK] 2 个字段完成')

    print('[Rev 2A-001] 完成！3 个表，5 个字段')
    print()

    # ========== Rev 2A-002: topup 模块 ==========
    print('[Rev 2A-002] 修复 topup 模块时间字段...')

    # topup_requests 表
    print('  [4/7] topup_requests 表...')
    cursor.execute("""
        ALTER TABLE topup_requests
        ALTER COLUMN created_at TYPE TIMESTAMPTZ
        USING created_at AT TIME ZONE 'UTC'
    """)
    cursor.execute("""
        ALTER TABLE topup_requests
        ALTER COLUMN updated_at TYPE TIMESTAMPTZ
        USING updated_at AT TIME ZONE 'UTC'
    """)
    print('    [OK] 2 个字段完成')

    # topup_transactions 表
    print('  [5/7] topup_transactions 表...')
    cursor.execute("""
        ALTER TABLE topup_transactions
        ALTER COLUMN paid_at TYPE TIMESTAMPTZ
        USING paid_at AT TIME ZONE 'UTC'
    """)
    cursor.execute("""
        ALTER TABLE topup_transactions
        ALTER COLUMN created_at TYPE TIMESTAMPTZ
        USING created_at AT TIME ZONE 'UTC'
    """)
    print('    [OK] 2 个字段完成')

    # topup_approval_logs 表
    print('  [6/7] topup_approval_logs 表...')
    cursor.execute("""
        ALTER TABLE topup_approval_logs
        ALTER COLUMN created_at TYPE TIMESTAMPTZ
        USING created_at AT TIME ZONE 'UTC'
    """)
    print('    [OK] 1 个字段完成')

    print('[Rev 2A-002] 完成！3 个表，5 个字段')
    print()

    # ========== Rev 2A-003: ledger 模块 ==========
    print('[Rev 2A-003] 修复 ledger 模块时间字段...')

    # ledger_entries 表
    print('  [7/7] ledger_entries 表...')
    cursor.execute("""
        ALTER TABLE ledger_entries
        ALTER COLUMN occurred_at TYPE TIMESTAMPTZ
        USING occurred_at AT TIME ZONE 'UTC'
    """)
    print('    [OK] 1 个字段完成')

    print('[Rev 2A-003] 完成！1 个表，1 个字段')
    print()

    # ========== Gate 验证 ==========
    print('=' * 60)
    print('Gate #2A: 验证迁移结果')
    print('=' * 60)
    print()

    # Check 1: 字段类型验证
    print('[Check 1] 验证字段类型...')
    cursor.execute("""
        SELECT
            table_name,
            column_name,
            data_type,
            CASE
                WHEN data_type = 'timestamp with time zone' THEN 'PASS'
                ELSE 'FAIL'
            END AS status
        FROM information_schema.columns
        WHERE table_name IN (
            'projects', 'project_members', 'project_expenses',
            'topup_requests', 'topup_transactions', 'topup_approval_logs',
            'ledger_entries'
        )
        AND column_name IN (
            'created_at', 'updated_at', 'occurred_at', 'joined_at', 'paid_at'
        )
        ORDER BY table_name, column_name
    """)

    results = cursor.fetchall()
    all_pass = True
    for table, column, dtype, status in results:
        symbol = '✅' if status == 'PASS' else '❌'
        print(f'  {symbol} {table}.{column}: {dtype}')
        if status == 'FAIL':
            all_pass = False

    print()

    if not all_pass:
        print('[FAIL] 字段类型验证失败！正在回滚...')
        conn.rollback()
        print('[ROLLBACK] 已回滚所有更改')
        sys.exit(1)

    # Check 2: 数据完整性验证
    print('[Check 2] 验证数据完整性...')

    tables_to_check = [
        ('projects', ['created_at', 'updated_at']),
        ('project_members', ['joined_at']),
        ('project_expenses', ['occurred_at', 'created_at']),
        ('topup_requests', ['created_at', 'updated_at']),
        ('topup_transactions', ['paid_at', 'created_at']),
        ('topup_approval_logs', ['created_at']),
        ('ledger_entries', ['occurred_at']),
    ]

    integrity_pass = True
    for table, columns in tables_to_check:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        total_count = cursor.fetchone()[0]

        for col in columns:
            cursor.execute(f'SELECT COUNT({col}) FROM {table}')
            col_count = cursor.fetchone()[0]

            if total_count > 0 and col_count != total_count:
                print(f'  ❌ {table}.{col}: {col_count}/{total_count}')
                integrity_pass = False
            else:
                print(f'  ✅ {table}.{col}: {col_count}/{total_count}')

    print()

    if not integrity_pass:
        print('[WARNING] 数据完整性验证发现差异（可能字段允许 NULL）')
        print('[INFO] 如果字段定义允许 NULL，此警告可以忽略')
        print()

    # 提交事务
    conn.commit()

    print('=' * 60)
    print('✅ Phase 2A 执行成功！')
    print('=' * 60)
    print()
    print('下一步:')
    print('1. 执行完整的 Gate 验证: 查看 phase2a_gate_verification.sql')
    print('2. 更新 SQLAlchemy 模型代码（参考 PHASE2A_EXECUTION_GUIDE.md）')
    print('3. 进入 3 天观察期')
    print('4. 观察期无问题后，执行 Phase 2B')
    print()

except Exception as e:
    conn.rollback()
    print(f'[ERROR] 执行失败: {e}')
    print()
    import traceback
    traceback.print_exc()
    print()
    print('[ROLLBACK] 已回滚所有更改')
    print('[INFO] 数据库已恢复到执行前状态')
    sys.exit(1)

finally:
    cursor.close()
    conn.close()
