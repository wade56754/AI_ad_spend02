"""
导入任务路由
Version: 2.0
Author: Claude协作开发

提供导入任务的完整API端点：
- 文件上传与解析
- 任务列表与详情
- 任务状态管理
- 进度查询
- 统计信息
"""

import hashlib
from math import ceil
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.models import User, ImportJob
from backend.models.enums import ImportJobStatus, ImportJobType
from backend.schemas.import_job import (
    ImportJobResponse,
    ImportJobUploadResponse,
    ImportJobProgressResponse,
    ImportJobStatisticsResponse,
    ImportJobCancelRequest,
)
from backend.services.import_job_service import ImportJobService
from backend.services.log_service import LogService
from backend.core.dependencies import require_role
from backend.core.response import success_response, paginated_response, error_response
from backend.exceptions.custom_exceptions import (
    ValidationError,
    ResourceNotFoundError,
    PermissionDeniedError,
    BusinessLogicError
)


router = APIRouter(prefix="/import-jobs", tags=["导入任务"])


def get_import_job_service(db: Session = Depends(get_db)) -> ImportJobService:
    """获取导入任务服务实例"""
    return ImportJobService(db)


# ========== 文件上传端点 ==========

@router.post("/upload", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_import_file(
    file: UploadFile = File(..., description="CSV文件"),
    job_type: str = Query("finance", regex="^(finance|spend|reconciliation|daily_report)$", description="导入类型"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance", "data_operator"])),
    service: ImportJobService = Depends(get_import_job_service)
):
    """
    上传并解析导入文件

    - **file**: CSV格式的导入文件
    - **job_type**: 导入类型 (finance/spend/reconciliation/daily_report)

    返回解析结果和任务信息
    """
    try:
        # 读取文件内容
        file_content = await file.read()
        if not file_content:
            return error_response(code="VALIDATION_001", message="文件内容为空", status_code=400)

        # 检查文件类型
        if not file.filename or not file.filename.lower().endswith('.csv'):
            return error_response(code="VALIDATION_002", message="仅支持CSV格式文件", status_code=400)

        # 上传并解析
        job, parsed_rows, errors = await service.upload_and_parse(
            file_content=file_content,
            file_name=file.filename,
            job_type=job_type,
            current_user_id=current_user.id
        )

        # 记录日志
        LogService.write(
            db,
            action="import_job_upload",
            operator_id=current_user.id,
            target="import_jobs",
            target_id=job.id,
            detail={
                "job_id": job.id,
                "job_no": job.job_no,
                "type": job_type,
                "status": job.status,
                "file_name": file.filename,
                "total_rows": len(parsed_rows) + len(errors)
            }
        )

        # 构建响应
        response_data = ImportJobUploadResponse(
            job_id=job.id,
            job_no=job.job_no,
            status=job.status,
            file_name=job.file_name,
            file_hash=job.file_hash,
            total_rows=job.total_rows,
            parsed_rows=parsed_rows[:100] if parsed_rows else [],  # 限制返回行数
            error_log=errors,
            message="文件上传成功" if job.status == ImportJobStatus.COMPLETED.value else "文件解析完成，存在错误"
        )

        return success_response(
            data=response_data.model_dump(),
            message=response_data.message
        )

    except ValidationError as e:
        return error_response(code=e.error_code, message=str(e), status_code=400)
    except BusinessLogicError as e:
        return error_response(code=e.error_code, message=str(e), status_code=409)
    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


# ========== 任务列表与详情 ==========

@router.get("", response_model=dict)
async def list_import_jobs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status_filter: Optional[str] = Query(None, alias="status", description="状态过滤"),
    type_filter: Optional[str] = Query(None, alias="type", description="类型过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance", "data_operator", "account_manager", "media_buyer"])),
    service: ImportJobService = Depends(get_import_job_service)
):
    """
    获取导入任务列表

    支持分页和过滤：
    - **status**: 状态过滤 (pending/processing/completed/failed/cancelled)
    - **type**: 类型过滤 (finance/spend/reconciliation/daily_report)
    """
    try:
        jobs, total = await service.get_jobs(
            page=page,
            page_size=page_size,
            status=status_filter,
            job_type=type_filter,
            current_user_id=current_user.id,
            user_role=current_user.role
        )

        # 转换为响应格式
        job_responses = []
        for job in jobs:
            job_data = ImportJobResponse.model_validate(job)
            job_data.progress_percent = job.progress_percent
            job_data.success_rate = job.success_rate
            job_responses.append(job_data)

        return paginated_response(
            items=[j.model_dump() for j in job_responses],
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


@router.get("/statistics", response_model=dict)
async def get_import_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance", "data_operator"])),
    service: ImportJobService = Depends(get_import_job_service)
):
    """获取导入任务统计信息"""
    try:
        statistics = await service.get_statistics(
            current_user_id=current_user.id,
            user_role=current_user.role
        )

        return success_response(data=statistics.model_dump())

    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


@router.get("/{job_id}", response_model=dict)
async def get_import_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance", "data_operator", "account_manager", "media_buyer"])),
    service: ImportJobService = Depends(get_import_job_service)
):
    """获取导入任务详情"""
    try:
        job = await service.get_job_by_id(
            job_id,
            current_user.id,
            current_user.role
        )

        job_data = ImportJobResponse.model_validate(job)
        job_data.progress_percent = job.progress_percent
        job_data.success_rate = job.success_rate

        return success_response(data=job_data.model_dump())

    except ResourceNotFoundError as e:
        return error_response(code=e.error_code or "SYS_004", message=str(e), status_code=404)
    except PermissionDeniedError as e:
        return error_response(code=e.error_code or "AUTH_003", message=str(e), status_code=403)
    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


