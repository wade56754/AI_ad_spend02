"""
pytest配置和共享fixtures
Version: 1.1
Author: Claude Code
"""

import os
import hashlib
import pytest
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any
from uuid import UUID as PyUUID

from dotenv import load_dotenv

# 加载测试环境配置
env_path = os.path.join(os.path.dirname(__file__), '..', '.env.test')
load_dotenv(env_path, override=True)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, TypeDecorator, CHAR, event
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


# ============================================================================
# SQLite UUID 类型适配器（必须在导入模型之前定义）
# ============================================================================

class GUID(TypeDecorator):
    """
    Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def __init__(self, as_uuid=True, *args, **kwargs):
        """初始化 GUID 类型，接受 as_uuid 参数以兼容 PostgreSQL UUID"""
        self.as_uuid = as_uuid
        super().__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=self.as_uuid))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value) if not self.as_uuid else value
        else:
            if isinstance(value, PyUUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, PyUUID):
            return value
        if isinstance(value, str):
            return PyUUID(value) if self.as_uuid else value
        return value


# 替换 PostgreSQL UUID 类型为兼容的 GUID 类型
from sqlalchemy.dialects import postgresql
postgresql.UUID = GUID


# ============================================================================
# 现在可以安全导入模型
# ============================================================================

from backend.core.db import get_db, Base
from backend.main import app
from backend.models import (
    User,
    Project,
    Channel,
    AdAccount,
    DailyReport,
    TopupRequest,
    AdSpendDaily,
)
# 注意：不导入 TopupTransaction 和 TopupApprovalLog，因为它们使用了 SQLite 不支持的 PostgreSQL 函数
from backend.core.security import jwt_manager


# ============================================================================
# 辅助函数
# ============================================================================

def get_password_hash(password: str) -> str:
    """
    简化的测试密码哈希（仅用于测试环境）
    使用SHA256而非bcrypt以避免版本兼容性问题
    """
    return hashlib.sha256(password.encode()).hexdigest()


def create_access_token(data: dict) -> str:
    """创建JWT token"""
    return jwt_manager.create_access_token(data)


# ============================================================================
# 测试数据库配置
# ============================================================================

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)

# 启用 SQLite 外键约束
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ============================================================================
# Pytest Fixtures
# ============================================================================

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
    # 只创建测试需要的核心表，避免UUID兼容性问题
    # 注意：不创建 TopupTransaction 和 TopupApprovalLog 表，它们使用了 SQLite 不支持的 gen_random_uuid()
    tables_to_create = [
        User.__table__,
        Project.__table__,
        Channel.__table__,
        AdAccount.__table__,
        DailyReport.__table__,
        TopupRequest.__table__,
        AdSpendDaily.__table__,
    ]
    for table in tables_to_create:
        table.create(bind=engine, checkfirst=True)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # 清理测试表
        for table in reversed(tables_to_create):
            table.drop(bind=engine, checkfirst=True)


@pytest.fixture(scope="function")
def client(db_session):
    """创建测试客户端"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session):
    """创建测试用户"""
    from uuid import uuid4
    user = User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_token(test_user):
    """创建认证token"""
    token_data = {
        "sub": str(test_user.id),
        "email": test_user.email,
        "role": test_user.role,
    }
    return create_access_token(token_data)


@pytest.fixture(scope="function")
def auth_headers(auth_token):
    """创建认证请求头"""
    return {"Authorization": f"Bearer {auth_token}"}
