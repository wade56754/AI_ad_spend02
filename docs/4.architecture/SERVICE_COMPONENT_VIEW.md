---
version: v1.0
status: ready_for_production
layer: architecture
owner: wade
last_reviewed: 2025-11-27
baseline: MASTER.md v3.4, SoT Freeze v1.0, Dev-Guides Freeze v2.1
---

# Service Component View (服务组件视图 - C4 Level 2/3)

## 1. Overview

### 1.1 Purpose of Service Component View

服务组件视图 (Service Component View) 是C4模型的第二、三层视图，从技术实现角度展示系统的容器和组件结构。本文档回答以下问题:

- **What Containers**: 系统由哪些应用容器组成 (Web App, API Server, Database, etc.)
- **What Components**: 每个容器内部有哪些组件 (Router, Service, Repository)
- **How They Interact**: 组件间如何交互 (API调用, Database访问, Event发送)
- **What Technologies**: 使用哪些技术栈 (FastAPI, Next.js, PostgreSQL, etc.)

### 1.2 C4 Model Level 2/3 Definition

**C4模型层级**:
```
Level 1: System Context (SYSTEM_CONTEXT_VIEW.md) - 系统与外部环境
Level 2: Container (本文档 §2-3) - 容器(应用/数据库/队列)
Level 3: Component (本文档 §4-5) - 组件(类/模块)
Level 4: Code (代码实现) - 不在架构文档范围
```

### 1.3 Baseline References

**引用**:
- **MASTER.md v3.4**: 系统架构宪法，定义三大不可变量
- **API_DEVELOPMENT_FLOW.md**: 6步开发流程
- **DATA_SCHEMA.md v5.2**: 数据库表结构
- **DDD_API_ARCHITECTURE.md**: 三层架构设计

## 2. Container Diagram (C4 Level 2 - 容器视图)

### 2.1 Container Overview

```mermaid
C4Container
  title 容器视图 - AI广告代投系统

  Person(buyer, "投手", "media_buyer")
  Person(operator, "运营", "data_operator")
  Person(finance, "财务", "finance")
  Person(admin, "管理员", "admin")

  System_Boundary(system, "AI Ad Spend System") {
    Container(web, "Web Application", "Next.js 14, TypeScript, TanStack Query", "前端单页应用<br/>React Server Components")
    Container(api, "API Server", "FastAPI, Python 3.11, Pydantic", "后端API服务<br/>RESTful API")
    ContainerDb(db, "Database", "PostgreSQL 15 (Supabase)", "业务数据存储<br/>双账本+8状态机")
    Container(queue, "Task Queue", "Celery + Redis (规划中)", "异步任务处理<br/>Email/导入任务")
    ContainerDb(cache, "Cache", "Redis (规划中)", "TanStack Query缓存<br/>API响应缓存")
  }

  System_Ext(meta, "Meta Ads API", "广告消耗数据")
  System_Ext(email, "Email Service", "SMTP通知")
  System_Ext(storage, "File Storage", "CSV/凭证存储")

  Rel(buyer, web, "提交日报", "HTTPS")
  Rel(operator, web, "审核日报", "HTTPS")
  Rel(finance, web, "审批充值", "HTTPS")
  Rel(admin, web, "系统管理", "HTTPS")

  Rel(web, api, "API调用", "HTTPS/REST")
  Rel(api, db, "读写数据", "PostgreSQL Wire Protocol")
  Rel(api, queue, "发送任务", "Redis Protocol")
  Rel(api, cache, "缓存查询", "Redis Protocol")

  Rel(api, meta, "拉取消耗", "HTTPS/REST")
  Rel(queue, email, "发送邮件", "SMTP")
  Rel(api, storage, "存储/读取", "S3 API/本地FS")

  UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

### 2.2 Container Details

#### 2.2.1 Web Application (前端应用)

**技术栈**:
- **框架**: Next.js 14 (App Router)
- **语言**: TypeScript 5.3
- **UI库**: Tailwind CSS + shadcn/ui
- **状态管理**: TanStack Query v5 (服务端状态) + Zustand (客户端状态)
- **路由**: Next.js App Router
- **认证**: Supabase Auth Client

**部署方式**:
- **开发环境**: `npm run dev` (localhost:3000)
- **生产环境**: Vercel / Docker + Nginx

**环境变量** (`.env.local`):
```bash
NEXT_PUBLIC_API_URL=https://api.example.com
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbG...
```

**关键目录结构**:
```
frontend/
├── app/                    # App Router路由
│   ├── (auth)/            # 认证路由组
│   │   ├── login/
│   │   └── logout/
│   ├── (dashboard)/       # 仪表盘路由组
│   │   ├── projects/
│   │   ├── daily-reports/
│   │   ├── topups/
│   │   └── reconciliation/
│   └── layout.tsx         # 根布局
├── components/            # React组件
│   ├── ui/               # shadcn/ui组件
│   ├── forms/            # 表单组件
│   └── charts/           # 图表组件
├── lib/                  # 工具库
│   ├── api-client.ts     # API客户端
│   ├── supabase.ts       # Supabase客户端
│   └── query-hooks.ts    # TanStack Query hooks
└── types/                # TypeScript类型定义
```

**引用**: FRONTEND_DEVELOPMENT_RULES.md

#### 2.2.2 API Server (后端API服务)

**技术栈**:
- **框架**: FastAPI 0.109
- **语言**: Python 3.11
- **ORM**: SQLAlchemy 2.0 (同步版)
- **迁移**: Alembic
- **认证**: Supabase Auth + JWT验证
- **校验**: Pydantic v2
- **日志**: structlog

**部署方式**:
- **开发环境**: `uvicorn main:app --reload` (localhost:8000)
- **生产环境**: Docker + Gunicorn + Uvicorn Workers

**环境变量** (`.env`):
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/ai_ad_spend
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbG...
SUPABASE_JWT_SECRET=your-jwt-secret
```

