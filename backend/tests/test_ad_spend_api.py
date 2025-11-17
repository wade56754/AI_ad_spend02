"""
广告消耗API测试
"""

import pytest
import json
from decimal import Decimal
from datetime import date, datetime
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models import AdAccount, AdSpendDaily, User
from routers.ad_spend import AdSpendReportPayload
from core.security import get_password_hash
from core.db import Base


class TestAdSpendAPI:
    """广告消耗API测试类"""

    @pytest.fixture(autouse=True)
    def setup_db(self, db_session: Session):
        """设置测试数据库"""
        Base.metadata.create_all(bind=db_session.bind)

        # 创建测试用户
        test_user = User(
            email="test@example.com",
            name="测试用户",
            password_hash=get_password_hash("testpassword"),
            role="media_buyer",
            is_active=True
        )
        db_session.add(test_user)

        # 创建测试广告账户
        test_account = AdAccount(
            account_name="测试账户1",
            platform="facebook",
            account_id="act_123456",
            status="active",
            project_id=1,
            channel_id=1
        )
        db_session.add(test_account)
        db_session.commit()

        yield

        # 清理
        Base.metadata.drop_all(bind=db_session.bind)

    def test_list_ad_spend_reports_empty(self, client: TestClient, auth_headers):
        """测试获取空的广告消耗报告列表"""
        response = client.get("/api/v1/adspend/reports", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []
        assert "pagination" in data["meta"]

    def test_list_ad_spend_reports_with_filters(self, client: TestClient, auth_headers):
        """测试带过滤条件的广告消耗报告列表"""
        response = client.get(
            "/api/v1/adspend/reports?ad_account_id=123&page=1&size=10",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert "pagination" in data["meta"]
        assert data["meta"]["pagination"]["page"] == 1
        assert data["meta"]["pagination"]["size"] == 10

    def test_get_ad_spend_report_not_found(self, client: TestClient, auth_headers):
        """测试获取不存在的广告消耗报告"""
        fake_id = uuid4()
        response = client.get(f"/api/v1/adspend/reports/{fake_id}", headers=auth_headers)

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "日报记录不存在" in data["detail"]["message"]

    def test_create_ad_spend_report_success(self, client: TestClient, auth_headers, db_session: Session):
        """测试成功创建广告消耗报告"""
        # 获取测试账户
        account = db_session.query(AdAccount).first()

        payload = {
            "ad_account_id": str(account.id),
            "date": date.today().isoformat(),
            "spend": 100.50,
            "leads": 25,
            "follows": 30,
            "conversions": 5,
            "impressions": 1000,
            "clicks": 50
        }

        response = client.post(
            "/api/v1/adspend/report",
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True

        # 验证返回的数据
        report_data = data["data"]
        assert report_data["ad_account_id"] == payload["ad_account_id"]
        assert report_data["spend"] == payload["spend"]
        assert report_data["leads"] == payload["leads"]
        assert report_data["follows"] == payload["follows"]
        assert report_data["conversions"] == payload["conversions"]

    def test_create_ad_spend_report_invalid_account(self, client: TestClient, auth_headers):
        """测试创建报告时使用无效的广告账户ID"""
        fake_id = uuid4()
        payload = {
            "ad_account_id": str(fake_id),
            "date": date.today().isoformat(),
            "spend": 100.50,
            "leads": 25,
            "follows": 30,
            "conversions": 5
        }

        response = client.post(
            "/api/v1/adspend/report",
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "广告账户不存在" in data["detail"]["message"]

    def test_create_ad_spend_report_duplicate_date(self, client: TestClient, auth_headers, db_session: Session):
        """测试创建重复日期的报告"""
        account = db_session.query(AdAccount).first()
        report_date = date.today()

        # 创建第一个报告
        payload = {
            "ad_account_id": str(account.id),
            "date": report_date.isoformat(),
            "spend": 100.50,
            "leads": 25,
            "follows": 30,
            "conversions": 5
        }

        response1 = client.post(
            "/api/v1/adspend/report",
            json=payload,
            headers=auth_headers
        )
        assert response1.status_code == 201

        # 创建第二个相同日期的报告
        response2 = client.post(
            "/api/v1/adspend/report",
            json=payload,
            headers=auth_headers
        )

        assert response2.status_code == 409
        data = response2.json()
        assert data["success"] is False
        assert "同一广告账户该日期的日报已存在" in data["detail"]["message"]

    def test_create_ad_spend_report_invalid_payload(self, client: TestClient, auth_headers):
        """测试创建报告时使用无效载荷"""
        payload = {
            "ad_account_id": "invalid-uuid",
            "date": "invalid-date",
            "spend": -100,  # 负数
            "leads": -1,     # 负数
            "follows": -1,   # 负数
            "conversions": -1  # 负数
        }

        response = client.post(
            "/api/v1/adspend/report",
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == 422  # Validation error

    def test_create_ad_spend_report_missing_fields(self, client: TestClient, auth_headers):
        """测试创建报告时缺少必需字段"""
        payload = {
            "ad_account_id": str(uuid4()),
            "date": date.today().isoformat()
            # 缺少 spend, leads 等必需字段
        }

        response = client.post(
            "/api/v1/adspend/report",
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == 422  # Validation error

    def test_create_ad_spend_report_exceeds_limits(self, client: TestClient, auth_headers):
        """测试创建报告时超出限制"""
        payload = {
            "ad_account_id": str(uuid4()),
            "date": date.today().isoformat(),
            "spend": "20000000.00",  # 超过MAX_SPEND
            "leads": 2000000,          # 超过MAX_LEADS
            "follows": 30,
            "conversions": 5
        }

        response = client.post(
            "/api/v1/adspend/report",
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == 422  # Validation error

    def test_unauthorized_access(self, client: TestClient):
        """测试未授权访问"""
        response = client.get("/api/v1/adspend/reports")
        assert response.status_code == 401

    def test_invalid_auth_token(self, client: TestClient):
        """测试无效的认证令牌"""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/v1/adspend/reports", headers=headers)
        assert response.status_code == 401

    def test_pagination_parameters(self, client: TestClient, auth_headers):
        """测试分页参数"""
        # 测试有效的分页参数
        response = client.get(
            "/api/v1/adspend/reports?page=2&size=50",
            headers=auth_headers
        )
        assert response.status_code == 200

        # 测试无效的分页参数
        response = client.get(
            "/api/v1/adspend/reports?page=0&size=200",
            headers=auth_headers
        )
        # 应该通过验证，因为会使用默认值
        assert response.status_code == 200

    def test_date_filtering(self, client: TestClient, auth_headers):
        """测试日期过滤"""
        today = date.today()
        yesterday = date.fromordinal(today.toordinal() - 1)

        # 测试日期范围过滤
        response = client.get(
            f"/api/v1/adspend/reports?date_from={yesterday}&date_to={today}",
            headers=auth_headers
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_large_dataset_handling(self, client: TestClient, auth_headers, db_session: Session):
        """测试大数据集处理"""
        account = db_session.query(AdAccount).first()

        # 创建多条测试数据
        reports = []
        base_date = date.fromordinal(date.today().toordinal() - 10)

        for i in range(100):  # 创建100条记录
            report = AdSpendDaily(
                ad_account_id=account.id,
                date=date.fromordinal(base_date.toordinal() + i),
                spend=Decimal(f"{100 + i}.50"),
                leads=25 + i,
                follows=30 + i,
                conversions=5 + i,
                impressions=1000 + i * 10,
                clicks=50 + i * 5
            )
            reports.append(report)

        db_session.add_all(reports)
        db_session.commit()

        # 测试分页查询
        response = client.get(
            "/api/v1/adspend/reports?page=1&size=20",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 20
        assert data["meta"]["pagination"]["total"] == 100
        assert data["meta"]["pagination"]["total_pages"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])