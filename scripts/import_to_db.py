#!/usr/bin/env python3
"""
财务数据导入到数据库

从解析的财务数据导入到 Supabase 数据库

使用方法：
    python scripts/import_to_db.py
"""

import sys
import os
from pathlib import Path
from decimal import Decimal
from datetime import date

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(project_root / '.env')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 导入解析函数
from scripts.import_finance_data import (
    parse_income_expense_report,
    parse_receivables_report,
    print_summary,
)


def get_database_url():
    """获取数据库连接 URL"""
    url = os.environ.get('DATABASE_URL')
    if not url:
        # 尝试从 Supabase 配置构建
        host = os.environ.get('SUPABASE_DB_HOST', 'localhost')
        port = os.environ.get('SUPABASE_DB_PORT', '5432')
        user = os.environ.get('SUPABASE_DB_USER', 'postgres')
        password = os.environ.get('SUPABASE_DB_PASSWORD', '')
        dbname = os.environ.get('SUPABASE_DB_NAME', 'postgres')
        url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    return url


def import_transactions_to_db(session, transactions: list[dict]) -> tuple[int, int]:
    """导入交易记录到 financial_events 表"""
    imported = 0
    skipped = 0

    for tx in transactions:
        # 使用 idempotency_key 检查是否已存在
        idempotency_key = tx['transaction_number']
        result = session.execute(
            text("SELECT id FROM financial_events WHERE idempotency_key = :key"),
            {"key": idempotency_key}
        )
        if result.fetchone():
            skipped += 1
            continue

        # 映射交易类型 (financial_events 支持: TOPUP, SPEND, PAYMENT, TRANSFER, ADJUSTMENT, FEE, REFUND)
        event_type = tx['transaction_type']  # 直接使用, 已经匹配

        # 金额 (始终为正, 由 event_type 决定方向)
        amount = float(tx['amount'])

        # 构建 payload JSON
        import json
        payload = json.dumps({
            "project_name": tx['project_name'],
            "description": tx['description'],
            "direction": tx['direction'],
            "transaction_time": tx.get('transaction_time', ''),
            "source": "tsv_import_2025_12",
        }, ensure_ascii=False)

        # 插入记录
        session.execute(
            text("""
                INSERT INTO financial_events (
                    event_type, event_status, source_type, source_ref,
                    amount, currency, event_date, payload, idempotency_key, created_at
                ) VALUES (
                    :event_type, 'confirmed', 'import', :source_ref,
                    :amount, 'CNY', :event_date, CAST(:payload AS jsonb), :idempotency_key, NOW()
                )
            """),
            {
                "event_type": event_type,
                "source_ref": f"tsv_import_{tx['transaction_date'].strftime('%Y%m')}",
                "amount": amount,
                "event_date": tx['transaction_date'],
                "payload": payload,
                "idempotency_key": idempotency_key,
            }
        )
        imported += 1

    return imported, skipped


def create_or_update_projects(session, receivables: list[dict]) -> dict:
    """创建或更新项目记录，返回项目名称到ID的映射"""
    project_map = {}

    for r in receivables:
        project_name = r['project_name']
        if not project_name:
            continue

        # 检查是否存在
        result = session.execute(
            text("SELECT id FROM projects WHERE name = :name"),
            {"name": project_name}
        )
        row = result.fetchone()

        if row:
            project_map[project_name] = row[0]
        else:
            # 创建新项目 (client_name/client_company 使用项目名称)
            result = session.execute(
                text("""
                    INSERT INTO projects (name, client_name, client_company, status, created_at, updated_at)
                    VALUES (:name, :client_name, :client_company, 'active', NOW(), NOW())
                    RETURNING id
                """),
                {"name": project_name, "client_name": project_name, "client_company": project_name}
            )
            project_map[project_name] = result.fetchone()[0]
            print(f"  创建项目: {project_name}")

    return project_map


def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser(description='财务数据导入到数据库')
    parser.add_argument('--yes', '-y', action='store_true', help='跳过确认直接导入')
    args = parser.parse_args()

    print("=" * 60)
    print("  财务数据导入到数据库")
    print("=" * 60)

    # 文件路径
    income_expense_file = r"C:\Users\user\Downloads\公司业务账单 - 2025年12月收支财务报表.tsv"
    receivables_file = r"C:\Users\user\Downloads\12月收支表汇总 - 2025年12月应收未收.tsv"

    # 检查文件存在
    for f in [income_expense_file, receivables_file]:
        if not os.path.exists(f):
            print(f"[ERROR] 文件不存在: {f}")
            return

    print("\n[INFO] 解析数据文件...")
    transactions = parse_income_expense_report(income_expense_file)
    receivables = parse_receivables_report(receivables_file)

    print(f"   交易记录: {len(transactions)} 条")
    print(f"   应收记录: {len(receivables)} 条")

    # 打印摘要
    print_summary(transactions, receivables)

    # 连接数据库
    print("\n[INFO] 连接数据库...")
    try:
        database_url = get_database_url()
        print(f"   数据库: {database_url[:50]}...")

        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()

        # 测试连接
        session.execute(text("SELECT 1"))
        print("   连接成功!")

    except Exception as e:
        print(f"[ERROR] 数据库连接失败: {e}")
        return

    # 询问确认
    print("\n" + "=" * 60)
    print("  确认导入?")
    print("=" * 60)
    print(f"  将导入 {len(transactions)} 条交易记录")
    print(f"  将创建/更新 {len(receivables)} 个项目")

    if args.yes:
        print("\n  [--yes 参数] 自动确认导入")
        answer = 'yes'
    else:
        print("\n  输入 'yes' 确认导入: ", end='')
        try:
            answer = input().strip().lower()
        except EOFError:
            answer = 'no'

    if answer != 'yes':
        print("\n[INFO] 已取消导入")
        session.close()
        return

    # 执行导入
    try:
        print("\n[INFO] 导入交易记录...")
        imported, skipped = import_transactions_to_db(session, transactions)
        print(f"   导入: {imported} 条")
        print(f"   跳过: {skipped} 条 (已存在)")

        print("\n[INFO] 创建/更新项目...")
        project_map = create_or_update_projects(session, receivables)
        print(f"   项目数: {len(project_map)}")

        session.commit()
        print("\n[SUCCESS] 导入完成!")

    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] 导入失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        session.close()


if __name__ == "__main__":
    main()
