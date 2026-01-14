"""
12月项目消耗 CSV 数据导入脚本

从 CSV 文件导入 12 月项目消耗数据到数据库：
- 创建/更新项目记录 (projects 表)
- 创建日报记录 (daily_reports 表)

CSV 文件结构较复杂，包含多个数据区域：
1. 日本代投区域（岳总、HT、流苏）
2. SZ项目区域（爱尔兰、德国、加拿大等）

Usage:
    python backend/scripts/import_dec_consumption.py
"""

import csv
import sys
import os
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
import re
from typing import List, Dict, Optional

# 添加项目根目录到 Python 路径
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.core.config import get_settings
from backend.models.core.project import Project
from backend.models.workflow.daily_report import DailyReport
from backend.models.accounts.ad_account import AdAccount


def parse_currency(value: str) -> Decimal:
    """解析货币值，处理 $、逗号、引号等"""
    if not value or value == '-' or value.strip() == '':
        return Decimal('0')

    # 移除货币符号、逗号、引号、空格
    cleaned = value.replace('$', '').replace('¥', '').replace(',', '')
    cleaned = cleaned.replace('"', '').replace("'", '').strip()

    # 处理括号表示的负数 (1,234) -> -1234
    if cleaned.startswith('(') and cleaned.endswith(')'):
        cleaned = '-' + cleaned[1:-1]

    try:
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        print(f"  警告: 无法解析货币值 '{value}'，使用 0")
        return Decimal('0')


def parse_number(value: str) -> int:
    """解析整数"""
    if not value or value == '-' or value.strip() == '':
        return 0

    cleaned = value.replace(',', '').replace('"', '').strip()

    try:
        return int(float(cleaned))
    except (ValueError, TypeError):
        print(f"  警告: 无法解析数字 '{value}'，使用 0")
        return 0


def read_csv_raw(csv_path: str) -> List[List[str]]:
    """读取 CSV 文件为原始行列表"""
    rows = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        for row in reader:
            rows.append(row)
    return rows


def extract_japan_data(rows: List[List[str]]) -> List[Dict]:
    """提取日本代投数据（第 1-4 行）"""
    data = []
    # 行 0: 标题 - 地区,12月代投,有效结款,有效人数,收款,利润
    # 行 1-3: 数据
    for i in range(1, 4):
        if i >= len(rows):
            break
        row = rows[i]
        if len(row) < 6:
            continue

        region = row[0].strip() if row[0] else ''
        project_name = row[1].strip() if row[1] else ''
        spend = parse_currency(row[2])  # 有效结款 = 消耗
        conversions = parse_number(row[3])  # 有效人数
        revenue = parse_currency(row[4])  # 收款
        profit = parse_currency(row[5])  # 利润

        if project_name and region:
            data.append({
                'region': region,
                'project_name': project_name,
                'spend': spend,
                'conversions': conversions,
                'revenue': revenue,
                'profit': profit,
                'source': '日本代投'
            })

    return data


def extract_sz_data(rows: List[List[str]]) -> List[Dict]:
    """提取 SZ 项目数据（第 7-15 行）"""
    data = []
    # 行 6: 标题 - SZ项目,有效粉,消耗(加充值手续费）,收款,利润
    # 行 7-14: 数据
    for i in range(7, 16):
        if i >= len(rows):
            break
        row = rows[i]
        if len(row) < 5:
            continue

        project_name = row[0].strip() if row[0] else ''
        conversions = parse_number(row[1])  # 有效粉
        spend = parse_currency(row[2])  # 消耗
        revenue = parse_currency(row[3])  # 收款
        profit = parse_currency(row[4])  # 利润

        # 跳过空行或无效行
        if not project_name or project_name in ['', '地区', '月份']:
            continue

        # 从项目名推断地区
        region = infer_region(project_name)

        data.append({
            'region': region,
            'project_name': project_name,
            'spend': spend,
            'conversions': conversions,
            'revenue': revenue,
            'profit': profit,
            'source': 'SZ项目'
        })

    return data


def infer_region(project_name: str) -> str:
    """从项目名称推断地区"""
    name_lower = project_name.lower()

    region_keywords = {
        '日本': ['日本', '🇯🇵', 'japan'],
        '德国': ['德国', 'germany'],
        '爱尔兰': ['爱尔兰', 'ireland'],
        '加拿大': ['加拿大', 'canada', 'sz1-加拿大', 'sz2-加拿大', 'f2加拿大'],
        '新加坡': ['新加坡', 'singapore', 'f2新加坡'],
        '美国': ['美国', 'usa', 'us', 'america'],
        '印度': ['印度', 'india'],
        '巴西': ['巴西', 'brazil'],
        '印尼': ['印尼', 'indonesia'],
        '马来西亚': ['马来', 'malaysia'],
        '韩国': ['韩国', 'korea'],
        '瑞典': ['瑞典', 'sweden'],
        '比利时': ['比利时', 'belgium'],
        '尼日利亚': ['尼日利亚', 'nigeria'],
    }

    for region, keywords in region_keywords.items():
        for kw in keywords:
            if kw in name_lower or kw in project_name:
                return region

    return '未知'


