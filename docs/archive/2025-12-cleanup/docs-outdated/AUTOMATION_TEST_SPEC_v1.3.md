# AI_ad_spend02 自动化测试规范

> **版本**: v1.3
> **status**: active
> **owner**: wade
> **last_reviewed**: 2025-12-01
> **baseline**: SoT Freeze v2.6, Dev-Guides Freeze vFinal, ASDD 6-Layer v1.0

---

## 0. 文档元信息

| 属性 | 值 |
|------|-----|
| **文档标识** | `AUTOMATION_TEST_SPEC_v1.3.md` |
| **所属系统** | AI_ad_spend02 |
| **SoT 定位** | Layer 3 Dev-Guides 下位规范 |
| **Owner** | Testing SoT Owner（后端技术负责人） |
| **强制级别** | 新增测试 **MUST**；存量测试 **SHOULD** 逐步迁移 |

### v1.3 变更摘要

| 变更项 | 说明 |
|--------|------|
| 规范性增强 | 引入 RFC 2119 关键词（MUST/SHOULD/MAY） |
| SoT 路径精确化 | 所有引用使用 `docs/2.sot/<file>.md` 完整路径 |
| 示范测试用例 | 新增 DailyReport 8状态机完整测试示例 |
| Claude/Agent 协作 | 结构化提示语模板 + 审查清单 |
| CI/CD 配置 | GitHub Actions + pytest-cov 完整配置 |
| 覆盖率标准 | 新增最小覆盖率目标表 |

### 上游 SoT 依赖（完整路径）

本规范的测试用例设计 **MUST** 对齐以下权威文档：

| 优先级 | SoT 文档 | 路径 | 版本 | 用途 |
|--------|----------|------|------|------|
| P0 | STATE_MACHINE | `docs/2.sot/STATE_MACHINE.md` | v2.6 | 状态枚举、流转白名单、终态规则 |
| P0 | DATA_SCHEMA | `docs/2.sot/DATA_SCHEMA.md` | v5.2 | 数据结构、字段约束、CHECK 约束 |
| P1 | ERROR_CODES_SOT | `docs/2.sot/ERROR_CODES_SOT.md` | v2.1 | 错误码定义、响应格式校验 |
| P1 | LEDGER_SOT | `docs/2.sot/LEDGER_SOT.md` | v1.1 | 账本分录类型、余额计算规则 |
| P2 | DAILY_REPORT_SOT | `docs/2.sot/DAILY_REPORT_SOT.md` | v1.0 | 日报 8 状态机、粉数确认流程 |
| P2 | BUSINESS_RULES | `docs/2.sot/BUSINESS_RULES.md` | v3.1 | 业务约束、金额限制、风控规则 |
| P3 | AUTH_SPEC | `docs/2.sot/AUTH_SPEC.md` | v2.0 | 角色权限矩阵、访问控制规则 |

### 下游产物

- `backend/tests/**` 下的所有 pytest 测试代码
- `scripts/run_tests_ci.sh` CI 测试脚本
- `.github/workflows/test.yml` GitHub Actions 配置
- `htmlcov/` 覆盖率报告目录

---

## 1. 规范目的与适用范围

### 1.1 目的

本规范约束 AI_ad_spend02 的自动化测试体系，核心目标：

| # | 目标 | 说明 |
|---|------|------|
| 1 | **分层清晰** | 明确 L0/L1/L2/L3 测试层级的职责边界 |
| 2 | **规则可执行** | 开发者和 Agent 一眼知道「写到哪里、起什么名、加什么 marker」 |
| 3 | **SoT 对齐** | 所有测试用例 **MUST** 显式关联上游 SoT 文档 |
| 4 | **自动化友好** | 为 Claude / Agent 提供明确的生成规则和提示语模板 |

### 1.2 适用范围

| 范围 | 说明 |
|------|------|
| **代码仓库** | `AI_ad_spend02` |
| **技术栈** | FastAPI + SQLAlchemy 2.x + pytest 8.x |
| **测试目录** | `backend/tests/` |
| **约束强度** | 新增测试 **MUST** 遵守；存量测试 **SHOULD** 逐步迁移 |

> **不适用**：前端（Next.js）的纯前端单元测试（jest/rtl），但 **SHOULD** 保持命名风格一致。

### 1.3 目标角色

| 角色 | 职责 | 主要关注层级 |
|------|------|-------------|
| **Backend Developer** | 为新功能补齐测试 | L0/L1/L2 |
| **Test / QA Engineer** | 主导测试设计，维护 E2E 流程 | L2/L3 |
| **Claude / Agent** | 遵守本规范自动生成、修改、审查测试 | 所有层级 |

### 1.4 RFC 2119 关键词说明

本文档使用以下关键词表示要求级别：

| 关键词 | 含义 |
|--------|------|
| **MUST** | 绝对要求，必须遵守 |
| **MUST NOT** | 绝对禁止 |
| **SHOULD** | 推荐做法，有正当理由可例外 |
| **SHOULD NOT** | 不推荐做法 |
| **MAY** | 可选，根据情况选择 |

---

## 2. 测试层级模型

### 2.1 四层测试金字塔

```
        ┌─────────────┐
        │     L3      │  E2E / UI 自动化（少量，高价值场景）
        │   端到端    │  目标：<5% 测试用例
        ├─────────────┤
        │     L2      │  API 测试（核心业务流程）
        │   API 层    │  目标：~20% 测试用例
        ├─────────────┤
        │     L1      │  集成测试（组件协作）
        │   集成层    │  目标：~25% 测试用例
        ├─────────────┤
        │     L0      │  单元测试（大量，快速反馈）
        │   单元层    │  目标：~50% 测试用例
        └─────────────┘
```

### 2.2 层级定义与 pytest markers

| 层级 | 名称 | pytest marker | 目标 | 依赖 | 执行速度 |
|------|------|---------------|------|------|----------|
| **L0** | 单元测试 | `@pytest.mark.unit` | 验证单个函数/方法/类 | Mock，无外部依赖 | <10ms/case |
| **L1** | 集成测试 | `@pytest.mark.integration` | 验证 service + repository + DB | 测试数据库 | <100ms/case |
| **L2** | API 测试 | `@pytest.mark.api` | HTTP 入口验证完整链路 | TestClient + 测试库 | <500ms/case |
| **L3** | E2E 测试 | `@pytest.mark.e2e` | 用户视角完整业务流程 | 浏览器驱动 | <5s/case |

### 2.3 各层级详细说明

#### L0：单元测试（Unit Test）

```python
# 位置：backend/tests/unit/test_<module>.py
# marker：@pytest.mark.unit
# SoT 引用：通常无需，纯逻辑测试

@pytest.mark.unit
class TestUserValidator:
    """验证用户输入校验函数"""

    def test_valid_email__returns_true(self):
        """有效邮箱应返回 True"""
        assert validate_email("user@example.com") is True

    def test_invalid_email__raises_validation_error(self):
        """无效邮箱应抛出 ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_email("invalid-email")
        assert exc_info.value.code == "VALIDATION_010"  # ERROR_CODES_SOT
```

**L0 规则**：
- **MUST** 无外部依赖（数据库、网络、文件系统）
- **MUST** 使用 mock/stub 隔离依赖
- **SHOULD** 执行时间 < 10ms

