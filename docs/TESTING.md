# 🧪 AI广告代投系统 - 测试指南

## 目录
- [概述](#概述)
- [测试架构](#测试架构)
- [环境准备](#环境准备)
- [运行测试](#运行测试)
- [测试类型](#测试类型)
- [编写测试](#编写测试)
- [测试覆盖率](#测试覆盖率)
- [CI/CD集成](#cicd集成)

## 概述

本文档介绍了AI广告代投系统的测试框架和测试指南。系统采用pytest作为测试框架，实现了完整的测试金字塔结构，包括单元测试、集成测试和端到端测试。

### 测试目标
- 确保代码质量和功能正确性
- 验证业务逻辑的准确性
- 保障财务数据的精确性
- 测试安全性和权限控制
- 提供回归测试保障

## 测试架构

```
tests/
├── conftest.py                # 测试配置和共享fixtures
├── test_models.py            # 数据库模型单元测试
├── test_business_logic.py    # 业务逻辑测试
├── test_permissions.py       # 权限测试
├── test_api_endpoints.py     # API接口测试
├── test_reconciliation.py    # 对账功能测试
└── test_files/              # 测试文件存储
```

### 测试分类

1. **单元测试 (70%)** - 测试单个函数、类或模块
2. **集成测试 (20%)** - 测试模块间的交互
3. **功能测试 (10%)** - 端到端业务流程测试

## 环境准备

### 1. 安装依赖

```bash
# 安装测试依赖
pip install -r requirements-test.txt

# 或使用Poetry
poetry install --with test
```

### 2. 环境变量

创建 `.env.test` 文件：

```bash
# 测试环境配置
TESTING=true
DATABASE_URL=sqlite:///./test.db
REDIS_URL=redis://localhost:6379/1
JWT_SECRET=test_secret_key_32_characters_long
ALLOWED_ORIGINS=http://localhost:3000
```

### 3. 测试数据库

测试使用独立的SQLite数据库，每次测试都会自动创建和销毁。

## 运行测试

### 使用测试运行脚本（推荐）

```bash
# 运行所有测试
python run_tests.py

# 运行特定类型的测试
python run_tests.py --type unit         # 单元测试
python run_tests.py --type integration  # 集成测试
python run_tests.py --type database     # 数据库测试
python run_tests.py --type security     # 安全测试

# 运行特定测试文件
python run_tests.py --file tests/test_models.py

# 生成覆盖率报告
python run_tests.py --coverage

# 生成HTML报告
python run_tests.py --html-report

# 详细输出
python run_tests.py --verbose

# 并行执行
python run_tests.py --parallel 4
```

### 直接使用pytest

```bash
# 运行所有测试
pytest

# 运行带标记的测试
pytest -m unit          # 单元测试
pytest -m integration   # 集成测试
pytest -m security      # 安全测试

# 运行特定文件
pytest tests/test_models.py

# 运行特定测试函数
pytest tests/test_models.py::TestUser::test_create_user_success

# 覆盖率报告
pytest --cov=backend --cov-report=html

# 并行执行
pytest -n auto
```

## 测试类型

### 1. 单元测试

标记：`@pytest.mark.unit`

测试独立的函数和类，不涉及外部资源。

```python
@pytest.mark.unit
class TestUser:
    def test_create_user_success(self, db_session):
        user = User(email="test@example.com", ...)
        assert user.email == "test@example.com"
```

### 2. 集成测试

标记：`@pytest.mark.integration`

测试模块间的交互，如数据库操作、API调用等。

```python
@pytest.mark.integration
class TestTopUpFlow:
    def test_complete_topup_flow(self, client, db_session):
        # 测试完整的充值流程
        response = client.post("/api/topups", json={...})
        assert response.status_code == 201
```

### 3. 功能测试

标记：`@pytest.mark.functional`

端到端的业务流程测试。

```python
@pytest.mark.functional
def test_project_to_topup_flow(client, db_session):
    # 创建项目 -> 创建广告账户 -> 申请充值 -> 审批 -> 入账
```

### 4. 安全测试

标记：`@pytest.mark.security`

测试权限控制、认证、数据安全等。

```python
@pytest.mark.security
def test_unauthorized_access(client):
    response = client.get("/api/admin/users")
    assert response.status_code == 401
```

### 5. 性能测试

标记：`@pytest.mark.performance`

测试系统性能，如响应时间、并发处理等。

```python
@pytest.mark.performance
@pytest.mark.slow
def test_api_response_time(client):
    start = time.time()
    response = client.get("/api/projects")
    duration = time.time() - start
    assert duration < 1.0  # 响应时间小于1秒
```

## 编写测试

### 1. 测试文件命名规范

- 单元测试：`test_<module_name>.py`
- 集成测试：`test_<feature>_integration.py`
- 功能测试：`test_<workflow>_functional.py`

### 2. 测试类命名规范

```python
class TestModelName:      # 模型测试
class TestServiceName:    # 服务测试
class TestEndpointName:   # API端点测试
```

### 3. 测试函数命名规范

```python
def test_<function>_success():      # 成功场景
def test_<function>_failure():      # 失败场景
def test_<function>_edge_case():    # 边界条件
def test_<function>_permission():   # 权限测试
```

### 4. 使用Fixtures

```python
def test_user_creation(db_session, test_user):
    # db_session: 数据库会话
    # test_user: 预创建的测试用户
    pass
```

### 5. Mock外部依赖

```python
from unittest.mock import patch

@patch('requests.get')
def test_external_api(mock_get):
    mock_get.return_value.json.return_value = {"status": "ok"}
    # 测试代码
```

### 6. 参数化测试

```python
@pytest.mark.parametrize("status,expected", [
    ("draft", False),
    ("approved", True),
    ("paid", True),
])
def test_topup_is_paid(status, expected):
    topup = TopUp(status=status)
    assert topup.is_paid() == expected
```

## 测试覆盖率

### 覆盖率目标

- 整体覆盖率：≥ 80%
- 核心模块覆盖率：≥ 90%
- 业务逻辑覆盖率：≥ 95%

### 查看覆盖率报告

```bash
# 生成HTML报告
pytest --cov=backend --cov-report=html

# 在浏览器中查看
open htmlcov/index.html
```

### 排除不需要测试的代码

在 `.coveragerc` 中配置：

```ini
[omit]
*/tests/*
*/migrations/*
*/conftest.py

[exclude_lines]
pragma: no cover
def __repr__
raise NotImplementedError
```

## 常见测试场景

### 1. 数据模型测试

```python
def test_model_validation():
    # 测试字段验证
    # 测试约束
    # 测试默认值
```

### 2. 业务逻辑测试

```python
def test_state_machine():
    # 测试状态转换
    # 测试权限检查
    # 测试业务规则
```

### 3. API接口测试

```python
def test_api_endpoint():
    # 测试成功响应
    # 测试错误处理
    # 测试认证授权
```

### 4. 财务计算测试

```python
def test_financial_calculations():
    # 使用精确的Decimal
    # 测试边界值
    # 测试舍入规则
```

## 测试数据管理

### 使用Factory模式

```python
class UserFactory(factory.Factory):
    class Meta:
        model = User

    email = factory.Faker('email')
    name = factory.Faker('name')
```

### 数据清理

每个测试都会自动回滚事务，确保测试之间的隔离。

## 性能测试

### 使用pytest-benchmark

```python
def test_function_performance(benchmark):
    result = benchmark(my_function)
    assert result > 0
```

### 负载测试

使用Locust进行负载测试，配置在 `locustfile.py`。

## CI/CD集成

测试已集成到GitHub Actions，会在以下情况自动运行：

- Push到main/develop分支
- 创建Pull Request
- 每日定时运行（凌晨2点）

### 测试流水线

1. **代码质量检查** - Flake8, Black, isort, MyPy
2. **单元测试** - 快速验证核心功能
3. **集成测试** - 验证模块交互
4. **安全测试** - Bandit安全扫描
5. **性能测试** - 仅在main分支运行

### 测试报告

- 覆盖率报告上传到Codecov
- 测试报告保存在GitHub Artifacts
- 测试总结显示在Pull Request中

## 最佳实践

1. **测试命名** - 使用描述性的名称
2. **单一职责** - 每个测试只验证一个功能
3. **AAA模式** - Arrange（准备）- Act（执行）- Assert（断言）
4. **独立性** - 测试之间不应相互依赖
5. **可重复** - 测试结果应该一致
6. **快速执行** - 单元测试应该快速完成
7. **及时更新** - 代码变更时同步更新测试

## 故障排查

### 常见问题

1. **导入错误** - 检查PYTHONPATH设置
2. **数据库连接** - 确认测试数据库配置
3. **权限错误** - 检查文件和目录权限
4. **依赖缺失** - 运行 `pip install -r requirements-test.txt`

### 调试测试

```bash
# 详细输出
pytest -v -s

# 进入调试器
pytest --pdb

# 只运行失败的测试
pytest --lf

# 停在第一个失败
pytest -x
```

## 贡献指南

添加新测试时：

1. 遵循现有的测试结构和命名规范
2. 使用适当的测试标记
3. 确保测试独立性
4. 维持测试覆盖率
5. 更新相关文档

---

## 📞 支持

如有测试相关问题，请联系开发团队或提交Issue。