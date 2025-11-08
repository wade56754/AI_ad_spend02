from datetime import datetime, timezone
from typing import Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from core.db import get_db
from models import AdAccount, Log
from schemas import AdAccountRead, AdAccountStatusUpdate

router = APIRouter(prefix="/api/ad-accounts", tags=["ad_accounts"])

ALLOWED_TRANSITIONS: Dict[str, List[str]] = {
    "new": ["testing"],
    "testing": ["active"],
    "active": ["suspended", "dead"],
    "suspended": ["dead", "active"],
    "dead": ["archived"],
    "archived": [],
}


def build_response(data, error=None):
    return {
        "data": data,
        "error": error,
        "meta": {"timestamp": datetime.now(tz=timezone.utc).isoformat()},
    }


@router.post("/{account_id}/status", response_model=dict)
def update_ad_account_status(
    account_id: UUID, payload: AdAccountStatusUpdate, db: Session = Depends(get_db)
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

    before_state = jsonable_encoder(AdAccountRead.from_orm(account))

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

    after_state = jsonable_encoder(AdAccountRead.from_orm(account))
    log_entry.after_data = after_state

    db.commit()
    db.refresh(account)

    return build_response(data=after_state)


