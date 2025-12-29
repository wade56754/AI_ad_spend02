#!/usr/bin/env python3
"""
修复 CEO 驾驶舱数据问题 - 合并项目数据

问题诊断:
- Project 7: 有消耗(628万), follows_count=378,120
- Project 12: 无消耗, follows_count=380,254

修复方案:
1. 将 Project 12 的 ad_accounts 合并到 Project 7
2. 删除空的 Project 12

执行前请确认: 数据库已备份!
"""

import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# 配置
SOURCE_PROJECT_ID = 12  # 要合并的项目 (无消耗的)
TARGET_PROJECT_ID = 7   # 目标项目 (有消耗的)


def preview_fix():
    """预览修复操作"""
    print("=" * 80)
    print("FIX PREVIEW: Merge ad_accounts from Project 12 to Project 7")
    print("=" * 80)

    with engine.connect() as conn:
        # 检查当前状态
        print("\n[BEFORE] Current state:")

        result = conn.execute(text(f"""
            SELECT
                aa.project_id,
                COUNT(aa.id) as account_count,
                COUNT(DISTINCT dr.id) as report_count,
                COALESCE(SUM(dr.follows_count), 0) as total_follows,
                COALESCE(SUM(dr.raw_spend), 0) as total_spend
            FROM ad_accounts aa
            LEFT JOIN daily_reports dr ON aa.id = dr.ad_account_id
            WHERE aa.project_id IN ({SOURCE_PROJECT_ID}, {TARGET_PROJECT_ID})
            GROUP BY aa.project_id
            ORDER BY aa.project_id
        """))

        for row in result:
            print(f"  Project {row[0]}: {row[1]} accounts, {row[2]} reports, "
                  f"follows={row[3]}, spend={row[4]:.2f}")

        # 检查 ad_accounts 详情
        print(f"\n[INFO] Accounts to move from Project {SOURCE_PROJECT_ID} to Project {TARGET_PROJECT_ID}:")
        result = conn.execute(text(f"""
            SELECT id, name, account_code
            FROM ad_accounts
            WHERE project_id = {SOURCE_PROJECT_ID}
            LIMIT 10
        """))
        for row in result:
            name = row[1] if row[1] and row[1].isascii() else f"Account {row[0]}"
            print(f"  - id={row[0]}, name={name}, code={row[2]}")

        # 计算合并后的预期值
        result = conn.execute(text(f"""
            SELECT
                COUNT(DISTINCT aa.id) as account_count,
                COUNT(DISTINCT dr.id) as report_count,
                COALESCE(SUM(dr.follows_count), 0) as total_follows,
                COALESCE(SUM(dr.raw_spend), 0) as total_spend
            FROM ad_accounts aa
            LEFT JOIN daily_reports dr ON aa.id = dr.ad_account_id
            WHERE aa.project_id IN ({SOURCE_PROJECT_ID}, {TARGET_PROJECT_ID})
        """))

        row = result.fetchone()
        print(f"\n[AFTER] Expected state for Project {TARGET_PROJECT_ID}:")
        print(f"  {row[0]} accounts, {row[1]} reports, follows={row[2]}, spend={row[3]:.2f}")

        # 计算预期收入和利润
        unit_price = 24.77
        revenue = float(row[2]) * unit_price
        cost = float(row[3])
        profit = revenue - cost
        profit_rate = (profit / revenue * 100) if revenue > 0 else 0

        print(f"\n[PROFIT] Expected profit calculation:")
        print(f"  Revenue = {row[2]} follows x ${unit_price} = ${revenue:,.2f}")
        print(f"  Cost = ${cost:,.2f}")
        print(f"  Profit = ${profit:,.2f}")
        print(f"  Profit Rate = {profit_rate:.1f}%")


def execute_fix(dry_run=True):
    """执行修复"""
    if dry_run:
        print("\n" + "=" * 80)
        print("DRY RUN MODE - No changes will be made")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("EXECUTING FIX - Changes will be committed!")
        print("=" * 80)

    with engine.begin() as conn:
        # Step 1: 更新 ad_accounts 的 project_id
        if not dry_run:
            result = conn.execute(text(f"""
                UPDATE ad_accounts
                SET project_id = {TARGET_PROJECT_ID}
                WHERE project_id = {SOURCE_PROJECT_ID}
            """))
            print(f"[STEP 1] Updated {result.rowcount} ad_accounts from Project {SOURCE_PROJECT_ID} to Project {TARGET_PROJECT_ID}")
        else:
            result = conn.execute(text(f"""
                SELECT COUNT(*) FROM ad_accounts WHERE project_id = {SOURCE_PROJECT_ID}
            """))
            count = result.scalar()
            print(f"[STEP 1] Would update {count} ad_accounts from Project {SOURCE_PROJECT_ID} to Project {TARGET_PROJECT_ID}")

        # Step 2: 验证结果
        result = conn.execute(text(f"""
            SELECT
                aa.project_id,
                COUNT(aa.id) as account_count,
                COUNT(DISTINCT dr.id) as report_count,
                COALESCE(SUM(dr.follows_count), 0) as total_follows,
                COALESCE(SUM(dr.raw_spend), 0) as total_spend
            FROM ad_accounts aa
            LEFT JOIN daily_reports dr ON aa.id = dr.ad_account_id
            WHERE aa.project_id IN ({SOURCE_PROJECT_ID}, {TARGET_PROJECT_ID})
            GROUP BY aa.project_id
            ORDER BY aa.project_id
        """))

        print("\n[RESULT] After fix:")
        for row in result:
            print(f"  Project {row[0]}: {row[1]} accounts, {row[2]} reports, "
                  f"follows={row[3]}, spend={row[4]:.2f}")

        if dry_run:
            print("\n[INFO] Run with --execute to apply changes")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fix CEO Dashboard data issue")
    parser.add_argument("--execute", action="store_true", help="Execute the fix (default: dry-run)")
    args = parser.parse_args()

    preview_fix()
    execute_fix(dry_run=not args.execute)
