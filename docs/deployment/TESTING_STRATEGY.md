# 测试策略文档

> **文档目的**: 为AI广告代投系统提供全面的测试策略和质量保证指南
> **目标读者**: 测试工程师、开发团队、质量保证团队
> **更新日期**: 2025-11-11
> **版本**: v1.0

---

## 📋 目录

1. [测试架构概览](#1-测试架构概览)
2. [测试金字塔](#2-测试金字塔)
3. [单元测试](#3-单元测试)
4. [集成测试](#4-集成测试)
5. [API测试](#5-api测试)
6. [前端测试](#6-前端测试)
7. [端到端测试](#7-端到端测试)
8. [性能测试](#8-性能测试)
9. [安全测试](#9-安全测试)
10. [测试自动化](#10-测试自动化)

---

## 1. 测试架构概览

### 1.1 测试策略体系

```
┌─────────────────────────────────────────────────────────────┐
│                    测试策略金字塔                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                E2E测试 (5%)                          │   │
│  │           用户场景、业务流程验证                        │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │              集成测试 (25%)                         │   │
│  │        API测试、数据库测试、服务间交互                 │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │              单元测试 (70%)                          │   │
│  │        函数级测试、组件测试、逻辑验证                  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 测试分类

| 测试类型 | 比例 | 执行频率 | 负责人 | 工具 |
|----------|------|----------|--------|------|
| **单元测试** | 70% | 每次提交 | 开发者 | Jest, Pytest |
| **集成测试** | 25% | 每次构建 | 测试团队 | Supertest, TestContainers |
| **E2E测试** | 5% | 发布前 | QA团队 | Playwright |
| **性能测试** | - | 定期 | 性能团队 | K6, JMeter |
| **安全测试** | - | 定期 | 安全团队 | OWASP ZAP, Bandit |

### 1.3 测试环境

| 环境 | 用途 | 数据来源 | 测试类型 |
|------|------|----------|----------|
| **本地开发** | 单元测试、集成测试 | Mock数据 | 单元测试、集成测试 |
| **测试环境** | 功能测试、API测试 | 测试数据 | 集成测试、API测试 |
| **预生产环境** | 端到端测试、性能测试 | 脱敏生产数据 | E2E测试、性能测试 |
| **生产环境** | 监控测试、健康检查 | 生产数据 | 监控测试 |

---

## 2. 测试金字塔

### 2.1 测试层次定义

```python
# tests/conftest.py - 测试配置
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os

# 测试数据库配置
@pytest.fixture(scope="session")
def test_db():
    """创建测试数据库"""
    # 使用内存数据库或临时文件
    db_fd, db_path = tempfile.mkstemp()

    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False}
    )

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # 创建表
    Base.metadata.create_all(bind=engine)

    yield TestingSessionLocal

    # 清理
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def db_session(test_db):
    """创建数据库会话"""
    session = test_db()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def client(db_session):
    """创建测试客户端"""
    from app.main import app
    from app.database import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
```

### 2.2 测试数据管理

```python
# tests/fixtures/data.py
import pytest
from app.models import User, Project, AdAccount, DailyReport
from app.core.security import get_password_hash
from datetime import datetime, date

@pytest.fixture
def sample_user():
    """示例用户数据"""
    return User(
        id="test-user-id",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        name="Test User",
        role="media_buyer",
        is_active=True,
        created_at=datetime.utcnow()
    )

@pytest.fixture
def sample_project():
    """示例项目数据"""
    return Project(
        id="test-project-id",
        name="Test Project",
        description="Test project description",
        client_name="Test Client",
        status="active",
        budget=10000.0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@pytest.fixture
def sample_ad_account():
    """示例广告账户数据"""
    return AdAccount(
        id="test-account-id",
        name="Test Ad Account",
        account_id="act_test123",
        platform="facebook",
        status="active",
        daily_budget=100.0,
        project_id="test-project-id",
        assigned_user_id="test-user-id",
        created_at=datetime.utcnow()
    )

@pytest.fixture
def sample_daily_report():
    """示例日报数据"""
    return DailyReport(
        id="test-report-id",
        ad_account_id="test-account-id",
        user_id="test-user-id",
        report_date=date.today(),
        spend=50.0,
        impressions=1000,
        clicks=50,
        conversions=5,
        created_at=datetime.utcnow()
    )
```

---

## 3. 单元测试

### 3.1 后端单元测试

```python
# tests/unit/test_user_service.py
import pytest
from unittest.mock import Mock, patch
from app.services.user_service import UserService
from app.models import User
from app.schemas import UserCreate

class TestUserService:

    @pytest.fixture
    def user_service(self, db_session):
        """创建用户服务实例"""
        return UserService(db_session)

    @pytest.fixture
    def user_create_data(self):
        """用户创建数据"""
        return UserCreate(
            email="newuser@example.com",
            password="newpassword123",
            name="New User",
            role="media_buyer"
        )

    def test_create_user_success(self, user_service, user_create_data):
        """测试成功创建用户"""
        # 执行
        user = user_service.create_user(user_create_data)

        # 验证
        assert user.email == user_create_data.email
        assert user.name == user_create_data.name
        assert user.role == user_create_data.role
        assert user.hashed_password is not None
        assert user.hashed_password != user_create_data.password

    def test_create_user_duplicate_email(self, user_service, user_create_data, sample_user):
        """测试创建重复邮箱用户"""
        # 添加已有用户
        user_service.db.add(sample_user)
        user_service.db.commit()

        # 尝试创建相同邮箱的用户
        with pytest.raises(ValueError, match="邮箱已存在"):
            user_service.create_user(user_create_data)

    def test_authenticate_user_success(self, user_service, sample_user):
        """测试成功认证用户"""
        # 添加用户到数据库
        user_service.db.add(sample_user)
        user_service.db.commit()

        # 执行认证
        authenticated_user = user_service.authenticate_user(
            sample_user.email,
            "testpassword"
        )

        # 验证
        assert authenticated_user is not None
        assert authenticated_user.id == sample_user.id

    def test_authenticate_user_wrong_password(self, user_service, sample_user):
        """测试错误密码认证"""
        # 添加用户到数据库
        user_service.db.add(sample_user)
        user_service.db.commit()

        # 执行认证
        authenticated_user = user_service.authenticate_user(
            sample_user.email,
            "wrongpassword"
        )

        # 验证
        assert authenticated_user is None

    def test_authenticate_user_not_found(self, user_service):
        """测试不存在的用户认证"""
        # 执行认证
        authenticated_user = user_service.authenticate_user(
            "nonexistent@example.com",
            "password"
        )

        # 验证
        assert authenticated_user is None

    @patch('app.services.user_service.redis_client')
    def test_reset_password_success(self, mock_redis, user_service, sample_user):
        """测试成功重置密码"""
        # 添加用户到数据库
        user_service.db.add(sample_user)
        user_service.db.commit()

        # 模拟Redis操作
        mock_redis.get.return_value = "valid_token"
        mock_redis.delete.return_value = True

        # 执行密码重置
        result = user_service.reset_password(
            sample_user.email,
            "reset_token",
            "newpassword123"
        )

        # 验证
        assert result is True
        mock_redis.get.assert_called_once_with(f"reset_token:{sample_user.email}")
        mock_redis.delete.assert_called_once()

    def test_get_user_by_id_success(self, user_service, sample_user):
        """测试根据ID获取用户"""
        # 添加用户到数据库
        user_service.db.add(sample_user)
        user_service.db.commit()

        # 执行查询
        user = user_service.get_user_by_id(sample_user.id)

        # 验证
        assert user is not None
        assert user.id == sample_user.id
        assert user.email == sample_user.email

    def test_get_user_by_id_not_found(self, user_service):
        """测试获取不存在的用户"""
        # 执行查询
        user = user_service.get_user_by_id("nonexistent-id")

        # 验证
        assert user is None
```

### 3.2 工具函数测试

```python
# tests/unit/test_utils.py
import pytest
from app.utils.format import format_currency, format_percentage
from app.utils.validation import validate_email, validate_phone
from app.utils.date import get_date_range

class TestFormatUtils:

    def test_format_currency_valid(self):
        """测试有效货币格式化"""
        assert format_currency(1234.56) == "¥1,234.56"
        assert format_currency(0) == "¥0.00"
        assert format_currency(-123.45) == "-¥123.45"

    def test_format_currency_none(self):
        """测试None值货币格式化"""
        assert format_currency(None) == "¥0.00"

    def test_format_percentage_valid(self):
        """测试有效百分比格式化"""
        assert format_percentage(0.1234) == "12.34%"
        assert format_percentage(1.0) == "100.00%"
        assert format_percentage(0) == "0.00%"

class TestValidationUtils:

    def test_validate_email_valid(self):
        """测试有效邮箱验证"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org"
        ]
        for email in valid_emails:
            assert validate_email(email) is True

    def test_validate_email_invalid(self):
        """测试无效邮箱验证"""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user..name@example.com"
        ]
        for email in invalid_emails:
            assert validate_email(email) is False

    def test_validate_phone_valid(self):
        """测试有效手机号验证"""
        valid_phones = [
            "13812345678",
            "15987654321",
            "18612345678"
        ]
        for phone in valid_phones:
            assert validate_phone(phone) is True

    def test_validate_phone_invalid(self):
        """测试无效手机号验证"""
        invalid_phones = [
            "12345678901",
            "1381234567",
            "12812345678",
            "abc12345678"
        ]
        for phone in invalid_phones:
            assert validate_phone(phone) is False

class TestDateUtils:

    def test_get_date_range_this_month(self):
        """测试获取本月日期范围"""
        start_date, end_date = get_date_range("this_month")

        assert start_date.day == 1
        assert end_date >= start_date
        assert end_date.day >= start_date.day

    def test_get_date_range_last_month(self):
        """测试获取上月日期范围"""
        start_date, end_date = get_date_range("last_month")

        assert start_date.day == 1
        assert end_date.day >= 28  # 至少28天

    def test_get_date_range_custom(self):
        """测试自定义日期范围"""
        start_date, end_date = get_date_range("2024-01-01", "2024-01-31")

        assert start_date.strftime("%Y-%m-%d") == "2024-01-01"
        assert end_date.strftime("%Y-%m-%d") == "2024-01-31"
```

---

## 4. 集成测试

### 4.1 API集成测试

```python
# tests/integration/test_projects_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token

class TestProjectsAPI:

    @pytest.fixture
    def auth_headers(self, sample_user):
        """认证头"""
        token = create_access_token(data={"sub": sample_user.id})
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def sample_project_data(self):
        """示例项目数据"""
        return {
            "name": "Integration Test Project",
            "description": "Test project for integration testing",
            "client_name": "Test Client",
            "budget": 15000.0,
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        }

    def test_create_project_success(self, client: TestClient, auth_headers, sample_project_data):
        """测试成功创建项目"""
        response = client.post(
            "/api/projects",
            json=sample_project_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == sample_project_data["name"]
        assert data["data"]["client_name"] == sample_project_data["client_name"]
        assert "id" in data["data"]

    def test_create_project_unauthorized(self, client: TestClient, sample_project_data):
        """测试未授权创建项目"""
        response = client.post("/api/projects", json=sample_project_data)

        assert response.status_code == 401

    def test_create_project_invalid_data(self, client: TestClient, auth_headers):
        """测试无效数据创建项目"""
        invalid_data = {
            "name": "",  # 空名称
            "budget": -1000  # 负预算
        }

        response = client.post(
            "/api/projects",
            json=invalid_data,
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_get_projects_list(self, client: TestClient, auth_headers, sample_project, db_session):
        """测试获取项目列表"""
        # 添加示例项目
        db_session.add(sample_project)
        db_session.commit()

        response = client.get("/api/projects", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1
        assert any(p["id"] == sample_project.id for p in data["data"])

    def test_get_project_by_id(self, client: TestClient, auth_headers, sample_project, db_session):
        """测试根据ID获取项目"""
        # 添加示例项目
        db_session.add(sample_project)
        db_session.commit()

        response = client.get(
            f"/api/projects/{sample_project.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == sample_project.id
        assert data["data"]["name"] == sample_project.name

    def test_get_project_not_found(self, client: TestClient, auth_headers):
        """测试获取不存在的项目"""
        response = client.get(
            "/api/projects/nonexistent-id",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_update_project_success(self, client: TestClient, auth_headers, sample_project, db_session):
        """测试成功更新项目"""
        # 添加示例项目
        db_session.add(sample_project)
        db_session.commit()

        update_data = {
            "name": "Updated Project Name",
            "description": "Updated description",
            "budget": 20000.0
        }

        response = client.put(
            f"/api/projects/{sample_project.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == update_data["name"]
        assert data["data"]["budget"] == update_data["budget"]

    def test_delete_project_success(self, client: TestClient, auth_headers, sample_project, db_session):
        """测试成功删除项目"""
        # 添加示例项目
        db_session.add(sample_project)
        db_session.commit()

        response = client.delete(
            f"/api/projects/{sample_project.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_delete_project_not_found(self, client: TestClient, auth_headers):
        """测试删除不存在的项目"""
        response = client.delete(
            "/api/projects/nonexistent-id",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_project_statistics(self, client: TestClient, auth_headers, sample_project, db_session):
        """测试项目统计"""
        # 添加示例项目
        db_session.add(sample_project)
        db_session.commit()

        response = client.get(
            "/api/projects/statistics",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_projects" in data["data"]
        assert "active_projects" in data["data"]
        assert "total_budget" in data["data"]
```

### 4.2 数据库集成测试

```python
# tests/integration/test_database.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, User, Project, AdAccount
from app.services.project_service import ProjectService

class TestDatabaseIntegration:

    @pytest.fixture
    def engine(self):
        """创建测试数据库引擎"""
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=engine)
        yield engine
        Base.metadata.drop_all(bind=engine)

    @pytest.fixture
    def db_session(self, engine):
        """创建数据库会话"""
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def test_foreign_key_constraints(self, db_session, sample_user, sample_project):
        """测试外键约束"""
        # 添加用户和项目
        db_session.add(sample_user)
        db_session.add(sample_project)
        db_session.commit()

        # 创建关联的广告账户
        ad_account = AdAccount(
            name="Test Account",
            account_id="act_test123",
            platform="facebook",
            project_id=sample_project.id,  # 有效的外键
            assigned_user_id=sample_user.id  # 有效的外键
        )

        db_session.add(ad_account)
        db_session.commit()

        # 验证关联关系
        retrieved_account = db_session.query(AdAccount).first()
        assert retrieved_account.project_id == sample_project.id
        assert retrieved_account.assigned_user_id == sample_user.id

    def test_cascade_delete(self, db_session, sample_project, sample_ad_account):
        """测试级联删除"""
        # 添加项目和广告账户
        db_session.add(sample_project)
        db_session.add(sample_ad_account)
        db_session.commit()

        # 删除项目
        db_session.delete(sample_project)
        db_session.commit()

        # 验证关联的广告账户也被删除
        remaining_accounts = db_session.query(AdAccount).filter(
            AdAccount.project_id == sample_project.id
        ).all()

        assert len(remaining_accounts) == 0

    def test_transaction_rollback(self, db_session, sample_user):
        """测试事务回滚"""
        try:
            # 开始事务
            user = User(
                email="rollback@test.com",
                hashed_password="password",
                name="Rollback User"
            )
            db_session.add(user)
            db_session.flush()  # 不提交，只刷新

            # 模拟错误
            raise Exception("模拟错误")

        except Exception:
            # 回滚事务
            db_session.rollback()

        # 验证用户没有被保存
        saved_user = db_session.query(User).filter(
            User.email == "rollback@test.com"
        ).first()

        assert saved_user is None

    def test_database_indexes(self, db_session, sample_user):
        """测试数据库索引"""
        # 添加用户
        db_session.add(sample_user)
        db_session.commit()

        # 测试查询性能
        import time
        start_time = time.time()

        user = db_session.query(User).filter(
            User.email == sample_user.email
        ).first()

        end_time = time.time()
        query_time = end_time - start_time

        # 验证查询很快（应该使用索引）
        assert query_time < 0.01  # 10ms内完成
        assert user is not None
        assert user.email == sample_user.email
```

---

## 5. API测试

### 5.1 API测试框架

```python
# tests/api/test_api_framework.py
import pytest
import requests
from typing import Dict, Any, Optional

class APIClient:
    """API测试客户端"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.token: Optional[str] = None

    def login(self, email: str, password: str) -> bool:
        """登录获取token"""
        response = self.session.post(
            f"{self.base_url}/api/auth/login",
            json={"email": email, "password": password}
        )

        if response.status_code == 200:
            data = response.json()
            self.token = data["data"]["access_token"]
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}"
            })
            return True
        return False

    def get(self, endpoint: str, params: Dict[str, Any] = None) -> requests.Response:
        """GET请求"""
        return self.session.get(f"{self.base_url}{endpoint}", params=params)

    def post(self, endpoint: str, data: Dict[str, Any] = None) -> requests.Response:
        """POST请求"""
        return self.session.post(f"{self.base_url}{endpoint}", json=data)

    def put(self, endpoint: str, data: Dict[str, Any] = None) -> requests.Response:
        """PUT请求"""
        return self.session.put(f"{self.base_url}{endpoint}", json=data)

    def delete(self, endpoint: str) -> requests.Response:
        """DELETE请求"""
        return self.session.delete(f"{self.base_url}{endpoint}")

@pytest.fixture
def api_client():
    """API测试客户端fixture"""
    return APIClient("http://localhost:8000")

class TestAPIFramework:

    def test_api_health_check(self, api_client):
        """测试API健康检查"""
        response = api_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "services" in data

    def test_api_authentication(self, api_client):
        """测试API认证"""
        # 未认证请求
        response = api_client.get("/api/users/profile")
        assert response.status_code == 401

        # 登录
        login_success = api_client.login("test@example.com", "testpassword")
        assert login_success is True

        # 认证后的请求
        response = api_client.get("/api/users/profile")
        assert response.status_code == 200
```

### 5.2 API契约测试

```python
# tests/api/test_contract.py
import pytest
import jsonschema
from jsonschema import validate

class TestAPIContract:

    # API响应schema定义
    project_schema = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "data": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "client_name": {"type": "string"},
                    "status": {"type": "string"},
                    "budget": {"type": "number"},
                    "created_at": {"type": "string"},
                    "updated_at": {"type": "string"}
                },
                "required": ["id", "name", "client_name", "status", "budget"]
            },
            "message": {"type": "string"}
        },
        "required": ["success", "data"]
    }

    error_schema = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "message": {"type": "string"},
            "code": {"type": "string"},
            "errors": {"type": "array"}
        },
        "required": ["success", "message"]
    }

    def test_create_project_contract(self, api_client):
        """测试创建项目API契约"""
        # 登录
        api_client.login("test@example.com", "testpassword")

        # 创建项目
        project_data = {
            "name": "Contract Test Project",
            "description": "Test project for contract testing",
            "client_name": "Test Client",
            "budget": 10000.0
        }

        response = api_client.post("/api/projects", data=project_data)

        assert response.status_code == 201

        # 验证响应schema
        response_data = response.json()
        validate(instance=response_data, schema=self.project_schema)

        # 验证具体字段
        assert response_data["success"] is True
        assert response_data["data"]["name"] == project_data["name"]
        assert response_data["data"]["client_name"] == project_data["client_name"]
        assert response_data["data"]["budget"] == project_data["budget"]

    def test_error_response_contract(self, api_client):
        """测试错误响应API契约"""
        # 发送无效数据
        invalid_data = {
            "name": "",  # 空名称
            "budget": "invalid"  # 无效预算
        }

        response = api_client.post("/api/projects", data=invalid_data)

        assert response.status_code == 422

        # 验证错误响应schema
        response_data = response.json()
        validate(instance=response_data, schema=self.error_schema)

        # 验证错误字段
        assert response_data["success"] is False
        assert "errors" in response_data
        assert len(response_data["errors"]) > 0

    def test_pagination_contract(self, api_client):
        """测试分页API契约"""
        # 登录
        api_client.login("test@example.com", "testpassword")

        # 获取项目列表
        response = api_client.get("/api/projects?page=1&size=10")

        assert response.status_code == 200

        # 验证分页响应
        data = response.json()
        assert "pagination" in data

        pagination = data["pagination"]
        assert "page" in pagination
        assert "size" in pagination
        assert "total" in pagination
        assert "pages" in pagination

        assert pagination["page"] == 1
        assert pagination["size"] == 10
        assert pagination["total"] >= 0
