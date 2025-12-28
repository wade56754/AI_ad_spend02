#!/usr/bin/env python3
"""诊断 CEO 驾驶舱数据问题 v3 - 修复编码"""

import os
import sys

# 设置输出编码
sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def safe_print(msg):
    """安全打印，处理编码问题"""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'replace').decode('ascii'))

def run_diagnose():
    with engine.connect() as conn:
        # 诊断1: 通过 ad_accounts 关联查看项目级别数据
        safe_print("=" * 80)
        safe_print("DIAG 1: Project-level daily report data (via ad_accounts)")
        safe_print("=" * 80)
        result = conn.execute(text("""
            SELECT
                p.id as project_id,
                p.name as project_name,
                COUNT(DISTINCT dr.id) as daily_report_count,
                COALESCE(SUM(dr.conversions), 0) as total_conversions,
                COALESCE(SUM(dr.raw_spend), 0) as total_raw_spend,
                COALESCE(SUM(dr.real_spend), 0) as total_real_spend
            FROM projects p
            LEFT JOIN ad_accounts aa ON p.id = aa.project_id
            LEFT JOIN daily_reports dr ON aa.id = dr.ad_account_id
            GROUP BY p.id, p.name
            ORDER BY p.id
        """))
        for row in result:
            name = row[1] if row[1].isascii() else f"[Project {row[0]}]"
            safe_print(f"project_id={row[0]}: {name}")
            safe_print(f"  reports={row[2]}, conversions={row[3]}, raw_spend={row[4]:.2f}, real_spend={row[5]:.2f}")

        # 诊断2: ad_accounts 按项目分布
        safe_print("")
        safe_print("=" * 80)
        safe_print("DIAG 2: ad_accounts distribution by project")
        safe_print("=" * 80)
        result = conn.execute(text("""
            SELECT
                p.id as project_id,
                p.name as project_name,
                COUNT(aa.id) as account_count
            FROM projects p
            LEFT JOIN ad_accounts aa ON p.id = aa.project_id
            GROUP BY p.id, p.name
            ORDER BY p.id
        """))
        for row in result:
            name = row[1] if row[1].isascii() else f"[Project {row[0]}]"
            safe_print(f"project_id={row[0]}: {name} - {row[2]} accounts")

        # 诊断3: 检查 ledger_entries
        safe_print("")
        safe_print("=" * 80)
        safe_print("DIAG 3: ledger_entries check")
        safe_print("=" * 80)
        try:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM ledger_entries
            """))
            count = result.scalar()
            safe_print(f"  ledger_entries count: {count}")

            if count > 0:
                result = conn.execute(text("""
                    SELECT entry_type, COUNT(*), SUM(amount)
                    FROM ledger_entries
                    GROUP BY entry_type
                """))
                for row in result:
                    safe_print(f"    {row[0]}: {row[1]} entries, total={row[2]:.2f}")
        except Exception as e:
            safe_print(f"  Table not exist: {e}")

        # 诊断4: topups 按项目汇总
        safe_print("")
        safe_print("=" * 80)
        safe_print("DIAG 4: topups by project")
        safe_print("=" * 80)
        try:
            result = conn.execute(text("""
                SELECT
                    p.id as project_id,
                    p.name as project_name,
                    COUNT(t.id) as topup_count,
                    COALESCE(SUM(t.amount), 0) as total_amount
                FROM projects p
                LEFT JOIN ad_accounts aa ON p.id = aa.project_id
                LEFT JOIN topups t ON aa.id = t.ad_account_id
                GROUP BY p.id, p.name
                ORDER BY p.id
            """))
            for row in result:
                name = row[1] if row[1].isascii() else f"[Project {row[0]}]"
                safe_print(f"project_id={row[0]}: {name} - {row[2]} topups, amount={row[3]:.2f}")
        except Exception as e:
            safe_print(f"  Query failed: {e}")

        # 诊断5: settlements 按项目汇总
        safe_print("")
        safe_print("=" * 80)
        safe_print("DIAG 5: settlements by project")
        safe_print("=" * 80)
        try:
            result = conn.execute(text("""
                SELECT
                    p.id as project_id,
                    p.name as project_name,
                    COUNT(s.id) as settlement_count,
                    COALESCE(SUM(s.settlement_amount), 0) as total_amount
                FROM projects p
                LEFT JOIN settlements s ON p.id = s.project_id
                GROUP BY p.id, p.name
                ORDER BY p.id
            """))
            for row in result:
                name = row[1] if row[1].isascii() else f"[Project {row[0]}]"
                safe_print(f"project_id={row[0]}: {name} - {row[2]} settlements, amount={row[3]:.2f}")
        except Exception as e:
            safe_print(f"  Query failed: {e}")

        # 诊断6: 检查收款数据来源
        safe_print("")
        safe_print("=" * 80)
        safe_print("DIAG 6: Check revenue/payment tables")
        safe_print("=" * 80)
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result]
        safe_print(f"  All tables ({len(tables)}): {tables}")

        # 诊断7: 检查 conversions 字段的数据
        safe_print("")
        safe_print("=" * 80)
        safe_print("DIAG 7: Check conversions field in daily_reports")
        safe_print("=" * 80)
        result = conn.execute(text("""
            SELECT
                SUM(conversions) as total_conversions,
                SUM(conversions_raw) as total_conversions_raw,
                SUM(conversions_final) as total_conversions_final,
                SUM(result_count) as total_result_count
            FROM daily_reports
        """))
        row = result.fetchone()
        safe_print(f"  conversions: {row[0]}")
        safe_print(f"  conversions_raw: {row[1]}")
        safe_print(f"  conversions_final: {row[2]}")
        safe_print(f"  result_count: {row[3]}")

        # 诊断8: 数据库总体概览
        safe_print("")
        safe_print("=" * 80)
        safe_print("DIAG 8: Database overview")
        safe_print("=" * 80)
        table_list = ['projects', 'ad_accounts', 'daily_reports', 'topups', 'settlements', 'ledger_entries']
        for table in table_list:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                safe_print(f"  {table}: {count} records")
            except:
                safe_print(f"  {table}: table not exist")

if __name__ == "__main__":
    run_diagnose()
