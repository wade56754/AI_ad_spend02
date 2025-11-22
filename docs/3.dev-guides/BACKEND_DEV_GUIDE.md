# Backend Development Guide · 后端开发指南

> **版本**: v1.0
> **更新日期**: 2025-01-22
> **维护团队**: 后端开发团队
> **定位**: 后端工程实践规范，指导 FastAPI + SQLAlchemy + PostgreSQL/Supabase 体系的开发流程、编码规范、测试策略。

---

## 📌 文档定位 (Document Scope)

### 本文档职责

本文档是后端开发的**工程实践指南**，用于指导：

1. ✅ 后端目录结构与分层架构
2. ✅ FastAPI Router/Service/Repository 开发流程
3. ✅ SQLAlchemy 模型定义与数据库交互规范
4. ✅ API 开发规范（路由、响应、错误处理）
5. ✅ 并发控制（乐观锁/悲观锁/分布式锁）
6. ✅ 测试规范（单元测试/集成测试）
7. ✅ 性能优化与安全规范
8. ✅ PR 提交与代码审查流程

### 本文档不包含

❌ **业务逻辑定义** → 查阅各模块 SoT（TOPUP_SOT.md、RECONCILIATION_SOT.md 等）
❌ **字段定义与数据类型** → 查阅 DATA_SCHEMA.md
❌ **状态机流转规则** → 查阅 STATE_MACHINE.md
❌ **错误码定义** → 查阅 ERROR_CODES_SOT.md
❌ **认证授权规则** → 查阅 AUTH_SPEC.md
❌ **双账本业务逻辑** → 查阅 LEDGER_SOT.md

**核心原则**: 本文档描述"如何开发"，SoT 文档描述"开发什么"。

---

## 1. 技术栈说明 (Tech Stack Overview)

### 1.1 核心技术栈

| 技术 | 版本 | 用途 | 强制性 |
|-----|------|------|--------|
| **Python** | 3.11+ | 后端语言 | 🔴 强制 |
| **FastAPI** | 0.104+ | Web 框架 | 🔴 强制 |
| **SQLAlchemy** | 2.0+ | ORM（Async 支持） | 🔴 强制 |
| **Pydantic** | v2.0+ | 数据验证与序列化 | 🔴 强制 |
| **PostgreSQL** | 15+ | 数据库（Supabase 托管） | 🔴 强制 |
| **Alembic** | 最新 | 数据库迁移工具 | 🔴 强制 |
| **Redis** | 7.0+ | 缓存与分布式锁 | 🟡 推荐 |
| **Pytest** | 最新 | 测试框架 | 🔴 强制 |
| **Uvicorn** | 最新 | ASGI 服务器 | 🔴 强制 |

### 1.2 关键依赖

```python
# pyproject.toml / requirements.txt 核心依赖
fastapi>=0.104.0
sqlalchemy>=2.0.0
pydantic>=2.0.0
pydantic-settings
alembic
asyncpg  # PostgreSQL async driver
psycopg2-binary  # PostgreSQL sync driver (迁移用)
redis
pytest
pytest-asyncio
httpx  # 测试用 HTTP 客户端
```

### 1.3 开发工具

| 工具 | 用途 | 强制性 |
|-----|------|--------|
| **Black** | 代码格式化 | 🟡 推荐 |
| **Ruff** | Linter（替代 Flake8） | 🟡 推荐 |
| **mypy** | 静态类型检查 | 🟢 可选 |
| **pre-commit** | Git 提交前检查 | 🟡 推荐 |

---

## 2. 目录结构要求 (Project Structure)

### 2.1 标准后端目录结构

```
backend/
├── alembic/                    # Alembic 迁移
│   ├── versions/               # 迁移脚本（按时间戳命名）
│   ├── env.py                  # Alembic 环境配置
│   └── alembic.ini             # Alembic 配置文件
│
├── app/                        # 主应用目录
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   │
│   ├── api/                    # API 路由层（仅路由与验证）
│   │   ├── __init__.py
│   │   ├── v1/                 # API 版本控制
│   │   │   ├── __init__.py
│   │   │   ├── router.py       # 路由聚合
│   │   │   ├── projects.py     # 项目模块路由
│   │   │   ├── topups.py       # 充值模块路由
│   │   │   ├── daily_reports.py# 日报模块路由
│   │   │   └── reconciliations.py # 对账模块路由
│   │   └── deps.py             # 依赖注入（get_db, get_current_user）
│   │
│   ├── services/               # 业务逻辑层（核心业务逻辑）
│   │   ├── __init__.py
│   │   ├── project_service.py
│   │   ├── topup_service.py
│   │   ├── daily_report_service.py
│   │   ├── reconciliation_service.py
│   │   └── ledger_service.py   # 账本逻辑
│   │
│   ├── repositories/           # 数据访问层（可选，Repository Pattern）
│   │   ├── __init__.py
│   │   └── base_repository.py  # 通用 CRUD 封装
│   │
│   ├── models/                 # SQLAlchemy 模型（对齐 DATA_SCHEMA.md）
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── topup.py
│   │   ├── daily_report.py
│   │   ├── reconciliation.py
│   │   └── ledger.py
│   │
│   ├── schemas/                # Pydantic 模型（请求/响应）
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── topup.py
│   │   ├── daily_report.py
│   │   └── reconciliation.py
│   │
│   ├── core/                   # 核心配置与工具
│   │   ├── __init__.py
│   │   ├── config.py           # 配置类（环境变量）
│   │   ├── security.py         # JWT 验证、密码哈希
│   │   ├── response.py         # 统一响应封装（Envelope）
│   │   ├── error_codes.py      # 错误码定义（对齐 ERROR_CODES_SOT.md）
│   │   └── enums.py            # 枚举类（对齐 STATE_MACHINE.md）
│   │
│   ├── db/                     # 数据库连接与会话
│   │   ├── __init__.py
│   │   ├── session.py          # SQLAlchemy Session 工厂
│   │   └── base.py             # Base 模型基类
│   │
│   ├── exceptions/             # 自定义异常
│   │   ├── __init__.py
│   │   └── handlers.py         # 异常处理器（BusinessRuleException 等）
│   │
│   └── utils/                  # 工具函数
│       ├── __init__.py
│       ├── audit.py            # 审计日志工具
│       └── datetime_utils.py   # UTC 时间处理
│
├── tests/                      # 测试目录
│   ├── __init__.py
│   ├── conftest.py             # Pytest 配置与 Fixture
│   ├── unit/                   # 单元测试
│   │   ├── test_services/
│   │   └── test_models/
│   ├── integration/            # 集成测试
│   │   └── test_api/
│   └── e2e/                    # 端到端测试（可选）
│
├── scripts/                    # 运维脚本
│   ├── init_db.py              # 初始化数据库
│   └── seed_data.py            # 测试数据种子
│
├── .env.example                # 环境变量示例
├── pyproject.toml              # 项目依赖与配置
└── README.md                   # 后端 README
```

