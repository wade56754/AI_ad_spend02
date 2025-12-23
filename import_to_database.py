"""
数据库导入脚本
将处理后的Excel数据导入到数据库中

数据导入顺序：
1. Teams (团队)
2. Buyers (投手)
3. Suppliers (渠道商/户商)
4. Projects (项目) - 默认项目
5. AdAccounts (广告账户)
6. TopupRequests (充值记录) - 可选
"""

import json
import sys
import os
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

# 添加项目路径
sys.path.insert(0, 'D:/project/AI_ad_spend02')

# 设置环境变量
os.environ.setdefault('DATABASE_URL', 'sqlite:///D:/project/AI_ad_spend02/ai_ad_spend_dev.db')
os.environ.setdefault('JWT_SECRET', 'dev_secret_for_testing_only_not_for_production_use_64_chars_minimum')
os.environ.setdefault('ENCRYPTION_KEY', 'dev_encryption_key_32_chars_min')
os.environ.setdefault('SUPABASE_URL', 'https://placeholder.supabase.co')
os.environ.setdefault('SUPABASE_ANON_KEY', 'placeholder_anon_key_for_dev')
os.environ.setdefault('SUPABASE_SERVICE_ROLE_KEY', 'placeholder_service_key_for_dev')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 数据库连接
DATABASE_URL = 'sqlite:///D:/project/AI_ad_spend02/ai_ad_spend_dev.db'


