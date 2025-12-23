"""
SQLite数据导入脚本 (简化版)
将处理后的Excel数据导入到SQLite数据库中

直接使用SQL创建表和导入数据，避免ORM兼容性问题
"""

import json
import sqlite3
import os
from datetime import datetime
from uuid import uuid4

# 数据库路径
DB_PATH = 'D:/project/AI_ad_spend02/ai_ad_spend_dev.db'
JSON_PATH = 'D:/project/AI_ad_spend02/processed_data.json'


def create_tables(conn):
    """创建必要的表"""
    cursor = conn.cursor()

    # 创建团队表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id TEXT PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            name TEXT,
            description TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT,
            updated_at TEXT
        )
    ''')

    # 创建投手表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS buyers (
            id TEXT PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            name TEXT,
            team_id TEXT,
            user_id TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (team_id) REFERENCES teams(id)
        )
    ''')

    # 创建渠道商表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            contact_name TEXT,
            contact_email TEXT,
            contact_phone TEXT,
            base_currency TEXT DEFAULT 'USD',
            payment_method TEXT DEFAULT 'bank_transfer',
            payment_terms TEXT,
            address TEXT,
            country TEXT,
            status TEXT DEFAULT 'active',
            platform TEXT,
            fee_rate REAL DEFAULT 0.1,
            fee_type TEXT DEFAULT 'PERCENTAGE',
            notes TEXT,
            total_accounts INTEGER DEFAULT 0,
            total_spend REAL DEFAULT 0,
            created_at TEXT,
            updated_at TEXT,
            created_by TEXT
        )
    ''')

    # 创建项目表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT,
            updated_at TEXT,
            created_by TEXT
        )
    ''')

    # 创建广告账户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ad_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            channel_id TEXT,
            supplier_id INTEGER,
            owner_id TEXT,
            team_id TEXT,
            buyer_id TEXT,
            name TEXT,
            account_code TEXT UNIQUE,
            status TEXT DEFAULT 'active',
            status_reason TEXT,
            spend_limit REAL DEFAULT 0,
            currency TEXT DEFAULT 'CNY',
            timezone TEXT DEFAULT 'Asia/Shanghai',
            created_at TEXT,
            updated_at TEXT,
            created_by TEXT,
            updated_by TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
            FOREIGN KEY (team_id) REFERENCES teams(id),
            FOREIGN KEY (buyer_id) REFERENCES buyers(id)
        )
    ''')

    # 创建充值记录表（新增）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS topup_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_name TEXT,
            supplier_id INTEGER,
            topup_date TEXT,
            buyer_code TEXT,
            account_name TEXT,
            amount REAL,
            clear_amount REAL DEFAULT 0,
            submit_clear REAL DEFAULT 0,
            transfer_amount REAL DEFAULT 0,
            settlement_status TEXT,
            fee REAL DEFAULT 0,
            notes TEXT,
            created_at TEXT,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        )
    ''')

    # 创建项目收支表（新增）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_date TEXT,
            team_code TEXT,
            business_type TEXT,
            region TEXT,
            project_name TEXT,
            follows_count INTEGER DEFAULT 0,
            raw_spend REAL DEFAULT 0,
            revenue REAL DEFAULT 0,
            profit REAL DEFAULT 0,
            prepaid_balance TEXT,
            notes TEXT,
            created_at TEXT
        )
    ''')

    # 创建财务事件表（新增）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS financial_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_date TEXT,
            event_type TEXT,
            team_code TEXT,
            amount REAL,
            description TEXT,
            notes TEXT,
            created_at TEXT
        )
    ''')

    conn.commit()
    print("数据库表创建完成")


