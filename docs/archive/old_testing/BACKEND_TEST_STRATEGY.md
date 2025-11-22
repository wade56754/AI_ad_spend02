# 后端测试策略（Backend Test Strategy）

**版本**: v1.0
**最后更新**: 2025-01-19
**文档状态**: ✅ Source of Truth（真相源）

---

## 📌 真相源引用（Truth Source References）

本文档基于以下配置文件和代码生成，所有测试策略均来自实际测试实现：

| 文件路径 | 说明 | 用途 |
|---------|------|------|
| `pytest.ini` | Pytest 配置文件 | 定义测试路径、标记、日志和覆盖率配置 |
| `tests/conftest.py` | 测试 Fixture 配置 | 提供共享测试 Fixture 和数据工厂 |
| `tests/` | 集成测试目录 | 包含 21 个集成测试文件 |
| `backend/tests/` | 单元测试目录 | 包含 27 个单元/API 测试文件 |
| `.github/workflows/` | CI/CD 配置 | 自动化测试流水线（如存在） |

---

## 1. 测试框架与工具

### 1.1 核心框架

| 工具/库 | 版本要求 | 用途 |
|--------|---------|------|
| `pytest` | ≥ 6.0 | 测试框架（核心） |
| `pytest-asyncio` | latest | 异步测试支持 |
| `pytest-cov` | latest | 测试覆盖率统计 |
| `pytest-xdist` | latest | 并行测试执行 |
| `pytest-timeout` | latest | 测试超时控制 |
| `pytest-mock` | latest | Mock 工具支持 |

### 1.2 HTTP 测试工具

| 工具/库 | 用途 |
|--------|------|
| `fastapi.testclient.TestClient` | FastAPI 应用测试客户端 |
| `httpx` | 异步 HTTP 客户端 |

### 1.3 数据库测试工具

| 工具/库 | 用途 |
|--------|------|
| `sqlalchemy` | ORM 框架 |
| `sqlite3` | 测试数据库（内存模式） |
| `alembic` | 数据库迁移工具 |

### 1.4 Mock 与 Fixture 工具

| 工具/库 | 用途 |
|--------|------|
| `unittest.mock` | Python 标准 Mock 库 |
| `pytest.fixture` | 测试 Fixture 管理 |
| `faker` | 测试数据生成（如需要） |

---

## 2. 测试分类与标记体系

### 2.1 按测试层级分类

| 标记 | 说明 | 执行时间 | 依赖外部资源 |
|------|------|---------|-------------|
| `@pytest.mark.unit` | **单元测试**：测试单个函数/类，完全隔离 | 毫秒级 | ❌ 无 |
| `@pytest.mark.integration` | **集成测试**：测试模块间交互 | 秒级 | ✅ 数据库 |
| `@pytest.mark.functional` | **功能测试**：端到端业务流程 | 秒级 | ✅ 数据库+API |
| `@pytest.mark.system` | **系统测试**：完整系统测试 | 分钟级 | ✅ 全部 |

### 2.2 按测试类型分类

| 标记 | 说明 | 示例 |
|------|------|------|
| `@pytest.mark.api` | API 接口测试 | 测试 REST API 端点 |
| `@pytest.mark.database` | 数据库测试 | 测试 CRUD 操作、事务、约束 |
| `@pytest.mark.security` | 安全测试 | 测试认证、授权、RLS 权限 |
| `@pytest.mark.performance` | 性能测试 | 响应时间、吞吐量 |
| `@pytest.mark.load` | 负载测试 | 并发请求处理 |
| `@pytest.mark.stress` | 压力测试 | 极限场景测试 |

### 2.3 按测试速度分类

| 标记 | 说明 | 建议执行频率 |
|------|------|-------------|
| `@pytest.mark.fast` | 快速测试 | 每次提交前 |
| `@pytest.mark.slow` | 慢速测试 | PR 合并前 |
| `@pytest.mark.smoke` | 冒烟测试 | 部署后验证 |

