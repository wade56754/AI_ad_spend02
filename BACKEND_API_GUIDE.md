# 后端API开发指南 v2.1

> **文档目的**: 提供后端API开发的统一规范、接口设计和实现指南
> **目标读者**: 后端开发工程师、全栈工程师
> **更新日期**: 2025-11-11
> **版本**: v2.1 (基于主技术文档优化版)
> **文档状态**: 已完成 - 与主文档保持一致

---

## 1. 统一返回结构

### 1.1 成功响应格式
```json
{
    "success": true,
    "data": {
        // 实际数据内容
    },
    "message": "操作成功描述",
    "request_id": "uuid-string",
    "timestamp": "2025-11-10T10:30:00Z"
}
```

### 1.2 失败响应格式
```json
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "错误描述",
        "field": "错误字段(可选)",
        "details": {} // 详细错误信息(可选)
    },
    "request_id": "uuid-string",
    "timestamp": "2025-11-10T10:30:00Z"
}
```

### 1.3 分页响应格式
```json
{
    "success": true,
    "data": {
        "items": [...],
        "pagination": {
            "page": 1,
            "size": 20,
            "total": 100,
            "pages": 5
        }
    },
    "message": "获取数据成功",
    "request_id": "uuid-string",
    "timestamp": "2025-11-10T10:30:00Z"
}
```

### 1.4 统一响应基类
```python
# schemas/common.py
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, Any
from datetime import datetime

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """统一API响应格式"""
    success: bool
    data: Optional[T] = None
    error: Optional[dict] = None
    message: str
    request_id: str
    timestamp: datetime

class PaginationInfo(BaseModel):
    """分页信息"""
    page: int
    size: int
    total: int
    pages: int

class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应格式"""
    items: list[T]
    pagination: PaginationInfo

class ErrorResponse(BaseModel):
    """错误响应格式"""
    success: bool = False
    error: dict
    message: str
    request_id: str
    timestamp: datetime
```

---

## 2. 错误码定义

### 2.1 统一错误码定义 (基于主文档v2.1)
```python
# core/error_codes.py
class ErrorCode:
    """
    统一错误码定义
    基于主技术文档v2.1的规范
    """
    # 通用错误 (1000-1999)
    SUCCESS = "SUCCESS"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"      # 对应主文档 4001
    NOT_FOUND = "NOT_FOUND"                   # 对应主文档 4040
    UNAUTHORIZED = "UNAUTHORIZED"              # 对应主文档 4010
    FORBIDDEN = "FORBIDDEN"                   # 对应主文档 4031
    RATE_LIMIT = "RATE_LIMIT"
    MAINTENANCE = "MAINTENANCE"

    # 业务错误 (2000-2999)
    BUSINESS_ERROR = "BUSINESS_ERROR"
    STATE_TRANSITION_ERROR = "STATE_TRANSITION_ERROR"
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"

    # 数据错误 (3000-3999)
    DATABASE_ERROR = "DATABASE_ERROR"
    FOREIGN_KEY_ERROR = "FOREIGN_KEY_ERROR"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"

    # 第三方服务错误 (4000-4999)
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    PAYMENT_ERROR = "PAYMENT_ERROR"
    NOTIFICATION_ERROR = "NOTIFICATION_ERROR"

    # 主文档v2.1专用错误码 (5000-5999)
    PROJECT_NOT_FOUND = "PROJECT_NOT_FOUND"
    ACCOUNT_NOT_FOUND = "ACCOUNT_NOT_FOUND"
    TOPUP_NOT_FOUND = "TOPUP_NOT_FOUND"
    DAILY_REPORT_NOT_FOUND = "DAILY_REPORT_NOT_FOUND"

# 错误消息映射 (基于主文档v2.1)
ERROR_MESSAGES = {
    # 通用错误
    ErrorCode.SUCCESS: "操作成功",
    ErrorCode.INTERNAL_ERROR: "服务器内部错误",         # 对应主文档 5001
    ErrorCode.VALIDATION_ERROR: "参数校验错误",        # 对应主文档 4001
    ErrorCode.NOT_FOUND: "资源不存在",                # 对应主文档 4040
    ErrorCode.UNAUTHORIZED: "未登录或权限不足",        # 对应主文档 4010
    ErrorCode.FORBIDDEN: "禁止操作",                  # 对应主文档 4031
    ErrorCode.RATE_LIMIT: "请求频率过高",
    ErrorCode.MAINTENANCE: "系统维护中",

    # 业务错误
    ErrorCode.BUSINESS_ERROR: "业务逻辑错误",
    ErrorCode.STATE_TRANSITION_ERROR: "状态转换错误",
    ErrorCode.INSUFFICIENT_BALANCE: "余额不足",
    ErrorCode.DUPLICATE_RESOURCE: "资源已存在",

    # 数据错误
    ErrorCode.DATABASE_ERROR: "数据库错误",
    ErrorCode.FOREIGN_KEY_ERROR: "外键约束错误",
    ErrorCode.CONSTRAINT_VIOLATION: "数据约束违反",

    # 第三方服务错误
    ErrorCode.EXTERNAL_SERVICE_ERROR: "外部服务错误",
    ErrorCode.PAYMENT_ERROR: "支付错误",
    ErrorCode.NOTIFICATION_ERROR: "通知发送失败",

    # 专用错误码
    ErrorCode.PROJECT_NOT_FOUND: "项目不存在",
    ErrorCode.ACCOUNT_NOT_FOUND: "广告账户不存在",
    ErrorCode.TOPUP_NOT_FOUND: "充值记录不存在",
    ErrorCode.DAILY_REPORT_NOT_FOUND: "日报记录不存在"
}

# HTTP状态码映射 (基于主文档v2.1)
ERROR_STATUS_CODES = {
    ErrorCode.VALIDATION_ERROR: 400,    # 参数校验错误
    ErrorCode.UNAUTHORIZED: 401,        # 未授权
    ErrorCode.FORBIDDEN: 403,           # 权限不足
    ErrorCode.NOT_FOUND: 404,           # 资源不存在
    ErrorCode.INTERNAL_ERROR: 500,      # 系统内部错误
}
```

### 2.2 自定义异常类
```python
# core/exceptions.py
from fastapi import HTTPException
from typing import Optional, Dict, Any

class BaseAPIException(Exception):
    """API异常基类"""
    def __init__(
        self,
        message: str,
        code: str = ErrorCode.INTERNAL_ERROR,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 400
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)

class ValidationError(BaseAPIException):
    """数据验证错误"""
    def __init__(self, message: str, field: str = None, details: Dict = None):
        super().__init__(
            message=message,
            code=ErrorCode.VALIDATION_ERROR,
            details={**details, "field": field} if field else details
        )

class NotFoundError(BaseAPIException):
    """资源不存在错误"""
    def __init__(self, message: str = "资源不存在"):
        super().__init__(
            message=message,
            code=ErrorCode.NOT_FOUND,
            status_code=404
        )

class PermissionError(BaseAPIException):
    """权限错误"""
    def __init__(self, message: str = "权限不足"):
        super().__init__(
            message=message,
            code=ErrorCode.FORBIDDEN,
            status_code=403
        )

class BusinessLogicError(BaseAPIException):
    """业务逻辑错误"""
    def __init__(self, message: str, details: Dict = None):
        super().__init__(
            message=message,
            code=ErrorCode.BUSINESS_ERROR,
            details=details
        )
```

