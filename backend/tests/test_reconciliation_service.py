"""
对账管理服务测试
Version: 2.0 (Test Fixture & Architecture Repair Flow)
Author: Claude协作开发

修复内容:
- P0-RS-001: 修复异常导入 (ValidationError/NotFoundError/PermissionError → custom_exceptions)
- P0-RS-002: 修复 User 模型字段 (id int → UUID, name → username)
- P1-RS-001: 修复状态值 (pending → draft for ReconciliationBatch)
- P1-RS-002: 修复 mock 路径 (services → backend.services)
"""

import pytest
import uuid
from decimal import Decimal
from datetime import date, datetime
from unittest.mock import Mock, patch, AsyncMock

from backend.models.reconciliation import (
    ReconciliationBatch, ReconciliationDetail,
    ReconciliationAdjustment, ReconciliationReport
)
from backend.models import User
from backend.models import AdAccount
from backend.models import Project
from backend.models import Channel
from backend.models.enums import UserRole
from backend.schemas.reconciliation import (
    ReconciliationBatchCreateRequest,
    ReconciliationDetailReviewRequest,
    ReconciliationAdjustmentCreateRequest,
    ReconciliationReportGenerateRequest
)
from backend.services.reconciliation_service import ReconciliationService
# P0-RS-001: 使用正确的异常类
from backend.exceptions.custom_exceptions import (
    ValidationError,
    ResourceNotFoundError,
    PermissionDeniedError,
    BusinessLogicError
)


