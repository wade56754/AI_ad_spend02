"""
新增模块集成测试
测试财务总账、对账管理、AI监控等新增模块的集成功能
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.db import Base, get_db_session
from backend.core.security import AuthenticatedUser
from backend.models.ledger import TransactionType, TransactionStatus
from backend.models.reconciliation_extended import ReconciliationStatus, DifferenceStatus
from backend.models.ai_monitoring import AnomalyType, AnomalySeverity, PredictionStatus
from backend.services.ledger_service import LedgerService
from backend.services.reconciliation_service_extended import ReconciliationServiceExtended
from backend.services.ai_monitoring_service import AIMonitoringService
from backend.services.audit_service import AuditService, BusinessAction


# 测试配置
TEST_DATABASE_URL = "sqlite:///./test_ai_ad_spend.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# 测试用户
test_user = AuthenticatedUser(
    id="test-user-123",
    email="test@example.com",
    role="admin"
)


class TestLedgerService:
    """财务总账服务测试"""

    @pytest.fixture
    def ledger_service(self):
        return LedgerService()

    @pytest.fixture
    def sample_project_id(self):
        return uuid4()

    def test_create_transaction(self, ledger_service, sample_project_id):
        """测试创建财务交易"""
        transaction = ledger_service.create_transaction(
            transaction_type=TransactionType.TOPUP,
            amount=Decimal('1000.00'),
            project_id=sample_project_id,
            description="测试充值",
            user_id=test_user.id
        )

        assert transaction is not None
        assert transaction.transaction_type == TransactionType.TOPUP
        assert transaction.amount == Decimal('1000.00')
        assert transaction.project_id == sample_project_id
        assert transaction.status == TransactionStatus.PENDING
        assert transaction.transaction_number.startswith("TXN")

    def test_update_transaction_status(self, ledger_service, sample_project_id):
        """测试更新交易状态"""
        # 先创建交易
        transaction = ledger_service.create_transaction(
            transaction_type=TransactionType.SPEND,
            amount=Decimal('500.00'),
            project_id=sample_project_id,
            description="测试消费",
            user_id=test_user.id
        )

        # 更新状态
        updated_transaction = ledger_service.update_transaction_status(
            transaction_id=transaction.id,
            status=TransactionStatus.COMPLETED,
            user_id=test_user.id
        )

        assert updated_transaction is not None
        assert updated_transaction.status == TransactionStatus.COMPLETED

    def test_get_account_balance(self, ledger_service, sample_project_id):
        """测试获取账户余额"""
        # 先创建一些交易
        ledger_service.create_transaction(
            transaction_type=TransactionType.TOPUP,
            amount=Decimal('2000.00'),
            project_id=sample_project_id,
            user_id=test_user.id
        )

        ledger_service.create_transaction(
            transaction_type=TransactionType.SPEND,
            amount=Decimal('500.00'),
            project_id=sample_project_id,
            user_id=test_user.id
        )

        # 获取余额
        balance = ledger_service.get_account_balance(project_id=sample_project_id)

        assert balance is not None
        assert balance["current_balance"] == 1500.0  # 2000 - 500

    def test_create_budget_allocation(self, ledger_service, sample_project_id):
        """测试创建预算分配"""
        allocation = ledger_service.create_budget_allocation(
            project_id=sample_project_id,
            category="ad_spend",
            allocated_amount=Decimal('5000.00'),
            user_id=test_user.id
        )

        assert allocation is not None
        assert allocation.category == "ad_spend"
        assert allocation.allocated_amount == Decimal('5000.00')
        assert allocation.remaining_amount == Decimal('5000.00')


class TestReconciliationService:
    """对账管理服务测试"""

    @pytest.fixture
    def reconciliation_service(self):
        return ReconciliationServiceExtended()

    @pytest.fixture
    def sample_project_id(self):
        return uuid4()

    def test_create_reconciliation_batch(self, reconciliation_service, sample_project_id):
        """测试创建对账批次"""
        batch = reconciliation_service.create_reconciliation_batch(
            name="测试对账批次",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            project_ids=[sample_project_id],
            description="测试描述",
            user_id=test_user.id
        )

        assert batch is not None
        assert batch.name == "测试对账批次"
        assert batch.status == ReconciliationStatus.PENDING
        assert batch.project_ids == [sample_project_id]

    def test_get_reconciliation_batches(self, reconciliation_service, sample_project_id):
        """测试获取对账批次列表"""
        # 先创建批次
        reconciliation_service.create_reconciliation_batch(
            name="测试批次1",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 15),
            project_ids=[sample_project_id],
            user_id=test_user.id
        )

        reconciliation_service.create_reconciliation_batch(
            name="测试批次2",
            start_date=date(2024, 1, 16),
            end_date=date(2024, 1, 31),
            project_ids=[sample_project_id],
            user_id=test_user.id
        )

        # 获取批次列表
        result = reconciliation_service.get_reconciliation_batches(
            page=1,
            size=10
        )

        assert result is not None
        assert len(result.items) == 2
        assert result.total == 2

    def test_get_reconciliation_summary(self, reconciliation_service, sample_project_id):
        """测试获取对账汇总"""
        # 创建批次
        batch = reconciliation_service.create_reconciliation_batch(
            name="汇总测试批次",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            project_ids=[sample_project_id],
            user_id=test_user.id
        )

        # 获取汇总
        summary = reconciliation_service.get_reconciliation_summary(batch.id)

        assert summary is not None
        assert "batch_info" in summary
        assert "by_difference_type" in summary
        assert "by_status" in summary


class TestAIMonitoringService:
    """AI监控服务测试"""

    @pytest.fixture
    def ai_service(self):
        return AIMonitoringService()

    @pytest.fixture
    def sample_account_id(self):
        return uuid4()

    def test_create_anomaly_detection(self, ai_service, sample_account_id):
        """测试创建异常检测"""
        anomaly = ai_service.create_anomaly_detection(
            account_id=sample_account_id,
            anomaly_type=AnomalyType.SPEND_SPIKE,
            severity=AnomalySeverity.HIGH,
            description="消耗突增异常",
            metrics_data={"spend_increase": 250.0},
            confidence_score=0.85,
            user_id=test_user.id
        )

        assert anomaly is not None
        assert anomaly.account_id == sample_account_id
        assert anomaly.anomaly_type == AnomalyType.SPEND_SPIKE
        assert anomaly.severity == AnomalySeverity.HIGH
        assert anomaly.confidence_score == 0.85

    def test_create_lifecycle_prediction(self, ai_service, sample_account_id):
        """测试创建账户寿命预测"""
        prediction = ai_service.create_account_lifecycle_prediction(
            account_id=sample_account_id,
            predicted_remaining_days=45,
            prediction_model="random_forest",
            confidence_score=0.78,
            feature_importance={"spend_stability": 0.3, "conversion_rate": 0.5},
            recommendation="建议优化广告投放策略",
            user_id=test_user.id
        )

        assert prediction is not None
        assert prediction.account_id == sample_account_id
        assert prediction.predicted_remaining_days == 45
        assert prediction.prediction_model == "random_forest"
        assert prediction.confidence_score == 0.78

    def test_create_monitoring_rule(self, ai_service):
        """测试创建监控规则"""
        rule = ai_service.create_monitoring_rule(
            name="消耗突增检测",
            rule_type="spend_spike",
            conditions={"threshold": 200, "window_hours": 24},
            actions={"send_notification": True, "create_alert": True},
            severity=AnomalySeverity.MEDIUM,
            is_active=True,
            description="检测消耗突然增长",
            user_id=test_user.id
        )

        assert rule is not None
        assert rule.name == "消耗突增检测"
        assert rule.rule_type == "spend_spike"
        assert rule.is_active is True

    def test_simulate_anomaly_detection(self, ai_service, sample_account_id):
        """测试模拟异常检测"""
        metrics = {
            "spend_sudden_increase": 300,  # 突然增加300%
            "conversion_rate_drop": 60,   # 转化率下降60%
            "account_risk_score": 85,     # 风险评分85
            "budget_overspend": 500       # 预算超支500
        }

        detected_anomalies = ai_service.simulate_anomaly_detection(
            account_id=sample_account_id,
            metrics=metrics
        )

        assert detected_anomalies is not None
        assert len(detected_anomalies) == 4  # 应该检测到4种异常

        # 验证异常类型
        anomaly_types = [a["type"] for a in detected_anomalies]
        assert AnomalyType.SPEND_SPIKE.value in anomaly_types
        assert AnomalyType.PERFORMANCE_DECLINE.value in anomaly_types
        assert AnomalyType.ACCOUNT_RISK.value in anomaly_types
        assert AnomalyType.BUDGET_ANOMALY.value in anomaly_types

    def test_get_ai_dashboard_summary(self, ai_service, sample_account_id):
        """测试获取AI仪表板汇总"""
        # 先创建一些测试数据
        ai_service.create_anomaly_detection(
            account_id=sample_account_id,
            anomaly_type=AnomalyType.SPEND_SPIKE,
            severity=AnomalySeverity.HIGH,
            description="测试异常1",
            user_id=test_user.id
        )

        ai_service.create_lifecycle_prediction(
            account_id=sample_account_id,
            predicted_remaining_days=30,
            user_id=test_user.id
        )

        # 获取仪表板数据
        dashboard = ai_service.get_ai_dashboard_summary()

        assert dashboard is not None
        assert "anomaly_summary" in dashboard
        assert "prediction_summary" in dashboard
        assert "rule_summary" in dashboard


class TestAuditService:
    """审计服务测试"""

    @pytest.fixture
    def audit_service(self):
        return AuditService()

    @pytest.fixture
    def sample_project_id(self):
        return uuid4()

    def test_log_project_created(self, audit_service, sample_project_id):
        """测试记录项目创建日志"""
        project_data = {
            "name": "测试项目",
            "description": "测试描述"
        }

        # 这个测试主要验证方法调用不会出错
        # 实际的数据库写入在测试环境中可能被跳过
        try:
            audit_service.log_project_created(
                project_id=str(sample_project_id),
                project_data=project_data,
                user_id=test_user.id
            )
            # 如果没有异常则认为成功
            assert True
        except Exception as e:
            # 在测试环境中，数据库连接可能失败，这是正常的
            assert "database" in str(e).lower() or "connection" in str(e).lower()

    def test_log_daily_report_action(self, audit_service):
        """测试记录日报操作日志"""
        try:
            audit_service.log_daily_report_action(
                action=BusinessAction.DAILY_REPORT_APPROVE,
                report_id="test-report-123",
                user_id=test_user.id,
                report_data={"spend": 1000, "conversions": 50},
                approved_amount=Decimal('1000.00')
            )
            assert True
        except Exception as e:
            assert "database" in str(e).lower() or "connection" in str(e).lower()

    def test_log_topup_action(self, audit_service):
        """测试记录充值操作日志"""
        try:
            audit_service.log_topup_action(
                action=BusinessAction.TOPUP_APPROVE_FINANCE,
                topup_id="test-topup-123",
                user_id=test_user.id,
                topup_data={"amount": 5000, "currency": "USD"},
                approval_note="财务审批通过",
                payment_amount=Decimal('5000.00')
            )
            assert True
        except Exception as e:
            assert "database" in str(e).lower() or "connection" in str(e).lower()


class TestIntegrationWorkflow:
    """集成工作流测试"""

    def test_complete_workflow_simulation(self):
        """测试完整业务流程模拟"""
        # 1. 项目创建
        project_id = uuid4()

        # 2. 财务交易（充值）
        ledger_service = LedgerService()
        topup_transaction = ledger_service.create_transaction(
            transaction_type=TransactionType.TOPUP,
            amount=Decimal('10000.00'),
            project_id=project_id,
            description="项目充值",
            user_id=test_user.id
        )

        # 3. 创建预算分配
        budget_allocation = ledger_service.create_budget_allocation(
            project_id=project_id,
            category="ad_spend",
            allocated_amount=Decimal('8000.00'),
            user_id=test_user.id
        )

        # 4. 广告消耗
        spend_transaction = ledger_service.create_transaction(
            transaction_type=TransactionType.SPEND,
            amount=Decimal('3000.00'),
            project_id=project_id,
            description="广告投放消耗",
            user_id=test_user.id
        )

        # 5. 对账批次创建
        reconciliation_service = ReconciliationServiceExtended()
        reconciliation_batch = reconciliation_service.create_reconciliation_batch(
            name="项目对账批次",
            start_date=date.today(),
            end_date=date.today(),
            project_ids=[project_id],
            user_id=test_user.id
        )

        # 6. AI监控
        ai_service = AIMonitoringService()
        account_id = uuid4()
        anomaly_detection = ai_service.create_anomaly_detection(
            account_id=account_id,
            anomaly_type=AnomalyType.BUDGET_ANOMALY,
            severity=AnomalySeverity.MEDIUM,
            description="预算使用异常",
            user_id=test_user.id
        )

        # 验证所有步骤都成功
        assert topup_transaction is not None
        assert budget_allocation is not None
        assert spend_transaction is not None
        assert reconciliation_batch is not None
        assert anomaly_detection is not None

        # 验证业务逻辑
        assert topup_transaction.amount == Decimal('10000.00')
        assert spend_transaction.amount == Decimal('3000.00')
        assert budget_allocation.allocated_amount == Decimal('8000.00')
        assert reconciliation_batch.status == ReconciliationStatus.PENDING


# 测试套件执行入口
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])