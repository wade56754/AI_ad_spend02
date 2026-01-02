#!/usr/bin/env python3
"""
12月消耗汇总数据导入脚本

将 CSV 数据导入到 ad_spend_daily 表
"""

import csv
import os
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation
import uuid
import json

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库连接
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in environment")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def parse_date(date_str: str) -> str:
    """解析日期格式 2025-12-1 -> 2025-12-01，返回 None 表示无效日期"""
    if not date_str:
        return None
    # 跳过非日期文本
    if not date_str[0].isdigit():
        return None
    try:
        parts = date_str.split("-")
        if len(parts) == 3:
            year, month, day = parts
            # 验证是有效数字
            int(year)
            int(month)
            int(day)
            return f"{year}-{int(month):02d}-{int(day):02d}"
    except (ValueError, IndexError):
        pass
    return None


def parse_decimal(value: str) -> Decimal:
    """解析数字，处理空值和特殊格式"""
    if not value or value.strip() == "":
        return Decimal("0.00")
    try:
        # 移除可能的逗号
        clean_value = value.replace(",", "").strip()
        return Decimal(clean_value).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return Decimal("0.00")


def extract_account_id(account_str: str) -> str:
    """从账户名称中提取账户ID"""
    if not account_str:
        return ""
    # 格式: "SONZDD-ADA+7-GX-324  1138647123633445"
    parts = account_str.strip().split()
    if len(parts) >= 2:
        # 取最后一个部分作为 ID
        return parts[-1]
    return account_str


def extract_account_name(account_str: str) -> str:
    """从账户名称中提取名称部分"""
    if not account_str:
        return ""
    parts = account_str.strip().split()
    if len(parts) >= 2:
        return " ".join(parts[:-1])
    return account_str


def import_csv(csv_path: str, dry_run: bool = False):
    """导入 CSV 数据"""

    print(f"\n{'='*60}")
    print(f"开始导入: {csv_path}")
    print(f"模式: {'预览 (dry-run)' if dry_run else '实际导入'}")
    print(f"{'='*60}\n")

    session = Session()

    try:
        # 读取 CSV
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        print(f"读取到 {len(rows)} 行数据\n")

        # 统计
        stats = {"total": len(rows), "imported": 0, "skipped": 0, "errors": []}

        # 检查表是否存在
        result = session.execute(
            text(
                """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'ad_spend_daily'
            )
        """
            )
        )
        table_exists = result.scalar()

        if not table_exists:
            print("ERROR: ad_spend_daily 表不存在!")
            return

        # 处理每一行
        for i, row in enumerate(rows):
            try:
                # 解析日期
                spend_date = parse_date(row.get("日期", ""))
                if not spend_date:
                    stats["skipped"] += 1
                    continue

                # 解析账户
                account_full = row.get("账户名称/ID", "")
                account_code = extract_account_id(account_full)
                account_name = extract_account_name(account_full)

                if not account_code:
                    stats["skipped"] += 1
                    continue

                # 解析消耗金额
                real_spend = parse_decimal(row.get("实际消耗", "0"))

                # 跳过消耗为0或历史消耗
                if real_spend == 0:
                    notes = row.get("备注", "")
                    if "历史消耗" in notes:
                        stats["skipped"] += 1
                        continue

                # 构建原始数据
                raw_payload = {
                    "region": row.get("地区", ""),
                    "pitcher": row.get("投手", ""),
                    "account_name": account_name,
                    "account_type": row.get("账户种类", ""),
                    "agent": row.get("代理商", ""),
                    "today_max": row.get("转点截图Today MAX", ""),
                    "yesterday_max": row.get("转点截图yesterday MAX", ""),
                    "notes": row.get("备注", ""),
                    "fee": row.get("手续费", ""),
                    "spend_with_fee": row.get("包含手续费\n的消耗", "")
                    or row.get("包含手续费的消耗", ""),
                    "opening_fee": row.get("开户费", ""),
                    "source_file": os.path.basename(csv_path),
                    "row_number": i + 2,  # CSV 行号（加表头）
                }

                # 生成 UUID
                record_id = str(uuid.uuid4())

                # 构建 INSERT 语句（简单插入，不处理冲突）
                insert_sql = text(
                    """
                    INSERT INTO ad_spend_daily (
                        id, source_platform, ad_account_code, spend_date,
                        spend_amount, currency, raw_payload, imported_at
                    ) VALUES (
                        :id, :source_platform, :ad_account_code, :spend_date,
                        :spend_amount, :currency, :raw_payload, NOW()
                    )
                """
                )

                params = {
                    "id": record_id,
                    "source_platform": row.get("平台", "FB"),
                    "ad_account_code": account_code,
                    "spend_date": spend_date,
                    "spend_amount": float(real_spend),
                    "currency": "USD",
                    "raw_payload": json.dumps(raw_payload, ensure_ascii=False),
                }

                if dry_run:
                    if i < 5:  # 只显示前5条
                        print(
                            f"[预览] {spend_date} | {account_code} | ${real_spend} | {raw_payload.get('pitcher')}"
                        )
                else:
                    session.execute(insert_sql, params)

                stats["imported"] += 1

            except Exception as e:
                stats["errors"].append(f"行 {i+2}: {str(e)}")
                continue

        if not dry_run:
            session.commit()
            print("\n数据已提交到数据库")

        # 打印统计
        print(f"\n{'='*60}")
        print("导入统计:")
        print(f"  总行数: {stats['total']}")
        print(f"  成功导入: {stats['imported']}")
        print(f"  跳过: {stats['skipped']}")
        print(f"  错误: {len(stats['errors'])}")

        if stats["errors"]:
            print("\n错误详情 (前10条):")
            for err in stats["errors"][:10]:
                print(f"  - {err}")

        print(f"{'='*60}\n")

    except Exception as e:
        session.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        session.close()


