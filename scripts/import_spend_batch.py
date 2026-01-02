#!/usr/bin/env python3
"""
12月消耗汇总数据批量导入脚本（优化版）
"""

import csv
import os
import sys
from decimal import Decimal, InvalidOperation
import uuid
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)


def parse_date(date_str: str) -> str:
    """解析日期"""
    if not date_str or not date_str[0].isdigit():
        return None
    try:
        parts = date_str.split("-")
        if len(parts) == 3:
            year, month, day = parts
            return f"{int(year)}-{int(month):02d}-{int(day):02d}"
    except:
        pass
    return None


def parse_decimal(value: str) -> float:
    """解析数字"""
    if not value or value.strip() == "":
        return 0.0
    try:
        return float(value.replace(",", "").strip())
    except:
        return 0.0


def extract_account_id(account_str: str) -> str:
    """提取账户ID"""
    if not account_str:
        return ""
    parts = account_str.strip().split()
    return parts[-1] if len(parts) >= 2 else account_str


def extract_account_name(account_str: str) -> str:
    """提取账户名称"""
    if not account_str:
        return ""
    parts = account_str.strip().split()
    return " ".join(parts[:-1]) if len(parts) >= 2 else account_str


def main():
    csv_path = "/Users/wade/Downloads/12月消耗汇总-ZZ - 12月消耗汇总表.csv"

    print(f"读取 CSV: {csv_path}")

    # 读取并过滤数据
    records = []
    skipped = 0

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            spend_date = parse_date(row.get("日期", ""))
            if not spend_date:
                skipped += 1
                continue

            account_full = row.get("账户名称/ID", "")
            account_code = extract_account_id(account_full)
            if not account_code:
                skipped += 1
                continue

            real_spend = parse_decimal(row.get("实际消耗", "0"))
            if real_spend == 0 and "历史消耗" in row.get("备注", ""):
                skipped += 1
                continue

            raw_payload = {
                "region": row.get("地区", ""),
                "pitcher": row.get("投手", ""),
                "account_name": extract_account_name(account_full),
                "account_type": row.get("账户种类", ""),
                "agent": row.get("代理商", ""),
                "fee": row.get("手续费", ""),
                "row": i + 2,
            }

            records.append(
                {
                    "id": str(uuid.uuid4()),
                    "source_platform": row.get("平台", "FB") or "FB",
                    "ad_account_code": account_code,
                    "spend_date": spend_date,
                    "spend_amount": real_spend,
                    "currency": "USD",
                    "raw_payload": json.dumps(raw_payload, ensure_ascii=False),
                }
            )

    print(f"有效记录: {len(records)}, 跳过: {skipped}")

    if not records:
        print("没有有效数据")
        return

    # 批量插入
    print("开始批量插入...")

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

    with engine.begin() as conn:
        # 分批插入，每批 50 条
        batch_size = 50
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            for record in batch:
                conn.execute(insert_sql, record)
            print(f"  已插入 {min(i+batch_size, len(records))}/{len(records)}")

    print("\n导入完成!")

    # 验证
    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
            SELECT COUNT(*), SUM(spend_amount)
            FROM ad_spend_daily
            WHERE spend_date >= '2025-12-01'
        """
            )
        )
        row = result.fetchone()
        print(f"\n统计: {row[0]} 条记录, 总消耗 ${row[1]:,.2f}")

        result = conn.execute(
            text(
                """
            SELECT raw_payload->>'pitcher' as pitcher, COUNT(*), SUM(spend_amount)
            FROM ad_spend_daily
            WHERE spend_date >= '2025-12-01'
            GROUP BY raw_payload->>'pitcher'
            ORDER BY SUM(spend_amount) DESC
        """
            )
        )
        print("\n按投手统计:")
        for row in result:
            print(f"  {row[0]}: {row[1]} 条, ${row[2]:,.2f}")


if __name__ == "__main__":
    main()
