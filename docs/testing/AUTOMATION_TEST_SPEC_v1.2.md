# AI_ad_spend02 自动化测试规范

> **版本**: v1.2
> **状态**: Active
> **更新说明**: 基于 v1.1 进行结构重组，增强可执行性，补充外部 Boilerplate 设计理念说明和 Claude/Agent 协作指南。

---

## 0. 文档元信息

| 属性 | 值 |
|------|-----|
| **文档标识** | `AUTOMATION_TEST_SPEC_v1.2.md` |
| **所属系统** | AI_ad_spend02 |
| **SoT 定位** | 测试体系下位规范（隶属于 `TESTING_SOT.md`） |
| **Owner** | Testing SoT Owner（默认：后端技术负责人） |

### 上游 SoT 依赖

本规范的测试用例设计必须对齐以下权威文档：

| 优先级 | SoT 文档 | 用途 |
|--------|----------|------|
| P0 | `STATE_MACHINE.md` | 状态枚举、流转白名单、终态规则 |
| P1 | `ERROR_CODES_SOT.md` | 错误码定义、测试断言参照 |
| P1 | `LEDGER_SOT.md` | 账本分录类型、余额计算规则 |
| P2 | `DAILY_REPORT_SOT.md` | 日报 8 状态机、粉数确认流程 |
| P2 | `BUSINESS_RULES.md` | 业务约束、金额限制、风控规则 |
| P3 | `AUTH_SPEC.md` | 角色权限矩阵、访问控制规则 |

### 下游产物

- `backend/tests/**` 下的所有 pytest 测试代码
- CI 测试脚本（如 `scripts/run_tests_ci.sh`）
- 测试覆盖率报告

---

## 1. 规范目的与适用范围

### 1.1 目的

本规范用于约束 AI_ad_spend02 的自动化测试体系，核心目标：

1. **分层清晰**：明确 L0/L1/L2/L3 测试层级的职责边界
2. **规则可执行**：让开发者和 Agent 一眼知道「写到哪里、起什么名、加什么 marker、怎么跑」
3. **SoT 对齐**：所有测试用例必须显式关联上游 SoT 文档
4. **自动化友好**：为 Claude / Agent 提供明确的生成规则

### 1.2 适用范围

| 范围 | 说明 |
|------|------|
| **代码仓库** | `AI_ad_spend02` |
| **技术栈** | FastAPI + SQLAlchemy + pytest |
| **测试目录** | `backend/tests/` |
| **约束强度** | 新增测试**必须**遵守；存量测试逐步迁移 |

> **不适用**：前端（Next.js）的纯前端单元测试（jest/rtl），但建议保持命名风格一致。

### 1.3 目标角色

| 角色 | 职责 |
|------|------|
| **Backend Developer** | 为新功能补齐 L0/L1/L2 层测试 |
| **Test / QA Engineer** | 主导 L2/L3 测试设计，维护 E2E 流程 |
| **Claude / Agent** | 遵守本规范自动生成、修改、审查测试 |

---

## 2. 测试层级模型

### 2.1 四层测试金字塔

```
        ┌─────────────┐
        │     L3      │  E2E / UI 自动化（少量，高价值场景）
        │   端到端    │
        ├─────────────┤
        │     L2      │  API 测试（核心业务流程）
        │   API 层    │
        ├─────────────┤
        │     L1      │  集成测试（组件协作）
        │   集成层    │
        ├─────────────┤
        │     L0      │  单元测试（大量，快速反馈）
        │   单元层    │
        └─────────────┘
```

### 2.2 层级定义与 pytest markers

| 层级 | 名称 | pytest marker | 目标 | 依赖 | 执行速度 |
|------|------|---------------|------|------|----------|
| **L0** | 单元测试 | `@pytest.mark.unit` | 验证单个函数/方法/类的行为 | Mock，无外部依赖 | 极快 |
| **L1** | 集成测试 | `@pytest.mark.integration` | 验证 service + repository + DB 协作 | 测试数据库，外部服务可 mock | 快 |
| **L2** | API 测试 | `@pytest.mark.api` | 以 HTTP 入口验证完整链路 | FastAPI TestClient + 测试库 | 中等 |
| **L3** | E2E 测试 | `@pytest.mark.e2e` | 用户视角的完整业务流程 | 前后端运行，浏览器驱动 | 慢 |

