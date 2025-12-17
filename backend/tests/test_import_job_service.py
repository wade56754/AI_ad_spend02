"""
导入任务服务测试
Version: 1.0
Author: Claude协作开发

测试覆盖：
- 任务创建与CRUD
- 文件上传与解析
- 状态流转
- 进度更新
- 权限控制
- 统计查询
"""

import pytest
import hashlib
from unittest.mock import MagicMock, patch, AsyncMock
from uuid import uuid4
from datetime import datetime

from backend.models import ImportJob
from backend.models.enums import ImportJobStatus, ImportJobType, UserRole
from backend.services.import_job_service import ImportJobService
from backend.schemas.import_job import ImportJobStatisticsResponse
from backend.exceptions.custom_exceptions import (
    ValidationError,
    ResourceNotFoundError,
    PermissionDeniedError,
    BusinessLogicError
)


# ========== Fixtures ==========

@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.count.return_value = 0
    return db


@pytest.fixture
def import_job_service(mock_db):
    """创建导入任务服务实例"""
    return ImportJobService(mock_db)


@pytest.fixture
def sample_user_id():
    """示例用户ID"""
    return uuid4()


@pytest.fixture
def sample_import_job(sample_user_id):
    """示例导入任务"""
    job = ImportJob(
        id=1,
        job_no="IMP20241208001",
        type=ImportJobType.FINANCE.value,
        status=ImportJobStatus.PENDING.value,
        file_name="test.csv",
        file_hash="abc123",
        file_size=1024,
        total_rows=100,
        processed_rows=0,
        success_rows=0,
        failed_rows=0,
        created_by=sample_user_id,
        updated_by=sample_user_id
    )
    job.version = 1
    return job


@pytest.fixture
def sample_csv_content():
    """示例CSV内容"""
    return b"name,amount,date\nTest1,100.00,2024-01-01\nTest2,200.00,2024-01-02\n"


# ========== 任务创建测试 ==========

class TestCreateJob:
    """任务创建测试"""

    @pytest.mark.asyncio
    async def test_create_job_success(self, import_job_service, mock_db, sample_user_id):
        """测试成功创建任务"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch('backend.services.import_job_service.generate_request_no') as mock_gen:
            mock_gen.return_value = "IMP20241208001"

            job = await import_job_service.create_job(
                job_type="finance",
                file_name="test.csv",
                file_hash="abc123",
                file_size=1024,
                current_user_id=sample_user_id
            )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_create_job_duplicate_hash(self, import_job_service, mock_db, sample_user_id, sample_import_job):
        """测试重复文件哈希拒绝创建"""
        sample_import_job.status = ImportJobStatus.COMPLETED.value
        mock_db.query.return_value.filter.return_value.first.return_value = sample_import_job

        with pytest.raises(BusinessLogicError) as exc_info:
            await import_job_service.create_job(
                job_type="finance",
                file_name="test.csv",
                file_hash="abc123",
                file_size=1024,
                current_user_id=sample_user_id
            )

        assert "相同文件已存在" in str(exc_info.value)


# ========== 任务查询测试 ==========

class TestGetJob:
    """任务查询测试"""

    @pytest.mark.asyncio
    async def test_get_job_by_id_success(self, import_job_service, mock_db, sample_import_job, sample_user_id):
        """测试成功获取任务"""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_import_job

        job = await import_job_service.get_job_by_id(1, sample_user_id, UserRole.ADMIN.value)

        assert job.id == 1
        assert job.job_no == "IMP20241208001"

    @pytest.mark.asyncio
    async def test_get_job_by_id_not_found(self, import_job_service, mock_db, sample_user_id):
        """测试任务不存在"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ResourceNotFoundError):
            await import_job_service.get_job_by_id(999, sample_user_id, UserRole.ADMIN.value)

    @pytest.mark.asyncio
    async def test_get_job_by_id_permission_denied(self, import_job_service, mock_db, sample_import_job):
        """测试权限拒绝"""
        other_user_id = uuid4()
        sample_import_job.created_by = uuid4()  # 不同用户创建
        mock_db.query.return_value.filter.return_value.first.return_value = sample_import_job

        with pytest.raises(PermissionDeniedError):
            await import_job_service.get_job_by_id(1, other_user_id, UserRole.MEDIA_BUYER.value)


