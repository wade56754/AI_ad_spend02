"""
导入任务模型 - 数据导入流程管理

提供CSV/Excel文件导入跟踪，支持：
- 文件上传与验证
- 处理进度追踪
- 错误日志记录
- 结果汇总
"""
from datetime import datetime
from uuid import UUID
from sqlalchemy import Column, BigInteger, String, Text, Integer, DateTime, Index, CheckConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base, TimestampMixin
from backend.models.enums import ImportJobStatus, ImportJobType, UserRole
from backend.models.mixins.serializable import SerializableMixin


class ImportJob(Base, TimestampMixin, SerializableMixin):
    """
    导入任务表

    字段：
    - id: 主键
    - job_no: 任务编号（唯一）
    - type: 导入类型（finance/spend/reconciliation/daily_report）
    - status: 状态（pending/processing/completed/failed/cancelled）
    - file_name: 原始文件名
    - file_path: 存储路径
    - file_hash: 文件SHA256哈希（用于去重）
    - file_size: 文件大小（字节）
    - total_rows: 总行数
    - processed_rows: 已处理行数
    - success_rows: 成功行数
    - failed_rows: 失败行数
    - error_log: 错误详情（JSONB）
    - result_summary: 处理结果摘要（JSONB）
    - started_at: 开始处理时间
    - completed_at: 完成时间
    - created_by: 创建人
    - updated_by: 更新人
    - created_at/updated_at: 时间戳（自动管理）
    """
    __tablename__ = 'import_jobs'

    # 序列化配置
    __json_include_relationships__ = ['creator', 'updater']
    __json_hidden__ = []

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="导入任务ID")

    # 业务字段
    job_no = Column(String(50), unique=True, nullable=False, comment="任务编号")
    type = Column(String(20), nullable=False, comment="导入类型")
    status = Column(String(20), nullable=False, default="pending", comment="状态")

    # 文件信息
    file_name = Column(String(255), nullable=True, comment="原始文件名")
    file_path = Column(String(500), nullable=True, comment="存储路径")
    file_hash = Column(String(64), nullable=True, index=True, comment="文件SHA256哈希")
    file_size = Column(BigInteger, nullable=True, comment="文件大小（字节）")

    # 处理进度
    total_rows = Column(Integer, nullable=True, default=0, comment="总行数")
    processed_rows = Column(Integer, nullable=True, default=0, comment="已处理行数")
    success_rows = Column(Integer, nullable=True, default=0, comment="成功行数")
    failed_rows = Column(Integer, nullable=True, default=0, comment="失败行数")

    # 结果详情
    error_log = Column(JSONB, nullable=True, default=list, comment="错误详情")
    result_summary = Column(JSONB, nullable=True, default=dict, comment="处理结果摘要")

    # 时间字段
    started_at = Column(DateTime(timezone=True), nullable=True, comment="开始处理时间")
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="完成时间")

    # 外键
    created_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="创建人ID"
    )
    updated_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="更新人ID"
    )

    # 并发控制
    version = Column(Integer, nullable=False, server_default='1', comment="乐观锁版本号")

    # ========== 关系定义 ==========

    # 多对一：导入任务 -> 创建人
    creator = relationship(
        "User",
        foreign_keys=[created_by],
        lazy="selectin",
        doc="创建人"
    )

    # 多对一：导入任务 -> 更新人
    updater = relationship(
        "User",
        foreign_keys=[updated_by],
        lazy="selectin",
        doc="更新人"
    )

    # 约束和索引
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')",
            name='chk_import_jobs_status'
        ),
        CheckConstraint(
            "type IN ('finance', 'spend', 'reconciliation', 'daily_report')",
            name='chk_import_jobs_type'
        ),
        Index('idx_import_jobs_job_no', 'job_no'),
        Index('idx_import_jobs_status', 'status'),
        Index('idx_import_jobs_type', 'type'),
        Index('idx_import_jobs_created_by', 'created_by'),
        Index('idx_import_jobs_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<ImportJob(id={self.id}, job_no='{self.job_no}', type='{self.type}', status='{self.status}')>"

    # ========== 业务属性 ==========

    @property
    def status_enum(self) -> ImportJobStatus:
        """返回状态枚举对象"""
        return ImportJobStatus(self.status)

    @property
    def type_enum(self) -> ImportJobType:
        """返回类型枚举对象"""
        return ImportJobType(self.type)

    @property
    def is_pending(self) -> bool:
        """是否待处理"""
        return self.status == ImportJobStatus.PENDING.value

    @property
    def is_processing(self) -> bool:
        """是否处理中"""
        return self.status == ImportJobStatus.PROCESSING.value

    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.status == ImportJobStatus.COMPLETED.value

    @property
    def is_failed(self) -> bool:
        """是否失败"""
        return self.status == ImportJobStatus.FAILED.value

    @property
    def is_cancelled(self) -> bool:
        """是否已取消"""
        return self.status == ImportJobStatus.CANCELLED.value

    @property
    def is_terminal(self) -> bool:
        """是否为终态"""
        return self.status in [
            ImportJobStatus.COMPLETED.value,
            ImportJobStatus.FAILED.value,
            ImportJobStatus.CANCELLED.value
        ]

    @property
    def progress_percent(self) -> float:
        """处理进度百分比"""
        if not self.total_rows or self.total_rows == 0:
            return 0.0
        return round((self.processed_rows or 0) / self.total_rows * 100, 2)

    @property
    def success_rate(self) -> float:
        """成功率百分比"""
        if not self.processed_rows or self.processed_rows == 0:
            return 0.0
        return round((self.success_rows or 0) / self.processed_rows * 100, 2)

    # ========== 状态流转方法 ==========

    def can_transition_to(self, new_status: ImportJobStatus) -> bool:
        """
        检查是否可以转换到新状态

        状态流转规则：
        - pending -> processing, cancelled
        - processing -> completed, failed
        - completed -> (终态)
        - failed -> (终态)
        - cancelled -> (终态)
        """
        current = ImportJobStatus(self.status)
        transitions = {
            ImportJobStatus.PENDING: [ImportJobStatus.PROCESSING, ImportJobStatus.CANCELLED],
            ImportJobStatus.PROCESSING: [ImportJobStatus.COMPLETED, ImportJobStatus.FAILED],
            ImportJobStatus.COMPLETED: [],
            ImportJobStatus.FAILED: [],
            ImportJobStatus.CANCELLED: [],
        }
        return new_status in transitions.get(current, [])

    def start_processing(self):
        """开始处理"""
        if not self.can_transition_to(ImportJobStatus.PROCESSING):
            raise ValueError(f"不允许从 {self.status} 状态开始处理")

        self.status = ImportJobStatus.PROCESSING.value
        self.started_at = func.now()
        self.version += 1

    def complete(self, success_rows: int, failed_rows: int, result_summary: dict = None):
        """标记为已完成"""
        if not self.can_transition_to(ImportJobStatus.COMPLETED):
            raise ValueError(f"不允许从 {self.status} 状态标记完成")

        self.status = ImportJobStatus.COMPLETED.value
        self.success_rows = success_rows
        self.failed_rows = failed_rows
        self.processed_rows = success_rows + failed_rows
        self.completed_at = func.now()
        if result_summary:
            self.result_summary = result_summary
        self.version += 1

    def fail(self, error_message: str, error_log: list = None):
        """标记为失败"""
        if not self.can_transition_to(ImportJobStatus.FAILED):
            raise ValueError(f"不允许从 {self.status} 状态标记失败")

        self.status = ImportJobStatus.FAILED.value
        self.completed_at = func.now()
        if error_log:
            self.error_log = error_log
        else:
            self.error_log = [{"error": error_message}]
        self.version += 1

    def cancel(self, user_id: UUID):
        """取消任务"""
        if not self.can_transition_to(ImportJobStatus.CANCELLED):
            raise ValueError(f"不允许从 {self.status} 状态取消任务")

        self.status = ImportJobStatus.CANCELLED.value
        self.updated_by = user_id
        self.completed_at = func.now()
        self.version += 1

    def add_error(self, row: int, error: str, data: dict = None):
        """添加错误记录"""
        if self.error_log is None:
            self.error_log = []

        error_entry = {"row": row, "error": error}
        if data:
            error_entry["data"] = data

        self.error_log.append(error_entry)
        self.failed_rows = (self.failed_rows or 0) + 1

    def update_progress(self, processed: int, success: int = None, failed: int = None):
        """更新处理进度"""
        self.processed_rows = processed
        if success is not None:
            self.success_rows = success
        if failed is not None:
            self.failed_rows = failed

    # ========== 权限判断方法 ==========

    def can_be_cancelled_by(self, user_id: UUID, user_role: UserRole) -> bool:
        """检查用户是否可以取消此任务"""
        # 只有待处理状态可以取消
        if self.status != ImportJobStatus.PENDING.value:
            return False

        # 管理员可以取消所有任务
        if user_role == UserRole.ADMIN:
            return True

        # 创建者可以取消自己的任务
        return self.created_by == user_id

    def can_be_viewed_by(self, user_id: UUID, user_role: UserRole) -> bool:
        """检查用户是否可以查看此任务"""
        # 管理员和数据员可以查看所有任务
        if user_role in [UserRole.ADMIN, UserRole.DATA_OPERATOR, UserRole.FINANCE]:
            return True

        # 其他用户只能查看自己的任务
        return self.created_by == user_id

    # ========== 查询作用域方法 ==========

    @classmethod
    def get_user_accessible_query(cls, session, user_id: UUID, user_role: UserRole):
        """获取用户可访问的导入任务查询"""
        query = session.query(cls)

        # 管理员、数据员、财务可以访问所有任务
        if user_role in [UserRole.ADMIN, UserRole.DATA_OPERATOR, UserRole.FINANCE]:
            return query

        # 其他用户只能访问自己创建的任务
        return query.filter(cls.created_by == user_id)

    @classmethod
    def get_by_hash(cls, session, file_hash: str):
        """根据文件哈希查找任务"""
        return session.query(cls).filter(cls.file_hash == file_hash).first()

    @classmethod
    def get_pending_jobs(cls, session):
        """获取待处理的任务"""
        return session.query(cls).filter(
            cls.status == ImportJobStatus.PENDING.value
        ).order_by(
            cls.created_at.asc()
        ).all()

    @classmethod
    def get_processing_jobs(cls, session):
        """获取处理中的任务"""
        return session.query(cls).filter(
            cls.status == ImportJobStatus.PROCESSING.value
        ).order_by(
            cls.started_at.asc()
        ).all()