**关键目录结构**:
```
backend/
├── main.py               # FastAPI应用入口
├── core/                 # 核心模块
│   ├── config.py        # 配置管理
│   ├── error_codes.py   # 错误码定义
│   ├── response.py      # 响应封装
│   └── security.py      # 认证中间件
├── models/              # SQLAlchemy模型
│   ├── __init__.py
│   ├── user.py
│   ├── project.py
│   ├── daily_report.py
│   ├── ledger.py
│   └── ...
├── schemas/             # Pydantic模型
│   ├── user.py
│   ├── project.py
│   ├── daily_report.py
│   └── ...
├── services/            # Service层
│   ├── user_service.py
│   ├── project_service.py
│   ├── daily_report_service.py
│   ├── ledger_service.py
│   └── ...
├── routers/             # API路由
│   ├── users.py
│   ├── projects.py
│   ├── daily_reports.py
│   ├── topups.py
│   └── ...
├── repositories/        # Repository层(规划中)
├── exceptions/          # 自定义异常
│   └── handlers.py
├── utils/               # 工具函数
│   ├── datetime.py
│   ├── decimal.py
│   └── validators.py
└── alembic/             # 数据库迁移
    └── versions/
```

**引用**: BACKEND_DEV_GUIDE.md

#### 2.2.3 Database (PostgreSQL数据库)

**技术栈**:
- **数据库**: PostgreSQL 15
- **托管服务**: Supabase (包含 Auth + Storage + Realtime)
- **Schema**: 详见 DATA_SCHEMA.md v5.2

**核心表分类**:

**用户与权限**:
- `users` (业务用户，主键UUID)
- `user_sessions` (登录会话)
- `audit_logs` (系统审计日志)

**业务核心**:
- `projects` (项目，主键BIGSERIAL)
- `ad_accounts` (广告账户)
- `daily_reports` (日报，8状态机)
- `ledger_entries` (账本记录，双账本)
- `topup_requests` (充值申请)
- `reconciliation_batches` (对账批次)

**数据库连接配置**:
```python
# backend/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://user:pass@localhost:5432/ai_ad_spend"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=40,
    echo=False  # 生产环境关闭SQL日志
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
```

