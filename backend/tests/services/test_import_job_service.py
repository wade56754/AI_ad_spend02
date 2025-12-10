"""
测试用例: backend/services/import_job_service.py

覆盖范围:
- 导入任务创建 (create_job) - 带文件哈希去重
- 导入任务查询 (get_job_by_id, get_jobs) - 带权限检查
- 导入任务更新 (update_job) - 终态不可修改
- 导入任务删除 (delete_job) - 仅pending状态
- 文件上传和解析 (upload_and_parse, _parse_csv)
- 状态转换 (start_processing, complete_job, fail_job, cancel_job)
- 进度更新 (update_progress, add_error)
- 统计查询 (get_statistics)
- 重复检查 (check_duplicate)
- 异常处理和边界情况

目标覆盖率: 16.58% → ≥65%
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime
from uuid import UUID, uuid4

from backend.services.import_job_service import ImportJobService
from backend.models import ImportJob, User
from backend.models.enums import ImportJobStatus, ImportJobType, UserRole
from backend.exceptions.custom_exceptions import (
    ValidationError,
    ResourceNotFoundError,
    PermissionDeniedError,
    BusinessLogicError
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock数据库会话"""
    return Mock()


@pytest.fixture
def import_job_service(mock_db):
    """导入任务服务实例"""
    return ImportJobService(mock_db)


@pytest.fixture
def sample_job():
    """示例导入任务"""
    job = Mock(spec=ImportJob)
    job.id = 1
    job.job_no = "IMP202512100001"
    job.type = "finance"
    job.status = "pending"
    job.file_name = "test.csv"
    job.file_hash = "abc123"
    job.file_size = 1024
    job.total_rows = 100
    job.processed_rows = 0
    job.success_rows = 0
    job.failed_rows = 0
    job.error_log = None
    job.created_by = uuid4()
    job.updated_by = uuid4()
    job.version = 1
    job.is_terminal = False
    job.created_at = datetime.utcnow()
    return job


@pytest.fixture
def sample_user_id():
    """示例用户ID"""
    return uuid4()


# ============================================================================
# 1. 导入任务创建测试
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.import_job
class TestCreateJob:
    """测试导入任务创建"""

    async def test_create_job_success(self, import_job_service, mock_db, sample_user_id):
        """测试成功创建导入任务"""
        with patch.object(ImportJob, 'get_by_hash', return_value=None):
            with patch('backend.services.import_job_service.generate_request_no', return_value="IMP202512100001"):
                job = await import_job_service.create_job(
                    job_type="finance",
                    file_name="test.csv",
                    file_hash="abc123",
                    file_size=1024,
                    current_user_id=sample_user_id
                )

                mock_db.add.assert_called_once()
                mock_db.commit.assert_called_once()
                mock_db.refresh.assert_called_once()

    async def test_create_job_duplicate_hash_completed(self, import_job_service, mock_db, sample_job, sample_user_id):
        """测试文件哈希重复且任务已完成时抛出异常"""
        sample_job.status = ImportJobStatus.COMPLETED.value

        with patch.object(ImportJob, 'get_by_hash', return_value=sample_job):
            with pytest.raises(BusinessLogicError) as exc:
                await import_job_service.create_job(
                    job_type="finance",
                    file_name="test.csv",
                    file_hash="abc123",
                    file_size=1024,
                    current_user_id=sample_user_id
                )

            assert "相同文件已存在或正在处理中" in str(exc.value)

    async def test_create_job_duplicate_hash_processing(self, import_job_service, mock_db, sample_job, sample_user_id):
        """测试文件哈希重复且任务正在处理时抛出异常"""
        sample_job.status = ImportJobStatus.PROCESSING.value

        with patch.object(ImportJob, 'get_by_hash', return_value=sample_job):
            with pytest.raises(BusinessLogicError) as exc:
                await import_job_service.create_job(
                    job_type="finance",
                    file_name="test.csv",
                    file_hash="abc123",
                    file_size=1024,
                    current_user_id=sample_user_id
                )

            assert "相同文件已存在或正在处理中" in str(exc.value)


