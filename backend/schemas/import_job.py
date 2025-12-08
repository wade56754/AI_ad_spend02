"""
导入任务数据模型
Version: 1.0
Author: Claude协作开发
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator


class ImportJobStatusEnum(str, Enum):
    """导入任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ImportJobTypeEnum(str, Enum):
    """导入任务类型枚举"""
    FINANCE = "finance"
    SPEND = "spend"
    RECONCILIATION = "reconciliation"
    DAILY_REPORT = "daily_report"


# ========== 请求模型 ==========

class ImportJobCreateRequest(BaseModel):
    """创建导入任务请求"""
    model_config = ConfigDict(from_attributes=True)

    type: str = Field(
        ...,
        pattern="^(finance|spend|reconciliation|daily_report)$",
        description="导入类型"
    )
    notes: Optional[str] = Field(None, max_length=1000, description="备注说明")


class ImportJobUploadRequest(BaseModel):
    """上传文件请求（配合文件上传使用）"""
    model_config = ConfigDict(from_attributes=True)

    type: str = Field(
        "finance",
        pattern="^(finance|spend|reconciliation|daily_report)$",
        description="导入类型"
    )
    auto_process: bool = Field(True, description="是否自动处理")


class ImportJobCancelRequest(BaseModel):
    """取消导入任务请求"""
    model_config = ConfigDict(from_attributes=True)

    reason: Optional[str] = Field(None, max_length=500, description="取消原因")


class ImportJobRetryRequest(BaseModel):
    """重试导入任务请求"""
    model_config = ConfigDict(from_attributes=True)

    skip_errors: bool = Field(False, description="是否跳过错误行继续处理")


# ========== 响应模型 ==========

class ImportJobResponse(BaseModel):
    """
    导入任务响应

    与 ImportJob 模型对齐
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_no: str = Field(..., description="任务编号")
    type: str = Field(..., description="导入类型")
    status: str = Field(..., description="状态")
    file_name: Optional[str] = Field(None, description="原始文件名")
    file_path: Optional[str] = Field(None, description="存储路径")
    file_hash: Optional[str] = Field(None, description="文件哈希")
    file_size: Optional[int] = Field(None, description="文件大小（字节）")
    total_rows: Optional[int] = Field(None, description="总行数")
    processed_rows: Optional[int] = Field(None, description="已处理行数")
    success_rows: Optional[int] = Field(None, description="成功行数")
    failed_rows: Optional[int] = Field(None, description="失败行数")
    error_log: Optional[List[Dict[str, Any]]] = Field(None, description="错误详情")
    result_summary: Optional[Dict[str, Any]] = Field(None, description="处理结果摘要")
    started_at: Optional[datetime] = Field(None, description="开始处理时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    created_by: Optional[str] = Field(None, description="创建人ID")
    created_at: datetime
    updated_at: datetime

    # 计算字段
    progress_percent: Optional[float] = Field(None, description="处理进度百分比")
    success_rate: Optional[float] = Field(None, description="成功率百分比")

    @property
    def is_terminal(self) -> bool:
        """是否为终态"""
        return self.status in ["completed", "failed", "cancelled"]


class ImportJobListResponse(BaseModel):
    """导入任务列表响应"""
    items: List[ImportJobResponse]
    meta: dict


class ImportJobUploadResponse(BaseModel):
    """文件上传响应"""
    model_config = ConfigDict(from_attributes=True)

    job_id: int = Field(..., description="任务ID")
    job_no: str = Field(..., description="任务编号")
    status: str = Field(..., description="状态")
    file_name: Optional[str] = Field(None, description="文件名")
    file_hash: Optional[str] = Field(None, description="文件哈希")
    total_rows: Optional[int] = Field(None, description="总行数")
    parsed_rows: Optional[List[Dict[str, Any]]] = Field(None, description="解析的数据行")
    error_log: Optional[List[Dict[str, Any]]] = Field(None, description="错误信息")
    message: str = Field(..., description="处理消息")


class ImportJobProgressResponse(BaseModel):
    """导入任务进度响应"""
    model_config = ConfigDict(from_attributes=True)

    job_id: int
    job_no: str
    status: str
    total_rows: int = Field(0)
    processed_rows: int = Field(0)
    success_rows: int = Field(0)
    failed_rows: int = Field(0)
    progress_percent: float = Field(0.0)
    started_at: Optional[datetime] = None
    estimated_remaining_seconds: Optional[int] = None


class ImportJobStatisticsResponse(BaseModel):
    """导入任务统计响应"""
    model_config = ConfigDict(from_attributes=True)

    # 总体统计
    total_jobs: int = Field(0, description="总任务数")
    pending_jobs: int = Field(0, description="待处理任务")
    processing_jobs: int = Field(0, description="处理中任务")
    completed_jobs: int = Field(0, description="已完成任务")
    failed_jobs: int = Field(0, description="失败任务")
    cancelled_jobs: int = Field(0, description="已取消任务")

    # 成功率统计
    overall_success_rate: float = Field(0.0, description="整体成功率")
    total_rows_processed: int = Field(0, description="总处理行数")
    total_rows_success: int = Field(0, description="成功行数")
    total_rows_failed: int = Field(0, description="失败行数")

    # 按类型统计
    by_type: Dict[str, int] = Field(default_factory=dict, description="按类型统计")

    # 最近任务
    recent_jobs: List[Dict[str, Any]] = Field(default_factory=list, description="最近任务")


class ImportJobErrorDetail(BaseModel):
    """错误详情"""
    row: int = Field(..., description="行号")
    error: str = Field(..., description="错误信息")
    data: Optional[Dict[str, Any]] = Field(None, description="原始数据")


class ImportJobResultSummary(BaseModel):
    """处理结果摘要"""
    total_rows: int = Field(0)
    success_rows: int = Field(0)
    failed_rows: int = Field(0)
    skipped_rows: int = Field(0)
    duplicated_rows: int = Field(0)
    processing_time_seconds: float = Field(0.0)
    errors_by_type: Dict[str, int] = Field(default_factory=dict)


# ========== 导出数据模型 ==========

class ImportJobExportData(BaseModel):
    """导入任务导出数据"""
    job_no: str
    type: str
    status: str
    file_name: Optional[str]
    total_rows: int
    success_rows: int
    failed_rows: int
    success_rate: float
    created_by: Optional[str]
    created_at: str
    completed_at: Optional[str]
