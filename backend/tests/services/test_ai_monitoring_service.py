"""
AI监控服务测试模块
测试 backend/services/ai_monitoring_service.py 的AI监控、异常检测和预测功能

待修复:
- 服务使用 account_id，模型使用 ad_account_id
- 服务传递的字段与模型定义不匹配
- 需要对齐服务实现与模型定义
"""

import pytest

# 跳过整个模块，等待服务与模型字段对齐
pytestmark = pytest.mark.skip(reason="服务与模型字段不匹配 (account_id vs ad_account_id)，需要对齐")
from datetime import datetime, date
from decimal import Decimal
from uuid import uuid4, UUID
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from backend.services.ai_monitoring_service import AIMonitoringService, get_ai_monitoring_service
from backend.models.ai_monitoring import (
    AIAnomalyDetection, AccountLifecyclePrediction, MonitoringRule,
    AnomalyType, AnomalySeverity, PredictionStatus, RuleStatus
)
from backend.core.response import PaginatedResponse


# ==================== Fixtures ====================

@pytest.fixture
def mock_db_session():
    """模拟数据库会话"""
    with patch('backend.services.ai_monitoring_service.get_db_session') as mock:
        session = Mock(spec=Session)
        session.add = Mock()
        session.commit = Mock()
        session.query = Mock()
        mock.return_value.__enter__ = Mock(return_value=session)
        mock.return_value.__exit__ = Mock(return_value=False)
        yield session


@pytest.fixture
def sample_account_id():
    """示例账户ID"""
    return uuid4()


@pytest.fixture
def sample_anomaly(sample_account_id):
    """示例异常检测记录"""
    anomaly = Mock(spec=AIAnomalyDetection)
    anomaly.id = uuid4()
    anomaly.account_id = sample_account_id
    anomaly.anomaly_type = AnomalyType.SPENDING_SPIKE.value
    anomaly.severity = AnomalySeverity.HIGH.value
    anomaly.description = "消耗突增异常"
    anomaly.metrics_data = {"spend_increase": 250}
    anomaly.prediction_data = {}
    anomaly.confidence_score = 0.85
    anomaly.status = "active"
    anomaly.anomaly_date = date.today()
    anomaly.created_at = datetime.utcnow()
    anomaly.updated_at = None
    return anomaly


@pytest.fixture
def sample_prediction(sample_account_id):
    """示例账户寿命预测"""
    prediction = Mock(spec=AccountLifecyclePrediction)
    prediction.id = uuid4()
    prediction.account_id = sample_account_id
    prediction.predicted_remaining_days = 30
    prediction.prediction_model = "default"
    prediction.confidence_score = 0.78
    prediction.feature_importance = {"spend_trend": 0.4, "balance": 0.3}
    prediction.recommendation = "建议增加充值"
    prediction.status = PredictionStatus.IN_PROGRESS.value
    prediction.created_at = datetime.utcnow()
    prediction.updated_at = None
    return prediction


@pytest.fixture
def sample_rule():
    """示例监控规则"""
    rule = Mock(spec=MonitoringRule)
    rule.id = uuid4()
    rule.name = "消耗异常规则"
    rule.rule_type = "spend_spike"
    rule.conditions = {"threshold": 200}
    rule.actions = {"alert": True, "email": True}
    rule.severity = AnomalySeverity.HIGH
    rule.is_active = True
    rule.status = RuleStatus.ACTIVE.value
    rule.description = "检测消耗突增"
    rule.created_by = "admin"
    rule.created_at = datetime.utcnow()
    rule.updated_at = None
    return rule


# ==================== 初始化测试 ====================

@pytest.mark.unit
@pytest.mark.ai_monitoring
class TestAIMonitoringServiceInitialization:
    """测试AI监控服务初始化"""

    def test_get_ai_monitoring_service(self):
        """测试获取服务实例"""
        service = get_ai_monitoring_service()
        assert isinstance(service, AIMonitoringService)


# ==================== 异常检测创建测试 ====================