# ============================================================================
# 2. 导入任务查询测试
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.import_job
class TestGetJobById:
    """测试导入任务详情查询"""

    async def test_get_job_by_id_success(self, import_job_service, mock_db, sample_job):
        """测试成功获取任务详情"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_job
        mock_db.query.return_value = mock_query

        job = await import_job_service.get_job_by_id(1)

        assert job.id == 1
        assert job.job_no == "IMP202512100001"

    async def test_get_job_by_id_not_found(self, import_job_service, mock_db):
        """测试任务不存在时抛出异常"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        with pytest.raises(ResourceNotFoundError) as exc:
            await import_job_service.get_job_by_id(999)

        assert "导入任务不存在" in str(exc.value)

    async def test_get_job_by_id_permission_denied(self, import_job_service, mock_db, sample_job, sample_user_id):
        """测试无权限访问其他人的任务"""
        sample_job.created_by = uuid4()  # 不同的用户
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_job
        mock_db.query.return_value = mock_query

        with pytest.raises(PermissionDeniedError) as exc:
            await import_job_service.get_job_by_id(
                1,
                current_user_id=sample_user_id,
                user_role=UserRole.ANALYST.value
            )

        assert "无权限访问此导入任务" in str(exc.value)

    async def test_get_job_by_id_admin_access(self, import_job_service, mock_db, sample_job, sample_user_id):
        """测试管理员可访问所有任务"""
        sample_job.created_by = uuid4()  # 不同的用户
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_job
        mock_db.query.return_value = mock_query

        job = await import_job_service.get_job_by_id(
            1,
            current_user_id=sample_user_id,
            user_role=UserRole.ADMIN.value
        )

        assert job.id == 1


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.import_job
class TestGetJobs:
    """测试导入任务列表查询"""

    async def test_get_jobs_admin_role(self, import_job_service, mock_db, sample_job, sample_user_id):
        """测试管理员可查看所有任务"""
        mock_query = Mock()
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sample_job]
        mock_db.query.return_value = mock_query

        jobs, total = await import_job_service.get_jobs(
            current_user_id=sample_user_id,
            user_role=UserRole.ADMIN.value
        )

        assert total == 1
        assert len(jobs) == 1

    async def test_get_jobs_regular_user(self, import_job_service, mock_db, sample_job, sample_user_id):
        """测试普通用户只能看到自己的任务"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sample_job]
        mock_db.query.return_value = mock_query

        jobs, total = await import_job_service.get_jobs(
            current_user_id=sample_user_id,
            user_role=UserRole.ANALYST.value
        )

        assert total == 1
        # 验证过滤了created_by
        mock_query.filter.assert_called()

    async def test_get_jobs_with_filters(self, import_job_service, mock_db, sample_job, sample_user_id):
        """测试带过滤条件查询"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sample_job]
        mock_db.query.return_value = mock_query

        jobs, total = await import_job_service.get_jobs(
            status="pending",
            job_type="finance",
            current_user_id=sample_user_id,
            user_role=UserRole.ADMIN.value
        )

        assert total == 1
        # 验证filter被调用了多次
        assert mock_query.filter.call_count >= 2


# ============================================================================
# 3. 导入任务更新测试
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.import_job
class TestUpdateJob:
    """测试导入任务更新"""

    async def test_update_job_success(self, import_job_service, mock_db, sample_job, sample_user_id):
        """测试成功更新任务"""
        with patch.object(import_job_service, 'get_job_by_id', new=AsyncMock(return_value=sample_job)):
            updates = {"status": "processing"}
            job = await import_job_service.update_job(1, updates, sample_user_id)

            assert job.version == 2
            mock_db.commit.assert_called_once()

    async def test_update_job_terminal_state(self, import_job_service, mock_db, sample_job, sample_user_id):
        """测试终态任务不可修改"""
        sample_job.is_terminal = True

        with patch.object(import_job_service, 'get_job_by_id', new=AsyncMock(return_value=sample_job)):
            with pytest.raises(BusinessLogicError) as exc:
                await import_job_service.update_job(1, {"status": "cancelled"}, sample_user_id)

            assert "任务已完成，无法修改" in str(exc.value)


# ============================================================================
# 4. 导入任务删除测试
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.import_job
class TestDeleteJob:
    """测试导入任务删除"""

    async def test_delete_job_pending_status(self, import_job_service, mock_db, sample_job, sample_user_id):
        """测试删除pending状态的任务"""
        sample_job.status = ImportJobStatus.PENDING.value

        with patch.object(import_job_service, 'get_job_by_id', new=AsyncMock(return_value=sample_job)):
            result = await import_job_service.delete_job(1, sample_user_id)

            assert result is True
            mock_db.delete.assert_called_once_with(sample_job)
            mock_db.commit.assert_called_once()

    async def test_delete_job_non_pending_status(self, import_job_service, mock_db, sample_job, sample_user_id):
        """测试删除非pending状态的任务抛出异常"""
        sample_job.status = ImportJobStatus.PROCESSING.value

        with patch.object(import_job_service, 'get_job_by_id', new=AsyncMock(return_value=sample_job)):
            with pytest.raises(BusinessLogicError) as exc:
                await import_job_service.delete_job(1, sample_user_id)

            assert "只能删除待处理的任务" in str(exc.value)