def verify_import():
    """验证导入结果"""
    session = Session()
    try:
        # 统计记录数
        result = session.execute(
            text(
                """
            SELECT
                COUNT(*) as total,
                MIN(spend_date) as min_date,
                MAX(spend_date) as max_date,
                SUM(spend_amount) as total_spend,
                COUNT(DISTINCT ad_account_code) as account_count
            FROM ad_spend_daily
            WHERE spend_date >= '2025-12-01' AND spend_date <= '2025-12-31'
        """
            )
        )
        row = result.fetchone()

        print("\n12月消耗数据统计:")
        print(f"  记录数: {row[0]}")
        print(f"  日期范围: {row[1]} ~ {row[2]}")
        print(f"  总消耗: ${row[3]:,.2f}" if row[3] else "  总消耗: $0.00")
        print(f"  账户数: {row[4]}")

        # 按投手统计
        result = session.execute(
            text(
                """
            SELECT
                raw_payload->>'pitcher' as pitcher,
                COUNT(*) as records,
                SUM(spend_amount) as total_spend
            FROM ad_spend_daily
            WHERE spend_date >= '2025-12-01' AND spend_date <= '2025-12-31'
            GROUP BY raw_payload->>'pitcher'
            ORDER BY total_spend DESC
            LIMIT 10
        """
            )
        )

        print("\n按投手统计 (Top 10):")
        for row in result:
            pitcher = row[0] or "Unknown"
            print(f"  {pitcher}: {row[1]} 条记录, ${row[2]:,.2f}")

    finally:
        session.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="导入12月消耗数据")
    parser.add_argument(
        "csv_path",
        nargs="?",
        default="/Users/wade/Downloads/12月消耗汇总-ZZ - 12月消耗汇总表.csv",
        help="CSV 文件路径",
    )
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际导入")
    parser.add_argument("--verify", action="store_true", help="验证导入结果")

    args = parser.parse_args()

    if args.verify:
        verify_import()
    else:
        import_csv(args.csv_path, dry_run=args.dry_run)
        if not args.dry_run:
            verify_import()