### 2.3 各层级详细说明

#### L0：单元测试（Unit Test）

```python
# 位置：backend/tests/unit/test_<module>.py
# marker：@pytest.mark.unit

@pytest.mark.unit
class TestUserValidator:
    """验证用户输入校验函数"""

    def test_valid_email__returns_true(self):
        assert validate_email("user@example.com") is True

    def test_invalid_email__raises_validation_error(self):
        with pytest.raises(ValidationError):
            validate_email("invalid-email")
```

- **目标**：验证单个函数/方法的正确性
- **依赖**：尽量无外部依赖，使用 mock/stub
- **典型场景**：工具函数、验证器、纯业务逻辑、模型方法

#### L1：集成测试（Integration Test）

```python
# 位置：backend/tests/integration/test_<service>.py
# marker：@pytest.mark.integration

@pytest.mark.integration
class TestReconciliationHelper:
    """
    验证 ReconciliationStateHelper 与数据库状态联动

    SOT 引用：STATE_MACHINE.md#reconciliation
    """

    def test_approve_batch__updates_status_and_ledger(self, db_session):
        # 准备数据
        batch = create_reconciliation_batch(db_session, status="pending_review")
        # 执行
        helper = ReconciliationStateHelper(db_session)
        result = helper.approve(batch.id)
        # 断言
        assert result.status == "approved"
        assert db_session.query(LedgerEntry).filter_by(batch_id=batch.id).count() > 0
```

- **目标**：验证多个组件（service + repository + DB）协同工作
- **依赖**：真实测试数据库，外部服务可 mock
- **典型场景**：状态机流转、账本写入、复杂业务规则

#### L2：API 测试（API-level E2E）

```python
# 位置：backend/tests/api/test_<resource>_flow.py
# marker：@pytest.mark.api

@pytest.mark.api
class TestTopupFlow:
    """
    充值申请完整 API 流程测试

    SOT 引用：
    - STATE_MACHINE.md#topup-request
    - ERROR_CODES_SOT.md#TOP_*
    - LEDGER_SOT.md#topup-entries
    """

    def test_topup_happy_path__draft_to_completed(self, client, admin_token):
        # 1. 创建充值申请
        resp = client.post("/api/v1/topups/", json={...}, headers=auth_header(admin_token))
        assert resp.status_code == 201
        topup_id = resp.json()["data"]["id"]

        # 2. 提交审核
        resp = client.post(f"/api/v1/topups/{topup_id}/submit", headers=auth_header(admin_token))
        assert resp.json()["data"]["status"] == "pending_review"

        # 3. 财务审批
        resp = client.post(f"/api/v1/topups/{topup_id}/approve", headers=auth_header(finance_token))
        assert resp.json()["data"]["status"] == "finance_approve"

        # 4. 完成充值
        resp = client.post(f"/api/v1/topups/{topup_id}/complete", headers=auth_header(admin_token))
        assert resp.json()["data"]["status"] == "completed"
```

- **目标**：以 HTTP API 入口验证从路由 → service → DB → 状态机的完整链路
- **依赖**：FastAPI TestClient + 真实测试库
- **典型场景**：核心业务流程、权限控制、错误码校验

#### L3：端到端测试（Full E2E / UI Automation）

```python
# 位置：backend/tests/e2e/test_<scenario>.py
# marker：@pytest.mark.e2e

@pytest.mark.e2e
class TestDailyReportWorkflow:
    """
    媒体购买角色完整日报提交流程

    场景：登录 → 创建日报 → 提交 → 审核 → 锁定
    """

    def test_media_buyer_submits_daily_report(self, browser, test_user):
        # 使用 Playwright/Selenium 驱动浏览器
        page = browser.new_page()
        page.goto(f"{BASE_URL}/login")
        # ...完整用户操作流程
```

