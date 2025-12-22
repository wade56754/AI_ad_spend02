"""
将处理后的Excel数据导入到Supabase PostgreSQL数据库

使用方法:
    python import_to_supabase.py

依赖:
    - 已运行 import_excel_data.py 生成 processed_data.json
    - .env 文件中配置了正确的 DATABASE_URL
"""

import json
import os
import sys
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

# 添加项目路径
sys.path.insert(0, 'D:/project/AI_ad_spend02')

# 设置环境变量 (如果.env未加载)
from dotenv import load_dotenv
load_dotenv('D:/project/AI_ad_spend02/.env')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 获取数据库URL
DATABASE_URL = os.getenv('DATABASE_URL')
JSON_PATH = 'D:/project/AI_ad_spend02/processed_data.json'


def load_data():
    """加载处理后的JSON数据"""
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def import_teams(session, teams_data):
    """导入团队数据"""
    print("\n--- 导入团队 ---")
    imported, skipped = 0, 0
    now = datetime.now().isoformat()

    for team in teams_data:
        code = team['code']
        try:
            # 检查是否存在
            result = session.execute(
                text("SELECT id FROM teams WHERE code = :code"),
                {"code": code}
            ).fetchone()

            if result:
                print(f"  跳过: {code} (已存在)")
                skipped += 1
                continue

            # 插入新记录
            team_id = str(uuid4())
            session.execute(
                text("""
                    INSERT INTO teams (id, code, name, status, created_at, updated_at)
                    VALUES (:id, :code, :name, :status, :created_at, :updated_at)
                """),
                {
                    'id': team_id,
                    'code': code,
                    'name': team.get('name', f"{code}团队"),
                    'status': 'active',
                    'created_at': now,
                    'updated_at': now
                }
            )
            print(f"  + 导入: {code}")
            imported += 1

        except Exception as e:
            print(f"  ! 错误 ({code}): {e}")

    session.commit()
    print(f"团队: {imported} 新增, {skipped} 跳过")
    return imported


def import_suppliers(session, suppliers_data):
    """导入渠道商数据"""
    print("\n--- 导入渠道商 ---")
    imported, skipped = 0, 0
    now = datetime.now().isoformat()

    for supplier in suppliers_data:
        name = supplier['name']
        try:
            # 检查是否存在
            result = session.execute(
                text("SELECT id FROM suppliers WHERE name = :name"),
                {"name": name}
            ).fetchone()

            if result:
                skipped += 1
                continue

            # 插入新记录
            session.execute(
                text("""
                    INSERT INTO suppliers (
                        name, platform, status, base_currency, payment_method,
                        fee_rate, fee_type, notes, total_accounts, total_spend,
                        created_at, updated_at
                    )
                    VALUES (
                        :name, :platform, :status, :base_currency, :payment_method,
                        :fee_rate, :fee_type, :notes, :total_accounts, :total_spend,
                        :created_at, :updated_at
                    )
                """),
                {
                    'name': name,
                    'platform': supplier.get('platform', 'FB'),
                    'status': 'active',
                    'base_currency': 'USD',
                    'payment_method': 'bank_transfer',
                    'fee_rate': 0.10,
                    'fee_type': 'PERCENTAGE',
                    'notes': supplier.get('notes', ''),
                    'total_accounts': 0,
                    'total_spend': 0,
                    'created_at': now,
                    'updated_at': now
                }
            )
            imported += 1

        except Exception as e:
            print(f"  ! 错误 ({name}): {e}")

    session.commit()
    print(f"渠道商: {imported} 新增, {skipped} 跳过")
    return imported


def import_buyers(session, buyers_data):
    """导入投手数据"""
    print("\n--- 导入投手 ---")
    imported, skipped = 0, 0
    now = datetime.now().isoformat()

    # 获取团队映射
    teams = session.execute(text("SELECT id, code FROM teams")).fetchall()
    team_map = {t[1]: t[0] for t in teams}

    for buyer in buyers_data:
        code = buyer['code']

        # 跳过复合代码
        if ',' in code or '，' in code:
            skipped += 1
            continue

        try:
            # 检查是否存在
            result = session.execute(
                text("SELECT id FROM buyers WHERE code = :code"),
                {"code": code}
            ).fetchone()

            if result:
                skipped += 1
                continue

            team_id = team_map.get(buyer.get('team_code', 'ZZ'))
            buyer_id = str(uuid4())

            session.execute(
                text("""
                    INSERT INTO buyers (id, code, name, team_id, status, created_at, updated_at)
                    VALUES (:id, :code, :name, :team_id, :status, :created_at, :updated_at)
                """),
                {
                    'id': buyer_id,
                    'code': code,
                    'name': buyer.get('name', code),
                    'team_id': team_id,
                    'status': 'active',
                    'created_at': now,
                    'updated_at': now
                }
            )
            print(f"  + 导入: {code}")
            imported += 1

        except Exception as e:
            print(f"  ! 错误 ({code}): {e}")

    session.commit()
    print(f"投手: {imported} 新增, {skipped} 跳过")
    return imported


