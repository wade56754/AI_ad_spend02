"""
将处理后的Excel数据导入到Supabase PostgreSQL数据库 (v2)

修复:
- 添加 code 字段到 suppliers
- 使用独立事务处理每条记录
- 正确的错误处理
"""

import json
import os
import sys
import re
from datetime import datetime
from uuid import uuid4

sys.path.insert(0, 'D:/project/AI_ad_spend02')

from dotenv import load_dotenv
load_dotenv('D:/project/AI_ad_spend02/.env')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv('DATABASE_URL')
JSON_PATH = 'D:/project/AI_ad_spend02/processed_data.json'


def load_data():
    """加载处理后的JSON数据"""
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_code(name: str) -> str:
    """从名称生成唯一代码"""
    # 移除特殊字符，取前10个字符
    code = re.sub(r'[^\w\u4e00-\u9fff]', '', name)[:10]
    # 添加随机后缀确保唯一
    return f"{code}-{str(uuid4())[:4].upper()}"


def import_teams(engine, teams_data):
    """导入团队数据"""
    print("\n--- 导入团队 ---")
    imported, skipped = 0, 0
    now = datetime.now().isoformat()

    for team in teams_data:
        code = team['code']
        with engine.connect() as conn:
            try:
                result = conn.execute(
                    text("SELECT id FROM teams WHERE code = :code"),
                    {"code": code}
                ).fetchone()

                if result:
                    print(f"  跳过: {code} (已存在)")
                    skipped += 1
                    continue

                team_id = str(uuid4())
                conn.execute(
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
                conn.commit()
                print(f"  + 导入: {code}")
                imported += 1

            except Exception as e:
                conn.rollback()
                print(f"  ! 错误 ({code}): {str(e)[:50]}")

    print(f"团队: {imported} 新增, {skipped} 跳过")
    return imported


def import_suppliers(engine, suppliers_data):
    """导入渠道商数据"""
    print("\n--- 导入渠道商 ---")
    imported, skipped = 0, 0

    for supplier in suppliers_data:
        name = supplier['name']
        with engine.connect() as conn:
            try:
                result = conn.execute(
                    text("SELECT id FROM suppliers WHERE name = :name"),
                    {"name": name}
                ).fetchone()

                if result:
                    skipped += 1
                    continue

                # 生成唯一代码
                code = generate_code(name)

                conn.execute(
                    text("""
                        INSERT INTO suppliers (
                            name, code, status, balance, platform,
                            fee_rate, fee_type, notes, base_currency, payment_method
                        )
                        VALUES (
                            :name, :code, :status, :balance, :platform,
                            :fee_rate, :fee_type, :notes, :base_currency, :payment_method
                        )
                    """),
                    {
                        'name': name,
                        'code': code,
                        'status': 'active',
                        'balance': 0,
                        'platform': supplier.get('platform', 'FB'),
                        'fee_rate': 0.10,
                        'fee_type': 'PERCENTAGE',
                        'notes': supplier.get('notes', ''),
                        'base_currency': 'USD',
                        'payment_method': 'bank_transfer'
                    }
                )
                conn.commit()
                print(f"  + {name[:25]}...")
                imported += 1

            except Exception as e:
                conn.rollback()
                error_msg = str(e)[:80]
                print(f"  ! 错误: {error_msg}")

    print(f"渠道商: {imported} 新增, {skipped} 跳过")
    return imported


def import_buyers(engine, buyers_data):
    """导入投手数据"""
    print("\n--- 导入投手 ---")
    imported, skipped = 0, 0

    # 获取团队映射
    with engine.connect() as conn:
        teams = conn.execute(text("SELECT id, code FROM teams")).fetchall()
        team_map = {t[1]: t[0] for t in teams}

    for buyer in buyers_data:
        code = buyer['code']

        # 跳过复合代码
        if ',' in code or '，' in code:
            skipped += 1
            continue

        with engine.connect() as conn:
            try:
                result = conn.execute(
                    text("SELECT id FROM buyers WHERE code = :code"),
                    {"code": code}
                ).fetchone()

                if result:
                    skipped += 1
                    continue

                team_id = team_map.get(buyer.get('team_code', 'ZZ'))
                buyer_id = str(uuid4())

                conn.execute(
                    text("""
                        INSERT INTO buyers (id, code, name, team_id, status)
                        VALUES (:id, :code, :name, :team_id, :status)
                    """),
                    {
                        'id': buyer_id,
                        'code': code,
                        'name': buyer.get('name', code),
                        'team_id': team_id,
                        'status': 'active'
                    }
                )
                conn.commit()
                print(f"  + {code}")
                imported += 1

            except Exception as e:
                conn.rollback()
                print(f"  ! 错误 ({code}): {str(e)[:50]}")

    print(f"投手: {imported} 新增, {skipped} 跳过")
    return imported


def ensure_default_project(engine):
    """确保默认项目存在"""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id FROM projects WHERE name = :name"),
            {"name": "默认项目"}
        ).fetchone()

        if result:
            print(f"\n默认项目已存在 (ID: {result[0]})")
            return result[0]

        try:
            conn.execute(
                text("""
                    INSERT INTO projects (name, client_name, client_company, status)
                    VALUES (:name, :client_name, :client_company, :status)
                """),
                {'name': '默认项目', 'client_name': '默认客户', 'client_company': '默认公司', 'status': 'active'}
            )
            conn.commit()

            result = conn.execute(
                text("SELECT id FROM projects WHERE name = :name"),
                {"name": "默认项目"}
            ).fetchone()

            print(f"\n创建默认项目 (ID: {result[0]})")
            return result[0]
        except Exception as e:
            conn.rollback()
            print(f"\n项目创建失败: {e}")
            return None