```

---

## 6. 前端测试

### 6.1 组件单元测试

```typescript
// tests/components/ProjectCard.test.tsx
import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ProjectCard } from '@/components/projects/ProjectCard'
import { Project } from '@/types/project'

// Mock项目数据
const mockProject: Project = {
  id: '1',
  name: 'Test Project',
  description: 'Test Description',
  client_name: 'Test Client',
  status: 'active',
  budget: 10000,
  start_date: '2024-01-01',
  end_date: '2024-12-31',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z'
}

// 测试包装器
const createTestWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('ProjectCard', () => {
  it('renders project information correctly', () => {
    const Wrapper = createTestWrapper()

    render(
      <Wrapper>
        <ProjectCard project={mockProject} />
      </Wrapper>
    )

    expect(screen.getByText('Test Project')).toBeInTheDocument()
    expect(screen.getByText('Test Description')).toBeInTheDocument()
    expect(screen.getByText('Test Client')).toBeInTheDocument()
    expect(screen.getByText('¥10,000')).toBeInTheDocument()
  })

  it('displays correct status badge', () => {
    const Wrapper = createTestWrapper()

    render(
      <Wrapper>
        <ProjectCard project={mockProject} />
      </Wrapper>
    )

    const statusBadge = screen.getByText('active')
    expect(statusBadge).toBeInTheDocument()
    expect(statusBadge).toHaveClass('bg-green-100')
  })

  it('calls onEdit when edit button is clicked', () => {
    const onEdit = jest.fn()
    const Wrapper = createTestWrapper()

    render(
      <Wrapper>
        <ProjectCard project={mockProject} onEdit={onEdit} />
      </Wrapper>
    )

    const editButton = screen.getByRole('button', { name: /edit/i })
    fireEvent.click(editButton)

    expect(onEdit).toHaveBeenCalledWith(mockProject)
  })

  it('calls onDelete when delete button is clicked', () => {
    const onDelete = jest.fn()
    const Wrapper = createTestWrapper()

    render(
      <Wrapper>
        <ProjectCard project={mockProject} onDelete={onDelete} />
      </Wrapper>
    )

    const deleteButton = screen.getByRole('button', { name: /delete/i })
    fireEvent.click(deleteButton)

    expect(onDelete).toHaveBeenCalledWith(mockProject)
  })

  it('shows loading state during deletion', async () => {
    const onDelete = jest.fn(() => new Promise(resolve => setTimeout(resolve, 100)))
    const Wrapper = createTestWrapper()

    render(
      <Wrapper>
        <ProjectCard project={mockProject} onDelete={onDelete} />
      </Wrapper>
    )

    const deleteButton = screen.getByRole('button', { name: /delete/i })
    fireEvent.click(deleteButton)

    // 检查加载状态
    await waitFor(() => {
      expect(screen.getByText('删除中...')).toBeInTheDocument()
    })

    // 等待删除完成
    await waitFor(() => {
      expect(screen.queryByText('删除中...')).not.toBeInTheDocument()
    })
  })
})
```

### 6.2 React Hook测试

```typescript
// tests/hooks/useProjects.test.ts
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useProjects, useCreateProject } from '@/hooks/useProjects'
import { projectApi } from '@/lib/api/projects'
import { ProjectCreateRequest } from '@/types/project'