### 2.2 分层职责说明

| 层级 | 职责 | 禁止事项 |
|-----|------|---------|
| **API Layer (Router)** | 1. 路由定义<br>2. 请求参数验证（Pydantic）<br>3. Token 验证（`@require_role`）<br>4. 调用 Service 层<br>5. 返回统一响应（Envelope） | ❌ 不写业务逻辑<br>❌ 不直接操作 SQLAlchemy<br>❌ 不处理状态机流转<br>❌ 不进行数据权限过滤 |
| **Service Layer** | 1. 业务逻辑实现<br>2. 状态机流转验证<br>3. 数据权限过滤（user_id/role）<br>4. 并发控制（乐观锁/悲观锁）<br>5. 事务管理<br>6. 调用 Repository/ORM | ❌ 不直接处理 HTTP 请求<br>❌ 不返回 FastAPI Response |
| **Repository Layer (可选)** | 1. 封装 SQLAlchemy 查询<br>2. 通用 CRUD 操作 | ❌ 不写业务逻辑<br>❌ 不处理权限过滤 |
| **Model Layer** | 1. SQLAlchemy 模型定义<br>2. 数据库表映射<br>3. 关系定义（Foreign Key） | ❌ 不包含业务逻辑<br>❌ 必须对齐 DATA_SCHEMA.md |
| **Schema Layer** | 1. Pydantic 请求/响应模型<br>2. 数据验证规则 | ❌ 不包含业务逻辑<br>❌ 字段必须对齐 DATA_SCHEMA.md |

---

## 3. 开发流程 (Development Flow)

### 3.1 标准开发流程（8 步法）

```
1. 阅读 SoT 文档
   ↓
2. 设计 Pydantic Schema（请求/响应）
   ↓
3. 实现 SQLAlchemy Model（如需新表）
   ↓
4. 编写 Alembic 迁移（如需新表/字段）
   ↓
5. 实现 Service 层业务逻辑
   ↓
6. 实现 Router 层路由
   ↓
7. 编写测试（单元 + 集成）
   ↓
8. 自检 → 提 PR → Code Review
```

### 3.2 开发前必读文档清单

| 任务类型 | 必读文档 |
|---------|---------|
| **新增 API** | 1. API_SOT.md（响应格式、错误码）<br>2. DATA_SCHEMA.md（字段定义）<br>3. STATE_MACHINE.md（状态流转）<br>4. 对应模块 SoT（如 TOPUP_SOT.md） |
| **修改字段** | 1. DATA_SCHEMA.md<br>2. MASTER_SPEC.md（确认不违反核心原则） |
| **状态流转** | 1. STATE_MACHINE.md<br>2. 对应模块 SoT |
| **权限控制** | 1. AUTH_SPEC.md<br>2. RLS_POLICIES_SOT.md |
| **错误处理** | 1. ERROR_CODES_SOT.md |

### 3.3 开发示例：新增充值 API

```python
# 步骤 1: 阅读 TOPUP_SOT.md，明确业务逻辑

# 步骤 2: 定义 Pydantic Schema
# app/schemas/topup.py
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import date

class TopupRequestCreate(BaseModel):
    project_id: int = Field(..., description="项目ID")
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="充值金额")
    urgency_level: str = Field(..., pattern="^(low|normal|high|urgent)$")
    expected_pay_date: date

class TopupRequestResponse(BaseModel):
    id: int
    request_no: str
    status: str
    amount: Decimal
    # ... 其他字段（对齐 DATA_SCHEMA.md）

# 步骤 3: 实现 Service 层
# app/services/topup_service.py
from app.models.topup import TopupRequest
from app.core.error_codes import BusinessErrorCodes
from app.exceptions import BusinessRuleException

class TopupService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_topup(self, data: TopupRequestCreate, user_id: str) -> TopupRequest:
        # 1. 幂等性检查（request_no）
        # 2. 业务规则验证
        # 3. 创建记录
        # 4. 审计日志
        pass

# 步骤 4: 实现 Router 层
# app/api/v1/topups.py
from fastapi import APIRouter, Depends
from app.core.response import success_response
from app.api.deps import get_db, get_current_user

router = APIRouter(prefix="/topups", tags=["topups"])

@router.post("/", response_model=dict)
async def create_topup(
    data: TopupRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    service = TopupService(db)
    topup = await service.create_topup(data, current_user.id)
    return success_response(data=TopupRequestResponse.model_validate(topup))

# 步骤 5: 编写测试
# tests/integration/test_api/test_topups.py
async def test_create_topup_success(client, auth_headers):
    response = await client.post("/api/v1/topups", json={
        "project_id": 1,
        "amount": "1000.00",
        "urgency_level": "normal",
        "expected_pay_date": "2025-02-01"
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
```