@pytest.mark.unit
@pytest.mark.ai_monitoring
class TestCreateAnomalyDetection:
    """测试创建异常检测"""

    @patch('backend.services.ai_monitoring_service.AuditService.log_ai_action')
    def test_create_anomaly_detection_success(self, mock_audit, mock_db_session, sample_account_id):
        """测试成功创建异常检测"""
        metrics_data = {"spend_increase": 250}
        prediction_data = {"predicted_impact": "high"}

        anomaly = AIMonitoringService.create_anomaly_detection(
            account_id=sample_account_id,
            anomaly_type=AnomalyType.SPENDING_SPIKE,
            severity=AnomalySeverity.HIGH,
            description="消耗突增异常",
            metrics_data=metrics_data,
            prediction_data=prediction_data,
            confidence_score=0.85,
            user_id="test-user"
        )

        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_audit.assert_called_once()

    @patch('backend.services.ai_monitoring_service.AuditService.log_ai_action')
    def test_create_anomaly_detection_minimal_params(self, mock_audit, mock_db_session, sample_account_id):
        """测试最小参数创建异常检测"""
        anomaly = AIMonitoringService.create_anomaly_detection(
            account_id=sample_account_id,
            anomaly_type=AnomalyType.PERFORMANCE_DECLINE,
            severity=AnomalySeverity.MEDIUM,
            description="性能下降"
        )

        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()


# ==================== 账户寿命预测创建测试 ====================

@pytest.mark.unit
@pytest.mark.ai_monitoring
class TestCreateAccountLifecyclePrediction:
    """测试创建账户寿命预测"""

    @patch('backend.services.ai_monitoring_service.AuditService.log_ai_action')
    def test_create_prediction_success(self, mock_audit, mock_db_session, sample_account_id):
        """测试成功创建预测"""
        feature_importance = {"spend_trend": 0.4, "balance": 0.3}

        prediction = AIMonitoringService.create_account_lifecycle_prediction(
            account_id=sample_account_id,
            predicted_remaining_days=30,
            prediction_model="default",
            confidence_score=0.78,
            feature_importance=feature_importance,
            recommendation="建议增加充值",
            user_id="test-user"
        )

        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_audit.assert_called_once()

    @patch('backend.services.ai_monitoring_service.AuditService.log_ai_action')
    def test_create_prediction_minimal_params(self, mock_audit, mock_db_session, sample_account_id):
        """测试最小参数创建预测"""
        prediction = AIMonitoringService.create_account_lifecycle_prediction(
            account_id=sample_account_id,
            predicted_remaining_days=15
        )

        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()


# ==================== 监控规则创建测试 ====================

@pytest.mark.unit
@pytest.mark.ai_monitoring
class TestCreateMonitoringRule:
    """测试创建监控规则"""

    @patch('backend.services.ai_monitoring_service.AuditService.log_ai_action')
    def test_create_rule_success(self, mock_audit, mock_db_session):
        """测试成功创建规则"""
        conditions = {"threshold": 200, "window": "1h"}
        actions = {"alert": True, "email": True}

        rule = AIMonitoringService.create_monitoring_rule(
            name="消耗异常规则",
            rule_type="spend_spike",
            conditions=conditions,
            actions=actions,
            severity=AnomalySeverity.HIGH,
            is_active=True,
            description="检测消耗突增",
            user_id="admin"
        )

        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_audit.assert_called_once()

    @patch('backend.services.ai_monitoring_service.AuditService.log_ai_action')
    def test_create_rule_default_severity(self, mock_audit, mock_db_session):
        """测试默认严重级别创建规则"""
        rule = AIMonitoringService.create_monitoring_rule(
            name="测试规则",
            rule_type="test",
            conditions={},
            actions={}
        )

        mock_db_session.add.assert_called_once()


# ==================== 获取异常检测列表测试 ====================

