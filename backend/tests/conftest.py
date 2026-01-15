"""
pytest配置和共享fixtures
Version: 3.0 - 统一异步测试栈
Author: Claude Code

变更说明：
- 添加 async_client fixture 支持异步测试
- 保留 client fixture 用于同步测试
- 添加缺失的 fixtures（sample_topup_request_id 等）
- 移除 session-scoped event_loop（使用 pytest-asyncio 默认配置）
"""

import os
import hashlib
import pytest
import pytest_asyncio
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any, AsyncIterator
from uuid import UUID as PyUUID, uuid4

from dotenv import load_dotenv

# 加载测试环境配置
env_path = os.path.join(os.path.dirname(__file__), "..", ".env.test")
load_dotenv(env_path, override=True)

from sqlalchemy import (
    create_engine,
    TypeDecorator,
    CHAR,
    event,
    Text,
    JSON,
    Integer,
    BigInteger,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB as PG_JSONB
from sqlalchemy.dialects import sqlite
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.compiler import compiles


# ============================================================================
# SQLite BigInteger → INTEGER 编译器（必须在导入模型之前注册！）
# 解决 SQLite 中 BigInteger 主键的 autoincrement 问题
# SQLite 只支持 INTEGER PRIMARY KEY AUTOINCREMENT，不支持 BIGINT
# ============================================================================


@compiles(BigInteger, "sqlite")
def compile_biginteger_sqlite(element, compiler, **kw):
    """
    在 SQLite 中将 BigInteger 编译为 INTEGER
    这允许 autoincrement 正常工作（SQLite 要求 INTEGER PRIMARY KEY 才能自增）
    """
    return "INTEGER"


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
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=self.as_uuid))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
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


class JSONBCompat(TypeDecorator):
    """
    Platform-independent JSONB type.
    Uses PostgreSQL's JSONB type, otherwise uses JSON (SQLite compatible).
    """

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_JSONB())
        else:
            # SQLite 和其他数据库使用 JSON 类型
            return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        return value

    def process_result_value(self, value, dialect):
        return value


# ============================================================================
# 替换 PostgreSQL 特定类型为兼容类型（必须在导入模型之前执行）
# ============================================================================

from sqlalchemy.dialects import postgresql

# 替换 UUID 类型
postgresql.UUID = GUID

# 替换 JSONB 类型
postgresql.JSONB = JSONBCompat

# 同时替换 sqlalchemy.dialects.postgresql 模块中的引用
import sqlalchemy.dialects.postgresql as pg_module

pg_module.UUID = GUID
pg_module.JSONB = JSONBCompat


# ============================================================================
# 设置测试环境
# ============================================================================
os.environ["TESTING"] = "true"


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
from backend.models.finance.reconciliation import (
    ReconciliationBatch,
    ReconciliationDetail,
)
from backend.models.ledger import (
    LedgerTransaction,
    AccountBalance,
    BudgetAllocation,
)
from backend.core.audit import CoreAuditLog, SecurityEvent
from backend.models.base import (
    UserRole,
    DailyReportStatus,
    LedgerEntryType,
    ReconciliationBatchStatus,
    ReconciliationDetailStatus,
    TopupStatus,
)
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

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
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
# Pytest Fixtures - 数据库会话
# ============================================================================


@pytest.fixture(scope="function")
def db_session():
    """
    创建测试数据库会话

    使用 Base.metadata.create_all 创建所有表，
    依赖上面定义的 GUID 和 JSONBCompat 类型适配器来处理 PostgreSQL 特定类型
    """
    # 创建所有表
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # 清理所有表
        Base.metadata.drop_all(bind=engine)


# ============================================================================
# Pytest Fixtures - 测试客户端
# ============================================================================