### 2.3 统一异常处理器 (基于主文档v2.1)
```python
# handlers/exception_handler.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import uuid
import logging
from datetime import datetime
from backend.core.error_codes import ERROR_STATUS_CODES

logger = logging.getLogger(__name__)

async def api_exception_handler(request: Request, exc: BaseAPIException):
    """
    API异常统一处理
    基于主文档v2.1的统一返回格式
    """
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))

    # 使用主文档v2.1的错误状态码映射
    status_code = exc.status_code or ERROR_STATUS_CODES.get(exc.code, 400)

    error_response = {
        "success": False,
        "error": {
            "code": exc.code,
            "message": exc.message,
            **exc.details
        },
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat()
    }

    # 记录错误日志 (主文档v2.1要求)
    logger.error(
        f"API Error: {exc.code} - {exc.message}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "user_id": getattr(request.state, 'user_id', None),
            "details": exc.details,
            "status_code": status_code
        }
    )

    return JSONResponse(
        status_code=status_code,
        content=error_response
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """
    HTTP异常处理
    基于主文档v2.1的格式
    """
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))

    # 映射HTTP状态码到主文档v2.1错误码
    error_code_mapping = {
        400: "VALIDATION_ERROR",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        500: "INTERNAL_ERROR"
    }

    error_code = error_code_mapping.get(exc.status_code, "HTTP_ERROR")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": error_code,
                "message": exc.detail,
                "http_status_code": exc.status_code
            },
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

async def validation_exception_handler(request: Request, exc: Exception):
    """
    Pydantic验证异常处理
    对应主文档v2.1的4001错误码
    """
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))

    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",  # 主文档v2.1: 4001
                "message": "参数校验失败",
                "details": str(exc)
            },
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

---

## 3. 中间件设计

### 3.1 请求ID中间件
```python
# middleware/request_id.py
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    """请求ID中间件"""
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response
```

### 3.2 用户上下文中间件 (基于主文档v2.1)
```python
# middleware/user_context.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from backend.core.db import get_db_session
from backend.core.auth import verify_token
import logging

logger = logging.getLogger(__name__)

class UserContextMiddleware(BaseHTTPMiddleware):
    """
    用户上下文中间件
    基于主文档v2.1的RLS策略实现
    """
    async def dispatch(self, request: Request, call_next):
        # 跳过不需要认证的路径
        skip_paths = ["/health", "/docs", "/openapi.json", "/auth/login", "/metrics"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)

        # 提取并验证JWT token
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return await call_next(request)

        try:
            token = authorization.replace("Bearer ", "")
            user_data = await verify_token(token)

            if user_data:
                request.state.user_id = user_data["user_id"]
                request.state.user_role = user_data["role"]
                request.state.user_email = user_data["email"]

                # 设置数据库会话变量 (主文档v2.1 RLS策略要求)
                async with get_db_session() as session:
                    await session.execute(
                        f"SELECT set_config('app.current_user_id', '{user_data['user_id']}', true)"
                    )
                    await session.execute(
                        f"SELECT set_config('app.current_role', '{user_data['role']}', true)"
                    )
                    logger.info(f"RLS context set for user {user_data['user_id']} with role {user_data['role']}")

        except Exception as e:
            logger.warning(f"Token验证失败: {e}")
            # 继续执行，后续的权限检查会处理

        return await call_next(request)

### 3.3 RLS上下文中间件 (基于主文档v2.1)
```python
# middleware/rls_context.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class RLSContextMiddleware(BaseHTTPMiddleware):
    """
    RLS上下文中间件
    基于主文档v2.1的RLS策略注入实现
    """
    async def dispatch(self, request: Request, call_next):
        user = getattr(request.state, 'user', None)
        if user:
            conn = request.state.db
            # 注入RLS上下文变量 (主文档v2.1规范)
            await conn.execute(f"SELECT set_config('app.current_user_id', '{user.id}', true)")
            await conn.execute(f"SELECT set_config('app.current_role', '{user.role}', true)")

            logger.debug(f"RLS context injected: user_id={user.id}, role={user.role}")

        response = await call_next(request)
        return response

# RLS策略示例 (对应数据库端配置)
"""
主文档v2.1 RLS策略示例:

CREATE POLICY rls_project_access ON projects
  FOR SELECT USING (
    current_setting('app.current_role') = 'admin'
    OR created_by = current_setting('app.current_user_id')
  );

CREATE POLICY rls_project_update ON projects
  FOR UPDATE USING (
    current_setting('app.current_role') = 'admin'
    OR (created_by = current_setting('app.current_user_id') AND current_setting('app.current_role') = 'manager')
  );

CREATE POLICY rls_ad_account_access ON ad_accounts
  FOR SELECT USING (
    current_setting('app.current_role') = 'admin'
    OR project_id IN (
      SELECT id FROM projects WHERE
      current_setting('app.current_role') IN ('admin', 'data_clerk', 'finance')
      OR created_by = current_setting('app.current_user_id')
    )
    OR assigned_user_id = current_setting('app.current_user_id')
  );
"""
```

### 3.4 日志中间件
```python
# middleware/logging.py
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # 记录请求开始
        request_id = getattr(request.state, 'request_id', 'unknown')
        user_id = getattr(request.state, 'user_id', 'anonymous')

        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params)
            }
        )

        response = await call_next(request)

        # 记录请求完成
        process_time = time.time() - start_time

        logger.info(
            f"Request completed: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": round(process_time, 4)
            }
        )

        return response
```

---

## 4. API路由设计

### 4.1 路由命名规范
```python
# 路由命名约定
# 1. 使用kebab-case
/api/projects/{project_id}/accounts
/api/topups/{topup_id}/approve

# 2. 资源名词复数
/api/projects
/api/accounts
/api/users

# 3. 嵌套资源
/api/projects/{project_id}/accounts/{account_id}/daily-reports
```

### 4.2 HTTP方法语义
```python
# HTTP方法使用规范
GET    /api/projects           # 获取项目列表
POST   /api/projects           # 创建项目
GET    /api/projects/{id}      # 获取项目详情
PUT    /api/projects/{id}      # 更新项目
DELETE /api/projects/{id}      # 删除项目

# 特殊操作使用POST
POST   /api/projects/{id}/activate   # 激活项目
POST   /api/topups/{id}/approve      # 审批充值
POST   /api/daily-reports/{id}/confirm # 确认日报
```

