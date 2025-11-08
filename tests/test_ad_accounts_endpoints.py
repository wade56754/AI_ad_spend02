from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models import AdAccount, Channel, Project, User


def _cleanup(db: Session) -> None:
    db.query(AdAccount).delete()
    db.query(Project).delete()
    db.query(Channel).delete()
    db.query(User).delete()
    db.commit()


def _prepare_entities(db: Session):
    user_id = uuid4()
    user = User(id=user_id, email=f"user-{user_id}@example.com", name="Tester", role="admin")
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
    db.add_all([user, project, channel])
    db.commit()
    return user, project, channel


def test_ad_account_create_list_and_detail(client: TestClient, db_session: Session) -> None:
    _cleanup(db_session)
    user, project, channel = _prepare_entities(db_session)

    payload = {
        "name": "Account-Test",
        "project_id": str(project.id),
        "channel_id": str(channel.id),
        "assigned_user_id": str(user.id),
        "status": "new",
        "created_by": str(user.id),
        "updated_by": str(user.id),
    }

    create_resp = client.post("/api/v1/ad-accounts", json=payload)
    assert create_resp.status_code == 201
    account_id = create_resp.json()["data"]["id"]

    detail_resp = client.get(f"/api/v1/ad-accounts/{account_id}")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()["data"]
    assert detail_data["id"] == account_id
    assert detail_data["name"] == payload["name"]

    list_resp = client.get("/api/v1/ad-accounts")
    assert list_resp.status_code == 200
    ids = [item["id"] for item in list_resp.json()["data"]]
    assert account_id in ids

