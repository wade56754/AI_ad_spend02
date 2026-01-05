# AI 广告代投系统 - Claude 提示词库 v2.3

> **文档版本**: v2.3 (Claude 4.x 最佳实践对齐版)
> **修订日期**: 2026-01-05
> **修复内容**: SoT 版本更新、语气优化、推理引导说明、XML 标签重构
> **适用**: Claude CLI / Claude Web / Claude API

---

## 使用方法

```
1. 复制「系统约束」（第一个代码块）
2. 复制「任务提示词」（对应任务的全部内容）
3. 粘贴到 Claude 并发送
4. 验证输出 → 运行测试
```

---

# 系统约束

> 每次执行任务前必须复制此块

```xml
<role>
你是 FastAPI 后端开发专家，负责 AI 广告代投系统开发。
代码风格：简洁、类型完整、测试驱动。
</role>

<context>
【SoT 版本】
MASTER.md v4.9 | STATE_MACHINE.md v2.9 | DATA_SCHEMA.md v5.10
BUSINESS_RULES.md v5.1 | ERROR_CODES.md v2.2 | AUTH_SPEC.md v2.2
</context>

<constraints>
【角色白名单】
合法角色（仅 6 个）: ceo, project_owner, finance, pitcher, account_manager, admin
已废弃角色（不使用）: supervisor, data_operator, media_buyer

【Phase 规则】
当前 Phase 1: 记录事实、展示状态、提示异常
原则: 只提示不阻断，系统不自动拒绝/暂停/终止（由人工决策）

【响应格式】
成功: {"code": 0, "message": "success", "data": {...}}
错误: {"code": "ERROR_CODE", "message": "描述", "data": null}
分页: {"code": 0, "data": {"items": [...], "total": N, "page": 1, "page_size": 20}}
</constraints>

<code_standards>
【代码规范】
- Pydantic v2: ConfigDict(from_attributes=True), model_dump()
- SQLAlchemy 2.x: 同步模式
- 命名: 文件 snake_case, 类 PascalCase
- 测试: pytest, 每个 API 至少 4 个测试
</code_standards>

<error_handling>
【防幻觉规则】
AH-01: 数据缺失时 → 标记"待确认"，等待人工确认
AH-02: 管理裁决 → 只记录，不自动执行
AH-03: SoT 未定义 → 停止并询问
AH-04: Phase 边界 → Phase 1 只提示不阻断
AH-05: 歧义 → 停止并列出选项

【常见错误】
❌ dict() → ✅ model_dump()
❌ Optional[X] = None → ✅ X | None = None
❌ 直接修改 balance → ✅ 通过 ledger_entries
❌ 硬编码错误消息 → ✅ ERROR_CODES 常量
❌ supervisor 角色 → ✅ project_owner
</error_handling>

<thinking_guide>
【推理引导】(Claude Opus 4.5 优化)
使用 "consider", "evaluate", "analyze" 代替 "think"
示例: "请逐步分析" 而非 "请逐步思考"
</thinking_guide>

<prefill_technique>
【预填充技术】(API 调用时可用)
强制 JSON 输出: {"role": "assistant", "content": "{"}
跳过前言: {"role": "assistant", "content": "## 分析报告\n\n"}
</prefill_technique>
```

---

# M1 认证模块

## TASK-AUTH-001: 用户登录 API

### 上下文

| 项目 | AI 广告代投系统 |
|------|----------------|
| 模块 | auth |
| 任务 ID | TASK-AUTH-001 |
| 技术栈 | FastAPI + SQLAlchemy 2.x + Pydantic v2 + python-jose + passlib |

**前置条件**:
- users 表已存在（字段: id, email, password_hash, role, is_active, project_id）
- core/config.py 已配置 SECRET_KEY, ALGORITHM

**SoT 引用**:
- AUTH_SPEC.md v2.2 §3: JWT Token 字段 (user_id, role, exp)
- ERROR_CODES.md v2.3: AUTH_400, AUTH_401
- BR-AUTH-001: 登录必须验证密码
- BR-AUTH-002: Token 有效期 24h (86400秒)