- **目标**：从用户视角驱动浏览器或脚本，覆盖完整业务流程
- **依赖**：前后端都运行，浏览器驱动
- **典型场景**：核心用户旅程、跨系统集成、冒烟测试

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
    │   ├── test_user_crud.py
    │   ├── test_validators.py
    │   └── test_utils.py
    │
    ├── integration/          # L1：集成测试
    │   ├── __init__.py
    │   ├── conftest.py       # 集成测试专用 fixture（如 db_session）
    │   ├── test_reconciliation_helper.py
    │   └── test_state_machine_transitions.py
    │
    ├── api/                  # L2：API 层测试
    │   ├── __init__.py
    │   ├── conftest.py       # API 测试专用 fixture（如 authenticated_client）
    │   ├── test_topup_flow.py
    │   ├── test_daily_report_api.py
    │   └── test_ledger_api.py
    │
    ├── e2e/                  # L3：端到端自动化（预留）
    │   ├── __init__.py
    │   ├── conftest.py       # E2E 专用 fixture（如 browser）
    │   ├── pages/            # Page Object 模式（UI 自动化时使用）
    │   └── flows/            # 业务流程脚本
    │
    └── common/               # 公共工具
        ├── __init__.py
        ├── factories.py      # 测试数据工厂
        ├── api_client.py     # HTTP 客户端封装
        ├── state_asserts.py  # 状态机断言工具
        └── error_codes.py    # 错误码校验工具
```

### 3.2 目录职责说明

| 目录 | 层级 | 职责 | 文件命名模式 |
|------|------|------|-------------|
| `unit/` | L0 | 单元测试 | `test_<module>.py` |
| `integration/` | L1 | 集成测试 | `test_<service/helper>.py` |
| `api/` | L2 | API 测试 | `test_<resource>_flow.py` 或 `test_<resource>_api.py` |
| `e2e/` | L3 | E2E 测试 | `test_<scenario>.py` |
| `common/` | - | 公共工具 | `<功能>.py`（如 `factories.py`） |

### 3.3 存量测试迁移策略

对于现有零散的测试文件（如 `backend/tests/test_state_machine_transitions.py`）：

1. **迁移期可保留**在根目录
2. **逐步拆分**并移入对应子目录
3. **新增测试必须**放入正确的子目录
4. 迁移时需添加对应的 pytest marker

---

## 4. 命名规范

### 4.1 文件命名

| 类型 | 规范 | 示例 |
|------|------|------|
| 测试文件 | `test_<模块/场景>.py` | `test_user_crud.py`, `test_topup_flow.py` |
| 公共模块 | `<功能>.py` | `factories.py`, `api_client.py` |
| conftest | `conftest.py` | 固定名称 |

### 4.2 类命名

| 规范 | 示例 |
|------|------|
| `Test<模块/对象名>` | `TestUserCRUD`, `TestDailyReportStateMachine` |
| `Test<场景>Flow` | `TestTopupApprovalFlow` |

### 4.3 函数命名

**格式**：`test_<条件>__<预期结果>`

| 场景 | 示例 |
|------|------|
| 成功路径 | `test_create_user__success` |
| 失败路径 | `test_create_user_duplicate_email__raises_conflict` |
| 状态流转 | `test_submit_draft_topup__status_becomes_pending` |
| 权限校验 | `test_media_buyer_access_admin_api__returns_403` |
| 错误码校验 | `test_invalid_amount__returns_TOP_001` |

### 4.4 命名示例速查表

```python
# 文件：backend/tests/api/test_topup_flow.py

@pytest.mark.api
class TestTopupApprovalFlow:
    """充值审批流程 API 测试"""

    # Happy path
    def test_submit_draft_topup__status_becomes_pending_review(self): ...

    # 权限边界
    def test_media_buyer_approves_topup__returns_403_forbidden(self): ...

    # 异常路径
    def test_submit_already_submitted__returns_TOP_002_invalid_transition(self): ...

    # 错误码校验
    def test_negative_amount__returns_TOP_001_invalid_amount(self): ...