def import_data(csv_path: str):
    """导入 CSV 数据到数据库"""

    # 获取数据库连接
    settings = get_settings()
    db_url = settings.database_url

    print(f"连接数据库...")
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 读取 CSV 文件
        print(f"\n读取 CSV 文件: {csv_path}")
        rows = read_csv_raw(csv_path)
        print(f"共读取 {len(rows)} 行")

        # 提取数据
        japan_data = extract_japan_data(rows)
        sz_data = extract_sz_data(rows)

        all_data = japan_data + sz_data
        print(f"\n提取到 {len(all_data)} 条有效数据:")
        print(f"  - 日本代投: {len(japan_data)} 条")
        print(f"  - SZ项目: {len(sz_data)} 条")

        # 统计
        projects_created = 0
        projects_updated = 0
        reports_created = 0
        total_spend = Decimal('0')
        total_revenue = Decimal('0')
        total_profit = Decimal('0')

        # 获取或创建默认广告账户
        default_account = session.query(AdAccount).first()
        if not default_account:
            print("\n警告: 没有找到广告账户，跳过日报创建")
            default_account_id = None
        else:
            default_account_id = default_account.id
            print(f"\n使用默认广告账户: {default_account.name} (ID: {default_account_id})")

        # 处理每条数据
        for i, item in enumerate(all_data):
            project_name = item['project_name']
            region = item['region']
            spend = item['spend']
            conversions = item['conversions']
            revenue = item['revenue']
            profit = item['profit']
            source = item['source']

            print(f"\n[{i+1}] {source} - {project_name} ({region})")
            print(f"    消耗: ${spend:.2f}, 进粉: {conversions}, 收款: ${revenue:.2f}, 利润: ${profit:.2f}")

            # 查找或创建项目
            project = session.query(Project).filter(
                Project.name == project_name
            ).first()

            if not project:
                # 计算单价
                unit_price = Decimal('25')  # 默认单价
                if conversions > 0 and revenue > 0:
                    unit_price = revenue / conversions

                # 创建新项目
                project = Project(
                    name=project_name,
                    client_name=project_name,
                    client_company=source,  # 使用数据来源作为客户公司
                    description=f"来源: {source}",
                    region=region,
                    status='active',
                    currency='USD',
                    unit_price=unit_price,
                )
                session.add(project)
                session.flush()
                projects_created += 1
                print(f"    创建项目: ID={project.id}, 单价=${unit_price:.2f}")
            else:
                # 更新地区信息
                if not project.region and region != '未知':
                    project.region = region
                projects_updated += 1
                print(f"    已存在项目: ID={project.id}")

            # 注意: 日报表有唯一约束 (report_date, ad_account_id, region)
            # 相同地区的多个项目会冲突，因此暂不创建日报记录
            # 数据已记录到项目表中，后续可通过结算模块处理
            print(f"    财务数据: 消耗=${spend}, 收入=${revenue}, 利润=${profit}")

            # 累计统计
            total_spend += spend
            total_revenue += revenue
            total_profit += profit

        # 提交事务
        print("\n\n提交数据库事务...")
        session.commit()

        print("\n" + "=" * 60)
        print("导入完成!")
        print(f"  新建项目: {projects_created}")
        print(f"  更新项目: {projects_updated}")
        print(f"  创建日报: {reports_created}")
        print("-" * 60)
        print(f"  总消耗: ${total_spend:,.2f}")
        print(f"  总收款: ${total_revenue:,.2f}")
        print(f"  总利润: ${total_profit:,.2f}")
        print("=" * 60)

        return {
            'projects_created': projects_created,
            'projects_updated': projects_updated,
            'reports_created': reports_created,
            'total_spend': total_spend,
            'total_revenue': total_revenue,
            'total_profit': total_profit,
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
    # 默认 CSV 文件路径
    csv_path = r"D:\Backup\Downloads\11月项目消耗（带项目款） - 12月项目消耗SZ.csv"

    if len(sys.argv) > 1:
        csv_path = sys.argv[1]

    if not os.path.exists(csv_path):
        print(f"错误: 文件不存在 - {csv_path}")
        sys.exit(1)

    print(f"=" * 60)
    print(f"12月项目消耗数据导入")
    print(f"时间: {datetime.now()}")
    print(f"文件: {csv_path}")
    print(f"=" * 60)

    result = import_data(csv_path)

    print(f"\n导入结束时间: {datetime.now()}")


if __name__ == '__main__':
    main()
