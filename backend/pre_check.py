#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2A 执行前环境检查脚本
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse

print('=' * 70)
print('Phase 2A 执行前环境检查')
print('=' * 70)
print()

# ========== Check 1: 环境变量 ==========
print('[Check 1] 检查环境变量...')
load_dotenv('C:/Users/Administrator/.env')
db_url = os.getenv('DATABASE_URL')

if not db_url:
    print('  [FAIL] DATABASE_URL 未设置')
    sys.exit(1)
else:
    parsed = urlparse(db_url)
    print(f'  [PASS] DATABASE_URL 已设置')
    print(f'     主机: {parsed.hostname}')
    print(f'     端口: {parsed.port}')
    print(f'     数据库: {parsed.path[1:]}')

    # 判断环境
    if 'supabase.co' in parsed.hostname:
        if 'dev' in parsed.hostname or 'test' in parsed.hostname:
            print(f'     环境: Dev/Test [OK]')
        else:
            print(f'     环境: [WARNING] 请确认不是生产环境！')
print()

# ========== Check 2: 数据库连接 ==========
print('[Check 2] 测试数据库连接...')
try:
    conn = psycopg2.connect(
        dbname=parsed.path[1:],
        user=parsed.username,
        password=parsed.password,
        host=parsed.hostname,
        port=parsed.port
    )
    cursor = conn.cursor()

    # 获取数据库版本
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f'  [PASS] 数据库连接成功')
    print(f'     版本: {version.split(",")[0]}')

except Exception as e:
    print(f'  [FAIL] 数据库连接失败: {e}')
    sys.exit(1)
print()

# ========== Check 3: 目标表存在性 ==========
print('[Check 3] 检查目标表是否存在...')
target_tables = [
    'projects', 'project_members', 'project_expenses',
    'topup_requests', 'topup_transactions', 'topup_approval_logs',
    'ledger_entries'
]

cursor.execute("""
    SELECT tablename
    FROM pg_tables
    WHERE tablename IN %s
    ORDER BY tablename
""", (tuple(target_tables),))

existing_tables = [row[0] for row in cursor.fetchall()]

if len(existing_tables) == len(target_tables):
    print(f'  [PASS] 所有目标表都存在 ({len(existing_tables)}/7)')
    for table in existing_tables:
        print(f'     - {table}')
else:
    print(f'  [FAIL] 部分表缺失 ({len(existing_tables)}/7)')
    missing = set(target_tables) - set(existing_tables)
    print(f'     缺失: {missing}')
    cursor.close()
    conn.close()
    sys.exit(1)
print()

# ========== Check 4: 当前字段类型 ==========
print('[Check 4] 检查当前时间字段类型...')
cursor.execute("""
    SELECT
        table_name,
        column_name,
        data_type
    FROM information_schema.columns
    WHERE table_name IN %s
    AND column_name IN ('created_at', 'updated_at', 'occurred_at', 'joined_at', 'paid_at')
    ORDER BY table_name, column_name
""", (tuple(target_tables),))

field_types = cursor.fetchall()
timestamp_count = 0
timestamptz_count = 0

for table, column, dtype in field_types:
    if dtype == 'timestamp without time zone':
        print(f'  [TODO] {table}.{column}: TIMESTAMP (待升级)')
        timestamp_count += 1
    elif dtype == 'timestamp with time zone':
        print(f'  [DONE] {table}.{column}: TIMESTAMPTZ (已升级)')
        timestamptz_count += 1
    else:
        print(f'  [WARN] {table}.{column}: {dtype} (非预期类型)')

print()
print(f'  汇总: TIMESTAMP={timestamp_count}, TIMESTAMPTZ={timestamptz_count}')

if timestamp_count == 14:
    print(f'  [PASS] 所有 14 个字段都是 TIMESTAMP，符合 Phase 2A 执行前提')
elif timestamptz_count == 14:
    print(f'  [WARN] 所有字段已经是 TIMESTAMPTZ，Phase 2A 可能已执行过')
else:
    print(f'  [WARN] 字段类型混合，请检查是否部分迁移已执行')
print()

# ========== Check 5: Alembic 配置 ==========
print('[Check 5] 检查 Alembic 配置...')
alembic_ini = 'D:/git/1108/AI_ad_spend02/backend/alembic.ini'
alembic_env = 'D:/git/1108/AI_ad_spend02/backend/alembic/env.py'

if os.path.exists(alembic_ini) and os.path.exists(alembic_env):
    print(f'  [PASS] Alembic 配置文件存在')
    print(f'     - alembic.ini')
    print(f'     - alembic/env.py')
else:
    print(f'  [FAIL] Alembic 配置文件缺失')
print()

# ========== Check 6: Phase 2A 迁移脚本 ==========
print('[Check 6] 检查 Phase 2A 迁移脚本...')
migration_files = [
    'D:/git/1108/AI_ad_spend02/backend/alembic/versions/20251118_phase2a_001_projects_timezone.py',
    'D:/git/1108/AI_ad_spend02/backend/alembic/versions/20251118_phase2a_002_topup_timezone.py',
    'D:/git/1108/AI_ad_spend02/backend/alembic/versions/20251118_phase2a_003_ledger_timezone.py',
]

all_exist = True
for file in migration_files:
    if os.path.exists(file):
        print(f'  [PASS] {os.path.basename(file)}')
    else:
        print(f'  [FAIL] {os.path.basename(file)} (缺失)')
        all_exist = False

if not all_exist:
    print(f'  [WARN] 部分迁移脚本缺失，请先生成脚本')
print()

# ========== Check 7: Gate 验证脚本 ==========
print('[Check 7] 检查 Gate 验证脚本...')
gate_script = 'D:/git/1108/AI_ad_spend02/backend/phase2a_gate_verification.sql'
if os.path.exists(gate_script):
    print(f'  [PASS] phase2a_gate_verification.sql 存在')
else:
    print(f'  [FAIL] Gate 验证脚本缺失')
print()

# ========== Check 8: 磁盘空间（简化） ==========
print('[Check 8] 检查工作目录可访问性...')
if os.path.exists('D:/git/1108/AI_ad_spend02/backend'):
    print(f'  [PASS] 工作目录可访问')
else:
    print(f'  [FAIL] 工作目录不存在')
print()

cursor.close()
conn.close()

# ========== 总结 ==========
print('=' * 70)
print('[SUCCESS] 执行前检查完成！')
print('=' * 70)
print()
print('下一步建议:')
print('1. 登录 Supabase Dashboard 创建数据库快照备份')
print('2. 确认当前数据库是 Dev 环境（非生产）')
print('3. 如果 Check 4 显示所有字段都是 TIMESTAMP，可以执行 Phase 2A')
print('4. 如果 Check 4 显示已经是 TIMESTAMPTZ，则 Phase 2A 已完成，跳过')
print()