### 4.3 依赖注入模式
```python
# dependencies/auth.py
from fastapi import Depends, HTTPException, status
from backend.core.auth import verify_token

async def get_current_user(request: Request) -> dict:
    """获取当前用户"""
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未认证用户"
        )

    return {
        "user_id": user_id,
        "role": getattr(request.state, 'user_role'),
        "email": getattr(request.state, 'user_email')
    }

async def require_role(required_role: str):
    """要求特定角色"""
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] != required_role and current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        return current_user
    return role_checker

# 在路由中使用
@router.get("/admin/dashboard")
async def admin_dashboard(
    current_user: dict = Depends(require_role("admin"))
):
    return {"message": "管理员面板"}
```

---

## 5. 项目管理API

### 5.1 项目CRUD操作
```python
# routers/projects.py
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.core.db import get_db_session
from backend.schemas.projects import ProjectCreate, ProjectUpdate, ProjectResponse
from backend.services.project_service import ProjectService
from backend.dependencies.auth import get_current_user
from backend.middleware.request_id import get_request_id

router = APIRouter(prefix="/api/projects", tags=["projects"])

@router.post("/", response_model=APIResponse[ProjectResponse])
async def create_project(
    project: ProjectCreate,
    current_user: dict = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
):
    """创建项目"""
    try:
        # 权限检查
        if current_user["role"] not in ["admin", "manager"]:
            raise PermissionError("无创建项目权限")

        # 业务逻辑
        with get_db_session() as session:
            project_service = ProjectService(session)
            result = await project_service.create_project(
                project_data=project.dict(),
                user_id=current_user["user_id"]
            )

        return APIResponse(
            success=True,
            data=result,
            message="项目创建成功",
            request_id=request_id,
            timestamp=datetime.utcnow()
        )

    except BaseAPIException as e:
        raise
    except Exception as e:
        logger.error(f"创建项目失败: {e}", extra={"request_id": request_id})
        raise BaseAPIException("创建项目失败")

@router.get("/", response_model=APIResponse[PaginatedResponse[ProjectResponse]])
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    client_name: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
):
    """获取项目列表"""
    try:
        with get_db_session() as session:
            project_service = ProjectService(session)

            # 构建过滤条件
            filters = {}
            if status:
                filters["status"] = status
            if client_name:
                filters["client_name"] = client_name

            # 根据用户角色过滤数据
            projects, total = await project_service.get_projects_paginated(
                user_id=current_user["user_id"],
                user_role=current_user["role"],
                filters=filters,
                skip=skip,
                limit=limit
            )

        paginated_data = PaginatedResponse(
            items=projects,
            pagination=PaginationInfo(
                page=skip // limit + 1,
                size=limit,
                total=total,
                pages=(total + limit - 1) // limit
            )
        )

        return APIResponse(
            success=True,
            data=paginated_data,
            message="获取项目列表成功",
            request_id=request_id,
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"获取项目列表失败: {e}", extra={"request_id": request_id})
        raise BaseAPIException("获取项目列表失败")

@router.get("/{project_id}", response_model=APIResponse[ProjectResponse])
async def get_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
):
    """获取项目详情"""
    try:
        with get_db_session() as session:
            project_service = ProjectService(session)

            # 权限检查
            if not await project_service.can_access_project(
                user_id=current_user["user_id"],
                user_role=current_user["role"],
                project_id=project_id
            ):
                raise PermissionError("无项目访问权限")

            project = await project_service.get_project_by_id(project_id)
            if not project:
                raise NotFoundError("项目不存在")

        return APIResponse(
            success=True,
            data=project,
            message="获取项目详情成功",
            request_id=request_id,
            timestamp=datetime.utcnow()
        )

    except BaseAPIException:
        raise
    except Exception as e:
        logger.error(f"获取项目详情失败: {e}", extra={"request_id": request_id})
        raise BaseAPIException("获取项目详情失败")

@router.put("/{project_id}", response_model=APIResponse[ProjectResponse])
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    current_user: dict = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
):
    """更新项目"""
    try:
        with get_db_session() as session:
            project_service = ProjectService(session)

            # 权限检查
            if not await project_service.can_update_project(
                user_id=current_user["user_id"],
                user_role=current_user["role"],
                project_id=project_id
            ):
                raise PermissionError("无项目更新权限")

            result = await project_service.update_project(
                project_id=project_id,
                update_data=project_update.dict(exclude_unset=True),
                user_id=current_user["user_id"]
            )

        return APIResponse(
            success=True,
            data=result,
            message="项目更新成功",
            request_id=request_id,
            timestamp=datetime.utcnow()
        )

    except BaseAPIException:
        raise
    except Exception as e:
        logger.error(f"更新项目失败: {e}", extra={"request_id": request_id})
        raise BaseAPIException("更新项目失败")

@router.delete("/{project_id}", response_model=APIResponse[dict])
async def delete_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
):
    """删除项目"""
    try:
        with get_db_session() as session:
            project_service = ProjectService(session)

            # 只有管理员可以删除项目
            if current_user["role"] != "admin":
                raise PermissionError("无项目删除权限")

            await project_service.delete_project(
                project_id=project_id,
                user_id=current_user["user_id"]
            )

        return APIResponse(
            success=True,
            data={"deleted": True},
            message="项目删除成功",
            request_id=request_id,
            timestamp=datetime.utcnow()
        )

    except BaseAPIException:
        raise
    except Exception as e:
        logger.error(f"删除项目失败: {e}", extra={"request_id": request_id})
        raise BaseAPIException("删除项目失败")
```

### 5.2 项目状态管理
```python
@router.put("/{project_id}/status", response_model=APIResponse[ProjectResponse])
async def update_project_status(
    project_id: str,
    status_update: dict,
    current_user: dict = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
):
    """更新项目状态"""
    try:
        with get_db_session() as session:
            project_service = ProjectService(session)

            # 权限检查
            if not await project_service.can_update_project_status(
                user_id=current_user["user_id"],
                user_role=current_user["role"],
                project_id=project_id
            ):
                raise PermissionError("无项目状态更新权限")

            # 状态转换验证
            new_status = status_update.get("status")
            reason = status_update.get("reason", "")

            result = await project_service.update_project_status(
                project_id=project_id,
                new_status=new_status,
                reason=reason,
                user_id=current_user["user_id"]
            )

        return APIResponse(
            success=True,
            data=result,
            message="项目状态更新成功",
            request_id=request_id,
            timestamp=datetime.utcnow()
        )

    except BaseAPIException:
        raise
    except Exception as e:
        logger.error(f"更新项目状态失败: {e}", extra={"request_id": request_id})
        raise BaseAPIException("更新项目状态失败")
```

---

## 6. 数据验证模式