### 2.4 特殊标记

| 标记 | 说明 | 用途 |
|------|------|------|
| `@pytest.mark.skip_ci` | 跳过 CI 执行 | 仅本地运行的测试 |
| `@pytest.mark.wip` | 工作进行中 | 开发中的测试（跳过） |
| `@pytest.mark.manual` | 手动测试 | 需要人工介入的测试 |
| `@pytest.mark.regression` | 回归测试 | 修复 Bug 后的验证测试 |
| `@pytest.mark.edge_case` | 边界条件测试 | 极端输入场景 |

### 2.5 使用示例

```python
import pytest

# 单元测试 + 快速测试
@pytest.mark.unit
@pytest.mark.fast
def test_calculate_cpl():
    from backend.services.calculation import calculate_cpl
    result = calculate_cpl(spend=100, conversions=10)
    assert result == 10.0

# 集成测试 + API 测试
@pytest.mark.integration
@pytest.mark.api
def test_create_project_endpoint(client, test_user):
    response = client.post("/projects", json={
        "name": "Test Project",
        "status": "draft"
    })
    assert response.status_code == 201

# 安全测试
@pytest.mark.security
@pytest.mark.functional
def test_unauthorized_access(client_as_user):
    response = client_as_user.delete("/projects/1")
    assert response.status_code == 403

# 性能测试 + 慢速测试
@pytest.mark.performance
@pytest.mark.slow
def test_bulk_report_generation():
    # 生成1000条日报
    ...
```

---

## 3. 测试目录结构

### 3.1 当前结构

```
project_root/
├── tests/                          # 集成测试目录
│   ├── conftest.py                 # 测试 Fixture 配置
│   ├── test_smoke.py               # 冒烟测试
│   ├── test_api_contract.py        # API 契约测试
│   ├── test_permissions.py         # 权限测试
│   ├── test_ad_accounts_endpoints.py
│   ├── test_projects_list.py
│   ├── test_topups.py
│   ├── test_topups_flow.py         # 业务流程测试
│   ├── test_reconciliation.py
│   ├── test_reconciliation_auto.py
│   ├── test_ad_spend.py
│   ├── test_ad_spend_report.py
│   ├── test_reports.py
│   ├── test_performance.py         # 性能测试
│   ├── test_financial_calculations.py
│   ├── test_business_logic.py
│   ├── test_data_import.py
│   ├── test_import_jobs.py
│   ├── test_models.py
│   ├── test_models_crud.py
│   └── test_openapi_endpoints.py
│
├── backend/tests/                  # 单元/模块测试目录
│   ├── conftest.py                 # 模块级 Fixture
│   ├── test_app_smoke.py           # 应用级冒烟测试
│   ├── test_api_health.py          # 健康检查测试
│   │
│   ├── # API 层测试
│   ├── test_api_endpoints.py
│   ├── test_api_projects.py
│   ├── test_project_api.py
│   ├── test_ad_spend_api.py
│   ├── test_daily_report_api.py
│   ├── test_topup_api.py
│   ├── test_reconciliation_api.py
│   ├── test_ai_analytics_api.py
│   ├── test_authentication_api.py
│   │
│   ├── # Service 层测试
│   ├── test_project_service.py
│   ├── test_topup_service.py
│   ├── test_daily_report_service.py
│   ├── test_reconciliation_service.py
│   ├── test_ai_analytics_service.py
│   ├── test_auth_service.py
│   │
│   ├── # 权限测试
│   ├── test_permissions.py
│   ├── test_rbac_permissions.py
│   ├── test_project_permissions.py
│   ├── test_topup_permissions.py
│   ├── test_daily_report_permissions.py
│   ├── test_reconciliation_permissions.py
│   │
│   ├── # 功能测试
│   ├── test_excel_import_export.py
│   ├── test_new_modules_integration.py
│   ├── test_models_crud.py
│   │
│   └── # 性能测试
│       └── test_daily_report_performance.py
│
└── pytest.ini                      # Pytest 配置文件
```

