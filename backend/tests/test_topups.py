import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models import AdAccount, Channel, Project, User


def prepare_entities(db: Session):
    requester_id = uuid.uuid4()
    account_mgr_id = uuid.uuid4()
    finance_id = uuid.uuid4()

    project_id = uuid.uuid4()
    channel_id = uuid.uuid4()
    ad_account_id = uuid.uuid4()

    users = [
        User(id=requester_id, email="buyer@example.com", name="Buyer", role="media_buyer"),
        User(id=account_mgr_id, email="mgr@example.com", name="Manager", role="account_mgr"),
        User(id=finance_id, email="finance@example.com", name="Finance", role="finance"),
    ]

    project = Project(
        id=project_id,
        name="Project Beta",
        currency="USD",
        status="active",
        created_by=requester_id,
        updated_by=requester_id,
    )
    channel = Channel(
        id=channel_id,
        name="Channel Two",
        service_fee_type="percent",
        service_fee_value=10,
        created_by=requester_id,
        updated_by=requester_id,
    )
    ad_account = AdAccount(
        id=ad_account_id,
        name="Account Y",
        project_id=project_id,
        channel_id=channel_id,
        assigned_user_id=requester_id,
        status="active",
        created_by=requester_id,
        updated_by=requester_id,
    )

    db.add_all(users + [project, channel, ad_account])
    db.commit()

    return {
        "requester_id": str(requester_id),
        "account_mgr_id": str(account_mgr_id),
        "finance_id": str(finance_id),
        "project_id": str(project_id),
        "channel_id": str(channel_id),
        "ad_account_id": str(ad_account_id),
    }


def test_topup_state_machine(client: TestClient, db_session: Session):
    ids = prepare_entities(db_session)

    create_payload = {
        "ad_account_id": ids["ad_account_id"],
        "project_id": ids["project_id"],
        "channel_id": ids["channel_id"],
        "requested_by": ids["requester_id"],
        "amount": "500.00",
        "remark": "Initial request",
        "created_by": ids["requester_id"],
    }

    create_response = client.post("/api/topups", json=create_payload)
    assert create_response.status_code == 201
    topup_data = create_response.json()["data"]
    topup_id = topup_data["id"]
    assert topup_data["status"] == "pending"

    # Invalid transition: trying to pay before approval
    invalid_transition = client.post(
        f"/api/topups/{topup_id}/pay",
        json={"actor_id": ids["finance_id"]},
    )
    assert invalid_transition.status_code == 422

    # Approve
    approve_response = client.post(
        f"/api/topups/{topup_id}/approve",
        json={"actor_id": ids["account_mgr_id"]},
    )
    assert approve_response.status_code == 200
    approved_data = approve_response.json()["data"]
    assert approved_data["status"] == "approved"
    assert approved_data["service_fee_amount"] == "50.00"

    # Pay
    pay_response = client.post(
        f"/api/topups/{topup_id}/pay",
        json={"actor_id": ids["finance_id"]},
    )
    assert pay_response.status_code == 200
    paid_data = pay_response.json()["data"]
    assert paid_data["status"] == "paid"

    # Confirm
    confirm_response = client.post(
        f"/api/topups/{topup_id}/confirm",
        json={"actor_id": ids["account_mgr_id"]},
    )
    assert confirm_response.status_code == 200
    confirm_data = confirm_response.json()["data"]
    assert confirm_data["status"] == "done"

    # Cannot approve after completion
    post_confirm = client.post(
        f"/api/topups/{topup_id}/approve",
        json={"actor_id": ids["account_mgr_id"]},
    )
    assert post_confirm.status_code == 422