#### L1：集成测试（Integration Test）

```python
# 位置：backend/tests/integration/test_<service>.py
# marker：@pytest.mark.integration
# SoT 引用：STATE_MACHINE.md

@pytest.mark.integration
class TestDailyReportStateHelper:
    """
    验证 DailyReportStateHelper 与数据库状态联动

    SoT 引用：
    - docs/2.sot/STATE_MACHINE.md v2.7 第8章 (DailyReport 8状态机)
    - docs/2.sot/LEDGER_SOT.md v1.2 (账本分录规则)
    """

    def test_submit_raw__transitions_to_trend_pending(self, db_session):
        """
        验证：raw_submitted → trend_pending 自动流转

        STATE_MACHINE.md 8.2 合法流转：
        "raw_submitted": ["trend_pending"]
        """
        # Arrange
        report = create_daily_report(db_session, status="raw_submitted")

        # Act
        helper = DailyReportStateHelper(db_session)
        result = helper.submit_raw(report.id)

        # Assert
        assert result.status == "trend_pending"
```

**L1 规则**：
- **MUST** 使用测试数据库（非生产库）
- **MUST** 在 docstring 中标注 SoT 引用
- **SHOULD** 每个测试函数独立事务，测试后回滚

#### L2：API 测试（API-level E2E）

```python
# 位置：backend/tests/api/test_<resource>_flow.py
# marker：@pytest.mark.api
# SoT 引用：STATE_MACHINE + ERROR_CODES_SOT + API_SOT

@pytest.mark.api
class TestDailyReportFlow:
    """
    日报完整 API 流程测试

    SoT 引用：
    - docs/2.sot/STATE_MACHINE.md v2.7 第8章 (DailyReport 8状态机)
    - docs/2.sot/ERROR_CODES_SOT.md v2.1 (STATE_* / BIZ_* 错误码)
    - docs/2.sot/API_SOT.md v9.3 (API 端点定义)
    """

    def test_daily_report_happy_path__raw_to_final_locked(
        self, client, media_buyer_token, data_operator_token
    ):
        """
        Happy Path: raw_submitted → ... → final_locked

        完整流程：
        1. 投手提交 raw (raw_submitted)
        2. 系统自动风控 (trend_pending → trend_ok)
        3. 运营录入 real_spend (final_pending)
        4. 运营确认 final (final_confirmed)
        5. 系统锁定 (final_locked)
        """
        # 1. 投手提交 raw
        resp = client.post(
            "/api/v1/daily-reports/",
            json={"ad_account_id": "...", "conversions_raw": 100, "raw_spend": 1000},
            headers=auth_header(media_buyer_token)
        )
        assert resp.status_code == 201
        report_id = resp.json()["data"]["id"]
        assert resp.json()["data"]["status"] == "raw_submitted"

        # ... (完整流程见第7章示范用例)
```

**L2 规则**：
- **MUST** 使用 FastAPI TestClient
- **MUST** 覆盖 Happy Path + 权限边界 + 错误码校验
- **MUST** 在 docstring 中标注完整 SoT 引用

#### L3：端到端测试（Full E2E / UI Automation）

```python
# 位置：backend/tests/e2e/test_<scenario>.py
# marker：@pytest.mark.e2e
# SoT 引用：完整业务流程 SoT

@pytest.mark.e2e
class TestDailyReportWorkflow:
    """
    媒体购买角色完整日报提交流程

    场景：登录 → 创建日报 → 提交 → 审核 → 锁定
    """

    def test_media_buyer_submits_daily_report(self, browser, test_user):
        """使用 Playwright 驱动浏览器完成完整用户流程"""
        page = browser.new_page()
        page.goto(f"{BASE_URL}/login")
        # ... 完整用户操作流程
```

**L3 规则**：
- **SHOULD** 仅覆盖核心用户旅程
- **MAY** 使用 Playwright / Selenium
- **MUST** 独立于 CI 快速流水线（按需运行）

---

## 3. 目录结构规范

### 3.1 标准目录布局

```
backend/
└── tests/
    ├── conftest.py           # 全局 pytest 配置 & 顶级 fixture
    ├── pytest.ini            # pytest 配置文件
    │
    ├── unit/                 # L0：单元测试
    │   ├── __init__.py
    │   ├── conftest.py       # L0 专用 fixture（可选）
    │   ├── test_validators.py
    │   ├── test_utils.py
    │   └── models/           # 模型单元测试
    │       ├── __init__.py
    │       └── test_user_model.py
    │
    ├── integration/          # L1：集成测试
    │   ├── __init__.py
    │   ├── conftest.py       # L1 专用 fixture（db_session 等）
    │   ├── test_daily_report_state_helper.py
    │   ├── test_topup_state_helper.py
    │   └── test_ledger_service.py
    │
    ├── api/                  # L2：API 层测试
    │   ├── __init__.py
    │   ├── conftest.py       # L2 专用 fixture（authenticated_client 等）
    │   ├── test_daily_report_flow.py
    │   ├── test_topup_flow.py
    │   ├── test_ledger_api.py
    │   └── test_auth_api.py
    │
    ├── e2e/                  # L3：端到端自动化（预留）
    │   ├── __init__.py
    │   ├── conftest.py       # E2E 专用 fixture（browser 等）
    │   ├── pages/            # Page Object 模式
    │   └── flows/            # 业务流程脚本
    │
    └── common/               # 公共工具
        ├── __init__.py
        ├── factories.py      # 测试数据工厂
        ├── api_client.py     # HTTP 客户端封装
        ├── state_asserts.py  # 状态机断言工具
        └── error_helpers.py  # 错误码校验工具
```

### 3.2 目录职责映射表

| 目录 | 层级 | 职责 | 文件命名模式 | conftest 内容 |
|------|------|------|-------------|--------------|
| `unit/` | L0 | 单元测试 | `test_<module>.py` | mock fixture |
| `integration/` | L1 | 集成测试 | `test_<service>_<helper>.py` | `db_session` |
| `api/` | L2 | API 测试 | `test_<resource>_flow.py` | `client`, `*_token` |
| `e2e/` | L3 | E2E 测试 | `test_<scenario>.py` | `browser` |
| `common/` | - | 公共工具 | `<功能>.py` | N/A |

### 3.3 存量测试迁移策略

对于现有零散的测试文件（如 `backend/tests/test_state_machine.py`）：

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | **识别层级** | 根据测试内容确定 L0/L1/L2/L3 |
| 2 | **移动文件** | 迁入对应子目录 |
| 3 | **添加 marker** | `@pytest.mark.<level>` |
| 4 | **补充 SoT 引用** | docstring 中标注 |
| 5 | **调整命名** | 符合 `test_<条件>__<预期>` |

> **过渡期规则**：存量测试 **MAY** 保留在根目录，但新增测试 **MUST** 放入正确子目录。

---

## 4. 命名规范

### 4.1 文件命名

| 类型 | 规范 | 示例 | 说明 |
|------|------|------|------|
| 测试文件 | `test_<模块/场景>.py` | `test_daily_report_flow.py` | **MUST** 以 `test_` 开头 |
| 公共模块 | `<功能>.py` | `factories.py` | **MUST NOT** 以 `test_` 开头 |
| conftest | `conftest.py` | 固定名称 | pytest 自动发现 |