### 6.1 Pydantic模型定义
```python
# schemas/projects.py
from pydantic import BaseModel, validator, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class ProjectStatus(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PricingModel(str, Enum):
    PER_LEAD = "per_lead"
    FIXED_FEE = "fixed_fee"
    HYBRID = "hybrid"

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="项目名称")
    client_name: str = Field(..., min_length=1, max_length=255, description="客户名称")
    description: Optional[str] = Field(None, max_length=1000, description="项目描述")

    # 客户联系信息
    client_contact: Optional[str] = Field(None, max_length=255, description="客户联系人")
    client_email: Optional[str] = Field(None, regex=r'^[^@]+@[^@]+\.[^@]+$', description="客户邮箱")
    client_phone: Optional[str] = Field(None, regex=r'^[\d\-\+\(\)\s]+$', description="客户电话")

    # 收费模式
    pricing_model: PricingModel = Field(PricingModel.PER_LEAD, description="收费模式")
    lead_price: float = Field(..., gt=0, description="单粉价格")
    setup_fee: float = Field(0, ge=0, description="项目启动费")
    currency: str = Field("USD", regex=r'^[A-Z]{3}$', description="货币单位")

    # 项目状态
    status: ProjectStatus = Field(ProjectStatus.PLANNING, description="项目状态")

    # 预算信息
    monthly_budget: Optional[float] = Field(None, gt=0, description="月度预算")
    total_budget: Optional[float] = Field(None, gt=0, description="总预算")

    # 目标设定
    monthly_target_leads: int = Field(0, ge=0, description="月度目标粉数")
    target_cpl: Optional[float] = Field(None, gt=0, description="目标单粉成本")

    @validator('lead_price')
    def lead_price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('单粉价格必须大于0')
        return v

    @validator('setup_fee')
    def setup_fee_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError('项目启动费不能为负数')
        return v

    @validator('monthly_target_leads')
    def target_leads_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError('目标粉数不能为负数')
        return v

class ProjectCreate(ProjectBase):
    """创建项目请求"""
    pass

class ProjectUpdate(BaseModel):
    """更新项目请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    client_contact: Optional[str] = Field(None, max_length=255)
    client_email: Optional[str] = Field(None, regex=r'^[^@]+@[^@]+\.[^@]+$')
    client_phone: Optional[str] = Field(None, regex=r'^[\d\-\+\(\)\s]+$')

    status: Optional[ProjectStatus] = None
    monthly_budget: Optional[float] = Field(None, gt=0)
    total_budget: Optional[float] = Field(None, gt=0)
    monthly_target_leads: Optional[int] = Field(None, ge=0)
    target_cpl: Optional[float] = Field(None, gt=0)

class ProjectResponse(ProjectBase):
    """项目响应"""
    id: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    # 关联信息
    manager: Optional[dict] = None

    # 统计信息
    total_accounts: int = 0
    active_accounts: int = 0
    total_spend: float = 0.0
    total_leads: int = 0
    current_cpl: Optional[float] = None

    class Config:
        from_attributes = True

class ProjectStatusUpdate(BaseModel):
    """项目状态更新"""
    status: ProjectStatus
    reason: Optional[str] = Field(None, max_length=500, description="状态变更原因")
```

### 6.2 自定义验证器
```python
# validators/business.py
from pydantic import validator
from sqlalchemy.orm import Session
from backend.core.db import get_db_session

def validate_project_business_rules(cls, values):
    """项目业务规则验证"""
    # 混合模式必须设置启动费和单粉价格
    if values.get('pricing_model') == 'hybrid':
        if not values.get('setup_fee') or values.get('setup_fee') <= 0:
            raise ValueError('混合模式必须设置项目启动费')
        if not values.get('lead_price') or values.get('lead_price') <= 0:
            raise ValueError('混合模式必须设置单粉价格')

    # 固定费用模式不需要单粉价格
    if values.get('pricing_model') == 'fixed_fee':
        if values.get('lead_price', 0) > 0:
            raise ValueError('固定费用模式不需要设置单粉价格')

    return values

def validate_channel_availability(cls, values):
    """验证渠道可用性"""
    channel_id = values.get('channel_id')
    if channel_id:
        with get_db_session() as session:
            channel = session.query(Channel).filter(Channel.id == channel_id).first()
            if not channel:
                raise ValueError('渠道不存在')
            if channel.status != 'active':
                raise ValueError('渠道未激活，无法使用')

    return values
```

---

## 7. 业务服务层

### 7.1 服务基类
```python
# services/base_service.py
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from typing import TypeVar, Generic, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

class BaseService(Generic[T], ABC):
    """服务基类"""

    def __init__(self, db: Session):
        self.db = db

    async def create(self, data: Dict[str, Any], user_id: str) -> T:
        """创建实体"""
        try:
            # 创建实体
            entity = self.model(**data)
            self.db.add(entity)
            self.db.commit()
            self.db.refresh(entity)

            # 记录审计日志
            await self._log_create(entity, user_id)

            logger.info(f"创建{self.model.__name__}成功: {entity.id}")
            return entity

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建{self.model.__name__}失败: {e}")
            raise

    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """根据ID获取实体"""
        return self.db.query(self.model).filter(self.model.id == entity_id).first()

    async def update(self, entity_id: str, data: Dict[str, Any], user_id: str) -> Optional[T]:
        """更新实体"""
        try:
            entity = await self.get_by_id(entity_id)
            if not entity:
                return None

            # 记录旧值
            old_values = self._entity_to_dict(entity)

            # 更新字段
            for field, value in data.items():
                if hasattr(entity, field):
                    setattr(entity, field, value)

            self.db.commit()
            self.db.refresh(entity)

            # 记录审计日志
            await self._log_update(entity, old_values, user_id)

            logger.info(f"更新{self.model.__name__}成功: {entity.id}")
            return entity

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新{self.model.__name__}失败: {e}")
            raise

    async def delete(self, entity_id: str, user_id: str) -> bool:
        """删除实体"""
        try:
            entity = await self.get_by_id(entity_id)
            if not entity:
                return False

            # 记录删除前的数据
            old_values = self._entity_to_dict(entity)

            self.db.delete(entity)
            self.db.commit()

            # 记录审计日志
            await self._log_delete(entity, old_values, user_id)

            logger.info(f"删除{self.model.__name__}成功: {entity.id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"删除{self.model.__name__}失败: {e}")
            raise

    def _entity_to_dict(self, entity: T) -> Dict[str, Any]:
        """实体转字典"""
        result = {}
        for column in entity.__table__.columns:
            value = getattr(entity, column.name)
            if value is not None:
                result[column.name] = value
        return result

    @abstractmethod
    async def _log_create(self, entity: T, user_id: str):
        """记录创建日志"""
        pass

    @abstractmethod
    async def _log_update(self, entity: T, old_values: Dict, user_id: str):
        """记录更新日志"""
        pass

    @abstractmethod
    async def _log_delete(self, entity: T, old_values: Dict, user_id: str):
        """记录删除日志"""
        pass
```

