"""
数据导入任务服务

提供 ImportJob 的 CRUD 操作和业务逻辑。
"""

import csv
import hashlib
import io
from math import ceil
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from backend.models import ImportJob, ImportJobType, ImportJobStatus


class ImportJobService:
    """数据导入任务服务类"""

    @staticmethod
    def list_jobs(
        db: Session,
        *,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
        type_filter: Optional[str] = None,
    ) -> Tuple[List[ImportJob], Dict[str, Any]]:
        """
        获取导入任务列表

        Args:
            db: 数据库会话
            page: 页码
            page_size: 每页数量
            status_filter: 状态过滤
            type_filter: 类型过滤

        Returns:
            (任务列表, 分页信息)
        """
        query = db.query(ImportJob)

        if status_filter:
            query = query.filter(ImportJob.status == status_filter)
        if type_filter:
            query = query.filter(ImportJob.type == type_filter)

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

        return records, pagination

    @staticmethod
    def get_by_id(db: Session, job_id: UUID) -> Optional[ImportJob]:
        """
        根据 ID 获取导入任务

        Args:
            db: 数据库会话
            job_id: 任务 ID

        Returns:
            ImportJob 或 None
        """
        return db.query(ImportJob).filter(ImportJob.id == job_id).first()

    @staticmethod
    def create_job(
        db: Session,
        *,
        job_type: str,
        file_path: Optional[str] = None,
        file_hash: Optional[str] = None,
        created_by: Optional[UUID] = None,
    ) -> ImportJob:
        """
        创建导入任务

        Args:
            db: 数据库会话
            job_type: 任务类型 (finance/ad_spend/leads)
            file_path: 文件路径
            file_hash: 文件哈希
            created_by: 创建者 ID

        Returns:
            新创建的 ImportJob
        """
        job = ImportJob(
            id=uuid4(),
            type=job_type,
            status=ImportJobStatus.PENDING.value,
            file_path=file_path,
            file_hash=file_hash,
            error_log=[],
            created_by=created_by,
            updated_by=created_by,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def update_status(
        db: Session,
        job: ImportJob,
        new_status: str,
        *,
        error_log: Optional[List[Dict[str, Any]]] = None,
        updated_by: Optional[UUID] = None,
    ) -> ImportJob:
        """
        更新任务状态

        Args:
            db: 数据库会话
            job: 任务对象
            new_status: 新状态
            error_log: 错误日志
            updated_by: 更新者 ID

        Returns:
            更新后的 ImportJob
        """
        job.status = new_status
        if error_log is not None:
            job.error_log = error_log
        if updated_by:
            job.updated_by = updated_by
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def check_duplicate(db: Session, file_hash: str) -> Optional[ImportJob]:
        """
        检查是否存在重复文件

        Args:
            db: 数据库会话
            file_hash: 文件 SHA256 哈希

        Returns:
            已存在的 ImportJob 或 None
        """
        return db.query(ImportJob).filter(ImportJob.file_hash == file_hash).first()

    @staticmethod
    def parse_csv(content: bytes) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        解析 CSV 文件

        Args:
            content: 文件内容

        Returns:
            (解析结果, 错误列表)
        """
        errors: List[Dict[str, Any]] = []
        rows: List[Dict[str, Any]] = []

        try:
            text = content.decode("utf-8")
            reader = csv.DictReader(io.StringIO(text))
            rows = [row for row in reader]
            if not rows:
                errors.append({"row": 0, "error": "文件没有数据"})
        except UnicodeDecodeError:
            errors.append({"row": 0, "error": "文件编码错误，请使用 UTF-8 编码"})
        except Exception as exc:
            errors.append({"row": 0, "error": str(exc)})

        return rows, errors

    @staticmethod
    def compute_file_hash(content: bytes) -> str:
        """
        计算文件 SHA256 哈希

        Args:
            content: 文件内容

        Returns:
            哈希值
        """
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def serialize(job: ImportJob) -> Dict[str, Any]:
        """
        序列化 ImportJob 对象

        Args:
            job: ImportJob 对象

        Returns:
            字典表示
        """
        return {
            "id": str(job.id),
            "type": job.type,
            "status": job.status,
            "file_path": job.file_path,
            "file_hash": job.file_hash,
            "error_log": job.error_log,
            "created_by": str(job.created_by) if job.created_by else None,
            "updated_by": str(job.updated_by) if job.updated_by else None,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        }

    @staticmethod
    def is_valid_job_type(job_type: str) -> bool:
        """
        验证任务类型是否有效

        Args:
            job_type: 任务类型

        Returns:
            是否有效
        """
        return job_type in [t.value for t in ImportJobType]

    @staticmethod
    def is_valid_status(status: str) -> bool:
        """
        验证状态是否有效

        Args:
            status: 状态

        Returns:
            是否有效
        """
        return status in [s.value for s in ImportJobStatus]
