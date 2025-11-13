"""
对账管理服务测试
Version: 1.0
Author: Claude协作开发
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
from unittest.mock import Mock, patch, AsyncMock

from models.reconciliation import (
    ReconciliationBatch, ReconciliationDetail,
    ReconciliationAdjustment, ReconciliationReport
)
from models.user import User
from models.ad_account import AdAccount
from models.project import Project
from models.channel import Channel
from schemas.reconciliation import (
    ReconciliationBatchCreateRequest,
    ReconciliationDetailReviewRequest,
    ReconciliationAdjustmentCreateRequest,
    ReconciliationReportGenerateRequest
)
from services.reconciliation_service import ReconciliationService
from exceptions import ValidationError, NotFoundError, PermissionError


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
        return User(
            id=1,
            name="测试用户",
            email="test@example.com",
            role="admin"
        )

    @pytest.fixture
    def sample_batch(self):
        """示例对账批次"""
        return ReconciliationBatch(
            id=1,
            batch_no="REC20251112143000123",
            reconciliation_date=date.today(),
            status="pending",
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

        # 模拟批次创建
        with patch('services.reconciliation_service.generate_request_no') as mock_gen:
            mock_gen.return_value = "REC20251112143000123"

            batch = ReconciliationBatch(
                batch_no="REC20251112143000123",
                reconciliation_date=request.reconciliation_date,
                status="pending",
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
            assert result.status == "pending"
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

        # 执行并验证异常
        with pytest.raises(ValidationError) as exc_info:
            await service.create_batch(request, 1)

        assert exc_info.value.error_code == "BIZ_302"
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

        # 执行
        batches, total = await service.get_batches(
            page=1,
            page_size=20,
            status="pending",
            date_from=date(2025, 11, 1),
            date_to=date(2025, 11, 30)
        )

        # 验证
        assert len(batches) == 1
        assert total == 1
        assert batches[0].status == "pending"

    @pytest.mark.asyncio
    async def test_get_batch_by_id_not_found(self, service, mock_db):
        """测试获取不存在的对账批次"""
        # 模拟批次不存在
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # 执行并验证异常
        with pytest.raises(NotFoundError) as exc_info:
            await service.get_batch_by_id(999)

        assert exc_info.value.error_code == "SYS_004"
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

        # 执行并验证异常
        with pytest.raises(ValidationError) as exc_info:
            await service.run_reconciliation(1, 1)

        assert exc_info.value.error_code == "BIZ_306"
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
        assert detail.match_status == "resolved"

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

        # 执行并验证异常
        with pytest.raises(PermissionError) as exc_info:
            await service.get_batch_by_id(1, sample_user.id, sample_user.role)

        assert exc_info.value.error_code == "BIZ_303"
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