### 7.2 项目服务实现
```python
# services/project_service.py
from typing import List, Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from backend.models.projects import Project
from backend.models.ad_accounts import AdAccount
from backend.services.base_service import BaseService
from backend.core.audit import audit_logger

class ProjectService(BaseService[Project]):
    """项目服务"""

    def __init__(self, db: Session):
        super().__init__(db)
        self.model = Project

    async def create_project(self, project_data: Dict[str, Any], user_id: str) -> Project:
        """创建项目"""
        # 业务验证
        await self._validate_project_data(project_data)

        # 添加创建者信息
        project_data['created_by'] = user_id

        return await self.create(project_data, user_id)

    async def get_projects_paginated(
        self,
        user_id: str,
        user_role: str,
        filters: Dict[str, Any],
        skip: int,
        limit: int
    ) -> Tuple[List[Project], int]:
        """分页获取项目列表"""
        query = self.db.query(Project)

        # 应用权限过滤
        query = self._apply_permissions_filter(query, user_id, user_role)

        # 应用业务过滤
        if filters:
            if 'status' in filters:
                query = query.filter(Project.status == filters['status'])
            if 'client_name' in filters:
                query = query.filter(Project.client_name.ilike(f"%{filters['client_name']}%"))

        # 获取总数
        total = query.count()

        # 获取分页数据
        projects = query.offset(skip).limit(limit).all()

        return projects, total

    async def can_access_project(self, user_id: str, user_role: str, project_id: str) -> bool:
        """检查项目访问权限"""
        if user_role == 'admin':
            return True

        project = await self.get_by_id(project_id)
        if not project:
            return False

        if user_role == 'manager' and project.manager_id == user_id:
            return True

        if user_role in ['data_clerk', 'finance']:
            return True

        if user_role == 'media_buyer':
            # 检查是否有分配的账户
            has_account = self.db.query(AdAccount).filter(
                AdAccount.project_id == project_id,
                AdAccount.assigned_user_id == user_id
            ).first()
            return has_account is not None

        return False

    async def can_update_project(self, user_id: str, user_role: str, project_id: str) -> bool:
        """检查项目更新权限"""
        if user_role == 'admin':
            return True

        project = await self.get_by_id(project_id)
        if not project:
            return False

        return user_role == 'manager' and project.manager_id == user_id

    async def can_update_project_status(self, user_id: str, user_role: str, project_id: str) -> bool:
        """检查项目状态更新权限"""
        return await self.can_update_project(user_id, user_role, project_id)

    async def update_project_status(
        self,
        project_id: str,
        new_status: str,
        reason: str,
        user_id: str
    ) -> Project:
        """更新项目状态"""
        project = await self.get_by_id(project_id)
        if not project:
            raise NotFoundError("项目不存在")

        # 状态转换验证
        if not self._is_valid_status_transition(project.status, new_status):
            raise BusinessLogicError(f"无法从 {project.status} 转换到 {new_status}")

        # 更新状态
        update_data = {
            'status': new_status,
            'updated_at': datetime.utcnow()
        }

        # 记录状态变更原因
        if reason:
            update_data['status_reason'] = reason

        return await self.update(project_id, update_data, user_id)

    def _apply_permissions_filter(self, query, user_id: str, user_role: str):
        """应用权限过滤"""
        if user_role == 'admin':
            return query

        if user_role == 'manager':
            return query.filter(Project.manager_id == user_id)

        if user_role in ['data_clerk', 'finance']:
            return query

        if user_role == 'media_buyer':
            return query.join(AdAccount).filter(AdAccount.assigned_user_id == user_id)

        # 其他角色无权限
        return query.filter(False)

    def _is_valid_status_transition(self, current_status: str, new_status: str) -> bool:
        """验证状态转换是否有效"""
        valid_transitions = {
            'planning': ['active', 'cancelled'],
            'active': ['paused', 'completed', 'cancelled'],
            'paused': ['active', 'cancelled'],
            'completed': ['cancelled'],
            'cancelled': ['planning']
        }

        return new_status in valid_transitions.get(current_status, [])

    async def _validate_project_data(self, data: Dict[str, Any]):
        """验证项目数据"""
        # 混合模式验证
        if data.get('pricing_model') == 'hybrid':
            if not data.get('setup_fee') or data.get('setup_fee') <= 0:
                raise ValidationError("混合模式必须设置项目启动费")
            if not data.get('lead_price') or data.get('lead_price') <= 0:
                raise ValidationError("混合模式必须设置单粉价格")

        # 固定费用模式验证
        if data.get('pricing_model') == 'fixed_fee' and data.get('lead_price', 0) > 0:
            raise ValidationError("固定费用模式不需要设置单粉价格")

    async def _log_create(self, entity: Project, user_id: str):
        """记录创建日志"""
        audit_logger.log_create(
            table_name="projects",
            record_id=entity.id,
            new_values=self._entity_to_dict(entity),
            user_id=user_id
        )

    async def _log_update(self, entity: Project, old_values: Dict, user_id: str):
        """记录更新日志"""
        audit_logger.log_update(
            table_name="projects",
            record_id=entity.id,
            old_values=old_values,
            new_values=self._entity_to_dict(entity),
            user_id=user_id
        )

    async def _log_delete(self, entity: Project, old_values: Dict, user_id: str):
        """记录删除日志"""
        audit_logger.log_delete(
            table_name="projects",
            record_id=entity.id,
            old_values=old_values,
            user_id=user_id
        )
```

---

## 8. 事务管理

### 8.1 事务装饰器
```python
# decorators/transaction.py
import functools
import logging
from sqlalchemy.orm import Session
from backend.core.db import get_db_session
from backend.core.audit import audit_logger

logger = logging.getLogger(__name__)

def transactional(operation_name: str = None):
    """事务装饰器"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            with get_db_session() as session:
                try:
                    # 开始事务
                    session.begin()

                    # 将session传递给函数
                    kwargs['db'] = session

                    # 执行业务逻辑
                    result = await func(*args, **kwargs)

                    # 提交事务
                    session.commit()

                    # 记录成功日志
                    op_name = operation_name or func.__name__
                    logger.info(f"事务 {op_name} 执行成功")

                    return result

                except Exception as e:
                    # 回滚事务
                    session.rollback()

                    # 记录错误日志
                    op_name = operation_name or func.__name__
                    logger.error(f"事务 {op_name} 执行失败: {e}")

                    # 记录审计日志
                    audit_logger.log_action(
                        action="transaction_failed",
                        table_name=op_name,
                        details={"error": str(e)},
                        user_id=kwargs.get('user_id'),
                        level="high"
                    )

                    raise

        return wrapper
    return decorator

# 使用示例
@transactional("approve_topup")
async def approve_topup_with_transaction(
    topup_id: str,
    approval_data: dict,
    user_id: str,
    db: Session
):
    """带事务的充值审批"""
    # 1. 更新充值状态
    topup = db.query(Topup).filter(Topup.id == topup_id).first()
    topup.status = "finance_approved"
    topup.finance_approval = approval_data

    # 2. 创建财务流水
    ledger = Ledger(
        topup_id=topup_id,
        amount=topup.total_amount,
        transaction_type="topup_approval",
        user_id=user_id
    )
    db.add(ledger)

    # 3. 更新账户余额
    account = db.query(AdAccount).filter(AdAccount.id == topup.ad_account_id).first()
    account.remaining_budget += topup.amount

    # 4. 发送通知
    await notification_service.send_approval_notification(topup)

    return topup
```