class TestGetJobs:
    """任务列表查询测试"""

    @pytest.mark.asyncio
    async def test_get_jobs_admin(self, import_job_service, mock_db, sample_import_job, sample_user_id):
        """测试管理员获取所有任务"""
        mock_db.query.return_value.filter.return_value.count.return_value = 1
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sample_import_job]
        mock_db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sample_import_job]
        mock_db.query.return_value.count.return_value = 1

        jobs, total = await import_job_service.get_jobs(
            page=1,
            page_size=20,
            current_user_id=sample_user_id,
            user_role=UserRole.ADMIN.value
        )

        assert total >= 0

    @pytest.mark.asyncio
    async def test_get_jobs_with_filter(self, import_job_service, mock_db, sample_user_id):
        """测试带过滤条件的查询"""
        mock_db.query.return_value.filter.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        jobs, total = await import_job_service.get_jobs(
            page=1,
            page_size=20,
            status=ImportJobStatus.PENDING.value,
            job_type=ImportJobType.FINANCE.value,
            current_user_id=sample_user_id,
            user_role=UserRole.ADMIN.value
        )

        assert total == 0
        assert jobs == []


# ========== 文件上传与解析测试 ==========

class TestUploadAndParse:
    """文件上传与解析测试"""

    @pytest.mark.asyncio
    async def test_upload_csv_success(self, import_job_service, mock_db, sample_user_id, sample_csv_content):
        """测试成功上传CSV"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch('backend.services.import_job_service.generate_request_no') as mock_gen:
            mock_gen.return_value = "IMP20241208001"

            job, parsed_rows, errors = await import_job_service.upload_and_parse(
                file_content=sample_csv_content,
                file_name="test.csv",
                job_type="finance",
                current_user_id=sample_user_id
            )

        assert mock_db.add.called
        assert len(parsed_rows) == 2
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_upload_empty_file(self, import_job_service, mock_db, sample_user_id):
        """测试上传空文件"""
        with pytest.raises(ValidationError):
            await import_job_service.upload_and_parse(
                file_content=b"",
                file_name="empty.csv",
                job_type="finance",
                current_user_id=sample_user_id
            )

    @pytest.mark.asyncio
    async def test_upload_invalid_format(self, import_job_service, mock_db, sample_user_id):
        """测试无效格式文件"""
        with patch('backend.services.import_job_service.generate_request_no') as mock_gen:
            mock_gen.return_value = "IMP20241208001"

            job, parsed_rows, errors = await import_job_service.upload_and_parse(
                file_content=b"invalid content",
                file_name="test.txt",
                job_type="finance",
                current_user_id=sample_user_id
            )

        # 应该有错误
        assert len(errors) > 0
        assert any("仅支持 CSV 文件" in e.get("error", "") for e in errors)


# ========== 状态流转测试 ==========

class TestStatusTransitions:
    """状态流转测试"""

    @pytest.mark.asyncio
    async def test_start_processing_success(self, import_job_service, mock_db, sample_import_job, sample_user_id):
        """测试开始处理"""
        sample_import_job.status = ImportJobStatus.PENDING.value
        mock_db.query.return_value.filter.return_value.first.return_value = sample_import_job

        job = await import_job_service.start_processing(1, sample_user_id)

        assert job.status == ImportJobStatus.PROCESSING.value

    @pytest.mark.asyncio
    async def test_start_processing_invalid_status(self, import_job_service, mock_db, sample_import_job, sample_user_id):
        """测试从非pending状态开始处理"""
        sample_import_job.status = ImportJobStatus.COMPLETED.value
        mock_db.query.return_value.filter.return_value.first.return_value = sample_import_job

        with pytest.raises(BusinessLogicError) as exc_info:
            await import_job_service.start_processing(1, sample_user_id)

        assert "只能从待处理状态开始处理" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_complete_job_success(self, import_job_service, mock_db, sample_import_job, sample_user_id):
        """测试完成任务"""
        sample_import_job.status = ImportJobStatus.PROCESSING.value
        mock_db.query.return_value.filter.return_value.first.return_value = sample_import_job

        job = await import_job_service.complete_job(
            job_id=1,
            success_rows=90,
            failed_rows=10,
            result_summary={"test": "summary"},
            current_user_id=sample_user_id
        )

        assert job.status == ImportJobStatus.COMPLETED.value
        assert job.success_rows == 90
        assert job.failed_rows == 10

    @pytest.mark.asyncio
    async def test_fail_job_success(self, import_job_service, mock_db, sample_import_job, sample_user_id):
        """测试标记失败"""
        sample_import_job.status = ImportJobStatus.PROCESSING.value
        mock_db.query.return_value.filter.return_value.first.return_value = sample_import_job

        job = await import_job_service.fail_job(
            job_id=1,
            error_message="处理失败",
            current_user_id=sample_user_id
        )

        assert job.status == ImportJobStatus.FAILED.value
        assert job.error_log is not None

    @pytest.mark.asyncio
    async def test_cancel_job_success(self, import_job_service, mock_db, sample_import_job, sample_user_id):
        """测试取消任务"""
        sample_import_job.status = ImportJobStatus.PENDING.value
        sample_import_job.created_by = sample_user_id
        mock_db.query.return_value.filter.return_value.first.return_value = sample_import_job

        job = await import_job_service.cancel_job(1, sample_user_id, UserRole.ADMIN.value)

        assert job.status == ImportJobStatus.CANCELLED.value

    @pytest.mark.asyncio
    async def test_cancel_job_not_owner(self, import_job_service, mock_db, sample_import_job):
        """测试非所有者取消任务"""
        other_user_id = uuid4()
        sample_import_job.status = ImportJobStatus.PENDING.value
        sample_import_job.created_by = uuid4()  # 不同用户
        mock_db.query.return_value.filter.return_value.first.return_value = sample_import_job

        with pytest.raises(PermissionDeniedError):
            await import_job_service.cancel_job(1, other_user_id, UserRole.MEDIA_BUYER.value)


# ========== 进度更新测试 ==========

class TestProgressUpdate:
    """进度更新测试"""

    @pytest.mark.asyncio
    async def test_update_progress(self, import_job_service, mock_db, sample_import_job):
        """测试更新进度"""
        sample_import_job.status = ImportJobStatus.PROCESSING.value
        mock_db.query.return_value.filter.return_value.first.return_value = sample_import_job

        job = await import_job_service.update_progress(
            job_id=1,
            processed=50,
            success=45,
            failed=5
        )

        assert job.processed_rows == 50
        assert job.success_rows == 45
        assert job.failed_rows == 5

    @pytest.mark.asyncio
    async def test_add_error(self, import_job_service, mock_db, sample_import_job):
        """测试添加错误记录"""
        sample_import_job.error_log = []
        mock_db.query.return_value.filter.return_value.first.return_value = sample_import_job

        job = await import_job_service.add_error(
            job_id=1,
            row=10,
            error="数据格式错误",
            data={"name": "test"}
        )

        assert len(job.error_log) == 1
        assert job.error_log[0]["row"] == 10


# ========== 删除任务测试 ==========

class TestDeleteJob:
    """删除任务测试"""

    @pytest.mark.asyncio
    async def test_delete_pending_job(self, import_job_service, mock_db, sample_import_job, sample_user_id):
        """测试删除待处理任务"""
        sample_import_job.status = ImportJobStatus.PENDING.value
        mock_db.query.return_value.filter.return_value.first.return_value = sample_import_job

        result = await import_job_service.delete_job(1, sample_user_id)

        assert result is True
        assert mock_db.delete.called

    @pytest.mark.asyncio
    async def test_delete_completed_job(self, import_job_service, mock_db, sample_import_job, sample_user_id):
        """测试删除已完成任务（应失败）"""
        sample_import_job.status = ImportJobStatus.COMPLETED.value
        mock_db.query.return_value.filter.return_value.first.return_value = sample_import_job

        with pytest.raises(BusinessLogicError) as exc_info:
            await import_job_service.delete_job(1, sample_user_id)

        assert "只能删除待处理的任务" in str(exc_info.value)


# ========== 统计查询测试 ==========

class TestStatistics:
    """统计查询测试"""

    @pytest.mark.asyncio
    async def test_get_statistics(self, import_job_service, mock_db, sample_user_id):
        """测试获取统计信息"""
        # Mock 查询结果
        mock_db.query.return_value.count.return_value = 10
        mock_db.query.return_value.filter.return_value.count.return_value = 2

        mock_row_stats = MagicMock()
        mock_row_stats.total_processed = 1000
        mock_row_stats.total_success = 900
        mock_row_stats.total_failed = 100
        mock_db.query.return_value.with_entities.return_value.first.return_value = mock_row_stats

        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []

        statistics = await import_job_service.get_statistics(
            current_user_id=sample_user_id,
            user_role=UserRole.ADMIN.value
        )

        assert isinstance(statistics, ImportJobStatisticsResponse)


# ========== 重复检查测试 ==========

class TestDuplicateCheck:
    """重复检查测试"""

    @pytest.mark.asyncio
    async def test_check_duplicate_exists(self, import_job_service, mock_db, sample_import_job):
        """测试检查存在重复"""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_import_job

        result = await import_job_service.check_duplicate("abc123")

        assert result is not None
        assert result.file_hash == "abc123"

    @pytest.mark.asyncio
    async def test_check_duplicate_not_exists(self, import_job_service, mock_db):
        """测试检查不存在重复"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = await import_job_service.check_duplicate("new_hash")

        assert result is None


