# 🧪 AI广告代投系统测试套件

## 概述

本测试套件为AI广告代投系统提供全面的测试覆盖，包括单元测试、集成测试、功能测试、性能测试和安全测试。

## 测试文件结构

```
tests/
├── README.md                           # 本文件
├── conftest.py                         # 测试配置和共享fixtures
├── test_models.py                      # 数据库模型单元测试
├── test_api_endpoints.py               # API端点集成测试
├── test_business_logic.py              # 业务逻辑测试
├── test_financial_calculations.py      # 财务计算专项测试
├── test_data_import.py                 # 数据导入功能测试
├── test_reconciliation.py              # 对账功能测试
├── test_performance.py                 # 性能基准测试
├── test_permissions.py                 # 权限验证测试
├── test_smoke.py                       # 冒烟测试
├── test_ad_spend_report.py             # 广告消费报表测试
├── test_reconciliation_auto.py         # 自动对账测试
└── test_files/                         # 测试文件存储目录
```

## 快速开始

### 1. 安装测试依赖

```bash
pip install -r requirements-test.txt
```

### 2. 运行所有测试

```bash
python run_tests.py
```

### 3. 运行特定类型测试

```bash
# 单元测试
python run_tests.py --type unit

# 集成测试
python run_tests.py --type integration

# API测试
python run_tests.py --file tests/test_api_endpoints.py

# 财务计算测试
python run_tests.py --file tests/test_financial_calculations.py
```

### 4. 生成测试报告

```bash
# 生成覆盖率报告
python run_tests.py --coverage

# 生成HTML测试报告
python run_tests.py --html-report
```

## 测试类型说明

### 1. 单元测试 (Unit Tests)
**标记**: `@pytest.mark.unit`

- 测试单个函数、类或模块
- 不依赖外部资源
- 执行速度快
- 覆盖率目标: >90%

**示例文件**: `test_models.py`, `test_financial_calculations.py`

### 2. 集成测试 (Integration Tests)
**标记**: `@pytest.mark.integration`

- 测试模块间交互
- 使用测试数据库
- 验证数据流和API调用
- 覆盖率目标: >80%

**示例文件**: `test_api_endpoints.py`, `test_data_import.py`

### 3. 功能测试 (Functional Tests)
**标记**: `@pytest.mark.functional`

- 端到端业务流程测试
- 验证完整的用户场景
- 关注业务逻辑正确性
- 覆盖率目标: >70%

**示例文件**: `test_business_logic.py`, `test_reconciliation.py`

### 4. 性能测试 (Performance Tests)
**标记**: `@pytest.mark.performance`, `@pytest.mark.slow`

- 测试系统性能指标
- 建立性能基准线
- 检测性能回归
- 执行时间: >30秒

**示例文件**: `test_performance.py`

### 5. 安全测试 (Security Tests)
**标记**: `@pytest.mark.security`

- 测试权限控制
- 验证认证机制
- 检测安全漏洞
- 覆盖率目标: 100%

## 测试标记

使用pytest标记来组织和运行特定类型的测试：

```python
# 在测试中使用标记
@pytest.mark.unit
def test_user_creation():
    pass

@pytest.mark.integration
@pytest.mark.slow
def test_large_data_import():
    pass
```

## 常用测试命令

### 基础命令

```bash
# 运行所有测试
pytest

# 运行特定文件
pytest tests/test_models.py

# 运行特定测试函数
pytest tests/test_models.py::TestUser::test_create_user

# 显示详细输出
pytest -v

# 只运行失败的测试
pytest --lf

# 在第一个失败时停止
pytest -x
```

### 覆盖率测试

```bash
# 生成覆盖率报告
pytest --cov=backend --cov-report=html

# 只显示未覆盖的行
pytest --cov=backend --cov-report=term-missing

# 设置覆盖率阈值
pytest --cov=backend --cov-fail-under=80
```

### 并行测试

```bash
# 自动检测CPU核心数
pytest -n auto

# 指定进程数
pytest -n 4
```

### 性能测试