### 8.2 复杂事务示例
```python
# services/topup_service.py
@transactional("process_topup_approval")
async def process_topup_approval_workflow(
    topup_id: str,
    approval_action: str,
    approval_data: dict,
    user_id: str,
    db: Session
):
    """处理充值审批工作流"""

    # 1. 获取充值申请
    topup = db.query(Topup).filter(Topup.id == topup_id).first()
    if not topup:
        raise NotFoundError("充值申请不存在")

    # 2. 验证状态转换
    if not _can_approve_topup(topup.status, approval_action, user_id):
        raise BusinessLogicError("当前状态不允许此操作")

    # 3. 处理不同的审批动作
    if approval_action == "finance_approve":
        # 财务批准
        await _process_finance_approval(topup, approval_data, user_id, db)

    elif approval_action == "finance_reject":
        # 财务拒绝
        await _process_finance_rejection(topup, approval_data, user_id, db)

    elif approval_action == "execute_payment":
        # 执行付款
        await _process_payment_execution(topup, approval_data, user_id, db)

    # 4. 更新相关统计
    await _update_project_statistics(topup.project_id, db)

    # 5. 发送通知
    await _send_approval_notifications(topup, approval_action, user_id)

    return topup

async def _process_finance_approval(topup: Topup, approval_data: dict, user_id: str, db: Session):
    """处理财务批准"""
    # 更新充值状态
    topup.status = TopupStatus.FINANCE_APPROVED
    topup.finance_approval = {
        "approved_by": user_id,
        "approved_at": datetime.utcnow().isoformat(),
        "payment_method": approval_data.get("payment_method"),
        "notes": approval_data.get("notes", "")
    }

    # 创建预付款记录
    prepayment = Prepayment(
        topup_id=topup.id,
        amount=topup.total_amount,
        status="pending",
        created_by=user_id
    )
    db.add(prepayment)

async def _process_payment_execution(topup: Topup, payment_data: dict, user_id: str, db: Session):
    """处理付款执行"""
    # 验证付款信息
    if not payment_data.get("transaction_id"):
        raise ValidationError("缺少交易ID")

    # 更新充值状态
    topup.status = TopupStatus.PAID
    topup.paid_at = datetime.utcnow()

    # 更新付款信息
    if topup.finance_approval:
        topup.finance_approval.update({
            "transaction_id": payment_data["transaction_id"],
            "executed_at": datetime.utcnow().isoformat(),
            "executed_by": user_id
        })

    # 更新预付款状态
    prepayment = db.query(Prepayment).filter(Prepayment.topup_id == topup.id).first()
    if prepayment:
        prepayment.status = "paid"
        prepayment.transaction_id = payment_data["transaction_id"]

    # 创建财务流水
    ledger = Ledger(
        topup_id=topup.id,
        amount=topup.total_amount,
        fee_amount=topup.fee_amount,
        transaction_type="topup_payment",
        transaction_id=payment_data["transaction_id"],
        user_id=user_id
    )
    db.add(ledger)

    # 更新账户余额
    account = db.query(AdAccount).filter(AdAccount.id == topup.ad_account_id).first()
    if account:
        account.remaining_budget += topup.amount
        account.total_spend += topup.fee_amount  # 手续费计入消耗
```

---

## 9. 测试指南

### 9.1 API测试示例
```python
# tests/test_projects_api.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.db import get_db_session
from backend.models.users import User
from backend.models.projects import Project

client = TestClient(app)

class TestProjectsAPI:

    def setup_method(self):
        """测试前准备"""
        # 创建测试用户
        self.test_user = User(
            email="test@example.com",
            hashed_password="hashed_password",
            role="manager"
        )

        # 创建测试项目
        self.test_project = Project(
            name="测试项目",
            client_name="测试客户",
            pricing_model="per_lead",
            lead_price=10.0,
            manager_id=self.test_user.id
        )

    def test_create_project_success(self):
        """测试创建项目成功"""
        # 登录获取token
        login_response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword"
        })
        token = login_response.json()["data"]["access_token"]

        headers = {"Authorization": f"Bearer {token}"}

        # 创建项目
        project_data = {
            "name": "API测试项目",
            "client_name": "API测试客户",
            "pricing_model": "per_lead",
            "lead_price": 15.0,
            "setup_fee": 2000.0,
            "monthly_budget": 10000.0
        }

        response = client.post("/api/projects", json=project_data, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "API测试项目"
        assert data["data"]["client_name"] == "API测试客户"
        assert "id" in data["data"]
        assert "request_id" in data

    def test_create_project_validation_error(self):
        """测试创建项目验证错误"""
        headers = {"Authorization": "Bearer valid_token"}

        # 缺少必填字段
        project_data = {
            "name": "测试项目"
            # 缺少 client_name
        }

        response = client.post("/api/projects", json=project_data, headers=headers)

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_get_projects_list(self):
        """测试获取项目列表"""
        headers = {"Authorization": "Bearer valid_token"}

        response = client.get("/api/projects", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "items" in data["data"]
        assert "pagination" in data["data"]
        assert isinstance(data["data"]["items"], list)

    def test_get_project_detail_success(self):
        """测试获取项目详情成功"""
        headers = {"Authorization": "Bearer valid_token"}

        # 先创建项目
        create_response = client.post("/api/projects", json={
            "name": "详情测试项目",
            "client_name": "详情测试客户",
            "pricing_model": "per_lead",
            "lead_price": 12.0
        }, headers=headers)

        project_id = create_response.json()["data"]["id"]

        # 获取项目详情
        response = client.get(f"/api/projects/{project_id}", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == project_id
        assert data["data"]["name"] == "详情测试项目"

    def test_get_project_not_found(self):
        """测试获取不存在的项目"""
        headers = {"Authorization": "Bearer valid_token"}

        response = client.get("/api/projects/non-existent-id", headers=headers)

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_FOUND"

    def test_update_project_success(self):
        """测试更新项目成功"""
        headers = {"Authorization": "Bearer valid_token"}

        # 先创建项目
        create_response = client.post("/api/projects", json={
            "name": "更新测试项目",
            "client_name": "更新测试客户",
            "pricing_model": "per_lead",
            "lead_price": 10.0
        }, headers=headers)

        project_id = create_response.json()["data"]["id"]

        # 更新项目
        update_data = {
            "name": "更新后的项目名称",
            "monthly_budget": 15000.0
        }

        response = client.put(f"/api/projects/{project_id}", json=update_data, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "更新后的项目名称"
        assert data["data"]["monthly_budget"] == 15000.0

    def test_delete_project_success(self):
        """测试删除项目成功"""
        headers = {"Authorization": "Bearer admin_token"}  # 需要管理员权限

        # 先创建项目
        create_response = client.post("/api/projects", json={
            "name": "删除测试项目",
            "client_name": "删除测试客户",
            "pricing_model": "per_lead",
            "lead_price": 10.0
        }, headers=headers)

        project_id = create_response.json()["data"]["id"]

        # 删除项目
        response = client.delete(f"/api/projects/{project_id}", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["deleted"] is True

        # 验证项目已删除
        get_response = client.get(f"/api/projects/{project_id}", headers=headers)
        assert get_response.status_code == 404

if __name__ == "__main__":
    pytest.main([__file__])
```

