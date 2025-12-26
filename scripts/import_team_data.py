r"""
导入 CSV 团队数据并更新用户 team_id

从投手日报 CSV 提取投手-团队映射关系，更新 users 表的 team_id 字段。

用法:
    python scripts/import_team_data.py <csv_path>

示例:
    python scripts/import_team_data.py "C:\Users\user\Downloads\投手日报.csv"
"""
import csv
import sys
from pathlib import Path
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.core.db import get_db_session
from backend.models.core.user import User
from backend.models.finance.team import Team
from sqlalchemy import select, or_

# 团队名称 -> 团队代码映射
TEAM_CODE_MAP = {
    "深圳团队": "SZ",
    "郑州团队": "ZZ",
    "金边团队": "JB",
}


def extract_pitcher_team_mapping(csv_path: str) -> dict[str, str]:
    """从 CSV 提取投手-团队映射"""
    pitcher_teams = {}

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pitcher = row.get('投手', '').strip()
            team = row.get('所属团队（team）', '').strip()

            if pitcher and team:
                # 如果同一投手有多个团队记录，保留第一个
                if pitcher not in pitcher_teams:
                    pitcher_teams[pitcher] = team

    return pitcher_teams


def main(csv_path: str):
    print(f"\n=== 导入团队数据 ===")
    print(f"CSV 路径: {csv_path}\n")

    # 1. 提取投手-团队映射
    pitcher_teams = extract_pitcher_team_mapping(csv_path)
    print(f"从 CSV 提取 {len(pitcher_teams)} 个投手-团队映射:")

    # 统计每个团队的投手数
    team_counts = defaultdict(list)
    for pitcher, team in pitcher_teams.items():
        team_counts[team].append(pitcher)

    for team, pitchers in sorted(team_counts.items()):
        print(f"  {team}: {len(pitchers)} 人 - {', '.join(pitchers)}")

    print()

    # 2. 数据库操作
    session = get_db_session()
    try:
        # 2.1 获取或创建团队
        team_map = {}  # team_name -> team_id
        unique_teams = set(pitcher_teams.values())

        # 过滤掉无效团队名
        valid_teams = [t for t in unique_teams if t and t != "#N/A"]

        for team_name in valid_teams:
            team_code = TEAM_CODE_MAP.get(team_name, team_name[:2].upper())

            # 先按 code 精确查找
            team = session.execute(
                select(Team).where(Team.code == team_code)
            ).scalar_one_or_none()

            if team:
                print(f"团队已存在: {team_name} (code={team.code}, id={team.id})")
            else:
                team = Team(code=team_code, name=team_name)
                session.add(team)
                session.flush()  # 获取 id
                print(f"创建团队: {team_name} (code={team_code}, id={team.id})")

            team_map[team_name] = team.id

        print()

        # 2.2 更新用户 team_id
        updated_count = 0
        skipped_invalid = 0
        not_found = []

        for pitcher_name, team_name in pitcher_teams.items():
            # 跳过无效团队
            if not team_name or team_name == "#N/A":
                skipped_invalid += 1
                continue

            team_id = team_map.get(team_name)
            if not team_id:
                skipped_invalid += 1
                continue

            # 尝试多种匹配方式：username 或 full_name
            user = session.execute(
                select(User).where(
                    or_(
                        User.username == pitcher_name,
                        User.full_name == pitcher_name
                    )
                )
            ).scalar_one_or_none()

            if user:
                if user.team_id != team_id:
                    old_team = user.team_id
                    user.team_id = team_id
                    updated_count += 1
                    print(f"更新: {pitcher_name} -> {team_name}")
                else:
                    print(f"跳过: {pitcher_name} (已是 {team_name})")
            else:
                not_found.append(pitcher_name)

        # 提交事务
        session.commit()

        print(f"\n=== 结果汇总 ===")
        print(f"更新用户: {updated_count}")
        print(f"跳过无效团队: {skipped_invalid}")
        print(f"未找到用户: {len(not_found)}")

        if not_found:
            print(f"\n未找到的投手 (需手动检查):")
            for name in not_found:
                print(f"  - {name}")

        # 2.3 验证结果
        print(f"\n=== 验证: 各团队用户数 ===")
        from sqlalchemy import func
        for team_name, team_id in team_map.items():
            count = session.execute(
                select(func.count()).select_from(User).where(User.team_id == team_id)
            ).scalar()
            print(f"{team_name}: {count} 人")

    except Exception as e:
        session.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python scripts/import_team_data.py <csv_path>")
        print('示例: python scripts/import_team_data.py "C:\\Users\\user\\Downloads\\投手日报（回复） - 第 1 张表单回复.csv"')
        sys.exit(1)

    csv_path = sys.argv[1]
    if not Path(csv_path).exists():
        print(f"ERROR: 文件不存在: {csv_path}")
        sys.exit(1)

    main(csv_path)
