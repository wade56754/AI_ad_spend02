#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse

# 加载环境变量
load_dotenv('D:/git/1108/AI_ad_spend02/.env')
db_url = os.getenv('DATABASE_URL')

output_file = 'migration_result.txt'

with open(output_file, 'w', encoding='utf-8') as f:
    f.write('=== Phase 2A Migration Check ===\n\n')

    if not db_url:
        f.write("[ERROR] DATABASE_URL not set\n")
        sys.exit(1)

    try:
        # 解析连接字符串
        parsed = urlparse(db_url)
        f.write(f'Database: {parsed.path[1:]}\n')
        f.write(f'Host: {parsed.hostname}\n\n')

        conn = psycopg2.connect(
            dbname=parsed.path[1:],
            user=parsed.username,
            password=parsed.password,
            host=parsed.hostname,
            port=parsed.port
        )
        cursor = conn.cursor()

        # 检查当前字段类型状态
        f.write('Current field status:\n')
        cursor.execute("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_name IN (
                'projects', 'project_members', 'project_expenses',
                'topup_requests', 'topup_transactions', 'topup_approval_logs',
                'ledger_entries'
            )
            AND column_name IN ('created_at', 'updated_at', 'occurred_at', 'joined_at', 'paid_at')
            ORDER BY table_name, column_name
        """)

        results = cursor.fetchall()
        tz_count = 0
        for table, column, dtype in results:
            is_tz = 'timestamp with time zone' in dtype
            if is_tz:
                tz_count += 1
            f.write(f'  {table}.{column}: {dtype} {"✅" if is_tz else "❌"}\n')

        f.write(f'\nFields with timezone: {tz_count}/14\n\n')

        # 如果没有完全迁移，执行迁移
        if tz_count < 14:
            f.write('=== Starting Migration ===\n\n')

            try:
                # projects 表
                f.write('[1/7] Migrating projects table...\n')
                cursor.execute("ALTER TABLE projects ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'")
                cursor.execute("ALTER TABLE projects ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC'")
                f.write('  ✅ projects: 2 fields\n')

                # project_members 表
                f.write('[2/7] Migrating project_members table...\n')
                cursor.execute("ALTER TABLE project_members ALTER COLUMN joined_at TYPE TIMESTAMPTZ USING joined_at AT TIME ZONE 'UTC'")
                f.write('  ✅ project_members: 1 field\n')

                # project_expenses 表
                f.write('[3/7] Migrating project_expenses table...\n')
                cursor.execute("ALTER TABLE project_expenses ALTER COLUMN occurred_at TYPE TIMESTAMPTZ USING occurred_at AT TIME ZONE 'UTC'")
                cursor.execute("ALTER TABLE project_expenses ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'")
                f.write('  ✅ project_expenses: 2 fields\n')

                # topup_requests 表
                f.write('[4/7] Migrating topup_requests table...\n')
                cursor.execute("ALTER TABLE topup_requests ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'")
                cursor.execute("ALTER TABLE topup_requests ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC'")
                f.write('  ✅ topup_requests: 2 fields\n')

                # topup_transactions 表
                f.write('[5/7] Migrating topup_transactions table...\n')
                cursor.execute("ALTER TABLE topup_transactions ALTER COLUMN paid_at TYPE TIMESTAMPTZ USING paid_at AT TIME ZONE 'UTC'")
                cursor.execute("ALTER TABLE topup_transactions ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'")
                f.write('  ✅ topup_transactions: 2 fields\n')

                # topup_approval_logs 表
                f.write('[6/7] Migrating topup_approval_logs table...\n')
                cursor.execute("ALTER TABLE topup_approval_logs ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'")
                f.write('  ✅ topup_approval_logs: 1 field\n')

                # ledger_entries 表
                f.write('[7/7] Migrating ledger_entries table...\n')
                cursor.execute("ALTER TABLE ledger_entries ALTER COLUMN occurred_at TYPE TIMESTAMPTZ USING occurred_at AT TIME ZONE 'UTC'")
                f.write('  ✅ ledger_entries: 1 field\n\n')

                # 提交事务
                conn.commit()
                f.write('✅ Migration committed successfully!\n\n')

                # 再次验证
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

                final_count = cursor.fetchone()[0]
                f.write(f'Final verification: {final_count}/14 fields migrated\n')

                if final_count == 14:
                    f.write('✅ Phase 2A COMPLETED SUCCESSFULLY!\n')
                else:
                    f.write('❌ Migration incomplete!\n')

            except Exception as e:
                conn.rollback()
                f.write(f'\n❌ Migration failed: {e}\n')
                f.write('Changes rolled back.\n')
                import traceback
                f.write(traceback.format_exc())

        else:
            f.write('✅ All fields already migrated to TIMESTAMPTZ\n')

        cursor.close()
        conn.close()

    except Exception as e:
        f.write(f'\n[ERROR] {e}\n')
        import traceback
        f.write(traceback.format_exc())

print('Migration check complete. See migration_result.txt for details.')