# ============================================================================
# 5. 文件上传和解析测试
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.import_job
class TestUploadAndParse:
    """测试文件上传和解析"""

    async def test_upload_and_parse_empty_file(self, import_job_service, sample_user_id):
        """测试上传空文件抛出异常"""
        with pytest.raises(ValidationError) as exc:
            await import_job_service.upload_and_parse(
                file_content=b"",
                file_name="test.csv",
                job_type="finance",
                current_user_id=sample_user_id
            )

        assert "文件内容为空" in str(exc.value)

    async def test_upload_and_parse_invalid_format(self, import_job_service, mock_db, sample_user_id):
        """测试上传非CSV文件"""
        with patch('backend.services.import_job_service.generate_request_no', return_value="IMP202512100001"):
            job, rows, errors = await import_job_service.upload_and_parse(
                file_content=b"test content",
                file_name="test.xlsx",
                job_type="finance",
                current_user_id=sample_user_id
            )

            assert len(errors) == 1
            assert "仅支持 CSV 文件" in errors[0]["error"]

    async def test_upload_and_parse_csv_success(self, import_job_service, mock_db, sample_user_id):
        """测试成功解析CSV文件"""
        csv_content = b"name,amount\ntest1,100\ntest2,200"

        with patch('backend.services.import_job_service.generate_request_no', return_value="IMP202512100001"):
            job, rows, errors = await import_job_service.upload_and_parse(
                file_content=csv_content,
                file_name="test.csv",
                job_type="finance",
                current_user_id=sample_user_id
            )

            assert len(rows) == 2
            assert len(errors) == 0
            mock_db.add.assert_called_once()


@pytest.mark.unit
@pytest.mark.import_job
class TestParseCSV:
    """测试CSV解析"""

    def test_parse_csv_utf8(self, import_job_service):
        """测试解析UTF-8编码的CSV"""
        csv_content = b"name,amount\ntest1,100\ntest2,200"
        rows, errors = import_job_service._parse_csv(csv_content)

        assert len(rows) == 2
        assert len(errors) == 0
        assert rows[0]["name"] == "test1"
        assert rows[0]["amount"] == "100"

    def test_parse_csv_gbk(self, import_job_service):
        """测试解析GBK编码的CSV"""
        csv_content = "姓名,金额\n测试1,100".encode('gbk')
        rows, errors = import_job_service._parse_csv(csv_content)

        assert len(rows) == 1
        assert len(errors) == 0

    def test_parse_csv_with_empty_values(self, import_job_service):
        """测试解析包含空值的CSV"""
        csv_content = b"name,amount\ntest1,\n,200"
        rows, errors = import_job_service._parse_csv(csv_content)

        assert len(rows) == 2
        assert rows[0]["amount"] is None
        assert rows[1]["name"] is None


