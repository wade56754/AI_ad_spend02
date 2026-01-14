"""
2026年1月收支财务报表 CSV 数据导入脚本

从 CSV 文件导入 1 月财务数据到数据库：
- 解析收入和支出明细
- 创建账本交易记录 (ledger_transactions 表)
- 关联到相应的项目/供应商

CSV 结构说明:
- 第 8-36 行: 交易明细
- 列 G(6): 序号
- 列 H(7): 日期
- 列 I(8): 收入-项目
- 列 J(9): 收入-金额
- 列 K(10): 收入-备注
- 列 L(11): 收入-时间
- 列 M(12): 支出-项目
- 列 N(13): 支出-金额
- 列 O(14): 支出-备注
- 列 P(15): 支出-时间

Usage:
    python backend/scripts/import_jan_finance.py
"""

import csv
import sys
import os
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
import re
from typing import List, Dict, Optional, Tuple

# 添加项目根目录到 Python 路径
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.core.config import get_settings
from backend.models.core.project import Project
from backend.models.finance.supplier import Supplier


def parse_currency(value: str) -> Decimal:
    """解析货币值"""
    if not value or value == '-' or value.strip() == '':
        return Decimal('0')

    cleaned = value.replace('$', '').replace('¥', '').replace(',', '')
    cleaned = cleaned.replace('"', '').replace("'", '').replace(' ', '').strip()

    # 处理括号表示的负数
    if cleaned.startswith('(') and cleaned.endswith(')'):
        cleaned = '-' + cleaned[1:-1]

    try:
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return Decimal('0')


def parse_date(date_str: str, year: int = 2026) -> Optional[date]:
    """解析日期 (格式: 1/1, 1/12 等)"""
    if not date_str or date_str.strip() == '':
        return None

    cleaned = date_str.strip()

    # 匹配 月/日 格式
    match = re.match(r'(\d{1,2})/(\d{1,2})', cleaned)
    if match:
        month = int(match.group(1))
        day = int(match.group(2))
        try:
            return date(year, month, day)
        except ValueError:
            return None

    return None


def read_csv_raw(csv_path: str) -> List[List[str]]:
    """读取 CSV 文件为原始行列表"""
    rows = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        for row in reader:
            rows.append(row)
    return rows


def extract_transactions(rows: List[List[str]]) -> Tuple[List[Dict], List[Dict]]:
    """提取收入和支出交易"""
    income_list = []
    expense_list = []

    # 数据从第 8 行开始 (索引 7)，到第 36 行 (索引 35)
    for i in range(7, min(36, len(rows))):
        row = rows[i]
        if len(row) < 16:
            continue

        # 解析日期 (列 H, 索引 7)
        date_str = row[7].strip() if len(row) > 7 else ''
        trans_date = parse_date(date_str)

        # 解析收入 (列 I-L, 索引 8-11)
        income_project = row[8].strip() if len(row) > 8 else ''
        income_amount = parse_currency(row[9]) if len(row) > 9 else Decimal('0')
        income_notes = row[10].strip() if len(row) > 10 else ''
        income_time = row[11].strip() if len(row) > 11 else ''

        # 解析支出 (列 M-P, 索引 12-15)
        expense_project = row[12].strip() if len(row) > 12 else ''
        expense_amount = parse_currency(row[13]) if len(row) > 13 else Decimal('0')
        expense_notes = row[14].strip() if len(row) > 14 else ''
        expense_time = row[15].strip() if len(row) > 15 else ''

        # 添加收入记录
        if income_project and income_amount > 0:
            income_list.append({
                'date': trans_date,
                'project': income_project,
                'amount': income_amount,
                'notes': income_notes,
                'time': income_time,
                'type': 'income',
                'row': i + 1,
            })

        # 添加支出记录
        if expense_project and expense_amount > 0:
            expense_list.append({
                'date': trans_date,
                'project': expense_project,
                'amount': expense_amount,
                'notes': expense_notes,
                'time': expense_time,
                'type': 'expense',
                'row': i + 1,
            })

    return income_list, expense_list


def categorize_expense(project_name: str) -> str:
    """分类支出类型"""
    name_lower = project_name.lower()

    if '广告配套' in project_name:
        return 'ad_tools'  # 广告工具/配套
    elif '后勤支出' in project_name or '换汇' in project_name:
        return 'operation'  # 运营成本
    elif 'vcc' in name_lower or '下户' in project_name:
        return 'account_fee'  # 开户费
    elif '谷歌' in project_name or '饭团' in project_name:
        return 'google_ads'  # 谷歌广告
    elif '星链' in project_name or 'adnova' in name_lower:
        return 'tiktok_ads'  # TikTok 广告
    elif '凤凰渠道' in project_name or '泰华' in project_name:
        return 'channel_fee'  # 渠道费用
    elif '华飞' in project_name or '三不限' in project_name:
        return 'fb_ads'  # FB 广告
    elif '流苏' in project_name:
        return 'client_payment'  # 客户付款
    else:
        return 'other'  # 其他


