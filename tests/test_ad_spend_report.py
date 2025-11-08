from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.core.error_codes import ErrorCode
from backend.models import AdAccount, Channel, Project, User


def _create_account(db: Session, user_id: UUID) -> AdAccount:
    owner = User(id=user_id, email="reporter@example.com", name="Reporter", role="media_buyer")
    project = Project(
        id=uuid4(),
        name=f"Project-{uuid4()}",
        currency="USD",
        status="active",
        created_by=user_id,
        updated_by=user_id,
    )
    channel = Channel(
        id=uuid4(),
        name=f"Channel-{uuid4()}",
        service_fee_type="percent",
        service_fee_value=Decimal("5.00"),
        is_active=True,
        created_by=user_id,
        updated_by=user_id,
    )
    account = AdAccount(
        id=uuid4(),
        name=f"Account-{uuid4()}",
        project_id=project.id,
        channel_id=channel.id,
        assigned_user_id=user_id,
        status="active",
        created_by=user_id,
        updated_by=user_id,
    )
    db.add_all([owner, project, channel, account])
    db.commit()
    return account


def test_submit_report_success(client: TestClient, db_session: Session, test_user) -> None:
    user_id = UUID(test_user.id)
    account = _create_account(db_session, user_id)

    payload = {
        "ad_account_id": str(account.id),
        "date": date.today().isoformat(),
        "spend": "100.00",
        "leads_count": 10,
        "note": "日常投放",
    }

    response = client.post("/api/v1/adspend/report", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["error"] is None
    assert body["data"]["ad_account_id"] == payload["ad_account_id"]
    assert body["data"]["is_anomaly"] is False
    assert body["data"]["anomaly_reason"] is None


def test_submit_report_duplicate(client: TestClient, db_session: Session, test_user) -> None:
    user_id = UUID(test_user.id)
    account = _create_account(db_session, user_id)

    payload = {
        "ad_account_id": str(account.id),
        "date": date.today().isoformat(),
        "spend": "80.00",
        "leads_count": 8,
    }

    first = client.post("/api/v1/adspend/report", json=payload)
    assert first.status_code == 201

    second = client.post("/api/v1/adspend/report", json=payload)
    assert second.status_code == 409
    body = second.json()
    assert body["error"]["code"] == ErrorCode.INVALID_STATUS
    assert body["data"] is None


def test_anomaly_when_leads_zero(client: TestClient, db_session: Session, test_user) -> None:
    user_id = UUID(test_user.id)
    account = _create_account(db_session, user_id)

    payload = {
        "ad_account_id": str(account.id),
        "date": date.today().isoformat(),
        "spend": "120.00",
        "leads_count": 0,
    }

    response = client.post("/api/v1/adspend/report", json=payload)
    assert response.status_code == 201
    body = response.json()["data"]
    assert body["is_anomaly"] is True
    assert body["anomaly_reason"] == "LEADS_COUNT_ZERO"


def test_anomaly_when_spend_spikes(client: TestClient, db_session: Session, test_user) -> None:
    user_id = UUID(test_user.id)
    account = _create_account(db_session, user_id)

    day1_payload = {
        "ad_account_id": str(account.id),
        "date": date.today().isoformat(),
        "spend": "100.00",
        "leads_count": 10,
    }
    day2_payload = {
        "ad_account_id": str(account.id),
        "date": (date.today() + timedelta(days=1)).isoformat(),
        "spend": "200.00",
        "leads_count": 8,
    }

    first = client.post("/api/v1/adspend/report", json=day1_payload)
    assert first.status_code == 201

    second = client.post("/api/v1/adspend/report", json=day2_payload)
    assert second.status_code == 201
    data = second.json()["data"]
    assert data["is_anomaly"] is True
    assert data["anomaly_reason"] == "SPEND_CHANGE_100.00%"


def test_spend_validation(client: TestClient, db_session: Session, test_user) -> None:
    user_id = UUID(test_user.id)
    account = _create_account(db_session, user_id)

    payload = {
        "ad_account_id": str(account.id),
        "date": date.today().isoformat(),
        "spend": "10000001.00",
        "leads_count": 10,
    }

    response = client.post("/api/v1/adspend/report", json=payload)
    assert response.status_code == 422


def test_list_and_detail_reports(client: TestClient, db_session: Session, test_user) -> None:
    user_id = UUID(test_user.id)
    account = _create_account(db_session, user_id)

    payload1 = {
        "ad_account_id": str(account.id),
        "date": date.today().isoformat(),
        "spend": "120.00",
        "leads_count": 12,
    }
    payload2 = {
        "ad_account_id": str(account.id),
        "date": (date.today() + timedelta(days=1)).isoformat(),
        "spend": "130.00",
        "leads_count": 13,
    }

    resp1 = client.post("/api/v1/adspend/report", json=payload1)
    assert resp1.status_code == 201
    report_id = resp1.json()["data"]["id"]

    resp2 = client.post("/api/v1/adspend/report", json=payload2)
    assert resp2.status_code == 201

    list_resp = client.get(f"/api/v1/adspend/reports?ad_account_id={account.id}")
    assert list_resp.status_code == 200
    reports = list_resp.json()["data"]
    assert len(reports) >= 2

    detail_resp = client.get(f"/api/v1/adspend/reports/{report_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()["data"]
    assert detail["id"] == report_id

