from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_
from sqlalchemy.orm import Session

from core.db import get_db
from models import AdSpendDaily, Ledger, Log, Reconciliation
from schemas import (
    ReconciliationAutoRequest,
    ReconciliationManualRequest,
    ReconciliationRead,
)

router = APIRouter(prefix="/api/reconciliations", tags=["reconciliations"])


def build_response(data, error=None):
    return {
        "data": data,
        "error": error,
        "meta": {"timestamp": datetime.now(tz=timezone.utc).isoformat()},
    }


def ensure_no_existing_record(db: Session, ledger_id: UUID, ad_spend_id: Optional[UUID] = None) -> None:
    query = db.query(Reconciliation).filter(Reconciliation.ledger_id == ledger_id)
    if ad_spend_id is not None:
        query = query.filter(Reconciliation.ad_spend_id == ad_spend_id)
    existing = query.first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Reconciliation already exists for the provided identifiers",
        )


def calculate_match_score(ledger_amount: Decimal, spend: Decimal) -> Decimal:
    if ledger_amount == 0:
        return Decimal("1")
    difference_ratio = abs(ledger_amount - spend) / ledger_amount
    score = Decimal("1") - difference_ratio
    if score < 0:
        score = Decimal("0")
    return score.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def create_reconciliation(
    db: Session,
    ledger: Ledger,
    ad_spend: AdSpendDaily,
    matched_by: str,
    actor_id: Optional[UUID],
    match_score: Optional[Decimal] = None,
    remark: Optional[str] = None,
) -> Reconciliation:
    if match_score is None:
        match_score = calculate_match_score(ledger.amount, ad_spend.spend)

    reconciliation = Reconciliation(
        ledger_id=ledger.id,
        ad_spend_id=ad_spend.id,
        match_score=match_score,
        matched_by=matched_by,
        remark=remark,
        created_by=actor_id,
        updated_by=actor_id,
    )
    db.add(reconciliation)
    db.flush()
    db.refresh(reconciliation)

    log_entry = Log(
        actor_id=actor_id,
        action=f"{matched_by}_reconciliation",
        target_table="reconciliations",
        target_id=reconciliation.id,
        before_data=None,
        after_data=jsonable_encoder(ReconciliationRead.from_orm(reconciliation)),
    )
    db.add(log_entry)

    return reconciliation


@router.post("/auto", response_model=dict)
def auto_reconcile(payload: ReconciliationAutoRequest, db: Session = Depends(get_db)) -> dict:
    ledger = db.query(Ledger).filter(Ledger.id == payload.ledger_id).first()
    if not ledger:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ledger not found")

    if ledger.ad_account_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Ledger is not associated with an ad account",
        )

    ensure_no_existing_record(db, ledger_id=ledger.id)

    ledger_date = ledger.occurred_at.date()
    start_date = ledger_date - timedelta(days=1)
    end_date = ledger_date + timedelta(days=1)

    candidates: List[AdSpendDaily] = (
        db.query(AdSpendDaily)
        .filter(
            and_(
                AdSpendDaily.ad_account_id == ledger.ad_account_id,
                AdSpendDaily.date >= start_date,
                AdSpendDaily.date <= end_date,
            )
        )
        .all()
    )

    if not candidates:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No candidate spend records found")

    best_candidate = None
    best_diff = None
    tolerance = ledger.amount * Decimal("0.05")

    for candidate in candidates:
        diff = abs(candidate.spend - ledger.amount)
        if diff <= tolerance:
            if best_diff is None or diff < best_diff:
                best_candidate = candidate
                best_diff = diff

    if best_candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No matching spend record within tolerance",
        )

    ensure_no_existing_record(db, ledger_id=ledger.id, ad_spend_id=best_candidate.id)

    reconciliation = create_reconciliation(
        db=db,
        ledger=ledger,
        ad_spend=best_candidate,
        matched_by="auto",
        actor_id=payload.actor_id,
        remark=payload.remark,
    )

    db.commit()
    db.refresh(reconciliation)

    return build_response(data=ReconciliationRead.from_orm(reconciliation).dict())


@router.post("/manual", response_model=dict)
def manual_reconcile(payload: ReconciliationManualRequest, db: Session = Depends(get_db)) -> dict:
    ledger = db.query(Ledger).filter(Ledger.id == payload.ledger_id).first()
    if not ledger:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ledger not found")

    ad_spend = db.query(AdSpendDaily).filter(AdSpendDaily.id == payload.ad_spend_id).first()
    if not ad_spend:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ad spend record not found")

    ensure_no_existing_record(db, ledger_id=ledger.id, ad_spend_id=ad_spend.id)

    reconciliation = create_reconciliation(
        db=db,
        ledger=ledger,
        ad_spend=ad_spend,
        matched_by="manual",
        actor_id=payload.actor_id,
        match_score=payload.match_score,
        remark=payload.remark,
    )

    db.commit()
    db.refresh(reconciliation)

    return build_response(data=ReconciliationRead.from_orm(reconciliation).dict())