// Mock API
jest.mock('@/lib/api/projects')
const mockProjectApi = projectApi as jest.Mocked<typeof projectApi>

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('useProjects', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch projects successfully', async () => {
    const mockProjects = [
      { id: '1', name: 'Project 1' },
      { id: '2', name: 'Project 2' }
    ]

    mockProjectApi.getProjects.mockResolvedValue(mockProjects)

    const { result } = renderHook(() => useProjects(), {
      wrapper: createWrapper()
    })

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.projects).toEqual(mockProjects)
    expect(result.current.error).toBeNull()
    expect(mockProjectApi.getProjects).toHaveBeenCalledTimes(1)
  })

  it('should handle API error', async () => {
    const mockError = new Error('Failed to fetch projects')
    mockProjectApi.getProjects.mockRejectedValue(mockError)

    const { result } = renderHook(() => useProjects(), {
      wrapper: createWrapper()
    })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.projects).toEqual([])
    expect(result.current.error).toBeTruthy()
  })
})

describe('useCreateProject', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should create project successfully', async () => {
    const newProject = { id: '3', name: 'New Project' }
    const projectData: ProjectCreateRequest = {
      name: 'New Project',
      client_name: 'Test Client',
      budget: 10000
    }

    mockProjectApi.create.mockResolvedValue(newProject)

    const { result } = renderHook(() => useCreateProject(), {
      wrapper: createWrapper()
    })

    expect(result.current.isPending).toBe(false)

    result.current.mutate(projectData)

    expect(result.current.isPending).toBe(true)

    await waitFor(() => {
      expect(result.current.isPending).toBe(false)
    })

    expect(result.current.isSuccess).toBe(true)
    expect(result.current.data).toEqual(newProject)
    expect(mockProjectApi.create).toHaveBeenCalledWith(projectData)
  })

  it('should handle create error', async () => {
    const mockError = new Error('Failed to create project')
    const projectData: ProjectCreateRequest = {
      name: 'New Project',
      client_name: 'Test Client',
      budget: 10000
    }

    mockProjectApi.create.mockRejectedValue(mockError)

    const { result } = renderHook(() => useCreateProject(), {
      wrapper: createWrapper()
    })

    result.current.mutate(projectData)

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toBeTruthy()
    expect(result.current.isPending).toBe(false)
  })
})
```

---

## 7. 端到端测试

### 7.1 Playwright E2E测试

```typescript
// tests/e2e/project-management.spec.ts
import { test, expect } from '@playwright/test'