**引用**: DATA_SCHEMA.md v5.2

#### 2.2.4 Task Queue (任务队列 - 规划中)

**技术栈**:
- **任务队列**: Celery 5.3
- **Broker**: Redis 7.0
- **Result Backend**: Redis 7.0

**使用场景**:
- Email通知发送 (异步)
- CSV批量导入 (后台任务)
- 定时拉取Meta Ads API数据 (Cron任务)

**示例任务**:
```python
# backend/tasks/email_tasks.py
from celery import Celery

app = Celery('tasks', broker='redis://localhost:6379/0')

@app.task
def send_trend_flagged_email(report_id: int):
    """发送趋势异常通知邮件"""
    # 实现邮件发送逻辑
    pass
```

#### 2.2.5 Cache (缓存 - 规划中)

**技术栈**:
- **缓存**: Redis 7.0

**使用场景**:
- TanStack Query缓存 (前端)
- API响应缓存 (后端)
- Session缓存 (后端)

**缓存策略**:
```python
# backend/core/cache.py
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_api_response(ttl: int = 300):
    """API响应缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator
```

## 3. Container Interaction Patterns (容器交互模式)

### 3.1 Request-Response Flow (请求-响应流)

```mermaid
sequenceDiagram
    participant User as 投手
    participant Web as Next.js
    participant API as FastAPI
    participant DB as PostgreSQL
    participant Auth as Supabase Auth

    User->>Web: 提交日报
    Web->>Auth: 获取Access Token
    Auth-->>Web: JWT Token
    Web->>API: POST /daily-reports<br/>Header: Authorization Bearer <token>
    API->>Auth: 验证JWT签名
    Auth-->>API: 返回user_id
    API->>DB: 查询users表获取role
    DB-->>API: role=media_buyer
    API->>API: 校验权限 @require_role('daily_report:submit')
    API->>DB: INSERT daily_reports<br/>status=raw_submitted
    DB-->>API: 返回日报ID
    API->>DB: INSERT daily_report_audit_logs
    API-->>Web: 200 OK {success: true, data: {id: 123}}
    Web-->>User: 提示"日报提交成功"
```

### 3.2 Async Task Flow (异步任务流 - 规划中)

```mermaid
sequenceDiagram
    participant API as FastAPI
    participant Queue as Celery
    participant Worker as Celery Worker
    participant Email as Email Service

    API->>API: 检测到 trend_flagged
    API->>Queue: send_task('send_trend_flagged_email', args=[report_id])
    API-->>Client: 200 OK (立即返回)

    Queue->>Worker: 分发任务
    Worker->>API: GET /daily-reports/{id}
    API-->>Worker: 日报详情
    Worker->>Email: SMTP发送邮件
    Email-->>Worker: 发送成功
    Worker->>Queue: 任务完成
```

## 4. Component Diagram (C4 Level 3 - 组件视图)

### 4.1 Backend Component Architecture (后端三层架构)

```mermaid
graph TD
    subgraph "API Server (FastAPI)"
        subgraph "Router Layer (路由层)"
            R1[users.py<br/>用户管理API]
            R2[projects.py<br/>项目管理API]
            R3[daily_reports.py<br/>日报管理API]
            R4[topups.py<br/>充值管理API]
            R5[ledger.py<br/>账本查询API]
        end

        subgraph "Service Layer (服务层)"
            S1[UserService<br/>用户业务逻辑]
            S2[ProjectService<br/>项目业务逻辑]
            S3[DailyReportService<br/>日报状态机]
            S4[TopupService<br/>充值审批流]
            S5[LedgerService<br/>双账本逻辑]
        end

        subgraph "Repository Layer (仓储层 - 规划中)"
            Repo1[UserRepository<br/>用户数据访问]
            Repo2[ProjectRepository<br/>项目数据访问]
            Repo3[DailyReportRepository<br/>日报数据访问]
            Repo4[TopupRepository<br/>充值数据访问]
            Repo5[LedgerRepository<br/>账本数据访问]
        end

        subgraph "Model Layer (模型层)"
            M1[(SQLAlchemy Models)]
            M2[(Pydantic Schemas)]
        end

        subgraph "Core Layer (核心层)"
            C1[Security<br/>JWT验证]
            C2[ErrorCodes<br/>错误码]
            C3[Response<br/>响应封装]
        end
    end

    R1 --> S1
    R2 --> S2
    R3 --> S3
    R4 --> S4
    R5 --> S5

    S1 --> Repo1
    S2 --> Repo2
    S3 --> Repo3
    S4 --> Repo4
    S5 --> Repo5

    Repo1 --> M1
    Repo2 --> M1
    Repo3 --> M1
    Repo4 --> M1
    Repo5 --> M1

    R1 --> C1
    R2 --> C1
    R3 --> C1
    S3 --> C2
    S4 --> C2
    R3 --> C3

    style S3 fill:#ff6b6b,stroke:#c92a2a,color:#fff
    style S5 fill:#ff6b6b,stroke:#c92a2a,color:#fff
```