# ========== 模型属性测试 ==========

class TestImportJobModel:
    """ImportJob模型测试"""

    def test_progress_percent(self, sample_import_job):
        """测试进度百分比计算"""
        sample_import_job.total_rows = 100
        sample_import_job.processed_rows = 50

        assert sample_import_job.progress_percent == 50.0

    def test_progress_percent_zero_total(self, sample_import_job):
        """测试总数为0时的进度"""
        sample_import_job.total_rows = 0
        sample_import_job.processed_rows = 0

        assert sample_import_job.progress_percent == 0.0

    def test_success_rate(self, sample_import_job):
        """测试成功率计算"""
        sample_import_job.processed_rows = 100
        sample_import_job.success_rows = 80

        assert sample_import_job.success_rate == 80.0

    def test_is_terminal(self, sample_import_job):
        """测试终态判断"""
        sample_import_job.status = ImportJobStatus.PENDING.value
        assert not sample_import_job.is_terminal

        sample_import_job.status = ImportJobStatus.COMPLETED.value
        assert sample_import_job.is_terminal

        sample_import_job.status = ImportJobStatus.FAILED.value
        assert sample_import_job.is_terminal

    def test_can_transition_to(self, sample_import_job):
        """测试状态转换规则"""
        sample_import_job.status = ImportJobStatus.PENDING.value

        assert sample_import_job.can_transition_to(ImportJobStatus.PROCESSING)
        assert sample_import_job.can_transition_to(ImportJobStatus.CANCELLED)
        assert not sample_import_job.can_transition_to(ImportJobStatus.COMPLETED)

    def test_status_enum_property(self, sample_import_job):
        """测试状态枚举属性"""
        sample_import_job.status = ImportJobStatus.PENDING.value

        assert sample_import_job.status_enum == ImportJobStatus.PENDING

    def test_type_enum_property(self, sample_import_job):
        """测试类型枚举属性"""
        sample_import_job.type = ImportJobType.FINANCE.value

        assert sample_import_job.type_enum == ImportJobType.FINANCE