### 4.2 类命名

| 规范 | 示例 | 说明 |
|------|------|------|
| `Test<模块/对象名>` | `TestUserCRUD` | 通用命名 |
| `Test<场景>Flow` | `TestTopupApprovalFlow` | 流程测试 |
| `Test<模块><状态机名>` | `TestDailyReportStateMachine` | 状态机测试 |

### 4.3 函数命名（核心规范）

**格式**：`test_<条件>__<预期结果>`

> **注意**：使用双下划线 `__` 分隔条件和预期，便于解析和搜索。

| 场景 | 命名模式 | 示例 |
|------|----------|------|
| 成功路径 | `test_<动作>__<成功结果>` | `test_create_user__success` |
| 失败路径 | `test_<条件>__raises_<异常>` | `test_invalid_email__raises_validation_error` |
| 状态流转 | `test_<动作>__status_becomes_<状态>` | `test_submit_raw__status_becomes_trend_pending` |
| 权限校验 | `test_<角色>_<动作>__returns_<状态码>` | `test_media_buyer_approve__returns_403` |
| 错误码校验 | `test_<条件>__returns_<错误码>` | `test_negative_amount__returns_BIZ_100` |

### 4.4 命名示例速查表

```python
# 文件：backend/tests/api/test_topup_flow.py

@pytest.mark.api
class TestTopupApprovalFlow:
    """
    充值审批流程 API 测试

    SoT 引用：
    - docs/2.sot/STATE_MACHINE.md v2.7 第10章 (TopupRequest 状态机)
    - docs/2.sot/ERROR_CODES_SOT.md v2.1 (BIZ_* 错误码)
    """

    # Happy path
    def test_submit_draft_topup__status_becomes_pending_review(self): ...

    # 权限边界
    def test_media_buyer_approves_topup__returns_403(self): ...

    # 状态机禁止流转
    def test_completed_topup_submit__returns_STATE_001(self): ...

    # 错误码校验
    def test_negative_amount__returns_BIZ_100(self): ...

    # 终态保护
    def test_modify_completed_topup__returns_STATE_100(self): ...
```

---

## 5. Fixture 与配置规范

### 5.1 conftest 分层架构

```
backend/tests/
├── conftest.py              # 全局 fixture（所有层共用）
├── unit/
│   └── conftest.py          # L0 专用（mock 工具）
├── integration/
│   └── conftest.py          # L1 专用（db_session）
├── api/
│   └── conftest.py          # L2 专用（authenticated_client）
└── e2e/
    └── conftest.py          # L3 专用（browser）
```

### 5.2 全局 conftest.py 模板

```python
# backend/tests/conftest.py
"""
全局 pytest 配置与公共 fixture

SoT 引用：
- docs/testing/AUTOMATION_TEST_SPEC_v1.3.md
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.models.base import Base
from backend.core.config import get_settings


# ============== 配置 Fixture ==============

@pytest.fixture(scope="session")
def test_settings():
    """测试环境配置（整个测试会话共享）"""
    settings = get_settings()
    assert "test" in settings.database_url, "MUST use test database"
    return settings


@pytest.fixture(scope="session")
def test_engine(test_settings):
    """测试数据库引擎（整个测试会话共享）"""
    engine = create_engine(
        test_settings.test_database_url,
        echo=False,
        pool_pre_ping=True
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine):
    """
    每个测试函数独立的数据库会话

    MUST: 测试后自动回滚，确保隔离性
    """
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


# ============== 应用 Fixture ==============

@pytest.fixture(scope="module")
def app_instance():
    """FastAPI 应用实例（测试模式）"""
    return app


@pytest.fixture(scope="function")
def client(app_instance, db_session):
    """
    FastAPI TestClient

    注意：每个测试函数获取新的 client 实例
    """
    # 依赖注入测试 db_session
    def override_get_db():
        yield db_session

    app_instance.dependency_overrides[get_db] = override_get_db
    with TestClient(app_instance) as c:
        yield c
    app_instance.dependency_overrides.clear()


# ============== pytest 配置 ==============

def pytest_configure(config):
    """注册自定义 markers"""
    config.addinivalue_line("markers", "unit: L0 单元测试")
    config.addinivalue_line("markers", "integration: L1 集成测试")
    config.addinivalue_line("markers", "api: L2 API 测试")
    config.addinivalue_line("markers", "e2e: L3 端到端自动化测试")
    config.addinivalue_line("markers", "slow: 执行时间 > 1s 的测试")
```

### 5.3 pytest.ini 配置

```ini
# backend/tests/pytest.ini

[pytest]
testpaths = backend/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# 注册 markers
markers =
    unit: L0 单元测试（无外部依赖）
    integration: L1 集成测试（需要测试数据库）
    api: L2 API 测试（需要 TestClient）
    e2e: L3 端到端自动化测试（需要浏览器）
    slow: 执行时间超过 1 秒的测试

# 默认选项
addopts =
    -v
    --tb=short
    --strict-markers
    -W ignore::DeprecationWarning

# 异步支持
asyncio_mode = auto

# 日志配置
log_cli = true
log_cli_level = WARNING

# 并行执行（需要 pytest-xdist）
# addopts = -n auto
```

### 5.4 层级专用 fixture 示例

```python
# backend/tests/api/conftest.py
"""
L2 API 测试专用 fixture

SoT 引用：
- docs/2.sot/AUTH_SPEC.md v2.0 (角色定义)
"""

import pytest
from backend.tests.common.factories import create_user


@pytest.fixture
def admin_user(db_session):
    """创建管理员用户"""
    return create_user(db_session, role="admin")


@pytest.fixture
def media_buyer_user(db_session):
    """创建投手用户"""
    return create_user(db_session, role="media_buyer")


@pytest.fixture
def data_operator_user(db_session):
    """创建数据员用户"""
    return create_user(db_session, role="data_operator")


@pytest.fixture
def finance_user(db_session):
    """创建财务用户"""
    return create_user(db_session, role="finance")


@pytest.fixture
def admin_token(admin_user, client):
    """获取管理员认证 token"""
    resp = client.post("/api/v1/auth/login", json={
        "email": admin_user.email,
        "password": "test_password_123"
    })
    assert resp.status_code == 200, f"Login failed: {resp.json()}"
    return resp.json()["data"]["access_token"]


@pytest.fixture
def media_buyer_token(media_buyer_user, client):
    """获取投手认证 token"""
    resp = client.post("/api/v1/auth/login", json={
        "email": media_buyer_user.email,
        "password": "test_password_123"
    })
    return resp.json()["data"]["access_token"]


@pytest.fixture
def data_operator_token(data_operator_user, client):
    """获取数据员认证 token"""
    resp = client.post("/api/v1/auth/login", json={
        "email": data_operator_user.email,
        "password": "test_password_123"
    })
    return resp.json()["data"]["access_token"]


def auth_header(token: str) -> dict:
    """构造认证请求头"""
    return {"Authorization": f"Bearer {token}"}
```

---

## 6. 公共工具规范（common/）

### 6.1 模块职责映射