class TestReconciliationService:
    """对账管理服务测试类"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = Mock()
        db.query = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        db.rollback = Mock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """获取服务实例"""
        return ReconciliationService(mock_db)

    @pytest.fixture
    def sample_user(self):
        """示例用户"""
        # P0-RS-002: 修复 User 模型字段
        return User(
            id=uuid.uuid4(),
            username="test_reconciliation_user",
            email="test_recon@example.com",
            hashed_password="hashed_test_password",
            role=UserRole.ADMIN.value,
            is_active=True
        )

    @pytest.fixture
    def sample_batch(self):
        """示例对账批次"""
        # P1-RS-001: status pending → draft (STATE_MACHINE.md v2.6)
        return ReconciliationBatch(
            id=1,
            batch_no="REC20251112143000123",
            reconciliation_date=date.today(),
            status="draft",  # P1-RS-001: pending → draft
            total_accounts=0,
            matched_accounts=0,
            mismatched_accounts=0,
            total_platform_spend=Decimal('0.00'),
            total_internal_spend=Decimal('0.00'),
            total_difference=Decimal('0.00'),
            created_by=1
        )

    @pytest.fixture
    def sample_detail(self):
        """示例对账详情"""
        return ReconciliationDetail(
            id=1,
            batch_id=1,
            ad_account_id=1,
            project_id=1,
            channel_id=1,
            platform_spend=Decimal('1000.00'),
            platform_currency="USD",
            internal_spend=Decimal('950.00'),
            internal_currency="USD",
            spend_difference=Decimal('50.00'),
            is_matched=False,
            match_status="pending",
            auto_confidence=Decimal('0.00')
        )

    @pytest.mark.asyncio
    async def test_create_batch_success(self, service, mock_db, sample_user):
        """测试成功创建对账批次"""
        # 准备数据
        request = ReconciliationBatchCreateRequest(
            reconciliation_date=date.today(),
            channel_ids=[1, 2],
            auto_match=True,
            threshold=Decimal('100.00'),
            notes="测试批次"
        )

        # 模拟没有已存在的批次
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # P1-RS-002: 修复 mock 路径
        with patch('backend.services.reconciliation_service.generate_request_no') as mock_gen:
            mock_gen.return_value = "REC20251112143000123"

            batch = ReconciliationBatch(
                batch_no="REC20251112143000123",
                reconciliation_date=request.reconciliation_date,
                status="draft",  # P1-RS-001: pending → draft
                created_by=sample_user.id,
                notes=request.notes
            )
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None

            # 执行
            result = await service.create_batch(request, sample_user.id)

            # 验证
            assert result.batch_no == "REC20251112143000123"
            assert result.reconciliation_date == request.reconciliation_date
            # P1-RS-001: pending → draft (STATE_MACHINE.md v2.6)
            assert result.status == "draft"
            assert result.created_by == sample_user.id
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_batch_duplicate_date(self, service, mock_db, sample_batch):
        """测试创建重复日期的对账批次"""
        # 准备数据
        request = ReconciliationBatchCreateRequest(
            reconciliation_date=date.today(),
            auto_match=True
        )

        # 模拟已存在相同日期的批次
        mock_db.query.return_value.filter.return_value.first.return_value = sample_batch

        # P0-RS-001: ValidationError → BusinessLogicError
        with pytest.raises(BusinessLogicError) as exc_info:
            await service.create_batch(request, 1)

        # P0 修复：BIZ_302 不存在于 ERROR_CODES_SOT.md v2.1
        # 资源已存在应使用 BIZ_003（资源已存在, 409）
        assert "BIZ_003" in str(exc_info.value) or exc_info.value.code == "BIZ_003"
        assert "已存在对账批次" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_batches_with_filters(self, service, mock_db, sample_batch):
        """测试带过滤条件获取对账批次列表"""
        # 准备模拟数据
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = [sample_batch]

        # P1-RS-001: pending → draft
        batches, total = await service.get_batches(
            page=1,
            page_size=20,
            status="draft",  # P1-RS-001: pending → draft
            date_from=date(2025, 11, 1),
            date_to=date(2025, 11, 30)
        )

        # 验证
        assert len(batches) == 1
        assert total == 1
        assert batches[0].status == "draft"  # P1-RS-001: pending → draft

    @pytest.mark.asyncio
    async def test_get_batch_by_id_not_found(self, service, mock_db):
        """测试获取不存在的对账批次"""
        # 模拟批次不存在
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # P0-RS-001: NotFoundError → ResourceNotFoundError
        with pytest.raises(ResourceNotFoundError) as exc_info:
            await service.get_batch_by_id(999)

        # P1 修复：SYS_004 是"请求过于频繁"(429)，不是"资源不存在"
        # 资源不存在应使用 BIZ_002（资源不存在, 404）- ERROR_CODES_SOT.md v2.1
        assert "BIZ_002" in str(exc_info.value) or exc_info.value.code == "BIZ_002"
        assert "对账批次不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_run_reconciliation_success(
        self, service, mock_db, sample_batch, sample_detail
    ):
        """测试成功执行对账"""
        # 准备模拟数据
        mock_db.query.return_value.filter.return_value.first.return_value = sample_batch

        # 模拟广告账户
        mock_accounts = [
            Mock(id=1, project_id=1, channel_id=1, status="active"),
            Mock(id=2, project_id=1, channel_id=1, status="active")
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_accounts

        # 执行
        result = await service.run_reconciliation(1, 1)

        # 验证
        assert result.status == "completed"
        assert result.total_accounts == 2
        assert result.started_at is not None
        assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_run_reconciliation_invalid_status(
        self, service, mock_db, sample_batch
    ):
        """测试执行非pending状态的对账批次"""
        # 设置批次为已完成状态
        sample_batch.status = "completed"
        mock_db.query.return_value.filter.return_value.first.return_value = sample_batch

        # P0-RS-001: ValidationError → BusinessLogicError
        with pytest.raises(BusinessLogicError) as exc_info:
            await service.run_reconciliation(1, 1)

        # P1 修复：BIZ_306 不存在于 ERROR_CODES_SOT.md v2.1
        # 状态转换不允许应使用 BIZ_301（状态转换不允许, 400）或 STATE_400（非法状态流转, 400）
        assert "BIZ_301" in str(exc_info.value) or "STATE_400" in str(exc_info.value) or \
               exc_info.value.code in ["BIZ_301", "STATE_400"]
        assert "只能对待处理的批次执行对账" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_review_detail_success(self, service, mock_db, sample_detail):
        """测试成功审核对账差异"""
        # 准备数据
        mock_db.query.return_value.filter.return_value.first.return_value = sample_detail
        request = ReconciliationDetailReviewRequest(
            action="approve",
            is_matched=True,
            match_status="matched",
            review_notes="审核通过",
            auto_confidence=Decimal('0.95')
        )

        # 执行
        result = await service.review_detail(1, request, 1)

        # 验证
        assert result.match_status == "matched"
        assert result.is_matched is True
        assert result.reviewed_by == 1
        assert result.review_notes == "审核通过"
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_create_adjustment_success(self, service, mock_db, sample_detail):
        """测试成功创建调整记录"""
        # 准备数据
        mock_db.query.return_value.filter.return_value.first.return_value = sample_detail
        request = ReconciliationAdjustmentCreateRequest(
            adjustment_type="spend_adjustment",
            original_amount=Decimal('1000.00'),
            adjustment_amount=Decimal('-50.00'),
            adjustment_reason="data_error",
            detailed_reason="平台数据延迟",
            evidence_url="https://example.com/evidence.pdf"
        )

        # 模拟调整记录
        adjustment = ReconciliationAdjustment(
            detail_id=1,
            batch_id=1,
            adjustment_type=request.adjustment_type,
            original_amount=request.original_amount,
            adjustment_amount=request.adjustment_amount,
            adjusted_amount=Decimal('950.00'),
            adjustment_reason=request.adjustment_reason,
            detailed_reason=request.detailed_reason,
            evidence_url=request.evidence_url,
            approved_by=1
        )
        mock_db.add.return_value = None

        # 执行
        result = await service.create_adjustment(1, request, 1)

        # 验证
        assert result.adjustment_type == "spend_adjustment"
        assert result.adjustment_amount == Decimal('-50.00')
        assert result.adjusted_amount == Decimal('950.00')
        # P1 修复：修复未定义变量 detail → sample_detail
        assert sample_detail.match_status == "resolved"

    @pytest.mark.asyncio
    async def test_get_statistics(self, service, mock_db):
        """测试获取对账统计"""
        # 准备模拟数据
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10

        # 模拟统计结果
        mock_stats = Mock()
        mock_stats.platform_total = Decimal('10000.00')
        mock_stats.internal_total = Decimal('9500.00')
        mock_stats.difference_total = Decimal('500.00')
        mock_query.with_entities.return_value.first.return_value = mock_stats

        # 执行
        result = await service.get_statistics()

        # 验证
        assert result.total_batches == 10
        assert result.total_platform_spend == Decimal('10000.00')
        assert result.total_internal_spend == Decimal('9500.00')
        assert result.total_difference == Decimal('500.00')

    @pytest.mark.asyncio
    async def test_export_reconciliation_data(self, service, mock_db):
        """测试导出对账数据"""
        # 准备模拟数据
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query

        # 模拟导出数据
        mock_details = [
            Mock(
                batch=Mock(batch_no="REC001", reconciliation_date=date.today()),
                ad_account=Mock(account_name="账户1"),
                project=Mock(name="项目1"),
                channel=Mock(name="渠道1"),
                platform_spend=Decimal('1000.00'),
                internal_spend=Decimal('950.00'),
                spend_difference=Decimal('50.00'),
                is_matched=False,
                match_status="pending",
                difference_type="amount_mismatch",
                difference_reason="时间差异",
                created_at=datetime.now()
            )
        ]
        mock_query.all.return_value = mock_details

        # 执行
        result = await service.export_reconciliation_data()

        # 验证
        assert len(result) == 1
        assert result[0]["batch_no"] == "REC001"
        assert result[0]["ad_account_name"] == "账户1"
        assert result[0]["platform_spend"] == 1000.00
        assert result[0]["spend_difference"] == 50.00

    @pytest.mark.asyncio
    async def test_update_batch_statistics(self, service, mock_db):
        """测试更新批次统计"""
        # 准备模拟数据
        mock_batch = Mock()
        mock_batch.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_batch

        # 模拟详情数据
        mock_details = [
            Mock(is_matched=True, platform_spend=Decimal('1000.00'), internal_spend=Decimal('1000.00'),
                  spend_difference=Decimal('0.00'), match_status="auto_matched"),
            Mock(is_matched=False, platform_spend=Decimal('1000.00'), internal_spend=Decimal('950.00'),
                  spend_difference=Decimal('50.00'), match_status="manual_review")
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_details

        # 执行
        await service._update_batch_statistics(1)

        # 验证
        assert mock_batch.total_accounts == 2
        assert mock_batch.matched_accounts == 1
        assert mock_batch.mismatched_accounts == 1
        assert mock_batch.total_platform_spend == Decimal('2000.00')
        assert mock_batch.total_internal_spend == Decimal('1950.00')
        assert mock_batch.total_difference == Decimal('50.00')
        assert mock_batch.auto_matched == 1
        assert mock_batch.manual_reviewed == 1

    @pytest.mark.asyncio
    async def test_permission_check_for_account_manager(
        self, service, mock_db, sample_user
    ):
        """测试账户管理员权限检查"""
        # 设置用户角色
        sample_user.role = "account_manager"

        # 模拟没有权限的批次
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        # P0-RS-001: PermissionError → PermissionDeniedError
        with pytest.raises(PermissionDeniedError) as exc_info:
            await service.get_batch_by_id(1, sample_user.id, sample_user.role)

        # P1 修复：BIZ_303 不存在于 ERROR_CODES_SOT.md v2.1
        # 权限不足应使用 AUTH_500（权限不足, 403）- ERROR_CODES_SOT.md v2.1
        assert "AUTH_500" in str(exc_info.value) or exc_info.value.code == "AUTH_500"
        assert "无权限访问" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_auto_match_rate_calculation(self, service, mock_db):
        """测试自动匹配率计算"""
        # 准备模拟数据
        mock_batch = Mock()
        mock_batch.total_accounts = 100
        mock_batch.matched_accounts = 80
        mock_batch.mismatched_accounts = 20
        mock_batch.total_platform_spend = Decimal('10000.00')
        mock_batch.total_difference = Decimal('100.00')
        mock_db.query.return_value.filter.return_value.first.return_value = mock_batch

        # 模拟统计数据
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 100

        mock_stats = Mock()
        mock_stats.platform_total = Decimal('10000.00')
        mock_stats.internal_total = Decimal('9900.00')
        mock_stats.difference_total = Decimal('100.00')
        mock_query.with_entities.return_value.first.return_value = mock_stats

        # 执行
        result = await service.get_statistics()

        # 验证计算结果
        assert result.auto_match_rate == 80.0  # 80/100 * 100
        assert result.manual_review_rate == 20.0  # 20/100 * 100
        assert result.difference_rate == 1.0  # 100/10000 * 100