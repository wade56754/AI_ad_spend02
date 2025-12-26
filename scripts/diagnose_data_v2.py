#!/usr/bin/env python3
"""诊断 CEO 驾驶舱数据问题 v2 - 通过 ad_account_id 关联"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def run_diagnose():
    with engine.connect() as conn:
        # 诊断1: 通过 ad_accounts 关联查看项目级别数据
        print("=" * 80)
        print("诊断1: 各项目的日报数据 (通过 ad_accounts 关联)")
        print("=" * 80)
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
            print(f"project_id={row[0]}: {row[1]}")
            print(f"  日报数={row[2]}, 转化={row[3]}, raw_spend={row[4]:.2f}, real_spend={row[5]:.2f}")

        # 诊断2: ad_accounts 按项目分布
        print()
        print("=" * 80)
        print("诊断2: ad_accounts 按项目分布")
        print("=" * 80)
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
            print(f"project_id={row[0]}: {row[1]} - {row[2]} 个账户")

        # 诊断3: 检查日报中 ad_account_id 的分布
        print()
        print("=" * 80)
        print("诊断3: daily_reports 按 ad_account_id 汇总 (top 10)")
        print("=" * 80)
        result = conn.execute(text("""
            SELECT
                dr.ad_account_id,
                aa.name as account_name,
                aa.project_id,
                p.name as project_name,
                COUNT(*) as report_count,
                SUM(dr.conversions) as total_conversions,
                SUM(dr.raw_spend) as total_spend
            FROM daily_reports dr
            JOIN ad_accounts aa ON dr.ad_account_id = aa.id
            JOIN projects p ON aa.project_id = p.id
            GROUP BY dr.ad_account_id, aa.name, aa.project_id, p.name
            ORDER BY total_spend DESC
            LIMIT 10
        """))
        for row in result:
            print(f"ad_account_id={row[0]} ({row[1]})")
            print(f"  project_id={row[2]} ({row[3]}), 日报数={row[4]}, 转化={row[5]}, 消耗={row[6]:.2f}")

        # 诊断4: 检查 ledger_entries 是否存在
        print()
        print("=" * 80)
        print("诊断4: ledger_entries 表检查")
        print("=" * 80)
        try:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM ledger_entries
            """))
            count = result.scalar()
            print(f"  ledger_entries 记录数: {count}")

            if count > 0:
                result = conn.execute(text("""
                    SELECT entry_type, COUNT(*), SUM(amount)
                    FROM ledger_entries
                    GROUP BY entry_type
                """))
                for row in result:
                    print(f"    {row[0]}: {row[1]} 条, 总额={row[2]:.2f}")
        except Exception as e:
            print(f"  表不存在: {e}")

        # 诊断5: 检查收款相关字段
        print()
        print("=" * 80)
        print("诊断5: 收款数据来源检查")
        print("=" * 80)
        # 检查 daily_reports 中是否有 revenue 字段
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'daily_reports'
            AND column_name IN ('revenue', 'income', 'payment', 'amount')
        """))
        revenue_cols = [row[0] for row in result]
        print(f"  daily_reports 收款相关字段: {revenue_cols if revenue_cols else '无'}")

        # 检查是否有 payments/settlements 表
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('payments', 'settlements', 'invoices', 'receipts', 'revenues')
        """))
        payment_tables = [row[0] for row in result]
        print(f"  收款相关表: {payment_tables if payment_tables else '无'}")

        # 诊断6: 检查 topups 表（充值=收款来源？）
        print()
        print("=" * 80)
        print("诊断6: topups 表按项目汇总")
        print("=" * 80)
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
                print(f"project_id={row[0]}: {row[1]} - {row[2]} 次充值, 总额={row[3]:.2f}")
        except Exception as e:
            print(f"  查询失败: {e}")

        # 诊断7: 总体数据概览
        print()
        print("=" * 80)
        print("诊断7: 数据库总体概览")
        print("=" * 80)
        tables = ['projects', 'ad_accounts', 'daily_reports', 'topups', 'settlements']
        for table in tables:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"  {table}: {count} 条记录")
            except:
                print(f"  {table}: 表不存在")

if __name__ == "__main__":
    run_diagnose()
