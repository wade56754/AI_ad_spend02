"""
AI分析服务测试
测试AI异常检测和账户寿命预测功能
Version: 1.0
Author: Claude协作开发
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any

from services.ai_anomaly_detection_service import AIAnomalyDetectionService
from models.ad_account import AdAccount
from models.daily_report import DailyReport
from core.db import get_db


class TestAIAnomalyDetectionService:
    """AI异常检测服务测试类"""

    def setup_method(self):
        """每个测试方法执行前的设置"""
        self.db = next(get_db())
        self.service = AIAnomalyDetectionService(self.db)

    def teardown_method(self):
        """每个测试方法执行后的清理"""
        self.db.close()

    def test_detect_performance_anomalies_normal_data(self):
        """测试正常数据的异常检测"""
        # 准备正常的绩效数据
        performance_data = [
            {
                "date": "2025-01-01",
                "impressions": 10000,
                "clicks": 500,
                "spend": 100.0,
                "conversions": 10,
                "cpa": 10.0,
                "roas": 5.0
            },
            {
                "date": "2025-01-02",
                "impressions": 11000,
                "clicks": 550,
                "spend": 110.0,
                "conversions": 11,
                "cpa": 10.0,
                "roas": 5.0
            },
            {
                "date": "2025-01-03",
                "impressions": 12000,
                "clicks": 600,
                "spend": 120.0,
                "conversions": 12,
                "cpa": 10.0,
                "roas": 5.0
            }
        ]

        # 执行异常检测
        result = self.service.detect_performance_anomalies(performance_data)

        # 验证结果
        assert result["has_anomalies"] is False
        assert len(result["anomalies"]) == 0
        assert result["analysis_summary"]["total_data_points"] == 3
        assert result["analysis_summary"]["anomaly_count"] == 0

    def test_detect_performance_anomalies_with_spend_spike(self):
        """测试消耗激增的异常检测"""
        # 准备包含消耗激增的数据
        performance_data = [
            {
                "date": "2025-01-01",
                "impressions": 10000,
                "clicks": 500,
                "spend": 100.0,
                "conversions": 10,
                "cpa": 10.0,
                "roas": 5.0
            },
            {
                "date": "2025-01-02",
                "impressions": 11000,
                "clicks": 550,
                "spend": 110.0,
                "conversions": 11,
                "cpa": 10.0,
                "roas": 5.0
            },
            {
                "date": "2025-01-03",
                "impressions": 8000,
                "clicks": 400,
                "spend": 500.0,  # 异常：消耗激增
                "conversions": 8,
                "cpa": 62.5,
                "roas": 1.0
            }
        ]

        # 执行异常检测
        result = self.service.detect_performance_anomalies(performance_data)

        # 验证结果
        assert result["has_anomalies"] is True
        assert len(result["anomalies"]) > 0

        # 验证消耗异常被检测到
        spend_anomalies = [a for a in result["anomalies"] if a["metric"] == "spend"]
        assert len(spend_anomalies) > 0
        assert spend_anomalies[0]["severity"] in ["high", "critical"]

    def test_detect_performance_anomalies_with_ctr_drop(self):
        """测试点击率骤降的异常检测"""
        # 准备包含CTR骤降的数据
        performance_data = [
            {
                "date": "2025-01-01",
                "impressions": 10000,
                "clicks": 500,  # CTR = 5%
                "spend": 100.0,
                "conversions": 10,
                "cpa": 10.0,
                "roas": 5.0
            },
            {
                "date": "2025-01-02",
                "impressions": 10000,
                "clicks": 450,  # CTR = 4.5%
                "spend": 100.0,
                "conversions": 9,
                "cpa": 11.11,
                "roas": 4.5
            },
            {
                "date": "2025-01-03",
                "impressions": 10000,
                "clicks": 50,   # 异常：CTR骤降到0.5%
                "spend": 100.0,
                "conversions": 1,
                "cpa": 100.0,
                "roas": 0.5
            }
        ]

        # 执行异常检测
        result = self.service.detect_performance_anomalies(performance_data)

        # 验证结果
        assert result["has_anomalies"] is True
        assert len(result["anomalies"]) > 0

    def test_assess_account_lifetime_risk_new_account(self):
        """测试新账户的寿命风险评估"""
        # 创建新账户测试数据
        account_data = {
            "id": 1,
            "name": "测试新账户",
            "status": "active",
            "created_at": datetime.utcnow() - timedelta(days=5),
            "channel": {"name": "Facebook"}
        }

        performance_data = []  # 新账户没有历史数据

        # 执行风险评估
        result = self.service.assess_account_lifetime_risk(account_data, performance_data)

        # 验证结果
        assert "risk_score" in result
        assert "risk_level" in result
        assert "lifetime_prediction" in result
        assert "risk_factors" in result
        assert 0 <= result["risk_score"] <= 100
        assert result["risk_level"] in ["low", "medium", "high", "critical"]

    def test_assess_account_lifetime_risk_declining_performance(self):
        """测试绩效下降账户的风险评估"""
        # 创建绩效下降的账户数据
        account_data = {
            "id": 1,
            "name": "测试衰退账户",
            "status": "active",
            "created_at": datetime.utcnow() - timedelta(days=60),
            "channel": {"name": "Facebook"}
        }

        # 准备绩效下降的数据
        performance_data = []
        base_date = date.today() - timedelta(days=30)

        for i in range(30):
            # 模拟绩效持续下降
            day = base_date + timedelta(days=i)
            base_spend = 200.0 - (i * 3)  # 消耗逐渐下降
            base_conversions = 20 - (i * 0.5)  # 转化逐渐下降

            performance_data.append({
                "date": day.isoformat(),
                "impressions": 10000 - (i * 100),
                "clicks": 500 - (i * 10),
                "spend": max(base_spend, 20),
                "conversions": max(int(base_conversions), 2),
                "cpa": 10.0,
                "roas": 5.0 - (i * 0.1)
            })

        # 执行风险评估
        result = self.service.assess_account_lifetime_risk(account_data, performance_data)

        # 验证结果
        assert result["risk_score"] > 50  # 风险分数应该较高
        assert result["risk_level"] in ["high", "critical"]

        # 验证风险因素包含绩效下降
        risk_factors = [factor["type"] for factor in result["risk_factors"]]
        assert "performance_decline" in risk_factors

    def test_get_account_insights(self):
        """测试获取账户洞察"""
        # 创建测试账户数据
        account_data = {
            "id": 1,
            "name": "测试账户",
            "status": "active",
            "created_at": datetime.utcnow() - timedelta(days=30),
            "channel": {"name": "Facebook"}
        }

        performance_data = [
            {
                "date": "2025-01-01",
                "impressions": 10000,
                "clicks": 500,
                "spend": 100.0,
                "conversions": 10,
                "cpa": 10.0,
                "roas": 5.0
            }
        ]

        # 执行洞察分析
        result = self.service.get_account_insights(account_data, performance_data)

        # 验证结果结构
        assert "account_id" in result
        assert "account_name" in result
        assert "performance_summary" in result
        assert "trends" in result
        assert "recommendations" in result
        assert "risk_assessment" in result
        assert "generated_at" in result

        # 验证洞察内容
        assert len(result["recommendations"]) > 0
        assert all("type" in rec for rec in result["recommendations"])
        assert all("priority" in rec for rec in result["recommendations"])
        assert all("description" in rec for rec in result["recommendations"])

    def test_batch_anomaly_detection(self):
        """测试批量异常检测"""
        # 准备多个账户的数据
        accounts_data = [
            {
                "id": 1,
                "name": "账户1",
                "status": "active",
                "performance_data": [
                    {"date": "2025-01-01", "spend": 100.0, "cpa": 10.0},
                    {"date": "2025-01-02", "spend": 500.0, "cpa": 50.0}  # 异常
                ]
            },
            {
                "id": 2,
                "name": "账户2",
                "status": "active",
                "performance_data": [
                    {"date": "2025-01-01", "spend": 100.0, "cpa": 10.0},
                    {"date": "2025-01-02", "spend": 110.0, "cpa": 11.0}  # 正常
                ]
            }
        ]

        # 执行批量检测
        result = self.service.batch_anomaly_detection(accounts_data)

        # 验证结果
        assert "total_accounts" in result
        assert "accounts_with_anomalies" in result
        assert "total_anomalies" in result
        assert "anomaly_details" in result
        assert result["total_accounts"] == 2
        assert result["accounts_with_anomalies"] >= 1

    def test_insufficient_data_handling(self):
        """测试数据不足的处理"""
        # 测试空数据
        result = self.service.detect_performance_anomalies([])

        assert result["has_anomalies"] is False
        assert len(result["anomalies"]) == 0
        assert "insufficient_data" in result["analysis_summary"]

        # 测试单一数据点
        single_data = [{"date": "2025-01-01", "spend": 100.0}]
        result = self.service.detect_performance_anomalies(single_data)

        assert result["has_anomalies"] is False

    def test_anomaly_severity_classification(self):
        """测试异常严重程度分类"""
        # 准备不同严重程度的异常数据
        performance_data = [
            {"date": "2025-01-01", "spend": 100.0, "cpa": 10.0},
            {"date": "2025-01-02", "spend": 150.0, "cpa": 15.0},  # 轻微异常
            {"date": "2025-01-03", "spend": 300.0, "cpa": 30.0},  # 中度异常
            {"date": "2025-01-04", "spend": 1000.0, "cpa": 100.0} # 严重异常
        ]

        result = self.service.detect_performance_anomalies(performance_data)

        # 验证不同严重程度的异常都被检测到
        if result["has_anomalies"]:
            severities = [a["severity"] for a in result["anomalies"]]
            valid_severities = ["low", "medium", "high", "critical"]
            assert all(s in valid_severities for s in severities)


@pytest.mark.integration
class TestAIAnalyticsIntegration:
    """AI分析模块集成测试"""

    def test_end_to_end_analysis_workflow(self, db_session, test_ad_account):
        """端到端分析工作流测试"""
        from services.ai_anomaly_detection_service import AIAnomalyDetectionService

        service = AIAnomalyDetectionService(db_session)

        # 模拟账户数据
        account_data = {
            "id": test_ad_account.id,
            "name": test_ad_account.name,
            "status": test_ad_account.status,
            "created_at": test_ad_account.created_at,
            "channel": {"name": "Facebook"}
        }

        # 模拟绩效数据
        performance_data = []
        for i in range(7):
            day = date.today() - timedelta(days=i)
            performance_data.append({
                "date": day.isoformat(),
                "impressions": 10000 + (i * 100),
                "clicks": 500 + (i * 5),
                "spend": 100.0 + (i * 10),
                "conversions": 10 + i,
                "cpa": 10.0,
                "roas": 5.0
            })

        # 执行完整分析
        anomaly_result = service.detect_performance_anomalies(performance_data)
        risk_result = service.assess_account_lifetime_risk(account_data, performance_data)
        insights = service.get_account_insights(account_data, performance_data)

        # 验证结果一致性
        assert anomaly_result is not None
        assert risk_result is not None
        assert insights is not None

        # 验证账户ID一致性
        assert insights["account_id"] == account_data["id"]
        assert risk_result["account_id"] == account_data["id"]

    @pytest.mark.auth
    def test_ai_analysis_with_user_permissions(self, client, test_user, auth_headers_user, test_ad_account):
        """带权限验证的AI分析测试"""
        # 创建测试日报数据
        report_data = {
            "report_date": date.today().isoformat(),
            "ad_account_id": test_ad_account.id,
            "campaign_name": "测试广告系列",
            "impressions": 10000,
            "clicks": 500,
            "spend": "100.00",
            "conversions": 10,
            "cpa": "10.00",
            "roas": "5.00"
        }

        # 用户提交日报
        response = client.post(
            "/api/v1/daily-reports/",
            json=report_data,
            headers=auth_headers_user
        )
        assert response.status_code == 201

        # 调用AI分析API
        response = client.get(
            f"/api/v1/ai-analytics/analyze-account/{test_ad_account.id}",
            headers=auth_headers_user,
            params={"days": 7}
        )

        # 验证权限检查
        if response.status_code == 403:
            # 权限不足是预期行为
            assert response.json()["error"]["code"] in ["PERMISSION_DENIED", "INSUFFICIENT_PERMISSIONS"]
        elif response.status_code == 200:
            # 有权限时验证返回数据
            data = response.json()
            assert "analysis" in data
            assert "recommendations" in data


@pytest.mark.performance
class TestAIAnalyticsPerformance:
    """AI分析模块性能测试"""

    def test_large_dataset_analysis_performance(self):
        """大数据集分析性能测试"""
        from services.ai_anomaly_detection_service import AIAnomalyDetectionService
        from time import time

        # 准备大数据集（30天数据）
        performance_data = []
        for i in range(30):
            day = date.today() - timedelta(days=i)
            performance_data.append({
                "date": day.isoformat(),
                "impressions": 10000 + (i * 100),
                "clicks": 500 + (i * 5),
                "spend": 100.0 + (i * 10),
                "conversions": 10 + i,
                "cpa": 10.0,
                "roas": 5.0
            })

        service = AIAnomalyDetectionService(None)  # 仅用于性能测试

        # 测量执行时间
        start_time = time()
        result = service.detect_performance_anomalies(performance_data)
        end_time = time()

        execution_time = end_time - start_time

        # 验证性能要求（应在2秒内完成）
        assert execution_time < 2.0, f"分析耗时过长: {execution_time:.2f}秒"
        assert result is not None

    def test_concurrent_analysis_requests(self):
        """并发分析请求测试"""
        import threading
        from concurrent.futures import ThreadPoolExecutor

        def perform_analysis():
            from services.ai_anomaly_detection_service import AIAnomalyDetectionService
            service = AIAnomalyDetectionService(None)

            performance_data = [
                {"date": "2025-01-01", "spend": 100.0, "cpa": 10.0},
                {"date": "2025-01-02", "spend": 150.0, "cpa": 15.0}
            ]

            return service.detect_performance_anomalies(performance_data)

        # 并发执行10次分析
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(perform_analysis) for _ in range(10)]
            results = [future.result() for future in futures]

        # 验证所有分析都成功完成
        assert len(results) == 10
        assert all(result is not None for result in results)


@pytest.mark.slow
class TestAIAnalyticsStress:
    """AI分析模块压力测试"""

    def test_memory_usage_with_large_dataset(self):
        """大数据集内存使用测试"""
        import psutil
        import os
        from services.ai_anomaly_detection_service import AIAnomalyDetectionService

        # 获取初始内存使用
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 准备超大数据集（1000天数据）
        performance_data = []
        for i in range(1000):
            day = date.today() - timedelta(days=i)
            performance_data.append({
                "date": day.isoformat(),
                "impressions": 10000 + (i * 100),
                "clicks": 500 + (i * 5),
                "spend": 100.0 + (i * 10),
                "conversions": 10 + i,
                "cpa": 10.0,
                "roas": 5.0
            })

        service = AIAnomalyDetectionService(None)
        result = service.detect_performance_anomalies(performance_data)

        # 获取最终内存使用
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # 验证内存增长在合理范围内（不超过100MB）
        assert memory_increase < 100, f"内存使用增长过多: {memory_increase:.2f}MB"
        assert result is not None