---

## 4. API 开发规范 (API Layer Rules)

### 4.1 核心约束

| 规则 | 说明 | 强制性 |
|-----|------|--------|
| **统一响应格式** | 必须使用 `success_response` / `error_response`（Envelope Pattern） | 🔴 强制 |
| **禁止业务逻辑** | Router 层只处理路由、验证、调用 Service | 🔴 强制 |
| **禁止直接 ORM** | Router 层不得直接操作 SQLAlchemy | 🔴 强制 |
| **权限在 Service** | 数据权限过滤（user_id/role）必须在 Service 层 | 🔴 强制 |
| **RESTful 路由** | 遵循 REST 命名规范 | 🟡 推荐 |
| **错误码引用** | 所有错误码必须来自 ERROR_CODES_SOT.md | 🔴 强制 |

### 4.2 统一响应格式（Envelope Pattern）

**引用**: API_SOT.md 第 4 章

```python
# app/core/response.py
from typing import Any, Optional
from datetime import datetime, timezone
from uuid import uuid4

def success_response(
    data: Any = None,
    message: str = "操作成功",
    code: str = "SUCCESS"
) -> dict:
    """成功响应封装"""
    return {
        "success": True,
        "message": message,
        "code": code,
        "data": data,
        "request_id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def error_response(
    message: str,
    code: str,
    status_code: int = 400,
    data: Any = None
) -> dict:
    """错误响应封装"""
    return {
        "success": False,
        "message": message,
        "code": code,
        "data": data,
        "request_id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
```

**使用示例**:
```python
# ✅ 正确
@router.get("/projects/{project_id}")
async def get_project(project_id: int, service: ProjectService = Depends()):
    project = await service.get_project(project_id)
    return success_response(data=project)

# ❌ 错误（不使用 Envelope）
@router.get("/projects/{project_id}")
async def get_project(project_id: int):
    return {"id": 1, "name": "Project A"}  # 禁止
```

### 4.3 RESTful 路由命名规范

| 操作 | HTTP 方法 | 路由示例 | 说明 |
|-----|---------|---------|------|
| 列表查询 | GET | `/api/v1/projects` | 查询所有项目 |
| 单个查询 | GET | `/api/v1/projects/{id}` | 查询指定项目 |
| 创建 | POST | `/api/v1/projects` | 创建项目 |
| 更新 | PUT/PATCH | `/api/v1/projects/{id}` | 更新项目 |
| 删除 | DELETE | `/api/v1/projects/{id}` | 删除项目 |
| 自定义操作 | POST | `/api/v1/topups/{id}/submit` | 提交充值审核 |
| 子资源 | GET | `/api/v1/projects/{id}/members` | 查询项目成员 |

### 4.4 权限验证装饰器

```python
# app/core/security.py
from functools import wraps
from fastapi import HTTPException
from app.core.error_codes import AuthErrorCodes

def require_role(*allowed_roles: str):
    """角色权限装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user, **kwargs):
            if current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=403,
                    detail=error_response(
                        message="权限不足",
                        code=AuthErrorCodes.PERMISSION_DENIED.code
                    )
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# 使用示例
@router.post("/topups/{id}/approve")
@require_role("finance", "admin")
async def approve_topup(id: int, current_user = Depends(get_current_user)):
    # 仅 finance/admin 可访问
    pass
```

---

## 5. Service 层规范 (Service Layer Rules)

### 5.1 Service 层职责

| 职责 | 说明 | 强制性 |
|-----|------|--------|
| **业务逻辑实现** | 所有业务规则必须在 Service 层实现 | 🔴 强制 |
| **状态机验证** | 状态流转必须引用 STATE_MACHINE.md | 🔴 强制 |
| **数据权限过滤** | 基于 user_id/role 过滤数据（对齐 AUTH_SPEC.md） | 🔴 强制 |
| **并发控制** | 乐观锁/悲观锁在此执行 | 🔴 强制 |
| **事务管理** | 使用 `async with db.begin()` 或 `@transactional` | 🔴 强制 |
| **幂等性保证** | 检查唯一性约束（如 request_no） | 🔴 强制 |
| **审计日志** | 关键操作记录 audit_logs | 🟡 推荐 |

### 5.2 状态机流转验证

**引用**: STATE_MACHINE.md

