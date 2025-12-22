"""
投手日报 Excel 数据导入脚本

将 Excel 文件 `投手日报（回复）.xlsx` 导入到数据库 daily_reports 表
"""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import re

# Excel 文件路径
EXCEL_FILE = r'C:\Users\user\Downloads\投手日报（回复）.xlsx'

# 数据库连接 - 从环境变量或配置文件读取
# 使用 Supabase PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL', '')

# 如果没有环境变量，尝试从 .env 文件读取
if not DATABASE_URL:
    env_file = os.path.join(os.path.dirname(__file__), 'backend', '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('DATABASE_URL='):
                    DATABASE_URL = line.split('=', 1)[1].strip().strip('"\'')
                    break

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


def read_excel_data():
    """读取 Excel 数据"""
    print(f"正在读取 Excel 文件: {EXCEL_FILE}")

    # 读取主数据表
    df = pd.read_excel(EXCEL_FILE, sheet_name='第 1 张表单回复')

    print(f"读取到 {len(df)} 条记录")
    print(f"列名: {list(df.columns)}")

    return df


def get_or_create_ad_account(session, account_name, platform):
    """获取或创建广告账户（简化版，使用默认项目）"""
    # 查找是否存在同名账户
    result = session.execute(
        text("SELECT id FROM ad_accounts WHERE name = :name LIMIT 1"),
        {"name": account_name}
    ).fetchone()

    if result:
        return result[0]

    # 查找默认项目
    project_result = session.execute(
        text("SELECT id FROM projects LIMIT 1")
    ).fetchone()

    if not project_result:
        # 创建默认项目
        session.execute(
            text("""
                INSERT INTO projects (name, status, created_at, updated_at)
                VALUES ('默认项目', 'active', NOW(), NOW())
                RETURNING id
            """)
        )
        project_result = session.execute(text("SELECT id FROM projects ORDER BY id DESC LIMIT 1")).fetchone()

    project_id = project_result[0]

    # 创建广告账户
    session.execute(
        text("""
            INSERT INTO ad_accounts (name, platform, project_id, status, created_at, updated_at)
            VALUES (:name, :platform, :project_id, 'active', NOW(), NOW())
        """),
        {"name": account_name, "platform": platform or 'FB', "project_id": project_id}
    )
    session.commit()

    result = session.execute(
        text("SELECT id FROM ad_accounts WHERE name = :name ORDER BY id DESC LIMIT 1"),
        {"name": account_name}
    ).fetchone()

    return result[0]


def import_data(df, session):
    """导入数据到数据库"""
    success_count = 0
    error_count = 0
    errors = []

    # 缓存账户 ID
    account_cache = {}

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
                    session, account_name, platform
                )
            ad_account_id = account_cache[cache_key]

            # 检查是否已存在相同日期和账户的记录
            existing = session.execute(
                text("""
                    SELECT id FROM daily_reports
                    WHERE report_date = :report_date AND ad_account_id = :ad_account_id
                """),
                {"report_date": report_date, "ad_account_id": ad_account_id}
            ).fetchone()

            if existing:
                # 更新现有记录
                session.execute(
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
                session.execute(
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
                session.commit()
                print(f"已处理 {success_count} 条记录...")

        except Exception as e:
            error_count += 1
            errors.append(f"行 {idx + 2}: {str(e)}")
            if error_count <= 10:
                print(f"错误 (行 {idx + 2}): {e}")

    # 最终提交
    session.commit()

    return success_count, error_count, errors


def main():
    """主函数"""
    print("=" * 60)
    print("投手日报数据导入工具")
    print("=" * 60)

    # 检查数据库连接
    if not DATABASE_URL:
        print("错误: 未找到 DATABASE_URL 环境变量")
        print("请设置 DATABASE_URL 或在 backend/.env 文件中配置")
        return

    print(f"数据库连接: {DATABASE_URL[:50]}...")

    # 检查 Excel 文件
    if not os.path.exists(EXCEL_FILE):
        print(f"错误: Excel 文件不存在: {EXCEL_FILE}")
        return

    try:
        # 读取 Excel 数据
        df = read_excel_data()

        # 创建数据库连接
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()

        print("\n开始导入数据...")

        # 导入数据
        success, errors, error_details = import_data(df, session)

        print("\n" + "=" * 60)
        print("导入完成!")
        print(f"成功: {success} 条")
        print(f"失败: {errors} 条")

        if error_details and len(error_details) <= 20:
            print("\n错误详情:")
            for err in error_details[:20]:
                print(f"  - {err}")

        session.close()

    except Exception as e:
        print(f"导入失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
