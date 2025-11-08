from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from core.db import get_db
from models import Channel, Log, Topup
from schemas import (
    TopupApprove,
    TopupCreate,
    TopupConfirm,
    TopupPay,
    TopupRead,
    TopupReject,
)

router = APIRouter(prefix="/api/topups", tags=["topups"])

ALLOWED_TRANSITIONS = {
    "pending": {"approved", "rejected"},
    "approved": {"paid", "rejected"},
    "paid": {"done", "rejected"},
    "done": set(),
    "rejected": set(),
}


def build_response(data, error=None):
    return {
        "data": data,
        "error": error,
        "meta": {"timestamp": datetime.now(tz=timezone.utc).isoformat()},
    }


def calculate_service_fee(amount: Decimal, fee_type: str, fee_value: Decimal) -> Decimal:
    if fee_type == "percent":
        fee = amount * (fee_value / Decimal("100"))
    else:
        fee = fee_value
    return fee.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def ensure_transition(current_status: str, target_status: str) -> None:
    allowed = ALLOWED_TRANSITIONS.get(current_status, set())
    if target_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Status transition from {current_status} to {target_status} is not allowed",
        )


def log_change(
    db: Session,
    actor_id: Optional[UUID],
    target_id: UUID,
    action: str,
    before: Optional[dict],
    after: Optional[dict],
) -> None:
    log_entry = Log(
        actor_id=actor_id,
        action=action,
        target_table="topups",
        target_id=target_id,
        before_data=before,
        after_data=after,
    )
    db.add(log_entry)


@router.get("/", response_model=dict)
def list_topups(db: Session = Depends(get_db)) -> dict:
    topups: List[Topup] = db.query(Topup).all()
    data = [TopupRead.from_orm(topup).dict() for topup in topups]
    return build_response(data=data)


@router.get("/{topup_id}", response_model=dict)
def get_topup(topup_id: UUID, db: Session = Depends(get_db)) -> dict:
    topup = db.query(Topup).filter(Topup.id == topup_id).first()
    if not topup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topup not found")
    return build_response(data=TopupRead.from_orm(topup).dict())


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_topup(payload: TopupCreate, db: Session = Depends(get_db)) -> dict:
    topup = Topup(**payload.dict())
    db.add(topup)
    db.flush()
    db.refresh(topup)

    after_state = jsonable_encoder(TopupRead.from_orm(topup))
    log_change(db, payload.created_by, topup.id, "create_topup", before=None, after=after_state)

    db.commit()
    db.refresh(topup)

    return build_response(data=after_state)


@router.post("/{topup_id}/approve", response_model=dict)
def approve_topup(topup_id: UUID, payload: TopupApprove, db: Session = Depends(get_db)) -> dict:
    topup = db.query(Topup).filter(Topup.id == topup_id).first()
    if not topup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topup not found")

    ensure_transition(topup.status, "approved")

    before_state = jsonable_encoder(TopupRead.from_orm(topup))

    channel = db.query(Channel).filter(Channel.id == topup.channel_id).first()
    if not channel:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Channel not found")

    service_fee_amount = calculate_service_fee(topup.amount, channel.service_fee_type, channel.service_fee_value)

    topup.status = "approved"
    topup.service_fee_amount = service_fee_amount
    topup.updated_by = payload.actor_id
    if payload.remark is not None:
        topup.remark = payload.remark

    db.flush()
    db.refresh(topup)

    after_state = jsonable_encoder(TopupRead.from_orm(topup))
    log_change(db, payload.actor_id, topup.id, "approve_topup", before_state, after_state)

    db.commit()
    db.refresh(topup)

    return build_response(data=after_state)


@router.post("/{topup_id}/pay", response_model=dict)
def pay_topup(topup_id: UUID, payload: TopupPay, db: Session = Depends(get_db)) -> dict:
    topup = db.query(Topup).filter(Topup.id == topup_id).first()
    if not topup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topup not found")

    ensure_transition(topup.status, "paid")

    before_state = jsonable_encoder(TopupRead.from_orm(topup))

    topup.status = "paid"
    topup.updated_by = payload.actor_id
    if payload.remark is not None:
        topup.remark = payload.remark

    db.flush()
    db.refresh(topup)

    after_state = jsonable_encoder(TopupRead.from_orm(topup))
    log_change(db, payload.actor_id, topup.id, "pay_topup", before_state, after_state)

    db.commit()
    db.refresh(topup)

    return build_response(data=after_state)


@router.post("/{topup_id}/confirm", response_model=dict)
def confirm_topup(topup_id: UUID, payload: TopupConfirm, db: Session = Depends(get_db)) -> dict:
    topup = db.query(Topup).filter(Topup.id == topup_id).first()
    if not topup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topup not found")

    ensure_transition(topup.status, "done")

    before_state = jsonable_encoder(TopupRead.from_orm(topup))

    topup.status = "done"
    topup.updated_by = payload.actor_id
    if payload.remark is not None:
        topup.remark = payload.remark

    db.flush()
    db.refresh(topup)

    after_state = jsonable_encoder(TopupRead.from_orm(topup))
    log_change(db, payload.actor_id, topup.id, "confirm_topup", before_state, after_state)

    db.commit()
    db.refresh(topup)

    return build_response(data=after_state)


@router.post("/{topup_id}/reject", response_model=dict)
def reject_topup(topup_id: UUID, payload: TopupReject, db: Session = Depends(get_db)) -> dict:
    topup = db.query(Topup).filter(Topup.id == topup_id).first()
    if not topup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topup not found")

    ensure_transition(topup.status, "rejected")

    before_state = jsonable_encoder(TopupRead.from_orm(topup))

    topup.status = "rejected"
    topup.updated_by = payload.actor_id
    if payload.remark is not None:
        topup.remark = payload.remark

    db.flush()
    db.refresh(topup)

    after_state = jsonable_encoder(TopupRead.from_orm(topup))
    log_change(db, payload.actor_id, topup.id, "reject_topup", before_state, after_state)

    db.commit()
    db.refresh(topup)

    return build_response(data=after_state)