### 3.2 测试文件统计

| 目录 | 测试文件数 | 主要测试内容 |
|------|-----------|-------------|
| `tests/` | 21 | 集成测试、业务流程测试 |
| `backend/tests/` | 27 | 单元测试、API 测试、Service 测试 |
| **总计** | **48** | 覆盖 API、Service、权限、性能等 |

---

## 4. 测试配置（pytest.ini）

### 4.1 核心配置

```ini
[tool:pytest]
# 测试路径
testpaths = tests

# Python 路径
pythonpath = .

# 最小版本要求
minversion = 6.0

# 测试发现模式
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*

# 异步测试支持
asyncio_mode = auto

# 超时配置（秒）
timeout = 300
```

### 4.2 测试执行选项

```ini
addopts =
    --strict-markers      # 严格标记检查
    --strict-config       # 严格配置检查
    --tb=short            # 简短回溯
    --showlocals          # 显示局部变量
    -ra                   # 显示所有测试结果摘要
    --no-header           # 不显示pytest头部
```

### 4.3 日志配置

```ini
# 控制台日志
log_cli = true
log_cli_level = INFO
log_cli_format = %(asctime)s [%(levelname)8s] %(message)s

# 文件日志
log_file = tests.log
log_file_level = DEBUG
log_file_format = %(asctime)s [%(levelname)8s] %(filename)s:%(lineno)d %(message)s
```

### 4.4 警告过滤

```ini
filterwarnings =
    ignore::UserWarning
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

---

## 5. Fixture 管理（conftest.py）

### 5.1 会话级 Fixture

**定义位置**：`tests/conftest.py`

```python
@pytest.fixture(scope="session")
def engine():
    """创建测试数据库引擎（会话级，所有测试共享）"""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="session")
def test_user():
    """创建管理员测试用户（会话级）"""
    return AuthenticatedUser(
        id=str(uuid4()),
        role="admin",
        email="admin@test.com",
        name="测试管理员",
    )

@pytest.fixture(scope="session")
def client(engine, test_user):
    """提供管理员权限的测试客户端（会话级）"""
    app.dependency_overrides[get_current_user] = lambda: test_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_current_user, None)
