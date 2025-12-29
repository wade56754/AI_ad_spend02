#!/usr/bin/env python3
"""诊断数据库表结构"""

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
        # 检查 daily_reports 表结构
        print("=" * 80)
        print("daily_reports 表结构")
        print("=" * 80)
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'daily_reports'
            ORDER BY ordinal_position
        """))
        for row in result:
            print(f"  {row[0]}: {row[1]} (nullable: {row[2]})")

        # 检查 projects 表结构
        print()
        print("=" * 80)
        print("projects 表结构")
        print("=" * 80)
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'projects'
            ORDER BY ordinal_position
        """))
        for row in result:
            print(f"  {row[0]}: {row[1]} (nullable: {row[2]})")

        # 检查 ad_accounts 表结构
        print()
        print("=" * 80)
        print("ad_accounts 表结构")
        print("=" * 80)
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'ad_accounts'
            ORDER BY ordinal_position
        """))
        for row in result:
            print(f"  {row[0]}: {row[1]} (nullable: {row[2]})")

        # 查看 daily_reports 样本数据
        print()
        print("=" * 80)
        print("daily_reports 样本数据 (前5行)")
        print("=" * 80)
        result = conn.execute(text("""
            SELECT * FROM daily_reports LIMIT 5
        """))
        columns = result.keys()
        print(f"  列: {list(columns)}")
        for i, row in enumerate(result):
            print(f"  行{i+1}: {dict(zip(columns, row))}")

        # 查看 projects 数据
        print()
        print("=" * 80)
        print("projects 全部数据")
        print("=" * 80)
        result = conn.execute(text("""
            SELECT * FROM projects
        """))
        columns = result.keys()
        print(f"  列: {list(columns)}")
        for row in result:
            print(f"  {dict(zip(columns, row))}")

        # 查看 ad_accounts 与 projects 的关联
        print()
        print("=" * 80)
        print("ad_accounts 按 project_id 分布")
        print("=" * 80)
        result = conn.execute(text("""
            SELECT project_id, COUNT(*) as count
            FROM ad_accounts
            GROUP BY project_id
            ORDER BY project_id
        """))
        for row in result:
            print(f"  project_id={row[0]}: {row[1]} 个账户")

if __name__ == "__main__":
    run_diagnose()