| 模块 | 职责 | SoT 对齐 |
|------|------|----------|
| `factories.py` | 测试数据构造 | DATA_SCHEMA.md |
| `api_client.py` | HTTP 客户端封装 | API_SOT.md |
| `state_asserts.py` | 状态机断言工具 | STATE_MACHINE.md |
| `error_helpers.py` | 错误码校验工具 | ERROR_CODES_SOT.md |

### 6.2 factories.py 完整示例

```python
# backend/tests/common/factories.py
"""
测试数据工厂

SoT 引用：
- docs/2.sot/DATA_SCHEMA.md v5.3 (字段定义)
- docs/2.sot/STATE_MACHINE.md v2.7 (初始状态)
"""

from uuid import uuid4
from decimal import Decimal
from datetime import date
from typing import Optional

from backend.models import User, Project, DailyReport, TopupRequest
from backend.models.enums import UserRole


def create_user(
    db_session,
    role: str = "media_buyer",
    email: Optional[str] = None,
    **kwargs
) -> User:
    """
    创建测试用户

    Args:
        db_session: 数据库会话
        role: 角色（admin/finance/data_operator/account_manager/media_buyer）
        email: 邮箱（默认自动生成）

    Returns:
        User: 创建的用户实例

    SoT 引用：AUTH_SPEC.md v2.0 第2章 (角色定义)
    """
    defaults = {
        "id": uuid4(),
        "email": email or f"test_{uuid4().hex[:8]}@example.com",
        "username": f"user_{uuid4().hex[:8]}",
        "hashed_password": "$2b$12$test_hash",  # 对应密码: test_password_123
        "role": role,
        "is_active": True,
    }
    defaults.update(kwargs)
    user = User(**defaults)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_daily_report(
    db_session,
    user: User,
    status: str = "raw_submitted",
    report_date: Optional[date] = None,
    **kwargs
) -> DailyReport:
    """
    创建测试日报

    Args:
        db_session: 数据库会话
        user: 关联用户
        status: 初始状态（默认 raw_submitted）
        report_date: 日报日期（默认今天）

    Returns:
        DailyReport: 创建的日报实例

    SoT 引用：
    - STATE_MACHINE.md v2.7 第8章 (DailyReport 8状态机)
    - DATA_SCHEMA.md v5.3 (daily_reports 表结构)
    """
    defaults = {
        "id": uuid4(),
        "ad_account_id": uuid4(),
        "report_date": report_date or date.today(),
        "status": status,
        "conversions_raw": 100,
        "raw_spend": Decimal("1000.00"),
        "conversions_final": None,
        "real_spend": None,
        "created_by": user.id,
    }
    defaults.update(kwargs)
    report = DailyReport(**defaults)
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)
    return report


def create_topup_request(
    db_session,
    user: User,
    status: str = "draft",
    amount: Decimal = Decimal("1000.00"),
    **kwargs
) -> TopupRequest:
    """
    创建测试充值申请

    Args:
        db_session: 数据库会话
        user: 关联用户
        status: 初始状态（默认 draft）
        amount: 充值金额

    Returns:
        TopupRequest: 创建的充值申请实例

    SoT 引用：
    - STATE_MACHINE.md v2.7 第10章 (TopupRequest 状态机)
    - BUSINESS_RULES.md v4.1 (金额限制)
    """
    defaults = {
        "id": uuid4(),
        "ad_account_id": uuid4(),
        "amount": amount,
        "status": status,
        "created_by": user.id,
    }
    defaults.update(kwargs)
    topup = TopupRequest(**defaults)
    db_session.add(topup)
    db_session.commit()
    db_session.refresh(topup)
    return topup
```

### 6.3 state_asserts.py 完整示例

```python
# backend/tests/common/state_asserts.py
"""
状态机断言工具

SoT 引用：
- docs/2.sot/STATE_MACHINE.md v2.7 (状态流转规则)
"""

from typing import Optional


# 合法流转白名单（同步自 STATE_MACHINE.md v2.7 第14.5章）
DAILY_REPORT_TRANSITIONS = {
    "raw_submitted": ["trend_pending"],
    "trend_pending": ["trend_ok", "trend_flagged"],
    "trend_ok": ["final_pending"],
    "trend_flagged": ["trend_resolved", "raw_submitted"],
    "trend_resolved": ["final_pending"],
    "final_pending": ["final_confirmed"],
    "final_confirmed": ["final_locked"],
    "final_locked": [],  # 终态
}

TOPUP_REQUEST_TRANSITIONS = {
    "draft": ["pending_review", "cancelled"],
    "pending_review": ["finance_approve", "rejected"],
    "finance_approve": ["paid", "rejected"],
    "paid": ["completed"],
    "completed": [],  # 终态
    "rejected": [],   # 终态
    "cancelled": [],  # 终态
}


def assert_status_transition(
    entity,
    expected_status: str,
    sot_ref: Optional[str] = None
):
    """
    断言实体状态符合预期

    Args:
        entity: 数据库实体（必须有 status 属性）
        expected_status: 预期状态
        sot_ref: SoT 引用（用于错误消息）

    Raises:
        AssertionError: 状态不符时抛出

    Example:
        assert_status_transition(
            report, "trend_pending",
            sot_ref="STATE_MACHINE.md 8.2"
        )
    """
    actual = entity.status
    ref_msg = f" (SOT: {sot_ref})" if sot_ref else ""
    assert actual == expected_status, (
        f"状态不符: 预期 '{expected_status}', 实际 '{actual}'{ref_msg}"
    )


def assert_valid_transition(
    entity_type: str,
    from_status: str,
    to_status: str
):
    """
    断言状态流转在白名单内

    Args:
        entity_type: 实体类型（daily_report / topup_request）
        from_status: 原状态
        to_status: 目标状态

    Raises:
        AssertionError: 非法流转时抛出
    """
    transitions = {
        "daily_report": DAILY_REPORT_TRANSITIONS,
        "topup_request": TOPUP_REQUEST_TRANSITIONS,
    }

    whitelist = transitions.get(entity_type, {})
    allowed = whitelist.get(from_status, [])

    assert to_status in allowed, (
        f"非法状态流转: {entity_type} 从 '{from_status}' 到 '{to_status}' "
        f"(允许: {allowed}). 参考 STATE_MACHINE.md 第14.5章"
    )


def assert_terminal_state(entity, entity_type: str):
    """
    断言实体处于终态

    Args:
        entity: 数据库实体
        entity_type: 实体类型

    Raises:
        AssertionError: 非终态时抛出
    """
    transitions = {
        "daily_report": DAILY_REPORT_TRANSITIONS,
        "topup_request": TOPUP_REQUEST_TRANSITIONS,
    }

    whitelist = transitions.get(entity_type, {})
    allowed_next = whitelist.get(entity.status, None)

    assert allowed_next == [], (
        f"预期终态，但 {entity_type}.status='{entity.status}' 仍可流转至 {allowed_next}"
    )
```

### 6.4 error_helpers.py 完整示例