### 4.2 Layer Responsibilities (层级职责)

#### 4.2.1 Router Layer (路由层)

**职责**:
- HTTP请求路由与参数解析
- Pydantic请求体校验
- JWT Token验证 (Depends)
- 调用Service层
- 响应封装 (success_response / error_response)

**禁止行为**:
- ❌ 禁止在Router层编写业务逻辑
- ❌ 禁止直接操作SQLAlchemy模型
- ❌ 禁止在Router层手动解析JWT (必须使用Depends)

**示例代码**:
```python
# backend/routers/daily_reports.py
from fastapi import APIRouter, Depends
from backend.core.security import get_current_user
from backend.core.response import success_response, error_response
from backend.services.daily_report_service import DailyReportService
from backend.schemas.daily_report import DailyReportCreate, DailyReportResponse

router = APIRouter(prefix="/api/v1/daily-reports", tags=["daily-reports"])

@router.post("", response_model=DailyReportResponse)
async def submit_daily_report(
    data: DailyReportCreate,
    current_user: User = Depends(get_current_user),
    service: DailyReportService = Depends()
):
    """提交日报 (投手)"""
    try:
        report = service.submit_report(data, current_user)
        return success_response(data=report)
    except BusinessRuleException as e:
        return error_response(code=e.code, message=e.message, status_code=e.status_code)
```

**引用**: API_DEVELOPMENT_FLOW.md §4 (Router层开发)

#### 4.2.2 Service Layer (服务层)

**职责**:
- 业务规则校验 (BUSINESS_RULES.md)
- 状态机流转 (STATE_MACHINE.md)
- 数据转换与计算
- 事务管理 (db.begin)
- 调用Repository层
- 触发Event (规划中)

**关键原则**:
- ✅ Service方法必须是原子操作 (要么全成功，要么全失败)
- ✅ Service方法必须使用 `@require_role` 装饰器校验权限
- ✅ Service方法必须处理所有业务异常，不得抛出未定义的Exception