# ============================================================================
# 6. 状态转换测试
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.import_job
class TestStartProcessing:
    """测试开始处理"""

    async def test_start_processing_success(self, import_job_service, sample_job, sample_user_id):
        """测试成功开始处理"""
        sample_job.status = ImportJobStatus.PENDING.value
        sample_job.start_processing = Mock()

        with patch.object(import_job_service, 'get_job_by_id', new=AsyncMock(return_value=sample_job)):
            job = await import_job_service.start_processing(1, sample_user_id)

            sample_job.start_processing.assert_called_once()

    async def test_start_processing_invalid_status(self, import_job_service, sample_job, sample_user_id):
        """测试非pending状态不能开始处理"""
        sample_job.status = ImportJobStatus.PROCESSING.value

        with patch.object(import_job_service, 'get_job_by_id', new=AsyncMock(return_value=sample_job)):
            with pytest.raises(BusinessLogicError) as exc:
                await import_job_service.start_processing(1, sample_user_id)

            assert "只能从待处理状态开始处理" in str(exc.value)


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.import_job
class TestCompleteJob:
    """测试完成任务"""

    async def test_complete_job_success(self, import_job_service, sample_job, sample_user_id):
        """测试成功完成任务"""
        sample_job.status = ImportJobStatus.PROCESSING.value
        sample_job.complete = Mock()

        with patch.object(import_job_service, 'get_job_by_id', new=AsyncMock(return_value=sample_job)):
            job = await import_job_service.complete_job(
                1,
                success_rows=90,
                failed_rows=10,
                result_summary={"total": 100},
                current_user_id=sample_user_id
            )

            sample_job.complete.assert_called_once_with(90, 10, {"total": 100})

    async def test_complete_job_invalid_status(self, import_job_service, sample_job, sample_user_id):
        """测试非processing状态不能完成"""
        sample_job.status = ImportJobStatus.PENDING.value

        with patch.object(import_job_service, 'get_job_by_id', new=AsyncMock(return_value=sample_job)):
            with pytest.raises(BusinessLogicError) as exc:
                await import_job_service.complete_job(1, 90, 10, None, sample_user_id)

            assert "只能从处理中状态完成" in str(exc.value)


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.import_job
class TestFailJob:
    """测试标记任务失败"""

    async def test_fail_job_success(self, import_job_service, sample_job, sample_user_id):
        """测试成功标记任务失败"""
        sample_job.status = ImportJobStatus.PROCESSING.value
        sample_job.fail = Mock()

        with patch.object(import_job_service, 'get_job_by_id', new=AsyncMock(return_value=sample_job)):
            job = await import_job_service.fail_job(
                1,
                error_message="处理失败",
                error_log=[{"row": 1, "error": "格式错误"}],
                current_user_id=sample_user_id
            )

            sample_job.fail.assert_called_once()

    async def test_fail_job_invalid_status(self, import_job_service, sample_job, sample_user_id):
        """测试非processing状态不能标记失败"""
        sample_job.status = ImportJobStatus.PENDING.value

        with patch.object(import_job_service, 'get_job_by_id', new=AsyncMock(return_value=sample_job)):
            with pytest.raises(BusinessLogicError) as exc:
                await import_job_service.fail_job(1, "处理失败", None, sample_user_id)

            assert "只能从处理中状态标记失败" in str(exc.value)


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.import_job
class TestCancelJob:
    """测试取消任务"""

    async def test_cancel_job_success(self, import_job_service, sample_job, sample_user_id):
        """测试成功取消任务"""
        sample_job.status = ImportJobStatus.PENDING.value
        sample_job.can_be_cancelled_by = Mock(return_value=True)
        sample_job.cancel = Mock()

        with patch.object(import_job_service, 'get_job_by_id', new=AsyncMock(return_value=sample_job)):
            job = await import_job_service.cancel_job(
                1,
                sample_user_id,
                UserRole.ADMIN.value
            )

            sample_job.cancel.assert_called_once_with(sample_user_id)

    async def test_cancel_job_invalid_status(self, import_job_service, sample_job, sample_user_id):
        """测试非pending状态不能取消"""
        sample_job.status = ImportJobStatus.PROCESSING.value

        with patch.object(import_job_service, 'get_job_by_id', new=AsyncMock(return_value=sample_job)):
            with pytest.raises(BusinessLogicError) as exc:
                await import_job_service.cancel_job(1, sample_user_id, UserRole.ADMIN.value)

            assert "只能取消待处理状态的任务" in str(exc.value)

    async def test_cancel_job_permission_denied(self, import_job_service, sample_job, sample_user_id):
        """测试无权限取消任务"""
        sample_job.status = ImportJobStatus.PENDING.value
        sample_job.can_be_cancelled_by = Mock(return_value=False)

        with patch.object(import_job_service, 'get_job_by_id', new=AsyncMock(return_value=sample_job)):
            with pytest.raises(PermissionDeniedError) as exc:
                await import_job_service.cancel_job(1, sample_user_id, UserRole.ANALYST.value)

            assert "无权限取消此任务" in str(exc.value)


