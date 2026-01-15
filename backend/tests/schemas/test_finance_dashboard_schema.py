"""
财务仪表盘 Schema 层测试 - TC-121 ~ TC-125

测试 Pydantic 模型验证：
- FinanceOverviewResponse: 财务概览响应
- ProfitRankingResponse: 项目盈亏排行响应
- TransactionsResponse: 收支流水响应
- AgingResponse: 账期分析响应
- Decimal 精度验证

SoT References:
- DATA_SCHEMA.md v5.11 (数据模型)
- FINANCE_MODULE_DEV.md v1.1 (字段定义)

Version: 1.0
Author: AI Code Factory
Created: 2026-01-15
"""

import pytest
from datetime import date
from decimal import Decimal
from pydantic import ValidationError

from backend.schemas.finance_dashboard import (
    # Response models
    FinanceOverviewResponse,
    BalanceData,
    SpendData,
    ProfitData,
    ProfitRankingResponse,
    ProfitRankingItem,
    FundDistributionResponse,
    FundDistributionItem,
    TransactionsResponse,
    TransactionItem,
    AgingResponse,
    AgingBucketSummary,
    AgingDetailItem,
    ProjectProfitTableItem,
    AccountBalanceItem,
    # Request params
    FinanceOverviewParams,
    ProfitRankingParams,
    TransactionsParams,
    AgingParams,
)


class TestFinanceOverviewResponse:
    """TC-121: FinanceOverviewResponse 必填字段验证"""

    def test_valid_response(self):
        """测试有效响应"""
        response = FinanceOverviewResponse(
            balance=BalanceData(
                current=Decimal("10000.00"),
                previous=Decimal("9000.00"),
                change_percent=11.11
            ),
            spend=SpendData(
                current_month=Decimal("3000.00"),
                previous_month=Decimal("2500.00"),
                change_percent=20.0
            ),
            profit=ProfitData(
                gross_profit=Decimal("2000.00"),
                margin_rate=25.0,
                revenue=Decimal("8000.00"),
                cost=Decimal("6000.00"),
            )
        )

        assert response.balance.current == Decimal("10000.00")
        assert response.spend.current_month == Decimal("3000.00")
        assert response.profit.gross_profit == Decimal("2000.00")

    def test_default_values(self):
        """测试默认值"""
        response = FinanceOverviewResponse()

        assert response.balance.current == Decimal("0")
        assert response.balance.change_percent is None
        assert response.spend.current_month == Decimal("0")
        assert response.profit.margin_rate == 0.0

    def test_balance_data_fields(self):
        """测试余额数据字段"""
        balance = BalanceData(
            current=Decimal("5000.00"),
            previous=Decimal("4000.00"),
            change_percent=25.0
        )

        assert balance.current == Decimal("5000.00")
        assert balance.previous == Decimal("4000.00")
        assert balance.change_percent == 25.0

    def test_spend_data_fields(self):
        """测试消耗数据字段"""
        spend = SpendData(
            current_month=Decimal("1000.00"),
            previous_month=Decimal("800.00"),
            change_percent=25.0
        )

        assert spend.current_month == Decimal("1000.00")
        assert spend.previous_month == Decimal("800.00")

    def test_profit_data_fields(self):
        """测试毛利数据字段"""
        profit = ProfitData(
            gross_profit=Decimal("2000.00"),
            margin_rate=20.0,
            revenue=Decimal("10000.00"),
            cost=Decimal("8000.00"),
        )

        assert profit.gross_profit == Decimal("2000.00")
        assert profit.margin_rate == 20.0
        assert profit.revenue == Decimal("10000.00")
        assert profit.cost == Decimal("8000.00")


