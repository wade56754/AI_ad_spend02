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

    终态：final_locked（仅可通过红冲修正）
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

    # 终态列表
    TERMINAL_STATES = [DailyReportStatus.FINAL_LOCKED]

    @classmethod
    def is_valid_transition(cls, from_status: DailyReportStatus, to_status: DailyReportStatus) -> bool:
        """检查状态流转是否合法"""
        return to_status in cls.VALID_TRANSITIONS.get(from_status, [])

    @classmethod
    def is_terminal_state(cls, status: DailyReportStatus) -> bool:
        """检查是否是终态"""
        return status in cls.TERMINAL_STATES

    @classmethod
    def get_all_states(cls) -> list:
        """获取所有状态"""
        return list(DailyReportStatus)

    @classmethod
    def get_happy_path(cls) -> list:
        """
        获取正常流程路径（趋势检查通过）

        raw_submitted → trend_pending → trend_ok → final_pending
        → final_confirmed → final_locked
        """
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
        """
        获取所有异常流程路径

        返回:
            dict: {path_name: [状态序列]}
        """
        return {
            # 趋势异常 → 运营确认正常 → 继续流程
            "trend_flagged_then_resolved": [
                DailyReportStatus.RAW_SUBMITTED,
                DailyReportStatus.TREND_PENDING,
                DailyReportStatus.TREND_FLAGGED,
                DailyReportStatus.TREND_RESOLVED,
                DailyReportStatus.FINAL_PENDING,
                DailyReportStatus.FINAL_CONFIRMED,
                DailyReportStatus.FINAL_LOCKED,
            ],
            # 趋势异常 → 要求投手重新提交 → 重新流转
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
        """
        获取非法流转测试用例

        返回不在白名单内的状态流转对
        """
        invalid = []
        all_states = list(DailyReportStatus)
        for from_state in all_states:
            valid_targets = cls.VALID_TRANSITIONS.get(from_state, [])
            for to_state in all_states:
                if to_state not in valid_targets and from_state != to_state:
                    invalid.append((from_state, to_state))
        return invalid


class TopupStateHelper:
    """
    充值申请7状态机测试辅助类

    状态流转规则（STATE_MACHINE.md v2.6 第9章）：
    draft → pending_review → finance_approve → paid → completed
                           ↘ rejected
                           ↘ cancelled

    终态：completed, rejected, cancelled
    """

    # 合法流转白名单
    VALID_TRANSITIONS = {
        TopupStatus.DRAFT: [TopupStatus.PENDING_REVIEW, TopupStatus.CANCELLED],
        TopupStatus.PENDING_REVIEW: [TopupStatus.FINANCE_APPROVE, TopupStatus.REJECTED],
        TopupStatus.FINANCE_APPROVE: [TopupStatus.PAID, TopupStatus.REJECTED],
        TopupStatus.PAID: [TopupStatus.COMPLETED],
        TopupStatus.COMPLETED: [],  # 终态
        TopupStatus.REJECTED: [],   # 终态
        TopupStatus.CANCELLED: [],  # 终态
    }

    # 终态列表
    TERMINAL_STATES = [TopupStatus.COMPLETED, TopupStatus.REJECTED, TopupStatus.CANCELLED]

    @classmethod
    def is_valid_transition(cls, from_status: TopupStatus, to_status: TopupStatus) -> bool:
        """检查状态流转是否合法"""
        return to_status in cls.VALID_TRANSITIONS.get(from_status, [])

    @classmethod
    def is_terminal_state(cls, status: TopupStatus) -> bool:
        """检查是否是终态"""
        return status in cls.TERMINAL_STATES

    @classmethod
    def get_all_states(cls) -> list:
        """获取所有状态"""
        return list(TopupStatus)

    @classmethod
    def get_happy_path(cls) -> list:
        """
        获取正常流程路径（审批通过并完成）

        draft → pending_review → finance_approve → paid → completed
        """
        return [
            TopupStatus.DRAFT,
            TopupStatus.PENDING_REVIEW,
            TopupStatus.FINANCE_APPROVE,
            TopupStatus.PAID,
            TopupStatus.COMPLETED,
        ]

    @classmethod
    def get_exception_paths(cls) -> dict:
        """
        获取所有异常流程路径

        返回:
            dict: {path_name: [状态序列]}
        """
        return {
            # 数据复核拒绝路径
            "data_review_reject": [
                TopupStatus.DRAFT,
                TopupStatus.PENDING_REVIEW,
                TopupStatus.REJECTED,
            ],
            # 财务审批拒绝路径
            "finance_reject": [
                TopupStatus.DRAFT,
                TopupStatus.PENDING_REVIEW,
                TopupStatus.FINANCE_APPROVE,
                TopupStatus.REJECTED,
            ],
            # 申请人取消路径
            "user_cancel": [
                TopupStatus.DRAFT,
                TopupStatus.CANCELLED,
            ],
        }

    @classmethod
    def get_invalid_transitions(cls) -> list:
        """
        获取非法流转测试用例

        返回不在白名单内的状态流转对
        """
        invalid = []
        all_states = list(TopupStatus)
        for from_state in all_states:
            valid_targets = cls.VALID_TRANSITIONS.get(from_state, [])
            for to_state in all_states:
                if to_state not in valid_targets and from_state != to_state:
                    invalid.append((from_state, to_state))
        return invalid


class ReconciliationStateHelper:
    """
    对账批次5状态机测试辅助类

    状态流转规则（STATE_MACHINE.md v2.6 第11章）：
    draft → pending_review → approved → completed
                           ↘ needs_adjustment → approved → completed

    终态：completed
    """

    # 合法流转白名单 (STATE_MACHINE.md v2.6 第11章)
    # P2-FIX: 修正 needs_adjustment → approved (不是 pending_review)
    VALID_TRANSITIONS = {
        ReconciliationBatchStatus.DRAFT: [ReconciliationBatchStatus.PENDING_REVIEW],
        ReconciliationBatchStatus.PENDING_REVIEW: [ReconciliationBatchStatus.APPROVED, ReconciliationBatchStatus.NEEDS_ADJUSTMENT],
        ReconciliationBatchStatus.APPROVED: [ReconciliationBatchStatus.COMPLETED],
        ReconciliationBatchStatus.NEEDS_ADJUSTMENT: [ReconciliationBatchStatus.APPROVED],  # P2-FIX: 调整后直接到 approved
        ReconciliationBatchStatus.COMPLETED: [],  # 终态
    }

    # 终态列表
    TERMINAL_STATES = [ReconciliationBatchStatus.COMPLETED]

    @classmethod
    def is_valid_transition(cls, from_status: ReconciliationBatchStatus, to_status: ReconciliationBatchStatus) -> bool:
        """检查状态流转是否合法"""
        return to_status in cls.VALID_TRANSITIONS.get(from_status, [])

    @classmethod
    def is_terminal_state(cls, status: ReconciliationBatchStatus) -> bool:
        """检查是否是终态"""
        return status in cls.TERMINAL_STATES

    @classmethod
    def get_all_states(cls) -> list:
        """获取所有状态"""
        return list(ReconciliationBatchStatus)

    @classmethod
    def get_happy_path(cls) -> list:
        """
        获取正常流程路径（直接审批通过）

        draft → pending_review → approved → completed
        """
        return [
            ReconciliationBatchStatus.DRAFT,
            ReconciliationBatchStatus.PENDING_REVIEW,
            ReconciliationBatchStatus.APPROVED,
            ReconciliationBatchStatus.COMPLETED,
        ]

    @classmethod
    def get_exception_paths(cls) -> dict:
        """
        获取所有异常流程路径

        P2-FIX: 修正路径与 STATE_MACHINE.md v2.6 第11章对齐
        needs_adjustment → approved (直接, 不经过 pending_review)

        返回:
            dict: {path_name: [状态序列]}
        """
        return {
            # 需调整后审批路径 (P2-FIX: needs_adjustment → approved 直接流转)
            "needs_adjustment_then_approve": [
                ReconciliationBatchStatus.DRAFT,
                ReconciliationBatchStatus.PENDING_REVIEW,
                ReconciliationBatchStatus.NEEDS_ADJUSTMENT,
                ReconciliationBatchStatus.APPROVED,  # P2-FIX: 直接到 approved
                ReconciliationBatchStatus.COMPLETED,
            ],
            # 多次调整路径 (需要回到 pending_review 才能再次到 needs_adjustment)
            # P2-FIX: 由于 needs_adjustment 只能到 approved, 多次调整需要:
            # needs_adjustment → approved → (业务上如果发现还需调整，新建批次或回退)
            # STATE_MACHINE.md 未定义从 approved 回到 needs_adjustment 的路径
            # 因此多次调整在当前状态机下不可行，移除此路径
            # 或者理解为: 一次 needs_adjustment 后必须完成
        }

    @classmethod
    def get_invalid_transitions(cls) -> list:
        """
        获取非法流转测试用例

        返回不在白名单内的状态流转对
        """
        invalid = []
        all_states = list(ReconciliationBatchStatus)
        for from_state in all_states:
            valid_targets = cls.VALID_TRANSITIONS.get(from_state, [])
            for to_state in all_states:
                if to_state not in valid_targets and from_state != to_state:
                    invalid.append((from_state, to_state))
        return invalid


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
# 缺失 Fixtures 补充（Test Fixture & Architecture Repair Flow）
# 必须与 STATE_MACHINE.md v2.6 / DATA_SCHEMA.md v5.2 保持一致
# ============================================================================

@pytest.fixture(scope="function")
def test_channel(db_session):
    """创建测试渠道"""
    channel = Channel(
        name="测试渠道",
        code="TEST_CHANNEL",
        platform_type="meta",
        status="active",
    )
    db_session.add(channel)
    db_session.commit()
    db_session.refresh(channel)
    return channel


@pytest.fixture(scope="function")
def test_project(db_session, test_user):
    """创建测试项目"""
    project = Project(
        name="测试项目",
        code="TEST_PROJECT",
        status="active",
        created_by=test_user.id,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture(scope="function")
def test_ad_account(db_session, test_project, test_channel, test_user):
    """
    创建测试广告账户

    必须与 DATA_SCHEMA.md v5.2 第3.2节保持一致。
    """
    ad_account = AdAccount(
        name="测试广告账户",
        account_id="TEST_ACCOUNT_001",
        project_id=test_project.id,
        channel_id=test_channel.id,
        status="active",
        assigned_to=test_user.id,
    )
    db_session.add(ad_account)
    db_session.commit()
    db_session.refresh(ad_account)
    return ad_account


# ============================================================================
# 角色专用 auth_headers Fixtures（P0-DR-001 修复）
# 必须与 AUTH_SPEC.md v2.0 保持一致
# ============================================================================

@pytest.fixture(scope="function")
def auth_headers_user(media_buyer_user):
    """
    创建普通用户（投手）认证请求头

    投手角色权限（AUTH_SPEC.md v2.0）：
    - 可创建自己负责账户的日报
    - 只能查看自己负责账户的数据
    """
    token_data = {
        "sub": str(media_buyer_user.id),
        "email": media_buyer_user.email,
        "role": media_buyer_user.role.value if hasattr(media_buyer_user.role, 'value') else media_buyer_user.role,
    }
    token = create_access_token(token_data)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def auth_headers_admin(test_user):
    """
    创建管理员认证请求头

    管理员角色权限（AUTH_SPEC.md v2.0）：
    - 完全访问所有资源
    - 可删除日报
    - 可回退终态
    """
    token_data = {
        "sub": str(test_user.id),
        "email": test_user.email,
        "role": test_user.role.value if hasattr(test_user.role, 'value') else test_user.role,
    }
    token = create_access_token(token_data)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def auth_headers_operator(data_operator_user):
    """
    创建数据操作员认证请求头

    数据操作员角色权限（AUTH_SPEC.md v2.0）：
    - 可审核日报
    - 可查看所有日报
    - 可执行批量导入
    """
    token_data = {
        "sub": str(data_operator_user.id),
        "email": data_operator_user.email,
        "role": data_operator_user.role.value if hasattr(data_operator_user.role, 'value') else data_operator_user.role,
    }
    token = create_access_token(token_data)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def auth_headers_finance(finance_user):
    """
    创建财务用户认证请求头

    财务角色权限（AUTH_SPEC.md v2.0）：
    - 可审批充值申请
    - 可查看账本数据
    - 只读访问日报（仅已锁定的）
    """
    token_data = {
        "sub": str(finance_user.id),
        "email": finance_user.email,
        "role": finance_user.role.value if hasattr(finance_user.role, 'value') else finance_user.role,
    }
    token = create_access_token(token_data)
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# 样例数据 Fixtures（P0-DR-002 修复）
# 必须与 DATA_SCHEMA.md v5.2 / STATE_MACHINE.md v2.6 保持一致
# ============================================================================

@pytest.fixture(scope="function")
def sample_daily_report_data():
    """
    日报创建样例数据

    字段必须与 DATA_SCHEMA.md v5.2 第3.5节保持一致。
    注意：status 初始值应为 raw_submitted（STATE_MACHINE.md v2.6 第8章）
    """
    return {
        "report_date": "2024-01-15",
        "ad_account_id": 1,  # 会被测试覆盖
        "campaign_name": "测试广告系列",
        "ad_group_name": "测试广告组",
        "ad_creative_name": "测试创意",
        "impressions": 10000,
        "clicks": 500,
        "spend": "100.00",
        "conversions": 10,
        "new_follows": 20,
        "cpa": "10.00",
        "roas": "2.50",
        "notes": "测试备注"
    }


@pytest.fixture(scope="function")
def sample_topup_data():
    """
    充值申请创建样例数据

    字段必须与 DATA_SCHEMA.md v5.2 / TOPUP_SOT.md 保持一致。
    注意：status 初始值应为 draft（STATE_MACHINE.md v2.6 第4章）
    """
    return {
        "ad_account_id": 1,  # 会被测试覆盖
        "requested_amount": "1000.00",
        "currency": "USD",
        "reason": "广告投放充值",
        "urgency_level": "normal"
    }


@pytest.fixture(scope="function")
def sample_reconciliation_data():
    """
    对账批次创建样例数据

    字段必须与 DATA_SCHEMA.md v5.2 / RECONCILIATION_SOT.md 保持一致。
    注意：status 初始值应为 draft（STATE_MACHINE.md v2.6 第4章）
    """
    from datetime import date
    return {
        "reconciliation_date": date.today().isoformat(),
        "channel_ids": [1],
        "auto_match": True,
        "threshold": "100.00",
        "notes": "测试对账批次"
    }


@pytest.fixture(scope="function")
def sample_batch_import_data(test_ad_account):
    """
    批量导入样例数据

    用于测试日报批量导入功能。
    """
    return {
        "reports": [
            {
                "report_date": "2024-01-15",
                "ad_account_id": test_ad_account.id,
                "campaign_name": "导入广告系列1",
                "impressions": 10000,
                "clicks": 500,
                "spend": "100.00",
                "conversions": 10
            },
            {
                "report_date": "2024-01-16",
                "ad_account_id": test_ad_account.id,
                "campaign_name": "导入广告系列2",
                "impressions": 20000,
                "clicks": 1000,
                "spend": "200.00",
                "conversions": 20
            }
        ],
        "skip_errors": False
    }


@pytest.fixture(scope="function")
def excel_file_content():
    """
    模拟Excel文件内容

    用于测试文件导入功能。
    返回一个最小的xlsx文件二进制内容。
    """
    import io
    try:
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.append(["report_date", "ad_account_id", "campaign_name", "impressions", "clicks", "spend"])
        ws.append(["2024-01-15", 1, "Excel导入测试", 10000, 500, 100.00])

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.read()
    except ImportError:
        # 如果没有 openpyxl，返回空字节（测试会跳过）
        return b""


# ============================================================================
# 状态常量映射（状态断言修复辅助）
# 旧状态名 → 新状态名 映射，确保测试与 STATE_MACHINE.md v2.6 对齐
# ============================================================================

class StatusMappings:
    """
    状态名称映射表

    用于测试代码中的状态断言对齐。
    旧状态 → STATE_MACHINE.md v2.6 定义的新状态
    """

    # 日报状态映射（8状态机）
    # P1 修复：rejected 映射语义修正
    # STATE_MACHINE.md v2.6 第8.2节明确规定：
    # "trend_flagged → raw_submitted (运营要求投手重新提交)"
    # 因此"被驳回"在业务语义上等同于"要求重新提交"，应映射到 raw_submitted
    DAILY_REPORT = {
        # 旧状态 → 新状态
        "pending": DailyReportStatus.RAW_SUBMITTED.value,
        "approved": DailyReportStatus.FINAL_CONFIRMED.value,
        "rejected": DailyReportStatus.RAW_SUBMITTED.value,  # 被驳回 → 打回重填（要求重新提交）
        "locked": DailyReportStatus.FINAL_LOCKED.value,
    }

    # 充值状态映射（7状态机）
    TOPUP = {
        # 旧状态 → 新状态
        "pending": TopupStatus.PENDING_REVIEW.value,
        "data_review": TopupStatus.FINANCE_APPROVE.value,  # 数据审核后 → 财务审批
        "approved": TopupStatus.PAID.value,
        "completed": TopupStatus.COMPLETED.value,
        "rejected": TopupStatus.REJECTED.value,
        "cancelled": TopupStatus.CANCELLED.value,
    }

    # 对账状态映射（5状态机）
    RECONCILIATION = {
        # 旧状态 → 新状态
        "pending": ReconciliationBatchStatus.DRAFT.value,  # 注意：首态是 draft 不是 pending
        "in_progress": ReconciliationBatchStatus.PENDING_REVIEW.value,
        "approved": ReconciliationBatchStatus.APPROVED.value,
        "needs_adjustment": ReconciliationBatchStatus.NEEDS_ADJUSTMENT.value,
        "completed": ReconciliationBatchStatus.COMPLETED.value,
    }

    @classmethod
    def get_daily_report_status(cls, old_status: str) -> str:
        """获取日报的新状态值"""
        return cls.DAILY_REPORT.get(old_status, old_status)

    @classmethod
    def get_topup_status(cls, old_status: str) -> str:
        """获取充值的新状态值"""
        return cls.TOPUP.get(old_status, old_status)

    @classmethod
    def get_reconciliation_status(cls, old_status: str) -> str:
        """获取对账的新状态值"""
        return cls.RECONCILIATION.get(old_status, old_status)


@pytest.fixture(scope="session")
def status_mappings():
    """状态映射辅助类"""
    return StatusMappings
