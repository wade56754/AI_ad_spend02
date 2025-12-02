"""
对账管理服务测试
Version: 2.0 - Aligned with SoT (align-reconciliation-batch-v2)
Author: Claude协作开发

变更说明：
- v2.0: 完全对齐 SoT DATA_SCHEMA.md v5.2 和 STATE_MACHINE.md v2.6
  - 使用正确的字段名：batch_code, period_start/period_end, total_system_spend 等
  - 使用属性别名：batch_no → batch_code, reconciliation_date → period_end
  - ReconciliationAdjustment 模型已实现
  - 所有 pytest.skip() 已移除，13/13 测试通过
"""

import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from backend.models import (
    ReconciliationBatch, ReconciliationDetail, ReconciliationAdjustment,
    User, AdAccount, Project, Channel
)
from backend.schemas.reconciliation import (
    ReconciliationBatchCreateRequest,
    ReconciliationDetailReviewRequest,
    ReconciliationAdjustmentCreateRequest,
    ReconciliationReportGenerateRequest
)
from backend.services.reconciliation_service import ReconciliationService
from backend.exceptions.custom_exceptions import (
    ValidationError,
    ResourceNotFoundError as NotFoundError,
    PermissionDeniedError as PermissionError,
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
        """示例用户 - 使用 Mock 对象模拟 User 字段"""
        from unittest.mock import Mock
        from uuid import uuid4
        # 使用 Mock 创建用户，避免数据库操作
        user = Mock()
        user.id = uuid4()  # UUID 类型
        user.username = "测试用户"
        user.email = "test@example.com"
        user.role = "admin"  # 字符串类型，与 UserRole.ADMIN.value 一致
        user.is_active = True
        return user

    @pytest.fixture
    def sample_batch(self):
        """示例对账批次 - 使用 Mock 对象模拟模型字段"""
        from unittest.mock import Mock
        from uuid import uuid4

        # 使用 Mock 创建批次对象，包含测试所需的所有字段
        batch = Mock()
        batch.id = 1
        batch.batch_code = "REC20251112143000123"
        batch.batch_no = "REC20251112143000123"  # 兼容别名
        batch.period_start = date.today() - timedelta(days=7)
        batch.period_end = date.today()
        batch.reconciliation_date = date.today()  # 测试需要的字段
        batch.status = "draft"  # 使用字符串值
        batch.total_system_spend = Decimal('0.00')
        batch.total_actual_spend = Decimal('0.00')
        batch.discrepancy = Decimal('0.00')
        batch.created_by = uuid4()
        batch.reviewed_by = None
        batch.closed_at = None
        batch.version = 1
        # 测试可能需要的额外字段
        batch.total_accounts = 0
        batch.matched_accounts = 0
        batch.mismatched_accounts = 0
        batch.auto_matched = 0
        batch.manual_reviewed = 0
        batch.auto_match = True
        batch.notes = None
        batch.started_at = None
        batch.completed_at = None
        batch.created_at = datetime.now()
        batch.updated_at = datetime.now()
        # 向后兼容属性
        batch.total_platform_spend = Decimal('0.00')
        batch.total_internal_spend = Decimal('0.00')
        batch.total_difference = Decimal('0.00')
        return batch

    @pytest.fixture
    def sample_detail(self):
        """示例对账详情 - 使用 Mock 对象模拟模型字段"""
        from unittest.mock import Mock
        from datetime import datetime

        # 使用 Mock 创建明细对象，包含测试所需的所有字段
        detail = Mock()
        detail.id = 1
        detail.batch_id = 1
        detail.ad_account_id = 1
        detail.system_spend = Decimal('1000.00')
        detail.actual_spend = Decimal('950.00')
        detail.discrepancy = Decimal('50.00')
        detail.status = "pending"  # 使用字符串值
        detail.notes = "测试对账明细"
        detail.version = 1
        # 测试可能需要的额外字段（来自 service 中使用的字段）
        detail.is_matched = False
        detail.match_status = "pending"
        detail.reviewed_by = None
        detail.reviewed_at = None
        detail.review_notes = None
        detail.auto_confidence = Decimal('0.00')
        detail.difference_type = None
        detail.difference_reason = None
        detail.resolved_by = None
        detail.resolved_at = None
        detail.resolution_method = None
        detail.resolution_notes = None
        detail.created_at = datetime.now()
        detail.updated_at = datetime.now()
        # 兼容别名
        detail.platform_spend = Decimal('1000.00')
        detail.internal_spend = Decimal('950.00')
        detail.spend_difference = Decimal('50.00')
        return detail

    @pytest.mark.asyncio
    async def test_create_batch_success(self, service, mock_db, sample_user):
        """测试成功创建对账批次

        服务代码使用 period_end 进行重复检查，使用 batch_code/period_start/period_end 创建批次。
        属性别名 batch_no → batch_code, reconciliation_date → period_end 已实现。
        """
        # 模拟不存在重复批次
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # 创建请求
        request = ReconciliationBatchCreateRequest(
            reconciliation_date=date.today() - timedelta(days=1),  # 昨天
            auto_match=True,
            notes="测试批次"
        )

        # 执行
        result = await service.create_batch(request, sample_user.id)

        # 验证 - 服务代码会调用 db.add, db.commit, db.refresh
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_batch_duplicate_date(self, service, mock_db, sample_batch):
        """测试创建重复日期的对账批次

        服务代码使用 period_end 进行重复检查，如果存在相同日期的批次，抛出 BusinessLogicError。
        """
        # 模拟已存在相同日期的批次
        mock_db.query.return_value.filter.return_value.first.return_value = sample_batch

        # 创建请求
        request = ReconciliationBatchCreateRequest(
            reconciliation_date=date.today(),
            auto_match=True
        )

        # 执行并验证异常
        with pytest.raises(BusinessLogicError) as exc_info:
            await service.create_batch(request, 1)

        assert exc_info.value.error_code == "BIZ_302"
        assert "该日期已存在对账批次" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_batches_with_filters(self, service, mock_db, sample_batch):
        """测试带过滤条件获取对账批次列表"""
        # 修改 sample_batch 的 status 为测试所需的值
        sample_batch.status = "draft"

        # 准备模拟数据
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_batch]

        # 执行
        batches, total = await service.get_batches(
            page=1,
            page_size=20,
            status="draft",  # 使用正确的状态值
            date_from=date(2025, 11, 1),
            date_to=date(2025, 11, 30)
        )

        # 验证
        assert len(batches) == 1
        assert total == 1
        assert batches[0].status == "draft"  # 匹配 fixture 中的状态

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
        """测试成功执行对账

        服务代码流程：
        1. get_batch_by_id 检查批次存在且有权限
        2. 检查状态必须是 draft 或 pending_review
        3. 为所有活跃账户创建对账明细
        4. 更新批次汇总金额：total_system_spend, total_actual_spend, discrepancy
        """
        # 设置 sample_batch 为 draft 状态
        sample_batch.status = "draft"

        # 模拟 AdAccount 查询返回空列表（简化测试）
        mock_ad_account = Mock()
        mock_ad_account.id = 1
        mock_ad_account.status = "active"

        call_count = [0]

        def query_side_effect(model):
            call_count[0] += 1
            mock_query = Mock()

            model_name = getattr(model, '__name__', str(model))

            if 'ReconciliationBatch' in model_name:
                mock_query.filter.return_value.first.return_value = sample_batch
            elif 'AdAccount' in model_name:
                mock_query.filter.return_value.all.return_value = []  # 无账户，简化测试
            else:
                mock_query.filter.return_value.first.return_value = None
                mock_query.filter.return_value.all.return_value = []

            return mock_query

        mock_db.query = Mock(side_effect=query_side_effect)

        # 执行
        result = await service.run_reconciliation(1, 1)

        # 验证状态已更新（最终为 approved）
        assert sample_batch.status == "approved"
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_run_reconciliation_invalid_status(
        self, service, mock_db, sample_batch
    ):
        """测试执行非 draft/pending_review 状态的对账批次

        服务代码检查状态必须是 draft 或 pending_review，否则抛出 BusinessLogicError。
        """
        # 设置 sample_batch 为 completed 状态（终态，不允许执行对账）
        sample_batch.status = "completed"
        mock_db.query.return_value.filter.return_value.first.return_value = sample_batch

        # 执行并验证异常
        with pytest.raises(BusinessLogicError) as exc_info:
            await service.run_reconciliation(1, 1)

        assert exc_info.value.error_code == "BIZ_306"
        assert "只能对草稿或待审核的批次执行对账" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_review_detail_success(self, service, mock_db, sample_detail):
        """测试成功审核对账差异

        注意：服务代码中 review_detail 将审核信息存储在 notes 字段中，
        并使用 status 字段（而非 match_status）来表示匹配状态。
        """
        # 准备数据
        mock_db.query.return_value.filter.return_value.first.return_value = sample_detail
        # 确保 sample_detail 有 _update_batch_statistics 需要的 batch_id
        sample_detail.batch_id = 1

        # 为 _update_batch_statistics 准备 mock
        mock_batch = Mock()
        mock_batch.id = 1
        mock_batch.total_accounts = 0
        mock_batch.matched_accounts = 0
        mock_batch.mismatched_accounts = 0
        mock_batch.auto_matched = 0
        mock_batch.manual_reviewed = 0
        mock_batch.total_system_spend = Decimal('0.00')
        mock_batch.total_actual_spend = Decimal('0.00')
        mock_batch.discrepancy = Decimal('0.00')

        # 设置 mock_db.query 返回不同的结果
        def query_side_effect(model):
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = (
                sample_detail if model.__name__ == 'ReconciliationDetail' else mock_batch
            )
            mock_query.filter.return_value.all.return_value = [sample_detail]
            return mock_query

        mock_db.query = Mock(side_effect=query_side_effect)
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        request = ReconciliationDetailReviewRequest(
            action="approve",
            is_matched=True,
            match_status="matched",
            review_notes="审核通过",
            auto_confidence=Decimal('0.95')
        )

        # 执行
        result = await service.review_detail(1, request, 1)

        # 验证 - 使用 status 字段而非 match_status
        # 服务代码会将 approve + is_matched=True 映射到 status = "confirmed"
        assert result.status == "confirmed"
        # 服务代码将审核信息存储在 notes 字段中，不是 reviewed_by
        assert "审核人" in result.notes
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_create_adjustment_success(self, service, mock_db, sample_detail):
        """测试成功创建调整记录

        ReconciliationAdjustment 模型已按 DATA_SCHEMA.md v5.2 实现。
        字段：detail_id, adjustment_type, amount, reason, created_by
        """
        # 设置 mock 返回 sample_detail
        mock_batch = Mock()
        mock_batch.id = 1
        mock_batch.total_system_spend = Decimal('1000.00')
        mock_batch.total_actual_spend = Decimal('950.00')
        mock_batch.discrepancy = Decimal('50.00')

        def query_side_effect(model):
            mock_query = Mock()
            model_name = getattr(model, '__name__', str(model))

            if 'ReconciliationDetail' in model_name:
                mock_query.filter.return_value.first.return_value = sample_detail
                mock_query.filter.return_value.all.return_value = [sample_detail]
            elif 'ReconciliationBatch' in model_name:
                mock_query.filter.return_value.first.return_value = mock_batch
            else:
                mock_query.filter.return_value.first.return_value = None
                mock_query.filter.return_value.all.return_value = []

            return mock_query

        mock_db.query = Mock(side_effect=query_side_effect)

        # 创建请求 - 使用 SoT 定义的调整类型
        request = ReconciliationAdjustmentCreateRequest(
            adjustment_type="increase",  # SoT: increase/decrease/writeoff
            adjustment_amount=Decimal('50.00'),
            adjustment_reason="数据差异调整"
        )

        # 执行
        result = await service.create_adjustment(1, request, 1)

        # 验证 - 服务代码会调用 db.add, db.commit, db.refresh
        mock_db.add.assert_called()
        mock_db.commit.assert_called()
        # 验证 sample_detail 状态已更新
        assert sample_detail.status == "adjusted"

    @pytest.mark.asyncio
    async def test_get_statistics(self, service, mock_db):
        """测试获取对账统计"""
        # ========================================
        # 简单的 QueryStub 模式 - 避免 MagicMock 属性泄漏
        # ========================================

        # 1. FakeBatchStats - 模拟 with_entities().first() 的返回值
        class FakeBatchStats:
            """统计结果对象，属性必须是 Decimal 类型"""
            platform_total = Decimal('10000.00')
            internal_total = Decimal('9500.00')
            difference_total = Decimal('500.00')

        # 2. QueryStub - 链式调用返回 self，特定方法返回固定值
        class QueryStub:
            """简单的查询存根，支持链式调用"""
            def __init__(self, count_val=0, first_val=None, scalar_val=None, filtered_count_val=None):
                self._count_val = count_val
                self._first_val = first_val
                self._scalar_val = scalar_val
                self._filtered_count_val = filtered_count_val  # filter().count() 的返回值

            def filter(self, *args, **kwargs):
                # filter() 返回一个新的 QueryStub，使用 filtered_count_val 作为 count() 的返回值
                if self._filtered_count_val is not None:
                    return QueryStub(
                        count_val=self._filtered_count_val,
                        first_val=self._first_val,
                        scalar_val=self._scalar_val
                    )
                # 如果没有设置 filtered_count_val，返回自身（用于链式调用）
                return self

            def join(self, *args, **kwargs):
                return self

            def with_entities(self, *args, **kwargs):
                return self

            def order_by(self, *args, **kwargs):
                return self

            def count(self):
                return self._count_val

            def first(self):
                return self._first_val

            def scalar(self):
                return self._scalar_val

        # 3. 创建各类查询的 Stub 实例
        # batch_query: query.count() = 10, query.filter(...).count() = 5 (每个 filter 都返回 5)
        batch_query_stub = QueryStub(
            count_val=10,  # total_batches
            first_val=FakeBatchStats(),  # batch_stats
            filtered_count_val=5  # completed_batches, exception_batches, resolved_batches
        )

        # detail_query: details_query.count() = 10, details_query.filter(...).count() = 8
        detail_query_stub = QueryStub(
            count_val=10,  # total_accounts
            filtered_count_val=8  # matched_accounts
        )

        adjustment_query_stub = QueryStub(scalar_val=Decimal('0.00'))
        avg_query_stub = QueryStub(scalar_val=24.5)

        # 4. 设置 mock_db.query 的返回值
        def query_side_effect(model):
            # 处理 SQLAlchemy 函数表达式（如 func.avg(...)）
            # func.avg(...) 返回的是一个 Function 对象，通常有 __class__.__name__ == 'Function'
            model_type_name = getattr(model, '__class__', type(model)).__name__
            if model_type_name == 'Function' or (hasattr(model, '__call__') and not hasattr(model, '__name__')):
                return avg_query_stub
            
            model_name = getattr(model, '__name__', '') or str(model)
            
            if 'ReconciliationAdjustment' in model_name:
                return adjustment_query_stub
            elif 'ReconciliationDetail' in model_name:
                # detail_query.join(...) 返回 detail_query_stub
                class DetailQueryWithJoin:
                    def join(self, *args):
                        return detail_query_stub
                    def filter(self, *args):
                        return QueryStub(count_val=8)  # matched_accounts
                    def count(self):
                        return 10  # total_accounts
                return DetailQueryWithJoin()
            elif 'ReconciliationBatch' in model_name:
                # 明确处理 ReconciliationBatch
                return batch_query_stub
            else:
                # 默认返回 batch_query_stub（用于 ReconciliationBatch 或其他模型）
                return batch_query_stub

        # 直接设置 mock_db.query 为函数，而不是使用 side_effect
        mock_db.query = query_side_effect

        # 执行
        result = await service.get_statistics()

        # 验证 - 确保返回的是普通数值，不是 MagicMock
        assert isinstance(result.total_batches, int)
        assert isinstance(result.total_platform_spend, Decimal)
        assert isinstance(result.total_internal_spend, Decimal)
        assert isinstance(result.total_difference, Decimal)

        assert result.total_batches == 10
        assert result.completed_batches == 5
        assert result.exception_batches == 5
        assert result.resolved_batches == 5
        assert result.total_platform_spend == Decimal('10000.00')
        assert result.total_internal_spend == Decimal('9500.00')
        assert result.total_difference == Decimal('500.00')
        assert result.total_accounts == 10
        assert result.matched_accounts == 8
        assert result.mismatched_accounts == 2
        assert result.total_adjustments == Decimal('0.00')
        assert result.net_difference == Decimal('500.00')
        assert result.auto_match_rate == 80.0
        assert result.manual_review_rate == 20.0
        assert result.difference_rate == 5.0
        assert result.avg_processing_time_hours == 24.5
        assert result.resolution_rate == 50.0  # 5/10 * 100

    @pytest.mark.asyncio
    async def test_export_reconciliation_data(self, service, mock_db):
        """测试导出对账数据

        服务代码使用属性别名访问：
        - detail.batch.batch_no → batch_code
        - detail.batch.reconciliation_date → period_end
        - detail.ad_account.project.name
        - detail.ad_account.channel.name
        """
        # 创建 mock 对象链
        mock_project = Mock()
        mock_project.name = "测试项目"

        mock_channel = Mock()
        mock_channel.name = "测试渠道"

        mock_ad_account = Mock()
        mock_ad_account.account_name = "测试账户"
        mock_ad_account.project = mock_project
        mock_ad_account.channel = mock_channel

        mock_batch = Mock()
        mock_batch.batch_code = "REC20251112143000123"
        mock_batch.batch_no = "REC20251112143000123"  # 属性别名
        mock_batch.period_end = date.today()
        mock_batch.reconciliation_date = date.today()  # 属性别名

        mock_detail = Mock()
        mock_detail.batch = mock_batch
        mock_detail.ad_account = mock_ad_account
        mock_detail.system_spend = Decimal('1000.00')
        mock_detail.actual_spend = Decimal('950.00')
        mock_detail.discrepancy = Decimal('50.00')
        mock_detail.status = "pending"
        mock_detail.notes = "测试备注"
        mock_detail.created_at = datetime.now()

        # 设置 mock_db.query 返回
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_detail]
        mock_db.query.return_value = mock_query

        # 执行
        result = await service.export_reconciliation_data(batch_id=1)

        # 验证
        assert len(result) == 1
        assert result[0]["batch_no"] == "REC20251112143000123"
        assert result[0]["ad_account_name"] == "测试账户"
        assert result[0]["project_name"] == "测试项目"
        assert result[0]["channel_name"] == "测试渠道"
        assert result[0]["platform_spend"] == 1000.00
        assert result[0]["internal_spend"] == 950.00
        assert result[0]["spend_difference"] == 50.00
        assert result[0]["match_status"] == "pending"

    @pytest.mark.asyncio
    async def test_update_batch_statistics(self, service, mock_db):
        """测试更新批次统计

        根据 SoT spec，服务代码只更新批次的汇总金额字段：
        - total_system_spend
        - total_actual_spend
        - discrepancy

        统计字段如 total_accounts, matched_accounts 等应从 ReconciliationDetail 按需计算，
        不再存储在批次表中。
        """
        # 准备模拟数据
        mock_batch = Mock()
        mock_batch.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_batch

        # 模拟详情数据 - 使用服务代码实际使用的字段名
        mock_details = [
            Mock(
                system_spend=Decimal('1000.00'),
                actual_spend=Decimal('1000.00'),
                discrepancy=Decimal('0.00')
            ),
            Mock(
                system_spend=Decimal('1000.00'),
                actual_spend=Decimal('950.00'),
                discrepancy=Decimal('50.00')
            )
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_details

        # 执行
        await service._update_batch_statistics(1)

        # 验证 - 只检查模型中存在的汇总金额字段
        assert mock_batch.total_system_spend == Decimal('2000.00')
        assert mock_batch.total_actual_spend == Decimal('1950.00')
        assert mock_batch.discrepancy == Decimal('50.00')
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_permission_check_for_account_manager(
        self, service, mock_db, sample_user
    ):
        """测试账户管理员权限检查

        服务代码逻辑：
        1. 首先查询 ReconciliationBatch（必须存在，否则抛出 ResourceNotFoundError）
        2. 如果角色是 account_manager，进行权限检查
        3. 权限检查通过 join ReconciliationDetail -> AdAccount -> Project
        4. 如果权限检查失败（first() 返回 None），抛出 PermissionDeniedError
        """
        # 设置用户角色
        sample_user.role = "account_manager"

        # 创建一个 mock batch 对象（批次必须存在，才能进行权限检查）
        mock_batch = Mock()
        mock_batch.id = 1
        mock_batch.status = "draft"

        # 计数器跟踪 query() 调用
        call_count = [0]

        def query_side_effect(model):
            call_count[0] += 1
            mock_query = Mock()

            if call_count[0] == 1:
                # 第一次查询：ReconciliationBatch - 返回 batch 对象
                mock_query.filter.return_value.first.return_value = mock_batch
            else:
                # 第二次查询：ReconciliationDetail 权限检查 - 返回 None（无权限）
                mock_query.filter.return_value = mock_query
                mock_query.join.return_value = mock_query
                mock_query.first.return_value = None

            return mock_query

        mock_db.query = Mock(side_effect=query_side_effect)

        # 执行并验证异常
        with pytest.raises(PermissionError) as exc_info:
            await service.get_batch_by_id(1, sample_user.id, sample_user.role)

        assert exc_info.value.error_code == "BIZ_303"
        assert "无权限访问" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_auto_match_rate_calculation(self, service, mock_db):
        """测试自动匹配率计算"""
        # ========================================
        # 简单的 QueryStub 模式 - 避免 MagicMock 属性泄漏
        # ========================================

        # 1. FakeBatchStats - 模拟 with_entities().first() 的返回值
        class FakeBatchStats:
            """统计结果对象，属性必须是 Decimal 类型"""
            platform_total = Decimal('10000.00')
            internal_total = Decimal('9900.00')
            difference_total = Decimal('100.00')

        # 2. QueryStub - 链式调用返回 self，特定方法返回固定值
        class QueryStub:
            """简单的查询存根，支持链式调用"""
            def __init__(self, count_val=0, first_val=None, scalar_val=None, filtered_count_val=None):
                self._count_val = count_val
                self._first_val = first_val
                self._scalar_val = scalar_val
                self._filtered_count_val = filtered_count_val  # filter().count() 的返回值

            def filter(self, *args, **kwargs):
                # filter() 返回一个新的 QueryStub，使用 filtered_count_val 作为 count() 的返回值
                if self._filtered_count_val is not None:
                    return QueryStub(
                        count_val=self._filtered_count_val,
                        first_val=self._first_val,
                        scalar_val=self._scalar_val
                    )
                # 如果没有设置 filtered_count_val，返回自身（用于链式调用）
                return self

            def join(self, *args, **kwargs):
                return self

            def with_entities(self, *args, **kwargs):
                return self

            def order_by(self, *args, **kwargs):
                return self

            def count(self):
                return self._count_val

            def first(self):
                return self._first_val

            def scalar(self):
                return self._scalar_val

        # 3. 创建各类查询的 Stub 实例
        # batch_query: query.count() = 10, query.filter(...).count() = 5 (每个 filter 都返回 5)
        batch_query_stub = QueryStub(
            count_val=10,  # total_batches
            first_val=FakeBatchStats(),  # batch_stats
            filtered_count_val=5  # completed_batches, exception_batches, resolved_batches
        )

        # detail_query: details_query.count() = 100, details_query.filter(...).count() = 80
        detail_query_stub = QueryStub(
            count_val=100,  # total_accounts
            filtered_count_val=80  # matched_accounts
        )

        adjustment_query_stub = QueryStub(scalar_val=Decimal('0.00'))
        avg_query_stub = QueryStub(scalar_val=24.5)

        # 4. 设置 mock_db.query 的返回值
        def query_side_effect(model):
            # 处理 SQLAlchemy 函数表达式（如 func.avg(...)）
            # func.avg(...) 返回的是一个 Function 对象，通常有 __class__.__name__ == 'Function'
            model_type_name = getattr(model, '__class__', type(model)).__name__
            if model_type_name == 'Function' or (hasattr(model, '__call__') and not hasattr(model, '__name__')):
                return avg_query_stub
            
            model_name = getattr(model, '__name__', '') or str(model)
            
            if 'ReconciliationAdjustment' in model_name:
                return adjustment_query_stub
            elif 'ReconciliationDetail' in model_name:
                # detail_query.join(...) 返回 detail_query_stub
                class DetailQueryWithJoin:
                    def join(self, *args):
                        return detail_query_stub
                    def filter(self, *args):
                        return QueryStub(count_val=80)  # matched_accounts
                    def count(self):
                        return 100  # total_accounts
                return DetailQueryWithJoin()
            elif 'ReconciliationBatch' in model_name:
                # 明确处理 ReconciliationBatch
                return batch_query_stub
            else:
                # 默认返回 batch_query_stub（用于 ReconciliationBatch 或其他模型）
                return batch_query_stub

        # 直接设置 mock_db.query 为函数，而不是使用 side_effect
        mock_db.query = query_side_effect

        # 执行
        result = await service.get_statistics()

        # 验证 - 确保返回的是普通数值，不是 MagicMock
        assert isinstance(result.auto_match_rate, (int, float))
        assert isinstance(result.manual_review_rate, (int, float))

        # 验证计算结果
        assert result.total_batches == 10
        assert result.total_platform_spend == Decimal('10000.00')
        assert result.total_internal_spend == Decimal('9900.00')
        assert result.total_difference == Decimal('100.00')
        assert result.total_accounts == 100
        assert result.matched_accounts == 80
        assert result.mismatched_accounts == 20
        assert result.auto_match_rate == 80.0  # 80/100 * 100
        assert result.manual_review_rate == 20.0  # 20/100 * 100
        assert result.difference_rate == 1.0  # 100/10000 * 100
        assert result.avg_processing_time_hours == 24.5
        assert result.completed_batches == 5
        assert result.exception_batches == 5
        assert result.resolved_batches == 5
        assert result.resolution_rate == 50.0  # 5/10 * 100