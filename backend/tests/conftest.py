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
from backend.models.base import (
    UserRole,
    DailyReportStatus,
    LedgerEntryType,
    ReconciliationBatchStatus,
    ReconciliationDetailStatus,
    TopupStatus,
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
    """
    创建测试用户

    注意: role 必须使用 UserRole 枚举，与 AUTH_SPEC.md v2.0 保持一致。
    合法角色: admin, finance, data_operator, account_manager, media_buyer
    """
    from uuid import uuid4
    user = User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        role=UserRole.ADMIN,  # P0-FIXTURE-001 修复: 使用枚举而非字符串
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


# ============================================================================
# 角色专用 Fixtures（P2-FIXTURE-002 修复）
# 必须与 AUTH_SPEC.md v2.0 第2.2节保持一致
# ============================================================================

@pytest.fixture(scope="function")
def finance_user(db_session):
    """创建财务用户"""
    from uuid import uuid4
    user = User(
        id=uuid4(),
        email="finance@example.com",
        username="finance_user",
        role=UserRole.FINANCE,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def data_operator_user(db_session):
    """创建数据操作员用户"""
    from uuid import uuid4
    user = User(
        id=uuid4(),
        email="data_op@example.com",
        username="data_operator_user",
        role=UserRole.DATA_OPERATOR,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def account_manager_user(db_session):
    """创建客户经理用户"""
    from uuid import uuid4
    user = User(
        id=uuid4(),
        email="am@example.com",
        username="account_manager_user",
        role=UserRole.ACCOUNT_MANAGER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def media_buyer_user(db_session):
    """创建投手用户"""
    from uuid import uuid4
    user = User(
        id=uuid4(),
        email="buyer@example.com",
        username="media_buyer_user",
        role=UserRole.MEDIA_BUYER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ============================================================================
# 状态机测试辅助类（P2-FIXTURE-003 修复）
# 必须与 STATE_MACHINE.md v2.6 保持一致
# ============================================================================

class DailyReportStateHelper:
    """
    日报8状态机测试辅助类

    状态流转规则（STATE_MACHINE.md v2.6 第8章）：
    raw_submitted → trend_pending → trend_ok/trend_flagged
    → trend_resolved → final_pending → final_confirmed → final_locked
    """

    # 合法流转白名单
    VALID_TRANSITIONS = {
        DailyReportStatus.RAW_SUBMITTED: [DailyReportStatus.TREND_PENDING],
        DailyReportStatus.TREND_PENDING: [DailyReportStatus.TREND_OK, DailyReportStatus.TREND_FLAGGED],
        DailyReportStatus.TREND_OK: [DailyReportStatus.FINAL_PENDING],
        DailyReportStatus.TREND_FLAGGED: [DailyReportStatus.TREND_RESOLVED, DailyReportStatus.RAW_SUBMITTED],
        DailyReportStatus.TREND_RESOLVED: [DailyReportStatus.FINAL_PENDING],
        DailyReportStatus.FINAL_PENDING: [DailyReportStatus.FINAL_CONFIRMED],
        DailyReportStatus.FINAL_CONFIRMED: [DailyReportStatus.FINAL_LOCKED],
        DailyReportStatus.FINAL_LOCKED: [],  # 终态
    }

    @classmethod
    def is_valid_transition(cls, from_status: DailyReportStatus, to_status: DailyReportStatus) -> bool:
        """检查状态流转是否合法"""
        return to_status in cls.VALID_TRANSITIONS.get(from_status, [])

    @classmethod
    def is_terminal_state(cls, status: DailyReportStatus) -> bool:
        """检查是否是终态"""
        return status == DailyReportStatus.FINAL_LOCKED

    @classmethod
    def get_all_states(cls) -> list:
        """获取所有状态"""
        return list(DailyReportStatus)

    @classmethod
    def get_happy_path(cls) -> list:
        """获取正常流程路径"""
        return [
            DailyReportStatus.RAW_SUBMITTED,
            DailyReportStatus.TREND_PENDING,
            DailyReportStatus.TREND_OK,
            DailyReportStatus.FINAL_PENDING,
            DailyReportStatus.FINAL_CONFIRMED,
            DailyReportStatus.FINAL_LOCKED,
        ]


class ReconciliationStateHelper:
    """
    对账批次5状态机测试辅助类

    状态流转规则（STATE_MACHINE.md v2.6 第4章）：
    draft → pending_review → approved/needs_adjustment → completed
    """

    VALID_TRANSITIONS = {
        ReconciliationBatchStatus.DRAFT: [ReconciliationBatchStatus.PENDING_REVIEW],
        ReconciliationBatchStatus.PENDING_REVIEW: [ReconciliationBatchStatus.APPROVED, ReconciliationBatchStatus.NEEDS_ADJUSTMENT],
        ReconciliationBatchStatus.APPROVED: [ReconciliationBatchStatus.COMPLETED],
        ReconciliationBatchStatus.NEEDS_ADJUSTMENT: [ReconciliationBatchStatus.PENDING_REVIEW],
        ReconciliationBatchStatus.COMPLETED: [],  # 终态
    }

    @classmethod
    def is_valid_transition(cls, from_status: ReconciliationBatchStatus, to_status: ReconciliationBatchStatus) -> bool:
        """检查状态流转是否合法"""
        return to_status in cls.VALID_TRANSITIONS.get(from_status, [])

    @classmethod
    def is_terminal_state(cls, status: ReconciliationBatchStatus) -> bool:
        """检查是否是终态"""
        return status == ReconciliationBatchStatus.COMPLETED


class LedgerInvariantHelper:
    """
    账本不可变量检查辅助类

    金额方向规则（LEDGER_SOT.md v1.1 第4章）：
    - REVENUE: 正数
    - COST: 负数
    - TOPUP: 正数
    - TRANSFER_OUT: 负数
    - TRANSFER_IN: 正数
    - REVERSAL: 负数
    """

    POSITIVE_TYPES = [LedgerEntryType.REVENUE, LedgerEntryType.TOPUP, LedgerEntryType.TRANSFER_IN]
    NEGATIVE_TYPES = [LedgerEntryType.COST, LedgerEntryType.TRANSFER_OUT, LedgerEntryType.REVERSAL]

    @classmethod
    def validate_amount_direction(cls, entry_type: LedgerEntryType, amount: Decimal) -> bool:
        """验证金额方向是否正确"""
        if entry_type in cls.POSITIVE_TYPES:
            return amount >= 0
        elif entry_type in cls.NEGATIVE_TYPES:
            return amount <= 0
        return False

    @classmethod
    def get_project_ledger_types(cls) -> list:
        """获取PROJECT账本允许的分录类型"""
        return [LedgerEntryType.REVENUE, LedgerEntryType.TOPUP, LedgerEntryType.REVERSAL]

    @classmethod
    def get_supplier_ledger_types(cls) -> list:
        """获取SUPPLIER账本允许的分录类型"""
        return [LedgerEntryType.COST, LedgerEntryType.TOPUP, LedgerEntryType.TRANSFER_OUT,
                LedgerEntryType.TRANSFER_IN, LedgerEntryType.REVERSAL]


# 导出辅助类供测试使用
@pytest.fixture(scope="session")
def daily_report_state_helper():
    """日报状态机辅助类"""
    return DailyReportStateHelper


@pytest.fixture(scope="session")
def reconciliation_state_helper():
    """对账状态机辅助类"""
    return ReconciliationStateHelper


@pytest.fixture(scope="session")
def ledger_invariant_helper():
    """账本不可变量辅助类"""
    return LedgerInvariantHelper
