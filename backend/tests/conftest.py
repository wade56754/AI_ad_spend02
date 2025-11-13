"""
pytest配置和共享fixtures
Version: 1.0
Author: Claude协作开发
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import get_db, Base
from main import app
from models.user import User
from models.project import Project
from models.channel import Channel
from models.ad_account import AdAccount
from core.security import create_access_token, get_password_hash


# 测试数据库配置
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """创建测试数据库会话"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """创建测试客户端"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
    user = User(
        nickname="测试投手",
        email="buyer@test.com",
        hashed_password=get_password_hash("test123"),
        role="media_buyer",
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin_user(db_session):
    """创建测试管理员用户"""
    user = User(
        nickname="测试管理员",
        email="admin@test.com",
        hashed_password=get_password_hash("admin123"),
        role="admin",
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_data_operator_user(db_session):
    """创建测试数据员用户"""
    user = User(
        nickname="测试数据员",
        email="operator@test.com",
        hashed_password=get_password_hash("operator123"),
        role="data_operator",
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_project(db_session, test_admin_user):
    """创建测试项目"""
    project = Project(
        name="测试项目",
        client_name="测试客户",
        client_company="测试公司",
        description="这是一个测试项目",
        status="planning",
        budget=Decimal("10000.00"),
        currency="USD",
        created_by=test_admin_user.id
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_channel(db_session):
    """创建测试渠道"""
    channel = Channel(
        name="Facebook",
        service_fee_type="percent",
        service_fee_value=Decimal("3.00"),
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(channel)
    db_session.commit()
    db_session.refresh(channel)
    return channel


@pytest.fixture
def test_ad_account(db_session, test_project, test_channel, test_user):
    """创建测试广告账户"""
    ad_account = AdAccount(
        name="测试账户",
        project_id=test_project.id,
        channel_id=test_channel.id,
        assigned_user_id=test_user.id,
        status="active",
        created_at=datetime.utcnow()
    )
    db_session.add(ad_account)
    db_session.commit()
    db_session.refresh(ad_account)
    return ad_account


@pytest.fixture
def auth_headers_user(test_user):
    """用户认证头"""
    access_token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def auth_headers_admin(test_admin_user):
    """管理员认证头"""
    access_token = create_access_token(data={"sub": test_admin_user.email})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def auth_headers_operator(test_data_operator_user):
    """数据员认证头"""
    access_token = create_access_token(data={"sub": test_data_operator_user.email})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def sample_daily_report_data():
    """示例日报数据"""
    return {
        "report_date": "2024-01-15",
        "ad_account_id": 1,
        "campaign_name": "测试广告系列",
        "ad_group_name": "测试广告组",
        "ad_creative_name": "测试广告创意",
        "impressions": 10000,
        "clicks": 500,
        "spend": "100.00",
        "conversions": 10,
        "new_follows": 20,
        "cpa": "10.00",
        "roas": "5.00",
        "notes": "测试备注"
    }


@pytest.fixture
def sample_batch_import_data():
    """示例批量导入数据"""
    return {
        "reports": [
            {
                "report_date": "2024-01-15",
                "ad_account_id": 1,
                "campaign_name": "广告系列1",
                "impressions": 10000,
                "clicks": 500,
                "spend": "100.00",
                "conversions": 10,
                "new_follows": 20
            },
            {
                "report_date": "2024-01-16",
                "ad_account_id": 1,
                "campaign_name": "广告系列2",
                "impressions": 15000,
                "clicks": 750,
                "spend": "150.00",
                "conversions": 15,
                "new_follows": 30
            }
        ],
        "skip_errors": False
    }


@pytest.fixture
def excel_file_content():
    """Excel文件内容"""
    import pandas as pd
    from io import BytesIO

    data = {
        "报表日期": ["2024-01-15", "2024-01-16"],
        "广告账户ID": [1, 1],
        "广告系列名称": ["广告系列1", "广告系列2"],
        "展示次数": [10000, 15000],
        "点击次数": [500, 750],
        "消耗金额": [100.00, 150.00],
        "转化次数": [10, 15],
        "新增粉丝数": [20, 30],
        "备注": ["备注1", "备注2"]
    }

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output.getvalue()


# ===== 项目管理模块所需的Fixtures =====

@pytest.fixture
def test_account_manager_user(db_session):
    """创建测试账户管理员用户"""
    user = User(
        nickname="测试账户经理",
        email="manager@test.com",
        hashed_password=get_password_hash("manager123"),
        role="account_manager",
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_finance_user(db_session):
    """创建测试财务用户"""
    user = User(
        nickname="测试财务",
        email="finance@test.com",
        hashed_password=get_password_hash("finance123"),
        role="finance",
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(test_admin_user):
    """管理员访问令牌"""
    return create_access_token(data={"sub": test_admin_user.email})


@pytest.fixture
def media_buyer_token(test_user):
    """媒体买家访问令牌"""
    return create_access_token(data={"sub": test_user.email})


@pytest.fixture
def data_operator_token(test_data_operator_user):
    """数据员访问令牌"""
    return create_access_token(data={"sub": test_data_operator_user.email})


@pytest.fixture
def account_manager_token(test_account_manager_user):
    """账户管理员访问令牌"""
    return create_access_token(data={"sub": test_account_manager_user.email})


@pytest.fixture
def finance_token(test_finance_user):
    """财务访问令牌"""
    return create_access_token(data={"sub": test_finance_user.email})


@pytest.fixture
def sample_project_id(test_project):
    """示例项目ID"""
    return test_project.id


@pytest.fixture
def account_manager_project(db_session, test_admin_user, test_account_manager_user):
    """创建由账户管理员管理的项目"""
    project = Project(
        name="账户经理项目",
        client_name="经理客户",
        client_company="经理公司",
        description="由账户经理管理的项目",
        status="active",
        budget=Decimal("20000.00"),
        currency="USD",
        account_manager_id=test_account_manager_user.id,
        created_by=test_admin_user.id
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def account_manager_project_id(account_manager_project):
    """账户经理管理的项目ID"""
    return account_manager_project.id


@pytest.fixture
def media_buyer_project(db_session, test_admin_user, test_user):
    """创建媒体买家参与的项目"""
    from models.project import ProjectMember

    project = Project(
        name="媒体买家项目",
        client_name="买家客户",
        client_company="买家公司",
        description="媒体买家参与的项目",
        status="active",
        budget=Decimal("15000.00"),
        currency="USD",
        created_by=test_admin_user.id
    )
    db_session.add(project)
    db_session.flush()

    # 添加媒体买家为项目成员
    member = ProjectMember(
        project_id=project.id,
        user_id=test_user.id,
        role="media_buyer"
    )
    db_session.add(member)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def media_buyer_project_id(media_buyer_project):
    """媒体买家参与的项目ID"""
    return media_buyer_project.id


@pytest.fixture
def media_buyer_user_id(test_user):
    """媒体买家用户ID"""
    return test_user.id


@pytest.fixture
def sample_project_data():
    """示例项目数据"""
    return {
        "name": "新项目",
        "client_name": "新客户",
        "client_company": "新公司",
        "description": "新项目描述",
        "budget": "10000.00",
        "currency": "USD",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31"
    }


# ===== 充值管理模块所需的Fixtures =====

@pytest.fixture
def test_finance_user(db_session):
    """创建测试财务用户"""
    user = User(
        nickname="测试财务",
        email="finance@test.com",
        hashed_password=get_password_hash("finance123"),
        role="finance",
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_account_manager_user(db_session):
    """创建测试账户管理员用户"""
    user = User(
        nickname="测试账户经理",
        email="manager@test.com",
        hashed_password=get_password_hash("manager123"),
        role="account_manager",
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def finance_token(test_finance_user):
    """财务访问令牌"""
    return create_access_token(data={"sub": test_finance_user.email})


@pytest.fixture
def data_operator_token(test_data_operator_user):
    """数据员访问令牌"""
    return create_access_token(data={"sub": test_data_operator_user.email})


@pytest.fixture
def account_manager_token(test_account_manager_user):
    """账户管理员访问令牌"""
    return create_access_token(data={"sub": test_account_manager_user.email})


@pytest.fixture
def sample_topup_request_id(test_topup_request):
    """示例充值申请ID"""
    return test_topup_request.id


@pytest.fixture
def managed_project(db_session, test_admin_user, test_account_manager_user):
    """创建由账户管理员管理的项目"""
    from models.project import Project

    project = Project(
        name="经理项目",
        client_name="经理客户",
        client_company="经理公司",
        status="active",
        account_manager_id=test_account_manager_user.id,
        created_by=test_admin_user.id
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def managed_ad_account(db_session, managed_project, test_user):
    """创建由媒体买家管理的账户"""
    from models.ad_account import AdAccount

    ad_account = AdAccount(
        name="买家账户",
        project_id=managed_project.id,
        assigned_user_id=test_user.id,
        status="active",
        created_at=datetime.utcnow()
    )
    db_session.add(ad_account)
    db_session.commit()
    db_session.refresh(ad_account)
    return ad_account


@pytest.fixture
def managed_ad_account_id(managed_ad_account):
    """媒体买家管理的账户ID"""
    return managed_ad_account.id


@pytest.fixture
def sample_topup_request(db_session, test_ad_account, test_admin_user):
    """创建示例充值申请"""
    from models.topup import TopupRequest
    from utils.id_generator import generate_request_no

    request = TopupRequest(
        request_no=generate_request_no("TOP"),
        ad_account_id=test_ad_account.id,
        project_id=test_ad_account.project_id,
        requested_amount=Decimal("1000.00"),
        currency="USD",
        urgency_level="normal",
        reason="测试充值申请",
        status="pending",
        requested_by=test_admin_user.id
    )
    db_session.add(request)
    db_session.commit()
    db_session.refresh(request)
    return request


@pytest.fixture
def account_manager_project_id(managed_project):
    """账户经理管理的项目ID"""
    return managed_project.id


@pytest.fixture
def sample_ad_account_id(test_ad_account):
    """示例广告账户ID"""
    return test_ad_account.id