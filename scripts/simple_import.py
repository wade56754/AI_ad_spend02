"""
简化版 CSV 数据导入脚本

直接将日报数据导入数据库，跳过账户关联
"""

import os
import sys
import csv
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal
from uuid import uuid4
import io

# 修复 Windows 控制台编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.core.config import get_settings

# 配置
CSV_DIR = project_root / "dataset" / "out" / "csv"

# 地区映射
REGION_MAP = {
    "印度": "India", "印度（India）": "India",
    "土耳其": "Turkey", "土耳其(Turkey)": "Turkey",
    "巴西": "Brazil", "意大利": "Italy", "德国": "Germany",
    "英国": "UK", "韩国": "Korea", "法国": "France",
    "马来西亚": "Malaysia", "日本": "Japan",
}

def parse_decimal(value):
    if not value or value.strip() == "":
        return Decimal("0.00")
    try:
        return Decimal(value.replace(",", "").strip())
    except:
        return Decimal("0.00")

def parse_int(value):
    if not value or value.strip() == "":
        return 0
    try:
        return int(float(value.replace(",", "").strip()))
    except:
        return 0

def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value.strip().split(" ")[0], "%Y-%m-%d").date()
    except:
        return None

def normalize_region(region):
    if not region:
        return "Other"
    return REGION_MAP.get(region.strip(), region.strip())

