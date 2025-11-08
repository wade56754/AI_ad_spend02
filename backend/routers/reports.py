from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.db import get_db
from models import AdAccount, AdSpendDaily, Channel, Ledger, Project, Topup

router = APIRouter(prefix="/api/reports", tags=["reports"])


def build_response(data: Any, error: Optional[str] = None) -> Dict[str, Any]:
    return {
        "data": data,
        "error": error,
        "meta": {"timestamp": datetime.now(tz=timezone.utc).isoformat()},
    }


@router.get("/performers", response_model=dict)
def performers_report(
    start: datetime = Query(..., description="ISO datetime for report start (inclusive)"),
    end: datetime = Query(..., description="ISO datetime for report end (inclusive)"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if end < start:
        raise HTTPException(status_code=422, detail="end must be greater than start")

    results = (
        db.query(
            AdSpendDaily.user_id.label("user_id"),
            func.sum(AdSpendDaily.spend).label("total_spend"),
            func.sum(AdSpendDaily.leads_count).label("total_leads"),
            func.count(AdSpendDaily.id).label("report_days"),
            func.sum(
                func.case(
                    ((AdSpendDaily.anomaly_flag == True), 1),  # noqa: E712
                    else_=0,
                )
            ).label("anomaly_days"),
        )
        .filter(AdSpendDaily.date >= start.date(), AdSpendDaily.date <= end.date())
        .group_by(AdSpendDaily.user_id)
        .all()
    )

    data = []
    for row in results:
        leads = row.total_leads or 0
        spend = Decimal(row.total_spend or 0)
        cpl = spend / leads if leads else None
        data.append(
            {
                "user_id": str(row.user_id),
                "total_spend": str(spend.quantize(Decimal("0.01"))),
                "total_leads": int(leads),
                "report_days": int(row.report_days or 0),
                "anomaly_days": int(row.anomaly_days or 0),
                "cost_per_lead": str(cpl.quantize(Decimal("0.01"))) if cpl is not None else None,
            }
        )

    return build_response(data=data)


@router.get("/projects", response_model=dict)
def projects_report(
    month: str = Query(..., regex=r"^\d{4}-\d{2}$", description="YYYY-MM for report scope"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    try:
        year, month_value = map(int, month.split("-"))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid month format") from exc

    spend_subquery = (
        db.query(
            AdAccount.project_id.label("project_id"),
            func.sum(AdSpendDaily.spend).label("total_spend"),
            func.sum(AdSpendDaily.leads_count).label("total_leads"),
        )
        .join(AdAccount, AdAccount.id == AdSpendDaily.ad_account_id)
        .filter(
            func.extract("year", AdSpendDaily.date) == year,
            func.extract("month", AdSpendDaily.date) == month_value,
        )
        .group_by(AdAccount.project_id)
        .subquery()
    )

    ledger_subquery = (
        db.query(
            Ledger.project_id.label("project_id"),
            func.sum(
                func.case(
                    ((Ledger.type == "income"), Ledger.amount),
                    else_=-Ledger.amount,
                )
            ).label("net_amount"),
        )
        .filter(
            func.extract("year", Ledger.occurred_at) == year,
            func.extract("month", Ledger.occurred_at) == month_value,
        )
        .group_by(Ledger.project_id)
        .subquery()
    )

    project_rows = (
        db.query(
            Project.id,
            Project.name,
            func.coalesce(spend_subquery.c.total_spend, 0).label("total_spend"),
            func.coalesce(spend_subquery.c.total_leads, 0).label("total_leads"),
            func.coalesce(ledger_subquery.c.net_amount, 0).label("net_amount"),
        )
        .outerjoin(spend_subquery, spend_subquery.c.project_id == Project.id)
        .outerjoin(ledger_subquery, ledger_subquery.c.project_id == Project.id)
        .all()
    )

    data = []
    for row in project_rows:
        spend = Decimal(row.total_spend or 0)
        net_amount = Decimal(row.net_amount or 0)
        profit = net_amount - spend
        leads = int(row.total_leads or 0)
        data.append(
            {
                "project_id": str(row.id),
                "project_name": row.name,
                "total_spend": str(spend.quantize(Decimal("0.01"))),
                "total_leads": leads,
                "net_amount": str(net_amount.quantize(Decimal("0.01"))),
                "profit": str(profit.quantize(Decimal("0.01"))),
            }
        )

    return build_response(data=data)


@router.get("/channels", response_model=dict)
def channels_report(
    month: str = Query(..., regex=r"^\d{4}-\d{2}$", description="YYYY-MM for channel report"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    try:
        year, month_value = map(int, month.split("-"))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid month format") from exc

    spend_subquery = (
        db.query(
            AdAccount.channel_id.label("channel_id"),
            func.sum(AdSpendDaily.spend).label("total_spend"),
            func.count(func.distinct(AdSpendDaily.ad_account_id)).label("account_count"),
        )
        .join(AdAccount, AdAccount.id == AdSpendDaily.ad_account_id)
        .filter(
            func.extract("year", AdSpendDaily.date) == year,
            func.extract("month", AdSpendDaily.date) == month_value,
        )
        .group_by(AdAccount.channel_id)
        .subquery()
    )

    topup_subquery = (
        db.query(
            Topup.channel_id.label("channel_id"),
            func.sum(Topup.amount).label("total_topup"),
            func.sum(func.coalesce(Topup.service_fee_amount, 0)).label("total_fee"),
        )
        .filter(
            func.extract("year", Topup.created_at) == year,
            func.extract("month", Topup.created_at) == month_value,
            Topup.status.in_(["approved", "paid", "done"]),
        )
        .group_by(Topup.channel_id)
        .subquery()
    )

    channel_rows = (
        db.query(
            Channel.id,
            Channel.name,
            func.coalesce(spend_subquery.c.total_spend, 0).label("total_spend"),
            func.coalesce(spend_subquery.c.account_count, 0).label("account_count"),
            func.coalesce(topup_subquery.c.total_topup, 0).label("total_topup"),
            func.coalesce(topup_subquery.c.total_fee, 0).label("total_fee"),
        )
        .outerjoin(spend_subquery, spend_subquery.c.channel_id == Channel.id)
        .outerjoin(topup_subquery, topup_subquery.c.channel_id == Channel.id)
        .all()
    )

    data = []
    for row in channel_rows:
        spend = Decimal(row.total_spend or 0)
        topup_amount = Decimal(row.total_topup or 0)
        service_fee = Decimal(row.total_fee or 0)
        data.append(
            {
                "channel_id": str(row.id),
                "channel_name": row.name,
                "total_spend": str(spend.quantize(Decimal("0.01"))),
                "account_count": int(row.account_count or 0),
                "total_topup": str(topup_amount.quantize(Decimal("0.01"))),
                "service_fee_amount": str(service_fee.quantize(Decimal("0.01"))),
            }
        )

    return build_response(data=data)


