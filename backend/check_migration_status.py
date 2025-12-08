#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse

# 加载环境变量
load_dotenv('D:/git/1108/AI_ad_spend02/.env')
db_url = os.getenv('DATABASE_URL')

if not db_url:
    sys.stderr.write("[ERROR] DATABASE_URL not set\n")
    sys.exit(1)

try:
    # 解析连接字符串
    parsed = urlparse(db_url)
    conn = psycopg2.connect(
        dbname=parsed.path[1:],
        user=parsed.username,
        password=parsed.password,
        host=parsed.hostname,
        port=parsed.port
    )
    cursor = conn.cursor()

    # 检查字段类型
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.columns
        WHERE table_name IN (
            'projects', 'project_members', 'project_expenses',
            'topup_requests', 'topup_transactions', 'topup_approval_logs',
            'ledger_entries'
        )
        AND column_name IN ('created_at', 'updated_at', 'occurred_at', 'joined_at', 'paid_at')
        AND data_type = 'timestamp with time zone'
    """)

    migrated_count = cursor.fetchone()[0]
    sys.stdout.write(f"MIGRATED_FIELDS:{migrated_count}\n")
    sys.stdout.flush()

    cursor.close()
    conn.close()

except Exception as e:
    sys.stderr.write(f"ERROR:{str(e)}\n")
    sys.exit(1)