```python
# app/services/topup_service.py
from app.core.enums import TopupStatus
from app.exceptions import BusinessRuleException
from app.core.error_codes import StateErrorCodes

# 状态流转白名单（对齐 STATE_MACHINE.md）
TOPUP_STATUS_TRANSITIONS = {
    TopupStatus.DRAFT: [TopupStatus.PENDING_REVIEW, TopupStatus.CANCELLED],
    TopupStatus.PENDING_REVIEW: [TopupStatus.FINANCE_APPROVE, TopupStatus.REJECTED, TopupStatus.DRAFT],
    TopupStatus.FINANCE_APPROVE: [TopupStatus.PAID, TopupStatus.REJECTED],
    TopupStatus.PAID: [TopupStatus.COMPLETED],
    TopupStatus.COMPLETED: [],  # 终态
    TopupStatus.REJECTED: [],   # 终态
    TopupStatus.CANCELLED: []   # 终态
}

def validate_status_transition(current_status: str, target_status: str):
    """验证状态流转合法性"""
    allowed = TOPUP_STATUS_TRANSITIONS.get(current_status, [])
    if target_status not in allowed:
        raise BusinessRuleException(
            message=f"非法流转: {current_status} → {target_status}",
            code=StateErrorCodes.FORBIDDEN_TRANSITION.code  # STATE_400
        )

# 使用示例
async def submit_topup(self, topup_id: int, user_id: str):
    topup = await self.get_topup(topup_id)
    validate_status_transition(topup.status, TopupStatus.PENDING_REVIEW)
    topup.status = TopupStatus.PENDING_REVIEW
    await self.db.commit()
```

### 5.3 数据权限过滤

**引用**: AUTH_SPEC.md

```python
# app/services/project_service.py
from app.core.enums import UserRole

async def get_projects(self, user_id: str, user_role: str) -> list:
    """获取项目列表（基于角色过滤）"""
    query = select(Project)

    if user_role == UserRole.ADMIN:
        # admin 查看所有项目
        pass
    elif user_role == UserRole.ACCOUNT_MANAGER:
        # account_manager 查看自己负责的项目
        query = query.where(Project.account_manager_id == user_id)
    elif user_role == UserRole.MEDIA_BUYER:
        # media_buyer 查看自己参与的项目
        query = query.join(ProjectMember).where(ProjectMember.user_id == user_id)
    else:
        # 其他角色无权限
        return []

    result = await self.db.execute(query)
    return result.scalars().all()
```

### 5.4 并发控制：乐观锁

```python
# app/services/topup_service.py
from app.exceptions import ConcurrencyConflictError
from app.core.error_codes import StateErrorCodes

async def approve_topup(self, topup_id: int, expected_version: int, user_id: str):
    """审批充值（乐观锁）"""
    topup = await self.get_topup(topup_id)

    # 验证版本号
    if topup.version != expected_version:
        raise ConcurrencyConflictError(
            message=f"充值记录已被其他用户修改（当前版本: {topup.version}）",
            code=StateErrorCodes.CONCURRENCY_CONFLICT.code  # STATE_409
        )

    # 更新状态
    topup.status = TopupStatus.FINANCE_APPROVE
    topup.approved_by = user_id
    topup.version += 1
    await self.db.commit()
```

### 5.5 并发控制：悲观锁

```python
# app/services/topup_service.py
from sqlalchemy import select

async def approve_topup_with_lock(self, topup_id: int, user_id: str):
    """审批充值（悲观锁）"""
    async with self.db.begin():
        # 锁定记录（SELECT ... FOR UPDATE）
        result = await self.db.execute(
            select(TopupRequest)
            .where(TopupRequest.id == topup_id)
            .with_for_update()
        )
        topup = result.scalar_one_or_none()

        if not topup:
            raise ResourceNotFoundException(code="BIZ_002")

        # 验证状态
        validate_status_transition(topup.status, TopupStatus.FINANCE_APPROVE)

        # 更新状态
        topup.status = TopupStatus.FINANCE_APPROVE
        topup.approved_by = user_id
        topup.version += 1

        # 事务自动提交（with_begin）
```

---

## 6. 数据库规范 (Database Rules)

### 6.1 核心约束

| 规则 | 说明 | 强制性 |
|-----|------|--------|
| **对齐 DATA_SCHEMA** | 所有表/字段必须与 DATA_SCHEMA.md 一致 | 🔴 强制 |
| **枚举值引用 SoT** | 状态枚举必须来自 STATE_MACHINE.md | 🔴 强制 |
| **金额用 Decimal** | 金额字段必须 `DECIMAL(15,2)`，禁止 `float` | 🔴 强制 |
| **时间用 UTC** | `TIMESTAMPTZ`，Python 使用 `datetime.now(timezone.utc)` | 🔴 强制 |
| **主键类型一致** | UUID 用于跨系统实体，BIGSERIAL 用于业务表 | 🔴 强制 |

### 6.2 SQLAlchemy 模型定义

```python
# app/models/topup.py
from sqlalchemy import Column, BigInteger, String, Numeric, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
from datetime import datetime, timezone

class TopupRequest(Base):
    __tablename__ = "topup_requests"

    # 主键：BIGSERIAL
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # 唯一编号
    request_no = Column(String(50), unique=True, nullable=False)

    # 外键：BIGINT（对应 projects.id）
    project_id = Column(BigInteger, ForeignKey("projects.id"), nullable=False)

    # 外键：UUID（对应 users.id）
    applicant_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # 金额：DECIMAL(15,2)
    amount = Column(Numeric(15, 2), nullable=False, default=0.00)

    # 枚举状态（对齐 STATE_MACHINE.md）
    status = Column(String(20), nullable=False, default="draft")

    # 时间：TIMESTAMPTZ（UTC）
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    # 乐观锁版本号
    version = Column(Integer, default=1, nullable=False)
```

### 6.3 枚举类定义

**引用**: STATE_MACHINE.md

```python
# app/core/enums.py
from enum import Enum

class TopupStatus(str, Enum):
    """充值状态枚举（对齐 STATE_MACHINE.md）"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    FINANCE_APPROVE = "finance_approve"
    PAID = "paid"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class UserRole(str, Enum):
    """用户角色枚举（对齐 AUTH_SPEC.md）"""
    ADMIN = "admin"
    FINANCE = "finance"
    DATA_OPERATOR = "data_operator"
    ACCOUNT_MANAGER = "account_manager"
    MEDIA_BUYER = "media_buyer"
```

