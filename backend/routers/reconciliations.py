from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Set
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.error_codes import ErrorCode
from backend.core.response import fail, ok
from backend.core.security import AuthenticatedUser, get_current_user
from backend.models import AdSpendDaily, Ledger, Reconciliation, ReconciliationLog
from backend.services.log_service import LogService

router = APIRouter(prefix="/reconciliations", tags=["reconciliations"])

AMOUNT_DIFF_THRESHOLD = Decimal("0.05")
DATE_DIFF_THRESHOLD_DAYS = 1


def _to_date(value: datetime) -> datetime.date:
    if isinstance(value, datetime):
        return value.date()
    return value  # type: ignore[return-value]


def _serialize_reconciliation(record: Reconciliation) -> Dict[str, object]:
    return {
        "id": str(record.id),
        "ad_account_id": str(record.ad_account_id),
        "daily_spend_id": str(record.daily_spend_id),
        "finance_txn_id": str(record.finance_txn_id),
        "match_type": record.match_type,
        "status": record.status,
        "amount_diff": format(record.amount_diff, "f"),
        "date_diff": record.date_diff,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }


class ReconciliationCreatePayload(BaseModel):
    ad_account_id: UUID
    daily_spend_id: UUID
    finance_txn_id: UUID
    amount_diff: Decimal
    date_diff: int
    status: str = "manual_review"
    match_type: str = "manual"

    @validator("amount_diff")
    def validate_amount_diff(cls, value: Decimal) -> Decimal:
        if value < 0:
            raise ValueError("amount_diff must be non-negative")
        return value.quantize(Decimal("0.01"))

    @validator("date_diff")
    def validate_date_diff(cls, value: int) -> int:
        if value < 0:
            raise ValueError("date_diff must be non-negative")
        return value


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_reconciliation(
    payload: ReconciliationCreatePayload,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    spend = db.query(AdSpendDaily).filter(AdSpendDaily.id == payload.daily_spend_id).first()
    if spend is None:
        return fail(ErrorCode.INVALID_PARAM, "日报记录不存在", status_code=status.HTTP_404_NOT_FOUND)
    ledger = db.query(Ledger).filter(Ledger.id == payload.finance_txn_id).first()
    if ledger is None:
        return fail(ErrorCode.INVALID_PARAM, "财务流水不存在", status_code=status.HTTP_404_NOT_FOUND)

    record = Reconciliation(
        ad_account_id=payload.ad_account_id,
        daily_spend_id=payload.daily_spend_id,
        finance_txn_id=payload.finance_txn_id,
        match_type=payload.match_type,
        status=payload.status,
        amount_diff=payload.amount_diff,
        date_diff=payload.date_diff,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    LogService.write(
        db,
        action="create_reconciliation",
        operator_id=current_user.id,
        target="reconciliations",
        target_id=record.id,
        detail=_serialize_reconciliation(record),
    )

    return ok(data=_serialize_reconciliation(record), status_code=status.HTTP_201_CREATED)


@router.post("/auto", response_model=dict, status_code=status.HTTP_200_OK)
def auto_reconcile(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    spends: List[AdSpendDaily] = db.query(AdSpendDaily).all()
    ledgers: List[Ledger] = db.query(Ledger).all()

    used_finance_ids: Set[UUID] = set()
    matched_count = 0
    manual_count = 0

    for spend in spends:
        candidates = [
            ledger
            for ledger in ledgers
            if ledger.ad_account_id == spend.ad_account_id and ledger.id not in used_finance_ids
        ]
        if not candidates:
            continue

        candidates.sort(
            key=lambda ledger: (
                abs(Decimal(spend.spend) - Decimal(ledger.amount)),
                abs((_to_date(ledger.occurred_at) - spend.date).days),
            )
        )
        ledger = candidates[0]
        used_finance_ids.add(ledger.id)

        spend_amount = Decimal(spend.spend)
        ledger_amount = Decimal(ledger.amount)
        amount_diff_value = abs(spend_amount - ledger_amount)
        ratio_base = ledger_amount if ledger_amount != 0 else Decimal("1")
        amount_ratio = amount_diff_value / ratio_base

        spend_date = spend.date
        ledger_date = _to_date(ledger.occurred_at)
        date_diff_days = abs((ledger_date - spend_date).days)

        if amount_ratio <= AMOUNT_DIFF_THRESHOLD and date_diff_days <= DATE_DIFF_THRESHOLD_DAYS:
            status_value = "matched"
            match_type = "auto"
            matched_count += 1
        else:
            status_value = "manual_review"
            match_type = "auto"
            manual_count += 1

        record = Reconciliation(
            ad_account_id=spend.ad_account_id,
            daily_spend_id=spend.id,
            finance_txn_id=ledger.id,
            match_type=match_type,
            status=status_value,
            amount_diff=amount_diff_value.quantize(Decimal("0.01")),
            date_diff=date_diff_days,
        )
        db.add(record)

    total_processed = matched_count + manual_count
    db.flush()

    detail_payload = {
        "matched": matched_count,
        "manual_review": manual_count,
        "total": total_processed,
    }

    log_entry = ReconciliationLog(
        id=uuid4(),
        reconciliation_id=None,
        action="auto_reconcile",
        operator_id=UUID(str(current_user.id)),
        detail=str(detail_payload),
    )
    db.add(log_entry)
    db.commit()

    LogService.write(
        db,
        action="auto_reconcile",
        operator_id=current_user.id,
        target="reconciliations",
        detail=detail_payload,
    )

    return ok(
        data=detail_payload,
        status_code=status.HTTP_200_OK,
    )


@router.get("", response_model=dict, status_code=status.HTTP_200_OK)
def list_reconciliations(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    records = (
        db.query(Reconciliation)
        .filter(Reconciliation.status.in_(["matched", "manual_review"]))
        .order_by(Reconciliation.created_at.desc())
        .all()
    )
    data = [_serialize_reconciliation(record) for record in records]
    return ok(data=data, status_code=status.HTTP_200_OK)


@router.get("/{reconciliation_id}", response_model=dict, status_code=status.HTTP_200_OK)
def get_reconciliation(
    reconciliation_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(Reconciliation).filter(Reconciliation.id == reconciliation_id).first()
    if record is None:
        return fail(ErrorCode.INVALID_PARAM, "对账记录不存在", status_code=status.HTTP_404_NOT_FOUND)
    return ok(data=_serialize_reconciliation(record), status_code=status.HTTP_200_OK)