def import_accounts(engine, accounts_data, project_id):
    """导入广告账户数据"""
    print("\n--- 导入广告账户 ---")
    imported, skipped = 0, 0

    if not project_id:
        print("  跳过: 没有默认项目")
        return 0

    for account in accounts_data[:30]:  # 限制数量
        name = account.get('name', '')

        if not name or name == 'nan':
            skipped += 1
            continue

        with engine.connect() as conn:
            try:
                result = conn.execute(
                    text("SELECT id FROM ad_accounts WHERE name = :name"),
                    {"name": name}
                ).fetchone()

                if result:
                    skipped += 1
                    continue

                account_code = f"ACC-{datetime.now().strftime('%m%d')}-{imported + 1:04d}"

                conn.execute(
                    text("""
                        INSERT INTO ad_accounts (
                            project_id, name, account_code, status,
                            currency, timezone, spend_limit
                        )
                        VALUES (
                            :project_id, :name, :account_code, :status,
                            :currency, :timezone, :spend_limit
                        )
                    """),
                    {
                        'project_id': project_id,
                        'name': name,
                        'account_code': account_code,
                        'status': 'active',
                        'currency': 'USD',
                        'timezone': 'Asia/Shanghai',
                        'spend_limit': 0
                    }
                )
                conn.commit()
                imported += 1

            except Exception as e:
                conn.rollback()
                error_msg = str(e)[:80]
                print(f"  ! 错误: {error_msg}")

    print(f"广告账户: {imported} 新增, {skipped} 跳过")
    return imported


def show_stats(engine):
    """显示数据库统计"""
    print("\n" + "=" * 50)
    print("数据库统计")
    print("=" * 50)

    tables = [
        ('teams', '团队'),
        ('buyers', '投手'),
        ('suppliers', '渠道商'),
        ('projects', '项目'),
        ('ad_accounts', '广告账户'),
    ]

    with engine.connect() as conn:
        for table, name in tables:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()
                print(f"  {name}: {result[0]} 条")
            except Exception as e:
                print(f"  {name}: 查询失败")


def main():
    """主函数"""
    print("=" * 50)
    print("导入数据到 Supabase PostgreSQL (v2)")
    print("=" * 50)

    if not os.path.exists(JSON_PATH):
        print(f"错误: 找不到 {JSON_PATH}")
        return

    if not DATABASE_URL:
        print("错误: DATABASE_URL 未配置")
        return

    db_host = DATABASE_URL.split('@')[-1].split('/')[0] if '@' in DATABASE_URL else 'unknown'
    print(f"\n数据库: {db_host}")

    print(f"\n加载数据: {JSON_PATH}")
    data = load_data()
    print(f"  团队: {len(data.get('teams', []))} 条")
    print(f"  投手: {len(data.get('buyers', []))} 条")
    print(f"  渠道商: {len(data.get('suppliers', []))} 条")
    print(f"  账户: {len(data.get('accounts', []))} 条")

    try:
        engine = create_engine(DATABASE_URL)
        # 测试连接
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("\n数据库连接成功!")
    except Exception as e:
        print(f"\n数据库连接失败: {e}")
        return

    # 导入数据
    import_teams(engine, data.get('teams', []))
    import_suppliers(engine, data.get('suppliers', []))
    import_buyers(engine, data.get('buyers', []))
    project_id = ensure_default_project(engine)
    import_accounts(engine, data.get('accounts', []), project_id)

    # 显示统计
    show_stats(engine)

    print("\n" + "=" * 50)
    print("导入完成!")
    print("=" * 50)


if __name__ == '__main__':
    main()
