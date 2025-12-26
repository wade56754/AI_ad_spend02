# 后端代码重构提案

> **版本**: v1.0
> **日期**: 2025-12-18
> **作者**: AI Code Factory
> **状态**: Draft

---

## 1. 执行摘要

本提案描述使用 **AI 代码工厂** 方法论，参考业界优秀开源项目，对后端代码进行系统性重构。

### 1.1 重构目标

| 目标 | 当前状态 | 目标状态 |
|------|----------|----------|
| 代码质量 | SoT 合规率 ~60% | SoT 合规率 >95% |
| 错误处理 | 错误码不统一 | 统一错误码体系 |
| 状态管理 | 多种状态定义 | 统一状态机 |
| 测试覆盖 | 缺少系统测试 | 覆盖率 >80% |
| 代码复用 | 重复代码多 | 模块化复用 |

### 1.2 参考开源项目

| 项目 | Stars | 借鉴内容 |
|------|-------|----------|
| [FastAPI](https://github.com/tiangolo/fastapi) | 75k+ | API 设计模式、依赖注入 |
| [SQLModel](https://github.com/tiangolo/sqlmodel) | 14k+ | Pydantic + SQLAlchemy 集成 |
| [Polar](https://github.com/polarsource/polar) | 3k+ | SaaS 后端架构、支付流程 |
| [Paperless-ngx](https://github.com/paperless-ngx/paperless-ngx) | 20k+ | 文档管理、工作流 |
| [Saleor](https://github.com/saleor/saleor) | 21k+ | 电商后端、状态机实现 |

---

## 2. 当前问题分析

### 2.1 验证器检测结果

基于 `EnhancedCodeVerifier` 扫描，发现以下问题：

```
问题分类统计:
┌─────────┬───────┬────────────────────────────────────────┐
│ 问题码  │ 数量  │ 说明                                   │
├─────────┼───────┼────────────────────────────────────────┤
│ SOT-005 │  63   │ 无效的错误码前缀 (STATE, INTERNAL)     │
│ SOT-001 │  39   │ 无效的状态值 (draft, pending_review)   │
│ SOT-004 │  42   │ 错误码格式不正确 (已部分修复)          │
│ SOT-007 │   3   │ 直接修改 balance 字段                  │
│ SOT-006 │   3   │ 未使用标准响应格式                     │
└─────────┴───────┴────────────────────────────────────────┘
```

### 2.2 核心问题

#### 问题 1: 状态管理混乱

```python
# 当前代码 - 多种状态定义
class TopupStatus:
    DRAFT = "draft"              # ❌ 非标准
    PENDING_REVIEW = "pending_review"  # ❌ 非标准
    FINANCE_APPROVE = "finance_approve"  # ❌ 非标准

# SoT 定义 (STATE_MACHINE.md v2.7 §9)
TOPUP_STATES = {
    "draft", "pending_review", "data_reviewed",
    "finance_approved", "paid", "completed",
    "rejected", "cancelled"
}
```

#### 问题 2: 错误码不统一

```python
# 当前代码 - 多种错误码格式
raise BusinessError(code="INTERNAL_001")   # ❌ 非标准前缀
raise BusinessError(code="STATE_001")      # ❌ 非标准前缀
raise BusinessError(code="VALIDATION_001") # ❌ 非标准前缀

# SoT 定义 (ERROR_CODES_SOT.md v2.1)
VALID_PREFIXES = {"VAL", "AUTH", "BIZ", "SYS", "DB"}
```

#### 问题 3: 缺少领域模型

```python
# 当前代码 - 贫血模型
def approve_topup(topup_id: int, user_id: int):
    topup = db.query(Topup).get(topup_id)
    topup.status = "approved"  # ❌ 业务逻辑散落在 Service
    topup.approved_by = user_id
    db.commit()

# 目标 - 充血模型
class Topup(BaseModel):
    def approve(self, approver: User) -> None:
        """状态机控制的审批"""
        self._validate_can_approve(approver)
        self._transition_to(TopupStatus.APPROVED)
        self.approved_by = approver.id
        self._record_event(TopupApproved(self.id, approver.id))
```

---

## 3. 重构策略

### 3.1 AI 代码工厂流程

```
┌──────────────────────────────────────────────────────────────┐
│                    AI Code Factory Pipeline                   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐     │
│  │ SEARCH  │ → │ SELECT  │ → │  ADAPT  │ → │ASSEMBLE │     │
│  │ 搜索    │   │ 筛选    │   │  适配   │   │  组装   │     │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘     │
│       │             │             │             │           │
│       ▼             ▼             ▼             ▼           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                      VERIFY                          │   │
│  │  HallucinationDetector → ASTVerifier → SpecVerifier │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 重构模块划分

| 模块 | 优先级 | 参考项目 | 预计工作量 |
|------|--------|----------|------------|
| 错误码统一 | P0 | FastAPI | 2 天 |
| 状态机重构 | P0 | Saleor | 3 天 |
| 响应格式统一 | P1 | FastAPI | 1 天 |
| 领域模型重构 | P1 | Polar | 5 天 |
| 测试补充 | P2 | Paperless-ngx | 3 天 |

---

## 4. 详细重构方案

### 4.1 错误码统一 (P0)

#### 参考: FastAPI 异常处理

```python
# 来源: https://github.com/tiangolo/fastapi/blob/master/fastapi/exceptions.py

class HTTPException(StarletteHTTPException):
    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)
```

#### 重构方案

**文件**: `backend/core/exceptions.py`

```python
"""
统一异常体系

借鉴: FastAPI HTTPException 设计
参考: ERROR_CODES_SOT.md v2.1
"""

from enum import Enum
from typing import Any, Optional
from fastapi import HTTPException


class ErrorCode(str, Enum):
    """标准错误码 (来自 ERROR_CODES_SOT.md)"""

    # 验证错误 (VAL-xxx)
    VAL_001 = "VAL-001"  # 必填字段缺失
    VAL_002 = "VAL-002"  # 字段格式错误
    VAL_003 = "VAL-003"  # 字段值超出范围

    # 认证授权错误 (AUTH-xxx)
    AUTH_001 = "AUTH-001"  # 未认证
    AUTH_002 = "AUTH-002"  # 认证过期
    AUTH_003 = "AUTH-003"  # 权限不足

    # 业务逻辑错误 (BIZ-xxx)
    BIZ_001 = "BIZ-001"  # 状态转换非法
    BIZ_002 = "BIZ-002"  # 资源不存在
    BIZ_003 = "BIZ-003"  # 资源已存在
    BIZ_004 = "BIZ-004"  # 业务规则冲突

    # 系统错误 (SYS-xxx)
    SYS_001 = "SYS-001"  # 内部错误
    SYS_002 = "SYS-002"  # 服务不可用
    SYS_003 = "SYS-003"  # 超时

    # 数据库错误 (DB-xxx)
    DB_001 = "DB-001"  # 连接失败
    DB_002 = "DB-002"  # 查询失败
    DB_003 = "DB-003"  # 数据完整性错误


class BusinessException(HTTPException):
    """业务异常基类"""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = 400,
        details: Optional[Any] = None,
    ):
        super().__init__(
            status_code=status_code,
            detail={
                "code": code.value,
                "message": message,
                "details": details,
            }
        )
        self.code = code
        self.message = message


class ValidationError(BusinessException):
    """验证错误"""
    def __init__(self, message: str, code: ErrorCode = ErrorCode.VAL_001, details: Any = None):
        super().__init__(code=code, message=message, status_code=422, details=details)


class AuthorizationError(BusinessException):
    """授权错误"""
    def __init__(self, message: str, code: ErrorCode = ErrorCode.AUTH_003, details: Any = None):
        super().__init__(code=code, message=message, status_code=403, details=details)


class NotFoundError(BusinessException):
    """资源不存在"""
    def __init__(self, message: str, resource: str = None):
        super().__init__(
            code=ErrorCode.BIZ_002,
            message=message,
            status_code=404,
            details={"resource": resource}
        )


class StateTransitionError(BusinessException):
    """状态转换错误"""
    def __init__(self, current_state: str, target_state: str, reason: str = None):
        super().__init__(
            code=ErrorCode.BIZ_001,
            message=f"无法从 {current_state} 转换到 {target_state}",
            status_code=400,
            details={
                "current_state": current_state,
                "target_state": target_state,
                "reason": reason,
            }
        )
```

#### 迁移脚本

```python
# 错误码映射表 (旧 → 新)
ERROR_CODE_MIGRATION = {
    "INTERNAL_001": ErrorCode.SYS_001,
    "INTERNAL_002": ErrorCode.SYS_001,
    "STATE_001": ErrorCode.BIZ_001,
    "STATE_002": ErrorCode.BIZ_001,
    "VALIDATION_001": ErrorCode.VAL_001,
    "VALIDATION_002": ErrorCode.VAL_002,
    "RESOURCE-NOT-FOUND": ErrorCode.BIZ_002,
    "OPERATION_001": ErrorCode.BIZ_004,
}
```

---

### 4.2 状态机重构 (P0)

#### 参考: Saleor 状态机实现

```python
# 来源: https://github.com/saleor/saleor/blob/main/saleor/order/models.py

class OrderStatus:
    DRAFT = "draft"
    UNCONFIRMED = "unconfirmed"
    UNFULFILLED = "unfulfilled"
    PARTIALLY_FULFILLED = "partially_fulfilled"
    FULFILLED = "fulfilled"
    CANCELED = "canceled"

    CHOICES = [
        (DRAFT, "Draft"),
        (UNCONFIRMED, "Unconfirmed"),
        # ...
    ]
```

#### 重构方案

**文件**: `backend/core/state_machine.py`

```python
"""
统一状态机

借鉴: Saleor OrderStatus 设计
参考: STATE_MACHINE.md v2.7
"""

from enum import Enum
from typing import Dict, List, Set, Optional, Callable
from dataclasses import dataclass


class DailyReportStatus(str, Enum):
    """日报 8 状态机 (STATE_MACHINE.md v2.7 §6)"""
    RAW_SUBMITTED = "raw_submitted"
    TREND_PENDING = "trend_pending"
    TREND_OK = "trend_ok"
    TREND_FLAGGED = "trend_flagged"
    TREND_RESOLVED = "trend_resolved"
    FINAL_PENDING = "final_pending"
    FINAL_CONFIRMED = "final_confirmed"
    FINAL_LOCKED = "final_locked"


class TopupStatus(str, Enum):
    """充值状态机 (STATE_MACHINE.md v2.7 §9)"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    DATA_REVIEWED = "data_reviewed"
    FINANCE_APPROVED = "finance_approved"
    PAID = "paid"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class TransferStatus(str, Enum):
    """转账状态机 (STATE_MACHINE.md v2.7 §12)"""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    COMPLETED = "completed"
    REJECTED = "rejected"


@dataclass
class Transition:
    """状态转换定义"""
    from_state: Enum
    to_state: Enum
    required_role: Optional[str] = None
    guard: Optional[Callable] = None
    action: Optional[Callable] = None


class StateMachine:
    """通用状态机"""

    def __init__(self, transitions: List[Transition]):
        self._transitions: Dict[tuple, Transition] = {}
        for t in transitions:
            key = (t.from_state, t.to_state)
            self._transitions[key] = t

    def can_transition(self, from_state: Enum, to_state: Enum) -> bool:
        """检查是否可以转换"""
        return (from_state, to_state) in self._transitions

    def get_allowed_transitions(self, current_state: Enum) -> List[Enum]:
        """获取允许的目标状态"""
        return [
            t.to_state for (f, _), t in self._transitions.items()
            if f == current_state
        ]

    def transition(
        self,
        entity: any,
        from_state: Enum,
        to_state: Enum,
        user_role: Optional[str] = None,
    ) -> None:
        """执行状态转换"""
        key = (from_state, to_state)
        if key not in self._transitions:
            raise StateTransitionError(
                from_state.value, to_state.value,
                reason="不允许的状态转换"
            )

        transition = self._transitions[key]

        # 检查角色权限
        if transition.required_role and user_role != transition.required_role:
            raise AuthorizationError(
                f"需要 {transition.required_role} 角色"
            )

        # 执行 guard
        if transition.guard and not transition.guard(entity):
            raise StateTransitionError(
                from_state.value, to_state.value,
                reason="前置条件不满足"
            )

        # 执行转换
        entity.status = to_state.value

        # 执行 action
        if transition.action:
            transition.action(entity)


# 预定义状态机
TOPUP_STATE_MACHINE = StateMachine([
    Transition(TopupStatus.DRAFT, TopupStatus.PENDING_REVIEW),
    Transition(TopupStatus.PENDING_REVIEW, TopupStatus.DATA_REVIEWED, required_role="data_operator"),
    Transition(TopupStatus.DATA_REVIEWED, TopupStatus.FINANCE_APPROVED, required_role="finance"),
    Transition(TopupStatus.FINANCE_APPROVED, TopupStatus.PAID, required_role="finance"),
    Transition(TopupStatus.PAID, TopupStatus.COMPLETED, required_role="finance"),
    Transition(TopupStatus.PENDING_REVIEW, TopupStatus.REJECTED, required_role="data_operator"),
    Transition(TopupStatus.DATA_REVIEWED, TopupStatus.REJECTED, required_role="finance"),
    Transition(TopupStatus.DRAFT, TopupStatus.CANCELLED),
])
```

---

### 4.3 响应格式统一 (P1)

#### 参考: FastAPI 响应模型

```python
# 来源: https://github.com/tiangolo/fastapi/discussions/10289

from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar("T")

class Response(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    message: str = ""
```

#### 重构方案

**文件**: `backend/core/response.py`

```python
"""
统一响应格式

借鉴: FastAPI Generic Response 设计
参考: API_SOT.md v9.3 响应规范
"""

from typing import Any, Generic, TypeVar, Optional, List
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应"""
    success: bool
    code: str = "OK"
    message: str = ""
    data: Optional[T] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    success: bool = True
    code: str = "OK"
    message: str = ""
    data: List[T]
    pagination: dict  # {page, page_size, total, total_pages}


def success_response(
    data: Any = None,
    message: str = "操作成功",
) -> dict:
    """成功响应"""
    return {
        "success": True,
        "code": "OK",
        "message": message,
        "data": data,
    }


def error_response(
    code: str,
    message: str,
    details: Any = None,
) -> dict:
    """错误响应"""
    return {
        "success": False,
        "code": code,
        "message": message,
        "data": details,
    }


def paginated_response(
    items: List[Any],
    page: int,
    page_size: int,
    total: int,
) -> dict:
    """分页响应"""
    total_pages = (total + page_size - 1) // page_size
    return {
        "success": True,
        "code": "OK",
        "message": "",
        "data": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        }
    }
```

---

### 4.4 领域模型重构 (P1)

#### 参考: Polar 领域模型

```python
# 来源: https://github.com/polarsource/polar/blob/main/server/polar/subscription/service.py

class SubscriptionService:
    async def create_subscription(
        self,
        session: AsyncSession,
        *,
        user: User,
        product: Product,
    ) -> Subscription:
        subscription = Subscription(
            user=user,
            product=product,
            status=SubscriptionStatus.active,
        )
        session.add(subscription)
        await session.flush()
        return subscription
```

#### 重构方案

**文件**: `backend/domains/topup/service.py`

```python
"""
充值领域服务

借鉴: Polar SubscriptionService 设计
参考: BUSINESS_RULES.md 充值规则
"""

from typing import Optional, List
from sqlalchemy.orm import Session

from backend.core.state_machine import TOPUP_STATE_MACHINE, TopupStatus
from backend.core.exceptions import NotFoundError, StateTransitionError
from backend.domains.topup.models import Topup, TopupApprovalLog
from backend.domains.topup.schemas import TopupCreate, TopupResponse


class TopupService:
    """充值领域服务"""

    def __init__(self, db: Session):
        self.db = db
        self.state_machine = TOPUP_STATE_MACHINE

    def create(self, data: TopupCreate, user_id: int) -> Topup:
        """创建充值申请"""
        topup = Topup(
            amount=data.amount,
            account_id=data.account_id,
            status=TopupStatus.DRAFT.value,
            created_by=user_id,
        )
        self.db.add(topup)
        self.db.flush()
        return topup

    def submit_for_review(self, topup_id: int, user_id: int) -> Topup:
        """提交审核"""
        topup = self._get_or_raise(topup_id)
        self._transition(
            topup,
            TopupStatus(topup.status),
            TopupStatus.PENDING_REVIEW,
            user_id,
        )
        return topup

    def approve_data_review(
        self,
        topup_id: int,
        user_id: int,
        user_role: str,
        notes: str = None,
    ) -> Topup:
        """数据审核通过"""
        topup = self._get_or_raise(topup_id)
        self._transition(
            topup,
            TopupStatus(topup.status),
            TopupStatus.DATA_REVIEWED,
            user_id,
            user_role,
        )
        self._log_approval(topup_id, user_id, "data_review", "approved", notes)
        return topup

    def approve_finance(
        self,
        topup_id: int,
        user_id: int,
        user_role: str,
        notes: str = None,
    ) -> Topup:
        """财务审核通过"""
        topup = self._get_or_raise(topup_id)
        self._transition(
            topup,
            TopupStatus(topup.status),
            TopupStatus.FINANCE_APPROVED,
            user_id,
            user_role,
        )
        self._log_approval(topup_id, user_id, "finance_review", "approved", notes)
        return topup

    def _get_or_raise(self, topup_id: int) -> Topup:
        """获取充值记录或抛出异常"""
        topup = self.db.query(Topup).filter(Topup.id == topup_id).first()
        if not topup:
            raise NotFoundError(f"充值记录 {topup_id} 不存在", resource="topup")
        return topup

    def _transition(
        self,
        topup: Topup,
        from_state: TopupStatus,
        to_state: TopupStatus,
        user_id: int,
        user_role: str = None,
    ) -> None:
        """执行状态转换"""
        self.state_machine.transition(
            topup, from_state, to_state, user_role
        )
        topup.updated_by = user_id
        self.db.flush()

    def _log_approval(
        self,
        topup_id: int,
        user_id: int,
        action: str,
        result: str,
        notes: str = None,
    ) -> None:
        """记录审批日志"""
        log = TopupApprovalLog(
            topup_id=topup_id,
            user_id=user_id,
            action=action,
            result=result,
            notes=notes,
        )
        self.db.add(log)
```

---

## 5. 代码库参考清单

### 5.1 核心参考项目

| 项目 | GitHub | License | 借鉴模块 |
|------|--------|---------|----------|
| FastAPI | [tiangolo/fastapi](https://github.com/tiangolo/fastapi) | MIT | 异常处理、依赖注入、响应模型 |
| SQLModel | [tiangolo/sqlmodel](https://github.com/tiangolo/sqlmodel) | MIT | Pydantic + SQLAlchemy 集成 |
| Saleor | [saleor/saleor](https://github.com/saleor/saleor) | BSD-3 | 状态机、订单流程 |
| Polar | [polarsource/polar](https://github.com/polarsource/polar) | Apache-2.0 | 领域服务、支付流程 |
| Paperless-ngx | [paperless-ngx/paperless-ngx](https://github.com/paperless-ngx/paperless-ngx) | GPL-3.0 | 文档管理、工作流 |

### 5.2 代码片段索引

| 功能 | 来源 | 文件路径 |
|------|------|----------|
| HTTP 异常 | FastAPI | `fastapi/exceptions.py` |
| 依赖注入 | FastAPI | `fastapi/dependencies/utils.py` |
| 响应模型 | FastAPI | `fastapi/responses.py` |
| 状态枚举 | Saleor | `saleor/order/models.py` |
| 领域服务 | Polar | `server/polar/subscription/service.py` |
| 事件发布 | Polar | `server/polar/eventstream/service.py` |

---

## 6. 实施计划

### 6.1 Phase 1: 基础设施 (Week 1)

- [ ] 创建统一异常体系 (`backend/core/exceptions.py`)
- [ ] 创建统一状态机 (`backend/core/state_machine.py`)
- [ ] 创建统一响应格式 (`backend/core/response.py`)
- [ ] 更新验证器规则

### 6.2 Phase 2: 错误码迁移 (Week 1-2)

- [ ] 生成错误码映射表
- [ ] 批量替换旧错误码
- [ ] 更新测试用例
- [ ] 验证迁移完成

### 6.3 Phase 3: 状态机迁移 (Week 2-3)

- [ ] 迁移充值状态机
- [ ] 迁移转账状态机
- [ ] 迁移日报状态机
- [ ] 验证状态转换

### 6.4 Phase 4: 领域模型重构 (Week 3-4)

- [ ] 重构 TopupService
- [ ] 重构 TransferService
- [ ] 重构 DailyReportService
- [ ] 集成测试

---

## 7. 验收标准

### 7.1 代码质量

```bash
# 运行验证器
python -m agents.skills.verifiers.test_real_code

# 期望结果
总错误: 0
总警告: < 20
SoT 合规率: > 95%
```

### 7.2 测试覆盖

```bash
# 运行测试
pytest --cov=backend --cov-report=term-missing

# 期望结果
覆盖率: > 80%
失败测试: 0
```

### 7.3 回归测试

```bash
# 运行回归测试
python run_tests.py --type regression

# 期望结果
所有测试通过
```

---

## 8. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 状态迁移数据不一致 | 高 | 先在测试环境验证，逐步迁移 |
| 错误码变更影响前端 | 中 | 提供映射表，通知前端团队 |
| 业务逻辑变更 | 中 | 保留旧接口兼容期 |
| 测试覆盖不足 | 低 | 增加测试用例 |

---

## 9. 附录

### 9.1 错误码完整映射表

```yaml
# 旧错误码 → 新错误码
migrations:
  INTERNAL_001: SYS-001
  INTERNAL_002: SYS-001
  STATE_001: BIZ-001
  STATE_002: BIZ-001
  VALIDATION_001: VAL-001
  VALIDATION_002: VAL-002
  RESOURCE-NOT-FOUND: BIZ-002
  OPERATION_001: BIZ-004
  AUTH_500: AUTH-001
```

### 9.2 状态映射表

```yaml
# 充值状态映射
topup_status:
  draft: draft  # 保持
  pending_review: pending_review  # 保持
  finance_approve: finance_approved  # 修正
  approved: finance_approved  # 合并
  paid: paid  # 保持
  settled: completed  # 重命名
  rejected: rejected  # 保持
  cancelled: cancelled  # 保持
```

---

**文档历史**:
- v1.0 (2025-12-18): 初始版本
