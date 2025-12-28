#!/usr/bin/env python3
"""诊断 CEO 驾驶舱数据问题"""

import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)


def run_diagnostics():
    with engine.connect() as conn:
        print("=" * 80)
        print("CHECK 1: All projects")
        print("=" * 80)
        result = conn.execute(text("SELECT id, name, unit_price, status FROM projects ORDER BY id"))
        for row in result:
            name = row[1] if row[1] and str(row[1]).isascii() else f"[Project {row[0]}]"
            print(f"  id={row[0]}: {name}, unit_price={row[2]}, status={row[3]}")

        print()
        print("=" * 80)
        print("CHECK 2: Daily reports by project (via ad_accounts)")
        print("=" * 80)
        result = conn.execute(text("""
            SELECT
                aa.project_id,
                COUNT(DISTINCT dr.id) as report_count,
                COALESCE(SUM(dr.follows_count), 0) as total_follows,
                COALESCE(SUM(dr.raw_spend), 0) as total_spend
            FROM daily_reports dr
            JOIN ad_accounts aa ON dr.ad_account_id = aa.id
            GROUP BY aa.project_id
            ORDER BY aa.project_id
        """))
        for row in result:
            print(f"  project_id={row[0]}: reports={row[1]}, follows={row[2]}, spend=${row[3]:,.2f}")

        print()
        print("=" * 80)
        print("CHECK 3: Check if ad_spend_daily table exists")
        print("=" * 80)
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name LIKE '%spend%'
        """))
        tables = [row[0] for row in result]
        if tables:
            print(f"  Tables with 'spend': {tables}")
        else:
            print("  No tables with 'spend' found")

        print()
        print("=" * 80)
        print("CHECK 4: Projects with billing type / price rules")
        print("=" * 80)
        result = conn.execute(text("SELECT id, name, unit_price, price_rules FROM projects ORDER BY id"))
        for row in result:
            name = row[1] if row[1] and str(row[1]).isascii() else f"[Project {row[0]}]"
            print(f"  id={row[0]}: {name}, unit_price={row[2]}, price_rules={row[3]}")

        print()
        print("=" * 80)
        print("CHECK 5: Profit calculation verification")
        print("=" * 80)
        result = conn.execute(text("""
            SELECT
                aa.project_id,
                p.name,
                p.unit_price,
                COUNT(DISTINCT dr.id) as report_count,
                COALESCE(SUM(dr.follows_count), 0) as total_follows,
                COALESCE(SUM(dr.raw_spend), 0) as total_spend
            FROM daily_reports dr
            JOIN ad_accounts aa ON dr.ad_account_id = aa.id
            JOIN projects p ON aa.project_id = p.id
            GROUP BY aa.project_id, p.name, p.unit_price
            ORDER BY total_spend DESC
        """))

        for row in result:
            project_id = row[0]
            name = row[1] if row[1] and str(row[1]).isascii() else f"[Project {project_id}]"
            unit_price = float(row[2]) if row[2] else 0
            reports = row[3]
            follows = int(row[4])
            spend = float(row[5])

            revenue = follows * unit_price
            profit = revenue - spend
            profit_rate = (profit / revenue * 100) if revenue > 0 else None

            print(f"\n  Project {project_id} ({name}):")
            print(f"    Reports: {reports:,}")
            print(f"    Follows: {follows:,}")
            print(f"    Unit Price: ${unit_price:.2f}")
            print(f"    Spend: ${spend:,.2f}")
            print(f"    Revenue: ${revenue:,.2f}")
            print(f"    Profit: ${profit:,.2f}")
            if profit_rate is not None:
                print(f"    Profit Rate: {profit_rate:.1f}%")
            else:
                print(f"    Profit Rate: -- (no revenue)")


if __name__ == "__main__":
    run_diagnostics()