**示例代码**:
```python
# backend/services/daily_report_service.py
from decimal import Decimal
from sqlalchemy.orm import Session
from backend.models import DailyReport, User
from backend.schemas.daily_report import DailyReportCreate
from backend.core.error_codes import BusinessErrorCodes, StateErrorCodes
from backend.exceptions import BusinessRuleException
from backend.utils.decorators import require_role

class DailyReportService:
    def __init__(self, db: Session):
        self.db = db

    @require_role('daily_report:submit')
    def submit_report(
        self,
        data: DailyReportCreate,
        current_user: User
    ) -> DailyReport:
        """提交日报 (投手) - BR-RPT-001"""

        # 1. 业务规则校验
        if data.report_date > date.today():
            raise BusinessRuleException(
                message="日期不能为未来",
                code=BusinessErrorCodes.INVALID_DATE.code  # BIZ_201
            )

        # 2. 幂等性检查
        existing = self.db.query(DailyReport).filter(
            DailyReport.report_date == data.report_date,
            DailyReport.ad_account_id == data.ad_account_id
        ).first()
        if existing:
            raise BusinessRuleException(
                message="该账户当日日报已存在",
                code=BusinessErrorCodes.RESOURCE_ALREADY_EXISTS.code  # BIZ_003
            )

        # 3. 创建日报 (初始状态: raw_submitted)
        with self.db.begin():
            report = DailyReport(
                report_date=data.report_date,
                ad_account_id=data.ad_account_id,
                conversions_raw=data.conversions_raw,
                raw_spend=data.raw_spend,
                status="raw_submitted",  # 初始状态
                submitted_by=current_user.id,
                submitted_at=datetime.now(timezone.utc)
            )
            self.db.add(report)
            self.db.flush()  # 获取ID

            # 4. 审计日志
            audit_log = DailyReportAuditLog(
                daily_report_id=report.id,
                action="submit",
                old_status=None,
                new_status="raw_submitted",
                audit_user_id=current_user.id,
                audit_time=datetime.now(timezone.utc)
            )
            self.db.add(audit_log)
            self.db.commit()

        return report

    @require_role('daily_report:final_confirm')
    def confirm_final(
        self,
        report_id: int,
        conversions_final: int,
        current_user: User
    ) -> DailyReport:
        """确认final粉数 (运营) - BR-RPT-005"""

        with self.db.begin():
            # 1. 锁定记录
            report = self.db.query(DailyReport).filter(
                DailyReport.id == report_id
            ).with_for_update().first()

            if not report:
                raise ResourceNotFoundException(code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code)

            # 2. 状态机校验
            if report.status != "final_pending":
                raise BusinessRuleException(
                    message=f"当前状态{report.status}不允许确认final",
                    code=StateErrorCodes.FORBIDDEN_TRANSITION.code  # STATE_400
                )

            # 3. 更新字段
            report.conversions_final = conversions_final
            report.status = "final_confirmed"
            report.updated_by = current_user.id

            # 4. 审计日志
            audit_log = DailyReportAuditLog(
                daily_report_id=report.id,
                action="final_confirm",
                old_status="final_pending",
                new_status="final_confirmed",
                audit_user_id=current_user.id,
                audit_notes=f"确认final粉数: {conversions_final}"
            )
            self.db.add(audit_log)
            self.db.commit()

        return report
```

**引用**: API_DEVELOPMENT_FLOW.md §5 (Service层开发)

#### 4.2.3 Repository Layer (仓储层 - 规划中)

**职责**:
- 封装SQLAlchemy查询逻辑
- 提供数据访问接口 (CRUD)
- 隐藏ORM实现细节

**示例代码**:
```python
# backend/repositories/daily_report_repository.py
from sqlalchemy.orm import Session
from backend.models import DailyReport
from typing import List, Optional
from datetime import date

class DailyReportRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, report_id: int) -> Optional[DailyReport]:
        """根据ID查询日报"""
        return self.db.query(DailyReport).filter(DailyReport.id == report_id).first()

    def get_by_date_and_account(
        self,
        report_date: date,
        ad_account_id: int
    ) -> Optional[DailyReport]:
        """查询指定日期和账户的日报"""
        return self.db.query(DailyReport).filter(
            DailyReport.report_date == report_date,
            DailyReport.ad_account_id == ad_account_id
        ).first()

    def list_by_account(
        self,
        ad_account_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[DailyReport]:
        """查询账户的日报列表"""
        query = self.db.query(DailyReport).filter(
            DailyReport.ad_account_id == ad_account_id
        )
        if start_date:
            query = query.filter(DailyReport.report_date >= start_date)
        if end_date:
            query = query.filter(DailyReport.report_date <= end_date)
        return query.order_by(DailyReport.report_date.desc()).all()

    def create(self, report: DailyReport) -> DailyReport:
        """创建日报"""
        self.db.add(report)
        self.db.flush()
        return report

    def update(self, report: DailyReport) -> DailyReport:
        """更新日报"""
        self.db.flush()
        return report
```

#### 4.2.4 Model Layer (模型层)