```

### 5.2 函数级 Fixture

```python
@pytest.fixture
def db_session(engine):
    """提供数据库会话（函数级，每个测试独立）"""
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(autouse=True)
def reset_database(engine):
    """每个测试前重置数据库（自动应用）"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
```

### 5.3 测试数据工厂

```python
class TestDataFactory:
    """测试数据工厂类"""

    @staticmethod
    def create_project_data(**kwargs):
        """创建项目测试数据"""
        defaults = {
            "name": f"测试项目_{datetime.now().timestamp()}",
            "status": "active",
            "total_budget": 10000.00,
        }
        defaults.update(kwargs)
        return defaults

@pytest.fixture
def test_data_factory():
    """提供测试数据工厂"""
    return TestDataFactory
```

### 5.4 Mock Fixture

```python
@pytest.fixture
def redis_client():
    """提供 Redis Mock 客户端"""
    test_redis = Mock(spec=redis.Redis)
    test_redis.ping.return_value = True
    test_redis.get.return_value = None
    test_redis.set.return_value = True
    return test_redis
```

---

## 6. 测试数据管理策略

### 6.1 测试数据库策略

**当前实现**：使用 SQLite 内存数据库

```python
# tests/conftest.py
TEST_DB_PATH = Path("test.db")
os.environ.setdefault("DATABASE_URL", f"sqlite:///./{TEST_DB_PATH.name}")
```

**优点**：
- ✅ 快速：不需要连接真实数据库
- ✅ 隔离：每次测试独立的数据库实例
- ✅ 可重复：测试结果一致

**限制**：
- ⚠️ SQLite 与 PostgreSQL 功能差异（部分 SQL 不兼容）
- ⚠️ 无法测试 PostgreSQL 特定功能（如 RLS、JSONB 操作）

**未来改进**：
- 考虑使用 Docker PostgreSQL 容器用于集成测试
- 使用 Testcontainers 库管理测试容器

### 6.2 测试数据生成策略

#### 策略 1：Fixture 提供预定义数据

```python
@pytest.fixture
def sample_financial_data():
    """提供财务测试数据"""
    return {
        "daily_budget": Decimal("100.00"),
        "total_budget": Decimal("10000.00"),
        "spend": Decimal("250.00"),
        "revenue": Decimal("500.00"),
    }

def test_budget_calculation(sample_financial_data):
    result = calculate_remaining_budget(
        total_budget=sample_financial_data["total_budget"],
        spent=sample_financial_data["spend"]
    )
    assert result == Decimal("9750.00")
```

#### 策略 2：使用测试数据工厂

```python
def test_create_project(test_data_factory, db_session):
    project_data = test_data_factory.create_project_data(name="特定项目名")
    project = Project(**project_data)
    db_session.add(project)
    db_session.commit()
    assert project.id is not None
```

#### 策略 3：内联测试数据

```python
@pytest.mark.parametrize("spend,conversions,expected_cpl", [
    (100, 10, 10.0),
    (250, 5, 50.0),
    (1000, 20, 50.0),
    (0, 0, 0.0),
])
def test_cpl_calculation(spend, conversions, expected_cpl):
    result = calculate_cpl(spend, conversions)
    assert result == expected_cpl
```

### 6.3 测试数据清理策略

#### 自动清理（推荐）

```python
@pytest.fixture(autouse=True)
def reset_database(engine):
    """每个测试前自动重置数据库"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    # 测试后无需手动清理，下次自动重置
```

#### 事务回滚策略（可选）

```python
@pytest.fixture
def db_session_with_rollback(engine):
    """提供事务回滚的数据库会话"""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
```

---

## 7. Mock 与 Stub 策略

### 7.1 何时使用 Mock

**适用场景**：
- 外部 API 调用（如第三方广告平台 API）
- 文件系统操作
- 时间依赖（如 `datetime.now()`）
- 数据库操作（特定场景下）
- Redis/缓存操作
- 邮件/通知服务

### 7.2 Mock 示例

#### Mock 外部 API

```python
from unittest.mock import Mock, patch

@pytest.mark.unit
@patch('backend.services.external_api.fetch_ad_spend')
def test_sync_ad_spend(mock_fetch, db_session):
    # 配置 Mock 返回值
    mock_fetch.return_value = {
        "spend": 250.00,
        "impressions": 10000,
        "clicks": 500
    }

    # 执行测试
    service = AdSpendService(db_session)
    result = service.sync_from_external_api(account_id=1)

    # 断言
    assert result["spend"] == 250.00
    mock_fetch.assert_called_once_with(account_id=1)
```

#### Mock 时间函数

```python
from unittest.mock import patch
from datetime import datetime

@pytest.mark.unit
@patch('backend.services.report.datetime')
def test_generate_daily_report(mock_datetime, db_session):
    # 固定当前时间
    mock_datetime.now.return_value = datetime(2025, 1, 19, 10, 0, 0)
    mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

    # 执行测试
    report = generate_daily_report(account_id=1)

    # 断言
    assert report.report_date == datetime(2025, 1, 19).date()
```

#### Mock Redis

```python
def test_cache_hit(redis_client):
    # 配置 Mock 行为
    redis_client.get.return_value = json.dumps({"cached": "data"})

    # 执行测试
    service = CacheService(redis_client)
    result = service.get_cached_report(report_id=1)

    # 断言
    assert result == {"cached": "data"}
    redis_client.get.assert_called_with("report:1")
