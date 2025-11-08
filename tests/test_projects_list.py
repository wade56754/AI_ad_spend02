import pytest


pytest.skip("当前阶段仅验证后端接口连通性，数据库相关测试暂时跳过", allow_module_level=True)
import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models import Project, User


def seed_projects(db: Session, count: int = 3) -> None:
    owner_id = uuid.uuid4()
    user = User(id=owner_id, email="owner@example.com", name="Owner", role="admin")
    db.add(user)
    db.flush()

    for index in range(count):
        project = Project(
            id=uuid.uuid4(),
            name=f"Project {index}",
            currency="USD",
            status="active",
            created_by=owner_id,
            updated_by=owner_id,
        )
        db.add(project)
    db.commit()


def test_projects_list_pagination(client: TestClient, db_session: Session) -> None:
    seed_projects(db_session, count=3)

    response = client.get("/api/v1/projects?page=1&page_size=2")
    assert response.status_code == 200
    payload = response.json()
    assert payload["error"] == {"code": None, "message": None}
    assert len(payload["data"]) == 2
    assert payload["meta"]["pagination"]["total"] == 3
    assert payload["meta"]["pagination"]["total_pages"] == 2

    response_page_2 = client.get("/api/v1/projects?page=2&page_size=2")
    assert response_page_2.status_code == 200
    payload_page_2 = response_page_2.json()
    assert len(payload_page_2["data"]) == 1

