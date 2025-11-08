import logging
from math import ceil
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.error_codes import ErrorCode
from backend.core.response import fail, ok
from backend.core.security import AuthenticatedUser, get_current_user
from backend.models import AdAccount, AdSpendDaily
from backend.services.log_service import LogService

router = APIRouter(prefix="/adspend", tags=["ad_spend"])

MAX_SPEND = Decimal("10000000")
MAX_LEADS = 1_000_000


class AdSpendReportPayload(BaseModel):
    ad_account_id: UUID
    date: date
    spend: Decimal
    leads_count: int
    note: Optional[str] = None

    @validator("spend")
    def validate_spend(cls, value: Decimal) -> Decimal:
        value = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if value < Decimal("0"):
            raise ValueError("spend must be non-negative")
        if value > MAX_SPEND:
            raise ValueError(f"spend must not exceed {MAX_SPEND}")
        return value

    @validator("leads_count")
    def validate_leads(cls, value: int) -> int:
        if value < 0:
            raise ValueError("leads_count must be non-negative")
        if value > MAX_LEADS:
            raise ValueError(f"leads_count must not exceed {MAX_LEADS}")
        return value


def _calculate_cost_per_lead(spend: Decimal, leads: int) -> Decimal:
    if leads <= 0:
        return Decimal("0")
    return (spend / Decimal(leads)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _detect_anomaly(
    current_spend: Decimal,
    leads_count: int,
    previous: Optional[AdSpendDaily],
) -> Tuple[bool, Optional[str]]:
    if leads_count == 0:
        return True, "LEADS_COUNT_ZERO"
    if previous is None:
        return False, None
    prev_spend = previous.spend or Decimal("0")
    if prev_spend == 0:
        if current_spend > 0:
            return True, "SPEND_PREVIOUS_ZERO"
        return False, None
    change_ratio = (current_spend - prev_spend).copy_abs() / prev_spend.copy_abs()
    if change_ratio > Decimal("0.30"):
        percentage = (change_ratio * Decimal("100")).quantize(Decimal("0.01"))
        return True, f"SPEND_CHANGE_{percentage}%"
    return False, None


def _serialize_report(record: AdSpendDaily) -> Dict[str, Any]:
    return {
        "id": record.id,
        "ad_account_id": record.ad_account_id,
        "date": record.date,
        "spend": record.spend,
        "leads_count": record.leads_count,
        "note": record.note,
        "is_anomaly": record.is_anomaly,
        "anomaly_reason": record.anomaly_reason,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


@router.get("/reports", response_model=dict)
def list_ad_spend_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ad_account_id: Optional[UUID] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(AdSpendDaily)

    if ad_account_id:
        query = query.filter(AdSpendDaily.ad_account_id == ad_account_id)
    if start_date:
        query = query.filter(AdSpendDaily.date >= start_date)
    if end_date:
        query = query.filter(AdSpendDaily.date <= end_date)

    total = query.count()
    records: List[AdSpendDaily] = (
        query.order_by(AdSpendDaily.date.desc(), AdSpendDaily.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    data = [_serialize_report(record) for record in records]
    pagination = {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": ceil(total / page_size) if page_size else 0,
    }
    return ok(data=data, meta={"pagination": pagination})


@router.get("/reports/{report_id}", response_model=dict)
def get_ad_spend_report(
    report_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(AdSpendDaily).filter(AdSpendDaily.id == report_id).first()
    if record is None:
        return fail(ErrorCode.INVALID_PARAM, "日报记录不存在", status_code=status.HTTP_404_NOT_FOUND)
    return ok(data=_serialize_report(record))


@router.post("/report", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_ad_spend_report(
    payload: AdSpendReportPayload,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        actor_id = UUID(str(current_user.id))
    except (TypeError, ValueError):
        return fail(ErrorCode.INVALID_PARAM, "当前用户缺少有效 ID", status_code=status.HTTP_401_UNAUTHORIZED)

    account = db.query(AdAccount).filter(AdAccount.id == payload.ad_account_id).first()
    if account is None:
        return fail(ErrorCode.INVALID_PARAM, "广告账户不存在", status_code=status.HTTP_404_NOT_FOUND)

    exists = (
        db.query(AdSpendDaily)
        .filter(
            AdSpendDaily.ad_account_id == payload.ad_account_id,
            AdSpendDaily.date == payload.date,
        )
        .first()
    )
    if exists:
        return fail(
            ErrorCode.INVALID_STATUS,
            "同一广告账户该日期的日报已存在",
            status_code=status.HTTP_409_CONFLICT,
        )

    previous = (
        db.query(AdSpendDaily)
        .filter(
            AdSpendDaily.ad_account_id == payload.ad_account_id,
            AdSpendDaily.date < payload.date,
        )
        .order_by(AdSpendDaily.date.desc())
        .first()
    )

    spend_amount = payload.spend
    is_anomaly, anomaly_reason = _detect_anomaly(spend_amount, payload.leads_count, previous)
    cost_per_lead = _calculate_cost_per_lead(spend_amount, payload.leads_count)

    record = AdSpendDaily(
        ad_account_id=payload.ad_account_id,
        user_id=actor_id,
        date=payload.date,
        spend=spend_amount,
        leads_count=payload.leads_count,
        cost_per_lead=cost_per_lead,
        is_anomaly=is_anomaly,
        anomaly_reason=anomaly_reason,
        note=payload.note,
        created_by=actor_id,
        updated_by=actor_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    serialized = jsonable_encoder(_serialize_report(record))

    LogService.write(
        db,
        action="create_ad_spend_daily",
        operator_id=current_user.id,
        target="ad_spend_daily",
        target_id=record.id,
        detail=serialized,
    )

    return ok(data=serialized, status_code=status.HTTP_201_CREATED)
