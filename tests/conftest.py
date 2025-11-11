#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库测试配置文件
提供测试所需的共享 fixtures 和配置
"""

import os
import sys
import uuid
import asyncio
from pathlib import Path
from typing import Generator, Dict, Any
from decimal import Decimal
from datetime import datetime, date
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, joinedload
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.ext.compiler import compiles
import redis
import json
from unittest.mock import Mock, patch

# 把项目根目录加入 Python 搜索路径
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 设置测试环境变量
os.environ['TESTING'] = 'true'
os.environ['JWT_SECRET'] = 'test_secret_key_32_characters_long'
os.environ['ALLOWED_ORIGINS'] = 'http://localhost:3000'

# 测试数据库配置
TEST_DB_PATH = Path("test.db")
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()
os.environ.setdefault("DATABASE_URL", f"sqlite:///./{TEST_DB_PATH.name}")

# 导入应用模块
from backend.core.db import Base, get_engine, get_session_factory
from backend.core.security import AuthenticatedUser, get_current_user
from backend.main import app


# SQLite UUID 和 JSONB 兼容性
@compiles(PG_UUID, "sqlite")
def compile_uuid_sqlite(*_args, **_kwargs):
    return "CHAR(36)"


@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(*_args, **_kwargs):
    return "TEXT"


# pytest fixtures
@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def engine():
    """创建测试数据库引擎"""
    engine = get_engine()

    @event.listens_for(engine, "connect")
    def register_uuid_function(dbapi_connection, _):
        dbapi_connection.create_function("gen_random_uuid", 0, lambda: str(uuid.uuid4()))

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture(autouse=True)
def reset_database(engine):
    """每个测试前重置数据库"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(scope="session")
def test_user():
    """创建测试用户"""
    return AuthenticatedUser(
        id=str(uuid4()),
        role="admin",
        email="admin@test.com",
        name="测试管理员",
        raw_claims={"source": "pytest"},
    )


@pytest.fixture(scope="session")
def test_client_user():
    """创建普通测试用户"""
    return AuthenticatedUser(
        id=str(uuid4()),
        role="client",
        email="client@test.com",
        name="测试客户",
        raw_claims={"source": "pytest"},
    )


@pytest.fixture(scope="session")
def client(engine, test_user):
    """提供管理员权限的测试客户端"""
    app.dependency_overrides[get_current_user] = lambda: test_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture(scope="session")
def client_as_user(engine, test_client_user):
    """提供普通用户权限的测试客户端"""
    app.dependency_overrides[get_current_user] = lambda: test_client_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def db_session(engine):
    """提供数据库会话"""
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


# Redis测试客户端
@pytest.fixture
def redis_client():
    """提供Redis测试客户端"""
    test_redis = Mock(spec=redis.Redis)
    test_redis.ping.return_value = True
    test_redis.get.return_value = None
    test_redis.set.return_value = True
    test_redis.delete.return_value = True
    test_redis.exists.return_value = False
    return test_redis


# 测试数据工厂
class TestDataFactory:
    """测试数据工厂类"""

    @staticmethod
    def create_user_data(**kwargs):
        """创建用户数据"""
        defaults = {
            "email": f"user_{datetime.now().timestamp()}@test.com",
            "username": f"user_{datetime.now().timestamp()}",
            "name": "测试用户",
            "role": "client",
            "is_active": True
        }
        defaults.update(kwargs)
        return defaults

    @staticmethod
    def create_project_data(**kwargs):
        """创建项目数据"""
        defaults = {
            "name": f"测试项目_{datetime.now().timestamp()}",
            "description": "这是一个测试项目",
            "status": "active",
            "total_budget": 10000.00,
            "daily_budget": 500.00,
            "cpl_target": 50.00,
            "cpl_tolerance": 5.00
        }
        defaults.update(kwargs)
        return defaults

    @staticmethod
    def create_topup_data(**kwargs):
        """创建充值申请数据"""
        defaults = {
            "amount": 1000.00,
            "status": "draft",
            "notes": "测试充值申请"
        }
        defaults.update(kwargs)
        return defaults

    @staticmethod
    def create_daily_report_data(**kwargs):
        """创建日报数据"""
        defaults = {
            "report_date": date.today(),
            "impressions": 10000,
            "clicks": 500,
            "conversions": 10,
            "spend": 250.00,
            "revenue": 500.00,
            "cpl": 25.00,
            "cpa": 50.00,
            "ctr": 0.05,
            "conversion_rate": 0.02
        }
        defaults.update(kwargs)
        return defaults


@pytest.fixture
def test_data_factory():
    """提供测试数据工厂"""
    return TestDataFactory


# 示例数据 fixtures
@pytest.fixture
def sample_financial_data():
    """提供测试用的财务数据"""
    return {
        "daily_budget": Decimal("100.00"),
        "total_budget": Decimal("10000.00"),
        "cpl_target": Decimal("50.00"),
        "cpl_actual": Decimal("52.30"),
        "spend": Decimal("250.00"),
        "revenue": Decimal("500.00"),
        "topup_amount": Decimal("1000.00"),
        "service_fee": Decimal("10.00")
    }


@pytest.fixture
def sample_report_data():
    """提供测试用的报表数据"""
    return {
        "impressions": 10000,
        "clicks": 500,
        "conversions": 10,
        "spend": Decimal("250.00"),
        "revenue": Decimal("500.00"),
        "cpl": Decimal("25.00"),
        "cpa": Decimal("50.00"),
        "ctr": Decimal("0.05"),
        "conversion_rate": Decimal("0.02")
    }


# 辅助函数
def assert_decimal_equal(value1: Decimal, value2: Decimal, tolerance: Decimal = None):
    """断言两个Decimal值在容差范围内相等"""
    if tolerance is None:
        tolerance = Decimal("0.01")  # 默认精度为0.01

    difference = abs(value1 - value2)
    assert difference <= tolerance, f"{value1} != {value2}, difference: {difference}"


def create_test_file(filename: str, content: str = "test content") -> str:
    """创建测试文件"""
    filepath = f"tests/test_files/{filename}"
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath


def delete_test_file(filepath: str):
    """删除测试文件"""
    if os.path.exists(filepath):
        os.remove(filepath)


# Pytest配置
def pytest_configure(config):
    """配置pytest标记"""
    config.addinivalue_line(
        "markers", "unit: 单元测试（快速，不涉及外部资源）"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试（测试模块间交互）"
    )
    config.addinivalue_line(
        "markers", "functional: 功能测试（端到端业务流程）"
    )
    config.addinivalue_line(
        "markers", "performance: 性能测试（可能需要较长时间）"
    )
    config.addinivalue_line(
        "markers", "security: 安全测试（权限、认证等）"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试标记"
    )
    config.addinivalue_line(
        "markers", "smoke: 冒烟测试（基本功能验证）"
    )


# 测试标记集合
pytest_marks = {
    "unit": pytest.mark.unit,
    "integration": pytest.mark.integration,
    "functional": pytest.mark.functional,
    "performance": pytest.mark.performance,
    "security": pytest.mark.security,
    "slow": pytest.mark.slow,
    "smoke": pytest.mark.smoke,
}