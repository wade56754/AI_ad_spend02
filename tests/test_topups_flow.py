from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.core.error_codes import ErrorCode
from backend.models import Topup


def _clear(db: Session) -> None:
    db.query(Topup).delete()
    db.commit()


def test_topups_full_flow(client: TestClient, db_session: Session) -> None:
    _clear(db_session)

    payload = {
        "project_id": str(uuid4()),
        "ad_account_id": str(uuid4()),
        "amount": "250.00",
    }

    create_resp = client.post("/api/v1/topups", json=payload)
    assert create_resp.status_code == 201
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

    repeat_confirm = client.post(f"/api/v1/topups/{topup_id}/confirm")
    assert repeat_confirm.status_code == 400
    error = repeat_confirm.json()["error"]
    assert error["code"] == ErrorCode.INVALID_STATUS
    assert error["message"] == "当前状态不允许此操作"