def ensure_default_project(session):
    """确保默认项目存在"""
    result = session.execute(
        text("SELECT id FROM projects WHERE name = :name"),
        {"name": "默认项目"}
    ).fetchone()

    if result:
        print(f"\n默认项目已存在 (ID: {result[0]})")
        return result[0]

    now = datetime.now().isoformat()
    session.execute(
        text("""
            INSERT INTO projects (name, status, created_at, updated_at)
            VALUES (:name, :status, :created_at, :updated_at)
            RETURNING id
        """),
        {
            'name': '默认项目',
            'status': 'active',
            'created_at': now,
            'updated_at': now
        }
    )
    session.commit()

    result = session.execute(
        text("SELECT id FROM projects WHERE name = :name"),
        {"name": "默认项目"}
    ).fetchone()

    print(f"\n创建默认项目 (ID: {result[0]})")
    return result[0]


def import_accounts(session, accounts_data, project_id):
    """导入广告账户数据"""
    print("\n--- 导入广告账户 ---")
    imported, skipped = 0, 0
    now = datetime.now().isoformat()

    # 获取渠道商映射
    suppliers = session.execute(text("SELECT id, name FROM suppliers")).fetchall()
    supplier_map = {s[1]: s[0] for s in suppliers}

    for account in accounts_data:
        name = account.get('name', '')

        if not name or name == 'nan':
            skipped += 1
            continue

        try:
            # 检查是否存在
            result = session.execute(
                text("SELECT id FROM ad_accounts WHERE name = :name"),
                {"name": name}
            ).fetchone()

            if result:
                skipped += 1
                continue

            supplier_id = supplier_map.get(account.get('supplier_name'))
            account_code = f"ACC-{datetime.now().strftime('%Y%m%d')}-{imported + 1:04d}"

            session.execute(
                text("""
                    INSERT INTO ad_accounts (
                        project_id, name, account_code, supplier_id, status,
                        currency, timezone, spend_limit, created_at, updated_at
                    )
                    VALUES (
                        :project_id, :name, :account_code, :supplier_id, :status,
                        :currency, :timezone, :spend_limit, :created_at, :updated_at
                    )
                """),
                {
                    'project_id': project_id,
                    'name': name,
                    'account_code': account_code,
                    'supplier_id': supplier_id,
                    'status': 'active',
                    'currency': 'USD',
                    'timezone': 'Asia/Shanghai',
                    'spend_limit': 0,
                    'created_at': now,
                    'updated_at': now
                }
            )
            imported += 1

        except Exception as e:
            print(f"  ! 错误: {e}")

    session.commit()
    print(f"广告账户: {imported} 新增, {skipped} 跳过")
    return imported


def show_stats(session):
    """显示数据库统计"""
    print("\n" + "=" * 60)
    print("数据库统计")
    print("=" * 60)

    tables = [
        ('teams', '团队'),
        ('buyers', '投手'),
        ('suppliers', '渠道商'),
        ('projects', '项目'),
        ('ad_accounts', '广告账户'),
    ]

    for table, name in tables:
        try:
            result = session.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()
            print(f"  {name}: {result[0]} 条")
        except Exception as e:
            print(f"  {name}: 查询失败 ({e})")


def main():
    """主函数"""
    print("=" * 60)
    print("导入数据到 Supabase PostgreSQL")
    print("=" * 60)

    # 检查数据文件
    if not os.path.exists(JSON_PATH):
        print(f"错误: 找不到 {JSON_PATH}")
        print("请先运行 import_excel_data.py")
        return

    # 检查数据库URL
    if not DATABASE_URL:
        print("错误: DATABASE_URL 未配置")
        return

    print(f"\n数据库: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")

    # 加载数据
    print(f"\n加载数据: {JSON_PATH}")
    data = load_data()
    print(f"数据概览:")
    print(f"  - 团队: {len(data.get('teams', []))} 条")
    print(f"  - 投手: {len(data.get('buyers', []))} 条")
    print(f"  - 渠道商: {len(data.get('suppliers', []))} 条")
    print(f"  - 账户: {len(data.get('accounts', []))} 条")

    # 创建数据库连接
    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        print("\n数据库连接成功!")
    except Exception as e:
        print(f"\n数据库连接失败: {e}")
        return

    try:
        # 导入数据
        import_teams(session, data.get('teams', []))
        import_suppliers(session, data.get('suppliers', []))
        import_buyers(session, data.get('buyers', []))
        project_id = ensure_default_project(session)
        import_accounts(session, data.get('accounts', []), project_id)

        # 显示统计
        show_stats(session)

        print("\n" + "=" * 60)
        print("数据导入完成!")
        print("=" * 60)

    except Exception as e:
        session.rollback()
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == '__main__':
    main()
