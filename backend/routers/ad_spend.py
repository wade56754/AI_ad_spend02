import structlog
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4
from math import ceil
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session
from backend.core.db import get_db
from backend.core.error_codes import ErrorCode
from backend.core.response import success_response
from backend.core.security import AuthenticatedUser, get_current_user
from backend.core.logging import log_requests, setup_user_context
from backend.models import AdAccount, AdSpendDaily
from backend.services.log_service import LogService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/adspend", tags=["ad_spend"])

MAX_SPEND = Decimal("10000000")
MAX_LEADS = 1_000_000


class AdSpendReportPayload(BaseModel):
    ad_account_id: UUID
    date: date
    spend: Decimal
    leads: int
    follows: int
    conversions: int
    impressions: Optional[int] = None
    clicks: Optional[int] = None

    @validator("spend")
    def spend_must_be_positive(cls, v):
        if v < 0:
            raise ValueError("spend must be non-negative")
        if v > MAX_SPEND:
            raise ValueError(f"spend exceeds maximum allowed amount of {MAX_SPEND}")
        return v

    @validator("leads")
    def leads_must_be_positive(cls, v):
        if v < 0:
            raise ValueError("leads must be non-negative")
        if v > MAX_LEADS:
            raise ValueError(f"leads exceeds maximum allowed amount of {MAX_LEADS}")
        return v

    @validator("follows", "conversions")
    def non_negative_int(cls, v):
        if v < 0:
            raise ValueError("value must be non-negative")
        return v


def _serialize_report(report: AdSpendDaily) -> dict:
    return {
        "id": str(report.id),
        "ad_account_id": str(report.ad_account_id),
        "date": report.date.isoformat(),
        "spend": float(report.spend),
        "leads": report.leads,
        "follows": report.follows,
        "conversions": report.conversions,
        "impressions": report.impressions,
        "clicks": report.clicks,
        "created_at": report.created_at.isoformat() if report.created_at else None,
    }


@router.get("/reports", response_model=dict)
@log_requests("ad_spend")
def list_ad_spend_reports(
    ad_account_id: Optional[UUID] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(AdSpendDaily)

    if ad_account_id:
        query = query.filter(AdSpendDaily.ad_account_id == ad_account_id)
    if date_from:
        query = query.filter(AdSpendDaily.date >= date_from)
    if date_to:
        query = query.filter(AdSpendDaily.date <= date_to)

    total = query.count()
    pagination = {
        "page": page,
        "size": size,
        "total": total,
        "total_pages": ceil(total / size),
        "has_next": page * size < total,
        "has_prev": page > 1,
    }

    records = query.offset((page - 1) * size).limit(size).all()
    data = [_serialize_report(record) for record in records]

    return success_response(data=data, meta={"pagination": pagination})


@router.get("/reports/{report_id}", response_model=dict)
@log_requests("ad_spend")
def get_ad_spend_report(
    report_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(AdSpendDaily).filter(AdSpendDaily.id == report_id).first()
    if record is None:
        logger.warning(f"日报记录不存在: report_id={report_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": ErrorCode.INVALID_PARAM,
                "message": "日报记录不存在"
            }
        )
    return success_response(data=_serialize_report(record))


@router.post("/report", response_model=dict, status_code=status.HTTP_201_CREATED)
@log_requests("ad_spend")
def create_ad_spend_report(
    payload: AdSpendReportPayload,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        actor_id = UUID(str(current_user.id))
    except (TypeError, ValueError):
        logger.error(f"用户缺少有效ID: user_id={current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": ErrorCode.INVALID_PARAM,
                "message": "当前用户缺少有效 ID"
            }
        )

    logger.info(f"查找广告账户: ad_account_id={payload.ad_account_id}")
    account = db.query(AdAccount).filter(AdAccount.id == payload.ad_account_id).first()
    if account is None:
        logger.warning(f"广告账户不存在: ad_account_id={payload.ad_account_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": ErrorCode.INVALID_PARAM,
                "message": "广告账户不存在"
            }
        )

    exists = (
        db.query(AdSpendDaily)
        .filter(
            AdSpendDaily.ad_account_id == payload.ad_account_id,
            AdSpendDaily.date == payload.date,
        )
        .first()
    )
    if exists:
        logger.warning(f"日报已存在: ad_account_id={payload.ad_account_id}, date={payload.date}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": ErrorCode.INVALID_STATUS,
                "message": "同一广告账户该日期的日报已存在"
            }
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

    try:
        record = AdSpendDaily(
            id=uuid4(),
            ad_account_id=payload.ad_account_id,
            date=payload.date,
            spend=payload.spend,
            leads=payload.leads,
            follows=payload.follows,
            conversions=payload.conversions,
            impressions=payload.impressions,
            clicks=payload.clicks,
            previous_balance=previous.balance if previous else Decimal("0"),
            balance=(previous.balance if previous else Decimal("0")) + payload.spend,
        )

        db.add(record)
        db.commit()

        # 记录日志
        LogService.write(
            db,
            action="create_ad_spend",
            operator_id=str(actor_id),
            target="ad_spend_daily",
            detail={"payload": jsonable_encoder(payload), "record_id": str(record.id)},
            target_id=record.id,
        )

        logger.info(f"广告消耗日报创建成功: record_id={record.id}")

    except Exception as e:
        db.rollback()
        logger.error(f"创建广告消耗日报失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "创建日报失败"
            }
        )

    serialized = _serialize_report(record)
    return success_response(data=serialized, status_code=status.HTTP_201_CREATED)