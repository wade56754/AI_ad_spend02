#!/usr/bin/env python3
"""检查转化数据字段"""

import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def run_check():
    with engine.connect() as conn:
        print("=" * 80)
        print("CHECK 1: Conversion field totals")
        print("=" * 80)
        result = conn.execute(text("""
            SELECT
                SUM(conversions) as conversions,
                SUM(conversions_raw) as conversions_raw,
                SUM(conversions_final) as conversions_final,
                SUM(result_count) as result_count,
                SUM(follows_count) as follows_count,
                SUM(new_follows) as new_follows
            FROM daily_reports
        """))
        row = result.fetchone()
        print(f"  conversions: {row[0]}")
        print(f"  conversions_raw: {row[1]}")
        print(f"  conversions_final: {row[2]}")
        print(f"  result_count: {row[3]}")
        print(f"  follows_count: {row[4]}")
        print(f"  new_follows: {row[5]}")

        print()
        print("=" * 80)
        print("CHECK 2: Spend field totals")
        print("=" * 80)
        result = conn.execute(text("""
            SELECT
                SUM(raw_spend) as raw_spend,
                SUM(real_spend) as real_spend
            FROM daily_reports
        """))
        row = result.fetchone()
        print(f"  raw_spend: {row[0]:.2f}")
        print(f"  real_spend: {row[1]:.2f}")

        print()
        print("=" * 80)
        print("CHECK 3: Conversion by project (via ad_accounts)")
        print("=" * 80)
        result = conn.execute(text("""
            SELECT
                aa.project_id,
                SUM(dr.result_count) as result_count,
                SUM(dr.follows_count) as follows_count,
                SUM(dr.raw_spend) as raw_spend
            FROM daily_reports dr
            JOIN ad_accounts aa ON dr.ad_account_id = aa.id
            GROUP BY aa.project_id
            ORDER BY aa.project_id
        """))
        for row in result:
            print(f"project_id={row[0]}: result_count={row[1]}, follows_count={row[2]}, raw_spend={row[3]:.2f}")

        print()
        print("=" * 80)
        print("CHECK 4: Sample data with conversions > 0")
        print("=" * 80)
        result = conn.execute(text("""
            SELECT id, report_date, ad_account_id,
                   conversions, conversions_raw, conversions_final,
                   result_count, follows_count, raw_spend
            FROM daily_reports
            WHERE result_count > 0 OR follows_count > 0
            LIMIT 5
        """))
        for row in result:
            print(f"id={row[0]}, date={row[1]}, account={row[2]}")
            print(f"  conversions={row[3]}, raw={row[4]}, final={row[5]}")
            print(f"  result_count={row[6]}, follows={row[7]}, spend={row[8]:.2f}")

        print()
        print("=" * 80)
        print("CHECK 5: Projects table")
        print("=" * 80)
        result = conn.execute(text("""
            SELECT id, name, unit_price, status
            FROM projects
            ORDER BY id
        """))
        for row in result:
            name = row[1] if row[1] and row[1].isascii() else f"[Project {row[0]}]"
            print(f"id={row[0]}: {name}, unit_price={row[2]}, status={row[3]}")

if __name__ == "__main__":
    run_check()