def load_data():
    """加载JSON数据"""
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def import_teams(conn, teams_data):
    """导入团队"""
    print("\n--- 导入团队 ---")
    cursor = conn.cursor()
    imported, skipped = 0, 0
    now = datetime.now().isoformat()

    for team in teams_data:
        try:
            cursor.execute(
                "SELECT id FROM teams WHERE code = ?",
                (team['code'],)
            )
            if cursor.fetchone():
                skipped += 1
                continue

            team_id = str(uuid4())
            cursor.execute('''
                INSERT INTO teams (id, code, name, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                team_id,
                team['code'],
                team.get('name', f"{team['code']}团队"),
                team.get('status', 'active'),
                now, now
            ))
            print(f"  + {team['code']}")
            imported += 1
        except Exception as e:
            print(f"  ! 团队 {team['code']} 导入失败: {e}")

    conn.commit()
    print(f"团队: {imported} 新增, {skipped} 跳过")


def import_suppliers(conn, suppliers_data):
    """导入渠道商"""
    print("\n--- 导入渠道商 ---")
    cursor = conn.cursor()
    imported, skipped = 0, 0
    now = datetime.now().isoformat()

    for supplier in suppliers_data:
        name = supplier['name']
        try:
            cursor.execute(
                "SELECT id FROM suppliers WHERE name = ?",
                (name,)
            )
            if cursor.fetchone():
                skipped += 1
                continue

            cursor.execute('''
                INSERT INTO suppliers (
                    name, platform, status, base_currency, payment_method,
                    notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                name,
                supplier.get('platform', 'FB'),
                supplier.get('status', 'active'),
                'USD',
                'bank_transfer',
                supplier.get('notes', ''),
                now, now
            ))
            imported += 1
        except Exception as e:
            print(f"  ! 渠道商 {name} 导入失败: {e}")

    conn.commit()
    print(f"渠道商: {imported} 新增, {skipped} 跳过")


def import_buyers(conn, buyers_data):
    """导入投手"""
    print("\n--- 导入投手 ---")
    cursor = conn.cursor()
    imported, skipped = 0, 0
    now = datetime.now().isoformat()

    # 获取团队映射
    cursor.execute("SELECT id, code FROM teams")
    team_map = {row[1]: row[0] for row in cursor.fetchall()}

    for buyer in buyers_data:
        code = buyer['code']

        # 跳过复合代码
        if ',' in code or '，' in code:
            skipped += 1
            continue

        try:
            cursor.execute(
                "SELECT id FROM buyers WHERE code = ?",
                (code,)
            )
            if cursor.fetchone():
                skipped += 1
                continue

            team_id = team_map.get(buyer.get('team_code', 'ZZ'))
            buyer_id = str(uuid4())

            cursor.execute('''
                INSERT INTO buyers (id, code, name, team_id, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                buyer_id,
                code,
                buyer.get('name', code),
                team_id,
                buyer.get('status', 'active'),
                now, now
            ))
            print(f"  + {code}")
            imported += 1
        except Exception as e:
            print(f"  ! 投手 {code} 导入失败: {e}")

    conn.commit()
    print(f"投手: {imported} 新增, {skipped} 跳过")


def ensure_default_project(conn):
    """确保默认项目存在"""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM projects WHERE name = '默认项目'")
    result = cursor.fetchone()

    if result:
        print(f"\n默认项目已存在 (ID: {result[0]})")
        return result[0]

    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO projects (name, status, created_at, updated_at)
        VALUES ('默认项目', 'active', ?, ?)
    ''', (now, now))
    conn.commit()
    project_id = cursor.lastrowid
    print(f"\n创建默认项目 (ID: {project_id})")
    return project_id


def import_accounts(conn, accounts_data, project_id):
    """导入广告账户"""
    print("\n--- 导入广告账户 ---")
    cursor = conn.cursor()
    imported, skipped = 0, 0
    now = datetime.now().isoformat()

    # 获取渠道商映射
    cursor.execute("SELECT id, name FROM suppliers")
    supplier_map = {row[1]: row[0] for row in cursor.fetchall()}

    for account in accounts_data:
        name = account.get('name', '')

        if not name or name == 'nan':
            skipped += 1
            continue

        try:
            cursor.execute(
                "SELECT id FROM ad_accounts WHERE name = ?",
                (name,)
            )
            if cursor.fetchone():
                skipped += 1
                continue

            supplier_id = supplier_map.get(account.get('supplier_name'))
            account_code = f"ACC-{datetime.now().strftime('%Y%m%d')}-{imported + 1:04d}"

            cursor.execute('''
                INSERT INTO ad_accounts (
                    project_id, name, account_code, supplier_id, status,
                    currency, timezone, spend_limit, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                project_id,
                name,
                account_code,
                supplier_id,
                account.get('status', 'active'),
                'USD',
                'Asia/Shanghai',
                0,
                now, now
            ))
            imported += 1
        except Exception as e:
            print(f"  ! 账户 {name} 导入失败: {e}")

    conn.commit()
    print(f"广告账户: {imported} 新增, {skipped} 跳过")


def import_topups(conn, topups_data):
    """导入充值记录"""
    print("\n--- 导入充值记录 ---")
    cursor = conn.cursor()
    imported = 0
    now = datetime.now().isoformat()

    # 获取渠道商映射
    cursor.execute("SELECT id, name FROM suppliers")
    supplier_map = {row[1]: row[0] for row in cursor.fetchall()}

    for topup in topups_data:
        try:
            supplier_id = supplier_map.get(topup.get('supplier_name'))

            cursor.execute('''
                INSERT INTO topup_records (
                    supplier_name, supplier_id, topup_date, buyer_code,
                    account_name, amount, clear_amount, submit_clear,
                    transfer_amount, settlement_status, fee, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                topup.get('supplier_name', ''),
                supplier_id,
                topup.get('topup_date', ''),
                topup.get('buyer_code', ''),
                topup.get('account_name', ''),
                float(topup.get('amount', 0)),
                float(topup.get('clear_amount', 0)),
                float(topup.get('submit_clear', 0)),
                float(topup.get('transfer_amount', 0)),
                topup.get('settlement_status', ''),
                float(topup.get('fee', 0)),
                topup.get('notes', ''),
                now
            ))
            imported += 1
        except Exception as e:
            pass  # 静默处理

    conn.commit()
    print(f"充值记录: {imported} 条")