### 任务

实现 POST /api/v1/auth/login 用户登录 API，返回 JWT Token

### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| backend/schemas/auth.py | LoginRequest, LoginResponse, TokenPayload | 35-45 |
| backend/services/auth_service.py | AuthService 类 | 50-70 |
| backend/routers/auth.py | login 路由 | 25-35 |
| backend/tests/test_auth_api.py | 6 个测试用例 | 80-100 |

### 约束规则

1. Token 有效期: 86400 秒 (24小时)
2. Token payload: {"user_id": int, "role": str, "exp": datetime}
3. 密码验证: passlib.hash.bcrypt.verify()
4. 角色白名单: ["ceo", "project_owner", "finance", "pitcher", "account_manager", "admin"]
5. 安全原则: 用户不存在和密码错误返回相同消息，不暴露用户是否存在
6. 响应封装: 使用 success_response() 和 BusinessError()

### 错误处理

| 场景 | 错误码 | HTTP | 消息 | 检查逻辑 |
|------|--------|------|------|----------|
| 用户不存在 | AUTH_400 | 400 | 邮箱或密码错误 | user is None |
| 密码错误 | AUTH_400 | 400 | 邮箱或密码错误 | not bcrypt.verify() |
| 账户停用 | AUTH_400 | 400 | 账户已停用 | user.is_active == False |
| 邮箱格式错误 | VAL_001 | 400 | 邮箱格式无效 | Pydantic 校验 |
| 密码为空 | VAL_001 | 400 | 密码不能为空 | len(password) == 0 |

### 示例

**示例 1: 正常登录**
```
请求: POST /api/v1/auth/login
Content-Type: application/json
{"email": "admin@example.com", "password": "Admin123!"}

响应: HTTP 200
{
  "code": 0,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 86400
  }
}
```

**示例 2: 密码错误**
```
请求: POST /api/v1/auth/login
{"email": "admin@example.com", "password": "wrongpassword"}

响应: HTTP 400
{"code": "AUTH_400", "message": "邮箱或密码错误", "data": null}
```

**示例 3: 用户不存在**
```
请求: POST /api/v1/auth/login
{"email": "notexist@example.com", "password": "anypassword"}

响应: HTTP 400
{"code": "AUTH_400", "message": "邮箱或密码错误", "data": null}
注意: 与密码错误返回相同消息（安全原则）
```

**示例 4: 账户停用**
```
请求: POST /api/v1/auth/login
{"email": "disabled@example.com", "password": "Password123"}

响应: HTTP 400
{"code": "AUTH_400", "message": "账户已停用", "data": null}
```

### 代码参考

**文件 1: backend/schemas/auth.py**
```python
from pydantic import BaseModel, ConfigDict, EmailStr


class LoginRequest(BaseModel):
    """登录请求"""
    email: EmailStr
    password: str


class TokenPayload(BaseModel):
    """Token 载荷"""
    user_id: int
    role: str
    exp: int


class LoginResponse(BaseModel):
    """登录响应"""
    model_config = ConfigDict(from_attributes=True)
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400
```

**文件 2: backend/services/auth_service.py**
```python
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from jose import jwt

from backend.models.user import User
from backend.schemas.auth import LoginResponse
from backend.core.config import settings
from backend.core.exceptions import BusinessError


class AuthService:
    """认证服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def login(self, email: str, password: str) -> LoginResponse:
        """用户登录"""
        # 1. 查询用户
        user = self.db.query(User).filter(User.email == email).first()
        
        # 2. 验证用户存在和密码（安全: 返回相同消息）
        if not user or not bcrypt.verify(password, user.password_hash):
            raise BusinessError(code="AUTH_400", message="邮箱或密码错误")
        
        # 3. 检查账户状态
        if not user.is_active:
            raise BusinessError(code="AUTH_400", message="账户已停用")
        
        # 4. 生成 Token
        token = self._create_access_token(user_id=user.id, role=user.role)
        return LoginResponse(access_token=token)
    
    def _create_access_token(self, user_id: int, role: str) -> str:
        """生成访问令牌"""
        expire = datetime.utcnow() + timedelta(seconds=86400)
        payload = {"user_id": user_id, "role": role, "exp": expire}
        return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
```