def load_processed_data(json_path='D:/project/AI_ad_spend02/processed_data.json'):
    """加载处理后的JSON数据"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_tables(engine):
    """创建数据库表（如果不存在）"""
    from backend.models.base import Base
    from backend.models.finance.team import Team
    from backend.models.finance.buyer import Buyer
    from backend.models.finance.supplier import Supplier
    from backend.models.accounts.ad_account import AdAccount
    from backend.models.core.project import Project
    Base.metadata.create_all(engine)
    print("数据库表创建完成")


def import_teams(session, teams_data):
    """导入团队数据"""
    print("\n--- 导入团队 ---")
    imported = 0
    skipped = 0

    for team in teams_data:
        # 检查是否已存在
        existing = session.execute(
            text("SELECT id FROM teams WHERE code = :code"),
            {"code": team['code']}
        ).fetchone()

        if existing:
            print(f"  跳过已存在: {team['code']}")
            skipped += 1
            continue

        # 插入新团队
        team_id = str(uuid4())
        session.execute(
            text("""
                INSERT INTO teams (id, code, name, status, created_at, updated_at)
                VALUES (:id, :code, :name, :status, :created_at, :updated_at)
            """),
            {
                'id': team_id,
                'code': team['code'],
                'name': team.get('name', f"{team['code']}团队"),
                'status': team.get('status', 'active'),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        )
        print(f"  导入: {team['code']} (ID: {team_id[:8]}...)")
        imported += 1

    session.commit()
    print(f"团队导入完成: {imported} 新增, {skipped} 跳过")
    return imported


def import_suppliers(session, suppliers_data):
    """导入渠道商/户商数据"""
    print("\n--- 导入渠道商 ---")
    imported = 0
    skipped = 0

    for supplier in suppliers_data:
        name = supplier['name']

        # 检查是否已存在
        existing = session.execute(
            text("SELECT id FROM suppliers WHERE name = :name"),
            {"name": name}
        ).fetchone()

        if existing:
            skipped += 1
            continue

        # 插入新渠道商
        supplier_id = session.execute(
            text("""
                INSERT INTO suppliers (
                    name, platform, status, base_currency, payment_method,
                    notes, created_at, updated_at
                )
                VALUES (
                    :name, :platform, :status, :base_currency, :payment_method,
                    :notes, :created_at, :updated_at
                )
            """),
            {
                'name': name,
                'platform': supplier.get('platform', 'FB'),
                'status': supplier.get('status', 'active'),
                'base_currency': 'USD',
                'payment_method': 'bank_transfer',
                'notes': supplier.get('notes', ''),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        )
        imported += 1

    session.commit()
    print(f"渠道商导入完成: {imported} 新增, {skipped} 跳过")
    return imported


def import_buyers(session, buyers_data):
    """导入投手数据"""
    print("\n--- 导入投手 ---")
    imported = 0
    skipped = 0

    # 获取团队ID映射
    teams = session.execute(text("SELECT id, code FROM teams")).fetchall()
    team_map = {t[1]: t[0] for t in teams}

    for buyer in buyers_data:
        code = buyer['code']

        # 跳过复合投手代码（如 "YJ，HY，LM"）
        if '，' in code or ',' in code:
            skipped += 1
            continue

        # 检查是否已存在
        existing = session.execute(
            text("SELECT id FROM buyers WHERE code = :code"),
            {"code": code}
        ).fetchone()

        if existing:
            skipped += 1
            continue

        # 获取团队ID
        team_code = buyer.get('team_code', 'ZZ')
        team_id = team_map.get(team_code)

        # 插入新投手
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
                'status': buyer.get('status', 'active'),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        )
        imported += 1

    session.commit()
    print(f"投手导入完成: {imported} 新增, {skipped} 跳过")
    return imported


def ensure_default_project(session):
    """确保默认项目存在"""
    print("\n--- 检查默认项目 ---")

    existing = session.execute(
        text("SELECT id FROM projects WHERE name = :name"),
        {"name": "默认项目"}
    ).fetchone()

    if existing:
        print(f"  默认项目已存在 (ID: {existing[0]})")
        return existing[0]

    # 创建默认项目
    project_id = 1
    session.execute(
        text("""
            INSERT INTO projects (id, name, status, created_at, updated_at)
            VALUES (:id, :name, :status, :created_at, :updated_at)
        """),
        {
            'id': project_id,
            'name': '默认项目',
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
    )
    session.commit()
    print(f"  创建默认项目 (ID: {project_id})")
    return project_id


def import_accounts(session, accounts_data, project_id):
    """导入广告账户数据"""
    print("\n--- 导入广告账户 ---")
    imported = 0
    skipped = 0

    # 获取渠道商ID映射
    suppliers = session.execute(text("SELECT id, name FROM suppliers")).fetchall()
    supplier_map = {s[1]: s[0] for s in suppliers}

    for account in accounts_data:
        name = account['name']

        # 跳过空名称
        if not name or name == 'nan':
            skipped += 1
            continue

        # 检查是否已存在（按名称）
        existing = session.execute(
            text("SELECT id FROM ad_accounts WHERE name = :name"),
            {"name": name}
        ).fetchone()

        if existing:
            skipped += 1
            continue

        # 获取渠道商ID
        supplier_name = account.get('supplier_name', '')
        supplier_id = supplier_map.get(supplier_name)

        # 生成账户代码
        account_code = f"ACC-{datetime.now().strftime('%Y%m%d')}-{imported + 1:04d}"

        # 插入新账户
        session.execute(
            text("""
                INSERT INTO ad_accounts (
                    project_id, name, account_code, status, currency, timezone,
                    spend_limit, created_at, updated_at
                )
                VALUES (
                    :project_id, :name, :account_code, :status, :currency, :timezone,
                    :spend_limit, :created_at, :updated_at
                )
            """),
            {
                'project_id': project_id,
                'name': name,
                'account_code': account_code,
                'status': account.get('status', 'active'),
                'currency': 'USD',
                'timezone': 'Asia/Shanghai',
                'spend_limit': 0,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        )
        imported += 1

    session.commit()
    print(f"广告账户导入完成: {imported} 新增, {skipped} 跳过")
    return imported


def show_database_stats(session):
    """显示数据库统计信息"""
    print("\n" + "=" * 60)
    print("数据库统计信息")
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
            count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()[0]
            print(f"  {name}: {count} 条")
        except Exception as e:
            print(f"  {name}: 表不存在或查询失败 ({e})")


def main():
    """主函数"""
    print("=" * 60)
    print("Excel数据导入到数据库")
    print("=" * 60)

    # 加载处理后的数据
    print("\n加载处理后的数据...")
    data = load_processed_data()
    print(f"数据加载成功:")
    print(f"  - 团队: {len(data['teams'])} 个")
    print(f"  - 投手: {len(data['buyers'])} 个")
    print(f"  - 渠道商: {len(data['suppliers'])} 个")
    print(f"  - 账户: {len(data['accounts'])} 个")

    # 创建数据库连接
    print(f"\n连接数据库: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)

    # 创建表
    create_tables(engine)

    # 创建会话
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 导入数据
        import_teams(session, data['teams'])
        import_suppliers(session, data['suppliers'])
        import_buyers(session, data['buyers'])
        project_id = ensure_default_project(session)
        import_accounts(session, data['accounts'], project_id)

        # 显示统计
        show_database_stats(session)

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