@pytest.fixture(scope="function")
def client(db_session):
    """
    创建同步测试客户端（TestClient）

    用于同步测试，不使用 await。
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    from fastapi.testclient import TestClient

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session) -> AsyncIterator:
    """
    创建异步测试客户端（httpx.AsyncClient）

    用于异步测试，使用 await client.get() 等语法。
    使用 httpx.ASGITransport 直接与 FastAPI 应用通信。
    """
    import httpx

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ============================================================================
# 用户 Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def test_user(db_session):
    """
    创建测试用户

    注意: role 必须符合 MASTER.md v4.6 §2.4 宪法定义。
    合法角色（6个）: ceo, project_owner, finance, pitcher, account_manager, admin
    废弃角色: media_buyer → pitcher, data_operator → 移除, supervisor → project_owner
    """
    user = User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        password_hash="$2b$12$test_hashed_password_placeholder",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_user(db_session):
    """创建管理员用户"""
    user = User(
        id=uuid4(),
        email="admin@example.com",
        username="admin_user",
        password_hash="$2b$12$test_hashed_password_placeholder",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def ceo_user(db_session):
    """创建 CEO 用户 (最高权限)"""
    user = User(
        id=uuid4(),
        email="ceo@example.com",
        username="ceo_user",
        password_hash="$2b$12$test_hashed_password_placeholder",
        role=UserRole.CEO,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def finance_user(db_session):
    """创建财务用户"""
    user = User(
        id=uuid4(),
        email="finance@example.com",
        username="finance_user",
        password_hash="$2b$12$test_hashed_password_placeholder",
        role=UserRole.FINANCE,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def data_operator_user(db_session):
    """
    [DEPRECATED] 创建数据操作员用户

    警告: data_operator 角色已废弃 (MASTER.md v4.6)
    此 fixture 仅为向后兼容而保留，新测试不应使用此角色。
    使用此角色的 API 测试将返回 403 Forbidden。
    """
    user = User(
        id=uuid4(),
        email="data_op@example.com",
        username="data_operator_user",
        password_hash="$2b$12$test_hashed_password_placeholder",
        role="data_operator",  # 废弃角色，仅用于向后兼容
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def account_manager_user(db_session):
    """创建客户经理用户"""
    user = User(
        id=uuid4(),
        email="am@example.com",
        username="account_manager_user",
        password_hash="$2b$12$test_hashed_password_placeholder",
        role=UserRole.ACCOUNT_MANAGER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def project_owner_user(db_session):
    """
    创建项目负责人用户

    SoT: MASTER.md v4.6 §2.4 - project_owner 是合法角色
    """
    user = User(
        id=uuid4(),
        email="project_owner@example.com",
        username="project_owner_user",
        password_hash="$2b$12$test_hashed_password_placeholder",
        role="project_owner",  # 直接使用字符串以匹配 API 路由权限检查
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def pitcher_user(db_session):
    """
    创建投手用户

    SoT: MASTER.md v4.6 §2.4 - pitcher 是合法角色
    注意: 使用字符串 "pitcher" 而非枚举，因为 UserRole.MEDIA_BUYER 的值是 "media_buyer"
    """
    user = User(
        id=uuid4(),
        email="pitcher@example.com",
        username="pitcher_user",
        password_hash="$2b$12$test_hashed_password_placeholder",
        role="pitcher",  # 直接使用字符串以匹配 API 路由权限检查
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def media_buyer_user(pitcher_user):
    """
    [向后兼容别名] 请使用 pitcher_user

    DEPRECATED: media_buyer 已重命名为 pitcher (MASTER.md v4.6)
    """
    return pitcher_user


# ============================================================================
# Token Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def auth_token(test_user):
    """创建认证token"""
    token_data = {
        "sub": str(test_user.id),
        "email": test_user.email,
        "role": test_user.role.value
        if hasattr(test_user.role, "value")
        else str(test_user.role),
    }
    return create_access_token(token_data)


@pytest.fixture(scope="function")
def auth_headers(auth_token):
    """创建认证请求头"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="function")
def admin_token(admin_user):
    """管理员 token"""
    token_data = {
        "sub": str(admin_user.id),
        "email": admin_user.email,
        "role": admin_user.role.value
        if hasattr(admin_user.role, "value")
        else str(admin_user.role),
    }
    return create_access_token(token_data)


