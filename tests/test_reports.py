from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models import AdAccount, AdSpendDaily, Ledger, Project, Reconciliation, User


def _clear_data(db: Session) -> None:
    db.query(Reconciliation).delete()
    db.query(Ledger).delete()
    db.query(AdSpendDaily).delete()
    db.query(AdAccount).delete()
    db.query(Project).delete()
    db.query(User).delete()
    db.commit()


def _setup_data(db: Session):
    user_id = uuid4()
    project_id = uuid4()
    account_id = uuid4()

    user = User(id=user_id, email="reporter@example.com", name="Reporter", role="admin")
    project = Project(
        id=project_id,
        name="Performance Project",
        currency="USD",
        status="active",
        created_by=user_id,
        updated_by=user_id,
    )
    account = AdAccount(
        id=account_id,
        name="Account Perf",
        project_id=project_id,
        channel_id=uuid4(),
        assigned_user_id=user_id,
        status="active",
        created_by=user_id,
        updated_by=user_id,
    )
    db.add_all([user, project, account])
    db.commit()

    spend1 = AdSpendDaily(
        id=uuid4(),
        ad_account_id=account_id,
        user_id=user_id,
        date=date(2024, 1, 1),
        spend=Decimal("100.00"),
        leads_count=10,
        cost_per_lead=Decimal("10.00"),
        is_anomaly=False,
        created_by=user_id,
        updated_by=user_id,
    )
    spend2 = AdSpendDaily(
        id=uuid4(),
        ad_account_id=account_id,
        user_id=user_id,
        date=date(2024, 1, 2),
        spend=Decimal("150.00"),
        leads_count=15,
        cost_per_lead=Decimal("10.00"),
        is_anomaly=False,
        created_by=user_id,
        updated_by=user_id,
    )

    ledger1 = Ledger(
        id=uuid4(),
        type="income",
        project_id=project_id,
        channel_id=uuid4(),
        ad_account_id=account_id,
        amount=Decimal("260.00"),
        currency="USD",
        occurred_at=datetime(2024, 1, 2),
        remark="Income",
        created_by=user_id,
        updated_by=user_id,
    )

    reconciliation1 = Reconciliation(
        id=uuid4(),
        ad_account_id=account_id,
        daily_spend_id=spend1.id,
        finance_txn_id=ledger1.id,
        match_type="auto",
        status="matched",
        amount_diff=Decimal("10.00"),
        date_diff=1,
    )

    db.add_all([spend1, spend2, ledger1, reconciliation1])
    db.commit()

    return project_id


def test_reports_performance(client: TestClient, db_session: Session) -> None:
    _clear_data(db_session)
    project_id = _setup_data(db_session)

    response = client.get("/api/v1/reports/performance")
    assert response.status_code == 200
    body = response.json()["data"]
    assert body
    record = next(item for item in body if item["project_id"] == str(project_id))
    assert record["total_spend"] == "250.00"
    assert record["total_leads"] == 25


def test_reports_profit(client: TestClient, db_session: Session) -> None:
    _clear_data(db_session)
    project_id = _setup_data(db_session)

    response = client.get("/api/v1/reports/profit")
    assert response.status_code == 200
    data = response.json()["data"]
    record = next(item for item in data if item["project_id"] == str(project_id))
    assert record["spend"] == "100.00"
    assert record["finance_amount"] == "260.00"
    assert record["profit"] == "160.00"


def test_reports_summary_and_detail(client: TestClient, db_session: Session) -> None:
    _clear_data(db_session)
    project_id = _setup_data(db_session)

    summary_resp = client.get("/api/v1/reports")
    assert summary_resp.status_code == 200
    summary_data = summary_resp.json()["data"]
    assert any(item["project_id"] == str(project_id) for item in summary_data)

    detail_resp = client.get(f"/api/v1/reports/{project_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()["data"]
    assert detail["project_id"] == str(project_id)
    assert detail["total_spend"] == "250.00"
    assert detail["profit"] == "160.00"


def test_reports_snapshot_post(client: TestClient, db_session: Session) -> None:
    _clear_data(db_session)
    project_id = _setup_data(db_session)

    payload = {"project_id": str(project_id)}
    response = client.post("/api/v1/reports", json=payload)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["project_id"] == str(project_id)

