#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ORM 模型与数据库 Schema 同步验证脚本

验证目的：
  防止 LedgerEntry.balance_after 类问题（ORM 定义了数据库中不存在的列）

验证内容：
  1. ORM 模型列 vs 数据库实际列 对比
  2. 列出 ORM 独有列（会导致 INSERT/SELECT 失败）
  3. 列出 DB 独有列（可能是遗漏的模型字段）

使用方法：
  python backend/scripts/check_schema.py

环境变量：
  DATABASE_URL - 数据库连接字符串（自动从 .env 加载）

退出码：
  0 - 完全匹配
  1 - 存在不匹配（ORM 有 DB 没有的列 = 严重错误）
  2 - 存在警告（DB 有 ORM 没有的列 = 可能是遗漏）
"""

import sys
import os
from pathlib import Path
from typing import Dict, Set, List, Tuple
from collections import defaultdict

# 添加项目根目录到路径
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(ROOT_DIR / '.env')

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

# 导入所有模型以确保 Base.metadata 完整
from backend.models import Base


def get_orm_columns() -> Dict[str, Set[str]]:
    """获取 ORM 模型定义的所有表和列"""
    orm_tables = {}

    for table_name, table in Base.metadata.tables.items():
        columns = set()
        for col in table.columns:
            columns.add(col.name)
        orm_tables[table_name] = columns

    return orm_tables


def get_db_columns(engine) -> Dict[str, Set[str]]:
    """从实际数据库获取所有表和列"""
    db_tables = {}

    inspector = inspect(engine)

    for table_name in inspector.get_table_names():
        columns = set()
        for col in inspector.get_columns(table_name):
            columns.add(col['name'])
        db_tables[table_name] = columns

    return db_tables


def compare_schemas(orm_tables: Dict[str, Set[str]],
                   db_tables: Dict[str, Set[str]]) -> Tuple[List, List, List]:
    """
    对比 ORM 与数据库 Schema

    Returns:
        (errors, warnings, infos)
        - errors: ORM 有但 DB 没有的列（会导致运行时错误）
        - warnings: DB 有但 ORM 没有的列（可能遗漏）
        - infos: ORM 有但 DB 没有的表（可能未迁移）
    """
    errors = []    # P0: ORM 列在 DB 中不存在 -> INSERT 会失败
    warnings = []  # P1: DB 列在 ORM 中未定义 -> 可能遗漏
    infos = []     # P2: 表级别差异

    # 所有 ORM 表名
    orm_table_names = set(orm_tables.keys())
    db_table_names = set(db_tables.keys())

    # ORM 定义了但 DB 没有的表
    orm_only_tables = orm_table_names - db_table_names
    for table in orm_only_tables:
        infos.append({
            'type': 'table_not_in_db',
            'table': table,
            'message': f"Table '{table}' defined in ORM but not in database (may need migration)"
        })

    # DB 有但 ORM 没有的表
    db_only_tables = db_table_names - orm_table_names
    for table in db_only_tables:
        # 跳过系统表
        if table.startswith('_') or table in ('alembic_version', 'spatial_ref_sys'):
            continue
        infos.append({
            'type': 'table_not_in_orm',
            'table': table,
            'message': f"Table '{table}' exists in database but not defined in ORM"
        })

    # 共同表的列对比
    common_tables = orm_table_names & db_table_names

    for table in common_tables:
        orm_cols = orm_tables[table]
        db_cols = db_tables[table]

        # ORM 有但 DB 没有 -> 严重错误！
        orm_only = orm_cols - db_cols
        for col in orm_only:
            errors.append({
                'type': 'column_not_in_db',
                'table': table,
                'column': col,
                'message': f"Column '{table}.{col}' defined in ORM but not in database"
            })

        # DB 有但 ORM 没有 -> 警告
        db_only = db_cols - orm_cols
        for col in db_only:
            warnings.append({
                'type': 'column_not_in_orm',
                'table': table,
                'column': col,
                'message': f"Column '{table}.{col}' exists in database but not defined in ORM"
            })

    return errors, warnings, infos


def print_report(errors: List, warnings: List, infos: List) -> int:
    """打印验证报告并返回退出码"""
    print("=" * 80)
    print("ORM vs Database Schema Validation Report")
    print("=" * 80)

    # 错误（ORM 列在 DB 中不存在）
    if errors:
        print(f"\n[ERROR] Critical ({len(errors)}) - Must fix immediately:")
        print("-" * 60)
        for err in errors:
            print(f"  [X] {err['message']}")
            print(f"      -> Fix: Remove column from ORM model, or create DB migration")

    # 警告（DB 列在 ORM 中未定义）
    if warnings:
        print(f"\n[WARN] Warnings ({len(warnings)}) - Please review:")
        print("-" * 60)
        for warn in warnings:
            print(f"  [!] {warn['message']}")

    # 信息（表级别差异）
    if infos:
        print(f"\n[INFO] Information ({len(infos)}):")
        print("-" * 60)
        for info in infos:
            print(f"  [i] {info['message']}")

    # 汇总
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)

    if not errors and not warnings:
        print("\n[OK] Perfect! ORM models and database schema are fully synchronized")
        return 0

    if errors:
        print(f"\n[FAIL] Found {len(errors)} critical error(s)")
        print("       These will cause INSERT/SELECT operations to fail!")
        return 1

    if warnings:
        print(f"\n[PASS] Passed with {len(warnings)} warning(s): DB columns not defined in ORM")
        return 2

    return 0


def main():
    """主函数"""
    # 获取数据库连接
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("[ERROR] DATABASE_URL environment variable not set")
        print("        Please ensure .env file exists and contains DATABASE_URL")
        sys.exit(1)

    # 隐藏密码显示连接信息
    safe_url = database_url.split('@')[-1] if '@' in database_url else database_url
    print(f"Connecting to database: ...@{safe_url}")

    try:
        engine = create_engine(database_url)

        # 测试连接
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        print("[OK] Database connection successful\n")

    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        sys.exit(1)

    # 获取 ORM 和 DB 的 schema
    print("Fetching ORM model definitions...")
    orm_tables = get_orm_columns()
    print(f"  Found {len(orm_tables)} ORM tables\n")

    print("Fetching actual database schema...")
    db_tables = get_db_columns(engine)
    print(f"  Found {len(db_tables)} database tables\n")

    # 对比
    print("Comparing ORM vs Database...")
    errors, warnings, infos = compare_schemas(orm_tables, db_tables)

    # 打印报告
    exit_code = print_report(errors, warnings, infos)

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
