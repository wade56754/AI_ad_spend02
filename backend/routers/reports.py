from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.error_codes import ErrorCode
from backend.core.response import fail, ok
from backend.core.security import AuthenticatedUser, get_current_user
from backend.models import AdAccount, AdSpendDaily, Ledger, Project, Reconciliation
from backend.services.log_service import LogService

router = APIRouter(prefix="/reports", tags=["reports"])


def _date_filter(query, column, start: Optional[date], end: Optional[date]):
    if start:
        query = query.filter(column >= start)
    if end:
        query = query.filter(column <= end)
    return query


class ReportRequestPayload(BaseModel):
    start: Optional[date] = None
    end: Optional[date] = None
    project_id: Optional[UUID] = None


def _collect_performance(
    db: Session, start: Optional[date], end: Optional[date], project_id: Optional[UUID] = None
):
    query = (
        db.query(
            Project.id.label("project_id"),
            Project.name.label("project_name"),
            func.coalesce(func.sum(AdSpendDaily.spend), 0).label("total_spend"),
            func.coalesce(func.sum(AdSpendDaily.leads_count), 0).label("total_leads"),
        )
        .join(AdAccount, AdAccount.project_id == Project.id)
        .join(AdSpendDaily, AdSpendDaily.ad_account_id == AdAccount.id)
        .group_by(Project.id, Project.name)
    )
    if project_id:
        query = query.filter(Project.id == project_id)
    query = _date_filter(query, AdSpendDaily.date, start, end)
    return query.all()


def _collect_profit(
    db: Session, start: Optional[date], end: Optional[date], project_id: Optional[UUID] = None
):
    query = (
        db.query(
            Project.id.label("project_id"),
            Project.name.label("project_name"),
            func.coalesce(func.sum(Ledger.amount), 0).label("ledger_amount"),
            func.coalesce(func.sum(AdSpendDaily.spend), 0).label("spend_amount"),
        )
        .join(AdAccount, AdAccount.project_id == Project.id)
        .join(AdSpendDaily, AdSpendDaily.ad_account_id == AdAccount.id)
        .join(Reconciliation, Reconciliation.daily_spend_id == AdSpendDaily.id)
        .join(Ledger, Ledger.id == Reconciliation.finance_txn_id)
        .filter(Reconciliation.status == "matched")
        .group_by(Project.id, Project.name)
    )
    if project_id:
        query = query.filter(Project.id == project_id)
    query = _date_filter(query, AdSpendDaily.date, start, end)
    return query.all()


def _merge_report_rows(perf_rows, profit_rows):
    summary: Dict[UUID, Dict[str, Any]] = {}

    for row in perf_rows:
        summary[row.project_id] = {
            "project_id": row.project_id,
            "project_name": row.project_name,
            "total_spend": Decimal(row.total_spend or 0),
            "matched_spend": Decimal("0"),
            "leads": int(row.total_leads or 0),
            "finance": Decimal("0"),
        }

    for row in profit_rows:
        entry = summary.get(row.project_id)
        if entry is None:
            entry = {
                "project_id": row.project_id,
                "project_name": row.project_name,
                "total_spend": Decimal(row.spend_amount or 0),
                "matched_spend": Decimal(row.spend_amount or 0),
                "leads": 0,
                "finance": Decimal("0"),
            }
            summary[row.project_id] = entry
        entry["finance"] = Decimal(row.ledger_amount or 0)
        entry["matched_spend"] = Decimal(row.spend_amount or 0)
        if "total_spend" not in entry or entry["total_spend"] == Decimal("0"):
            entry["total_spend"] = Decimal(row.spend_amount or 0)

    results = []
    for entry in summary.values():
        total_spend = entry["total_spend"]
        matched_spend = entry["matched_spend"]
        finance = entry["finance"]
        profit = finance - matched_spend
        results.append(
            {
                "project_id": str(entry["project_id"]),
                "project_name": entry["project_name"],
                "total_spend": str(total_spend.quantize(Decimal("0.01"))),
                "total_leads": entry["leads"],
                "finance_amount": str(finance.quantize(Decimal("0.01"))),
                "profit": str(profit.quantize(Decimal("0.01"))),
            }
        )
    results.sort(key=lambda item: item["project_name"])
    return results