**职责**:
- SQLAlchemy模型定义 (ORM)
- Pydantic模型定义 (请求/响应校验)
- 数据库表结构映射

**SQLAlchemy Model示例**:
```python
# backend/models/daily_report.py
from sqlalchemy import Column, Integer, Date, String, Numeric, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from backend.models.base import Base

class DailyReport(Base):
    __tablename__ = "daily_reports"

    id = Column(Integer, primary_key=True)
    report_date = Column(Date, nullable=False)
    ad_account_id = Column(Integer, ForeignKey("ad_accounts.id"), nullable=False)

    # 三数据流字段
    conversions_raw = Column(Integer, default=0)
    raw_spend = Column(Numeric(15, 2), default=0.00)
    conversions_final = Column(Integer, default=0)
    real_spend = Column(Numeric(15, 2), default=0.00)

    # 状态机
    status = Column(String(20), nullable=False, default="raw_submitted")

    # 审计字段
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False)
    submitted_by = Column(String(255), ForeignKey("users.id"))

    # Relationships
    ad_account = relationship("AdAccount", back_populates="daily_reports")
    submitted_by_user = relationship("User", foreign_keys=[submitted_by])
```

**Pydantic Schema示例**:
```python
# backend/schemas/daily_report.py
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from datetime import date

class DailyReportCreate(BaseModel):
    report_date: date
    ad_account_id: int
    conversions_raw: int = Field(ge=0)
    raw_spend: Decimal = Field(ge=0, decimal_places=2)

    @field_validator('report_date')
    def validate_date_not_future(cls, v):
        if v > date.today():
            raise ValueError("日期不能为未来")
        return v

class DailyReportResponse(BaseModel):
    id: int
    report_date: date
    ad_account_id: int
    conversions_raw: int
    raw_spend: Decimal
    conversions_final: int
    real_spend: Decimal
    status: str

    class Config:
        from_attributes = True
```

**引用**: DATA_SCHEMA.md v5.2

### 4.3 Frontend Component Architecture (前端组件架构)

```mermaid
graph TD
    subgraph "Next.js App"
        subgraph "Pages (App Router)"
            P1[app/(dashboard)/daily-reports/page.tsx]
            P2[app/(dashboard)/projects/page.tsx]
            P3[app/(dashboard)/topups/page.tsx]
        end

        subgraph "Components"
            C1[DailyReportForm<br/>日报提交表单]
            C2[DailyReportList<br/>日报列表]
            C3[StatusBadge<br/>状态徽章]
        end

        subgraph "Hooks (TanStack Query)"
            H1[useDailyReports<br/>日报查询]
            H2[useSubmitReport<br/>日报提交]
            H3[useConfirmFinal<br/>确认final]
        end

        subgraph "API Client"
            API[api-client.ts<br/>封装fetch调用]
        end

        subgraph "Supabase Client"
            SB[supabase.ts<br/>认证客户端]
        end
    end

    P1 --> C1
    P1 --> C2
    C1 --> H2
    C2 --> H1
    C2 --> C3

    H1 --> API
    H2 --> API
    H3 --> API

    API --> SB
```

**关键组件职责**:

**Pages (页面)**:
- 路由定义
- Server Component数据预取
- Client Component渲染

**Components (组件)**:
- UI展示
- 用户交互
- 状态管理 (Zustand)

**Hooks (TanStack Query)**:
- 服务端状态管理
- 缓存策略
- 乐观更新

**API Client**:
- HTTP请求封装
- 错误处理
- Token自动刷新

**引用**: FRONTEND_DEVELOPMENT_RULES.md

## 5. Technology Stack (技术栈清单)

### 5.1 Backend Stack

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **Framework** | FastAPI | 0.109 | Web框架 |
| **Language** | Python | 3.11 | 编程语言 |
| **ORM** | SQLAlchemy | 2.0 | 数据库ORM |
| **Migration** | Alembic | 1.13 | 数据库迁移 |
| **Validation** | Pydantic | v2 | 数据校验 |
| **Auth** | Supabase Auth | - | JWT认证 |
| **Database** | PostgreSQL | 15 | 关系型数据库 |
| **Task Queue** | Celery | 5.3 (规划中) | 异步任务 |
| **Cache** | Redis | 7.0 (规划中) | 缓存 |
| **Logging** | structlog | - | 结构化日志 |