def main():
    print("[INFO] 开始导入日报数据...")

    settings = get_settings()
    engine = create_engine(settings.database_url)

    # 读取 CSV
    csv_file = CSV_DIR / "tou_shou_ri_bao_hui_fu_di_1_zhang_biao_dan_hui_fu.csv"
    if not csv_file.exists():
        print(f"[ERR] 文件不存在: {csv_file}")
        return

    with open(csv_file, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"[INFO] 读取到 {len(rows)} 条记录")
    print(f"[INFO] 列名: {list(rows[0].keys())}")

    # 收集所有投手名称
    pitchers = set()
    for row in rows:
        pitcher = row.get("投手", "").strip()
        if pitcher:
            pitchers.add(pitcher)

    print(f"[INFO] 发现 {len(pitchers)} 个投手")

    # 创建投手用户
    with engine.connect() as conn:
        for pitcher in pitchers:
            user_id = uuid4()
            email = f"{pitcher.lower().replace(' ', '_')}@import.local"

            # 检查是否已存在
            result = conn.execute(
                text("SELECT id FROM users WHERE username = :username"),
                {"username": pitcher}
            )
            existing = result.fetchone()

            if existing:
                print(f"[SKIP] 用户已存在: {pitcher}")
                continue

            # 插入用户
            try:
                conn.execute(
                    text("""
                        INSERT INTO users (id, username, email, role, is_active)
                        VALUES (:id, :username, :email, :role, :is_active)
                    """),
                    {
                        "id": str(user_id),
                        "username": pitcher,
                        "email": email,
                        "role": "media_buyer",
                        "is_active": True
                    }
                )
                conn.commit()
                print(f"[OK] 创建用户: {pitcher}")
            except Exception as e:
                print(f"[ERR] 创建用户失败 {pitcher}: {e}")
                conn.rollback()

    print("[INFO] 用户创建完成")

    # 获取用户 ID 映射
    user_map = {}
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, username FROM users"))
        for row in result:
            user_map[row[1]] = row[0]

    print(f"[INFO] 加载 {len(user_map)} 个用户映射")

    # 获取或创建默认项目
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id FROM projects WHERE name = '导入默认项目' LIMIT 1")
        )
        project_row = result.fetchone()
        if project_row:
            project_id = project_row[0]
            print(f"[INFO] 使用现有项目 ID: {project_id}")
        else:
            result = conn.execute(
                text("""
                    INSERT INTO projects (name, client_name, client_company, status, currency)
                    VALUES ('导入默认项目', '导入数据', '导入公司', 'active', 'USD')
                    RETURNING id
                """)
            )
            conn.commit()
            project_id = result.fetchone()[0]
            print(f"[OK] 创建默认项目 ID: {project_id}")

    # 为每个投手创建单独的 ad_account (避免唯一约束冲突)
    account_map = {}  # pitcher -> account_id
    with engine.connect() as conn:
        for pitcher in pitchers:
            account_code = f"IMP-{pitcher.upper().replace(' ', '_')[:20]}"
            account_name = f"导入账户-{pitcher}"

            # 检查是否已存在
            result = conn.execute(
                text("SELECT id FROM ad_accounts WHERE account_code = :code LIMIT 1"),
                {"code": account_code}
            )
            existing = result.fetchone()

            if existing:
                account_map[pitcher] = existing[0]
                continue

            # 创建新账户
            try:
                result = conn.execute(
                    text("""
                        INSERT INTO ad_accounts (project_id, account_code, name, platform, status, currency)
                        VALUES (:project_id, :account_code, :name, 'FB', 'active', 'USD')
                        RETURNING id
                    """),
                    {
                        "project_id": project_id,
                        "account_code": account_code,
                        "name": account_name
                    }
                )
                conn.commit()
                account_id = result.fetchone()[0]
                account_map[pitcher] = account_id
                print(f"[OK] 创建账户: {pitcher} -> ID {account_id}")
            except Exception as e:
                print(f"[ERR] 创建账户失败 {pitcher}: {e}")
                conn.rollback()

    print(f"[INFO] 加载 {len(account_map)} 个账户映射")

    # 导入日报
    inserted = 0
    skipped = 0
    errors = 0

    with engine.connect() as conn:
        for i, row in enumerate(rows):
            try:
                report_date = parse_date(row.get("日期", ""))
                if not report_date:
                    skipped += 1
                    continue

                pitcher = row.get("投手", "").strip()
                region = normalize_region(row.get("地区", ""))
                platform = row.get("平台", "").strip() or "FB"
                raw_spend = parse_decimal(row.get("广告消耗（AD Spend） 美元(USD)", "0"))
                result_count = parse_int(row.get("成效（result）", "0"))
                follows_count = parse_int(row.get("进粉数（people）", "0"))
                team = row.get("所属团队（team）", "").strip()

                user_id = user_map.get(pitcher)
                account_id = account_map.get(pitcher)

                if not account_id:
                    skipped += 1
                    continue

                # 检查是否已存在 (同日期+同账户)
                result = conn.execute(
                    text("""
                        SELECT id FROM daily_reports
                        WHERE report_date = :date AND ad_account_id = :account_id
                    """),
                    {
                        "date": report_date,
                        "account_id": account_id
                    }
                )
                existing = result.fetchone()

                if existing:
                    skipped += 1
                    continue

                # 插入日报
                conn.execute(
                    text("""
                        INSERT INTO daily_reports (
                            report_date, ad_account_id, region, platform,
                            raw_spend, result_count, follows_count, conversions_raw,
                            status, submitted_by, submitted_at, notes
                        ) VALUES (
                            :report_date, :account_id, :region, :platform,
                            :raw_spend, :result_count, :follows_count, :conversions_raw,
                            'raw_submitted', :submitted_by, NOW(), :notes
                        )
                    """),
                    {
                        "report_date": report_date,
                        "account_id": account_id,
                        "region": region,
                        "platform": platform,
                        "raw_spend": float(raw_spend),
                        "result_count": result_count,
                        "follows_count": follows_count,
                        "conversions_raw": follows_count,
                        "submitted_by": str(user_id) if user_id else None,
                        "notes": f"投手: {pitcher}, 团队: {team}"
                    }
                )
                inserted += 1

                if inserted % 100 == 0:
                    conn.commit()
                    print(f"[INFO] 已导入 {inserted} 条")

            except Exception as e:
                errors += 1
                if errors <= 10:
                    print(f"[ERR] 行 {i+1}: {e}")

        conn.commit()

    print("=" * 60)
    print(f"[INFO] 导入完成:")
    print(f"  插入: {inserted}")
    print(f"  跳过: {skipped}")
    print(f"  错误: {errors}")

if __name__ == "__main__":
    main()