def import_daily_reports(conn, reports_data):
    """导入日报数据"""
    print("\n--- 导入项目收支 ---")
    cursor = conn.cursor()
    imported = 0
    now = datetime.now().isoformat()

    for report in reports_data:
        try:
            cursor.execute('''
                INSERT INTO project_reports (
                    report_date, team_code, business_type, region,
                    project_name, follows_count, raw_spend, revenue,
                    profit, prepaid_balance, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(report.get('report_date', '')),
                report.get('team_code', ''),
                report.get('business_type', ''),
                report.get('region', ''),
                report.get('project_name', ''),
                int(report.get('follows_count', 0)),
                float(report.get('raw_spend', 0)),
                float(report.get('revenue', 0)),
                float(report.get('profit', 0)),
                report.get('prepaid_balance', ''),
                report.get('notes', ''),
                now
            ))
            imported += 1
        except Exception as e:
            pass  # 静默处理

    conn.commit()
    print(f"项目收支: {imported} 条")


def import_financial_events(conn, events_data):
    """导入财务事件"""
    print("\n--- 导入财务事件 ---")
    cursor = conn.cursor()
    imported = 0
    now = datetime.now().isoformat()

    for event in events_data:
        try:
            cursor.execute('''
                INSERT INTO financial_events (
                    event_date, event_type, team_code, amount,
                    description, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(event.get('event_date', '')),
                event.get('event_type', ''),
                event.get('team_code', ''),
                float(event.get('amount', 0)),
                event.get('description', ''),
                event.get('notes', ''),
                now
            ))
            imported += 1
        except Exception as e:
            pass  # 静默处理

    conn.commit()
    print(f"财务事件: {imported} 条")


def show_stats(conn):
    """显示数据库统计"""
    cursor = conn.cursor()
    print("\n" + "=" * 60)
    print("数据库统计")
    print("=" * 60)

    tables = [
        ('teams', '团队'),
        ('buyers', '投手'),
        ('suppliers', '渠道商'),
        ('projects', '项目'),
        ('ad_accounts', '广告账户'),
        ('topup_records', '充值记录'),
        ('project_reports', '项目收支'),
        ('financial_events', '财务事件'),
    ]

    for table, name in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {name}: {count} 条")
        except Exception as e:
            print(f"  {name}: 表不存在")


def main():
    """主函数"""
    print("=" * 60)
    print("Excel数据导入SQLite数据库")
    print("=" * 60)

    # 检查文件
    if not os.path.exists(JSON_PATH):
        print(f"错误: 找不到数据文件 {JSON_PATH}")
        print("请先运行 import_excel_data.py 处理Excel文件")
        return

    # 加载数据
    print(f"\n加载数据: {JSON_PATH}")
    data = load_data()
    print(f"数据概览:")
    for key in ['teams', 'buyers', 'suppliers', 'accounts', 'topups', 'daily_reports', 'financial_events']:
        if key in data:
            print(f"  - {key}: {len(data[key])} 条")

    # 连接数据库
    print(f"\n连接数据库: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)

    try:
        # 创建表
        create_tables(conn)

        # 导入数据
        import_teams(conn, data.get('teams', []))
        import_suppliers(conn, data.get('suppliers', []))
        import_buyers(conn, data.get('buyers', []))
        project_id = ensure_default_project(conn)
        import_accounts(conn, data.get('accounts', []), project_id)
        import_topups(conn, data.get('topups', []))
        import_daily_reports(conn, data.get('daily_reports', []))
        import_financial_events(conn, data.get('financial_events', []))

        # 显示统计
        show_stats(conn)

        print("\n" + "=" * 60)
        print("数据导入完成!")
        print("=" * 60)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == '__main__':
    main()
