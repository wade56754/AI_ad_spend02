"""
运行数据库迁移并导入投手日报数据
"""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Excel 文件路径
EXCEL_FILE = r'C:\Users\user\Downloads\投手日报（回复）.xlsx'

# 数据库连接
DATABASE_URL = "postgresql://postgres:dI3YqJj1ZbC3IO4C@db.jzmcoivxhiyidizncyaq.supabase.co:5432/postgres"

# 平台映射
PLATFORM_MAP = {
    'FB': 'FB',
    'Facebook': 'FB',
    'facebook': 'FB',
    'Google': 'Google',
    'google': 'Google',
    'TikTok': 'TikTok',
    'tiktok': 'TikTok',
    'Tiktok': 'TikTok',
}

# 地区映射 (中文 -> 英文)
REGION_MAP = {
    '土耳其': 'Turkey',
    'Turkey': 'Turkey',
    '印度': 'India',
    'India': 'India',
    '意大利': 'Italy',
    'Italy': 'Italy',
    '德国': 'Germany',
    'Germany': 'Germany',
    '巴西': 'Brazil',
    'Brazil': 'Brazil',
    '英国': 'UK',
    'UK': 'UK',
    '韩国': 'Korea',
    'Korea': 'Korea',
    '法国': 'France',
    'France': 'France',
    '马来西亚': 'Malaysia',
    'Malaysia': 'Malaysia',
    '日本': 'Japan',
    'Japan': 'Japan',
    '奥地利': 'Austria',
    'Austria': 'Austria',
    '西班牙': 'Spain',
    'Spain': 'Spain',
    '尼日利亚': 'Nigeria',
    'Nigeria': 'Nigeria',
    '新加坡': 'Singapore',
    'Singapore': 'Singapore',
    '比利时': 'Belgium',
    'Belgium': 'Belgium',
    '瑞典': 'Sweden',
    'Sweden': 'Sweden',
    '加拿大': 'Canada',
    'Canada': 'Canada',
    '印度尼西亚': 'Indonesia',
    'Indonesia': 'Indonesia',
    '美国': 'USA',
    'USA': 'USA',
    '爱尔兰': 'Ireland',
    'Ireland': 'Ireland',
}


def normalize_platform(val):
    """标准化平台名称"""
    if pd.isna(val) or val is None:
        return None
    val_str = str(val).strip()
    return PLATFORM_MAP.get(val_str, 'Other')


def normalize_region(val):
    """标准化地区名称"""
    if pd.isna(val) or val is None:
        return 'Other'
    val_str = str(val).strip()
    return REGION_MAP.get(val_str, 'Other')


def safe_int(val, default=0):
    """安全转换为整数"""
    if pd.isna(val) or val is None:
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def safe_decimal(val, default=Decimal('0.00')):
    """安全转换为 Decimal"""
    if pd.isna(val) or val is None:
        return default
    try:
        return Decimal(str(float(val))).quantize(Decimal('0.01'))
    except (ValueError, TypeError):
        return default


def parse_date(val):
    """解析日期"""
    if pd.isna(val) or val is None:
        return None
    if isinstance(val, (datetime, date)):
        return val.date() if isinstance(val, datetime) else val
    try:
        return pd.to_datetime(val).date()
    except:
        return None


