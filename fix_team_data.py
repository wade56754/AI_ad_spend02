"""
修复团队数据脚本

从 Excel 读取团队信息，创建 Team 记录并关联到 AdAccount
"""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Excel 文件路径
EXCEL_FILE = r'C:\Users\user\Downloads\投手日报（回复）.xlsx'

# 数据库连接
DATABASE_URL = os.environ.get('DATABASE_URL', '')
if not DATABASE_URL:
    # 尝试多个 .env 文件位置
    env_files = [
        os.path.join(os.path.dirname(__file__), '.env'),
        os.path.join(os.path.dirname(__file__), 'backend', '.env'),
    ]
    for env_file in env_files:
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('DATABASE_URL='):
                        DATABASE_URL = line.split('=', 1)[1].strip().strip('"\'')
                        break
        if DATABASE_URL:
            break


def main():
    print("=" * 60)
    print("修复团队数据")
    print("=" * 60)

    if not DATABASE_URL:
        print("错误: 未找到 DATABASE_URL")
        return

    # 读取 Excel
    print(f"读取 Excel: {EXCEL_FILE}")
    df = pd.read_excel(EXCEL_FILE, sheet_name='第 1 张表单回复')

    # 找到团队列
    team_col = None
    for col in df.columns:
        if 'team' in col.lower() or '团队' in col:
            team_col = col
            break

    if not team_col:
        print("未找到团队列")
        return

    print(f"团队列: {team_col}")

    # 找到投手列
    buyer_col = None
    for col in df.columns:
        if '投手' in col:
            buyer_col = col
            break

    # 找到平台列
    platform_col = None
    for col in df.columns:
        if '平台' in col.lower():
            platform_col = col
            break

    # 找到地区列
    region_col = None
    for col in df.columns:
        if '地区' in col:
            region_col = col
            break

    print(f"投手列: {buyer_col}, 平台列: {platform_col}, 地区列: {region_col}")

    # 获取唯一团队
    teams = df[team_col].dropna().unique()
    print(f"唯一团队: {list(teams)}")

    # 构建投手->团队的映射
    buyer_team_map = {}
    for _, row in df.iterrows():
        buyer = str(row.get(buyer_col, '')).strip()
        team = str(row.get(team_col, '')).strip()
        # 过滤无效值
        if buyer and team and buyer != 'nan' and team != 'nan' and buyer not in buyer_team_map:
            buyer_team_map[buyer] = team

    print(f"\n投手-团队映射 ({len(buyer_team_map)} 条):")
    for buyer, team in buyer_team_map.items():
        print(f"  {buyer} -> {team}")

    # 连接数据库
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 团队代码映射
        team_code_map = {
            '深圳团队': 'SZ',
            '郑州团队': 'ZZ',
            '金边团队': 'JB',
        }

        # 1. 创建团队
        print("\n创建团队...")
        team_id_map = {}
        for team_name in teams:
            team_name = str(team_name).strip()
            if not team_name or team_name == 'nan':
                continue

            # 检查是否存在
            result = session.execute(
                text("SELECT id FROM teams WHERE name = :name"),
                {"name": team_name}
            ).fetchone()

            if result:
                team_id_map[team_name] = result[0]
                print(f"  团队已存在: {team_name} (ID: {result[0]})")
            else:
                # 生成团队代码
                team_code = team_code_map.get(team_name, team_name[:2].upper())
                # 检查代码是否已存在
                code_result = session.execute(
                    text("SELECT id FROM teams WHERE code = :code"),
                    {"code": team_code}
                ).fetchone()
                if code_result:
                    # 代码已存在，添加数字后缀
                    team_code = f"{team_code}2"

                # 创建团队
                session.execute(
                    text("""
                        INSERT INTO teams (code, name, status, created_at, updated_at)
                        VALUES (:code, :name, 'active', NOW(), NOW())
                    """),
                    {"code": team_code, "name": team_name}
                )
                session.commit()
                result = session.execute(
                    text("SELECT id FROM teams WHERE name = :name"),
                    {"name": team_name}
                ).fetchone()
                team_id_map[team_name] = result[0]
                print(f"  创建团队: {team_name} (代码: {team_code}, ID: {result[0]})")

        # 2. 更新 ad_accounts 的 team_id
        print("\n更新广告账户团队关联...")
        updated_count = 0

        # 获取所有广告账户
        accounts = session.execute(
            text("SELECT id, name, team_id FROM ad_accounts")
        ).fetchall()

        for account_id, account_name, current_team_id in accounts:
            # 从账户名提取投手名 (格式: "投手名_平台_地区")
            parts = account_name.split('_')
            if len(parts) >= 1:
                buyer_name = parts[0]
                if buyer_name in buyer_team_map:
                    team_name = buyer_team_map[buyer_name]
                    if team_name in team_id_map:
                        new_team_id = team_id_map[team_name]
                        if current_team_id != new_team_id:
                            session.execute(
                                text("UPDATE ad_accounts SET team_id = :team_id WHERE id = :id"),
                                {"team_id": new_team_id, "id": account_id}
                            )
                            updated_count += 1
                            print(f"  更新: {account_name} -> {team_name}")

        session.commit()
        print(f"\n完成! 更新了 {updated_count} 个广告账户的团队关联")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    main()