@router.get("/{job_id}/progress", response_model=dict)
async def get_import_job_progress(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance", "data_operator", "account_manager", "media_buyer"])),
    service: ImportJobService = Depends(get_import_job_service)
):
    """获取导入任务进度"""
    try:
        job = await service.get_job_by_id(
            job_id,
            current_user.id,
            current_user.role
        )

        progress = ImportJobProgressResponse(
            job_id=job.id,
            job_no=job.job_no,
            status=job.status,
            total_rows=job.total_rows or 0,
            processed_rows=job.processed_rows or 0,
            success_rows=job.success_rows or 0,
            failed_rows=job.failed_rows or 0,
            progress_percent=job.progress_percent,
            started_at=job.started_at
        )

        return success_response(data=progress.model_dump())

    except ResourceNotFoundError as e:
        return error_response(code=e.error_code or "SYS_004", message=str(e), status_code=404)
    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


@router.get("/{job_id}/errors", response_model=dict)
async def get_import_job_errors(
    job_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance", "data_operator"])),
    service: ImportJobService = Depends(get_import_job_service)
):
    """获取导入任务错误详情"""
    try:
        job = await service.get_job_by_id(
            job_id,
            current_user.id,
            current_user.role
        )

        error_log = job.error_log or []
        total = len(error_log)

        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        paginated_errors = error_log[start:end]

        return paginated_response(
            items=paginated_errors,
            total=total,
            page=page,
            page_size=page_size
        )

    except ResourceNotFoundError as e:
        return error_response(code=e.error_code or "SYS_004", message=str(e), status_code=404)
    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


# ========== 任务操作端点 ==========

@router.post("/{job_id}/start", response_model=dict)
async def start_import_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance", "data_operator"])),
    service: ImportJobService = Depends(get_import_job_service)
):
    """
    开始处理导入任务

    状态转换: pending → processing
    """
    try:
        job = await service.start_processing(job_id, current_user.id)

        LogService.write(
            db,
            action="import_job_start",
            operator_id=current_user.id,
            target="import_jobs",
            target_id=job.id,
            detail={"job_no": job.job_no, "status": job.status}
        )

        return success_response(
            data=ImportJobResponse.model_validate(job).model_dump(),
            message="任务已开始处理"
        )

    except BusinessLogicError as e:
        return error_response(code=e.error_code, message=str(e), status_code=400)
    except ResourceNotFoundError as e:
        return error_response(code=e.error_code or "SYS_004", message=str(e), status_code=404)
    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


@router.post("/{job_id}/cancel", response_model=dict)
async def cancel_import_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance", "data_operator"])),
    service: ImportJobService = Depends(get_import_job_service)
):
    """
    取消导入任务

    状态转换: pending → cancelled
    """
    try:
        job = await service.cancel_job(job_id, current_user.id, current_user.role)

        LogService.write(
            db,
            action="import_job_cancel",
            operator_id=current_user.id,
            target="import_jobs",
            target_id=job.id,
            detail={"job_no": job.job_no, "status": job.status}
        )

        return success_response(
            data=ImportJobResponse.model_validate(job).model_dump(),
            message="任务已取消"
        )

    except BusinessLogicError as e:
        return error_response(code=e.error_code, message=str(e), status_code=400)
    except PermissionDeniedError as e:
        return error_response(code=e.error_code or "AUTH_003", message=str(e), status_code=403)
    except ResourceNotFoundError as e:
        return error_response(code=e.error_code or "SYS_004", message=str(e), status_code=404)
    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


@router.delete("/{job_id}", response_model=dict)
async def delete_import_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
    service: ImportJobService = Depends(get_import_job_service)
):
    """
    删除导入任务（仅admin，仅pending状态）
    """
    try:
        # 先获取任务信息用于日志
        job = await service.get_job_by_id(job_id)
        job_no = job.job_no

        await service.delete_job(job_id, current_user.id)

        LogService.write(
            db,
            action="import_job_delete",
            operator_id=current_user.id,
            target="import_jobs",
            target_id=job_id,
            detail={"job_no": job_no}
        )

        return success_response(message="任务已删除")

    except BusinessLogicError as e:
        return error_response(code=e.error_code, message=str(e), status_code=400)
    except ResourceNotFoundError as e:
        return error_response(code=e.error_code or "SYS_004", message=str(e), status_code=404)
    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


# ========== 重复检查端点 ==========

@router.post("/check-duplicate", response_model=dict)
async def check_duplicate_file(
    file: UploadFile = File(..., description="要检查的文件"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance", "data_operator"])),
    service: ImportJobService = Depends(get_import_job_service)
):
    """
    检查文件是否已导入过

    根据文件哈希检查是否有重复导入
    """
    try:
        file_content = await file.read()
        if not file_content:
            return error_response(code="VALIDATION_001", message="文件内容为空", status_code=400)

        file_hash = hashlib.sha256(file_content).hexdigest()
        existing_job = await service.check_duplicate(file_hash)

        if existing_job:
            return success_response(
                data={
                    "is_duplicate": True,
                    "existing_job": {
                        "id": existing_job.id,
                        "job_no": existing_job.job_no,
                        "status": existing_job.status,
                        "file_name": existing_job.file_name,
                        "created_at": existing_job.created_at.isoformat() if existing_job.created_at else None
                    }
                },
                message="文件已存在"
            )

        return success_response(
            data={"is_duplicate": False, "file_hash": file_hash},
            message="文件未导入过"
        )

    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)
