import uuid
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models import AdAccount, Channel, Project, User


def create_base_entities(db: Session):
    user_id = uuid.uuid4()
    project_id = uuid.uuid4()
    channel_id = uuid.uuid4()
    ad_account_id = uuid.uuid4()

    user = User(id=user_id, email="buyer@example.com", name="Buyer", role="media_buyer")
    project = Project(
        id=project_id,
        name="Project Alpha",
        currency="USD",
        status="active",
        created_by=user_id,
        updated_by=user_id,
    )
    channel = Channel(
        id=channel_id,
        name="Channel One",
        service_fee_type="percent",
        service_fee_value=5,
        created_by=user_id,
        updated_by=user_id,
    )
    ad_account = AdAccount(
        id=ad_account_id,
        name="Account X",
        project_id=project_id,
        channel_id=channel_id,
        assigned_user_id=user_id,
        status="active",
        created_by=user_id,
        updated_by=user_id,
    )
    db.add_all([user, project, channel, ad_account])
    db.commit()
    return {
        "user_id": str(user_id),
        "project_id": str(project_id),
        "channel_id": str(channel_id),
        "ad_account_id": str(ad_account_id),
    }


def test_duplicate_daily_report_returns_409(client: TestClient, db_session: Session):
    ids = create_base_entities(db_session)

    payload = {
        "ad_account_id": ids["ad_account_id"],
        "user_id": ids["user_id"],
        "date": date.today().isoformat(),
        "spend": "120.50",
        "leads_count": 10,
        "note": "Daily report",
    }

    first_response = client.post("/api/ad-spend", json=payload)
    assert first_response.status_code == 201
    first_data = first_response.json()["data"]
    assert first_data["cost_per_lead"] == "12.05"

    second_response = client.post("/api/ad-spend", json=payload)
    assert second_response.status_code == 409
    assert second_response.json()["error"] == "Daily report already exists for this account and date"