```python
# backend/tests/common/error_helpers.py
"""
错误码校验工具

SoT 引用：
- docs/2.sot/ERROR_CODES_SOT.md v2.1 (错误码定义)
"""

from typing import Optional


def assert_error_response(
    response,
    expected_code: str,
    expected_http_status: int,
    message_contains: Optional[str] = None
):
    """
    断言错误响应符合 ERROR_CODES_SOT

    Args:
        response: FastAPI TestClient 响应对象
        expected_code: 预期错误码（如 "AUTH_001", "BIZ_100"）
        expected_http_status: 预期 HTTP 状态码
        message_contains: 错误消息应包含的文本（可选）

    Example:
        assert_error_response(
            resp,
            expected_code="STATE_001",
            expected_http_status=400,
            message_contains="invalid transition"
        )
    """
    # 校验 HTTP 状态码
    assert response.status_code == expected_http_status, (
        f"HTTP 状态码不符: 预期 {expected_http_status}, "
        f"实际 {response.status_code}. 响应: {response.json()}"
    )

    # 校验响应结构（ERROR_CODES_SOT.md 1.3 Envelope 格式）
    data = response.json()
    assert data.get("success") is False, "错误响应的 success 字段应为 false"
    assert "code" in data, "错误响应缺少 code 字段"

    # 校验错误码
    actual_code = data["code"]
    assert actual_code == expected_code, (
        f"错误码不符: 预期 '{expected_code}', 实际 '{actual_code}'"
    )

    # 校验错误消息（可选）
    if message_contains:
        message = data.get("message", "")
        assert message_contains.lower() in message.lower(), (
            f"错误消息应包含 '{message_contains}', 实际: '{message}'"
        )


def assert_success_response(response, expected_http_status: int = 200):
    """
    断言成功响应

    Args:
        response: FastAPI TestClient 响应对象
        expected_http_status: 预期 HTTP 状态码（默认 200）
    """
    assert response.status_code == expected_http_status, (
        f"HTTP 状态码不符: 预期 {expected_http_status}, "
        f"实际 {response.status_code}. 响应: {response.json()}"
    )

    data = response.json()
    assert data.get("success") is True, (
        f"成功响应的 success 字段应为 true, 实际: {data}"
    )
```

### 6.5 使用约束

| 规则 | 级别 | 说明 |
|------|------|------|
| 优先使用 common/ 工具 | **MUST** | 新增测试 **MUST** 优先使用已有工厂和断言 |
| 禁止 ad-hoc 工厂 | **SHOULD NOT** | 避免在测试文件内临时创建工厂函数 |
| 扩展前先检查 | **MUST** | 如需新工厂，**MUST** 先补充到 common/ |

---

## 7. 示范性测试用例（DailyReport 8状态机）

### 7.1 完整 L2 API 测试示例