```

---

## 5. Fixture 与配置规范

### 5.1 conftest 分层架构

```
backend/tests/
├── conftest.py              # 全局 fixture（所有层共用）
├── unit/
│   └── (无 conftest，直接使用全局)
├── integration/
│   └── conftest.py          # 集成测试专用 fixture
├── api/
│   └── conftest.py          # API 测试专用 fixture
└── e2e/
    └── conftest.py          # E2E 测试专用 fixture
```

### 5.2 全局 conftest.py 内容

```python
# backend/tests/conftest.py

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
    """测试环境配置"""
    return get_settings()

@pytest.fixture(scope="session")
def test_engine(test_settings):
    """测试数据库引擎"""
    engine = create_engine(test_settings.test_database_url)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(test_engine):
    """每个测试函数独立的数据库会话"""
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
def client(app_instance):
    """FastAPI TestClient"""
    with TestClient(app_instance) as c:
        yield c

# ============== pytest 配置 ==============

def pytest_configure(config):
    """注册自定义 markers"""
    config.addinivalue_line("markers", "unit: L0 单元测试")
    config.addinivalue_line("markers", "integration: L1 集成测试")
    config.addinivalue_line("markers", "api: L2 API 测试")
    config.addinivalue_line("markers", "e2e: L3 端到端自动化测试")
```

### 5.3 pytest.ini 配置

```ini
[pytest]
testpaths = backend/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

markers =
    unit: L0 单元测试
    integration: L1 集成测试
    api: L2 API 测试
    e2e: L3 端到端自动化测试

addopts = -v --tb=short
filterwarnings =
    ignore::DeprecationWarning
```

### 5.4 层级专用 fixture 示例

```python
# backend/tests/api/conftest.py

import pytest
from backend.tests.common.factories import create_user

@pytest.fixture
def admin_user(db_session):
    """创建管理员用户"""
    return create_user(db_session, role="admin")

@pytest.fixture
def admin_token(admin_user, client):
    """获取管理员认证 token"""
    resp = client.post("/api/v1/auth/login", json={
        "email": admin_user.email,
        "password": "test_password"
    })
    return resp.json()["access_token"]

@pytest.fixture
def authenticated_client(client, admin_token):
    """带认证的 HTTP 客户端"""
    client.headers["Authorization"] = f"Bearer {admin_token}"
    return client
```

---

## 6. 公共工具规范（common/）

### 6.1 模块职责映射

| 模块 | 职责 | 对应概念 |
|------|------|----------|
| `factories.py` | 测试数据构造 | Data Factory |
| `api_client.py` | HTTP 客户端封装 | API Client / Driver |
| `state_asserts.py` | 状态机断言工具 | Custom Assertions |
| `error_codes.py` | 错误码校验工具 | Error Code Helper |

### 6.2 factories.py 示例

```python
# backend/tests/common/factories.py

from uuid import uuid4
from decimal import Decimal
from backend.models import User, Project, TopupRequest

def create_user(db_session, **kwargs):
    """创建测试用户"""
    defaults = {
        "id": uuid4(),
        "email": f"test_{uuid4().hex[:8]}@example.com",
        "username": f"user_{uuid4().hex[:8]}",
        "role": "media_buyer",
        "is_active": True,
    }
    defaults.update(kwargs)
    user = User(**defaults)
    db_session.add(user)
    db_session.commit()
    return user

def create_topup_request(db_session, user, **kwargs):
    """创建测试充值申请"""
    defaults = {
        "amount": Decimal("1000.00"),
        "status": "draft",
        "created_by": user.id,
    }
    defaults.update(kwargs)
    topup = TopupRequest(**defaults)
    db_session.add(topup)
    db_session.commit()
    return topup
```

### 6.3 state_asserts.py 示例

```python
# backend/tests/common/state_asserts.py

