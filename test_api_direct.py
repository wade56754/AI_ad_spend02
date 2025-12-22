"""直接测试 API 响应"""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 模拟请求通过直接调用 router
from sqlalchemy.orm import Session
from backend.core.db import get_db_session
from backend.services.daily_report_service import DailyReportService
from backend.schemas.daily_report import DailyReportQueryParams, DailyReportResponse
from backend.models import User

# 获取数据库会话
db = get_db_session()

# 获取管理员用户
admin_user = db.query(User).filter(User.email == 'qwc1032217993@gmail.com').first()
if not admin_user:
    print("找不到用户")
    exit(1)

print(f"用户: {admin_user.email}, 角色: {admin_user.role}")

# 获取日报
service = DailyReportService(db)
params = DailyReportQueryParams()
reports, total = service.get_daily_reports(params, admin_user, page=1, page_size=3)

print(f"\n总数: {total}, 返回: {len(reports)}")

for i, report in enumerate(reports[:3]):
    print(f"\n--- 日报 {i+1} (ID: {report.id}) ---")
    print(f"  ad_account: {report.ad_account}")
    print(f"  ad_account.name: {report.ad_account.name if report.ad_account else 'None'}")
    print(f"  ad_account.team: {report.ad_account.team if report.ad_account else 'None'}")
    print(f"  ad_account.team.name: {report.ad_account.team.name if report.ad_account and report.ad_account.team else 'None'}")
    print(f"  submitter: {report.submitter}")

    # 模拟 router 的逻辑
    submitter_name = None
    team_name = None

    if report.submitter:
        submitter_name = report.submitter.username or report.submitter.email
    elif report.ad_account and report.ad_account.name:
        account_parts = report.ad_account.name.split('_')
        if len(account_parts) >= 1:
            submitter_name = account_parts[0]

    if report.ad_account and report.ad_account.team:
        team_name = report.ad_account.team.name

    print(f"  计算的 submitter_name: {submitter_name}")
    print(f"  计算的 team_name: {team_name}")

    # 创建响应对象
    resp = DailyReportResponse.model_validate(report)
    resp = resp.model_copy(update={
        'submitter_name': submitter_name,
        'team_name': team_name
    })

    print(f"  响应 submitter_name: {resp.submitter_name}")
    print(f"  响应 team_name: {resp.team_name}")

    # 检查序列化后的字典
    resp_dict = resp.model_dump()
    print(f"  序列化后 submitter_name: {resp_dict.get('submitter_name')}")
    print(f"  序列化后 team_name: {resp_dict.get('team_name')}")

db.close()
