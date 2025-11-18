# 测试文档

## 📌 概述

本目录包含AI广告代投系统的测试策略、测试用例和自动化测试指南。

## 📂 文档结构

```
testing/
├── README.md              # 测试文档索引（本文件）
├── test-strategy.md       # 测试策略
├── unit-testing.md        # 单元测试指南
├── integration-testing.md # 集成测试指南
├── e2e-testing.md        # E2E测试指南
├── performance-testing.md # 性能测试指南
├── test-cases/           # 测试用例
│   ├── auth.md          # 认证测试用例
│   ├── projects.md      # 项目管理测试用例
│   └── finance.md       # 财务模块测试用例
└── automation.md         # 自动化测试配置
```

## 🎯 测试目标

- **质量保证**: 确保代码质量和功能正确性
- **回归防护**: 防止新代码破坏现有功能
- **性能保障**: 确保系统性能满足要求
- **安全验证**: 验证安全措施有效性

## 📊 测试覆盖率要求

| 测试类型 | 覆盖率要求 | 当前覆盖率 |
|---------|-----------|-----------|
| 单元测试 | ≥80% | 82% |
| 集成测试 | ≥70% | 75% |
| E2E测试 | 核心流程100% | 100% |
| API测试 | 100% | 100% |

## 🧪 测试类型

### 1. 单元测试
针对单个函数或方法的测试

```python
# backend/tests/test_utils.py
import pytest
from app.utils import calculate_roi

def test_calculate_roi():
    """测试ROI计算函数"""
    assert calculate_roi(100, 150) == 50.0
    assert calculate_roi(0, 100) == 0.0
    assert calculate_roi(100, 100) == 0.0
```

### 2. 集成测试
测试模块间的交互

```python
# backend/tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_project():
    """测试创建项目API"""
    response = client.post(
        "/api/v1/projects",
        json={"name": "Test Project", "budget": 10000}
    )
    assert response.status_code == 201
    assert response.json()["data"]["name"] == "Test Project"
```

### 3. E2E测试
模拟用户完整操作流程

```typescript
// frontend/tests/e2e/login.spec.ts
import { test, expect } from '@playwright/test';

test('用户登录流程', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'password123');
  await page.click('[type="submit"]');
  await expect(page).toHaveURL('/dashboard');
});
```

### 4. 性能测试
测试系统性能和压力承受能力

```python
# tests/performance/load_test.py
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def get_projects(self):
        self.client.get("/api/v1/projects")

    @task(3)
    def get_project_detail(self):
        self.client.get("/api/v1/projects/1")
```

## 🛠️ 测试工具

### 后端测试工具
- **pytest**: Python测试框架
- **pytest-cov**: 覆盖率报告
- **pytest-asyncio**: 异步测试支持
- **factory-boy**: 测试数据工厂
- **faker**: 假数据生成

### 前端测试工具
- **Jest**: JavaScript测试框架
- **React Testing Library**: React组件测试
- **Playwright**: E2E测试
- **MSW**: Mock Service Worker
- **Cypress**: 可选的E2E测试工具

### 性能测试工具
- **Locust**: 负载测试
- **Apache JMeter**: 性能测试
- **k6**: 现代化负载测试

## 📝 测试流程

### 1. 开发阶段测试
```mermaid
graph LR
    A[编写代码] --> B[编写单元测试]
    B --> C[运行测试]
    C --> D{测试通过?}
    D -->|否| A
    D -->|是| E[提交代码]
```

### 2. CI/CD测试流程
```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Unit Tests
        run: pytest
      - name: Run Integration Tests
        run: pytest tests/integration
      - name: Run E2E Tests
        run: npm run test:e2e
      - name: Upload Coverage
        run: codecov
```

## 🚀 运行测试

### 后端测试命令
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_auth.py

# 运行带覆盖率的测试
pytest --cov=app --cov-report=html

# 运行并生成报告
pytest --html=report.html --self-contained-html
```

### 前端测试命令
```bash
# 运行单元测试
npm test

# 运行测试覆盖率
npm run test:coverage

# 运行E2E测试
npm run test:e2e

# 运行特定测试文件
npm test -- auth.test.ts
```

## 📋 测试用例示例

### 认证模块测试用例
| 用例ID | 用例名称 | 前置条件 | 测试步骤 | 预期结果 |
|--------|---------|---------|---------|---------|
| AUTH-001 | 正常登录 | 用户已注册 | 1.输入正确账号密码<br>2.点击登录 | 登录成功，跳转到首页 |
| AUTH-002 | 密码错误 | 用户已注册 | 1.输入错误密码<br>2.点击登录 | 显示错误提示 |
| AUTH-003 | Token过期 | 已登录 | 1.等待Token过期<br>2.访问受保护页面 | 跳转到登录页 |

### 项目管理测试用例
| 用例ID | 用例名称 | 前置条件 | 测试步骤 | 预期结果 |
|--------|---------|---------|---------|---------|
| PROJ-001 | 创建项目 | 管理员权限 | 1.填写项目信息<br>2.提交表单 | 项目创建成功 |
| PROJ-002 | 编辑项目 | 项目已存在 | 1.修改项目信息<br>2.保存更改 | 更新成功 |
| PROJ-003 | 删除项目 | 项目无关联数据 | 1.选择项目<br>2.确认删除 | 删除成功 |

## 🐛 测试数据管理

### 测试数据生成
```python
# tests/factories.py
import factory
from app.models import User, Project

class UserFactory(factory.Factory):
    class Meta:
        model = User

    email = factory.Faker('email')
    username = factory.Faker('user_name')
    is_active = True

class ProjectFactory(factory.Factory):
    class Meta:
        model = Project

    name = factory.Faker('company')
    budget = factory.Faker('random_int', min=1000, max=100000)
    status = 'active'
```

### 测试数据库
```bash
# 使用独立的测试数据库
export TEST_DATABASE_URL=postgresql://test:test@localhost/test_db

# 每次测试前重置数据库
pytest --create-db --migrations
```

## 📈 测试报告

### 覆盖率报告
```bash
# 生成HTML覆盖率报告
pytest --cov=app --cov-report=html
open htmlcov/index.html

# 生成XML报告（用于CI）
pytest --cov=app --cov-report=xml
```

### 测试结果可视化
- 使用Allure生成美观的测试报告
- 集成到CI/CD显示测试趋势
- 定期发送测试报告邮件

## ✅ 测试最佳实践

1. **保持测试独立**: 每个测试应该独立运行
2. **使用有意义的名称**: 测试名称应清晰描述测试内容
3. **遵循AAA模式**: Arrange-Act-Assert
4. **避免测试实现细节**: 测试行为而非实现
5. **保持测试简洁**: 一个测试只验证一个功能点
6. **使用Mock和Stub**: 隔离外部依赖
7. **定期维护测试**: 删除过时的测试，更新失效的测试

## 🔧 故障排查

### 常见问题

#### 测试环境配置问题
```bash
# 检查环境变量
echo $TEST_DATABASE_URL
echo $TEST_REDIS_URL

# 重置测试数据库
dropdb test_db
createdb test_db
```

#### 测试超时问题
```python
# 增加测试超时时间
@pytest.mark.timeout(30)
def test_slow_operation():
    pass
```

#### 异步测试问题
```python
# 使用pytest-asyncio
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

## 📞 支持资源

- **测试文档**: 本目录下的各个文档
- **问题反馈**: 提交Issue到GitHub
- **测试社区**: #testing Slack频道
- **培训资源**: 内部测试培训材料

---

*最后更新: 2024-11-18*