@router.get("", response_model=dict)
def report_summary(
    start: Optional[date] = Query(None, description="起始日期（包含）"),
    end: Optional[date] = Query(None, description="结束日期（包含）"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    perf_rows = _collect_performance(db, start, end)
    profit_rows = _collect_profit(db, start, end)
    data = _merge_report_rows(perf_rows, profit_rows)
    return ok(data=data)


@router.post("", response_model=dict, status_code=200)
def create_report_snapshot(
    payload: ReportRequestPayload,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    perf_rows = _collect_performance(db, payload.start, payload.end, payload.project_id)
    profit_rows = _collect_profit(db, payload.start, payload.end, payload.project_id)
    data = _merge_report_rows(perf_rows, profit_rows)
    LogService.write(
        db,
        action="generate_report_snapshot",
        operator_id=current_user.id,
        target="reports",
        target_id=None,
        detail={
            "project_id": str(payload.project_id) if payload.project_id else None,
            "start": payload.start.isoformat() if payload.start else None,
            "end": payload.end.isoformat() if payload.end else None,
            "records": len(data),
        },
    )
    return ok(data=data)


@router.get("/performance", response_model=dict)
def report_performance(
    start: Optional[date] = Query(None, description="起始日期（包含）"),
    end: Optional[date] = Query(None, description="结束日期（包含）"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    query = (
        db.query(
            Project.id.label("project_id"),
            Project.name.label("project_name"),
            func.coalesce(func.sum(AdSpendDaily.spend), 0).label("total_spend"),
            func.coalesce(func.sum(AdSpendDaily.leads_count), 0).label("total_leads"),
        )
        .join(AdAccount, AdAccount.project_id == Project.id)
        .join(AdSpendDaily, AdSpendDaily.ad_account_id == AdAccount.id)
        .group_by(Project.id, Project.name)
    )
    query = _date_filter(query, AdSpendDaily.date, start, end)

    results = query.all()
    data = [
        {
            "project_id": str(row.project_id),
            "project_name": row.project_name,
            "total_spend": str(Decimal(row.total_spend or 0).quantize(Decimal("0.01"))),
            "total_leads": int(row.total_leads or 0),
        }
        for row in results
    ]

    return ok(data=data)


@router.get("/profit", response_model=dict)
def report_profit(
    start: Optional[date] = Query(None, description="起始日期（包含）"),
    end: Optional[date] = Query(None, description="结束日期（包含）"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    query = (
        db.query(
            Project.id.label("project_id"),
            Project.name.label("project_name"),
            func.coalesce(func.sum(Ledger.amount), 0).label("ledger_amount"),
            func.coalesce(func.sum(AdSpendDaily.spend), 0).label("spend_amount"),
        )
        .join(AdAccount, AdAccount.project_id == Project.id)
        .join(AdSpendDaily, AdSpendDaily.ad_account_id == AdAccount.id)
        .join(Reconciliation, Reconciliation.daily_spend_id == AdSpendDaily.id)
        .join(Ledger, Ledger.id == Reconciliation.finance_txn_id)
        .filter(Reconciliation.status == "matched")
        .group_by(Project.id, Project.name)
    )

    query = _date_filter(query, AdSpendDaily.date, start, end)

    results = query.all()
    data = []
    for row in results:
        spend = Decimal(row.spend_amount or 0)
        ledger_value = Decimal(row.ledger_amount or 0)
        profit = ledger_value - spend
        data.append(
            {
                "project_id": str(row.project_id),
                "project_name": row.project_name,
                "spend": str(spend.quantize(Decimal("0.01"))),
                "finance_amount": str(ledger_value.quantize(Decimal("0.01"))),
                "profit": str(profit.quantize(Decimal("0.01"))),
            }
        )

    return ok(data=data)


@router.get("/{project_id}", response_model=dict)
def report_detail(
    project_id: UUID,
    start: Optional[date] = Query(None, description="起始日期（包含）"),
    end: Optional[date] = Query(None, description="结束日期（包含）"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    perf_rows = _collect_performance(db, start, end, project_id)
    profit_rows = _collect_profit(db, start, end, project_id)
    data = _merge_report_rows(perf_rows, profit_rows)
    if not data:
        return fail(code=ErrorCode.INVALID_PARAM, message="指定项目暂无报表数据", status_code=404)
    return ok(data=data[0])