```python
# backend/tests/api/test_daily_report_flow.py
"""
日报（DailyReport）完整 API 流程测试

SoT 引用：
- docs/2.sot/STATE_MACHINE.md v2.7 第8章 (DailyReport 8状态机)
- docs/2.sot/ERROR_CODES_SOT.md v2.1 (STATE_* / BIZ_* / TREND_* 错误码)
- docs/2.sot/DAILY_REPORT_SOT.md v1.0 (粉数确认业务规则)
- docs/2.sot/AUTH_SPEC.md v2.0 (角色权限矩阵)

测试覆盖：
- Happy Path: raw_submitted → ... → final_locked
- 权限边界: 各角色操作权限校验
- 状态机禁止: 非法流转校验
- 趋势风控: TF-001/002/003 触发与解决
- 错误码校验: 对齐 ERROR_CODES_SOT
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta

from backend.tests.common.factories import create_user, create_daily_report
from backend.tests.common.state_asserts import (
    assert_status_transition,
    assert_valid_transition,
    assert_terminal_state
)
from backend.tests.common.error_helpers import (
    assert_error_response,
    assert_success_response
)
from backend.tests.api.conftest import auth_header


@pytest.mark.api
class TestDailyReportHappyPath:
    """
    Happy Path: 完整状态流转测试

    流程：raw_submitted → trend_pending → trend_ok
          → final_pending → final_confirmed → final_locked
    """

    def test_full_flow__raw_to_final_locked(
        self,
        client,
        db_session,
        media_buyer_token,
        data_operator_token
    ):
        """
        完整 Happy Path 测试

        角色操作：
        1. 投手(media_buyer) 提交 raw
        2. 系统自动风控检查 → trend_ok
        3. 运营(data_operator) 录入 real_spend → final_pending
        4. 运营(data_operator) 确认 final → final_confirmed
        5. 系统自动锁定 → final_locked
        """
        # ========== Step 1: 投手提交 raw ==========
        resp = client.post(
            "/api/v1/daily-reports/",
            json={
                "ad_account_id": "test-account-001",
                "report_date": str(date.today()),
                "conversions_raw": 100,
                "raw_spend": "1000.00"
            },
            headers=auth_header(media_buyer_token)
        )
        assert_success_response(resp, 201)
        report_id = resp.json()["data"]["id"]
        assert resp.json()["data"]["status"] == "raw_submitted"

        # ========== Step 2: 系统自动风控 → trend_ok ==========
        # 触发风控检查（模拟定时任务）
        resp = client.post(
            f"/api/v1/daily-reports/{report_id}/trigger-trend-check",
            headers=auth_header(data_operator_token)  # 系统内部调用
        )
        assert_success_response(resp)

        # 验证状态流转
        resp = client.get(
            f"/api/v1/daily-reports/{report_id}",
            headers=auth_header(media_buyer_token)
        )
        # 假设风控通过（无异常数据）
        status = resp.json()["data"]["status"]
        assert status in ["trend_pending", "trend_ok"], (
            f"风控检查后状态应为 trend_pending 或 trend_ok, 实际: {status}"
        )

        # 如果是 trend_pending，等待自动流转
        if status == "trend_pending":
            # 模拟风控通过
            resp = client.post(
                f"/api/v1/daily-reports/{report_id}/complete-trend-check",
                json={"result": "ok"},
                headers=auth_header(data_operator_token)
            )
            assert_success_response(resp)

        # ========== Step 3: 运营录入 real_spend → final_pending ==========
        resp = client.post(
            f"/api/v1/daily-reports/{report_id}/input-real-spend",
            json={
                "real_spend": "980.00",
                "conversions_final": 95
            },
            headers=auth_header(data_operator_token)
        )
        assert_success_response(resp)
        assert resp.json()["data"]["status"] == "final_pending"

        # ========== Step 4: 运营确认 final → final_confirmed ==========
        resp = client.post(
            f"/api/v1/daily-reports/{report_id}/confirm-final",
            headers=auth_header(data_operator_token)
        )
        assert_success_response(resp)
        assert resp.json()["data"]["status"] == "final_confirmed"

        # ========== Step 5: 系统锁定 → final_locked ==========
        resp = client.post(
            f"/api/v1/daily-reports/{report_id}/lock",
            headers=auth_header(data_operator_token)  # 系统内部调用
        )
        assert_success_response(resp)
        assert resp.json()["data"]["status"] == "final_locked"


@pytest.mark.api
class TestDailyReportPermissions:
    """
    权限边界测试

    SoT 引用：AUTH_SPEC.md v2.0 第3章 (权限矩阵)

    规则：
    - 投手(media_buyer): 只能提交 raw
    - 运营(data_operator): 可以录入 real_spend、确认 final
    - 管理员(admin): 可以执行所有操作
    """

    def test_media_buyer_input_real_spend__returns_403(
        self,
        client,
        db_session,
        media_buyer_token,
        data_operator_user
    ):
        """
        投手不能录入 real_spend

        预期：返回 AUTH_501 权限不足
        """
        # 创建已通过风控的日报
        report = create_daily_report(
            db_session,
            user=data_operator_user,
            status="trend_ok"
        )

        resp = client.post(
            f"/api/v1/daily-reports/{report.id}/input-real-spend",
            json={"real_spend": "980.00", "conversions_final": 95},
            headers=auth_header(media_buyer_token)
        )

        assert_error_response(
            resp,
            expected_code="AUTH_501",
            expected_http_status=403,
            message_contains="permission denied"
        )

    def test_data_operator_submit_raw__returns_403(
        self,
        client,
        db_session,
        data_operator_token,
        media_buyer_user
    ):
        """
        运营不能提交 raw（应由投手提交）

        预期：返回 AUTH_501 权限不足
        """
        resp = client.post(
            "/api/v1/daily-reports/",
            json={
                "ad_account_id": "test-account-001",
                "report_date": str(date.today()),
                "conversions_raw": 100,
                "raw_spend": "1000.00"
            },
            headers=auth_header(data_operator_token)
        )

        assert_error_response(
            resp,
            expected_code="AUTH_501",
            expected_http_status=403
        )


@pytest.mark.api
class TestDailyReportStateMachineViolations:
    """
    状态机非法流转测试

    SoT 引用：STATE_MACHINE.md v2.7 第8.2章 (合法流转白名单)
    """

    def test_raw_submitted_to_final_pending__returns_STATE_001(
        self,
        client,
        db_session,
        data_operator_token,
        media_buyer_user
    ):
        """
        非法流转：raw_submitted 直接跳到 final_pending

        白名单：raw_submitted → [trend_pending] (仅此一个合法流转)
        预期：返回 STATE_001 非法状态流转
        """
        report = create_daily_report(
            db_session,
            user=media_buyer_user,
            status="raw_submitted"
        )

        resp = client.post(
            f"/api/v1/daily-reports/{report.id}/input-real-spend",
            json={"real_spend": "980.00", "conversions_final": 95},
            headers=auth_header(data_operator_token)
        )

        assert_error_response(
            resp,
            expected_code="STATE_001",
            expected_http_status=400,
            message_contains="invalid transition"
        )

    def test_final_locked_modification__returns_STATE_100(
        self,
        client,
        db_session,
        admin_token,
        media_buyer_user
    ):
        """
        终态保护：final_locked 不允许任何修改

        白名单：final_locked → [] (终态，无合法流转)
        预期：返回 STATE_100 终态保护
        """
        report = create_daily_report(
            db_session,
            user=media_buyer_user,
            status="final_locked"
        )

        resp = client.patch(
            f"/api/v1/daily-reports/{report.id}",
            json={"conversions_final": 999},
            headers=auth_header(admin_token)
        )

        assert_error_response(
            resp,
            expected_code="STATE_100",
            expected_http_status=403,
            message_contains="terminal state"
        )


@pytest.mark.api
class TestDailyReportTrendRiskControl:
    """
    趋势风控测试

    SoT 引用：
    - STATE_MACHINE.md v2.7 第8.3章 (趋势风控规则 TF-001/002/003)
    - ERROR_CODES_SOT.md v2.1 (TREND_* 错误码)
    """

    def test_conversions_drop_50_percent__triggers_TF_001(
        self,
        client,
        db_session,
        media_buyer_token,
        data_operator_token,
        media_buyer_user
    ):
        """
        TF-001: 粉数骤降检查

        规则：conversions_raw < 昨日最大值 × 0.5 → trend_flagged
        """
        # 创建昨日日报（粉数 200）
        yesterday = date.today() - timedelta(days=1)
        create_daily_report(
            db_session,
            user=media_buyer_user,
            report_date=yesterday,
            status="final_locked",
            conversions_raw=200,
            conversions_final=200
        )

        # 今日提交粉数 80（下降 60%，触发 TF-001）
        resp = client.post(
            "/api/v1/daily-reports/",
            json={
                "ad_account_id": "test-account-001",
                "report_date": str(date.today()),
                "conversions_raw": 80,  # < 200 × 0.5 = 100
                "raw_spend": "800.00"
            },
            headers=auth_header(media_buyer_token)
        )
        assert_success_response(resp, 201)
        report_id = resp.json()["data"]["id"]

        # 触发风控检查
        resp = client.post(
            f"/api/v1/daily-reports/{report_id}/trigger-trend-check",
            headers=auth_header(data_operator_token)
        )

        # 验证触发 trend_flagged
        resp = client.get(
            f"/api/v1/daily-reports/{report_id}",
            headers=auth_header(media_buyer_token)
        )
        data = resp.json()["data"]
        assert data["status"] == "trend_flagged"
        assert "TF-001" in data.get("trend_flag_reason", "")

    def test_trend_flagged_resolve__transitions_to_trend_resolved(
        self,
        client,
        db_session,
        data_operator_token,
        media_buyer_user
    ):
        """
        trend_flagged → trend_resolved (运营确认异常已解决)
        """
        report = create_daily_report(
            db_session,
            user=media_buyer_user,
            status="trend_flagged"
        )

        resp = client.post(
            f"/api/v1/daily-reports/{report.id}/resolve-trend",
            json={"resolution_note": "已与投手确认，数据正常"},
            headers=auth_header(data_operator_token)
        )

        assert_success_response(resp)
        assert resp.json()["data"]["status"] == "trend_resolved"


@pytest.mark.api
class TestDailyReportErrorCodes:
    """
    错误码校验测试

    SoT 引用：ERROR_CODES_SOT.md v2.1
    """

    def test_negative_raw_spend__returns_BIZ_100(
        self,
        client,
        media_buyer_token
    ):
        """
        负数金额校验

        预期：返回 BIZ_100 金额必须为正数
        """
        resp = client.post(
            "/api/v1/daily-reports/",
            json={
                "ad_account_id": "test-account-001",
                "report_date": str(date.today()),
                "conversions_raw": 100,
                "raw_spend": "-1000.00"  # 负数
            },
            headers=auth_header(media_buyer_token)
        )

        assert_error_response(
            resp,
            expected_code="BIZ_100",
            expected_http_status=400,
            message_contains="positive"
        )

    def test_missing_required_field__returns_VALIDATION_001(
        self,
        client,
        media_buyer_token
    ):
        """
        缺少必填字段

        预期：返回 VALIDATION_001 必填字段缺失
        """
        resp = client.post(
            "/api/v1/daily-reports/",
            json={
                "ad_account_id": "test-account-001",
                # 缺少 report_date, conversions_raw, raw_spend
            },
            headers=auth_header(media_buyer_token)
        )

        assert_error_response(
            resp,
            expected_code="VALIDATION_001",
            expected_http_status=400
        )

    def test_duplicate_report__returns_BIZ_001(
        self,
        client,
        db_session,
        media_buyer_token,
        media_buyer_user
    ):
        """
        重复提交同一天日报

        预期：返回 BIZ_001 重复记录
        """
        # 创建已存在的日报
        create_daily_report(
            db_session,
            user=media_buyer_user,
            report_date=date.today(),
            status="raw_submitted"
        )

        # 再次提交同一天
        resp = client.post(
            "/api/v1/daily-reports/",
            json={
                "ad_account_id": "test-account-001",
                "report_date": str(date.today()),
                "conversions_raw": 100,
                "raw_spend": "1000.00"
            },
            headers=auth_header(media_buyer_token)
        )

        assert_error_response(
            resp,
            expected_code="BIZ_001",
            expected_http_status=409,
            message_contains="duplicate"
        )
```