### 5.2 Frontend Stack

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **Framework** | Next.js | 14 | React框架 |
| **Language** | TypeScript | 5.3 | 编程语言 |
| **UI Library** | Tailwind CSS | 3.4 | CSS框架 |
| **Components** | shadcn/ui | - | UI组件库 |
| **State (Server)** | TanStack Query | v5 | 服务端状态 |
| **State (Client)** | Zustand | 4.4 | 客户端状态 |
| **Forms** | React Hook Form | 7.49 | 表单管理 |
| **Charts** | Recharts | 2.10 | 图表库 |
| **Auth** | Supabase Client | - | 认证客户端 |

### 5.3 DevOps Stack

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **Container** | Docker | 24.0 | 容器化 |
| **CI/CD** | GitHub Actions | - | 持续集成 |
| **Deployment** | Vercel / Docker Compose | - | 部署平台 |
| **Monitoring** | Sentry (规划中) | - | 错误监控 |

## 6. Deployment Architecture (部署架构)

### 6.1 Development Environment

```mermaid
graph LR
    Dev[开发者本地]

    subgraph "Docker Compose"
        API[FastAPI<br/>localhost:8000]
        DB[PostgreSQL<br/>localhost:5432]
        Redis[Redis<br/>localhost:6379]
    end

    Web[Next.js Dev Server<br/>localhost:3000]
    Supabase[Supabase Cloud<br/>认证/存储]

    Dev --> Web
    Dev --> API
    Web --> API
    API --> DB
    API --> Redis
    Web --> Supabase
    API --> Supabase
```

**启动命令**:
```bash
# 后端
cd backend
docker-compose up -d  # 启动PostgreSQL + Redis
uvicorn main:app --reload

# 前端
cd frontend
npm run dev
```

### 6.2 Production Environment (生产环境 - 规划)

```mermaid
graph TD
    User[用户]

    subgraph "Vercel"
        Web[Next.js<br/>静态资源 + SSR]
    end

    subgraph "Docker Swarm / Kubernetes"
        LB[Nginx Load Balancer]
        API1[FastAPI Instance 1]
        API2[FastAPI Instance 2]
        API3[FastAPI Instance 3]
    end

    subgraph "Supabase Cloud"
        DB[PostgreSQL<br/>Primary + Replica]
        Auth[Supabase Auth]
    end

    Redis[Redis Cluster]

    User --> Web
    User --> LB
    Web --> LB
    LB --> API1
    LB --> API2
    LB --> API3
    API1 --> DB
    API2 --> DB
    API3 --> DB
    API1 --> Redis
    API2 --> Redis
    API3 --> Redis
    Web --> Auth
    API1 --> Auth
```

## 7. Traceability (可追溯性)

### 7.1 References to MASTER.md v3.4

- **§2 INV-001**: 双账本独立核算 → LedgerService
- **§2 INV-002**: 三数据流分离 → DailyReportService
- **§2 INV-003**: 8状态机强制流转 → DailyReportService.submit_report / confirm_final

### 7.2 References to API_DEVELOPMENT_FLOW.md

- **§4 Router层**: Router职责定义
- **§5 Service层**: Service职责定义
- **§6 三层架构原则**: Router → Service → Repository

### 7.3 References to DATA_SCHEMA.md v5.2

- **§3.3.1 daily_reports表**: DailyReport模型定义
- **§3.4.4 ledger_entries表**: LedgerEntry模型定义
- **§3.1.1 users表**: User模型定义

### 7.4 References to DDD_API_ARCHITECTURE.md

- **§3 领域驱动设计**: Service层DDD模式
- **§4 Repository模式**: Repository层设计

---

**文档状态**: ✅ Draft完成，等待审计
**维护责任**: Architecture Team + Backend Team
**下次审查**: 每季度或技术栈重大变更时
