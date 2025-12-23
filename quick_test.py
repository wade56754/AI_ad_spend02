# Quick test - connect to DB and check data
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Get DATABASE_URL
DATABASE_URL = None
env_file = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_file):
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('DATABASE_URL='):
                DATABASE_URL = line.split('=', 1)[1].strip().strip('"\'')
                break

if not DATABASE_URL:
    print("No DATABASE_URL found")
    exit(1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Check ad_accounts with team
print("=== 检查广告账户的团队关联 ===")
result = session.execute(text("""
    SELECT a.id, a.name, a.team_id, t.name as team_name
    FROM ad_accounts a
    LEFT JOIN teams t ON a.team_id = t.id
    WHERE a.team_id IS NOT NULL
    LIMIT 5
""")).fetchall()

for row in result:
    print(f"  账户: {row[1]}, 团队ID: {row[2]}, 团队名: {row[3]}")

print("\n=== 检查日报数据 ===")
result = session.execute(text("""
    SELECT dr.id, dr.report_date, a.name as account_name, t.name as team_name
    FROM daily_reports dr
    JOIN ad_accounts a ON dr.ad_account_id = a.id
    LEFT JOIN teams t ON a.team_id = t.id
    ORDER BY dr.id DESC
    LIMIT 5
""")).fetchall()

for row in result:
    account_parts = row[2].split('_') if row[2] else []
    submitter = account_parts[0] if account_parts else None
    print(f"  日报ID: {row[0]}, 日期: {row[1]}, 账户: {row[2]}, 投手: {submitter}, 团队: {row[3]}")

session.close()