### 7.2 测试覆盖清单

| 测试类 | 场景类型 | 用例数 | SoT 引用 |
|--------|----------|--------|----------|
| `TestDailyReportHappyPath` | Happy Path | 1 | STATE_MACHINE 8.2 |
| `TestDailyReportPermissions` | 权限边界 | 2 | AUTH_SPEC 3 |
| `TestDailyReportStateMachineViolations` | 状态机禁止 | 2 | STATE_MACHINE 8.2 |
| `TestDailyReportTrendRiskControl` | 趋势风控 | 2 | STATE_MACHINE 8.3 |
| `TestDailyReportErrorCodes` | 错误码校验 | 3 | ERROR_CODES_SOT |

---

## 8. 运行命令规范

### 8.1 标准命令集

| 场景 | 命令 | 说明 |
|------|------|------|
| **全量测试** | `pytest backend/tests` | 运行所有测试 |
| **单元测试** | `pytest -m unit` | 仅 L0 |
| **集成测试** | `pytest -m integration` | 仅 L1 |
| **API 测试** | `pytest -m api` | 仅 L2 |
| **E2E 测试** | `pytest -m e2e` | 仅 L3 |
| **快速 CI** | `pytest -m "not e2e"` | 排除 E2E |
| **带覆盖率** | `pytest --cov=backend --cov-report=html` | 生成覆盖率报告 |
| **并行执行** | `pytest -n auto` | 使用 pytest-xdist |

### 8.2 CI 脚本（run_tests_ci.sh）

```bash
#!/bin/bash
# scripts/run_tests_ci.sh
#
# CI 测试脚本
# 用法: ./scripts/run_tests_ci.sh [--full | --quick | --coverage]

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_step() {
    echo -e "${GREEN}=== $1 ===${NC}"
}

echo_warn() {
    echo -e "${YELLOW}WARNING: $1${NC}"
}

echo_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

# 默认模式
MODE="${1:-quick}"

case $MODE in
    --full)
        echo_step "Running Full Test Suite (L0 + L1 + L2 + L3)"
        pytest backend/tests -v --tb=short
        ;;

    --quick)
        echo_step "Running Quick Test Suite (L0 + L1 + L2, excluding E2E)"

        echo_step "L0: Unit Tests"
        pytest backend/tests/unit -m unit --tb=short -q

        echo_step "L1: Integration Tests"
        pytest backend/tests/integration -m integration --tb=short -q

        echo_step "L2: API Tests"
        pytest backend/tests/api -m api --tb=short -q
        ;;

    --coverage)
        echo_step "Running Tests with Coverage Report"
        pytest backend/tests \
            -m "not e2e" \
            --cov=backend \
            --cov-report=html \
            --cov-report=xml \
            --cov-report=term-missing \
            --cov-fail-under=70

        echo_step "Coverage report generated: htmlcov/index.html"
        ;;

    *)
        echo_error "Unknown mode: $MODE"
        echo "Usage: $0 [--full | --quick | --coverage]"
        exit 1
        ;;
esac

echo_step "All Tests Passed!"
```

### 8.3 GitHub Actions 配置

```yaml
# .github/workflows/test.yml

name: Test Suite

on:
  push:
    branches: [main, develop]
    paths:
      - 'backend/**'
      - 'tests/**'
      - '.github/workflows/test.yml'
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: '3.11'
  POETRY_VERSION: '1.7.1'

jobs:
  unit-tests:
    name: L0 Unit Tests
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          pip install poetry==${{ env.POETRY_VERSION }}
          poetry install --with dev

      - name: Run unit tests
        run: |
          poetry run pytest backend/tests/unit -m unit \
            --tb=short \
            --junitxml=junit/unit-results.xml

      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: unit-test-results
          path: junit/unit-results.xml

  integration-tests:
    name: L1 Integration Tests
    runs-on: ubuntu-latest
    needs: unit-tests

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          pip install poetry==${{ env.POETRY_VERSION }}
          poetry install --with dev

      - name: Run integration tests
        env:
          TEST_DATABASE_URL: postgresql://test:test@localhost:5432/test_db
        run: |
          poetry run pytest backend/tests/integration -m integration \
            --tb=short \
            --junitxml=junit/integration-results.xml

      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: integration-test-results
          path: junit/integration-results.xml

  api-tests:
    name: L2 API Tests
    runs-on: ubuntu-latest
    needs: integration-tests

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          pip install poetry==${{ env.POETRY_VERSION }}
          poetry install --with dev

      - name: Run API tests
        env:
          TEST_DATABASE_URL: postgresql://test:test@localhost:5432/test_db
        run: |
          poetry run pytest backend/tests/api -m api \
            --tb=short \
            --junitxml=junit/api-results.xml

      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: api-test-results
          path: junit/api-results.xml

  coverage:
    name: Coverage Report
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests, api-tests]

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          pip install poetry==${{ env.POETRY_VERSION }}
          poetry install --with dev

      - name: Run tests with coverage
        env:
          TEST_DATABASE_URL: postgresql://test:test@localhost:5432/test_db
        run: |
          poetry run pytest backend/tests -m "not e2e" \
            --cov=backend \
            --cov-report=xml \
            --cov-report=html \
            --cov-fail-under=70

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          fail_ci_if_error: true

      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: htmlcov/
```

### 8.4 最小覆盖率目标

| 层级 | 目标覆盖率 | 说明 |
|------|-----------|------|
| **L0 Unit** | 80% | 核心业务逻辑 |
| **L1 Integration** | 70% | 状态机流转 |
| **L2 API** | 60% | 核心 API 端点 |
| **Overall** | 70% | CI 阻断阈值 |

---

## 9. Claude / Agent 协作规范

### 9.1 总则

| 规则 | 级别 | 说明 |
|------|------|------|
| 遵守目录规范 | **MUST** | 测试 **MUST** 放在指定目录 |
| 使用正确 marker | **MUST** | **MUST** 添加对应层级的 marker |
| 引用 SoT 文档 | **MUST** | docstring 中 **MUST** 标注 SoT 引用 |
| 使用 common/ 工具 | **SHOULD** | **SHOULD** 优先使用已有工厂和断言 |

### 9.2 任务类型速查表

| 任务类型 | 目录 | Marker | 必须引用的 SoT |
|----------|------|--------|---------------|
| 补单元测试 (L0) | `backend/tests/unit/` | `@pytest.mark.unit` | 无（纯逻辑） |
| 补集成测试 (L1) | `backend/tests/integration/` | `@pytest.mark.integration` | STATE_MACHINE |
| 补 API 测试 (L2) | `backend/tests/api/` | `@pytest.mark.api` | STATE_MACHINE + ERROR_CODES |
| 补 E2E 测试 (L3) | `backend/tests/e2e/` | `@pytest.mark.e2e` | 完整业务流程 SoT |
| 补公共工具 | `backend/tests/common/` | 无 marker | 按功能确定 |

