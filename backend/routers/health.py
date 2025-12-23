"""
健康检查路由
Version: 1.1
Author: Claude Code
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload

from backend.core.response import success_response
from backend.core.db import get_db

router = APIRouter(tags=["health"])


@router.get("/debug-daily-report")
async def debug_daily_report(db: Session = Depends(get_db)):
    """调试日报响应格式（无需认证）"""
    from backend.models import DailyReport
    from backend.models.accounts.ad_account import AdAccount
    from backend.schemas.daily_report import DailyReportResponse

    # 获取一条有团队关联的日报
    report = db.query(DailyReport).options(
        joinedload(DailyReport.ad_account).joinedload(AdAccount.team),
        joinedload(DailyReport.submitter)
    ).join(DailyReport.ad_account).filter(
        AdAccount.team_id.isnot(None)
    ).first()

    if not report:
        return {"error": "没有找到有团队关联的日报"}

    # 计算字段
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

    # 创建响应
    resp = DailyReportResponse.model_validate(report)
    resp = resp.model_copy(update={
        'submitter_name': submitter_name,
        'team_name': team_name
    })

    return {
        "raw_data": {
            "report_id": report.id,
            "ad_account_name": report.ad_account.name if report.ad_account else None,
            "team_name_from_db": report.ad_account.team.name if report.ad_account and report.ad_account.team else None,
            "computed_submitter_name": submitter_name,
            "computed_team_name": team_name,
        },
        "response_fields": {
            "submitter_name": resp.submitter_name,
            "team_name": resp.team_name,
        },
        "full_response_dump": resp.model_dump()
    }


@router.get("/health")
async def health_check() -> JSONResponse:
    """
    API 健康检查端点

    返回服务状态和时间戳
    """
    return success_response(
        data={
            "status": "ok",
            "service": "ai-ad-spend-backend",
            "version": "v2.1",
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        },
        message="Health check passed"
    )