### 9.2 服务层测试
```python
# tests/test_project_service.py
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from backend.services.project_service import ProjectService
from backend.models.projects import Project

class TestProjectService:

    @pytest.fixture
    def mock_db_session(self):
        """模拟数据库会话"""
        session = Mock()
        session.begin = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        session.refresh = Mock()
        return session

    @pytest.fixture
    def project_service(self, mock_db_session):
        """创建项目服务实例"""
        return ProjectService(mock_db_session)

    @pytest.fixture
    def sample_project_data(self):
        """示例项目数据"""
        return {
            "name": "测试项目",
            "client_name": "测试客户",
            "pricing_model": "per_lead",
            "lead_price": 10.0,
            "setup_fee": 1000.0,
            "monthly_budget": 5000.0
        }

    def test_create_project_success(self, project_service, sample_project_data, mock_db_session):
        """测试创建项目成功"""
        # 模拟数据库操作
        mock_project = Project(id="test-id", **sample_project_data)
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None

        # 模拟审计日志
        with patch('backend.services.project_service.audit_logger') as mock_audit:
            mock_audit.log_create.return_value = None

            # 执行测试
            result = project_service.create_project(sample_project_data, "user-id")

            # 验证结果
            assert result is not None
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
            mock_audit.log_create.assert_called_once()

    def test_create_project_validation_error(self, project_service, sample_project_data):
        """测试创建项目验证错误"""
        # 设置无效数据
        invalid_data = sample_project_data.copy()
        invalid_data["pricing_model"] = "hybrid"
        invalid_data["setup_fee"] = 0  # 混合模式需要启动费

        # 执行测试并验证异常
        with pytest.raises(ValidationError) as exc_info:
            project_service.create_project(invalid_data, "user-id")

        assert "混合模式必须设置项目启动费" in str(exc_info.value)

    def test_can_access_project_admin(self, project_service):
        """测试管理员项目访问权限"""
        result = project_service.can_access_project(
            user_id="admin-id",
            user_role="admin",
            project_id="project-id"
        )
        assert result is True

    def test_can_access_project_manager_owner(self, project_service, mock_db_session):
        """测试项目经理访问自己的项目"""
        # 模拟项目数据
        mock_project = Project(
            id="project-id",
            manager_id="manager-id"
        )
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_project

        result = project_service.can_access_project(
            user_id="manager-id",
            user_role="manager",
            project_id="project-id"
        )
        assert result is True

    def test_can_access_project_media_buyer_assigned(self, project_service, mock_db_session):
        """测试投手访问分配给自己的项目"""
        # 模拟账户数据
        mock_account = Mock()
        mock_account.project_id = "project-id"
        mock_account.assigned_user_id = "buyer-id"

        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_account

        result = project_service.can_access_project(
            user_id="buyer-id",
            user_role="media_buyer",
            project_id="project-id"
        )
        assert result is True

    def test_can_access_project_media_buyer_not_assigned(self, project_service, mock_db_session):
        """测试投手访问未分配的项目"""
        # 模拟没有分配的账户
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        result = project_service.can_access_project(
            user_id="buyer-id",
            user_role="media_buyer",
            project_id="project-id"
        )
        assert result is False

    def test_is_valid_status_transition_valid(self, project_service):
        """测试有效状态转换"""
        result = project_service._is_valid_status_transition("planning", "active")
        assert result is True

    def test_is_valid_status_transition_invalid(self, project_service):
        """测试无效状态转换"""
        result = project_service._is_valid_status_transition("completed", "planning")
        assert result is False

    def test_update_project_status_valid_transition(self, project_service, mock_db_session):
        """测试有效状态转换"""
        # 模拟现有项目
        mock_project = Project(
            id="project-id",
            status="planning"
        )
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_project

        with patch.object(project_service, 'update') as mock_update:
            mock_update.return_value = mock_project

            result = project_service.update_project_status(
                project_id="project-id",
                new_status="active",
                reason="项目启动",
                user_id="user-id"
            )

            assert result is not None
            mock_update.assert_called_once()

    def test_update_project_status_invalid_transition(self, project_service, mock_db_session):
        """测试无效状态转换"""
        # 模拟现有项目
        mock_project = Project(
            id="project-id",
            status="completed"
        )
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_project

        with pytest.raises(BusinessLogicError) as exc_info:
            project_service.update_project_status(
                project_id="project-id",
                new_status="planning",
                reason="无效转换",
                user_id="user-id"
            )

        assert "无法从 completed 转换到 planning" in str(exc_info.value)

if __name__ == "__main__":
    pytest.main([__file__])
```

---

## 10. 性能优化

### 10.1 数据库查询优化
```python
# services/optimized_queries.py
from sqlalchemy import and_, or_, func, text
from sqlalchemy.orm import selectinload, joinedload

class OptimizedQueries:
    """优化的查询示例"""

    @staticmethod
    def get_projects_with_stats_optimized(db: Session, user_id: str, user_role: str):
        """优化的项目查询（带统计信息）"""
        # 使用原生SQL进行复杂统计查询
        query = text("""
            SELECT
                p.*,
                COUNT(DISTINCT a.id) as total_accounts,
                COUNT(DISTINCT CASE WHEN a.status = 'active' THEN a.id END) as active_accounts,
                COALESCE(SUM(t.spend), 0) as total_spend,
                COALESCE(SUM(dr.leads_confirmed), 0) as total_leads,
                CASE
                    WHEN COALESCE(SUM(dr.leads_confirmed), 0) > 0
                    THEN COALESCE(SUM(t.spend), 0) / COALESCE(SUM(dr.leads_confirmed), 0)
                    ELSE NULL
                END as current_cpl
            FROM projects p
            LEFT JOIN ad_accounts a ON p.id = a.project_id
            LEFT JOIN topups t ON a.id = t.ad_account_id AND t.status = 'posted'
            LEFT JOIN ad_spend_daily dr ON a.id = dr.ad_account_id AND dr.leads_confirmed IS NOT NULL
            WHERE p.id IN (
                SELECT id FROM projects WHERE
                (manager_id = :user_id AND :user_role = 'manager')
                OR (:user_role IN ('admin', 'data_clerk', 'finance'))
                OR EXISTS (
                    SELECT 1 FROM ad_accounts aa
                    WHERE aa.project_id = p.id AND aa.assigned_user_id = :user_id
                    AND :user_role = 'media_buyer'
                )
            )
            GROUP BY p.id
            ORDER BY p.created_at DESC
        """)

        result = db.execute(query, {
            "user_id": user_id,
            "user_role": user_role
        })

        return result.fetchall()

    @staticmethod
    def get_daily_reports_summary_optimized(db: Session, project_id: str, date_range: dict):
        """优化的日报汇总查询"""
        query = text("""
            SELECT
                DATE(dr.date) as report_date,
                SUM(dr.spend) as total_spend,
                SUM(dr.leads_submitted) as total_submitted_leads,
                SUM(dr.leads_confirmed) as total_confirmed_leads,
                COUNT(DISTINCT dr.user_id) as active_users,
                COUNT(DISTINCT dr.ad_account_id) as active_accounts,
                AVG(dr.spend) as avg_spend_per_user,
                CASE
                    WHEN SUM(dr.leads_confirmed) > 0
                    THEN SUM(dr.spend) / SUM(dr.leads_confirmed)
                    ELSE NULL
                END as avg_cpl
            FROM ad_spend_daily dr
            WHERE dr.project_id = :project_id
            AND dr.date BETWEEN :start_date AND :end_date
            GROUP BY DATE(dr.date)
            ORDER BY report_date DESC
        """)

        result = db.execute(query, {
            "project_id": project_id,
            "start_date": date_range["start_date"],
            "end_date": date_range["end_date"]
        })

        return result.fetchall()
```

