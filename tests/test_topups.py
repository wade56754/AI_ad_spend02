from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.core.error_codes import ErrorCode
from backend.models import Topup


def _cleanup(db: Session) -> None:
    db.query(Topup).delete()
    db.commit()


def test_create_topup(client: TestClient, db_session: Session) -> None:
    _cleanup(db_session)
    payload = {
        "project_id": str(uuid4()),
        "ad_account_id": str(uuid4()),
        "amount": "150.00",
    }

    response = client.post("/api/v1/topups", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["error"] is None
    data = body["data"]
    assert data["project_id"] == payload["project_id"]
    assert data["ad_account_id"] == payload["ad_account_id"]
    assert data["amount"] == "150.00"
    assert data["status"] == "pending"


def test_topup_list_and_detail(client: TestClient, db_session: Session) -> None:
    _cleanup(db_session)
    payload = {
        "project_id": str(uuid4()),
        "ad_account_id": str(uuid4()),
        "amount": "210.00",
    }
    create_resp = client.post("/api/v1/topups", json=payload)
    assert create_resp.status_code == 201
    topup_id = create_resp.json()["data"]["id"]

    detail_resp = client.get(f"/api/v1/topups/{topup_id}")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()["data"]
    assert detail_data["id"] == topup_id

    list_resp = client.get("/api/v1/topups")
    assert list_resp.status_code == 200
    ids = [item["id"] for item in list_resp.json()["data"]]
    assert topup_id in ids


def test_invalid_transition_returns_4002(client: TestClient, db_session: Session) -> None:
    _cleanup(db_session)
    payload = {
        "project_id": str(uuid4()),
        "ad_account_id": str(uuid4()),
        "amount": "200.00",
    }
    create_resp = client.post("/api/v1/topups", json=payload)
    topup_id = create_resp.json()["data"]["id"]

    pay_resp = client.post(f"/api/v1/topups/{topup_id}/pay")
    assert pay_resp.status_code == 400
    error = pay_resp.json()["error"]
    assert error["code"] == ErrorCode.INVALID_STATUS
    assert error["message"] == "当前状态不允许此操作"


def test_full_status_flow(client: TestClient, db_session: Session) -> None:
    _cleanup(db_session)
    payload = {
        "project_id": str(uuid4()),
        "ad_account_id": str(uuid4()),
        "amount": "300.00",
    }
    create_resp = client.post("/api/v1/topups", json=payload)
    topup_id = create_resp.json()["data"]["id"]

    approve_resp = client.post(f"/api/v1/topups/{topup_id}/approve")
    assert approve_resp.status_code == 200
    assert approve_resp.json()["data"]["status"] == "approved"

    pay_resp = client.post(f"/api/v1/topups/{topup_id}/pay")
    assert pay_resp.status_code == 200
    assert pay_resp.json()["data"]["status"] == "paid"

    confirm_resp = client.post(f"/api/v1/topups/{topup_id}/confirm")
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["data"]["status"] == "done"

    # Further transitions should fail
    repeat_resp = client.post(f"/api/v1/topups/{topup_id}/approve")
    assert repeat_resp.status_code == 400
    repeat_error = repeat_resp.json()["error"]
    assert repeat_error["code"] == ErrorCode.INVALID_STATUS
    assert repeat_error["message"] == "当前状态不允许此操作"