### 6.4 禁止事项

❌ **禁止使用 float 存储金额**
```python
# ❌ 错误
amount = Column(Float)  # 禁止

# ✅ 正确
amount = Column(Numeric(15, 2))
```

❌ **禁止使用 naive datetime**
```python
# ❌ 错误
created_at = datetime.now()  # 无时区信息

# ✅ 正确
created_at = datetime.now(timezone.utc)
```

❌ **禁止自创状态枚举**
```python
# ❌ 错误
class TopupStatus(str, Enum):
    PENDING = "pending"  # STATE_MACHINE.md 中不存在

# ✅ 正确：对齐 STATE_MACHINE.md
class TopupStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
```

---

## 7. Alembic 迁移规范 (Migration Rules)

### 7.1 迁移流程

```
1. 修改 SQLAlchemy 模型（app/models/）
   ↓
2. 生成迁移脚本: `alembic revision --autogenerate -m "描述"`
   ↓
3. 检查迁移脚本（手动验证 upgrade/downgrade）
   ↓
4. 更新 DATA_SCHEMA.md（同步字段定义）
   ↓
5. 提交 PR（迁移脚本 + 模型 + 文档）
   ↓
6. Review 通过后执行: `alembic upgrade head`
```

### 7.2 迁移命名规范

```bash
# 格式: YYYYMMDD_HHMM_description.py
# 示例:
alembic revision --autogenerate -m "add topup_requests table"
# 生成: versions/20250122_1430_add_topup_requests_table.py
```

### 7.3 迁移注意事项

| 规则 | 说明 | 强制性 |
|-----|------|--------|
| **无损迁移** | 线上可滚动升级，不丢失数据 | 🔴 强制 |
| **禁止业务数据** | 迁移脚本不写业务数据（种子数据用脚本） | 🔴 强制 |
| **架构师审核** | 所有迁移必须经 DBA/架构师审核 | 🔴 强制 |
| **测试回滚** | 必须测试 `downgrade` 可正常回滚 | 🟡 推荐 |

### 7.4 迁移示例

```python
# alembic/versions/20250122_1430_add_topup_requests_table.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

def upgrade():
    op.create_table(
        'topup_requests',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('request_no', sa.String(50), nullable=False),
        sa.Column('project_id', sa.BigInteger(), nullable=False),
        sa.Column('applicant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False, server_default='0.00'),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('request_no'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['applicant_id'], ['users.id'])
    )
    op.create_index('idx_topup_requests_project', 'topup_requests', ['project_id'])

def downgrade():
    op.drop_index('idx_topup_requests_project')
    op.drop_table('topup_requests')
```

---

## 8. 并发控制 (Concurrency & Locking)

**引用**: MASTER_SPEC.md 第 6 章

### 8.1 三种锁机制

| 锁类型 | 使用场景 | 实现方式 | 性能 |
|-------|---------|---------|------|
| **乐观锁** | 并发写入冲突少的场景（如充值审批） | `version` 字段 + `expected_version` 参数 | 🟢 高 |
| **悲观锁** | 并发写入冲突多的场景（如余额扣减） | `SELECT ... FOR UPDATE` | 🟡 中 |
| **分布式锁** | 跨进程/跨服务的并发控制（如批量任务） | Redis `SETNX` | 🟡 中 |

### 8.2 乐观锁实现

```python
# Service 层
async def update_topup(self, topup_id: int, data: dict, expected_version: int):
    topup = await self.get_topup(topup_id)

    # 验证版本号
    if topup.version != expected_version:
        raise ConcurrencyConflictError(code="STATE_409")

    # 更新字段
    for key, value in data.items():
        setattr(topup, key, value)

    topup.version += 1
    await self.db.commit()
```

### 8.3 悲观锁实现

```python
# Service 层（事务内）
async def deduct_balance(self, project_id: int, amount: Decimal):
    async with self.db.begin():
        # 锁定项目记录
        result = await self.db.execute(
            select(Project)
            .where(Project.id == project_id)
            .with_for_update()
        )
        project = result.scalar_one()

        # 检查余额
        if project.balance < amount:
            raise BusinessRuleException(code="BIZ_101")  # 余额不足

        # 扣减余额
        project.balance -= amount
        # 事务自动提交
```

### 8.4 分布式锁实现

```python
# app/utils/redis_lock.py
import redis
from contextlib import asynccontextmanager

class RedisLock:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    @asynccontextmanager
    async def acquire(self, key: str, timeout: int = 10):
        """获取分布式锁"""
        lock_key = f"lock:{key}"
        acquired = self.redis.set(lock_key, "1", nx=True, ex=timeout)

        if not acquired:
            raise BusinessRuleException(message="资源被锁定，请稍后重试")

        try:
            yield
        finally:
            self.redis.delete(lock_key)

# 使用示例
async def batch_import_daily_reports(self, file_path: str):
    async with redis_lock.acquire("daily_report_import"):
        # 批量导入逻辑（确保同一时间只有一个导入任务）
        pass
```

---

## 9. 缓存规范 (Caching Rules)

### 9.1 缓存策略