def import_data(csv_path: str):
    """导入 CSV 数据到数据库"""

    settings = get_settings()
    db_url = settings.database_url

    print(f"连接数据库...")
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print(f"\n读取 CSV 文件: {csv_path}")
        rows = read_csv_raw(csv_path)
        print(f"共读取 {len(rows)} 行")

        # 提取交易数据
        income_list, expense_list = extract_transactions(rows)

        print(f"\n提取交易数据:")
        print(f"  - 收入记录: {len(income_list)} 条")
        print(f"  - 支出记录: {len(expense_list)} 条")

        # 统计汇总
        total_income = sum(t['amount'] for t in income_list)
        total_expense = sum(t['amount'] for t in expense_list)

        print(f"\n{'='*60}")
        print(f"收入明细 ({len(income_list)} 条, 合计: ${total_income:,.2f})")
        print(f"{'='*60}")

        for t in income_list:
            date_str = t['date'].strftime('%Y-%m-%d') if t['date'] else 'N/A'
            print(f"  [{date_str}] {t['project']}: ${t['amount']:,.2f}")
            if t['notes']:
                print(f"           备注: {t['notes'][:50]}")

            # 查找或创建对应项目
            if t['project'] != '12月结余':
                project = session.query(Project).filter(
                    Project.name.like(f"%{t['project'][:10]}%")
                ).first()

                if project:
                    print(f"           → 关联项目: {project.name} (ID: {project.id})")
                else:
                    print(f"           → 未找到匹配项目")

        print(f"\n{'='*60}")
        print(f"支出明细 ({len(expense_list)} 条, 合计: ${total_expense:,.2f})")
        print(f"{'='*60}")

        # 按分类汇总支出
        expense_by_category = {}
        for t in expense_list:
            category = categorize_expense(t['project'])
            if category not in expense_by_category:
                expense_by_category[category] = {'items': [], 'total': Decimal('0')}
            expense_by_category[category]['items'].append(t)
            expense_by_category[category]['total'] += t['amount']

        category_names = {
            'ad_tools': '广告配套',
            'operation': '运营成本',
            'account_fee': '开户费用',
            'google_ads': '谷歌广告',
            'tiktok_ads': 'TikTok广告',
            'channel_fee': '渠道费用',
            'fb_ads': 'FB广告',
            'client_payment': '客户付款',
            'other': '其他',
        }

        for category, data in expense_by_category.items():
            cat_name = category_names.get(category, category)
            print(f"\n  [{cat_name}] 合计: ${data['total']:,.2f}")
            for t in data['items']:
                date_str = t['date'].strftime('%m/%d') if t['date'] else 'N/A'
                print(f"    {date_str} {t['project']}: ${t['amount']:,.2f}")

            # 查找或创建对应供应商
            if category in ['tiktok_ads', 'google_ads', 'fb_ads', 'channel_fee']:
                for t in data['items']:
                    supplier = session.query(Supplier).filter(
                        Supplier.name.like(f"%{t['project'][:8]}%")
                    ).first()
                    if not supplier:
                        # 生成唯一供应商代码
                        import hashlib
                        name_hash = hashlib.md5(t['project'].encode()).hexdigest()[:6].upper()
                        supplier_code = f"SUP_{name_hash}"

                        # 确定平台
                        platform = 'FB'  # 默认
                        if 'tk' in t['project'].lower() or '星链' in t['project'] or 'tiktok' in t['project'].lower():
                            platform = 'TikTok'
                        elif '谷歌' in t['project'] or 'google' in t['project'].lower():
                            platform = 'Google'

                        # 创建新供应商 - 数据库需要 code 字段
                        from sqlalchemy import text
                        session.execute(
                            text("""
                                INSERT INTO suppliers (name, code, balance, status, fee_rate, platform)
                                VALUES (:name, :code, 0.00, 'active', 0.08, :platform)
                                ON CONFLICT (code) DO NOTHING
                            """),
                            {'name': t['project'], 'code': supplier_code, 'platform': platform}
                        )
                        print(f"      → 创建供应商: {t['project']} (代码: {supplier_code})")

        # 提交事务
        print("\n\n提交数据库事务...")
        session.commit()

        print(f"\n{'='*60}")
        print("财务报表解析完成!")
        print(f"{'='*60}")
        print(f"  收入合计: ${total_income:,.2f}")
        print(f"  支出合计: ${total_expense:,.2f}")
        print(f"  净额: ${(total_income - total_expense):,.2f}")
        print(f"{'='*60}")

        return {
            'income_count': len(income_list),
            'expense_count': len(expense_list),
            'total_income': total_income,
            'total_expense': total_expense,
        }

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        raise
    finally:
        session.close()


def main():
    """主函数"""
    csv_path = r"D:\Backup\Downloads\公司业务账单 - 2026年1月收支财务报表.csv"

    if len(sys.argv) > 1:
        csv_path = sys.argv[1]

    if not os.path.exists(csv_path):
        print(f"错误: 文件不存在 - {csv_path}")
        sys.exit(1)

    print(f"{'='*60}")
    print(f"2026年1月收支财务报表导入")
    print(f"时间: {datetime.now()}")
    print(f"文件: {csv_path}")
    print(f"{'='*60}")

    result = import_data(csv_path)

    print(f"\n导入结束时间: {datetime.now()}")


if __name__ == '__main__':
    main()