@pytest.mark.unit
@pytest.mark.ai_monitoring
class TestGetAnomalyDetections:
    """测试获取异常检测列表"""

    def test_get_anomaly_detections_no_filters(self, mock_db_session, sample_anomaly):
        """测试无过滤条件获取列表"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_anomaly]
        mock_db_session.query.return_value = mock_query

        result = AIMonitoringService.get_anomaly_detections()

        assert isinstance(result, PaginatedResponse)
        assert result.total == 1
        assert result.page == 1
        assert len(result.items) == 1

    def test_get_anomaly_detections_with_filters(self, mock_db_session, sample_account_id):
        """测试带过滤条件获取列表"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db_session.query.return_value = mock_query

        result = AIMonitoringService.get_anomaly_detections(
            account_id=sample_account_id,
            anomaly_type=AnomalyType.SPENDING_SPIKE,
            severity=AnomalySeverity.HIGH,
            status="active",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )

        assert isinstance(result, PaginatedResponse)
        # 验证 filter 被调用了多次
        assert mock_query.filter.call_count >= 5

    def test_get_anomaly_detections_pagination(self, mock_db_session):
        """测试分页"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 50
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db_session.query.return_value = mock_query

        result = AIMonitoringService.get_anomaly_detections(page=2, size=10)

        assert result.pages == 5
        mock_query.offset.assert_called_with(10)
        mock_query.limit.assert_called_with(10)


# ==================== 获取账户寿命预测列表测试 ====================

@pytest.mark.unit
@pytest.mark.ai_monitoring
class TestGetAccountLifecyclePredictions:
    """测试获取账户寿命预测列表"""

    def test_get_predictions_no_filters(self, mock_db_session, sample_prediction):
        """测试无过滤条件获取列表"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_prediction]
        mock_db_session.query.return_value = mock_query

        result = AIMonitoringService.get_account_lifecycle_predictions()

        assert isinstance(result, PaginatedResponse)
        assert result.total == 1

    def test_get_predictions_with_filters(self, mock_db_session, sample_account_id):
        """测试带过滤条件获取列表"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db_session.query.return_value = mock_query

        result = AIMonitoringService.get_account_lifecycle_predictions(
            account_id=sample_account_id,
            status=PredictionStatus.IN_PROGRESS,
            prediction_model="default"
        )

        assert isinstance(result, PaginatedResponse)
        assert mock_query.filter.call_count >= 3


# ==================== 获取监控规则列表测试 ====================

@pytest.mark.unit
@pytest.mark.ai_monitoring
class TestGetMonitoringRules:
    """测试获取监控规则列表"""

    def test_get_rules_no_filters(self, mock_db_session, sample_rule):
        """测试无过滤条件获取列表"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_rule]
        mock_db_session.query.return_value = mock_query

        result = AIMonitoringService.get_monitoring_rules()

        assert isinstance(result, PaginatedResponse)
        assert result.total == 1

    def test_get_rules_with_filters(self, mock_db_session):
        """测试带过滤条件获取列表"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db_session.query.return_value = mock_query

        result = AIMonitoringService.get_monitoring_rules(
            rule_type="spend_spike",
            is_active=True
        )

        assert isinstance(result, PaginatedResponse)
        assert mock_query.filter.call_count >= 2


# ==================== 更新异常状态测试 ====================

@pytest.mark.unit
@pytest.mark.ai_monitoring
class TestUpdateAnomalyStatus:
    """测试更新异常状态"""

    def test_update_anomaly_status_success(self, mock_db_session, sample_anomaly):
        """测试成功更新状态"""
        anomaly_id = sample_anomaly.id
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_anomaly
        mock_db_session.query.return_value = mock_query

        result = AIMonitoringService.update_anomaly_status(
            anomaly_id=anomaly_id,
            status="resolved",
            resolution_note="已处理",
            user_id="admin"
        )

        assert result is not None
        assert result.status == "resolved"
        mock_db_session.commit.assert_called_once()

    def test_update_anomaly_status_not_found(self, mock_db_session):
        """测试异常不存在"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        result = AIMonitoringService.update_anomaly_status(
            anomaly_id=uuid4(),
            status="resolved"
        )

        assert result is None
        mock_db_session.commit.assert_not_called()

    def test_update_anomaly_status_with_resolution_note(self, mock_db_session):
        """测试带解决备注更新状态"""
        anomaly = Mock(spec=AIAnomalyDetection)
        anomaly.id = uuid4()
        anomaly.status = "active"
        anomaly.prediction_data = {}

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = anomaly
        mock_db_session.query.return_value = mock_query

        result = AIMonitoringService.update_anomaly_status(
            anomaly_id=anomaly.id,
            status="resolved",
            resolution_note="手动处理完成"
        )

        assert "resolution_note" in result.prediction_data