def assert_status_transition(entity, expected_status, sot_ref=None):
    """
    断言实体状态符合预期

    Args:
        entity: 数据库实体
        expected_status: 预期状态
        sot_ref: SoT 引用（用于错误信息）
    """
    actual = entity.status
    assert actual == expected_status, (
        f"状态不符: 预期 '{expected_status}', 实际 '{actual}'. "
        f"SOT 引用: {sot_ref or 'N/A'}"
    )

def assert_ledger_entry_created(db_session, entity_type, entity_id, entry_type):
    """断言账本分录已创建"""
    from backend.models import LedgerEntry
    entry = db_session.query(LedgerEntry).filter_by(
        resource_type=entity_type,
        resource_id=str(entity_id),
        entry_type=entry_type
    ).first()
    assert entry is not None, f"未找到 {entry_type} 类型的账本分录"
```

### 6.4 使用约束

> **强制规则**：
> 1. 新增测试**必须优先使用** `common/` 内已有的工具和工厂
> 2. 避免在测试文件内随意新建 ad-hoc 工厂函数
> 3. 如现有工具无法满足需求，**优先补充 `common/`**，再在测试文件中使用

---

## 7. 测试用例设计规范

### 7.1 SoT 对齐要求

**所有测试用例必须显式声明其对应的业务规则 / 状态机节点**，在 docstring 中注明 SoT 引用：

```python
class TestDailyReportSubmit:
    """
    日报提交流程测试

    覆盖场景：
    - draft -> submitted (投手提交)
    - submitted -> approved (主管审核通过)
    - submitted -> rejected (主管驳回)

    SOT 引用：
    - STATE_MACHINE.md v2.6 第8章 (DailyReport 8状态机)
    - ERROR_CODES_SOT.md#DR_* (日报相关错误码)
    - DAILY_REPORT_SOT.md (粉数确认规则)
    """
```

### 7.2 必须覆盖的测试场景

对于 L2/L3 测试，每个业务流程**必须至少覆盖**：

| 场景类型 | 说明 | 示例 |
|----------|------|------|
| **Happy Path** | 成功流程 | `test_topup_draft_to_completed__success` |
| **权限边界** | 不同角色访问控制 | `test_media_buyer_approves__returns_403` |
| **状态机禁止** | 非法状态流转 | `test_completed_topup_submit__returns_invalid_transition` |
| **业务约束** | 金额限制、重复提交等 | `test_negative_amount__returns_validation_error` |
| **错误码校验** | 响应错误码对齐 ERROR_CODES_SOT | `test_duplicate_submit__returns_TOP_002` |

### 7.3 错误码断言模式

```python
def test_invalid_amount__returns_TOP_001(self, client, admin_token):
    """
    验证负数金额返回 TOP-001 错误码

    SOT 引用：ERROR_CODES_SOT.md#TOP-001
    """
    resp = client.post("/api/v1/topups/", json={
        "amount": -100,
        "ad_account_id": "..."
    }, headers=auth_header(admin_token))

    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "TOP-001"
    assert "invalid_amount" in resp.json()["error"]["message"].lower()
```

---

## 8. 运行命令规范

### 8.1 标准命令集

| 场景 | 命令 | 说明 |
|------|------|------|
| **全量测试** | `pytest backend/tests` | 运行所有测试 |
| **单元测试** | `pytest backend/tests/unit -m unit` | 仅 L0 |
| **集成测试** | `pytest backend/tests/integration -m integration` | 仅 L1 |
| **API 测试** | `pytest backend/tests/api -m api` | 仅 L2 |
| **E2E 测试** | `pytest backend/tests/e2e -m e2e` | 仅 L3 |
| **排除 E2E** | `pytest backend/tests -m "not e2e"` | 快速 CI |
| **带覆盖率** | `pytest backend/tests --cov=backend --cov-report=html` | 生成覆盖率报告 |

### 8.2 CI 脚本示例

```bash
#!/bin/bash
# scripts/run_tests_ci.sh

set -e

