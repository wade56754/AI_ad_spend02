---
version: v1.0
status: ready_for_production
layer: dev-guide
owner: wade
last_reviewed: 2025-11-27
baseline: MASTER.md v3.4, SoT Freeze v2.6
---

# TESTING_STRATEGY.md - AI广告代投系统测试策略

---

## 目录

1. [测试哲学与原则](#1-测试哲学与原则)
2. [测试金字塔](#2-测试金字塔)
3. [后端测试策略](#3-后端测试策略)
4. [前端测试策略](#4-前端测试策略)
5. [API契约测试](#5-api契约测试)
6. [状态机测试](#6-状态机测试)
7. [不变量测试](#7-不变量测试)
8. [测试数据管理](#8-测试数据管理)
9. [CI/CD集成](#9-cicd集成)
10. [覆盖率要求](#10-覆盖率要求)
11. [测试最佳实践](#11-测试最佳实践)
12. [附录：SoT引用索引](#12-附录sot引用索引)

---

## 1. 测试哲学与原则

### 1.1 核心测试哲学

**测试目标**: 通过自动化测试保障系统核心不变量，防止业务逻辑违反SoT定义的规则。

**测试信条**:
1. **测试裁判规则，而非实现细节** - 测试应验证SoT中定义的不变量，而非代码实现方式
2. **失败快，失败清晰** - 测试失败时应立即定位到违反的具体业务规则（如BR-FIN-003）
3. **测试即文档** - 测试用例应清晰展示业务场景，成为可执行的规范
4. **隔离性优先** - 单元测试不依赖外部服务，集成测试使用固定测试数据库

### 1.2 测试原则

| 原则 | 描述 | 示例 |
|------|------|------|
| **SoT驱动测试** | 所有测试必须明确引用对应的SoT规则 | `# Test: INV-001 - PROJECT账本独立核算` |
| **状态机覆盖** | 覆盖STATE_MACHINE.md v2.6中所有合法流转 | 测试`final_pending → final_confirmed` |
| **边界值测试** | 测试临界状态（如余额=0, 终态锁定后） | 账户余额为0.00时禁止扣款 |
| **错误码验证** | 所有异常场景必须验证ERROR_CODES_SOT v2.1中的错误码 | 断言`code == "BIZ_101"` |
| **幂等性验证** | 可重复操作必须测试幂等性 | 重复提交充值请求不应创建多笔记录 |

### 1.3 测试不应做什么

❌ **禁止**: 绕过状态机直接修改数据库状态
❌ **禁止**: 使用Float/Double进行金额断言（违反BR-FIN-003）
❌ **禁止**: 硬编码未在SoT中定义的状态/错误码
❌ **禁止**: 测试私有方法实现细节
❌ **禁止**: 依赖测试执行顺序（每个测试必须独立）

---

## 2. 测试金字塔

### 2.1 测试层次分布

```
           /\
          /E2E\         10% - 端到端测试（关键业务流程）
         /------\
        /  集成  \       30% - 集成测试（API + Service + DB）
       /----------\
      /   单元测试   \    60% - 单元测试（纯逻辑、工具函数）
     /--------------\
```

### 2.2 各层职责

#### 单元测试 (60%)
- **测试对象**: Service层业务逻辑、工具函数、Schema验证
- **隔离方式**: Mock数据库、Mock外部依赖
- **运行速度**: 毫秒级
- **覆盖率要求**: ≥90%

**示例场景**:
- 计费公式: `revenue = conversions_final × unit_price`
- 金额精度验证: `Decimal("100.00")` 保留2位小数
- 日期校验: 禁止未来日期的日报

#### 集成测试 (30%)
- **测试对象**: API端点 + Service + 数据库交互
- **隔离方式**: 使用测试数据库（SQLite/PostgreSQL）
- **运行速度**: 秒级
- **覆盖率要求**: 所有API端点

**示例场景**:
- `POST /api/v1/daily-reports` 创建日报并验证状态机流转
- `PUT /api/v1/topup-requests/{id}/approve` 充值审批并验证账本记录
- 权限验证: 非finance角色禁止修改Ledger

#### E2E测试 (10%)
- **测试对象**: 完整业务流程（前端 + 后端 + 数据库）
- **隔离方式**: 独立测试环境
- **运行速度**: 分钟级
- **覆盖率要求**: 核心业务路径

**示例场景**:
- 完整充值流程: 创建申请 → 数据员审核 → 财务审批 → 标记已付款 → 生成账本记录
- 日报确认流程: raw提交 → 趋势检查 → final确认 → 计费入账
- 死号迁移流程: 创建迁移申请 → 审批 → 执行双向账本记录

---

## 3. 后端测试策略

### 3.1 技术栈

| 组件 | 技术选型 | 版本 |
|------|---------|------|
| 测试框架 | pytest | ≥7.0 |
| 测试客户端 | FastAPI TestClient | - |
| 数据库 | SQLite (单元测试) + PostgreSQL (集成测试) | - |
| Mock库 | unittest.mock | - |
| 覆盖率工具 | pytest-cov | ≥4.0 |

### 3.2 测试文件结构

```
backend/tests/
├── conftest.py                    # 共享fixtures
├── test_*.py                      # 集成测试（API端点）
├── services/
│   ├── test_daily_report_service.py   # Service层单元测试
│   ├── test_topup_service.py
│   └── test_ledger_service.py
├── unit/
│   ├── test_error_codes.py            # 错误码覆盖测试
│   ├── test_business_rules.py         # 业务规则单元测试
│   └── test_state_machine.py          # 状态机逻辑测试
└── integration/
    ├── test_daily_report_flow.py      # 完整业务流程测试
    └── test_topup_flow.py
```

### 3.3 Fixtures设计模式

#### 3.3.1 数据库Fixture

```python
# conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.core.db import Base

@pytest.fixture(scope="function")
def db_session():
    """
    测试数据库会话
    - 每个测试函数独立会话
    - 测试结束后自动回滚
    """
    engine = create_engine("sqlite:///./test.db")
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)
```

#### 3.3.2 用户角色Fixture

```python
# conftest.py
from uuid import uuid4
from backend.models import User

@pytest.fixture
def admin_user(db_session):
    """管理员用户 - 拥有所有权限"""
    user = User(
        id=uuid4(),
        email="admin@test.com",
        username="admin",
        role="admin",  # 角色必须来自STATE_MACHINE.md §2
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def finance_user(db_session):
    """财务用户 - 仅可操作Ledger和充值审批"""
    user = User(
        id=uuid4(),
        email="finance@test.com",
        username="finance",
        role="finance",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def media_buyer_user(db_session):
    """投手 - 仅可提交raw数据"""
    user = User(
        id=uuid4(),
        email="buyer@test.com",
        username="buyer",
        role="media_buyer",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user
```

#### 3.3.3 业务实体Fixture

```python
# conftest.py
from decimal import Decimal
from datetime import date
from backend.models import Project, AdAccount, DailyReport

@pytest.fixture
def active_project(db_session, admin_user):
    """活跃项目 - 用于测试计费逻辑"""
    project = Project(
        name="测试项目A",
        client_name="客户A",
        client_company="公司A",
        unit_price=Decimal("10.00"),  # 遵循BR-FIN-003: 使用Decimal
        status="active",  # 状态来自STATE_MACHINE.md §5
        created_by=admin_user.id
    )
    db_session.add(project)
    db_session.commit()
    return project

@pytest.fixture
def test_ad_account(db_session, active_project):
    """测试广告账户"""
    account = AdAccount(
        name="测试账户001",
        project_id=active_project.id,
        platform="tiktok",
        status="active",  # 状态来自STATE_MACHINE.md §7.1
        balance=Decimal("1000.00")
    )
    db_session.add(account)
    db_session.commit()
    return account
```

### 3.4 Service层单元测试示例

#### 3.4.1 测试计费公式（INV-001）

```python
# tests/services/test_daily_report_service.py
import pytest
from decimal import Decimal
from datetime import date
from backend.services.daily_report_service import DailyReportService
from backend.schemas.daily_report import DailyReportCreateRequest

class TestDailyReportBilling:
    """
    测试目标: 验证 INV-001 - PROJECT账本计费公式
    引用: MASTER.md v3.4 §INV-001
    公式: revenue = conversions_final × unit_price
    """

    def test_revenue_calculation_basic(self, db_session, test_ad_account, media_buyer_user):
        """
        场景: 基础计费计算
        Given: unit_price=10.00, conversions_final=5
        When: 日报流转至final_locked
        Then: 生成 REVENUE=50.00 的账本记录
        """
        service = DailyReportService(db_session)

        # 创建日报
        request = DailyReportCreateRequest(
            report_date=date(2024, 1, 15),
            ad_account_id=test_ad_account.id,
            conversions_final=5
        )
        report = service.create_daily_report(request, media_buyer_user)

        # 流转至final_locked
        service.lock_final_data(report.id)

        # 验证账本记录
        from backend.models import LedgerEntry
        ledger = db_session.query(LedgerEntry).filter(
            LedgerEntry.daily_report_id == report.id,
            LedgerEntry.ledger_type == "PROJECT",
            LedgerEntry.entry_type == "REVENUE"
        ).first()

        assert ledger is not None, "未生成REVENUE账本记录"
        assert ledger.amount == Decimal("50.00"), f"计费金额错误: {ledger.amount}"
        assert ledger.project_id == test_ad_account.project_id

    def test_zero_conversions_no_billing(self, db_session, test_ad_account, media_buyer_user):
        """
        场景: 零转化不计费
        Given: conversions_final=0
        When: 日报流转至final_locked
        Then: 不生成REVENUE记录
        引用: MASTER.md v3.4 §INV-001 计费触发条件
        """
        service = DailyReportService(db_session)

        request = DailyReportCreateRequest(
            report_date=date(2024, 1, 15),
            ad_account_id=test_ad_account.id,
            conversions_final=0
        )
        report = service.create_daily_report(request, media_buyer_user)
        service.lock_final_data(report.id)

        from backend.models import LedgerEntry
        ledger_count = db_session.query(LedgerEntry).filter(
            LedgerEntry.daily_report_id == report.id,
            LedgerEntry.entry_type == "REVENUE"
        ).count()

        assert ledger_count == 0, "零转化不应生成计费记录"

    def test_decimal_precision(self, db_session, test_ad_account, media_buyer_user):
        """
        场景: 金额精度验证
        Given: unit_price=12.34, conversions_final=3
        When: 计算revenue
        Then: 精确保留2位小数 (12.34 × 3 = 37.02)
        引用: BR-FIN-003 - 金额必用Decimal
        """
        # 修改项目单价
        test_ad_account.project.unit_price = Decimal("12.34")
        db_session.commit()

        service = DailyReportService(db_session)
        request = DailyReportCreateRequest(
            report_date=date(2024, 1, 15),
            ad_account_id=test_ad_account.id,
            conversions_final=3
        )
        report = service.create_daily_report(request, media_buyer_user)
        service.lock_final_data(report.id)

        from backend.models import LedgerEntry
        ledger = db_session.query(LedgerEntry).filter(
            LedgerEntry.daily_report_id == report.id,
            LedgerEntry.entry_type == "REVENUE"
        ).first()

        assert ledger.amount == Decimal("37.02")
        # 验证是Decimal类型，不是Float
        assert isinstance(ledger.amount, Decimal), "金额必须是Decimal类型"
```

#### 3.4.2 测试状态机流转（STATE_MACHINE.md §8）

```python
# tests/services/test_daily_report_service.py
class TestDailyReportStateMachine:
    """
    测试目标: 验证日报状态机合法流转
    引用: STATE_MACHINE.md v2.6 §8
    合法流转: raw_submitted → trend_pending → trend_ok →
             trend_resolved → final_pending → final_confirmed → final_locked
    """

    def test_valid_state_transitions(self, db_session, test_ad_account, media_buyer_user):
        """
        场景: 完整合法流转路径
        Given: 新建日报 (status=raw_submitted)
        When: 按状态机顺序流转
        Then: 每个流转成功，最终到达final_locked
        """
        service = DailyReportService(db_session)

        # 1. 创建日报 -> raw_submitted
        request = DailyReportCreateRequest(
            report_date=date(2024, 1, 15),
            ad_account_id=test_ad_account.id,
            conversions_raw=10
        )
        report = service.create_daily_report(request, media_buyer_user)
        assert report.status == "raw_submitted"

        # 2. 触发趋势检查 -> trend_pending
        service.trigger_trend_check(report.id)
        db_session.refresh(report)
        assert report.status == "trend_pending"

        # 3. 趋势检查通过 -> trend_ok
        service.approve_trend(report.id)
        db_session.refresh(report)
        assert report.status == "trend_ok"

        # 4. 趋势解决 -> trend_resolved
        service.resolve_trend(report.id)
        db_session.refresh(report)
        assert report.status == "trend_resolved"

        # 5. 提交final数据 -> final_pending
        service.submit_final_data(report.id, conversions_final=8)
        db_session.refresh(report)
        assert report.status == "final_pending"

        # 6. 确认final -> final_confirmed
        service.confirm_final_data(report.id)
        db_session.refresh(report)
        assert report.status == "final_confirmed"

        # 7. 锁定 -> final_locked (终态)
        service.lock_final_data(report.id)
        db_session.refresh(report)
        assert report.status == "final_locked"

    def test_invalid_state_transition(self, db_session, test_ad_account, media_buyer_user):
        """
        场景: 非法状态跳转
        Given: 日报状态=raw_submitted
        When: 尝试直接跳转至final_locked
        Then: 抛出 BusinessLogicError, code=STATE_001
        引用: ERROR_CODES_SOT.md v2.1 - STATE_001
        """
        service = DailyReportService(db_session)

        request = DailyReportCreateRequest(
            report_date=date(2024, 1, 15),
            ad_account_id=test_ad_account.id
        )
        report = service.create_daily_report(request, media_buyer_user)

        from backend.exceptions.custom_exceptions import BusinessLogicError
        with pytest.raises(BusinessLogicError) as exc_info:
            service.lock_final_data(report.id)  # 跳过中间状态

        assert exc_info.value.code == "STATE_001"
        assert "非法状态流转" in exc_info.value.message

    def test_terminal_state_immutability(self, db_session, test_ad_account, media_buyer_user):
        """
        场景: 终态不可回退
        Given: 日报已流转至final_locked
        When: 尝试修改conversions_final
        Then: 抛出 BusinessLogicError, code=STATE_002
        引用: STATE_MACHINE.md v2.6 §8 - 终态保护
        """
        service = DailyReportService(db_session)

        # 创建并流转至终态
        request = DailyReportCreateRequest(
            report_date=date(2024, 1, 15),
            ad_account_id=test_ad_account.id,
            conversions_final=5
        )
        report = service.create_daily_report(request, media_buyer_user)
        # ... 省略中间流转步骤 ...
        service.lock_final_data(report.id)

        # 尝试修改终态数据
        from backend.exceptions.custom_exceptions import BusinessLogicError
        with pytest.raises(BusinessLogicError) as exc_info:
            service.update_conversions(report.id, conversions_final=10)

        assert exc_info.value.code == "STATE_002"
        assert "终态数据已锁定" in exc_info.value.message
```

### 3.5 API集成测试示例

```python
# tests/test_daily_report_api.py
import pytest
from fastapi.testclient import TestClient
from decimal import Decimal

class TestDailyReportAPI:
    """
    测试目标: 验证API契约与权限控制
    引用: API_SOT.md v9.0 §9
    """

    def test_create_daily_report_success(self, client, auth_headers, test_ad_account):
        """
        场景: 成功创建日报
        API: POST /api/v1/daily-reports
        引用: API_SOT.md v9.0 §9.1
        """
        payload = {
            "report_date": "2024-01-15",
            "ad_account_id": test_ad_account.id,
            "conversions_raw": 10,
            "raw_spend": "100.00"
        }

        response = client.post(
            "/api/v1/daily-reports",
            json=payload,
            headers=auth_headers
        )

        # 验证Envelope格式
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "request_id" in data
        assert "timestamp" in data

        # 验证业务数据
        report = data["data"]
        assert report["status"] == "raw_submitted"
        assert report["conversions_raw"] == 10

    def test_permission_denied_non_finance_modify_ledger(self, client, media_buyer_user, test_ad_account):
        """
        场景: 非finance角色禁止修改账本
        API: POST /api/v1/ledger-entries (手工调账)
        引用: AUTH_SPEC.md v2.0 - 权限矩阵
        """
        # 使用media_buyer身份
        token = create_access_token({"sub": str(media_buyer_user.id), "role": "media_buyer"})
        headers = {"Authorization": f"Bearer {token}"}

        payload = {
            "ledger_type": "PROJECT",
            "entry_type": "MANUAL_ADJUSTMENT",
            "amount": "50.00"
        }

        response = client.post(
            "/api/v1/ledger-entries",
            json=payload,
            headers=headers
        )

        # 验证权限拒绝
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert data["code"] == "AUTH_500"  # ERROR_CODES_SOT.md v2.1
        assert "权限不足" in data["message"]
```

### 3.6 覆盖率配置

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --cov=backend
    --cov-report=html
    --cov-report=term
    --cov-fail-under=90
    --strict-markers
    -v

markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (require DB)
    e2e: End-to-end tests (slow)
    state_machine: State machine transition tests
    invariant: System invariant tests
```

---

## 4. 前端测试策略

### 4.1 技术栈

| 组件 | 技术选型 | 版本 |
|------|---------|------|
| 测试框架 | Jest | ^29.7.0 |
| React测试库 | @testing-library/react | ^16.0.1 |
| 用户交互模拟 | @testing-library/user-event | ^14.5.2 |
| DOM断言 | @testing-library/jest-dom | ^6.5.0 |

### 4.2 测试分类

#### 4.2.1 组件单元测试

**测试对象**: 展示型组件、UI组件库
**隔离方式**: Mock API调用、Mock路由

```typescript
// __tests__/components/DailyReportCard.test.tsx
import { render, screen } from '@testing-library/react'
import { DailyReportCard } from '@/components/daily-reports/DailyReportCard'

describe('DailyReportCard', () => {
  it('should render report data correctly', () => {
    const mockReport = {
      id: 1,
      report_date: '2024-01-15',
      status: 'final_locked',
      conversions_final: 5,
      revenue: '50.00'
    }

    render(<DailyReportCard report={mockReport} />)

    expect(screen.getByText('2024-01-15')).toBeInTheDocument()
    expect(screen.getByText('已锁定')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('¥50.00')).toBeInTheDocument()
  })

  it('should show locked badge for final_locked status', () => {
    /**
     * 测试目标: 验证终态UI展示
     * 引用: STATE_MACHINE.md v2.6 §8 - final_locked为终态
     */
    const mockReport = {
      id: 1,
      status: 'final_locked'
    }

    render(<DailyReportCard report={mockReport} />)

    const badge = screen.getByRole('status')
    expect(badge).toHaveClass('badge-locked')
    expect(badge).toHaveTextContent('已锁定')
  })
})
```

#### 4.2.2 集成测试（页面级）

```typescript
// __tests__/pages/DailyReportsPage.test.tsx
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DailyReportsPage } from '@/app/daily-reports/page'
import { apiFetch } from '@/lib/api'

// Mock API调用
jest.mock('@/lib/api')

describe('DailyReportsPage', () => {
  beforeEach(() => {
    // 重置Mock
    jest.clearAllMocks()
  })

  it('should fetch and display daily reports', async () => {
    /**
     * 测试目标: 验证日报列表加载
     * API: GET /api/v1/daily-reports
     * 引用: API_SOT.md v9.0 §9.2
     */
    const mockReports = {
      success: true,
      data: {
        items: [
          { id: 1, report_date: '2024-01-15', status: 'final_locked' },
          { id: 2, report_date: '2024-01-16', status: 'trend_pending' }
        ],
        total: 2
      }
    }

    ;(apiFetch as jest.Mock).mockResolvedValueOnce(mockReports)

    render(<DailyReportsPage />)

    // 等待数据加载
    await waitFor(() => {
      expect(screen.getByText('2024-01-15')).toBeInTheDocument()
      expect(screen.getByText('2024-01-16')).toBeInTheDocument()
    })

    // 验证API调用
    expect(apiFetch).toHaveBeenCalledWith('/api/v1/daily-reports', {
      method: 'GET'
    })
  })

  it('should handle API error with proper error code', async () => {
    /**
     * 测试目标: 验证错误处理
     * 引用: ERROR_CODES_SOT.md v2.1 - BIZ_001
     */
    const mockError = {
      success: false,
      code: 'BIZ_001',
      message: '查询失败'
    }

    ;(apiFetch as jest.Mock).mockRejectedValueOnce(mockError)

    render(<DailyReportsPage />)

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('查询失败')
    })
  })
})
```

#### 4.2.3 用户交互测试

```typescript
// __tests__/features/TopupRequestFlow.test.tsx
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TopupRequestForm } from '@/components/topup/TopupRequestForm'
import { apiFetch } from '@/lib/api'

jest.mock('@/lib/api')

describe('TopupRequestFlow', () => {
  it('should create topup request successfully', async () => {
    /**
     * 测试目标: 验证充值申请创建流程
     * API: POST /api/v1/topup-requests
     * 引用: API_SOT.md v9.0 §10.1
     */
    const user = userEvent.setup()

    ;(apiFetch as jest.Mock).mockResolvedValueOnce({
      success: true,
      data: { id: 1, status: 'draft' }
    })

    render(<TopupRequestForm />)

    // 填写表单
    await user.type(screen.getByLabelText('充值金额'), '1000')
    await user.selectOptions(screen.getByLabelText('广告账户'), '1')
    await user.click(screen.getByRole('button', { name: '提交申请' }))

    // 验证API调用
    await waitFor(() => {
      expect(apiFetch).toHaveBeenCalledWith('/api/v1/topup-requests', {
        method: 'POST',
        body: JSON.stringify({
          amount: '1000.00',
          ad_account_id: 1
        })
      })
    })

    // 验证成功提示
    expect(screen.getByText('充值申请已提交')).toBeInTheDocument()
  })

  it('should validate amount precision (2 decimal places)', async () => {
    /**
     * 测试目标: 验证金额精度校验
     * 引用: BR-FIN-003 - 金额必保留2位小数
     */
    const user = userEvent.setup()
    render(<TopupRequestForm />)

    // 输入超过2位小数的金额
    await user.type(screen.getByLabelText('充值金额'), '100.123')
    await user.click(screen.getByRole('button', { name: '提交申请' }))

    // 验证前端校验
    expect(screen.getByText('金额最多保留2位小数')).toBeInTheDocument()
  })
})
```

### 4.3 Mock策略

#### 4.3.1 API Mock工厂

```typescript
// __tests__/utils/mockApi.ts
import { apiFetch } from '@/lib/api'

export const mockApiSuccess = <T>(data: T) => {
  (apiFetch as jest.Mock).mockResolvedValueOnce({
    success: true,
    data,
    request_id: 'test-request-id',
    timestamp: '2024-01-15T10:00:00Z'
  })
}

export const mockApiError = (code: string, message: string) => {
  (apiFetch as jest.Mock).mockRejectedValueOnce({
    success: false,
    code,
    message,
    request_id: 'test-request-id',
    timestamp: '2024-01-15T10:00:00Z'
  })
}

// 使用示例
mockApiSuccess({ items: [], total: 0 })
mockApiError('AUTH_001', '用户未登录')
```

---

## 5. API契约测试

### 5.1 契约测试目标

验证前后端API契约一致性，确保：
1. 请求参数符合API_SOT.md定义
2. 响应格式符合Envelope规范
3. 错误码符合ERROR_CODES_SOT.md
4. 字段类型与DATA_SCHEMA.md一致

### 5.2 契约测试示例

```python
# tests/integration/test_api_contract.py
import pytest
from decimal import Decimal

class TestDailyReportAPIContract:
    """
    测试目标: 验证日报API契约
    引用: API_SOT.md v9.0 §9
    """

    def test_create_daily_report_request_schema(self, client, auth_headers, test_ad_account):
        """
        场景: 验证请求Schema
        API: POST /api/v1/daily-reports
        Schema: DailyReportCreateRequest
        """
        # 完整有效载荷
        valid_payload = {
            "report_date": "2024-01-15",
            "ad_account_id": test_ad_account.id,
            "conversions_raw": 10,
            "raw_spend": "100.00",
            "impressions": 10000,
            "clicks": 500
        }

        response = client.post(
            "/api/v1/daily-reports",
            json=valid_payload,
            headers=auth_headers
        )
        assert response.status_code == 201

    def test_create_daily_report_response_envelope(self, client, auth_headers, test_ad_account):
        """
        场景: 验证响应Envelope格式
        引用: API_SOT.md v9.0 §4 - 响应格式规范
        """
        payload = {
            "report_date": "2024-01-15",
            "ad_account_id": test_ad_account.id
        }

        response = client.post(
            "/api/v1/daily-reports",
            json=payload,
            headers=auth_headers
        )

        data = response.json()

        # 验证Envelope必需字段
        assert "success" in data
        assert "message" in data
        assert "data" in data
        assert "request_id" in data
        assert "timestamp" in data

        # 验证类型
        assert isinstance(data["success"], bool)
        assert isinstance(data["data"], dict)
        assert isinstance(data["request_id"], str)
        assert isinstance(data["timestamp"], str)

    def test_error_response_contract(self, client, auth_headers):
        """
        场景: 验证错误响应契约
        引用: ERROR_CODES_SOT.md v2.1
        """
        # 请求不存在的资源
        response = client.get(
            "/api/v1/daily-reports/999999",
            headers=auth_headers
        )

        assert response.status_code == 404
        data = response.json()

        # 验证错误Envelope
        assert data["success"] is False
        assert "code" in data
        assert "message" in data
        assert data["data"] is None

        # 验证错误码格式
        assert data["code"].startswith("BIZ_") or data["code"].startswith("AUTH_")

    def test_field_types_match_schema(self, client, auth_headers, test_ad_account):
        """
        场景: 验证字段类型与DATA_SCHEMA.md一致
        引用: DATA_SCHEMA.md v5.2 §3.3.3
        """
        payload = {
            "report_date": "2024-01-15",
            "ad_account_id": test_ad_account.id,
            "conversions_raw": 10,
            "raw_spend": "100.00"
        }

        response = client.post(
            "/api/v1/daily-reports",
            json=payload,
            headers=auth_headers
        )

        report = response.json()["data"]

        # 验证字段类型
        assert isinstance(report["id"], int)  # BIGSERIAL
        assert isinstance(report["report_date"], str)  # DATE -> ISO string
        assert isinstance(report["conversions_raw"], int)  # INTEGER
        assert isinstance(report["raw_spend"], str)  # DECIMAL -> string
        assert isinstance(report["status"], str)  # VARCHAR
        assert isinstance(report["created_at"], str)  # TIMESTAMPTZ -> ISO string

        # 验证金额格式（2位小数）
        import re
        assert re.match(r'^\d+\.\d{2}$', report["raw_spend"])
```

---

## 6. 状态机测试

### 6.1 状态机测试策略

**测试目标**: 验证STATE_MACHINE.md v2.6中定义的所有状态流转规则

**覆盖要求**:
1. 所有合法流转路径
2. 所有非法流转（应抛出STATE_001错误）
3. 终态保护（应抛出STATE_002错误）
4. 权限控制（不同角色的流转权限）

### 6.2 状态机测试矩阵

#### 6.2.1 日报状态机 (STATE_MACHINE.md §8)

```python
# tests/unit/test_daily_report_state_machine.py
import pytest
from backend.services.daily_report_service import DailyReportService
from backend.exceptions.custom_exceptions import BusinessLogicError

class TestDailyReportStateMachine:
    """
    测试目标: 完整覆盖日报8状态机
    状态流转: raw_submitted → trend_pending → trend_ok/trend_flagged
             → trend_resolved → final_pending → final_confirmed → final_locked
    引用: STATE_MACHINE.md v2.6 §8
    """

    # 合法流转矩阵
    VALID_TRANSITIONS = [
        ("raw_submitted", "trigger_trend_check", "trend_pending"),
        ("trend_pending", "approve_trend", "trend_ok"),
        ("trend_pending", "flag_trend", "trend_flagged"),
        ("trend_ok", "resolve_trend", "trend_resolved"),
        ("trend_flagged", "resolve_trend", "trend_resolved"),
        ("trend_resolved", "submit_final_data", "final_pending"),
        ("final_pending", "confirm_final_data", "final_confirmed"),
        ("final_confirmed", "lock_final_data", "final_locked"),
    ]

    # 非法流转矩阵
    INVALID_TRANSITIONS = [
        ("raw_submitted", "lock_final_data", "STATE_001"),  # 跳过中间状态
        ("trend_pending", "submit_final_data", "STATE_001"),  # 未解决趋势
        ("final_locked", "submit_final_data", "STATE_002"),  # 终态不可修改
    ]

    @pytest.mark.parametrize("from_state,action,to_state", VALID_TRANSITIONS)
    def test_valid_transitions(self, db_session, from_state, action, to_state):
        """
        场景: 测试所有合法流转
        Given: 日报处于from_state
        When: 执行action
        Then: 状态流转至to_state
        """
        service = DailyReportService(db_session)
        report = self._create_report_in_state(db_session, from_state)

        # 执行动作
        action_method = getattr(service, action)
        action_method(report.id)

        # 验证状态
        db_session.refresh(report)
        assert report.status == to_state

    @pytest.mark.parametrize("from_state,action,expected_error", INVALID_TRANSITIONS)
    def test_invalid_transitions(self, db_session, from_state, action, expected_error):
        """
        场景: 测试所有非法流转
        Given: 日报处于from_state
        When: 尝试非法流转
        Then: 抛出BusinessLogicError，错误码=expected_error
        """
        service = DailyReportService(db_session)
        report = self._create_report_in_state(db_session, from_state)

        with pytest.raises(BusinessLogicError) as exc_info:
            action_method = getattr(service, action)
            action_method(report.id)

        assert exc_info.value.code == expected_error

    def _create_report_in_state(self, db_session, state: str):
        """辅助方法: 创建指定状态的日报"""
        # 实现省略...
        pass
```

#### 6.2.2 充值状态机 (STATE_MACHINE.md §10.2)

```python
# tests/unit/test_topup_state_machine.py
class TestTopupStateMachine:
    """
    测试目标: 充值状态机完整覆盖
    状态流转: draft → pending_review → finance_approve → paid → completed
    引用: STATE_MACHINE.md v2.6 §10.2
    """

    VALID_TRANSITIONS = [
        ("draft", "submit_for_review", "pending_review", "data_operator"),
        ("pending_review", "approve_by_data", "finance_approve", "data_operator"),
        ("pending_review", "reject", "rejected", "data_operator"),
        ("finance_approve", "mark_as_paid", "paid", "finance"),
        ("paid", "confirm_receipt", "completed", "system"),
    ]

    @pytest.mark.parametrize("from_state,action,to_state,role", VALID_TRANSITIONS)
    def test_valid_transitions_with_permissions(
        self, db_session, from_state, action, to_state, role
    ):
        """
        场景: 验证状态流转的权限控制
        Given: 充值申请处于from_state
        When: 指定角色执行action
        Then: 状态流转至to_state
        引用: AUTH_SPEC.md v2.0 - 充值审批权限
        """
        service = TopupService(db_session)
        request = self._create_topup_in_state(db_session, from_state)
        user = self._create_user_with_role(db_session, role)

        # 执行动作
        action_method = getattr(service, action)
        action_method(request.id, user)

        # 验证状态
        db_session.refresh(request)
        assert request.status == to_state

    def test_wrong_role_permission_denied(self, db_session):
        """
        场景: 错误角色执行流转被拒绝
        Given: 充值申请状态=finance_approve
        When: media_buyer尝试标记已付款
        Then: 抛出PermissionDeniedError, code=AUTH_500
        """
        service = TopupService(db_session)
        request = self._create_topup_in_state(db_session, "finance_approve")
        buyer = self._create_user_with_role(db_session, "media_buyer")

        from backend.exceptions.custom_exceptions import PermissionDeniedError
        with pytest.raises(PermissionDeniedError) as exc_info:
            service.mark_as_paid(request.id, buyer)

        assert exc_info.value.code == "AUTH_500"
```

---

## 7. 不变量测试

### 7.1 系统不变量定义

**引用**: MASTER.md v3.4 第二章

| 不变量编号 | 描述 | 测试类型 |
|----------|------|---------|
| INV-001 | 双账本独立核算 | 集成测试 |
| INV-002 | 三数据流分离 | 单元测试 |
| INV-003 | 审计不可逆 | 集成测试 |

### 7.2 INV-001: 双账本独立核算测试

```python
# tests/integration/test_invariant_dual_ledger.py
import pytest
from decimal import Decimal
from backend.models import LedgerEntry

class TestInvariantDualLedger:
    """
    测试目标: 验证 INV-001 - 双账本独立核算不变量
    引用: MASTER.md v3.4 §INV-001
    """

    def test_project_ledger_only_revenue(self, db_session, test_daily_report):
        """
        场景: PROJECT账本仅记录收入
        Given: 日报流转至final_locked
        When: 生成账本记录
        Then: PROJECT账本仅包含REVENUE类型
        """
        # 流转至终态，触发计费
        service = DailyReportService(db_session)
        service.lock_final_data(test_daily_report.id)

        # 查询PROJECT账本
        project_entries = db_session.query(LedgerEntry).filter(
            LedgerEntry.ledger_type == "PROJECT",
            LedgerEntry.project_id == test_daily_report.ad_account.project_id
        ).all()

        # 验证仅包含REVENUE
        for entry in project_entries:
            assert entry.entry_type in ["REVENUE", "TOPUP", "REVERSAL"], \
                f"PROJECT账本包含非法类型: {entry.entry_type}"
            assert entry.supplier_id is None, "PROJECT账本不应关联supplier_id"

    def test_supplier_ledger_only_cost(self, db_session, test_ad_account):
        """
        场景: SUPPLIER账本仅记录成本
        Given: 录入real_spend
        When: 生成成本账本
        Then: SUPPLIER账本仅包含COST类型
        """
        # 创建供应商成本记录
        service = LedgerService(db_session)
        service.record_supplier_cost(
            ad_account_id=test_ad_account.id,
            real_spend=Decimal("100.00")
        )

        # 查询SUPPLIER账本
        supplier_entries = db_session.query(LedgerEntry).filter(
            LedgerEntry.ledger_type == "SUPPLIER",
            LedgerEntry.ad_account_id == test_ad_account.id
        ).all()

        # 验证仅包含COST相关类型
        for entry in supplier_entries:
            assert entry.entry_type in [
                "COST", "TOPUP", "TRANSFER_OUT", "TRANSFER_IN", "REVERSAL"
            ], f"SUPPLIER账本包含非法类型: {entry.entry_type}"
            assert entry.project_id is None, "SUPPLIER账本不应关联project_id"

    def test_ledger_balance_calculation(self, db_session, test_project):
        """
        场景: 账本余额=所有entries的sum
        Given: 多笔账本记录
        When: 计算余额
        Then: balance = SUM(ledger_entries.amount)
        引用: LEDGER_SOT.md v1.1 §2.1
        """
        service = LedgerService(db_session)

        # 创建多笔记录
        service.create_entry({
            "ledger_type": "PROJECT",
            "entry_type": "TOPUP",
            "project_id": test_project.id,
            "amount": Decimal("1000.00")
        })
        service.create_entry({
            "ledger_type": "PROJECT",
            "entry_type": "REVENUE",
            "project_id": test_project.id,
            "amount": Decimal("-50.00")
        })

        # 计算余额
        entries = db_session.query(LedgerEntry).filter(
            LedgerEntry.ledger_type == "PROJECT",
            LedgerEntry.project_id == test_project.id
        ).all()

        calculated_balance = sum(e.amount for e in entries)

        # 验证余额
        db_session.refresh(test_project)
        assert test_project.balance == calculated_balance
        assert test_project.balance == Decimal("950.00")
```

### 7.3 INV-002: 三数据流分离测试

```python
# tests/unit/test_invariant_triple_stream.py
class TestInvariantTripleStream:
    """
    测试目标: 验证 INV-002 - 三数据流分离
    引用: MASTER.md v3.4 §1.3
    """

    def test_raw_stream_no_billing(self, db_session, test_daily_report):
        """
        场景: raw数据流不触发计费
        Given: 提交conversions_raw=10
        When: 日报状态=raw_submitted
        Then: 不生成REVENUE账本记录
        """
        assert test_daily_report.conversions_raw == 10
        assert test_daily_report.status == "raw_submitted"

        # 查询账本
        revenue_count = db_session.query(LedgerEntry).filter(
            LedgerEntry.daily_report_id == test_daily_report.id,
            LedgerEntry.entry_type == "REVENUE"
        ).count()

        assert revenue_count == 0, "raw数据不应触发计费"

    def test_real_stream_cost_only(self, db_session, test_daily_report):
        """
        场景: real数据流仅用于成本核算
        Given: 录入real_spend=80.00
        When: 状态=trend_resolved
        Then: 生成SUPPLIER COST记录，不生成PROJECT记录
        """
        service = DailyReportService(db_session)
        service.update_real_spend(test_daily_report.id, real_spend=Decimal("80.00"))

        # 验证SUPPLIER账本
        cost_entry = db_session.query(LedgerEntry).filter(
            LedgerEntry.daily_report_id == test_daily_report.id,
            LedgerEntry.ledger_type == "SUPPLIER",
            LedgerEntry.entry_type == "COST"
        ).first()

        assert cost_entry is not None
        assert cost_entry.amount == Decimal("-80.00")

        # 验证PROJECT账本无记录
        revenue_count = db_session.query(LedgerEntry).filter(
            LedgerEntry.daily_report_id == test_daily_report.id,
            LedgerEntry.ledger_type == "PROJECT"
        ).count()

        assert revenue_count == 0

    def test_final_stream_billing_only(self, db_session, test_daily_report):
        """
        场景: final数据流仅用于计费
        Given: conversions_final=5
        When: 状态=final_locked
        Then: 生成PROJECT REVENUE记录
        """
        service = DailyReportService(db_session)
        service.submit_final_data(test_daily_report.id, conversions_final=5)
        service.lock_final_data(test_daily_report.id)

        # 验证PROJECT账本
        revenue_entry = db_session.query(LedgerEntry).filter(
            LedgerEntry.daily_report_id == test_daily_report.id,
            LedgerEntry.ledger_type == "PROJECT",
            LedgerEntry.entry_type == "REVENUE"
        ).first()

        assert revenue_entry is not None
        assert revenue_entry.amount == Decimal("50.00")  # 5 × 10.00

    def test_no_reverse_inference(self, db_session, test_daily_report):
        """
        场景: 禁止从final反推raw
        Given: conversions_final=8
        When: 尝试反推conversions_raw
        Then: conversions_raw保持独立，不受final影响
        引用: MASTER.md v3.4 §1.3 - 禁止反向
        """
        original_raw = test_daily_report.conversions_raw

        service = DailyReportService(db_session)
        service.submit_final_data(test_daily_report.id, conversions_final=8)

        db_session.refresh(test_daily_report)

        # 验证raw数据未被修改
        assert test_daily_report.conversions_raw == original_raw
        assert test_daily_report.conversions_final == 8
```

### 7.4 INV-003: 审计不可逆测试

```python
# tests/integration/test_invariant_immutable_audit.py
class TestInvariantImmutableAudit:
    """
    测试目标: 验证 INV-003 - 审计不可逆
    引用: MASTER.md v3.4 §1.3.4
    """

    def test_ledger_entry_no_update(self, db_session, test_ledger_entry):
        """
        场景: 禁止UPDATE ledger_entries
        Given: 已存在账本记录
        When: 尝试UPDATE amount
        Then: 抛出BusinessLogicError, code=LEDGER_001
        """
        from backend.services.ledger_service import LedgerService
        from backend.exceptions.custom_exceptions import BusinessLogicError

        service = LedgerService(db_session)

        with pytest.raises(BusinessLogicError) as exc_info:
            service.update_entry(test_ledger_entry.id, amount=Decimal("200.00"))

        assert exc_info.value.code == "LEDGER_001"
        assert "禁止修改账本记录" in exc_info.value.message

    def test_ledger_entry_no_delete(self, db_session, test_ledger_entry):
        """
        场景: 禁止DELETE ledger_entries
        Given: 已存在账本记录
        When: 尝试DELETE
        Then: 抛出BusinessLogicError, code=LEDGER_002
        """
        from backend.services.ledger_service import LedgerService
        from backend.exceptions.custom_exceptions import BusinessLogicError

        service = LedgerService(db_session)

        with pytest.raises(BusinessLogicError) as exc_info:
            service.delete_entry(test_ledger_entry.id)

        assert exc_info.value.code == "LEDGER_002"
        assert "禁止删除账本记录" in exc_info.value.message

    def test_correction_via_reversal(self, db_session, test_ledger_entry):
        """
        场景: 修正唯一方式为REVERSAL（红冲）
        Given: 原账本记录 amount=+100.00
        When: 执行红冲
        Then: 生成新记录 entry_type=REVERSAL, amount=-100.00
        引用: LEDGER_SOT.md v1.1 §12
        """
        from backend.services.ledger_service import LedgerService

        service = LedgerService(db_session)
        original_amount = test_ledger_entry.amount

        # 执行红冲
        reversal = service.create_reversal(
            original_entry_id=test_ledger_entry.id,
            reason="数据错误修正"
        )

        # 验证红冲记录
        assert reversal.entry_type == "REVERSAL"
        assert reversal.amount == -original_amount
        assert reversal.reversal_of_id == test_ledger_entry.id
        assert reversal.reason == "数据错误修正"

        # 验证原记录未被修改
        db_session.refresh(test_ledger_entry)
        assert test_ledger_entry.amount == original_amount

        # 验证净值为0
        entries = db_session.query(LedgerEntry).filter(
            LedgerEntry.project_id == test_ledger_entry.project_id
        ).all()
        net_amount = sum(e.amount for e in entries)
        assert net_amount == Decimal("0.00")
```

---

## 8. 测试数据管理

### 8.1 测试数据原则

1. **隔离性**: 每个测试使用独立数据，测试间互不影响
2. **可重复性**: 测试数据确定，测试结果可复现
3. **SoT对齐**: 测试数据遵循DATA_SCHEMA.md定义
4. **真实性**: 测试数据模拟真实业务场景

### 8.2 Fixture工厂模式

```python
# tests/factories.py
from decimal import Decimal
from datetime import date, datetime, timezone
from uuid import uuid4
from backend.models import (
    User, Project, AdAccount, DailyReport, TopupRequest, LedgerEntry
)

class UserFactory:
    """用户工厂"""

    @staticmethod
    def create_user(db_session, role="admin", **kwargs):
        """
        创建测试用户
        角色必须为: admin/finance/data_operator/account_manager/media_buyer
        引用: STATE_MACHINE.md v2.6 §2
        """
        defaults = {
            "id": uuid4(),
            "email": f"{role}@test.com",
            "username": role,
            "role": role,
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        }
        defaults.update(kwargs)

        user = User(**defaults)
        db_session.add(user)
        db_session.commit()
        return user

    @staticmethod
    def create_admin(db_session):
        return UserFactory.create_user(db_session, role="admin")

    @staticmethod
    def create_finance(db_session):
        return UserFactory.create_user(db_session, role="finance")

class ProjectFactory:
    """项目工厂"""

    @staticmethod
    def create_project(db_session, created_by, **kwargs):
        """
        创建测试项目
        引用: DATA_SCHEMA.md v5.2 §3.2.1
        """
        defaults = {
            "name": f"测试项目{uuid4().hex[:8]}",
            "client_name": "测试客户",
            "client_company": "测试公司",
            "unit_price": Decimal("10.00"),  # BR-FIN-003: 使用Decimal
            "status": "active",
            "balance": Decimal("0.00"),
            "created_by": created_by.id,
            "created_at": datetime.now(timezone.utc)
        }
        defaults.update(kwargs)

        project = Project(**defaults)
        db_session.add(project)
        db_session.commit()
        return project

class DailyReportFactory:
    """日报工厂"""

    @staticmethod
    def create_report(db_session, ad_account, created_by, **kwargs):
        """
        创建测试日报
        引用: DATA_SCHEMA.md v5.2 §3.3.3
        """
        defaults = {
            "report_date": date(2024, 1, 15),
            "ad_account_id": ad_account.id,
            "status": "raw_submitted",  # STATE_MACHINE.md §8
            "conversions_raw": 10,
            "raw_spend": Decimal("100.00"),
            "created_by": created_by.id,
            "created_at": datetime.now(timezone.utc)
        }
        defaults.update(kwargs)

        report = DailyReport(**defaults)
        db_session.add(report)
        db_session.commit()
        return report

    @staticmethod
    def create_locked_report(db_session, ad_account, created_by):
        """创建已锁定的日报（用于测试终态）"""
        report = DailyReportFactory.create_report(
            db_session, ad_account, created_by,
            status="final_locked",
            conversions_final=5
        )
        return report

class LedgerFactory:
    """账本工厂"""

    @staticmethod
    def create_entry(db_session, ledger_type, entry_type, **kwargs):
        """
        创建账本记录
        引用: LEDGER_SOT.md v1.1 §3
        """
        defaults = {
            "ledger_type": ledger_type,  # PROJECT/SUPPLIER
            "entry_type": entry_type,    # REVENUE/COST/TOPUP/TRANSFER/REVERSAL
            "amount": Decimal("100.00"),
            "performed_by": uuid4(),
            "created_at": datetime.now(timezone.utc)
        }
        defaults.update(kwargs)

        entry = LedgerEntry(**defaults)
        db_session.add(entry)
        db_session.commit()
        return entry
```

### 8.3 测试数据使用示例

```python
# tests/test_example.py
from tests.factories import UserFactory, ProjectFactory, DailyReportFactory

class TestExample:
    def test_with_factories(self, db_session):
        # 创建测试用户
        admin = UserFactory.create_admin(db_session)
        buyer = UserFactory.create_user(db_session, role="media_buyer")

        # 创建项目
        project = ProjectFactory.create_project(
            db_session,
            created_by=admin,
            unit_price=Decimal("15.00")
        )

        # 创建日报
        report = DailyReportFactory.create_report(
            db_session,
            ad_account=project.ad_accounts[0],
            created_by=buyer,
            conversions_raw=20
        )

        # 执行测试...
        assert report.status == "raw_submitted"
```

---

## 9. CI/CD集成

### 9.1 CI Pipeline配置

#### 9.1.1 GitHub Actions配置

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run unit tests
        run: |
          cd backend
          pytest tests/unit -v --cov=backend --cov-report=xml

      - name: Run integration tests
        run: |
          cd backend
          pytest tests/integration -v --cov-append --cov=backend --cov-report=xml
        env:
          DATABASE_URL: postgresql://postgres:test@localhost/test_db

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
          flags: backend

      - name: Check coverage threshold
        run: |
          cd backend
          pytest --cov=backend --cov-fail-under=90

  frontend-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Run tests
        run: |
          cd frontend
          npm run test:ci

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./frontend/coverage/coverage-final.json
          flags: frontend

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]

    steps:
      - uses: actions/checkout@v3

      - name: Run E2E tests
        run: |
          # 启动后端和前端
          docker-compose -f docker-compose.test.yml up -d

          # 等待服务就绪
          sleep 10

          # 运行E2E测试
          npm run test:e2e
```

### 9.2 Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-unit
        name: Run unit tests
        entry: pytest tests/unit -v
        language: system
        pass_filenames: false
        always_run: true

      - id: type-check
        name: Type check
        entry: mypy backend --strict
        language: system
        pass_filenames: false
        types: [python]
```

### 9.3 测试报告生成

```python
# pytest.ini
[pytest]
addopts =
    --cov=backend
    --cov-report=html:htmlcov
    --cov-report=term-missing
    --cov-report=xml
    --html=report.html
    --self-contained-html
    --junit-xml=junit.xml
```

---

## 10. 覆盖率要求

### 10.1 覆盖率目标

| 模块 | 语句覆盖率 | 分支覆盖率 | 函数覆盖率 | 优先级 |
|------|-----------|-----------|-----------|--------|
| **Service层** | ≥90% | ≥85% | 100% | P0 |
| **Models** | ≥80% | ≥75% | ≥90% | P0 |
| **API路由** | ≥90% | ≥85% | 100% | P0 |
| **工具函数** | ≥95% | ≥90% | 100% | P1 |
| **前端组件** | ≥80% | ≥70% | ≥85% | P1 |
| **E2E** | 核心流程100% | - | - | P0 |

### 10.2 覆盖率豁免

以下场景可豁免覆盖率要求：
- 框架生成代码（如Alembic迁移）
- 开发环境调试代码
- 第三方库适配层（已有集成测试覆盖）

### 10.3 覆盖率检查

```bash
# 后端覆盖率检查
cd backend
pytest --cov=backend --cov-fail-under=90

# 前端覆盖率检查
cd frontend
npm run test:coverage -- --coverageThreshold='{"global":{"statements":80}}'
```

---

## 11. 测试最佳实践

### 11.1 测试命名规范

#### 11.1.1 测试函数命名

```python
def test_<场景>_<预期结果>():
    """
    场景: <详细描述>
    Given: <前置条件>
    When: <触发动作>
    Then: <预期结果>
    引用: <SoT文档引用>
    """
```

**示例**:
```python
def test_create_daily_report_future_date_validation_error():
    """
    场景: 创建未来日期日报应失败
    Given: report_date = 2030-01-01 (未来日期)
    When: 调用create_daily_report
    Then: 抛出ValidationError
    引用: BR-RPT-001 - 禁止未来日期
    """
```

### 11.2 断言最佳实践

#### 11.2.1 使用明确的断言消息

```python
# ❌ 不推荐
assert result == expected

# ✅ 推荐
assert result == expected, f"期望{expected}，实际{result}"
```

#### 11.2.2 金额断言使用Decimal

```python
# ❌ 错误
assert float(ledger.amount) == 100.00  # 违反BR-FIN-003

# ✅ 正确
from decimal import Decimal
assert ledger.amount == Decimal("100.00")
assert isinstance(ledger.amount, Decimal)
```

#### 11.2.3 错误码断言

```python
# ✅ 推荐
from backend.exceptions.custom_exceptions import BusinessLogicError

with pytest.raises(BusinessLogicError) as exc_info:
    service.invalid_operation()

assert exc_info.value.code == "BIZ_101"
assert "余额不足" in exc_info.value.message
```

### 11.3 Mock最佳实践

#### 11.3.1 最小化Mock范围

```python
# ❌ 过度Mock
@patch('backend.services.daily_report_service.db')
@patch('backend.services.daily_report_service.LedgerService')
@patch('backend.services.daily_report_service.datetime')
def test_create_report(mock_dt, mock_ledger, mock_db):
    # 测试变得脆弱，依赖实现细节
    pass

# ✅ 仅Mock外部依赖
def test_create_report(db_session, test_ad_account):
    # 使用真实数据库会话和fixture
    service = DailyReportService(db_session)
    report = service.create_daily_report(...)
    assert report.status == "raw_submitted"
```

#### 11.3.2 使用上下文管理器Mock

```python
# ✅ 推荐
from unittest.mock import patch

def test_external_api_call():
    with patch('backend.services.external_api.requests.post') as mock_post:
        mock_post.return_value.json.return_value = {"status": "success"}

        result = service.call_external_api()

        assert result["status"] == "success"
        mock_post.assert_called_once()
```

### 11.4 测试隔离

#### 11.4.1 数据库隔离

```python
@pytest.fixture(scope="function")
def db_session():
    """每个测试独立会话，测试结束后回滚"""
    session = TestingSessionLocal()

    yield session

    session.rollback()
    session.close()
```

#### 11.4.2 时间隔离

```python
from unittest.mock import patch
from datetime import datetime, timezone

def test_time_sensitive_logic():
    """测试时间敏感逻辑"""
    fixed_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

    with patch('backend.services.daily_report_service.datetime') as mock_dt:
        mock_dt.now.return_value = fixed_time

        report = service.create_report()
        assert report.created_at == fixed_time
```

### 11.5 参数化测试

```python
import pytest

@pytest.mark.parametrize("role,expected_permission", [
    ("admin", True),
    ("finance", True),
    ("data_operator", False),
    ("account_manager", False),
    ("media_buyer", False),
])
def test_ledger_modify_permission(db_session, role, expected_permission):
    """
    场景: 测试不同角色的账本修改权限
    引用: AUTH_SPEC.md v2.0 - 权限矩阵
    """
    user = UserFactory.create_user(db_session, role=role)
    service = LedgerService(db_session)

    if expected_permission:
        # 应允许操作
        entry = service.create_manual_entry(..., user)
        assert entry is not None
    else:
        # 应拒绝操作
        with pytest.raises(PermissionDeniedError):
            service.create_manual_entry(..., user)
```

---

## 12. 附录：SoT引用索引

### 12.1 核心SoT文档版本

| SoT文档 | 版本 | 测试关注点 |
|--------|------|-----------|
| MASTER.md | v3.4 | 系统不变量（INV-001/002/003） |
| STATE_MACHINE.md | v2.6 | 状态流转、权限边界 |
| DATA_SCHEMA.md | v5.2 | 字段类型、约束 |
| API_SOT.md | v9.0 | 端点定义、Envelope格式 |
| ERROR_CODES_SOT.md | v2.1 | 错误码、HTTP状态码 |
| BUSINESS_RULES.md | v3.1 | 业务规则（BR-*-*） |
| LEDGER_SOT.md | v1.1 | 双账本逻辑、金额方向 |
| AUTH_SPEC.md | v2.0 | 角色权限矩阵 |

### 12.2 常用业务规则索引

| 规则编号 | 描述 | 测试类型 |
|---------|------|---------|
| BR-FIN-003 | 金额必用Decimal | 单元测试 |
| BR-DATA-002 | 时间必用UTC | 单元测试 |
| BR-DATA-001 | 核心数据禁删 | 集成测试 |
| BR-AUTH-001 | 角色不可混用 | 集成测试 |
| BR-RPT-004 | 终态不可回退 | 状态机测试 |
| BR-RPT-005 | 红冲修正 | 不变量测试 |

### 12.3 常用错误码索引

| 错误码 | HTTP状态码 | 场景 | 测试验证 |
|--------|-----------|------|---------|
| AUTH_001 | 401 | 用户未登录 | API集成测试 |
| AUTH_500 | 403 | 权限不足 | 权限测试 |
| BIZ_101 | 400 | 余额不足 | 业务逻辑测试 |
| STATE_001 | 400 | 非法状态流转 | 状态机测试 |
| STATE_002 | 403 | 终态已锁定 | 不变量测试 |
| LEDGER_001 | 403 | 禁止修改账本 | 审计不可逆测试 |
| LEDGER_002 | 403 | 禁止删除账本 | 审计不可逆测试 |

### 12.4 测试标记（Markers）

```python
# 使用pytest标记组织测试
@pytest.mark.unit
def test_calculation():
    """单元测试"""
    pass

@pytest.mark.integration
def test_api_endpoint():
    """集成测试"""
    pass

@pytest.mark.state_machine
def test_daily_report_flow():
    """状态机测试"""
    pass

@pytest.mark.invariant
def test_dual_ledger():
    """不变量测试"""
    pass

@pytest.mark.e2e
def test_complete_topup_flow():
    """端到端测试"""
    pass
```

---

## 结语

本文档定义了AI广告代投系统的完整测试策略，覆盖单元测试、集成测试、E2E测试、状态机测试、不变量测试等多个层次。

**核心要点**:
1. 测试必须引用SoT文档，验证业务规则而非实现细节
2. 后端测试覆盖率≥90%，核心Service层函数覆盖率100%
3. 状态机测试覆盖STATE_MACHINE.md中所有合法/非法流转
4. 不变量测试验证MASTER.md定义的系统不变量（INV-001/002/003）
5. API契约测试确保前后端通信符合API_SOT.md规范
6. CI/CD集成自动化测试，PR必须通过所有测试

**持续改进**:
- 定期review测试覆盖率报告，补充缺失测试
- 每次SoT文档更新后，同步更新对应测试用例
- 测试失败时，优先检查是否违反SoT规则，而非盲目修改测试

---

**文档维护**: 本文档随SoT文档演进同步更新
**反馈渠道**: 测试策略问题请提交至项目Issue Tracker