| 数据类型 | 是否缓存 | 缓存时间 | 失效策略 |
|---------|---------|---------|---------|
| 项目列表 | ✅ 是 | 5 分钟 | 项目创建/更新时清除 |
| 用户信息 | ✅ 是 | 10 分钟 | 用户更新时清除 |
| 充值记录 | ❌ 否 | - | 实时查询 |
| 日报数据 | ❌ 否 | - | 实时查询 |
| 账本余额 | ❌ 否 | - | 实时查询（强一致性） |

### 9.2 缓存 Key 命名规范

```python
# 格式: {模块}:{实体}:{ID}
# 示例:
CACHE_KEY_USER = "user:profile:{user_id}"
CACHE_KEY_PROJECT_LIST = "project:list:user:{user_id}"
CACHE_KEY_PROJECT_DETAIL = "project:detail:{project_id}"
```

### 9.3 缓存使用示例

```python
# app/services/project_service.py
import redis
import json

async def get_project(self, project_id: int) -> Project:
    """获取项目（带缓存）"""
    cache_key = f"project:detail:{project_id}"

    # 1. 尝试从缓存获取
    cached = redis_client.get(cache_key)
    if cached:
        return Project(**json.loads(cached))

    # 2. 查询数据库
    project = await self.db.get(Project, project_id)
    if not project:
        raise ResourceNotFoundException(code="BIZ_002")

    # 3. 写入缓存（5分钟）
    redis_client.setex(cache_key, 300, json.dumps(project.dict()))

    return project

async def update_project(self, project_id: int, data: dict):
    """更新项目（清除缓存）"""
    project = await self.get_project(project_id)

    for key, value in data.items():
        setattr(project, key, value)

    await self.db.commit()

    # 清除缓存
    cache_key = f"project:detail:{project_id}"
    redis_client.delete(cache_key)
```

---

## 10. 日志与监控 (Logging & Monitoring)

### 10.1 日志规范

| 日志级别 | 使用场景 | 示例 |
|---------|---------|------|
| **DEBUG** | 开发调试 | 变量值、SQL 查询 |
| **INFO** | 关键业务操作 | 用户登录、充值创建、状态流转 |
| **WARNING** | 可恢复的异常 | 缓存失效、外部 API 慢响应 |
| **ERROR** | 业务异常 | 余额不足、状态流转失败 |
| **CRITICAL** | 系统级错误 | 数据库连接失败、Redis 宕机 |

### 10.2 request_id 贯穿全流程

```python
# app/core/logging.py
import logging
import contextvars

request_id_var = contextvars.ContextVar("request_id", default=None)

class RequestIDFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get() or "N/A"
        return True

# 配置日志格式
logging.basicConfig(
    format="%(asctime)s [%(request_id)s] %(levelname)s: %(message)s"
)

# Middleware 设置 request_id
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid4())
    request_id_var.set(request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

### 10.3 审计日志（Audit Log）

```python
# app/utils/audit.py
from app.models.audit_log import AuditLog

async def log_audit(
    db: AsyncSession,
    module: str,
    action: str,
    entity_id: str,
    user_id: str,
    user_role: str,
    payload_before: dict = None,
    payload_after: dict = None
):
    """记录审计日志"""
    audit = AuditLog(
        module=module,
        action=action,
        entity_id=entity_id,
        performed_by=user_id,
        role=user_role,
        payload_before=payload_before,
        payload_after=payload_after,
        ip_address=request_id_var.get("ip"),
        user_agent=request_id_var.get("user_agent")
    )
    db.add(audit)
    await db.commit()

# 使用示例
async def approve_topup(self, topup_id: int, user_id: str, user_role: str):
    topup = await self.get_topup(topup_id)

    # 记录审计日志
    await log_audit(
        db=self.db,
        module="topup",
        action="approve",
        entity_id=str(topup_id),
        user_id=user_id,
        user_role=user_role,
        payload_before={"status": topup.status},
        payload_after={"status": "finance_approve"}
    )

    topup.status = "finance_approve"
    await self.db.commit()
```

---

## 11. 错误处理 (Error Handling)

### 11.1 核心约束

| 规则 | 说明 | 强制性 |
|-----|------|--------|
| **错误码引用 SoT** | 所有错误码必须来自 ERROR_CODES_SOT.md | 🔴 强制 |
| **禁止原生异常** | 不得直接 `raise Exception`，必须使用自定义异常 | 🔴 强制 |
| **统一异常封装** | 使用 `BusinessRuleException`、`ResourceNotFoundException` 等 | 🔴 强制 |

### 11.2 自定义异常类

```python
# app/exceptions/handlers.py
class AppException(Exception):
    """基础异常类"""
    def __init__(self, message: str, code: str, status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)

class BusinessRuleException(AppException):
    """业务规则异常"""
    def __init__(self, message: str, code: str = "BIZ_001"):
        super().__init__(message, code, status_code=400)

class ResourceNotFoundException(AppException):
    """资源不存在异常"""
    def __init__(self, message: str = "资源不存在", code: str = "BIZ_002"):
        super().__init__(message, code, status_code=404)

class ConcurrencyConflictError(AppException):
    """并发冲突异常"""
    def __init__(self, message: str, code: str = "STATE_409"):
        super().__init__(message, code, status_code=409)
```

### 11.3 全局异常处理器

```python
# app/main.py
from fastapi import FastAPI, Request
from app.exceptions import AppException
from app.core.response import error_response

app = FastAPI()

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            message=exc.message,
            code=exc.code
        )
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=error_response(
            message="系统内部错误",
            code="SYS_001"
        )
    )
