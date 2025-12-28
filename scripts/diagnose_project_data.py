#!/usr/bin/env python3
"""诊断 CEO 驾驶舱数据问题 - 检查项目数据分布"""

import os
import sys

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)


def run_diagnose():
    with engine.connect() as conn:
        # 诊断1: 项目级别的日报数据分布
        print("=" * 80)
        print("诊断1: 各项目的日报数据分布")
        print("=" * 80)
        result = conn.execute(
            text(
                """
            SELECT
                p.id as project_id,
                p.name as project_name,
                COUNT(DISTINCT dr.id) as daily_report_count,
                COALESCE(SUM(dr.conversions), 0) as total_conversions,
                COALESCE(SUM(dr.revenue), 0) as total_revenue,
                COALESCE(SUM(dr.spend), 0) as total_spend
            FROM projects p
            LEFT JOIN daily_reports dr ON p.id = dr.project_id
            GROUP BY p.id, p.name
            ORDER BY p.id
        """
            )
        )
        for row in result:
            print(f"项目ID={row[0]}, 名称={row[1]}")
            print(
                f"  日报数={row[2]}, 转化={row[3]:.0f}, 收款={row[4]:.2f}, 消耗={row[5]:.2f}"
            )

        # 诊断2: 检查消耗相关表
        print()
        print("=" * 80)
        print("诊断2: 检查消耗相关表")
        print("=" * 80)
        result = conn.execute(
            text(
                """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND (table_name LIKE '%spend%' OR table_name LIKE '%account%' OR table_name LIKE '%ledger%')
            ORDER BY table_name
        """
            )
        )
        tables = [row[0] for row in result]
        for t in tables:
            print(f"  表: {t}")

        # 诊断3: ad_accounts 的项目分布
        print()
        print("=" * 80)
        print("诊断3: ad_accounts 的项目分布")
        print("=" * 80)
        result = conn.execute(
            text(
                """
            SELECT
                p.id as project_id,
                p.name as project_name,
                COUNT(aa.id) as account_count,
                COALESCE(SUM(aa.balance), 0) as total_balance
            FROM projects p
            LEFT JOIN ad_accounts aa ON p.id = aa.project_id
            GROUP BY p.id, p.name
            ORDER BY p.id
        """
            )
        )
        for row in result:
            print(
                f"项目ID={row[0]}, 名称={row[1]}, 账户数={row[2]}, 总余额={row[3]:.2f}"
            )

        # 诊断4: 日报中的 project_id 分布（不通过 join）
        print()
        print("=" * 80)
        print("诊断4: daily_reports 表中的 project_id 分布")
        print("=" * 80)
        result = conn.execute(
            text(
                """
            SELECT
                project_id,
                COUNT(*) as count,
                SUM(conversions) as total_conversions,
                SUM(spend) as total_spend,
                SUM(revenue) as total_revenue
            FROM daily_reports
            GROUP BY project_id
            ORDER BY project_id
        """
            )
        )
        for row in result:
            print(
                f"project_id={row[0]}: 日报数={row[1]}, 转化={row[2]:.0f}, 消耗={row[3]:.2f}, 收款={row[4]:.2f}"
            )

        # 诊断5: 检查 ledger_entries 表
        print()
        print("=" * 80)
        print("诊断5: ledger_entries 按项目汇总")
        print("=" * 80)
        try:
            result = conn.execute(
                text(
                    """
                SELECT
                    p.id as project_id,
                    p.name as project_name,
                    le.entry_type,
                    COUNT(*) as count,
                    SUM(le.amount) as total_amount
                FROM ledger_entries le
                JOIN projects p ON le.project_id = p.id
                GROUP BY p.id, p.name, le.entry_type
                ORDER BY p.id, le.entry_type
            """
                )
            )
            for row in result:
                print(
                    f"项目ID={row[0]} ({row[1]}), 类型={row[2]}, 数量={row[3]}, 总额={row[4]:.2f}"
                )
        except Exception as e:
            print(f"  表不存在或查询失败: {e}")

        # 诊断6: 项目表详情
        print()
        print("=" * 80)
        print("诊断6: 项目表详情")
        print("=" * 80)
        result = conn.execute(
            text(
                """
            SELECT id, name, status, created_at
            FROM projects
            ORDER BY id
        """
            )
        )
        for row in result:
            print(f"ID={row[0]}, 名称={row[1]}, 状态={row[2]}, 创建时间={row[3]}")


if __name__ == "__main__":
    run_diagnose()
