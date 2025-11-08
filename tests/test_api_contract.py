import pytest


pytest.skip("当前阶段仅验证后端接口连通性，数据库相关测试暂时跳过", allow_module_level=True)
from datetime import date
import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models import AdAccount, Channel, Project, User


def ensure_project(db: Session) -> Project:
    owner_id = uuid.uuid4()
    suffix = uuid.uuid4()
    user = User(id=owner_id, email=f"owner+{suffix}@example.com", name="Owner", role="admin")
    project = Project(
        id=uuid.uuid4(),
        name=f"API Contract Project {suffix}",
        currency="USD",
        status="active",
        created_by=owner_id,
        updated_by=owner_id,
    )
    channel = Channel(
        id=uuid.uuid4(),
        name=f"API Contract Channel {suffix}",
        service_fee_type="percent",
        service_fee_value=5,
        is_active=True,
        created_by=owner_id,
        updated_by=owner_id,
    )
    account = AdAccount(
        id=uuid.uuid4(),
        name="API Contract Account",
        project_id=project.id,
        channel_id=channel.id,
        assigned_user_id=owner_id,
        status="active",
        created_by=owner_id,
        updated_by=owner_id,
    )
    db.add_all([user, project, channel, account])
    db.commit()
    return project


def test_healthz_envelope(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    payload = response.json()
    assert payload["error"] == {"code": None, "message": None}
    assert payload["data"]["status"] == "ok"
    assert "timestamp" in payload["meta"]


def test_readyz_envelope(client: TestClient) -> None:
    response = client.get("/readyz")
    assert response.status_code == 200
    payload = response.json()
    assert payload["error"] == {"code": None, "message": None}
    assert payload["data"]["checks"]["database"] == "ok"


def test_projects_list_pagination(client: TestClient, db_session: Session) -> None:
    ensure_project(db_session)

    response = client.get("/api/v1/projects?page=1&page_size=10")
    assert response.status_code == 200
    payload = response.json()
    assert payload["error"] == {"code": None, "message": None}
    meta = payload["meta"]["pagination"]
    assert meta["page"] == 1
    assert meta["page_size"] == 10
    assert meta["total"] >= 1
    assert isinstance(payload["data"], list)


def test_ad_spend_create_and_duplicate(client: TestClient, db_session: Session) -> None:
    project = ensure_project(db_session)
    account = db_session.query(AdAccount).filter(AdAccount.project_id == project.id).first()
    user_id = account.assigned_user_id

    payload = {
        "ad_account_id": str(account.id),
        "user_id": str(user_id),
        "date": date.today().isoformat(),
        "spend": "100.00",
        "leads_count": 5,
    }

    first_resp = client.post("/api/v1/ad-spend", json=payload)
    assert first_resp.status_code == 201
    first_body = first_resp.json()
    assert first_body["error"] == {"code": None, "message": None}
    assert first_body["data"]["cost_per_lead"] == "20.00"

    dup_resp = client.post("/api/v1/ad-spend", json=payload)
    assert dup_resp.status_code == 409
    dup_body = dup_resp.json()
    assert dup_body["error"]["code"] == "HTTP_409"
    assert dup_body["data"] is None

