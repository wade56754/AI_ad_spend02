import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')
from sqlalchemy import text
from backend.core.db import get_db_session

db = get_db_session()
result = db.execute(text('''
    SELECT dr.id, dr.report_date, a.name, t.name as team
    FROM daily_reports dr
    JOIN ad_accounts a ON dr.ad_account_id = a.id
    LEFT JOIN teams t ON a.team_id = t.id
    WHERE t.id IS NOT NULL
    ORDER BY dr.id DESC
    LIMIT 5
''')).fetchall()

print("有团队关联的日报:")
for r in result:
    parts = r[2].split('_')
    print(f'  日报{r[0]}: 日期={r[1]}, 投手={parts[0]}, 团队={r[3]}')
db.close()
