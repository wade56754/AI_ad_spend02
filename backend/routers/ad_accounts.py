from math import ceil
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.response import ok
from backend.core.security import AuthenticatedUser, get_current_user
from backend.models import AdAccount, Log
from backend.schemas import AdAccountCreate, AdAccountRead, AdAccountStatusUpdate
from backend.services.log_service import LogService

router = APIRouter(prefix="/ad-accounts", tags=["ad_accounts"])

ALLOWED_TRANSITIONS: Dict[str, List[str]] = {
    "new": ["testing"],
    "testing": ["active"],
    "active": ["suspended", "dead"],
    "suspended": ["dead", "active"],
    "dead": ["archived"],
    "archived": [],
}


@router.get("", response_model=dict)
def list_ad_accounts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    project_id: Optional[UUID] = Query(None),
    channel_id: Optional[UUID] = Query(None),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(AdAccount)

    if status_filter:
        query = query.filter(AdAccount.status == status_filter)

    if project_id:
        query = query.filter(AdAccount.project_id == project_id)

    if channel_id:
        query = query.filter(AdAccount.channel_id == channel_id)

    total = query.count()
    items: List[AdAccount] = (
        query.order_by(AdAccount.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    data = [AdAccountRead.model_validate(item, from_attributes=True).model_dump() for item in items]
    pagination = {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": ceil(total / page_size) if page_size else 0,
    }
    return ok(data=data, meta={"pagination": pagination})


@router.get("/{account_id}", response_model=dict)
def get_ad_account(
    account_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    account = db.query(AdAccount).filter(AdAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ad account not found")
    data = AdAccountRead.model_validate(account, from_attributes=True).model_dump()
    return ok(data=data)


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_ad_account(
    payload: AdAccountCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    account = AdAccount(id=uuid4(), **payload.dict())
    db.add(account)
    db.commit()
    db.refresh(account)
    data = AdAccountRead.model_validate(account, from_attributes=True).model_dump()

    LogService.write(
        db,
        action="create_ad_account",
        operator_id=current_user.id,
        target="ad_accounts",
        target_id=account.id,
        detail=data,
    )

    return ok(data=data, status_code=status.HTTP_201_CREATED)


@router.post("/{account_id}/status", response_model=dict)
def update_ad_account_status(
    account_id: UUID,
    payload: AdAccountStatusUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    account = db.query(AdAccount).filter(AdAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ad account not found")

    target_status = payload.status
    current_status = account.status

    if target_status == current_status:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Status is unchanged",
        )

    allowed = ALLOWED_TRANSITIONS.get(current_status, [])
    if target_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Status transition from {current_status} to {target_status} is not allowed",
        )

    before_state = jsonable_encoder(AdAccountRead.model_validate(account, from_attributes=True).model_dump())

    account.status = target_status
    if payload.dead_reason is not None:
        account.dead_reason = payload.dead_reason
    if payload.updated_by is not None:
        account.updated_by = payload.updated_by

    log_entry = Log(
        actor_id=payload.updated_by,
        action="update_ad_account_status",
        target_table="ad_accounts",
        target_id=account.id,
        before_data=before_state,
        after_data=None,
    )
    db.add(log_entry)

    db.flush()
    db.refresh(account)

    after_state = jsonable_encoder(AdAccountRead.model_validate(account, from_attributes=True).model_dump())
    log_entry.after_data = after_state

    db.commit()
    db.refresh(account)

    return ok(data=after_state)


