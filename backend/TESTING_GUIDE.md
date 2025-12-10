# 后端测试完整指南
> **AI 代码工厂生成** | 2025-12-10

---

## 📦 测试环境准备

### 1. 安装测试依赖

```powershell
cd D:\git\1108\backend
pip install -r requirements.txt
```

或者单独安装测试工具：
```powershell
pip install pytest pytest-cov pytest-asyncio pytest-mock httpx
```

### 2. 验证安装

```powershell
python -m pytest --version
# 应输出: pytest 8.3.4 或更高版本
```

---

## 🚀 快速开始

### 方式 1: 使用交互式脚本（推荐）

```powershell
cd D:\git\1108\backend
.\run_tests.ps1
```

然后选择测试策略（1-6）。

### 方式 2: 直接运行命令

#### 快速验证（2分钟）
```powershell
cd D:\git\1108\backend
python -m pytest tests/test_api_health.py tests/test_app_smoke.py -v
```

#### 核心模块测试（5分钟）
```powershell
python -m pytest -m "auth or project or daily_report" -v
```

#### 完整回归测试（25分钟）
```powershell
python -m pytest --cov=backend --cov-report=html -v
```

---

## 📊 测试覆盖模块清单

### ✅ 已覆盖模块 (45个测试文件)

#### 核心功能
- ✅ **认证系统** (3个测试)
  - `test_authentication_api.py`
  - `test_auth_service.py`
  - `test_permissions.py`

- ✅ **项目管理** (3个测试)
  - `test_project_api.py`
  - `test_project_service.py`
  - `test_project_permissions.py`

- ✅ **日报系统** (5个测试)
  - `test_daily_report_api.py`
  - `test_daily_report_service.py`
  - `test_daily_report_state_machine.py`
  - `test_daily_report_performance.py`
  - `test_daily_report_permissions.py`

#### 财务模块
- ✅ **充值管理** (3个测试)
  - `test_topup_api.py`
  - `test_topup_service.py`
  - `test_topup_permissions.py`

- ✅ **对账系统** (3个测试)
  - `test_reconciliation_api.py`
  - `test_reconciliation_service.py`
  - `test_reconciliation_permissions.py`

- ✅ **财务总账** (2个测试)
  - `test_ledger_service.py`
  - `test_ledger_invariants.py`

#### 广告系统
- ✅ **广告账户** (2个测试)
  - `test_ad_account_api.py`
  - `test_ad_account_service.py`

- ✅ **广告消耗**
  - `test_ad_spend_api.py`

#### AI 分析
- ✅ **AI 分析** (2个测试)
  - `test_ai_analytics_api.py`
  - `test_ai_analytics_service.py`

### ⚠️ 未覆盖模块 (需补充)

| 路由模块 | 优先级 | 建议覆盖率 |
|---------|-------|-----------|
| `reports.py` | 🟡 中 | ≥65% |
| `channels.py` | 🟢 低 | ≥50% |
| `project_templates.py` | 🟢 低 | ≥50% |
| `agents.py` | 🟢 低 | ≥50% |

---

## 🎯 测试策略

### Level 1: 冒烟测试（每次部署必跑）
**时间**: 2分钟
```powershell
pytest tests/test_api_health.py tests/test_app_smoke.py -v
```

**验证内容**:
- API 服务可启动
- 健康检查端点可访问
- 数据库连接正常

---

### Level 2: 核心模块测试（代码变更后）
**时间**: 5-8分钟
```powershell
pytest -m "auth or project or daily_report" -v
```

**验证内容**:
- 用户认证流程
- 项目CRUD操作
- 日报状态机转换

---

### Level 3: 单元测试（Pull Request 前）
**时间**: 10分钟
```powershell
pytest -m unit --cov=backend --cov-report=term-missing
```

**验证内容**:
- 所有业务逻辑单元
- 服务层函数
- 工具函数

---

### Level 4: 集成测试（发布前）
**时间**: 15分钟
```powershell
pytest -m integration --cov=backend
```