test.describe('项目管理 E2E 测试', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('/auth/login')
    await page.fill('[data-testid="email"]', 'test@example.com')
    await page.fill('[data-testid="password"]', 'testpassword123')
    await page.click('[data-testid="login-button"]')

    // 等待跳转到仪表盘
    await expect(page).toHaveURL('/dashboard')
  })

  test('should create, view, edit and delete a project', async ({ page }) => {
    // 1. 创建项目
    await page.click('[data-testid="nav-projects"]')
    await expect(page).toHaveURL('/dashboard/projects')

    await page.click('[data-testid="create-project-button"]')
    await expect(page.locator('[data-testid="project-modal"]')).toBeVisible()

    await page.fill('[data-testid="project-name"]', 'E2E Test Project')
    await page.fill('[data-testid="project-description"]', 'This is a test project for E2E testing')
    await page.fill('[data-testid="client-name"]', 'E2E Test Client')
    await page.fill('[data-testid="project-budget"]', '15000')
    await page.click('[data-testid="submit-button"]')

    // 验证项目创建成功
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible()
    await expect(page.locator('text=E2E Test Project')).toBeVisible()

    // 2. 查看项目详情
    await page.click('[data-testid="view-project-E2E Test Project"]')
    await expect(page).toHaveURL(/\/dashboard\/projects\/\w+/)

    await expect(page.locator('[data-testid="project-name"]')).toHaveText('E2E Test Project')
    await expect(page.locator('[data-testid="project-description"]')).toHaveText('This is a test project for E2E testing')
    await expect(page.locator('[data-testid="client-name"]')).toHaveText('E2E Test Client')
    await expect(page.locator('[data-testid="project-budget"]')).toHaveText('¥15,000')

    // 3. 编辑项目
    await page.click('[data-testid="edit-project-button"]')
    await expect(page.locator('[data-testid="project-modal"]')).toBeVisible()

    await page.fill('[data-testid="project-name"]', 'Updated E2E Test Project')
    await page.fill('[data-testid="project-budget"]', '20000')
    await page.click('[data-testid="submit-button"]')

    // 验证更新成功
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible()
    await expect(page.locator('[data-testid="project-name"]')).toHaveText('Updated E2E Test Project')
    await expect(page.locator('[data-testid="project-budget"]')).toHaveText('¥20,000')

    // 4. 删除项目
    page.on('dialog', dialog => dialog.accept())
    await page.click('[data-testid="delete-project-button"]')

    // 验证删除成功
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible()
    await expect(page).toHaveURL('/dashboard/projects')

    // 验证项目不在列表中
    await expect(page.locator('text=Updated E2E Test Project')).not.toBeVisible()
  })

  test('should filter and search projects', async ({ page }) => {
    // 导航到项目列表
    await page.click('[data-testid="nav-projects"]')

    // 测试搜索功能
    await page.fill('[data-testid="search-input"]', 'Test')
    await page.press('[data-testid="search-input"]', 'Enter')

    // 验证搜索结果
    const projectCards = page.locator('[data-testid="project-card"]')
    const count = await projectCards.count()

    for (let i = 0; i < count; i++) {
      const card = projectCards.nth(i)
      const text = await card.textContent()
      expect(text?.toLowerCase()).toContain('test')
    }

    // 测试状态过滤
    await page.selectOption('[data-testid="status-filter"]', 'active')
    await page.press('[data-testid="status-filter"]', 'Enter')

    // 验证过滤结果
    const activeCards = page.locator('[data-testid="project-card"][data-status="active"]')
    const activeCount = await activeCards.count()

    const allCards = await page.locator('[data-testid="project-card"]').count()
    expect(activeCount).toBeLessThanOrEqual(allCards)
  })

  test('should export project data', async ({ page }) => {
    // 导航到项目列表
    await page.click('[data-testid="nav-projects"]')

    // 点击导出按钮
    const downloadPromise = page.waitForEvent('download')
    await page.click('[data-testid="export-button"]')

    const download = await downloadPromise

    // 验证下载文件
    expect(download.suggestedFilename()).toMatch(/\.(xlsx|csv)$/)

    // 保存下载文件（可选）
    await download.saveAs('/tmp/projects-export.xlsx')
  })
})
```

### 7.2 跨浏览器测试

```typescript
// tests/e2e/cross-browser.spec.ts
import { test, devices } from '@playwright/test'

