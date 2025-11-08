from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models import AdAccount, AdSpendDaily, Ledger, Project, Reconciliation, User


def _prepare_entities(db: Session):
    user_id = uuid4()
    project_id = uuid4()
    ad_account_id = uuid4()

    user = User(id=user_id, email="owner@example.com", name="Owner", role="admin")
    project = Project(
        id=project_id,
        name="Reconcile Project",
        currency="USD",
        status="active",
        created_by=user_id,
        updated_by=user_id,
    )
    account = AdAccount(
        id=ad_account_id,
        name="Reconcile Account",
        project_id=project_id,
        channel_id=uuid4(),
        assigned_user_id=user_id,
        status="active",
        created_by=user_id,
        updated_by=user_id,
    )
    db.add_all([user, project, account])
    db.commit()
    return user_id, ad_account_id


def _clear_tables(db: Session) -> None:
    db.query(Reconciliation).delete()
    db.query(Ledger).delete()
    db.query(AdSpendDaily).delete()
    db.commit()


def test_auto_reconcile_matches_and_manual_review(client: TestClient, db_session: Session) -> None:
    _clear_tables(db_session)
    user_id, ad_account_id = _prepare_entities(db_session)

    spend_match = AdSpendDaily(
        ad_account_id=ad_account_id,
        user_id=user_id,
        date=datetime.utcnow().date(),
        spend=Decimal("100.00"),
        leads_count=10,
        cost_per_lead=Decimal("10.00"),
        is_anomaly=False,
        created_by=user_id,
        updated_by=user_id,
    )
    spend_manual = AdSpendDaily(
        ad_account_id=ad_account_id,
        user_id=user_id,
        date=datetime.utcnow().date() + timedelta(days=2),
        spend=Decimal("200.00"),
        leads_count=8,
        cost_per_lead=Decimal("25.00"),
        is_anomaly=False,
        created_by=user_id,
        updated_by=user_id,
    )

    ledger_match = Ledger(
        id=uuid4(),
        type="expense",
        project_id=uuid4(),
        channel_id=uuid4(),
        ad_account_id=ad_account_id,
        amount=Decimal("102.00"),
        currency="USD",
        occurred_at=datetime.utcnow(),
        remark="Matched ledger",
        created_by=user_id,
        updated_by=user_id,
    )
    ledger_manual = Ledger(
        id=uuid4(),
        type="expense",
        project_id=uuid4(),
        channel_id=uuid4(),
        ad_account_id=ad_account_id,
        amount=Decimal("250.00"),
        currency="USD",
        occurred_at=datetime.utcnow() + timedelta(days=3),
        remark="Manual ledger",
        created_by=user_id,
        updated_by=user_id,
    )

    db_session.add_all([spend_match, spend_manual, ledger_match, ledger_manual])
    db_session.commit()

    response = client.post("/api/v1/reconciliations/auto")
    body = response.json()
    assert response.status_code == 200, body
    assert body["data"] == {"matched": 1, "manual_review": 1, "total": 2}

    records = db_session.query(Reconciliation).all()
    statuses = {record.status for record in records}
    assert statuses == {"matched", "manual_review"}
    matched_record = next(r for r in records if r.status == "matched")
    assert matched_record.amount_diff == Decimal("2.00")

    manual_record = next(r for r in records if r.status == "manual_review")
    assert manual_record.date_diff >= 1

    list_resp = client.get("/api/v1/reconciliations")
    assert list_resp.status_code == 200
    listed_statuses = {item["status"] for item in list_resp.json()["data"]}
    assert listed_statuses == {"matched", "manual_review"}


def test_manual_reconciliation_create_and_detail(client: TestClient, db_session: Session) -> None:
    _clear_tables(db_session)
    user_id, ad_account_id = _prepare_entities(db_session)

    spend = AdSpendDaily(
        id=uuid4(),
        ad_account_id=ad_account_id,
        user_id=user_id,
        date=datetime.utcnow().date(),
        spend=Decimal("120.00"),
        leads_count=12,
        cost_per_lead=Decimal("10.00"),
        is_anomaly=False,
        created_by=user_id,
        updated_by=user_id,
    )
    ledger = Ledger(
        id=uuid4(),
        type="expense",
        project_id=uuid4(),
        channel_id=uuid4(),
        ad_account_id=ad_account_id,
        amount=Decimal("118.00"),
        currency="USD",
        occurred_at=datetime.utcnow(),
        remark="Manual match",
        created_by=user_id,
        updated_by=user_id,
    )
    db_session.add_all([spend, ledger])
    db_session.commit()

    payload = {
        "ad_account_id": str(ad_account_id),
        "daily_spend_id": str(spend.id),
        "finance_txn_id": str(ledger.id),
        "amount_diff": "2.00",
        "date_diff": 0,
        "status": "manual_review",
        "match_type": "manual",
    }

    create_resp = client.post("/api/v1/reconciliations", json=payload)
    assert create_resp.status_code == 201
    rec_data = create_resp.json()["data"]
    rec_id = rec_data["id"]
    assert rec_data["status"] == "manual_review"

    detail_resp = client.get(f"/api/v1/reconciliations/{rec_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()["data"]
    assert detail["id"] == rec_id
    assert detail["amount_diff"] == "2.00"