@pytest.fixture(scope="function")
def admin_headers(admin_token):
    """管理员请求头"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="function")
def finance_token(finance_user):
    """财务 token"""
    token_data = {
        "sub": str(finance_user.id),
        "email": finance_user.email,
        "role": finance_user.role.value
        if hasattr(finance_user.role, "value")
        else str(finance_user.role),
    }
    return create_access_token(token_data)


@pytest.fixture(scope="function")
def finance_headers(finance_token):
    """财务请求头"""
    return {"Authorization": f"Bearer {finance_token}"}


@pytest.fixture(scope="function")
def data_operator_token(data_operator_user):
    """数据操作员 token"""
    token_data = {
        "sub": str(data_operator_user.id),
        "email": data_operator_user.email,
        "role": data_operator_user.role.value
        if hasattr(data_operator_user.role, "value")
        else str(data_operator_user.role),
    }
    return create_access_token(token_data)


@pytest.fixture(scope="function")
def data_operator_headers(data_operator_token):
    """数据操作员请求头"""
    return {"Authorization": f"Bearer {data_operator_token}"}


@pytest.fixture(scope="function")
def project_owner_token(project_owner_user):
    """项目负责人 token (SoT: MASTER.md v4.6)"""
    token_data = {
        "sub": str(project_owner_user.id),
        "email": project_owner_user.email,
        "role": project_owner_user.role.value
        if hasattr(project_owner_user.role, "value")
        else str(project_owner_user.role),
    }
    return create_access_token(token_data)


@pytest.fixture(scope="function")
def pitcher_token(pitcher_user):
    """投手 token (SoT: MASTER.md v4.6)"""
    token_data = {
        "sub": str(pitcher_user.id),
        "email": pitcher_user.email,
        "role": pitcher_user.role.value
        if hasattr(pitcher_user.role, "value")
        else str(pitcher_user.role),
    }
    return create_access_token(token_data)


@pytest.fixture(scope="function")
def pitcher_headers(pitcher_token):
    """投手请求头 (SoT: MASTER.md v4.6)"""
    return {"Authorization": f"Bearer {pitcher_token}"}


@pytest.fixture(scope="function")
def media_buyer_token(pitcher_token):
    """[向后兼容别名] 请使用 pitcher_token"""
    return pitcher_token


@pytest.fixture(scope="function")
def media_buyer_headers(pitcher_headers):
    """[向后兼容别名] 请使用 pitcher_headers"""
    return pitcher_headers


@pytest.fixture(scope="function")
def account_manager_token(account_manager_user):
    """客户经理 token"""
    token_data = {
        "sub": str(account_manager_user.id),
        "email": account_manager_user.email,
        "role": account_manager_user.role.value
        if hasattr(account_manager_user.role, "value")
        else str(account_manager_user.role),
    }
    return create_access_token(token_data)


@pytest.fixture(scope="function")
def account_manager_headers(account_manager_token):
    """客户经理请求头"""
    return {"Authorization": f"Bearer {account_manager_token}"}


# ============================================================================
# 业务数据 Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def test_project(db_session, test_user):
    """创建测试项目"""
    project = Project(
        id=1,
        project_name="测试项目",
        project_code="TEST001",
        client_name="测试客户",
        status="active",
        created_by=test_user.id,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture(scope="function")
def test_project_2(db_session, test_user):
    """创建第二个测试项目（用于对比测试）"""
    project = Project(
        id=2,
        project_name="测试项目2",
        project_code="TEST002",
        client_name="测试客户2",
        status="active",
        created_by=test_user.id,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture(scope="function")
def test_channel(db_session):
    """创建测试渠道

    Channel 模型字段 (channel.py):
    - id, name, platform, status, risk_level, created_by, channel_metadata
    """
    channel = Channel(
        id=uuid4(),
        name="Facebook",
        platform="Meta",
        status="active",
    )
    db_session.add(channel)
    db_session.commit()
    db_session.refresh(channel)
    return channel


@pytest.fixture(scope="function")
def test_ad_account(db_session, test_project, test_channel, media_buyer_user):
    """创建测试广告账户

    AdAccount 模型字段 (ad_account.py):
    - id, project_id, channel_id, supplier_id, owner_id, team_id, buyer_id
    - name, account_code, status, status_reason
    """
    account = AdAccount(
        id=1,
        account_code="ACT_TEST_001",
        name="测试广告账户",
        status="active",
        project_id=test_project.id,
        channel_id=test_channel.id,
        owner_id=media_buyer_user.id,  # 分配给 media_buyer_user，以便权限检查通过
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture(scope="function")
def test_ad_account_2(db_session, test_project, test_channel, media_buyer_user):
    """创建第二个测试广告账户（用于迁移测试）"""
    account = AdAccount(
        id=2,
        account_code="ACT_TEST_002",
        name="测试广告账户2",
        status="active",
        project_id=test_project.id,
        channel_id=test_channel.id,
        owner_id=media_buyer_user.id,
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture(scope="function")
def funded_ad_account(db_session, test_ad_account):
    """
    创建有余额的测试广告账户（用于转账测试）

    为 test_ad_account 设置初始余额 10000.00，确保转账测试可以正常进行。
    """
    from decimal import Decimal
    from backend.models.finance.ledger import LedgerEntry
    from backend.models.enums import LedgerEntryType
    from datetime import datetime

    # 设置账户余额 (使用 balance 字段 - 服务层检查此字段)
    test_ad_account.balance = Decimal("10000.00")
    test_ad_account.deposit = Decimal("10000.00")  # 保持一致
    db_session.add(test_ad_account)

    # 创建对应的 LedgerEntry 记录（保持数据一致性）
    ledger_entry = LedgerEntry(
        ad_account_id=test_ad_account.id,
        entry_type=LedgerEntryType.TOPUP.value,
        amount=Decimal("10000.00"),
        currency="USD",
        notes="测试 fixture 初始化余额",
        occurred_at=datetime.utcnow(),
        entry_date=datetime.utcnow(),
    )
    db_session.add(ledger_entry)
    db_session.commit()
    db_session.refresh(test_ad_account)

    return test_ad_account


@pytest.fixture(scope="function")
def funded_ad_account_2(db_session, test_ad_account_2):
    """
    创建有余额的第二个测试广告账户（用于转账测试）

    为 test_ad_account_2 设置初始余额 10000.00。
    """
    from decimal import Decimal
    from backend.models.finance.ledger import LedgerEntry
    from backend.models.enums import LedgerEntryType
    from datetime import datetime

    # 设置账户余额 (使用 balance 字段 - 服务层检查此字段)
    test_ad_account_2.balance = Decimal("10000.00")
    test_ad_account_2.deposit = Decimal("10000.00")  # 保持一致
    db_session.add(test_ad_account_2)

    # 创建对应的 LedgerEntry 记录
    ledger_entry = LedgerEntry(
        ad_account_id=test_ad_account_2.id,
        entry_type=LedgerEntryType.TOPUP.value,
        amount=Decimal("10000.00"),
        balance_after=Decimal("10000.00"),
        reference_type="test_fixture",
        notes="测试 fixture 初始化余额",
        entry_date=datetime.utcnow(),
    )
    db_session.add(ledger_entry)
    db_session.commit()
    db_session.refresh(test_ad_account_2)

    return test_ad_account_2


# ============================================================================
# 账户转移/死号测试 Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def sample_pitcher(db_session):
    """
    创建独立的投手用户 (用于账户转移测试的目标投手)

    SoT: MASTER.md v4.6 §2.4 - pitcher 是合法角色
    用于: test_account_transfer_api.py - 账户转移目标
    """
    user = User(
        id=uuid4(),
        email="sample_pitcher@example.com",
        username="sample_pitcher",
        password_hash="$2b$12$test_hashed_password_placeholder",
        role="pitcher",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def sample_account_with_owner(db_session, test_project, test_channel, pitcher_user):
    """
    创建有 owner 的测试广告账户 (用于账户转移测试)

    用于: test_account_transfer_api.py - 账户转移源账户
    """
    account = AdAccount(
        id=100,
        account_code="ACT_TRANSFER_001",
        name="转移测试广告账户",
        status="active",
        project_id=test_project.id,
        channel_id=test_channel.id,
        owner_id=pitcher_user.id,  # 有 owner
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture(scope="function")
def sample_active_account(db_session, test_project, test_channel, pitcher_user):
    """
    创建活跃状态的测试广告账户 (用于死号处理测试)

    用于: test_mark_dead_api.py - 标记死号源账户
    状态: active (非 dead, 非 archived)
    """
    account = AdAccount(
        id=101,
        account_code="ACT_DEAD_001",
        name="死号测试广告账户",
        status="active",
        project_id=test_project.id,
        channel_id=test_channel.id,
        owner_id=pitcher_user.id,
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture(scope="function")
def sample_account_without_owner(db_session, test_project, test_channel):
    """
    创建无 owner 的测试广告账户 (用于账户转移测试)

    用于: test_account_transfer_api.py - 测试转移未分配账户
    """
    account = AdAccount(
        id=102,
        account_code="ACT_NO_OWNER_001",
        name="无负责人账户",
        status="active",
        project_id=test_project.id,
        channel_id=test_channel.id,
        owner_id=None,  # 无 owner
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture(scope="function")
def sample_finance_user(finance_user):
    """
    [别名] 财务用户 - 用于账户转移测试

    用于: test_account_transfer_api.py - 测试转移目标必须是投手
    """
    return finance_user


@pytest.fixture(scope="function")
def sample_dead_account(db_session, test_project, test_channel, pitcher_user):
    """
    创建已死号状态的测试广告账户

    用于: test_mark_dead_api.py - 测试不能重复标记
    """
    account = AdAccount(
        id=103,
        account_code="ACT_DEAD_002",
        name="已死号账户",
        status="dead",
        project_id=test_project.id,
        channel_id=test_channel.id,
        owner_id=pitcher_user.id,
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture(scope="function")
def sample_archived_account(db_session, test_project, test_channel, pitcher_user):
    """
    创建已归档状态的测试广告账户

    用于: test_mark_dead_api.py - 测试不能标记已归档账户
    """
    account = AdAccount(
        id=104,
        account_code="ACT_ARCHIVED_001",
        name="已归档账户",
        status="archived",
        project_id=test_project.id,
        channel_id=test_channel.id,
        owner_id=pitcher_user.id,
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture(scope="function")
def sample_new_account(db_session, test_project, test_channel, pitcher_user):
    """
    创建新建状态的测试广告账户

    用于: test_mark_dead_api.py - 测试从 new 状态标记死号
    """
    account = AdAccount(
        id=105,
        account_code="ACT_NEW_001",
        name="新建账户",
        status="new",
        project_id=test_project.id,
        channel_id=test_channel.id,
        owner_id=pitcher_user.id,
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture(scope="function")
def sample_testing_account(db_session, test_project, test_channel, pitcher_user):
    """
    创建测试中状态的测试广告账户

    用于: test_mark_dead_api.py - 测试从 testing 状态标记死号
    """
    account = AdAccount(
        id=106,
        account_code="ACT_TESTING_001",
        name="测试中账户",
        status="testing",
        project_id=test_project.id,
        channel_id=test_channel.id,
        owner_id=pitcher_user.id,
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture(scope="function")
def sample_suspended_account(db_session, test_project, test_channel, pitcher_user):
    """
    创建暂停状态的测试广告账户

    用于: test_mark_dead_api.py - 测试从 suspended 状态标记死号
    """
    account = AdAccount(
        id=107,
        account_code="ACT_SUSPENDED_001",
        name="已暂停账户",
        status="suspended",
        project_id=test_project.id,
        channel_id=test_channel.id,
        owner_id=pitcher_user.id,
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture(scope="function")
def sample_account_with_balance(db_session, test_project, test_channel, pitcher_user):
    """
    创建有余额的测试广告账户

    用于: test_mark_dead_api.py - 测试余额转移提示
    注意: AdAccount 使用 deposit 字段存储余额
    """
    from decimal import Decimal
    from backend.models.finance.ledger import LedgerEntry
    from backend.models.enums import LedgerEntryType
    from datetime import datetime

    account = AdAccount(
        id=108,
        account_code="ACT_BALANCE_001",
        name="有余额账户",
        status="active",
        project_id=test_project.id,
        channel_id=test_channel.id,
        owner_id=pitcher_user.id,
        deposit=Decimal("5000.00"),  # 使用 deposit 而非 balance
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    # 创建对应的 LedgerEntry 记录
    ledger_entry = LedgerEntry(
        ad_account_id=account.id,
        entry_type=LedgerEntryType.TOPUP.value,
        amount=Decimal("5000.00"),
        balance_after=Decimal("5000.00"),
        reference_type="test_fixture",
        notes="测试 fixture 初始化余额",
        entry_date=datetime.utcnow(),
    )
    db_session.add(ledger_entry)
    db_session.commit()
    db_session.refresh(account)

    return account


@pytest.fixture(scope="function")
def test_daily_report(db_session, test_ad_account, test_user):
    """
    创建测试日报

    字段命名对齐 SoT:
    - conversions_raw: 原始粉数 (raw 数据流)
    - raw_spend: 原始消耗 (raw 数据流)

    引用: API_SOT.md v9.0 第 9.2 节, STATE_MACHINE.md v2.6 第8章
    """
    report = DailyReport(
        id=1,
        ad_account_id=test_ad_account.id,
        report_date=date.today(),
        status=DailyReportStatus.RAW_SUBMITTED.value,
        # raw 数据流字段 (SoT-aligned)
        conversions_raw=50,
        raw_spend=Decimal("100.00"),
        # 其他字段
        submitted_by=test_user.id,
        notes="测试日报",
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)
    return report


@pytest.fixture(scope="function")
def test_reconciliation_batch(db_session, test_user, admin_user):
    """
    创建测试对账批次

    状态: draft (初始状态，符合 STATE_MACHINE.md v2.6)
    引用: STATE_MACHINE.md v2.6 第 11.1 章
    """
    from datetime import date, timedelta

    batch = ReconciliationBatch(
        batch_code=f"REC{datetime.now().strftime('%Y%m%d%H%M%S')}",
        period_start=date.today() - timedelta(days=7),
        period_end=date.today(),
        status=ReconciliationBatchStatus.DRAFT.value,
        total_system_spend=Decimal("10000.00"),
        total_actual_spend=Decimal("9500.00"),
        discrepancy=Decimal("500.00"),
        created_by=test_user.id,
        reviewed_by=None,
        closed_at=None,
        version=1,
    )
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)
    return batch


@pytest.fixture(scope="function")
def test_reconciliation_detail(db_session, test_reconciliation_batch, test_ad_account):
    """
    创建测试对账明细

    状态: pending (初始状态，符合 STATE_MACHINE.md v2.6)
    引用: STATE_MACHINE.md v2.6 第 11.2 章
    """
    detail = ReconciliationDetail(
        batch_id=test_reconciliation_batch.id,
        ad_account_id=test_ad_account.id,
        system_spend=Decimal("1000.00"),
        actual_spend=Decimal("950.00"),
        discrepancy=Decimal("50.00"),
        status=ReconciliationDetailStatus.PENDING.value,
        notes="测试对账明细",
        version=1,
    )
    db_session.add(detail)
    db_session.commit()
    db_session.refresh(detail)
    return detail


@pytest.fixture(scope="function")
def sample_reconciliation_batch_id(test_reconciliation_batch):
    """提供对账批次 ID（向后兼容）"""
    return test_reconciliation_batch.id


@pytest.fixture(scope="function")
def sample_reconciliation_detail_id(test_reconciliation_detail):
    """提供对账明细 ID（向后兼容）"""
    return test_reconciliation_detail.id


# ============================================================================
# Topup 相关 Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def managed_ad_account_id(test_ad_account):
    """返回被管理的广告账户 ID"""
    return test_ad_account.id


@pytest.fixture(scope="function")
def sample_ad_account_id(test_ad_account):
    """返回示例广告账户 ID（managed_ad_account_id 的别名）"""
    return test_ad_account.id


@pytest.fixture(scope="function")
def sample_topup_id(db_session, test_ad_account, media_buyer_user):
    """创建并返回示例充值申请 ID"""
    topup = TopupRequest(
        ad_account_id=test_ad_account.id,
        amount=Decimal("1000.00"),
        status=TopupStatus.DRAFT.value,
        requested_by=media_buyer_user.id,
        request_notes="测试充值申请",
    )
    db_session.add(topup)
    db_session.commit()
    db_session.refresh(topup)
    return topup.id


@pytest.fixture(scope="function")
def sample_topup_request_id(db_session, test_ad_account, media_buyer_user):
    """创建并返回示例充值申请 ID（sample_topup_id 的别名）"""
    topup = TopupRequest(
        ad_account_id=test_ad_account.id,
        amount=Decimal("2000.00"),
        status=TopupStatus.DRAFT.value,
        requested_by=media_buyer_user.id,
        request_notes="测试充值申请2",
    )
    db_session.add(topup)
    db_session.commit()
    db_session.refresh(topup)
    return topup.id


@pytest.fixture(scope="function")
def sample_topup(db_session, test_ad_account, media_buyer_user):
    """创建并返回完整的示例充值申请对象"""
    topup = TopupRequest(
        ad_account_id=test_ad_account.id,
        amount=Decimal("5000.00"),
        status=TopupStatus.DRAFT.value,
        requested_by=media_buyer_user.id,
        request_notes="测试充值申请对象",
    )
    db_session.add(topup)
    db_session.commit()
    db_session.refresh(topup)
    return topup


# ============================================================================
# 状态机测试辅助类
# ============================================================================


class DailyReportStateHelper:
    """日报8状态机测试辅助类"""

    VALID_TRANSITIONS = {
        DailyReportStatus.RAW_SUBMITTED: [DailyReportStatus.TREND_PENDING],
        DailyReportStatus.TREND_PENDING: [
            DailyReportStatus.TREND_OK,
            DailyReportStatus.TREND_FLAGGED,
        ],
        DailyReportStatus.TREND_OK: [DailyReportStatus.FINAL_PENDING],
        DailyReportStatus.TREND_FLAGGED: [
            DailyReportStatus.TREND_RESOLVED,
            DailyReportStatus.RAW_SUBMITTED,
        ],
        DailyReportStatus.TREND_RESOLVED: [DailyReportStatus.FINAL_PENDING],
        DailyReportStatus.FINAL_PENDING: [DailyReportStatus.FINAL_CONFIRMED],
        DailyReportStatus.FINAL_CONFIRMED: [DailyReportStatus.FINAL_LOCKED],
        DailyReportStatus.FINAL_LOCKED: [],
    }

    TERMINAL_STATES = [DailyReportStatus.FINAL_LOCKED]

    @classmethod
    def is_valid_transition(
        cls, from_status: DailyReportStatus, to_status: DailyReportStatus
    ) -> bool:
        return to_status in cls.VALID_TRANSITIONS.get(from_status, [])

    @classmethod
    def is_terminal_state(cls, status: DailyReportStatus) -> bool:
        return status == DailyReportStatus.FINAL_LOCKED

    @classmethod
    def get_all_states(cls) -> list:
        return list(DailyReportStatus)

    @classmethod
    def get_happy_path(cls) -> list:
        return [
            DailyReportStatus.RAW_SUBMITTED,
            DailyReportStatus.TREND_PENDING,
            DailyReportStatus.TREND_OK,
            DailyReportStatus.FINAL_PENDING,
            DailyReportStatus.FINAL_CONFIRMED,
            DailyReportStatus.FINAL_LOCKED,
        ]

    @classmethod
    def get_exception_paths(cls) -> dict:
        """获取异常路径（STATE_MACHINE.md v2.6 第8章）"""
        return {
            "trend_flagged_then_resolved": [
                DailyReportStatus.RAW_SUBMITTED,
                DailyReportStatus.TREND_PENDING,
                DailyReportStatus.TREND_FLAGGED,
                DailyReportStatus.TREND_RESOLVED,
                DailyReportStatus.FINAL_PENDING,
                DailyReportStatus.FINAL_CONFIRMED,
                DailyReportStatus.FINAL_LOCKED,
            ],
            "trend_flagged_then_resubmit": [
                DailyReportStatus.RAW_SUBMITTED,
                DailyReportStatus.TREND_PENDING,
                DailyReportStatus.TREND_FLAGGED,
                DailyReportStatus.RAW_SUBMITTED,
                DailyReportStatus.TREND_PENDING,
                DailyReportStatus.TREND_OK,
                DailyReportStatus.FINAL_PENDING,
                DailyReportStatus.FINAL_CONFIRMED,
                DailyReportStatus.FINAL_LOCKED,
            ],
        }

    @classmethod
    def get_invalid_transitions(cls) -> list:
        """获取所有非法流转（用于测试）"""
        all_states = cls.get_all_states()
        invalid = []
        for from_state in all_states:
            valid_targets = cls.VALID_TRANSITIONS.get(from_state, [])
            for to_state in all_states:
                if to_state != from_state and to_state not in valid_targets:
                    invalid.append((from_state, to_state))
        return invalid


class ReconciliationStateHelper:
    """对账批次5状态机测试辅助类（STATE_MACHINE.md v2.6 第11章）"""

    VALID_TRANSITIONS = {
        ReconciliationBatchStatus.DRAFT: [ReconciliationBatchStatus.PENDING_REVIEW],
        ReconciliationBatchStatus.PENDING_REVIEW: [
            ReconciliationBatchStatus.APPROVED,
            ReconciliationBatchStatus.NEEDS_ADJUSTMENT,
        ],
        ReconciliationBatchStatus.APPROVED: [ReconciliationBatchStatus.COMPLETED],
        ReconciliationBatchStatus.NEEDS_ADJUSTMENT: [
            ReconciliationBatchStatus.APPROVED
        ],  # 修复：needs_adjustment → approved（不是 pending_review）
        ReconciliationBatchStatus.COMPLETED: [],
    }

    TERMINAL_STATES = [ReconciliationBatchStatus.COMPLETED]

    @classmethod
    def is_valid_transition(
        cls,
        from_status: ReconciliationBatchStatus,
        to_status: ReconciliationBatchStatus,
    ) -> bool:
        return to_status in cls.VALID_TRANSITIONS.get(from_status, [])

    @classmethod
    def is_terminal_state(cls, status: ReconciliationBatchStatus) -> bool:
        return status == ReconciliationBatchStatus.COMPLETED

    @classmethod
    def get_all_states(cls) -> list:
        return list(ReconciliationBatchStatus)

    @classmethod
    def get_happy_path(cls) -> list:
        """正常流程：draft → pending_review → approved → completed"""
        return [
            ReconciliationBatchStatus.DRAFT,
            ReconciliationBatchStatus.PENDING_REVIEW,
            ReconciliationBatchStatus.APPROVED,
            ReconciliationBatchStatus.COMPLETED,
        ]

    @classmethod
    def get_exception_paths(cls) -> dict:
        """获取异常路径（STATE_MACHINE.md v2.6 第11章）"""
        return {
            "needs_adjustment_then_approve": [
                ReconciliationBatchStatus.DRAFT,
                ReconciliationBatchStatus.PENDING_REVIEW,
                ReconciliationBatchStatus.NEEDS_ADJUSTMENT,
                ReconciliationBatchStatus.APPROVED,
                ReconciliationBatchStatus.COMPLETED,
            ],
        }

    @classmethod
    def get_invalid_transitions(cls) -> list:
        """获取所有非法流转（用于测试）"""
        all_states = cls.get_all_states()
        invalid = []
        for from_state in all_states:
            valid_targets = cls.VALID_TRANSITIONS.get(from_state, [])
            for to_state in all_states:
                if to_state != from_state and to_state not in valid_targets:
                    invalid.append((from_state, to_state))
        return invalid


class LedgerInvariantHelper:
    """账本不可变量检查辅助类"""

    POSITIVE_TYPES = [
        LedgerEntryType.REVENUE,
        LedgerEntryType.TOPUP,
        LedgerEntryType.TRANSFER_IN,
    ]
    NEGATIVE_TYPES = [
        LedgerEntryType.COST,
        LedgerEntryType.TRANSFER_OUT,
        LedgerEntryType.REVERSAL,
    ]

    @classmethod
    def validate_amount_direction(
        cls, entry_type: LedgerEntryType, amount: Decimal
    ) -> bool:
        if entry_type in cls.POSITIVE_TYPES:
            return amount >= 0
        elif entry_type in cls.NEGATIVE_TYPES:
            return amount <= 0
        return False

    @classmethod
    def get_project_ledger_types(cls) -> list:
        return [
            LedgerEntryType.REVENUE,
            LedgerEntryType.TOPUP,
            LedgerEntryType.REVERSAL,
        ]

    @classmethod
    def get_supplier_ledger_types(cls) -> list:
        return [
            LedgerEntryType.COST,
            LedgerEntryType.TOPUP,
            LedgerEntryType.TRANSFER_OUT,
            LedgerEntryType.TRANSFER_IN,
            LedgerEntryType.REVERSAL,
        ]


@pytest.fixture(scope="session")
def daily_report_state_helper():
    """日报状态机辅助类"""
    return DailyReportStateHelper


# ============================================================================
# Daily Report 测试数据 Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def sample_daily_report_data(test_ad_account):
    """
    示例日报创建数据（用于 API 测试）

    对齐 API_SOT.md v9.0 第 9.2 节 DailyReportCreateRequest
    字段命名遵循 SoT 三数据流规范:
    - conversions_raw / raw_spend: raw 数据流（投手提交）
    """
    return {
        "report_date": date.today().isoformat(),
        "ad_account_id": test_ad_account.id,
        "conversions_raw": 50,
        "raw_spend": "100.00",
        "campaign_name": "测试广告系列",
        "ad_group_name": "测试广告组",
        "ad_creative_name": "测试创意",
        "impressions": 10000,
        "clicks": 500,
        "notes": "测试日报数据",
    }


@pytest.fixture(scope="function")
def sample_batch_import_data(test_ad_account):
    """
    示例批量导入数据（用于批量导入 API 测试）

    对齐 API_SOT.md v9.0 DailyReportBatchImportRequest
    """
    from datetime import timedelta

    return {
        "reports": [
            {
                "report_date": (date.today() - timedelta(days=1)).isoformat(),
                "ad_account_id": test_ad_account.id,
                "conversions_raw": 30,
                "raw_spend": "80.00",
                "impressions": 8000,
                "clicks": 400,
            },
            {
                "report_date": (date.today() - timedelta(days=2)).isoformat(),
                "ad_account_id": test_ad_account.id,
                "conversions_raw": 40,
                "raw_spend": "90.00",
                "impressions": 9000,
                "clicks": 450,
            },
        ],
        "skip_errors": False,
    }


# Alias fixtures for backward compatibility with existing tests
@pytest.fixture(scope="function")
def auth_headers_user(media_buyer_headers):
    """投手用户请求头（向后兼容别名）"""
    return media_buyer_headers


@pytest.fixture(scope="function")
def auth_headers_admin(admin_headers):
    """管理员请求头（向后兼容别名）"""
    return admin_headers


@pytest.fixture(scope="function")
def auth_headers_operator(data_operator_headers):
    """数据操作员请求头（向后兼容别名）"""
    return data_operator_headers


class TopupStateHelper:
    """充值申请7状态机测试辅助类（STATE_MACHINE.md v2.6 第9章）"""

    VALID_TRANSITIONS = {
        TopupStatus.DRAFT: [TopupStatus.PENDING_REVIEW, TopupStatus.CANCELLED],
        TopupStatus.PENDING_REVIEW: [TopupStatus.FINANCE_APPROVE, TopupStatus.REJECTED],
        TopupStatus.FINANCE_APPROVE: [TopupStatus.PAID, TopupStatus.REJECTED],
        TopupStatus.PAID: [TopupStatus.COMPLETED],
        TopupStatus.COMPLETED: [],
        TopupStatus.REJECTED: [],
        TopupStatus.CANCELLED: [],
    }

    TERMINAL_STATES = [
        TopupStatus.COMPLETED,
        TopupStatus.REJECTED,
        TopupStatus.CANCELLED,
    ]

    @classmethod
    def is_valid_transition(
        cls, from_status: TopupStatus, to_status: TopupStatus
    ) -> bool:
        return to_status in cls.VALID_TRANSITIONS.get(from_status, [])

    @classmethod
    def is_terminal_state(cls, status: TopupStatus) -> bool:
        return status in cls.TERMINAL_STATES

    @classmethod
    def get_all_states(cls) -> list:
        return list(TopupStatus)

    @classmethod
    def get_happy_path(cls) -> list:
        """正常流程：draft → pending_review → finance_approve → paid → completed"""
        return [
            TopupStatus.DRAFT,
            TopupStatus.PENDING_REVIEW,
            TopupStatus.FINANCE_APPROVE,
            TopupStatus.PAID,
            TopupStatus.COMPLETED,
        ]

    @classmethod
    def get_exception_paths(cls) -> dict:
        """获取异常路径（STATE_MACHINE.md v2.6 第9章）"""
        return {
            "data_review_reject": [
                TopupStatus.DRAFT,
                TopupStatus.PENDING_REVIEW,
                TopupStatus.REJECTED,
            ],
            "finance_reject": [
                TopupStatus.DRAFT,
                TopupStatus.PENDING_REVIEW,
                TopupStatus.FINANCE_APPROVE,
                TopupStatus.REJECTED,
            ],
            "user_cancel": [
                TopupStatus.DRAFT,
                TopupStatus.CANCELLED,
            ],
        }

    @classmethod
    def get_invalid_transitions(cls) -> list:
        """获取所有非法流转（用于测试）"""
        all_states = cls.get_all_states()
        invalid = []
        for from_state in all_states:
            valid_targets = cls.VALID_TRANSITIONS.get(from_state, [])
            for to_state in all_states:
                if to_state != from_state and to_state not in valid_targets:
                    invalid.append((from_state, to_state))
        return invalid


@pytest.fixture(scope="session")
def topup_state_helper():
    """充值状态机辅助类"""
    return TopupStateHelper


@pytest.fixture(scope="session")
def reconciliation_state_helper():
    """对账状态机辅助类"""
    return ReconciliationStateHelper


@pytest.fixture(scope="session")
def ledger_invariant_helper():
    """账本不可变量辅助类"""
    return LedgerInvariantHelper


# ============================================================================
# Projects 模块测试 Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def sample_project_id(test_project):
    """返回示例项目 ID"""
    return test_project.id


@pytest.fixture(scope="function")
def media_buyer_user_id(media_buyer_user):
    """返回投手用户 ID"""
    return media_buyer_user.id


@pytest.fixture(scope="function")
def account_manager_project(db_session, account_manager_user):
    """创建由客户经理管理的项目"""
    # 注意：created_by 是 UUID 类型，SQLite 需要字符串
    # account_manager_id 是 BigInteger，这里用简单的整数
    from uuid import UUID

    created_by_value = account_manager_user.id
    if isinstance(created_by_value, UUID):
        created_by_value = str(created_by_value)

    # account_manager_id 是 BigInteger，但 account_manager_user.id 是 UUID
    # 在测试环境中，我们需要确保 account_manager_id 与 account_manager_user.id 匹配
    # 由于类型不匹配，我们使用 account_manager_user.id 的整数哈希值作为 account_manager_id
    # 但这样会导致权限检查失败，因为 service 层检查 project.account_manager_id == user.id
    # 所以我们需要修改 service 层的检查逻辑，或者使用一个映射
    # 为了简化，我们直接使用 account_manager_user.id，让 SQLAlchemy 处理类型转换
    # 但 account_manager_id 是 BigInteger，不能直接存储 UUID
    # 解决方案：在 service 层，我们需要将 UUID 转换为整数进行比较
    # 或者，我们可以使用 account_manager_user.id 的整数表示
    account_manager_id_value = account_manager_user.id
    if isinstance(account_manager_id_value, UUID):
        # 使用 UUID 的整数表示（取绝对值以避免负数）
        account_manager_id_value = abs(account_manager_id_value.int) % (2**63)

    project = Project(
        name="Account Manager Project",  # 使用 name 而非 project_name
        client_name="AM Client",
        status="active",
        created_by=created_by_value,
        account_manager_id=account_manager_id_value,  # 使用 account_manager_user.id 的整数表示
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture(scope="function")
def account_manager_project_id(account_manager_project):
    """返回客户经理管理的项目 ID"""
    return account_manager_project.id


@pytest.fixture(scope="function")
def media_buyer_project(db_session, test_user, media_buyer_user):
    """创建投手参与的项目（通过 ProjectMember 关联）"""
    from backend.models import ProjectMember
    from uuid import UUID

    # 处理 UUID 兼容性
    created_by_value = test_user.id
    if isinstance(created_by_value, UUID):
        created_by_value = str(created_by_value)

    user_id_value = media_buyer_user.id
    if isinstance(user_id_value, UUID):
        user_id_value = str(user_id_value)

    project = Project(
        name="Media Buyer Project",  # 使用 name 而非 project_name
        client_name="MB Client",
        status="active",
        created_by=created_by_value,
    )
    db_session.add(project)
    db_session.flush()

    # 添加投手为项目成员 (SoT: MASTER.md v4.6 - pitcher 是合法角色)
    member = ProjectMember(project_id=project.id, user_id=user_id_value, role="pitcher")
    db_session.add(member)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture(scope="function")
def media_buyer_project_id(media_buyer_project):
    """返回投手参与的项目 ID"""
    return media_buyer_project.id


# ============================================================================
# 别名 Fixtures（向后兼容）
# ============================================================================


@pytest.fixture(scope="function")
def test_admin_user(admin_user):
    """admin_user 的别名"""
    return admin_user


@pytest.fixture(scope="function")
def test_finance_user(finance_user):
    """finance_user 的别名"""
    return finance_user


@pytest.fixture(scope="function")
def test_data_operator_user(data_operator_user):
    """data_operator_user 的别名"""
    return data_operator_user


@pytest.fixture(scope="function")
def test_account_manager_user(account_manager_user):
    """account_manager_user 的别名"""
    return account_manager_user


@pytest.fixture(scope="function")
def test_user_token(auth_token):
    """auth_token 的别名"""
    return auth_token


@pytest.fixture(scope="function")
def auth_headers_admin(admin_headers):
    """admin_headers 的别名"""
    return admin_headers


@pytest.fixture(scope="function")
def auth_headers_user(auth_headers):
    """auth_headers 的别名（普通用户）"""
    return auth_headers


@pytest.fixture(scope="function")
def auth_headers_operator(data_operator_headers):
    """data_operator_headers 的别名"""
    return data_operator_headers


# ============================================================================
# 日报测试数据 Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def sample_daily_report_data(test_ad_account, test_user):
    """
    示例日报数据（用于 API 测试）

    字段命名对齐 SoT:
    - conversions_raw: 原始粉数 (raw 数据流)
    - raw_spend: 原始消耗 (raw 数据流)

    引用: API_SOT.md v9.0 第 9.2 节
    """
    return {
        "ad_account_id": test_ad_account.id,
        "report_date": date.today().isoformat(),
        # raw 数据流字段 (SoT-aligned)
        "conversions_raw": 50,
        "raw_spend": "100.00",
        # 可选字段
        "notes": "测试日报数据",
    }


@pytest.fixture(scope="function")
def mock_daily_reports(db_session, test_ad_account, test_user):
    """
    创建多条模拟日报记录（用于分页测试）

    字段命名对齐 SoT:
    - conversions_raw: 原始粉数 (raw 数据流)
    - raw_spend: 原始消耗 (raw 数据流)

    引用: API_SOT.md v9.0 第 9.2 节, STATE_MACHINE.md v2.6 第8章
    """
    reports = []
    base_date = date.today()

    for i in range(10):
        report_date = date.fromordinal(base_date.toordinal() - i)
        report = DailyReport(
            ad_account_id=test_ad_account.id,
            report_date=report_date,
            status=DailyReportStatus.RAW_SUBMITTED.value,
            # raw 数据流字段 (SoT-aligned)
            conversions_raw=50 + i,
            raw_spend=Decimal(f"{100 + i * 10}.00"),
            # 其他字段
            submitted_by=test_user.id,
            notes=f"测试日报 {i+1}",
        )
        db_session.add(report)
        reports.append(report)

    db_session.commit()
    for r in reports:
        db_session.refresh(r)

    return reports