def run_migration(engine):
    """运行数据库迁移 - 添加新字段"""
    print("检查并添加新字段...")

    with engine.connect() as conn:
        # 检查字段是否存在
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'daily_reports' AND column_name = 'region'
        """)).fetchone()

        if not result:
            print("添加 region 字段...")
            conn.execute(text("""
                ALTER TABLE daily_reports
                ADD COLUMN IF NOT EXISTS region VARCHAR(50)
            """))

        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'daily_reports' AND column_name = 'platform'
        """)).fetchone()

        if not result:
            print("添加 platform 字段...")
            conn.execute(text("""
                ALTER TABLE daily_reports
                ADD COLUMN IF NOT EXISTS platform VARCHAR(20)
            """))

        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'daily_reports' AND column_name = 'result_count'
        """)).fetchone()

        if not result:
            print("添加 result_count 字段...")
            conn.execute(text("""
                ALTER TABLE daily_reports
                ADD COLUMN IF NOT EXISTS result_count INTEGER NOT NULL DEFAULT 0
            """))

        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'daily_reports' AND column_name = 'follows_count'
        """)).fetchone()

        if not result:
            print("添加 follows_count 字段...")
            conn.execute(text("""
                ALTER TABLE daily_reports
                ADD COLUMN IF NOT EXISTS follows_count INTEGER NOT NULL DEFAULT 0
            """))

        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'daily_reports' AND column_name = 'currency'
        """)).fetchone()

        if not result:
            print("添加 currency 字段...")
            conn.execute(text("""
                ALTER TABLE daily_reports
                ADD COLUMN IF NOT EXISTS currency VARCHAR(10) NOT NULL DEFAULT 'USD'
            """))

        conn.commit()
        print("数据库迁移完成!")


def get_or_create_ad_account(conn, account_name, platform, media_buyer=None):
    """获取或创建广告账户"""
    # 查找是否存在同名账户
    result = conn.execute(
        text("SELECT id FROM ad_accounts WHERE name = :name LIMIT 1"),
        {"name": account_name}
    ).fetchone()

    if result:
        return result[0]

    # 查找默认项目
    project_result = conn.execute(
        text("SELECT id FROM projects WHERE name = '日报导入项目' LIMIT 1")
    ).fetchone()

    if not project_result:
        # 创建默认项目 - 包含所有必填字段
        conn.execute(
            text("""
                INSERT INTO projects (name, client_name, client_company, status, currency, created_at, updated_at)
                VALUES ('日报导入项目', '导入客户', '导入公司', 'active', 'USD', NOW(), NOW())
            """)
        )
        conn.commit()
        project_result = conn.execute(text("SELECT id FROM projects WHERE name = '日报导入项目' LIMIT 1")).fetchone()

    project_id = project_result[0]

    # 创建广告账户
    conn.execute(
        text("""
            INSERT INTO ad_accounts (name, platform, project_id, status, created_at, updated_at)
            VALUES (:name, :platform, :project_id, 'active', NOW(), NOW())
        """),
        {"name": account_name, "platform": platform or 'FB', "project_id": project_id}
    )
    conn.commit()

    result = conn.execute(
        text("SELECT id FROM ad_accounts WHERE name = :name ORDER BY id DESC LIMIT 1"),
        {"name": account_name}
    ).fetchone()

    return result[0]


def import_data(df, engine):
    """导入数据到数据库"""
    success_count = 0
    error_count = 0
    errors = []

    # 缓存账户 ID
    account_cache = {}

    with engine.connect() as conn:
        for idx, row in df.iterrows():
            try:
                # 解析日期
                report_date = parse_date(row.get('日期'))
                if not report_date:
                    errors.append(f"行 {idx + 2}: 无效日期")
                    error_count += 1
                    continue

                # 解析其他字段
                platform = normalize_platform(row.get('平台'))
                region = normalize_region(row.get('地区'))
                raw_spend = safe_decimal(row.get('广告消耗（AD Spend） 美元(USD) '))
                result_count = safe_int(row.get('成效（result）'))
                follows_count = safe_int(row.get('进粉数（people）'))

                # 获取投手名称作为账户名
                media_buyer = str(row.get('投手', 'Unknown')).strip()
                account_name = f"{media_buyer}_{platform or 'FB'}_{region}"

                # 获取或创建广告账户
                cache_key = account_name
                if cache_key not in account_cache:
                    account_cache[cache_key] = get_or_create_ad_account(
                        conn, account_name, platform
                    )
                ad_account_id = account_cache[cache_key]

                # 检查是否已存在相同日期和账户的记录
                existing = conn.execute(
                    text("""
                        SELECT id FROM daily_reports
                        WHERE report_date = :report_date AND ad_account_id = :ad_account_id
                    """),
                    {"report_date": report_date, "ad_account_id": ad_account_id}
                ).fetchone()

                if existing:
                    # 更新现有记录
                    conn.execute(
                        text("""
                            UPDATE daily_reports SET
                                region = :region,
                                platform = :platform,
                                raw_spend = :raw_spend,
                                result_count = :result_count,
                                follows_count = :follows_count,
                                currency = 'USD',
                                status = 'raw_submitted',
                                updated_at = NOW()
                            WHERE id = :id
                        """),
                        {
                            "id": existing[0],
                            "region": region,
                            "platform": platform,
                            "raw_spend": float(raw_spend),
                            "result_count": result_count,
                            "follows_count": follows_count,
                        }
                    )
                else:
                    # 插入新记录
                    conn.execute(
                        text("""
                            INSERT INTO daily_reports (
                                report_date, ad_account_id, region, platform,
                                raw_spend, result_count, follows_count, currency,
                                status, conversions_raw, impressions, clicks, conversions,
                                new_follows, real_spend, unit_price, trend_flag,
                                created_at, updated_at
                            ) VALUES (
                                :report_date, :ad_account_id, :region, :platform,
                                :raw_spend, :result_count, :follows_count, 'USD',
                                'raw_submitted', 0, 0, 0, 0,
                                0, 0, 0, 'normal',
                                NOW(), NOW()
                            )
                        """),
                        {
                            "report_date": report_date,
                            "ad_account_id": ad_account_id,
                            "region": region,
                            "platform": platform,
                            "raw_spend": float(raw_spend),
                            "result_count": result_count,
                            "follows_count": follows_count,
                        }
                    )

                success_count += 1

                # 每 100 条提交一次
                if success_count % 100 == 0:
                    conn.commit()
                    print(f"已处理 {success_count} 条记录...")

            except Exception as e:
                error_count += 1
                errors.append(f"行 {idx + 2}: {str(e)}")
                if error_count <= 10:
                    print(f"错误 (行 {idx + 2}): {e}")

        # 最终提交
        conn.commit()

    return success_count, error_count, errors


def main():
    """主函数"""
    print("=" * 60)
    print("投手日报数据导入工具")
    print("=" * 60)

    # 检查 Excel 文件
    if not os.path.exists(EXCEL_FILE):
        print(f"错误: Excel 文件不存在: {EXCEL_FILE}")
        return

    try:
        # 创建数据库连接
        print(f"连接数据库...")
        engine = create_engine(DATABASE_URL)

        # 运行迁移
        run_migration(engine)

        # 读取 Excel 数据
        print(f"\n正在读取 Excel 文件: {EXCEL_FILE}")
        df = pd.read_excel(EXCEL_FILE, sheet_name='第 1 张表单回复')
        print(f"读取到 {len(df)} 条记录")

        print("\n开始导入数据...")

        # 导入数据
        success, errors, error_details = import_data(df, engine)

        print("\n" + "=" * 60)
        print("导入完成!")
        print(f"成功: {success} 条")
        print(f"失败: {errors} 条")

        if error_details and len(error_details) <= 20:
            print("\n错误详情:")
            for err in error_details[:20]:
                print(f"  - {err}")

        # 显示统计
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM daily_reports")).fetchone()
            print(f"\n数据库中共有 {result[0]} 条日报记录")

            result = conn.execute(text("SELECT COUNT(*) FROM ad_accounts")).fetchone()
            print(f"数据库中共有 {result[0]} 个广告账户")

    except Exception as e:
        print(f"导入失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
