"""
导入任务服务
Version: 1.0
Author: Claude协作开发

提供导入任务的完整生命周期管理，包括：
- 文件上传与验证
- CSV解析
- 任务状态管理
- 进度追踪
- 错误处理
"""

import csv
import hashlib
import io
from datetime import datetime
from decimal import Decimal
from math import ceil
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from backend.models import ImportJob, User
from backend.models.enums import ImportJobStatus, ImportJobType, UserRole
from backend.schemas.import_job import (
    ImportJobUploadRequest,
    ImportJobStatisticsResponse,
)
from backend.utils.id_generator import generate_request_no
from backend.exceptions.custom_exceptions import (
    ValidationError,
    ResourceNotFoundError,
    PermissionDeniedError,
    BusinessLogicError
)


class ImportJobService:
    """导入任务服务类"""

    def __init__(self, db: Session):
        self.db = db

    # ========== 基础 CRUD ==========

    async def create_job(
        self,
        job_type: str,
        file_name: str,
        file_hash: str,
        file_size: int,
        current_user_id: UUID
    ) -> ImportJob:
        """
        创建导入任务

        Args:
            job_type: 导入类型
            file_name: 文件名
            file_hash: 文件哈希
            file_size: 文件大小
            current_user_id: 当前用户ID

        Returns:
            ImportJob: 创建的任务
        """
        # 检查是否有相同哈希的任务（去重）
        existing = ImportJob.get_by_hash(self.db, file_hash)
        if existing and existing.status in [ImportJobStatus.COMPLETED.value, ImportJobStatus.PROCESSING.value]:
            raise BusinessLogicError(
                message="相同文件已存在或正在处理中",
                error_code="IMPORT-001"
            )

        # 生成任务编号
        job_no = generate_request_no("IMP")

        # 创建任务
        job = ImportJob(
            job_no=job_no,
            type=job_type,
            status=ImportJobStatus.PENDING.value,
            file_name=file_name,
            file_hash=file_hash,
            file_size=file_size,
            created_by=current_user_id,
            updated_by=current_user_id
        )

        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        return job

    async def get_job_by_id(
        self,
        job_id: int,
        current_user_id: UUID = None,
        user_role: str = None
    ) -> ImportJob:
        """
        获取导入任务详情

        Args:
            job_id: 任务ID
            current_user_id: 当前用户ID
            user_role: 用户角色

        Returns:
            ImportJob: 任务详情
        """
        job = self.db.query(ImportJob).filter(ImportJob.id == job_id).first()

        if not job:
            raise ResourceNotFoundError(
                message="导入任务不存在",
                error_code="SYS-004"
            )

        # 权限检查
        if user_role and user_role not in [UserRole.ADMIN.value, UserRole.DATA_OPERATOR.value, UserRole.FINANCE.value]:
            if job.created_by != current_user_id:
                raise PermissionDeniedError(
                    message="无权限访问此导入任务",
                    error_code="AUTH-003"
                )

        return job

    async def get_jobs(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        job_type: Optional[str] = None,
        current_user_id: UUID = None,
        user_role: str = None
    ) -> Tuple[List[ImportJob], int]:
        """
        获取导入任务列表

        Args:
            page: 页码
            page_size: 每页数量
            status: 状态过滤
            job_type: 类型过滤
            current_user_id: 当前用户ID
            user_role: 用户角色

        Returns:
            Tuple[List[ImportJob], int]: (任务列表, 总数)
        """
        # 根据角色构建查询
        if user_role in [UserRole.ADMIN.value, UserRole.DATA_OPERATOR.value, UserRole.FINANCE.value]:
            query = self.db.query(ImportJob)
        else:
            query = self.db.query(ImportJob).filter(ImportJob.created_by == current_user_id)

        # 应用过滤条件
        if status:
            query = query.filter(ImportJob.status == status)
        if job_type:
            query = query.filter(ImportJob.type == job_type)

        # 计算总数
        total = query.count()

        # 分页
        jobs = query.order_by(
            ImportJob.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return jobs, total

    async def update_job(
        self,
        job_id: int,
        updates: Dict[str, Any],
        current_user_id: UUID
    ) -> ImportJob:
        """
        更新导入任务

        Args:
            job_id: 任务ID
            updates: 更新字段
            current_user_id: 当前用户ID

        Returns:
            ImportJob: 更新后的任务
        """
        job = await self.get_job_by_id(job_id)

        # 终态不可修改
        if job.is_terminal:
            raise BusinessLogicError(
                message="任务已完成，无法修改",
                error_code="STATE-400"
            )

        # 更新字段
        for key, value in updates.items():
            if hasattr(job, key):
                setattr(job, key, value)

        job.updated_by = current_user_id
        job.version += 1

        self.db.commit()
        self.db.refresh(job)

        return job

    async def delete_job(
        self,
        job_id: int,
        current_user_id: UUID
    ) -> bool:
        """
        删除导入任务（仅 pending 状态）

        Args:
            job_id: 任务ID
            current_user_id: 当前用户ID

        Returns:
            bool: 是否删除成功
        """
        job = await self.get_job_by_id(job_id)

        if job.status != ImportJobStatus.PENDING.value:
            raise BusinessLogicError(
                message="只能删除待处理的任务",
                error_code="STATE-400"
            )

        self.db.delete(job)
        self.db.commit()

        return True

    # ========== 文件处理 ==========

    async def upload_and_parse(
        self,
        file_content: bytes,
        file_name: str,
        job_type: str,
        current_user_id: UUID
    ) -> Tuple[ImportJob, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        上传并解析文件

        Args:
            file_content: 文件内容
            file_name: 文件名
            job_type: 导入类型
            current_user_id: 当前用户ID

        Returns:
            Tuple[ImportJob, List[Dict], List[Dict]]: (任务, 解析的行, 错误列表)
        """
        if not file_content:
            raise ValidationError(
                message="文件内容为空",
                error_code="VAL-001"
            )

        # 计算文件哈希
        file_hash = hashlib.sha256(file_content).hexdigest()
        file_size = len(file_content)

        # 解析文件
        parsed_rows = []
        errors = []

        try:
            if file_name.lower().endswith('.csv'):
                parsed_rows, errors = self._parse_csv(file_content)
            else:
                errors.append({"row": 0, "error": "仅支持 CSV 文件"})
        except Exception as e:
            errors.append({"row": 0, "error": f"文件解析失败: {str(e)}"})

        # 确定状态
        if errors and not parsed_rows:
            status = ImportJobStatus.FAILED.value
        elif errors:
            status = ImportJobStatus.PENDING.value  # 有部分错误但仍可处理
        else:
            status = ImportJobStatus.COMPLETED.value

        # 创建任务
        job_no = generate_request_no("IMP")
        job = ImportJob(
            job_no=job_no,
            type=job_type,
            status=status,
            file_name=file_name,
            file_hash=file_hash,
            file_size=file_size,
            total_rows=len(parsed_rows) + len(errors),
            processed_rows=len(parsed_rows) + len(errors),
            success_rows=len(parsed_rows),
            failed_rows=len(errors),
            error_log=errors if errors else None,
            created_by=current_user_id,
            updated_by=current_user_id
        )

        if status == ImportJobStatus.COMPLETED.value:
            job.completed_at = func.now()
            job.result_summary = {
                "total_rows": len(parsed_rows),
                "success_rows": len(parsed_rows),
                "failed_rows": 0
            }

        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        return job, parsed_rows, errors

    def _parse_csv(self, content: bytes) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        解析CSV文件

        Args:
            content: 文件内容

        Returns:
            Tuple[List[Dict], List[Dict]]: (解析的行, 错误列表)
        """
        parsed_rows = []
        errors = []

        try:
            # 尝试检测编码
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                text = content.decode('gbk')

            reader = csv.DictReader(io.StringIO(text))

            for row_num, row in enumerate(reader, start=2):  # 从第2行开始（第1行是表头）
                try:
                    # 基础数据清洗
                    cleaned_row = {}
                    for key, value in row.items():
                        if key:  # 跳过空键
                            cleaned_row[key.strip()] = value.strip() if value else None
                    parsed_rows.append(cleaned_row)
                except Exception as e:
                    errors.append({
                        "row": row_num,
                        "error": str(e),
                        "data": dict(row) if row else None
                    })

        except Exception as e:
            errors.append({"row": 0, "error": f"CSV解析失败: {str(e)}"})

        return parsed_rows, errors

    # ========== 状态转换 ==========

    async def start_processing(
        self,
        job_id: int,
        current_user_id: UUID
    ) -> ImportJob:
        """
        开始处理任务

        Args:
            job_id: 任务ID
            current_user_id: 当前用户ID

        Returns:
            ImportJob: 更新后的任务
        """
        job = await self.get_job_by_id(job_id)

        if job.status != ImportJobStatus.PENDING.value:
            raise BusinessLogicError(
                message=f"只能从待处理状态开始处理，当前状态: {job.status}",
                error_code="STATE-400"
            )

        job.start_processing()
        job.updated_by = current_user_id

        self.db.commit()
        self.db.refresh(job)

        return job

    async def complete_job(
        self,
        job_id: int,
        success_rows: int,
        failed_rows: int,
        result_summary: Dict[str, Any] = None,
        current_user_id: UUID = None
    ) -> ImportJob:
        """
        完成任务

        Args:
            job_id: 任务ID
            success_rows: 成功行数
            failed_rows: 失败行数
            result_summary: 结果摘要
            current_user_id: 当前用户ID

        Returns:
            ImportJob: 更新后的任务
        """
        job = await self.get_job_by_id(job_id)

        if job.status != ImportJobStatus.PROCESSING.value:
            raise BusinessLogicError(
                message=f"只能从处理中状态完成，当前状态: {job.status}",
                error_code="STATE-400"
            )

        job.complete(success_rows, failed_rows, result_summary)
        if current_user_id:
            job.updated_by = current_user_id

        self.db.commit()
        self.db.refresh(job)

        return job

    async def fail_job(
        self,
        job_id: int,
        error_message: str,
        error_log: List[Dict[str, Any]] = None,
        current_user_id: UUID = None
    ) -> ImportJob:
        """
        标记任务失败

        Args:
            job_id: 任务ID
            error_message: 错误消息
            error_log: 错误日志
            current_user_id: 当前用户ID

        Returns:
            ImportJob: 更新后的任务
        """
        job = await self.get_job_by_id(job_id)

        if job.status != ImportJobStatus.PROCESSING.value:
            raise BusinessLogicError(
                message=f"只能从处理中状态标记失败，当前状态: {job.status}",
                error_code="STATE-400"
            )

        job.fail(error_message, error_log)
        if current_user_id:
            job.updated_by = current_user_id

        self.db.commit()
        self.db.refresh(job)

        return job

    async def cancel_job(
        self,
        job_id: int,
        current_user_id: UUID,
        user_role: str
    ) -> ImportJob:
        """
        取消任务

        Args:
            job_id: 任务ID
            current_user_id: 当前用户ID
            user_role: 用户角色

        Returns:
            ImportJob: 更新后的任务
        """
        job = await self.get_job_by_id(job_id)

        if job.status != ImportJobStatus.PENDING.value:
            raise BusinessLogicError(
                message=f"只能取消待处理状态的任务，当前状态: {job.status}",
                error_code="STATE-400"
            )

        # 权限检查
        if not job.can_be_cancelled_by(current_user_id, UserRole(user_role)):
            raise PermissionDeniedError(
                message="无权限取消此任务",
                error_code="AUTH-003"
            )

        job.cancel(current_user_id)
        self.db.commit()
        self.db.refresh(job)

        return job

    # ========== 进度更新 ==========

    async def update_progress(
        self,
        job_id: int,
        processed: int,
        success: int = None,
        failed: int = None
    ) -> ImportJob:
        """
        更新处理进度

        Args:
            job_id: 任务ID
            processed: 已处理行数
            success: 成功行数
            failed: 失败行数

        Returns:
            ImportJob: 更新后的任务
        """
        job = await self.get_job_by_id(job_id)

        if job.status != ImportJobStatus.PROCESSING.value:
            raise BusinessLogicError(
                message="只能更新处理中任务的进度",
                error_code="STATE-400"
            )

        job.update_progress(processed, success, failed)
        self.db.commit()
        self.db.refresh(job)

        return job

    async def add_error(
        self,
        job_id: int,
        row: int,
        error: str,
        data: Dict[str, Any] = None
    ) -> ImportJob:
        """
        添加错误记录

        Args:
            job_id: 任务ID
            row: 行号
            error: 错误信息
            data: 原始数据

        Returns:
            ImportJob: 更新后的任务
        """
        job = await self.get_job_by_id(job_id)
        job.add_error(row, error, data)
        self.db.commit()
        self.db.refresh(job)

        return job

    # ========== 统计查询 ==========

    async def get_statistics(
        self,
        current_user_id: UUID = None,
        user_role: str = None
    ) -> ImportJobStatisticsResponse:
        """
        获取导入任务统计

        Args:
            current_user_id: 当前用户ID
            user_role: 用户角色

        Returns:
            ImportJobStatisticsResponse: 统计响应
        """
        # 构建基础查询
        if user_role in [UserRole.ADMIN.value, UserRole.DATA_OPERATOR.value, UserRole.FINANCE.value]:
            query = self.db.query(ImportJob)
        else:
            query = self.db.query(ImportJob).filter(ImportJob.created_by == current_user_id)

        # 总数统计
        total_jobs = query.count()
        pending_jobs = query.filter(ImportJob.status == ImportJobStatus.PENDING.value).count()
        processing_jobs = query.filter(ImportJob.status == ImportJobStatus.PROCESSING.value).count()
        completed_jobs = query.filter(ImportJob.status == ImportJobStatus.COMPLETED.value).count()
        failed_jobs = query.filter(ImportJob.status == ImportJobStatus.FAILED.value).count()
        cancelled_jobs = query.filter(ImportJob.status == ImportJobStatus.CANCELLED.value).count()

        # 行数统计
        row_stats = query.with_entities(
            func.sum(ImportJob.processed_rows).label('total_processed'),
            func.sum(ImportJob.success_rows).label('total_success'),
            func.sum(ImportJob.failed_rows).label('total_failed')
        ).first()

        total_rows_processed = int(row_stats.total_processed or 0)
        total_rows_success = int(row_stats.total_success or 0)
        total_rows_failed = int(row_stats.total_failed or 0)

        # 成功率
        overall_success_rate = 0.0
        if total_rows_processed > 0:
            overall_success_rate = round(total_rows_success / total_rows_processed * 100, 2)

        # 按类型统计
        by_type = {}
        for job_type in ImportJobType:
            count = query.filter(ImportJob.type == job_type.value).count()
            by_type[job_type.value] = count

        # 最近任务
        recent_jobs = query.order_by(ImportJob.created_at.desc()).limit(10).all()
        recent_jobs_data = [
            {
                "id": job.id,
                "job_no": job.job_no,
                "type": job.type,
                "status": job.status,
                "file_name": job.file_name,
                "created_at": job.created_at.isoformat() if job.created_at else None
            }
            for job in recent_jobs
        ]

        return ImportJobStatisticsResponse(
            total_jobs=total_jobs,
            pending_jobs=pending_jobs,
            processing_jobs=processing_jobs,
            completed_jobs=completed_jobs,
            failed_jobs=failed_jobs,
            cancelled_jobs=cancelled_jobs,
            overall_success_rate=overall_success_rate,
            total_rows_processed=total_rows_processed,
            total_rows_success=total_rows_success,
            total_rows_failed=total_rows_failed,
            by_type=by_type,
            recent_jobs=recent_jobs_data
        )

    async def check_duplicate(self, file_hash: str) -> Optional[ImportJob]:
        """
        检查是否有重复文件

        Args:
            file_hash: 文件哈希

        Returns:
            Optional[ImportJob]: 如果存在重复则返回已有任务
        """
        return ImportJob.get_by_hash(self.db, file_hash)