```

---

## 12. 测试规范 (Testing Guide)

### 12.1 测试分类

| 测试类型 | 测试范围 | 工具 | 覆盖率要求 |
|---------|---------|------|-----------|
| **单元测试** | Service/Repository 层逻辑 | Pytest | > 80% |
| **集成测试** | API 端到端流程 | Pytest + TestClient | > 70% |
| **E2E 测试** | 前后端联调（可选） | Playwright | - |

### 12.2 测试目录结构

```
tests/
├── conftest.py              # Pytest 配置与 Fixture
├── unit/                    # 单元测试
│   ├── test_services/
│   │   ├── test_topup_service.py
│   │   └── test_project_service.py
│   └── test_models/
│       └── test_topup_model.py
└── integration/             # 集成测试
    └── test_api/
        ├── test_topups.py
        └── test_projects.py
```

### 12.3 Fixture 示例

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from httpx import AsyncClient
from app.main import app
from app.db.base import Base

@pytest.fixture(scope="session")
async def engine():
    """测试数据库引擎"""
    engine = create_async_engine("postgresql+asyncpg://test:test@localhost/test_db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db(engine):
    """测试数据库会话"""
    async with AsyncSession(engine) as session:
        yield session

@pytest.fixture
async def client():
    """测试 HTTP 客户端"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def auth_headers():
    """认证 Header"""
    token = "test_jwt_token"
    return {"Authorization": f"Bearer {token}"}
```

### 12.4 单元测试示例

```python
# tests/unit/test_services/test_topup_service.py
import pytest
from app.services.topup_service import TopupService
from app.exceptions import BusinessRuleException

@pytest.mark.asyncio
async def test_create_topup_success(db):
    """测试创建充值成功"""
    service = TopupService(db)
    topup = await service.create_topup({
        "project_id": 1,
        "amount": 1000.00,
        "urgency_level": "normal"
    }, user_id="user-001")

    assert topup.status == "draft"
    assert topup.amount == 1000.00

@pytest.mark.asyncio
async def test_create_topup_invalid_amount(db):
    """测试创建充值（金额无效）"""
    service = TopupService(db)

    with pytest.raises(BusinessRuleException) as exc_info:
        await service.create_topup({
            "project_id": 1,
            "amount": -100.00,  # 负数
            "urgency_level": "normal"
        }, user_id="user-001")

    assert exc_info.value.code == "BIZ_100"
```

### 12.5 集成测试示例

```python
# tests/integration/test_api/test_topups.py
import pytest

@pytest.mark.asyncio
async def test_create_topup_api(client, auth_headers):
    """测试创建充值 API"""
    response = await client.post("/api/v1/topups", json={
        "project_id": 1,
        "amount": "1000.00",
        "urgency_level": "normal",
        "expected_pay_date": "2025-02-01"
    }, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "draft"

@pytest.mark.asyncio
async def test_approve_topup_concurrency(client, auth_headers, db):
    """测试充值审批并发冲突"""
    # 1. 创建充值
    topup = await create_test_topup(db)

    # 2. 用户A审批（version=1）
    response1 = await client.post(f"/api/v1/topups/{topup.id}/approve", json={
        "expected_version": 1
    }, headers=auth_headers)
    assert response1.status_code == 200

    # 3. 用户B审批（version=1，应失败）
    response2 = await client.post(f"/api/v1/topups/{topup.id}/approve", json={
        "expected_version": 1
    }, headers=auth_headers)
    assert response2.status_code == 409
    assert response2.json()["code"] == "STATE_409"
```

---

## 13. 性能规范 (Performance Rules)

### 13.1 数据库查询优化

| 规则 | 说明 | 强制性 |
|-----|------|--------|
| **索引覆盖** | WHERE/JOIN 字段必须有索引 | 🔴 强制 |
| **避免 N+1** | 使用 `joinedload`/`selectinload` 预加载关联 | 🔴 强制 |
| **分页查询** | 大数据集必须分页（limit/offset） | 🔴 强制 |
| **避免 SELECT *** | 仅查询需要的字段 | 🟡 推荐 |

### 13.2 避免 N+1 查询

```python
# ❌ 错误：N+1 查询
async def get_projects_with_members(self):
    projects = await self.db.execute(select(Project))
    for project in projects:
        # 每个项目额外查询一次（N+1）
        members = await self.db.execute(
            select(ProjectMember).where(ProjectMember.project_id == project.id)
        )

# ✅ 正确：使用 joinedload
from sqlalchemy.orm import joinedload

async def get_projects_with_members(self):
    result = await self.db.execute(
        select(Project).options(joinedload(Project.members))
    )
    projects = result.unique().scalars().all()
```

### 13.3 分页查询

```python
# app/services/project_service.py
async def get_projects_paginated(self, page: int = 1, page_size: int = 20):
    """分页查询项目"""
    offset = (page - 1) * page_size

    # 查询总数
    count_result = await self.db.execute(select(func.count(Project.id)))
    total = count_result.scalar()

    # 查询分页数据
    result = await self.db.execute(
        select(Project)
        .order_by(Project.created_at.desc())
        .limit(page_size)
        .offset(offset)
    )
    projects = result.scalars().all()

    return {
        "items": projects,
        "total": total,
        "page": page,
        "page_size": page_size
    }
```

---

## 14. 安全规范 (Security Rules)

### 14.1 核心约束

**引用**: AUTH_SPEC.md、RLS_POLICIES_SOT.md

| 规则 | 说明 | 强制性 |
|-----|------|--------|
| **不信任 JWT** | 每次请求查询真实用户与角色 | 🔴 强制 |
| **敏感字段过滤** | 不返回 `password_hash` 等敏感字段 | 🔴 强制 |
| **SQL 注入防护** | 使用参数化查询（SQLAlchemy 自动处理） | 🔴 强制 |
| **XSS 防护** | 输入验证（Pydantic 自动处理） | 🔴 强制 |
| **CSRF 防护** | 写操作必须带 `request_id` | 🟡 推荐 |

