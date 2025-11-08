from datetime import datetime, timezone
from decimal import Decimal
from math import ceil
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.error_codes import ErrorCode
from backend.core.permissions import require_roles
from backend.core.response import fail, ok
from backend.core.security import AuthenticatedUser, get_current_user
from backend.models import Topup
from backend.services.log_service import LogService

router = APIRouter(prefix="/topups", tags=["topups"])

ALLOWED_TRANSITIONS = {
    "pending": {"approved"},
    "approved": {"paid"},
    "paid": {"done"},
    "done": set(),
}


class TopupCreatePayload(BaseModel):
    project_id: UUID
    ad_account_id: UUID
    amount: Decimal

    @validator("amount")
    def validate_amount(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("amount must be positive")
        return value.quantize(Decimal("0.01"))


def _serialize_topup(topup: Topup) -> dict:
    return {
        "id": str(topup.id),
        "project_id": str(topup.project_id),
        "ad_account_id": str(topup.ad_account_id),
        "amount": format(topup.amount, "f"),
        "status": topup.status,
        "created_by": str(topup.created_by) if topup.created_by else None,
        "created_at": topup.created_at.isoformat() if topup.created_at else None,
        "updated_at": topup.updated_at.isoformat() if topup.updated_at else None,
    }


def _load_topup(db: Session, topup_id: UUID) -> Optional[Topup]:
    return db.query(Topup).filter(Topup.id == topup_id).first()


def _transition_or_fail(topup: Topup, target_status: str) -> Optional[str]:
    allowed = ALLOWED_TRANSITIONS.get(topup.status, set())
    if target_status not in allowed:
        return "当前状态不允许此操作"
    topup.status = target_status
    topup.updated_at = datetime.now(timezone.utc)
    return None


@router.get("", response_model=dict)
def list_topups(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    project_id: Optional[UUID] = Query(None),
    ad_account_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    query = db.query(Topup)

    if status_filter:
        query = query.filter(Topup.status == status_filter)
    if project_id:
        query = query.filter(Topup.project_id == project_id)
    if ad_account_id:
        query = query.filter(Topup.ad_account_id == ad_account_id)

    total = query.count()
    records: List[Topup] = (
        query.order_by(Topup.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    pagination = {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": ceil(total / page_size) if page_size else 0,
    }
    data = [_serialize_topup(record) for record in records]
    return ok(data=data, meta={"pagination": pagination})


@router.get("/{topup_id}", response_model=dict)
def get_topup(
    topup_id: UUID,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    topup = _load_topup(db, topup_id)
    if topup is None:
        return fail(ErrorCode.INVALID_PARAM, "充值记录不存在", status_code=status.HTTP_404_NOT_FOUND)
    return ok(data=_serialize_topup(topup))


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_topup(
    payload: TopupCreatePayload,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    actor_id = UUID(str(current_user.id))

    topup = Topup(
        project_id=payload.project_id,
        ad_account_id=payload.ad_account_id,
        amount=payload.amount,
        status="pending",
        created_by=actor_id,
    )
    db.add(topup)
    db.commit()
    db.refresh(topup)

    LogService.write(
        db,
        action="create_topup",
        operator_id=current_user.id,
        target="topups",
        target_id=topup.id,
        detail=_serialize_topup(topup),
    )

    return ok(data=_serialize_topup(topup), status_code=status.HTTP_201_CREATED)


@router.post("/{topup_id}/approve", response_model=dict)
@require_roles("manager", "admin")
def approve_topup(
    topup_id: UUID,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    topup = _load_topup(db, topup_id)
    if topup is None:
        return fail(ErrorCode.INVALID_PARAM, "充值记录不存在", status_code=status.HTTP_404_NOT_FOUND)

    error_message = _transition_or_fail(topup, "approved")
    if error_message:
        return fail(ErrorCode.INVALID_STATUS, error_message, status_code=status.HTTP_400_BAD_REQUEST)

    db.commit()
    db.refresh(topup)
    LogService.write(
        db,
        action="approve_topup",
        operator_id=current_user.id,
        target="topups",
        target_id=topup.id,
        detail=_serialize_topup(topup),
    )
    return ok(data=_serialize_topup(topup))


@router.post("/{topup_id}/pay", response_model=dict)
@require_roles("finance", "admin")
def pay_topup(
    topup_id: UUID,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    topup = _load_topup(db, topup_id)
    if topup is None:
        return fail(ErrorCode.INVALID_PARAM, "充值记录不存在", status_code=status.HTTP_404_NOT_FOUND)

    error_message = _transition_or_fail(topup, "paid")
    if error_message:
        return fail(ErrorCode.INVALID_STATUS, error_message, status_code=status.HTTP_400_BAD_REQUEST)

    db.commit()
    db.refresh(topup)
    LogService.write(
        db,
        action="pay_topup",
        operator_id=current_user.id,
        target="topups",
        target_id=topup.id,
        detail=_serialize_topup(topup),
    )
    return ok(data=_serialize_topup(topup))


@router.post("/{topup_id}/confirm", response_model=dict)
@require_roles("manager", "admin")
def confirm_topup(
    topup_id: UUID,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    topup = _load_topup(db, topup_id)
    if topup is None:
        return fail(ErrorCode.INVALID_PARAM, "充值记录不存在", status_code=status.HTTP_404_NOT_FOUND)

    error_message = _transition_or_fail(topup, "done")
    if error_message:
        return fail(ErrorCode.INVALID_STATUS, error_message, status_code=status.HTTP_400_BAD_REQUEST)

    db.commit()
    db.refresh(topup)
    LogService.write(
        db,
        action="confirm_topup",
        operator_id=current_user.id,
        target="topups",
        target_id=topup.id,
        detail=_serialize_topup(topup),
    )
    return ok(data=_serialize_topup(topup))