// 移动设备测试
test.describe('移动设备测试', () => {
  test('should work on mobile devices', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 }) // iPhone SE

    await page.goto('/')

    // 测试响应式布局
    await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible()
    await expect(page.locator('[data-testid="desktop-sidebar"]')).not.toBeVisible()

    // 测试移动端导航
    await page.click('[data-testid="mobile-menu-toggle"]')
    await expect(page.locator('[data-testid="mobile-navigation"]')).toBeVisible()
  })
})

// 跨浏览器测试
const browsers = ['chromium', 'firefox', 'webkit']
for (const browser of browsers) {
  test.describe(`${browser} 浏览器测试`, () => {
    test.use({ browserName: browser })

    test('should work correctly in different browsers', async ({ page }) => {
      await page.goto('/auth/login')

      // 基本功能测试
      await expect(page.locator('h1')).toContainText('登录')
      await expect(page.locator('[data-testid="email-input"]')).toBeVisible()
      await expect(page.locator('[data-testid="password-input"]')).toBeVisible()
      await expect(page.locator('[data-testid="login-button"]')).toBeVisible()
    })
  })
}
```

---

## 8. 性能测试

### 8.1 API性能测试

```javascript
// tests/performance/api-performance-test.js
import { check, sleep } from 'k6';
import http from 'k6/http';