### 9.3 结构化提示语模板

#### 生成 L2 API 测试

```markdown
## 任务：为 [模块名] 生成 L2 API 测试

### 输入
- 目标模块: [模块名，如 topup_request]
- 状态机定义: docs/2.sot/STATE_MACHINE.md 第[X]章
- 错误码定义: docs/2.sot/ERROR_CODES_SOT.md

### 输出要求
1. 文件位置: backend/tests/api/test_[模块名]_flow.py
2. 必须包含的测试类:
   - Test[模块名]HappyPath: 成功流程
   - Test[模块名]Permissions: 权限边界
   - Test[模块名]StateMachineViolations: 非法流转
   - Test[模块名]ErrorCodes: 错误码校验
3. 每个测试类必须有 SoT 引用的 docstring
4. 使用 common/ 内的 factories 和断言工具
5. 添加 @pytest.mark.api marker
```

#### 审查现有测试

```markdown
## 任务：审查 [文件路径] 测试文件

### 审查清单
- [ ] 是否有正确的 pytest marker (unit/integration/api/e2e)
- [ ] 文件命名是否符合 test_<模块>.py 规范
- [ ] 类命名是否符合 Test<模块> 规范
- [ ] 函数命名是否符合 test_<条件>__<预期> 规范
- [ ] 是否在 docstring 中引用了 SoT 文档
- [ ] 是否覆盖了必须的测试场景:
  - [ ] Happy Path
  - [ ] 权限边界
  - [ ] 状态机非法流转
  - [ ] 错误码校验
- [ ] 是否使用了 common/ 内的工具

### 输出格式
```text
## 审查报告: [文件名]

### 符合规范
- [列出符合的项]

### 需要修改
- [列出需要修改的项及修改建议]

### 修改优先级
- P0 (阻塞): [...]
- P1 (应修): [...]
- P2 (建议): [...]
```
```

#### 迁移存量测试

```markdown
## 任务：迁移 [旧文件路径] 到规范目录

### 迁移步骤
1. 分析测试内容，确定层级 (L0/L1/L2/L3)
2. 移动到对应子目录
3. 添加正确的 pytest marker
4. 补充 SoT 引用到 docstring
5. 调整命名符合 test_<条件>__<预期> 规范
6. 验证测试仍能通过

### 输出
- 新文件路径
- 添加的 marker
- SoT 引用
- 命名调整清单
```

### 9.4 审查清单（Checklist）

**生成测试前**：
- [ ] 确认目标层级 (L0/L1/L2/L3)
- [ ] 查阅对应 SoT 文档
- [ ] 检查 common/ 是否有可复用的工厂/断言

**生成测试后**：
- [ ] 文件在正确目录
- [ ] 有正确的 pytest marker
- [ ] docstring 包含 SoT 引用
- [ ] 命名符合规范
- [ ] 使用了 common/ 工具
- [ ] 覆盖了必须的测试场景

---

## 10. 最小落地检查清单

### 10.1 v1.3 必须完成项

- [ ] **目录结构搭建完成**
  - [ ] `backend/tests/unit/`
  - [ ] `backend/tests/integration/`
  - [ ] `backend/tests/api/`
  - [ ] `backend/tests/e2e/`
  - [ ] `backend/tests/common/`

- [ ] **pytest 配置完成**
  - [ ] `pytest.ini` 注册 markers: `unit` / `integration` / `api` / `e2e`
  - [ ] 全局 `conftest.py` 包含基础 fixture
  - [ ] `--strict-markers` 启用

- [ ] **公共工具模块**
  - [ ] `common/factories.py` 包含 User / DailyReport / TopupRequest 工厂
  - [ ] `common/state_asserts.py` 包含状态流转断言
  - [ ] `common/error_helpers.py` 包含错误码校验

- [ ] **示范性 L2 测试**
  - [ ] DailyReport 完整流程测试 (Happy Path + 权限 + 状态机 + 错误码)
  - [ ] docstring 中写明 SoT 引用

- [ ] **CI/CD 配置**
  - [ ] `scripts/run_tests_ci.sh` 脚本
  - [ ] `.github/workflows/test.yml` 配置
  - [ ] 覆盖率阈值 70% 配置

### 10.2 验收命令

```bash
# 1. 验证 markers 注册
pytest --markers | grep -E "unit|integration|api|e2e"

# 2. 验证目录结构
ls -la backend/tests/unit backend/tests/integration backend/tests/api backend/tests/e2e backend/tests/common

# 3. 运行 L2 API 测试
pytest backend/tests/api -m api -v

# 4. 生成覆盖率报告
pytest backend/tests -m "not e2e" --cov=backend --cov-report=html --cov-fail-under=70

# 5. 验证 strict markers
pytest --strict-markers -m "unknown_marker" 2>&1 | grep -q "Unknown pytest.mark"
```

---

## 11. 版本演进路线

| 版本 | 重点 | 状态 |
|------|------|------|
| **v1.0** | 初始规范草稿 | Superseded |
| **v1.1** | 结构调整，增加 L1/L2 说明 | Superseded |
| **v1.2** | 结构重组，增强可执行性，补充 Agent 协作指南 | Superseded |
| **v1.3** | RFC 2119 规范化、SoT 路径精确化、示范测试用例、CI/CD 完整配置 | **Current** |
| v1.4 | 引入 UI 自动化（L3），绑定 Playwright 框架 | Planned |
| v2.0 | 测试体系纳入自动化 Agent 流水线 | Future |

---

## 附录 A：快速参考卡片

### 测试层级速查

```
L0 Unit       → backend/tests/unit/        → @pytest.mark.unit
L1 Integration → backend/tests/integration/ → @pytest.mark.integration
L2 API        → backend/tests/api/         → @pytest.mark.api
L3 E2E        → backend/tests/e2e/         → @pytest.mark.e2e
```

### 命名速查

```
文件：test_<模块>.py
类：  Test<模块>
函数：test_<条件>__<预期>
```

### SoT 路径速查

```
docs/2.sot/STATE_MACHINE.md      v2.7  状态枚举、流转白名单
docs/2.sot/DATA_SCHEMA.md        v5.3  数据结构、字段约束
docs/2.sot/ERROR_CODES_SOT.md    v2.1  错误码定义
docs/2.sot/LEDGER_SOT.md         v1.2  账本分录规则
docs/2.sot/AUTH_SPEC.md          v2.0  角色权限矩阵
docs/2.sot/BUSINESS_RULES.md     v4.1  业务约束规则
```

### 运行速查

```bash
pytest backend/tests                    # 全量
pytest -m unit                          # L0
pytest -m integration                   # L1
pytest -m api                           # L2
pytest -m e2e                           # L3
pytest -m "not e2e"                     # 快速 CI
pytest --cov=backend --cov-fail-under=70  # 带覆盖率
```

### 错误码快速校验

```python
from backend.tests.common.error_helpers import assert_error_response

assert_error_response(resp, "STATE_001", 400)  # 非法状态流转
assert_error_response(resp, "AUTH_501", 403)   # 权限不足
assert_error_response(resp, "BIZ_100", 400)    # 金额错误
```

---

**文档结束**