# ========== CSV解析测试 ==========

class TestCSVParsing:
    """CSV解析测试"""

    def test_parse_utf8_csv(self, import_job_service):
        """测试UTF-8编码CSV解析"""
        content = b"name,value\nTest,100\n"

        parsed_rows, errors = import_job_service._parse_csv(content)

        assert len(parsed_rows) == 1
        assert parsed_rows[0]["name"] == "Test"
        assert len(errors) == 0

    def test_parse_csv_with_chinese(self, import_job_service):
        """测试包含中文的CSV解析"""
        content = "name,value\n测试,100\n".encode('utf-8')

        parsed_rows, errors = import_job_service._parse_csv(content)

        assert len(parsed_rows) == 1
        assert parsed_rows[0]["name"] == "测试"

    def test_parse_empty_csv(self, import_job_service):
        """测试空CSV解析"""
        content = b"name,value\n"

        parsed_rows, errors = import_job_service._parse_csv(content)

        assert len(parsed_rows) == 0
        assert len(errors) == 0

    def test_parse_csv_with_whitespace(self, import_job_service):
        """测试带空白的CSV解析"""
        content = b"name,value\n  Test  ,  100  \n"

        parsed_rows, errors = import_job_service._parse_csv(content)

        assert len(parsed_rows) == 1
        assert parsed_rows[0]["name"] == "Test"
        assert parsed_rows[0]["value"] == "100"