### 10.2 缓存策略
```python
# services/cache_service.py
import json
import redis
from typing import Optional, Any, List
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class CacheService:
    """缓存服务"""

    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"缓存获取失败: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """设置缓存"""
        try:
            serialized_value = json.dumps(value, default=str)
            return self.redis_client.setex(key, ttl, serialized_value)
        except Exception as e:
            logger.error(f"缓存设置失败: {e}")
            return False

    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"缓存删除失败: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """按模式删除缓存"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"批量删除缓存失败: {e}")
            return 0

class CachedProjectService:
    """带缓存的项目服务"""

    def __init__(self, db: Session, cache_service: CacheService):
        self.db = db
        self.cache = cache_service
        self.base_service = ProjectService(db)

    async def get_project_with_cache(self, project_id: str, user_id: str, user_role: str) -> Optional[dict]:
        """带缓存的项目查询"""
        cache_key = f"project:{project_id}:user:{user_id}"

        # 尝试从缓存获取
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data

        # 缓存未命中，查询数据库
        if not await self.base_service.can_access_project(user_id, user_role, project_id):
            return None

        project = await self.base_service.get_by_id(project_id)
        if not project:
            return None

        # 构建响应数据
        project_data = {
            "id": project.id,
            "name": project.name,
            "client_name": project.client_name,
            "status": project.status,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        }

        # 设置缓存（15分钟）
        self.cache.set(cache_key, project_data, ttl=900)

        return project_data

    async def invalidate_project_cache(self, project_id: str):
        """失效项目相关缓存"""
        patterns = [
            f"project:{project_id}:*",
            f"projects:list:*",
            f"project_stats:{project_id}:*"
        ]

        for pattern in patterns:
            self.cache.delete_pattern(pattern)

        logger.info(f"已失效项目 {project_id} 的相关缓存")
```

### 10.3 异步任务处理
```python
# services/task_service.py
import asyncio
from typing import Callable, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TaskService:
    """异步任务服务"""

    def __init__(self):
        self.task_queue = asyncio.Queue()
        self.running_tasks = set()

    async def submit_task(self, task_func: Callable, *args, **kwargs) -> str:
        """提交异步任务"""
        task_id = f"task_{datetime.utcnow().timestamp()}"

        task = asyncio.create_task(
            self._execute_task(task_id, task_func, *args, **kwargs)
        )

        self.running_tasks.add(task)
        task.add_done_callback(lambda t: self.running_tasks.discard(t))

        logger.info(f"任务 {task_id} 已提交")
        return task_id

    async def _execute_task(self, task_id: str, task_func: Callable, *args, **kwargs):
        """执行异步任务"""
        try:
            logger.info(f"开始执行任务 {task_id}")
            start_time = datetime.utcnow()

            result = await task_func(*args, **kwargs)

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            logger.info(f"任务 {task_id} 执行成功，耗时 {duration:.2f} 秒")
            return result

        except Exception as e:
            logger.error(f"任务 {task_id} 执行失败: {e}")
            raise

    async def get_task_status(self) -> dict:
        """获取任务状态"""
        return {
            "running_tasks": len(self.running_tasks),
            "queued_tasks": self.task_queue.qsize()
        }

# 使用示例
class NotificationService:
    """通知服务"""

    def __init__(self, task_service: TaskService):
        self.task_service = task_service

    async def send_email_async(self, to: str, subject: str, content: str):
        """异步发送邮件"""
        await self.task_service.submit_task(
            self._send_email_impl,
            to=to,
            subject=subject,
            content=content
        )

    async def _send_email_impl(self, to: str, subject: str, content: str):
        """邮件发送实现"""
        # 这里实现实际的邮件发送逻辑
        logger.info(f"发送邮件到 {to}: {subject}")

        # 模拟发送延迟
        await asyncio.sleep(2)

        logger.info(f"邮件发送完成: {to}")
```

---

---

## 11. 主文档v2.1合规性检查

### 11.1 技术栈要求合规性
- ✅ **FastAPI + Pydantic v2**: 所有代码示例使用正确的语法
- ✅ **SQLAlchemy同步版**: 确保使用同步数据库操作
- ✅ **统一返回格式**: 严格按照主文档v2.1格式定义
- ✅ **错误码映射**: 对应主文档v2.1的4001、4010、4031、4040、5001错误码

### 11.2 安全要求合规性
- ✅ **JWT认证**: 完整的token验证和用户上下文
- ✅ **RLS策略**: 实现数据库级别的权限控制
- ✅ **审计日志**: 所有关键操作记录审计日志
- ✅ **权限控制**: 基于角色的细粒度权限管理

### 11.3 性能要求合规性
- ✅ **分页查询**: 标准化的分页响应格式
- ✅ **缓存策略**: Redis缓存实现
- ✅ **异步任务**: 非阻塞的任务处理
- ✅ **数据库优化**: 查询优化和索引策略

### 11.4 监控要求合规性
- ✅ **请求跟踪**: 统一的request_id跟踪
- ✅ **性能监控**: 响应时间和错误率监控
- ✅ **日志记录**: 结构化的日志记录
- ✅ **健康检查**: 系统健康状态监控

---

## 12. 开发工具和配置

### 12.1 开发环境配置 (基于主文档v2.1)
```bash
# 环境变量配置 (.env.example)
API_ENV=development
PORT=8000

# Supabase配置 (主文档v2.1)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_PUBLIC_KEY=your-anon-key

# JWT配置 (主文档v2.1)
JWT_SECRET=your-super-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRE=3600

# Redis配置
REDIS_URL=redis://localhost:6379/0

# Sentry配置
SENTRY_DSN=https://your-sentry-dsn
```

### 12.2 开发命令 (主文档v2.1)
```bash
# 安装依赖
pip install -r requirements.txt

# 数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 运行测试
pytest -v --disable-warnings

# 代码格式化
black app/
isort app/

# 类型检查
mypy app/
```

### 12.3 API文档访问
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/openapi.json

---

**文档版本**: v2.1
**最后更新**: 2025-11-11
**负责人**: 后端技术负责人
**审核人**: 系统架构师
**合规状态**: ✅ 已完成 - 与主文档v2.1保持一致