**验证内容**:
- 数据库操作
- API 端点集成
- 外部服务调用

---

### Level 5: 完整回归测试（重大版本发布）
**时间**: 25-30分钟
```powershell
pytest --cov=backend --cov-report=html --cov-report=term-missing -v
```

**验证内容**:
- 全部45个测试文件
- 代码覆盖率报告
- 性能基准测试

---

## 📈 覆盖率报告

### 查看 HTML 报告
测试完成后，浏览器打开：
```
D:\git\1108\backend\htmlcov\index.html
```

### 覆盖率目标
| 模块类型 | 目标覆盖率 |
|---------|-----------|
| 核心业务逻辑 | ≥80% |
| API 路由 | ≥75% |
| 服务层 | ≥75% |
| 工具函数 | ≥70% |
| 整体项目 | ≥60% |

---

## 🔍 常用测试命令

### 运行特定文件
```powershell
pytest tests/test_topup_api.py -v
```

### 运行特定测试用例
```powershell
pytest tests/test_topup_api.py::test_create_topup -v
```

### 只运行失败的测试
```powershell
pytest --lf -v
```

### 显示最慢的10个测试
```powershell
pytest --durations=10
```

### 并行运行测试（需要 pytest-xdist）
```powershell
pip install pytest-xdist
pytest -n auto
```

### 生成 JUnit XML 报告
```powershell
pytest --junitxml=test-results.xml
```

---

## 🚨 常见问题

### 1. 导入错误 `ModuleNotFoundError`
**解决**:
```powershell
$env:PYTHONPATH = "D:\git\1108"
```

### 2. 数据库连接失败
**原因**: 测试依赖数据库连接
**解决**: 确保 `.env` 文件配置正确，或使用 SQLite

### 3. 异步测试失败
**原因**: 缺少 `pytest-asyncio`
**解决**:
```powershell
pip install pytest-asyncio
```

### 4. 覆盖率低于阈值
**原因**: `pytest.ini` 设置了 `--cov-fail-under=60`
**解决**:
- 提高测试覆盖率
- 或临时调整阈值: `pytest --cov-fail-under=0`

---

## 📋 测试标记 (Markers)

项目定义了以下标记，可用于筛选测试：

| 标记 | 说明 | 示例 |
|-----|------|------|
| `@pytest.mark.unit` | 单元测试 | `pytest -m unit` |
| `@pytest.mark.integration` | 集成测试 | `pytest -m integration` |
| `@pytest.mark.e2e` | 端到端测试 | `pytest -m e2e` |
| `@pytest.mark.slow` | 慢速测试 | `pytest -m "not slow"` |
| `@pytest.mark.auth` | 认证测试 | `pytest -m auth` |
| `@pytest.mark.api` | API测试 | `pytest -m api` |
| `@pytest.mark.permissions` | 权限测试 | `pytest -m permissions` |

### 组合标记
```powershell
# 快速单元测试（排除慢速）
pytest -m "unit and not slow"

# 核心功能集成测试
pytest -m "(auth or project) and integration"
```

---

## 🎯 测试最佳实践

### 1. 测试隔离
- 每个测试独立运行
- 使用 fixture 管理测试数据
- 测试后清理资源

### 2. 命名规范
- 测试文件: `test_*.py`
- 测试类: `Test*`
- 测试函数: `test_*`

### 3. 断言清晰
```python
# ❌ 不好
assert response.status_code == 200

# ✅ 好
assert response.status_code == 200, f"期望200，实际{response.status_code}"
```

### 4. 使用参数化
```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input, expected):
    assert input * 2 == expected
```

---

## 📞 获取帮助

- **测试执行计划**: [TEST_EXECUTION_PLAN.md](./TEST_EXECUTION_PLAN.md)
- **Pytest 文档**: https://docs.pytest.org/
- **项目测试**: `backend/tests/` 目录

---

**准备就绪！开始测试你的后端代码吧！** 🚀