# ============================================================================
# 7. 进度更新测试
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.import_job
class TestUpdateProgress:
    """测试进度更新"""

    async def test_update_progress_success(self, import_job_service, sample_job):
        """测试成功更新进度"""
        sample_job.status = ImportJobStatus.PROCESSING.value
        sample_job.update_progress = Mock()

        with patch.object(import_job_service, 'get_job_by_id', new=AsyncMock(return_value=sample_job)):
            job = await import_job_service.update_progress(1, processed=50, success=45, failed=5)

            sample_job.update_progress.assert_called_once_with(50, 45, 5)

    async def test_update_progress_invalid_status(self, import_job_service, sample_job):
        """测试非processing状态不能更新进度"""
        sample_job.status = ImportJobStatus.PENDING.value

        with patch.object(import_job_service, 'get_job_by_id', new=AsyncMock(return_value=sample_job)):
            with pytest.raises(BusinessLogicError) as exc:
                await import_job_service.update_progress(1, processed=50)

            assert "只能更新处理中任务的进度" in str(exc.value)


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.import_job
class TestAddError:
    """测试添加错误记录"""

    async def test_add_error_success(self, import_job_service, sample_job):
        """测试成功添加错误记录"""
        sample_job.add_error = Mock()

        with patch.object(import_job_service, 'get_job_by_id', new=AsyncMock(return_value=sample_job)):
            job = await import_job_service.add_error(
                1,
                row=10,
                error="格式错误",
                data={"name": "test"}
            )

            sample_job.add_error.assert_called_once_with(10, "格式错误", {"name": "test"})


# ============================================================================
# 8. 统计查询测试
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.import_job
class TestGetStatistics:
    """测试统计查询"""

    async def test_get_statistics_admin_role(self, import_job_service, mock_db, sample_user_id):
        """测试管理员统计"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.side_effect = [100, 20, 10, 60, 5, 5]  # total, pending, processing, completed, failed, cancelled

        mock_row_stats = Mock()
        mock_row_stats.total_processed = 10000
        mock_row_stats.total_success = 9500
        mock_row_stats.total_failed = 500
        mock_query.with_entities.return_value.first.return_value = mock_row_stats

        mock_query.order_by.return_value.limit.return_value.all.return_value = []

        mock_db.query.return_value = mock_query

        stats = await import_job_service.get_statistics(
            current_user_id=sample_user_id,
            user_role=UserRole.ADMIN.value
        )

        assert stats.total_jobs == 100
        assert stats.completed_jobs == 60
        assert stats.total_rows_processed == 10000
        assert stats.overall_success_rate == 95.0

    async def test_get_statistics_regular_user(self, import_job_service, mock_db, sample_user_id):
        """测试普通用户统计（只看自己的）"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.side_effect = [10, 2, 1, 6, 1, 0]

        mock_row_stats = Mock()
        mock_row_stats.total_processed = 1000
        mock_row_stats.total_success = 950
        mock_row_stats.total_failed = 50
        mock_query.with_entities.return_value.first.return_value = mock_row_stats

        mock_query.order_by.return_value.limit.return_value.all.return_value = []

        mock_db.query.return_value = mock_query

        stats = await import_job_service.get_statistics(
            current_user_id=sample_user_id,
            user_role=UserRole.ANALYST.value
        )

        assert stats.total_jobs == 10
        # 验证过滤了created_by
        mock_query.filter.assert_called()


# ============================================================================
# 9. 重复检查测试
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.import_job
class TestCheckDuplicate:
    """测试重复检查"""

    async def test_check_duplicate_exists(self, import_job_service, sample_job):
        """测试检查到重复文件"""
        with patch.object(ImportJob, 'get_by_hash', return_value=sample_job):
            result = await import_job_service.check_duplicate("abc123")

            assert result == sample_job

    async def test_check_duplicate_not_exists(self, import_job_service):
        """测试没有重复文件"""
        with patch.object(ImportJob, 'get_by_hash', return_value=None):
            result = await import_job_service.check_duplicate("abc123")

            assert result is None


# ============================================================================
# 10. 集成测试
# ============================================================================

@pytest.mark.integration
@pytest.mark.import_job
class TestImportJobServiceIntegration:
    """测试导入任务服务集成场景"""

    @pytest.mark.asyncio
    async def test_full_import_workflow(self, import_job_service, mock_db, sample_job, sample_user_id):
        """测试完整导入流程"""
        # pending → processing → completed
        sample_job.status = ImportJobStatus.PENDING.value
        sample_job.start_processing = Mock()
        sample_job.update_progress = Mock()
        sample_job.complete = Mock()

        with patch.object(import_job_service, 'get_job_by_id', new=AsyncMock(return_value=sample_job)):
            # 1. 开始处理
            await import_job_service.start_processing(1, sample_user_id)
            sample_job.status = ImportJobStatus.PROCESSING.value

            # 2. 更新进度
            await import_job_service.update_progress(1, 50, 45, 5)

            # 3. 完成任务
            await import_job_service.complete_job(1, 90, 10, None, sample_user_id)

            sample_job.start_processing.assert_called_once()
            sample_job.update_progress.assert_called_once()
            sample_job.complete.assert_called_once()