class TestProfitRankingResponse:
    """TC-122: ProfitRankingResponse 列表元素验证"""

    def test_valid_response(self):
        """测试有效响应"""
        response = ProfitRankingResponse(
            items=[
                ProfitRankingItem(
                    project_id=1,
                    project_name="项目A",
                    revenue=Decimal("10000.00"),
                    cost=Decimal("6000.00"),
                    profit=Decimal("4000.00"),
                    margin_rate=40.0
                ),
                ProfitRankingItem(
                    project_id=2,
                    project_name="项目B",
                    revenue=Decimal("8000.00"),
                    cost=Decimal("5000.00"),
                    profit=Decimal("3000.00"),
                    margin_rate=37.5
                ),
            ]
        )

        assert len(response.items) == 2
        assert response.items[0].project_name == "项目A"
        assert response.items[1].profit == Decimal("3000.00")

    def test_empty_items(self):
        """测试空列表"""
        response = ProfitRankingResponse(items=[])
        assert response.items == []

    def test_profit_ranking_item_required_fields(self):
        """测试项目必填字段"""
        item = ProfitRankingItem(
            project_id=1,
            project_name="测试项目",
            revenue=Decimal("1000.00"),
            cost=Decimal("500.00"),
            profit=Decimal("500.00"),
            margin_rate=50.0
        )

        assert item.project_id == 1
        assert item.project_name == "测试项目"

    def test_profit_ranking_item_missing_required(self):
        """测试缺少必填字段"""
        with pytest.raises(ValidationError):
            ProfitRankingItem(
                project_name="测试项目"  # 缺少 project_id
            )


class TestTransactionsResponse:
    """TC-123: TransactionListResponse 分页字段验证"""

    def test_valid_response(self):
        """测试有效响应"""
        response = TransactionsResponse(
            items=[
                TransactionItem(
                    id="123e4567-e89b-12d3-a456-426614174000",
                    event_date=date(2026, 1, 15),
                    event_type="TOPUP",
                    amount=Decimal("5000.00"),
                    project_id=1,
                    project_name="测试项目",
                    description="充值",
                    source_type="manual"
                )
            ],
            total=1,
            page=1,
            page_size=20
        )

        assert response.total == 1
        assert response.page == 1
        assert response.page_size == 20
        assert len(response.items) == 1

    def test_pagination_fields(self):
        """测试分页字段"""
        response = TransactionsResponse(
            items=[],
            total=100,
            page=3,
            page_size=20
        )

        assert response.total == 100
        assert response.page == 3
        assert response.page_size == 20

    def test_transaction_item_event_types(self):
        """测试事件类型枚举"""
        valid_types = ["TOPUP", "SPEND", "PAYMENT", "TRANSFER", "ADJUSTMENT", "FEE", "REFUND"]

        for event_type in valid_types:
            item = TransactionItem(
                id="123e4567-e89b-12d3-a456-426614174000",
                event_date=date(2026, 1, 15),
                event_type=event_type,
                amount=Decimal("100.00")
            )
            assert item.event_type == event_type

    def test_transaction_item_source_types(self):
        """测试来源类型枚举"""
        valid_sources = ["excel_import", "api", "manual", "system"]

        for source in valid_sources:
            item = TransactionItem(
                id="123e4567-e89b-12d3-a456-426614174000",
                event_date=date(2026, 1, 15),
                event_type="TOPUP",
                amount=Decimal("100.00"),
                source_type=source
            )
            assert item.source_type == source

    def test_transaction_item_optional_fields(self):
        """测试可选字段"""
        item = TransactionItem(
            id="123e4567-e89b-12d3-a456-426614174000",
            event_date=date(2026, 1, 15),
            event_type="TOPUP",
            amount=Decimal("100.00")
        )

        assert item.project_id is None
        assert item.project_name is None
        assert item.description is None
        assert item.source_type is None


