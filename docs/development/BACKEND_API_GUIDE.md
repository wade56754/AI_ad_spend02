# 后端API开发指南

> **文档目的**: 提供完整的API设计规范、接口说明和开发指南
> **目标读者**: 后端开发工程师、前端开发工程师、测试工程师
> **更新日期**: 2025-11-11

---

## 📋 目录

1. [API设计原则](#-api设计原则)
2. [统一响应格式](#-统一响应格式)
3. [认证与授权](#-认证与授权)
4. [错误处理规范](#-错误处理规范)
5. [接口模块说明](#-接口模块说明)
6. [API文档生成](#-api文档生成)
7. [开发示例](#-开发示例)
8. [测试指南](#-测试指南)

---

## 🎯 API设计原则

### RESTful设计规范

1. **资源导向**
   - URL表示资源，使用名词而非动词
   - 使用复数形式表示资源集合
   - 使用HTTP方法表示操作

2. **版本管理**
   - API版本通过URL路径管理
   - 当前版本：`/api/v1/`
   - 向后兼容原则

3. **状态码使用**
   - 200-299: 成功响应
   - 400-499: 客户端错误
   - 500-599: 服务端错误

### URL设计规范

```bash
# 基础格式
https://domain.com/api/v1/{resource}/{id}

# 示例
GET    /api/v1/projects           # 获取项目列表
POST   /api/v1/projects           # 创建项目
GET    /api/v1/projects/{id}      # 获取特定项目
PUT    /api/v1/projects/{id}      # 更新项目
DELETE /api/v1/projects/{id}      # 删除项目

# 嵌套资源
GET    /api/v1/projects/{id}/accounts
POST   /api/v1/projects/{id}/accounts

# 查询参数
GET    /api/v1/projects?status=active&limit=20&offset=0
```

### 命名规范

- **资源名**: 小写字母，下划线分隔，复数形式
- **HTTP头部**: 首字母大写，单词间用连字符
- **JSON字段**: 小写字母，下划线分隔

---

## 📦 统一响应格式

### 成功响应

```json
{
  "success": true,
  "data": {
    // 实际数据内容
  },
  "message": "操作成功",
  "code": "SUCCESS",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-11-11T10:30:00.000Z",
  "pagination": {  // 分页数据时存在
    "page": 1,
    "page_size": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

### 错误响应

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "参数验证失败",
    "details": {
      "field": "email",
      "reason": "邮箱格式不正确"
    }
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-11-11T10:30:00.000Z"
}
```

### 数据格式规范

#### 分页响应
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "项目名称",
      "created_at": "2025-11-11T10:30:00.000Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 100,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

#### 批量操作响应
```json
{
  "success": true,
  "data": {
    "processed": 10,
    "successful": 8,
    "failed": 2,
    "results": [
      {
        "id": 1,
        "status": "success"
      },
      {
        "id": 2,
        "status": "failed",
        "error": "数据验证失败"
      }
    ]
  }
}
```

---

## 🔐 认证与授权

### JWT Token结构

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "role": "media_buyer",
  "permissions": [
    "project:read",
    "account:read",
    "report:read"
  ],
  "iat": 1736703000,
  "exp": 1736789400
}
```

### Token刷新机制

```python
# Access Token: 15分钟过期
# Refresh Token: 7天过期

# Token端点
POST /api/v1/auth/refresh
{
  "refresh_token": "refresh_token_string"
}

# 响应
{
  "success": true,
  "data": {
    "access_token": "new_access_token",
    "refresh_token": "new_refresh_token",  // 可选，有时只返回新的access_token
    "expires_in": 900  // 秒
  }
}
```

### 请求头规范

```bash
# 认证请求
Authorization: Bearer <access_token>

# 内容类型
Content-Type: application/json
Accept: application/json

# 追踪ID（推荐）
X-Request-ID: <uuid>

# 版本控制（推荐）
API-Version: v1
```

### 权限控制

```python
# 装饰器示例
@router.get("/projects")
@require_permission("project:read")
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pass

# 权限检查
def require_permission(permission: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get('current_user')
            if not user.has_permission(permission):
                raise HTTPException(
                    status_code=403,
                    detail="Insufficient permissions"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

---

## ⚠️ 错误处理规范

### 错误码定义

#### 通用错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|------------|------|
| SUCCESS | 200 | 操作成功 |
| VALIDATION_ERROR | 400 | 参数验证失败 |
| UNAUTHORIZED | 401 | 未认证 |
| FORBIDDEN | 403 | 无权限 |
| NOT_FOUND | 404 | 资源不存在 |
| CONFLICT | 409 | 资源冲突 |
| RATE_LIMIT | 429 | 请求过于频繁 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |

#### 业务错误码

| 错误码 | 说明 |
|--------|------|
| PROJECT_NOT_FOUND | 项目不存在 |
| PROJECT_CODE_EXISTS | 项目代码已存在 |
| ACCOUNT_NOT_ASSIGNED | 账户未分配给用户 |
| INSUFFICIENT_BALANCE | 账户余额不足 |
| TOPUP_ALREADY_APPROVED | 充值已审批 |
| INVALID_STATE_TRANSITION | 无效的状态转换 |

### 错误响应示例

```python
# 自定义异常
class ValidationError(Exception):
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)

# 异常处理器
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": exc.message,
                "details": {
                    "field": exc.field
                } if exc.field else None
            },
            "request_id": request.state.request_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

---

## 📚 接口模块说明

### 1. 认证模块 (`/api/v1/auth`)

#### 用户注册
```bash
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "Password123!",
  "full_name": "张三",
  "role": "media_buyer"
}
```

#### 用户登录
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "Password123!"
}

# 响应
{
  "success": true,
  "data": {
    "access_token": "jwt_token",
    "refresh_token": "refresh_token",
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "full_name": "张三",
      "role": "media_buyer"
    }
  }
}
```

#### 退出登录
```bash
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
```

### 2. 项目管理 (`/api/v1/projects`)

#### 获取项目列表
```bash
GET /api/v1/projects?page=1&page_size=20&status=active
Authorization: Bearer <access_token>

# 查询参数
- page: 页码（默认1）
- page_size: 每页数量（默认20，最大100）
- status: 项目状态过滤
- search: 搜索关键词
- manager_id: 项目经理ID过滤
```

#### 创建项目
```bash
POST /api/v1/projects
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "测试项目",
  "code": "TEST001",
  "description": "项目描述",
  "client_name": "测试客户",
  "client_email": "client@example.com",
  "pricing_model": "per_lead",
  "lead_price": 15.00,
  "setup_fee": 5000.00,
  "currency": "USD",
  "monthly_budget": 10000.00,
  "monthly_target_leads": 500
}
```

#### 更新项目
```bash
PUT /api/v1/projects/{project_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "更新后的项目名",
  "status": "active"
}
```

### 3. 渠道管理 (`/api/v1/channels`)

#### 获取渠道列表
```bash
GET /api/v1/channels?status=active
Authorization: Bearer <access_token>
```

#### 创建渠道
```bash
POST /api/v1/channels
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "优质渠道A",
  "code": "channel_a",
  "company_name": "优质广告有限公司",
  "contact_person": "张经理",
  "contact_email": "contact@channela.com",
  "contact_phone": "+86 13800138000",
  "service_fee_rate": 0.10,
  "account_setup_fee": 500.00,
  "minimum_topup": 1000.00
}
```

### 4. 广告账户 (`/api/v1/ad-accounts`)

#### 获取账户列表
```bash
GET /api/v1/ad-accounts?project_id={uuid}&status=active
Authorization: Bearer <access_token>
```

#### 创建账户
```bash
POST /api/v1/ad-accounts
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "account_id": "act_1234567890",
  "name": "Facebook账户A",
  "platform": "facebook",
  "project_id": "project_uuid",
  "channel_id": "channel_uuid",
  "assigned_user_id": "user_uuid",
  "daily_budget": 500.00,
  "total_budget": 15000.00,
  "currency": "USD"
}
```

### 5. 日报管理 (`/api/v1/daily-reports`)

#### 提交日报
```bash
POST /api/v1/daily-reports
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "ad_account_id": "account_uuid",
  "date": "2025-11-11",
  "leads_submitted": 100,
  "spend": 1500.00,
  "impressions": 50000,
  "clicks": 2500,
  "metadata": {
    "notes": "投放效果良好"
  }
}
```

#### 审核日报
```bash
PUT /api/v1/daily-reports/{report_id}/confirm
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "leads_confirmed": 95,
  "diff_reason": "5个无效线索"
}
```

### 6. 充值管理 (`/api/v1/topups`)

#### 申请充值
```bash
POST /api/v1/topups
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "ad_account_id": "account_uuid",
  "amount": 5000.00,
  "purpose": "常规充值",
  "urgency_level": "normal"
}
```

#### 审批充值（数据员）
```bash
PUT /api/v1/topups/{topup_id}/clerk-approve
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "approved": true,
  "notes": "审核通过"
}
```

#### 审批充值（财务）
```bash
PUT /api/v1/topups/{topup_id}/finance-approve
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "approved": true,
  "payment_method": "支付宝",
  "transaction_id": "txn_1234567890"
}
```

### 7. 财务对账 (`/api/v1/reconciliations`)

#### 创建对账
```bash
POST /api/v1/reconciliations
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "project_id": "project_uuid",
  "period_type": "monthly",
  "period_start": "2025-11-01",
  "period_end": "2025-11-30"
}
```

#### 获取对账列表
```bash
GET /api/v1/reconciliations?project_id={uuid}&period=monthly
Authorization: Bearer <access_token>
```

### 8. 报表 (`/api/v1/reports`)

#### 项目统计报表
```bash
GET /api/v1/reports/projects/{project_id}/stats
Authorization: Bearer <access_token>
Query Parameters:
- start_date: 开始日期
- end_date: 结束日期
- group_by: 分组方式（day/week/month）
```

#### 财务报表
```bash
GET /api/v1/reports/financial
Authorization: Bearer <access_token>
Query Parameters:
- period: 时期（monthly/quarterly）
- year: 年份
- month: 月份
```

---

## 📖 API文档生成

### OpenAPI配置

```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="AI广告代投系统 API",
    description="专为Facebook广告代理商设计的智能化管理平台",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    return get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

app.openapi = custom_openapi
```

### 文档注解示例

```python
from typing import List, Optional
from fastapi import Query, Path
from pydantic import BaseModel, Field

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="项目名称")
    code: str = Field(..., min_length=1, max_length=50, description="项目代码")
    description: Optional[str] = Field(None, description="项目描述")
    client_name: str = Field(..., description="客户名称")

    class Config:
        schema_extra = {
            "example": {
                "name": "测试项目",
                "code": "TEST001",
                "description": "这是一个测试项目",
                "client_name": "测试客户"
            }
        }

@router.post(
    "/projects",
    response_model=ProjectResponse,
    summary="创建项目",
    description="创建一个新的项目",
    tags=["项目管理"]
)
async def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建一个新项目

    - **name**: 项目名称，1-255个字符
    - **code**: 项目代码，1-50个字符，必须唯一
    - **client_name**: 客户名称

    需要项目管理权限才能创建项目。
    """
    pass
```

---

## 💻 开发示例

### 完整的Controller示例

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.deps import get_db, get_current_user
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.project_service import ProjectService
from app.core.response import success_response, error_response
from app.core.exceptions import ValidationError, NotFoundError

router = APIRouter(prefix="/api/v1/projects", tags=["项目管理"])

@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="项目状态过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取项目列表

    支持分页、状态过滤和搜索功能。
    """
    try:
        service = ProjectService(db)
        projects = service.list_projects(
            user=current_user,
            page=page,
            page_size=page_size,
            status=status,
            search=search
        )
        return success_response(data=projects)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建新项目

    需要项目管理权限。
    """
    try:
        service = ProjectService(db)
        project = service.create(project_data, current_user.id)
        return success_response(
            data=project,
            message="项目创建成功",
            code="PROJECT_CREATED"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=error_response(
                code="VALIDATION_ERROR",
                message=e.message
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str = Path(..., description="项目ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取项目详情
    """
    try:
        service = ProjectService(db)
        project = service.get_by_id(project_id, current_user)
        if not project:
            raise HTTPException(
                status_code=404,
                detail=error_response(
                    code="PROJECT_NOT_FOUND",
                    message="项目不存在"
                )
            )
        return success_response(data=project)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新项目信息
    """
    try:
        service = ProjectService(db)
        project = service.update(project_id, project_data, current_user)
        return success_response(
            data=project,
            message="项目更新成功"
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                code="PROJECT_NOT_FOUND",
                message=str(e)
            )
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=error_response(
                code="VALIDATION_ERROR",
                message=e.message
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除项目

    需要管理员权限。
    """
    try:
        service = ProjectService(db)
        service.delete(project_id, current_user)
        return success_response(
            message="项目删除成功",
            code="PROJECT_DELETED"
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                code="PROJECT_NOT_FOUND",
                message=str(e)
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Service层示例

```python
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.core.exceptions import ValidationError, NotFoundError

class ProjectService:
    def __init__(self, db: Session):
        self.db = db

    def list_projects(
        self,
        user: User,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Project]:
        query = self.db.query(Project)

        # 应用权限过滤
        if user.role != "admin":
            if user.role == "manager":
                query = query.filter(Project.manager_id == user.id)
            else:
                # 投手只能看到分配给自己的项目
                query = query.join(Project.accounts).filter(
                    Project.accounts.any(assigned_user_id=user.id)
                )

        # 状态过滤
        if status:
            query = query.filter(Project.status == status)

        # 搜索
        if search:
            query = query.filter(
                or_(
                    Project.name.ilike(f"%{search}%"),
                    Project.code.ilike(f"%{search}%"),
                    Project.client_name.ilike(f"%{search}%")
                )
            )

        # 分页
        offset = (page - 1) * page_size
        projects = query.offset(offset).limit(page_size).all()

        return projects

    def create(self, project_data: ProjectCreate, user_id: str) -> Project:
        # 检查代码唯一性
        existing = self.db.query(Project).filter(
            Project.code == project_data.code
        ).first()
        if existing:
            raise ValidationError("项目代码已存在", "code")

        project = Project(
            name=project_data.name,
            code=project_data.code,
            description=project_data.description,
            client_name=project_data.client_name,
            client_email=project_data.client_email,
            client_phone=project_data.client_phone,
            pricing_model=project_data.pricing_model,
            lead_price=project_data.lead_price,
            setup_fee=project_data.setup_fee,
            currency=project_data.currency,
            status="planning",
            created_by=user_id
        )

        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)

        return project

    def get_by_id(self, project_id: str, user: User) -> Project:
        project = self.db.query(Project).filter(Project.id == project_id).first()

        if not project:
            raise NotFoundError("项目不存在")

        # 权限检查
        if not self._can_access(project, user):
            raise NotFoundError("项目不存在")

        return project

    def update(self, project_id: str, project_data: ProjectUpdate, user: User) -> Project:
        project = self.get_by_id(project_id, user)

        update_data = project_data.dict(exclude_unset=True)

        for field, value in update_data.items():
            setattr(project, field, value)

        self.db.commit()
        self.db.refresh(project)

        return project

    def delete(self, project_id: str, user: User) -> None:
        project = self.get_by_id(project_id, user)

        if user.role != "admin":
            raise ValidationError("只有管理员可以删除项目")

        self.db.delete(project)
        self.db.commit()

    def _can_access(self, project: Project, user: User) -> bool:
        if user.role == "admin":
            return True

        if user.role == "manager" and project.manager_id == user.id:
            return True

        if user.role in ["data_clerk", "finance"]:
            return True

        if user.role == "media_buyer":
            # 检查是否有分配的账户
            return self.db.query(ProjectAccount).filter(
                ProjectAccount.project_id == project.id,
                ProjectAccount.assigned_user_id == user.id
            ).first() is not None

        return False
```

---

## 🧪 测试指南

### 单元测试示例

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.deps import get_db
from app.models.user import User
from app.schemas.project import ProjectCreate

client = TestClient(app)

class TestProjectAPI:
    def setup_method(self):
        # 创建测试用户
        self.user = User(
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="测试用户",
            role="admin"
        )
        self.db.add(self.user)
        self.db.commit()

        # 获取认证token
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123"
            }
        )
        self.token = response.json()["data"]["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_create_project_success(self):
        """测试成功创建项目"""
        project_data = {
            "name": "测试项目",
            "code": "TEST001",
            "client_name": "测试客户",
            "pricing_model": "per_lead",
            "lead_price": 15.00
        }

        response = client.post(
            "/api/v1/projects",
            json=project_data,
            headers=self.headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "测试项目"
        assert data["data"]["code"] == "TEST001"

    def test_create_project_duplicate_code(self):
        """测试重复的项目代码"""
        project_data = {
            "name": "测试项目",
            "code": "TEST001",
            "client_name": "测试客户"
        }

        # 第一次创建
        client.post("/api/v1/projects", json=project_data, headers=self.headers)

        # 第二次创建相同代码
        response = client.post(
            "/api/v1/projects",
            json=project_data,
            headers=self.headers
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_get_projects(self):
        """测试获取项目列表"""
        response = client.get("/api/v1/projects", headers=self.headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_unauthorized_access(self):
        """测试未授权访问"""
        response = client.get("/api/v1/projects")

        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "UNAUTHORIZED"

# 集成测试示例
@pytest.fixture
def test_db():
    # 创建测试数据库会话
    engine = create_test_engine()
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def client(test_db):
    def override_get_db():
        return test_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client

def test_project_workflow(client):
    """测试完整的项目工作流"""
    # 1. 登录
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@example.com",
            "password": "password123"
        }
    )
    token = login_response.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. 创建项目
    project_response = client.post(
        "/api/v1/projects",
        json={
            "name": "完整测试项目",
            "code": "FULL_TEST",
            "client_name": "测试客户公司"
        },
        headers=headers
    )
    assert project_response.status_code == 200
    project_id = project_response.json()["data"]["id"]

    # 3. 获取项目
    get_response = client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["data"]["name"] == "完整测试项目"

    # 4. 更新项目
    update_response = client.put(
        f"/api/v1/projects/{project_id}",
        json={"status": "active"},
        headers=headers
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["status"] == "active"

    # 5. 删除项目
    delete_response = client.delete(f"/api/v1/projects/{project_id}", headers=headers)
    assert delete_response.status_code == 200

    # 6. 验证删除
    verify_response = client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert verify_response.status_code == 404
```

### API测试脚本

```python
# scripts/test_api.py
import requests
import json

BASE_URL = "http://localhost:8000"

class APITester:
    def __init__(self):
        self.token = None
        self.headers = {}

    def login(self, email: str, password: str):
        """登录获取token"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            self.token = response.json()["data"]["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        return response

    def test_endpoint(self, method: str, endpoint: str, data=None):
        """测试API端点"""
        url = f"{BASE_URL}{endpoint}"

        if method.upper() == "GET":
            response = requests.get(url, headers=self.headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=self.headers)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=self.headers)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=self.headers)

        return response

# 使用示例
if __name__ == "__main__":
    tester = APITester()

    # 登录
    login_res = tester.login("admin@example.com", "password123")
    print(f"登录状态: {login_res.status_code}")

    # 测试创建项目
    project_data = {
        "name": "API测试项目",
        "code": "API_TEST",
        "client_name": "API测试客户"
    }
    create_res = tester.test_endpoint("POST", "/api/v1/projects", project_data)
    print(f"创建项目: {create_res.status_code}")
    print(f"响应内容: {create_res.json()}")
```

---

## 📋 附录

### API速率限制

| 端点类型 | 限制 |
|----------|------|
| 认证相关 | 10次/分钟 |
| 查询接口 | 100次/分钟 |
| 创建接口 | 50次/分钟 |
| 更新接口 | 50次/分钟 |
| 删除接口 | 20次/分钟 |

### 版本更新策略

- **主版本更新**: 不兼容的API变更
- **次版本更新**: 向后兼容的新功能
- **修订版本**: Bug修复

### 开发工具推荐

1. **Postman**: API测试工具
2. **Insomnia**: API客户端
3. **Swagger UI**: 交互式文档
4. **curl**: 命令行工具

---

**文档版本**: v1.0
**创建日期**: 2025-11-11
**最后更新**: 2025-11-11
**维护人**: 后端开发团队
**审核人**: 技术负责人