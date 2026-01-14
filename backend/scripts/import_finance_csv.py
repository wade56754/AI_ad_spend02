"""
收支表 CSV 数据导入脚本

从 CSV 文件导入月度财务数据到数据库：
- 创建/更新项目记录 (projects 表)
- 创建财务交易记录 (ledger_transactions 表)

CSV 列结构:
- 月份: 10月/11月
- 团队: SZ/ZZ
- 业务类型: 自投项目/外部代投
- 地区: 德国/日本/新加坡等
- 项目/代投人名称: 项目名称
- 有效数(粉/人): 转化数
- 总支出/消耗: 成本
- 实际收款: 收入
- 项目毛利: 利润
- 剩余预付款: 预付款余额
- 备注: 备注信息

Usage:
    python scripts/import_finance_csv.py <csv_file_path>
"""

import csv
import sys
import os
from decimal import Decimal, InvalidOperation
from datetime import datetime
import re

# 添加项目根目录到 Python 路径 (backend 的父目录)
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.core.config import get_settings
from backend.models.core.project import Project


def parse_number(value: str) -> Decimal:
    """解析数字，处理逗号分隔和负数"""
    if not value or value == '-' or value == '0':
        return Decimal('0')

    # 移除逗号和空格
    cleaned = value.replace(',', '').replace(' ', '').strip()

    # 处理带引号的数字
    cleaned = cleaned.strip('"').strip("'")

    try:
        return Decimal(cleaned)
    except InvalidOperation:
        print(f"  警告: 无法解析数字 '{value}'，使用 0")
        return Decimal('0')


def parse_month(month_str: str) -> tuple:
    """解析月份，返回 (year, month)"""
    # 假设数据是 2024 年的
    year = 2024

    match = re.search(r'(\d+)月', month_str)
    if match:
        month = int(match.group(1))
        return (year, month)

    return (year, 1)  # 默认 1 月


def import_csv(csv_path: str, db_url: str = None):
    """导入 CSV 数据到数据库"""

    # 获取数据库连接
    if not db_url:
        settings = get_settings()
        db_url = settings.database_url

    print(f"连接数据库: {db_url[:50]}...")
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 读取 CSV 文件
        print(f"\n读取 CSV 文件: {csv_path}")
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        print(f"共读取 {len(rows)} 行数据")

        # 过滤空行
        valid_rows = [r for r in rows if r.get('月份') and r.get('项目/代投人名称')]
        print(f"有效数据行: {len(valid_rows)} 行")

        # 统计
        projects_created = 0
        projects_updated = 0
        total_revenue = Decimal('0')
        total_spend = Decimal('0')

        for i, row in enumerate(valid_rows):
            month_str = row.get('月份', '').strip()
            team = row.get('团队', '').strip()
            business_type = row.get('业务类型', '').strip()
            region = row.get('地区', '').strip()
            project_name = row.get('项目/代投人名称', '').strip()
            conversions = parse_number(row.get('有效数(粉/人)', '0'))
            spend = parse_number(row.get('总支出/消耗', '0'))
            revenue = parse_number(row.get('实际收款', '0'))
            profit = parse_number(row.get('项目毛利', '0'))
            prepayment = parse_number(row.get('剩余预付款', '0'))
            notes = row.get('备注', '').strip()

            if not project_name:
                continue

            print(f"\n[{i+1}] 处理: {month_str} - {project_name} ({region})")
            print(f"    消耗: ¥{spend}, 收入: ¥{revenue}, 利润: ¥{profit}")

            # 查找或创建项目
            project = session.query(Project).filter(
                Project.name == project_name
            ).first()

            if not project:
                # 计算单价 (收入 / 进粉数)
                unit_price = Decimal('0')
                if conversions > 0 and revenue > 0:
                    unit_price = revenue / conversions

                # 创建新项目
                project = Project(
                    name=project_name,
                    client_name=project_name,  # 使用项目名称作为客户名称
                    client_company=team,  # 使用团队名称作为客户公司
                    description=f"团队: {team}, 业务类型: {business_type}",
                    region=region,
                    status='active',
                    currency='CNY',
                    unit_price=unit_price,
                )
                session.add(project)
                session.flush()  # 获取 ID
                projects_created += 1
                print(f"    创建项目: ID={project.id}, 单价=¥{unit_price:.2f}")
            else:
                # 更新项目信息
                if not project.region and region:
                    project.region = region
                projects_updated += 1
                print(f"    已存在项目: ID={project.id}")

            # 解析月份
            year, month = parse_month(month_str)
            period_start = datetime(year, month, 1)

            # 累计统计
            total_revenue += revenue
            total_spend += spend
            print(f"    收入: ¥{revenue}, 支出: ¥{spend}")

        # 提交事务
        print("\n\n提交数据库事务...")
        session.commit()

        print("\n" + "=" * 50)
        print("导入完成!")
        print(f"  新建项目: {projects_created}")
        print(f"  更新项目: {projects_updated}")
        print(f"  总收入: ¥{total_revenue:,.2f}")
        print(f"  总支出: ¥{total_spend:,.2f}")
        print(f"  总利润: ¥{(total_revenue - total_spend):,.2f}")
        print("=" * 50)

    except Exception as e:
        print(f"\n错误: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def main():
    """主函数"""
    if len(sys.argv) < 2:
        # 默认使用指定的 CSV 文件
        csv_path = r"d:\Backup\Downloads\收支表 - 明细表 (1).csv"
    else:
        csv_path = sys.argv[1]

    if not os.path.exists(csv_path):
        print(f"错误: 文件不存在 - {csv_path}")
        sys.exit(1)

    # 设置日志文件
    log_file = os.path.join(os.path.dirname(__file__), 'import_log.txt')
    sys.stdout = open(log_file, 'w', encoding='utf-8')
    print(f"导入开始时间: {datetime.now()}")

    try:
        import_csv(csv_path)
    except Exception as e:
        print(f"\n导入失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"\n导入结束时间: {datetime.now()}")
        sys.stdout.close()


if __name__ == '__main__':
    main()