export let options = {
  stages: [
    { duration: '2m', target: 100 }, // 2分钟内增加到100用户
    { duration: '5m', target: 100 }, // 保持100用户5分钟
    { duration: '2m', target: 200 }, // 2分钟内增加到200用户
    { duration: '5m', target: 200 }, // 保持200用户5分钟
    { duration: '2m', target: 0 },   // 2分钟内减少到0用户
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95%的请求响应时间小于500ms
    http_req_failed: ['rate<0.1'],    // 错误率小于10%
  },
};

const BASE_URL = 'http://localhost:8000';

export function setup() {
  // 获取认证token
  const loginResponse = http.post(`${BASE_URL}/api/auth/login`, JSON.stringify({
    email: 'test@example.com',
    password: 'testpassword123'
  }), {
    headers: {
      'Content-Type': 'application/json',
    },
  });

  return {
    token: loginResponse.json('data.access_token'),
  };
}

export default function(data) {
  const headers = {
    'Authorization': `Bearer ${data.token}`,
    'Content-Type': 'application/json',
  };

  // 测试项目列表API
  let response = http.get(`${BASE_URL}/api/projects`, { headers });

  check(response, {
    '项目列表状态码是200': (r) => r.status === 200,
    '项目列表响应时间<200ms': (r) => r.timings.duration < 200,
    '项目列表返回数据': (r) => r.json('success') === true,
  });

  sleep(1);

  // 测试项目统计API
  response = http.get(`${BASE_URL}/api/projects/statistics`, { headers });

  check(response, {
    '统计数据状态码是200': (r) => r.status === 200,
    '统计数据响应时间<300ms': (r) => r.timings.duration < 300,
    '统计数据包含必要字段': (r) => {
      const data = r.json('data');
      return data.total_projects !== undefined &&
             data.active_projects !== undefined;
    },
  });

  sleep(1);
}

export function teardown() {
  console.log('性能测试完成');
}
```

### 8.2 前端性能测试

```typescript
// tests/performance/frontend-performance.spec.ts
import { test, expect } from '@playwright/test'

