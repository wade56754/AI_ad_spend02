"""
数据导入任务路由

提供导入任务的 API 接口。
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.error_codes import BusinessErrorCodes, ValidationErrorCodes
from backend.core.response import fail, ok
from backend.core.security import AuthenticatedUser, get_current_user
from backend.models import ImportJobType, ImportJobStatus
from backend.services.import_job_service import ImportJobService
from backend.services.log_service import LogService

router = APIRouter(prefix="/import_jobs", tags=["import_jobs"])


@router.get("", response_model=dict)
def list_import_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    type_filter: Optional[str] = Query(None, alias="type"),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    获取导入任务列表

    - **page**: 页码 (默认 1)
    - **page_size**: 每页数量 (默认 20, 最大 100)
    - **status**: 状态过滤 (pending/processing/completed/failed)
    - **type**: 类型过滤 (finance/ad_spend/leads)
    """
    # 校验 status 参数
    if status_filter and not ImportJobService.is_valid_status(status_filter):
        valid_values = [s.value for s in ImportJobStatus]
        return fail(
            ValidationErrorCodes.INVALID_ENUM_VALUE,
            f"无效的 status 值，允许: {valid_values}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # 校验 type 参数
    if type_filter and not ImportJobService.is_valid_job_type(type_filter):
        valid_values = [t.value for t in ImportJobType]
        return fail(
            ValidationErrorCodes.INVALID_ENUM_VALUE,
            f"无效的 type 值，允许: {valid_values}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    records, pagination = ImportJobService.list_jobs(
        db,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        type_filter=type_filter,
    )

    data = [ImportJobService.serialize(record) for record in records]
    return ok(data=data, meta={"pagination": pagination})


@router.get("/{job_id}", response_model=dict)
def get_import_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    根据 ID 获取导入任务详情
    """
    job = ImportJobService.get_by_id(db, job_id)
    if job is None:
        return fail(
            BusinessErrorCodes.RESOURCE_NOT_FOUND,
            "导入任务不存在",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return ok(data=ImportJobService.serialize(job))


@router.post("/upload", response_model=dict)
async def upload_import_job(
    file: UploadFile = File(...),
    job_type: str = Query("finance", alias="type"),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    上传文件创建导入任务

    - **file**: CSV 文件
    - **type**: 导入类型 (finance/ad_spend/leads, 默认 finance)
    """
    # 校验 type 参数
    if not ImportJobService.is_valid_job_type(job_type):
        valid_values = [t.value for t in ImportJobType]
        return fail(
            ValidationErrorCodes.INVALID_ENUM_VALUE,
            f"无效的 type 值，允许: {valid_values}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # 读取文件内容
    payload = await file.read()
    if not payload:
        return fail(
            BusinessErrorCodes.EMPTY_FILE,
            "文件内容为空",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # 计算文件哈希
    file_hash = ImportJobService.compute_file_hash(payload)

    # 检查文件类型
    if not (file.filename and file.filename.lower().endswith(".csv")):
        return fail(
            BusinessErrorCodes.INVALID_FILE_TYPE,
            "仅支持 CSV 文件",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # 解析 CSV
    parsed_rows, errors = ImportJobService.parse_csv(payload)

    # 确定任务状态
    status_value = ImportJobStatus.COMPLETED.value if not errors else ImportJobStatus.FAILED.value

    # 获取当前用户 ID
    created_by_uuid: Optional[UUID] = None
    try:
        created_by_uuid = UUID(str(current_user.id))
    except (TypeError, ValueError):
        created_by_uuid = None

    # 创建任务记录
    job = ImportJobService.create_job(
        db,
        job_type=job_type,
        file_path=file.filename,
        file_hash=file_hash,
        created_by=created_by_uuid,
    )

    # 更新状态和错误日志
    job = ImportJobService.update_status(
        db,
        job,
        status_value,
        error_log=errors,
        updated_by=created_by_uuid,
    )

    # 记录操作日志
    LogService.write(
        db,
        action="import_job_upload",
        operator_id=current_user.id,
        target="import_jobs",
        target_id=job.id,
        detail={"job_id": str(job.id), "type": job_type, "status": status_value},
    )

    return ok(
        data={
            "job_id": str(job.id),
            "type": job.type,
            "status": job.status,
            "rows": parsed_rows if parsed_rows else [],
            "error_log": errors,
        },
        status_code=status.HTTP_201_CREATED if status_value == ImportJobStatus.COMPLETED.value else status.HTTP_200_OK,
    )
