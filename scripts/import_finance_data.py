#!/usr/bin/env python3
"""
财务数据导入脚本

从 TSV 文件导入财务数据到数据库：
1. 收支报表 → ledger_transactions 表
2. 应收未收表 → 更新项目应收账款

使用方法：
    python scripts/import_finance_data.py
"""

import sys
import os
import csv
import re
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置 stdout 编码
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 交易类型常量
TOPUP = "TOPUP"
SPEND = "SPEND"
REFUND = "REFUND"
FEE = "FEE"
ADJUSTMENT = "ADJUSTMENT"
COMPLETED = "completed"


def parse_amount(value: str) -> Decimal:
    """解析金额字符串为 Decimal"""
    if not value or value.strip() in ('', '-', '/'):
        return Decimal('0')

    # 移除货币符号和空格
    clean = value.strip().replace('$', '').replace('¥', '').replace(',', '').replace(' ', '')

    try:
        return Decimal(clean)
    except InvalidOperation:
        return Decimal('0')


def parse_date(date_str: str, year: int = 2025) -> date:
    """解析日期字符串"""
    if not date_str:
        return date.today()

    # 处理 12/1, 12/21 等格式
    match = re.match(r'(\d{1,2})/(\d{1,2})', date_str.strip())
    if match:
        month, day = int(match.group(1)), int(match.group(2))
        return date(year, month, day)

    return date.today()


def generate_transaction_number(tx_type: str, tx_date: date, seq: int) -> str:
    """生成交易流水号"""
    type_code = {
        'TOPUP': 'TP',
        'SPEND': 'SP',
        'REFUND': 'RF',
        'FEE': 'FE',
        'ADJUSTMENT': 'AD',
        'TRANSFER': 'TR',
    }.get(tx_type, 'XX')

    return f"TXN{tx_date.strftime('%Y%m%d')}{type_code}{seq:04d}"


def parse_income_expense_report(filepath: str) -> list[dict]:
    """
    解析收支报表 TSV 文件

    列结构 (基于文件2):
    序号, 日期, 收入项目, 收入金额, 收入备注, 收入时间, 支出项目, 支出金额, 支出备注, 支出时间
    """
    transactions = []

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        rows = list(reader)

    # 跳过标题行，从第7行开始是数据 (索引6)
    seq = 1
    for row in rows[6:]:
        if len(row) < 14:
            continue

        try:
            # 列索引 (根据文件结构)
            # 6: 序号, 7: 日期, 8: 收入项目, 9: 收入金额, 10: 收入备注, 11: 收入时间
            # 12: 支出项目, 13: 支出金额, 14: 支出备注, 15: 支出时间

            row_num = row[6].strip() if len(row) > 6 else ''
            date_str = row[7].strip() if len(row) > 7 else ''

            if not row_num or not row_num.isdigit():
                continue

            tx_date = parse_date(date_str)

            # 收入记录
            income_project = row[8].strip() if len(row) > 8 else ''
            income_amount = parse_amount(row[9]) if len(row) > 9 else Decimal('0')
            income_note = row[10].strip() if len(row) > 10 else ''
            income_time = row[11].strip() if len(row) > 11 else ''

            if income_project and income_amount > 0:
                # 判断交易类型
                if '退款' in income_note or '已退' in income_project:
                    tx_type = REFUND
                elif '结余' in income_project:
                    tx_type = ADJUSTMENT
                else:
                    tx_type = TOPUP

                transactions.append({
                    'transaction_number': generate_transaction_number(tx_type, tx_date, seq),
                    'transaction_type': tx_type,
                    'direction': 'IN',
                    'amount': income_amount,
                    'project_name': income_project,
                    'description': income_note,
                    'transaction_date': tx_date,
                    'transaction_time': income_time,
                    'status': COMPLETED,
                })
                seq += 1

            # 支出记录
            expense_project = row[12].strip() if len(row) > 12 else ''
            expense_amount = parse_amount(row[13]) if len(row) > 13 else Decimal('0')
            expense_note = row[14].strip() if len(row) > 14 else ''
            expense_time = row[15].strip() if len(row) > 15 else ''

            if expense_project and expense_amount > 0:
                # 判断支出类型
                if '后勤' in expense_project or '工资' in expense_note:
                    tx_type = FEE
                elif '广告配套' in expense_project:
                    tx_type = FEE
                else:
                    tx_type = SPEND

                transactions.append({
                    'transaction_number': generate_transaction_number(tx_type, tx_date, seq),
                    'transaction_type': tx_type,
                    'direction': 'OUT',
                    'amount': expense_amount,
                    'project_name': expense_project,
                    'description': expense_note,
                    'transaction_date': tx_date,
                    'transaction_time': expense_time,
                    'status': COMPLETED,
                })
                seq += 1

        except Exception as e:
            print(f"  跳过行: {row[:5]}... 错误: {e}")
            continue

    return transactions


