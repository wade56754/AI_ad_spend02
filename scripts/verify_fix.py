#!/usr/bin/env python3
"""验证 CEO 驾驶舱数据修复结果"""

import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def verify():
    with engine.connect() as conn:
        print("=" * 80)
        print("VERIFICATION: Data fix result")
        print("=" * 80)

        result = conn.execute(text("""
            SELECT
                aa.project_id,
                COUNT(DISTINCT dr.id) as daily_report_count,
                SUM(dr.follows_count) as total_follows,
                SUM(dr.raw_spend) as total_spend
            FROM daily_reports dr
            JOIN ad_accounts aa ON dr.ad_account_id = aa.id
            GROUP BY aa.project_id
            ORDER BY total_spend DESC
        """))

        print("\nProject data distribution:")
        for row in result:
            spend = float(row[3]) if row[3] else 0
            follows = int(row[2]) if row[2] else 0
            reports = int(row[1]) if row[1] else 0

            # 计算利润
            unit_price = 24.77
            revenue = follows * unit_price
            profit = revenue - spend
            profit_rate = (profit / revenue * 100) if revenue > 0 else None

            print(f"\n  Project {row[0]}:")
            print(f"    Reports: {reports:,}")
            print(f"    Follows: {follows:,}")
            print(f"    Spend: ${spend:,.2f}")
            print(f"    Revenue: ${revenue:,.2f}")
            print(f"    Profit: ${profit:,.2f}")
            print(f"    Profit Rate: {profit_rate:.1f}%" if profit_rate else "    Profit Rate: --")

        print("\n" + "=" * 80)
        print("Expected result for Project 7:")
        print("  - Reports: ~8,176")
        print("  - Follows: ~758,374")
        print("  - Spend: ~$6,280,162.91")
        print("  - Revenue: ~$18,784,923.98")
        print("  - Profit: ~$12,504,761.07")
        print("  - Profit Rate: ~66.6%")
        print("=" * 80)

if __name__ == "__main__":
    verify()
