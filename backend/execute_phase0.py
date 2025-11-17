#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 0 执行脚本
清理废弃表并创建符合 DATA_SCHEMA v5.0 的新表
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse

# 加载环境变量
load_dotenv('C:/Users/Administrator/.env')
db_url = os.getenv('DATABASE_URL')

if not db_url:
    print("[ERROR] DATABASE_URL 未设置！请检查 .env 文件")
    sys.exit(1)

# 解析连接字符串
parsed = urlparse(db_url)
dbname = parsed.path[1:]
user = parsed.username
password = parsed.password
host = parsed.hostname
port = parsed.port

print('=' * 70)
print('Phase 0: 清理废弃表并创建新表')
print('=' * 70)
print(f'数据库: {dbname}')
print(f'主机: {host}')
print(f'端口: {port}')
print()

# 用户确认
print('警告: 此操作将删除废弃表并创建新表！')
print()
print('确认以下条件:')
print('1. 已通过 Supabase Dashboard 创建数据库快照（或已确认可以跳过）')
print('2. DATABASE_URL 指向 Dev 环境（不是生产库）')
print('3. 废弃表（topups, ledgers）为空表')
print()

confirm = input('是否继续执行 Phase 0？(yes/no): ')
if confirm.lower() != 'yes':
    print('[CANCELLED] 用户取消执行')
    sys.exit(0)

print()
print('开始执行 Phase 0...')
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
    # ========== Step 1: DROP 废弃表 ==========
    print('[Step 1/6] Dropping deprecated tables...')
    cursor.execute('DROP TABLE IF EXISTS topups CASCADE;')
    cursor.execute('DROP TABLE IF EXISTS ledgers CASCADE;')
    print('  [OK] Dropped: topups, ledgers')
    print()

    # ========== Step 2: CREATE topup_requests ==========
    print('[Step 2/6] Creating topup_requests table...')
    cursor.execute('''
        CREATE TABLE topup_requests (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            request_no VARCHAR(50) UNIQUE NOT NULL,
            project_id UUID NOT NULL REFERENCES projects(id),
            ad_account_id UUID REFERENCES ad_accounts(id),
            applicant_id UUID NOT NULL REFERENCES user_profiles(id),
            amount NUMERIC(15,2) NOT NULL,
            currency VARCHAR(10) NOT NULL DEFAULT 'CNY',
            urgency_level VARCHAR(20) NOT NULL DEFAULT 'normal',
            status VARCHAR(20) NOT NULL,
            status_reason TEXT,
            expected_pay_date DATE,
            voucher_url TEXT,
            notes TEXT,
            created_by UUID REFERENCES user_profiles(id),
            updated_by UUID REFERENCES user_profiles(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    ''')
    cursor.execute('CREATE INDEX idx_topup_requests_project ON topup_requests(project_id);')
    cursor.execute('CREATE INDEX idx_topup_requests_status ON topup_requests(status);')
    cursor.execute('CREATE INDEX idx_topup_requests_applicant ON topup_requests(applicant_id);')
    print('  [OK] Created: topup_requests + 3 indexes')
    print()

    # ========== Step 3: CREATE topup_transactions ==========
    print('[Step 3/6] Creating topup_transactions table...')
    cursor.execute('''
        CREATE TABLE topup_transactions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            topup_request_id UUID NOT NULL REFERENCES topup_requests(id),
            paid_amount NUMERIC(15,2) NOT NULL,
            paid_currency VARCHAR(10) NOT NULL,
            payment_method VARCHAR(50) NOT NULL,
            payment_reference VARCHAR(100),
            paid_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            receipt_url TEXT,
            notes TEXT,
            created_by UUID REFERENCES user_profiles(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    ''')
    cursor.execute('CREATE INDEX idx_topup_transactions_request ON topup_transactions(topup_request_id);')
    cursor.execute('CREATE INDEX idx_topup_transactions_paid_at ON topup_transactions(paid_at);')
    print('  [OK] Created: topup_transactions + 2 indexes')
    print()

    # ========== Step 4: CREATE topup_approval_logs ==========
    print('[Step 4/6] Creating topup_approval_logs table...')
    cursor.execute('''
        CREATE TABLE topup_approval_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            topup_request_id UUID NOT NULL REFERENCES topup_requests(id),
            action VARCHAR(50) NOT NULL,
            from_status VARCHAR(20),
            to_status VARCHAR(20),
            operator_id UUID NOT NULL REFERENCES user_profiles(id),
            comments TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    ''')
    cursor.execute('CREATE INDEX idx_topup_approval_logs_request ON topup_approval_logs(topup_request_id);')
    cursor.execute('CREATE INDEX idx_topup_approval_logs_action ON topup_approval_logs(action);')
    cursor.execute('CREATE INDEX idx_topup_approval_logs_operator ON topup_approval_logs(operator_id);')
    print('  [OK] Created: topup_approval_logs + 3 indexes')
    print()

    # ========== Step 5: CREATE ledger_entries ==========
    print('[Step 5/6] Creating ledger_entries table...')
    cursor.execute('''
        CREATE TABLE ledger_entries (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id UUID NOT NULL REFERENCES projects(id),
            ad_account_id UUID REFERENCES ad_accounts(id),
            entry_type VARCHAR(20) NOT NULL,
            amount NUMERIC(15,2) NOT NULL,
            currency VARCHAR(10) NOT NULL,
            reference_id UUID,
            occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by UUID REFERENCES user_profiles(id),
            notes TEXT
        );
    ''')
    cursor.execute('CREATE INDEX idx_ledger_project ON ledger_entries(project_id);')
    cursor.execute('CREATE INDEX idx_ledger_account ON ledger_entries(ad_account_id);')
    cursor.execute('CREATE INDEX idx_ledger_entry_type ON ledger_entries(entry_type);')
    print('  [OK] Created: ledger_entries + 3 indexes')
    print()

    # ========== Step 6: 初始化 Alembic 版本控制 ==========
    print('[Step 6/6] Initializing Alembic version control...')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alembic_version (
            version_num VARCHAR(32) NOT NULL PRIMARY KEY
        );
    ''')
    cursor.execute("""
        INSERT INTO alembic_version (version_num) VALUES ('20251118_phase0')
        ON CONFLICT (version_num) DO NOTHING;
    """)
    print('  [OK] Alembic version: 20251118_phase0')
    print()

    # 提交事务
    conn.commit()

    print('=' * 70)
    print('[SUCCESS] Phase 0 执行成功！')
    print('=' * 70)
    print()
    print('已完成:')
    print('  - Dropped: 2 tables (topups, ledgers)')
    print('  - Created: 4 tables (topup_requests, topup_transactions, topup_approval_logs, ledger_entries)')
    print('  - Created: 11 indexes')
    print('  - Initialized: Alembic version control')
    print()
    print('下一步:')
    print('1. 执行 Gate 验证脚本')
    print('2. 检查应用日志')
    print('3. 进入观察期（1 天）')
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
