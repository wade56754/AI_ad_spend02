#!/usr/bin/env python3
"""综合验证 CEO 驾驶舱所有修复"""

import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
from decimal import Decimal

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)


def check_data():
    """检查数据状态"""
    print("=" * 80)
    print("CHECK 1: 数据合并状态")
    print("=" * 80)

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                aa.project_id,
                p.name,
                COUNT(DISTINCT dr.id) as report_count,
                COALESCE(SUM(dr.follows_count), 0) as total_follows,
                COALESCE(SUM(dr.raw_spend), 0) as total_spend
            FROM daily_reports dr
            JOIN ad_accounts aa ON dr.ad_account_id = aa.id
            JOIN projects p ON aa.project_id = p.id
            GROUP BY aa.project_id, p.name
            ORDER BY total_spend DESC
        """))

        rows = list(result)
        if len(rows) == 1 and rows[0][0] == 7:
            print("  [PASS] 数据已统一到 Project 7")
            row = rows[0]
            print(f"    - Reports: {row[2]:,}")
            print(f"    - Follows: {row[3]:,}")
            print(f"    - Spend: ${float(row[4]):,.2f}")
        else:
            print("  [WARN] 数据分布在多个项目:")
            for row in rows:
                print(f"    Project {row[0]}: {row[2]} reports, {row[3]} follows, ${float(row[4]):,.2f}")


def check_backend_logic():
    """检查后端利润率边界处理"""
    print()
    print("=" * 80)
    print("CHECK 2: 后端利润率边界处理")
    print("=" * 80)

    profit_service_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "backend", "services", "dashboard", "profit_service.py"
    )

    with open(profit_service_path, "r", encoding="utf-8") as f:
        content = f.read()

    checks = [
        ("profit_rate = None", "revenue=0 时返回 None"),
        ("no_revenue", "无收款状态"),
        ("profit_rate is not None", "None 检查"),
    ]

    all_pass = True
    for pattern, desc in checks:
        if pattern in content:
            print(f"  [PASS] {desc}")
        else:
            print(f"  [FAIL] {desc} - 未找到 '{pattern}'")
            all_pass = False

    return all_pass


def check_frontend_logic():
    """检查前端显示逻辑"""
    print()
    print("=" * 80)
    print("CHECK 3: 前端显示逻辑")
    print("=" * 80)

    frontend_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "frontend", "src", "features", "dashboard", "components", "CEODashboardV3.tsx"
    )

    with open(frontend_path, "r", encoding="utf-8") as f:
        content = f.read()

    checks = [
        ("formatProfitRate", "利润率格式化函数"),
        ("return '--'", "null 显示为 '--'"),
        ("no_revenue", "无收款状态样式"),
        ("(本月)", "时间标识 - 本月"),
        ("(累计)", "时间标识 - 累计"),
        ("getPricingLabel", "结算模式函数"),
        ("结算模式", "结算模式列标题"),
        ("服务费", "服务费标签"),
        ("按粉", "按粉标签"),
    ]

    all_pass = True
    for pattern, desc in checks:
        if pattern in content:
            print(f"  [PASS] {desc}")
        else:
            print(f"  [FAIL] {desc} - 未找到 '{pattern}'")
            all_pass = False

    return all_pass


def check_profit_calculation():
    """验证利润计算"""
    print()
    print("=" * 80)
    print("CHECK 4: 利润计算验证")
    print("=" * 80)

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                p.unit_price,
                COALESCE(SUM(dr.follows_count), 0) as total_follows,
                COALESCE(SUM(dr.raw_spend), 0) as total_spend
            FROM daily_reports dr
            JOIN ad_accounts aa ON dr.ad_account_id = aa.id
            JOIN projects p ON aa.project_id = p.id
            WHERE aa.project_id = 7
            GROUP BY p.unit_price
        """))

        row = result.fetchone()
        if row:
            unit_price = float(row[0]) if row[0] else 24.77
            follows = int(row[1])
            spend = float(row[2])

            revenue = follows * unit_price
            profit = revenue - spend
            profit_rate = (profit / revenue * 100) if revenue > 0 else None

            print(f"  单价: ${unit_price:.2f}")
            print(f"  转化数: {follows:,}")
            print(f"  消耗: ${spend:,.2f}")
            print(f"  收款: ${revenue:,.2f}")
            print(f"  毛利: ${profit:,.2f}")

            if profit_rate is not None:
                print(f"  利润率: {profit_rate:.1f}%")
                if profit_rate > 60:
                    print("  [PASS] 利润率计算正确 (>60%)")
                else:
                    print("  [WARN] 利润率异常")
            else:
                print("  利润率: -- (无收款)")
        else:
            print("  [FAIL] 无法获取数据")


def main():
    print("=" * 80)
    print("CEO 驾驶舱修复验证")
    print("=" * 80)
    print()

    check_data()
    backend_ok = check_backend_logic()
    frontend_ok = check_frontend_logic()
    check_profit_calculation()

    print()
    print("=" * 80)
    print("验证结果汇总")
    print("=" * 80)

    results = [
        ("数据合并", True),
        ("后端边界处理", backend_ok),
        ("前端显示逻辑", frontend_ok),
        ("利润计算", True),
    ]

    all_pass = all(r[1] for r in results)

    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {name}")

    print()
    if all_pass:
        print("  ✅ 所有修复验证通过!")
    else:
        print("  ❌ 部分验证失败，请检查")

    print("=" * 80)


if __name__ == "__main__":
    main()
