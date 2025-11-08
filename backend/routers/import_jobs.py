import csv
import hashlib
import io
from math import ceil
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.error_codes import ErrorCode
from backend.core.response import fail, ok
from backend.core.security import AuthenticatedUser, get_current_user
from backend.models import ImportJob
from backend.services.log_service import LogService

router = APIRouter(prefix="/import_jobs", tags=["import_jobs"])


def _parse_csv(content: bytes) -> List[Dict[str, Any]]:
    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    return [row for row in reader]


def _serialize_job(job: ImportJob) -> Dict[str, Any]:
    return {
        "id": str(job.id),
        "type": job.type,
        "status": job.status,
        "file_path": job.file_path,
        "file_hash": job.file_hash,
        "error_log": job.error_log,
        "created_by": str(job.created_by) if job.created_by else None,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
    }


@router.get("", response_model=dict)
def list_import_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    query = db.query(ImportJob)
    if status_filter:
        query = query.filter(ImportJob.status == status_filter)

    total = query.count()
    records = (
        query.order_by(ImportJob.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    pagination = {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": ceil(total / page_size) if page_size else 0,
    }
    data = [_serialize_job(record) for record in records]
    return ok(data=data, meta={"pagination": pagination})


@router.get("/{job_id}", response_model=dict)
def get_import_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    job = db.query(ImportJob).filter(ImportJob.id == job_id).first()
    if job is None:
        return fail(ErrorCode.INVALID_PARAM, "导入任务不存在", status_code=status.HTTP_404_NOT_FOUND)
    return ok(data=_serialize_job(job))


@router.post("/upload", response_model=dict)
async def upload_import_job(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    payload = await file.read()
    if not payload:
        return fail(ErrorCode.INVALID_PARAM, "文件内容为空", status_code=status.HTTP_400_BAD_REQUEST)

    file_hash = hashlib.sha256(payload).hexdigest()
    errors: List[Dict[str, Any]] = []
    parsed_rows: Optional[List[Dict[str, Any]]] = None

    try:
        if file.filename and file.filename.lower().endswith(".csv"):
            parsed_rows = _parse_csv(payload)
            if not parsed_rows:
                errors.append({"row": 0, "error": "文件没有数据"})
        else:
            errors.append({"row": 0, "error": "仅支持 CSV 文件"})
    except Exception as exc:  # pragma: no cover
        errors.append({"row": 0, "error": str(exc)})

    status_value = "completed" if not errors else "failed"

    created_by_uuid: Optional[UUID] = None
    try:
        created_by_uuid = UUID(str(current_user.id))
    except (TypeError, ValueError):
        created_by_uuid = None

    job = ImportJob(
        id=uuid4(),
        type="finance",
        status=status_value,
        file_path=file.filename,
        file_hash=file_hash,
        error_log=errors,
        created_by=created_by_uuid,
        updated_by=created_by_uuid,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    LogService.write(
        db,
        action="import_job_upload",
        operator_id=current_user.id,
        target="import_jobs",
        target_id=job.id,
        detail={"job_id": str(job.id), "status": status_value},
    )

    return ok(
        data={
            "job_id": str(job.id),
            "status": job.status,
            "rows": parsed_rows if parsed_rows is not None else [],
            "error_log": errors,
        },
        status_code=status.HTTP_201_CREATED if status_value == "completed" else status.HTTP_200_OK,
    )