class TestAgingResponse:
    """TC-124: AgingAnalysisResponse 区间字段验证"""

    def test_valid_response(self):
        """测试有效响应"""
        response = AgingResponse(
            summary=[
                AgingBucketSummary(
                    bucket="0-30",
                    amount=Decimal("10000.00"),
                    percentage=50.0,
                    count=5
                ),
                AgingBucketSummary(
                    bucket="31-60",
                    amount=Decimal("5000.00"),
                    percentage=25.0,
                    count=3
                ),
                AgingBucketSummary(
                    bucket="61-90",
                    amount=Decimal("3000.00"),
                    percentage=15.0,
                    count=2
                ),
                AgingBucketSummary(
                    bucket="90+",
                    amount=Decimal("2000.00"),
                    percentage=10.0,
                    count=1
                ),
            ],
            details=[
                AgingDetailItem(
                    project_id=1,
                    project_name="项目A",
                    receivable=Decimal("5000.00"),
                    aging_days=45,
                    customer="客户X",
                    status="collecting"
                )
            ]
        )

        assert len(response.summary) == 4
        assert len(response.details) == 1

    def test_aging_bucket_enum(self):
        """测试账期区间枚举"""
        valid_buckets = ["0-30", "31-60", "61-90", "90+"]

        for bucket in valid_buckets:
            summary = AgingBucketSummary(
                bucket=bucket,
                amount=Decimal("1000.00"),
                percentage=25.0,
                count=1
            )
            assert summary.bucket == bucket

    def test_aging_status_enum(self):
        """测试账期状态枚举"""
        valid_statuses = ["normal", "collecting", "overdue"]

        for status in valid_statuses:
            detail = AgingDetailItem(
                project_id=1,
                project_name="测试项目",
                receivable=Decimal("1000.00"),
                aging_days=30,
                status=status
            )
            assert detail.status == status

    def test_aging_detail_item_fields(self):
        """测试账期明细字段"""
        detail = AgingDetailItem(
            project_id=1,
            project_name="项目A",
            receivable=Decimal("5000.00"),
            aging_days=45,
            customer="客户X",
            status="collecting"
        )

        assert detail.project_id == 1
        assert detail.receivable == Decimal("5000.00")
        assert detail.aging_days == 45
        assert detail.customer == "客户X"


class TestDecimalPrecision:
    """TC-125: Decimal 精度验证 (2 位小数)"""

    def test_balance_decimal_precision(self):
        """测试余额小数精度"""
        balance = BalanceData(
            current=Decimal("10000.99"),
            previous=Decimal("9000.01")
        )

        # Decimal 应该保持精度
        assert str(balance.current) == "10000.99"
        assert str(balance.previous) == "9000.01"

    def test_spend_decimal_precision(self):
        """测试消耗小数精度"""
        spend = SpendData(
            current_month=Decimal("3000.50"),
            previous_month=Decimal("2500.75")
        )

        assert str(spend.current_month) == "3000.50"
        assert str(spend.previous_month) == "2500.75"

    def test_profit_decimal_precision(self):
        """测试毛利小数精度"""
        profit = ProfitData(
            gross_profit=Decimal("2000.33"),
            margin_rate=25.55,
            revenue=Decimal("8000.00"),
            cost=Decimal("5999.67")
        )

        assert str(profit.gross_profit) == "2000.33"
        assert str(profit.cost) == "5999.67"

    def test_transaction_amount_precision(self):
        """测试交易金额精度"""
        item = TransactionItem(
            id="123e4567-e89b-12d3-a456-426614174000",
            event_date=date(2026, 1, 15),
            event_type="TOPUP",
            amount=Decimal("12345.67")
        )

        assert str(item.amount) == "12345.67"

    def test_ranking_item_precision(self):
        """测试排行项目金额精度"""
        item = ProfitRankingItem(
            project_id=1,
            project_name="测试",
            revenue=Decimal("10000.12"),
            cost=Decimal("6000.34"),
            profit=Decimal("3999.78"),
            margin_rate=39.99
        )

        assert str(item.revenue) == "10000.12"
        assert str(item.cost) == "6000.34"
        assert str(item.profit) == "3999.78"

    def test_decimal_from_string(self):
        """测试从字符串创建 Decimal"""
        balance = BalanceData(
            current=Decimal("10000.99")
        )
        assert balance.current == Decimal("10000.99")

    def test_decimal_from_int(self):
        """测试从整数创建 Decimal"""
        balance = BalanceData(
            current=Decimal(10000)
        )
        assert balance.current == Decimal("10000")

    def test_large_decimal_values(self):
        """测试大数值 Decimal"""
        balance = BalanceData(
            current=Decimal("999999999.99"),
            previous=Decimal("888888888.88")
        )

        assert balance.current == Decimal("999999999.99")
        assert balance.previous == Decimal("888888888.88")

    def test_negative_decimal_values(self):
        """测试负数 Decimal"""
        profit = ProfitData(
            gross_profit=Decimal("-1000.50"),
            margin_rate=-10.5,
            revenue=Decimal("9500.00"),
            cost=Decimal("10500.50")
        )

        assert profit.gross_profit == Decimal("-1000.50")
        assert profit.margin_rate == -10.5