echo "=== Running L0 Unit Tests ==="
pytest backend/tests/unit -m unit --tb=short

echo "=== Running L1 Integration Tests ==="
pytest backend/tests/integration -m integration --tb=short

echo "=== Running L2 API Tests ==="
pytest backend/tests/api -m api --tb=short

echo "=== Generating Coverage Report ==="
pytest backend/tests -m "not e2e" --cov=backend --cov-report=xml

echo "=== All Tests Passed ==="
```

### 8.3 按 marker 组合运行

```bash
# 运行 API 和 E2E 测试
pytest -m "api or e2e"

# 运行除 E2E 外的所有测试
pytest -m "not e2e"

# 运行单元和集成测试
pytest -m "unit or integration"
```

---

## 9. 自动化测试设计理念

### 9.1 借鉴外部 Boilerplate 的思路

本规范参考了 [sanbercode-api-automation-boilerplate](https://github.com/jfrelis/sanbercode-api-automation-boilerplate) 的设计模式，但技术栈保持 FastAPI + pytest 不变。

#### 核心借鉴点

| 外部模式 | 本项目实现 | 说明 |
|----------|-----------|------|
| **配置与执行分离** | `conftest.py` + `common/` | 测试配置、数据工厂、执行逻辑分离 |
| **环境变量管理** | `test_settings` fixture | 集中管理测试环境配置 |
| **报告自动生成** | pytest HTML/XML 报告 | `--cov-report=html` 生成覆盖率报告 |
| **模块化组织** | `unit/` `integration/` `api/` `e2e/` | 按测试类型分目录 |
| **声明式配置** | pytest markers + pytest.ini | 通过 marker 声明测试类型 |

#### 概念映射表

| Automation Boilerplate 概念 | 本项目对应 |
|----------------------------|-----------|
| `tests/` 根目录 | `backend/tests/` |
| 顶层 conftest | `backend/tests/conftest.py` |
| `base_test` / `driver_manager` | `common/api_client.py` + E2E 驱动层 |
| `data_factory` | `common/factories.py` |
| Newman Collection | pytest 测试类 |
| Environment JSON | `test_settings` fixture |
| HTML Reporter | `pytest-html` / `pytest-cov` |

### 9.2 与 Newman 模式的区别

| 方面 | Newman (Postman CLI) | 本项目 (pytest) |
|------|---------------------|-----------------|
| **测试定义** | JSON Collection | Python 代码 |
| **执行引擎** | Node.js + Newman | Python + pytest |
| **断言方式** | Postman 脚本 | pytest assert |
| **数据驱动** | Environment JSON | pytest fixture / parametrize |
| **报告格式** | htmlextra | pytest-html / pytest-cov |
| **CI 集成** | `newman run` | `pytest` |

**设计选择**：我们选择 pytest 而非 Newman，因为：
1. 与 FastAPI 后端技术栈一致（Python 全栈）
2. 更强的代码表达能力和调试体验
3. 原生支持 fixture 依赖注入
4. 与 IDE 深度集成

---

## 10. Claude / Agent 协作规范

### 10.1 总则

1. **自动生成的测试必须放在本规范指定的目录中**
2. **必须遵守命名规范和 markers 规则**
3. **生成前必须引用本规范和对应的 SoT 文档**

### 10.2 任务类型与落点速查表

| 任务类型 | 目录 | Marker | 必须引用的 SoT |
|----------|------|--------|---------------|
| 补单元测试 (L0) | `backend/tests/unit/` | `@pytest.mark.unit` | 无（纯逻辑） |
| 补集成测试 (L1) | `backend/tests/integration/` | `@pytest.mark.integration` | STATE_MACHINE |
| 补 API 测试 (L2) | `backend/tests/api/` | `@pytest.mark.api` | STATE_MACHINE + ERROR_CODES |
| 补 E2E 测试 (L3) | `backend/tests/e2e/` | `@pytest.mark.e2e` | 完整业务流程 SoT |
| 补公共工具 | `backend/tests/common/` | 无 marker | 按功能确定 |

### 10.3 Agent 提示语模板

#### 生成 L2 API 测试

```
阅读 AUTOMATION_TEST_SPEC_v1.2.md 和 STATE_MACHINE.md，
为 [模块名] 按 L2 API 测试规范补齐：
1. Happy Path 测试
2. 权限边界测试（至少覆盖 admin / media_buyer 两种角色）
3. 状态机非法流转测试
4. 错误码校验测试（对齐 ERROR_CODES_SOT.md）

