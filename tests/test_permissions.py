from uuid import uuid4

from fastapi.testclient import TestClient

from backend.core.error_codes import ErrorCode
from backend.core.security import AuthenticatedUser, get_current_user


def test_role_permissions_enforced(client: TestClient):
    payload = {
        "project_id": str(uuid4()),
        "ad_account_id": str(uuid4()),
        "amount": "180.00",
    }
    create_resp = client.post("/api/v1/topups", json=payload)
    topup_id = create_resp.json()["data"]["id"]

    original_dependency = client.app.dependency_overrides[get_current_user]

    def trader_user():
        return AuthenticatedUser(id=str(uuid4()), role="trader", email="trader@example.com", raw_claims={})

    def manager_user():
        return AuthenticatedUser(id=str(uuid4()), role="manager", email="manager@example.com", raw_claims={})

    try:
        client.app.dependency_overrides[get_current_user] = trader_user
        forbidden = client.post(f"/api/v1/topups/{topup_id}/approve")
        assert forbidden.status_code == 403
        error = forbidden.json()["error"]
        assert error["code"] == ErrorCode.PERMISSION_DENIED

        client.app.dependency_overrides[get_current_user] = manager_user
        allowed = client.post(f"/api/v1/topups/{topup_id}/approve")
        assert allowed.status_code == 200
    finally:
        client.app.dependency_overrides[get_current_user] = original_dependency