class TestRequestParams:
    """请求参数验证测试"""

    def test_finance_overview_params(self):
        """测试财务概览参数"""
        params = FinanceOverviewParams(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            project_ids=[1, 2, 3],
            team_ids=["team1", "team2"]
        )

        assert params.start_date == date(2026, 1, 1)
        assert len(params.project_ids) == 3

    def test_profit_ranking_params_defaults(self):
        """测试盈亏排行参数默认值"""
        params = ProfitRankingParams()

        assert params.limit == 10
        assert params.order == "desc"

    def test_profit_ranking_params_limit_validation(self):
        """测试 limit 范围验证"""
        # 有效范围 1-50
        params = ProfitRankingParams(limit=50)
        assert params.limit == 50

        # 超出范围应该失败
        with pytest.raises(ValidationError):
            ProfitRankingParams(limit=100)

        with pytest.raises(ValidationError):
            ProfitRankingParams(limit=0)

    def test_transactions_params_page_validation(self):
        """测试分页参数验证"""
        # 有效参数
        params = TransactionsParams(page=1, page_size=50)
        assert params.page == 1
        assert params.page_size == 50

        # page 必须 >= 1
        with pytest.raises(ValidationError):
            TransactionsParams(page=0)

        # page_size 必须 1-100
        with pytest.raises(ValidationError):
            TransactionsParams(page_size=101)

    def test_aging_params_default(self):
        """测试账期参数默认值"""
        params = AgingParams()
        assert params.as_of_date is None


class TestAdditionalSchemas:
    """附加 Schema 测试"""

    def test_project_profit_table_item(self):
        """测试项目盈亏表项"""
        item = ProjectProfitTableItem(
            project_id=1,
            project_name="测试项目",
            revenue=Decimal("10000.00"),
            cost=Decimal("6000.00"),
            gross_profit=Decimal("4000.00"),
            margin_rate=40.0,
            status="profit"
        )

        assert item.status == "profit"

    def test_project_profit_status_enum(self):
        """测试盈亏状态枚举"""
        valid_statuses = ["profit", "loss", "even"]

        for status in valid_statuses:
            item = ProjectProfitTableItem(
                project_id=1,
                project_name="测试",
                status=status
            )
            assert item.status == status

    def test_account_balance_item(self):
        """测试账户余额表项"""
        item = AccountBalanceItem(
            account_id=1,
            account_name="测试账户",
            platform="Facebook",
            balance=Decimal("5000.00"),
            total_topup=Decimal("10000.00"),
            total_spend=Decimal("5000.00"),
            status="normal"
        )

        assert item.platform == "Facebook"
        assert item.status == "normal"

    def test_account_balance_status_enum(self):
        """测试账户状态枚举"""
        valid_statuses = ["normal", "warning", "frozen"]

        for status in valid_statuses:
            item = AccountBalanceItem(
                account_id=1,
                account_name="测试",
                platform="Facebook",
                status=status
            )
            assert item.status == status

    def test_fund_distribution_item(self):
        """测试资金分布项"""
        item = FundDistributionItem(
            name="项目A",
            amount=Decimal("5000.00"),
            percentage=35.5
        )

        assert item.name == "项目A"
        assert item.amount == Decimal("5000.00")
        assert item.percentage == 35.5

    def test_fund_distribution_response(self):
        """测试资金分布响应"""
        response = FundDistributionResponse(
            items=[
                FundDistributionItem(
                    name="项目A",
                    amount=Decimal("5000.00"),
                    percentage=50.0
                ),
                FundDistributionItem(
                    name="项目B",
                    amount=Decimal("5000.00"),
                    percentage=50.0
                ),
            ],
            total=Decimal("10000.00")
        )

        assert len(response.items) == 2
        assert response.total == Decimal("10000.00")