```bash
# 只运行性能测试
pytest -m performance

# 超时控制
pytest --timeout=300
```

## 测试数据管理

### Fixtures

使用fixtures创建和管理测试数据：

```python
# 使用预定义的fixture
def test_with_user(db_session, test_user):
    assert test_user.email is not None

# 创建自定义fixture
@pytest.fixture
def custom_project(db_session, test_user):
    project = Project(name="Custom", owner_id=test_user.id)
    db_session.add(project)
    db_session.commit()
    return project
```

### 测试数据工厂

使用TestDataFactory生成测试数据：

```python
def test_multiple_projects(db_session, test_data_factory):
    projects = []
    for i in range(5):
        project = test_data_factory.create_project(db_session)
        projects.append(project)
    assert len(projects) == 5
```

## 调试测试

### 调试技巧

```bash
# 进入调试器
pytest --pdb

# 在失败时进入调试器
pytest --pdb -x

# 打印详细输出
pytest -s -v

# 查看最慢的10个测试
pytest --durations=10
```

### 常见问题

1. **导入错误**: 确保PYTHONPATH正确设置
2. **数据库错误**: 检查测试数据库配置
3. **依赖缺失**: 运行 `pip install -r requirements-test.txt`
4. **权限错误**: 检查文件和目录权限

## 测试最佳实践

### 1. 命名规范
- 测试文件: `test_*.py`
- 测试类: `Test*`
- 测试函数: `test_*`

### 2. 测试结构 (AAA模式)
```python
def test_something():
    # Arrange - 准备测试数据和环境
    user = create_test_user()

    # Act - 执行要测试的操作
    result = user.calculate_spend()

    # Assert - 验证结果
    assert result > 0
```

### 3. 测试独立性
- 每个测试应该独立运行
- 使用fixture提供测试数据
- 自动清理测试数据

### 4. 覆盖率要求
- 核心业务逻辑: 100%
- API端点: 90%
- 工具函数: 95%
- 整体覆盖率: 85%

## 持续集成

测试已集成到GitHub Actions，会在以下情况自动运行：

1. **Push到main/develop分支**
2. **创建Pull Request**
3. **每日定时运行（凌晨2点）**

### 测试流水线
1. 代码质量检查 (Flake8, Black, isort)
2. 单元测试
3. 集成测试
4. 安全测试
5. 性能测试（仅main分支）

## 测试报告

### 覆盖率报告
- HTML报告: `htmlcov/index.html`
- 终端报告: 直接在控制台显示
- JSON报告: `coverage.json`

### 测试结果报告
- HTML报告: `test_reports.html`
- JUnit XML: `report.xml`（CI/CD使用）

## 性能基准

### API响应时间
- 健康检查: < 100ms
- 用户信息: < 200ms
- 项目列表: < 300ms
- 报表生成: < 1s

### 数据库操作
- 简单查询: < 50ms
- 批量插入: > 1000 records/s
- 并发操作: < 100ms avg

### 财务计算
- CPL计算: < 1ms
- ROI计算: < 0.5ms
- 预算分析: < 5ms

## 贡献指南

添加新测试时：

1. **遵循现有结构**: 使用相同的命名和结构模式
2. **添加适当的标记**: 使用pytest标记分类测试
3. **编写清晰的文档**: 添加docstring说明测试目的
4. **保持独立性**: 确保测试不相互依赖
5. **更新覆盖率**: 维护整体测试覆盖率

### 新测试模板

```python
import pytest
from tests.conftest import pytest_marks

@pytest.mark.unit
class TestNewFeature:
    """新功能测试"""

    def test_basic_functionality(self, db_session):
        """测试基础功能"""
        # Arrange
        # Act
        # Assert
        pass

    @pytest.mark.parametrize("input,expected", [
        ("case1", "result1"),
        ("case2", "result2"),
    ])
    def test_parameterized(self, input, expected):
        """参数化测试"""
        pass
```

## 联系方式

如有测试相关问题，请联系：
- 开发团队: dev-team@company.com
- 测试负责人: test-lead@company.com

---

## 最后更新

2025-01-12 - 测试框架V2.1