def parse_receivables_report(filepath: str) -> list[dict]:
    """
    解析应收未收表 TSV 文件

    列结构 (基于文件1):
    地区, 项目, 群表格链接, 消耗, 进粉, 单粉成本, 打款, 单粉价格, 应收, 未收, 剩余, 备注
    """
    receivables = []

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        rows = list(reader)

    # 跳过标题行，从第2行开始是数据
    for row in rows[1:30]:  # 只处理前30行有效数据
        if len(row) < 11:
            continue

        try:
            project_name = row[1].strip() if len(row) > 1 else ''
            if not project_name or project_name in ('甲方', ''):
                continue

            spend = parse_amount(row[3]) if len(row) > 3 else Decimal('0')
            payment = parse_amount(row[6]) if len(row) > 6 else Decimal('0')
            receivable = parse_amount(row[8]) if len(row) > 8 else Decimal('0')
            unpaid = parse_amount(row[9]) if len(row) > 9 else Decimal('0')
            remaining = parse_amount(row[10]) if len(row) > 10 else Decimal('0')
            note = row[11].strip() if len(row) > 11 else ''

            if payment > 0 or receivable > 0:
                receivables.append({
                    'project_name': project_name,
                    'total_spend': spend,
                    'total_payment': payment,
                    'total_receivable': receivable,
                    'unpaid': unpaid,
                    'remaining': remaining,
                    'note': note,
                })
        except Exception as e:
            print(f"  跳过行: {row[:3]}... 错误: {e}")
            continue

    return receivables


def import_transactions(session, transactions: list[dict]):
    """导入交易记录到数据库"""
    imported = 0
    skipped = 0

    for tx in transactions:
        # 检查是否已存在
        existing = session.query(LedgerTransaction).filter_by(
            transaction_number=tx['transaction_number']
        ).first()

        if existing:
            skipped += 1
            continue

        # 创建交易记录
        ledger_tx = LedgerTransaction(
            transaction_number=tx['transaction_number'],
            transaction_type=tx['transaction_type'],
            status=tx['status'],
            amount=tx['amount'],
            currency='USD',
            description=f"{tx['project_name']}: {tx['description']}",
            transaction_date=tx['transaction_date'],
            # 这些字段可能需要关联到实际的项目/账户
            project_id=None,
            account_id=None,
        )

        session.add(ledger_tx)
        imported += 1

    return imported, skipped


def print_summary(transactions: list[dict], receivables: list[dict]):
    """打印数据摘要"""
    print("\n" + "=" * 60)
    print("  数据摘要")
    print("=" * 60)

    # 交易统计
    income_total = sum(tx['amount'] for tx in transactions if tx['direction'] == 'IN')
    expense_total = sum(tx['amount'] for tx in transactions if tx['direction'] == 'OUT')

    print(f"\n[收支明细统计]")
    print(f"   总收入: ${income_total:,.2f}")
    print(f"   总支出: ${expense_total:,.2f}")
    print(f"   净额: ${income_total - expense_total:,.2f}")
    print(f"   交易笔数: {len(transactions)}")

    # 按类型统计
    by_type = {}
    for tx in transactions:
        tx_type = tx['transaction_type']
        if tx_type not in by_type:
            by_type[tx_type] = {'count': 0, 'amount': Decimal('0')}
        by_type[tx_type]['count'] += 1
        by_type[tx_type]['amount'] += tx['amount']

    print(f"\n[按类型统计]")
    for tx_type, stats in by_type.items():
        print(f"   {tx_type}: {stats['count']} 笔, ${stats['amount']:,.2f}")

    # 应收统计
    if receivables:
        total_receivable = sum(r['total_receivable'] for r in receivables)
        total_unpaid = sum(r['unpaid'] for r in receivables)

        print(f"\n[应收账款统计]")
        print(f"   项目数: {len(receivables)}")
        print(f"   总应收: ${total_receivable:,.2f}")
        print(f"   未收: ${total_unpaid:,.2f}")

    print("\n" + "=" * 60)


def main():
    """主函数"""
    print("=" * 60)
    print("  财务数据导入工具")
    print("=" * 60)

    # 文件路径
    income_expense_file = r"C:\Users\user\Downloads\公司业务账单 - 2025年12月收支财务报表.tsv"
    receivables_file = r"C:\Users\user\Downloads\12月收支表汇总 - 2025年12月应收未收.tsv"

    # 检查文件存在
    for f in [income_expense_file, receivables_file]:
        if not os.path.exists(f):
            print(f"[ERROR] 文件不存在: {f}")
            return

    print("\n[INFO] 解析收支报表...")
    transactions = parse_income_expense_report(income_expense_file)
    print(f"   找到 {len(transactions)} 条交易记录")

    print("\n[INFO] 解析应收未收表...")
    receivables = parse_receivables_report(receivables_file)
    print(f"   找到 {len(receivables)} 条应收记录")

    # 打印摘要
    print_summary(transactions, receivables)

    # 打印前10条交易明细
    print("\n" + "=" * 60)
    print("  前10条交易明细")
    print("=" * 60)
    for i, tx in enumerate(transactions[:10]):
        direction = "收入" if tx['direction'] == 'IN' else "支出"
        print(f"  {i+1}. [{tx['transaction_date']}] {direction} ${tx['amount']:,.2f} - {tx['project_name']}")

    # 打印应收明细
    print("\n" + "=" * 60)
    print("  应收账款明细")
    print("=" * 60)
    for r in receivables:
        if r['total_payment'] > 0:
            print(f"  - {r['project_name']}: 打款 ${r['total_payment']:,.2f}, 应收 ${r['total_receivable']:,.2f}, 剩余 ${r['remaining']:,.2f}")

    print("\n[INFO] 数据解析完成！")
    print("[INFO] 如需导入数据库，请运行: python scripts/import_to_db.py")


if __name__ == "__main__":
    main()