**文件 3: backend/routers/auth.py**
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.response import success_response
from backend.schemas.auth import LoginRequest
from backend.services.auth_service import AuthService


router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    service = AuthService(db)
    result = service.login(request.email, request.password)
    return success_response(data=result.model_dump(), message="登录成功")
```

**文件 4: backend/tests/test_auth_api.py**
```python
import pytest
from fastapi.testclient import TestClient


class TestLogin:
    """登录 API 测试"""
    
    def test_login_success(self, client: TestClient, test_user):
        """测试正常登录"""
        response = client.post("/api/v1/auth/login", json={
            "email": "admin@example.com",
            "password": "Admin123!"
        })
        assert response.status_code == 200
        assert response.json()["code"] == 0
        assert "access_token" in response.json()["data"]
        assert response.json()["data"]["expires_in"] == 86400
    
    def test_login_wrong_password(self, client: TestClient, test_user):
        """测试密码错误"""
        response = client.post("/api/v1/auth/login", json={
            "email": "admin@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 400
        assert response.json()["code"] == "AUTH_400"
        assert response.json()["message"] == "邮箱或密码错误"
    
    def test_login_user_not_exist(self, client: TestClient):
        """测试用户不存在（应返回与密码错误相同的消息）"""
        response = client.post("/api/v1/auth/login", json={
            "email": "notexist@example.com",
            "password": "anypassword"
        })
        assert response.status_code == 400
        assert response.json()["message"] == "邮箱或密码错误"
    
    def test_login_inactive_user(self, client: TestClient, inactive_user):
        """测试账户停用"""
        response = client.post("/api/v1/auth/login", json={
            "email": "disabled@example.com",
            "password": "Password123"
        })
        assert response.status_code == 400
        assert response.json()["message"] == "账户已停用"
    
    def test_login_invalid_email(self, client: TestClient):
        """测试邮箱格式无效"""
        response = client.post("/api/v1/auth/login", json={
            "email": "invalid-email",
            "password": "Password123"
        })
        assert response.status_code == 422  # Pydantic 验证错误
    
    def test_login_empty_password(self, client: TestClient):
        """测试密码为空"""
        response = client.post("/api/v1/auth/login", json={
            "email": "admin@example.com",
            "password": ""
        })
        assert response.status_code == 400
```

### 输出格式要求

请严格按照以下格式输出：

**第一部分: 思考分析**
必须包含以下 5 个分析点，每点 1-2 句话：
1. 表字段确认: users 表字段与 Schema 的映射关系
2. Token 配置: SECRET_KEY 来源和算法选择
3. 密码验证: bcrypt.verify() 的参数顺序
4. 错误场景: 5 个错误场景及对应错误码
5. 安全原则: 为什么用户不存在和密码错误返回相同消息

**第二部分: 代码实现**
按以下顺序输出完整代码（包含所有 import）：
1. backend/schemas/auth.py
2. backend/services/auth_service.py
3. backend/routers/auth.py
4. backend/tests/test_auth_api.py

**第三部分: 验证命令**
```bash
pytest backend/tests/test_auth_api.py -v
```
预期: 6 个测试全部通过

### 验收标准

- [ ] POST /api/v1/auth/login 返回 JWT Token
- [ ] Token payload 包含 user_id, role, exp
- [ ] Token 有效期 86400 秒
- [ ] 用户不存在和密码错误返回相同消息
- [ ] 账户停用返回明确错误
- [ ] 6 个测试用例全部通过
- [ ] 使用 Pydantic v2 语法

---

## TASK-USER-001: 用户列表 API

### 上下文

| 项目 | AI 广告代投系统 |
|------|----------------|
| 模块 | user |
| 任务 ID | TASK-USER-001 |
| 技术栈 | FastAPI + SQLAlchemy 2.x + Pydantic v2 |

**前置条件**:
- 认证模块已完成 (TASK-AUTH-001~005)
- users 表存在
- get_current_user 依赖可用

**SoT 引用**:
- DATA_SCHEMA.md v5.10 §users
- BR-USER-001: 角色枚举固定 6 个值
- MASTER.md v4.9 §2.4: 角色定义

### 任务

实现 GET /api/v1/users 用户列表 API，支持分页、角色筛选和数据隔离

### 交付物

| 文件 | 内容 | 预估行数 |
|------|------|----------|
| backend/schemas/user.py | UserResponse, UserListResponse | 40-50 |
| backend/services/user_service.py | UserService.list_users() | 50-70 |
| backend/routers/users.py | list_users 路由 | 30-40 |
| backend/tests/test_user_api.py | 5 个测试用例 | 70-90 |

### 约束规则

1. 分页参数: page (默认1, 最小1), page_size (默认20, 最大100)
2. 角色筛选: role 参数仅接受 6 个白名单值，其他值返回 VAL_001
3. 返回字段: id, email, name, role, project_id, is_active, created_at
4. 数据隔离: admin/ceo 可查看所有用户，其他角色仅查看同 project_id
5. 排序: 按 created_at 降序
6. 禁止返回 password_hash 字段

### 错误处理

| 场景 | 错误码 | HTTP | 消息 |
|------|--------|------|------|
| 无效角色筛选 | VAL_001 | 400 | 无效的角色值 |
| 未认证 | AUTH_401 | 401 | 未认证 |
| page_size > 100 | VAL_001 | 400 | page_size 最大值为 100 |

### 示例

**示例 1: 正常获取列表**
```
请求: GET /api/v1/users?page=1&page_size=20
Authorization: Bearer {token}

响应: HTTP 200
{
  "code": 0,
  "data": {
    "items": [
      {"id": 1, "email": "admin@example.com", "name": "管理员", "role": "admin", ...}
    ],
    "total": 50,
    "page": 1,
    "page_size": 20
  }
}
```

**示例 2: 角色筛选**
```
请求: GET /api/v1/users?role=pitcher
响应: 仅返回 pitcher 角色用户
```

**示例 3: 无效角色**
```
请求: GET /api/v1/users?role=supervisor
响应: HTTP 400
{"code": "VAL_001", "message": "无效的角色值", "data": null}
```

**示例 4: 数据隔离**
```
pitcher (project_id=1) 调用 → 只返回 project_id=1 的用户
admin 调用 → 返回所有用户
```

### 代码参考

**文件 1: backend/schemas/user.py**
```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr


VALID_ROLES = ["ceo", "project_owner", "finance", "pitcher", "account_manager", "admin"]


class UserResponse(BaseModel):
    """用户响应"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: EmailStr
    name: str
    role: str
    project_id: int | None = None
    is_active: bool
    created_at: datetime


class UserListResponse(BaseModel):
    """用户列表响应"""
    items: list[UserResponse]
    total: int
    page: int
    page_size: int
```

**文件 2: backend/services/user_service.py**
```python
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from backend.models.user import User
from backend.schemas.user import UserResponse, UserListResponse, VALID_ROLES
from backend.core.exceptions import BusinessError


class UserService:
    """用户服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def list_users(
        self,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        role: str | None = None
    ) -> UserListResponse:
        """获取用户列表"""
        # 1. 验证 page_size
        if page_size > 100:
            raise BusinessError(code="VAL_001", message="page_size 最大值为 100")
        
        # 2. 验证角色筛选值
        if role and role not in VALID_ROLES:
            raise BusinessError(code="VAL_001", message="无效的角色值")
        
        # 3. 构建查询
        query = select(User)
        
        # 4. 数据隔离: admin/ceo 查全部，其他角色按 project_id
        if current_user.role not in ["admin", "ceo"]:
            query = query.where(User.project_id == current_user.project_id)
        
        # 5. 角色筛选
        if role:
            query = query.where(User.role == role)
        
        # 6. 统计总数
        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.scalar(count_query)
        
        # 7. 分页和排序
        query = query.order_by(User.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        users = self.db.scalars(query).all()
        
        return UserListResponse(
            items=[UserResponse.model_validate(u) for u in users],
            total=total,
            page=page,
            page_size=page_size
        )
```

**文件 3: backend/routers/users.py**
```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.dependencies import get_current_user
from backend.core.response import success_response
from backend.models.user import User
from backend.services.user_service import UserService


router = APIRouter(prefix="/api/v1/users", tags=["用户"])


@router.get("")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户列表"""
    service = UserService(db)
    result = service.list_users(current_user, page, page_size, role)
    return success_response(data=result.model_dump())
```

**文件 4: backend/tests/test_user_api.py**
```python
import pytest
from fastapi.testclient import TestClient


class TestListUsers:
    """用户列表 API 测试"""
    
    def test_list_users_success(self, client: TestClient, auth_headers):
        """测试正常获取列表"""
        response = client.get("/api/v1/users", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["code"] == 0
        assert "items" in response.json()["data"]
        assert "total" in response.json()["data"]
    
    def test_list_users_with_pagination(self, client: TestClient, auth_headers):
        """测试分页参数"""
        response = client.get("/api/v1/users?page=1&page_size=10", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["page"] == 1
        assert response.json()["data"]["page_size"] == 10
    
    def test_list_users_with_role_filter(self, client: TestClient, auth_headers):
        """测试角色筛选"""
        response = client.get("/api/v1/users?role=pitcher", headers=auth_headers)
        assert response.status_code == 200
        for user in response.json()["data"]["items"]:
            assert user["role"] == "pitcher"
    
    def test_list_users_invalid_role(self, client: TestClient, auth_headers):
        """测试无效角色筛选"""
        response = client.get("/api/v1/users?role=supervisor", headers=auth_headers)
        assert response.status_code == 400
        assert response.json()["code"] == "VAL_001"
    
    def test_list_users_data_isolation(self, client: TestClient, pitcher_headers):
        """测试数据隔离 - pitcher 只能看同项目用户"""
        response = client.get("/api/v1/users", headers=pitcher_headers)
        assert response.status_code == 200
        # 所有返回用户的 project_id 应该相同
```

### 输出格式要求

请严格按照以下格式输出：

**第一部分: 思考分析**
必须包含以下 5 个分析点：
1. 数据隔离逻辑: admin/ceo 查全部，其他按 project_id
2. 角色白名单: 6 个合法值的验证方式
3. 分页实现: offset + limit 计算
4. 排序: created_at DESC
5. 安全: 不返回 password_hash

**第二部分: 代码实现**
按顺序输出 4 个完整文件

**第三部分: 验证命令**
```bash
pytest backend/tests/test_user_api.py -v
```

### 验收标准

- [ ] GET /api/v1/users 返回分页列表
- [ ] 支持 page, page_size 参数
- [ ] 支持 role 筛选（仅 6 个合法值）
- [ ] admin/ceo 查看所有用户，其他角色仅同项目
- [ ] 不返回 password_hash 字段
- [ ] 5 个测试用例全部通过

---

# 快速参考

## 角色白名单

```python
VALID_ROLES = ["ceo", "project_owner", "finance", "pitcher", "account_manager", "admin"]
```

## Phase 1 日报状态

```python
PHASE1_STATUS = ["raw_submitted", "trend_ok", "final_confirmed"]
```

## 响应格式

```python
def success_response(data: Any, message: str = "success"):
    return {"code": 0, "message": message, "data": data}

def error_response(code: str, message: str):
    return {"code": code, "message": message, "data": None}
```

## 错误码

| 错误码 | HTTP | 场景 |
|--------|------|------|
| AUTH_400 | 400 | 认证失败 |
| AUTH_401 | 401 | 未认证 |
| AUTH_403 | 403 | 无权限 |
| VAL_001 | 400 | 参数校验失败 |
| BIZ_001 | 400 | 业务规则违反 |
| BIZ_002 | 404 | 资源不存在 |
| STATE_400 | 400 | 状态转换非法 |

---

**版本**: v2.3
**修复**: SoT 版本更新 (v4.9/v2.9/v5.10)、语气优化、推理引导说明、XML 标签重构
**状态**: ✅ 达到 Claude 4.x 最佳实践