### 14.2 JWT 验证与用户查询

```python
# app/api/deps.py
from fastapi import Depends, HTTPException
from app.core.security import verify_token
from app.models.user import User

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前用户（不信任 JWT，查询数据库）"""
    # 1. 验证 JWT
    payload = verify_token(token)
    user_id = payload.get("sub")

    # 2. 查询真实用户（含角色）
    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")

    return user
```

### 14.3 敏感字段过滤

```python
# app/schemas/user.py
from pydantic import BaseModel

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    # ❌ 不包含 password_hash
    # ❌ 不包含 refresh_token

    class Config:
        from_attributes = True
```

---

## 15. PR 规范 (Pull Request Rules)

### 15.1 PR 提交检查清单

- [ ] 已阅读相关 SoT 文档（API_SOT、DATA_SCHEMA、STATE_MACHINE 等）
- [ ] 代码对齐 SoT（无字段发明、无状态发明、无错误码发明）
- [ ] 已编写单元测试与集成测试
- [ ] 测试通过（`pytest`）
- [ ] 代码格式化（`black .`）
- [ ] Linter 检查通过（`ruff check`）
- [ ] 数据库迁移已生成（如有模型变更）
- [ ] DATA_SCHEMA.md 已更新（如有模型变更）
- [ ] API_SOT.md 已更新（如有新增 API）
- [ ] 提交信息清晰（格式: `feat: 新增充值审批 API`）

### 15.2 PR 描述模板

```markdown
## 变更类型
- [ ] 新增功能
- [ ] Bug 修复
- [ ] 重构
- [ ] 文档更新
- [ ] 性能优化

## 变更说明
简要描述本次变更的目的与实现方式。

## 相关 SoT 文档
- [ ] API_SOT.md
- [ ] DATA_SCHEMA.md
- [ ] STATE_MACHINE.md
- [ ] TOPUP_SOT.md
- [ ] 其他: ___________

## 测试覆盖
- [ ] 单元测试
- [ ] 集成测试
- [ ] 手动测试

## 自检清单
- [ ] 无字段发明
- [ ] 无状态发明
- [ ] 无错误码发明
- [ ] 代码已格式化
- [ ] 测试已通过
- [ ] 文档已更新
```

### 15.3 Code Review 关注点

| 审查维度 | 关键问题 |
|---------|---------|
| **SoT 对齐** | 字段/状态/错误码是否对齐 SoT？ |
| **分层架构** | 业务逻辑是否在 Service 层？Router 是否包含逻辑？ |
| **状态机** | 状态流转是否合法？是否遗漏验证？ |
| **并发控制** | 是否需要乐观锁/悲观锁？是否有并发风险？ |
| **性能** | 是否有 N+1 查询？是否需要分页？ |
| **安全** | 是否有 SQL 注入风险？敏感字段是否过滤？ |
| **测试** | 测试是否覆盖关键场景？是否测试边界条件？ |

---

## 16. 附录：开发者自检清单

### 16.1 SoT 对齐自检

- [ ] 所有字段来自 DATA_SCHEMA.md
- [ ] 所有状态来自 STATE_MACHINE.md
- [ ] 所有错误码来自 ERROR_CODES_SOT.md
- [ ] 角色仅使用 5 个标准角色（admin/finance/data_operator/account_manager/media_buyer）
- [ ] 金额字段使用 Decimal（不用 float）
- [ ] 时间字段使用 UTC（不用 naive datetime）

### 16.2 架构分层自检

- [ ] Router 层仅处理路由与验证
- [ ] Service 层包含所有业务逻辑
- [ ] 数据权限过滤在 Service 层
- [ ] 状态机验证在 Service 层
- [ ] 使用统一响应格式（Envelope）

### 16.3 并发控制自检

- [ ] 并发写入场景已加锁（乐观/悲观）
- [ ] 乐观锁使用 `version` + `expected_version`
- [ ] 悲观锁使用 `SELECT ... FOR UPDATE`
- [ ] 事务边界清晰（`async with db.begin()`）

### 16.4 测试覆盖自检

- [ ] Service 层单元测试覆盖 > 80%
- [ ] API 集成测试覆盖关键流程
- [ ] 测试状态机流转（合法/非法）
- [ ] 测试并发冲突场景
- [ ] 测试权限过滤（不同角色）

### 16.5 性能与安全自检

- [ ] 无 N+1 查询
- [ ] 大数据集使用分页
- [ ] WHERE/JOIN 字段有索引
- [ ] 敏感字段已过滤（password_hash）
- [ ] JWT 不作为权限唯一来源
- [ ] 所有写操作记录审计日志

---

## 17. 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|-----|------|----------|------|
| v1.0 | 2025-01-22 | 初始版本，定义后端开发完整规范，包含 16 章节:<br>1. 技术栈说明<br>2. 目录结构<br>3. 开发流程<br>4. API 规范<br>5. Service 规范<br>6. 数据库规范<br>7. 迁移规范<br>8. 并发控制<br>9. 缓存规范<br>10. 日志与监控<br>11. 错误处理<br>12. 测试规范<br>13. 性能规范<br>14. 安全规范<br>15. PR 规范<br>16. 自检清单 | 后端开发团队 |

---

**文档维护者**: 后端开发团队
**最后审核**: 2025-01-22
**下次审核**: 技术栈重大升级时或季度性审核
