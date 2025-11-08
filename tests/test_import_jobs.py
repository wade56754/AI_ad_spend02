from io import BytesIO

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models import ImportJob


def _clear_jobs(db: Session) -> None:
    db.query(ImportJob).delete()
    db.commit()


def _create_csv_upload(client: TestClient) -> str:
    csv_content = "date,amount\n2024-01-01,100.00\n".encode("utf-8")
    files = {"file": ("finance.csv", BytesIO(csv_content), "text/csv")}
    response = client.post("/api/v1/import_jobs/upload", files=files)
    assert response.status_code == 201
    return response.json()["data"]["job_id"]


def test_import_job_upload_csv(client: TestClient, db_session: Session) -> None:
    _clear_jobs(db_session)
    job_id = _create_csv_upload(client)
    assert job_id


def test_import_job_upload_unsupported_file(client: TestClient, db_session: Session) -> None:
    _clear_jobs(db_session)
    files = {"file": ("finance.txt", BytesIO(b"invalid"), "text/plain")}

    response = client.post("/api/v1/import_jobs/upload", files=files)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "failed"
    assert data["error_log"]


def test_import_job_list_and_detail(client: TestClient, db_session: Session) -> None:
    _clear_jobs(db_session)
    job_id = _create_csv_upload(client)

    list_resp = client.get("/api/v1/import_jobs")
    assert list_resp.status_code == 200
    payload = list_resp.json()
    assert payload["error"] is None
    assert payload["meta"]["pagination"]["total"] >= 1
    ids = [item["id"] for item in payload["data"]]
    assert job_id in ids

    detail_resp = client.get(f"/api/v1/import_jobs/{job_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()["data"]
    assert detail["id"] == job_id