```

### 7.3 Mock vs Stub vs Fake

| 类型 | 说明 | 使用场景 |
|------|------|----------|
| **Mock** | 验证行为（调用次数、参数） | 外部 API 调用验证 |
| **Stub** | 返回预定义响应 | 测试数据提供 |
| **Fake** | 简化实现（如内存数据库） | 测试数据库、文件系统 |

---

## 8. API 测试策略

### 8.1 API 测试层级

```
┌─────────────────────────────────────┐
│  Contract Tests（契约测试）          │  ← 验证 API 规范一致性
│  - OpenAPI Schema 验证               │
│  - 响应格式验证                      │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│  Functional API Tests（功能测试）    │  ← 验证业务逻辑
│  - 正常流程测试                      │
│  - 异常场景测试                      │
│  - 权限验证测试                      │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│  Integration Tests（集成测试）       │  ← 验证端到端流程
│  - 跨模块测试                        │
│  - 数据库集成测试                    │
└─────────────────────────────────────┘
```

### 8.2 API 测试示例

#### 基本 CRUD 测试

```python
@pytest.mark.api
@pytest.mark.integration
class TestProjectAPI:
    def test_create_project(self, client, test_user):
        """测试创建项目"""
        response = client.post("/projects", json={
            "name": "Test Project",
            "client_name": "Test Client",
            "status": "draft"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "id" in data["data"]

    def test_get_project(self, client, project_id):
        """测试获取项目"""
        response = client.get(f"/projects/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == project_id

    def test_update_project(self, client, project_id):
        """测试更新项目"""
        response = client.put(f"/projects/{project_id}", json={
            "name": "Updated Project"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "Updated Project"

    def test_delete_project(self, client, project_id):
        """测试删除项目"""
        response = client.delete(f"/projects/{project_id}")
        assert response.status_code == 204
```

#### 权限测试

```python
@pytest.mark.security
class TestProjectPermissions:
    def test_admin_can_delete(self, client, project_id):
        """管理员可以删除项目"""
        response = client.delete(f"/projects/{project_id}")
        assert response.status_code == 204

    def test_user_cannot_delete(self, client_as_user, project_id):
        """普通用户不能删除项目"""
        response = client_as_user.delete(f"/projects/{project_id}")
        assert response.status_code == 403
        data = response.json()
        assert data["code"] == "AUTH_500"  # PERMISSION_DENIED
```

#### 业务逻辑测试

```python
@pytest.mark.functional
def test_topup_approval_workflow(client, db_session):
    """测试充值审批流程"""
    # 1. 创建充值申请
    response = client.post("/topup-requests", json={
        "amount": 1000.00,
        "project_id": 1
    })
    assert response.status_code == 201
    topup_id = response.json()["data"]["id"]

    # 2. 提交审核
    response = client.put(f"/topup-requests/{topup_id}/submit")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "pending_review"

    # 3. 财务审批
    response = client.put(f"/topup-requests/{topup_id}/approve")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "finance_approve"

    # 4. 标记已支付
    response = client.put(f"/topup-requests/{topup_id}/mark-paid")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "paid"
```

---

## 9. 测试覆盖率要求

### 9.1 覆盖率目标

| 代码层级 | 最低覆盖率 | 目标覆盖率 | 备注 |
|---------|-----------|-----------|------|
| 整体代码库 | 70% | 85% | 包含所有 backend/ 代码 |
| 核心业务逻辑 | 90% | 95% | Service 层 |
| API 路由层 | 80% | 90% | Router 层 |
| 模型层 | 60% | 75% | ORM 模型（部分自动生成） |
| 工具类/辅助函数 | 80% | 90% | utils, helpers 等 |

### 9.2 覆盖率统计命令

```bash
# 生成覆盖率报告
pytest --cov=backend --cov-report=html --cov-report=term

# 生成详细覆盖率报告
pytest --cov=backend --cov-report=html:htmlcov --cov-report=term-missing

# 指定最低覆盖率阈值
pytest --cov=backend --cov-fail-under=70
```

### 9.3 覆盖率配置（.coveragerc）

```ini
[run]
source = backend
omit =
    */tests/*
    */test_*.py
    */__pycache__/*
    */migrations/*
    */alembic/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod
```

---

## 10. CI/CD 集成

### 10.1 GitHub Actions 示例（假设）

```yaml
name: Backend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-xdist

      - name: Run tests
        run: |
          pytest tests/ -n auto --cov=backend --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v2
        with:
          file: ./coverage.xml
```

### 10.2 测试执行策略

#### 本地开发

```bash
# 快速测试（仅单元测试）
pytest -m "unit"

# 完整测试（所有标记）
pytest

# 并行测试（加速）
pytest -n auto

# 详细输出
pytest -v --tb=long
```

#### Pre-commit Hook

```bash
# 提交前运行快速测试
pytest -m "fast" --exitfirst

# 仅测试修改的模块
pytest tests/test_projects*.py
```

#### Pull Request

```bash
# 完整测试 + 覆盖率
pytest --cov=backend --cov-fail-under=70

# 包含慢速测试
pytest -m "not skip_ci"
```

#### 生产部署前

```bash
# 全量测试（包括性能测试）
pytest --cov=backend --cov-fail-under=80

# 冒烟测试
pytest -m "smoke"
```

---

## 11. 测试最佳实践

### 11.1 测试命名规范

```python
# ✅ 好的测试名称：描述测试场景
def test_create_project_with_valid_data_returns_201():
    ...

def test_delete_project_without_admin_role_returns_403():
    ...

def test_calculate_cpl_with_zero_conversions_returns_zero():
    ...

# ❌ 不好的测试名称：不清楚测试什么
def test_project():
    ...

def test_create():
    ...

def test_1():
    ...
```

### 11.2 测试结构（Arrange-Act-Assert）

```python
def test_update_project_status():
    # Arrange（准备）
    project = Project(name="Test", status="draft")
    db.add(project)
    db.commit()

    # Act（执行）
    project.status = "active"
    db.commit()

    # Assert（断言）
    updated_project = db.query(Project).filter(Project.id == project.id).first()
    assert updated_project.status == "active"
```

### 11.3 测试独立性原则

```python
# ✅ 好的测试：独立可运行
def test_project_creation(db_session):
    project = Project(name="Test")
    db_session.add(project)
    db_session.commit()
    assert project.id is not None

# ❌ 不好的测试：依赖其他测试
project_id = None

def test_create_project(db_session):
    global project_id
    project = Project(name="Test")
    db_session.add(project)
    db_session.commit()
    project_id = project.id

def test_get_project(db_session):
    # 依赖上一个测试的 project_id
    project = db_session.query(Project).filter(Project.id == project_id).first()
    assert project is not None
```

### 11.4 参数化测试

```python
@pytest.mark.parametrize("role,expected_status", [
    ("admin", 204),
    ("account_manager", 403),
    ("media_buyer", 403),
    ("finance", 403),
])
def test_delete_project_permission(client, role, expected_status, project_id):
    """测试不同角色删除项目的权限"""
    # 切换用户角色
    test_user = AuthenticatedUser(id=str(uuid4()), role=role)
    app.dependency_overrides[get_current_user] = lambda: test_user

    response = client.delete(f"/projects/{project_id}")
    assert response.status_code == expected_status
```

### 11.5 错误测试

```python
@pytest.mark.unit
def test_calculate_cpl_with_negative_spend_raises_error():
    """测试负数消耗抛出异常"""
    with pytest.raises(ValueError, match="spend must be non-negative"):
        calculate_cpl(spend=-100, conversions=10)

@pytest.mark.api
def test_create_project_with_invalid_data_returns_400(client):
    """测试无效数据返回 400"""
    response = client.post("/projects", json={
        "name": "",  # 空名称
        "status": "invalid_status"  # 无效状态
    })
    assert response.status_code == 400
    data = response.json()
    assert "VALIDATION_" in data["code"]
```

### 11.6 异步测试

```python
import pytest

@pytest.mark.asyncio
async def test_async_fetch_ad_spend():
    """测试异步 API 调用"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/ad-spend/1")
    assert response.status_code == 200
```

---

## 12. 性能测试策略

### 12.1 响应时间测试

```python
@pytest.mark.performance
def test_api_response_time(client, benchmark):
    """测试 API 响应时间"""
    def fetch_projects():
        response = client.get("/projects")
        assert response.status_code == 200
        return response

    result = benchmark(fetch_projects)
    assert result.elapsed_time < 0.5  # 500ms 内
```

### 12.2 批量操作性能测试

```python
@pytest.mark.slow
@pytest.mark.performance
def test_bulk_report_generation_performance(db_session):
    """测试批量生成日报的性能"""
    import time

    start_time = time.time()

    # 生成 1000 条日报
    reports = [
        DailyReport(
            ad_account_id=1,
            report_date=date.today(),
            spend=100.00,
            impressions=1000
        )
        for _ in range(1000)
    ]
    db_session.bulk_insert_mappings(DailyReport, [r.__dict__ for r in reports])
    db_session.commit()

    elapsed_time = time.time() - start_time
    assert elapsed_time < 5.0  # 5秒内完成
```

---

## 13. 测试报告与监控

### 13.1 JUnit XML 报告

```bash
pytest --junit-xml=test-results.xml
```

### 13.2 HTML 报告

```bash
pytest --html=report.html --self-contained-html
```

### 13.3 Allure 报告（可选）

```bash
pip install allure-pytest
pytest --alluredir=allure-results
allure serve allure-results
```

---

## 14. 常见问题与解决方案

### 14.1 SQLite 与 PostgreSQL 兼容性问题

**问题**：SQLite 不支持某些 PostgreSQL 特性

**解决方案**：
```python
# 使用编译器适配器
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.compiler import compiles

@compiles(UUID, "sqlite")
def compile_uuid_sqlite(*_args, **_kwargs):
    return "CHAR(36)"

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(*_args, **_kwargs):
    return "TEXT"
```

### 14.2 测试数据库状态污染

**问题**：测试之间数据相互影响

**解决方案**：
```python
@pytest.fixture(autouse=True)
def reset_database(engine):
    """每个测试前重置数据库"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
```

### 14.3 异步测试失败

**问题**：`RuntimeError: Event loop is closed`

**解决方案**：
```python
# pytest.ini
[tool:pytest]
asyncio_mode = auto

# 或在测试中明确指定
@pytest.mark.asyncio
async def test_async_endpoint():
    ...
```

---

## 15. 附录

### 15.1 相关文档

- [错误码 SoT](../ERROR_CODES.md) - 测试中使用的错误码
- [RLS 策略 SoT](../security/RLS_POLICIES.md) - 权限测试参考
- [模型索引](../models/MODEL_INDEX.md) - 数据库模型测试参考
- [API 开发流程](../core/API_DEVELOPMENT_FLOW.md) - API 测试规范

### 15.2 测试清单

| 测试类型 | 当前覆盖 | 目标覆盖 | 状态 |
|---------|---------|---------|------|
| 单元测试 | ✅ | 90%+ | 持续改进 |
| 集成测试 | ✅ | 80%+ | 持续改进 |
| API 测试 | ✅ | 85%+ | 持续改进 |
| 权限测试 | ✅ | 100% | 重点关注 |
| 性能测试 | ⚠️ 部分 | 关键路径 | 待完善 |
| 负载测试 | ❌ 缺失 | 可选 | 未实施 |

### 15.3 变更日志

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| v1.0 | 2025-01-19 | 初始版本，基于当前测试配置生成 | Claude |

---

**文档维护者**: 后端开发团队
**最后审核**: 2025-01-19
**下次审核**: 季度性审核或测试框架重大变更时