将新测试写入 backend/tests/api/test_[模块名]_flow.py，
使用 common/ 内的 factories 和断言工具。
```

#### 审查现有测试

```
阅读 AUTOMATION_TEST_SPEC_v1.2.md，审查 backend/tests/[目录]/[文件].py：
1. 检查是否有正确的 pytest marker
2. 检查命名是否符合规范
3. 检查是否引用了 SoT 文档
4. 检查是否覆盖了必须的测试场景（Happy Path / 权限 / 异常 / 错误码）
输出审查报告和修改建议。
```

#### 迁移存量测试

```
将 backend/tests/test_[旧文件].py 按 AUTOMATION_TEST_SPEC_v1.2.md 迁移：
1. 确定测试层级（L0/L1/L2）
2. 移动到对应子目录
3. 添加正确的 pytest marker
4. 补充 SoT 引用到 docstring
5. 调整命名符合规范
```

### 10.4 重构约定

在自动重构测试时：

1. **优先保持原层级和位置不变**，只优化内部结构和断言
2. 若需调整层级（如从 integration 升级为 api），必须：
   - 在测试文件头部注释中写明「层级变更原因」
   - 在 PR / Commit 信息中体现变更

---

## 11. 最小落地检查清单

### 11.1 v1.2 必须完成项

- [ ] **目录结构搭建完成**
  - [ ] `backend/tests/unit/`
  - [ ] `backend/tests/integration/`
  - [ ] `backend/tests/api/`
  - [ ] `backend/tests/e2e/`
  - [ ] `backend/tests/common/`

- [ ] **pytest 配置完成**
  - [ ] `pytest.ini` 中注册 markers: `unit` / `integration` / `api` / `e2e`
  - [ ] 全局 `conftest.py` 包含基础 fixture

- [ ] **公共工具模块**
  - [ ] `common/factories.py` 至少包含 User / Project 工厂
  - [ ] `common/api_client.py` 包含认证 header 辅助函数

- [ ] **示范性 L2 测试**
  - [ ] 至少 1 个业务流（推荐：Topup 或 DailyReport）
  - [ ] 完整覆盖 Happy Path + 权限边界 + 错误码
  - [ ] docstring 中写明 SoT 引用

### 11.2 验收命令

```bash
# 1. 验证 markers 注册
pytest --markers | grep -E "unit|integration|api|e2e"

# 2. 验证目录结构
ls -la backend/tests/unit backend/tests/integration backend/tests/api backend/tests/e2e backend/tests/common

# 3. 运行 L2 API 测试
pytest backend/tests/api -m api -v

# 4. 生成覆盖率报告
pytest backend/tests -m "not e2e" --cov=backend --cov-report=html
```

---

## 12. 版本演进路线

| 版本 | 重点 | 状态 |
|------|------|------|
| **v1.0** | 初始规范草稿 | Superseded |
| **v1.1** | 结构调整，增加 L1/L2 说明 | Superseded |
| **v1.2** | 结构重组，增强可执行性，补充 Agent 协作指南 | **Current** |
| v1.3 | 引入覆盖率统计与最小覆盖标准 | Planned |
| v1.4 | 引入 UI 自动化（L3），绑定具体框架 | Planned |
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

### 运行速查

```bash
pytest backend/tests                    # 全量
pytest -m unit                          # L0
pytest -m integration                   # L1
pytest -m api                           # L2
pytest -m e2e                           # L3
pytest -m "not e2e"                     # 快速 CI
```

---

**文档结束**