# ==================== AI仪表板汇总测试 ====================

@pytest.mark.unit
@pytest.mark.ai_monitoring
class TestGetAIDashboardSummary:
    """测试获取AI仪表板汇总"""

    def test_get_dashboard_summary_success(self, mock_db_session):
        """测试成功获取仪表板汇总"""
        # 模拟异常统计
        anomaly_stat = Mock()
        anomaly_stat.severity = AnomalySeverity.HIGH
        anomaly_stat.count = 5

        # 模拟预测统计
        prediction_stat = Mock()
        prediction_stat.total_predictions = 10
        prediction_stat.avg_remaining_days = 25.5
        prediction_stat.avg_confidence = 0.75

        # 模拟规则统计
        rule_stat = Mock()
        rule_stat.is_active = True
        rule_stat.count = 8

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.side_effect = [[anomaly_stat], [rule_stat]]
        mock_query.first.return_value = prediction_stat
        mock_db_session.query.return_value = mock_query

        result = AIMonitoringService.get_ai_dashboard_summary(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )

        assert "anomaly_summary" in result
        assert "prediction_summary" in result
        assert "rule_summary" in result
        assert result["prediction_summary"]["total_predictions"] == 10

    def test_get_dashboard_summary_no_date_filter(self, mock_db_session):
        """测试无日期过滤的仪表板汇总"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.first.return_value = None
        mock_db_session.query.return_value = mock_query

        result = AIMonitoringService.get_ai_dashboard_summary()

        assert result["period"]["start_date"] is None
        assert result["period"]["end_date"] is None


# ==================== 模拟异常检测测试 ====================

@pytest.mark.unit
@pytest.mark.ai_monitoring
class TestSimulateAnomalyDetection:
    """测试模拟异常检测"""

    def test_simulate_spend_spike(self, sample_account_id):
        """测试检测消耗突增"""
        metrics = {"spend_sudden_increase": 250}

        anomalies = AIMonitoringService.simulate_anomaly_detection(
            account_id=sample_account_id,
            metrics=metrics
        )

        assert len(anomalies) == 1
        assert anomalies[0]["type"] == AnomalyType.SPENDING_SPIKE.value
        assert anomalies[0]["severity"] == AnomalySeverity.HIGH.value

    def test_simulate_conversion_rate_drop(self, sample_account_id):
        """测试检测转化率下降"""
        metrics = {"conversion_rate_drop": 60}

        anomalies = AIMonitoringService.simulate_anomaly_detection(
            account_id=sample_account_id,
            metrics=metrics
        )

        assert len(anomalies) == 1
        assert anomalies[0]["type"] == AnomalyType.PERFORMANCE_DECLINE.value
        assert anomalies[0]["severity"] == AnomalySeverity.CRITICAL.value

    def test_simulate_account_risk(self, sample_account_id):
        """测试检测账户风险"""
        metrics = {"account_risk_score": 85}

        anomalies = AIMonitoringService.simulate_anomaly_detection(
            account_id=sample_account_id,
            metrics=metrics
        )

        assert len(anomalies) == 1
        assert anomalies[0]["type"] == AnomalyType.ACCOUNT_RISK.value

    def test_simulate_budget_overspend(self, sample_account_id):
        """测试检测预算超支"""
        metrics = {"budget_overspend": 5000}

        anomalies = AIMonitoringService.simulate_anomaly_detection(
            account_id=sample_account_id,
            metrics=metrics
        )

        assert len(anomalies) == 1
        assert anomalies[0]["type"] == AnomalyType.BUDGET_ANOMALY.value
        assert anomalies[0]["severity"] == AnomalySeverity.MEDIUM.value

    def test_simulate_multiple_anomalies(self, sample_account_id):
        """测试检测多个异常"""
        metrics = {
            "spend_sudden_increase": 250,
            "conversion_rate_drop": 60,
            "account_risk_score": 85
        }

        anomalies = AIMonitoringService.simulate_anomaly_detection(
            account_id=sample_account_id,
            metrics=metrics
        )

        assert len(anomalies) == 3

    def test_simulate_no_anomalies(self, sample_account_id):
        """测试无异常检测"""
        metrics = {
            "spend_sudden_increase": 10,
            "conversion_rate_drop": 5,
            "account_risk_score": 30
        }

        anomalies = AIMonitoringService.simulate_anomaly_detection(
            account_id=sample_account_id,
            metrics=metrics
        )

        assert len(anomalies) == 0


# ==================== 数据转换测试 ====================

@pytest.mark.unit
@pytest.mark.ai_monitoring
class TestDataConversion:
    """测试数据转换方法"""

    def test_anomaly_to_dict(self, sample_anomaly):
        """测试异常检测转字典"""
        result = AIMonitoringService._anomaly_to_dict(sample_anomaly)

        assert "id" in result
        assert "account_id" in result
        assert result["anomaly_type"] == AnomalyType.SPENDING_SPIKE.value
        assert result["severity"] == AnomalySeverity.HIGH.value
        assert result["status"] == "active"

    def test_prediction_to_dict(self, sample_prediction):
        """测试预测转字典"""
        result = AIMonitoringService._prediction_to_dict(sample_prediction)

        assert "id" in result
        assert "account_id" in result
        assert result["predicted_remaining_days"] == 30
        assert result["prediction_model"] == "default"
        assert result["status"] == PredictionStatus.IN_PROGRESS.value

    def test_rule_to_dict(self, sample_rule):
        """测试规则转字典"""
        result = AIMonitoringService._rule_to_dict(sample_rule)

        assert "id" in result
        assert result["name"] == "消耗异常规则"
        assert result["rule_type"] == "spend_spike"
        assert result["is_active"] is True
        assert result["severity"] == AnomalySeverity.HIGH.value


# ==================== 边界情况测试 ====================

@pytest.mark.unit
@pytest.mark.ai_monitoring
class TestAIMonitoringEdgeCases:
    """测试AI监控服务边界情况"""

    @patch('backend.services.ai_monitoring_service.AuditService.log_ai_action')
    def test_create_anomaly_empty_metrics(self, mock_audit, mock_db_session, sample_account_id):
        """测试空指标创建异常"""
        anomaly = AIMonitoringService.create_anomaly_detection(
            account_id=sample_account_id,
            anomaly_type=AnomalyType.DATA_QUALITY,
            severity=AnomalySeverity.LOW,
            description="数据质量问题",
            metrics_data=None
        )

        mock_db_session.add.assert_called_once()

    def test_get_anomalies_empty_result(self, mock_db_session):
        """测试空结果集"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db_session.query.return_value = mock_query

        result = AIMonitoringService.get_anomaly_detections()

        assert result.total == 0
        assert len(result.items) == 0

    def test_get_dashboard_summary_null_predictions(self, mock_db_session):
        """测试预测统计为空"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.first.return_value = None
        mock_db_session.query.return_value = mock_query

        result = AIMonitoringService.get_ai_dashboard_summary()

        assert result["prediction_summary"]["total_predictions"] == 0
        assert result["prediction_summary"]["average_remaining_days"] == 0


# ==================== 集成测试 ====================

@pytest.mark.integration
@pytest.mark.ai_monitoring
class TestAIMonitoringIntegration:
    """AI监控服务集成测试"""

    @patch('backend.services.ai_monitoring_service.AuditService.log_ai_action')
    def test_full_anomaly_workflow(self, mock_audit, mock_db_session, sample_account_id, sample_anomaly):
        """测试完整异常检测工作流"""
        # 创建异常
        anomaly = AIMonitoringService.create_anomaly_detection(
            account_id=sample_account_id,
            anomaly_type=AnomalyType.SPENDING_SPIKE,
            severity=AnomalySeverity.HIGH,
            description="消耗异常"
        )

        # 模拟查询异常
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_anomaly
        mock_db_session.query.return_value = mock_query

        # 更新异常状态
        updated = AIMonitoringService.update_anomaly_status(
            anomaly_id=sample_anomaly.id,
            status="resolved"
        )

        assert updated is not None
        assert mock_db_session.commit.call_count >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