test.describe('前端性能测试', () => {
  test('should load main dashboard within performance budgets', async ({ page }) => {
    const start = Date.now()

    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')

    const loadTime = Date.now() - start

    // 性能预算检查
    expect(loadTime).toBeLessThan(3000) // 3秒内加载完成

    // Core Web Vitals
    const webVitals = await page.evaluate(() => {
      return new Promise((resolve) => {
        const vitals = {}

        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.entryType === 'largest-contentful-paint') {
              vitals.LCP = entry.startTime
            } else if (entry.entryType === 'first-input') {
              vitals.FID = entry.processingStart - entry.startTime
            } else if (entry.entryType === 'layout-shift') {
              vitals.CLS = (vitals.CLS || 0) + entry.value
            }
          }
        })

        observer.observe({ entryTypes: ['largest-contentful-paint', 'first-input', 'layout-shift'] })

        setTimeout(() => resolve(vitals), 5000)
      })
    })

    // LCP (Largest Contentful Paint) < 2.5s
    expect(webVitals.LCP).toBeLessThan(2500)

    // FID (First Input Delay) < 100ms
    expect(webVitals.FID).toBeLessThan(100)

    // CLS (Cumulative Layout Shift) < 0.1
    expect(webVitals.CLS).toBeLessThan(0.1)
  })

  test('should handle large datasets efficiently', async ({ page }) => {
    await page.goto('/dashboard/projects')

    // 模拟大数据集
    await page.evaluate(() => {
      // 注入大量项目数据
      const projects = Array.from({ length: 1000 }, (_, i) => ({
        id: `project-${i}`,
        name: `Project ${i}`,
        client_name: `Client ${i}`,
        budget: Math.random() * 100000,
        status: 'active'
      }))

      // 渲染到页面上
      window.testProjects = projects
    })

    const start = Date.now()

    // 测试大数据集渲染性能
    await page.evaluate(() => {
      const container = document.createElement('div')
      container.innerHTML = window.testProjects.map(project =>
        `<div class="project-card" data-id="${project.id}">${project.name}</div>`
      ).join('')
      document.body.appendChild(container)
    })

    const renderTime = Date.now() - start

    expect(renderTime).toBeLessThan(1000) // 1秒内完成渲染
  })
})
```

---

## 9. 安全测试

### 9.1 OWASP安全测试

```python
# tests/security/owasp_tests.py
import pytest
import requests
from urllib.parse import urljoin

