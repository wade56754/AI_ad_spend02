from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.db import get_db
from models import AdAccount, AdSpendDaily, Log
from schemas import AdSpendDailyCreate, AdSpendDailyRead

router = APIRouter(prefix="/api/ad-spend", tags=["ad_spend"])


def build_response(data, error=None):
    return {
        "data": data,
        "error": error,
        "meta": {"timestamp": datetime.now(tz=timezone.utc).isoformat()},
    }


def calculate_cost_per_lead(spend: Decimal, leads: int) -> Decimal:
    if leads <= 0:
        return Decimal("0")
    return (spend / Decimal(leads)).quantize(Decimal("0.01"))


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_ad_spend(payload: AdSpendDailyCreate, db: Session = Depends(get_db)) -> dict:
    account = db.query(AdAccount).filter(AdAccount.id == payload.ad_account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ad account not found")

    existing = (
        db.query(AdSpendDaily)
        .filter(
            AdSpendDaily.ad_account_id == payload.ad_account_id,
            AdSpendDaily.date == payload.date,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Daily report already exists for this account and date",
        )

    spend_record = AdSpendDaily(
        ad_account_id=payload.ad_account_id,
        user_id=payload.user_id,
        date=payload.date,
        spend=payload.spend,
        leads_count=payload.leads_count,
        cost_per_lead=calculate_cost_per_lead(payload.spend, payload.leads_count),
        anomaly_flag=payload.anomaly_flag,
        anomaly_reason=payload.anomaly_reason,
        note=payload.note,
        created_by=payload.created_by or payload.user_id,
        updated_by=payload.updated_by or payload.user_id,
    )
    db.add(spend_record)
    db.flush()

    log_entry = Log(
        actor_id=payload.user_id,
        action="create_ad_spend",
        target_table="ad_spend_daily",
        target_id=spend_record.id,
        before_data=None,
        after_data=jsonable_encoder(AdSpendDailyRead.from_orm(spend_record)),
    )
    db.add(log_entry)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Daily report already exists for this account and date",
        )

    db.refresh(spend_record)

    return build_response(data=AdSpendDailyRead.from_orm(spend_record).dict())