class OWASPSecurityTests:

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()

    def test_sql_injection(self):
        """测试SQL注入漏洞"""
        sql_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "UNION SELECT * FROM users --",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --"
        ]

        for payload in sql_payloads:
            response = self.session.get(
                f"{self.base_url}/api/projects",
                params={"search": payload}
            )

            # 不应该返回数据库错误信息
            assert response.status_code not in [500, 502]
            assert "error" not in response.text.lower()
            assert "mysql" not in response.text.lower()

    def test_xss_attacks(self):
        """测试XSS攻击"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>"
        ]

        for payload in xss_payloads:
            response = self.session.post(
                f"{self.base_url}/api/projects",
                json={"name": payload, "description": payload}
            )

            if response.status_code == 200:
                # 检查响应是否被正确转义
                response_data = response.json()
                assert "<script>" not in str(response_data)
                assert "javascript:" not in str(response_data)

    def test_csrf_protection(self):
        """测试CSRF防护"""
        # 尝试没有CSRF令牌的请求
        response = self.session.post(
            f"{self.base_url}/api/projects",
            json={"name": "CSRF Test"}
        )

        # 应该返回403或包含CSRF令牌要求
        assert response.status_code in [403, 422]

    def test_authentication_bypass(self):
        """测试认证绕过"""
        protected_endpoints = [
            "/api/projects",
            "/api/users",
            "/api/reports"
        ]

        for endpoint in protected_endpoints:
            response = self.session.get(f"{self.base_url}{endpoint}")
            assert response.status_code == 401, f"{endpoint} 应该需要认证"

    def test_authorization_bypass(self):
        """测试权限绕过"""
        # 先登录普通用户
        login_response = self.session.post(
            f"{self.base_url}/api/auth/login",
            json={"email": "user@example.com", "password": "password"}
        )

        if login_response.status_code == 200:
            token = login_response.json()["data"]["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {token}"})

            # 尝试访问管理员端点
            admin_endpoints = [
                "/api/admin/users",
                "/api/admin/system-config"
            ]

            for endpoint in admin_endpoints:
                response = self.session.get(f"{self.base_url}{endpoint}")
                assert response.status_code == 403, f"{endpoint} 应该需要管理员权限"

# Pytest集成
@pytest.fixture
def security_tester():
    return OWASPSecurityTests("http://localhost:8000")

class TestOWASPSecurity:

    def test_sql_injection_protection(self, security_tester):
        """测试SQL注入防护"""
        security_tester.test_sql_injection()

    def test_xss_protection(self, security_tester):
        """测试XSS防护"""
        security_tester.test_xss_attacks()

    def test_authentication_required(self, security_tester):
        """测试认证要求"""
        security_tester.test_authentication_bypass()

    def test_authorization_check(self, security_tester):
        """测试权限检查"""
        security_tester.test_authorization_bypass()
```

---

## 10. 测试自动化

### 10.1 CI/CD集成

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run code linting
      run: |
        cd backend
        flake8 app/
        black --check app/
        isort --check-only app/

    - name: Run security checks
      run: |
        cd backend
        bandit -r app/ -f json -o security-report.json
        safety check

    - name: Run unit tests
      run: |
        cd backend
        pytest tests/unit/ -v --cov=app --cov-report=xml --cov-report=html

    - name: Run integration tests
      run: |
        cd backend
        pytest tests/integration/ -v

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '20'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json

    - name: Install dependencies
      run: |
        cd frontend
        npm ci

    - name: Run code linting
      run: |
        cd frontend
        npm run lint
        npm run type-check

    - name: Run unit tests
      run: |
        cd frontend
        npm run test:unit -- --coverage --watchAll=false

    - name: Run component tests
      run: |
        cd frontend
        npm run test:component -- --watchAll=false

    - name: Build application
      run: |
        cd frontend
        npm run build

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./frontend/coverage/lcov.info

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]

    steps:
    - uses: actions/checkout@v4

    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '20'

    - name: Install Playwright
      run: |
        npx playwright install --with-deps

    - name: Start services
      run: |
        docker-compose -f docker-compose.test.yml up -d
        sleep 30

    - name: Run E2E tests
      run: |
        npx playwright test

    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: playwright-report
        path: playwright-report/

  performance-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests]
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v4

    - name: Set up K6
      run: |
        sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
        echo "deb https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
        sudo apt-get update
        sudo apt-get install k6

    - name: Start backend service
      run: |
        docker-compose -f docker-compose.test.yml up -d
        sleep 30

    - name: Run performance tests
      run: |
        k6 run tests/performance/api-performance-test.js

    - name: Upload performance results
      uses: actions/upload-artifact@v3
      with:
        name: performance-results
        path: performance-results/
```

### 10.2 测试报告生成

```python
# tests/utils/report_generator.py
import json
import pytest
from datetime import datetime
from typing import Dict, List, Any

class TestReportGenerator:
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()

    def add_test_result(self, test_name: str, status: str, duration: float, details: Dict[str, Any] = None):
        """添加测试结果"""
        self.results.append({
            "test_name": test_name,
            "status": status,  # passed, failed, skipped
            "duration": duration,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })

    def generate_summary(self) -> Dict[str, Any]:
        """生成测试摘要"""
        total = len(self.results)
        passed = len([r for r in self.results if r["status"] == "passed"])
        failed = len([r for r in self.results if r["status"] == "failed"])
        skipped = len([r for r in self.results if r["status"] == "skipped"])

        total_duration = sum(r["duration"] for r in self.results)
        avg_duration = total_duration / total if total > 0 else 0

        return {
            "summary": {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "pass_rate": f"{(passed / total * 100):.1f}%" if total > 0 else "0%",
                "total_duration": f"{total_duration:.2f}s",
                "average_duration": f"{avg_duration:.2f}s"
            },
            "execution_time": {
                "start": self.start_time.isoformat(),
                "end": datetime.now().isoformat(),
                "total_seconds": (datetime.now() - self.start_time).total_seconds()
            }
        }

    def generate_html_report(self, output_file: str = "test-report.html"):
        """生成HTML测试报告"""
        summary = self.generate_summary()

        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>测试报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .summary {{ background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .passed {{ color: green; }}
                .failed {{ color: red; }}
                .skipped {{ color: orange; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>测试报告</h1>

            <div class="summary">
                <h2>测试摘要</h2>
                <p><strong>总测试数:</strong> {summary['summary']['total_tests']}</p>
                <p class="passed"><strong>通过:</strong> {summary['summary']['passed']}</p>
                <p class="failed"><strong>失败:</strong> {summary['summary']['failed']}</p>
                <p class="skipped"><strong>跳过:</strong> {summary['summary']['skipped']}</p>
                <p><strong>通过率:</strong> {summary['summary']['pass_rate']}</p>
                <p><strong>总耗时:</strong> {summary['summary']['total_duration']}</p>
                <p><strong>平均耗时:</strong> {summary['summary']['average_duration']}</p>
            </div>

            <h2>详细结果</h2>
            <table>
                <tr>
                    <th>测试名称</th>
                    <th>状态</th>
                    <th>耗时</th>
                    <th>详情</th>
                </tr>
        """

        for result in self.results:
            status_class = result["status"]
            html_template += f"""
                <tr>
                    <td>{result['test_name']}</td>
                    <td class="{status_class}">{result['status']}</td>
                    <td>{result['duration']:.3f}s</td>
                    <td>{json.dumps(result['details'], ensure_ascii=False)}</td>
                </tr>
            """

        html_template += """
            </table>
        </body>
        </html>
        """

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_template)

    def generate_json_report(self, output_file: str = "test-report.json"):
        """生成JSON测试报告"""
        report_data = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "generator": "TestReportGenerator v1.0"
            },
            "summary": self.generate_summary(),
            "test_results": self.results
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

# Pytest插件
def pytest_configure(config):
    """Pytest配置钩子"""
    config._test_report_generator = TestReportGenerator()

def pytest_runtest_logreport(report):
    """测试结果记录钩子"""
    if hasattr(config, '_test_report_generator'):
        generator = config._test_report_generator

        if report.when == 'call':
            details = {}
            if hasattr(report, 'longrepr') and report.longrepr:
                details["error"] = str(report.longrepr)

            generator.add_test_result(
                test_name=report.nodeid,
                status="passed" if report.passed else "failed",
                duration=report.duration,
                details=details
            )

def pytest_sessionfinish(session, exitstatus):
    """测试会话结束钩子"""
    if hasattr(config, '_test_report_generator'):
        generator = config._test_report_generator

        generator.generate_html_report()
        generator.generate_json_report()

        print(f"\n测试报告已生成:")
        print(f"- HTML报告: test-report.html")
        print(f"- JSON报告: test-report.json")
```

---

## 📞 测试支持

### 测试团队联系
- **测试负责人**: qa@company.com
- **自动化工程师**: automation@company.com
- **性能测试**: performance@company.com
- **安全测试**: security@company.com

### 测试工具和资源
- **测试管理**: https://testrail.yourdomain.com
- **缺陷管理**: https://jira.yourdomain.com
- **测试报告**: https://reports.yourdomain.com
- **测试文档**: https://wiki.yourdomain.com/testing

### 测试环境
- **测试环境**: https://test.yourdomain.com
- **预生产环境**: https://staging.yourdomain.com
- **性能测试环境**: https://perf.yourdomain.com

---

**文档版本**: v1.0
**最后更新**: 2025-11-11
**下次审查**: 测试流程更新时
**维护责任人**: 测试团队负责人